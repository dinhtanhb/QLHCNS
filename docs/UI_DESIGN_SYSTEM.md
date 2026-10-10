# Hệ thống giao diện IHRMS

Tài liệu này là chuẩn triển khai hiện hành cho portal và trang Báo cáo. Đặc tả trong [09_UI_UX_Specification.md](09_UI_UX_Specification.md) mô tả yêu cầu nghiệp vụ; khi màu, cỡ chữ hoặc menu mẫu cũ khác mã đang chạy, dùng chuẩn tại đây và đối chiếu quyền trong [10_RBAC_Permission_Matrix.md](10_RBAC_Permission_Matrix.md). Lịch sử thay đổi được ghi tại [PROJECT_WORK_LOG.md](PROJECT_WORK_LOG.md).

## Nguồn mã

- Bố cục, header, menu và vùng nội dung: `src/templates/base.html`.
- Token dùng chung portal/Jazzmin: `src/static/css/design_tokens.css`; font, form, focus và menu responsive: `src/static/css/ihrms.css`.
- Tailwind: nguồn `src/frontend/tailwind.input.css`, đầu ra build `src/static/css/tailwind.css`. Không chỉnh đầu ra bằng tay.
- Dashboard Báo cáo: `src/apps/portal/templates/portal/report_hub.html` và `src/static/css/report_dashboard.css`.
- Form HCNS có kiểu giấy/in riêng trong `src/static/css/hcns_forms.css`; Jazzmin dùng `src/static/css/admin.css`. Giữ font của bản in theo mẫu nghiệp vụ.

## Quy tắc hiển thị

| Thành phần | Chuẩn portal |
| --- | --- |
| Font | System sans, ưu tiên Segoe UI trên Windows; chữ nội dung tối thiểu 14px, nhãn dữ liệu quan trọng tối thiểu 13px |
| Tiêu đề | Trang 24px, panel 18px, đậm và theo thứ bậc h1/h2 |
| Màu chính | Theo [DESIGN.md](../DESIGN.md): primary `#8b5cf6`, strong `#4c1d95`, soft `#ddd6fe`, surface `#f5f3ff`; CTA dùng strong để chữ trắng rõ |
| Chữ | System sans; heading/nội dung `#2e1065`, chữ phụ `#4c1d95`; tiêu đề ưu tiên weight 600 |
| Viền/focus | `#5b21b6`; focus bàn phím rõ, không phụ thuộc hover |
| Điều khiển | Nút thao tác chính và vùng chạm mobile tối thiểu 44px cao |
| Card | Nền trắng, bo góc 12px, shadow raised nhẹ; form/selection inset; bảng dữ liệu phẳng, không lồng nhiều shadow |

Toàn bộ portal dùng theme Tailwind từ `tailwind.input.css`: các utility thương hiệu blue/indigo ánh xạ sang tím, font system và weight nhấn mạnh 600; giữ màu trạng thái đỏ/cam/xanh lá. Jazzmin có adapter trong `admin.css`, HCNS và sơ đồ tổ chức dùng token chung. CSS riêng chỉ chứa layout hoặc thành phần thực sự riêng; tránh style inline cho chữ/màu. Không đổi font Times New Roman, kích thước giấy và bố cục biểu mẫu in/xuất đã được nghiệp vụ duyệt. Áp dụng theme dùng chung không đồng nghĩa mọi trang đã được UAT trực quan.

Header, menu và nội dung dùng cùng khung 64rem mặc định; trang rộng điều chỉnh token khung tương ứng. Chỉ giá trị KPI được căn giữa, dùng tabular-nums và nhãn có chiều cao ổn định; không căn giữa tự động toàn bộ cột tiền/số trong bảng. KPI mới dùng `.ihrms-kpi-card`/`.ihrms-kpi-value` (dashboard Trang chủ/Báo cáo có selector riêng tương đương).

Khi đổi CSS, tăng phiên bản URL stylesheet và cache trong `src/static/js/service-worker.js` để PWA không giữ bản cũ; chỉ cache static, không cache HTML hay dữ liệu nghiệp vụ.

## Chế độ sáng / tối

Nút mặt trăng/mặt trời trên header (cả portal, đăng nhập và quản trị) chuyển giữa hai chế độ. Mặc định sáng; chỉ lưu lựa chọn `ihrms-theme` trong localStorage của trình duyệt, không lưu dữ liệu tài khoản. Lựa chọn được áp dụng trước stylesheet để hạn chế nháy nền và đồng bộ giữa các tab. Nếu storage bị chặn, nút vẫn hoạt động trong trang hiện tại. Theme tối là biến thể của palette tím trong DESIGN.md, giữ màu trạng thái và số KPI rõ nét. Adapter `theme.css` chỉ đổi màu trên màn hình; biểu mẫu giấy và chế độ in vẫn giữ nền trắng/Times New Roman, không thay đổi định dạng xuất Office.

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
