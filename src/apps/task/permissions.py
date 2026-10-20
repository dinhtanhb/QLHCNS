"""Selector và quyền truy cập dữ liệu công việc (Task)."""
from django.db.models import Q
from apps.security.permissions import (
    SUPER_ADMIN,
    DIRECTOR,
    HR_MANAGER,
    DEPT_MANAGER,
    PROJECT_MANAGER,
    PROJECT_COORDINATOR,
    CBDA,
    get_role_code,
)


def visible_tasks_for(user, queryset=None):
    """Giới hạn danh sách Task mà user được phép xem.

    - Superuser, SUPER_ADMIN, DIRECTOR, HR_MANAGER: toàn quyền xem mọi Task.
    - DEPT_MANAGER: Task trong các phòng ban quản lý, hoặc Task liên quan Hoạt động
      thuộc dự án của phòng ban, hoặc Task do chính mình giao/nhận.
    - PROJECT_MANAGER, PROJECT_COORDINATOR, CBDA: Task liên kết với Hoạt động dự án
      thuộc phạm vi được xem (visible_activities_for), hoặc Task do chính mình giao/nhận.
      Tuyệt đối không xem được Task hành chính/HR riêng không có Activity.
    - EMPLOYEE và các vai trò khác: Task do chính mình giao hoặc phụ trách.
    """
    from apps.task.models import Task
    from apps.activity.permissions import visible_activities_for

    qs = queryset if queryset is not None else Task.objects.all()
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return qs.none()
    if getattr(user, "is_superuser", False):
        return qs

    role_code = get_role_code(user)
    if role_code in (SUPER_ADMIN, DIRECTOR, HR_MANAGER):
        return qs

    employee = getattr(user, "employee", None)
    if not employee:
        return qs.none()

    q_filter = Q(assigned_to_employee=employee) | Q(assigned_by_employee=employee)

    if role_code == DEPT_MANAGER:
        dept_ids = employee.managed_departments.values_list("pk", flat=True)
        q_filter |= Q(department_id__in=dept_ids) | Q(assigned_to_employee__department_id__in=dept_ids)
        visible_acts = visible_activities_for(user)
        q_filter |= Q(activity__in=visible_acts)
    elif role_code in (PROJECT_MANAGER, PROJECT_COORDINATOR, CBDA):
        visible_acts = visible_activities_for(user)
        q_filter |= Q(activity__in=visible_acts)

    return qs.filter(q_filter).distinct()
