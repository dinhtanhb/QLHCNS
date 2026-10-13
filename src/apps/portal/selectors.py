"""Read selectors shared by approval views and the homepage."""
from apps.leave.models import LeaveRequest
from apps.security.permissions import get_role_code, has_permission


def approvable_leave_requests(user):
    """Preserve the existing Pending scope and locking-capable queryset."""
    qs = LeaveRequest.objects.filter(status="Pending").select_related("employee", "leave_type")
    if has_permission(user, "approve_leave_all_departments"):
        return qs
    if get_role_code(user) == "DEPT_MANAGER":
        employee = getattr(user, "employee", None)
        if not employee:
            return qs.none()
        dept_ids = employee.managed_departments.values_list("pk", flat=True)
        return qs.filter(employee__department_id__in=dept_ids)
    return qs.none()
