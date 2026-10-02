from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.lifecycle.models import EmployeeLifecycleCase, LifecycleChecklistItem
from apps.notification.services import notify


@transaction.atomic
def open_onboarding_case(employee, template, created_by=None):
    key = f"onboarding:{employee.employee_code}"
    return _open_case(employee, template, "Onboarding", employee.join_date, key, created_by)


@transaction.atomic
def open_offboarding_case(employee, template, leave_date, created_by=None):
    key = f"offboarding:{employee.employee_code}:{leave_date.isoformat()}"
    return _open_case(employee, template, "Offboarding", leave_date, key, created_by)


def _open_case(employee, template, case_type, effective_date, key, created_by):
    if template.template_type != case_type or not template.is_active:
        raise ValueError("Mẫu checklist không hoạt động hoặc không khớp loại hồ sơ.")
    case, created = EmployeeLifecycleCase.objects.get_or_create(
        triggering_event_ref=key,
        defaults={
            "employee": employee, "template": template, "case_type": case_type,
            "effective_date": effective_date, "created_by": created_by,
        },
    )
    if created:
        for template_item in template.items.order_by("sequence", "id"):
            LifecycleChecklistItem.objects.create(
                case=case,
                template_item=template_item,
                item_name=template_item.item_name,
                responsible_role_code=template_item.responsible_role_code,
                requires_asset_return=template_item.requires_asset_return,
                due_date=effective_date + timedelta(days=template_item.due_offset_days),
                created_by=created_by,
            )
    return case, created


@transaction.atomic
def send_lifecycle_reminders(today=None):
    today = today or timezone.localdate()
    overdue = LifecycleChecklistItem.objects.select_for_update().filter(
        case__status="Open", status="Pending", due_date__lt=today,
    ).select_related("case__employee", "assigned_to_user__employee")
    count = 0
    for item in overdue:
        if not item.assigned_to_user_id or item.last_reminded_on == today:
            continue
        employee = getattr(item.assigned_to_user, "employee", None)
        if not employee:
            continue
        notify(
            employee=employee,
            notification_type="LifecycleOverdue",
            title="Checklist nhân sự quá hạn",
            message=f"Đầu việc “{item.item_name}” cho hồ sơ {item.case.employee.employee_code} đã quá hạn.",
            link=f"/portal/lifecycle/cases/{item.case_id}/",
        )
        item.last_reminded_on = today
        item.save(update_fields=["last_reminded_on", "modified_date"])
        count += 1
    return count
