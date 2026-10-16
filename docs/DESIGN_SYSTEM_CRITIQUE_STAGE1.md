# Báo Cáo Phê Bình Thiết Kế — Điểm Dừng 1 (Impeccable & Refactoring UI Critique)

**Thời điểm thực hiện:** 2026-10-16  
**Phạm vi:** 6 trang mẫu đại diện (Dashboard, Danh sách nhân sự, Form thêm nhân sự, Form quản lý tài sản, Báo cáo cơ cấu nhân sự, Trang đăng nhập) trên 3 độ rộng màn hình (1440x900, 1756px, 390px) và 2 theme (Sáng / Tối).  
**Số lượng ảnh chụp thực tế (Edge Headless UAT):** 36 ảnh tại `docs/screenshots/stage1_samples/`.

---

## 1. Phê bình chi tiết theo 5 Tiêu chí Thiết kế

### Tiêu chí 1: Phân cấp thị giác (Visual Hierarchy)
- **Đạt chuẩn "Exactly one primary solid button":**
  - **Dashboard:** Duy nhất nút `Tạo đơn nghỉ` mang kiểu `.ui-button--primary` (nền đặc teal thương hiệu `#0a7a68`, chữ trắng `#ffffff`).
  - Các nút tác vụ phân hệ (`Giao công việc`, `Tạo hồ sơ nhân viên`, `Tạo công văn`) đã được chuyển đổi triệt để sang `.ui-button--secondary` (nền trong suốt, viền mảnh `--ui-border-control`, chữ thương hiệu), loại bỏ hoàn toàn sự cạnh tranh thị giác và cảm giác "loạn nút đặc" của giao diện cũ.
  - Các liên kết điều hướng (`Mở đơn nghỉ →`, `Mở công việc →`, `Vào làm trong tháng: 0 →`) giữ định dạng tertiary/chip nhẹ nhàng.
  - **Trang Đăng nhập:** Nút `Đăng nhập` nổi bật duy nhất ở vị trí chân form, tập trung mọi chú ý vào hành động cốt lõi.
  - **Trang Danh sách & Form:** `Thêm nhân sự`, `Thêm tài sản` là nút hành động chính của trang, định vị rõ ràng ở góc trên hoặc chân form.
- **Phân cấp thông tin:**
  - KPI chính thứ 4 (`Cần duyệt và xử lý`): số hiển thị đồng bộ với nhãn, có icon `checklist` phân biệt rõ với icon hợp đồng và nghỉ phép; chấm cảnh báo (`attention`) chỉ kích hoạt khi có phát sinh công việc cần xử lý.

### Tiêu chí 2: Nhịp điệu & Khoảng cách (Rhythm & Spacing)
- **Khắc phục triệt để lỗi khoảng cách nhãn form ~36px:**
  - Trước đây: Nhãn form bị áp `min-height` 2 dòng giả tạo, tạo khoảng cách nhãn → ô nhập lên tới 36px, khiến nhãn trông như thuộc về ô phía trên (vi phạm nguyên tắc khoảng cách Gestalt).
  - Hiện tại: Đã loại bỏ `min-height`, thiết lập `margin-bottom: var(--ui-space-2)` (8px). Khoảng cách giữa các hàng form là `var(--ui-space-4)` (16px).
  - Tỷ lệ khoảng cách trong nhóm (8px) nhỏ hơn rõ rệt khoảng cách giữa các nhóm (16px), giúp người dùng lập tức nhận diện nhãn thuộc về ô nhập ngay dưới.
- **Thang khoảng cách chặt chẽ:** Toàn bộ khoảng cách tuân thủ thang 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64px của Refactoring UI.

### Tiêu chí 3: Kiểu chữ (Typography)
- **Thang cỡ chữ chuẩn:**
  - `Display / KPI`: 36px (`--ui-font-size-display`, bold 600) — dành riêng cho 4 số liệu Dashboard.
  - `Page Title`: 24px (`--ui-font-size-title`, bold 600) — tiêu đề trang.
  - `Section / Card Title`: 18px (`--ui-font-size-lg`, semibold 600) — tiêu đề nhóm và thẻ.
  - `Body / Form Label`: 16px (`--ui-font-size-body`, regular 400 & medium 500) — văn bản chính và nhãn nhập liệu.
  - `Caption / Small`: 14px (`--ui-font-size-small`, regular 400) — chú thích phụ, breadcrumb.
- **Ràng buộc trợ năng:** Tuyệt đối không dùng cỡ chữ dưới 14px cho nội dung đọc; loại bỏ hoàn toàn đơn vị `em` trong thang chữ màn hình; chiều cao dòng đạt 1.5 cho body và 1.25 cho tiêu đề lớn.

### Tiêu chí 4: Sự tiết chế (Restraint)
- **Thiết kế phẳng, tinh giản:**
  - Thẻ (`.ui-card`): `--ui-shadow-card: none`, sử dụng viền mảnh `--ui-border-subtle` để phân tách không gian thay cho bóng đổ mờ ảo không cần thiết.
  - Bo góc cố định 3 vai trò: `--ui-radius-control: 0.25rem` (4px), `--ui-radius-card: 0.5rem` (8px), `--ui-radius-pill: 9999px`. Không còn các giá trị lẻ như 3px, 6px, 10px rải rác.
  - Không sử dụng dải màu chuyển (gradient) hay emoji trang trí gây xao nhãng.

### Tiêu chí 5: Trợ năng & Tính nhất quán (Accessibility & Consistency)
- **Khắc phục lỗi tương phản Hover nút "Tạo đơn nghỉ":**
  - Tỷ lệ tương phản ở trạng thái hover trước đây: **1.12:1** (chữ trắng trên nền xám nhạt do xung đột nạp CSS).
  - Tỷ lệ tương phản hiện tại: **7.70:1** (chữ trắng `#ffffff` trên nền `--ui-brand-hover: #085e50`), vượt xa ngưỡng WCAG AA 4.5:1.
- **Tương phản tổng thể:** 208/208 cặp màu đạt chuẩn (`ops/check_ui_contrast.py`), text contrast tối thiểu 5.10:1 ở theme sáng và 7.01:1 ở theme tối.
- **Vòng nét bàn phím (Focus Ring):** 3px `--ui-focus-ring` rõ ràng trên mọi điều khiển tương tác.
- **Khả năng đáp ứng (Responsiveness):** Kiểm tra hoàn hảo ở 1756px (desktop lớn), 1440x900 (laptop) và 390px (mobile) với lưới co giãn tự nhiên không tràn viền.

---

## 2. Bảng Danh mục Ảnh Kiểm thử Thực tế (36 ảnh)

Thư mục lưu trữ: `docs/screenshots/stage1_samples/`

| STT | Trang | 1440x900 (Sáng / Tối) | 1756px (Sáng / Tối) | 390px Mobile (Sáng / Tối) |
|:---:|:---|:---:|:---:|:---:|
| 1 | **Bảng điều khiển (Dashboard)** | `dashboard_1440x900_light.png`<br>`dashboard_1440x900_dark.png` | `dashboard_1756px_light.png`<br>`dashboard_1756px_dark.png` | `dashboard_390px_light.png`<br>`dashboard_390px_dark.png` |
| 2 | **Hồ sơ nhân viên (List)** | `hr_employee_list_1440x900_light.png`<br>`hr_employee_list_1440x900_dark.png` | `hr_employee_list_1756px_light.png`<br>`hr_employee_list_1756px_dark.png` | `hr_employee_list_390px_light.png`<br>`hr_employee_list_390px_dark.png` |
| 3 | **Tạo nhân viên mới (Form)** | `hr_employee_form_1440x900_light.png`<br>`hr_employee_form_1440x900_dark.png` | `hr_employee_form_1756px_light.png`<br>`hr_employee_form_1756px_dark.png` | `hr_employee_form_390px_light.png`<br>`hr_employee_form_390px_dark.png` |
| 4 | **Quản lý tài sản (Asset Form)** | `asset_form_1440x900_light.png`<br>`asset_form_1440x900_dark.png` | `asset_form_1756px_light.png`<br>`asset_form_1756px_dark.png` | `asset_form_390px_light.png`<br>`asset_form_390px_dark.png` |
| 5 | **Báo cáo cơ cấu nhân sự** | `report_headcount_1440x900_light.png`<br>`report_headcount_1440x900_dark.png` | `report_headcount_1756px_light.png`<br>`report_headcount_1756px_dark.png` | `report_headcount_390px_light.png`<br>`report_headcount_390px_dark.png` |
| 6 | **Đăng nhập hệ thống (Login)** | `login_1440x900_light.png`<br>`login_1440x900_dark.png` | `login_1756px_light.png`<br>`login_1756px_dark.png` | `login_390px_light.png`<br>`login_390px_dark.png` |

---

## 3. Kết luận Bàn giao Điểm Dừng 1
Hệ thống thiết kế mới đã được xác minh thành công trên các mẫu giao diện cốt lõi. Cả 5 tiêu chí của Refactoring UI & Impeccable đều đạt chuẩn, các khiếm khuyết hiển thị cũ (hover nút, khoảng cách nhãn form, nút đăng nhập) đã được xử lý triệt để tận gốc trong CSS tokens và components nền tảng mà không làm vỡ bất kỳ quy tắc hay bài kiểm thử nào.
