from django.core.management.base import BaseCommand

from apps.hrm.services import apply_due_employee_changes


class Command(BaseCommand):
    help = "Apply employee transfers and promotions whose effective date has arrived."

    def handle(self, *args, **options):
        count = apply_due_employee_changes()
        self.stdout.write(self.style.SUCCESS(f"Applied {count} effective employee changes."))
