# Hệ thống giao diện IHRMS

## Hợp đồng thành phần đang áp dụng

Chuẩn màu hiện hành là VietHealth (xanh lá logo)/trung tính theo quyết định chủ dự án 26/10/2026 trong `DESIGN.md`, `design-system/MASTER.md` và token `--ui-*` trong `ui_tokens.css`; hai pack dự phòng Chàm Đông và Than Ấm bật bằng `UI_PALETTE` (xem mục "Quay lại dải dự phòng" cuối tài liệu).

- Khung nội dung tối đa 1440px, lề 24px trên desktop và 16px dưới 768px; nhóm nội dung cách nhau 24px.
- Card màn hình mặc định có đệm 24px, mobile 16px, viền nhẹ và không bóng. Nội dung trực tiếp trong `.ui-card` vẫn được hỗ trợ. `.ui-card--sectioned` dùng header/body tự có đệm; `.ui-card--table` cho bảng sát mép, tiêu đề vẫn có đệm. Không dùng các modifier này cho card chưa có cấu trúc tương ứng.
- Tiêu đề trang 24px/700; tiêu đề nhóm/card 18px/600, cách nội dung 16px; nhãn và nhãn KPI 14px. Không đặt chiều cao cố định để ép nội dung.
- Nút thường tối thiểu 44px, chữ 14px, bo 8px, nhóm có gap 8–12px và wrap. Primary xanh lá VietHealth (mặc định; indigo/thanam khi chọn pack dự phòng) dùng cho tạo/thêm/lưu/gửi/đặt/giao/duyệt/tiếp nhận/cập nhật/chọn-áp dụng; secondary cho mở/xem/quản lý/theo dõi/in/xuất/tải/quay lại/hủy điều hướng; tertiary là liên kết điều hướng phụ. Từ chối, hủy dữ liệu, khóa kỳ và thanh lý dùng danger viền; chỉ xác nhận phá hủy trong dialog mới dùng danger đặc. Dashboard cho phép mọi thao tác tạo hoặc giao việc là primary, còn điều hướng là link. Dữ liệu kiểm tra máy đọc từ `UI_BUTTON_KINDS.json`; hành động ngang vai dùng cùng variant.
- `.ui-form-stack` có trường nhập, `.ui-form-container` và `.ui-form-section` cung cấp named container `ui-form`; grid tương thích cũ chuyển 1/2/3/4 cột ở 420/640/900px; form đã chuyển dùng mẫu inline/grouped/long/event theo nội dung. Form chỉ có nút không tạo size container để tránh mất bề rộng nội tại trong hàng flex. Không đặt size container trên chính grid để query grid đó. Span số cũ chỉ là lớp tương thích; khi chuyển từng form phải xác định trường thường/rộng/toàn hàng theo nội dung.
- Hàng nút nằm cuối form, không sticky đè lên trường nhập. Dải lọc GET giữ hợp đồng riêng trong `MASTER.md`; bản in và giấy HCNS độc lập với lưới màn hình.

Ba trang mẫu Dashboard/Tuyển dụng/Tài sản và ảnh trước/sau là điểm duyệt trước khi mở rộng template. Có CSS dùng chung không đồng nghĩa mọi route đã được nghiệm thu. Bằng chứng, số vi phạm và phần còn mở ghi duy nhất tại `PROJECT_WORK_LOG.md`.

Dashboard: header và thân thẻ dùng cùng lề ngang 24px (16px trên mobile); tiêu đề nhóm cùng lề với tiêu đề thẻ. Hai thẻ cùng hàng chia sẻ track header/thân để đường phân cách và mép đáy thẳng nhau, kể cả nhóm Nhân sự và nghỉ phép. Khi thẻ hẹp, link hành động xuống dòng riêng, tiêu đề và nút thông tin vẫn cùng dòng nếu đủ chỗ; tên dài được xuống dòng đầy đủ. Container query đặt trên header/thân, không đặt trên thẻ dùng subgrid. Disclosure nghỉ cá nhân nằm sau cặp thẻ Hành chính. Đây là căn chỉnh màn hình theo phản hồi 26/10/2026; giữ vùng bấm 44px và hợp đồng bản in độc lập.

Tài liệu này là chuẩn triển khai hiện hành cho portal và trang Báo cáo. Đặc tả trong [09_UI_UX_Specification.md](09_UI_UX_Specification.md) mô tả yêu cầu nghiệp vụ; khi màu, cỡ chữ hoặc menu mẫu cũ khác mã đang chạy, dùng chuẩn tại đây và đối chiếu quyền trong [10_RBAC_Permission_Matrix.md](10_RBAC_Permission_Matrix.md). Lịch sử thay đổi được ghi tại [PROJECT_WORK_LOG.md](PROJECT_WORK_LOG.md).

## Nguồn mã

- Bố cục, header, menu và vùng nội dung: `src/templates/base.html`.
- Token nguồn: `src/static/css/ui_tokens.css`; `design_tokens.css` là adapter. Thành phần nền ở `components.css`, tổ hợp dùng chung ở `shared_components.css`, khung ở `app_shell.css`.
- Tailwind: nguồn `src/frontend/tailwind.input.css`, đầu ra build `src/static/css/tailwind.css`. Không chỉnh đầu ra bằng tay.
- Dashboard Báo cáo: `src/apps/portal/templates/portal/report_hub.html` và `src/static/css/report_dashboard.css`.
- Form HCNS có kiểu giấy/in riêng trong `src/static/css/hcns_forms.css`; Jazzmin dùng `src/static/css/admin.css`. Giữ font của bản in theo mẫu nghiệp vụ.

## Quy tắc hiển thị

| Thành phần | Chuẩn portal |
| --- | --- |
| Font | System sans, ưu tiên Segoe UI trên Windows; nội dung và nhãn tối thiểu 14px |
| Tiêu đề | Trang 24px, panel 18px, đậm và theo thứ bậc h1/h2 |
| Màu chính | VietHealth theo `--ui-brand`, `--ui-on-brand` (mặc định); bề mặt theo token ngữ nghĩa và theme |
| Chữ | `--ui-text`, `--ui-text-muted`; tiêu đề card 600, tiêu đề trang 700 |
| Viền/focus | `--ui-border`, `--ui-focus`; focus bàn phím rõ, không phụ thuộc hover |
| Điều khiển | Nút thao tác chính và vùng chạm mobile tối thiểu 44px cao |
| Card | Bề mặt theo theme, bo 8px, viền nhẹ, không bóng; đệm theo hợp đồng ở trên |

Portal dùng theme Tailwind từ `tailwind.input.css`: utility thương hiệu ánh xạ sang token `--ui-brand` (theo palette đang cấu hình); giữ màu trạng thái đỏ/cam/xanh lá. Jazzmin có adapter trong `admin.css`, HCNS và sơ đồ tổ chức dùng token chung. CSS riêng chỉ chứa layout hoặc thành phần thực sự riêng; tránh style inline cho chữ/màu. Không đổi font Times New Roman, kích thước giấy và bố cục biểu mẫu in/xuất đã được nghiệp vụ duyệt. Áp dụng theme dùng chung không đồng nghĩa mọi trang đã được UAT trực quan.

Vùng nội dung dùng `--ui-content-max-width` (1440px), trừ diện tích sidebar và lề khi không đủ chỗ. Giá trị KPI dùng tabular-nums; cột tiền/số trong bảng căn phải. Thành phần mới dùng `.ui-kpi`/`.ui-kpi-value`; Dashboard có bố cục riêng nhưng giữ cùng token.

Tài nguyên dùng template tag `asset` để băm nội dung và đồng bộ phiên bản service worker; chỉ cache static, không cache HTML hay dữ liệu nghiệp vụ. `print_forms.css` vẫn tuân thủ quy tắc tăng `?v=` khi sửa theo AGENTS.md.

## Chế độ sáng / tối

Nút mặt trăng/mặt trời trên header (cả portal, đăng nhập và quản trị) chuyển giữa hai chế độ. Mặc định sáng; chỉ lưu lựa chọn `ihrms-theme` trong localStorage của trình duyệt, không lưu dữ liệu tài khoản. Lựa chọn được áp dụng trước stylesheet để hạn chế nháy nền và đồng bộ giữa các tab. Nếu storage bị chặn, nút vẫn hoạt động trong trang hiện tại. Theme tối dùng palette đang cấu hình trong DESIGN.md, giữ màu trạng thái và số KPI rõ nét. Adapter `theme.css` chỉ đổi màu trên màn hình; biểu mẫu giấy và chế độ in vẫn giữ nền trắng/Times New Roman, không thay đổi định dạng xuất Office.

Admin đồng bộ `data-bs-theme` của Jazzmin/Bootstrap với `data-theme` theo duy nhất lựa chọn `ihrms-theme`; giá trị `jazzmin-theme-mode` cũ không được quyết định màu thẻ riêng. Adapter màn hình trong `admin.css` đặt các biến Bootstrap/Django và màu bề mặt ngoài CSS layer để thắng CSS vendor; thẻ, lịch sử, bảng, ô nhập và dropdown theo token của palette. Admin và login nạp CSS/JS bằng hash nội dung. Nghiệm thu bằng `ops/run_admin_theme_uat.py` phải đo màu thực của từng thành phần, kiểm chuyển bằng bàn phím, reload, storage event và fallback hệ điều hành; chỉ kiểm thuộc tính `<html>` chưa đủ.

`admin.css` chỉ nạp một lần qua link có hash trong `extrahead` của admin hoặc login, không khai báo lại qua Jazzmin `custom_css`; admin cũng hash `ui_controls.css` và `ui_numbers.js`. Nút Django `.submit-row a.deletelink`/`a.closelink` không nhận màu link thương hiệu: giữ nền đỏ/xám của Django và chữ trắng rõ ở cả ba palette, sáng/tối. Cổng UAT phải đo tương phản chữ/nền thực của cả Delete và Close trên form sửa, gồm thường/hover/focus, tối thiểu 4,5:1; phải có ca kiểm âm trên nguồn trước sửa. Các nút `.btn` tương ứng của Jazzmin được kiểm riêng; không tự tạo hoặc cấp quyền xóa để làm xuất hiện nút.

## Điều hướng, bảng và biểu đồ

- Menu hiển thị theo ma trận quyền; URL trực tiếp vẫn phải được kiểm tra quyền ở view.
- Nhân sự gom nhóm “Hồ sơ & quá trình” (bao gồm Quyết định nhân sự) và “Cần duyệt & xử lý”. Người có quyền duyệt nhưng không quản lý HR vẫn thấy các liên kết duyệt được phép; không hiện liên kết quản lý hồ sơ cho họ. Tuyển dụng giữ nhóm riêng.
- Link chi tiết nêu đúng đích khi nhóm có nhiều báo cáo, như “Xem định biên” và “Xem ngân sách”.
- Vùng cuộn ngang nhận focus bàn phím, có tên truy cập và không làm toàn trang tràn ngang.
- Biểu đồ có cùng dữ liệu dạng bảng hoặc danh sách đọc được bằng bàn phím/trình đọc màn hình. Màu chỉ là tín hiệu phụ; nhãn và số luôn hiện diện.
- Dùng `h1`–`h2`, `label`, bảng có `th scope`; kiểm tra focus, contrast, zoom và trạng thái rỗng.
- Dashboard Báo cáo chỉ tổng hợp số liệu, không trình bày định danh nhân viên hoặc số tiền lương cá nhân. Excel/Word/PowerPoint dùng cùng snapshot và cùng quyền xem báo cáo.

## Kiểm tra khi đổi giao diện

1. Chạy `venv\Scripts\python.exe src\manage.py check` và test Django của màn hình liên quan trên DB thử cô lập.
2. Nếu đổi class Tailwind, chạy `npm run build:css`; kiểm tra `git diff --check`.
3. Thử trình duyệt đã đăng nhập ở 375px, 768px và 1440px: menu, lọc, nút, bảng, focus bàn phím, zoom 200%, chữ tiếng Việt và xuất tệp.
4. Với Báo cáo, đối chiếu số tổng hợp trên dữ liệu UAT đại diện, mở Excel/Word/PowerPoint trong Office. Kiểm tra quyền của HR Manager, Ban giám đốc và người không có `view_reports`.

Kiểm tra tự động HTML/CSS không thay thế UAT thị giác hoặc đối soát nghiệp vụ.

## Hợp đồng form màn hình — 17/10/2026

Ô ngày/tháng/số có chiều rộng tối đa 12rem; ngày kèm giờ 16rem; họ tên đầy đủ 36rem. Đây là giới hạn theo nội dung, không phải chiều rộng cố định: trường thu theo vùng chứa và form ngắn có thể xếp dọc toàn hàng khi hẹp. Áp dụng cả widget riêng qua loại control, không chỉ field truyền `type` vào partial. Trong grid, trường gọn vẫn giữ vị trí track đã khai báo; kiểm khoảng trống theo track, đồng thời kiểm riêng giới hạn chiều rộng control. Tháng/năm kỳ lương dùng select đủ miền 1–12 và 2000–2100; quan hệ người phụ thuộc dùng các lựa chọn thông dụng.

Chọn cấu trúc theo nghiệp vụ trong [UI_FORM_REGISTRY.json](UI_FORM_REGISTRY.json), không ép mọi form thành bốn cột. `.ui-form-grid--inline` cho form ngắn: nút liền sau control cuối, căn đáy; khoảng trống dư nằm sau nút. `.ui-form-grid--grouped` cho form vừa, `--long` cho form dài chia nhóm. `ui/field.html` dùng `width="regular|wide|full"`; span số chỉ tương thích cũ. Bộ lọc giữ `ui-query-bar` riêng; thao tác trong bảng giữ form POST độc lập.

Chủ dự án chốt bốn cột ngày 18/10/2026: form nhóm/dài dùng 1/2/3/4 track tại các ngưỡng container 420/640/900px; trường thường một track, trường rộng hai track hoặc toàn hàng khi hẹp, ghi chú dài có thể toàn hàng. Giao việc có mã một track và tên tự điền ba track; mô tả toàn hàng; người nhận/ưu tiên/ngày bắt đầu/hạn hoàn thành cùng hàng bốn track. Form ngắn vẫn dùng inline theo nội dung. Gap 16px, nhóm 24px; control/nút tối thiểu 44px, chữ 14px; mobile theo thứ tự DOM, không bóp control.

Kiểm kê: Tên đợt → Văn phòng/Bộ phận → Thời điểm → nút, một hàng khi đủ chỗ. Đặt phòng: Phòng → Mục đích → Bắt đầu → Kết thúc → nút, một hàng khi đủ chỗ; hướng dẫn ở dưới. Sự kiện dùng `--event`, từ container 1080px: hàng 1 Tiêu đề/Loại/Phòng ban/Hình thức; hàng 2 Bắt đầu/Kết thúc/Địa điểm/Mô tả/nút. Hẹp hơn wrap theo thứ tự; không cắt dữ liệu để giữ số hàng.

Danh mục từ 10 lựa chọn (trừ tháng/năm) có combobox cho gõ tìm trực tiếp, ArrowUp/Down di chuyển, Enter chọn, Escape trả về giá trị đã chọn. Select gốc vẫn gửi ID và là fallback khi tắt JS. Từ tìm chưa khớp một lựa chọn không được gửi thay ID; việc tạo danh mục mới phải dùng luồng riêng theo quyền. Văn bản dùng lại dùng `ui/text_choice.html` (input + datalist), vẫn nhập mới trong phạm vi cho phép. Mã công việc và mã hoạt động lấy từ `docs/ActCode.md`; tên do máy chủ xác định lại theo mã. Giữ giá trị khi validation thất bại.

Header card/nhóm dùng vùng nền `--ui-surface-tint`, padding và đường phân cách theo token; không dùng gạch chân giả làm header. Giữ cấu trúc KPI/Dashboard; hover KPI dùng nền/viền, không gạch chân toàn ô. Mục menu Thao tác có nền hover/focus giống tín hiệu hover dòng bảng.

Hình thức sự kiện lưu `attendance_mode` Online/Offline; mới mặc định Offline, lịch sử NULL hiển thị Chưa xác định. Đây là ngoại lệ hợp đồng được duyệt; migration vận hành cần xác minh đích và backup riêng. Giấy/in giữ hợp đồng độc lập.

## Quay lại dải dự phòng

Palette mặc định là **VietHealth**. Hai dải dự phòng Chàm Đông (indigo) và Than Ấm (graphite) được chọn bằng cấu hình máy chủ `UI_PALETTE ∈ {viethealth, chamdong, thanam}`; không có nút chọn cho từng người dùng. Cách bật: đặt `UI_PALETTE=chamdong` hoặc `UI_PALETTE=thanam` trong môi trường máy chủ (hoặc `.env`) rồi khởi động lại ứng dụng — không cần đổi mã. Giá trị lạ tự quay về `viethealth` kèm cảnh báo log. Than Ấm chỉ áp cho màn hình; bản in/bản giấy HCNS không đổi với mọi palette.

`UI_PALETTE` áp dụng cho **portal và admin**, kể cả hai trang đăng nhập. Portal đặt `data-palette` trực tiếp trên `<html>`; Jazzmin có template gốc ngoài `src/`, nên admin truyền `<meta name="ui-palette">` qua `extrahead` của `admin/base_site.html` và `registration/base.html`. `theme.js` nạp đồng bộ trong head, đọc meta và đặt `document.documentElement.dataset.palette` trước khi vẽ, cùng cơ chế đặt theme sáng/tối; không thêm inline script. `manifest.json` vẫn tĩnh theo VietHealth và bản in/bản giấy HCNS không đổi theo `UI_PALETTE`.
