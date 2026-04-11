import json
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DetailView

from accounts.mixins import AdminRequiredMixin, StaffRequiredMixin
from .forms import MemberForm
from .models import Member, MembershipPlan


@method_decorator(login_required, name='dispatch')
class MemberListView(View):
    template_name = 'members/list.html'

    def get(self, request):
        qs = Member.objects.select_related('membership_plan').order_by('full_name')
        q = request.GET.get('q', '').strip()
        status_filter = request.GET.get('status', '').strip()

        if q:
            qs = qs.filter(full_name__icontains=q) | qs.filter(email__icontains=q)
            qs = qs.distinct()
        if status_filter:
            qs = qs.filter(status=status_filter)

        paginator = Paginator(qs, 20)
        page = paginator.get_page(request.GET.get('page'))
        return render(request, self.template_name, {'page_obj': page, 'q': q, 'status_filter': status_filter})


@method_decorator(login_required, name='dispatch')
class MemberDetailView(View):
    template_name = 'members/detail.html'

    def get(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        payments = member.payments.order_by('-date_paid')
        attendances = member.attendances.order_by('-date')[:30]
        return render(request, self.template_name, {
            'member': member,
            'payments': payments,
            'attendances': attendances,
        })


class MemberCreateView(StaffRequiredMixin, View):
    template_name = 'members/form.html'

    def get(self, request):
        form = MemberForm(initial={'join_date': date.today()})
        return render(request, self.template_name, {'form': form, 'title': 'Add Member'})

    def post(self, request):
        form = MemberForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save(commit=False)
            member.face_descriptor = form.cleaned_data['face_descriptor']
            member.save()
            messages.success(request, f"Member '{member.full_name}' registered successfully.")
            return redirect('member_detail', pk=member.pk)
        return render(request, self.template_name, {'form': form, 'title': 'Add Member'})


class MemberEditView(StaffRequiredMixin, View):
    template_name = 'members/form.html'

    def get(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        # Pre-populate face_descriptor as JSON string for the hidden field
        initial = {}
        if member.face_descriptor:
            initial['face_descriptor'] = json.dumps(member.face_descriptor)
        form = MemberForm(instance=member, initial=initial)
        return render(request, self.template_name, {'form': form, 'title': 'Edit Member', 'member': member})

    def post(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        form = MemberForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            m = form.save(commit=False)
            m.face_descriptor = form.cleaned_data['face_descriptor']
            m.save()
            messages.success(request, "Member updated successfully.")
            return redirect('member_detail', pk=m.pk)
        return render(request, self.template_name, {'form': form, 'title': 'Edit Member', 'member': member})


class MemberDeleteView(AdminRequiredMixin, View):
    template_name = 'members/confirm_delete.html'

    def get(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        return render(request, self.template_name, {'member': member})

    def post(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        name = member.full_name
        member.delete()
        messages.success(request, f"Member '{name}' deleted.")
        return redirect('member_list')


@login_required
def member_search_api(request):
    """Real-time member search — returns JSON for the live search UI."""
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    qs = Member.objects.select_related('membership_plan').order_by('full_name')
    if q:
        qs = (qs.filter(full_name__icontains=q) | qs.filter(email__icontains=q)).distinct()
    if status_filter:
        qs = qs.filter(status=status_filter)

    is_admin = hasattr(request.user, 'profile') and request.user.profile.role == 'admin'

    data = []
    for m in qs[:50]:  # cap at 50 for performance
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


@login_required
def descriptors_api(request):
    """Return all member face descriptors for browser-side matching.
    Restricted to admin role only — face biometric data is sensitive.
    """
    if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    members = Member.objects.exclude(face_descriptor__isnull=True).values('id', 'full_name', 'face_descriptor')
    data = [{'id': m['id'], 'full_name': m['full_name'], 'descriptor': m['face_descriptor']} for m in members]
    return JsonResponse(data, safe=False)
