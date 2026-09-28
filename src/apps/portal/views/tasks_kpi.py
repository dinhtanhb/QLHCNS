from django.core.exceptions import ValidationError
from django.db import transaction
from django.views.decorators.http import require_POST
from apps.security.permissions import has_permission
from django.db.models import Prefetch, Q
from apps.activity.permissions import can_view_activity, visible_activities_for
from apps.common.uploads import validate_upload
from apps.m365.graph_client import GraphAPIError
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from apps.notification.services import notify
from apps.notification.models import Notification, NotificationEmailOutbox
from decimal import Decimal, InvalidOperation
from django.http import HttpResponseForbidden
from django.utils import timezone
from apps.hrm.models import Employee
from apps.task.models import Task, TaskComment
from apps.kpi.models import EmployeeKPI, KPIPeriod, KPITemplate
from .common import _friendly_error, _get_employee, _role_code




def _can_assign_task(request):
    return has_permission(request.user, "assign_task")


@login_required
def task_list(request):
    employee = _get_employee(request)
    is_project_overview = has_permission(request.user, "view_activity_dashboard")
    can_assign_task = _can_assign_task(request)
    can_view_task_scopes = can_assign_task or is_project_overview
    requested_scope = request.GET.get("scope")
    if requested_scope in {"assigned_to_me", "assigned_by_me"}:
        task_scope_name = requested_scope
    elif requested_scope == "activity_overview" and is_project_overview:
        task_scope_name = "activity_overview"
    else:
        task_scope_name = "activity_overview" if is_project_overview else "assigned_to_me"

    if task_scope_name == "assigned_by_me":
        # Người giao chỉ xem được những Task do chính họ giao; không mở rộng
        # sang toàn bộ công việc chỉ vì họ có quyền giao việc.
        task_scope = Q(assigned_by_employee=employee) if employee else Q(pk__in=[])
    elif task_scope_name == "activity_overview":
        # Quyền giám sát hoạt động chỉ áp dụng trong phạm vi riêng này,
        # không trộn Task của CBDA vào tab "Việc của tôi".
        task_scope = Q(activity__in=visible_activities_for(request.user))
    else:
        task_scope = Q(assigned_to_employee=employee) if employee else Q(pk__in=[])
    tasks = Task.objects.filter(task_scope).select_related(
        "assigned_to_employee", "assigned_by_employee", "activity"
    ).order_by("due_date", "created_date")
    return render(request, "portal/task_list.html", {
        "tasks": tasks,
        "can_assign_task": can_assign_task,
        "can_view_task_scopes": can_view_task_scopes,
        "is_project_overview": is_project_overview,
        "task_scope_name": task_scope_name,
    })


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    employee = _get_employee(request)
    is_owner = bool(employee and task.assigned_to_employee_id == employee.id)
    is_assigner = bool(employee and task.assigned_by_employee_id == employee.id)

    if task.activity_id:
        can_view = bool(
            is_owner or is_assigner or request.user.is_superuser
            or can_view_activity(request.user, task.activity)
        )
    elif request.user.is_superuser or is_owner:
        can_view = True
    elif _role_code(request) == "HR_MANAGER":
        can_view = True
    elif _role_code(request) == "DEPT_MANAGER" and employee:
        managed_department_ids = employee.managed_departments.values_list("pk", flat=True)
        can_view = task.assigned_to_employee.department_id in managed_department_ids
    else:
        can_view = is_assigner

    if not can_view:
        messages.error(request, "Anh/chị không có quyền xem công việc này.")
        return redirect("portal:task_list")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "update_status" and is_owner:
            new_status = request.POST.get("status")
            if new_status in dict(Task.STATUS_CHOICES):
                task.status = new_status
                task.completed_date = timezone.localdate() if new_status == "Done" else None
                try:
                    task.clean()
                    task.save()
                    status_label = dict(Task.STATUS_CHOICES).get(new_status, new_status)
                    notify(
                        task.assigned_by_employee, "task", "Công việc có cập nhật trạng thái",
                        f"{task.task_name}: {status_label}.",
                        link=f"/portal/tasks/{task.pk}/", created_by=request.user,
                    )
                    messages.success(request, "Đã cập nhật trạng thái công việc.")
                except ValidationError as exc:
                    messages.error(request, "; ".join(exc.messages))
        elif action == "upload_activity_report" and is_owner and task.activity_id:
            uploaded = request.FILES.get("report_file")
            if not uploaded:
                messages.error(request, "Chọn tệp báo cáo trước khi tải lên.")
            else:
                try:
                    validate_upload(uploaded)
                    task.report_file = uploaded
                    task.clean()
                    task.save()
                    messages.success(request, "Đã tải báo cáo hoạt động lên kho SharePoint.")
                except (ValidationError, OSError, ValueError, GraphAPIError) as exc:
                    _friendly_error(request, exc, "Không thể tải báo cáo lên kho tài liệu.")
        elif action == "add_comment" and employee:
            text = request.POST.get("comment_text", "").strip()
            if text:
                TaskComment.objects.create(task=task, employee=employee, comment_text=text, created_by=request.user)
                other_party = task.assigned_by_employee if is_owner else task.assigned_to_employee
                if other_party and other_party.pk != employee.pk:
                    notify(
                        other_party, "task", "Có bình luận mới trong công việc",
                        f"{task.task_name}: {text[:150]}",
                        link=f"/portal/tasks/{task.pk}/", created_by=request.user,
                    )
                messages.success(request, "Đã thêm bình luận.")
        return redirect("portal:task_detail", pk=pk)

    return render(request, "portal/task_detail.html", {
        "task": task, "is_owner": is_owner, "comments": task.comments.select_related("employee"),
    })


@login_required
def task_create(request):
    if not _can_assign_task(request):
        messages.error(request, "Anh/chị không có quyền giao việc.")
        return redirect("portal:task_list")

    employee = _get_employee(request)
    role_code = _role_code(request)
    if not request.user.is_superuser and role_code == "DEPT_MANAGER" and employee:
        dept_ids = employee.managed_departments.values_list("pk", flat=True)
        candidates = Employee.objects.filter(department_id__in=dept_ids)
    else:
        candidates = Employee.objects.all()

    if request.method == "POST":
        try:
            assignee = candidates.filter(
                pk=request.POST.get("assigned_to_employee")
            ).first()
            if assignee is None:
                raise ValidationError(
                    "Chỉ được giao việc cho nhân viên thuộc phạm vi phòng ban của anh/chị."
                )
            task = Task(
                task_code=request.POST.get("task_code"),
                task_name=request.POST.get("task_name"),
                description=request.POST.get("description", ""),
                assigned_by_employee=employee,
                assigned_to_employee=assignee,
                department_id=request.POST.get("department") or None,
                priority=request.POST.get("priority", "Normal"),
                start_date=request.POST.get("start_date") or timezone.localdate(),
                due_date=request.POST.get("due_date") or None,
                created_by=request.user,
            )
            task.full_clean()
            task.save()
            notify(
                task.assigned_to_employee, "task",
                "Bạn được giao công việc mới",
                f"{task.task_name} — hạn {task.due_date or 'chưa xác định'}.",
                link=f"/portal/tasks/{task.pk}/", created_by=request.user,
            )
            messages.success(request, "Đã giao việc thành công.")
            return redirect("portal:task_list")
        except Exception as e:
            _friendly_error(request, e, "Không thể tạo công việc.")

    return render(request, "portal/task_create.html", {
        "candidates": candidates,
        "today": timezone.localdate(),
    })


def _can_score_kpi(request):
    return has_permission(request.user, "score_kpi")


@login_required
def kpi_my_list(request):
    employee = _get_employee(request)
    results = EmployeeKPI.objects.filter(employee=employee).select_related(
        "kpi_template", "kpi_period"
    ).order_by("-kpi_period__year", "-kpi_period__month") if employee else []
    return render(request, "portal/kpi_my_list.html", {
        "results": results, "can_score_kpi": _can_score_kpi(request),
    })


@login_required
def kpi_score_list(request):
    if not _can_score_kpi(request):
        messages.error(request, "Anh/chị không có quyền chấm điểm KPI.")
        return redirect("portal:dashboard")

    qs = EmployeeKPI.objects.select_related("employee", "kpi_template", "kpi_period")
    role_code = _role_code(request)
    if not request.user.is_superuser and role_code == "DEPT_MANAGER":
        employee = _get_employee(request)
        if not employee:
            qs = qs.none()
        else:
            dept_ids = employee.managed_departments.values_list("pk", flat=True)
            qs = qs.filter(employee__department_id__in=dept_ids)

    period_id = request.GET.get("period")
    if period_id:
        qs = qs.filter(kpi_period_id=period_id)

    return render(request, "portal/kpi_score_list.html", {
        "results": qs.order_by("employee__full_name"),
        "periods": KPIPeriod.objects.all().order_by("-year", "-month"),
        "selected_period": period_id,
    })


@login_required
@require_POST
def kpi_score_update(request, pk):
    if not _can_score_kpi(request):
        messages.error(request, "Anh/chị không có quyền chấm điểm KPI.")
        return redirect("portal:dashboard")

    result = get_object_or_404(EmployeeKPI, pk=pk)
    actual = request.POST.get("actual")
    try:
        result.actual = Decimal(actual) if actual not in (None, "") else None
        result.modified_by = request.user
        result.save()
        notify(
            result.employee, "kpi", "KPI của bạn vừa được chấm điểm",
            f"{result.kpi_template} - kỳ {result.kpi_period}: đạt {result.actual}.",
            link="/portal/kpi/", created_by=request.user,
        )
        messages.success(request, f"Đã cập nhật KPI cho {result.employee}.")
    except InvalidOperation:
        messages.error(request, "Giá trị 'Thực tế' không hợp lệ, vui lòng nhập số.")
    except Exception as e:
        _friendly_error(request, e, "Không thể cập nhật.")
    return redirect("portal:kpi_score_list")


@login_required
def kpi_assign_create(request):
    """Tạo chỉ tiêu KPI cho 1 nhân viên trong 1 kỳ — dành cho HR/Trưởng phòng."""
    if not _can_score_kpi(request):
        messages.error(request, "Anh/chị không có quyền tạo chỉ tiêu KPI.")
        return redirect("portal:dashboard")

    employee = _get_employee(request)
    role_code = _role_code(request)
    if not request.user.is_superuser and role_code == "DEPT_MANAGER" and employee:
        dept_ids = employee.managed_departments.values_list("pk", flat=True)
        candidates = Employee.objects.filter(department_id__in=dept_ids)
    else:
        candidates = Employee.objects.all()

    if request.method == "POST":
        try:
            kpi_result = EmployeeKPI(
                employee_id=request.POST.get("employee"),
                kpi_template_id=request.POST.get("kpi_template"),
                kpi_period_id=request.POST.get("kpi_period"),
                target=request.POST.get("target") or 0,
                created_by=request.user,
            )
            kpi_result.full_clean()
            kpi_result.save()
            notify(
                kpi_result.employee, "kpi", "Bạn có chỉ tiêu KPI mới",
                f"{kpi_result.kpi_template} - kỳ {kpi_result.kpi_period}: mục tiêu {kpi_result.target}.",
                link="/portal/kpi/", created_by=request.user,
            )
            messages.success(request, "Đã tạo chỉ tiêu KPI.")
            return redirect("portal:kpi_score_list")
        except Exception as e:
            _friendly_error(request, e, "Không thể tạo.")

    return render(request, "portal/kpi_assign_create.html", {
        "candidates": candidates,
        "templates": KPITemplate.objects.all(),
        "periods": KPIPeriod.objects.all().order_by("-year", "-month"),
    })


@login_required
def notification_list(request):
    employee = _get_employee(request)
    items = []
    if employee:
        items = Notification.objects.filter(employee=employee).prefetch_related(
            Prefetch(
                "email_outbox_entries",
                queryset=NotificationEmailOutbox.objects.filter(status__in=("Draft", "Sent")),
                to_attr="email_drafts",
            )
        )
        Notification.objects.filter(employee=employee, is_read=False).update(is_read=True)
    return render(request, "portal/notification_list.html", {"items": items})


@login_required
@require_POST
def notification_email_outbox_mark_sent(request, pk):
    employee = _get_employee(request)
    with transaction.atomic():
        outbox = get_object_or_404(NotificationEmailOutbox.objects.select_for_update(), pk=pk)
        if not has_permission(request.user, "manage_hr") and (
            not employee or outbox.notification.employee_id != employee.pk
        ):
            return HttpResponseForbidden("Không có quyền xác nhận gửi email này.")
        if outbox.status == "Sent":
            messages.info(request, "Email này đã được xác nhận gửi trước đó.")
            return redirect("portal:notification_list")
        if outbox.status != "Draft":
            messages.error(request, "Chỉ có thể xác nhận email đang ở trạng thái nháp Outlook.")
            return redirect("portal:notification_list")
        outbox.status = "Sent"
        outbox.sent_by = request.user
        outbox.sent_at = timezone.now()
        outbox.save(update_fields=("status", "sent_by", "sent_at", "modified_date"))
    messages.success(request, "Đã ghi nhận anh/chị gửi thư qua Outlook.")
    return redirect("portal:notification_list")
