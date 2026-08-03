from django.db import models
from django.utils import timezone

from members.models import Member


class Attendance(models.Model):
    METHOD_CHOICES = [('face', 'Face'), ('manual', 'Manual')]

    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name='attendances')
    check_in_time = models.DateTimeField()
    date = models.DateField()
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)

    class Meta:
        unique_together = ('member', 'date')
        ordering = ['-check_in_time']

    def save(self, *args, **kwargs):
        # Single source of truth for the timestamp: the local date is derived
        # from check_in_time so the two can never disagree.
        if not self.check_in_time:
            self.check_in_time = timezone.now()
        if not self.date:
            self.date = timezone.localdate(self.check_in_time)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.member.full_name} — {self.date} ({self.method})"
