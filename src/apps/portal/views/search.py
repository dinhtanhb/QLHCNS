"""Authenticated, bounded search. Apply existing access rules before querying."""
import unicodedata

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache

from apps.hrm.models import Employee
from apps.portal.dashboard_data import dashboard_employee_scope
from apps.security.permissions import has_permission
from .common import _get_employee

# Destinations are read pages, never actions. Permission names use the shared matrix.
PAGES = (
    ("Bảng điều khiển Dashboard", "dashboard", None),
    ("Hồ sơ cá nhân", "profile", None),
    ("Nghỉ phép", "leave_list", None),
    ("Bảng công chấm công", "timesheet_month", None),
    ("Công việc Task", "task_list", None),
    ("Thông báo", "notification_list", None),
    ("Nhân viên & hồ sơ nhân sự", "hr_employee_list", "manage_hr"),
    ("Hợp đồng lao động", "hr_contract_list", "manage_hr"),
    ("Tuyển dụng", "recruitment_hub", ("request_recruitment", "approve_recruitment", "manage_hr")),
    ("Báo cáo điều hành", "report_hub", "view_reports"),
    ("Định biên nhân sự", "report_headcount", "view_reports"),
    ("Hoạt động dự án", "activity_dashboard", "view_activity_dashboard"),
    ("Tài sản", "asset_list", "view_asset"),
    ("Yêu cầu cập nhật hồ sơ", "profile_change_request_list", None),
    ("Sơ đồ tổ chức", "org_chart", None),
    ("KPI cá nhân", "kpi_my_list", None),
    ("Phiếu lương cá nhân", "payslip_list", None),
    ("Tài liệu đã ban hành", "document_list", None),
    ("Phòng họp", "room_booking_list", None),
    ("Đặt xe", "vehicle_booking_list", None),
    ("Văn phòng phẩm VPP", "supply_request_list", None),
    ("Lịch công tác", "event_list", None),
    ("Đào tạo", "training_my_list", None),
    ("Checklist tiếp nhận nghỉ việc", "lifecycle_case_list", "manage_hr"),
    ("Biểu mẫu HCNS", "hcns_catalog", "manage_hr"),
    ("Quyết định nhân sự", "personnel_decision_list", ("manage_hr", "approve_personnel_decision")),
    ("Duyệt nghỉ phép", "leave_approval_list", "approve_leave"),
    ("Duyệt chấm công", "timesheet_approval_list", "approve_timesheet"),
    ("Duyệt tài liệu", "document_approval_list", "approve_document"),
    ("Đề xuất tuyển dụng", "recruitment_list", ("request_recruitment", "approve_recruitment")),
    ("Ứng viên tuyển dụng", "hr_candidate_list", "manage_hr"),
    ("Chạy lương hàng tháng", "finance_period_list", "manage_finance"),
    ("Lương cơ bản nhân viên", "finance_salary_list", "manage_finance"),
    ("Người phụ thuộc", "finance_dependent_list", "manage_finance"),
    ("Cấu hình Thuế BH", "finance_tax_config", "manage_finance"),
    ("Quản lý tài sản", "asset_admin_list", "view_asset"),
    ("Kiểm kê tài sản", "inventory_session_list", "view_asset"),
    ("Thanh lý tài sản", "disposal_request_list", "view_asset"),
    ("Quản lý ngày lễ", "holiday_list", "manage_calendar"),
    ("Duyệt đề xuất hoạt động", "activity_proposal_approval_list", "approve_activity_proposals"),
    ("Lịch hoạt động dự án", "activity_calendar", "view_activity_dashboard"),
)


def normalized(value):
    return "".join(c for c in unicodedata.normalize("NFD", value.casefold().replace("đ", "d"))
                   if not unicodedata.combining(c))


@login_required
@require_GET
@never_cache
def global_search(request):
    query = request.GET.get("q", "").strip()[:100]
    people, pages = [], []
    if len(query) >= 2:
        needle = normalized(query)
        pages = [dict(label=label, href=reverse("portal:" + route))
                 for label, route, permission in PAGES
                 if (permission is None or any(has_permission(request.user, p)
                     for p in (permission if isinstance(permission, tuple) else (permission,))))
                 and needle in normalized(label)]
        employee = _get_employee(request)
        qs, _ = dashboard_employee_scope(request.user, employee)
        if qs is None:
            qs = Employee.objects.filter(pk=employee.pk) if employee and not employee.is_deleted else Employee.objects.none()
        # Email is a normal non-encrypted work contact, not identity/compensation data.
        matches = qs.filter(Q(full_name__icontains=query) | Q(employee_code__icontains=query)
                            | Q(company_email__icontains=query)).select_related("department").order_by("full_name", "pk")[:21]
        can_open = has_permission(request.user, "manage_hr") or has_permission(request.user, "view_all_employees")
        for person in matches:
            people.append(dict(name=person.full_name, code=person.employee_code, email=person.company_email,
                               department=person.department.department_name if person.department else "—",
                               href=reverse("portal:hr_employee_detail", args=[person.pk]) if can_open
                               else reverse("portal:profile") if employee and person.pk == employee.pk else None))
    return render(request, "portal/global_search.html", dict(search_query=query,
                  search_people=people[:20], search_pages=pages, search_more=len(people) > 20))
