from datetime import date, timedelta

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import ProtectedError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from accounts.mixins import AdminRequiredMixin, StaffRequiredMixin
from members.models import Member, MembershipPlan
from .forms import MembershipPlanForm, PaymentForm
from .models import Payment


class PlanListView(AdminRequiredMixin, View):
    template_name = 'billing/plans.html'

    def get(self, request):
        plans = MembershipPlan.objects.all()
        form = MembershipPlanForm()
        return render(request, self.template_name, {'plans': plans, 'form': form})

    def post(self, request):
        form = MembershipPlanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Membership plan created.")
            return redirect('plan_list')
        plans = MembershipPlan.objects.all()
        return render(request, self.template_name, {'plans': plans, 'form': form})


class PlanEditView(AdminRequiredMixin, View):
    template_name = 'billing/plan_form.html'

    def get(self, request, pk):
        plan = get_object_or_404(MembershipPlan, pk=pk)
        form = MembershipPlanForm(instance=plan)
        return render(request, self.template_name, {'form': form, 'plan': plan})

    def post(self, request, pk):
        plan = get_object_or_404(MembershipPlan, pk=pk)
        form = MembershipPlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, "Plan updated.")
            return redirect('plan_list')
        return render(request, self.template_name, {'form': form, 'plan': plan})


class PlanDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        plan = get_object_or_404(MembershipPlan, pk=pk)
        try:
            plan.delete()
            messages.success(request, "Plan deleted.")
        except ProtectedError:
            messages.error(request, "Cannot delete this plan — it has active members assigned to it.")
        return redirect('plan_list')


class PaymentListView(StaffRequiredMixin, View):
    template_name = 'billing/payments.html'

    def get(self, request):
        qs = Payment.objects.select_related('member').order_by('-date_paid')
        member_id = request.GET.get('member')
        start = request.GET.get('start')
        end = request.GET.get('end')

        if member_id:
            qs = qs.filter(member_id=member_id)
        if start:
            qs = qs.filter(date_paid__gte=start)
        if end:
            qs = qs.filter(date_paid__lte=end)

        paginator = Paginator(qs, 25)
        page = paginator.get_page(request.GET.get('page'))

        members = Member.objects.order_by('full_name')
        return render(request, self.template_name, {
            'page_obj': page,
            'members': members,
            'selected_member': member_id,
            'start': start,
            'end': end,
        })


class PaymentCreateView(StaffRequiredMixin, View):
    template_name = 'billing/payment_form.html'

    def get(self, request):
        initial = {}
        member_id = request.GET.get('member')
        if member_id:
            initial['member'] = member_id
        form = PaymentForm(initial=initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save()
            messages.success(request, f"Payment of Rs. {payment.amount} recorded for {payment.member.full_name}.")
            return redirect('payment_list')
        return render(request, self.template_name, {'form': form})


class MemberPlanInfoView(StaffRequiredMixin, View):
    """Returns a member's plan details as JSON for auto-filling the payment form."""

    def get(self, request, pk):
        member = get_object_or_404(Member, pk=pk)
        plan = member.membership_plan
        today = date.today()

        # Period start = today
        # Period end = today + plan duration
        period_end = today + timedelta(days=plan.duration_days)

        return JsonResponse({
            'plan_name':     plan.name,
            'plan_price':    str(plan.price),
            'duration_days': plan.duration_days,
            'period_start':  today.strftime('%Y-%m-%d'),
            'period_end':    period_end.strftime('%Y-%m-%d'),
            'date_paid':     today.strftime('%Y-%m-%d'),
        })


# ── Payment Approval (admin only) ─────────────────────────────────────────────

class PaymentApprovalView(AdminRequiredMixin, View):
    """
    Shows all pending payments for admin review.
    Admins can approve or flag each payment.
    Flagging a payment also sets member.is_flagged = True,
    blocking them from face recognition attendance.
    """
    template_name = 'billing/payment_approval.html'

    def get(self, request):
        pending = (
            Payment.objects
            .filter(approval_status='pending')
            .select_related('member', 'member__membership_plan')
            .order_by('date_paid')
        )
        flagged = (
            Payment.objects
            .filter(approval_status='flagged')
            .select_related('member', 'reviewed_by')
            .order_by('-reviewed_at')[:20]
        )
        pending_count = pending.count()
        return render(request, self.template_name, {
            'pending': pending,
            'flagged': flagged,
            'pending_count': pending_count,
        })


class PaymentApproveView(AdminRequiredMixin, View):
    """Approve a single payment."""

    def post(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk)
        if payment.approval_status != 'pending':
            messages.warning(request, "This payment has already been reviewed.")
            return redirect('payment_approval')

        payment.approval_status = 'approved'
        payment.reviewed_by = request.user
        payment.reviewed_at = timezone.now()
        payment.save(update_fields=['approval_status', 'reviewed_by', 'reviewed_at'])

        messages.success(
            request,
            f"Payment of ₹{payment.amount} for {payment.member.full_name} approved."
        )
        return redirect('payment_approval')


class PaymentFlagView(AdminRequiredMixin, View):
    """
    Flag a payment as suspicious.
    Also sets member.is_flagged = True so face attendance is blocked.
    """

    def post(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk)
        reason = request.POST.get('reason', '').strip()

        if payment.approval_status != 'pending':
            messages.warning(request, "This payment has already been reviewed.")
            return redirect('payment_approval')

        payment.approval_status = 'flagged'
        payment.reviewed_by = request.user
        payment.reviewed_at = timezone.now()
        payment.flag_reason = reason
        payment.save(update_fields=[
            'approval_status', 'reviewed_by', 'reviewed_at', 'flag_reason'
        ])

        # Block member from face attendance
        Member.objects.filter(pk=payment.member_id).update(is_flagged=True)

        messages.warning(
            request,
            f"{payment.member.full_name} has been flagged. "
            f"Face attendance is now blocked for this member."
        )
        return redirect('payment_approval')


class PaymentUnflagView(AdminRequiredMixin, View):
    """Remove flag from a member (admin clears the flag)."""

    def post(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk)
        payment.approval_status = 'approved'
        payment.flag_reason = ''
        payment.reviewed_by = request.user
        payment.reviewed_at = timezone.now()
        payment.save(update_fields=[
            'approval_status', 'flag_reason', 'reviewed_by', 'reviewed_at'
        ])

        # Only clear flag if member has no other flagged payments
        other_flagged = Payment.objects.filter(
            member=payment.member, approval_status='flagged'
        ).exclude(pk=pk).exists()
        if not other_flagged:
            Member.objects.filter(pk=payment.member_id).update(is_flagged=False)
            messages.success(
                request,
                f"Flag removed from {payment.member.full_name}. Face attendance restored."
            )
        else:
            messages.info(
                request,
                f"Payment approved, but {payment.member.full_name} still has other flagged payments."
            )
        return redirect('payment_approval')


class PaymentApproveAllView(AdminRequiredMixin, View):
    """Bulk-approve all currently pending payments."""

    def post(self, request):
        now = timezone.now()
        count = Payment.objects.filter(approval_status='pending').update(
            approval_status='approved',
            reviewed_by=request.user,
            reviewed_at=now,
        )
        messages.success(request, f"{count} payment{'s' if count != 1 else ''} approved.")
        return redirect('payment_approval')
