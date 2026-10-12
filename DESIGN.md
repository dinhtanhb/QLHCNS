---
name: "QLHCNS / IHRMS Design System"
description: "Quy tắc thiết kế giao diện cổng nhân sự nội bộ IHRMS (Django template, tiếng Việt). Khớp design-system/MASTER.md đã duyệt."

colors:
  # Giá trị nguồn; triển khai dùng token --ui-* trong ui_tokens.css, không rải mã hex trong template.
  brandLight:     "#6d28d9"
  brandDark:      "#c4b5fd"
  bgLight:        "#f8fafc"
  surfaceLight:   "#ffffff"
  textLight:      "#0f172a"
  textMutedLight: "#475569"
  borderLight:    "#64748b"
  bgDark:         "#0f172a"
  surfaceDark:    "#1e293b"
  textDark:       "#f8fafc"
  textMutedDark:  "#cbd5e1"
  borderDark:     "#94a3b8"
  # 4 màu ngữ nghĩa (mỗi màu có text/bg/border cho cả light và dark trong tokens)
  success: "xanh lá"
  warning: "hổ phách"
  danger:  "đỏ"
  info:    "xanh dương"

typography:
  family:   "\"Segoe UI\", system-ui, -apple-system, Roboto, Arial, sans-serif"
  monoFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
  source:   "font hệ thống, không tải font ngoài"
  weights:  "400 (thân), 600 (nhãn), 700 (tiêu đề)"
  body: 16px
  table: 14px
  caption: 12px
  lineHeightBody: 1.5
  lineHeightHeading: 1.25

spacing: { xs: 4px, sm: 8px, md: 12px, lg: 16px, xl: 24px, xxl: 32px, section: 48px }
radius:  { sm: 4px, md: 8px, lg: 12px }
motion:  { feedback: 120ms, panel: 180ms }
---

# Quy tắc thiết kế IHRMS

## Mục đích và thứ bậc tài liệu
Đây là nguồn quy tắc thiết kế cho mọi thay đổi giao diện của IHRMS. Thứ bậc khi có mâu thuẫn:
1. `design-system/MASTER.md` (quyết định đã duyệt của chủ dự án) và `src/static/css/ui_tokens.css` (giá trị cụ thể).
2. Tệp này (nguyên tắc chung, quy trình, điều nên/không nên).
3. Hướng dẫn mặc định của skill UI UX Pro Max (chỉ dùng khi hai mục trên không nói tới).

Nếu phát hiện mâu thuẫn, ghi vào `docs/PROJECT_WORK_LOG.md` và chọn phương án dễ tiếp cận, nhất quán hơn; không tự đổi quyết định thiết kế.

**Lịch sử:** bản cũ của tệp này định hướng Neumorphism (bóng nổi/chìm). Đã thay bằng card có viền + bóng nhẹ vì Neumorphism làm giảm độ rõ của bảng dữ liệu dày, trạng thái và focus. Không dùng lại quy tắc Neumorphism.

## Chế độ làm việc: cải tạo dự án có sẵn
- Dự án hiện có là nguồn chân lý về nội dung, route, hành vi, dữ liệu, phân quyền và cấu trúc thông tin. Chỉ đổi lớp trình bày.
- Vá theo từng phần (token, spacing, chữ, thứ bậc, trạng thái, responsive); không viết lại toàn bộ trang khi vá nhỏ là đủ.
- Không thay nội dung thật bằng nội dung mẫu. Phần nào lệch hệ thiết kế thì chỉnh kiểu dáng, không xóa.
- Nếu thấy cần xóa nội dung, route, tính năng hay logic dữ liệu: dừng lại và hỏi chủ dự án.

### Bảo toàn khi đổi giao diện
- Giữ mọi tiêu đề, nhãn, nút, liên kết, biểu mẫu, mục menu, route, URL name, tên field, CSRF và logic lấy dữ liệu.
- Giữ nguyên điều kiện hiển thị theo quyền (RBAC). CSS/JS không thay được kiểm tra quyền ở server; không thêm vai trò mới vào giao diện.
- Giữ tương tác đang chạy: biểu mẫu, menu, chuyển light/dark, hộp thoại, phân trang.
- Giữ tên sản phẩm/công ty (VietHealth) và thuật ngữ nghiệp vụ tiếng Việt.
- Không áp token toàn cục lên biểu mẫu/giấy tờ in (HCNS). Cần in thì kiểm tra bản in riêng.

### Quy trình an toàn
1. Đọc mã giao diện hiện có trước khi sửa: template, CSS, JS, thành phần dùng chung.
2. Ánh xạ giá trị cũ sang token `--ui-*`; không thêm giá trị tùy ý ngoài thang.
3. Làm từng phần nhỏ, sau mỗi phần xác nhận nội dung gốc vẫn còn, nhìn thấy được và bấm tới được.
4. Sau khi đổi màu, đo lại tương phản các cặp bị ảnh hưởng (cả light và dark).
5. Kiểm tra desktop, tablet, mobile trước khi báo xong.

## Hướng thiết kế
- **Màu:** một màu thương hiệu tím trên nền trung tính slate; bốn màu ngữ nghĩa success/warning/danger/info. Không gradient, không glow, không tím đơn sắc toàn trang.
- **Chữ:** font hệ thống, đủ dấu tiếng Việt, không tải font từ CDN.
- **Phong cách:** doanh nghiệp, dữ liệu dày, đáng tin cậy. Card có viền 1px và bóng nhẹ; bề mặt phẳng. Bảng, form dài và tài liệu luôn dùng bề mặt phẳng dễ đọc.
- **Điều hướng:** desktop (từ 1024px) sidebar nhóm theo phân hệ, thu gọn được; dưới 1024px dùng drawer. Không dùng thanh menu ngang nhiều dropdown, không làm bottom bar.

## Token
Dùng token ngữ nghĩa trước. Giá trị nguồn trong phần frontmatter chỉ để tham chiếu, không được rải mã hex hay kích thước lẻ trong template.

### Màu
- Nền `--ui-bg`, bề mặt `--ui-surface`, bề mặt nâng `--ui-surface-raised`.
- Chữ `--ui-text`, chữ phụ `--ui-text-muted`. Viền control `--ui-border`; `--ui-divider` chỉ để chia nhóm trang trí, **không** dùng làm viền ô nhập.
- Nút chính `--ui-brand` + chữ `--ui-on-brand`, hover/active dùng `--ui-brand-hover`/`--ui-brand-active`. Chọn/selected dùng `--ui-selected-bg`/`--ui-selected-text`.
- Trạng thái: `--ui-{success,warning,danger,info}-{text,bg,border}`; lỗi dùng `--ui-error-*`.
- Warning chỉ cho việc chờ xử lý; danger chỉ cho lỗi, quá hạn, hành động nguy hiểm.
- Trạng thái luôn kèm chữ và icon, không chỉ dựa vào màu.
- Khi đổi nền sáng/tối, đảm bảo không còn chữ trắng trên nền sáng hoặc ngược lại do lớp CSS cũ.

### Chữ
- Họ chữ: `"Segoe UI", system-ui, -apple-system, Roboto, Arial, sans-serif`.
- Thân 16px, bảng và nhãn 14px, chú thích 12px; không giảm root font-size, phải zoom được tới 200%.
- Số dùng `tabular-nums`; tiền định dạng `vi-VN`, ngày `dd/MM/yyyy`; không đổi quy tắc làm tròn/dữ liệu backend.
- Tiêu đề đúng cấp ngữ nghĩa; kích thước theo tầm quan trọng bố cục, không theo số h1–h6. Letter-spacing mặc định 0.

### Khoảng cách và bo góc
- Thang 4/8/12/16/24/32/48px. Không thêm giá trị mới nếu thang giải quyết được.
- Bo góc: 4px (control nhỏ), 8px (card, ô nhập chuẩn), 12px (khối lớn).
- Control và dòng bảng cao tối thiểu 44px (có thể cao hơn khi chữ xuống dòng).

### Chọn văn bản
Dùng màu chọn từ token (`--ui-selected-bg` nền, `--ui-selected-text` chữ), không dùng `text-shadow` kiểu Neumorphism.

## Bố cục
- Mobile-first: viewport nhỏ nhất (360px) là nền tảng. Breakpoint bằng media query thật ở 360/768/1024/1440px; vùng nội dung rộng tối đa 1440px.
- Trang không được tràn ngang. Bảng rộng cuộn ngang trong khung có nhãn và focus được, hoặc chuyển thành thẻ có nhãn cột.
- Trạng thái trống, đang tải, lỗi giữ bố cục ổn định và nêu bước tiếp theo.
- Dữ liệu dày: tiêu đề bảng sticky nhưng không che focus, bộ lọc có nhãn, nút áp dụng/xóa, hiển thị số kết quả.

## Thành phần
Mọi thành phần tương tác định nghĩa đủ: mặc định, hover, active, focus-visible, disabled (dùng thuộc tính thật, không chỉ làm mờ), đang tải, thành công, lỗi — khi áp dụng.
- **Nút:** phân vai primary / secondary / tertiary / destructive / chỉ-icon. Nhãn nêu rõ hành động (tránh "Gửi" chung chung nếu gọi tên được).
- **Form:** nhãn luôn hiện; trợ giúp gần ô; lỗi cụ thể, đặt cạnh field (`aria-describedby`, `aria-invalid`); form dài chia `fieldset/legend`; có tóm tắt lỗi dẫn tới field và nhận focus sau khi gửi lỗi.
- **Card:** đại diện mục lặp hoặc công cụ độc lập, không lồng card trong card.
- **Badge/alert:** có icon SVG outline (24 viewBox, stroke 2) và chữ. Cảnh báo nghiêm trọng không tự đóng.
- **Toast:** thông tin thường `role="status"`, không giành focus, tự đóng sau ~5 giây chỉ khi không cần thao tác; lỗi và toast có hành động không tự đóng.
- **Hộp thoại/drawer:** quản lý focus, đóng bằng Esc, có nút đóng rõ, trả focus về nút mở.
- **Biểu đồ:** so sánh nhóm dùng thanh ngang, theo thời gian dùng đường; nhãn trực tiếp, đơn vị, tóm tắt chữ và bảng dữ liệu thay thế; một sắc thương hiệu cho cùng đại lượng. Không hiện biểu đồ rỗng hay thanh 100% cho một nhóm duy nhất.
- **Icon:** một bộ SVG inline nhất quán; không dùng emoji làm icon; icon trang trí `aria-hidden`, nút icon có tên truy cập.

## Chuyển động
- Chuyển động chỉ để làm rõ thay đổi trạng thái: feedback 120ms, panel 180ms, dùng token motion.
- Tôn trọng `prefers-reduced-motion` (về 0ms). Không shimmer liên tục, không chuyển màu khi đổi theme.
- Không để hover là cách duy nhất để lộ điều khiển quan trọng.

## Khả năng tiếp cận
Mục tiêu tối thiểu: **WCAG 2.1 AA**; áp dụng thêm tiêu chí 2.2 (kích thước vùng chạm, focus không bị che) khi khả thi.
- Chữ ≥ 4.5:1; thành phần UI và focus ≥ 3:1; đo cho cả light và dark.
- Focus ring 3px, offset 3px, rõ ràng, không bị overflow hoặc sticky header che; nút filled có khoảng nền tương phản quanh ring.
- Dùng được hoàn toàn bằng bàn phím, có skip-link, landmark (`header`, `nav`, `main`), `aria-current="page"` cho mục đang chọn.
- Vùng chạm ≥ 44px.
- HTML ngữ nghĩa trước, ARIA chỉ để bổ sung. Chỉ dùng `aria-sort` khi backend thật sự hỗ trợ sắp xếp.
- Không tuyên bố "đạt WCAG" cho cả ứng dụng nếu chưa kiểm bằng công cụ và người; đo token không chứng minh toàn app.

## Giọng điệu nội dung
Rõ ràng, ngắn gọn, ít thuật ngữ, tiếng Việt tự nhiên.
- Nhãn hành động trực tiếp.
- Trạng thái trống hữu ích: chuyện gì đã xảy ra, vì sao quan trọng, người dùng làm gì tiếp.
- Phân biệt: chưa có dữ liệu / bộ lọc không có kết quả / không có quyền / lỗi tải.

## Nên
- Dùng token ngữ nghĩa thay giá trị thô.
- Giữ nội dung, route, hành vi và quyền khi áp dụng hệ thiết kế.
- Tạo thứ bậc bằng khoảng cách, tương phản, chữ và trạng thái.
- Thiết kế mobile-first rồi mở rộng cho tablet/desktop.
- Dùng chung một ánh xạ trạng thái → màu/icon cho toàn app.
- Tái sử dụng thành phần dùng chung (`{% include %}`/CSS component) khi đã có.

## Không nên
- Dùng chữ tương phản thấp, ẩn focus, hoặc truyền đạt trạng thái chỉ bằng màu.
- Xóa/thay nội dung sản phẩm khi chưa được yêu cầu.
- Thêm giá trị spacing/chữ/bo góc ngoài hệ token.
- Dùng bóng nổi/chìm (Neumorphism), gradient, glow, hiệu ứng nặng.
- Tải font hoặc script từ CDN ngoài; thêm dependency mà không ghi log.
- Gán mỗi phòng ban một màu trong biểu đồ.
- Biến mọi card thành liên kết khi chưa có trang đích hoặc người dùng không có quyền xem.
- Thêm animation trang trí không có phương án reduced-motion.

## Danh sách kiểm cho AI trước khi báo xong
- Đã đọc `MASTER.md`, tệp này và tokens trước khi đổi giao diện.
- Mọi mục menu, nút, biểu mẫu, liên kết, route gốc vẫn còn và đúng quyền hiển thị.
- Không có chữ vô hình do màu nền/độ mờ/kế thừa màu.
- Màn hình đầu tiên có nội dung thật, không chỉ nền trang trí.
- Đã kiểm tra bàn phím, focus-visible, responsive (360/768/1024/1440px), light/dark, tràn chữ, trạng thái tải/lỗi/trống.
- Phần chưa kiểm tra được ghi rõ trong nhật ký, không báo đạt khi chưa có bằng chứng.

## Ngoại lệ điều hướng đã được chủ dự án duyệt — Đợt 2b

Sidebar được phép dùng nền thương hiệu nhạt `--ui-sidebar-hover-bg`, chữ `--ui-sidebar-hover-text`, vạch trái 3px `--ui-sidebar-marker`, viền thương hiệu mờ 1px `--ui-sidebar-hover-border` và bóng nhẹ `--ui-shadow-card` khi hover hoặc focus-visible. Viền mờ là trang trí; vạch và chữ cung cấp tín hiệu tương phản. Dùng `--ui-motion-feedback` 120ms, về 0ms khi reduced-motion; không gradient, blur hay glow. Pointer không hiện vòng focus; bàn phím giữ vòng focus-visible rõ. Mục con chỉ có chữ thụt vào, đường nối dọc mảnh, active đậm và `aria-current="page"`; nhóm chỉ giữ chevron bên phải.

Nền trang/card/control và track biểu đồ dùng slate; KPI mặc định `--ui-text`, cảnh báo chỉ khi giá trị > 0 và có nhãn. Biểu đồ bốn chuỗi dùng `--ui-chart-hire/departure/transfer/promotion`, chú giải chữ và bảng số liệu; giá trị 0 không vẽ thanh. Tím chỉ dùng cho hành động chính, link, selected/active, focus và dữ liệu chính; ngoại lệ hover sidebar nêu trên. Biểu mẫu HCNS giữ palette giấy/in đã có. Kết quả đo và giới hạn xác minh: [nhật ký dự án](docs/PROJECT_WORK_LOG.md).

## Mẫu bố cục trang chuẩn — triển khai ở Giai đoạn 4

Đây là quy chuẩn chuẩn bị; đợt 2b chưa áp dụng bố cục này trên toàn ứng dụng.

- Mọi trang: breadcrumb (nếu có) → tiêu đề trang (h1, 24px, 700) + mô tả ngắn + nhóm hành động chính căn phải (xuống dòng gọn trên mobile) → các card nội dung cách nhau 24px. Lề trang và độ rộng tối đa giống nhau mọi nơi.
- Card: viền 1px, bo 8–12px, đệm 24px, tiêu đề card 18px/600.
- Form/bộ lọc: nhãn luôn hiện phía trên ô (không dùng placeholder thay nhãn), mọi ô cao 44px, bo 8px, viền `--ui-border`; lưới nhiều cột trên desktop, xếp dọc trên mobile; nút gửi cùng hàng, cao 44px, `white-space: nowrap`, có chiều rộng tối thiểu, không bao giờ bị bóp để chữ rớt dòng.
- Bảng: đặt trong card; tiêu đề cột 14px/600 trên nền `--ui-surface-raised`; ô đệm 12px 16px, dòng cao tối thiểu 44px, kẻ ngang `--ui-divider`; hover dòng; cột số và tiền căn phải, `tabular-nums`; cột trạng thái dùng badge (chữ + icon); cột thao tác căn phải, cùng một kiểu nút; độ rộng cột đặt chủ động.
- Trạng thái trống nằm trong chính card của bảng: icon, một câu giải thích, một hành động hợp lệ (nếu có quyền).
- Trang chi tiết: card theo nhóm, dạng nhãn–giá trị 2 cột trên desktop, 1 cột trên mobile.


## Quy tắc số và control thống nhất — phản hồi ngày 12/10/2026

Hiển thị theo Việt Nam: `5.000.000`, `0,07`, số âm `-1.234,5`; số tiền/số lượng căn phải, tabular-nums. Năm/tháng, mã, ID, URL, JSON, thuộc tính máy và giá trị POST không phân nhóm. Ô số hiển thị qua proxy tiếng Việt; native NumberInput giữ tên trường, min/max/step và giá trị chuẩn, không dùng parseFloat cho chuỗi phân nhóm. Không đổi phép tính hay giá trị ô Excel số.

Nút và input/select một dòng cao tối thiểu 44px, bo 8px, chữ 14px, padding theo token; nút không co hẹp, nhóm control có gap 8–12px và wrap trên mobile. Textarea nhiều dòng, checkbox/radio và nội dung giấy HCNS giữ loại control riêng. Bảng rộng cuộn trong vùng bảng, không ép tiêu đề thành từng ký tự. Editor/catalog/card/control dark dùng surface slate và chữ token; bản giấy HCNS giữ nền trắng/chữ đen ở cả hai theme. Dùng “Trung tâm” trong nội dung hiển thị nguồn; không thay dữ liệu nghiệp vụ đã lưu hay sửa lịch sử migration.

## Component opt-in Giai đoạn 4

Quy chuẩn trang được triển khai qua `.ui-page`, `.ui-card`, `.ui-table`, `.ui-field`, `.ui-badge` và các partial dùng chung trên bốn trang mẫu. Các trang khác chưa chuyển layout. Cách dùng, registry trạng thái và kitchen sink xem [tài liệu thành phần](docs/UI_SHARED_COMPONENTS_PHASE4.md). Kết quả kiểm tra/việc còn mở chỉ ghi trong nhật ký dự án.
