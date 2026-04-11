from django.db import models
from members.models import Member


class Attendance(models.Model):
    METHOD_CHOICES = [('face', 'Face'), ('manual', 'Manual')]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='attendances')
    check_in_time = models.TimeField(auto_now_add=True)
    date = models.DateField(auto_now_add=True)
    method = models.CharField(max_length=10, choices=METHOD_CHOICES)

    class Meta:
        unique_together = ('member', 'date')
        ordering = ['-date', '-check_in_time']

    def __str__(self):
        return f"{self.member.full_name} — {self.date} ({self.method})"
