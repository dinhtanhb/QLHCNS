"""Explicit object scopes; staff status never grants business data access."""
from django.db.models import Q
from apps.security.permissions import get_role_code, has_permission


def visible_dispatches_for(user, queryset=None):
    from apps.document.models import OfficialDispatch
    qs = queryset if queryset is not None else OfficialDispatch.objects.all()
    if not user.is_authenticated or not user.is_active:
        return qs.none()
    if user.is_superuser:
        return qs
    employee = getattr(user, 'employee', None)
    role = get_role_code(user)
    if role in ('PROJECT_MANAGER', 'PROJECT_COORDINATOR'):
        qs = qs.filter(dispatch_type='Outgoing')
    elif not has_permission(user, 'access_outgoing_document'):
        if not employee:
            return qs.none()
        scope = Q(assigned_to=employee)
        if employee.department_id:
            scope |= Q(department_id=employee.department_id)
        qs = qs.filter(scope)
    if role not in ('SUPER_ADMIN', 'DIRECTOR', 'HR_MANAGER', 'HR_OFFICER'):
        private_scope = Q(created_by=user)
        if employee:
            private_scope |= Q(assigned_to=employee) | Q(signer=employee)
        qs = qs.filter(Q(security_level='Normal') | private_scope)
    return qs


def can_read_file(user, obj):
    if not user.is_authenticated or not user.is_active or obj.is_deleted:
        return False
    employee = getattr(user, 'employee', None)
    if employee and employee.is_deleted:
        return False
    if user.is_superuser:
        return True
    role = get_role_code(user)
    label = obj._meta.label_lower
    if label == 'document.document':
        return obj.status == 'Approved' or obj.created_by_id == user.pk or has_permission(user, 'approve_document') or has_permission(user, 'manage_hr')
    if label == 'document.officialdispatch':
        return visible_dispatches_for(user).filter(pk=obj.pk).exists()
    if label == 'office.incomingdocument':
        return has_permission(user, 'manage_office') or bool(employee and employee.pk in (obj.handler_id, obj.received_by_id))
    if label == 'office.outgoingdocument':
        return has_permission(user, 'access_outgoing_document')
    if label == 'recruitment.candidate':
        return has_permission(user, 'manage_hr')
    if label in ('leave.leaverequest', 'hrm.employeeprofilechangerequest'):
        if obj.employee.is_deleted:
            return False
        if employee and obj.employee_id == employee.pk:
            return True
        if label == 'hrm.employeeprofilechangerequest':
            return has_permission(user, 'approve_profile_change_request')
        if has_permission(user, 'manage_hr') or has_permission(user, 'approve_leave_all_departments'):
            return True
        return bool(employee and role == 'DEPT_MANAGER' and employee.managed_departments.filter(pk=obj.employee.department_id).exists())
    if label == 'm365.companymedia':
        return True  # Published internal company media, after authentication.
    if label in ('activity.activityproposal', 'task.task'):
        from apps.activity.permissions import can_view_activity
        if obj.activity_id and obj.activity.is_deleted:
            return False
        if label == 'activity.activityproposal':
            return can_view_activity(user, obj.activity)
        own = bool(employee and employee.pk in (obj.assigned_to_employee_id, obj.assigned_by_employee_id))
        if obj.activity_id:
            return own or can_view_activity(user, obj.activity)
        return own or role == 'HR_MANAGER' or bool(employee and role == 'DEPT_MANAGER' and employee.managed_departments.filter(pk=obj.assigned_to_employee.department_id).exists())
    return False
