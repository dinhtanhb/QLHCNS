"""Explicit object scopes; staff status never grants business data access."""
from django.db.models import Q
from apps.security.permissions import (
    DEPT_MANAGER,
    DIRECTOR,
    HR_MANAGER,
    HR_OFFICER,
    SUPER_ADMIN,
    get_role_code,
    has_permission,
)

# Vai trò xem được công văn ở MỌI độ mật trong cổng. Tách thành hằng số vì
# `apps/assistant/m365_search.py` phải dựng đúng cùng một phạm vi cho nguồn
# SharePoint: Graph chạy app-only và không biết gì về `security_level` của từng
# tệp, nên ai chưa được xem bản Mật ở cổng thì cũng không được nghe tên tệp đó.
# Ở phía assistant, tập này còn được GIAO với hai quyền sổ văn thư - xem
# `SHARED_LIBRARY_PERMISSIONS` - vì hai thư mục công văn cũng chứa tệp đính kèm
# của `IncomingDocument`/`OutgoingDocument`.
FULL_DISPATCH_SECURITY_ROLES = (SUPER_ADMIN, DIRECTOR, HR_MANAGER, HR_OFFICER)


def managed_departments_for(user, *, global_roles=(), scoped_roles=(DEPT_MANAGER,)):
    """Departments a role may target in department-scoped write workflows."""
    from apps.organization.models import Department

    qs = Department.objects.all()
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return qs.none()
    role = get_role_code(user)
    if getattr(user, "is_superuser", False) or role in global_roles:
        return qs
    if role not in scoped_roles:
        return qs.none()
    employee = getattr(user, "employee", None)
    if not employee or employee.is_deleted:
        return qs.none()
    return employee.managed_departments.all()


def employees_for_department_scope(user, *, global_roles=(), scoped_roles=(DEPT_MANAGER,)):
    """Employees selectable by a global role or within managed departments."""
    from apps.hrm.models import Employee

    qs = Employee.objects.all()
    departments = managed_departments_for(
        user, global_roles=global_roles, scoped_roles=scoped_roles,
    )
    if getattr(user, "is_superuser", False) or get_role_code(user) in global_roles:
        return qs
    return qs.filter(department__in=departments)


def employee_and_subordinate_ids(user):
    """Employee IDs visible through the reporting line, including all depths."""
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return set()
    employee = getattr(user, "employee", None)
    if not employee or employee.is_deleted:
        return set()
    from apps.hrm.models import Employee
    children_by_manager = {}
    for pk, manager_id in Employee.objects.filter(is_deleted=False).values_list("pk", "manager_id"):
        children_by_manager.setdefault(manager_id, set()).add(pk)
    visible = {employee.pk}
    frontier = {employee.pk}
    while frontier:
        children = set().union(*(children_by_manager.get(pk, set()) for pk in frontier)) - visible
        visible.update(children)
        frontier = children
    return visible


def visible_leave_requests_for(user, queryset=None):
    from apps.leave.models import LeaveRequest
    qs = queryset if queryset is not None else LeaveRequest.objects.all()
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return qs.none()
    return qs.filter(employee_id__in=employee_and_subordinate_ids(user))


def visible_personnel_decisions_for(user, queryset=None):
    from apps.document.models import PersonnelDecision
    qs = queryset if queryset is not None else PersonnelDecision.objects.all()
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return qs.none()
    qs = qs.filter(employee__is_deleted=False)
    if has_permission(user, "view_all_personnel_decisions"):
        return qs
    return qs.filter(employee_id__in=employee_and_subordinate_ids(user))


def visible_dispatches_for(user, queryset=None):
    from apps.document.models import OfficialDispatch
    qs = queryset if queryset is not None else OfficialDispatch.objects.all()
    if not user.is_authenticated or not user.is_active:
        return qs.none()
    if user.is_superuser:
        return qs
    employee = getattr(user, 'employee', None)
    role = get_role_code(user)
    shared = qs.filter(dispatch_type__in=("Incoming", "Outgoing"))
    qs = qs.exclude(dispatch_type__in=("Incoming", "Outgoing"))
    if role in ('PROJECT_MANAGER', 'PROJECT_COORDINATOR'):
        return shared
    elif not has_permission(user, 'access_outgoing_document'):
        if not employee:
            return shared
        scope = Q(assigned_to=employee)
        if employee.department_id:
            scope |= Q(department_id=employee.department_id)
        qs = qs.filter(scope)
    if role not in FULL_DISPATCH_SECURITY_ROLES:
        private_scope = Q(created_by=user)
        if employee:
            private_scope |= Q(assigned_to=employee) | Q(signer=employee)
        qs = qs.filter(Q(security_level='Normal') | private_scope)
    return shared | qs


def can_read_file(user, obj):
    if not user.is_authenticated or not user.is_active or obj.is_deleted:
        return False
    employee = getattr(user, 'employee', None)
    if employee and employee.is_deleted:
        return False
    if user.is_superuser and obj._meta.label_lower != 'leave.leaverequest':
        return True
    role = get_role_code(user)
    label = obj._meta.label_lower
    if label == 'document.personneldecision':
        return visible_personnel_decisions_for(user).filter(pk=obj.pk).exists()
    if label == 'document.document':
        return obj.status == 'Approved' or obj.created_by_id == user.pk or has_permission(user, 'approve_document') or has_permission(user, 'manage_hr')
    if label == 'document.officialdispatch':
        return visible_dispatches_for(user).filter(pk=obj.pk).exists()
    if label == 'office.incomingdocument':
        return True
    if label == 'office.outgoingdocument':
        return True
    if label == 'recruitment.candidate':
        return has_permission(user, 'manage_hr') or has_permission(user, 'view_candidate')
    if label in ('leave.leaverequest', 'hrm.employeeprofilechangerequest'):
        if obj.employee.is_deleted:
            return False
        if employee and obj.employee_id == employee.pk:
            return True
        if label == 'hrm.employeeprofilechangerequest':
            return has_permission(user, 'approve_profile_change_request')
        return visible_leave_requests_for(user).filter(pk=obj.pk).exists()
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
