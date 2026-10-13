"""Read-only homepage presentation using existing counts and permission checks."""
from django.urls import reverse
from django.utils import timezone

from apps.security.permissions import has_permission


def home_presentation(user, context):
    """Build links without changing count scopes or issuing database queries."""
    result = {"home_period": timezone.localdate().strftime("%d/%m/%Y")}
    groups = []
    queue = []
    sections = context.get("dashboard_snapshot", {}).get("sections", {})
    status = sections.get("status", {})
    new_queue = sections.get("queue", {})

    def status_duplicates(key):
        return (status.get("state") in ("ready", "empty") and
                context.get(key) is not None and context[key] == status.get("counts", {}).get("active"))

    def queue_duplicates(key):
        rows = new_queue.get("rows", [])
        return (new_queue.get("state") in ("ready", "empty") and len(rows) == 1 and
                context.get(key) is not None and context[key] == rows[0].get("value"))

    def target(name, permission=None):
        return reverse("portal:" + name) if not permission or has_permission(user, permission) else None

    def card(label, key, name=None, permission=None, pending=False, query="", actionable=True):
        href = target(name, permission) if name else None
        value = context.get(key)
        item = {"label": label, "value": value, "href": href + query if href else None,
                "warning": pending, "period": "Hiện tại", "icon": "calendar" if "leave" in key else "checklist" if "lifecycle" in key else "briefcase" if "task" in key else "people"}
        if name == "hr_employee_list":
            # A status total does not represent the contracted directory set.
            item["href"] = None
            item["note"] = "Gồm cả hồ sơ chưa có hợp đồng; danh sách Hồ sơ nhân viên chỉ hiện hồ sơ đã có hợp đồng."
        if pending and actionable and href and value is not None:
            queue.append(item)
        return item

    if context.get("employee"):
        groups.append({"title": "Công việc của tôi", "cards": [
            card("Đơn nghỉ của tôi đang chờ duyệt", "my_pending_leaves", "leave_list", pending=True, actionable=False),
            card("Công việc của tôi chưa hoàn thành", "my_open_tasks", "task_list", query="?scope=assigned_to_me"),
        ]})
    if context.get("is_management_view"):
        cards = [
            card("Nhân viên đang làm việc", "total_employees", "hr_employee_list", "view_all_employees"),
            card("Đơn nghỉ chờ duyệt", "pending_leave_approvals", "leave_approval_list", "approve_leave", True),
            card("Đề xuất tuyển dụng chờ duyệt", "pending_recruitment", "recruitment_list", "approve_recruitment", True),
            card("Tài liệu chờ ban hành", "pending_documents", "document_approval_list", "approve_document", True),
            card("Công việc đang mở toàn Trung tâm", "open_tasks_company"),
        ]
        if has_permission(user, "view_asset"):
            cards.append(card("Tài sản đang cấp phát", "assets_in_use", "asset_admin_list", "view_asset"))
        cards = [c for i,c in enumerate(cards) if not (i == 0 and status_duplicates("total_employees") or i == 1 and queue_duplicates("pending_leave_approvals"))]
        if status.get("state") in ("ready", "empty") and not status_duplicates("total_employees"):
            if cards and cards[0]["label"] == "Nhân viên đang làm việc": cards[0]["label"] = "Nhân viên Active theo tổng quan cũ"
        if new_queue.get("state") in ("ready", "empty") and not queue_duplicates("pending_leave_approvals"):
            for item in cards:
                if item["label"] == "Đơn nghỉ chờ duyệt": item["label"] = "Đơn nghỉ chờ duyệt theo tổng quan cũ"
        groups.append({"title": "Tổng quan Trung tâm", "cards": cards})
    elif context.get("is_manager_view"):
        cards = [
            card("Nhân viên trong phòng", "dept_employee_count", "hr_employee_list"),
            card("Đơn nghỉ phòng ban chờ duyệt", "dept_pending_leaves", "leave_approval_list", "approve_leave", True),
            card("Công việc phòng ban chưa hoàn thành", "dept_open_tasks"),
        ]
        if has_permission(user, "view_asset"):
            cards.append(card("Tài sản đang cấp phát trong phòng", "dept_assets_in_use"))
        cards = [c for i,c in enumerate(cards) if not (i == 0 and status_duplicates("dept_employee_count") or i == 1 and queue_duplicates("dept_pending_leaves"))]
        if status.get("state") in ("ready", "empty") and not status_duplicates("dept_employee_count"):
            if cards and cards[0]["label"] == "Nhân viên trong phòng": cards[0]["label"] = "Nhân viên Active trong phòng theo tổng quan cũ"
        if new_queue.get("state") in ("ready", "empty") and not queue_duplicates("dept_pending_leaves"):
            for item in cards:
                if item["label"] == "Đơn nghỉ phòng ban chờ duyệt": item["label"] = "Đơn nghỉ phòng ban theo tổng quan cũ"
        groups.append({"title": "Tổng quan phòng ban", "cards": cards})
    if has_permission(user, "view_own_lifecycle_items") and "lifecycle_overdue_count" in context:
        card("Checklist onboarding/offboarding quá hạn", "lifecycle_overdue_count", "lifecycle_case_list", "view_own_lifecycle_items", True)
    actions = []
    for label, name, permission, requires_employee in [
        ("Tạo đơn nghỉ", "leave_create", None, True),
        ("Giao công việc", "task_create", "assign_task", True),
        ("Tạo công văn", "dispatch_create", "manage_office", True),
        ("Tạo hồ sơ nhân viên", "hr_employee_create", "manage_hr", False),
        ("Mở báo cáo điều hành", "report_hub", "view_reports", False),
    ]:
        href = target(name, permission)
        if href and (not requires_employee or context.get("employee")):
            actions.append({"label": label, "href": href})
    if not context.get("employee"):
        if user.is_superuser and user.is_staff:
            result["profile_setup"] = {"label": "Gắn hồ sơ nhân viên", "href": reverse("admin:security_user_change", args=[user.pk])}
        elif has_permission(user, "manage_hr"):
            result["profile_setup"] = {"label": "Tạo hồ sơ nhân viên", "href": reverse("portal:hr_employee_create")}
    if "dept_counts" in context:
        # Evaluate the same queryset once, also reused by the alternative table.
        result["dept_counts"] = list(context["dept_counts"])
    result.update(home_groups=groups, home_queue=queue, home_actions=actions)
    return result
