# IHRMS — Design system đề xuất, Giai đoạn 1

Trạng thái: chờ chủ dự án duyệt trước Giai đoạn 2. Chỉ tài liệu và CSS variables; chưa áp dụng vào template. Nguồn quyết định: UI UX Pro Max, kiểm kê mã IHRMS và các ràng buộc của chủ dự án. Nhật ký duy nhất: [PROJECT_WORK_LOG](../docs/PROJECT_WORK_LOG.md).

## Phạm vi và nguồn của skill

Đã chạy mô tả đầy đủ do chủ dự án cung cấp bằng Python hệ thống với `--design-system -p IHRMS`. Kết quả đầu: Enterprise Gateway, OLED, Fira Code/Fira Sans, CTA bán hàng. Truy vấn lại `internal HR enterprise dashboard accessible` cho Accessible & Ethical, hỗ trợ hai theme. Đã chạy `--persist --output-dir D:/QLHCNS`; tool tạo `design-system/ihrms/MASTER.md`. Bản đã rà được chuẩn hóa về đường dẫn yêu cầu `design-system/MASTER.md`; không giữ bản sinh chưa điều chỉnh làm nguồn quy tắc thứ hai.

Chọn Accessible & Ethical kết hợp Data-Dense Dashboard (tìm kiếm KPI). Giữ focus rõ, semantic HTML, responsive, labels, reduced motion. Các phần marketing/Contact Sales/hero/carousel không phù hợp cổng nhân sự đã đăng nhập nên bỏ. Không có stack Django trong skill; không chạy stack React/shadcn và không coi ví dụ Tailwind là yêu cầu thêm framework.

`DESIGN.md` hiện định hướng violet/system sans/neumorphism. Đề xuất này giữ violet và system sans, giảm bóng nổi/inset thành card border và bóng nhẹ để đọc bảng dày rõ hơn. Đây là thay đổi thiết kế chờ duyệt, chưa thay thế quy tắc runtime trong `DESIGN.md`; khi chủ dự án duyệt Giai đoạn 2 cần thống nhất hai tài liệu trước áp dụng.

## Hệ màu, typography và tokens

Nguồn giá trị để triển khai sau duyệt: [`ui_tokens_proposed.css`](../src/static/css/ui_tokens_proposed.css), namespace `--ui-*`. Không import bộ này trong Giai đoạn 1. Giữ nguyên `design_tokens.css`, `theme.css`, theme JS và utilities đang chạy. Khi áp dụng, cần quyết định thứ tự stylesheet và chuyển từng component, không thay hàng loạt aliases Tailwind/admin hoặc recolor biểu mẫu in.

- Một màu thương hiệu tím: light `#6d28d9`, dark `#c4b5fd`. Giữ nhận diện tím hiện có; bỏ navy/blue CTA do skill gợi ý để tránh đổi thương hiệu chưa được yêu cầu. Bỏ gradient và glow, dùng neutral slate cho dữ liệu và surfaces.
- Bốn màu ngữ nghĩa: success xanh lá, warning hổ phách, danger đỏ, info xanh dương; mỗi trạng thái có text/background/border riêng cho hai theme. Trạng thái luôn có chữ và SVG tương ứng. Warning chỉ việc chờ xử lý, danger chỉ lỗi/quá hạn/hành động nguy hiểm.
- Dùng font hệ thống `Segoe UI`, Arial, sans-serif; không tải Google Fonts/CDN, không thêm asset/dependency. Cần kiểm tra glyph tiếng Việt ở máy đích; kết quả kiểm tra local ghi trong nhật ký. Bỏ Fira Code cho văn bản thường và Plus Jakarta Sans remote vì không cần font mạng hay phong cách kỹ thuật. Không tuyên bố đã kiểm Be Vietnam Pro/Inter khi chưa có font đó.
- Body 16px (`1rem` với root mặc định), bảng/nhãn 14px, phụ chú 12px; line height 1.5, heading 1.25. Không giảm root font-size; hỗ trợ zoom. Số dùng tabular-nums, tiền `vi-VN`, ngày `dd/MM/yyyy`; giữ quy tắc làm tròn và dữ liệu backend hiện có.
- Khoảng cách 4/8/12/16/24/32/48px; radius 4/8/12px; bóng nhẹ. Control/row min 44px nhưng có thể cao hơn khi chữ xuống dòng. Bỏ row 36px và thân chữ 12px trong đề xuất dashboard để đáp ứng vùng chạm và độ đọc.
- Focus 3px, offset 3px, thêm khoảng nền tương phản quanh nút filled trước ring; hover/active/selected/disabled/error có tokens. Disabled dùng semantics thật, không chỉ đổi màu hay opacity.
- Motion feedback 120ms, panel 180ms, về 0 khi reduced motion. Không thêm GSAP, shimmer liên tục hoặc transition màu khi đổi theme.

## Điều hướng và trang chủ

Desktop từ 1024px: sidebar rộng 256px, thu gọn 72px; nhóm Cá nhân, Nhân sự, Tuyển dụng, Kế toán, Hành chính, Kế hoạch, Báo cáo, Dự án. Trang chủ là link riêng. Active có nền, nét đánh dấu và `aria-current`; trạng thái thu gọn có tên truy cập, tooltip dùng được bằng focus. Header giữ thương hiệu, chuông và tài khoản; vùng nội dung rộng tối đa 1440px.

360–1023px: drawer thay sidebar, nút mở ≥44px. Drawer có nhãn, Escape/đóng, quản lý focus khi là modal, trả focus về nút mở; khóa tab nền chỉ khi modal. Chọn drawer cho tám phân hệ; chưa thêm bottom bar để tránh chia menu quá nhiều. Không dùng hover làm cách mở duy nhất; toàn bộ menu dùng bàn phím. Dùng media queries CSS thật ở 360/768/1024/1440px, không dùng CSS variable làm điều kiện breakpoint.

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

Kiểm tra 360/768/1024/1440px, zoom 200%, bàn phím, screen reader, reduced motion, tất cả guards/RBAC và print HCNS khi áp dụng Giai đoạn 2. Đo tokens không chứng minh toàn ứng dụng đạt WCAG 2.1 AA. Cần chủ dự án duyệt MASTER và tokens trước khi đổi base layout/template.
