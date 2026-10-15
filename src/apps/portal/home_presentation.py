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
            if cards and cards[0]["label"] == "Nhân viên đang làm việc": cards[0]["label"] = "Nhân viên Active (theo tổng quan chung)"
        if new_queue.get("state") in ("ready", "empty") and not queue_duplicates("pending_leave_approvals"):
            for item in cards:
                if item["label"] == "Đơn nghỉ chờ duyệt": item["label"] = "Đơn nghỉ chờ duyệt (theo tổng quan chung)"
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
            if cards and cards[0]["label"] == "Nhân viên trong phòng": cards[0]["label"] = "Nhân viên Active trong phòng (theo tổng quan chung)"
        if new_queue.get("state") in ("ready", "empty") and not queue_duplicates("dept_pending_leaves"):
            for item in cards:
                if item["label"] == "Đơn nghỉ phòng ban chờ duyệt": item["label"] = "Đơn nghỉ phòng ban (theo tổng quan chung)"
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
    # Legacy counters without a supplied source are not useful summary cards.
    # Keep real zero/error states of the current dashboard blocks unchanged.
    groups = [dict(group, cards=[card for card in group["cards"] if card["value"] is not None]) for group in groups]
    groups = [group for group in groups if group["cards"]]
    result.update(home_groups=groups, home_queue=queue, home_actions=actions)
    result["dashboard_layout"] = grouped_dashboard(user, context, result)
    return result


def grouped_dashboard(user, context, presentation):
    """Presentation only: reuse materialized DTOs and counters; never read the database."""
    snapshot = context.get("dashboard_snapshot", {})
    sections = snapshot.get("sections", {})
    compact = has_permission(user, "approve_personnel_decision") and not has_permission(user, "manage_hr")
    limit = 3 if compact else 5
    layout = {"density": "compact" if compact else "comfortable", "limit": limit,
              "main": [], "groups": [], "actions": {}, "queue": [], "totals": []}
    actions = {a["label"]: a for a in presentation["home_actions"]}
    layout["actions"] = actions
    layout["create_employee"] = actions.get("Tạo hồ sơ nhân viên")
    layout["create_dispatch"] = actions.get("Tạo công văn")
    layout["assign_task"] = actions.get("Giao công việc")
    layout["recruitment_href"] = reverse("portal:recruitment_hub") if any(has_permission(user,p) for p in ("manage_hr","request_recruitment","approve_recruitment")) else None
    layout["headcount_href"] = reverse("portal:report_headcount") + "?year=" + str(snapshot.get("plan_year", "")) if has_permission(user,"view_reports") else None
    layout["report_action"] = actions.get("Mở báo cáo điều hành")
    layout["my_work"] = bool(context.get("employee"))
    layout["manager"] = bool(context.get("is_manager_view"))
    counts = sections.get("status", {}).get("counts", {})
    metrics = {m["key"]: dict(m) for m in snapshot.get("metrics", [])}
    def add(item):
        if item and item.get("value") is not None and len(layout["main"]) < 4:
            layout["main"].append(dict(item))
    if layout["manager"]:
        item = metrics.get("managed")
        if item: item["label"] = "Nhân viên trong phòng"
        add(item)
        queue = sections.get("queue", {}).get("rows", [])
        if queue: add(dict(queue[0], label="Đơn nghỉ phòng chờ duyệt", icon="calendar"))
        if context.get("dept_open_tasks") is not None:
            add(dict(label="Công việc phòng chưa hoàn thành",value=context["dept_open_tasks"],icon="briefcase"))
        add(sections.get("joined"))
    elif metrics:
        add(metrics.get("managed")); add(metrics.get("approved"))
        contracts = sections.get("contracts")
        if contracts and contracts.get("upcoming_count") is not None:
            add(dict(label="Hợp đồng sắp hết hạn (≤60 ngày)",value=contracts["upcoming_count"],icon="contract",
                     note="Hợp đồng Active đã bắt đầu; đến 60 ngày tới.", overdue=contracts.get("overdue_count",0)))
        else: add(sections.get("joined"))
        queue = sections.get("queue", {}).get("rows", [])
        if queue: add(dict(queue[0], label="Đơn nghỉ chờ duyệt",icon="calendar"))
        elif context.get("open_tasks_company") is not None:
            add(dict(label="Công việc đang mở toàn Trung tâm",value=context["open_tasks_company"],icon="briefcase"))
        if len(layout["main"])<4 and "joined" in sections: add(sections["joined"])
    # Do not duplicate the joined counter when it fills a fallback main slot.
    unique=[]
    for item in layout["main"]:
        if not any(x.get("label")==item.get("label") for x in unique):unique.append(item)
    layout["main"]=unique
    short_labels = {"Nhân sự đang quản lý": "Nhân sự quản lý", "Nghỉ được duyệt trong ngày": "Nghỉ phép hôm nay",
                    "Hợp đồng sắp hết hạn (≤60 ngày)": "Hợp đồng sắp hết hạn",
                    "Công việc phòng chưa hoàn thành": "Việc phòng chưa xong", "Nhân sự vào làm trong tháng": "Vào làm trong tháng"}
    for item in layout["main"]:
        item["short_label"] = short_labels.get(item["label"], item["label"])

    layout["status_counts"] = counts
    layout["main_keys"] = [m.get("key") for m in layout["main"]]
    layout["my_checklist"] = next((item for item in presentation["home_queue"]
        if item.get("label", "").startswith("Checklist") and item.get("value")), None)
    # Urgent work comes from existing scoped queue DTOs or legacy supplied counters.
    queue = list(sections.get("queue", {}).get("rows", []))
    for item in presentation["home_queue"]:
        if item.get("label", "").startswith("Checklist"):
            continue  # Personal overdue work belongs to My work, not Administration.
        if not any(q.get("label")==item["label"] for q in queue):
            queue.append(item)
    requests = sections.get("requests", {})
    for row in requests.get("rows", []):
        if row["code"]=="Pending" and has_permission(user,"approve_recruitment"):
            queue.append(dict(label="Đề xuất tuyển dụng chờ duyệt",value=row["value"],href=requests.get("cta")))
    seen=set()
    for item in queue:
        if item.get("value",0) and item.get("href") and item["href"] not in seen:
            seen.add(item["href"]);layout["queue"].append(item)
    for group in presentation["home_groups"]:
        if group["title"]=="Công việc của tôi": continue
        for card in group["cards"]:
            if card.get("value",0) and not card.get("warning") and card["label"] not in {m["label"] for m in layout["main"]}:
                if "Nhân viên" not in card["label"]:layout["totals"].append(card)
    headcount=sections.get("headcount",{})
    # Geometry only; sort copies, preserving all DTO values and the full SR table.
    capacity = sorted(headcount.get("rows", []), key=lambda row: abs(row.get("gap") or 0), reverse=True)
    display_rows = []
    for original in capacity[:4 if compact else 6]:
        row = dict(original)
        maximum = max(row.get("actual", 0), row.get("planned") or 0, 1)
        actual = row.get("actual", 0)
        planned = row.get("planned")
        row.update(bar_width=f"{actual * 100 / maximum:.4f}",
                   plan_width=f"{(planned or 0) * 100 / maximum:.4f}",
                   over_width=f"{max(actual - (planned or 0), 0) * 100 / maximum:.4f}" if planned is not None else "0",
                   over=abs(row.get("gap") or 0))
        display_rows.append(row)
    layout["headcount"] = dict(headcount, rows=display_rows, all_rows=headcount.get("rows", []), total=len(capacity)) if capacity or headcount.get("state")=="error" else None
    contracts=sections.get("contracts",{})
    uncontracted=snapshot.get("uncontracted",{})
    layout["contracts"] = dict(contracts,upcoming_rows=contracts.get("upcoming_rows",[])[:3],overdue_rows=contracts.get("overdue_rows",[])[:limit]) if contracts else None
    layout["show_expiring"] = bool(contracts and (contracts.get("upcoming_count") or contracts.get("overdue_count") or uncontracted.get("value") or contracts.get("state")=="error"))
    layout["show_distribution"] = bool(contracts.get("types"))
    history=sections.get("history",{})
    layout["history"] = dict(history,rows=history.get("rows",[])[:limit],total=len(history.get("rows",[]))) if history.get("rows") or history.get("state")=="error" else None
    joined=sections.get("joined",{})
    layout["joined"] = joined if joined and not any(
        item.get("label") == joined.get("label") for item in layout["main"]
    ) else None
    leave=sections.get("global_leave") or (sections.get("own_leave") if layout["manager"] else None)
    layout["leave"] = dict(leave,rows=leave.get("rows",[])[:2 if compact else 3],all_rows=leave.get("rows",[]),total=len(leave.get("rows",[])),key="global_leave" if leave.get("global_scope") else "own_leave") if leave and (leave.get("rows") or leave.get("state")=="error") else None
    recruitment=[]
    for key in ("postings","candidates","requests"):
        data=sections.get(key)
        if data:
            rows = [dict(row, label="Đã đóng" if row.get("code") == "Closed" else row["label"]) for row in data.get("rows", [])]
            recruitment.append(dict(data, key=key, rows=rows))
    layout["recruitment"] = recruitment
    project_rows=[]
    if context.get("show_project_activity_summary"):
        for key, label in (("activity_total", "Hoạt động trong tháng"),
                           ("activity_completed", "Task báo cáo hoàn thành"),
                           ("activity_overdue", "Task quá hạn"),
                           ("activity_report_missing", "Task thiếu báo cáo"),
                           ("activity_without_task", "Hoạt động chưa có Task")):
            value = context.get(key, 0)
            project_rows.append(dict(label=label, value=value,
                warning=bool(value and key in ("activity_overdue", "activity_report_missing"))))
    layout["projects"]=project_rows
    layout["project_empty"]=not any(row["value"] for row in project_rows)
    layout["project_allowed"]=bool(context.get("show_project_activity_summary"))
    hr=bool(layout["show_expiring"] or layout["show_distribution"] or layout["headcount"] or layout["history"] or layout["joined"])
    admin=bool(layout["queue"] or layout["leave"] or layout["totals"] or sections.get("queue"))
    if layout["project_allowed"]:layout["groups"].append(dict(key="projects",label="Dự án"))
    if hr:layout["groups"].append(dict(key="hr",label="Nhân sự"))
    if admin:layout["groups"].append(dict(key="admin",label="Hành chính"))
    if recruitment:layout["groups"].append(dict(key="recruitment",label="Tuyển dụng"))
    layout["show_hr"],layout["show_admin"]=hr,admin
    return layout
