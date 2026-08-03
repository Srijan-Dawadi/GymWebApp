from django.db import models
from datetime import date, timedelta


class MembershipPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_days = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.name} ({self.duration_days} days)"


class Member(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ]

    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    address = models.TextField(blank=True, default='')
    photo = models.ImageField(upload_to='member_photos/', blank=True, null=True)
    face_descriptor = models.JSONField(null=True, blank=True)
    join_date = models.DateField()
    membership_plan = models.ForeignKey(MembershipPlan, on_delete=models.PROTECT, related_name='members')
    expiry_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    is_flagged = models.BooleanField(
        default=False,
        help_text='Flagged members are blocked from face recognition attendance.',
    )

    def __str__(self):
        return self.full_name

    def compute_expiry_date(self):
        """Return expiry_date based on join_date and plan duration."""
        return self.join_date + timedelta(days=self.membership_plan.duration_days)

    def compute_status(self):
        """Return 'active' if expiry_date is in the future, else 'expired'."""
        if self.status == 'suspended':
            return 'suspended'
        return 'active' if self.expiry_date > date.today() else 'expired'

    @classmethod
    def sync_expired_statuses(cls):
        """Bulk-update all non-suspended members whose status is stale.
        Call this from a management command or scheduled task.
        """
        today = date.today()
        cls.objects.filter(status='active', expiry_date__lt=today).update(status='expired')
        cls.objects.filter(status='expired', expiry_date__gte=today).update(status='active')

    def save(self, *args, **kwargs):
        # Derive expiry_date from join_date + plan duration ONLY when the
        # member is first created and no explicit expiry was supplied.
        # On subsequent saves the stored expiry_date is the source of truth —
        # it is extended by approved payments and must never be recomputed
        # (that would clobber renewals whenever an unrelated field is edited).
        if self._state.adding:
            if self.membership_plan_id and self.join_date and not self.expiry_date:
                self.expiry_date = self.compute_expiry_date()
        # Auto-calculate status (guard against expiry_date being unset on brand-new unsaved instances)
        if self.status != 'suspended' and self.expiry_date:
            self.status = 'active' if self.expiry_date > date.today() else 'expired'
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Keep the in-memory descriptor matrix in sync when a member is removed.
        try:
            from face_service import invalidate_descriptor_cache
            invalidate_descriptor_cache()
        except ImportError:
            pass
        super().delete(*args, **kwargs)
