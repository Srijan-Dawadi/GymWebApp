from datetime import date

from django.db import models

from members.models import Member


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('transfer', 'Transfer'),
    ]

    APPROVAL_STATUS = [
        ('pending',  'Pending Review'),
        ('approved', 'Approved'),
        ('flagged',  'Flagged'),
    ]

    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name='payments')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    date_paid = models.DateField()
    period_start = models.DateField()
    period_end = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    notes = models.TextField(blank=True)

    # ── Approval workflow ──────────────────────────────────────
    approval_status = models.CharField(
        max_length=10, choices=APPROVAL_STATUS, default='pending',
        db_index=True,
    )
    reviewed_by = models.ForeignKey(
        'auth.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='reviewed_payments',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    flag_reason = models.TextField(blank=True)

    def __str__(self):
        return f"{self.member.full_name} — ${self.amount} ({self.date_paid}) [{self.approval_status}]"

    def apply_to_membership(self):
        """Extend the member's expiry to this payment's period_end.

        Intentionally idempotent and only ever extends forward: if the member's
        current expiry is already later than period_end (e.g. an earlier renewal
        or a backdated payment), the current expiry is preserved.
        """
        member = Member.objects.get(pk=self.member_id)
        new_expiry = max(member.expiry_date, self.period_end)
        Member.objects.filter(pk=member.pk).update(
            expiry_date=new_expiry,
            status='active' if new_expiry > date.today() else 'expired',
        )
