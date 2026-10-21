from django.db import models
from apps.security.permissions import has_permission
from apps.security.permissions import HR_MANAGER
from apps.security.data_access import managed_departments_for
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from apps.notification.services import notify
from decimal import Decimal
from django.db.models import Sum
from datetime import date
from collections import defaultdict
from django.db.models import DecimalField, ExpressionWrapper, F
from django.utils.dateparse import parse_date
from django.core.exceptions import ValidationError
from apps.attendance.models import MonthlyAttendanceSummary, TimesheetEntry, WorkingCalendar
from apps.leave.models import ANNUAL_LEAVE_CODE, LeaveBalance, LeaveRequest, leave_days_in_year
from apps.attendance.services import holiday_dates
from apps.hrm.models import EmployeePromotion, EmployeeTransfer
from apps.planning.models import AnnualBudget, Event, HeadcountPlan, TrainingEnrollment, TrainingCourse, with_headcounts
from apps.procurement.models import ProcurementItem
from apps.common.params import parse_int
from apps.common.export_names import export_name
from apps.security.models import SecurityEvent
from django.utils import timezone
from apps.hrm.models import Employee
from ..reporting_dashboard import (
    build_report_snapshot,
    export_snapshot_docx,
    export_snapshot_pptx,
    export_snapshot_xlsx,
)
from .attendance import _holiday_weekday_count, _weekday_count
from .common import _friendly_error, _get_employee, _role_code




def _can_view_reports(request):
    return has_permission(request.user, "view_reports")


@login_required
def report_hub(request):
    if not _can_view_reports(request):
        messages.error(request, "Anh/chị không có quyền xem báo cáo.")
        return redirect("portal:dashboard")
    today = timezone.localdate()
    default_from = today.replace(month=1, day=1)
    try:
        from_date = parse_date(request.GET.get("from_date", default_from.isoformat()))
        to_date = parse_date(request.GET.get("to_date", today.isoformat()))
        if not from_date or not to_date or to_date < from_date or (to_date - from_date).days > 1095:
            raise ValueError
    except ValueError:
        messages.error(request, "Khoảng ngày không hợp lệ; đã dùng từ đầu năm đến hôm nay.")
        from_date, to_date = default_from, today
    return render(request, "portal/report_hub.html", build_report_snapshot(from_date, to_date))


@login_required
def report_hub_export(request, export_format):
    if not _can_view_reports(request):
        return HttpResponse("Anh/chị không có quyền xuất báo cáo.", status=403)
    today = timezone.localdate()
    default_from = today.replace(month=1, day=1)
    try:
        from_date = parse_date(request.GET.get("from_date", default_from.isoformat()))
        to_date = parse_date(request.GET.get("to_date", today.isoformat()))
    except ValueError:
        return HttpResponse("Khoảng ngày báo cáo không hợp lệ.", status=400)
    if not from_date or not to_date or to_date < from_date or (to_date - from_date).days > 1095:
        return HttpResponse("Khoảng ngày báo cáo không hợp lệ.", status=400)
    exporters = {
        "xlsx": (export_snapshot_xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "excel"),
        "docx": (export_snapshot_docx, "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "word"),
        "pptx": (export_snapshot_pptx, "application/vnd.openxmlformats-officedocument.presentationml.presentation", "powerpoint"),
    }
    if export_format not in exporters:
        return HttpResponse("Định dạng xuất không được hỗ trợ.", status=404)
    exporter, content_type, audit_label = exporters[export_format]
    response = HttpResponse(exporter(build_report_snapshot(from_date, to_date)), content_type=content_type)
    filename = export_name("BaoCao_DieuHanh_IHRMS", f"{from_date:%Y%m%d}-{to_date:%Y%m%d}", today, export_format)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    SecurityEvent.objects.create(user=request.user, action="data_export", resource=f"report_hub_{audit_label}")
    return response


@login_required
def report_timesheet(request):
    if not _can_view_reports(request):
        messages.error(request, "Anh/chị không có quyền xem báo cáo.")
        return redirect("portal:dashboard")

    today = timezone.localdate()
    year = parse_int(request.GET.get("year"), today.year, min_value=2000, max_value=2100)
    month = parse_int(request.GET.get("month"), today.month, min_value=1, max_value=12)

    base_days = _weekday_count(year, month) - _holiday_weekday_count(year, month)
    working_calendar = WorkingCalendar.objects.filter(calendar_year=year).first()
    hours_per_day = working_calendar.working_hours_per_day if working_calendar else Decimal("8")

    employees = list(Employee.objects.filter(employment_status="Active").select_related("department").order_by("department__department_name", "full_name"))
    employee_ids = [employee.pk for employee in employees]
    hours = dict(TimesheetEntry.objects.filter(employee_id__in=employee_ids, work_date__year=year, work_date__month=month).order_by().values(
        'employee_id'
    ).annotate(total=Sum('hours')).values_list('employee_id', 'total'))
    summaries = {summary.employee_id: summary for summary in MonthlyAttendanceSummary.objects.filter(employee_id__in=employee_ids, year=year, month=month)}
    balances = {balance.employee_id: balance for balance in LeaveBalance.objects.filter(employee_id__in=employee_ids, year=year)}
    annual_holidays = holiday_dates(date(year, 1, 1), date(year, 12, 31))
    annual_used = defaultdict(lambda: Decimal('0'))
    for leave in LeaveRequest.objects.filter(employee_id__in=employee_ids, status='Approved',
        leave_type__leave_type_code__iexact=ANNUAL_LEAVE_CODE, from_date__lte=date(year, 12, 31), to_date__gte=date(year, 1, 1)):
        annual_used[leave.employee_id] += leave_days_in_year(leave, year, holidays=annual_holidays)
    rows = []
    for emp in employees:
        total_hours = hours.get(emp.pk) or Decimal('0')
        submitted_summary = summaries.get(emp.pk)
        summary = submitted_summary if submitted_summary and submitted_summary.status == MonthlyAttendanceSummary.STATUS_APPROVED else None
        leave_total = summary.total_leave_days if summary else Decimal("0")
        required_hours = (Decimal(base_days) - leave_total) * hours_per_day
        balance = balances.get(emp.pk)
        has_pending_summary = bool(submitted_summary and submitted_summary.status == MonthlyAttendanceSummary.STATUS_PENDING)
        rows.append({
            "employee": emp, "total_hours": total_hours, "required_hours": required_hours,
            "diff_hours": total_hours - required_hours,
            "leave_remaining": balance.allocated_days + balance.carried_over_days - annual_used[emp.pk] if balance else None,
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

    today = timezone.localdate()
    default_from = today.replace(day=1)
    try:
        from_date = parse_date(request.GET.get("from_date", default_from.isoformat()))
        to_date = parse_date(request.GET.get("to_date", today.isoformat()))
        if not from_date or not to_date or to_date < from_date:
            raise ValueError
    except ValueError:
        messages.error(request, "Khoảng ngày không hợp lệ; đã dùng tháng hiện tại.")
        from_date, to_date = default_from, today

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
        "from_date": from_date.isoformat(), "to_date": to_date.isoformat(),
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
            raw_department = request.POST.get('department', '')
            department_id = parse_int(raw_department, None, min_value=1, max_value=2147483647)
            if raw_department and department_id is None:
                raise ValidationError('Phòng ban không hợp lệ.')
            allowed_departments = managed_departments_for(request.user, global_roles=(HR_MANAGER,))
            if department_id:
                if not allowed_departments.filter(pk=department_id).exists():
                    raise ValidationError('Chỉ được tạo sự kiện cho phòng ban thuộc phạm vi quản lý.')
            elif not (request.user.is_superuser or _role_code(request) == HR_MANAGER):
                raise ValidationError('Trưởng phòng phải chọn phòng ban thuộc phạm vi quản lý.')
            event = Event(
                title=request.POST.get("title"),
                event_type=request.POST.get("event_type", "Meeting"),
                attendance_mode=request.POST.get("attendance_mode", "Offline"),
                department_id=department_id,
                start_time=request.POST.get("start_time"),
                end_time=request.POST.get("end_time"),
                location=request.POST.get("location", ""),
                description=request.POST.get("description", ""),
                created_by_employee=employee,
                created_by=request.user,
            )
            if event.attendance_mode not in dict(Event.ATTENDANCE_MODE_CHOICES):
                raise ValidationError('Hình thức phải là Online hoặc Offline.')
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
            return redirect("portal:event_list")
        except Exception as e:
            _friendly_error(request, e, "Không thể tạo.")

    my_departments = managed_departments_for(request.user, global_roles=(HR_MANAGER,))
    from apps.common.ui_choices import text_choices
    events = list(events)
    return render(request, "portal/event_list.html", {
        "events": events, "can_create_event": _can_create_event(request), "departments": my_departments,
        "location_choices": text_choices(events, "location"),
        "submitted": request.POST if request.method == "POST" else {},
        "attendance_modes": Event.ATTENDANCE_MODE_CHOICES,
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
    today = timezone.localdate()
    year = parse_int(request.GET.get("year"), today.year, min_value=2000, max_value=2100)
    plans = with_headcounts(HeadcountPlan.objects.filter(year=year))
    return render(request, "portal/report_headcount.html", {
        "plans": plans, "year": year, "years": range(today.year - 1, today.year + 2),
    })


@login_required
def report_budget(request):
    if not _can_view_reports(request):
        messages.error(request, "Anh/chị không có quyền xem báo cáo.")
        return redirect("portal:dashboard")
    today = timezone.localdate()
    year = parse_int(request.GET.get("year"), today.year, min_value=2000, max_value=2100)
    budgets = AnnualBudget.objects.filter(year=year).select_related("department")

    costs = ProcurementItem.objects.filter(procurement_request__is_deleted=False,
        procurement_request__request_date__year=year, procurement_request__status__in=['Approved', 'Purchased'])
    amount = ExpressionWrapper(F('estimated_cost') * F('quantity'), output_field=DecimalField(max_digits=24, decimal_places=2))
    department_costs = dict(costs.order_by().values('procurement_request__department_id').annotate(total=Sum(amount)).values_list('procurement_request__department_id', 'total'))
    company_procurement = sum((value or Decimal('0') for value in department_costs.values()), Decimal('0'))
    training_cost = TrainingCourse.objects.filter(start_date__year=year).aggregate(total=Sum('cost'))['total'] or Decimal('0')
    rows = []
    for b in budgets:
        actual = Decimal("0")
        if b.category == "Procurement":
            actual = (department_costs.get(b.department_id) or Decimal('0')) if b.department_id else company_procurement
        elif b.category == "Training":
            actual = training_cost
        rows.append({"budget": b, "actual": actual, "remaining": b.allocated_amount - actual})

    return render(request, "portal/report_budget.html", {"rows": rows, "year": year, "years": range(today.year - 1, today.year + 2)})
