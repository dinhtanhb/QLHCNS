# IHRMS — Đặc tả kỹ thuật chi tiết cho 4 hạng mục tiếp theo

Ngày lập: 2026-09-26
Bổ sung cho: `docs/HRMS_Next_Features_Plan.md` (kế hoạch cấp chiến lược đã có trong repo — tài liệu này KHÔNG thay thế mà đi sâu xuống mức model/migration/view/test theo đúng quy ước code hiện tại: `BaseAuditModel`, `db_column` PascalCase, `db_table` tiền tố `tbl`, phân quyền tập trung trong `apps/security/permissions.py`, view function-based trong `apps/portal/views.py` +
`apps/<app>/views.py` cho app tự trị (theo mẫu `activity`).

Thứ tự triển khai giữ nguyên như tài liệu chiến lược: **1 → 4 → 2 → 3**. Mỗi hạng mục là một
đợt commit riêng, có backup trước, test + `manage.py check` + `makemigrations --check` sau,
cập nhật `docs/PROJECT_WORK_LOG.md`.

---

## Quy ước dùng chung cho cả 4 hạng mục

- App mới đặt trong `src/apps/<ten_app>/`, đăng ký vào `INSTALLED_APPS` trong `config/settings.py`.
- Mọi model kế thừa `apps.common.models.BaseAuditModel` (có sẵn `created_date`, `created_by`,
  `modified_date`, `modified_by`, `is_deleted`, `deleted_date`, `deleted_by`, soft-delete qua
  `SoftDeleteManager`/`all_objects`).
- Quyền mới khai báo **duy nhất** trong `PERMISSION_MATRIX` (`apps/security/permissions.py`);
  không viết điều kiện vai trò rải rác trong view.
- View dùng `@login_required` + kiểm tra `has_permission(request.user, "...")` ngay đầu hàm,
  trả `HttpResponseForbidden` hoặc `messages.error` + redirect khi không đủ quyền — đúng mẫu
  đang dùng trong `portal/views.py`.
- Test viết theo mẫu `apps/portal/tests.py` / `apps/activity/tests.py`: `TestCase` +
  `Client`/`self.client`, dựng fixture bằng `objects.create`, không mock DB.
- Mọi ngày giờ nghiệp vụ dùng `timezone.localdate()`/`timezone.now()`, không dùng
  `date.today()` trực tiếp trong code nghiệp vụ (bài học từ lỗi flaky test vừa sửa) — nếu cần
  "hôm nay" thì nhận qua tham số có default `None` như `send_activity_report_reminders`.

---

## Hạng mục 1 — Thông báo duyệt & nhắc việc (Notification + Outbox)

### 1.1 Phạm vi kỹ thuật

Không tạo app mới. Mở rộng app `notification` đã có (`Notification` model, hàm `notify()`).
Thêm lớp **outbox email** tách biệt, mặc định **tắt gửi thật** — theo đúng ràng buộc đã chốt:
công ty chỉ có POP3 + Outlook desktop, nên kênh gửi là "tạo bản nháp Outlook" (giống
`build_activity_proposal_email_draft` trong `apps/activity/services.py`), không phải SMTP/Graph
tự động.

### 1.2 Model (`apps/notification/models.py`)

```python
class NotificationEmailOutbox(BaseAuditModel):
    """Nhật ký & hàng chờ gửi thư cho các thông báo cần thêm kênh email.

    Giai đoạn 1: KHÔNG gửi tự động. Bản ghi ở trạng thái 'Draft' chỉ dùng để
    dựng link mailto (mở Outlook nháp) và ghi lại ai đã bấm "Đã gửi qua Outlook".
    Khi IT xác nhận có kênh gửi thật (SMTP relay hoặc Graph Mail.Send), thêm
    Celery/cron task đọc các bản ghi 'Pending' và chuyển 'Sent'/'Failed' —
    không cần đổi schema, chỉ đổi service xử lý.
    """
    STATUS_CHOICES = [
        ("Draft", "Nháp — chưa gửi"),
        ("Pending", "Đang chờ gửi (khi có kênh SMTP/Graph)"),
        ("Sent", "Đã gửi"),
        ("Failed", "Gửi lỗi"),
    ]

    notification = models.ForeignKey(
        "notification.Notification", on_delete=models.CASCADE,
        related_name="email_outbox_entries", db_column="NotificationID",
    )
    recipient_email = models.EmailField("Email người nhận", db_column="RecipientEmail")
    subject = models.CharField("Tiêu đề thư", max_length=300, db_column="Subject")
    body_text = models.TextField("Nội dung thư", db_column="BodyText")
    status = models.CharField(
        "Trạng thái", max_length=20, choices=STATUS_CHOICES, default="Draft",
        db_column="Status",
    )
    attempt_count = models.PositiveSmallIntegerField("Số lần thử", default=0, db_column="AttemptCount")
    last_attempt_at = models.DateTimeField("Lần thử gần nhất", null=True, blank=True, db_column="LastAttemptAt")
    error_message = models.CharField(
        "Lỗi (đã làm sạch, KHÔNG chứa dữ liệu lương/cá nhân)", max_length=500,
        null=True, blank=True, db_column="ErrorMessage",
    )
    idempotency_key = models.CharField(
        "Khóa chống gửi trùng", max_length=200, unique=True, db_column="IdempotencyKey",
    )
    sent_by = models.ForeignKey(
        "security.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+", db_column="SentByUserID",
    )
    sent_at = models.DateTimeField("Thời điểm xác nhận đã gửi", null=True, blank=True, db_column="SentAt")

    class Meta:
        db_table = "tblNotificationEmailOutbox"
        verbose_name = "Hàng chờ gửi email thông báo"
        verbose_name_plural = "Hàng chờ gửi email thông báo"
        indexes = [models.Index(fields=["status"])]
```

`idempotency_key` gợi ý: `f"{notification_type}:{object_type}:{object_id}:{recipient_id}"` —
tránh tạo 2 bản ghi outbox cho cùng 1 sự kiện nếu view/service bị gọi lại (double submit,
retry request).

### 1.3 Migration

`apps/notification/migrations/0002_notificationemailoutbox.py` — migration thuần tạo bảng mới,
không backfill dữ liệu, không đổi bảng `Notification` hiện có. Chạy
`python manage.py makemigrations notification` sau khi thêm model, review file sinh ra trước khi
commit (đúng quy ước "migration nhỏ, portable" trong work log).

### 1.4 Service layer (`apps/notification/services.py`)

```python
def notify_with_email_draft(
    employee, notification_type, title, message, link, email_subject, email_body,
    created_by=None,
):
    """Ghi 1 Notification trong app + 1 bản ghi outbox 'Draft' cho email.

    Dùng trong CÙNG transaction với hành động nghiệp vụ khi có thể
    (select_for_update ở nơi gọi), để không có notification "mồ côi" nếu phần
    còn lại của transaction rollback.
    """
    notification = notify(employee, notification_type, title, message, link, created_by)
    if notification is None:
        return None, None
    key = f"{notification_type}:{link}:{employee.pk}"
    email = employee.company_email or employee.personal_email
    outbox = None
    if email:
        outbox, _ = NotificationEmailOutbox.objects.get_or_create(
            idempotency_key=key,
            defaults=dict(
                notification=notification, recipient_email=email,
                subject=email_subject, body_text=email_body, status="Draft",
            ),
        )
    return notification, outbox


def build_outbox_mailto_url(outbox):
    """Tái dùng đúng cách dựng mailto: đã có trong apps/activity/services.py
    (build_activity_proposal_email_draft) — trích phần dựng URL thành hàm dùng
    chung ở apps/common/email_draft.py để tránh trùng logic urlencode giữa
    activity và notification."""
```

**Refactor đi kèm (không bắt buộc nhưng nên làm cùng đợt):** rút phần dựng `mailto:` URL trong
`apps/activity/services.py::build_activity_proposal_email_draft` ra `apps/common/email_draft.py`
làm hàm dùng chung, để hạng mục 1 không viết lại logic encode y hệt.

### 1.5 View & URL

- `apps/portal/views.py` thêm `notification_list` (đã có sẵn trang chuông thông báo theo work
  log — kiểm tra trước khi thêm, tránh trùng route) và `notification_email_outbox_mark_sent`
  (POST, chỉ cho phép người có quyền `manage_hr` hoặc chính người nhận xác nhận "đã gửi qua
  Outlook", giống cơ chế `activity_proposal` đang dùng).
- URL: `portal/urls.py` thêm
  `path("notifications/outbox/<int:pk>/mark-sent/", views.notification_email_outbox_mark_sent, name="notification_outbox_mark_sent")`.
- Áp dụng `notify_with_email_draft()` vào 3 điểm nghiệp vụ đầu tiên (đúng phạm vi đã chốt):
  `leave_approve` (khi duyệt/từ chối), `finance_payroll_lock`/`finance_payroll_calculate_all`
  (khi khóa kỳ lương — báo cho Giám đốc/Kế toán), `document`/công văn khi được duyệt.

### 1.6 Test (`apps/notification/tests.py` — hiện đang 0 test)

1. `test_notify_with_email_draft_creates_notification_and_outbox_once` — gọi 2 lần với cùng
   `idempotency_key` → chỉ 1 bản ghi outbox.
2. `test_outbox_without_employee_email_skips_gracefully` — nhân viên không có email → outbox
   `None`, không lỗi.
3. `test_mark_sent_requires_permission` — người không liên quan không thể POST đổi trạng thái
   outbox của người khác.
4. `test_leave_approve_creates_outbox_entry_for_requester` — tích hợp với `leave_approve` đã
   có ở `apps/portal/tests.py`.
5. `test_notification_link_enforces_server_side_permission` — mở lại đúng yêu cầu nghiệm thu
   trong tài liệu chiến lược: sửa URL thủ công không xem được đối tượng không có quyền.

### 1.7 Điều kiện dừng trước khi bật gửi thật

Không đổi `status` sang `Pending`/tạo cron gửi thật cho đến khi IT xác nhận kênh (SMTP relay có
xác thực, hoặc Graph `Mail.Send` + admin consent). Cho tới lúc đó, outbox chỉ phục vụ hiển thị
"bản nháp đã sẵn sàng, bấm để mở Outlook" — không có rủi ro gửi nhầm.

---

## Hạng mục 4 — Sơ đồ tổ chức & Yêu cầu tự cập nhật hồ sơ

*(làm trước hạng mục 2 theo thứ tự đã chốt, vì không phụ thuộc dữ liệu asset/checklist)*

### 4A. Sơ đồ tổ chức — không cần model mới

Dữ liệu đã đủ từ `hrm.Employee.manager` (self-FK) + `organization.Department`. Chỉ cần 1 view
đọc + 1 template, không migration.

**View** (`apps/portal/views.py`):
```python
@login_required
def org_chart(request):
    employees = (
        Employee.objects.filter(is_deleted=False, employment_status="Active")
        .select_related("department", "position", "manager")
        .only("id", "full_name", "position__position_name", "department__department_name", "manager_id")
    )
    # Dựng cây bằng dict {employee_id: [con...]} ở Python, KHÔNG đệ quy N+1 query.
    nodes = {e.id: {"employee": e, "children": []} for e in employees}
    roots = []
    for e in employees:
        if e.manager_id and e.manager_id in nodes:
            nodes[e.manager_id]["children"].append(nodes[e.id])
        else:
            roots.append(nodes[e.id])
    return render(request, "portal/org_chart.html", {"roots": roots})
```
Chỉ hiển thị `full_name`, `position`, `department`, `manager` theo đúng yêu cầu nghiệm thu
("không đưa thông tin liên lạc cá nhân lên sơ đồ mặc định"). Không cần permission riêng —
dùng chung `login_required` vì đây là thông tin nội bộ ai cũng cần biết cơ cấu, nhưng **loại
nhân viên `employment_status != Active`** để tránh lộ nhân sự đã nghỉ/đang thử việc chưa công bố
(chốt lại với HR nếu cần ẩn thêm phòng ban nhạy cảm).

**Test:** `test_org_chart_builds_tree_without_orphaning_cycles` (nhân viên tự làm quản lý của
chính mình hoặc vòng lặp quản lý — dữ liệu bẩn không được làm crash view, chỉ tách thành root
riêng), `test_org_chart_hides_inactive_employees`.

### 4B. Yêu cầu tự cập nhật hồ sơ — app mới `profile_request` (hoặc thêm vào `hrm`)

Đề xuất thêm vào `apps/hrm/models.py` (cùng domain Employee, tránh app quá nhỏ).

**Whitelist trường thực tế đang có trên `Employee`** (đã kiểm tra model, KHÔNG có sẵn trường
liên hệ khẩn cấp — cần HR xác nhận có bổ sung trường này không):
`personal_email`, `mobile_phone`, `address`.

```python
class EmployeeProfileChangeRequest(BaseAuditModel):
    ALLOWED_FIELDS = ("personal_email", "mobile_phone", "address")  # chỉnh khi HR chốt whitelist

    STATUS_CHOICES = [
        ("Draft", "Nháp"),
        ("Pending", "Chờ duyệt"),
        ("Approved", "Đã duyệt"),
        ("Rejected", "Từ chối"),
        ("NeedsMoreInfo", "Yêu cầu bổ sung"),
    ]

    employee = models.ForeignKey(
        "hrm.Employee", on_delete=models.CASCADE, related_name="profile_change_requests",
        db_column="EmployeeID",
    )
    field_name = models.CharField("Trường yêu cầu đổi", max_length=50, db_column="FieldName")
    old_value = models.CharField("Giá trị hiện tại", max_length=500, blank=True, db_column="OldValue")
    new_value = models.CharField("Giá trị đề nghị", max_length=500, db_column="NewValue")
    reason = models.CharField("Lý do", max_length=500, blank=True, db_column="Reason")
    attachment = models.FileField(
        "Chứng từ đính kèm", upload_to="profile_change_requests/%Y/%m/",
        validators=[validate_upload], null=True, blank=True, db_column="Attachment",
    )
    status = models.CharField(
        "Trạng thái", max_length=20, choices=STATUS_CHOICES, default="Pending",
        db_column="Status",
    )
    decided_by = models.ForeignKey(
        "security.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+", db_column="DecidedByUserID",
    )
    decided_at = models.DateTimeField(null=True, blank=True, db_column="DecidedAt")
    decision_note = models.CharField("Ý kiến xử lý", max_length=500, blank=True, db_column="DecisionNote")
    # Chống race condition: HR duyệt request A trong khi employee đã tạo request B đổi
    # CÙNG field — snapshot giá trị field tại thời điểm gửi để so sánh khi duyệt.
    submitted_snapshot = models.CharField(max_length=500, db_column="SubmittedSnapshot")

    class Meta:
        db_table = "tblEmployeeProfileChangeRequest"
        verbose_name = "Yêu cầu cập nhật hồ sơ"
        verbose_name_plural = "Yêu cầu cập nhật hồ sơ"

    def clean(self):
        super().clean()
        if self.field_name not in self.ALLOWED_FIELDS:
            raise ValidationError({"field_name": "Trường này không được phép tự cập nhật."})
```

### 4B.2 Migration

`apps/hrm/migrations/000X_employeeprofilechangerequest.py` — bảng mới độc lập, không đổi
`Employee`.

### 4B.3 Permissions

```python
"submit_profile_change_request": (EMPLOYEE, DEPT_MANAGER, HR_OFFICER, HR_MANAGER, DIRECTOR),  # tất cả nhân viên
"approve_profile_change_request": (HR_OFFICER, HR_MANAGER),
```

### 4B.4 View

```python
@login_required
def profile_change_request_create(request):
    ...
    # field_name lấy từ <select> giới hạn ALLOWED_FIELDS ở template — KHÔNG tin dữ liệu POST,
    # clean() ở model đã chặn lại lần 2 (I13-style: không tin input, kể cả field "chọn sẵn").

@login_required
def profile_change_request_approve(request, pk):
    _require_permission(request, "approve_profile_change_request")
    with transaction.atomic():
        req = EmployeeProfileChangeRequest.objects.select_for_update().get(pk=pk, status="Pending")
        current_value = getattr(req.employee, req.field_name)
        if str(current_value) != req.submitted_snapshot:
            messages.error(request, "Giá trị đã thay đổi kể từ lúc gửi yêu cầu — vui lòng từ chối và yêu cầu gửi lại.")
            return redirect(...)
        if request.POST.get("decision") == "approve":
            setattr(req.employee, req.field_name, req.new_value)
            req.employee.save(update_fields=[req.field_name])
            req.status = "Approved"
        else:
            req.status = "Rejected"
        req.decided_by = request.user
        req.decided_at = timezone.now()
        req.decision_note = request.POST.get("note", "")
        req.save()
    notify(req.employee, "ProfileChangeDecision", ...)
```

Dùng `select_for_update()` + so sánh `submitted_snapshot` — đúng mẫu chống race condition đã
áp dụng cho `leave_approve`/`finance_payroll_calculate_all` (I12).

### 4B.5 URL

```
path("profile/requests/new/", views.profile_change_request_create, name="profile_change_request_create"),
path("profile/requests/", views.profile_change_request_list, name="profile_change_request_list"),
path("profile/requests/<int:pk>/", views.profile_change_request_approve, name="profile_change_request_approve"),
```

### 4B.6 Test

1. `test_field_name_outside_whitelist_rejected_even_via_raw_post` — POST thẳng `field_name=salary`
   → `ValidationError`/400, không lưu.
2. `test_employee_cannot_view_others_requests` — truy cập URL id của người khác → 403/404.
3. `test_approve_applies_change_only_when_snapshot_matches` — HR sửa `Employee.address` thủ
   công giữa lúc gửi và lúc duyệt → duyệt bị chặn, có message rõ ràng.
4. `test_approve_is_atomic_and_notifies_employee`.
5. `test_org_chart_and_change_request_do_not_leak_sensitive_fields_to_template`.

---

## Hạng mục 2 — Checklist Onboarding/Offboarding

App mới: `apps/lifecycle/` (tên gợi ý; có thể đặt `onboarding` nếu muốn rõ nghĩa hơn — quyết
định cùng lúc đặt tên bảng vì đổi sau sẽ cần migration rename).

### 2.1 Model (`apps/lifecycle/models.py`)

```python
class ChecklistTemplate(BaseAuditModel):
    TEMPLATE_TYPE_CHOICES = [("Onboarding", "Tiếp nhận"), ("Offboarding", "Nghỉ việc")]
    template_code = models.CharField(max_length=50, unique=True, db_column="TemplateCode")
    template_name = models.CharField(max_length=200, db_column="TemplateName")
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPE_CHOICES, db_column="TemplateType")
    is_active = models.BooleanField(default=True, db_column="IsActive")

    class Meta:
        db_table = "tblChecklistTemplate"


class ChecklistTemplateItem(BaseAuditModel):
    template = models.ForeignKey(ChecklistTemplate, on_delete=models.CASCADE, related_name="items", db_column="TemplateID")
    sequence = models.PositiveSmallIntegerField(db_column="Sequence")
    item_name = models.CharField(max_length=300, db_column="ItemName")
    responsible_role_code = models.CharField(
        max_length=20, db_column="ResponsibleRoleCode",
        help_text="Mã vai trò chịu trách nhiệm mặc định (HR_OFFICER, DEPT_MANAGER, SYS_ADMIN...)",
    )
    due_offset_days = models.SmallIntegerField(
        default=0, db_column="DueOffsetDays",
        help_text="Số ngày lệch so với ngày hiệu lực (join_date/leave_date); âm = trước ngày hiệu lực",
    )
    requires_asset_return = models.BooleanField(default=False, db_column="RequiresAssetReturn")

    class Meta:
        db_table = "tblChecklistTemplateItem"
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(fields=["template", "sequence"], name="uq_checklist_template_item_sequence"),
        ]


class EmployeeLifecycleCase(BaseAuditModel):
    CASE_TYPE_CHOICES = [("Onboarding", "Tiếp nhận"), ("Offboarding", "Nghỉ việc")]
    STATUS_CHOICES = [("Open", "Đang xử lý"), ("Completed", "Hoàn tất"), ("Cancelled", "Hủy")]

    employee = models.ForeignKey("hrm.Employee", on_delete=models.CASCADE, related_name="lifecycle_cases", db_column="EmployeeID")
    template = models.ForeignKey(ChecklistTemplate, on_delete=models.PROTECT, db_column="TemplateID")
    case_type = models.CharField(max_length=20, choices=CASE_TYPE_CHOICES, db_column="CaseType")
    effective_date = models.DateField(db_column="EffectiveDate")  # join_date hoặc leave_date
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Open", db_column="Status")
    triggering_event_ref = models.CharField(
        max_length=100, unique=True, db_column="TriggeringEventRef",
        help_text="VD 'onboarding:EMP00123' hoặc 'offboarding:EMP00123:2026-11-01' — chống tạo hồ sơ trùng",
    )

    class Meta:
        db_table = "tblEmployeeLifecycleCase"


class LifecycleChecklistItem(BaseAuditModel):
    STATUS_CHOICES = [("Pending", "Chưa làm"), ("Done", "Hoàn tất"), ("Skipped", "Bỏ qua")]

    case = models.ForeignKey(EmployeeLifecycleCase, on_delete=models.CASCADE, related_name="items", db_column="CaseID")
    template_item = models.ForeignKey(ChecklistTemplateItem, on_delete=models.PROTECT, db_column="TemplateItemID")
    assigned_to_user = models.ForeignKey("security.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+", db_column="AssignedToUserID")
    due_date = models.DateField(null=True, blank=True, db_column="DueDate")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending", db_column="Status")
    completed_by = models.ForeignKey("security.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+", db_column="CompletedByUserID")
    completed_at = models.DateTimeField(null=True, blank=True, db_column="CompletedAt")
    skip_reason = models.CharField(max_length=500, blank=True, db_column="SkipReason")
    asset_allocation = models.ForeignKey(
        "asset.AssetAllocation", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="+", db_column="AssetAllocationID",
        help_text="Liên kết bản ghi cấp phát/thu hồi TÀI SẢN THẬT — không tự tạo/xóa lịch sử asset ở đây",
    )

    class Meta:
        db_table = "tblLifecycleChecklistItem"
```

**Vì sao tách `ChecklistTemplateItem` khỏi `LifecycleChecklistItem`:** sửa mẫu (thêm/bớt/đổi
hạn mặc định) sau này **không** làm thay đổi các case đã phát sinh — đúng điều kiện nghiệm thu
đã chốt ("Mẫu onboarding/offboarding có thể chỉnh mà không làm thay đổi checklist đã phát
sinh").

**Chống trùng hồ sơ:** `triggering_event_ref` unique — service tạo case dùng
`get_or_create(triggering_event_ref=key)`, không `create()` trần.

### 2.2 Migration

`0001_initial.py` cho app `lifecycle` — 4 bảng trên, không backfill (dữ liệu mẫu checklist tạo
qua fixture/`seed_demo_data` riêng, KHÔNG hardcode trong migration để tránh coupling schema với
dữ liệu nghiệp vụ có thể đổi).

### 2.3 Service (`apps/lifecycle/services.py`)

```python
def open_onboarding_case(employee, template, created_by=None):
    key = f"onboarding:{employee.employee_code}"
    case, created = EmployeeLifecycleCase.objects.get_or_create(
        triggering_event_ref=key,
        defaults=dict(
            employee=employee, template=template, case_type="Onboarding",
            effective_date=employee.join_date, created_by=created_by,
        ),
    )
    if created:
        _generate_items(case)
    return case, created


def open_offboarding_case(employee, template, leave_date, created_by=None):
    key = f"offboarding:{employee.employee_code}:{leave_date.isoformat()}"
    ...  # tương tự, effective_date=leave_date


def _generate_items(case):
    for template_item in case.template.items.all():
        LifecycleChecklistItem.objects.create(
            case=case, template_item=template_item,
            due_date=case.effective_date + timedelta(days=template_item.due_offset_days),
        )
```

**Điểm gọi:** `open_onboarding_case` gọi khi HR xác nhận field `employment_status` chuyển sang
"Active" lần đầu (hoặc 1 nút "Mở checklist tiếp nhận" tường minh trong HR — **không** tự động
100% vì tài liệu chiến lược ghi rõ "Không tự kích hoạt chỉ vì tạo một hồ sơ nháp"). Đề xuất: nút
tường minh trong trang chi tiết Employee, không hook vào `save()`.

`open_offboarding_case` gọi khi quyết định nghỉ việc **đã được duyệt** (không phải lúc tạo yêu
cầu nghỉ việc) — cần xác nhận với HR quy trình nghỉ việc hiện có gọi ở bước nào.

### 2.4 Permissions

```python
"manage_lifecycle_case": (HR_OFFICER, HR_MANAGER),
"view_own_lifecycle_items": (EMPLOYEE, DEPT_MANAGER, HR_OFFICER, HR_MANAGER, SYS_ADMIN, FINANCE_OFFICER),
```

### 2.5 View/URL — `apps/portal/views.py` + `portal/urls.py`

- `lifecycle_case_create` (chọn employee + template, chỉ `manage_lifecycle_case`)
- `lifecycle_case_detail` (danh sách item, người được giao chỉ sửa item của mình)
- `lifecycle_item_complete` / `lifecycle_item_skip` (POST, ghi `completed_by`/`skip_reason`)
- Dashboard: thêm số "checklist quá hạn" — dùng chung `notify()` khi item quá `due_date`
  (tái dùng pattern `send_activity_report_reminders`, viết
  `send_lifecycle_reminders(today=None)` riêng trong `lifecycle/services.py`, đăng ký management
  command `send_lifecycle_reminders` cạnh `send_activity_report_reminders` trong Task Scheduler).

### 2.6 Test (`apps/lifecycle/tests.py`)

1. `test_open_onboarding_case_generates_items_from_template_snapshot`.
2. `test_editing_template_after_case_created_does_not_change_existing_items`.
3. `test_duplicate_trigger_does_not_create_duplicate_case`.
4. `test_assigned_user_can_only_update_own_item`.
5. `test_employee_cannot_view_others_checklist_via_url`.
6. `test_completing_asset_item_links_existing_allocation_without_deleting_history`.
7. `test_overdue_items_appear_in_reminder_and_dashboard`.

---

## Hạng mục 3 — Báo cáo tuân thủ & chi phí lương theo phòng ban

**Chưa code cho tới khi có xác nhận từ Kế toán** (mẫu D02-LT hay bản thay thế hiện hành, mẫu
quyết toán PIT đúng năm, quy tắc phân bổ chi phí khi điều chuyển phòng ban) — đúng gate đã chốt.
Phần dưới là khung kỹ thuật để code nhanh **sau khi** có xác nhận, không phải để chạy ngay.

### 3.1 Kiến trúc đề xuất (mở rộng `apps/reporting/`, đã có 3 hàm Excel)

```python
# apps/reporting/services.py — thêm, KHÔNG sửa 3 hàm hiện có
def generate_insurance_change_report_excel(period, changes_queryset):
    """Khung mẫu D02-x — CHỜ Kế toán xác nhận mẫu chính thức trước khi map cột."""
    raise NotImplementedError("Chờ Kế toán cung cấp mẫu D02 chính thức trước khi triển khai")

def generate_pit_finalization_data(year):
    """Chuẩn bị data mapping cho quyết toán PIT — CHỜ mẫu/phụ lục theo năm áp dụng."""
    raise NotImplementedError("Chờ Kế toán xác nhận mẫu 05/QTT-TNCN (hoặc thay thế) cho năm áp dụng")

def generate_payroll_cost_by_department_excel(period, allocation_rule="current_department"):
    """allocation_rule: 'current_department' (mặc định, đơn giản) hoặc
    'department_at_period' (dùng lịch sử EmployeeTransfer) — CHỌN 1, không tự suy diễn."""
```

Cố tình để `NotImplementedError` với thông báo rõ ràng thay vì code "đoán" mẫu — tránh xuất báo
cáo sai biểu mẫu ra sản xuất.

### 3.2 Khi có xác nhận mẫu chính thức, việc cần làm

1. **Model:** nếu cần snapshot/chốt kỳ để tái tạo đúng bản đã xuất → thêm
   `ComplianceReportSnapshot(BaseAuditModel)` lưu `report_type`, `period`, `generated_at`,
   `generated_by`, `filters_json`, `file` (FileField), `checksum`.
2. **Permission:** `"export_compliance_report": (FINANCE_OFFICER, HR_MANAGER, DIRECTOR)`.
3. **View:** endpoint chỉ trả file khi `has_permission` đúng; ghi `ComplianceReportSnapshot` mỗi
   lần xuất (audit trail — ai xuất, khi nào, phạm vi lọc gì).
4. **Test bắt buộc trước khi release:** đối chiếu 3–5 bộ số liệu mẫu Kế toán cung cấp (input →
   output kỳ vọng), test nhân viên đổi phòng ban giữa kỳ theo đúng `allocation_rule` đã chọn,
   test người không có quyền không gọi được endpoint/không thấy link, và **chạy trên SQL Server
   SIT** (không chỉ SQLite) vì đây là báo cáo tài chính/pháp lý.

---

## Tổng hợp trình tự & gate (nhắc lại, khớp tài liệu chiến lược)

| Bước | Hạng mục | Phụ thuộc bên ngoài trước khi merge |
|---|---|---|
| 1 | Notification + outbox (draft-only) | Không có — có thể code & test ngay |
| 2 | Org chart + profile change request | HR chốt whitelist trường tự sửa (hiện chỉ có 3 trường khả dụng trên Employee) |
| 3 | Onboarding/Offboarding checklist | HR cung cấp nội dung 2 mẫu checklist + người phụ trách từng mục |
| 4 | Báo cáo BHXH/PIT/chi phí lương | Kế toán xác nhận mẫu D02, mẫu PIT theo năm, quy tắc phân bổ chi phí; chạy SIT SQL Server |

Mỗi bước: backup trước khi sửa lớn → migration riêng, nhỏ → test app liên quan +
`manage.py check` + `makemigrations --check --dry-run` → cập nhật
`docs/PROJECT_WORK_LOG.md` → commit riêng theo quy ước `AGENTS.md` hiện có.
