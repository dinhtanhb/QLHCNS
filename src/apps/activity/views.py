from calendar import monthrange
from datetime import date

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch, Q
from django.shortcuts import render
from django.utils import timezone

from apps.activity.models import Activity
from apps.activity.permissions import visible_activities_for
from apps.security.permissions import get_role_code, has_permission
from apps.task.models import Task


def _selected_month(value, today):
    try:
        year_text, month_text = value.split("-", 1)
        year, month = int(year_text), int(month_text)
        if 1 <= month <= 12 and 2000 <= year <= 2100:
            return date(year, month, 1)
    except (AttributeError, TypeError, ValueError):
        pass
    return date(today.year, today.month, 1)


@login_required
def activity_dashboard(request):
    if not has_permission(request.user, "view_activity_dashboard"):
        raise PermissionDenied

    today = timezone.localdate()
    month_start = _selected_month(request.GET.get("month"), today)
    month_end = date(month_start.year, month_start.month, monthrange(month_start.year, month_start.month)[1])
    task_prefetch = Prefetch(
        "tasks",
        queryset=Task.objects.order_by("created_date"),
        to_attr="tracking_tasks",
    )
    activities = visible_activities_for(request.user).filter(
        Q(start_date__lte=month_end, end_date__gte=month_start)
        | Q(tasks__due_date__gte=month_start, tasks__due_date__lte=month_end)
    ).exclude(status="Cancelled").select_related(
        "project", "lead_cbda", "coordinator", "outgoing_document"
    ).prefetch_related(task_prefetch).distinct().order_by("start_date", "activity_code")

    rows = []
    for activity in activities:
        task = activity.tracking_tasks[0] if activity.tracking_tasks else None
        is_overdue = bool(task and task.status not in ("Done", "Cancelled") and task.due_date and task.due_date < today)
        rows.append({"activity": activity, "task": task, "is_overdue": is_overdue})

    tasks = [row["task"] for row in rows if row["task"]]
    context = {
        "rows": rows,
        "month": month_start.strftime("%Y-%m"),
        "month_label": month_start.strftime("%m/%Y"),
        "today": today,
        "total_activities": len(rows),
        "completed_count": sum(task.status == "Done" for task in tasks),
        "overdue_count": sum(row["is_overdue"] for row in rows),
        "report_missing_count": sum(bool(task and task.status != "Cancelled" and not task.report_file) for task in tasks),
        "without_task_count": sum(row["task"] is None for row in rows),
        "is_overview": get_role_code(request.user) != "CBDA",
    }
    return render(request, "activity/dashboard.html", context)
