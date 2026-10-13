# Đặc tả kỹ thuật dashboard IHRMS theo Atoms

Ngày: **13/10/2026**. Trạng thái: **bản sửa để chủ dự án duyệt; chưa triển khai**.
Baseline từ `git rev-parse HEAD`: `cf8213554d829df3e7e094604f2bb36019a9638f`, nhánh `main`.
Lượt này chỉ sửa tài liệu và [nhật ký](PROJECT_WORK_LOG.md), không sửa mã/quyền/dữ liệu/dependency.

## 1. Tóm tắt để duyệt — một trang

“Sẵn sàng” là xác định được nguồn và quyền cho nhóm được ghi, **không phải đã triển khai/kiểm thử dashboard**. Ma trận ngoại lệ ở mục 7. Khối bị từ chối không có trong HTML.

| Khối | Nguồn dữ liệu | Quyền xem dựa trên mã hiện có | Đợt | Trạng thái |
| --- | --- | --- | --- | --- |
| Nhân sự theo status | Employee | view_all_employees; trưởng phòng trong phòng quản lý | 1 | Sẵn sàng |
| Approved trong ngày | LeaveRequest, khoảng ngày chứa D | view_reports: HR_MANAGER/DIRECTOR; superuser | 1 | Sẵn sàng |
| Hợp đồng sắp hết hạn + quá hạn riêng | Contract, status/start/end | manage_hr; DIRECTOR mặc định ẩn | 1 | Sẵn sàng |
| Loại hợp đồng | Contract + ContractType | manage_hr, chỉ số không tiền | 1 | Sẵn sàng |
| Định biên kế hoạch năm | HeadcountPlan + with_headcounts | view_reports, chỉ số không tiền | 1 | Sẵn sàng |
| Việc cần xử lý | Queryset từng trang duyệt | Quyền từng nghiệp vụ, không gộp quyền HR | 1 | Sẵn sàng |
| Đơn nghỉ gần đây | LeaveRequest, total_days | Scope lịch sử cần xác nhận, không suy từ approve Pending | 2 | Cần quyết định |
| Tuyển dụng mở / ứng viên | JobPosting, RecruitmentRequest, Candidate | manage_hr cho ứng viên; scope tin mở xác minh riêng | 2 | Cần quyết định |
| Cập nhật gần đây | Timestamp bản ghi được đọc | Quyền đọc nguồn, chưa phải sự kiện duyệt | 2 | Cần quyết định |
| Gross / phụ cấp kỳ lương | PayrollPeriod + Payroll | manage_finance và policy dashboard được duyệt | 2 có điều kiện | Cần quyết định |
| Trend, tỷ lệ có mặt, timeline, tuyển theo tháng | Lịch sử / lịch ca đã xác nhận | Policy tương ứng | 3 | Cần dữ liệu lịch sử |
| Header tầng 2 / search / giờ ca | Khung chung, route thật, ca áp dụng | Shell riêng, hiện hoãn | Riêng | Cần quyết định |

Giữ cá nhân/thông báo/tiến độ dự án theo quyền hiện có; nhân viên không tự nhận dashboard HR.

Có thể duyệt Đợt 1 trước mà chưa bật khối còn thiếu chính sách.

## 2. Mục tiêu, nguồn và bằng chứng

### Bổ sung được yêu cầu ngày 13/10/2026: tìm kiếm và demo Atoms

Ô tìm kiếm dùng chung trong header đã được chủ dự án yêu cầu triển khai riêng: GET `portal:global_search`, tìm trang chức năng và nhân viên theo tên/mã/email công việc. Chỉ tìm nhân viên trong scope hiện có (toàn Trung tâm, phòng đang quản lý hoặc chính mình); kiểm quyền trước truy vấn, không tìm lương, định danh nhạy cảm hay nội dung đơn nghỉ. Trang kết quả giới hạn 20 hồ sơ, tối thiểu 2 và tối đa 100 ký tự; không cache kết quả. Đây là phạm vi tìm kiếm hiện tại, chưa tìm toàn văn mọi tài liệu/công việc.

Dashboard tham chiếu bố cục Atoms: 4 KPI có điểm đến cùng scope/cách đếm; 6 màu biểu đồ phân biệt nhóm, thanh thực tế/kế hoạch chung thang đo; donut có ký hiệu, tên, số lượng, tỷ trọng và thanh tỷ trọng. Giữ KPI thử việc thay cho quỹ lương: chính sách tiền, xu hướng tháng và tỷ lệ có mặt vẫn chờ duyệt/nguồn dữ liệu tương ứng. Hợp đồng được đếm theo bản ghi hợp đồng đang hiệu lực, không đổi thành số người để khớp ảnh mẫu.

`ops/dashboard_demo.py` tạo/serve một SQLite riêng ngoài repository, media/log/email cách ly, banner dữ liệu giả và tài khoản nhiều vai trò. Demo có 22 nhân viên, 6 phòng ban, 4 loại/27 hợp đồng gồm các trạng thái và biên hiệu lực. Credentials/secrets/database nằm ngoài Git. Kết quả kiểm thử và cách mở demo được ghi duy nhất trong [nhật ký](PROJECT_WORK_LOG.md).

Dashboard trả lời hiện trạng, việc cần xử lý, phạm vi/kỳ của số liệu và nơi kiểm tra. Mỗi khối có nhãn, giá trị/đơn vị, kỳ, scope, nguồn/cách tính và trạng thái dữ liệu.

Tham chiếu [Atoms](https://r7rc1s.atoms.world/) và tám ảnh `design-system/reference/atoms/`: `01_dashboard.png`, `02_dashboard_lists.png`, `03_dashboard_tables.png`, `04_tuyen_dung_kanban.png`, `05_phong_ban.png`, `06_hop_dong.png`, `07_ho_so_nhan_vien.png`, `08_cham_cong.png`. Đã đọc lại tám ảnh trong lượt sửa. DESIGN tại `C:/Users/dinht/Downloads/atoms/DESIGN.md` là tham chiếu bố cục, không thay quy tắc dự án. Người/logo/số trong ảnh không là dữ liệu IHRMS.

Lượt soạn trước đã tải HTML HTTP 200 và bundle `/assets/index-CfxoekPe.js`. Lượt sửa này xác minh lại bằng `Get-FileHash -Algorithm SHA256` bản `%TEMP%/ihrms-atoms-spec-20261013/atoms-main.js`: `0a6e78dadc448d4664a3f7abf9a015f29dd148704d8d5d1be2ca1c2ed29dac11`. Hash chứng minh bản đã tải, không chứng minh website hiện vẫn cùng phiên bản. URL khôi phục từ yêu cầu/nhật ký. Chưa kiểm tương tác live; công cụ web/trình duyệt lượt trước không đọc được/khởi tạo lỗi.

Core hiện cấp tổng Active cho HR_MANAGER/DIRECTOR/superuser, số phòng cho DEPT_MANAGER linked, số cá nhân/dự án theo quyền. home_presentation dựng link/trình bày không query. Khối hợp đồng/định biên/Approved ngày D chưa có context; công thức dưới đây là đề xuất, không bằng chứng tính năng đã có.

Quy tắc lấy từ [MASTER](../design-system/MASTER.md), [DESIGN](../DESIGN.md), tokens, permissions.py, [RBAC](10_RBAC_Permission_Matrix.md) và guard/scope view đích. Mã/tài liệu lệch nhau thì ghi quyết định, không tự mở quyền.

Mẫu quyết định trình bày; mã và chính sách quyết định dữ liệu được xem.

## 3. Ràng buộc kế thừa G2–G5

Kiểm tra thật bằng `rg -n -- '--ui-brand:|--ui-sidebar-bg:|--ui-bg:|navy|teal|violet' src/static/css/ui_tokens.css DESIGN.md design-system/MASTER.md`:

- Light brand `#0b7461`, sidebar navy `#0c233b`, nền `#f4f7f5`; dark brand `#63dbc2`, nền `#0e1827`.
- DESIGN dòng 43/76 navy–teal; MASTER dòng 17 quyết định Atoms thay tím theo ủy quyền mới.
- **Còn mâu thuẫn:** MASTER dòng 11 vẫn nói violet và tài liệu thống nhất. Không kết luận hoàn toàn nhất quán; không sửa MASTER/DESIGN/tokens ở lượt này, đưa vào Q1.

Dùng lại G4: `src/templates/ui/kpi.html`, `ui/badge.html`, `ui/empty_state.html`, `ui/page_header.html`, `src/apps/portal/templates/portal/_pagination.html`; registry `ui_badge`, filters `ui_number/ui_date/ui_vnd` tại `apps/common/templatetags`. Card/KPI dùng cấu trúc/CSS chung; **không metric_card hay hệ card/badge thứ hai**. Status mới chỉ mở rộng registry nếu cần.

| Partial đề xuất, chưa tạo | Lý do nội dung chung chưa đủ | Tái sử dụng |
| --- | --- | --- |
| portal/dashboard/_headcount_chart.html | Actual/planned + bảng thay thế | Khung card/chart tokens/ui_number |
| portal/dashboard/_contract_distribution.html | Donut có nhãn + bảng | Khung card/chart tokens/ui_number |
| portal/dashboard/_expiring_contracts.html | Hạn và quá hạn riêng | ui_badge/ui_date/empty_state |
| portal/dashboard/_action_queue.html | Nhóm khác quyền/queryset | KPI/badge/link dùng chung |
| _recent_leaves.html, _recruitment_summary.html, _recent_updates.html trong portal/dashboard | Đợt 2 chỉ tạo sau chốt scope | Bảng/registry/phân trang/empty_state hiện có |

Màu/spacing/typography/focus dùng `--ui-*`, chart dùng `--ui-chart-*`. Không hard-code palette partial; cùng đại lượng dùng một sắc thương hiệu, không màu riêng từng phòng.

Sidebar nhóm theo phân hệ, drawer <1024 px, không bottom bar. Không gradient/glow/bóng nổi kiểu neumorphism. Font hệ thống/SVG cùng bộ, không emoji/CDN/font mạng. Body 16 px, bảng/nhãn 14 px, phụ chú 12 px; control/vùng bấm ≥44 ×44 px, focus 3 px. Giữ bàn phím/nhãn/zoom/prefers-reduced-motion; viền card trang trí không thay control.

Khi triển khai đo light/dark bằng `python ops/check_ui_contrast.py`. **Code tương lai:** bổ sung cặp chart foreground/track/surface, donut/legend, badge hạn ≤7 / 8–30 / 31–60 và quá hạn, focus mới nếu có. Text mục tiêu ≥4,5:1, control/focus ≥3:1. Lượt tài liệu không sửa/chạy script, không kết quả cũ để tuyên bố WCAG.

Dashboard dùng cùng hệ thiết kế với các trang đã hoàn tất.

## 4. Bố cục và khung riêng

Tiêu đề Bảng điều khiển dùng ui/page_header; phụ chú ngày/scope/năm kế hoạch/thời điểm dựng trang. Kỳ lương chỉ trong khối tiền được duyệt. Dashboard không phụ thuộc header tầng 2.

Thứ tự mục tiêu, bỏ khối thiếu quyền/điều kiện rồi tự lấp khoảng trống:

1. Tối đa bốn KPI: Nhân sự đang quản lý, Active, Approved ngày D, Thử việc. Không chèn tiền/số giả cho đủ bốn ô.
2. Cơ cấu: định biên trái 7/12, loại hợp đồng phải 5/12 nếu có quyền.
3. Vận hành: hợp đồng sắp hết hạn + quá hạn riêng trái, queue phải.
4. Đợt 2 mới đơn nghỉ gần đây/tuyển dụng/Cập nhật gần đây. Tiền sau policy, không điều kiện hoàn tất Đợt 1.
5. Giữ Công việc của tôi/Thao tác nhanh/Tiến độ dự án; nhân viên thường có khu vực cá nhân ở đầu trang.

≥1440 px: tối đa bốn KPI/lưới 7/5; 1024–1439 px: hai/bốn KPI theo chiều rộng thật; dưới 1024 px: drawer/panel một cột; 768–1023 px: hai KPI; 360–767 px: một KPI. Kiểm thêm 1920 px. Không tràn ngang cả trang; bảng cuộn trong vùng có nhãn; không spacer giả ép chiều cao/khoảng trống card ẩn.

**App shell riêng — HOÃN:** header tầng 2 (giờ ca/kỳ lương/badge duyệt) và search topbar dùng chung mọi trang. Không gộp dashboard; cần duyệt phạm vi/nguồn/quyền:

- Search có route/parser GET/scope thật; hiện chỉ tên/mã. Không email/toàn cục/search giả.
- WorkShift và ca áp dụng phải xác minh; chưa đủ liên kết/giờ nghỉ trưa. `08:30–17:30`, `12:00–13:30` là giờ mẫu, không hard-code.
- Kỳ lương không lộ khi chưa policy; nhiều kỳ mở phải cụ thể kỳ.
- Badge duyệt cùng queryset/scope/cấm tự duyệt; không tổng Trung tâm cho người chỉ duyệt phòng.

Dashboard vẫn rõ ràng khi topbar đang hoãn.

## 5. Công thức, phạm vi và giới hạn

D = timezone.localdate() hoặc GET parse hợp lệ; Y năm kế hoạch; M kỳ lương được đọc; S queryset giới hạn quyền. GET chỉ thu hẹp S. Employee luôn ghi Hiện tại; Contract status hiện tại không chứng minh status lịch sử tại D.

State ready/empty/unconfigured/partial/error: 0 hợp lệ hiện `0`; thiếu nguồn “Chưa có dữ liệu”; không đầy đủ “Dữ liệu chưa đầy đủ”; lỗi “Không tải được dữ liệu”. Không null/lỗi/thiếu quyền thành 0. Tỷ lệ có tử/mẫu, mẫu 0 ghi `—`. Trend cần lịch sử tương thích hai kỳ.

Mỗi số nói rõ nó đếm gì và chưa nói được điều gì.

### 5.1 Nhân sự / Approved ngày D — Đợt 1

Nhân sự đang quản lý = distinct Employee S có Active/Probation/OnLeave, không Resigned. Mặc định Q6, tách ba nhóm phụ, không đổi total_employees cũ chỉ Active. Active không “Có mặt hôm nay”; Thử việc là Probation riêng, không đổi rules payroll.

Approved ngày D = distinct employee có LeaveRequest Approved, `from_date <= D <= to_date`; hai đơn cùng người không đếm hai, loại Pending/Rejected/Cancelled. Ghi “Theo khoảng ngày đơn nghỉ, không phải số người vắng”. Ngày phép/nửa ngày/lễ theo dịch vụ nghiệp vụ, không phép trừ ngày tự viết.

Scope toàn Trung tâm dựa view_reports/báo cáo nghỉ hiện có. approve_leave chỉ chứng minh Pending; chưa đủ Approved cho HR_OFFICER/DEPT_MANAGER, mặc định ẩn phần chưa policy.

Active và nghỉ được duyệt là hai loại thông tin khác nhau.

### 5.2 Hợp đồng — Đợt 1

Phân bố loại: Contract Active, start_date≤D, end_date null hoặc ≥D, S được manage_hr đọc; nhóm ContractType thật. Mẫu số **hợp đồng**, không người; nhiều hiệu lực một người vẫn nhiều hợp đồng.

Donut ≥2 nhóm; một nhóm dùng số/tỷ trọng + bảng; 0 hợp đồng empty_state. Nhãn trực tiếp/ký hiệu/bảng loại–số–tỷ trọng, không chỉ màu; tooltip dùng bàn phím. SVG/CSS thuần, không chart library.

Sắp hết hạn: Active, start_date≤D, `D <= end_date <= D+60 ngày`, sort end_date/pk. Tối đa năm dòng, tổng cả queryset; tên/mã/loại/số hợp đồng/ngày hết hạn/ngày còn lại. D “Hết hạn hôm nay”; ≤7 danger, 8–30 warning, 31–60 info luôn có chữ. Ngưỡng trình bày không đổi status/gia hạn. Vô hạn không nằm trong sắp hết hạn.

Quá hạn riêng: Active nhưng end_date<D là dữ liệu/chưa xử lý; không nhập 60 ngày tương lai. Expired/Terminated muốn hiện có nhãn/công thức riêng. GET không cập nhật, không POST gia hạn từ card.

Phân biệt được sắp đến hạn với bản ghi quá hạn.

### 5.3 Định biên năm — Đợt 1

HeadcountPlan(year, department, planned_headcount) + with_headcounts(); actual Active hiện tại như helper. Nhãn Định biên kế hoạch năm Y / Nhân sự Active hiện tại, không “đã duyệt”/actual lịch sử vì không approval/snapshot.

Hai thanh actual/planned chung thang max toàn biểu đồ; actual cùng sắc thương hiệu mọi phòng, planned token đối chiếu đã đo. Nhãn actual/planned, không chuẩn mỗi hàng 100%; bảng phòng/actual/planned/chênh lệch/tỷ lệ đối chiếu tổng.

Thiếu kế hoạch = Chưa nhập kế hoạch, không 0. Field planned không nullable; null DTO là thiếu bản/nguồn lỗi. `planned = 0`: Kế hoạch 0; không tính tỷ lệ. Planned>0: actual/planned ×100, vượt giữ >100%. Không phòng = Chưa xác định, không tự tạo kế hoạch.

UniqueConstraint UX_Headcount_Year_Dept từ chối trùng năm/phòng; legacy/lỗi vẫn trùng báo partial, không chọn gần nhất/cộng trùng. Không property query theo phòng khi thiếu annotation.

Định biên so kế hoạch năm với hiện trạng, chưa phải lịch sử đã duyệt.

### 5.4 Việc cần xử lý — Đợt 1

Count/row cùng selector scoped trang duyệt/guard POST thật. Bắt đầu _approvable_leave_requests; nhóm hồ sơ/tài liệu/tuyển dụng/hoạt động/checklist chỉ thêm sau đối chiếu selector. Chưa selector chung thì chưa bật, không count rộng/link hẹp.

Selector nghỉ Pending toàn Trung tâm cho HR_MANAGER/DIRECTOR/superuser, managed_departments cho DEPT_MANAGER linked. Đơn tự mình có thể nằm trong list nhưng POST cấm tự duyệt: không CTA duyệt dòng đó, không gọi tổng “tôi được phép duyệt” khi chưa loại đúng. Tổng actionable mới cần thống nhất selector với trang duyệt ở code riêng.

DIRECTOR không approve_recruitment, không tổng Pending core thành CTA duyệt tuyển dụng. Quyền từng nhóm riêng; GET sang list, quyết định POST/CSRF/confirmation/transaction ở nghiệp vụ, không duyệt hàng loạt dashboard.

Số việc và danh sách mở ra phải cùng phạm vi.

### 5.5 Đợt 2 / lịch sử Đợt 3

Nghỉ gần đây tối đa sáu dòng created_date DESC/pk DESC, total_days nghiệp vụ/scope lịch sử được duyệt. Không lý do/chứng từ/sức khỏe; Pending và Approved không chung quyền suy diễn.

Tuyển dụng: JobPosting Open là tin mở; SUM chỉ tiêu distinct RecruitmentRequest liên quan, không nhân theo số tin. Approved RecruitmentRequest thay thế phải nhãn Nhu cầu tuyển đã duyệt. Candidate chưa liên kết vị trí/phòng đủ để suy scope, không source text làm khóa. Tối đa ba hồ sơ được đọc, badge registry. Hired hiện tại không tuyển trong tháng.

Cập nhật gần đây tối đa tám bản được đọc theo timestamp/khóa ổn định. Chỉ “Đã cập nhật hồ sơ …”, không actor nếu thiếu nguồn/modified_date thành ngày duyệt/chốt/điều chuyển. Event đầy đủ cần kiểm kê; SecurityEvent/LogEntry không bao phủ mặc định mọi luồng.

Đợt 3 trend/tỷ lệ có mặt tuần/hired_at/kế hoạch đã duyệt/transition/phân bổ lịch sử. Late/Absent chỉ bản ghi đã có; thiếu không Absent. Chưa lịch/mẫu số không tỷ lệ. Thai sản cần taxonomy LeaveType xác nhận, không dò tên tiếng Việt.

Thiếu lịch sử thì bỏ chỉ số lịch sử, không số gần đúng.

### 5.6 Tiền — một nơi duy nhất, mặc định ẩn

Nhật ký **09/10/2026 — Bỏ thông tin lương nhạy cảm khỏi Trang chủ** gỡ KPI/context lương, giữ Phiếu lương riêng. Không tự đảo quyết định. **Mọi tiền, kể cả tài chính/superuser, ẩn tới khi chủ dự án duyệt policy dashboard.** Sau duyệt manage_finance bắt buộc; view_reports/view_employee_compensation/use_salary_scale_form không cấp quỹ lương. HR/DIRECTOR cần policy/quyền riêng, không âm thầm đổi PERMISSION_MATRIX.

Đủ policy: Tổng Gross kỳ lương = SUM Payroll.gross_income theo Period M/S; Phụ cấp kỳ lương = SUM allowance cùng scope. Gross không tổng chi phí Trung tâm; không cộng allowance lần nữa/tách ăn ca/xăng xe/điện thoại khi thiếu taxonomy. Aggregate nguồn riêng trước join, Decimal không float.

**Số đầy đủ ui_vnd bắt buộc**, căn phải/tabular-nums/truy cập bàn phím và trình đọc màn hình. `550,9 triệu` chỉ phụ chú, không thay số đầy đủ/đổi rounding backend. Số khác ui_number, ngày ui_date, Việt Nam.

Ghi kỳ/Open/Locked/số dòng/độ đầy đủ. Open tạm tính, Locked khóa thật. Thiếu kỳ khác không dòng, không quỹ lương 0 hoàn tất; Payslip khác dòng Payroll. Readiness/chữ ký tính/khóa có sẵn, không gross_income !=0 làm cờ; phòng hiện tại không thay snapshot phòng kỳ lịch sử.

Duyệt bố cục không đồng nghĩa mở lại lương trên Trang chủ.

## 6. Lệch giữa ảnh Atoms và dữ liệu IHRMS

| Chi tiết ảnh | Có nguồn thật không? | Nhãn trung thực / xử lý |
| --- | --- | --- |
| Quỹ lương/phụ cấp | Có Payroll/Period, policy dashboard chưa duyệt | Ẩn; sau duyệt Tổng Gross / Phụ cấp kỳ lương, mục 5.6 |
| Đã tuyển trong tháng | Hired có, thiếu ngày chuyển Hired tin cậy | Bỏ theo tháng; có thể Tổng hồ sơ đang ở trạng thái Hired trong scope được phép |
| +2 so tháng trước | Status hiện tại không đủ hai kỳ | Bỏ trend tới khi có lịch sử tương thích |
| Đã chốt bảng lương trên timeline | Status kỳ thật, chưa tự chứng minh event/actor/thời điểm | Trạng thái kỳ được đọc; bỏ event nếu thiếu log |
| Đã duyệt nghỉ phép trên timeline | Status/ngày nghỉ không tự là event duyệt | Đơn Approved/Cập nhật gần đây; event cần nguồn xác nhận |
| Đã điều chuyển trên timeline | Có nguồn điều chuyển, ngày hiệu lực khác thao tác | Ngày hiệu lực thật, không suy actor/action từ modified_date |
| Thanh định biên 3/10 | Kế hoạch/actual Active có, không approval | Active hiện tại / Định biên kế hoạch năm, không sao chép số 3/10 |
| Có mặt 73%, thai sản | Attendance/LeaveType có, mẫu số/taxonomy chưa chốt | Hoãn phần chưa rõ; Active không có mặt |
| Giờ ca/nghỉ trưa/search email | WorkShift chưa đủ liên kết, search tên/mã | Hoãn shell, không hard-code/quảng cáo email |

Ảnh là mẫu thông tin rõ ràng, không chứng minh mọi nguồn đã có.

## 7. Ma trận vai trò × khối và hồ sơ liên kết

**Gate đề xuất cho khối mới dựa quyền/route đã đọc**, không phải khối đã hiện ở Trang chủ. “Thấy” là chỉ số không tiền trong scope ghi; “Ẩn (Q)” là thiếu policy/mâu thuẫn, không render. Không suy quyền từ tên vai trò/is_staff.

### 7.1 Đợt 1

| Vai trò/cờ | Status nhân sự | Approved ngày D | Hạn + quá hạn | Loại hợp đồng | Định biên năm | Việc cần xử lý |
| --- | --- | --- | --- | --- | --- | --- |
| EMPLOYEE | Ẩn | Ẩn | Ẩn | Ẩn | Ẩn | Chỉ cá nhân hiện có |
| DEPT_MANAGER | Thấy phòng quản lý nếu linked | Ẩn (Q: Approved khác Pending) | Ẩn | Ẩn | Ẩn | Nhóm có quyền; nghỉ Pending trong phòng quản lý |
| HR_OFFICER | Thấy view_all_employees | Ẩn (Q: không view_reports) | Thấy manage_hr | Thấy manage_hr | Ẩn | Profile/lifecycle hợp lệ, không approve_leave |
| HR_MANAGER | Thấy toàn Trung tâm | Thấy view_reports | Thấy manage_hr | Thấy manage_hr | Thấy view_reports | Từng quyền duyệt, gồm tuyển dụng; không mọi workflow |
| DIRECTOR | Thấy toàn Trung tâm | Thấy view_reports | Ẩn (Q: route chặn) | Ẩn (Q: quyền hợp đồng) | Thấy view_reports | Từng quyền duyệt, không tuyển dụng |
| FINANCE_OFFICER (kế toán) | Ẩn | Ẩn | Ẩn | Ẩn | Ẩn | Chỉ nhóm riêng như mua sắm, không HR |
| SYS_ADMIN | Ẩn | Ẩn | Ẩn | Ẩn | Ẩn | Chỉ approve_office_request, không HR |
| SUPER_ADMIN không is_superuser | Ẩn (Q: không view_all_employees) | Ẩn | Ẩn | Ẩn | Ẩn | Quyền thật, không suy toàn quyền |
| is_superuser=True, active | Thấy toàn Trung tâm | Thấy | Thấy | Thấy | Thấy | Guard thật, không bỏ cấm tự duyệt |
| is_staff=True, không superuser | Theo vai trò | Theo vai trò | Theo vai trò | Theo vai trò | Theo vai trò | Theo vai trò |

Core chưa management block HR_OFFICER; đề xuất thêm status không tiền theo Read All hiện có, không thêm approve/reports. Trưởng phòng dùng managed_departments, không thay bằng phòng hồ sơ. Approved chỉ scope báo cáo nghỉ; approve Pending không tự cho lịch sử.

RBAC cho DIRECTOR xem hợp đồng, hr_contract_list đòi manage_hr và hiện 403. Chưa chốt đường đọc thì ẩn khối hợp đồng mới; số hợp đồng báo cáo cũ không tự mở danh sách/hồ sơ. RBAC mô tả Super Admin toàn quyền nhưng has_permission cấp bằng **is_superuser**, không chỉ SUPER_ADMIN: giữ mã thật, ghi Q8. Không ACCOUNTANT; kế toán FINANCE_OFFICER.

Tên vai trò không thay kiểm quyền thật.

### 7.2 Đợt 2–3 và khung riêng

| Vai trò | Nghỉ gần đây | Tuyển dụng / ứng viên | Cập nhật gần đây | Mọi tiền | Trend/tỷ lệ/timeline | Header 2/search |
| --- | --- | --- | --- | --- | --- | --- |
| EMPLOYEE | Cá nhân, không lịch sử Trung tâm | Ẩn | Ẩn quản trị | Ẩn (Q2) | Ẩn | Hoãn |
| DEPT_MANAGER | Ẩn (Q: lịch sử) | Đề xuất theo scope cũ; ứng viên ẩn | Ẩn (Q: scope) | Ẩn (Q2) | Ẩn tới đủ nguồn/policy | Hoãn |
| HR_OFFICER | Ẩn (Q: lịch sử) | Ứng viên manage_hr, tin mở chờ scope | Nguồn được đọc, chờ kiểm kê | Ẩn (Q2) | Ẩn tới đủ nguồn/policy | Hoãn |
| HR_MANAGER | Scope báo cáo, đích chi tiết cần chốt | Ứng viên manage_hr, tin mở chờ scope | Nguồn được đọc, chờ kiểm kê | Ẩn (Q2) | Ẩn tới đủ nguồn/policy | Hoãn |
| DIRECTOR | Scope báo cáo, không tự mở HR list | Ẩn ứng viên, không approve_recruitment | Nguồn đọc, không vượt guard | Ẩn (Q2) | Ẩn tới đủ nguồn/policy | Hoãn |
| FINANCE_OFFICER | Ẩn | Ẩn | Tài chính nếu policy cho | Ẩn (Q2), manage_finance chưa đủ một mình | Ẩn tới đủ nguồn/policy | Hoãn |
| SYS_ADMIN | Ẩn | Ẩn | Kỹ thuật/office được đọc, không timeline HR | Ẩn (Q2) | Ẩn | Hoãn |
| SUPER_ADMIN không superuser | Quyền thật | Quyền thật | Quyền thật | Ẩn (Q2) | Ẩn tới đủ nguồn/policy | Hoãn |
| Superuser active | Nguồn thật | Nguồn thật/scope | Nguồn thật/loại sự kiện | Ẩn (Q2) | Ẩn tới đủ nguồn/policy | Hoãn |
| Staff không superuser | Theo vai trò | Theo vai trò | Theo vai trò | Ẩn (Q2) | Theo vai trò/nguồn | Hoãn |

Bảng là điều kiện triển khai, không phải quyền mới đã duyệt.

### 7.3 Linked / unlinked và guard chung

| Tình trạng | Gate bổ sung |
| --- | --- |
| Có Employee | Theo role; hồ sơ không cấp quản trị; cá nhân lọc đúng employee |
| Chưa Employee | Không số cá nhân/CTA cần employee; DEPT_MANAGER không scope phòng; HR_MANAGER/HR_OFFICER/DIRECTOR quyền global vẫn theo bảng, không lấy cá nhân người khác |
| Superuser linked/unlinked | Global giữ; hành động cần Employee giữ guard; link Admin gắn hồ sơ chỉ cả is_superuser/is_staff như home_presentation |
| Staff linked/unlinked | Chỉ thêm view_admin_menu, không nghiệp vụ/link vượt guard |
| Không active/chưa đăng nhập | Không snapshot, giữ xác thực/has_permission |

PROJECT_MANAGER/PROJECT_COORDINATOR/CBDA giữ dự án theo quyền, không mặc định HR. Denied section loại trước query/serialize/render, không CSS ẩn.

Được vào Trang chủ không nghĩa xem mọi khối.

## 8. Kiến trúc/context đề xuất

Giữ Django SSR/portal:dashboard. Service đọc đề xuất apps/portal/dashboard_data.py/helper scope nếu cần, **chưa tạo**. home_presentation chỉ trình bày, không query mới. Dùng has_permission/data_access, không ma trận quyền thứ hai.

Luồng: xác thực/quyền → S → parse D/Y/M → query khối được phép → DTO → component chung. Metric key/label/value(int/Decimal/null)/unit/state/period_label/scope_label/source_label/formula_label/numerator/denominator/note/href. Snapshot generated_at/operational_date/plan_year/section được phép. Chưa bật tiền không field tiền/query Payroll. `href=None` nếu đích không cùng scope/filter.

GET không tạo summary/tính lương/sửa status/event nghiệp vụ. generated_at là lúc dựng trang, không cam kết transaction snapshot. Escape server, JSON nếu cần json_script, không innerHTML từ input. Lỗi có state, không lộ SQL/PII/token.

Dữ liệu bị từ chối không được lấy và gửi ra trang.

## 9. Hạng mục riêng: GET chỉ đọc / drill-down

Tham số **đề xuất**, không phải đã triển khai. Code riêng sau duyệt, giữ URL name/POST/CSRF/field/guard. Card/đích cùng selector/ngày/status/scope; department GET không mở rộng quyền.

| Route hiện có | GET đề xuất / hiện có | Queryset trùng card | Gate trước link |
| --- | --- | --- | --- |
| portal:hr_employee_list | employment_status/department; q tên/mã hiện có | Employee S/status; tổng nhiều status cần parser thống nhất | Xác minh tham số, thiếu thêm parser/test trước |
| portal:hr_contract_list | as_of=YYYY-MM-DD; expiry=upcoming/overdue; horizon=60; contract_type; status=Active | Selector hạn/hiệu lực/type mục 5.2 | Chưa filters, manage_hr bắt buộc, Director không link |
| portal:leave_approval_list | Pending hiện có; date_from/date_to nếu thêm | _approvable_leave_requests/cấm tự duyệt | Không mở Approved, chưa kỳ không link kỳ |
| portal:leave_list | status/on_date=YYYY-MM-DD nếu thêm | Own Employee | Không đích Approved toàn Trung tâm |
| portal:report_headcount | year hiện có; department nếu thêm | HeadcountPlan Y/with_headcounts | view_reports, xác minh scope/phòng |
| portal:recruitment_list | status=Pending/kỳ nếu thêm | managed_departments_for(global_roles=(HR_MANAGER,))/approve_recruitment | Không tổng Pending link mọi status chưa lọc |

Chưa đích Approved toàn Trung tâm ngày D được duyệt: chỉ số href=None. Không thêm route vượt 403. Link riêng Mở danh sách tổng có thể đúng quyền, không cả card link nếu khác số.

Test filter biên ngày/status, sai tham số/ngày đảo/phòng ngoài scope, count bằng kết quả đích cùng fixture, pagination/GET không ghi/quyền URL. Reverse được, không link403/redirect sai quyền; trước parser/queryset/test, không link/cursor pointer giả.

Chỉ bấm được khi trang mở ra giải thích đúng số đó.

## 10. Query budget và đo

Mục tiêu **≤20 SELECT** Đợt 1, cả render/lazy trên fixture cố định, **chưa đo**. Baseline cá nhân/dự án nếu vượt thì báo/xử lý riêng, không bỏ query khỏi số đếm/thay nghiệp vụ.

G3–G5: fixture giả cố định, cùng role/scope/ngày/backend; login/warm-up ngoài đo. CaptureQueriesContext quanh GET/render, tách SELECT/câu ghi. Đo trước/sau/lạnh/warm-up theo role/profile/backend thật; không số G5 cũ chứng minh dashboard.

Tăng tối đa đề xuất: status +1 SELECT, Approved +1, hạn/loại hợp đồng +3 tổng, định biên +2, mỗi nhóm queue +1 khi row/count dùng chung kết quả/annotation. Baseline + tăng của **khối được phép** vẫn ≤20. Không query đủ khối mọi role; vượt rà aggregate/thu hẹp đợt/báo thật. assertNumQueries ca ổn định; đo SELECT khi auth/render baseline đổi.

Gate trước query; conditional Count/Sum/select_related/with_headcounts/group-by. Không vòng lặp query/load mọi row đếm Python. Thêm 100 phòng/1.000 người không tăng query theo dòng. Aggregate nguồn độc lập trước join, không SUM(DISTINCT amount) vá join vì khoản bằng nhau vẫn riêng.

List 5 hợp đồng/6 nghỉ/8 cập nhật/3 ứng viên theo đợt. Cache không bắt buộc; nếu có key user/scope/quyền/D/Y/M, TTL≤60 s/invalidation quyền, không cache global dữ liệu hạn chế. p95≤1,5 s mục tiêu máy UAT ghi cấu hình/fixture/backend, không suy mock.

Người dùng thường không trả query cho khối quản trị bị ẩn.

## 11. Test nghiệm thu đề xuất Đợt 1

Tệp đề xuất `src/apps/portal/test_home_dashboard.py`, nhãn `apps.portal.test_home_dashboard`; có thể tách `test_home_dashboard_filters.py` cho GET. **Chưa tạo/chưa chạy** trong lượt tài liệu; fixture giả/DB/media cách ly qua runner, không ghi dữ liệu vận hành.

| Nhóm test | Fixture / điều kiện đạt |
| --- | --- |
| Role × khối | Mọi role mục 7/linked/unlinked/superuser/staff/SUPER_ADMIN không cờ; denied block/giá trị không HTML/JSON; mọi tiền vắng khi chưa policy |
| Status / toàn 0 | Active/Probation/OnLeave/Resigned/không phòng, không nhân đôi join; 0 hiện 0, thiếu/null/lỗi không thành 0 |
| Approved D | Hai đơn cùng người, biên ngày từ/đến bằng D, Pending/Rejected/Cancelled/ngoài scope; distinct người/không đổi total_days/nửa ngày |
| Hợp đồng | Vô hạn/D/D+60/D+61/D−1/start tương lai/Active/Expired/Terminated; quá hạn riêng, GET không sửa status |
| Nhiều hiệu lực | Một người nhiều hợp đồng đếm hợp đồng không người; donut 0/1/≥2 nhóm/bảng thay thế |
| HeadcountPlan | Không kế hoạch/null DTO/planned=0/actual vượt/không phòng; trùng năm/phòng constraint từ chối, legacy trùng partial không cộng |
| Queue | Count/row đúng selector; phòng quản lý khác phòng hồ sơ, unlinked không scope; không tự duyệt, Director không duyệt tuyển dụng |
| SUM không nhân đôi | Join một-nhiều, hai khoản bằng nhau tính một lần mỗi khoản. Tiền/Decimal/rounding test riêng nếu bật sau; Đợt 1 không query Payroll |
| GET không ghi | CaptureQueriesContext không INSERT/UPDATE/DELETE; snapshot hàng trước/sau không đổi, không get_or_create summary/status |
| Query | assertNumQueries role ổn định, baseline/sau SELECT≤20, tăng row không N+1; ordinary user không query Contract/Payroll/HeadcountPlan bị ẩn |
| Filter/link | Đúng/sai/ngoài scope/biên ngày; count khớp đích, thiếu filter href=None, không403 |

Khi code: focused ops/run_tests.py --backend sqlite nhãn mới; suite/backend liên quan DB riêng, ghi số test/exit thật. SQL Server/UAT chưa chạy ghi chưa kiểm thử; SQLite không bằng chứng thay thế.

UI: 1920/1440/1024/768/360 px × light/dark, Tab/Enter/Escape/drawer/reduced-motion/zoom/chart/table labels; contrast script cặp mới. HCNS/in/PDF/Word/Excel giữ nguyên, regression phù hợp nếu bị ảnh hưởng. Không WCAG/hoàn tất chỉ bằng danh sách đề xuất.

**Lượt sửa tài liệu:** duy nhất kiểm bắt buộc `git diff --check`; không Django/contrast vì không code/ops/check_ui_contrast.py. Không dùng kết quả cũ.

Đây là điều kiện triển khai, chưa phải kết quả đạt.

## 12. Rủi ro và việc không làm

Không quick-attendance Đúng giờ/Muộn/Phép/Vắng hoặc kanban kéo-thả: cần nghiệp vụ/quyền ghi/kiểm toán riêng. Board hiện có chỉ đọc scope được phép. Không đổi tính lương/nghỉ/khóa/duyệt/view/model/migration/quyền/URL name/field/CSRF/POST/dependency/giấy HCNS lượt này.

Không lý do nghỉ/chứng từ sức khỏe/lương cá nhân/email/CCCD trên dashboard; tên/mã tối thiểu khi quyền/nguồn cho phép. Không dữ liệu mẫu thành thật/secret hoặc PII vào Git/ảnh nghiệm thu. Không status hiện tại thành lịch sử/GET chữa quá hạn/kế hoạch trùng.

Còn mở: brand cũ MASTER, quyền Director hợp đồng/SUPER_ADMIN, policy tiền, scope nghỉ/tin tuyển/cập nhật, lịch sử/lịch ca, filters chưa có, query chưa đo. Gate hoãn/ẩn từng điểm không chặn khối độc lập đủ nguồn/quyền.

Lượt này tạo bản đặc tả để duyệt, không đổi ứng dụng.

## 13. Phân kỳ triển khai

**Đợt 1:** status nhân sự; Approved D cho scope báo cáo; sắp hết hạn + quá hạn riêng; loại hợp đồng; định biên năm; queue selector trang duyệt. Giữ cá nhân/dự án; role đủ mục 7, không chờ Director hợp đồng/policy tiền. GET filters riêng, chưa có không link. Test/query/UI thật, không chỉ CSS.

**Đợt 2:** nghỉ gần đây/tuyển dụng mở/ứng viên/Cập nhật gần đây sau scope/đích. Gross/phụ cấp chỉ sau Q2; chưa policy vẫn ẩn, bàn giao được phần không tiền. Không chuyển các khối này lại Đợt 1.

**Đợt 3:** giữ trend/tỷ lệ có mặt tuần/định biên đã duyệt/timeline transition/hired_at/phân bổ chi phí lịch sử. Chốt nguồn/policy trước, schema nếu cần giao/duyệt riêng, không giả số khớp ảnh.

**Shell riêng — hoãn:** search/header tầng 2/giờ ca/kỳ lương/badge, không gộp ba đợt dashboard. Q7 đủ nguồn/route/scope mới mở.

Duyệt đợt nào chỉ triển khai khối đủ điều kiện đợt đó.

## 14. Quyết định cần chủ dự án chốt

| Mã | Cần duyệt | Mặc định an toàn khi chưa chốt |
| --- | --- | --- |
| Q1 | Navy–teal theo Atoms hay quay tím; câu violet MASTER dòng 11 | Giữ tokens đang chạy, không đổi brand lần nữa; đồng bộ MASTER/DESIGN nhiệm vụ riêng được duyệt |
| Q2 | Quỹ lương dashboard có mở không; Finance/superuser/HR/Director xem mức nào? | Mọi tiền ẩn, Phiếu lương cá nhân riêng; nếu mở manage_finance điều kiện cần, HR/Director policy/quyền riêng |
| Q3 | Director đọc hợp đồng đích nào; RBAC và manage_hr lệch? | Ẩn khối mới/không link hr_contract_list, không cấp sửa/gia hạn để đạt đọc |
| Q4 | Mẫu số có mặt người/ngày/ca; phép/lễ/nửa ngày/nguồn thiếu? | Hoãn tỷ lệ, Active không có mặt/thiếu Attendance không vắng |
| Q5 | Event/lịch sử/hired_at/ngày tuyển chính thức/snapshot chuẩn? | Không trend/transition/tuyển theo tháng; status hiện tại/Cập nhật gần đây sau kiểm kê |
| Q6 | Tổng nhân sự đang quản lý hay mọi hồ sơ gồm Resigned? | Nhân sự đang quản lý Active+Probation+OnLeave, tách Active, không đổi total_employees |
| Q7 | Search/header 2/giờ ca có làm không, route/ca nào? | Hoãn shell, tên/mã hiện có; không email/global/hard-code giờ |
| Q8 | SUPER_ADMIN không cờ toàn quyền không; HR_OFFICER/DEPT_MANAGER lịch sử nghỉ tới đâu? | has_permission/guard thật, thiếu rõ thì ẩn, không suy role/approve Pending |

Chủ dự án duyệt bảng này và Đợt 1 trước khi giao sửa mã dashboard.

## 15. Bổ sung theo yêu cầu ngày 13/10/2026: giao diện gọn và liên kết KPI

Theo yêu cầu tiếp theo của chủ dự án, bốn KPI nhân sự có đích chỉ đọc `portal:dashboard_people` (`/portal/dashboard/people/`), với `metric=managed|active|approved|probation` và `on_date=YYYY-MM-DD`. Dùng chung scope Employee với Dashboard; managed gồm Active/Probation/OnLeave, active và probation theo trạng thái hiện tại, approved là distinct người có đơn Approved chứa ngày đã chọn. Ba chỉ số trạng thái không được trình bày như dữ liệu lịch sử.

Đích mới dùng quyền đọc hiện có: view_all_employees toàn Trung tâm, DEPT_MANAGER linked trong phòng quản lý; approved thêm view_reports. Tham số không mở rộng scope. Giá trị metric/ngày sai trả 400, không đủ quyền trả 403; tìm tên/mã và phân trang giữ bộ lọc. Chỉ gửi tên/mã/phòng/trạng thái, không lý do/chứng từ nghỉ hoặc lương. Không đổi PERMISSION_MATRIX, quy trình duyệt hoặc điều kiện phải có hợp đồng của Nhân viên & hồ sơ: danh sách chi tiết chỉ số là một đích thống kê riêng, gồm đúng người đã được KPI tính.

Giao diện giữ ngày/phạm vi ở đầu trang; chuyển giải thích công thức vào disclosure Cách tính chỉ số, giữ cách nhận biết 0/thiếu dữ liệu. KPI dùng icon people/briefcase/calendar/person; bảng/biểu đồ dùng icon theo nội dung. Hai cột biểu đồ và các khối dưới cân bằng chiều rộng, KPI giảm khoảng đệm; danh sách dài có vùng cuộn bàn phím, bảng thay thế nằm trong disclosure. Không tạo biểu đồ/trend hoặc mở lại tiền ngoài phạm vi Đợt 1. Nghiệm thu bổ sung: bấm bốn KPI, số/row đích khớp fixture, vai trò không vượt quyền, search/pagination/ngày đúng, sáng/tối và 5 độ rộng; kết quả thực tế ghi duy nhất trong PROJECT_WORK_LOG.md.

## 16. Đợt 2 — Đặc tả để duyệt, chưa triển khai

Phạm vi chỉ gồm đơn nghỉ gần đây, tuyển dụng đang mở/ứng viên và cập nhật gần đây. Phần này là đề xuất dữ liệu/giao diện; không cấp quyền mới hoặc khẳng định các khối đã chạy. Các quyết định D2 bên dưới thay thế phần dự kiến Đợt 2 của mục 7.2 sau khi được duyệt. Tìm kiếm đã được giao riêng, không đồng nghĩa header tầng 2/giờ ca/kỳ lương được duyệt.

### 16.1 Bảng tóm tắt để duyệt

| Khối/nhãn dự kiến | Nguồn đã kiểm | Quyền xem tối đa theo nguồn hiện có | Trạng thái |
| --- | --- | --- | --- |
| Đơn nghỉ gần đây của tôi | LeaveRequest, created_date/from_date/to_date/total_days/status; leave_list | Tài khoản linked, chính mình | Sẵn sàng về nguồn; chốt nhãn loại nghỉ |
| Đơn nghỉ gần đây trong phạm vi quản lý | LeaveRequest; can_read_file và LeaveScopeMixin | manage_hr / approve_leave_all_departments; DEPT_MANAGER chỉ phòng quản lý | Cần quyết định phạm vi lịch sử và đích |
| Tin có trạng thái đang tuyển | JobPosting.status/open_date/close_date; báo cáo điều hành | view_reports chỉ số tổng; chi tiết theo JobPostingAdmin và is_staff | Cần quyết định ngày hiệu lực/quyền/đích |
| Ứng viên đang xử lý | Candidate.status; hr_candidate_list | manage_hr; không tự mở cho Trưởng phòng/Giám đốc | Sẵn sàng về nguồn; chốt cách hiển thị và bộ lọc đích |
| Cập nhật quyết định nhân sự | PersonnelDecisionHistory; phạm vi PersonnelDecision | manage_hr hoặc approve_personnel_decision với đúng tập quyết định được đọc | Cần quyết định chọn nguồn và giới hạn sự kiện |
| Nhật ký hoạt động HR tổng quát / tuyển trong tháng | Không có nhật ký đầy đủ mọi thao tác; không có Candidate.hired_at/liên kết Candidate–Employee | Chưa có scope/đích đủ để bật | Chưa có nguồn |

Mặc định khi chưa chốt: ẩn khối mới; không hiện số 0 thay cho thiếu quyền/nguồn. Bảng không là bằng chứng nghiệm thu. Sau duyệt, chỉ triển khai phần đủ nguồn/quyền và query budget.

### 16.2 Nguồn thật và giới hạn đã xác minh bằng mã

- `apps/leave/models.py`: LeaveRequest có employee, leave_type, from_date, to_date, total_days, reason, attachment, status; BaseAuditModel cung cấp created_date/modified_date. LeaveApproval có bản ghi quyết định; không dùng modified_date của đơn làm ngày duyệt. `views/attendance.py:leave_list` chỉ đơn của Employee đang đăng nhập; `selectors.py:approvable_leave_requests` chỉ Pending, không phải selector lịch sử. `security/data_access.py:can_read_file` kiểm riêng đơn của chính mình, manage_hr, approve_leave_all_departments hoặc DEPT_MANAGER trong phòng quản lý; đây là bằng chứng quyền đọc đối tượng, chưa phải selector lịch sử Dashboard.
- `apps/recruitment/models.py`: JobPosting liên kết RecruitmentRequest, có posting_title/open_date/close_date/status Open|Closed; RecruitmentRequest có department/position/required_quantity/required_date/status. Candidate có code/name/status New|Screening|Interviewing|Offered|Hired|Rejected, không có FK tới JobPosting, RecruitmentRequest hoặc Employee. Interview có interview_date/result; Offer có offer_date/expected_join_date/status, không có ngày nhận việc chính thức.
- `views/recruitment.py`: recruitment_hub kiểm manage_hr/request_recruitment/approve_recruitment; recruitment_list dùng managed_departments_for(global_roles=(HR_MANAGER,)), không có filter trạng thái/kỳ; hr_candidate_list kiểm manage_hr nhưng chưa có filter nhóm trạng thái. `recruitment/admin.py`: JobPostingAdmin chỉ HR_ROLES và điều kiện is_staff/is_active của RoleBasedAdminMixin. Không suy quyền chi tiết JobPosting từ quyền mở hub.
- `portal/reporting_dashboard.py:build_report_snapshot` có aggregate Candidate.status và JobPosting.status=Open; `views/reports_planning.py:report_hub` kiểm view_reports. Số Open hiện tại không xét ngày đóng, nên không tự coi bằng số “trong khoảng hiệu lực”. DIRECTOR có thể xem aggregate báo cáo, nhưng không có manage_hr để mở hồ sơ ứng viên.
- `CandidateAdmin.create_employee_from_candidate` đổi status Hired rồi chuyển tới form tạo nhân viên, trước khi người dùng lưu Employee. Vì vậy Hired không chứng minh đã tạo hồ sơ hay đã bắt đầu làm việc. Employee.join_date là ngày vào làm của hồ sơ Employee; không có nguồn nối ngày này tới ứng viên cụ thể. **Ngày tuyển chính thức của Candidate: chưa có nguồn**. Offer.expected_join_date chỉ dự kiến; Offer Accepted không phải đã vào làm.
- `apps/common/models.py:BaseAuditModel` chỉ giữ thời điểm/người tạo, lần sửa cuối, xóa mềm; không lưu toàn bộ thao tác hay chuyển trạng thái. `security/models.py:SecurityEvent` có action/resource/record_id/occurred_at/user; nguồn hiện ghi login/logout, file_download, data_export (`security/signals.py`, `security/files.py`, HCNS/report export). Không có audit CRUD HR tổng quát. SecurityEventAdmin chỉ SYS_ADMIN/SUPER_ADMIN có is_staff hoặc superuser đủ quyền Admin; không có route portal nhật ký bảo mật.
- `document/models.py:PersonnelDecisionHistory` có action/status_from/status_to/created_date/created_by/comment/decision; `document/hcns/views.py` ghi sự kiện quyết định thật. `personnel_decision_list` và `_visible_personnel_decision` giới hạn tập đọc; recipient Employee chỉ được quyết định Issued của mình, nhưng trang detail cố ý không gửi history cho recipient. Không dùng điều kiện recipient để mở timeline lịch sử.
- Notification có title/message/created_date và người nhận; thông báo không là audit mọi nghiệp vụ. Không đưa message thông báo vào một “nhật ký hoạt động” giả; không dùng thời điểm tải Dashboard làm thời điểm nghiệp vụ.

### 16.3 Công thức và dữ liệu tối thiểu

**Đơn nghỉ gần đây:** nhãn “Đơn nghỉ gần đây của tôi” hoặc “Đơn nghỉ gần đây trong phạm vi quản lý”. Đề xuất kỳ 30 ngày theo **ngày tạo đơn**, từ 00:00 ngày D−29 đến trước 00:00 ngày D+1 theo timezone dự án, không lọc bằng ngày bắt đầu nghỉ. Pending/Approved/Rejected/Cancelled là trạng thái hiện tại, không gọi “đã duyệt trong tháng”. Lọc scope trước; loại đơn/Employee/phòng/LeaveType đã xóa khỏi khối mới, không sửa selector Pending hiện có. Sắp created_date DESC, pk DESC, tối đa 6 dòng. DTO chỉ pk, tên/mã tối thiểu của người được phép đọc, from_date/to_date, total_days sẵn có, status và nhãn loại chung. Không tính lại phép/lễ/nửa ngày, không sửa total_days. Nếu chỉ lấy 6 dòng, ghi “Tối đa 6 đơn mới nhất”, không coi len(list) là tổng số đơn trong kỳ; tổng toàn kỳ chỉ thêm khi có query budget/selector đồng nhất.

Loại nghỉ mặc định hiển thị **“Nghỉ phép” cho tất cả vai trò**; chưa duyệt mapping thì không suy từ tên/mã loại nghỉ thành nhóm y tế. Không hiện “Thai sản”, “Nghỉ ốm” hay loại sức khỏe cho người chỉ được đọc metadata. Chốt ngoại lệ tên loại chi tiết ở D2-1, không suy quyền xem y tế từ quyền duyệt.

**Tin tuyển dụng:** phương án mặc định trung thực là số JobPosting live có status=Open, nhãn “Tin có trạng thái đang tuyển”; không gọi “đang hiệu lực hôm nay” nếu không xét ngày. Nếu chốt nhãn “Đang tuyển hôm nay”, dùng thêm open_date≤D và (close_date null hoặc ≥D); D và ngày đóng là biên inclusive. Loại posting/RecruitmentRequest/phòng/vị trí đã xóa khỏi công thức mới; parent Pending/Rejected không tự coi Approved. D2-7 chốt có bắt buộc RecruitmentRequest Approved hay không; chưa chốt thì chưa bật số hiệu lực mới. Không tự đóng posting quá ngày trên GET. Required_quantity không phải số người còn thiếu nếu chưa có nguồn gán người đã tuyển vào từng yêu cầu.

**Ứng viên:** distinct Candidate live với status thuộc New, Screening, Interviewing, Offered; nhóm Hired/Rejected riêng và không gọi là tuyển trong kỳ. Đề xuất aggregate 4 nhóm, tổng là tổng nhóm hợp lệ; không join Interview/Offer làm nhân đôi. Khi chỉ có count, không lấy tên/các trường hồ sơ. Nếu duyệt danh sách ngắn, tối đa 3 tên/mã/trạng thái theo created_date DESC, pk DESC, ghi đó là mới tạo hồ sơ, không phải vừa tuyển. **Ứng viên theo phòng/tin đăng: chưa có nguồn FK**, không lọc giả bằng nguồn ứng tuyển hoặc người phỏng vấn. Tin mở và ứng viên là hai nguồn độc lập, không trình bày như phễu chuyển đổi cùng cohort.

**Cập nhật gần đây:** khuyến nghị thu hẹp thành “Cập nhật quyết định nhân sự”, chỉ sự kiện thật PersonnelDecisionHistory trong 30 ngày created_date, sắp DESC/pk DESC, tối đa 8 dòng. Trước query lịch sử phải có queryset decision đúng manage_hr/global hoặc approve_personnel_decision: PendingApproval hoặc có history do chính user tạo, như trang đích. Loại decision/employee/phòng/history đã xóa. Chỉ action, thời điểm, số quyết định tối thiểu/status; không comment, content_snapshot, nội dung giấy, dữ liệu lương, tên người thao tác. Không suy “ai vừa sửa gì” từ modified_date. Nếu chưa chọn nguồn/không có nguồn chung, ẩn khối; nếu chủ dự án muốn placeholder, ghi “Chưa có nguồn nhật ký được duyệt”, không bịa hoạt động. Nếu đủ quyền/nguồn nhưng không có sự kiện thì “Chưa có cập nhật trong kỳ”.

SecurityEvent là phương án **nhật ký truy cập/xuất dữ liệu**, không thay nhãn sự kiện HR. Muốn dùng cần quyết định riêng nguồn, gate is_staff/role Admin, scope tài nguyên và mục đích hiển thị; default ẩn trên portal. Không lộ user FK/tên đăng nhập/người thao tác nếu chưa có policy đọc actor. Notification chỉ có thể là khối “Thông báo của tôi” giữ nguồn người nhận, không nhập vào audit chung.

### 16.4 Quyền × khối đề xuất

Các ô sau là mức tối đa đề xuất sau khi chốt D2; trước đó các khối mới ẩn. “Cá nhân” chỉ khi Employee live; “global” vẫn yêu cầu has_permission thật và nguồn live. Không sửa PERMISSION_MATRIX/guard để đạt UI.

| Vai trò | Nghỉ gần đây | Tin Open | Ứng viên đang xử lý | Cập nhật quyết định nhân sự |
| --- | --- | --- | --- | --- |
| EMPLOYEE | Cá nhân; nhãn chung | Ẩn | Ẩn | Ẩn, không tự mở history recipient |
| DEPT_MANAGER | Cá nhân; lịch sử phòng cần D2-2 và managed_departments | Ẩn, đề xuất phòng là nguồn khác | Ẩn, thiếu FK scope | Ẩn |
| HR_OFFICER | Global metadata qua manage_hr, cần D2-2 | Cần D2-3; quyền Admin không tự cấp portal | Global qua manage_hr | Global qua manage_hr; cần D2-5 |
| HR_MANAGER | Global metadata qua manage_hr/all-departments; cần D2-2 | Aggregate qua view_reports; dòng chi tiết chờ D2-3 | Global qua manage_hr | Global qua manage_hr; cần D2-5/budget |
| DIRECTOR | Global metadata qua all-departments; cần D2-2 | Aggregate qua view_reports, không link hồ sơ ứng viên | Ẩn vì không manage_hr | Chỉ tập decision đọc được theo approve_personnel_decision, cần D2-5 |
| FINANCE_OFFICER | Cá nhân; không lịch sử HR toàn Trung tâm | Ẩn | Ẩn | Ẩn |
| SYS_ADMIN | Cá nhân; không lịch sử HR toàn Trung tâm | Ẩn | Ẩn | Ẩn HR; audit bảo mật là quyết định riêng |
| Superuser active | Global nguồn thật; vẫn nhãn chung trước policy | Nguồn thật; link Admin chỉ đủ staff | Global nguồn thật | Global nguồn thật; actor vẫn ẩn trước policy |

SUPER_ADMIN **không cờ is_superuser** không tự nhận toàn quyền: kiểm has_permission/guard thật; staff không tự nhận HR. HR global unlinked có thể giữ khối global nếu được duyệt nhưng không khối cá nhân. DEPT_MANAGER unlinked không lịch sử phòng. Role dự án không tự nhận HR; chỉ cá nhân nếu nguồn/Employee cho phép. Mỗi denied block phải bị loại trước query/DTO/render, không CSS ẩn và không nhúng JSON bị từ chối.

### 16.5 Loại dữ liệu nhạy cảm

Không chọn/serialize reason/attachment, giấy y tế/thai sản, CCCD/thuế/BH/tài khoản ngân hàng, lương/Offer.salary_offer, CV, điện thoại/email/địa chỉ ứng viên, comments phỏng vấn, nội dung đơn/giấy hoặc tên actor. Chỉ tên/mã người của đúng scope khi cần nhận diện. Bảng tổng tuyển dụng không kéo dữ liệu hồ sơ; tên/PK không được vào HTML/JSON của role denied. Không thêm những trường này vào tìm kiếm chung. Escape SSR, không raw innerHTML; không coi dữ liệu không hiển thị bằng CSS là đã loại khỏi phản hồi.

### 16.6 Drill-down và các đích chưa đủ

| Nguồn/đích có sẵn | Giới hạn thật | Điều kiện link hoặc việc riêng cần làm |
| --- | --- | --- |
| portal:leave_list | Own Employee, mọi trạng thái/ngày; chưa filter kỳ tạo | Link “Mở đơn nghỉ của tôi” là mở danh sách chung, không link một tổng 30 ngày; filter created_from/created_to/status cần giao riêng trước khi link count |
| portal:leave_approval_list | Pending theo selector/quyền duyệt | Chỉ queue Pending; không dùng cho lịch sử Approved/Rejected/Cancelled |
| apps.security.files/download đơn nghỉ | can_read_file, có thể ghi SecurityEvent | Không đặt link tệp/nhạy cảm trên Dashboard; không tải tệp để kiểm số |
| portal:recruitment_list | Phòng quản lý/HR_MANAGER/superuser; chưa status/kỳ | Không dùng làm đích JobPosting hoặc Candidate; bộ lọc yêu cầu tuyển dụng là hạng mục riêng |
| portal:recruitment_hub | manage_hr/request_recruitment/approve_recruitment | Mở hub bằng CTA riêng, không biến count tin/candidate thành link vì khác queryset |
| portal:hr_candidate_list | manage_hr; mọi trạng thái, chưa filter | CTA danh sách chung được phép; filter status_group=processing và cùng parent/soft-delete cần riêng trước khi click KPI processing |
| admin:recruitment_jobposting_changelist | is_staff/is_active và quyền JobPostingAdmin | Chỉ đủ cả gate; Open status filter Admin chưa bảo đảm cùng khoảng ngày/parent. Đích portal tin mở hiện chưa có; ghi hạng mục riêng, không dựng link giả |
| portal:personnel_decision_list / personnel_decision_detail | manage_hr/approve_personnel_decision; recipient Issued chỉ detail, history bị loại | Link từng sự kiện tới decision chỉ khi cùng scope được đọc. Danh sách chưa filter kỳ history; tổng sự kiện không link thành tổng decision |
| admin:security_securityevent_changelist | Quyền Admin riêng; không portal timeline | Chỉ CTA audit khi đủ quyền và policy; không dùng làm đích cập nhật HR |

Không thêm route/filter ở lượt tài liệu này. Khi triển khai, href=None nếu chưa có đích cùng bộ lọc; CTA mở danh sách chung phải được ghi đúng nhãn, không làm cả card trông bấm được. Tất cả link cần test user thật và count/tập PK khớp, phân trang giữ filter, query parameter không mở rộng scope.

### 16.7 Query budget và kế hoạch đo

Baseline dưới đây lấy số **GET + render đã đo Đợt 1**, không phải số mới của khối Đợt 2. Hai cột là unlinked/linked; SQL Server có SELECT kiểm tra transaction, không trừ khỏi tổng. Nguồn: test_dashboard_followup.test_eight_role_query_matrix và mục Hoàn thiện Đợt 1 của nhật ký.

| Vai trò | SQLite unlinked / linked | SQL Server unlinked / linked |
| --- | --- | --- |
| EMPLOYEE | 3 / 7 | 4 / 8 |
| DEPT_MANAGER | 3 / 10 | 4 / 11 |
| HR_OFFICER | 9 / 13 | 10 / 14 |
| HR_MANAGER | 12 / 16 | 13 / 17 |
| DIRECTOR | 9 / 13 | 10 / 14 |
| FINANCE_OFFICER | 3 / 7 | 4 / 8 |
| SYS_ADMIN | 3 / 7 | 4 / 8 |
| SUPER_ADMIN không superuser | 4 / 8 | 5 / 9 |
| Superuser active | Chưa đo riêng trong bảng này | Chưa đo riêng trong bảng này |

Tăng tối đa đề xuất: nghỉ +1 SELECT lấy tối đa 6 dòng/relations cần thiết; tin Open +1 aggregate; ứng viên +1 grouped aggregate. Danh sách ngắn ứng viên hoặc tin chi tiết thêm tối đa +1 **mỗi nguồn**, chỉ sau chốt budget. Cập nhật quyết định +1 SELECT sau scope bằng subquery/Exists; không query từng sự kiện/actor. Bị ẩn +0, không query nguồn hoặc load nhạy cảm.

Trần Đợt 1 ≤20 SELECT vẫn là cổng hiện tại, không tự tăng: HR_MANAGER linked SQL 17 + nghỉ 1 + tin 1 + ứng viên 1 =20; thêm history thành21, chưa được phép bật đồng thời theo phương án đơn giản. D2-8 phải chốt giảm/reuse truy vấn hoặc chia rollout, không trừ câu query khỏi báo cáo để đạt. HR_OFFICER linked SQL14 với nghỉ/candidate/history +3 là17 nếu các scope được duyệt; Director SQL14 với nghỉ/tin/history +3 là17. Đây là **dự toán**, chưa đo Đợt 2; superuser/role dự án phải đo riêng trước bật. Không chạy build_report_snapshot toàn bộ chỉ để lấy hai số tuyển dụng vì sẽ kéo query không thuộc khối.

Đo CaptureQueriesContext quanh GET/render trên fixture cố định, login/warm-up ngoài đo, từng role/profile/backend, count SELECT và ghi riêng câu ghi; thêm 100 phòng/1.000 người/ứng viên/sự kiện không tăng số query theo dòng. Kiểm cả cold/warm, 0/thiếu/lỗi, nguồn denied +0. Báo p95/máy/khối thật riêng, không suy từ số query. Cache nếu có key user/scope/quyền/kỳ và không dùng dữ liệu global cho role hẹp; chưa cần cache để làm đúng quyền.

### 16.8 Nghiệm thu khi được giao triển khai

Tệp đề xuất: `test_home_dashboard_phase2.py` (role/source/privacy/state/budget), `test_home_dashboard_phase2_filters.py` (đích/filter), mở rộng runner Edge trên DB/media giả. Chưa tạo/chạy các test khối mới ở lượt tài liệu này.

- Role × bốn nhóm dữ liệu trong bảng, linked/unlinked/superuser/staff/SUPER_ADMIN không cờ: denied section, tên/PK/counter không có trong HTML/JSON, không query bảng nguồn. Role thiếu nguồn hoặc policy ẩn, không hiện 0 giả. Named scopes dùng chung với đích, query parameter ngoài scope không thêm hồ sơ.
- Nghỉ: ngày tạo D−29 và trước D+1, đơn tạo trước kỳ nhưng nghỉ trong kỳ, timezone biên nửa đêm, các trạng thái/đơn của mình/người khác/phòng khác/quản lý nhiều phòng, parent đã xóa, loại y tế chứa giá trị sentinel; không reason/file/chi tiết sức khỏe trên phản hồi. total_days giữ nguyên, không gọi clean/save/tính lại.
- Tuyển dụng: Open/Closed, open_date tương lai, close_date null/D/D−1, parent deleted/không Approved theo D2-7; Candidate 6 status, nhiều Interview/Offer không nhân đôi count. Không có FK thì không đưa số ứng viên theo phòng/tin. Hired trước khi form Employee lưu không thành “đã tuyển trong tháng”; không lấy lương/email/điện thoại/CV.
- Cập nhật: sự kiện history thật, thời gian bằng nhau sắp PK ổn định, event của decision ngoài scope/recipient không được đọc history/actor không được đọc; comment/content_snapshot có sentinel không lọt HTML/JSON. Không dùng SecurityEvent login làm HR transition, không tạo log/Notification giả khi GET; nguồn chưa chốt/rỗng/lỗi có trạng thái/nhãn đúng.
- Drill-down: chỉ href đúng route/guard, row PK và aggregate trùng selector/kỳ/status, invalid/reversed ngày/phòng ngoài scope, pagination giữ filter. Count event khác count decision không link nhầm; không 403/404 cho link đã liệt kê. Không CTA ghi/duyệt qua GET.
- GET: service khối không INSERT/UPDATE/DELETE, snapshot hàng nghiệp vụ trước/sau không đổi. Kiểm integration và ghi riêng middleware/session hiện có nếu phát sinh, không tuyên bố toàn request read-only hoặc sửa middleware trong lượt này. Auth/login và log tải/xuất có hành vi riêng, không lấy làm bằng chứng service ghi DB.
- UI: 360/768/1024/1440 × sáng/tối, nội dung dài, control ≥44px/chữ ≥14px, Tab/Enter/Escape, reduced-motion, table thay biểu đồ, label nguồn/kỳ/0/thiếu/lỗi. Đo contrast và scope bảo mật trước khi mở khối. Không chứng nhận WCAG từ screenshot; screen reader/zoom 200% và UAT tài khoản thật là cổng riêng.

### 16.9 Rủi ro và việc không làm

Không quick-attendance, kanban kéo-thả, KPI tiền, tên/lương người thao tác, trend tuyển theo tháng, đánh dấu đã vào làm từ Hired/Accepted, thêm model/migration/ngày tuyển tự chế hoặc log giả. Không đổi quyền/guard/logic duyệt/nghỉ/lương, field form, URL name, CSRF, middleware hoặc giấy HCNS. Không sửa selector Pending có parent đã xóa trong nhiệm vụ này. Không làm header tầng 2/giờ ca/kỳ lương cùng các khối mặc định; không hard-code lịch ca từ ảnh. Các trang/mẫu hiện có vẫn là đích thật, không thay UI hay backend Đợt 2 trước khi duyệt.

### 16.10 Quyết định cho chủ dự án

| Mã | Cần chốt | Khuyến nghị mặc định an toàn |
| --- | --- | --- |
| D2-1 | Hiện tên loại nghỉ chi tiết hay nhóm chung, ai được xem? | Chỉ “Nghỉ phép” cho mọi role; không suy role HR/duyệt cho quyền y tế; ngoại lệ phải chốt riêng |
| D2-2 | Lịch sử nghỉ của HR_OFFICER/DEPT_MANAGER/global được mở tới đâu, kỳ theo ngày nào? | Own 30 ngày tạo; lịch sử phòng/global chờ duyệt scope đọc, không kế thừa Pending; không lý do/file |
| D2-3 | Ai xem aggregate tin mở và hồ sơ ứng viên? Có mở metadata JobPosting cho HR_OFFICER không staff? | Candidate chỉ manage_hr; Open aggregate chỉ view_reports; chi tiết tin theo gate thật/đích có nguồn, role khác ẩn |
| D2-4 | Ngày tuyển chính thức và liên kết ứng viên–nhân viên lấy từ đâu? | Ghi chưa có nguồn; không dùng Hired/Offer dự kiến làm ngày tuyển. Nếu cần schema/history, giao nhiệm vụ riêng sau duyệt |
| D2-5 | Chọn nhật ký nào, ai được xem, có hiện tên actor không? | Hoãn nhật ký tổng quát; nếu bật chỉ “Cập nhật quyết định nhân sự” theo quyền đọc decision, actor/comment ẩn. SecurityEvent là khối audit riêng cần policy Admin |
| D2-6 | Header tầng 2/giờ ca/kỳ lương làm cùng lượt này hay hoãn? | Hoãn; tìm kiếm đã có không cấp phép giờ ca/kỳ lương. Chưa có mapping ca áp dụng cho mọi người, không hard-code ảnh; mọi tiền vẫn ẩn |
| D2-7 | Tin đang tuyển theo status Open hay hiệu lực ngày D; parent yêu cầu phải Approved không? | Nhãn theo status hiện có; muốn xét ngày/Approved chốt công thức và đích trước, không sửa status trên GET |
| D2-8 | Ưu tiên khối khi HR_MANAGER/superuser vượt 20 SELECT, có danh sách ngắn không? | Giữ trần20; aggregate tuyển dụng trước, không bật history/danh sách ngắn đồng thời khi chưa giảm query hoặc chốt rollout riêng |

Chủ dự án duyệt từng quyết định/phần đủ nguồn trước khi giao triển khai. Lượt này dừng ở đặc tả và sửa tìm kiếm; không mở các khối Đợt 2 hoặc push/deploy.
