"""
Injects pending_payments_count into every template context for admin users.
Used to show the badge on the Payment Approvals sidebar link.
"""


def pending_payments(request):
    if not request.user.is_authenticated:
        return {}
    try:
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'admin':
            return {}
    except Exception:
        return {}
    try:
        from billing.models import Payment
        count = Payment.objects.filter(approval_status='pending').count()
        return {'pending_payments_count': count}
    except Exception:
        return {}
