from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from apps.common.models import BaseAuditModel
from apps.common.uploads import upload_to_incoming_docs, upload_to_outgoing_docs, validate_upload
from apps.m365.storage import get_storage


# ============================================================
# 1. CÔNG VĂN ĐẾN / ĐI
# ============================================================

class IncomingDocument(BaseAuditModel):
    STATUS_CHOICES = [("New", "Mới nhận"), ("Processing", "Đang xử lý"), ("Done", "Đã xử lý xong")]

    incoming_no = models.CharField("Số công văn đến", max_length=50, unique=True, db_column="IncomingNo")
    incoming_date = models.DateField("Ngày nhận", db_column="IncomingDate")
    sender = models.CharField("Nơi gửi", max_length=300, db_column="Sender")
    subject = models.CharField("Trích yếu / Nội dung", max_length=500, db_column="Subject")
    received_by = models.ForeignKey(
        "hrm.Employee", verbose_name="Người tiếp nhận", on_delete=models.PROTECT,
        db_column="ReceivedBy", related_name="incoming_documents_received",
    )
    handler = models.ForeignKey(
        "hrm.Employee", verbose_name="Người xử lý", null=True, blank=True, on_delete=models.SET_NULL,
        db_column="HandlerID", related_name="incoming_documents_handled",
    )
    due_date = models.DateField("Hạn xử lý", null=True, blank=True, db_column="DueDate")
    attachment = models.FileField(
        "Tệp đính kèm", upload_to=upload_to_incoming_docs,
        validators=[validate_upload], null=True, blank=True,
        storage=get_storage("incoming_docs"),
    )
    status = models.CharField("Trạng thái", max_length=30, choices=STATUS_CHOICES, default="New", db_column="Status")
    note = models.CharField("Ghi chú", max_length=500, null=True, blank=True, db_column="Note")

    class Meta:
        db_table = "tblIncomingDocument"
        verbose_name = "Công văn đến"
        verbose_name_plural = "Sổ công văn đến"
        ordering = ["-incoming_date"]

    def __str__(self):
        return f"{self.incoming_no} - {self.subject}"

class OutgoingDocument(BaseAuditModel):
    outgoing_no = models.CharField("Số công văn đi", max_length=50, unique=True, db_column="OutgoingNo")
    outgoing_date = models.DateField("Ngày gửi", db_column="OutgoingDate")
    recipient = models.CharField("Nơi nhận", max_length=300, db_column="Recipient")
    subject = models.CharField("Trích yếu / Nội dung", max_length=500, db_column="Subject")
    drafted_by = models.ForeignKey(
        "hrm.Employee", verbose_name="Người soạn thảo", null=True, blank=True, on_delete=models.SET_NULL,
        db_column="DraftedBy", related_name="outgoing_documents_drafted",
    )
    signed_by = models.ForeignKey(
        "hrm.Employee", verbose_name="Người ký", on_delete=models.PROTECT,
        db_column="SignedBy", related_name="outgoing_documents_signed",
    )
    related_incoming = models.ForeignKey(
        IncomingDocument, verbose_name="Công văn đến liên quan", null=True, blank=True,
        on_delete=models.SET_NULL, db_column="RelatedIncomingID", related_name="outgoing_replies",
    )
    attachment = models.FileField(
        "Tệp đính kèm", upload_to=upload_to_outgoing_docs,
        validators=[validate_upload], null=True, blank=True,
        storage=get_storage("outgoing_docs"),
    )
    note = models.CharField("Ghi chú", max_length=500, null=True, blank=True, db_column="Note")

    class Meta:
        db_table = "tblOutgoingDocument"
        verbose_name = "Công văn đi"
        verbose_name_plural = "Sổ công văn đi"
        ordering = ["-outgoing_date"]

    def __str__(self):
        return f"{self.outgoing_no} - {self.subject}"


# ============================================================
# 2. PHÒNG HỌP / XE
# ============================================================

class MeetingRoom(BaseAuditModel):
    room_code = models.CharField("Mã phòng", max_length=50, unique=True, db_column="RoomCode")
    room_name = models.CharField("Tên phòng", max_length=200, db_column="RoomName")
    capacity = models.SmallIntegerField("Sức chứa (người)", default=10, db_column="Capacity")
    location = models.CharField("Vị trí", max_length=200, null=True, blank=True, db_column="Location")
    is_active = models.BooleanField("Đang sử dụng", default=True, db_column="IsActive")

    class Meta:
        db_table = "tblMeetingRoom"
        verbose_name = "Phòng họp"
        verbose_name_plural = "Phòng họp"

    def __str__(self):
        return self.room_name


class Vehicle(BaseAuditModel):
    vehicle_code = models.CharField("Mã xe", max_length=50, unique=True, db_column="VehicleCode")
    vehicle_name = models.CharField("Tên xe", max_length=200, db_column="VehicleName")
    plate_number = models.CharField("Biển số", max_length=20, db_column="PlateNumber")
    capacity = models.SmallIntegerField("Số chỗ ngồi", default=4, db_column="Capacity")
    is_active = models.BooleanField("Đang sử dụng", default=True, db_column="IsActive")

    class Meta:
        db_table = "tblVehicle"
        verbose_name = "Xe công ty"
        verbose_name_plural = "Xe công ty"

    def __str__(self):
        return f"{self.vehicle_name} ({self.plate_number})"


class RoomBooking(BaseAuditModel):
    STATUS_CHOICES = [
        ("Pending", "Chờ duyệt"), ("Approved", "Đã duyệt"),
        ("Rejected", "Từ chối"), ("Cancelled", "Đã hủy"),
    ]

    room = models.ForeignKey(MeetingRoom, verbose_name="Phòng họp", on_delete=models.PROTECT, db_column="RoomID", related_name="bookings")
    employee = models.ForeignKey("hrm.Employee", verbose_name="Người đặt", on_delete=models.PROTECT, db_column="EmployeeID", related_name="room_bookings")
    purpose = models.CharField("Mục đích", max_length=300, db_column="Purpose")
    start_time = models.DateTimeField("Bắt đầu", db_column="StartTime")
    end_time = models.DateTimeField("Kết thúc", db_column="EndTime")
    status = models.CharField("Trạng thái", max_length=30, choices=STATUS_CHOICES, default="Pending", db_column="Status")

    class Meta:
        db_table = "tblRoomBooking"
        verbose_name = "Đặt phòng họp"
        verbose_name_plural = "Đặt phòng họp"
        ordering = ["start_time"]

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("Giờ kết thúc phải sau giờ bắt đầu.")
        conflict = RoomBooking.objects.filter(
            room=self.room, status="Approved", start_time__lt=self.end_time, end_time__gt=self.start_time,
        ).exclude(pk=self.pk)
        if conflict.exists():
            raise ValidationError(f"Phòng đã được đặt trong khung giờ này bởi {conflict.first().employee}.")

    def __str__(self):
        return f"{self.room} - {self.employee} ({self.start_time:%d/%m %H:%M})"


class VehicleBooking(BaseAuditModel):
    STATUS_CHOICES = [
        ("Pending", "Chờ duyệt"), ("Approved", "Đã đặt"),
        ("Rejected", "Từ chối"), ("Cancelled", "Đã hủy"),
    ]

    vehicle = models.ForeignKey(Vehicle, verbose_name="Xe", on_delete=models.PROTECT, db_column="VehicleID", related_name="bookings")
    employee = models.ForeignKey("hrm.Employee", verbose_name="Người đặt", on_delete=models.PROTECT, db_column="EmployeeID", related_name="vehicle_bookings")
    destination = models.CharField("Điểm đến", max_length=300, db_column="Destination")
    purpose = models.CharField("Mục đích", max_length=300, null=True, blank=True, db_column="Purpose")
    start_time = models.DateTimeField("Bắt đầu", db_column="StartTime")
    end_time = models.DateTimeField("Kết thúc", db_column="EndTime")
    status = models.CharField("Trạng thái", max_length=30, choices=STATUS_CHOICES, default="Pending", db_column="Status")

    class Meta:
        db_table = "tblVehicleBooking"
        verbose_name = "Đặt xe"
        verbose_name_plural = "Đặt xe"
        ordering = ["start_time"]

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("Giờ kết thúc phải sau giờ bắt đầu.")
        conflict = VehicleBooking.objects.filter(
            vehicle=self.vehicle, status="Approved", start_time__lt=self.end_time, end_time__gt=self.start_time,
        ).exclude(pk=self.pk)
        if conflict.exists():
            raise ValidationError(f"Xe đã được đặt trong khung giờ này bởi {conflict.first().employee}.")

    def __str__(self):
        return f"{self.vehicle} - {self.employee} ({self.start_time:%d/%m %H:%M})"


# ============================================================
# 3. VĂN PHÒNG PHẨM & KHO NHỎ
# ============================================================

class SupplyItem(BaseAuditModel):
    item_code = models.CharField("Mã vật tư", max_length=50, unique=True, db_column="ItemCode")
    item_name = models.CharField("Tên vật tư", max_length=200, db_column="ItemName")
    unit = models.CharField("Đơn vị tính", max_length=30, default="Cái", db_column="Unit")
    quantity_in_stock = models.IntegerField("Số lượng tồn kho", default=0, db_column="QuantityInStock", validators=[MinValueValidator(0)])
    min_stock_alert = models.IntegerField("Mức cảnh báo tồn tối thiểu", default=5, db_column="MinStockAlert")

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(quantity_in_stock__gte=0), name="CK_SupplyItem_Stock_Nonnegative")]
        db_table = "tblSupplyItem"
        verbose_name = "Vật tư văn phòng"
        verbose_name_plural = "Vật tư văn phòng"

    def __str__(self):
        return f"{self.item_name} (tồn: {self.quantity_in_stock})"


class SupplyRequest(BaseAuditModel):
    STATUS_CHOICES = [("Pending", "Chờ duyệt"), ("Approved", "Đã duyệt"), ("Issued", "Đã cấp phát"), ("Rejected", "Từ chối")]

    request_no = models.CharField("Số đề nghị", max_length=50, unique=True, db_column="RequestNo")
    employee = models.ForeignKey("hrm.Employee", verbose_name="Người đề nghị", on_delete=models.PROTECT, db_column="EmployeeID", related_name="supply_requests")
    request_date = models.DateField("Ngày đề nghị", db_column="RequestDate")
    status = models.CharField("Trạng thái", max_length=30, choices=STATUS_CHOICES, default="Pending", db_column="Status")

    class Meta:
        db_table = "tblSupplyRequest"
        verbose_name = "Đề nghị cấp VPP"
        verbose_name_plural = "Đề nghị cấp VPP"
        ordering = ["-request_date"]

    def __str__(self):
        return f"{self.request_no} - {self.employee}"


class SupplyRequestItem(BaseAuditModel):
    supply_request = models.ForeignKey(SupplyRequest, on_delete=models.CASCADE, db_column="SupplyRequestID", related_name="items")
    item = models.ForeignKey(SupplyItem, verbose_name="Vật tư", on_delete=models.PROTECT, db_column="ItemID")
    quantity_requested = models.IntegerField("Số lượng đề nghị", default=1, db_column="QuantityRequested", validators=[MinValueValidator(1)])
    quantity_issued = models.IntegerField("Số lượng đã cấp", default=0, db_column="QuantityIssued", validators=[MinValueValidator(0)])

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity_requested__gte=1), name="CK_SupplyLine_Requested_Positive"),
            models.CheckConstraint(condition=models.Q(quantity_issued__gte=0) & models.Q(quantity_issued__lte=models.F("quantity_requested")), name="CK_SupplyLine_Issued_Range"),
        ]
        db_table = "tblSupplyRequestItem"
        verbose_name = "Hạng mục vật tư"
        verbose_name_plural = "Hạng mục vật tư"

    def __str__(self):
        return f"{self.item} x{self.quantity_requested}"


# ============================================================
# 4. CON DẤU / KÝ SỐ
# ============================================================

class SealUsageLog(BaseAuditModel):
    SEAL_TYPE_CHOICES = [("RoundSeal", "Dấu tròn công ty"), ("TitleSeal", "Dấu chức danh"), ("DigitalSignature", "Chữ ký số")]

    seal_type = models.CharField("Loại con dấu/chữ ký", max_length=30, choices=SEAL_TYPE_CHOICES, db_column="SealType")
    used_by = models.ForeignKey("hrm.Employee", verbose_name="Người sử dụng", on_delete=models.PROTECT, db_column="UsedBy", related_name="seal_usages")
    used_date = models.DateTimeField("Thời gian sử dụng", db_column="UsedDate")
    document_reference = models.CharField("Văn bản/Tài liệu liên quan", max_length=300, db_column="DocumentReference")
    purpose = models.CharField("Mục đích sử dụng", max_length=500, db_column="Purpose")
    approved_by = models.ForeignKey(
        "hrm.Employee", verbose_name="Người phê duyệt", null=True, blank=True, on_delete=models.SET_NULL,
        db_column="ApprovedBy", related_name="seal_usages_approved",
    )

    class Meta:
        db_table = "tblSealUsageLog"
        verbose_name = "Nhật ký sử dụng con dấu/ký số"
        verbose_name_plural = "Nhật ký sử dụng con dấu/ký số"
        ordering = ["-used_date"]

    def __str__(self):
        return f"{self.get_seal_type_display()} - {self.used_by} ({self.used_date:%d/%m/%Y})"
