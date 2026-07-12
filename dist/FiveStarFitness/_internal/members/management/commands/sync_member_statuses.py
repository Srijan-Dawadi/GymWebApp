from django.core.management.base import BaseCommand
from members.models import Member


class Command(BaseCommand):
    help = "Bulk-sync member active/expired statuses based on expiry_date. Run daily via cron or scheduler."

    def handle(self, *args, **options):
        Member.sync_expired_statuses()
        self.stdout.write(self.style.SUCCESS("Member statuses synced successfully."))
