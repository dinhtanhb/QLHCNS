# Báo cáo Rà soát Codebase QLHCNS (iHRMS)

**Ngày:** 22/09/2026
**Phạm vi:** Toàn bộ `src/` (20 app Django, ~640KB code Python), `config/`, `requirements.txt`, templates — logic, flow, bug, bảo mật, hiệu năng.
**Phương pháp:** Review trực tiếp code + 1 subagent review chuyên sâu payroll/planning.

---

## 1. Tổng quan

| Hạng mục | Đánh giá |
|---|---|
| Kiến trúc | Django 5.0.14, MTV chuẩn, 20 app nghiệp vụ, `portal` là module trung tâm (~2.400 dòng views) |
| RBAC | Tập trung duy nhất tại `apps/security/permissions.py` — thiết kế tốt |
| Tiền lương | `Decimal` xuyên suốt, làm tròn `ROUND_HALF_UP` — đúng chuẩn |
| Tests | **0 test** trên 20/20 app — rủi ro lớn nhất của dự án |
| Secrets | `.env` không commit, `db.sqlite3` không commit, `.gitignore` đúng |

---

## 2. Điểm mạnh

- **RBAC một nguồn duy nhất** (`src/apps/security/permissions.py`): bảng `PERMISSION_MATRIX` khai báo một chỗ, có doc giải thích lịch sử refactor; superuser bypass rõ ràng.
- **Chống IDOR ở công văn**: `_visible_dispatches()` (`portal/views.py:529`) dùng chung cho list + detail, chặn đọc công văn phòng khác bằng cách đổi pk trên URL.
- **Decimal cho tiền, không dùng float**: toàn bộ field tiền là `DecimalField(18,2)`, tính toán `Decimal` + `ROUND_HALF_UP` (`payroll/models.py:293,326`). `float()` chỉ xuất hiện 1 lần khi ghi Excel — chấp nhận được.
- **Chống chạy trùng kỳ lương**: `UniqueConstraint(payroll_period, employee)` + `UniqueConstraint(month, year)` + `transaction.atomic()` + `select_for_update()` (`payroll/models.py:183,210`; `portal/views.py:1846-1870`).
- **Upload an toàn** (`common/uploads.py`): whitelist extension, giới hạn 20MB, slugify tên file tiếng Việt + uuid chống ghi đè, chia thư mục theo năm/tháng.
- **Auth dùng built-in**: `LoginView`/`LogoutView` chuẩn Django (`portal/urls.py:7-8`), không tự viết password logic.
- **`select_related`/`prefetch_related` dùng rộng rãi và đúng chỗ** trong portal (~55 vị trí), `bulk_create` + `salary_map` 1 query khi sinh bảng lương.
- **Logic nghỉ phép chặt**: chống trùng ngày (`_validate_no_overlap`), giữ chỗ đơn Pending trong quỹ (`available_annual_days`), chặn nghỉ khi chưa cấp hạn mức.
- **Công thức thuế lũy tiến từng phần đúng** TT 111/2020; trần BHXH 20× lương cơ sở, BHTN 20× lương tối thiểu vùng — tách `sh_base`/`ui_base` riêng là chi tiết đúng luật.

---

## 3. Vấn đề

### 🔴 Nghiêm trọng (Critical)

**C1. Trộn thế hệ bậc thuế → tính thuế sai âm thầm khi luật đổi**
- `payroll/models.py:263-268`: filter bậc thuế lấy **mọi dòng** khớp thời điểm (`effective_to__isnull=True OR >= period`), trong khi `InsuranceRateConfig`/`TaxDeductionConfig` (dòng 249-261) chỉ lấy 1 dòng mới nhất.
- Form `finance_tax_config` (`portal/views.py:1962-1999`) **không bao giờ đóng `effective_to`** cho thế hệ cũ. Khi thêm bậc thuế mới (vd 01/01/2027), cả bậc cũ (`effective_to=NULL`) lẫn mới đều khớp filter → `bracket_no` trùng, **thuế tính đôi từng bậc**, không có lỗi hiển thị.
- **Sửa:** lấy `effective_from` mới nhất khớp trước rồi filter đúng thế hệ đó; hoặc bắt buộc đóng `effective_to` thế hệ cũ khi tạo thế hệ mới.

**C2. Cơ chế khóa kỳ lương bị Django Admin bypass toàn bộ**
- `payroll/admin.py:38-47`: action `calculate_selected` không kiểm tra `period.status == "Locked"` → tính lại lương kỳ đã chốt.
- `payroll/models.py:239-241`: `clean()` có `and self.pk` → **thêm mới** dòng `Payroll` vào kỳ Locked bị bỏ qua kiểm tra.
- FINANCE_OFFICER (`edit_roles`) đổi được status `Locked → Open`, đổi `start_date` (đổi cả thế hệ tỷ lệ thuế/BH áp dụng), và **xóa được** dòng lương kỳ khóa trong admin.
- **Sửa:** kiểm tra status trong action + `get_readonly_fields`/`has_delete_permission` nhận `obj` và chặn khi Locked; bỏ `and self.pk`; chặn đổi status ngược từ Locked.

**C3. Duyệt đề nghị thanh lý tài sản không kiểm tra quyền duyệt**
- `portal/views.py` (`disposal_request_detail`, nhánh POST `action == "approve"`): view chỉ chặn `_can_manage_asset` (HR_OFFICER trở lên) rồi **set thẳng `status = "Approved"`**. Biến `can_approve` (chỉ Giám đốc/superuser) chỉ dùng để ẩn/hiện nút trong template — gửi POST tay là HR_OFFICER tự duyệt được thanh lý.
- **Sửa:** trong nhánh `approve`, kiểm tra lại `can_approve` server-side trước khi đổi status.

**C4. Không có một dòng test nào trên toàn hệ thống**
- 20/20 file `tests.py` chỉ là placeholder `# Create your tests here`. Công thức thuế/BHXH/khấu hao/BCC — thứ dễ vỡ nhất — không có check tự động nào. Vi phạm cả quy chuẩn chính của repo (AGENTS.md: "non-trivial logic leaves ONE runnable check behind").
- **Sửa tối thiểu:** 1 test `Payroll.calculate()` với số liệu biết trước, 1 test trần BH, 1 test `standard_working_days`, 1 test quota nghỉ phép.

### 🟠 Quan trọng (Important)

**Logic / Flow**

- **I1. Điều chuyển/thăng chức hiệu lực tương lai áp dụng ngay lập tức** — `hrm/models.py` `EmployeeTransfer.save()` / `EmployeePromotion.save()`: save là đổi `employee.department`/`position` ngay, bỏ qua `effective_date`. Nhập điều chuyển hiệu lực 01/01 tới → phòng ban đổi ngay hôm nay. Flow `hr_employee_history_create` (`portal/views.py:1385+`) đi đúng đường này.
- **I2. Trưởng phòng duyệt được đơn nghỉ của chính mình** — `leave_approve` (`portal/views.py:225`) không chặn `leave_request.employee == approver`. Thêm guard: từ chối nếu đơn là của người duyệt (trừ DIRECTOR/HR_MANAGER theo quy định).
- **I3. Nhân viên tự khai số liệu ảnh hưởng BCC và nghỉ bù, không qua duyệt**
  - `timesheet_summary_update` (`portal/views.py:884+`): nhân viên tự nhập `annual_leave_days`, `sick_days`… → giảm trực tiếp `required_hours` của mình (`timesheet_month`).
  - `compensatory_days_earned` (`attendance/services.py:47`) tin hoàn toàn `TimesheetEntry` do nhân viên tự khai cuối tuần/lễ → **tự sinh ngày nghỉ bù không cần ai xác nhận**.
- **I4. Đơn nghỉ xuyên tháng/năm chỉ tính vào tháng/năm bắt đầu** — `_leave_days_in_month` (`portal/views.py:742`) và `LeaveBalance._days_by_status` (`leave/models.py:186`) đều lọc `from_date__year/month`. Nghỉ 28/12→03/01: cả 3 ngày tháng 1 tính vào quỹ năm trước.
- **I5. Cấp phát tài sản không chặn trùng** — `AssetAllocation.save()` (`asset/models.py:71`): không kiểm tra allocation đang mở của tài sản đó cho người khác; thu hồi 1 dòng thì đặt `status="Available"` dù còn dòng cấp phát mở khác.
- **I6. Thiếu tách lương tháng không tròn** — `finance_payroll_generate` (`portal/views.py:1848`) chỉ lấy `employment_status="Active"`: người nghỉ giữa tháng **vắng mặt** khỏi kỳ, người vào giữa tháng nhận **nguyên tháng**. `calculate()` không có khái niệm ngày công.
- **I7. Chọn lương cơ bản bỏ qua `effective_date` so với kỳ** — `portal/views.py:1854-1858`: lương tăng hiệu lực 01/01 bị dùng cho kỳ 12/2026; không có constraint chống 2 dòng `Active` chồng lấn của cùng nhân viên.
- **I8. `Payslip` là model chết + nhân viên thấy lương chưa chốt** — không có code nào tạo `Payslip`; `payslip_list` (`portal/views.py:263`) và `dashboard` (`latest_payroll`) không lọc `payroll_period__status="Locked"` → nhân viên thấy số lương draft.
- **I9. `EmployeeDependent` không chống trùng** — đăng ký cùng một người phụ thuộc 2 lần → giảm trừ gia cảnh nhân đôi → thiếu thu thuế (`payroll/models.py:147-165`, `portal/views.py:2005-2025`).
- **I10. Soft-dead `is_deleted` không được thi hành** — `BaseAuditModel.is_deleted` (`common/models.py:23`) tồn tại nhưng **không queryset nào** lọc `is_deleted=False`; dòng "đã xóa" vẫn được tính lương/báo cáo.
- **I11. Hoàn tất kiểm kê không kiểm tra đủ điều kiện** — `inventory_session_complete` (`portal/views.py:2155`) set `Completed` bất kể còn dòng chưa đếm; `inventory_line_update` không chặn sửa dòng của session đã Completed.
- **I12. Race khi hai người duyệt cùng một đơn** — `leave_approve` không `select_for_update` trên `LeaveRequest`; hai POST đồng thời → 2 dòng `LeaveApproval`, status cuối tùy thứ tự.

**Bảo mật / Ổn định**

- **I13. `except Exception` ~30 chỗ trong `portal/views.py`, message lỗi thô ra người dùng** — vd `portal/views.py:201,854,1896`: `messages.error(request, f"Không thể tạo đơn: {e}")` rò thông tin nội bộ (constraint name, stack). Đặc biệt `finance_payroll_calculate_all` (`portal/views.py:1896`) bắt `Exception` **bên trong** `transaction.atomic()` → lỗi DB làm transaction broken, các vòng sau nổ `TransactionManagementError` → 500. **Sửa:** bắt hẹp `ValidationError`, message tách khỏi log.
- **I14. `int()` không validate trên input người dùng → 500** — `timesheet_month` (`portal/views.py:764-765`: `?year=abc`, `?month=13`), `reporting/views.py:73,92` (`?days=abc`), `finance_period_create` (`portal/views.py:1797`: month=13). **Sửa:** helper parse an toàn kèm giá trị mặc định.
- **I15. SECRET_KEY có fallback biết trước** — `config/settings.py:26`: `os.getenv("SECRET_KEY", "fallback-insecure-key-if-missing")`. Thiếu env là chạy tiếp với key công khai (ai cũng có thể forge session cookie). **Sửa:** raise `ImproperlyConfigured` nếu thiếu. Ngoài ra chưa có `SESSION_COOKIE_HTTPONLY/SECURE_*` — chấp nhận cho intranet nhưng nên bật khi lên production.
- **I16. Phụ thuộc khai báo nhưng không dùng** — `requirements.txt`: DRF, simplejwt, django-filter, drf-spectacular, cors-headers, msal, requests không được import ở bất kỳ đâu trong `src/`. Mặt tấn công và khối lượng patch thừa. **Sửa:** xóa khỏi requirements đến khi có API thật.

### 🟡 Nhỏ (Minor)

- `payroll/models.py:290-294`: BHXH+BHYT+BHTN cộng rồi làm tròn 1 lần; thông lệ làm tròn từng khoản (lệch ≤1đ/người/tháng).
- `payroll/models.py:283-289`: có trần đóng BH nhưng **không có sàn** lương tối thiểu vùng.
- `planning/models.py:74-77`: `UniqueConstraint(year, department, category)` với `department` nullable — SQL không coi NULL=NULL nên ngân sách toàn công ty (NULL) tạo trùng được.
- `planning/models.py:60,90`: `TrainingCourse`/`Event` không validate `end > start`.
- `hrm/models.py`: `full_name` là field tự nhập, không đồng bộ `first_name`/`last_name` — dễ lệch nhau.
- `portal/views.py:2278` (`disposal_request_create`): `request_no` không validate unique trước → `IntegrityError` hiện message thô.
- `portal/views.py:1306-1309`: `hr_employee_create` gọi `_generate_next_employee_code()` 2 lần (code thừa).
- `portal/views.py:1906-1918`: khóa kỳ một chiều, không có unlock — khóa nhầm phải sửa tay DB.
- `portal/views.py:1921-1943`: `finance_payroll_update_line` không chặn giá trị âm (`allowance=-50tr` lưu được). Thêm `MinValueValidator(0)`.
- `src/apps/portal/views_backup_22092026.py` (~104KB, ~30 chỗ `except Exception`): file backup nằm ngay trong package app, chưa bị git track nhưng dễ import nhầm/lẫn lộn khi search — nên xóa hoặc移 ra ngoài repo.
- `templates/base_backup_22092026.html`: cùng vấn đề dead code.
- `payroll/admin.py:44-47`: action không `select_related`, không set `modified_by` khi tính lại lương — mất vết ai tính.

---

## 4. Hiệu năng

| # | Vị trí | Vấn đề | Ảnh hưởng |
|---|---|---|---|
| P1 | `payroll/models.py:249-303` (`Payroll.calculate`) | **4 query/nhân viên** (3 config + 1 count dependent); config giống hệt nhau cho cả kỳ | 500 người ≈ **2.000 query** mỗi lần bấm "Tính lương". Sửa: truyền config vào làm tham số, lấy 1 lần/kỳ → còn ~N+3 |
| P2 | `portal/views.py:508-510` (`document_approve`) | `for emp in Employee.objects...: notify(emp,...)` — 1 INSERT mỗi nhân viên, chạy đồng bộ trong request | 500 nhân viên = 500 query + request treo vài giây. Sửa: `bulk_create` `Notification` |
| P3 | `planning/models.py:22-27` + `planning/admin.py:14` | `actual_headcount`/`gap` là property đếm query, dùng trong `list_display` | Mỗi dòng changelist 2 query. Sửa: `annotate(Count(...))` trong `get_queryset` |
| P4 | `payroll/admin.py:38-47` | action lặp queryset không `select_related` | 2 query/dòng khi build message |

**Điểm tốt:** `select_related`/`prefetch_related` phủ rộng ở portal; `bulk_create` khi sinh bảng lương; các trang list đều lọc theo employee/phòng nên tập dữ liệu nhỏ.

---

## 5. Kết luận & Thứ tự ưu tiên

Nền tảng được thiết kế tử tế hơn mặt bằng chung: RBAC một nguồn, Decimal đúng chuẩn, chống trùng kỳ lương, upload có validate, secrets không lộ. Nhưng hệ thống **chưa an toàn để chạy kỳ lương thật**:

1. **Ngay trước kỳ lương đầu tiên:** C1 (trộn bậc thuế), C2 (admin bypass khóa kỳ), I6/I7 (proration + effective_date lương), I9 (dependent trùng).
2. **Trước khi mở rộng người dùng:** C3 (duyệt thanh lý), I2 (tự duyệt nghỉ phép), I3 (tự khai nghỉ bù), I13/I14 (500 + lỗi thô), I15 (SECRET_KEY fallback).
3. **Liên tục, bắt đầu ngay:** C4 — viết test cho công thức thuế/BHXH/BCC, mỗi sửa payroll một lần là một canh bạc không lưới an toàn.
4. **Dọn dẹp:** xóa `views_backup_22092026.py` / `base_backup_22092026.html`, gỡ dependencies không dùng khỏi `requirements.txt`, quyết định sinh `Payslip` thật hoặc bỏ model, thi hành `is_deleted` hoặc bỏ field.
