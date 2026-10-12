from django.db import models
from django.core.exceptions import ValidationError
from apps.common.models import BaseAuditModel
from apps.common.uploads import validate_upload, build_upload_path


def upload_to_profile_change(instance, filename):
    return build_upload_path("profile-change-requests", filename)


class Employee(BaseAuditModel):
    GENDER_CHOICES = [("Male", "Nam"), ("Female", "Nữ"), ("Other", "Khác")]
    EMPLOYMENT_STATUS_CHOICES = [
        ("Active", "Đang làm việc"),
        ("Probation", "Thử việc"),
        ("OnLeave", "Đang nghỉ dài hạn"),
        ("Resigned", "Đã nghỉ việc"),
    ]

    employee_code = models.CharField("Mã nhân viên", max_length=50, unique=True, db_column="EmployeeCode")
    first_name = models.CharField("Tên", max_length=100, db_column="FirstName")
    last_name = models.CharField("Họ", max_length=100, db_column="LastName")
    full_name = models.CharField("Họ và tên đầy đủ", max_length=200, db_column="FullName")
    date_of_birth = models.DateField("Ngày sinh", db_column="DateOfBirth")
    gender = models.CharField("Giới tính", max_length=10, choices=GENDER_CHOICES, db_column="Gender")

    national_id = models.CharField("Số CCCD", max_length=20, unique=True, db_column="NationalID")
    tax_code = models.CharField("Mã số thuế", max_length=20, null=True, blank=True, db_column="TaxCode")
    social_insurance_no = models.CharField(
        "Số sổ BHXH", max_length=20, null=True, blank=True, db_column="SocialInsuranceNo"
    )

    personal_email = models.EmailField(
        "Email cá nhân", max_length=100, null=True, blank=True, db_column="PersonalEmail"
    )
    company_email = models.EmailField("Email Trung tâm", max_length=100, unique=True, db_column="CompanyEmail")
    mobile_phone = models.CharField("Số điện thoại", max_length=20, db_column="MobilePhone")
    address = models.CharField("Địa chỉ", max_length=500, null=True, blank=True, db_column="Address")

    join_date = models.DateField("Ngày vào làm", db_column="JoinDate")
    leave_date = models.DateField("Ngày nghỉ việc", null=True, blank=True, db_column="LeaveDate")

    department = models.ForeignKey(
        "organization.Department", verbose_name="Phòng ban", on_delete=models.PROTECT,
        db_column="DepartmentID", related_name="employees",
    )
    position = models.ForeignKey(
        "organization.Position", verbose_name="Vị trí", on_delete=models.PROTECT,
        db_column="PositionID", related_name="employees",
    )
    job_title = models.ForeignKey(
        "organization.JobTitle", verbose_name="Chức danh", null=True, blank=True, on_delete=models.SET_NULL,
        db_column="JobTitleID", related_name="employees",
    )
    manager = models.ForeignKey(
        "self", verbose_name="Quản lý trực tiếp", null=True, blank=True, on_delete=models.SET_NULL,
        db_column="ManagerID", related_name="subordinates",
    )
    employment_status = models.CharField(
        "Trạng thái làm việc", max_length=30, choices=EMPLOYMENT_STATUS_CHOICES,
        default="Active", db_column="EmploymentStatus",
    )
    photo_url = models.CharField("Ảnh đại diện (URL)", max_length=500, null=True, blank=True, db_column="PhotoUrl")

    class Meta:
        db_table = "tblEmployee"
        verbose_name = "Nhân viên"
        verbose_name_plural = "Nhân viên"

    def __str__(self):
        return f"{self.employee_code} - {self.full_name}"


class EmployeeProfileChangeRequest(BaseAuditModel):
    ALLOWED_FIELDS = ("personal_email", "mobile_phone", "address")
    FIELD_CHOICES = [
        ("personal_email", "Email cá nhân"),
        ("mobile_phone", "Số điện thoại"),
        ("address", "Địa chỉ"),
    ]
    STATUS_CHOICES = [
        ("Pending", "Chờ duyệt"),
        ("Approved", "Đã duyệt"),
        ("Rejected", "Từ chối"),
        ("NeedsMoreInfo", "Yêu cầu bổ sung"),
    ]

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="profile_change_requests",
        db_column="EmployeeID",
    )
    field_name = models.CharField("Trường đề nghị đổi", max_length=50, choices=FIELD_CHOICES, db_column="FieldName")
    old_value = models.CharField("Giá trị hiện tại", max_length=500, blank=True, db_column="OldValue")
    new_value = models.CharField("Giá trị đề nghị", max_length=500, db_column="NewValue")
    submitted_snapshot = models.CharField(max_length=500, blank=True, db_column="SubmittedSnapshot")
    reason = models.CharField("Lý do", max_length=500, blank=True, db_column="Reason")
    attachment = models.FileField(
        "Chứng từ đính kèm", upload_to=upload_to_profile_change,
        validators=[validate_upload], null=True, blank=True, db_column="Attachment",
    )
    status = models.CharField(
        "Trạng thái", max_length=20, choices=STATUS_CHOICES, default="Pending", db_column="Status"
    )
    decided_by = models.ForeignKey(
        "security.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+", db_column="DecidedByUserID",
    )
    decided_at = models.DateTimeField(null=True, blank=True, db_column="DecidedAt")
    decision_note = models.CharField("Ý kiến xử lý", max_length=500, blank=True, db_column="DecisionNote")

    class Meta:
        db_table = "tblEmployeeProfileChangeRequest"
        verbose_name = "Yêu cầu cập nhật hồ sơ"
        verbose_name_plural = "Yêu cầu cập nhật hồ sơ"
        ordering = ["-created_date"]

    def clean(self):
        super().clean()
        if self.field_name not in self.ALLOWED_FIELDS:
            raise ValidationError({"field_name": "Trường này không được phép tự cập nhật."})

    def __str__(self):
        return f"{self.employee} — {self.field_name} ({self.status})"

class EmployeeTransfer(BaseAuditModel):
    employee = models.ForeignKey(
        Employee, verbose_name="Nhân viên", on_delete=models.CASCADE, db_column="EmployeeID", related_name="transfers"
    )
    from_department = models.ForeignKey(
        "organization.Department", verbose_name="Từ phòng ban", on_delete=models.PROTECT,
        db_column="FromDepartmentID", related_name="transfers_from",
    )
    to_department = models.ForeignKey(
        "organization.Department", verbose_name="Đến phòng ban", on_delete=models.PROTECT,
        db_column="ToDepartmentID", related_name="transfers_to",
    )
    effective_date = models.DateField("Ngày hiệu lực", db_column="EffectiveDate")
    reason = models.CharField("Lý do", max_length=500, null=True, blank=True, db_column="Reason")

    class Meta:
        db_table = "tblEmployeeTransfer"
        verbose_name = "Điều chuyển nhân sự"
        verbose_name_plural = "Điều chuyển nhân sự"
        ordering = ["-effective_date"]

    def save(self, *args, **kwargs):
        from django.db import transaction
        with transaction.atomic():
            super().save(*args, **kwargs)
            from apps.hrm.services import apply_due_employee_changes
            apply_due_employee_changes()

    def __str__(self):
        return f"{self.employee}: {self.from_department} → {self.to_department}"


class EmployeePromotion(BaseAuditModel):
    employee = models.ForeignKey(
        Employee, verbose_name="Nhân viên", on_delete=models.CASCADE, db_column="EmployeeID", related_name="promotions"
    )
    old_position = models.ForeignKey(
        "organization.Position", verbose_name="Vị trí cũ", on_delete=models.PROTECT,
        db_column="OldPositionID", related_name="promotions_from",
    )
    new_position = models.ForeignKey(
        "organization.Position", verbose_name="Vị trí mới", on_delete=models.PROTECT,
        db_column="NewPositionID", related_name="promotions_to",
    )
    effective_date = models.DateField("Ngày hiệu lực", db_column="EffectiveDate")
    reason = models.CharField("Lý do", max_length=500, null=True, blank=True, db_column="Reason")

    class Meta:
        db_table = "tblEmployeePromotion"
        verbose_name = "Thăng chức/Bổ nhiệm"
        verbose_name_plural = "Thăng chức/Bổ nhiệm"
        ordering = ["-effective_date"]

    def save(self, *args, **kwargs):
        from django.db import transaction
        with transaction.atomic():
            super().save(*args, **kwargs)
            from apps.hrm.services import apply_due_employee_changes
            apply_due_employee_changes()

    def __str__(self):
        return f"{self.employee}: {self.old_position} → {self.new_position}"


class EmployeeReward(BaseAuditModel):
    employee = models.ForeignKey(
        Employee, verbose_name="Nhân viên", on_delete=models.CASCADE, db_column="EmployeeID", related_name="rewards"
    )
    reward_type = models.CharField("Loại khen thưởng", max_length=100, db_column="RewardType")
    reward_date = models.DateField("Ngày khen thưởng", db_column="RewardDate")
    amount = models.DecimalField("Số tiền thưởng", max_digits=18, decimal_places=2, null=True, blank=True, db_column="Amount")
    description = models.CharField("Nội dung", max_length=500, null=True, blank=True, db_column="Description")

    class Meta:
        db_table = "tblEmployeeReward"
        verbose_name = "Khen thưởng"
        verbose_name_plural = "Khen thưởng"
        ordering = ["-reward_date"]

    def __str__(self):
        return f"{self.employee} - {self.reward_type}"


class EmployeeDiscipline(BaseAuditModel):
    employee = models.ForeignKey(
        Employee, verbose_name="Nhân viên", on_delete=models.CASCADE, db_column="EmployeeID", related_name="disciplines"
    )
    discipline_type = models.CharField("Hình thức kỷ luật", max_length=100, db_column="DisciplineType")
    discipline_date = models.DateField("Ngày kỷ luật", db_column="DisciplineDate")
    description = models.CharField("Nội dung", max_length=500, null=True, blank=True, db_column="Description")

    class Meta:
        db_table = "tblEmployeeDiscipline"
        verbose_name = "Kỷ luật"
        verbose_name_plural = "Kỷ luật"
        ordering = ["-discipline_date"]

    def __str__(self):
        return f"{self.employee} - {self.discipline_type}"
