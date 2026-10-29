from django.db import transaction
from django.utils import timezone

from apps.hrm.models import Employee, EmployeePromotion, EmployeeTransfer
from apps.hrm.models import EmployeeProfileChangeRequest
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from apps.security.permissions import has_permission
from apps.notification.services import notify


@transaction.atomic
def decide_profile_change(actor, pk, decision, note=''):
    """One decision command shared by the portal and the mobile transport."""
    if not has_permission(actor, 'approve_profile_change_request'):
        raise PermissionDenied('Không có quyền duyệt cập nhật hồ sơ.')
    status = {'approve': 'Approved', 'reject': 'Rejected', 'more_info': 'NeedsMoreInfo'}.get(decision)
    if not status:
        raise ValidationError('Quyết định không hợp lệ.')
    # Match submission's lock order: employee first, request second.
    target = get_object_or_404(EmployeeProfileChangeRequest.objects.only('employee_id'), pk=pk, status='Pending')
    employee = Employee.objects.select_for_update().get(pk=target.employee_id)
    item = get_object_or_404(EmployeeProfileChangeRequest.objects.select_for_update(), pk=pk, employee_id=employee.pk, status='Pending')
    if str(getattr(employee, item.field_name) or '') != item.submitted_snapshot:
        raise ValidationError('Giá trị hồ sơ đã thay đổi sau khi gửi. Không thể duyệt yêu cầu cũ; vui lòng yêu cầu nhân viên gửi lại.')
    if status == 'Approved':
        setattr(employee, item.field_name, item.new_value)
        employee.modified_by = actor
        employee.save(update_fields=[item.field_name, 'modified_by', 'modified_date'])
    item.status = status
    item.decided_by = actor
    item.decided_at = timezone.now()
    item.decision_note = note.strip()[:500]
    item.modified_by = actor
    item.save(update_fields=['status', 'decided_by', 'decided_at', 'decision_note', 'modified_by', 'modified_date'])
    labels = {'Approved': 'đã được duyệt', 'Rejected': 'bị từ chối', 'NeedsMoreInfo': 'cần bổ sung thông tin'}
    notify(employee, 'profile-change', 'Yêu cầu cập nhật hồ sơ đã được xử lý',
           f'Yêu cầu thay đổi hồ sơ của bạn {labels[status]}. Vui lòng xem chi tiết trong IHRMS.',
           link='/portal/profile/requests/', created_by=actor)
    return item


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
    if not candidates:
        return 0
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
