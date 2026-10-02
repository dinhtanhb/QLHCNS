import datetime
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.views.decorators.http import require_POST
from apps.security.permissions import has_permission
from django.db.models import Count, Prefetch, Q
from apps.activity.permissions import visible_activities_for
from apps.hrm.models import EmployeeProfileChangeRequest
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from apps.leave.models import LeaveRequest
from apps.notification.services import notify
import calendar as calendar_module
from django.http import FileResponse, Http404, HttpResponse, HttpResponseForbidden
from apps.payroll.models import Payroll
from apps.asset.models import Asset
from django.utils import timezone
from apps.hrm.models import Employee
from apps.task.models import Task
from apps.document.models import Document
from apps.recruitment.models import RecruitmentRequest
from .common import _get_employee, _role_code




def service_worker(request):
    """Serve the portal-only worker with its scope explicitly limited to /portal/."""
    worker_path = settings.BASE_DIR / "static" / "js" / "service-worker.js"
    try:
        worker_source = worker_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise Http404("Service worker file not found") from exc

    response = HttpResponse(worker_source, content_type="application/javascript; charset=utf-8")
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Service-Worker-Allowed"] = "/portal/"
    return response


@login_required
def dashboard(request):
    employee = _get_employee(request)
    role_code = _role_code(request)
    is_super = request.user.is_superuser
    context = {"employee": employee}

    if has_permission(request.user, "view_own_lifecycle_items"):
        from apps.lifecycle.models import LifecycleChecklistItem
        overdue_items = LifecycleChecklistItem.objects.filter(
            case__status="Open", status="Pending", due_date__lt=timezone.localdate()
        )
        if has_permission(request.user, "manage_lifecycle_case"):
            context["lifecycle_overdue_count"] = overdue_items.count()
        elif employee:
            context["lifecycle_overdue_count"] = overdue_items.filter(assigned_to_user=request.user).count()
        else:
            context["lifecycle_overdue_count"] = 0

    # Shared homepage: show the current month's project activity progress only
    # to roles that can open the activity dashboard. The scoped queryset keeps
    # department managers within their own departments.
    if has_permission(request.user, "view_activity_dashboard"):
        today = timezone.localdate()
        month_start = datetime.date(today.year, today.month, 1)
        month_end = datetime.date(
            today.year, today.month,
            calendar_module.monthrange(today.year, today.month)[1],
        )
        task_prefetch = Prefetch(
            "tasks",
            queryset=Task.objects.order_by("created_date"),
            to_attr="dashboard_tracking_tasks",
        )
        activities = visible_activities_for(request.user).filter(
            Q(start_date__lte=month_end, end_date__gte=month_start)
            | Q(tasks__due_date__gte=month_start, tasks__due_date__lte=month_end)
        ).exclude(status="Cancelled").prefetch_related(task_prefetch).distinct()

        activity_rows = []
        for activity in activities:
            task = activity.dashboard_tracking_tasks[0] if activity.dashboard_tracking_tasks else None
            overdue = bool(
                task and task.status not in ("Done", "Cancelled")
                and task.due_date and task.due_date < today
            )
            activity_rows.append((task, overdue))
        tracked_tasks = [task for task, _ in activity_rows if task]
        context.update({
            "show_project_activity_summary": True,
            "activity_month": month_start.strftime("%Y-%m"),
            "activity_month_label": month_start.strftime("%m/%Y"),
            "activity_total": len(activity_rows),
            "activity_completed": sum(task.status == "Done" for task in tracked_tasks),
            "activity_overdue": sum(overdue for _, overdue in activity_rows),
            "activity_report_missing": sum(
                task.status != "Cancelled" and not task.report_file
                for task in tracked_tasks
            ),
            "activity_without_task": sum(task is None for task, _ in activity_rows),
        })

    # Nhân viên thường: các con số cá nhân
    if employee:
        context["my_pending_leaves"] = LeaveRequest.objects.filter(employee=employee, status="Pending").count()
        context["my_open_tasks"] = Task.objects.filter(assigned_to_employee=employee).exclude(status__in=["Done", "Cancelled"]).count()
        # Mục I8: chỉ hiện lương của kỳ đã "Locked" (đã chốt). Kỳ còn "Open" là số
        # Kế toán đang tính/sửa, show ra cho nhân viên sẽ gây hoang mang khi số đổi qua lại.
        latest_payroll = Payroll.objects.filter(
            employee=employee, payroll_period__status="Locked"
        ).select_related("payroll_period").order_by(
            "-payroll_period__payroll_year", "-payroll_period__payroll_month"
        ).first()
        context["latest_payroll"] = latest_payroll

    # HR Manager / Director / Super Admin: bức tranh toàn công ty
    if is_super or role_code in ("HR_MANAGER", "DIRECTOR"):
        context["is_management_view"] = True
        context["total_employees"] = Employee.objects.filter(employment_status="Active").count()
        context["pending_leave_approvals"] = LeaveRequest.objects.filter(status="Pending").count()
        context["pending_recruitment"] = RecruitmentRequest.objects.filter(status="Pending").count()
        context["pending_documents"] = Document.objects.filter(status="PendingApproval").count()
        context["open_tasks_company"] = Task.objects.exclude(status__in=["Done", "Cancelled"]).count()
        if has_permission(request.user, "view_asset"):
            context["assets_in_use"] = Asset.objects.filter(status="InUse").count()
        dept_counts = (
            Employee.objects.filter(employment_status="Active")
            .values("department__department_name")
            .annotate(total=Count("id"))
            .order_by("-total")
        )
        context["dept_counts"] = dept_counts

    # Trưởng phòng: bức tranh phòng ban mình quản lý
    elif role_code == "DEPT_MANAGER" and employee:
        dept_ids = employee.managed_departments.values_list("pk", flat=True)
        context["is_manager_view"] = True
        context["dept_employee_count"] = Employee.objects.filter(department_id__in=dept_ids, employment_status="Active").count()
        context["dept_pending_leaves"] = LeaveRequest.objects.filter(
            employee__department_id__in=dept_ids, status="Pending"
        ).count()
        context["dept_open_tasks"] = Task.objects.filter(
            department_id__in=dept_ids
        ).exclude(status__in=["Done", "Cancelled"]).count()
        if has_permission(request.user, "view_asset"):
            context["dept_assets_in_use"] = Asset.objects.filter(
                allocations__employee__department_id__in=dept_ids, allocations__return_date__isnull=True
            ).distinct().count()

    return render(request, "portal/dashboard.html", context)


@login_required
def profile(request):
    employee = _get_employee(request)
    context = {"employee": employee}
    if employee:
        context.update({
            "transfers": employee.transfers.select_related("from_department", "to_department"),
            "promotions": employee.promotions.select_related("old_position", "new_position"),
            "rewards": employee.rewards.all(),
            "disciplines": employee.disciplines.all(),
            "current_salary": employee.salaries.filter(status="Active").order_by("-effective_date").first(),
            "current_contract": employee.contracts.order_by("-start_date").first(),
        })
    return render(request, "portal/profile.html", context)


@login_required
def org_chart(request):
    employees = list(
        Employee.objects.filter(employment_status="Active")
        .select_related("department", "position")
        .only("id", "full_name", "employee_code", "department__department_name",
              "position__position_name", "manager_id")
        .order_by("full_name", "id")
    )
    nodes = {employee.pk: {"employee": employee, "children": [], "manager": None} for employee in employees}
    parents = {employee.pk: employee.manager_id for employee in employees}
    roots = []
    # Break any pre-existing manager cycle deterministically by making the
    # employee whose manager edge closes the cycle a root.
    for employee in employees:
        parent_id = parents[employee.pk]
        if parent_id not in nodes:
            roots.append(nodes[employee.pk])
            continue
        cursor, visited = parent_id, {employee.pk}
        while cursor in nodes and cursor not in visited:
            visited.add(cursor)
            cursor = parents.get(cursor)
        if cursor in visited:
            roots.append(nodes[employee.pk])
        else:
            nodes[employee.pk]["manager"] = nodes[parent_id]["employee"]
            nodes[parent_id]["children"].append(nodes[employee.pk])
    return render(request, "portal/org_chart.html", {
        "roots": roots,
        "employee_count": len(employees),
        "department_count": len({employee.department_id for employee in employees if employee.department_id}),
    })


@login_required
def profile_change_request_list(request):
    if not has_permission(request.user, "submit_profile_change_request"):
        return HttpResponseForbidden()
    employee = _get_employee(request)
    if not employee:
        return HttpResponseForbidden("Tài khoản chưa được gắn hồ sơ nhân viên.")
    requests_qs = EmployeeProfileChangeRequest.objects.select_related("employee", "decided_by")
    if has_permission(request.user, "approve_profile_change_request"):
        pending = requests_qs.filter(status="Pending")
        own = requests_qs.filter(employee=employee).exclude(status="Pending")
        items = list(pending) + list(own)
    else:
        items = requests_qs.filter(employee=employee)
    return render(request, "portal/profile_change_request_list.html", {"items": items})


@login_required
def profile_change_request_create(request):
    if not has_permission(request.user, "submit_profile_change_request"):
        return HttpResponseForbidden()
    employee = _get_employee(request)
    if not employee:
        return HttpResponseForbidden("Tài khoản chưa được gắn hồ sơ nhân viên.")
    if request.method == "POST":
        field_name = request.POST.get("field_name", "")
        if field_name not in EmployeeProfileChangeRequest.ALLOWED_FIELDS:
            return HttpResponseForbidden("Trường hồ sơ không được phép cập nhật.")
        new_value = request.POST.get("new_value", "").strip()
        if field_name == "mobile_phone" and not new_value:
            messages.error(request, "Số điện thoại không được để trống.")
            return redirect("portal:profile_change_request_create")
        item = EmployeeProfileChangeRequest(
            employee=employee,
            field_name=field_name,
            old_value=str(getattr(employee, field_name) or ""),
            submitted_snapshot=str(getattr(employee, field_name) or ""),
            new_value=new_value,
            reason=request.POST.get("reason", "").strip(),
            attachment=request.FILES.get("attachment"),
            created_by=request.user,
        )
        try:
            item.full_clean()
            item.save()
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
            return redirect("portal:profile_change_request_create")
        messages.success(request, "Đã gửi yêu cầu cập nhật hồ sơ đến Nhân sự.")
        return redirect("portal:profile_change_request_list")
    return render(request, "portal/profile_change_request_form.html", {"employee": employee})


@login_required
@require_POST
def profile_change_request_decide(request, pk):
    if not has_permission(request.user, "approve_profile_change_request"):
        return HttpResponseForbidden()
    decision = request.POST.get("decision")
    status = {"approve": "Approved", "reject": "Rejected", "more_info": "NeedsMoreInfo"}.get(decision)
    if not status:
        return HttpResponseForbidden("Quyết định không hợp lệ.")
    with transaction.atomic():
        try:
            item = EmployeeProfileChangeRequest.objects.select_for_update().select_related("employee").get(
                pk=pk, status="Pending"
            )
        except EmployeeProfileChangeRequest.DoesNotExist:
            raise Http404
        employee = Employee.objects.select_for_update().get(pk=item.employee_id)
        if str(getattr(employee, item.field_name) or "") != item.submitted_snapshot:
            messages.error(request, "Giá trị hồ sơ đã thay đổi sau khi gửi. Không thể duyệt yêu cầu cũ; vui lòng yêu cầu nhân viên gửi lại.")
            return redirect("portal:profile_change_request_list")
        if status == "Approved":
            setattr(employee, item.field_name, item.new_value)
            employee.modified_by = request.user
            employee.save(update_fields=[item.field_name, "modified_by", "modified_date"])
        item.status = status
        item.decided_by = request.user
        item.decided_at = timezone.now()
        item.decision_note = request.POST.get("note", "").strip()[:500]
        item.modified_by = request.user
        item.save(update_fields=["status", "decided_by", "decided_at", "decision_note", "modified_by", "modified_date"])
        labels = {"Approved": "đã được duyệt", "Rejected": "bị từ chối", "NeedsMoreInfo": "cần bổ sung thông tin"}
        notify(employee, "profile-change", "Yêu cầu cập nhật hồ sơ đã được xử lý",
               f"Yêu cầu thay đổi hồ sơ của bạn {labels[status]}. Vui lòng xem chi tiết trong IHRMS.",
               link="/portal/profile/requests/", created_by=request.user)
    messages.success(request, "Đã ghi nhận quyết định xử lý yêu cầu.")
    return redirect("portal:profile_change_request_list")


@login_required
def profile_change_request_attachment(request, pk):
    employee = _get_employee(request)
    if not (employee and has_permission(request.user, "approve_profile_change_request")):
        if not employee:
            return HttpResponseForbidden()
        item = get_object_or_404(EmployeeProfileChangeRequest, pk=pk, employee=employee)
    else:
        item = get_object_or_404(EmployeeProfileChangeRequest, pk=pk)
    if not item.attachment:
        raise Http404
    from apps.security.files import protected_file_response
    return protected_file_response(request, item.attachment, obj=item)

