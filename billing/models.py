from django.db import models
from members.models import Member


class Payment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('transfer', 'Transfer'),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    date_paid = models.DateField()
    period_start = models.DateField()
    period_end = models.DateField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.member.full_name} — ${self.amount} ({self.date_paid})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update member expiry_date and status after payment
        member = self.member
        member.expiry_date = self.period_end
        # Bypass the auto-recalculate in Member.save by directly updating
        from datetime import date
        member.status = 'active' if self.period_end > date.today() else 'expired'
        Member.objects.filter(pk=member.pk).update(
            expiry_date=self.period_end,
            status=member.status,
        )
