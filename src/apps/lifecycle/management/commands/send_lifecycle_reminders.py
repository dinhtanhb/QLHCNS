from django.core.management.base import BaseCommand

from apps.lifecycle.services import send_lifecycle_reminders


class Command(BaseCommand):
    help = "Tạo thông báo IHRMS nhắc các đầu việc onboarding/offboarding quá hạn."

    def handle(self, *args, **options):
        sent = send_lifecycle_reminders()
        self.stdout.write(self.style.SUCCESS(f"Đã tạo {sent} thông báo nhắc checklist."))
