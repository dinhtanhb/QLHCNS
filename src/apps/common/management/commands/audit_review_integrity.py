"""Read-only counts of data requiring correction before review migrations."""
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Sum, Q, F
from apps.office.models import SupplyItem, SupplyRequestItem
from apps.attendance.models import TimesheetEntry
from apps.asset.models import AssetAllocation


class Command(BaseCommand):
    help = "Read-only integrity counts; no personal fields, writes, or automatic repair."

    def handle(self, *args, **options):
        checks = {
            "negative_stock_including_deleted": SupplyItem.all_objects.filter(quantity_in_stock__lt=0).count(),
            "invalid_supply_lines_including_deleted": SupplyRequestItem.all_objects.filter(
                Q(quantity_requested__lt=1) | Q(quantity_issued__lt=0) | Q(quantity_issued__gt=F("quantity_requested"))).count(),
            "invalid_timesheet_hours": TimesheetEntry.objects.filter(Q(hours__lt=0) | Q(hours__gt=24)).count(),
            "days_over_24_hours": TimesheetEntry.objects.values("employee_id","work_date").annotate(total=Sum("hours")).filter(total__gt=24).count(),
            "assets_with_multiple_open_allocations": AssetAllocation.objects.filter(return_date__isnull=True).values("asset_id").annotate(total=Count("pk")).filter(total__gt=1).count(),
        }
        for name, count in checks.items():
            self.stdout.write(f"{name}: {count}")
        if any(checks.values()):
            raise CommandError("Existing invalid data: obtain HR/Finance/IT correction approval before migration/release. No data changed.")
