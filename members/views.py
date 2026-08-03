import json
from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import ProtectedError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from accounts.mixins import AdminRequiredMixin, StaffRequiredMixin
from .forms import MemberForm
from .models import Member


@method_decorator(login_required, name='dispatch')
class MemberListView(View):
    template_name = 'members/list.html'

    def get(self, request):
        qs = Member.objects.select_related('membership_plan').order_by('full_name')
        q = request.GET.get('q', '').strip()
        status_filter = request.GET.get('status', '').strip()
        if q:
            qs = (qs.filter(full_name__icontains=q) | qs.filter(email__icontains=q)).distinct()
        if status_filter:
            qs = qs.filter(status=status_filter)
        paginator = Paginator(qs, 20)
        page = paginator.get_page(request.GET.get('page'))
        return render(request, self.template_name, {'page_obj': page, 'q': q, 'status_filter': status_filter})


@method_decorator(login_required, name='dispatch')
class MemberDetailView(View):
    template_name = 'members/detail.html'

    def get(self, request, pk):
        import json as _json
        from datetime import timedelta
        from django.db.models import Sum

        member      = get_object_or_404(Member, pk=pk)
        payments    = member.payments.order_by('-date_paid')
        attendances = member.attendances.order_by('-date')[:30]

        today             = date.today()
        days_until_expiry = (member.expiry_date - today).days
        total_paid        = payments.aggregate(t=Sum('amount'))['t'] or 0

        # ── Chart 1: 30-day attendance sparkline (1 = present, 0 = absent) ──
        att_dates = set(member.attendances.values_list('date', flat=True))
        spark_labels, spark_data = [], []
        for i in range(29, -1, -1):
            d = today - timedelta(days=i)
            spark_labels.append(d.strftime('%d %b').lstrip('0') or '0')
            spark_data.append(1 if d in att_dates else 0)
        sessions_30d = sum(spark_data)

        # ── Chart 2: last 6 months payment bar ──
        pay_labels, pay_amounts = [], []
        for i in range(5, -1, -1):
            # first day of each month going back
            ref = today.replace(day=1)
            month_start = date(ref.year, ref.month, 1)
            # subtract i months
            m_num = month_start.month - i
            y_num = month_start.year
            while m_num <= 0:
                m_num += 12
                y_num -= 1
            ms = date(y_num, m_num, 1)
            # last day of that month
            if ms.month == 12:
                me = date(ms.year + 1, 1, 1) - timedelta(days=1)
            else:
                me = date(ms.year, ms.month + 1, 1) - timedelta(days=1)
            amt = member.payments.filter(
                date_paid__gte=ms, date_paid__lte=me
            ).aggregate(t=Sum('amount'))['t'] or 0
            pay_labels.append(ms.strftime('%b %Y'))
            pay_amounts.append(float(amt))

        return render(request, self.template_name, {
            'member':            member,
            'payments':          payments,
            'attendances':       attendances,
            'today':             today,
            'days_until_expiry': days_until_expiry,
            'total_paid':        total_paid,
            'sessions_30d':      sessions_30d,
            'spark_labels':      _json.dumps(spark_labels),
            'spark_data':        _json.dumps(spark_data),
            'pay_labels':        _json.dumps(pay_labels),
            'pay_amounts':       _json.dumps(pay_amounts),
        })


def _extract_and_save_embedding(member):
    """Read the member's saved photo and extract InsightFace embedding."""
    from face_service import extract_embedding, invalidate_descriptor_cache
    try:
        with open(member.photo.path, 'rb') as f:
            image_bytes = f.read()
        result = extract_embedding(image_bytes)
        # extract_embedding returns a dict with 'status' and 'embedding'
        if result and result.get('status') == 'ok' and result.get('embedding'):
            Member.objects.filter(pk=member.pk).update(face_descriptor=result['embedding'])
            invalidate_descriptor_cache()
            return True
        return False
    except Exception:
        return False


class MemberCreateView(StaffRequiredMixin, View):
    template_name = 'members/form.html'

    def get(self, request):
        form = MemberForm(initial={'join_date': date.today()})
        return render(request, self.template_name, {'form': form, 'title': 'Add Member'})

    def post(self, request):
        form = MemberForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save()
            # Check for multi-angle embeddings submitted as JSON
            embeddings_json = request.POST.get('face_embeddings', '')
            if embeddings_json:
                try:
                    embeddings = json.loads(embeddings_json)
                    if embeddings and isinstance(embeddings, list) and len(embeddings) > 0:
                        from face_service import invalidate_descriptor_cache
                        Member.objects.filter(pk=member.pk).update(face_descriptor=embeddings)
                        invalidate_descriptor_cache()
                        messages.success(request, f"Member '{member.full_name}' registered with {len(embeddings)}-angle face recognition.")
                        return redirect('member_detail', pk=member.pk)
                except (json.JSONDecodeError, Exception):
                    pass
            # Fallback: extract from uploaded photo
            if member.photo:
                ok = _extract_and_save_embedding(member)
                if not ok:
                    messages.warning(request, f"Member '{member.full_name}' saved but no face detected in the photo.")
                else:
                    messages.success(request, f"Member '{member.full_name}' registered with face recognition.")
            else:
                messages.success(request, f"Member '{member.full_name}' registered (no photo).")
            return redirect('member_detail', pk=member.pk)
        return render(request, self.template_name, {'form': form, 'title': 'Add Member'})


class MemberEditView(StaffRequiredMixin, View):
    template_name = 'members/form.html'

    def get(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        form = MemberForm(instance=member)
        return render(request, self.template_name, {'form': form, 'title': 'Edit Member', 'member': member})

    def post(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        form = MemberForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            member = form.save()
            # Check for new multi-angle embeddings
            embeddings_json = request.POST.get('face_embeddings', '')
            if embeddings_json:
                try:
                    embeddings = json.loads(embeddings_json)
                    if embeddings and isinstance(embeddings, list) and len(embeddings) > 0:
                        from face_service import invalidate_descriptor_cache
                        Member.objects.filter(pk=member.pk).update(face_descriptor=embeddings)
                        invalidate_descriptor_cache()
                        messages.success(request, f"Member updated with {len(embeddings)}-angle face recognition.")
                        return redirect('member_detail', pk=member.pk)
                except (json.JSONDecodeError, Exception):
                    pass
            # Fallback: re-extract from new photo if uploaded
            if request.FILES.get('photo'):
                ok = _extract_and_save_embedding(member)
                if not ok:
                    messages.warning(request, "Member updated but no face detected in the new photo.")
                else:
                    messages.success(request, "Member updated with new face data.")
            else:
                messages.success(request, "Member updated successfully.")
            return redirect('member_detail', pk=member.pk)
        return render(request, self.template_name, {'form': form, 'title': 'Edit Member', 'member': member})


class MemberDeleteView(AdminRequiredMixin, View):
    template_name = 'members/confirm_delete.html'

    def get(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        return render(request, self.template_name, {'member': member})

    def post(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        name = member.full_name
        try:
            member.delete()
        except ProtectedError:
            messages.error(
                request,
                f"Cannot delete '{name}' — they have payment/attendance history. "
                f"Suspend the member instead to keep their records intact."
            )
            return redirect('member_detail', pk=pk)
        messages.success(request, f"Member '{name}' deleted.")
        return redirect('member_list')


class MemberToggleSuspendView(AdminRequiredMixin, View):
    """Admin can suspend an active/expired member or reactivate a suspended one."""

    def post(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        if member.status == 'suspended':
            # Reactivate — let the model recalculate status from expiry_date
            from datetime import date
            member.status = 'active' if member.expiry_date >= date.today() else 'expired'
            Member.objects.filter(pk=pk).update(status=member.status)
            messages.success(request, f"{member.full_name} has been reactivated.")
        else:
            Member.objects.filter(pk=pk).update(status='suspended')
            messages.warning(request, f"{member.full_name} has been suspended.")
        return redirect('member_detail', pk=pk)


@login_required
def enroll_frame_api(request):
    """
    Multi-angle enrollment — process a single frame during registration.
    Accepts: POST JSON { "image": "<base64 JPEG>" }
    Returns: { "status": "ok", "embedding": [...] } or error dict.
    Does NOT save to DB — the browser collects all embeddings and submits with the form.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    try:
        import base64
        body = json.loads(request.body)
        image_b64 = body.get('image', '')
        if ',' in image_b64:
            image_b64 = image_b64.split(',', 1)[1]
        image_bytes = base64.b64decode(image_b64)
    except Exception:
        return JsonResponse({'status': 'error', 'message': 'Invalid image data'}, status=400)

    from face_service import extract_embedding_for_enrollment
    result = extract_embedding_for_enrollment(image_bytes)
    return JsonResponse(result)


@login_required
def member_export_csv(request):
    """
    Export members as CSV.
    GET params:
      ids=1,2,3   → export only those IDs (used by bulk "Export selected")
      (no ids)    → export all members (used by the header Export button)
    Optional: status filter still applied when no ids given.
    """
    import csv

    ids_param = request.GET.get('ids', '').strip()
    if ids_param:
        try:
            id_list = [int(i) for i in ids_param.split(',') if i.strip().isdigit()]
        except ValueError:
            id_list = []
        qs = Member.objects.filter(pk__in=id_list).select_related('membership_plan').order_by('full_name')
    else:
        qs = Member.objects.select_related('membership_plan').order_by('full_name')
        status_filter = request.GET.get('status', '').strip()
        if status_filter:
            qs = qs.filter(status=status_filter)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="members.csv"'
    writer = csv.writer(response)
    writer.writerow(['Full Name', 'Email', 'Phone', 'Plan', 'Join Date', 'Expiry Date', 'Status'])
    for m in qs:
        writer.writerow([
            m.full_name, m.email, m.phone,
            m.membership_plan.name,
            str(m.join_date), str(m.expiry_date),
            m.get_status_display(),
        ])
    return response


@login_required
def member_bulk_action(request):
    """
    POST  { action: 'mark_expired', ids: [1,2,3] }
          { action: 'undo_mark_expired', ids: [1,2,3] }
    Returns JSON { ok: true, updated: N, undo_data: {...} }
    Only admins can mark_expired / undo_mark_expired.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        body   = json.loads(request.body)
        action = body.get('action', '')
        ids    = [int(i) for i in body.get('ids', []) if str(i).isdigit()]
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid payload'}, status=400)

    if not ids:
        return JsonResponse({'error': 'No members selected'}, status=400)

    is_admin = hasattr(request.user, 'profile') and request.user.profile.role == 'admin'
    if not is_admin:
        return JsonResponse({'error': 'Admin only'}, status=403)

    from datetime import date, timedelta

    if action == 'mark_expired':
        # Snapshot original expiry_dates so the client can undo
        originals = {
            m.pk: str(m.expiry_date)
            for m in Member.objects.filter(pk__in=ids).exclude(status='suspended')
        }
        yesterday = date.today() - timedelta(days=1)
        updated = Member.objects.filter(
            pk__in=list(originals.keys())
        ).update(status='expired', expiry_date=yesterday)
        return JsonResponse({'ok': True, 'updated': updated, 'originals': originals})

    if action == 'undo_mark_expired':
        # originals = { "pk": "YYYY-MM-DD", ... }
        originals = body.get('originals', {})
        if not originals:
            return JsonResponse({'error': 'No undo data provided'}, status=400)
        from datetime import datetime
        count = 0
        for pk_str, expiry_str in originals.items():
            try:
                pk          = int(pk_str)
                expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d').date()
                new_status  = 'active' if expiry_date >= date.today() else 'expired'
                Member.objects.filter(pk=pk).update(
                    expiry_date=expiry_date, status=new_status
                )
                count += 1
            except (ValueError, TypeError):
                continue
        return JsonResponse({'ok': True, 'restored': count})

    return JsonResponse({'error': f'Unknown action: {action}'}, status=400)


@login_required
def member_search_api(request):
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    qs = Member.objects.select_related('membership_plan').order_by('full_name')
    if q:
        qs = (qs.filter(full_name__icontains=q) | qs.filter(email__icontains=q)).distinct()
    if status_filter:
        qs = qs.filter(status=status_filter)
    is_admin = hasattr(request.user, 'profile') and request.user.profile.role == 'admin'
    data = []
    for m in qs[:50]:
        data.append({
            'id': m.pk,
            'full_name': m.full_name,
            'email': m.email,
            'plan': m.membership_plan.name,
            'expiry_date': str(m.expiry_date),
            'status': m.status,
            'status_display': m.get_status_display(),
            'photo_url': m.photo.url if m.photo else None,
            'is_admin': is_admin,
        })
    return JsonResponse({'results': data, 'count': len(data)})
