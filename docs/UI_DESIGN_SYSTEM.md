# Hệ thống giao diện IHRMS

## Hợp đồng thành phần đang áp dụng

Chuẩn màu hiện hành là teal/trung tính trong `DESIGN.md`, `design-system/MASTER.md` và token `--ui-*` trong `ui_tokens.css`.

- Khung nội dung tối đa 1440px, lề 24px trên desktop và 16px dưới 768px; nhóm nội dung cách nhau 24px.
- Card màn hình mặc định có đệm 24px, mobile 16px, viền nhẹ và không bóng. Nội dung trực tiếp trong `.ui-card` vẫn được hỗ trợ. `.ui-card--sectioned` dùng header/body tự có đệm; `.ui-card--table` cho bảng sát mép, tiêu đề vẫn có đệm. Không dùng các modifier này cho card chưa có cấu trúc tương ứng.
- Tiêu đề trang 24px/700; tiêu đề nhóm/card 18px/600, cách nội dung 16px; nhãn và nhãn KPI 14px. Không đặt chiều cao cố định để ép nội dung.
- Nút thường tối thiểu 44px, chữ 14px, bo 8px, nhóm có gap 8–12px và wrap. Primary teal dùng cho tạo/thêm/lưu/gửi/đặt/giao/duyệt/tiếp nhận/cập nhật/chọn-áp dụng; secondary cho mở/xem/quản lý/theo dõi/in/xuất/tải/quay lại/hủy điều hướng; tertiary là liên kết điều hướng phụ. Từ chối, hủy dữ liệu, khóa kỳ và thanh lý dùng danger viền; chỉ xác nhận phá hủy trong dialog mới dùng danger đặc. Dashboard cho phép mọi thao tác tạo hoặc giao việc là primary, còn điều hướng là link. Dữ liệu kiểm tra máy đọc từ `UI_BUTTON_KINDS.json`; hành động ngang vai dùng cùng variant.
- `.ui-form-stack` có trường nhập, `.ui-form-container` và `.ui-form-section` cung cấp named container `ui-form`; grid tương thích cũ chuyển 1/2/3/4 cột ở 420/640/900px; form đã chuyển dùng mẫu inline/grouped/long/event theo nội dung. Form chỉ có nút không tạo size container để tránh mất bề rộng nội tại trong hàng flex. Không đặt size container trên chính grid để query grid đó. Span số cũ chỉ là lớp tương thích; khi chuyển từng form phải xác định trường thường/rộng/toàn hàng theo nội dung.
- Hàng nút nằm cuối form, không sticky đè lên trường nhập. Dải lọc GET giữ hợp đồng riêng trong `MASTER.md`; bản in và giấy HCNS độc lập với lưới màn hình.

Ba trang mẫu Dashboard/Tuyển dụng/Tài sản và ảnh trước/sau là điểm duyệt trước khi mở rộng template. Có CSS dùng chung không đồng nghĩa mọi route đã được nghiệm thu. Bằng chứng, số vi phạm và phần còn mở ghi duy nhất tại `PROJECT_WORK_LOG.md`.

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
| Màu chính | Teal theo `--ui-brand`, `--ui-on-brand`; bề mặt theo token ngữ nghĩa và theme |
| Chữ | `--ui-text`, `--ui-text-muted`; tiêu đề card 600, tiêu đề trang 700 |
| Viền/focus | `--ui-border`, `--ui-focus`; focus bàn phím rõ, không phụ thuộc hover |
| Điều khiển | Nút thao tác chính và vùng chạm mobile tối thiểu 44px cao |
| Card | Bề mặt theo theme, bo 8px, viền nhẹ, không bóng; đệm theo hợp đồng ở trên |

Portal dùng theme Tailwind từ `tailwind.input.css`: utility thương hiệu ánh xạ sang token teal; giữ màu trạng thái đỏ/cam/xanh lá. Jazzmin có adapter trong `admin.css`, HCNS và sơ đồ tổ chức dùng token chung. CSS riêng chỉ chứa layout hoặc thành phần thực sự riêng; tránh style inline cho chữ/màu. Không đổi font Times New Roman, kích thước giấy và bố cục biểu mẫu in/xuất đã được nghiệp vụ duyệt. Áp dụng theme dùng chung không đồng nghĩa mọi trang đã được UAT trực quan.

Vùng nội dung dùng `--ui-content-max-width` (1440px), trừ diện tích sidebar và lề khi không đủ chỗ. Giá trị KPI dùng tabular-nums; cột tiền/số trong bảng căn phải. Thành phần mới dùng `.ui-kpi`/`.ui-kpi-value`; Dashboard có bố cục riêng nhưng giữ cùng token.

Tài nguyên dùng template tag `asset` để băm nội dung và đồng bộ phiên bản service worker; chỉ cache static, không cache HTML hay dữ liệu nghiệp vụ. `print_forms.css` vẫn tuân thủ quy tắc tăng `?v=` khi sửa theo AGENTS.md.

## Chế độ sáng / tối

Nút mặt trăng/mặt trời trên header (cả portal, đăng nhập và quản trị) chuyển giữa hai chế độ. Mặc định sáng; chỉ lưu lựa chọn `ihrms-theme` trong localStorage của trình duyệt, không lưu dữ liệu tài khoản. Lựa chọn được áp dụng trước stylesheet để hạn chế nháy nền và đồng bộ giữa các tab. Nếu storage bị chặn, nút vẫn hoạt động trong trang hiện tại. Theme tối dùng palette teal/trung tính trong DESIGN.md, giữ màu trạng thái và số KPI rõ nét. Adapter `theme.css` chỉ đổi màu trên màn hình; biểu mẫu giấy và chế độ in vẫn giữ nền trắng/Times New Roman, không thay đổi định dạng xuất Office.

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

Chọn cấu trúc theo nghiệp vụ trong [UI_FORM_REGISTRY.json](UI_FORM_REGISTRY.json), không ép mọi form thành bốn cột. `.ui-form-grid--inline` cho form ngắn: nút liền sau control cuối, căn đáy; khoảng trống dư nằm sau nút. `.ui-form-grid--grouped` cho form vừa, `--long` cho form dài chia nhóm. `ui/field.html` dùng `width="regular|wide|full"`; span số chỉ tương thích cũ. Bộ lọc giữ `ui-query-bar` riêng; thao tác trong bảng giữ form POST độc lập.

Form nhóm/dài giữ track đều theo vùng chứa (1/2/3 cột, ngưỡng 420/640px); trường thường chiếm một track kể cả cuối hàng, trường rộng chiếm hai track hoặc toàn hàng khi hẹp; ghi chú/địa chỉ dài có thể toàn hàng. Form ngắn chia phần dư theo nội dung và vẫn giữ nút liền field cuối. Nhãn luôn hiện; cùng hàng căn control theo nhãn cao nhất thực tế, không dành cố định hai dòng. Gap 16px; nhóm 24px; mobile xếp theo DOM, không bóp control. Control/nút tối thiểu 44px, chữ 14px. Nút form dài ở cuối nhóm, không sticky che focus. Form lồng trong khung hẹp wrap theo vùng chứa thực.

Kiểm kê: Tên đợt → Văn phòng/Bộ phận → Thời điểm → nút, một hàng khi đủ chỗ. Đặt phòng: Phòng → Mục đích → Bắt đầu → Kết thúc → nút, một hàng khi đủ chỗ; hướng dẫn ở dưới. Sự kiện dùng `--event`, từ container 1080px: hàng 1 Tiêu đề/Loại/Phòng ban/Hình thức; hàng 2 Bắt đầu/Kết thúc/Địa điểm/Mô tả/nút. Hẹp hơn wrap theo thứ tự; không cắt dữ liệu để giữ số hàng.

Danh mục dùng select gốc; từ 10 lựa chọn (trừ tháng/năm) có nút Tìm mở vùng tìm kiếm dùng chung, hỗ trợ bàn phím. Control gốc vẫn gửi đúng giá trị và hoạt động khi tắt JS. Văn bản dùng lại dùng `ui/text_choice.html` (input + datalist), chỉ lấy giá trị từ dữ liệu tài khoản được xem; vẫn nhập mới. Không gợi ý tên người hoặc nội dung tự do toàn hệ thống. Giữ dữ liệu khi validation thất bại.

Hình thức sự kiện lưu `attendance_mode` Online/Offline; mới mặc định Offline, lịch sử NULL hiển thị Chưa xác định. Đây là ngoại lệ hợp đồng được duyệt; migration vận hành cần xác minh đích và backup riêng. Giấy/in giữ hợp đồng độc lập.
