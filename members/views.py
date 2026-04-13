import json
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
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
        member = get_object_or_404(Member, pk=pk)
        payments = member.payments.order_by('-date_paid')
        attendances = member.attendances.order_by('-date')[:30]
        return render(request, self.template_name, {
            'member': member,
            'payments': payments,
            'attendances': attendances,
        })


def _extract_and_save_embedding(member):
    """Read the member's saved photo and extract InsightFace embedding."""
    from face_service import extract_embedding
    try:
        with open(member.photo.path, 'rb') as f:
            image_bytes = f.read()
        embedding = extract_embedding(image_bytes)
        if embedding:
            member.face_descriptor = embedding
            Member.objects.filter(pk=member.pk).update(face_descriptor=embedding)
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
            # Extract face embedding from uploaded photo
            if member.photo:
                ok = _extract_and_save_embedding(member)
                if not ok:
                    messages.warning(request, f"Member '{member.full_name}' saved but no face detected in the photo. Please re-upload a clear face photo.")
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
            # Re-extract embedding only if a new photo was uploaded
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
        member.delete()
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
