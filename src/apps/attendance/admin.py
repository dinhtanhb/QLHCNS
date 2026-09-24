from django.contrib import admin
from apps.common.admin import BaseAuditAdmin
from .models import WorkShift, Attendance, Holiday, WorkingCalendar
from .models import MonthlyAttendanceSummary
from .models import ProjectTimeAllocation


class WorkShiftAdmin(BaseAuditAdmin):
    view_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER")
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER")


admin.site.register(WorkShift, WorkShiftAdmin)


class CalendarBaseAdmin(BaseAuditAdmin):
    view_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER", "DEPT_MANAGER")
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER")


@admin.register(Holiday)
class HolidayAdmin(CalendarBaseAdmin):
    list_display = ("holiday_name", "holiday_date", "is_active")
    list_filter = ("is_active",)


@admin.register(WorkingCalendar)
class WorkingCalendarAdmin(CalendarBaseAdmin):
    list_display = ("calendar_year", "working_days_per_month", "working_hours_per_day", "is_default")


@admin.register(Attendance)
class AttendanceAdmin(BaseAuditAdmin):
    list_display = ("employee", "attendance_date", "check_in_time", "check_out_time", "status")
    list_filter = ("status", "attendance_date")
    search_fields = ("employee__full_name", "employee__employee_code")

    view_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER", "DEPT_MANAGER")
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER")

    def scope_queryset(self, request, qs):
        role_code = self._role_code(request)
        if role_code == "DEPT_MANAGER":
            employee = getattr(request.user, "employee", None)
            if not employee:
                return qs.none()
            dept_ids = employee.managed_departments.values_list("pk", flat=True)
            return qs.filter(employee__department_id__in=dept_ids)
        return qs

from .models import TimesheetEntry  # thêm vào dòng import ở đầu file, chung với các import cũ


@admin.register(TimesheetEntry)
class TimesheetEntryAdmin(BaseAuditAdmin):
    list_display = ("employee", "work_date", "project", "hours")
    list_filter = ("project",)
    search_fields = ("employee__full_name", "employee__employee_code")
    view_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER", "DEPT_MANAGER")
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER")  # nhân viên nhập qua Portal, Admin chỉ để HR sửa khi cần

@admin.register(MonthlyAttendanceSummary)
class MonthlyAttendanceSummaryAdmin(BaseAuditAdmin):
    list_display = ("employee", "year", "month", "sick_days", "maternity_days", "compensatory_days", "annual_leave_days", "unpaid_leave_days")
    search_fields = ("employee__full_name", "employee__employee_code")
    view_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER")
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER", "HR_OFFICER")

@admin.register(ProjectTimeAllocation)
class ProjectTimeAllocationAdmin(BaseAuditAdmin):
    list_display = ("employee", "project", "year", "month", "allocation_percent")
    search_fields = ("employee__full_name", "employee__employee_code")
    view_roles = ("SUPER_ADMIN", "HR_MANAGER", "FINANCE_OFFICER")
    edit_roles = ("SUPER_ADMIN", "HR_MANAGER", "FINANCE_OFFICER")