from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Count, IntegerField, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce
from apps.common.models import BaseAuditModel


# ============================================================
# 1. ĐỊNH BIÊN NHÂN SỰ NĂM
# ============================================================

class HeadcountPlan(BaseAuditModel):
    year = models.SmallIntegerField("Năm", db_column="Year")
    department = models.ForeignKey(
        "organization.Department", verbose_name="Phòng ban", on_delete=models.CASCADE,
        db_column="DepartmentID", related_name="headcount_plans",
    )
    planned_headcount = models.SmallIntegerField("Định biên (kế hoạch)", db_column="PlannedHeadcount")
    note = models.CharField("Ghi chú", max_length=500, null=True, blank=True, db_column="Note")

    class Meta:
        db_table = "tblHeadcountPlan"
        verbose_name = "Định biên nhân sự"
        verbose_name_plural = "Định biên nhân sự"
        constraints = [models.UniqueConstraint(fields=["year", "department"], name="UX_Headcount_Year_Dept")]

    @property
    def actual_headcount(self):
        if hasattr(self, '_actual_headcount'):
            return self._actual_headcount
        return self.department.employees.filter(employment_status="Active").count()

    @property
    def gap(self):
        return self.planned_headcount - self.actual_headcount

    def __str__(self):
        return f"{self.department} - {self.year}: {self.planned_headcount}"


def with_headcounts(queryset):
    from apps.hrm.models import Employee
    counts = Employee.objects.filter(department_id=OuterRef('department_id'), employment_status='Active').order_by().values(
        'department_id'
    ).annotate(total=Count('pk')).values('total')
    return queryset.select_related('department').annotate(
        _actual_headcount=Coalesce(Subquery(counts, output_field=IntegerField()), Value(0))
    )


# ============================================================
# 2. ĐÀO TẠO & PHÁT TRIỂN
# ============================================================

class TrainingCourse(BaseAuditModel):
    STATUS_CHOICES = [("Planned", "Kế hoạch"), ("Ongoing", "Đang diễn ra"), ("Completed", "Đã hoàn thành"), ("Cancelled", "Đã hủy")]

    course_code = models.CharField("Mã khóa học", max_length=50, unique=True, db_column="CourseCode")
    course_name = models.CharField("Tên khóa học", max_length=300, db_column="CourseName")
    provider = models.CharField("Đơn vị đào tạo", max_length=200, null=True, blank=True, db_column="Provider")
    start_date = models.DateField("Ngày bắt đầu", db_column="StartDate")
    end_date = models.DateField("Ngày kết thúc", null=True, blank=True, db_column="EndDate")
    cost = models.DecimalField("Chi phí (tổng)", max_digits=18, decimal_places=2, default=0, db_column="Cost")
    status = models.CharField("Trạng thái", max_length=30, choices=STATUS_CHOICES, default="Planned", db_column="Status")

    class Meta:
        db_table = "tblTrainingCourse"
        verbose_name = "Khóa đào tạo"
        verbose_name_plural = "Khóa đào tạo"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.course_code} - {self.course_name}"

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({'end_date': 'Ngày kết thúc không được trước ngày bắt đầu.'})


class TrainingEnrollment(BaseAuditModel):
    STATUS_CHOICES = [("Registered", "Đã đăng ký"), ("Completed", "Đã hoàn thành"), ("Cancelled", "Đã hủy")]

    course = models.ForeignKey(TrainingCourse, verbose_name="Khóa học", on_delete=models.CASCADE, db_column="CourseID", related_name="enrollments")
    employee = models.ForeignKey("hrm.Employee", verbose_name="Nhân viên", on_delete=models.CASCADE, db_column="EmployeeID", related_name="trainings")
    status = models.CharField("Trạng thái", max_length=30, choices=STATUS_CHOICES, default="Registered", db_column="Status")
    result = models.CharField("Kết quả / Chứng chỉ", max_length=300, null=True, blank=True, db_column="Result")

    class Meta:
        db_table = "tblTrainingEnrollment"
        verbose_name = "Đăng ký đào tạo"
        verbose_name_plural = "Đăng ký đào tạo"
        constraints = [models.UniqueConstraint(fields=["course", "employee"], name="UX_Enrollment_Course_Emp")]

    def __str__(self):
        return f"{self.employee} - {self.course}"


# ============================================================
# 3. NGÂN SÁCH NĂM
# ============================================================

class AnnualBudget(BaseAuditModel):
    CATEGORY_CHOICES = [("Procurement", "Mua sắm"), ("Training", "Đào tạo"), ("Recruitment", "Tuyển dụng"), ("Other", "Khác")]

    year = models.SmallIntegerField("Năm", db_column="Year")
    department = models.ForeignKey(
        "organization.Department", verbose_name="Phòng ban", null=True, blank=True,
        on_delete=models.SET_NULL, db_column="DepartmentID", related_name="budgets",
    )
    category = models.CharField("Hạng mục", max_length=30, choices=CATEGORY_CHOICES, db_column="Category")
    allocated_amount = models.DecimalField("Ngân sách được duyệt", max_digits=18, decimal_places=2, db_column="AllocatedAmount")
    note = models.CharField("Ghi chú", max_length=500, null=True, blank=True, db_column="Note")

    class Meta:
        db_table = "tblAnnualBudget"
        verbose_name = "Ngân sách năm"
        verbose_name_plural = "Ngân sách năm"
        constraints = [models.UniqueConstraint(fields=["year", "department", "category"], name="UX_Budget_Year_Dept_Cat")]

    def __str__(self):
        return f"{self.get_category_display()} - {self.department or 'Toàn Trung tâm'} - {self.year}"


# ============================================================
# 4. LỊCH CÔNG TÁC / SỰ KIỆN
# ============================================================

class Event(BaseAuditModel):
    EVENT_TYPE_CHOICES = [("Meeting", "Họp"), ("Training", "Đào tạo"), ("FieldTrip", "Công tác"), ("Company", "Sự kiện Trung tâm"), ("Other", "Khác")]

    title = models.CharField("Tiêu đề", max_length=300, db_column="Title")
    event_type = models.CharField("Loại sự kiện", max_length=30, choices=EVENT_TYPE_CHOICES, default="Meeting", db_column="EventType")
    department = models.ForeignKey(
        "organization.Department", verbose_name="Phòng ban", null=True, blank=True,
        on_delete=models.SET_NULL, db_column="DepartmentID", related_name="events",
        help_text="Để trống nếu là sự kiện toàn Trung tâm",
    )
    start_time = models.DateTimeField("Bắt đầu", db_column="StartTime")
    end_time = models.DateTimeField("Kết thúc", db_column="EndTime")
    location = models.CharField("Địa điểm", max_length=300, null=True, blank=True, db_column="Location")
    description = models.CharField("Mô tả", max_length=1000, null=True, blank=True, db_column="Description")
    created_by_employee = models.ForeignKey(
        "hrm.Employee", verbose_name="Người tạo", null=True, blank=True, on_delete=models.SET_NULL,
        db_column="CreatedByEmployeeID", related_name="events_created",
    )

    class Meta:
        db_table = "tblEvent"
        verbose_name = "Sự kiện / Lịch công tác"
        verbose_name_plural = "Sự kiện / Lịch công tác"
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.title} ({self.start_time:%d/%m %H:%M})"

    def clean(self):
        super().clean()
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError({'end_time': 'Thời điểm kết thúc phải sau thời điểm bắt đầu.'})
