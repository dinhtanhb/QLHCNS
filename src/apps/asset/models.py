from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from datetime import date as calendar_date
from apps.common.models import BaseAuditModel


class AssetType(BaseAuditModel):
    GROUP_CHOICES = [("Machinery", "I. Máy móc thiết bị"), ("Other", "II. Thiết bị khác")]

    asset_type_code = models.CharField("Mã loại tài sản", max_length=50, unique=True, db_column="AssetTypeCode")
    asset_type_name = models.CharField("Tên loại tài sản", max_length=100, db_column="AssetTypeName")
    asset_group = models.CharField("Nhóm (theo mẫu kiểm kê)", max_length=20, choices=GROUP_CHOICES, default="Machinery", db_column="AssetGroup")

    class Meta:
        db_table = "tblAssetType"
        verbose_name = "Loại tài sản"
        verbose_name_plural = "Loại tài sản"

    def __str__(self):
        return self.asset_type_name


class Asset(BaseAuditModel):
    STATUS_CHOICES = [
        ("Available", "Sẵn sàng cấp phát"),
        ("InUse", "Đang sử dụng"),
        ("Maintenance", "Đang bảo trì"),
        ("Disposed", "Đã thanh lý"),
    ]
    CONDITION_CHOICES = [("Normal", "Bình thường"), ("Damaged", "Hư hỏng"), ("Lost", "Mất/Thất lạc")]

    asset_code = models.CharField("Mã số thiết bị", max_length=50, unique=True, db_column="AssetCode")
    asset_name = models.CharField("Tên thiết bị", max_length=200, db_column="AssetName")
    asset_type = models.ForeignKey(
        AssetType, verbose_name="Loại trang thiết bị", on_delete=models.PROTECT,
        db_column="AssetTypeID", related_name="assets",
    )
    location = models.CharField("Nơi sử dụng", max_length=200, null=True, blank=True, db_column="Location")
    brand = models.CharField("Nhãn hiệu", max_length=100, null=True, blank=True, db_column="Brand")
    serial_number = models.CharField("Số Seri", max_length=100, null=True, blank=True, db_column="SerialNumber")
    funding_source = models.CharField("Nguồn mua sắm", max_length=100, null=True, blank=True, db_column="FundingSource")
    purchase_date = models.DateField("Ngày mua/bàn giao", null=True, blank=True, db_column="PurchaseDate")
    quantity = models.IntegerField("Số lượng", default=1, db_column="Quantity")
    unit = models.CharField("Đơn vị tính", max_length=30, default="chiếc", db_column="Unit")
    purchase_value = models.DecimalField(
        "Giá trị (VNĐ)", max_digits=18, decimal_places=2, null=True, blank=True, db_column="PurchaseValue"
    )
    condition = models.CharField("Tình trạng", max_length=20, choices=CONDITION_CHOICES, default="Normal", db_column="Condition")
    note = models.CharField("Ghi chú", max_length=500, null=True, blank=True, db_column="Note")
    status = models.CharField("Trạng thái", max_length=30, choices=STATUS_CHOICES, default="Available", db_column="Status")

    class Meta:
        db_table = "tblAsset"
        verbose_name = "Tài sản"
        verbose_name_plural = "Tài sản"
        ordering = ["asset_type__asset_group", "asset_code"]

    def __str__(self):
        return f"{self.asset_code} - {self.asset_name}"


class AssetAllocation(BaseAuditModel):
    asset = models.ForeignKey(Asset, verbose_name="Tài sản", on_delete=models.PROTECT, db_column="AssetID", related_name="allocations")
    employee = models.ForeignKey("hrm.Employee", verbose_name="Nhân viên sử dụng", on_delete=models.PROTECT, db_column="EmployeeID", related_name="asset_allocations")
    assigned_date = models.DateField("Ngày cấp phát", db_column="AssignedDate")
    return_date = models.DateField("Ngày thu hồi", null=True, blank=True, db_column="ReturnDate")

    class Meta:
        db_table = "tblAssetAllocation"
        verbose_name = "Cấp phát tài sản"
        verbose_name_plural = "Cấp phát tài sản"

    def clean(self):
        super().clean()
        if not self.asset_id or not self.assigned_date:
            return
        overlapping = AssetAllocation.objects.filter(
            asset_id=self.asset_id,
            assigned_date__lte=self.return_date or calendar_date.max,
        ).filter(models.Q(return_date__isnull=True) | models.Q(return_date__gte=self.assigned_date))
        if self.pk:
            overlapping = overlapping.exclude(pk=self.pk)
        existing = overlapping.order_by("assigned_date").first()
        if existing:
            if existing.return_date:
                message = (
                    f"Tài sản này đã được cấp cho {existing.employee} trong khoảng "
                    f"{existing.assigned_date:%d/%m/%Y}–{existing.return_date:%d/%m/%Y}."
                )
            else:
                message = (
                    f"Tài sản này hiện đang được cấp cho {existing.employee} "
                    f"từ {existing.assigned_date:%d/%m/%Y}."
                )
            raise ValidationError({
                "asset": message,
            })

    def save(self, *args, **kwargs):
        using = kwargs.get("using") or self._state.db or "default"
        with transaction.atomic(using=using):
            previous_asset_id = None
            was_active = False
            if self.pk:
                previous = AssetAllocation.all_objects.using(using).filter(pk=self.pk).values(
                    "asset_id", "return_date"
                ).first()
                if previous:
                    previous_asset_id = previous["asset_id"]
                    was_active = previous["return_date"] is None
            asset_ids = sorted({asset_id for asset_id in (previous_asset_id, self.asset_id) if asset_id})
            locked_assets = {
                asset.pk: asset for asset in Asset.objects.using(using).select_for_update().filter(pk__in=asset_ids).order_by("pk")
            }
            self.clean()
            asset = locked_assets.get(self.asset_id)
            if asset is None:
                raise ValidationError({"asset": "Không tìm thấy tài sản đang hoạt động."})
            if self.return_date is None:
                own_active_assignment = was_active and previous_asset_id == self.asset_id
                if asset.status != "Available" and not (asset.status == "InUse" and own_active_assignment):
                    raise ValidationError({"asset": "Tài sản hiện không sẵn sàng để cấp phát."})
                if not own_active_assignment:
                    claimed = Asset.objects.using(using).filter(pk=self.asset_id, status="Available").update(
                        status="InUse", modified_date=timezone.now(),
                    )
                    if not claimed:
                        raise ValidationError({"asset": "Tài sản vừa được cấp hoặc không còn sẵn sàng."})
                    asset.status = "InUse"
            super().save(*args, **kwargs)
            for asset_id in asset_ids:
                current_asset = locked_assets[asset_id]
                has_active_allocation = AssetAllocation.objects.using(using).filter(
                    asset_id=asset_id, return_date__isnull=True,
                ).exists()
                if has_active_allocation:
                    target_status = "InUse"
                elif current_asset.status == "InUse":
                    target_status = "Available"
                else:
                    continue
                if current_asset.status != target_status:
                    current_asset.status = target_status
                    current_asset.save(update_fields=["status"], using=using)

    def __str__(self):
        return f"{self.asset} - {self.employee}"


class AssetMaintenance(BaseAuditModel):
    asset = models.ForeignKey(Asset, verbose_name="Tài sản", on_delete=models.CASCADE, db_column="AssetID", related_name="maintenances")
    maintenance_date = models.DateField("Ngày bảo trì", db_column="MaintenanceDate")
    description = models.CharField("Nội dung", max_length=500, null=True, blank=True, db_column="Description")
    cost = models.DecimalField("Chi phí", max_digits=18, decimal_places=2, null=True, blank=True, db_column="Cost")

    class Meta:
        db_table = "tblAssetMaintenance"
        verbose_name = "Bảo trì tài sản"
        verbose_name_plural = "Bảo trì tài sản"

    def __str__(self):
        return f"{self.asset} - {self.maintenance_date}"


# ============================================================
# KIỂM KÊ TÀI SẢN
# ============================================================

class InventorySession(BaseAuditModel):
    STATUS_CHOICES = [("Draft", "Đang kiểm kê"), ("Completed", "Đã hoàn tất")]

    session_name = models.CharField("Tên đợt kiểm kê", max_length=200, db_column="SessionName")
    office_name = models.CharField("Văn phòng / Bộ phận kiểm kê", max_length=200, db_column="OfficeName")
    inventory_datetime = models.DateTimeField("Thời điểm kiểm kê", db_column="InventoryDatetime")
    status = models.CharField("Trạng thái", max_length=20, choices=STATUS_CHOICES, default="Draft", db_column="Status")
    recommendation = models.CharField("Kiến nghị", max_length=500, null=True, blank=True, default="Không.", db_column="Recommendation")

    class Meta:
        db_table = "tblInventorySession"
        verbose_name = "Đợt kiểm kê tài sản"
        verbose_name_plural = "Đợt kiểm kê tài sản"
        ordering = ["-inventory_datetime"]

    def __str__(self):
        return self.session_name

    def clean(self):
        super().clean()
        if self.status != "Completed" or not self.pk:
            return
        total = self.lines.count()
        uncounted = self.lines.filter(is_counted=False).count()
        if total == 0:
            raise ValidationError("Không thể hoàn tất đợt kiểm kê chưa có tài sản nào.")
        if uncounted:
            raise ValidationError(f"Còn {uncounted} tài sản chưa kiểm đếm.")

    def save(self, *args, **kwargs):
        if self.status == "Completed":
            self.clean()
        return super().save(*args, **kwargs)


class InventoryMember(BaseAuditModel):
    ROLE_CHOICES = [("Chairman", "Trưởng ban kiểm kê"), ("Member", "Thành viên kiểm kê"), ("Recorder", "Người lập biên bản")]

    session = models.ForeignKey(InventorySession, on_delete=models.CASCADE, db_column="SessionID", related_name="members")
    employee = models.ForeignKey("hrm.Employee", verbose_name="Nhân viên", on_delete=models.PROTECT, db_column="EmployeeID")
    role = models.CharField("Vai trò", max_length=20, choices=ROLE_CHOICES, db_column="Role")

    class Meta:
        db_table = "tblInventoryMember"
        verbose_name = "Thành viên Ban kiểm kê"
        verbose_name_plural = "Thành viên Ban kiểm kê"

    def __str__(self):
        return f"{self.employee} - {self.get_role_display()}"


class InventoryLine(BaseAuditModel):
    CONDITION_CHOICES = Asset.CONDITION_CHOICES

    session = models.ForeignKey(InventorySession, on_delete=models.CASCADE, db_column="SessionID", related_name="lines")
    asset = models.ForeignKey(Asset, verbose_name="Tài sản", on_delete=models.PROTECT, db_column="AssetID")
    is_counted = models.BooleanField("Đã kiểm đếm", default=False, db_column="IsCounted")
    actual_condition = models.CharField("Tình trạng thực tế", max_length=20, choices=CONDITION_CHOICES, default="Normal", db_column="ActualCondition")
    note = models.CharField("Ghi chú kiểm kê", max_length=300, null=True, blank=True, db_column="Note")

    class Meta:
        db_table = "tblInventoryLine"
        verbose_name = "Dòng kiểm kê"
        verbose_name_plural = "Dòng kiểm kê"
        constraints = [models.UniqueConstraint(fields=["session", "asset"], name="UX_InventoryLine_Session_Asset")]

    def save(self, *args, **kwargs):
        if self.session_id and InventorySession.objects.filter(pk=self.session_id, status="Completed").exists():
            raise ValidationError("Đợt kiểm kê đã hoàn tất, không thể thay đổi dòng kiểm kê.")
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.session} - {self.asset}"


# ============================================================
# THANH LÝ TÀI SẢN
# ============================================================

class AssetDisposalRequest(BaseAuditModel):
    STATUS_CHOICES = [("Pending", "Chờ duyệt"), ("Approved", "Đã duyệt"), ("Rejected", "Từ chối"), ("Completed", "Đã hoàn tất")]
    DISPOSAL_TYPE_CHOICES = [("Liquidate", "Thanh lý"), ("Destroy", "Tiêu hủy")]

    request_no = models.CharField("Số đề nghị", max_length=50, unique=True, db_column="RequestNo")
    request_date = models.DateField("Ngày lập biên bản kiểm tra", db_column="RequestDate")
    location_name = models.CharField("Địa điểm kiểm tra", max_length=200, db_column="LocationName")
    disposal_type = models.CharField("Hình thức xử lý", max_length=20, choices=DISPOSAL_TYPE_CHOICES, default="Liquidate", db_column="DisposalType")
    reason = models.CharField(
        "Nội dung kiểm tra / lý do đề nghị", max_length=1000, db_column="Reason",
        default="Các thiết bị, dụng cụ đã được kiểm tra, đánh giá hư hỏng không thể sử dụng được.",
    )
    requested_by = models.ForeignKey("hrm.Employee", verbose_name="Người đề nghị", on_delete=models.PROTECT, db_column="RequestedBy", related_name="disposal_requests")
    status = models.CharField("Trạng thái", max_length=20, choices=STATUS_CHOICES, default="Pending", db_column="Status")

    # --- Quyết định ---
    decision_no = models.CharField("Số Quyết định xử lý", max_length=50, null=True, blank=True, db_column="DecisionNo")
    decision_date = models.DateField("Ngày ký Quyết định", null=True, blank=True, db_column="DecisionDate")
    committee_decision_no = models.CharField("Số Quyết định thành lập Hội đồng", max_length=50, null=True, blank=True, db_column="CommitteeDecisionNo")
    decided_by = models.ForeignKey(
        "hrm.Employee", verbose_name="Người ký Quyết định", null=True, blank=True, on_delete=models.SET_NULL,
        db_column="DecidedBy", related_name="disposal_decisions_signed",
    )

    # --- Biên bản tiêu hủy/thanh lý (theo cả lô) ---
    execution_datetime = models.DateTimeField("Thời điểm bắt đầu thực hiện", null=True, blank=True, db_column="ExecutionDatetime")
    execution_end_time = models.TimeField("Giờ kết thúc", null=True, blank=True, db_column="ExecutionEndTime")
    disposal_reason = models.CharField("Lý do xử lý", max_length=300, default="Hư hỏng không thể tiếp tục sử dụng", db_column="DisposalReason")
    destroy_form = models.CharField("Hình thức tiêu hủy", max_length=200, null=True, blank=True, db_column="DestroyForm")
    handling_method = models.CharField("Biện pháp xử lý sau tiêu hủy", max_length=200, null=True, blank=True, db_column="HandlingMethod")

    class Meta:
        db_table = "tblAssetDisposalRequest"
        verbose_name = "Đề nghị Thanh lý/Tiêu hủy tài sản"
        verbose_name_plural = "Đề nghị Thanh lý/Tiêu hủy tài sản"
        ordering = ["-request_date"]

    def __str__(self):
        return f"{self.request_no}"


class AssetDisposalRequestMember(BaseAuditModel):
    PARTICIPATION_CHOICES = [("Direct", "Trực tiếp"), ("VideoCall", "Video call")]
    ROLE_CHOICES = [("Chairman", "Trưởng ban"), ("Member", "Thành viên"), ("DeptInCharge", "Phụ trách bộ phận"), ("Requester", "Người đề nghị")]

    request = models.ForeignKey(AssetDisposalRequest, on_delete=models.CASCADE, db_column="RequestID", related_name="members")
    employee = models.ForeignKey("hrm.Employee", verbose_name="Nhân viên", on_delete=models.PROTECT, db_column="EmployeeID")
    participation = models.CharField("Hình thức tham gia", max_length=20, choices=PARTICIPATION_CHOICES, default="Direct", db_column="Participation")
    role = models.CharField("Vai trò trong Ban", max_length=20, choices=ROLE_CHOICES, default="Member", db_column="Role")

    class Meta:
        db_table = "tblAssetDisposalRequestMember"
        verbose_name = "Thành viên kiểm tra"
        verbose_name_plural = "Thành viên kiểm tra"

    def __str__(self):
        return f"{self.employee}"


class AssetDisposalItem(BaseAuditModel):
    request = models.ForeignKey(AssetDisposalRequest, on_delete=models.CASCADE, db_column="RequestID", related_name="items")
    asset = models.ForeignKey(Asset, verbose_name="Tài sản", on_delete=models.PROTECT, db_column="AssetID")
    damage_description = models.CharField("Tình trạng hư hỏng", max_length=500, db_column="DamageDescription")

    class Meta:
        db_table = "tblAssetDisposalItem"
        verbose_name = "Hạng mục thanh lý"
        verbose_name_plural = "Hạng mục thanh lý"

    def __str__(self):
        return f"{self.asset} - {self.damage_description}"


class AssetDisposalMinutes(BaseAuditModel):
    item = models.OneToOneField(AssetDisposalItem, on_delete=models.CASCADE, db_column="ItemID", related_name="minutes")
    decision_date = models.DateField("Ngày lập biên bản thanh lý", db_column="DecisionDate")
    origin_country = models.CharField("Nước sản xuất", max_length=100, null=True, blank=True, db_column="OriginCountry")
    manufacture_year = models.SmallIntegerField("Năm sản xuất", null=True, blank=True, db_column="ManufactureYear")
    put_into_use_year = models.SmallIntegerField("Năm đưa vào sử dụng", null=True, blank=True, db_column="PutIntoUseYear")
    original_value = models.DecimalField("Nguyên giá", max_digits=18, decimal_places=2, default=0, db_column="OriginalValue")
    depreciated_value = models.DecimalField("Giá trị hao mòn đã trích", max_digits=18, decimal_places=2, default=0, db_column="DepreciatedValue")
    conclusion = models.CharField("Kết luận của Ban thanh lý", max_length=500, db_column="Conclusion")
    disposal_cost = models.DecimalField("Chi phí thanh lý", max_digits=18, decimal_places=2, default=0, db_column="DisposalCost")
    recovery_value = models.DecimalField("Giá trị thu hồi", max_digits=18, decimal_places=2, default=0, db_column="RecoveryValue")
    director_signer = models.ForeignKey(
        "hrm.Employee", verbose_name="Giám đốc phê duyệt", null=True, blank=True, on_delete=models.SET_NULL,
        db_column="DirectorSigner", related_name="disposal_minutes_approved",
    )
    accountant_signer = models.ForeignKey(
        "hrm.Employee", verbose_name="Kế toán trưởng ký", null=True, blank=True, on_delete=models.SET_NULL,
        db_column="AccountantSigner", related_name="disposal_minutes_signed",
    )

    class Meta:
        db_table = "tblAssetDisposalMinutes"
        verbose_name = "Biên bản Thanh lý"
        verbose_name_plural = "Biên bản Thanh lý"

    @property
    def remaining_value(self):
        return self.original_value - self.depreciated_value

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.item.asset.status = "Disposed"
        self.item.asset.save(update_fields=["status"])

    def __str__(self):
        return f"Biên bản thanh lý - {self.item.asset}"
