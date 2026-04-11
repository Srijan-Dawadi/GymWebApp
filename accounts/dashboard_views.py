from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.db.models import Sum
from django.utils import timezone


@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    template_name = 'accounts/dashboard.html'

    def get_context_data(self, **kwargs):
        from members.models import Member
        from attendance.models import Attendance
        from billing.models import Payment

        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()

        ctx['total_members'] = Member.objects.count()
        ctx['active_members'] = Member.objects.filter(status='active').count()
        ctx['today_attendance'] = Attendance.objects.filter(date=today).count()

        monthly_revenue = Payment.objects.filter(
            date_paid__year=today.year,
            date_paid__month=today.month
        ).aggregate(total=Sum('amount'))['total'] or 0
        ctx['monthly_revenue'] = monthly_revenue

        ctx['recent_checkins'] = Attendance.objects.filter(date=today).select_related('member').order_by('-check_in_time')[:10]
        ctx['overdue_members'] = Member.objects.filter(expiry_date__lt=today).count()

        return ctx
