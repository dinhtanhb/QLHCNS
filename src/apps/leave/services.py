"""Leave commands shared by the portal and mobile API; no transport concerns."""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models, transaction
from django.shortcuts import get_object_or_404

from apps.hrm.models import Employee
from apps.notification.services import notify, notify_with_email_draft
from apps.security.permissions import get_role_code, has_permission
from .models import LeaveApproval, LeaveRequest


def employee_for(user):
    employee = getattr(user, 'employee', None)
    return employee if employee and not employee.is_deleted else None


def leave_approvers_for(employee):
    ancestors, seen = [], {employee.pk}
    current = employee.manager
    while current and not current.is_deleted and current.pk not in seen:
        ancestors.append(current.pk)
        seen.add(current.pk)
        current = current.manager
    return Employee.objects.filter(pk__in=ancestors).filter(
        models.Q(user_account__role__role_code__in=['HR_MANAGER', 'DEPT_MANAGER', 'DIRECTOR'])
        | models.Q(user_account__is_superuser=True)
    ).distinct()


@transaction.atomic
def submit_leave(user, *, leave_type, from_date, to_date, reason=''):
    employee = employee_for(user)
    if not employee:
        raise PermissionDenied('Tài khoản chưa gắn hồ sơ nhân viên, không thể tạo đơn.')
    employee = Employee.objects.select_for_update().get(pk=employee.pk)
    leave = LeaveRequest(employee=employee, leave_type_id=leave_type,
        from_date=from_date, to_date=to_date, reason=reason, created_by=user)
    leave.full_clean()
    leave.save()
    for approver in leave_approvers_for(employee):
        notify(approver, 'leave', 'Có đơn nghỉ phép chờ duyệt',
            f'{employee.full_name} xin nghỉ {leave.from_date} - {leave.to_date}.',
            link='/portal/leave/approvals/', created_by=user)
    return leave


@transaction.atomic
def decide_leave(user, pk, decision):
    # Import lazily: the selector intentionally remains shared with Dashboard.
    from apps.portal.selectors import approvable_leave_requests
    if not has_permission(user, 'approve_leave'):
        raise PermissionDenied('Anh/chị không có quyền duyệt đơn nghỉ phép.')
    if decision not in ('Approved', 'Rejected'):
        raise ValidationError('Yêu cầu không hợp lệ.')
    approver = employee_for(user)
    if not approver:
        raise PermissionDenied('Tài khoản chưa gắn hồ sơ nhân viên, không thể duyệt.')
    leave = get_object_or_404(approvable_leave_requests(user).select_for_update(), pk=pk)
    if leave.employee_id == approver.pk and get_role_code(user) == 'DEPT_MANAGER':
        raise PermissionDenied('Anh/chị không thể tự duyệt đơn nghỉ phép của chính mình.')
    leave.status = decision
    leave.modified_by = user
    leave.save()
    LeaveApproval.objects.create(leave_request=leave, approver=approver,
        decision=decision, created_by=user)
    label = 'Đã duyệt' if decision == 'Approved' else 'Đã từ chối'
    notify_with_email_draft(leave.employee, 'leave', f'Đơn nghỉ phép {label.lower()}',
        f'Đơn nghỉ {leave.from_date} - {leave.to_date} của bạn {label.lower()}.',
        link='/portal/leave/', email_subject='IHRMS: Có cập nhật về đơn nghỉ phép của bạn',
        email_body='Anh/chị có cập nhật mới về yêu cầu nghỉ phép trong IHRMS. '
                   'Vui lòng đăng nhập cổng nhân viên để xem trạng thái và chi tiết.',
        created_by=user, idempotency_key=f'leave-decision:{leave.pk}:{decision}')
    return leave
