from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from django.utils import timezone
from apps.common.export_names import export_name

from apps.security.permissions import has_permission
from apps.security.data_access import visible_dispatches_for
from apps.security.models import SecurityEvent
from apps.common.params import parse_int

from apps.hrm.models import Employee
from apps.contract.models import Contract
from apps.document.models import OfficialDispatch
from apps.attendance.models import MonthlyAttendanceSummary
from .services import (
    generate_employee_list_excel,
    generate_expiring_contracts_excel,
    generate_dispatch_book_excel,
)


def _can_view_reports(request):
    return has_permission(request.user, "view_report_center")


@login_required
def report_dashboard(request):
    if not _can_view_reports(request):
        return HttpResponseForbidden("Anh/chị không có quyền truy cập Trung tâm Báo cáo.")

    today = date.today()
    limit_60 = today + timedelta(days=60)
    limit_30 = today + timedelta(days=30)

    # Thống kê nhân sự
    total_active = Employee.objects.filter(employment_status="Active").count()
    total_probation = Employee.objects.filter(employment_status="Probation").count()
    total_resigned = Employee.objects.filter(employment_status="Resigned").count()

    # Thống kê hợp đồng sắp hết hạn
    expiring_30_count = Contract.objects.filter(
        status="Active", end_date__isnull=False, end_date__lte=limit_30, end_date__gte=today
    ).count()
    expiring_60_count = Contract.objects.filter(
        status="Active", end_date__isnull=False, end_date__lte=limit_60, end_date__gte=today
    ).count()

    # Thống kê công văn
    pending_dispatches = OfficialDispatch.objects.filter(status="Pending").count()
    processing_dispatches = OfficialDispatch.objects.filter(status="Processing").count()
    overdue_dispatches = OfficialDispatch.objects.filter(
        status__in=["Pending", "Processing"], due_date__lt=today
    ).count()

    context = {
        "today": today,
        "total_active": total_active,
        "total_probation": total_probation,
        "total_resigned": total_resigned,
        "expiring_30_count": expiring_30_count,
        "expiring_60_count": expiring_60_count,
        "pending_dispatches": pending_dispatches,
        "processing_dispatches": processing_dispatches,
        "overdue_dispatches": overdue_dispatches,
    }
    return render(request, "reporting/dashboard.html", context)


@login_required
def export_employees(request):
    if not has_permission(request.user, 'export_employee_data'):
        return HttpResponseForbidden("Không có quyền xuất dữ liệu.")
    excel_stream = generate_employee_list_excel()
    response = HttpResponse(
        excel_stream.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{export_name("DS_NhanSu", "TongHop", timezone.localdate(), "xlsx")}"'
    SecurityEvent.objects.create(user=request.user, action="data_export", resource=request.resolver_match.url_name)
    return response


@login_required
def export_contracts(request):
    if not has_permission(request.user, 'export_employee_data'):
        return HttpResponseForbidden("Không có quyền xuất dữ liệu.")
    days = parse_int(request.GET.get("days"), 60, min_value=1, max_value=3650)
    excel_stream = generate_expiring_contracts_excel(days_threshold=days)
    response = HttpResponse(
        excel_stream.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{export_name("DS_HopDongSapHetHan", str(days) + "Ngay", timezone.localdate(), "xlsx")}"'
    SecurityEvent.objects.create(user=request.user, action="data_export", resource=request.resolver_match.url_name)
    return response


@login_required
def export_dispatches(request):
    if not _can_view_reports(request):
        return HttpResponseForbidden("Không có quyền xuất dữ liệu.")
    dispatch_type = request.GET.get("type", "Incoming")
    year = parse_int(request.GET.get("year"), date.today().year, min_value=2000, max_value=2100)
    excel_stream = generate_dispatch_book_excel(dispatch_type=dispatch_type, year=year, queryset=visible_dispatches_for(request.user))
    type_slug = "den" if dispatch_type == "Incoming" else "di"
    response = HttpResponse(
        excel_stream.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{export_name("So_CongVan", str(year) + "-" + type_slug, timezone.localdate(), "xlsx")}"'
    SecurityEvent.objects.create(user=request.user, action="data_export", resource=request.resolver_match.url_name)
    return response
