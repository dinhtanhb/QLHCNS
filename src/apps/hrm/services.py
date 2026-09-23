from django.db import transaction
from django.utils import timezone

from apps.hrm.models import Employee, EmployeePromotion, EmployeeTransfer


@transaction.atomic
def apply_due_employee_changes(as_of=None):
    """Apply effective-dated department and position changes due on or before a date."""
    as_of = as_of or timezone.localdate()
    departments = {}
    for employee_id, department_id in EmployeeTransfer.objects.filter(
        effective_date__lte=as_of,
    ).order_by("employee_id", "effective_date", "pk").values_list(
        "employee_id", "to_department_id",
    ):
        departments[employee_id] = department_id

    positions = {}
    for employee_id, position_id in EmployeePromotion.objects.filter(
        effective_date__lte=as_of,
    ).order_by("employee_id", "effective_date", "pk").values_list(
        "employee_id", "new_position_id",
    ):
        positions[employee_id] = position_id

    applied = 0
    for employee_id, department_id in departments.items():
        applied += Employee.objects.filter(pk=employee_id).exclude(
            department_id=department_id,
        ).update(department_id=department_id, modified_date=timezone.now())
    for employee_id, position_id in positions.items():
        applied += Employee.objects.filter(pk=employee_id).exclude(
            position_id=position_id,
        ).update(position_id=position_id, modified_date=timezone.now())
    return applied
