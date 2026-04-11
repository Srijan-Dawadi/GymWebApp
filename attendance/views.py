import csv
import json
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from accounts.mixins import AdminRequiredMixin, StaffRequiredMixin
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
        today = timezone.localdate()
        try:
            Attendance.objects.create(member=member, date=today, method='manual')
            messages.success(request, f"✅ {member.full_name} checked in manually.")
        except IntegrityError:
            messages.warning(request, f"{member.full_name} has already checked in today.")
        return redirect('attendance')


@login_required
def checkin_api(request):
    """Face recognition check-in endpoint."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        body = json.loads(request.body)
        member_id = body.get('member_id')
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not member_id:
        return JsonResponse({'error': 'member_id required'}, status=400)

    member = Member.objects.filter(pk=member_id).first()
    if not member:
        return JsonResponse({'error': 'Member not found'}, status=404)

    today = timezone.localdate()
    try:
        Attendance.objects.create(member=member, date=today, method='face')
        return JsonResponse({'status': 'ok', 'member_name': member.full_name})
    except IntegrityError:
        return JsonResponse({'status': 'duplicate', 'member_name': member.full_name}, status=409)


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
                record.check_in_time.strftime('%H:%M:%S'),
                record.method,
            ])
        return response
