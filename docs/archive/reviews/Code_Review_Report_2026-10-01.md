# Báo cáo Rà soát Codebase QLHCNS (iHRMS) — Lần 2

**Ngày:** 01/10/2026
**Phạm vi:** Toàn bộ `src/` sau chuỗi commit từ `38f0990` → `8258a3e` (fix nghiệp vụ + 3 file test, fix Công văn, nâng cấp Django 5.2.17, chuyển SQL Server, tích hợp SharePoint/Graph, phiếu lương PDF, soft-delete, middleware áp dụng điều chuyển theo ngày hiệu lực).
**Phương pháp:** Review trực tiếp code + đối chiếu từng mục của báo cáo 22/09/2026 (`docs/Code_Review_Report_2026-09-22.md`) + chạy thực tế `manage.py test` (86 test, OK) và `manage.py check --deploy`.

---

## 1. Kết quả đối chiếu báo cáo lần trước

### Đã sửa đúng và có test bảo vệ ✅

| Mục cũ | Trạng thái | Bằng chứng |
|---|---|---|
| **C1** Trộn thế hệ bậc thuế | ✅ Đã sửa | `payroll/models.py:355-363`: lấy `effective_from` mới nhất rồi filter đúng 1 thế hệ; `finance_tax_config` tự đóng `effective_to` thế hệ cũ; regression test `TaxBracketGenerationTests` tái hiện đúng kịch bản gây bug |
| **C2** Admin bypass khóa kỳ | ✅ Đã sửa | `payroll/admin.py`: `PayrollPeriodAdmin`/`PayrollAdmin` chặn change/delete khi Locked (SUPER_ADMIN được phép khẩn cấp); action `calculate_selected` bỏ qua dòng kỳ khóa; `clean()` bỏ `and self.pk` — có test `test_khong_duoc_tao_moi_bang_luong_cho_ky_da_khoa` |
| **C3** Duyệt thanh lý không kiểm quyền | ✅ Đã sửa | `_can_approve_disposal()` tách khỏi `manage_asset`, kiểm server-side trong nhánh `approve` + `select_for_update` + chỉ duyệt đơn Pending |
| **C4** 0 test | ✅ Cải thiện lớn | **86 test** (payroll 21, leave 33, security 18, asset 4, hrm 3, m365 5, common 2) — chạy `manage.py test`: **Ran 86 tests, OK** |
| **I1** Điều chuyển áp dụng ngay | ✅ Đã sửa | `hrm/services.py: apply_due_employee_changes()` + middleware chạy 1 lần/ngày + `EmployeeTransfer.save()` chỉ áp dụng khi đến hạn — có 3 test |
| **I2** Tự duyệt đơn nghỉ | ✅ Đã sửa | `leave_approve` chặn DEPT_MANAGER duyệt đơn của chính mình |
| **I3** Tự khai số liệu BCC | ✅ Đã sửa | `MonthlyAttendanceSummary` thêm trạng thái Pending/Approved + người duyệt; payroll và báo cáo BCC chỉ dùng số liệu Approved; nhân viên không sửa được bảng đã duyệt |
| **I4** Đơn nghỉ xuyên tháng/năm | ✅ Đã sửa | `leave_days_in_year`/`leave_days_in_month` chia đúng theo từng năm/tháng; `_validate_quota` kiểm từng năm — có 3 test |
| **I5** Cấp phát tài sản trùng | ✅ Đã sửa | `AssetAllocation.clean()` chống chồng lấn + `save()` dùng `select_for_update` + claim atomic — có 2 test |
| **I6** Thiếu tách lương | ✅ Đã sửa | `Payroll.calculate()`: proration theo `join_date`/`leave_date`/`unpaid_days` (migration `0003_payroll_working_days_proration`) |
| **I7** Lương bỏ qua effective_date | ✅ Đã sửa | `finance_payroll_generate` filter `effective_date__lte=period.start_date` + `end_date`; `hr_salary_create` đóng dòng Active cũ bằng `select_for_update` |
| **I8** Payslip chết + lộ lương draft | ✅ Đã sửa | `finance_payroll_lock` bulk_create Payslip + phát hành PDF (`payslip_pdf.py`, reportlab, font VN); `payslip_list`/`dashboard` chỉ hiện kỳ Locked + có Payslip; `payslip_pdf` chặn IDOR + `no-store` |
| **I9** Dependent trùng | ✅ Đã sửa | `EmployeeDependent._validate_no_overlap()` chống trùng họ tên + thời gian |
| **I10** `is_deleted` không thi hành | ✅ Đã sửa | `SoftDeleteQuerySet`/`SoftDeleteManager`/`all_objects`/`restore()` trong `common/models.py`; admin có action xóa mềm/khôi phục — có 2 test |
| **I11** Kiểm kê hoàn tất tùy tiện | ✅ Đã sửa | Model chặn Completed khi còn dòng chưa đếm; view chặn sửa dòng của session Completed — có 2 test |
| **I12** Race khi 2 người duyệt | ✅ Đã sửa | `select_for_update` phủ khắp: leave, document, recruitment, timesheet, room, vehicle, supply, procurement, disposal, salary, contract-renew, payroll |
| **I13** `except Exception` lộ lỗi | ✅ Đã sửa | `_friendly_error()`: log server, message thân thiện, ValidationError hiện chi tiết; `finance_payroll_calculate_all` dùng savepoint từng nhân viên |
| **I14** `int()` không validate | ✅ Đã sửa | `common/params.py: parse_int()` thay toàn bộ (portal + reporting) |
| **I15** SECRET_KEY fallback | ✅ Đã sửa | `settings.py:26-31`: raise `ImproperlyConfigured` khi thiếu |
| **I16** Dependencies thừa | ✅ Đã sửa | `requirements.txt` gọn: Django 5.2.17, jazzmin, openpyxl, reportlab, mssql-django, pyodbc, msal, requests, dotenv |
| **M backup files** | ✅ Đã xóa | `views_backup_22092026.py`, `base_backup_22092026.html` không còn |
| **M9** Budget NULL trùng | ✅ Đã sửa | `AnnualBudget` constraint theo (year, department, category) — xem lại phần còn lại bên dưới |
| **M11** month=13 | ✅ Đã sửa | `parse_int(min_value=1, max_value=12)` |

### Điểm mới đáng khen (không có trong lần trước)

- **Django 5.2.17** (LTS, hỗ trợ đến 04/2028) — xử lý đúng P0 "Django 5.0 hết hỗ trợ" của báo cáo Production Readiness 23/09.
- **Source tree đã track trong git thường** (commit `bdc4210`) — xử lý P0 gitlink.
- **App `m365`**: Graph client có token cache + lock, upload session cho file >4MB, tự tạo folder cha, timeout 60s; `ConfiguredStorage` wrapper migration-stable (deconstruct không phụ thuộc toggle) — có 5 test.
- **Phiếu lương PDF** reportlab với font tiếng Việt, chỉ render từ Payslip của kỳ Locked.
- **Middleware `ApplyDueEmployeeChangesMiddleware`**: chạy 1 lần/process/ngày trên traffic đã đăng nhập, nuốt `DatabaseError` để không làm sập trang không liên quan.
- **`_employees_with_permission`/`_leave_approvers_for`**: thông báo gửi đúng người có quyền duyệt thay vì broadcast.
- **`BaseAuditAdmin`**: RBAC theo role + scope_queryset theo phòng cho DEPT_MANAGER, xóa mềm/khôi phục, tự điền created_by/modified_by.

---

## 2. Vấn đề còn lại / mới phát hiện

### 🔴 Nghiêm trọng (Critical)

**C1. `hr_candidate_list` / `hr_candidate_detail` không kiểm tra quyền — mọi nhân viên xem được toàn bộ hồ sơ ứng viên.**
- `portal/views.py:2121-2159`: cả 2 view chỉ có `@login_required`, **không** gọi `_can_manage_hr()` hay `_employee_scope()`. `Candidate` chứa email, SĐT, địa chỉ, lịch sử phỏng vấn, offer (mức lương đề nghị).
- Bất kỳ tài khoản nhân viên nào đăng nhập cũng duyệt `/portal/hr/candidates/` và `/portal/hr/candidates/<pk>/` là xem được. Các view POST (`hr_candidate_create`, `hr_interview_create`…) đều kiểm `_can_manage_hr` — chỉ 2 view GET này bị bỏ sót.
- **Sửa:** thêm `if not _can_manage_hr(request): messages.error(...); return redirect("portal:dashboard")` vào cả 2 view (giống `hr_employee_list`).

**C2. `hr_contract_list` không kiểm tra quyền — mọi nhân viên xem được danh sách hợp đồng (kèm `basic_salary`).**
- `portal/views.py:2053-2056`: chỉ `@login_required`, không kiểm `_can_manage_hr`. Template `hr_contract_list.html` không render cột lương (đã check), nhưng model `Contract` có `basic_salary` và view trả nguyên queryset — chỉ cần template khác/admin export là lộ. Quan trọng hơn về mặt phân quyền: hợp đồng là dữ liệu HR nhạy cảm, EMPLOYEE không được xem toàn công ty.
- **Sửa:** thêm check `_can_manage_hr` (hoặc `_employee_scope` nếu muốn trưởng phòng xem phòng mình).

### 🟠 Quan trọng (Important)

**I1. `document_approve` vẫn tạo notification trong vòng lặp từng nhân viên (N+1 INSERT).**
- `portal/views.py:672-674`: `for emp in Employee.objects.filter(...): notify(emp, ...)` — 500 nhân viên = 500 INSERT đồng bộ trong request. Đây là mục P2 của báo cáo cũ, **chưa được sửa** (các chỗ khác như `finance_payroll_lock` cũng notify từng người nhưng số lượng nhỏ hơn).
- **Sửa:** `Notification.objects.bulk_create([...])` hoặc thêm hàm `notify_many()` trong `notification/services.py`.

**I2. `Payroll.calculate()` vẫn 4 query/nhân viên — P1 của báo cáo cũ chưa sửa.**
- `payroll/models.py:330-363`: mỗi dòng lương vẫn query `InsuranceRateConfig`, `TaxDeductionConfig`, `PersonalIncomeTaxBracket`, count `EmployeeDependent` riêng. 500 người ≈ 2.000 query mỗi lần bấm "Tính lương". Đã có savepoint từng người (tốt cho tính đúng) nhưng chưa tối ưu query.
- **Sửa:** tách phần lấy config ra tham số hoặc cache theo kỳ.

**I3. `report_timesheet` / `report_budget` — N+1 trong vòng lặp nhân viên/ngân sách.**
- `portal/views.py:1226-1246`: mỗi nhân viên 3 query (TimesheetEntry aggregate, Summary, LeaveBalance, has_pending) → 500 người ≈ 1.500-2.000 query.
- `portal/views.py:1846-1858`: mỗi budget dòng query ProcurementRequest/TrainingCourse rồi `sum()` trong Python thay vì `aggregate(Sum(...))`.
- **Sửa:** dùng `annotate`/`Subquery`/`values_list` gom 1 lần.

**I4. `supply_request_create` — `int(q)` trên input người dùng chưa validate.**
- `portal/views.py:1496`: `int(q) > 0` trong list comprehension — `q="abc"` raise `ValueError` → 500 (không nằm trong try). `procurement_request_create` đã dùng `qty.isdigit()` an toàn, chỗ này bỏ sót.
- **Sửa:** `q.isdigit() and int(q) > 0`.

**I5. `dispatch_create` — tăng số sổ công văn không khóa dòng (race) + `int(issue_date[:4])` chưa validate.**
- `portal/views.py:3122-3136`: `book.current_number += 1; book.save(update_fields=...)` không `select_for_update` — 2 người vào sổ cùng lúc đọc cùng `current_number` → trùng số. `year = int(issue_date[:4])` raise ValueError nếu `issue_date` rỗng/sai format (nằm trong try nên thành message lỗi chung, chấp nhận được nhưng nên parse rõ).
- **Sửa:** `DispatchBook.objects.select_for_update().get(...)` trong `transaction.atomic()`.

**I6. `notification_list` đánh dấu đã đọc ngay khi mở trang — không có nút "đánh dấu tất cả" riêng.**
- `portal/views.py:913`: `update(is_read=True)` chạy ngay khi GET list. Người dùng chỉ liếc qua tiêu đề trong dropdown (nếu có) mà chưa vào trang thì badge biến mất. Đây là quyết định UX, nhưng kết hợp với việc **không có view nào đánh dấu từng notification** → không thể giữ thông báo chưa đọc.
- **Sửa (tùy chọn):** tách action "đánh dấu tất cả đã đọc" thành POST riêng.

**I7. `timesheet_month` vẫn dùng `summary.total_leave_days` bất chấp trạng thái duyệt.**
- `portal/views.py:986-990`: trang BCC cá nhân lấy `summary` không filter `status="Approved"` (payroll và `report_timesheet` đã filter, riêng trang cá nhân chưa) → nhân viên thấy `required_hours` đổi theo số tự khai chưa duyệt, trong khi lương chờ duyệt — 2 nơi hiển thị lệch nhau gây nhầm lẫn.
- **Sửa:** filter `status=STATUS_APPROVED` và hiển thị nhãn "chờ duyệt" khi Pending.

**I8. `hr_employee_detail` — khối "Nâng lương"/"Gia hạn hợp đồng" nằm NGOÀI `{% if can_manage_hr %}`.**
- `portal/templates/portal/hr_employee_detail.html:72-100`: khối Điều chuyển/Bổ nhiệm/Khen thưởng/Kỷ luật nằm trong `{% if can_manage_hr %}` (dòng 25, đóng dòng 102), nhưng khối `#luong` (Nâng lương) và `#hopdong` (Gia hạn) nằm **sau** `{% endif %}` — DEPT_MANAGER (có `view_all_employees`? không — DEPT_MANAGER vào được trang qua `_employee_scope`) thấy form Nâng lương/Gia hạn hợp đồng của nhân viên phòng mình. View `hr_salary_create` có chặn `_can_manage_hr or _can_manage_finance` server-side nên submit sẽ bị từ chối — không phải lỗ hổng ghi dữ liệu, nhưng là UI sai (form hiện ra mà bấm không được) và **lộ mức lương hiện tại** (`salaries.first`) cho DEPT_MANAGER.
- **Sửa:** đưa 2 khối này vào trong `{% if can_manage_hr %}` (hoặc thêm biến `can_manage_salary` riêng).

**I9. `profile` hiển thị lương cơ bản cho nhân viên — đúng nghiệp vụ nhưng cần xác nhận.**
- `portal/views.py:209` + `profile.html:26-27`: nhân viên tự xem lương cơ bản của mình — thường là hợp lý, nhưng khác với chính sách "chỉ xem phiếu lương kỳ Locked" của payslip. Ghi chú để chủ nghiệp vụ quyết định nhất quán.

**I10. `check --deploy` vẫn còn 5 cảnh báo (W004/W008/W009/W012/W016).**
- Chạy thực tế: HSTS, SSL redirect, SECRET_KEY ngắn, SESSION/CSRF cookie secure chưa bật. Với intranet HTTP có thể chấp nhận tạm, nhưng đây là checklist production bắt buộc trước go-live (đã nêu trong Production Readiness 23/09, chưa xử lý).
- **Sửa:** cấu hình HTTPS nội bộ + bật `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`; sinh SECRET_KEY ≥50 ký tự.

**I11. `m365` — `SharePointStorage.exists()` nuốt GraphAPIError trả False.**
- `m365/storage.py:60-68`: comment nói "thà báo trùng tên còn hơn ghi đè" nhưng code trả **False** khi lỗi — Django sẽ KHÔNG thêm hậu tố → ghi đè tệp cũ khi Graph lỗi tạm thời. Logic ngược với comment.
- **Sửa:** trả `True` khi không chắc chắn (an toàn cho dữ liệu cũ), hoặc raise để request fail rõ ràng.

**I12. `m365` — `_upload_large_file` đọc toàn bộ file vào RAM.**
- `graph_client.py:196-226`: `content.read()` (trong `_save`) + `io.BytesIO(content)` — tệp 20MB (giới hạn upload) × nhiều request đồng thời = RAM tăng nhanh. Với 30-50 người dùng thì chấp nhận được, ghi chú để theo dõi.
- **Sửa (tùy chọn):** stream theo chunk từ `content` thay vì materialize.

**I13. Middleware áp dụng điều chuyển chạy trong request cycle.**
- `common/middleware.py`: chạy `apply_due_employee_changes` (2 query lớn quét toàn bộ Transfer/Promotion) ngay trong request đầu tiên của ngày — người dùng đó chịu độ trễ. Với quy mô nhỏ ổn; lâu dài nên chuyển sang management command chạy cron (đã có `apply_due_employee_changes` command sẵn — chỉ cần lên lịch).
- **Sửa (tùy chọn):** Windows Task Scheduler gọi command hàng ngày, middleware chỉ làm fallback.

**I14. `AnnualBudget` constraint (year, department, category) với department NULL.**
- `planning/models.py:99`: SQL không coi NULL=NULL nên ngân sách "toàn công ty" (department=NULL) cùng (year, category) vẫn tạo được nhiều dòng — mục M9 cũ chỉ sửa một nửa (đổi tên constraint nhưng vẫn để NULL lọt).
- **Sửa:** `UniqueConstraint(fields=["year", "category"], condition=models.Q(department__isnull=True), name=...)` + constraint cũ cho department NOT NULL.

**I15. `VehicleBooking` mặc định `status="Approved"` khi tạo.**
- `office/models.py:147`: đặt xe không qua duyệt (khác RoomBooking có Pending) — nếu đúng nghiệp vụ "đặt xe tự động duyệt" thì ổn, nhưng `vehicle_booking_create` không gọi `full_clean()` trước khi save → **xung đột giờ đặt xe không được kiểm tra** khi tạo từ portal (chỉ kiểm khi approve). 2 người đặt cùng xe cùng giờ đều thành công.
- **Sửa:** gọi `booking.full_clean()` trong view (room_booking_create đã làm đúng).

**I16. `kpi_score_update` không kiểm tra phạm vi DEPT_MANAGER.**
- `portal/views.py:546-568`: `kpi_score_list` có scope theo phòng cho DEPT_MANAGER, nhưng `kpi_score_update` lấy `EmployeeKPI` theo pk bất kỳ — DEPT_MANAGER gửi POST tay với pk của nhân viên phòng khác vẫn chấm điểm được (HR_MANAGER/SUPER_ADMIN thì đúng quyền).
- **Sửa:** kiểm tra `result.employee.department_id in dept_ids` khi role là DEPT_MANAGER.

**I17. `task_detail` cho HR_MANAGER/DEPT_MANAGER xem mọi task nhưng DEPT_MANAGER không giới hạn phòng.**
- `portal/views.py:410-417`: `_role_code in ("HR_MANAGER", "DEPT_MANAGER")` được xem mọi task toàn công ty — không nhất quán với scoping phòng ở `task_create`/`kpi_score_list`. Nhỏ nhưng nên thống nhất.

### 🟡 Nhỏ (Minor)

- `payroll/models.py:255-296`: các field tiền nhập tay (`allowance`, `overtime_amount`, `deduction_amount`…) vẫn **không có `MinValueValidator(0)`** — mục M7 cũ chưa sửa; `finance_payroll_update_line` vẫn lưu được giá trị âm.
- `payroll/models.py:404-410`: BHXH+BHYT+BHTN cộng rồi làm tròn 1 lần (M1 cũ) — lệch tối đa 1đ/khoản/người/tháng so với thông lệ làm tròn từng khoản.
- `payroll/models.py:376-380`: có trần đóng BH nhưng **không có sàn** lương tối thiểu vùng (M2 cũ).
- `portal/views.py:1948-1950`: `hr_employee_create` vẫn gọi `_generate_next_employee_code()` 2 lần (code thừa, mục cũ chưa dọn).
- `portal/views.py:67`: `_paginate()` được định nghĩa nhưng **không view nào dùng** — các danh sách (`hr_employee_list`, `dispatch_list`, `notification_list`, `hr_candidate_list`…) vẫn render toàn bộ queryset không phân trang. Với 30-50 người dùng thì tạm ổn, nhưng danh sách notification/candidate sẽ dài dần.
- `hrm/models.py`: `full_name` vẫn là field tự nhập không đồng bộ `first_name`/`last_name` (mục cũ).
- `planning/models.py`: `TrainingCourse`/`Event` vẫn không validate `end > start` (M10 cũ).
- `payroll/views.py`, `leave/views.py`, `document/views.py`…: file views trống placeholder — không sai, chỉ là dấu vết scaffold.
- `settings.py:136`: ODBC Driver cố định "17" — nên đọc từ env để dễ nâng Driver 18.
- `m365/graph_client.py:150-157`: `_drive_id` dò theo tên library mỗi lần cache miss — nếu library đổi tên sẽ raise lỗi rõ ràng (tốt), nhưng không có refresh cache khi thêm library mới trong cùng process (khởi động lại là hết — chấp nhận).
- `dispatch_create` (`portal/views.py:3122`): `book_names.get(dispatch_type)` trả None nếu dispatch_type lạ → `book_name=None` — nên validate dispatch_type trong choices trước.

---

## 3. Hiệu năng

| # | Vị trí | Vấn đề | Trạng thái so với lần trước |
|---|---|---|---|
| P1 | `payroll/models.py:330-363` | 4 query/nhân viên khi tính lương | ❌ Chưa sửa (I2) |
| P2 | `portal/views.py:672-674` | Notify từng nhân viên trong vòng lặp khi duyệt tài liệu | ❌ Chưa sửa (I1) |
| P3 | `planning/admin.py:10` | `actual_headcount`/`gap` property query trong `list_display` | ❌ Chưa sửa |
| P4 | `portal/views.py:1226-1246` | `report_timesheet` 3-4 query/nhân viên | Mới phát hiện (I3) |
| P5 | `portal/views.py:1846-1858` | `report_budget` query + sum Python từng dòng | Mới phát hiện (I3) |

**Điểm tốt mới:** `finance_payroll_generate` (bulk_create + salary_map 1 query), `finance_payroll_lock` (bulk_create Payslip), `select_related` vẫn phủ rộng, `payslip_pdf` render 1 lần theo yêu cầu.

---

## 4. Kết luận & Thứ tự ưu tiên

Chất lượng codebase **tăng rõ rệt so với 22/09**: 4/4 Critical cũ đã sửa đúng và có regression test; 12/12 Important cũ đã xử lý; 86 test chạy xanh; Django 5.2 LTS; secrets bắt buộc từ env; soft-delete, proration lương, phiếu lương PDF, SharePoint storage đều được làm tử tế với test. Kiến trúc comment "mục X (đã sửa)" trong code giúp truy vết rất tốt.

Việc còn lại theo thứ tự ưu tiên:

1. **Ngay (lỗ hổng phân quyền):** C1 + C2 — thêm check quyền cho `hr_candidate_list`, `hr_candidate_detail`, `hr_contract_list`; I8 đưa khối Nâng lương/Gia hạn vào `{% if can_manage_hr %}`; I16 scope KPI cho DEPT_MANAGER.
2. **Trước khi mở rộng người dùng:** I4 (`int(q)` crash), I5 (race số công văn), I15 (đặt xe không kiểm xung đột), I11 (`exists()` ngược logic), I7 (BCC cá nhân dùng số chưa duyệt).
3. **Trước production/go-live:** I10 — xử lý 5 cảnh báo `check --deploy` (HTTPS, HSTS, cookie secure, SECRET_KEY dài); xác nhận backup/restore SQL Server (P1 của báo cáo Production Readiness chưa có bằng chứng trong repo).
4. **Hiệu năng khi dữ liệu lớn:** I1/I2/I3 (bulk notify, config cache cho calculate, annotate cho báo cáo), bật `_paginate` cho các danh sách dài.
5. **Dọn nhỏ:** MinValueValidator cho field tiền, sàn BH, constraint budget NULL, validate end>start, xóa code thừa `_generate_next_employee_code` gọi 2 lần.

**Đánh giá tổng thể:** Codebase đã đạt mức "chạy nội bộ ổn định có test bảo vệ"; còn 2 lỗ hổng phân quyền view (C1/C2) cần vá ngay — mỗi cái chỉ vài dòng — và checklist hardening production trước khi ra khỏi môi trường dev.
