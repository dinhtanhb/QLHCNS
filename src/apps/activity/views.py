from calendar import Calendar, monthrange
from datetime import date, timedelta
import mimetypes

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse
from django.core.exceptions import PermissionDenied
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.activity.models import Activity, ActivityProposal
from apps.activity.activity_codes import ACTIVITY_CODE_NAMES
from apps.activity.forms import (
    ActivityForm,
    ActivityProposalDecisionForm,
    ActivityProposalSendForm,
    ActivityProposalUploadForm,
)
from apps.activity.permissions import can_manage_activities, visible_activities_for
from apps.activity.services import find_schedule_conflicts, send_activity_proposal_for_approval
from apps.hrm.models import Employee
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


def _monthly_activities(user, month_start, month_end):
    task_prefetch = Prefetch(
        "tasks",
        queryset=Task.objects.order_by("created_date"),
        to_attr="tracking_tasks",
    )
    return visible_activities_for(user).filter(
        Q(start_date__lte=month_end, end_date__gte=month_start)
        | Q(tasks__due_date__gte=month_start, tasks__due_date__lte=month_end)
    ).exclude(status="Cancelled").select_related(
        "project", "lead_cbda", "coordinator", "outgoing_document"
    ).prefetch_related(task_prefetch).distinct()


def _filter_monthly_activities(request, activities):
    cbda_ids = list(activities.order_by().values_list("lead_cbda_id", flat=True).distinct())
    cbda_choices = Employee.objects.filter(pk__in=cbda_ids).order_by("full_name")
    selected_cbda = request.GET.get("cbda", "").strip()
    if selected_cbda.isdigit() and int(selected_cbda) in cbda_ids:
        activities = activities.filter(lead_cbda_id=int(selected_cbda))
    else:
        selected_cbda = ""
    return activities, cbda_choices, selected_cbda


@login_required
def activity_dashboard(request):
    if not has_permission(request.user, "view_activity_dashboard"):
        raise PermissionDenied

    today = timezone.localdate()
    month_start = _selected_month(request.GET.get("month"), today)
    month_end = date(month_start.year, month_start.month, monthrange(month_start.year, month_start.month)[1])
    activities = _monthly_activities(request.user, month_start, month_end)
    activities, cbda_choices, selected_cbda = _filter_monthly_activities(request, activities)
    activities = activities.order_by("start_date", "activity_code")

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
        "cbda_choices": cbda_choices,
        "selected_cbda": selected_cbda,
    }
    return render(request, "activity/dashboard.html", context)


@login_required
def activity_calendar(request):
    if not has_permission(request.user, "view_activity_dashboard"):
        raise PermissionDenied

    today = timezone.localdate()
    month_start = _selected_month(request.GET.get("month"), today)
    month_end = date(month_start.year, month_start.month, monthrange(month_start.year, month_start.month)[1])
    activities, cbda_choices, selected_cbda = _filter_monthly_activities(
        request, _monthly_activities(request.user, month_start, month_end)
    )
    activities = activities.order_by("start_date", "activity_code")

    weeks = []
    for week in Calendar(firstweekday=0).monthdatescalendar(month_start.year, month_start.month):
        cells = []
        for day in week:
            cells.append({"date": day, "in_month": day.month == month_start.month, "items": []})
        weeks.append(cells)
    cells_by_date = {cell["date"]: cell for week in weeks for cell in week}

    for activity in activities:
        task = activity.tracking_tasks[0] if activity.tracking_tasks else None
        current = max(activity.start_date, month_start)
        final_day = min(activity.end_date, month_end)
        while current <= final_day:
            cells_by_date[current]["items"].append({"activity": activity})
            current += timedelta(days=1)
        if task and task.status != "Cancelled" and task.due_date in cells_by_date:
            cells_by_date[task.due_date]["items"].append({"task": task, "activity": activity})

    return render(request, "activity/calendar.html", {
        "weeks": weeks,
        "weekdays": ("Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"),
        "month": month_start.strftime("%Y-%m"),
        "month_label": month_start.strftime("%m/%Y"),
        "cbda_choices": cbda_choices,
        "selected_cbda": selected_cbda,
        "is_overview": get_role_code(request.user) != "CBDA",
    })


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
        "activity_code_names": ACTIVITY_CODE_NAMES,
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
        "activity_code_names": ACTIVITY_CODE_NAMES,
        "activity": activity,
        "page_title": "Cập nhật hoạt động dự án",
        "submit_label": "Lưu thay đổi",
    })


def _can_coordinate_package(user, activity):
    role = get_role_code(user)
    if getattr(user, "is_superuser", False) or role in ("SUPER_ADMIN", "PROJECT_MANAGER"):
        return True
    return role == "PROJECT_COORDINATOR" and getattr(user, "employee_id", None) == activity.coordinator_id


@login_required
def activity_proposal(request, activity_id):
    activity = get_object_or_404(visible_activities_for(request.user), pk=activity_id)
    is_lead = get_role_code(request.user) == "CBDA" and getattr(request.user, "employee_id", None) == activity.lead_cbda_id
    can_edit = is_lead or _can_coordinate_package(request.user, activity)
    can_send = _can_coordinate_package(request.user, activity)
    package = activity.proposal_packages.order_by("-version").first()
    package_history = activity.proposal_packages.select_related("approver", "decision_by").order_by("-version")
    upload_form = ActivityProposalUploadForm(instance=package) if package else ActivityProposalUploadForm()
    send_form = ActivityProposalSendForm()
    decision_form = ActivityProposalDecisionForm()

    if request.method == "POST":
        if not can_edit:
            raise PermissionDenied
        if package and package.status == "Submitted":
            messages.error(request, "Hồ sơ đang chờ Giám đốc duyệt nên không thể thay đổi.")
            return redirect("portal:activity_proposal", activity_id=activity.pk)
        if request.POST.get("action") != "send":
            if package and package.status in ("Approved", "ChangesRequested"):
                previous = package
                package = ActivityProposal(activity=activity, version=previous.version + 1)
                for field_name in ("proposal_excel", "proposal_pdf", "budget_excel", "budget_pdf"):
                    prior_file = getattr(previous, field_name)
                    if prior_file:
                        setattr(package, field_name, prior_file.name)
                upload_form = ActivityProposalUploadForm(request.POST, request.FILES, instance=package)
            elif package is None:
                package = ActivityProposal(activity=activity, version=1)
                upload_form = ActivityProposalUploadForm(request.POST, request.FILES, instance=package)

        if request.POST.get("action") == "send":
            if not can_send:
                raise PermissionDenied
            send_form = ActivityProposalSendForm(request.POST)
            if not package or not package.pk or not package.has_required_files():
                messages.error(request, "Cần lưu đủ 2 tệp Excel và 2 tệp PDF trước khi gửi.")
            elif send_form.is_valid():
                approver = send_form.cleaned_data["approver"]
                try:
                    approval_url = request.build_absolute_uri(
                        reverse("portal:activity_proposal", args=(activity.pk,))
                    )
                    recipient = send_activity_proposal_for_approval(package, approver, request.user, approval_url)
                except Exception as exc:
                    messages.error(request, f"Email chưa được gửi: {exc}")
                else:
                    package.status = "Submitted"
                    package.approver = approver
                    package.sent_to = recipient
                    package.submitted_by = request.user
                    package.submitted_at = timezone.now()
                    package.modified_by = request.user
                    package.save(update_fields=("status", "approver", "sent_to", "submitted_by", "submitted_at", "modified_by", "modified_date"))
                    messages.success(request, "Microsoft 365 đã chấp nhận email gửi đi; hồ sơ đang chờ phê duyệt.")
                    return redirect("portal:activity_proposal", activity_id=activity.pk)
        else:
            upload_form = ActivityProposalUploadForm(request.POST, request.FILES, instance=package)
            if upload_form.is_valid():
                package = upload_form.save(commit=False)
                package.activity = activity
                package.created_by = package.created_by or request.user
                package.modified_by = request.user
                package.save()
                messages.success(request, f"Đã lưu hồ sơ phiên bản {package.version}.")
                return redirect("portal:activity_proposal", activity_id=activity.pk)

    can_decide = bool(
        package and package.status == "Submitted"
        and get_role_code(request.user) == "DIRECTOR"
        and package.approver_id == request.user.pk
    )
    return render(request, "activity/proposal_detail.html", {
        "activity": activity,
        "package": package,
        "package_history": package_history,
        "upload_form": upload_form,
        "send_form": send_form,
        "decision_form": decision_form,
        "can_edit": can_edit and (not package or package.status in ("Draft", "ChangesRequested", "Approved")),
        "can_send": can_send,
        "can_decide": can_decide,
    })


@login_required
def activity_proposal_decide(request, package_id):
    package = get_object_or_404(ActivityProposal.objects.select_related("activity"), pk=package_id)
    activity = get_object_or_404(visible_activities_for(request.user), pk=package.activity_id)
    if (
        request.method != "POST"
        or get_role_code(request.user) != "DIRECTOR"
        or package.approver_id != request.user.pk
        or package.status != "Submitted"
    ):
        raise PermissionDenied
    form = ActivityProposalDecisionForm(request.POST)
    if form.is_valid():
        package.status = form.cleaned_data["decision"]
        package.decision_comment = form.cleaned_data["comment"].strip()
        package.decision_by = request.user
        package.decision_at = timezone.now()
        package.modified_by = request.user
        package.save(update_fields=("status", "decision_comment", "decision_by", "decision_at", "modified_by", "modified_date"))
        messages.success(request, "Đã ghi nhận quyết định hồ sơ.")
    else:
        messages.error(request, "Thông tin quyết định chưa hợp lệ. Vui lòng kiểm tra lại.")
    return redirect("portal:activity_proposal", activity_id=activity.pk)


@login_required
def activity_proposal_file(request, package_id, field_name):
    package = get_object_or_404(ActivityProposal.objects.select_related("activity"), pk=package_id)
    get_object_or_404(visible_activities_for(request.user), pk=package.activity_id)
    if field_name not in {"proposal_excel", "proposal_pdf", "budget_excel", "budget_pdf"}:
        raise PermissionDenied
    stored_file = getattr(package, field_name)
    if not stored_file:
        raise PermissionDenied
    content_type, _ = mimetypes.guess_type(stored_file.name)
    filename = stored_file.name.rsplit("/", 1)[-1]
    return FileResponse(
        stored_file.open("rb"),
        as_attachment=not field_name.endswith("_pdf"),
        filename=filename,
        content_type=content_type or "application/octet-stream",
    )
