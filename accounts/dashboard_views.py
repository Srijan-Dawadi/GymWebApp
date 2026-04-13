import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
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

        # Sync stale statuses so all counts are accurate
        Member.sync_expired_statuses()

        # ── Core stats ──────────────────────────────────────────────
        ctx['total_members']     = Member.objects.count()
        ctx['active_members']    = Member.objects.filter(status='active').count()
        ctx['expired_members']   = Member.objects.filter(status='expired').count()
        ctx['suspended_members'] = Member.objects.filter(status='suspended').count()
        ctx['today_attendance']  = Attendance.objects.filter(date=today).count()
        ctx['overdue_members']   = Member.objects.filter(expiry_date__lt=today).count()
        ctx['new_this_month']    = Member.objects.filter(join_date__gte=month_start).count()

        # Month-over-month new members comparison
        last_month_start = (month_start - timedelta(days=1)).replace(day=1)
        last_month_new = Member.objects.filter(
            join_date__gte=last_month_start, join_date__lt=month_start
        ).count()
        ctx['new_last_month'] = last_month_new
        ctx['new_members_trend'] = (
            '+' if ctx['new_this_month'] >= last_month_new else '-'
        )

        # Members expiring in next 7 days
        in_7_days = today + timedelta(days=7)
        ctx['expiring_soon'] = Member.objects.filter(
            status='active', expiry_date__gte=today, expiry_date__lte=in_7_days,
        ).order_by('expiry_date')

        # ── Revenue ─────────────────────────────────────────────────
        ctx['monthly_revenue'] = Payment.objects.filter(
            date_paid__gte=month_start
        ).aggregate(total=Sum('amount'))['total'] or 0

        # Last month revenue for comparison
        last_month_rev = Payment.objects.filter(
            date_paid__gte=last_month_start, date_paid__lt=month_start
        ).aggregate(total=Sum('amount'))['total'] or 0
        ctx['last_month_revenue'] = last_month_rev
        if last_month_rev > 0:
            ctx['revenue_change_pct'] = round(
                ((float(ctx['monthly_revenue']) - float(last_month_rev)) / float(last_month_rev)) * 100, 1
            )
        else:
            ctx['revenue_change_pct'] = None

        # ── Attendance chart — default 7 days (JS will reload dynamically) ──
        labels, counts = [], []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            labels.append(day.strftime('%a %d').lstrip('0') if i > 0 else 'Today')
            counts.append(Attendance.objects.filter(date=day).count())
        ctx['chart_labels'] = json.dumps(labels)
        ctx['chart_counts'] = json.dumps(counts)

        # ── Membership donut ─────────────────────────────────────────
        ctx['donut_data'] = json.dumps([
            ctx['active_members'],
            ctx['expired_members'],
            ctx['suspended_members'],
        ])

        # ── Recent check-ins ─────────────────────────────────────────
        ctx['recent_checkins'] = (
            Attendance.objects.filter(date=today)
            .select_related('member').order_by('-check_in_time')[:8]
        )

        # ── Recent payments ──────────────────────────────────────────
        ctx['recent_payments'] = (
            Payment.objects.select_related('member')
            .order_by('-date_paid', '-id')[:5]
        )

        return ctx


@login_required
def chart_data_api(request):
    """
    Returns attendance + revenue data for a given range.
    Query params: range = 7 | 30 | 90
    """
    from attendance.models import Attendance
    from billing.models import Payment

    try:
        days = int(request.GET.get('range', 7))
        if days not in (7, 30, 90):
            days = 7
    except ValueError:
        days = 7

    today = timezone.localdate()
    att_labels, att_counts = [], []
    rev_labels, rev_amounts = [], []

    if days <= 30:
        # Daily granularity
        for i in range(days - 1, -1, -1):
            day = today - timedelta(days=i)
            att_labels.append(day.strftime('%d %b'))
            att_counts.append(Attendance.objects.filter(date=day).count())
            rev = Payment.objects.filter(date_paid=day).aggregate(t=Sum('amount'))['t'] or 0
            rev_labels.append(day.strftime('%d %b'))
            rev_amounts.append(float(rev))
    else:
        # Weekly granularity for 90 days
        for i in range(12, -1, -1):
            week_end = today - timedelta(weeks=i)
            week_start = week_end - timedelta(days=6)
            label = week_start.strftime('%d %b')
            att_labels.append(label)
            att_counts.append(
                Attendance.objects.filter(date__gte=week_start, date__lte=week_end).count()
            )
            rev = Payment.objects.filter(
                date_paid__gte=week_start, date_paid__lte=week_end
            ).aggregate(t=Sum('amount'))['t'] or 0
            rev_labels.append(label)
            rev_amounts.append(float(rev))

    return JsonResponse({
        'attendance': {'labels': att_labels, 'data': att_counts},
        'revenue':    {'labels': rev_labels, 'data': rev_amounts},
    })
