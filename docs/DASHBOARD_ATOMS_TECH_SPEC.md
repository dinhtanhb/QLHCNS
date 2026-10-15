# Đặc tả kỹ thuật dashboard IHRMS theo Atoms

## Bố cục gọn và Dự án lên đầu — 15/10/2026

Mục này thay các quy tắc trình bày Dashboard ngày14/10 và các mục cũ khi mâu thuẫn. Giữ công thức, DTO, quyền/guard, Q2 ẩn tiền, Q3 hợp đồng chỉ theo quyền và riêng tư D2. Không đổi `dashboard_data.py`, URL hoặc tham số GET/POST. `grouped_dashboard` chỉ ánh xạ bản sao của dữ liệu đã cấp, không thêm SELECT hay ghi bảng nghiệp vụ.

Thứ tự DOM: **KPI chính → Công việc của tôi → Dự án → Nhân sự → Hành chính → Tuyển dụng**. Nhóm ngoài quyền không có trong HTML. Dự án có đủ5 số kể cả toàn0 cho người có guard hiện hữu; quyền HR Manager hiện không cấp khối này, không tự mở rộng chỉ để khớp ảnh. Giao công việc chuyển từ Hành chính vào header Dự án; Lịch/Công việc/Dashboard hoạt động giữ đích có sẵn. Không gán link drill-down cho chỉ số khi đích chưa có bộ lọc tương ứng. Không bật tầng2 “Tuần này” vì chưa có selector/bộ lọc tuần để dùng lại trực tiếp; đề xuất riêng ở nhật ký.

Một h1 Bảng điều khiển; h2 cho từng nhóm; h3 cho thẻ. KPI dùng nhãn thường,4 thẻ100px (trần104px), cùng chiều cao; bỏ gạch và dòng Hiện tại. Công việc của tôi có hai vùng độc lập72px ở desktop, đủ Tạo đơn nghỉ/Mở đơn nghỉ/Mở công việc; tài khoản chưa gắn hồ sơ không có nhóm này. **Theo lời nhắn mới nhất của chủ dự án, mọi cặp nội dung giữ60/40**, thay50/50 hoặc7/5 trong tệp yêu cầu. Dưới1024px các cặp nội dung xếp một cột; Công việc của tôi xếp một cột dưới768px. KPI có thể xuống2 cột khi hẹp, không đo đường cơ sở giữa hai hàng khác nhau.

Nhân sự: hàng A Định biên/Cơ cấu hợp đồng60/40; hàng B Hợp đồng sắp hết hạn/Quyết định60/40. Chế độ Giám đốc gộp Định biên/Quyết định cùng hàng, không dựng hợp đồng trái Q3. Vào làm trong tháng là chip ở header nếu chưa dùng làm KPI chính; không lặp cùng số ở hai nơi. Định biên hiển thị tối đa6 phòng (4 ở chế độ gọn), sắp độ lệch lớn trước, mỗi hàng28px; một thanh so actual/planned của chính phòng, vạch kế hoạch và chỉ phần vượt tô cảnh báo kèm nhãn. Bảng hỗ trợ tiếp cận giữ toàn bộ phòng và tỷ lệ gốc.

**Giữ biểu đồ vành khuyên loại hợp đồng ở bản gọn:** khôi phục SVG từ71b6a2f, khung144px, vành khoảng22px, ký hiệu số trong cung, tổng ở giữa, chú giải tên/số/% và bảng thay thế. Chỉ vẽ donut khi≥2 nhóm; một nhóm dùng số và thanh. Geometry, tổng và tỷ trọng lấy nguyên trường đã có trong DTO; không tính lại phân bố. Chú giải cắt tên dài có title và tên đầy đủ trong bảng/disclosure. Màu từ token--ui-chart-*.

Danh sách trên mặt thẻ: hợp đồng3 dòng; quyết định tối đa5/3; đơn nghỉ3 dòng (2 ở chế độ Giám đốc). Đây là lựa chọn mật độ thấp hơn các mức tối đa trong yêu cầu để đạt ngân sách trang; các đơn còn lại trong nguồn giới hạn hiện hữu giữ ở nút thông tin, số tổng không giảm. Huy hiệu24–28px một dòng, icon cạnh chữ. Hàng chờ rỗng thu thành thanh≤40px. Tuyển dụng gộp thành một vùng mỏng có số0 nếu được cấp, nhãn Closed hiển thị Đã đóng; không đổi giá trị lưu. Không bỏ khối nghiệp vụ đã yêu cầu.

Một nguồn CSS `home_dashboard.css`, chỉ `@media screen`, giới hạn trong main Dashboard; không đổi bản in hoặc CSS form chung. Dùng--ui-dash-* cho mật độ, --ui-* cho màu/spacing. Nút thông tin native details có vùng44px, mở Enter, đóng Escape/blur/click ngoài; body nổi neo thẻ, không đẩy nội dung. Không có hàng chữ Cách tính cuối thẻ. Chip nhảy nhóm chỉ bật bằng JS khi chiều cao Dashboard>2,2 viewport. Nút tạo/điều hướng chính44px; liên kết nội tuyến trong dòng32–36px giữ ngữ nghĩa link, không tăng vùng bấm chồng lên dòng bên cạnh.

Ngân sách1440×900 trên bộ demo cách ly: header≤56, KPI≤104, Công việc của tôi≤104, Dự án≤150; thấy trọn các khối được cấp và tiêu đề Nhân sự. HR document≤1260 và nhóm Nhân sự≤520; Giám đốc document≤990; nhân viên≤900. Đo số thực, ảnh first/full1440 và390 cho4 bậc; không dùng HTTP200 thay UAT. Test9 tài khoản, sáng/tối,6 độ rộng Dashboard và audit7 độ rộng toàn route; snapshot/query/GET-write trước/sau cùng DB giả, print/PDF/cache/contrast, full suite SQLite và SQL Server. Bằng chứng và phần chưa kiểm tra ghi ở [nhật ký duy nhất](PROJECT_WORK_LOG.md).

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

Phần dự kiến này đã được thay bằng mục 16 sau khi chủ dự án duyệt các quyết định D2; trước khi duyệt, mục 16 là đề xuất.

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

Phần dự kiến này đã được thay bằng mục 16 sau khi chủ dự án duyệt các quyết định D2; trước khi duyệt, mục 16 là đề xuất.

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

**Đối chiếu 7.2 ↔ 16.4**

| Điểm khác nhau | Dự kiến cũ 7.2 | Quyết định hiện hành 16.4 (đã chốt 13/10/2026) |
| --- | --- | --- |
| DEPT_MANAGER nghỉ gần đây | Ẩn lịch sử | Chỉ cá nhân linked; không lịch sử phòng |
| HR_OFFICER nghỉ gần đây | Ẩn chờ lịch sử | Chỉ cá nhân linked, tên loại chi tiết qua manage_hr |
| FINANCE_OFFICER/SYS_ADMIN nghỉ gần đây | Ẩn | Chỉ cá nhân linked, không lịch sử HR toàn Trung tâm |
| Tin tuyển dụng | Scope chưa chốt | Aggregate Open qua view_reports; không chi tiết tin |
| Cập nhật gần đây | Nguồn đọc chưa kiểm kê, có nhánh tài chính/kỹ thuật | Chỉ lịch sử quyết định HR theo scope, không actor/comment |
| Trưởng phòng tuyển dụng | Đề xuất theo scope cũ | D2-9 trạng thái đề xuất đúng phạm vi phòng đang quản lý |
| Search/header | Hoãn cả search | Search đã có theo nhiệm vụ riêng; header2/giờ ca/kỳ lương vẫn hoãn |

Mục 16 là quyết định chi tiết hiện hành; bảng dự kiến cũ giữ để tra cứu, không ghép thành quyền mới.

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

## 16. Đợt 2 — Đã chốt 13/10/2026

Các quyết định D2-1…D2-9 đã được chủ dự án giao triển khai ngày 13/10/2026. Phần này thay thế đề xuất Đợt 2 ở mục 7.2; không đổi công thức/quyền Đợt 1. Tìm kiếm đã có; header giờ ca/kỳ lương và mọi tiền vẫn hoãn. Kết quả nghiệm thu thực tế nằm tại [nhật ký](PROJECT_WORK_LOG.md).

### 16.1 Phạm vi đã duyệt

| Khối | Nguồn | Quyền/phạm vi |
| --- | --- | --- |
| Đơn nghỉ gần đây của tôi | LeaveRequest | Employee live liên kết, chính mình |
| Đơn nghỉ gần đây toàn Trung tâm | LeaveRequest | approve_leave_all_departments: HR_MANAGER, DIRECTOR, superuser |
| Tin có trạng thái đang tuyển | JobPosting Open | view_reports; chỉ aggregate |
| Ứng viên đang xử lý | Candidate | manage_hr; aggregate sáu trạng thái, tổng bốn nhóm xử lý |
| Nhân sự vào làm trong tháng | Employee.join_date | dashboard_employee_scope giống Đợt 1 |
| Cập nhật quyết định nhân sự | PersonnelDecisionHistory | manage_hr hoặc approve_personnel_decision theo scope trang đích |
| Đề xuất tuyển dụng | RecruitmentRequest | request_recruitment/approve_recruitment; managed_departments_for(global_roles=(HR_MANAGER,)) |

Nhãn toàn Trung tâm giữ quy ước tên đơn vị hiện có. HR Officer và Trưởng phòng chỉ nghỉ của mình, không kế thừa quyền đọc file hoặc queue Pending thành lịch sử toàn phòng. Khối bị từ chối loại trước truy vấn, DTO và HTML, không CSS ẩn.

### 16.2 Nguồn thật và giới hạn

LeaveRequest.created_date là ngày tạo; from_date/to_date là kỳ nghỉ; total_days có sẵn. LeaveApproval là nguồn duyệt riêng, không dùng modified_date. Candidate không có FK tới JobPosting/RecruitmentRequest/Employee hoặc hired_at. Hired/Offer Accepted không chứng minh bắt đầu làm việc. Employee.join_date là ngày vào làm của hồ sơ, không là ngày tuyển ứng viên. Không join Interview/Offer để tính Candidate.

PersonnelDecisionHistory giữ action/status_to/created_date/decision. Trang personnel_decision_list cho manage_hr toàn bộ; người chỉ approve_personnel_decision đọc PendingApproval hoặc quyết định có history do họ tạo. Reverse history của trang hiện bao gồm bản ghi actor đã xóa mềm; subquery visibility phải giữ cùng quy tắc, nhưng sự kiện hiển thị luôn live. Recipient chỉ được detail Issued của mình; không có timeline. SecurityEvent/Notification không thay thế history HR.

recruitment_list chỉ lọc RecruitmentRequest live theo phòng live được quản lý, không loại vị trí đã xóa; khối đề xuất giữ đúng tập này. JobPosting có công thức parent live chặt hơn theo D2-7; không dùng count posting làm count đề xuất. Không sửa guard, PERMISSION_MATRIX, model/migration, CSRF, middleware, field form, URL name, logic nghỉ/duyệt/lương/giấy HCNS.

### 16.3 Công thức và DTO

**Nghỉ:** created_date từ 00:00 D−29 inclusive đến trước 00:00 D+1 theo timezone dự án; sắp −created_date,−pk; tối đa6. Nhãn “Tối đa 6 đơn mới nhất trong 30 ngày”; len(rows) không là tổng. Loại đơn/Employee/phòng/LeaveType đã xóa. DTO chỉ pk, from_date, to_date, total_days, status, nhãn loại; global thêm tên/mã Employee. Chỉ manage_hr thấy tên loại chi tiết; mọi người khác kể cả DIRECTOR chỉ “Nghỉ phép”. Không chọn reason/attachment hoặc tính lại phép/lễ. Trạng thái hiện tại, không lịch sử số được duyệt trong tháng.

**Tin:** count JobPosting live status=Open; loại yêu cầu cha/phòng/vị trí đã xóa. Không lọc open_date/close_date hoặc status cha Approved; ghi “Theo trạng thái Open, chưa xét ngày đóng”. Không tự đóng posting trên GET. Không chi tiết/admin link.

**Ứng viên:** một grouped aggregate Candidate live theo sáu trạng thái. Tổng xử lý = New+Screening+Interviewing+Offered; Hired/Rejected riêng. Hired mang nhãn “Trạng thái Hired”, không gọi đã vào làm hoặc tuyển trong kỳ. Không query tên/email/điện thoại/CV/lương, Interview/Offer hoặc nguồn báo cáo tổng. Không số theo phòng/tin do thiếu FK.

**Vào làm:** Employee live, join_date trong [đầu tháng D,D], status Active/Probation/OnLeave, dashboard_employee_scope. Không ngày tương lai/tháng trước/Resigned. Nhãn “Nhân sự vào làm trong tháng”; ghi “Theo ngày vào làm của hồ sơ nhân sự” để tránh nhãn lẫn với tuyển dụng. Count gộp vào aggregate trạng thái Đợt 1, không tăng SELECT; không đổi bốn KPI chính. Drill-down metric=joined dùng cùng selector/phạm vi/kỳ, giữ chính sách hợp đồng của Nhân viên & hồ sơ độc lập.

**Quyết định:** history live trong 30 ngày tạo như nghỉ; sắp −created_date,−pk, tối đa8; decision/Employee/phòng live, scope ở16.2 bằng subquery/Exists không N+1. DTO pk/decision_id/số quyết định/action nhãn Việt/created_date/status_to/href detail đúng scope. Không actor/comment/content_snapshot/tên Employee/lương. Rỗng “Chưa có cập nhật trong kỳ”; không log giả.

**Đề xuất:** một grouped aggregate Pending/Approved/Rejected/Closed theo scope thật của recruitment_list, không required_quantity/request_reason/ứng viên. Closed ghi “Trạng thái Closed”; không là người tuyển được. Trưởng phòng linked ghi “của phòng tôi”; HR_MANAGER/superuser toàn Trung tâm ghi “Đề xuất tuyển dụng”; note “Trạng thái hiện tại”. Trưởng phòng unlinked ẩn; scope linked không có phòng cho tổng0 trung thực. Không lọc parent thêm ngoài trang đích.

### 16.4 Quyền × khối thực tế

| Vai trò | Nghỉ tôi | Nghỉ global | Tin Open | Candidate | Vào làm | History | Đề xuất |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EMPLOYEE | Linked, chung | Ẩn | Ẩn | Ẩn | Ẩn | Ẩn | Ẩn |
| DEPT_MANAGER | Linked, chung | Ẩn | Ẩn | Ẩn | Phòng quản lý khi linked | Ẩn | Phòng quản lý khi linked |
| HR_OFFICER | Linked, chi tiết | Ẩn | Ẩn | Global | Global | Global | Ẩn |
| HR_MANAGER | Linked, chi tiết | Global, chi tiết | Global | Global | Global | Global | Global |
| DIRECTOR | Linked, chung | Global, chung | Global | Ẩn | Global | Decision đọc được | Ẩn |
| FINANCE_OFFICER / SYS_ADMIN | Linked, chung | Ẩn | Ẩn | Ẩn | Ẩn | Ẩn | Ẩn |
| SUPER_ADMIN không cờ | Linked, chung | Ẩn | Ẩn | Ẩn | Ẩn | Ẩn | Ẩn |
| Superuser active | Linked, chi tiết | Global, chi tiết | Global | Global | Global | Global | Global |

Gate bằng has_permission thật; staff chỉ mở menu Admin, không cấp khối HR. Global cho HR/Director unlinked giữ nguyên quyền global, không có khối own. Role dự án không kế thừa HR, chỉ own khi Employee live. Gate nghỉ global approve_leave_all_departments đã xác minh chỉ HR_MANAGER/DIRECTOR ngoài superuser.

### 16.5 Privacy và trạng thái

Không chọn/serialize lý do/file/giấy y tế, CCCD/thuế/BH/ngân hàng, lương, CV, contact ứng viên, comment/content_snapshot/người thao tác. Chỉ tên loại nghỉ ở manage_hr theo D2-1 đã duyệt; các role khác không nhận tên nhạy cảm ngay trong SQL projection. SSR escape, không raw innerHTML. Nguồn hợp lệ rỗng = ready với0 hoặc empty list; thiếu nguồn “Chưa có dữ liệu”; lỗi DB “Không tải được dữ liệu”, không raw SQL. Denied không là0/placeholder.

### 16.6 Drill-down

- Own nghỉ: CTA “Mở đơn nghỉ của tôi” → leave_list chung, không link count30ngày; global href=None.
- Tin: count không link; CTA recruitment_hub riêng chỉ gate manage_hr/request_recruitment/approve_recruitment.
- Candidate: count không link; CTA hr_candidate_list chung chỉ manage_hr.
- Joined: dashboard_people?metric=joined&on_date=D, cùng selector. Không thêm route/GET filter khác.
- History: từng dòng personnel_decision_detail chỉ khi guard detail thật cho phép; list có thể nhận decision qua actor event đã xóa nhưng detail chỉ history live. Trường hợp lệch này giữ metadata đúng list và href=None, kiểm guard bằng subquery trong cùng SELECT; không sửa quyền/view. Tổng event không link tổng decision.
- Đề xuất: count href=None; CTA “Mở danh sách đề xuất” → recruitment_list, chưa filter trạng thái.

### 16.7 Ngân sách và đo

Trần đã duyệt24 SELECT toàn GET+render cho mỗi role/profile/backend, không trừ transaction SELECT SQL Server. Baseline phải đo lại cùng fixture trước sửa; login/warm-up ngoài đo. Nghỉ own/global mỗi nguồn tối đa1 SELECT; khi cùng bật gộp bằng hai ROW_NUMBER (global và partition Employee), mỗi danh sách vẫn tối đa6 độc lập. Tin/candidate/history/đề xuất mỗi nguồn tối đa1; joined gộp aggregate cũ. Denied +0. Không query trong loop, không build_report_snapshot, không N+1. Thêm100phòng/1.000Employee/Candidate/history không tăng số query; đo p95 GET mục tiêu≤1,5s, ghi CPU/RAM/backend/fixture/cold/warm. Vượt phải báo/gộp/chia rollout, không giấu query. Số đo cuối thực tế và baseline nằm trong nhật ký cùng đợt; không dùng số lượt trước chứng nhận mã mới.

### 16.8 Nghiệm thu

test_home_dashboard_phase2: role×linked/unlinked/superuser/staff/SUPER_ADMIN; nguồn denied không query/DTO/HTML; privacy sentinel loại Thai sản chỉ manage_hr; biên ngày tạo, stored total_days, soft-delete, max6/max8 và sorttie. Open parent live, sáu trạng thái Candidate không nhân đôi Interview/Offer. Joined count=drill-down, scope và biên tháng/ngày/status. History cùng scope/detail và không recipient. Đề xuất count=scope recruitment_list. Service GET không ghi; middleware/session ghi riêng nếu có.

Hồi quy test_home_dashboard/test_dashboard_followup/test_dashboard_drilldown/test_global_search; probe mới thất bại mã cũ khi khả thi. Full SQLite/SQL Server trên Git index xuất TEMP, DB/media cách ly APP_ENV=test M365 off, số thực không kết quả cũ. check/dryrunmigration/pipcheck/diffcheck/contrast trên nguồn cuối. Edge headless HR Manager/Officer/Manager/Director/Employee ×360/768/1024/1440/1920×light/dark, text≥14/control≥44, bàn phím/reduced-motion/nội dung dài/nooverflow/no duplicate counters. Bằng chứng ngoài Git. Screenreader/zoom200%/tài khoản thật ghi chưa kiểm nếu chưa thực hiện.

### 16.9 Hoãn và giới hạn

Không Phase3: xu hướng/+2 tháng trước/tỷ lệ có mặt/header ca/kỳ lương/tiền/kanban/quickattendance. Không schema/history tuyển tự chế, fake FK/phễu, log giả hoặc mở quyền mới. Giữ thứ tự khối Đợt 1; thêm hàng danh sách nghỉ trái/history phải và tối đa4ô nhỏ “Chỉ số theo dõi khác”. Token/component/SVG hiện có; không dependency/font mạng/CDN/emoji/gradient/glow. Ảnh01/02/03 không có ở path tham chiếu trong lượt thực hiện; dùng ảnh Atoms chủ dự án đã gửi và ghi giới hạn nhật ký.

### 16.10 Quyết định — Đã chốt 13/10/2026

| Mã | Quyết định đã duyệt |
| --- | --- |
| D2-1 | Tên loại nghỉ chi tiết chỉ manage_hr; khác “Nghỉ phép”; không reason/attachment |
| D2-2 | Own linked + global approve_leave_all_departments; HR Officer/Trưởng phòng chỉ own;30ngày tạo/max6 |
| D2-3 | Open aggregate view_reports; Candidate aggregate manage_hr; CTA chung đúng gate, count không link |
| D2-4 | Employee.join_date đầu tháng…D/status đang quản lý/cùng scope; metric joined, không nguồn Hired/Offer |
| D2-5 | PersonnelDecisionHistory30ngày/max8; manage_hr hoặc scope approve; actor/comment/snapshot ẩn |
| D2-6 | Hoãn header tầng2/ca/kỳ lương, không hard-code |
| D2-7 | Open theo status; parent live; không xét ngày hoặc Approved cha |
| D2-8 | ≤24 SELECT toàn GET/render, denied+0/noN+1/sizegrowth/p95≤1,5s đo thực hai backend |
| D2-9 | Bật đề xuất theo request/approve_recruitment và scope trang đích; aggregate, CTA chung riêng |

Quy trình: dọn nguồn, test cuối, bản sao review không runtime/bí mật, docs commit riêng và UI commit riêng, pushmain/remoteSHA. Không forcepush/deploy; việc chưa kiểm ghi rõ nhật ký.

## 17. Chỉnh bố cục theo phản hồi ngày 13/10/2026

Tham khảo vị trí/cân đối của Atoms, giữ nguồn dữ liệu và toàn bộ gate Đợt1/2. Theo phản hồi tiếp theo ngày13/10/2026, các hàng hai cột từ1280px thống nhất trái60%/phải40% (phần rộng khả dụng sau trừ gap16px): định biên/loại hợp đồng, hợp đồng/việc xử lý, nghỉ/history. Các hàng KPI vẫn chia đều. Dưới1280px các panel xếp một cột. Hàng có một khối được phép phải dùng toàn bộ chiều rộng, không giữ ô trống cho khối bị từ chối. Các thẻ cùng hàng có chung khoảng cách16px và đường căn giá trị; phần thao tác nằm trong thẻ. Hai khối biểu đồ có cùng chiều cao, nội dung dài cuộn trong vùng giới hạn; không kéo cao panel còn lại theo số phòng vô hạn. Không đưa số/tiền/giờ ca/xu hướng từ mẫu vào ứng dụng.

Nghỉ toàn Trung tâm và history là hai khối ngang hàng. Khi cùng có nghỉ global/own, own nằm trong disclosure “Đơn nghỉ gần đây của tôi”; chỉ dữ liệu được phép mới có trong HTML. Người chỉ có own vẫn thấy khối own bình thường. Tên dài hiển thị tối đa hai dòng, giữ nguyên tên đầy đủ trong DOM/title. KPI phụ có footer chung; nhóm trạng thái mở bằng disclosure, không tạo bảng/nút rời ngoài thẻ. Các KPI legacy value=None không có nguồn không chiếm ô; số0 thật và trạng thái lỗi của nguồn Đợt1/2 vẫn giữ.

Tiêu đề quyết định căn trái cùng mép nội dung; nút ở bên phải. Bộ lọc tìm kiếm/trạng thái/nút cùng đường căn, xuống một cột trên màn hình hẹp. Một panel xử lý trước giấy xem trước, Hủy/Từ chối thu gọn và mở lý do tại chỗ, lịch sử sau giấy; giữ action/field/CSRF/guard/xuất Word/PDF và giấy HCNS. Header legacy dùng ui-page-actions có h1 được căn như page-header chung. Chỉ CSS màn hình; không sửa bố cục giấy in.

Nghiệm thu hình học Edge: khối đơn rộng bằng grid (sai số2px); panel cùng hàng căn đỉnh; giá trị KPI phụ căn cùng đường và thẻ cao bằng nhau (sai số2px ở desktop). Kiểm5role×5width×2theme, trang quyết định theo quyền, dữ liệu/tên dài, nooverflow, chữ14/control44, bàn phím/disclosure/confirmation. ops/run_dashboard_layout_uat.py và ops/run_decision_layout_uat.py dùng demo có marker synthetic ngoài source; các luồng hồ sơ/hợp đồng/nghỉ vẫn kiểm qua ops/run_browser_uat.py. Không coi screenshot hoặc HTTP200 đủ để kết luận cân đối; ghi số đo/ảnh/giới hạn vào nhật ký.

## 18. Quy chuẩn bố cục toàn ứng dụng ngày 13/10/2026

Theo yêu cầu tiếp theo, tỷ lệ trái60%/phải40% áp dụng cho các cặp khối nội dung, form hai cột và nhóm chỉ có hai KPI ở desktop từ1280px. Quy tắc này thay phần “KPI chia đều” trong mục17 đối với nhóm đúng hai ô; nhóm ba/bốn/năm KPI vẫn giữ số cột tương ứng. Khoảng cách giữa cột16px, tỷ lệ tính sau trừ khoảng cách. Màn hình nhỏ hơn xếp một cột; khối đơn dùng toàn chiều rộng. Lịch tuần, bảng dữ liệu, các nhóm ba trường và chữ ký/giấy HCNS giữ cấu trúc theo ý nghĩa nội dung.

`project_layout.css` là lớp quy chuẩn màn hình dùng chung, nạp sau CSS phân hệ. `ui-layout-split` đánh dấu các grid legacy hai cột. Ô nhập trong form dùng chiều rộng cột để tránh khoảng trống lớn giữa hai bên; ô lọc vẫn giới hạn kích thước theo loại dữ liệu. Không thay đổi schema, công thức, quyền hoặc trường gửi về backend.

Mọi dải lọc GET dùng mẫu “Dải lọc với thao tác liền kề”: `[Tìm kiếm] [Lọc phụ…] [Áp dụng] [Xóa lọc]`, flex wrap, nút liền sau trường cuối cùng, cùng đáy ô nhập; phần dư ở sau nút. Quy tắc này thay yêu cầu cột nút bên phải ở bản trước. CSS chỉ ở `shared_components.css`, trường qua `ui/field.html`, thao tác qua `ui/query_actions.html`. Form aria-label/role=search khi phù hợp, trong vùng đầu thẻ kết quả, không có thẻ lọc hoặc h2 lọc riêng. Văn bản basis16rem/max24rem, select13rem, ngày/tháng/năm/số10rem; gap12/16px, nút44px/chữ14px/focus3px. Có điều kiện lọc khác rỗng mới hiện Xóa lọc, không tính page/scope; reset giữ metric/on_date drill-down và group catalog. Tổng kết quả từ paginator hoặc dữ liệu hiện có, aria-live=polite dưới form; không bịa tổng cho lịch/báo cáo nhiều nguồn. Desktop≥1024px một hàng nếu đủ;600–1023px trường hai cột/nút dưới căn trái; <600px trường một hàng/nút chính và phụ chung hàng ở cuối. Chỉ vùng/form lọc ẩn khi in, giữ thẻ kết quả. Giữ query parameter, năm raw2026, action/quyền/phân trang, native Enter GET; không onchange tự gửi. Nút in/xuất/tạo mới thuộc thao tác trang.

Kiểm kê dùng form tạo gọn có nhãn, nút bên phải trên desktop và căn phải khi xuống dòng trên mobile. Ba trang duyệt phòng họp/xe/VPP dùng bảng cuộn và các action/CSRF/backend hiện hữu; không thêm quyền hoặc trạng thái nghiệp vụ.

Nghiệm thu bổ sung: `ops/run_project_layout_uat.py` kiểm các đường dẫn màn hình không có tham số bằng Edge,1440/1024/390px và sáng/tối; đo tỷ lệ grid, tràn trang, vị trí nút, gửi GET bằng bàn phím, tạo kiểm kê, duyệt/từ chối phòng/xe/VPP và cấp phát tồn kho. Chỉ chạy với marker synthetic ngoài repository. HTTP405 của endpoint chỉ POST được ghi riêng, không tính là màn hình đã UAT; trang chi tiết có tham số và các role Dashboard được kiểm bằng bộ hồi quy liên quan. Không suy rộng thành đã thử mọi trạng thái hoặc phiên tài khoản thật.

## 19. Bảo vệ biểu mẫu và đầu ra in

Phản hồi ngày13/10/2026 xác nhận thiếu định dạng in sau các đợt chuyển CSS sang `@media screen`. Bố cục ứng dụng60/40 không áp dụng cho giấy, chữ ký hoặc grid nhập của trình soạn HCNS. Grid HCNS giữ quy tắc riêng; `print_forms.css` nạp riêng với `media="print"`, không dùng kích thước điều khiển44px hay màu theme cho giấy.

Khi in: ẩn shell, thông báo trạng thái và icon điều khiển, form nhập/lọc và dialog. Bảng chấm công phải có đường kẻ, đủ ngày/tổng, hai vùng tổng hợp/chữ ký; in giá trị đã lưu thay cho ô nhập. Mẫu kiểm kê13cột dùng giấy ngang. Định dạng trang, lề và Times New Roman từ profile HCNS tiếp tục làm chuẩn. Giãn dòng phỏng vấn216/240 và đánh giá264/240 đối chiếu trực tiếp XML Word gốc; ngăn phần ký tách khỏi đoạn cuối. Dữ liệu nullable trên năm mẫu tài sản cũ để trống, không in “None”, không thay số0 bằng trống.

Mỗi thay đổi liên quan mẫu hoặc CSS dùng chung phải chạy kiểm tra print media và xuất PDF thật; chỉ HTTP200, ảnh giao diện màn hình hoặc compile template không đủ. `ops/run_print_layout_uat.py` dùng tài khoản HR/Finance giả đúng quyền, marker synthetic, DB/media ngoài repository; kiểm26mẫu HCNS, chấm công/báo cáo/công văn và5mẫu tài sản cũ. Xem tất cả trang PDF, kiểm bảng/đầu mục/chữ ký/ngắt trang/mẫu ngang và việc thông báo không lọt vào giấy. Phân biệt PDF thử bằng Edge với xác nhận máy in vật lý và phiên trình duyệt thật của người dùng.


### Cập nhật 14/10/2026 — Bộ lọc gắn kết quả và khối xử lý

Mẫu chuẩn: tiêu đề → dải trường và Áp dụng/Xóa lọc liền kề → số kết quả → bảng/lịch/báo cáo → phân trang, trong cùng `ui-results-card`. `ui-query-card` là vùng con `no-print`, không còn là thẻ độc lập; không ẩn toàn thẻ kết quả khi in. Chỉ một tiêu đề trực quan cho mỗi thẻ; caption bảng giữ tên truy cập bằng `ui-visually-hidden`. Nhân viên: số kết quả và ghi chú có hợp đồng/liên kết tạo hợp đồng cùng vùng metadata, tự xuống dòng khi hẹp. Báo cáo nhiều nguồn/danh mục giữ các panel con và tỷ lệ 60/40; phần chọn kỳ/hồ sơ nằm đầu vùng kết quả chung. Kích thước và hành vi dải trường giữ quy chuẩn liền kề đã chốt.

Quyết định: tiêu đề/trạng thái và tiện ích phụ → một panel Xử lý quyết định → giấy xem trước → lịch sử. Trình duyệt/Duyệt/Ghi nhận ban hành là thao tác chính theo quyền/trạng thái; Hủy/Từ chối thu gọn, mở lý do và nút xác nhận/Đóng ngay trong panel. Đóng giữ nội dung nháp trong DOM, trả focus về summary; form POST độc lập giữ CSRF và xác nhận. Khi backend từ chối dữ liệu, giữ tối đa 2000 ký tự ghi chú trong session người dùng cho đúng quyết định, lấy ra một lần ở trang đích; không lưu vào localStorage. File cần chọn lại sau lỗi; không đổi guard, trạng thái hay URL. Mọi quy tắc mới chỉ cho màn hình, panel xử lý không in.

CSS/JS thay đổi phải có URL phiên bản mới, kể cả stylesheet nạp sau đã bỏ override; tăng phiên bản cache service worker cùng đợt. Cổng kiểm thử gồm phiên cache cũ → reload thường, không yêu cầu xóa dữ liệu trình duyệt; ảnh và đo khoảng cách, cùng hồi quy PDF và luồng nghiệp vụ trên dữ liệu giả. Chi tiết thực thi/kết quả nằm duy nhất trong [nhật ký dự án](PROJECT_WORK_LOG.md).
