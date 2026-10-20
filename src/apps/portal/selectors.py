"""Read selectors shared by approval views and the homepage."""
from apps.leave.models import LeaveRequest
from apps.security.data_access import visible_leave_requests_for
from apps.security.permissions import has_permission


def approvable_leave_requests(user):
    """Preserve the existing Pending scope and locking-capable queryset."""
    qs = LeaveRequest.objects.filter(status="Pending").select_related("employee", "leave_type")
    if has_permission(user, "approve_leave_all_departments") or has_permission(user, "approve_leave"):
        return visible_leave_requests_for(user, qs)
    return qs.none()
