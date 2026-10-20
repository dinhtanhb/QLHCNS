from django.db import transaction
from django.utils import timezone

from apps.hrm.models import Employee, EmployeePromotion, EmployeeTransfer


@transaction.atomic
def save_effective_change(instance, save, args, kwargs, destination):
    """Serialize scheduling with employee edits and consume each decision once."""
    Employee.objects.select_for_update().get(pk=instance.employee_id)
    fields = ('employee_id', 'effective_date', destination)
    previous = type(instance).all_objects.filter(pk=instance.pk).values(
        *fields, 'processed_at',
    ).first() if instance.pk else None
    if previous:
        update_fields = kwargs.get('update_fields')
        changed = any(
            getattr(instance, field) != previous[field]
            for field in fields
            if update_fields is None or field in update_fields or field.removesuffix('_id') in update_fields
        )
        instance.processed_at = None if changed else previous['processed_at']
        if update_fields is not None:
            kwargs['update_fields'] = set(update_fields) | {'processed_at'}
    result = save(*args, **kwargs)
    apply_due_employee_changes(employee_ids=[instance.employee_id])
    instance.processed_at = type(instance).all_objects.values_list('processed_at', flat=True).get(pk=instance.pk)
    return result


@transaction.atomic
def apply_due_employee_changes(as_of=None, *, employee_ids=None):
    """Consume due decisions once, preserving later direct profile corrections."""
    as_of = as_of or timezone.localdate()
    candidates = set()
    for model in (EmployeeTransfer, EmployeePromotion):
        pending = model.objects.filter(effective_date__lte=as_of, processed_at__isnull=True)
        if employee_ids is not None:
            pending = pending.filter(employee_id__in=employee_ids)
        candidates.update(pending.values_list('employee_id', flat=True))
    locked_ids = list(Employee.objects.select_for_update().filter(pk__in=candidates).order_by('pk').values_list('pk', flat=True))
    applied = 0
    now = timezone.now()
    for model, source, target in (
        (EmployeeTransfer, 'to_department_id', 'department_id'),
        (EmployeePromotion, 'new_position_id', 'position_id'),
    ):
        due = model.objects.filter(employee_id__in=locked_ids, effective_date__lte=as_of)
        latest = {}
        for event in due.order_by('employee_id', '-effective_date', '-pk'):
            latest.setdefault(event.employee_id, event)
        for employee_id, event in latest.items():
            if event.processed_at is None:
                value = getattr(event, source)
                applied += Employee.objects.filter(pk=employee_id).exclude(**{target: value}).update(
                    **{target: value}, modified_date=now,
                )
        due.filter(processed_at__isnull=True).update(processed_at=now)
    return applied
