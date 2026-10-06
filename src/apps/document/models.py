from django.db import models
from apps.common.models import BaseAuditModel
from apps.common.uploads import (
    upload_to_dispatches,
    upload_to_documents,
    upload_to_personnel_decisions,
    validate_decision_pdf,
    validate_upload,
)
from apps.m365.storage import get_storage


class DocumentCategory(BaseAuditModel):
    category_code = models.CharField("Mã danh mục", max_length=50, unique=True, db_column="CategoryCode")
    category_name = models.CharField("Tên danh mục", max_length=200, db_column="CategoryName")

    class Meta:
        db_table = "tblDocumentCategory"
        verbose_name = "Danh mục tài liệu"
        verbose_name_plural = "Danh mục tài liệu"

    def __str__(self):
        return self.category_name


class Document(BaseAuditModel):
    STATUS_CHOICES = [
        ("Draft", "Nháp"),
        ("PendingApproval", "Chờ phê duyệt"),
        ("Approved", "Đã ban hành"),
        ("Rejected", "Từ chối"),
    ]

    document_no = models.CharField("Số hiệu văn bản", max_length=50, unique=True, db_column="DocumentNo")
    document_name = models.CharField("Tên tài liệu", max_length=300, db_column="DocumentName")
    category = models.ForeignKey(
        DocumentCategory, verbose_name="Danh mục", on_delete=models.PROTECT,
        db_column="CategoryID", related_name="documents",
    )
    version_no = models.CharField("Phiên bản", max_length=20, default="1.0", db_column="VersionNo")
    effective_date = models.DateField("Ngày hiệu lực", null=True, blank=True, db_column="EffectiveDate")
    uploaded_file = models.FileField(
        "Tệp đính kèm", upload_to=upload_to_documents,
        validators=[validate_upload], null=True, blank=True,
        storage=get_storage("documents"),
    )
    document_url = models.CharField("Đường dẫn tài liệu", max_length=500, null=True, blank=True, db_column="DocumentUrl")
    status = models.CharField("Trạng thái", max_length=30, choices=STATUS_CHOICES, default="Draft", db_column="Status")

    class Meta:
        db_table = "tblDocument"
        verbose_name = "Tài liệu"
        verbose_name_plural = "Tài liệu"

    @property
    def safe_document_url(self):
        from urllib.parse import urlsplit
        url = self.document_url or ""
        if any(ord(char) < 32 for char in url):
            return ""
        try:
            parsed = urlsplit(url)
            if parsed.scheme in ("http", "https") and parsed.hostname and not parsed.username and not parsed.password:
                return url
        except ValueError:
            pass
        return ""

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.uploaded_file and self.uploaded_file.url != self.document_url:
            self.document_url = self.uploaded_file.url
            super().save(update_fields=["document_url"])

    def __str__(self):
        return f"{self.document_no} - {self.document_name} (v{self.version_no})"


class DocumentApproval(BaseAuditModel):
    DECISION_CHOICES = [("Approved", "Duyệt"), ("Rejected", "Từ chối")]

    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, db_column="DocumentID", related_name="approvals"
    )
    approver = models.ForeignKey(
        "hrm.Employee", on_delete=models.PROTECT, db_column="ApproverID", related_name="document_approvals"
    )
    approval_date = models.DateTimeField("Thời gian duyệt", auto_now_add=True, db_column="ApprovalDate")
    decision = models.CharField("Quyết định", max_length=20, choices=DECISION_CHOICES, db_column="Decision")

    class Meta:
        db_table = "tblDocumentApproval"
        verbose_name = "Lịch sử duyệt tài liệu"
        verbose_name_plural = "Lịch sử duyệt tài liệu"

    def __str__(self):
        return f"{self.document} - {self.get_decision_display()} bởi {self.approver}"


class PersonnelDecision(BaseAuditModel):
    STATUS_CHOICES = [
        ("Draft", "Bản nháp"),
        ("PendingApproval", "Chờ duyệt"),
        ("Approved", "Đã duyệt"),
        ("Rejected", "Từ chối"),
        ("Issued", "Đã ban hành"),
        ("Cancelled", "Đã hủy"),
    ]

    employee = models.ForeignKey(
        "hrm.Employee", on_delete=models.PROTECT, db_column="EmployeeID", related_name="personnel_decisions"
    )
    template_slug = models.SlugField(max_length=80, db_column="TemplateSlug")
    decision_no = models.CharField("Số quyết định", max_length=100, blank=True, db_column="DecisionNo")
    decision_date = models.DateField("Ngày quyết định", null=True, blank=True, db_column="DecisionDate")
    effective_date = models.DateField("Ngày hiệu lực", null=True, blank=True, db_column="EffectiveDate")
    content_snapshot = models.JSONField(default=dict, db_column="ContentSnapshot")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="Draft", db_column="Status")
    issued_file = models.FileField(
        "Bản PDF đã ký", upload_to=upload_to_personnel_decisions,
        validators=[validate_decision_pdf], null=True, blank=True,
        storage=get_storage("documents"),
    )
    issued_at = models.DateTimeField(null=True, blank=True, db_column="IssuedAt")

    class Meta:
        db_table = "tblPersonnelDecision"
        ordering = ["-created_date", "-id"]
        verbose_name = "Quyết định nhân sự"
        verbose_name_plural = "Quyết định nhân sự"

    def __str__(self):
        return f"{self.decision_no or self.template_slug} - {self.employee}"


class PersonnelDecisionHistory(BaseAuditModel):
    ACTION_CHOICES = [
        ("DraftCreated", "Tạo bản nháp"),
        ("DraftUpdated", "Cập nhật bản nháp"),
        ("Submitted", "Trình duyệt"),
        ("Approved", "Duyệt"),
        ("Rejected", "Từ chối"),
        ("Issued", "Ban hành"),
        ("Cancelled", "Hủy"),
    ]

    decision = models.ForeignKey(
        PersonnelDecision, on_delete=models.PROTECT, db_column="DecisionID", related_name="history"
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES, db_column="Action")
    status_from = models.CharField(max_length=30, blank=True, db_column="StatusFrom")
    status_to = models.CharField(max_length=30, db_column="StatusTo")
    comment = models.TextField(blank=True, db_column="Comment")

    class Meta:
        db_table = "tblPersonnelDecisionHistory"
        ordering = ["created_date", "id"]
        verbose_name = "Lịch sử quyết định nhân sự"
        verbose_name_plural = "Lịch sử quyết định nhân sự"

    def get_status_to_display(self):
        return dict(PersonnelDecision.STATUS_CHOICES).get(self.status_to, self.status_to)


class DispatchBook(BaseAuditModel):
    """Sổ công văn / Sổ theo dõi văn bản đến - đi theo năm."""
    BOOK_TYPE_CHOICES = [
        ("Incoming", "Sổ công văn đến"),
        ("Outgoing", "Sổ công văn đi"),
        ("Internal", "Sổ văn bản nội bộ"),
    ]

    book_code = models.CharField("Mã sổ", max_length=50, unique=True, db_column="BookCode")
    book_name = models.CharField("Tên sổ văn bản", max_length=200, db_column="BookName")
    book_type = models.CharField("Loại sổ", max_length=20, choices=BOOK_TYPE_CHOICES, db_column="BookType")
    year = models.PositiveSmallIntegerField("Năm theo dõi", db_column="Year")
    current_number = models.PositiveIntegerField("Số hiện tại", default=0, db_column="CurrentNumber")
    is_active = models.BooleanField("Đang sử dụng", default=True, db_column="IsActive")
    description = models.CharField("Mô tả / Ghi chú", max_length=500, null=True, blank=True, db_column="Description")

    class Meta:
        db_table = "tblDispatchBook"
        verbose_name = "Sổ văn bản"
        verbose_name_plural = "Sổ văn bản"
        constraints = [
            models.UniqueConstraint(fields=["book_type", "year"], name="UX_DispatchBook_Type_Year")
        ]

    def __str__(self):
        return f"{self.book_name} ({self.year})"


class OfficialDispatch(BaseAuditModel):
    """Văn bản / Công văn đến và đi trong quản lý hành chính."""
    DISPATCH_TYPE_CHOICES = [
        ("Incoming", "Công văn đến"),
        ("Outgoing", "Công văn đi"),
        ("InternalDirective", "Văn bản chỉ đạo nội bộ"),
    ]
    URGENCY_CHOICES = [
        ("Normal", "Thường"),
        ("Urgent", "Khẩn"),
        ("VeryUrgent", "Thượng khẩn"),
        ("TopUrgent", "Hỏa tốc"),
    ]
    SECURITY_CHOICES = [
        ("Normal", "Thường"),
        ("Confidential", "Mật"),
        ("TopSecret", "Tuyệt mật"),
    ]
    STATUS_CHOICES = [
        ("Pending", "Chờ phân công / xử lý"),
        ("Processing", "Đang xử lý"),
        ("Completed", "Đã hoàn thành"),
        ("Archived", "Đã lưu trữ"),
        ("Overdue", "Quá hạn"),
    ]

    dispatch_type = models.CharField("Loại văn bản", max_length=25, choices=DISPATCH_TYPE_CHOICES, db_column="DispatchType")
    dispatch_book = models.ForeignKey(
        DispatchBook, verbose_name="Sổ công văn", on_delete=models.PROTECT,
        db_column="DispatchBookID", related_name="dispatches"
    )
    dispatch_no = models.CharField("Số công văn", max_length=100, db_column="DispatchNo", help_text="Số vào sổ hoặc số phát hành")
    original_doc_no = models.CharField(
        "Số hiệu văn bản gốc", max_length=100, null=True, blank=True, db_column="OriginalDocNo",
        help_text="Số hiệu của cơ quan ban hành (đối với công văn đến)"
    )
    title = models.CharField("Trích yếu nội dung", max_length=500, db_column="Title")
    issuing_organization = models.CharField("Cơ quan / Đơn vị ban hành", max_length=250, db_column="IssuingOrganization")
    issue_date = models.DateField("Ngày ban hành", db_column="IssueDate")
    received_or_sent_date = models.DateField("Ngày đến / Ngày gửi", db_column="ReceivedOrSentDate")
    
    # Phân cấp khẩn / mật
    urgency_level = models.CharField("Độ khẩn", max_length=20, choices=URGENCY_CHOICES, default="Normal", db_column="UrgencyLevel")
    security_level = models.CharField("Độ mật", max_length=20, choices=SECURITY_CHOICES, default="Normal", db_column="SecurityLevel")

    # Phân công trách nhiệm xử lý
    department = models.ForeignKey(
        "organization.Department", verbose_name="Phòng ban chủ trì", null=True, blank=True,
        on_delete=models.SET_NULL, db_column="DepartmentID", related_name="assigned_dispatches"
    )
    assigned_to = models.ForeignKey(
        "hrm.Employee", verbose_name="Người phụ trách chính", null=True, blank=True,
        on_delete=models.SET_NULL, db_column="AssignedToID", related_name="responsible_dispatches"
    )
    signer = models.ForeignKey(
        "hrm.Employee", verbose_name="Người ký phát hành (nếu có)", null=True, blank=True,
        on_delete=models.SET_NULL, db_column="SignerID", related_name="signed_dispatches"
    )

    due_date = models.DateField("Hạn xử lý", null=True, blank=True, db_column="DueDate")
    status = models.CharField("Trạng thái", max_length=30, choices=STATUS_CHOICES, default="Pending", db_column="Status")
    leadership_directive = models.TextField("Bút phê / Ý kiến chỉ đạo", null=True, blank=True, db_column="LeadershipDirective")
    
    # File scan / tài liệu đính kèm
    attachment = models.FileField(
        "Tệp đính kèm scan", upload_to=upload_to_dispatches,
        validators=[validate_upload], null=True, blank=True,
        storage=get_storage("dispatches"),
    )
    
    # Liên kết phúc đáp (Văn bản này trả lời cho văn bản nào)
    reply_to = models.ForeignKey(
        "self", verbose_name="Văn bản phúc đáp cho", null=True, blank=True,
        on_delete=models.SET_NULL, db_column="ReplyToID", related_name="replies"
    )

    class Meta:
        db_table = "tblOfficialDispatch"
        verbose_name = "Công văn & Văn bản hành chính"
        verbose_name_plural = "Công văn & Văn bản hành chính"
        ordering = ["-received_or_sent_date", "-id"]

    def __str__(self):
        return f"[{self.get_dispatch_type_display()}] {self.dispatch_no} - {self.title[:60]}"


class DispatchTracking(BaseAuditModel):
    """Lịch sử luân chuyển, xử lý công văn giữa các phòng ban / cá nhân."""
    dispatch = models.ForeignKey(
        OfficialDispatch, verbose_name="Công văn", on_delete=models.CASCADE,
        db_column="DispatchID", related_name="trackings"
    )
    actor = models.ForeignKey(
        "hrm.Employee", verbose_name="Người thực hiện", on_delete=models.PROTECT,
        db_column="ActorID", related_name="dispatch_actions"
    )
    action_type = models.CharField("Hành động", max_length=100, db_column="ActionType", help_text="Chỉ đạo, Chuyển tiếp, Đã duyệt, Đã xử lý, Đóng...")
    comment = models.TextField("Nội dung xử lý / Ý kiến", null=True, blank=True, db_column="Comment")
    action_date = models.DateTimeField("Thời gian", auto_now_add=True, db_column="ActionDate")

    class Meta:
        db_table = "tblDispatchTracking"
        verbose_name = "Luân chuyển công văn"
        verbose_name_plural = "Luân chuyển công văn"
        ordering = ["-action_date"]

    def __str__(self):
        return f"{self.dispatch.dispatch_no} - {self.action_type} bởi {self.actor}"
