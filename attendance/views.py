import base64
import csv
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View

from accounts.mixins import AdminRequiredMixin
from members.models import Member
from .models import Attendance


@method_decorator(login_required, name='dispatch')
class AttendanceView(View):
    template_name = 'attendance/attendance.html'

    def get(self, request):
        today = timezone.localdate()
        today_records = Attendance.objects.filter(date=today).select_related('member').order_by('-check_in_time')
        all_records = Attendance.objects.select_related('member').order_by('-date', '-check_in_time')
        paginator = Paginator(all_records, 30)
        page = paginator.get_page(request.GET.get('page'))
        members = Member.objects.filter(status='active').order_by('full_name')
        return render(request, self.template_name, {
            'today_records': today_records,
            'page_obj': page,
            'members': members,
            'today': today,
        })

    def post(self, request):
        """Manual check-in."""
        member_id = request.POST.get('member_id')
        member = get_object_or_404(Member, pk=member_id)

        # Sync status before checking
        from members.models import Member as M
        M.sync_expired_statuses()
        member.refresh_from_db()

        today = timezone.localdate()

        if member.status == 'suspended':
            messages.error(request, f"⛔ {member.full_name}'s membership is suspended. Contact admin.")
            return redirect('attendance')
        if member.status == 'expired':
            messages.error(request, f"⛔ {member.full_name}'s membership has expired (since {member.expiry_date}). Please renew.")
            return redirect('attendance')

        try:
            Attendance.objects.create(member=member, date=today, method='manual')
            messages.success(request, f"✅ {member.full_name} checked in manually.")
        except IntegrityError:
            messages.warning(request, f"{member.full_name} has already checked in today.")
        return redirect('attendance')


@login_required
def checkin_api(request):
    """
    Face recognition check-in.
    Expects JSON body: { "image": "<base64-encoded JPEG frame>" }
    Server extracts embedding via InsightFace and matches against stored members.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        body = json.loads(request.body)
        image_b64 = body.get('image')
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not image_b64:
        return JsonResponse({'error': 'image field required'}, status=400)

    # Decode base64 → bytes
    try:
        # Strip data URL prefix if present (data:image/jpeg;base64,...)
        if ',' in image_b64:
            image_b64 = image_b64.split(',', 1)[1]
        image_bytes = base64.b64decode(image_b64)
    except Exception:
        return JsonResponse({'error': 'Invalid image data'}, status=400)

    # Extract embedding
    from face_service import extract_embedding, find_best_match
    embedding = extract_embedding(image_bytes)

    if embedding is None:
        return JsonResponse({'status': 'no_face', 'message': 'No face detected in frame'}, status=200)

    # Match against stored members
    member_id, score = find_best_match(embedding)

    if member_id is None:
        return JsonResponse({'status': 'unknown', 'message': 'Face not recognised', 'score': round(score, 3)}, status=200)

    member = Member.objects.filter(pk=member_id).first()
    if not member:
        return JsonResponse({'error': 'Member not found'}, status=404)

    # Sync status before checking
    from members.models import Member as M
    M.sync_expired_statuses()
    member.refresh_from_db()

    if member.status == 'suspended':
        return JsonResponse({
            'status': 'suspended',
            'member_name': member.full_name,
            'message': f"{member.full_name}'s membership is suspended.",
        }, status=200)

    if member.status == 'expired':
        return JsonResponse({
            'status': 'expired',
            'member_name': member.full_name,
            'message': f"{member.full_name}'s membership expired on {member.expiry_date}. Please renew.",
        }, status=200)

    today = timezone.localdate()
    try:
        Attendance.objects.create(member=member, date=today, method='face')
        return JsonResponse({
            'status': 'ok',
            'member_name': member.full_name,
            'member_id': member.pk,
            'score': round(score, 3),
        })
    except IntegrityError:
        return JsonResponse({
            'status': 'duplicate',
            'member_name': member.full_name,
            'member_id': member.pk,
        }, status=409)


class AttendanceExportView(AdminRequiredMixin, View):
    def get(self, request):
        qs = Attendance.objects.select_related('member').order_by('-date', '-check_in_time')
        start = request.GET.get('start')
        end = request.GET.get('end')
        if start:
            qs = qs.filter(date__gte=start)
        if end:
            qs = qs.filter(date__lte=end)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="attendance.csv"'
        writer = csv.writer(response)
        writer.writerow(['Member Name', 'Date', 'Check-in Time', 'Method'])
        for record in qs:
            writer.writerow([
                record.member.full_name,
                record.date,
                record.check_in_time.strftime('%I:%M %p'),
                record.method,
            ])
        return response
