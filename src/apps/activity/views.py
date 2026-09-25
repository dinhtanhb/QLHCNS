from calendar import monthrange
from datetime import date

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.activity.models import Activity
from apps.activity.forms import ActivityForm
from apps.activity.permissions import can_manage_activities, visible_activities_for
from apps.activity.services import find_schedule_conflicts
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
        "can_manage_activities": can_manage_activities(request.user),
    }
    return render(request, "activity/dashboard.html", context)


def _warn_schedule_conflicts(request, activity):
    conflicts = find_schedule_conflicts(
        employee_id=activity.lead_cbda_id,
        start_date=activity.start_date,
        end_date=activity.end_date,
        exclude_activity_id=activity.pk,
    )
    if conflicts:
        names = ", ".join(item.activity_code for item in conflicts)
        messages.warning(
            request,
            f"Lịch CBDA bị trùng với hoạt động {names}. Hoạt động đã được lưu; "
            "vui lòng kiểm tra và điều phối.",
        )


@login_required
def activity_create(request):
    if not can_manage_activities(request.user):
        raise PermissionDenied

    form = ActivityForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        activity = form.save(commit=False)
        activity.created_by = request.user
        activity.modified_by = request.user
        activity.save()
        _warn_schedule_conflicts(request, activity)
        messages.success(request, "Đã tạo hoạt động dự án.")
        if activity.outgoing_document_id:
            messages.info(request, "IHRMS đã tạo Task báo cáo theo công văn đi được liên kết.")
        return redirect("portal:activity_dashboard")

    return render(request, "activity/activity_form.html", {
        "form": form,
        "page_title": "Tạo hoạt động dự án",
        "submit_label": "Tạo hoạt động",
    })


@login_required
def activity_update(request, pk):
    if not can_manage_activities(request.user):
        raise PermissionDenied
    activity = get_object_or_404(visible_activities_for(request.user), pk=pk)
    had_tracking_task = activity.tasks.exists()
    form = ActivityForm(request.POST or None, instance=activity)
    if request.method == "POST" and form.is_valid():
        activity = form.save(commit=False)
        activity.modified_by = request.user
        activity.save()
        _warn_schedule_conflicts(request, activity)
        messages.success(request, "Đã cập nhật hoạt động dự án.")
        if activity.outgoing_document_id and not had_tracking_task and activity.tasks.exists():
            messages.info(request, "IHRMS đã tạo Task báo cáo theo công văn đi được liên kết.")
        return redirect("portal:activity_dashboard")

    return render(request, "activity/activity_form.html", {
        "form": form,
        "activity": activity,
        "page_title": "Cập nhật hoạt động dự án",
        "submit_label": "Lưu thay đổi",
    })
