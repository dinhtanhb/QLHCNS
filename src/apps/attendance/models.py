from django.conf import settings
from django.db import models
from apps.common.models import BaseAuditModel


class WorkShift(BaseAuditModel):
    shift_code = models.CharField(max_length=50, unique=True, db_column="ShiftCode")
    shift_name = models.CharField(max_length=100, db_column="ShiftName")
    start_time = models.TimeField(db_column="StartTime")
    end_time = models.TimeField(db_column="EndTime")

    class Meta:
        db_table = "tblWorkShift"
        verbose_name = "Ca làm việc"
        verbose_name_plural = "Ca làm việc"

    def __str__(self):
        return self.shift_name


class Attendance(BaseAuditModel):
    STATUS_CHOICES = [
        ("Present", "Đủ công"), ("Late", "Đi muộn"),
        ("Absent", "Vắng"), ("HalfDay", "Nửa ngày"),
    ]

    employee = models.ForeignKey(
        "hrm.Employee", on_delete=models.PROTECT,
        db_column="EmployeeID", related_name="attendances",
    )
    attendance_date = models.DateField(db_column="AttendanceDate")
    check_in_time = models.TimeField(null=True, blank=True, db_column="CheckInTime")
    check_out_time = models.TimeField(null=True, blank=True, db_column="CheckOutTime")
    working_hours = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True, db_column="WorkingHours"
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="Present", db_column="Status")

    class Meta:
        db_table = "tblAttendance"
        verbose_name = "Chấm công"
        verbose_name_plural = "Chấm công"
        constraints = [
            models.UniqueConstraint(fields=["employee", "attendance_date"], name="UX_Attendance_Employee_Date")
        ]

    def __str__(self):
        return f"{self.employee} - {self.attendance_date}"

class Holiday(BaseAuditModel):
    holiday_code = models.CharField("Mã ngày lễ", max_length=50, unique=True, db_column="HolidayCode")
    holiday_name = models.CharField("Tên ngày lễ", max_length=200, db_column="HolidayName")
    holiday_date = models.DateField("Ngày", unique=True, db_column="HolidayDate")
    description = models.CharField("Ghi chú", max_length=500, null=True, blank=True, db_column="Description")
    is_active = models.BooleanField("Áp dụng", default=True, db_column="IsActive")

    class Meta:
        db_table = "tblHoliday"
        verbose_name = "Ngày lễ"
        verbose_name_plural = "Ngày lễ"
        ordering = ["holiday_date"]

    def __str__(self):
        return f"{self.holiday_name} ({self.holiday_date})"


class WorkingCalendar(BaseAuditModel):
    calendar_year = models.SmallIntegerField("Năm", unique=True, db_column="CalendarYear")
    working_days_per_month = models.DecimalField(
        "Số ngày công chuẩn/tháng", max_digits=4, decimal_places=1, default=26, db_column="WorkingDaysPerMonth"
    )
    working_hours_per_day = models.DecimalField(
        "Số giờ công chuẩn/ngày", max_digits=4, decimal_places=1, default=8, db_column="WorkingHoursPerDay"
    )
    is_default = models.BooleanField("Áp dụng mặc định", default=False, db_column="IsDefault")

    class Meta:
        db_table = "tblWorkingCalendar"
        verbose_name = "Lịch làm việc"
        verbose_name_plural = "Lịch làm việc"

    def __str__(self):
        return f"Lịch làm việc {self.calendar_year}"

class TimesheetEntry(BaseAuditModel):
    employee = models.ForeignKey(
        "hrm.Employee", verbose_name="Nhân viên", on_delete=models.CASCADE,
        db_column="EmployeeID", related_name="timesheet_entries",
    )
    work_date = models.DateField("Ngày làm việc", db_column="WorkDate")
    project = models.ForeignKey(
        "project.Project", verbose_name="Dự án", null=True, blank=True,
        on_delete=models.PROTECT, db_column="ProjectID", related_name="timesheet_entries",
    )
    task_description = models.CharField("Công việc", max_length=500, null=True, blank=True, db_column="TaskDescription")
    hours = models.DecimalField("Số giờ", max_digits=4, decimal_places=2, default=0, db_column="Hours")

    class Meta:
        db_table = "tblTimesheetEntry"
        verbose_name = "Giờ làm việc theo dự án"
        verbose_name_plural = "Giờ làm việc theo dự án"
        constraints = [
            models.UniqueConstraint(fields=["employee", "work_date", "project"], name="UX_Timesheet_Emp_Date_Project")
        ]
        ordering = ["-work_date"]

    def __str__(self):
        return f"{self.employee} - {self.work_date} - {self.project} ({self.hours}h)"

class MonthlyAttendanceSummary(BaseAuditModel):
    employee = models.ForeignKey(
        "hrm.Employee", verbose_name="Nhân viên", on_delete=models.CASCADE,
        db_column="EmployeeID", related_name="monthly_summaries",
    )
    year = models.SmallIntegerField("Năm", db_column="Year")
    month = models.SmallIntegerField("Tháng", db_column="Month")
    sick_days = models.DecimalField("Số ngày nghỉ ốm", max_digits=4, decimal_places=1, default=0, db_column="SickDays")
    maternity_days = models.DecimalField("Số ngày thai sản", max_digits=4, decimal_places=1, default=0, db_column="MaternityDays")
    compensatory_days = models.DecimalField("Số ngày nghỉ bù", max_digits=4, decimal_places=1, default=0, db_column="CompensatoryDays")
    annual_leave_days = models.DecimalField("Số ngày nghỉ phép", max_digits=4, decimal_places=1, default=0, db_column="AnnualLeaveDays")
    unpaid_leave_days = models.DecimalField("Số ngày nghỉ không lương", max_digits=4, decimal_places=1, default=0, db_column="UnpaidLeaveDays")

    # I3 (đã sửa): trước đây nhân viên tự khai các số ngày ở trên rồi số liệu áp dụng thẳng vào
    # yêu cầu giờ công (timesheet_month) và trực tiếp trừ vào actual_working_days khi tính lương
    # (Payroll.calculate() — xem payroll/models.py) mà không ai xác nhận lại. Thêm trạng thái
    # duyệt: nhân viên chỉ tự khai được khi còn "Pending"; Trưởng phòng/HR_MANAGER/DIRECTOR phải
    # duyệt ("Approved") thì payroll và báo cáo BCC mới dùng số liệu này, tránh nhân viên tự đổi
    # số ảnh hưởng lương/BCC mà không qua kiểm tra.
    STATUS_PENDING = "Pending"
    STATUS_APPROVED = "Approved"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Chờ duyệt"),
        (STATUS_APPROVED, "Đã duyệt"),
    ]
    status = models.CharField(
        "Trạng thái", max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_column="Status",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="Người duyệt", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+", db_column="ApprovedBy",
    )
    approved_at = models.DateTimeField("Ngày duyệt", null=True, blank=True, db_column="ApprovedAt")

    class Meta:
        db_table = "tblMonthlyAttendanceSummary"
        verbose_name = "Tổng hợp chấm công tháng"
        verbose_name_plural = "Tổng hợp chấm công tháng"
        constraints = [
            models.UniqueConstraint(fields=["employee", "year", "month"], name="UX_MonthlySummary_Emp_Year_Month")
        ]

    @property
    def total_leave_days(self):
        return self.sick_days + self.maternity_days + self.compensatory_days + self.annual_leave_days + self.unpaid_leave_days

    def __str__(self):
        return f"{self.employee} - {self.month}/{self.year}"

class ProjectTimeAllocation(BaseAuditModel):
    employee = models.ForeignKey(
        "hrm.Employee", verbose_name="Nhân viên", on_delete=models.CASCADE,
        db_column="EmployeeID", related_name="project_allocations",
    )
    project = models.ForeignKey(
        "project.Project", verbose_name="Dự án", on_delete=models.CASCADE,
        db_column="ProjectID", related_name="employee_allocations",
    )
    year = models.SmallIntegerField("Năm", db_column="Year")
    month = models.SmallIntegerField("Tháng", db_column="Month")
    allocation_percent = models.DecimalField(
        "Tỷ lệ phân bổ (%)", max_digits=5, decimal_places=2, default=100, db_column="AllocationPercent"
    )

    class Meta:
        db_table = "tblProjectTimeAllocation"
        verbose_name = "Phân bổ thời gian theo dự án"
        verbose_name_plural = "Phân bổ thời gian theo dự án"
        constraints = [
            models.UniqueConstraint(fields=["employee", "project", "year", "month"], name="UX_Allocation_Emp_Proj_Month")
        ]

    def __str__(self):
        return f"{self.employee} - {self.project} - {self.month}/{self.year}: {self.allocation_percent}%"