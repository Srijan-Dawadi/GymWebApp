import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView


@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    template_name = 'accounts/dashboard.html'

    def get_context_data(self, **kwargs):
        from members.models import Member
        from attendance.models import Attendance
        from billing.models import Payment

        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        month_start = today.replace(day=1)

        # Sync stale statuses first so all counts are accurate
        Member.sync_expired_statuses()

        # ── Core stats ──────────────────────────────────────────────
        ctx['total_members']    = Member.objects.count()
        ctx['active_members']   = Member.objects.filter(status='active').count()
        ctx['expired_members']  = Member.objects.filter(status='expired').count()
        ctx['suspended_members'] = Member.objects.filter(status='suspended').count()
        ctx['today_attendance'] = Attendance.objects.filter(date=today).count()
        ctx['overdue_members']  = Member.objects.filter(expiry_date__lt=today).count()

        # New members joined this month
        ctx['new_this_month'] = Member.objects.filter(join_date__gte=month_start).count()

        # Members expiring in next 7 days (active only)
        in_7_days = today + timedelta(days=7)
        ctx['expiring_soon'] = Member.objects.filter(
            status='active',
            expiry_date__gte=today,
            expiry_date__lte=in_7_days,
        ).order_by('expiry_date')

        # ── Revenue ─────────────────────────────────────────────────
        ctx['monthly_revenue'] = Payment.objects.filter(
            date_paid__gte=month_start
        ).aggregate(total=Sum('amount'))['total'] or 0

        # ── Attendance chart — last 7 days ───────────────────────────
        labels, counts = [], []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            count = Attendance.objects.filter(date=day).count()
            labels.append(day.strftime('%a'))   # Mon, Tue …
            counts.append(count)
        ctx['chart_labels'] = json.dumps(labels)
        ctx['chart_counts'] = json.dumps(counts)

        # ── Membership breakdown for donut chart ────────────────────
        ctx['donut_data'] = json.dumps([
            ctx['active_members'],
            ctx['expired_members'],
            ctx['suspended_members'],
        ])

        # ── Recent check-ins (today) ─────────────────────────────────
        ctx['recent_checkins'] = (
            Attendance.objects
            .filter(date=today)
            .select_related('member')
            .order_by('-check_in_time')[:8]
        )

        # ── Recent payments ──────────────────────────────────────────
        ctx['recent_payments'] = (
            Payment.objects
            .select_related('member')
            .order_by('-date_paid', '-id')[:5]
        )

        return ctx
