from django.db import models
from apps.common.models import BaseAuditModel
from apps.common.uploads import upload_to_candidate_cv, validate_upload
from apps.m365.storage import get_storage


class RecruitmentRequest(BaseAuditModel):
    STATUS_CHOICES = [
        ("Pending", "Chờ duyệt"),
        ("Approved", "Đã duyệt"),
        ("Rejected", "Từ chối"),
        ("Closed", "Đã hoàn tất tuyển dụng"),
    ]

    request_code = models.CharField("Mã đề xuất", max_length=50, unique=True, db_column="RequestCode")
    department = models.ForeignKey(
        "organization.Department", verbose_name="Phòng ban", on_delete=models.PROTECT,
        db_column="DepartmentID", related_name="recruitment_requests",
    )
    position = models.ForeignKey(
        "organization.Position", verbose_name="Vị trí cần tuyển", on_delete=models.PROTECT,
        db_column="PositionID", related_name="recruitment_requests",
    )
    required_quantity = models.SmallIntegerField("Số lượng cần", default=1, db_column="RequiredQuantity")
    request_reason = models.CharField("Lý do tuyển dụng", max_length=1000, null=True, blank=True, db_column="RequestReason")
    required_date = models.DateField("Ngày cần có người", db_column="RequiredDate")
    status = models.CharField("Trạng thái", max_length=30, choices=STATUS_CHOICES, default="Pending", db_column="Status")

    class Meta:
        db_table = "tblRecruitmentRequest"
        verbose_name = "Đề xuất tuyển dụng"
        verbose_name_plural = "Đề xuất tuyển dụng"

    def __str__(self):
        return f"{self.request_code} - {self.position} ({self.department})"


class JobPosting(BaseAuditModel):
    STATUS_CHOICES = [("Open", "Đang tuyển"), ("Closed", "Đã đóng")]

    recruitment_request = models.ForeignKey(
        RecruitmentRequest, verbose_name="Đề xuất tuyển dụng", on_delete=models.PROTECT,
        db_column="RecruitmentRequestID", related_name="postings",
    )
    posting_title = models.CharField("Tiêu đề tin tuyển dụng", max_length=300, db_column="PostingTitle")
    open_date = models.DateField("Ngày đăng", db_column="OpenDate")
    close_date = models.DateField("Ngày đóng", null=True, blank=True, db_column="CloseDate")
    status = models.CharField("Trạng thái", max_length=30, choices=STATUS_CHOICES, default="Open", db_column="Status")

    class Meta:
        db_table = "tblJobPosting"
        verbose_name = "Tin tuyển dụng"
        verbose_name_plural = "Tin tuyển dụng"

    def __str__(self):
        return self.posting_title


class Candidate(BaseAuditModel):
    STATUS_CHOICES = [
        ("New", "Mới ứng tuyển"),
        ("Screening", "Đang sàng lọc"),
        ("Interviewing", "Đang phỏng vấn"),
        ("Offered", "Đã gửi offer"),
        ("Hired", "Đã tuyển"),
        ("Rejected", "Không phù hợp"),
    ]

    candidate_code = models.CharField("Mã ứng viên", max_length=50, unique=True, db_column="CandidateCode")
    full_name = models.CharField("Họ tên", max_length=200, db_column="FullName")
    phone_number = models.CharField("Số điện thoại", max_length=20, db_column="PhoneNumber")
    email = models.EmailField("Email", max_length=100, db_column="Email")
    current_address = models.CharField("Địa chỉ hiện tại", max_length=500, null=True, blank=True, db_column="CurrentAddress")
    source = models.CharField("Nguồn ứng tuyển", max_length=100, null=True, blank=True, db_column="Source")
    cv_file = models.FileField(
        "Hồ sơ CV", upload_to=upload_to_candidate_cv,
        validators=[validate_upload], null=True, blank=True,
        storage=get_storage("recruitment_cv"),
    )
    status = models.CharField("Trạng thái", max_length=30, choices=STATUS_CHOICES, default="New", db_column="Status")

    class Meta:
        db_table = "tblCandidate"
        verbose_name = "Ứng viên"
        verbose_name_plural = "Ứng viên"

    def __str__(self):
        return f"{self.candidate_code} - {self.full_name}"


class Interview(BaseAuditModel):
    RESULT_CHOICES = [("Pass", "Đạt"), ("Fail", "Không đạt"), ("Pending", "Chưa có kết quả")]

    candidate = models.ForeignKey(
        Candidate, verbose_name="Ứng viên", on_delete=models.CASCADE,
        db_column="CandidateID", related_name="interviews",
    )
    interview_date = models.DateTimeField("Thời gian phỏng vấn", db_column="InterviewDate")
    interview_type = models.CharField("Hình thức", max_length=50, db_column="InterviewType")
    interviewer = models.ForeignKey(
        "hrm.Employee", verbose_name="Người phỏng vấn", on_delete=models.PROTECT,
        db_column="InterviewerID", related_name="interviews_conducted",
    )
    result = models.CharField("Kết quả", max_length=20, choices=RESULT_CHOICES, default="Pending", db_column="Result")
    comments = models.CharField("Nhận xét", max_length=1000, null=True, blank=True, db_column="Comments")

    class Meta:
        db_table = "tblInterview"
        verbose_name = "Phỏng vấn"
        verbose_name_plural = "Phỏng vấn"

    def __str__(self):
        return f"{self.candidate} - {self.interview_date}"


class Offer(BaseAuditModel):
    STATUS_CHOICES = [
        ("Sent", "Đã gửi"),
        ("Accepted", "Đã chấp nhận"),
        ("Declined", "Đã từ chối"),
    ]

    candidate = models.ForeignKey(
        Candidate, verbose_name="Ứng viên", on_delete=models.CASCADE,
        db_column="CandidateID", related_name="offers",
    )
    offer_date = models.DateField("Ngày gửi offer", db_column="OfferDate")
    expected_join_date = models.DateField("Ngày dự kiến vào làm", db_column="ExpectedJoinDate")
    salary_offer = models.DecimalField("Mức lương đề nghị", max_digits=18, decimal_places=2, db_column="SalaryOffer")
    status = models.CharField("Trạng thái", max_length=30, choices=STATUS_CHOICES, default="Sent", db_column="Status")

    class Meta:
        db_table = "tblOffer"
        verbose_name = "Thư mời làm việc"
        verbose_name_plural = "Thư mời làm việc"

    def __str__(self):
        return f"Offer - {self.candidate}"