import datetime
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.views.decorators.http import require_POST
from apps.security.permissions import has_permission
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from apps.attendance.models import Attendance
from apps.leave.models import LeaveApproval, LeaveRequest, LeaveType
from apps.notification.services import notify, notify_with_email_draft
from decimal import Decimal
import calendar as calendar_module
from apps.project.models import Project
from apps.attendance.models import (
    Holiday,
    MonthlyAttendanceSummary,
    TimesheetEntry,
    WorkingCalendar,
)
from apps.leave.models import LeaveBalance
from apps.attendance.models import ProjectTimeAllocation
from apps.common.params import parse_int
from django.utils import timezone
from apps.hrm.models import Employee
from .common import _friendly_error, _get_employee, _role_code




def _can_approve(request):
    return has_permission(request.user, "approve_leave")


def _leave_approvers_for(employee):
    """Những nhân viên có quyền duyệt đơn nghỉ phép của `employee` (HR/Director toàn Trung tâm + Trưởng phòng của họ)."""
    q = models.Q(user_account__role__role_code__in=["HR_MANAGER", "DIRECTOR"])
    if employee.department_id:
        q |= models.Q(managed_departments=employee.department_id)
    return Employee.objects.filter(q).distinct()


def _approvable_leave_requests(request):
    """Compatibility wrapper; approval GET/POST and dashboard share this selector."""
    from apps.portal.selectors import approvable_leave_requests
    return approvable_leave_requests(request.user)


@login_required
def attendance_list(request):
    employee = _get_employee(request)
    records = Attendance.objects.filter(employee=employee).order_by("-attendance_date")[:31] if employee else []
    return render(request, "portal/attendance_list.html", {"records": records})


def _leave_balance(employee, year=None):
    """Số dư phép năm và nghỉ bù của nhân viên trong năm."""
    if not employee:
        return None
    year = year or timezone.localdate().year
    balance = LeaveBalance.objects.filter(employee=employee, year=year).first()
    if balance is None:
        balance = LeaveBalance(employee=employee, year=year)
    return balance


@login_required
def leave_list(request):
    employee = _get_employee(request)
    requests_qs = LeaveRequest.objects.filter(employee=employee).select_related("leave_type").order_by("-from_date") if employee else []
    return render(request, "portal/leave_list.html", {
        "requests": requests_qs,
        "balance": _leave_balance(employee),
        "current_year": timezone.localdate().year,
    })


@login_required
def leave_create(request):
    employee = _get_employee(request)
    if not employee:
        messages.error(request, "Tài khoản chưa gắn hồ sơ nhân viên, không thể tạo đơn.")
        return redirect("portal:leave_list")

    leave_types = LeaveType.objects.all()
    if request.method == "POST":
        leave_type_id = request.POST.get("leave_type")
        from_date = request.POST.get("from_date")
        to_date = request.POST.get("to_date")
        reason = request.POST.get("reason", "")
        try:
            with transaction.atomic():
                # Serialize submissions for one employee, including the case where a
                # LeaveBalance row has not been created yet.
                employee = Employee.objects.select_for_update().get(pk=employee.pk)
                leave_request = LeaveRequest(
                    employee=employee,
                    leave_type_id=leave_type_id,
                    from_date=from_date,
                    to_date=to_date,
                    reason=reason,
                    created_by=request.user,
                )
                leave_request.full_clean()
                leave_request.save()
                for approver in _leave_approvers_for(employee):
                    notify(
                        approver, "leave", "Có đơn nghỉ phép chờ duyệt",
                        f"{employee.full_name} xin nghỉ {leave_request.from_date} - {leave_request.to_date}.",
                        link="/portal/leave/approvals/", created_by=request.user,
                    )
            messages.success(request, "Đã gửi đơn xin nghỉ phép, chờ phê duyệt.")
            return redirect("portal:leave_list")
        except Exception as e:
            _friendly_error(request, e, "Không thể tạo đơn.")

    return render(request, "portal/leave_create.html", {
        "leave_types": leave_types,
        "balance": _leave_balance(employee),
        "current_year": timezone.localdate().year,
    })


@login_required
def leave_approval_list(request):
    """Danh sách đơn chờ duyệt — chỉ Trưởng phòng/HR Manager/Director/Superuser vào được."""
    if not _can_approve(request):
        messages.error(request, "Anh/chị không có quyền duyệt đơn nghỉ phép.")
        return redirect("portal:dashboard")

    qs = _approvable_leave_requests(request)

    return render(request, "portal/leave_approval_list.html", {"requests": qs.order_by("from_date")})


@login_required
@require_POST
def leave_approve(request, pk):
    if not _can_approve(request):
        messages.error(request, "Anh/chị không có quyền duyệt đơn nghỉ phép.")
        return redirect("portal:dashboard")

    decision = request.POST.get("decision")
    if decision not in ("Approved", "Rejected"):
        messages.error(request, "Yêu cầu không hợp lệ.")
        return redirect("portal:leave_approval_list")

    approver = _get_employee(request)
    if not approver:
        messages.error(request, "Tài khoản của anh/chị chưa gắn hồ sơ nhân viên, không thể duyệt.")
        return redirect("portal:leave_approval_list")

    # I12 (đã sửa): bọc transaction.atomic() + select_for_update() ngay trên chính đơn nghỉ
    # đang duyệt — trước đây get_object_or_404 lấy đơn từ _approvable_leave_requests() (filter
    # status="Pending") KHÔNG khóa dòng, nên 2 request duyệt gửi gần như đồng thời đều có thể
    # đọc được status="Pending" trước khi bên kia kịp lưu → tạo 2 dòng LeaveApproval trùng cho
    # cùng 1 đơn, status cuối cùng phụ thuộc thứ tự save (race condition).
    with transaction.atomic():
        leave_request = get_object_or_404(
            _approvable_leave_requests(request).select_for_update(), pk=pk
        )

        # I2 (đã sửa): trước đây không có bước nào chặn người duyệt tự duyệt đơn nghỉ của
        # chính mình — Trưởng phòng (DEPT_MANAGER) vốn nằm trong phạm vi _approvable_leave_requests
        # của chính phòng mình nên tự duyệt được đơn của bản thân. HR_MANAGER/DIRECTOR (có quyền
        # approve_leave_all_departments) vẫn được duyệt đơn của mình vì không còn ai cấp trên hơn
        # để duyệt thay — chỉ chặn khi người duyệt là DEPT_MANAGER duyệt đơn của chính mình.
        if leave_request.employee_id == approver.pk and _role_code(request) == "DEPT_MANAGER":
            messages.error(request, "Anh/chị không thể tự duyệt đơn nghỉ phép của chính mình.")
            return redirect("portal:leave_approval_list")

        leave_request.status = decision
        leave_request.modified_by = request.user
        leave_request.save()
        LeaveApproval.objects.create(
            leave_request=leave_request,
            approver=approver,
            decision=decision,
            created_by=request.user,
        )
        label = "Đã duyệt" if decision == "Approved" else "Đã từ chối"
        notify_with_email_draft(
            leave_request.employee,
            "leave",
            f"Đơn nghỉ phép {label.lower()}",
            f"Đơn nghỉ {leave_request.from_date} - {leave_request.to_date} của bạn {label.lower()}.",
            link="/portal/leave/",
            email_subject="IHRMS: Có cập nhật về đơn nghỉ phép của bạn",
            email_body=(
                "Anh/chị có cập nhật mới về yêu cầu nghỉ phép trong IHRMS. "
                "Vui lòng đăng nhập cổng nhân viên để xem trạng thái và chi tiết."
            ),
            created_by=request.user,
            idempotency_key=f"leave-decision:{leave_request.pk}:{decision}",
        )
    return redirect("portal:leave_approval_list")


def _leave_days_in_month(employee, code, year, month):
    requests = LeaveRequest.objects.filter(
        employee=employee, status="Approved", leave_type__leave_type_code=code,
        from_date__lte=datetime.date(year, month, calendar_module.monthrange(year, month)[1]),
        to_date__gte=datetime.date(year, month, 1),
    )
    from apps.leave.models import leave_days_in_month
    return sum(
        (leave_days_in_month(request, year, month) for request in requests),
        Decimal("0"),
    )


def _weekday_count(year, month):
    """Số ngày Thứ 2 - Thứ 6 trong tháng (không tính Thứ 7, Chủ nhật)."""
    days_in_month = calendar_module.monthrange(year, month)[1]
    return sum(1 for d in range(1, days_in_month + 1) if calendar_module.weekday(year, month, d) < 5)


def _holiday_weekday_count(year, month):
    """Số ngày lễ rơi vào ngày trong tuần (Thứ 2-6) của tháng — dùng để trừ vào số ngày cần làm."""
    holidays = Holiday.objects.filter(holiday_date__year=year, holiday_date__month=month, is_active=True)
    return sum(1 for h in holidays if h.holiday_date.weekday() < 5)


@login_required
def timesheet_month(request):

    employee = _get_employee(request)
    today = timezone.localdate()
    year = parse_int(request.GET.get("year"), today.year, min_value=2000, max_value=2100)
    month = parse_int(request.GET.get("month"), today.month, min_value=1, max_value=12)

    days_in_month = calendar_module.monthrange(year, month)[1]
    holidays = {h.holiday_date.day: h for h in Holiday.objects.filter(
        holiday_date__year=year, holiday_date__month=month, is_active=True
    )}
    entries = TimesheetEntry.objects.filter(
        employee=employee, work_date__year=year, work_date__month=month
    ).select_related("project") if employee else []
    entries_by_day = {}
    for e in entries:
        entries_by_day.setdefault(e.work_date.day, []).append(e)

    # Dựng đủ các dòng trong tháng, phân loại: cuối tuần / ngày lễ / ngày làm việc
    day_rows = []
    for d in range(1, days_in_month + 1):
        weekday = calendar_module.weekday(year, month, d)
        is_weekend = weekday >= 5
        holiday = holidays.get(d)
        day_rows.append({
            "day": d,
            "date": f"{year}-{month:02d}-{d:02d}",
            "is_weekend": is_weekend,
            "holiday": holiday,
            "entries": entries_by_day.get(d, []),
            "day_total": sum((e.hours for e in entries_by_day.get(d, [])), Decimal("0")),
        })

    total_hours = sum((e.hours for e in entries), Decimal("0"))

    summary, _ = (
        MonthlyAttendanceSummary.objects.get_or_create(employee=employee, year=year, month=month)
        if employee else (None, False)
    )

    base_days = _weekday_count(year, month) - _holiday_weekday_count(year, month)
    working_calendar = WorkingCalendar.objects.filter(calendar_year=year).first()
    hours_per_day = working_calendar.working_hours_per_day if working_calendar else Decimal("8")
    leave_total = (
        summary.total_leave_days
        if summary and summary.status == MonthlyAttendanceSummary.STATUS_APPROVED
        else Decimal("0")
    )
    required_days = Decimal(base_days) - leave_total
    required_hours = required_days * hours_per_day

    from apps.attendance.models import ProjectTimeAllocation
    projects_used = {e.project for e in entries if e.project}
    allocations = list(ProjectTimeAllocation.objects.filter(
        employee=employee, year=year, month=month, project__in=projects_used
    ).select_related("project")) if employee else []
    # Nếu chỉ làm 1 dự án và chưa có cấu hình % -> mặc định 100%
    if len(projects_used) == 1 and not allocations:
        only_project = list(projects_used)[0]
        allocations = [ProjectTimeAllocation(employee=employee, project=only_project, year=year, month=month, allocation_percent=100)]
    diff_hours = total_hours - required_hours

    balance = LeaveBalance.objects.filter(employee=employee, year=year).first() if employee else None

    context = {
        "day_rows": day_rows, "year": year, "month": month,
        "total_hours": total_hours,
        "base_days": base_days, "hours_per_day": hours_per_day,
        "required_days": required_days, "required_hours": required_hours,
        "approved_leave_total": leave_total,
        "allocations": allocations, "diff_hours": diff_hours,
        "summary": summary, "balance": balance,
        "projects": Project.objects.filter(is_active=True),
        "months": range(1, 13), "years": range(today.year - 1, today.year + 2),
    }
    return render(request, "portal/timesheet_month.html", context)


@login_required
@require_POST
def timesheet_entry_create(request):
    employee = _get_employee(request)
    if not employee:
        messages.error(request, "Tài khoản chưa gắn hồ sơ nhân viên.")
        return redirect("portal:timesheet_month")

    work_date = request.POST.get("work_date", "")
    try:
        entry = TimesheetEntry(
            employee=employee,
            work_date=work_date,
            project_id=request.POST.get("project") or None,
            task_description=request.POST.get("task_description", ""),
            hours=request.POST.get("hours") or 0,
            created_by=request.user,
        )
        entry.full_clean()
        entry.save()
        messages.success(request, "Đã ghi nhận giờ làm việc.")
    except Exception as e:
        _friendly_error(request, e, "Không thể lưu.")

    try:
        parsed_date = datetime.date.fromisoformat(work_date)
    except (ValueError, TypeError):
        parsed_date = None
    if parsed_date:
        return redirect(f"/portal/timesheet/?year={parsed_date.year}&month={parsed_date.month}")
    return redirect("portal:timesheet_month")


@login_required
@require_POST
def timesheet_entry_delete(request, pk):
    employee = _get_employee(request)
    entry = get_object_or_404(TimesheetEntry, pk=pk, employee=employee)
    year, month = entry.work_date.year, entry.work_date.month
    try:
        entry.delete(user=request.user)
        messages.success(request, "Đã xóa dòng chấm công.")
    except Exception as error:
        _friendly_error(request, error, "Không thể xóa dòng chấm công.")
    return redirect(f"/portal/timesheet/?year={year}&month={month}")


@login_required
@require_POST
def timesheet_summary_update(request):

    employee = _get_employee(request)
    today = timezone.localdate()
    year = parse_int(request.POST.get("year"), today.year, min_value=2000, max_value=2100)
    month = parse_int(request.POST.get("month"), today.month, min_value=1, max_value=12)
    if not employee:
        messages.error(request, "Tài khoản chưa gắn hồ sơ nhân viên.")
        return redirect("portal:timesheet_month")

    try:
        with transaction.atomic():
            from apps.payroll.models import PayrollPeriod
            list(PayrollPeriod.objects.select_for_update().filter(payroll_year=year, payroll_month=month).values_list("pk", flat=True))
            list(Employee.objects.select_for_update().filter(pk=employee.pk).values_list("pk", flat=True))
            summary, _ = MonthlyAttendanceSummary.objects.select_for_update().get_or_create(employee=employee, year=year, month=month)
            if summary.status != "Pending":
                raise ValidationError("Bảng tổng hợp đã duyệt; không thể tự sửa hoặc mở lại.")
            summary.sick_days = request.POST.get("sick_days") or 0
            summary.maternity_days = request.POST.get("maternity_days") or 0
            summary.compensatory_days = request.POST.get("compensatory_days") or 0
            summary.annual_leave_days = request.POST.get("annual_leave_days") or 0
            summary.unpaid_leave_days = request.POST.get("unpaid_leave_days") or 0
            summary.status = MonthlyAttendanceSummary.STATUS_PENDING
            summary.approved_by = None
            summary.approved_at = None
            summary.modified_by = request.user
            summary.full_clean()
            summary.save()
            messages.success(request, "Đã cập nhật số ngày nghỉ trong tháng — đang chờ quản lý duyệt.")
    except Exception as e:
        _friendly_error(request, e, "Không thể lưu.")

    return redirect(f"/portal/timesheet/?year={year}&month={month}")


def _can_approve_timesheet(request):
    return has_permission(request.user, "approve_timesheet")


def _approvable_timesheet_summaries(request):
    """Các bảng tổng hợp chấm công tháng (trạng thái Chờ duyệt) mà tài khoản đang đăng nhập
    thực sự có quyền duyệt — cùng cách phạm vi với `_approvable_leave_requests`."""
    qs = MonthlyAttendanceSummary.objects.filter(
        status=MonthlyAttendanceSummary.STATUS_PENDING
    ).select_related("employee", "employee__department")
    if has_permission(request.user, "approve_timesheet_all_departments"):
        return qs
    if _role_code(request) == "DEPT_MANAGER":
        employee = _get_employee(request)
        if not employee:
            return qs.none()
        dept_ids = employee.managed_departments.values_list("pk", flat=True)
        return qs.filter(employee__department_id__in=dept_ids)
    return qs.none()


@login_required
def timesheet_approval_list(request):
    if not _can_approve_timesheet(request):
        messages.error(request, "Anh/chị không có quyền duyệt bảng chấm công.")
        return redirect("portal:dashboard")
    qs = _approvable_timesheet_summaries(request)
    return render(request, "portal/timesheet_approval_list.html", {
        "summaries": qs.order_by("-year", "-month", "employee__full_name"),
    })


@login_required
@require_POST
def timesheet_summary_approve(request, pk):
    if not _can_approve_timesheet(request):
        messages.error(request, "Anh/chị không có quyền duyệt bảng chấm công.")
        return redirect("portal:dashboard")

    with transaction.atomic():
        target = get_object_or_404(_approvable_timesheet_summaries(request), pk=pk)
        from apps.payroll.models import PayrollPeriod
        list(PayrollPeriod.objects.select_for_update().filter(payroll_year=target.year, payroll_month=target.month).values_list("pk", flat=True))
        list(Employee.objects.select_for_update().filter(pk=target.employee_id).values_list("pk", flat=True))
        summary = get_object_or_404(
            _approvable_timesheet_summaries(request).select_for_update(), pk=pk,
        )
        summary.status = MonthlyAttendanceSummary.STATUS_APPROVED
        summary.approved_by = request.user
        summary.approved_at = timezone.now()
        summary.save()
    notify(
        summary.employee, "attendance", "Bảng chấm công tháng đã được duyệt",
        f"Tổng hợp chấm công {summary.month}/{summary.year} của bạn đã được duyệt.",
        link="/portal/timesheet/", created_by=request.user,
    )
    messages.success(request, "Đã duyệt bảng tổng hợp chấm công.")
    return redirect("portal:timesheet_approval_list")


def _can_manage_calendar(request):
    return has_permission(request.user, "manage_calendar")


@login_required
def holiday_list(request):
    if not _can_manage_calendar(request):
        messages.error(request, "Anh/chị không có quyền quản lý ngày lễ.")
        return redirect("portal:dashboard")

    if request.method == "POST":
        try:
            holiday = Holiday(
                holiday_code=request.POST.get("holiday_code"),
                holiday_name=request.POST.get("holiday_name"),
                holiday_date=request.POST.get("holiday_date"),
                created_by=request.user,
            )
            holiday.full_clean()
            holiday.save()
            messages.success(request, "Đã thêm ngày lễ.")
        except Exception as e:
            _friendly_error(request, e, "Không thể thêm.")
        return redirect("portal:holiday_list")

    return render(request, "portal/holiday_list.html", {
        "holidays": Holiday.objects.filter(is_active=True).order_by("holiday_date"),
    })


@login_required
@require_POST
def holiday_delete(request, pk):
    if not _can_manage_calendar(request):
        messages.error(request, "Anh/chị không có quyền quản lý ngày lễ.")
        return redirect("portal:dashboard")
    holiday = get_object_or_404(Holiday, pk=pk)
    holiday.is_active = False
    holiday.save(update_fields=["is_active"])
    messages.success(request, "Đã xóa ngày lễ.")
    return redirect("portal:holiday_list")

