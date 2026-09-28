from django.db import models
from apps.security.permissions import has_permission
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render
from apps.notification.services import notify
from decimal import Decimal
from django.db.models import Sum
from apps.attendance.models import MonthlyAttendanceSummary, TimesheetEntry, WorkingCalendar
from apps.leave.models import LeaveBalance
from apps.hrm.models import EmployeePromotion, EmployeeTransfer
from apps.planning.models import AnnualBudget, Event, HeadcountPlan, TrainingEnrollment
from apps.organization.models import Department
from apps.procurement.models import ProcurementRequest
from apps.common.params import parse_int
from django.utils import timezone
from apps.hrm.models import Employee
from .attendance import _holiday_weekday_count, _weekday_count
from .common import _friendly_error, _get_employee, _role_code




def _can_view_reports(request):
    return has_permission(request.user, "view_reports")


@login_required
def report_hub(request):
    if not _can_view_reports(request):
        messages.error(request, "Anh/chị không có quyền xem báo cáo.")
        return redirect("portal:dashboard")
    return render(request, "portal/report_hub.html")


@login_required
def report_timesheet(request):
    if not _can_view_reports(request):
        messages.error(request, "Anh/chị không có quyền xem báo cáo.")
        return redirect("portal:dashboard")

    today = timezone.now().date()
    year = parse_int(request.GET.get("year"), today.year, min_value=2000, max_value=2100)
    month = parse_int(request.GET.get("month"), today.month, min_value=1, max_value=12)

    base_days = _weekday_count(year, month) - _holiday_weekday_count(year, month)
    working_calendar = WorkingCalendar.objects.filter(calendar_year=year).first()
    hours_per_day = working_calendar.working_hours_per_day if working_calendar else Decimal("8")

    rows = []
    for emp in Employee.objects.filter(employment_status="Active").select_related("department").order_by("department__department_name", "full_name"):
        total_hours = TimesheetEntry.objects.filter(
            employee=emp, work_date__year=year, work_date__month=month
        ).aggregate(total=Sum("hours"))["total"] or Decimal("0")

        # I3 (đã sửa): báo cáo BCC cho quản lý chỉ tính theo số liệu đã được duyệt
        # (status="Approved"), không dùng thẳng số nhân viên tự khai chưa ai xác nhận.
        summary = MonthlyAttendanceSummary.objects.filter(
            employee=emp, year=year, month=month, status=MonthlyAttendanceSummary.STATUS_APPROVED,
        ).first()
        leave_total = summary.total_leave_days if summary else Decimal("0")
        required_hours = (Decimal(base_days) - leave_total) * hours_per_day
        balance = LeaveBalance.objects.filter(employee=emp, year=year).first()
        has_pending_summary = MonthlyAttendanceSummary.objects.filter(
            employee=emp, year=year, month=month, status=MonthlyAttendanceSummary.STATUS_PENDING,
        ).exists()
        rows.append({
            "employee": emp, "total_hours": total_hours, "required_hours": required_hours,
            "diff_hours": total_hours - required_hours,
            "leave_remaining": balance.remaining_days if balance else None,
            "has_pending_summary": has_pending_summary,
        })

    return render(request, "portal/report_timesheet.html", {
        "rows": rows, "year": year, "month": month,
        "months": range(1, 13), "years": range(today.year - 1, today.year + 2),
    })


@login_required
def report_personnel_changes(request):
    if not _can_view_reports(request):
        messages.error(request, "Anh/chị không có quyền xem báo cáo.")
        return redirect("portal:dashboard")

    today = timezone.now().date()
    default_from = today.replace(day=1)
    from_date = request.GET.get("from_date", default_from.isoformat())
    to_date = request.GET.get("to_date", today.isoformat())

    new_hires = Employee.objects.filter(join_date__range=[from_date, to_date]).select_related("department")
    departures = Employee.objects.filter(
        leave_date__range=[from_date, to_date], employment_status="Resigned"
    ).select_related("department")
    transfers = EmployeeTransfer.objects.filter(
        effective_date__range=[from_date, to_date]
    ).select_related("employee", "from_department", "to_department")
    promotions = EmployeePromotion.objects.filter(
        effective_date__range=[from_date, to_date]
    ).select_related("employee", "old_position", "new_position")

    return render(request, "portal/report_personnel_changes.html", {
        "new_hires": new_hires, "departures": departures,
        "transfers": transfers, "promotions": promotions,
        "from_date": from_date, "to_date": to_date,
    })


def _can_create_event(request):
    return has_permission(request.user, "create_event")


@login_required
def event_list(request):
    employee = _get_employee(request)
    today = timezone.now()
    if employee:
        dept_ids = list(employee.department_id and [employee.department_id] or [])
        events = Event.objects.filter(
            end_time__gte=today
        ).filter(models.Q(department__isnull=True) | models.Q(department_id__in=dept_ids)).order_by("start_time")
    else:
        events = Event.objects.filter(end_time__gte=today, department__isnull=True).order_by("start_time")

    if request.method == "POST":
        if not _can_create_event(request):
            messages.error(request, "Anh/chị không có quyền tạo sự kiện.")
            return redirect("portal:event_list")
        try:
            event = Event(
                title=request.POST.get("title"),
                event_type=request.POST.get("event_type", "Meeting"),
                department_id=request.POST.get("department") or None,
                start_time=request.POST.get("start_time"),
                end_time=request.POST.get("end_time"),
                location=request.POST.get("location", ""),
                description=request.POST.get("description", ""),
                created_by_employee=employee,
                created_by=request.user,
            )
            event.full_clean()
            event.save()
            if event.department_id:
                recipients = Employee.objects.filter(department_id=event.department_id, employment_status="Active")
            else:
                recipients = Employee.objects.filter(employment_status="Active")
            for emp in recipients:
                notify(
                    emp, "event", "Sự kiện mới",
                    f"{event.title} — {event.start_time:%d/%m/%Y %H:%M} tại {event.location or 'chưa rõ địa điểm'}.",
                    link="/portal/events/", created_by=request.user,
                )
            messages.success(request, "Đã tạo sự kiện.")
        except Exception as e:
            _friendly_error(request, e, "Không thể tạo.")
        return redirect("portal:event_list")

    my_departments = employee.managed_departments.all() if employee and _role_code(request) == "DEPT_MANAGER" else Department.objects.all()
    return render(request, "portal/event_list.html", {
        "events": events, "can_create_event": _can_create_event(request), "departments": my_departments,
    })


@login_required
def training_my_list(request):
    employee = _get_employee(request)
    enrollments = TrainingEnrollment.objects.filter(employee=employee).select_related("course") if employee else []
    return render(request, "portal/training_my_list.html", {"enrollments": enrollments})


@login_required
def report_headcount(request):
    if not _can_view_reports(request):
        messages.error(request, "Anh/chị không có quyền xem báo cáo.")
        return redirect("portal:dashboard")
    today = timezone.now().date()
    year = parse_int(request.GET.get("year"), today.year, min_value=2000, max_value=2100)
    plans = HeadcountPlan.objects.filter(year=year).select_related("department")
    return render(request, "portal/report_headcount.html", {
        "plans": plans, "year": year, "years": range(today.year - 1, today.year + 2),
    })


@login_required
def report_budget(request):
    if not _can_view_reports(request):
        messages.error(request, "Anh/chị không có quyền xem báo cáo.")
        return redirect("portal:dashboard")
    today = timezone.now().date()
    year = parse_int(request.GET.get("year"), today.year, min_value=2000, max_value=2100)
    budgets = AnnualBudget.objects.filter(year=year).select_related("department")

    rows = []
    for b in budgets:
        actual = Decimal("0")
        if b.category == "Procurement":
            from apps.procurement.models import ProcurementRequest
            qs = ProcurementRequest.objects.filter(request_date__year=year, status__in=["Approved", "Purchased"])
            if b.department:
                qs = qs.filter(department=b.department)
            actual = sum((pr.total_estimated_cost for pr in qs), Decimal("0"))
        elif b.category == "Training":
            from apps.planning.models import TrainingCourse
            qs = TrainingCourse.objects.filter(start_date__year=year)
            actual = sum((c.cost for c in qs), Decimal("0"))
        rows.append({"budget": b, "actual": actual, "remaining": b.allocated_amount - actual})

    return render(request, "portal/report_budget.html", {"rows": rows, "year": year, "years": range(today.year - 1, today.year + 2)})
