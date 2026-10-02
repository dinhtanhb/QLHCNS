from django.core.management.base import BaseCommand

from apps.activity.services import send_activity_report_reminders


class Command(BaseCommand):
    help = "Tạo thông báo IHRMS nhắc hạn Task báo cáo hoạt động dự án."

    def handle(self, *args, **options):
        sent = send_activity_report_reminders()
        self.stdout.write(self.style.SUCCESS(f"Đã tạo {sent} thông báo nhắc việc."))
