# Hệ thống giao diện IHRMS

Tài liệu này là chuẩn triển khai hiện hành cho portal và trang Báo cáo. Đặc tả trong [09_UI_UX_Specification.md](09_UI_UX_Specification.md) mô tả yêu cầu nghiệp vụ; khi màu, cỡ chữ hoặc menu mẫu cũ khác mã đang chạy, dùng chuẩn tại đây và đối chiếu quyền trong [10_RBAC_Permission_Matrix.md](10_RBAC_Permission_Matrix.md). Lịch sử thay đổi được ghi tại [PROJECT_WORK_LOG.md](PROJECT_WORK_LOG.md).

## Nguồn mã

- Bố cục, header, menu và vùng nội dung: `src/templates/base.html`.
- Token màu, font, form, focus và menu responsive: `src/static/css/ihrms.css`.
- Tailwind: nguồn `src/frontend/tailwind.input.css`, đầu ra build `src/static/css/tailwind.css`. Không chỉnh đầu ra bằng tay.
- Dashboard Báo cáo: `src/apps/portal/templates/portal/report_hub.html` và `src/static/css/report_dashboard.css`.
- Form HCNS có kiểu giấy/in riêng trong `src/static/css/hcns_forms.css`; Jazzmin dùng `src/static/css/admin.css`. Giữ font của bản in theo mẫu nghiệp vụ.

## Quy tắc hiển thị

| Thành phần | Chuẩn portal |
| --- | --- |
| Font | System sans, ưu tiên Segoe UI trên Windows; chữ nội dung tối thiểu 14px, nhãn dữ liệu quan trọng tối thiểu 13px |
| Tiêu đề | Trang 24px, panel 18px, đậm và theo thứ bậc h1/h2 |
| Màu chính | `--ihrms-primary: #1d4ed8`; hover `#1e40af`; nền nhạt `#eff6ff` |
| Chữ | Heading `#0f172a`, nội dung `#334155`, chữ phụ `#475569` |
| Viền/focus | `#cbd5e1`; focus bàn phím rõ, không phụ thuộc hover |
| Điều khiển | Nút thao tác chính và vùng chạm mobile tối thiểu 44px cao |
| Card | Nền trắng, viền nhạt, bo góc 12–16px, khoảng cách đều |

Trang mới dùng token từ `ihrms.css`; CSS riêng chỉ chứa layout hoặc thành phần thực sự riêng. Tránh style inline cho chữ/màu và tránh thêm thang màu xanh khác.

## Điều hướng, bảng và biểu đồ

- Menu hiển thị theo ma trận quyền; URL trực tiếp vẫn phải được kiểm tra quyền ở view.
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
