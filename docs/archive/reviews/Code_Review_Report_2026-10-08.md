# Báo cáo review tĩnh toàn mã nguồn — 2026-10-08

**Phạm vi:** FULL (đọc/quét toàn bộ `src/apps`, `src/config`, `src/templates`, CI), chế độ REVIEW — không sửa mã.
**Nguồn:** bản ZIP `QLHCNS-source-20261008-0004f7e047ed.zip` (mã băm ghi trong ZIP: `0004f7e047ed99db4c8e9a7f6d39539f3298f5c2`). Không phải checkout Git nên không đối chiếu được `HEAD`/`origin/main`.
**Hạn chế:** môi trường review không có Django và không có mạng; **chưa chạy bất kỳ test, `manage.py check` hay migration nào** (SQLite/SQL Server/CI đều chưa chạy). Mọi finding dưới đây xác nhận bằng đọc mã, chưa tái hiện bằng test. Không có bằng chứng Bugbot/Sixth đã chạy.

## 1. Mức độ đã rà

| Mức | Phân hệ/tệp |
|---|---|
| Đọc kỹ | `security/permissions.py`, `security/data_access.py`, `security/files.py`, `portal/views/{attendance,finance,documents,hr,office_procurement}.py` (phần chính), `portal/context_processors.py`, `templates/base.html` (menu), `leave/models.py`, `lifecycle/views.py`, `reporting/views.py`, `common/uploads.py`, `config/settings.py`, `config/urls.py`, `.github/workflows/ci.yml` |
| Đối chiếu tự động | Toàn bộ 150 route `portal/urls.py` ↔ guard của view (script AST); menu ↔ quyền |
| Quét mẫu rủi ro | toàn `src/` : `csrf_exempt`, `mark_safe`, `|safe`, SQL thô, `eval/exec`, `subprocess`, `verify=False`, `float()` tiền → **không có vi phạm** (chỉ 1 `float()` khi xuất Excel tài sản) |
| **Chưa rà sâu** | `document/hcns/*` (≈2.800 dòng, đã có review riêng ngày 06/10), `activity/*` ngoài guard, `m365/*`, `notification/*`, `planning`, `kpi`, `task`, `asset` (model), `recruitment` (model), `payroll/models.py` (công thức), `attendance/services.py`, migrations, `ops/*` (backup/scheduler), `src/frontend`, mọi template ngoài `base.html`, toàn bộ test hiện có |

Không được suy diễn "không có finding" cho phần **Chưa rà sâu**.

## 2. Điểm làm tốt (đã xác nhận qua đọc mã)

- Cấu hình production chặn `DEBUG`, `SECRET_KEY` yếu, `ALLOWED_HOSTS=*`; cookie Secure/HttpOnly/SameSite, `X_FRAME_OPTIONS=DENY`, nosniff; Axes giới hạn đăng nhập.
- Tệp tải lên không phục vụ trực tiếp (`/media/` trả 404); `private_file` có allowlist model/trường, chặn path traversal, kiểm tra quyền từng đối tượng, gửi CSP `sandbox`, `no-store`, ghi `SecurityEvent`.
- Hầu hết route portal có guard rõ ràng; phần còn lại là dữ liệu của chính người dùng hoặc nội dung chung có chủ ý (ví dụ tài liệu đã ban hành); mutation chính dùng `@require_POST`, `transaction.atomic()` + `select_for_update()` (duyệt nghỉ phép, khóa kỳ lương, duyệt mua sắm/VPP/đặt phòng/xe, nâng lương, gia hạn hợp đồng).
- Payslip PDF chỉ tải được bởi chính chủ và kỳ đã khóa.

## 3. Finding

Mức: P1 = sai nghiệp vụ/ảnh hưởng tiền, P2 = lỗ hổng kiểm soát hoặc lỗi có điều kiện kích hoạt thực tế, P3 = thấp/độ bền/tiện dụng. "Cần quyết định" = phải có chủ dự án chốt chính sách trước khi sửa.

### F-01 [P1, cần quyết định] Bảng lương và nhiều danh sách bỏ sót nhân viên Thử việc / Nghỉ dài hạn
- `portal/views/finance.py:120-125` `_employees_payable_for_period` chỉ lấy `employment_status="Active"` (hoặc có `leave_date` trong kỳ). `Employee.EMPLOYMENT_STATUS_CHOICES` có thêm `Probation` và `OnLeave`.
- Trigger: HR chọn "Thử việc" ở form nhân viên → nhân viên không bao giờ có dòng lương; vì kiểm tra khóa kỳ (`finance_payroll_lock`) dùng cùng hàm nên **không cảnh báo thiếu**, kỳ khóa và phát phiếu lương thiếu người.
- Cùng kiểu lọc chỉ `Active` ở khoảng 24 chỗ (đếm bằng grep): danh sách cấp phát tài sản (`assets.py:150,394`), nhận thông báo tài liệu (`documents.py:90`), người nhận thông báo theo vai trò (`common.py:69`), thống kê dashboard/kế hoạch nhân sự (`core.py`, `planning`), người phỏng vấn, quản lý trực tiếp… Chỉ `activity/forms.py:101` và `hr.py:285` đã dùng `Active+Probation`.
- Cần chốt: Thử việc có hưởng lương/phiếu lương không (gần như chắc chắn có), `OnLeave` (thai sản/ốm dài) xử lý thế nào. Đề xuất một hằng `EMPLOYED_STATUSES` dùng chung.

### F-02 [P2] Quyền "quản lý công văn" dùng nhầm quyền duyệt nghỉ phép
- `portal/views/documents.py:111` (`dispatch_list`) và `:158` (`dispatch_detail`): `is_mgmt = _can_approve(request) or request.user.is_staff`, mà `_can_approve` = `approve_leave` (`attendance.py:31`) → HR_MANAGER, DEPT_MANAGER, DIRECTOR.
- `dispatch_create` (`documents.py:203`) lại dùng `manage_office` (HR_MANAGER, HR_OFFICER, SYS_ADMIN).
- Hệ quả: (a) Trưởng phòng (và Giám đốc) cập nhật được trạng thái/tiến độ mọi công văn họ nhìn thấy dù không được giao; (b) HR_OFFICER và SYS_ADMIN vào sổ được nhưng không cập nhật được công văn của người khác.
- Sửa: dùng `manage_office` (hoặc quyền mới `manage_dispatch`) ở cả hai chỗ; test ma trận vai trò × (xem/cập nhật/tạo).

### F-03 [P2/P3, cần quyết định] Phạm vi xem công văn đến rộng hơn chú thích ma trận
- `security/data_access.py:48`: chỉ cần có `access_outgoing_document` là xem **mọi loại** công văn (kể cả Incoming) toàn công ty ở mức bảo mật Normal. Vai trò có quyền này: SUPER_ADMIN, SYS_ADMIN, DIRECTOR, HR_MANAGER, HR_OFFICER, DEPT_MANAGER, FINANCE_OFFICER, PROJECT_MANAGER, PROJECT_COORDINATOR (PM/PC bị cắt riêng chỉ còn Outgoing ở dòng 46-47).
- Chú thích `permissions.py` ("công văn đến — chỉ Nhân sự và Quản trị hệ thống") và `docs/10_RBAC_Permission_Matrix.md` (không có mục công văn nào) không khớp hành vi này.
- Cần chốt: ai được xem công văn đến; sau đó sửa `visible_dispatches_for` hoặc cập nhật ma trận/tài liệu, kèm test.

### F-04 [P2, cần quyết định] Thiếu tách người đề nghị và người duyệt (maker-checker)
- Mua sắm: `request_procurement` gồm FINANCE_OFFICER, HR_MANAGER…; `approve_procurement` gồm FINANCE_OFFICER, DIRECTOR → người đề nghị tự duyệt được (`office_procurement.py:442`, không so `requested_by` với người duyệt).
- VPP/đặt phòng/đặt xe: `approve_office_request` gồm HR_MANAGER, HR_OFFICER, SYS_ADMIN, chính nhóm này cũng tạo đề nghị (`:307`, `:96`, `:197`).
- Nghỉ phép: chỉ chặn DEPT_MANAGER tự duyệt (`attendance.py:172`); HR_MANAGER/DIRECTOR tự duyệt đơn của mình (đã ghi chú là chủ ý).
- Cần chốt chính sách; đề xuất: không tự duyệt đề nghị mua sắm/VPP của chính mình; nếu không còn người khác thì chuyển cấp trên.

### F-05 [P2, cần quyết định] Xuất Excel danh sách nhân sự kèm số CCCD cho cả Kế toán
- `reporting/views.py:72` cho `export_employee_data` (HR_MANAGER, HR_OFFICER, DIRECTOR, **FINANCE_OFFICER**) xuất toàn công ty; `reporting/services.py:105` ghi `national_id` của mọi nhân viên.
- Kế toán không có quyền `view_all_employees`/`view_employee_compensation` nhưng lấy được CCCD hàng loạt qua đường xuất. Có `SecurityEvent` ghi nhận nhưng không ngăn.
- Đề xuất: bỏ/che CCCD khỏi bản xuất hoặc tách quyền xuất đầy đủ cho HR; xác nhận `national_id` có được mã hóa lưu trữ không (chưa kiểm tra).

### F-06 [P2] Tạo dòng lương lặng lẽ để lương cơ bản = 0
- `finance.py:184-185,190`: nhân viên chưa có `EmployeeSalary` hiệu lực vẫn được tạo dòng với `basic_salary=0`, thông báo vẫn "thành công"; `bulk_create` bỏ qua `full_clean`/`save()`.
- Trigger: nhân viên mới chưa nhập lương; kỳ vẫn khóa được nếu `validate_calculated` chấp nhận 0 (chưa đọc công thức) → phiếu lương 0 đồng.
- Sửa: liệt kê nhân viên thiếu lương và chặn/cảnh báo rõ trước khi tạo; khóa kỳ không cho phép dòng lương cơ bản 0 trừ khi được xác nhận.

### F-07 [P2] Tạo đơn nghỉ phép không chống gửi đúp/đồng thời
- `attendance.py:87` (`leave_create`) và `leave/models.py:128` (`_validate_quota`, `_validate_no_overlap`): kiểm tra trùng ngày + quỹ phép rồi `save()` ngoài `transaction.atomic()`/khóa dòng.
- Trigger: nhấp đúp nút Gửi hoặc hai tab → hai đơn trùng ngày, hoặc vượt quỹ phép năm (cả hai cùng đọc quỹ trước khi bên kia lưu).
- Sửa: bọc `atomic()` + `select_for_update()` trên `LeaveBalance`/Employee (hoặc dòng nhân viên) quanh kiểm tra+lưu; test đồng thời tương tự test đã có cho công văn.

### F-08 [P3] Trang có quyền nhưng không có đường vào từ menu
- Không template nào link tới `procurement_request_list`, `room_booking_approval_list`, `vehicle_booking_approval_list`, `supply_request_approval_list`; chỉ vào được qua link thông báo hoặc gõ URL.
- `/reports/` (Trung tâm Báo cáo, `view_report_center`) chỉ có trong dropdown quản trị (`base.html:74`); HR_OFFICER và FINANCE_OFFICER có quyền nhưng không thấy link. Menu "Báo cáo" (`base.html:234`) dùng `view_reports` khác hẳn quyền này (F-09).
- "Giao việc & hoàn tất" nằm trong menu Dự án (`base.html:239`, cần `view_activity_dashboard`): HR_MANAGER (có `assign_task`) và nhân viên được giao việc không có mục menu (chưa kiểm tra dashboard có link riêng).
- Menu "Công văn đến/đi" hiện cho mọi tài khoản.

### F-09 [P3] Hai quyền báo cáo song song, dễ lệch
- `view_reports` (HR_MANAGER, DIRECTOR; `reports_planning.py:32`) và `view_report_center` (6 vai trò; `reporting/views.py:25`), thêm `export_employee_data`/`export_compliance_report`. Nên gộp hoặc ghi rõ ranh giới trong `docs/10_RBAC_Permission_Matrix.md`.

### F-10 [P3] Sinh mã nhân viên không an toàn đồng thời
- `portal/views/hr.py:315` quét toàn bộ mã nhân viên rồi +1, không khóa. `employee_code` có `unique=True` nên hai người tạo đồng thời nhận `IntegrityError` (hiện chỉ hiện lỗi chung), không phải mã trùng. Nên retry khi vi phạm unique hoặc dùng sequence/bảng đếm.

### F-11 [P3] Cập nhật đầu việc lifecycle không khóa dòng
- `lifecycle/views.py:119`: đọc `status="Pending"`, đổi, rồi kiểm tra "còn việc Pending → đóng case" ngoài transaction; hai thao tác đồng thời có thể ghi đè nhau hoặc đóng case sớm/hai lần. Bọc `atomic()` + `select_for_update()` trên item và case.

### F-12 [P3] Kiểm tra tệp tải lên chỉ theo đuôi và dung lượng
- `common/uploads.py:101`: không kiểm tra nội dung (magic bytes) trừ PDF quyết định; cho phép `.zip/.rar/.7z`. Được giảm nhẹ bởi tải xuống dạng đính kèm + CSP sandbox + nosniff, nhưng chưa có quét mã độc. Cân nhắc kiểm tra magic bytes cho các định dạng Office/ảnh và bỏ định dạng nén nếu không cần.

### F-13 [P3] `private_file` truy vấn lần lượt 11 model/trường cho mỗi lượt tải
- `security/files.py:56`: `model.objects.filter(<field>=name)` trên cột đường dẫn không có chỉ mục. Ổn khi dữ liệu nhỏ, chậm dần khi lớn. Cân nhắc đưa model/ID vào URL hoặc thêm chỉ mục.

### F-14 [P3] `CompanyMedia` đọc được bởi mọi tài khoản đăng nhập, dù chú thích ghi "Published"
- `security/data_access.py:101` luôn trả `True`; model `CompanyMedia` không có trường trạng thái xuất bản/ẩn (ngoài xóa mềm). Nếu cần bản nháp/nội bộ hẹp, phải thêm trường và kiểm tra.

### F-15 [P3] Gia hạn hợp đồng lấy hợp đồng mới nhất theo `start_date` bất kể trạng thái
- `portal/views/hr.py:369`: có thể gia hạn hợp đồng đã chấm dứt/hết hạn. Nên lọc `status="Active"` hoặc báo rõ.

### F-16 [P3] Xuất sổ công văn: loại không hợp lệ và tên tệp sai
- `reporting/views.py:105-107`: `dispatch_type` không được validate; `InternalDirective` bị đặt tên "di". Báo cáo tổng `report_dashboard` (`:51`) đếm công văn không lọc theo `visible_dispatches_for` (chỉ số tổng hợp, không lộ nội dung).

### F-17 [P3] Điểm nhỏ về nghỉ phép
- Không kiểm tra nhân viên còn làm việc khi tạo đơn; không có chức năng nhân viên hủy đơn đang chờ (chưa thấy route).

## 4. Hạng mục chưa kiểm chứng được (cần chạy)

1. `ops/run_tests.py --backend sqlite` và `--backend sqlserver` trên mã hiện tại (số test từ nhật ký cũ không dùng làm kết quả).
2. `manage.py check`, `makemigrations --check --dry-run`, `pip_audit`, `npm audit`, build CSS.
3. Tái hiện F-02, F-07 bằng test (bước đầu của Codex).
4. Công thức lương `payroll/models.py` (làm tròn Decimal, thuế/BH), `attendance/services.py`, `activity/*`, `m365/*`, `ops/*`.

## 5. Thứ tự đề xuất

1. Chốt chính sách F-01, F-03, F-04, F-05 với chủ dự án (không để Codex tự quyết).
2. Sửa độc lập có test: F-02, F-06, F-07, F-10, F-11, F-15, F-16.
3. Menu/quyền báo cáo: F-08, F-09 sau khi có quyết định F-03.
4. Tiếp tục review phần "Chưa rà sâu".
