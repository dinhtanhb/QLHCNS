# IHRMS — Design system đã duyệt

Trạng thái: đã duyệt bởi chủ dự án ngày 12/10/2026 kèm các điều kiện trong yêu cầu Giai đoạn 2. Nguồn quyết định: UI UX Pro Max, kiểm kê mã IHRMS và các ràng buộc của chủ dự án. Nhật ký duy nhất: [PROJECT_WORK_LOG](../docs/PROJECT_WORK_LOG.md). Thứ bậc: MASTER + tokens > DESIGN.md > mặc định skill. Giai đoạn 2 áp dụng khung; nội dung trang con chưa thiết kế lại.

## Phạm vi và nguồn của skill

Đã chạy mô tả đầy đủ do chủ dự án cung cấp bằng Python hệ thống với `--design-system -p IHRMS`. Kết quả đầu: Enterprise Gateway, OLED, Fira Code/Fira Sans, CTA bán hàng. Truy vấn lại `internal HR enterprise dashboard accessible` cho Accessible & Ethical, hỗ trợ hai theme. Đã chạy `--persist --output-dir D:/QLHCNS`; tool tạo `design-system/ihrms/MASTER.md`. Bản đã rà được chuẩn hóa về đường dẫn yêu cầu `design-system/MASTER.md`; không giữ bản sinh chưa điều chỉnh làm nguồn quy tắc thứ hai.

Chọn Accessible & Ethical kết hợp Data-Dense Dashboard (tìm kiếm KPI). Giữ focus rõ, semantic HTML, responsive, labels, reduced motion. Các phần marketing/Contact Sales/hero/carousel không phù hợp cổng nhân sự đã đăng nhập nên bỏ. Không có stack Django trong skill; không chạy stack React/shadcn và không coi ví dụ Tailwind là yêu cầu thêm framework.

Đã xác nhận `DESIGN.md` bản chủ dự án cập nhật: violet/system sans, card viền và bóng nhẹ, không dùng Neumorphism. Không ghi đè thay đổi cục bộ đó. Hai tài liệu thống nhất với quyết định đã duyệt.

## Hệ màu, typography và tokens

Nguồn giá trị chính thức: [`ui_tokens.css`](../src/static/css/ui_tokens.css), namespace `--ui-*`. Base tải theme JS trước CSS, rồi Tailwind, legacy adapters, theme, tokens, CSS trang con, cuối cùng CSS khung. `design_tokens.css` import tokens để admin cũng dùng được; aliases cũ chỉ trỏ một chiều tới `--ui-*` trong `@media screen`, defaults in giữ nguyên. Không đổi tên utility hàng loạt hoặc recolor giấy HCNS. OS fallback CSS chỉ khi chưa có `data-theme`; theme JS ưu tiên lựa chọn đã lưu, nếu chưa chọn theo `prefers-color-scheme`.

- Một màu thương hiệu tím: light `#6d28d9`, dark `#c4b5fd`. Giữ nhận diện tím hiện có; bỏ navy/blue CTA do skill gợi ý để tránh đổi thương hiệu chưa được yêu cầu. Bỏ gradient và glow, dùng neutral slate cho dữ liệu và surfaces.
- Bốn màu ngữ nghĩa: success xanh lá, warning hổ phách, danger đỏ, info xanh dương; mỗi trạng thái có text/background/border riêng cho hai theme. Trạng thái luôn có chữ và SVG tương ứng. Warning chỉ việc chờ xử lý, danger chỉ lỗi/quá hạn/hành động nguy hiểm.
- Dùng font hệ thống `"Segoe UI", system-ui, -apple-system, Roboto, Arial, sans-serif`; không tải Google Fonts/CDN, không thêm asset/dependency. Cần kiểm tra glyph tiếng Việt ở máy đích; kết quả kiểm tra local ghi trong nhật ký. Bỏ Fira Code cho văn bản thường và Plus Jakarta Sans remote vì không cần font mạng hay phong cách kỹ thuật. Không tuyên bố đã kiểm Be Vietnam Pro/Inter khi chưa có font đó.
- Body 16px (`1rem` với root mặc định), bảng/nhãn 14px, phụ chú 12px; line height 1.5, heading 1.25. Không giảm root font-size; hỗ trợ zoom. Số dùng tabular-nums, tiền `vi-VN`, ngày `dd/MM/yyyy`; giữ quy tắc làm tròn và dữ liệu backend hiện có.
- Khoảng cách 4/8/12/16/24/32/48px; radius 4/8/12px; bóng nhẹ. Control/row min 44px nhưng có thể cao hơn khi chữ xuống dòng. Bỏ row 36px và thân chữ 12px trong đề xuất dashboard để đáp ứng vùng chạm và độ đọc.
- Focus 3px, offset 3px, thêm khoảng nền tương phản quanh nút filled trước ring; hover/active/selected/disabled/error có tokens. Disabled dùng semantics thật, không chỉ đổi màu hay opacity.
- Motion feedback 120ms, panel 180ms, về 0 khi reduced motion. Không thêm GSAP, shimmer liên tục hoặc transition màu khi đổi theme.

## Điều hướng và trang chủ

Desktop từ 1024px: sidebar rộng 256px, thu gọn 72px; nhóm Cá nhân, Nhân sự, Tuyển dụng, Kế toán, Hành chính, Kế hoạch, Báo cáo, Dự án. Trang chủ là link riêng. Active có nền, nét đánh dấu và `aria-current`; trạng thái thu gọn có tên truy cập, tooltip dùng được bằng focus. Header giữ thương hiệu, chuông và tài khoản; vùng nội dung rộng tối đa 1440px.

360–1023px: drawer thay sidebar, nút mở ≥44px. Drawer có nhãn, Escape/đóng, quản lý focus khi là modal, trả focus về nút mở; khóa tab nền chỉ khi modal. Chọn drawer cho tám phân hệ; không dùng bottom bar. Không dùng hover làm cách mở duy nhất; toàn bộ menu dùng bàn phím. Dùng media queries CSS thật ở 360/768/1024/1440px, không dùng CSS variable làm điều kiện breakpoint.

Trang chủ ưu tiên Việc của tôi, Cần duyệt, Thao tác nhanh rồi Hoạt động gần đây; mỗi khu vực chỉ hiển thị khi guard và dữ liệu hiện tại hỗ trợ. Đề xuất mới cần dữ liệu view bổ sung phải thành nhiệm vụ riêng; không bịa số hoặc đổi view ở đợt UI này. KPI có nhãn, giá trị, phạm vi/kỳ và link hợp lệ tới danh sách đã có quyền xem; không biến mọi card thành link nếu chưa có đích. Cảnh báo chưa gắn hồ sơ có SVG và hướng dẫn; nút xử lý cho admin chỉ dùng route/guard hiện có sau xác minh, nhân viên nhận hướng dẫn liên hệ HR.

## Component contracts

- Card/KPI: tiêu đề 14–16px, số 24–32px, căn thống nhất; trạng thái chờ duyệt nhấn bằng chữ/icon, không chỉ màu. Số 0 hợp lệ giữ hiển thị; thiếu dữ liệu dùng “Chưa có dữ liệu”.
- Bảng: caption/heading, `scope`, link thực cho chi tiết; header sticky không che focus. Bộ lọc có labels, nút áp dụng/xóa và số kết quả; giữ GET, URL names, CSRF và field names. Chỉ dùng `aria-sort` khi backend đã hỗ trợ sort. 360px dùng vùng cuộn ngang có nhãn/focus hoặc card với nhãn cột; trang không tràn ngang. Không thêm bulk action/sort mới chỉ vì skill gợi ý.
- Form dài: chia nhóm `fieldset/legend`, một submit chính, errors cạnh field qua `aria-describedby`/`aria-invalid`; error summary có link tới field và nhận focus sau submit lỗi. Giữ dữ liệu đã nhập, CSRF, field name, validation và quyền hiện hành. Không thêm autosave/multi-step nghiệp vụ.
- Badge/alert: SVG outline 24 viewBox, stroke 2, dùng cùng hệ Heroicons-style inline sẵn có; icon trang trí `aria-hidden`, nút icon có accessible name. Sau duyệt chọn một bộ paths nhất quán; chưa thêm thư viện. Alert nguy cấp tồn tại đến khi giải quyết, không auto-dismiss.
- Empty state: phân biệt chưa tạo dữ liệu, bộ lọc không có kết quả, không có quyền và lỗi tải; thông điệp + một hành động hợp lệ. Không hiển thị chart rỗng hoặc thanh 100% cho một phòng ban; một nhóm dùng số/tóm tắt, nhiều nhóm dùng bar ngang và bảng dữ liệu thay thế.
- Toast: thông tin thường `role=status`, không giành focus; 5 giây chỉ cho thông báo không cần hành động, có bản lưu trong thông báo/messages. Pause khi hover/focus. Lỗi và toast có thao tác không tự đóng; ghi đè hướng dẫn auto-dismiss 3–5 giây của skill để không mất thông tin quan trọng.
- Chart: so sánh phòng ban dùng bar, thời gian dùng line, có labels trực tiếp, đơn vị, tóm tắt và bảng dữ liệu. Một hue brand cho cùng đại lượng, không gán mỗi phòng ban một màu. Tooltip phải có đường truy cập bằng bàn phím; không thêm chart library ở đợt này.
- Pagination: dùng partial hiện có; giữ filters/scope, `aria-current`, labels nút trước/sau, mục tiêu 44px. Hành động sửa/duyệt/xóa chỉ xuất hiện theo guard hiện hành; CSS không thay được kiểm tra quyền server.

## Gate trước áp dụng

Đo các cặp màu token được quy định (text ≥4.5:1, control/focus ≥3:1) cho cả hai theme; cặp không nằm trong danh sách đã đo phải đo lại. `--ui-divider` chỉ chia nhóm trang trí, không dùng làm viền control cần nhận biết. Scrim/bóng có alpha phải đo trên nền thực khi render.

Sidebar dùng bộ `--ui-sidebar-{bg,text,hover-bg,active-bg,active-text,marker,border}`; chart dùng `--ui-chart-{series,series-soft,series-strong,axis,grid,label}`. Các thang chart phục vụ cùng đại lượng, không tự phân màu phòng ban. Script `python ops/check_ui_contrast.py` đo lại các cặp đã quy định; bảng đầy đủ ở `docs/UI_DESIGN_SYSTEM_PHASE1.md`.

Kiểm tra 360/768/1024/1440px, zoom 200%, bàn phím, screen reader, reduced motion, tất cả guards/RBAC và print HCNS khi áp dụng Giai đoạn 2. Đo tokens không chứng minh toàn ứng dụng đạt WCAG 2.1 AA. Dừng cuối Giai đoạn 2 để chủ dự án xem giao diện trước giai đoạn kế tiếp.


## Ngoại lệ điều hướng đã được chủ dự án duyệt — Đợt 2b

Sidebar được phép dùng nền thương hiệu nhạt `--ui-sidebar-hover-bg`, chữ `--ui-sidebar-hover-text`, vạch trái 3px `--ui-sidebar-marker`, viền thương hiệu mờ 1px `--ui-sidebar-hover-border` và bóng nhẹ `--ui-shadow-card` khi hover hoặc focus-visible. Viền mờ là trang trí; vạch và chữ cung cấp tín hiệu tương phản. Dùng `--ui-motion-feedback` 120ms, về 0ms khi reduced-motion; không gradient, blur hay glow. Pointer không hiện vòng focus; bàn phím giữ vòng focus-visible rõ. Mục con chỉ có chữ thụt vào, đường nối dọc mảnh, active đậm và `aria-current="page"`; nhóm chỉ giữ chevron bên phải.

Nền trang/card/control và track biểu đồ dùng slate; KPI mặc định `--ui-text`, cảnh báo chỉ khi giá trị > 0 và có nhãn. Biểu đồ bốn chuỗi dùng `--ui-chart-hire/departure/transfer/promotion`, chú giải chữ và bảng số liệu; giá trị 0 không vẽ thanh. Tím chỉ dùng cho hành động chính, link, selected/active, focus và dữ liệu chính; ngoại lệ hover sidebar nêu trên. Biểu mẫu HCNS giữ palette giấy/in đã có. Kết quả đo và giới hạn xác minh: [nhật ký dự án](../docs/PROJECT_WORK_LOG.md).

## Mẫu bố cục trang chuẩn — triển khai ở Giai đoạn 4

Đây là quy chuẩn chuẩn bị; đợt 2b chưa áp dụng bố cục này trên toàn ứng dụng.

- Mọi trang: breadcrumb (nếu có) → tiêu đề trang (h1, 24px, 700) + mô tả ngắn + nhóm hành động chính căn phải (xuống dòng gọn trên mobile) → các card nội dung cách nhau 24px. Lề trang và độ rộng tối đa giống nhau mọi nơi.
- Card: viền 1px, bo 8–12px, đệm 24px, tiêu đề card 18px/600.
- Form/bộ lọc: nhãn luôn hiện phía trên ô (không dùng placeholder thay nhãn), mọi ô cao 44px, bo 8px, viền `--ui-border`; lưới nhiều cột trên desktop, xếp dọc trên mobile; nút gửi cùng hàng, cao 44px, `white-space: nowrap`, có chiều rộng tối thiểu, không bao giờ bị bóp để chữ rớt dòng.
- Bảng: đặt trong card; tiêu đề cột 14px/600 trên nền `--ui-surface-raised`; ô đệm 12px 16px, dòng cao tối thiểu 44px, kẻ ngang `--ui-divider`; hover dòng; cột số và tiền căn phải, `tabular-nums`; cột trạng thái dùng badge (chữ + icon); cột thao tác căn phải, cùng một kiểu nút; độ rộng cột đặt chủ động.
- Trạng thái trống nằm trong chính card của bảng: icon, một câu giải thích, một hành động hợp lệ (nếu có quyền).
- Trang chi tiết: card theo nhóm, dạng nhãn–giá trị 2 cột trên desktop, 1 cột trên mobile.
