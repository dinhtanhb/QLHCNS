from apps.security.permissions import (
    CBDA,
    DEPT_MANAGER,
    DIRECTOR,
    PROJECT_COORDINATOR,
    PROJECT_MANAGER,
    SUPER_ADMIN,
    get_role_code,
    has_permission,
)


ALL_ACTIVITY_ROLES = {SUPER_ADMIN, DIRECTOR, PROJECT_MANAGER, PROJECT_COORDINATOR}


def visible_activities_for(user, queryset=None):
    """Return only activities the current project role is allowed to see."""
    from django.db.models import Q
    from apps.activity.models import Activity

    qs = queryset if queryset is not None else Activity.objects.all()
    role_code = get_role_code(user)
    if getattr(user, "is_superuser", False) or role_code in ALL_ACTIVITY_ROLES:
        return qs

    employee = getattr(user, "employee", None)
    if role_code == DEPT_MANAGER and employee:
        department_ids = employee.managed_departments.values_list("pk", flat=True)
        return qs.filter(project__department_id__in=department_ids)
    if role_code == CBDA and employee:
        return qs.filter(Q(lead_cbda=employee) | Q(coordinator=employee))
    return qs.none()


def can_view_activity(user, activity):
    if not has_permission(user, "view_activity_dashboard"):
        return False
    return visible_activities_for(
        user, activity.__class__.objects.filter(pk=activity.pk)
    ).exists()


def can_manage_activities(user):
    return has_permission(user, "manage_project_activities")
