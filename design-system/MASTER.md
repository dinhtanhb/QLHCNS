# IHRMS — Design system đã duyệt

## Trang chủ và bảng số liệu — chuẩn thay thế ngày 15/10/2026

Dashboard/Định biên dùng thang opt-in h1/h2/nhãn/KPI/số vừa:24/32,18/28,14/20,32/40,24/32; trọng lượng600 cho tiêu đề/số,500 cho nhãn/link. Số công việc28/32. Nền trang và thẻ là hai mặt phẳng; thẻ viền subtle, không bóng, đệm ngang20/dọc16–20px, gap thẻ16px/nhóm32px. Không dùng trần chiều cao để ép toàn trang; các quy định mật độ/chiều cao cũ bên dưới không còn áp dụng cho hai trang này. Thứ tự nhóm và tỷ lệ60/40 giữ nguyên; màn hình đầu1440×900 ưu tiên header/KPI/công việc/Dự án khi được cấp quyền. Giám đốc gọn bằng số dòng, không nén chữ/đệm.

### Bảng số liệu & báo cáo

Tiêu đề24/32 và mô tả muted; bộ lọc cùng số kết quả nằm trong thẻ kết quả có viền/bo/đệm20px. Nhãn Năm cách control8px, không dự trữ hai dòng cho bộ lọc một nhãn. Nút áp dụng/xóa liền sau control. Bảng chỉ kẻ ngang nhạt; tiêu đề muted14/500, cột số và tiêu đề số căn phải/tabular; hàng tối thiểu44px. Chênh lệch giữ số gốc cho máy/in và diễn giải bằng “Vượt/Thiếu/Đủ”; cảnh báo kèm icon/chữ/nền nhẹ. Vùng bảng hẹp có nhãn, focus và hướng dẫn cuộn ngang. CSS màn hình không thay giấy in. Chuẩn mới chỉ triển khai tại report_headcount trong đợt này; các báo cáo khác chưa chuyển.

## Trang chủ gọn — 15/10/2026

Thứ tự: KPI chính → Công việc của tôi → Dự án → Nhân sự → Hành chính → Tuyển dụng. Quy chuẩn này thay thứ tự/cách dựng thẻ ở các mục cũ; quyền và nguồn dữ liệu giữ nguyên, khối ngoài quyền không dựng trong HTML. Dự án giữ5 số kể cả0 theo guard hiện hữu; Giao công việc ở header Dự án. Không thêm số liệu để lấp ô hoặc thêm selector tuần chưa được duyệt.

Một h1, h2 theo nhóm, h3 theo thẻ; KPI không dùng heading. KPI100px/trần104; hai ô công việc72px desktop, giữ đủ nút nghỉ phép/công việc. **Cặp nội dung60/40 theo lời nhắn mới nhất, kể cả Công việc của tôi**, một cột khi thiếu chỗ. Không áp tỷ lệ lên form; lưới form theo container 4/3/2/1 cột giữ riêng, span 12 cũ chỉ để tương thích. Header/nội dung sát nhau, một mức thẻ; biểu tượng20–24px, thông tin bằng details icon có vùng44px, body nổi không đẩy nội dung và hỗ trợ Enter/Escape/blur. Không có dòng Cách tính cuối thẻ. Nút chính44px; link nội tuyến trong hàng dữ liệu giữ ngoại lệ inline, không chồng hit area lên hàng khác.

Nhân sự: Định biên/Donut60/40, Hợp đồng/Quyết định60/40. Giám đốc chỉ ghép Định biên/Quyết định theo quyền, vẫn ẩn hợp đồng Q3. Donut loại hợp đồng phải giữ ở bản gọn144px, vành≈22px, số thứ tự trong từng cung, tổng giữa, chú giải số/% và bảng SR. Một nhóm không vẽ donut. Thanh định biên duy nhất từng phòng: thực tế, vạch kế hoạch, chỉ phần vượt dùng cảnh báo kèm nhãn; tối đa6/4 phòng theo độ lệch. Đơn nghỉ xem nhanh3/2 dòng và giữ phần còn lại ở thông tin; hợp đồng3 dòng; quyết định≤5/3. Badge một dòng≤28px, icon cạnh chữ. Các preview không đổi số tổng; liên kết tới danh sách giữ đúng phạm vi hỗ trợ hiện có.

Hàng chờ trống chỉ một thanh≤40px. Tuyển dụng gộp vùng mỏng, giữ số0 được cấp và nhãn Đã đóng. Chip vào làm ở header nếu chưa ở KPI; không thẻ số riêng trùng nghĩa. Dùng--ui-dash-* cho mật độ và--ui-* cho màu/spacing; CSS giới hạn màn hình Dashboard, giữ giấy in độc lập. Ngân sách1440×900: HR≤1260px (Nhân sự≤520), Giám đốc≤990, nhân viên≤900; KPI/My work/Dự án được cấp và tiêu đề Nhân sự phải có trong màn hình đầu. Ảnh trước/sau, số đo, kết quả kiểm tra và giới hạn ở [PROJECT_WORK_LOG](../docs/PROJECT_WORK_LOG.md).

Trạng thái: đã duyệt bởi chủ dự án ngày 12/10/2026 kèm các điều kiện trong yêu cầu Giai đoạn 2. Nguồn quyết định: UI UX Pro Max, kiểm kê mã IHRMS và các ràng buộc của chủ dự án. Nhật ký duy nhất: [PROJECT_WORK_LOG](../docs/PROJECT_WORK_LOG.md). Thứ bậc: MASTER + tokens > DESIGN.md > mặc định skill. Giai đoạn 2 áp dụng khung; nội dung trang con chưa thiết kế lại.

## Phạm vi và nguồn của skill

Đã chạy mô tả đầy đủ do chủ dự án cung cấp bằng Python hệ thống với `--design-system -p IHRMS`. Kết quả đầu: Enterprise Gateway, OLED, Fira Code/Fira Sans, CTA bán hàng. Truy vấn lại `internal HR enterprise dashboard accessible` cho Accessible & Ethical, hỗ trợ hai theme. Đã chạy `--persist --output-dir D:/QLHCNS`; tool tạo `design-system/ihrms/MASTER.md`. Bản đã rà được chuẩn hóa về đường dẫn yêu cầu `design-system/MASTER.md`; không giữ bản sinh chưa điều chỉnh làm nguồn quy tắc thứ hai.

Chọn Accessible & Ethical kết hợp Data-Dense Dashboard (tìm kiếm KPI). Giữ focus rõ, semantic HTML, responsive, labels, reduced motion. Các phần marketing/Contact Sales/hero/carousel không phù hợp cổng nhân sự đã đăng nhập nên bỏ. Không có stack Django trong skill; không chạy stack React/shadcn và không coi ví dụ Tailwind là yêu cầu thêm framework.

Đã xác nhận `DESIGN.md` và tokens hiện hành dùng navy–teal theo quyết định Atoms ngày 12/10/2026: font hệ thống, card có viền và bóng nhẹ, không dùng Neumorphism. Chủ dự án xác nhận giữ palette này trong Đợt 1 ngày 13/10/2026; không đổi màu thương hiệu. Điều chỉnh được chủ dự án yêu cầu ngày 13/10/2026: sidebar đổi sáng/tối cùng theme, light dùng nền trung tính sáng và dark dùng navy.

## Hệ màu, typography và tokens

Nguồn giá trị chính thức: [`ui_tokens.css`](../src/static/css/ui_tokens.css), namespace `--ui-*`. Base tải theme JS trước CSS, rồi Tailwind, legacy adapters, theme, tokens, CSS trang con, cuối cùng CSS khung. `design_tokens.css` import tokens để admin cũng dùng được; aliases cũ chỉ trỏ một chiều tới `--ui-*` trong `@media screen`, defaults in giữ nguyên. Không đổi tên utility hàng loạt hoặc recolor giấy HCNS. OS fallback CSS chỉ khi chưa có `data-theme`; theme JS ưu tiên lựa chọn đã lưu, nếu chưa chọn theo `prefers-color-scheme`.

- Theo yêu cầu tham khảo Atoms ngày12/10/2026, chuyển màu thương hiệu sang teal: light `#0b7461`, dark `#63dbc2`; sidebar light `#f0f5f2` / chữ navy `#0c233b`, sidebar dark navy `#0c233b`, nền light `#f4f7f5`, dark `#0e1827`. Giữ bốn màu ngữ nghĩa và không gradient/glow. Viền card `--ui-card-border` nhẹ, tách viền control `--ui-border` đủ3:1; sidebar có `--ui-sidebar-focus` riêng. Quyết định này thay palette tím trước đó theo ủy quyền mới của chủ dự án.
- Bốn màu ngữ nghĩa: success xanh lá, warning hổ phách, danger đỏ, info xanh dương; mỗi trạng thái có text/background/border riêng cho hai theme. Trạng thái luôn có chữ và SVG tương ứng. Warning chỉ việc chờ xử lý, danger chỉ lỗi/quá hạn/hành động nguy hiểm.
- Dùng font hệ thống `"Segoe UI", system-ui, -apple-system, Roboto, Arial, sans-serif`; không tải Google Fonts/CDN, không thêm asset/dependency. Cần kiểm tra glyph tiếng Việt ở máy đích; kết quả kiểm tra local ghi trong nhật ký. Bỏ Fira Code cho văn bản thường và Plus Jakarta Sans remote vì không cần font mạng hay phong cách kỹ thuật. Không tuyên bố đã kiểm Be Vietnam Pro/Inter khi chưa có font đó.
- Body 16px (`1rem` với root mặc định), bảng/nhãn 14px, phụ chú 12px; line height 1.5, heading 1.25. Không giảm root font-size; hỗ trợ zoom. Số dùng tabular-nums, tiền `vi-VN`, ngày `dd/MM/yyyy`; giữ quy tắc làm tròn và dữ liệu backend hiện có.
- Khoảng cách 4/8/12/16/24/32/48px; radius 4/8/12px theo vai trò; control 8px, card phẳng không bóng. Control/row min 44px nhưng có thể cao hơn khi chữ xuống dòng. Bỏ row 36px và thân chữ 12px trong đề xuất dashboard để đáp ứng vùng chạm và độ đọc.
- Focus 3px, offset 3px, thêm khoảng nền tương phản quanh nút filled trước ring; hover/active/selected/disabled/error có tokens. Disabled dùng semantics thật, không chỉ đổi màu hay opacity.
- Motion feedback 120ms, panel 180ms, về 0 khi reduced motion. Không thêm GSAP, shimmer liên tục hoặc transition màu khi đổi theme.

## Điều hướng và trang chủ

Desktop từ 1024px: sidebar rộng 256px, thu gọn 72px; nhóm Cá nhân, Nhân sự, Tuyển dụng, Kế toán, Hành chính, Kế hoạch, Báo cáo, Dự án. Trang chủ là link riêng. Active có nền, nét đánh dấu và `aria-current`; trạng thái thu gọn có tên truy cập, tooltip dùng được bằng focus. Header giữ thương hiệu, chuông và tài khoản; vùng nội dung rộng tối đa 1440px.

360–1023px: drawer thay sidebar, nút mở ≥44px. Drawer có nhãn, Escape/đóng, quản lý focus khi là modal, trả focus về nút mở; khóa tab nền chỉ khi modal. Chọn drawer cho tám phân hệ; không dùng bottom bar. Không dùng hover làm cách mở duy nhất; toàn bộ menu dùng bàn phím. Dùng media queries CSS thật ở 360/768/1024/1440px, không dùng CSS variable làm điều kiện breakpoint.

Trang chủ ưu tiên Việc của tôi, Cần duyệt, Thao tác nhanh rồi Hoạt động gần đây; mỗi khu vực chỉ hiển thị khi guard và dữ liệu hiện tại hỗ trợ. Đề xuất mới cần dữ liệu view bổ sung phải thành nhiệm vụ riêng; không bịa số hoặc đổi view ở đợt UI này. KPI có nhãn, giá trị, phạm vi/kỳ và link hợp lệ tới danh sách đã có quyền xem; không biến mọi card thành link nếu chưa có đích. Cảnh báo chưa gắn hồ sơ có SVG và hướng dẫn; nút xử lý cho admin chỉ dùng route/guard hiện có sau xác minh, nhân viên nhận hướng dẫn liên hệ HR.

## Component contracts

- Card/KPI: tiêu đề 14–16px, số 24–32px, căn thống nhất; trạng thái chờ duyệt nhấn bằng chữ/icon, không chỉ màu. Số 0 hợp lệ giữ hiển thị; thiếu dữ liệu dùng “Chưa có dữ liệu”.
- Bảng: caption/heading, `scope`, link thực cho chi tiết; header sticky không che focus. Bộ lọc dùng mẫu “Dải lọc với thao tác liền kề” dưới đây; giữ GET, URL names, CSRF và field names. Chỉ dùng `aria-sort` khi backend đã hỗ trợ sort. 360px dùng vùng cuộn ngang có nhãn/focus hoặc card với nhãn cột; trang không tràn ngang. Không thêm bulk action/sort mới chỉ vì skill gợi ý.
- Form dài: chia nhóm `fieldset/legend`, một submit chính, errors cạnh field qua `aria-describedby`/`aria-invalid`; error summary có link tới field và nhận focus sau submit lỗi. Giữ dữ liệu đã nhập, CSRF, field name, validation và quyền hiện hành. Không thêm autosave/multi-step nghiệp vụ.
- Badge/alert: SVG outline 24 viewBox, stroke 2, dùng cùng hệ Heroicons-style inline sẵn có; icon trang trí `aria-hidden`, nút icon có accessible name. Sau duyệt chọn một bộ paths nhất quán; chưa thêm thư viện. Alert nguy cấp tồn tại đến khi giải quyết, không auto-dismiss.
- Empty state: phân biệt chưa tạo dữ liệu, bộ lọc không có kết quả, không có quyền và lỗi tải; thông điệp + một hành động hợp lệ. Không hiển thị chart rỗng hoặc thanh 100% cho một phòng ban; một nhóm dùng số/tóm tắt, nhiều nhóm dùng bar ngang và bảng dữ liệu thay thế.

### Dải lọc với thao tác liền kề — ngày 13/10/2026

Mẫu: `[Tìm kiếm] [Lọc phụ…] [Áp dụng] [Xóa lọc]`, khoảng trống dư nằm sau nút. Form GET có aria-label, role=search khi tìm kiếm, nằm trong vùng đầu thẻ kết quả chung, không có thẻ lọc hoặc h2 lọc riêng. Trường dùng partial `ui/field.html`, thao tác dùng `ui/query_actions.html`; CSS duy nhất ở `shared_components.css`. Ô văn bản basis16rem/max24rem, select13rem, ngày/tháng/năm/số10rem; gap12px/16px. Nút44px căn đáy ô nhập, nhãn/nút≥14px, focus3px. Không margin-left:auto/justify-content:flex-end để đẩy thao tác ra xa.

Chỉ hiện Xóa lọc khi ít nhất một tham số lọc khai báo khác rỗng; bỏ page, giữ scope metric/ngày của drill-down và group catalog. Nút chính luôn Áp dụng và đứng trước liên kết Xóa lọc. Số kết quả dùng tổng paginator hoặc độ dài tập dữ liệu đã có, aria-live=polite, ngay dưới form trong card; không tạo số tổng giả cho báo cáo nhiều nguồn hay lặp hoạt động theo ngày.

≥1024px flex một hàng nếu đủ, wrap khi thiếu;600–1023px trường hai cột/nút dưới căn trái; <600px mỗi trường toàn hàng, hai nút cùng hàng và chia rộng đều. Tab theo trường→Áp dụng→Xóa lọc; Enter gửi native GET, không onchange tự gửi. Chỉ vùng lọc ẩn khi in, giữ thẻ kết quả;60/40 chỉ cho các khối nội dung khác. Ảnh trước/sau và số đo xem metadata/ảnh của đợt trong PROJECT_WORK_LOG, không lưu dữ liệu giả hoặc ảnh tài khoản thật vào Git.
- Toast: thông tin thường `role=status`, không giành focus; 5 giây chỉ cho thông báo không cần hành động, có bản lưu trong thông báo/messages. Pause khi hover/focus. Lỗi và toast có thao tác không tự đóng; ghi đè hướng dẫn auto-dismiss 3–5 giây của skill để không mất thông tin quan trọng.
- Chart: so sánh phòng ban dùng bar, thời gian dùng line, có labels trực tiếp, đơn vị, tóm tắt và bảng dữ liệu. Một hue brand cho cùng đại lượng, không gán mỗi phòng ban một màu. Tooltip phải có đường truy cập bằng bàn phím; không thêm chart library ở đợt này.
- Pagination: dùng partial hiện có; giữ filters/scope, `aria-current`, labels nút trước/sau, mục tiêu 44px. Hành động sửa/duyệt/xóa chỉ xuất hiện theo guard hiện hành; CSS không thay được kiểm tra quyền server.

## Gate trước áp dụng

Đo các cặp màu token được quy định (text ≥4.5:1, control/focus ≥3:1) cho cả hai theme; cặp không nằm trong danh sách đã đo phải đo lại. `--ui-divider` chỉ chia nhóm trang trí, không dùng làm viền control cần nhận biết. Scrim/bóng có alpha phải đo trên nền thực khi render.

Sidebar dùng bộ `--ui-sidebar-{bg,text,hover-bg,active-bg,active-text,marker,border}`; chart dùng `--ui-chart-{series,series-soft,series-strong,axis,grid,label}`. Các thang chart phục vụ cùng đại lượng, không tự phân màu phòng ban. Script `python ops/check_ui_contrast.py` đo lại các cặp đã quy định; bảng đầy đủ ở `docs/UI_DESIGN_SYSTEM_PHASE1.md`.

Kiểm tra 360/768/1024/1440px, zoom 200%, bàn phím, screen reader, reduced motion, tất cả guards/RBAC và print HCNS khi áp dụng Giai đoạn 2. Đo tokens không chứng minh toàn ứng dụng đạt WCAG 2.1 AA. Dừng cuối Giai đoạn 2 để chủ dự án xem giao diện trước giai đoạn kế tiếp.


## Ngoại lệ điều hướng đã được chủ dự án duyệt — Đợt 2b

Sidebar được phép dùng nền thương hiệu nhạt `--ui-sidebar-hover-bg`, chữ `--ui-sidebar-hover-text`, vạch trái 3px `--ui-sidebar-marker`, viền thương hiệu mờ 1px `--ui-sidebar-hover-border` và bóng nhẹ `--ui-shadow-card` khi hover hoặc focus-visible. Viền mờ là trang trí; vạch và chữ cung cấp tín hiệu tương phản. Dùng `--ui-motion-feedback` 120ms, về 0ms khi reduced-motion; không gradient, blur hay glow. Pointer không hiện vòng focus; bàn phím giữ vòng focus-visible rõ. Mục con chỉ có chữ thụt vào, đường nối dọc mảnh, active đậm và `aria-current="page"`; nhóm chỉ giữ chevron bên phải.

Nền trang/card/control và track biểu đồ dùng neutral xanh theo palette Atoms; KPI mặc định `--ui-text`, cảnh báo chỉ khi giá trị > 0 và có nhãn. Biểu đồ bốn chuỗi dùng `--ui-chart-hire/departure/transfer/promotion`, chú giải chữ và bảng số liệu; giá trị 0 không vẽ thanh. Teal chỉ dùng cho hành động chính, link, selected/active, focus và dữ liệu chính; ngoại lệ hover sidebar nêu trên. Biểu mẫu HCNS giữ palette giấy/in đã có. Kết quả đo và giới hạn xác minh: [nhật ký dự án](../docs/PROJECT_WORK_LOG.md).

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

Nút và input/select một dòng cao tối thiểu 44px, bo 8px, chữ 14px, padding theo token; nút không co hẹp, nhóm control có gap 8–12px và wrap trên mobile. Textarea nhiều dòng, checkbox/radio và nội dung giấy HCNS giữ loại control riêng. Bảng rộng cuộn trong vùng bảng, không ép tiêu đề thành từng ký tự. Editor/catalog/card/control dark dùng surface token và chữ token; bản giấy HCNS giữ nền trắng/chữ đen ở cả hai theme. Dùng “Trung tâm” trong nội dung hiển thị nguồn; không thay dữ liệu nghiệp vụ đã lưu hay sửa lịch sử migration.

## Component opt-in Giai đoạn 4

Quy chuẩn trang được triển khai qua `.ui-page`, `.ui-card`, `.ui-table`, `.ui-field`, `.ui-badge` và các partial dùng chung trên bốn trang mẫu. Các trang khác chưa chuyển layout. Cách dùng, registry trạng thái và kitchen sink xem [tài liệu thành phần](../docs/UI_SHARED_COMPONENTS_PHASE4.md). Kết quả kiểm tra/việc còn mở chỉ ghi trong nhật ký dự án.

## Bố cục tham khảo Atoms — cập nhật ngày12/10/2026

Phạm vi được chủ dự án chọn: khung chung, trang chủ và các trang đã hoàn tất G5 (Cá nhân/Nhân sự/Tuyển dụng/Kế toán). Tám ảnh trong design-system/reference/atoms chỉ là tham khảo. Giữ branding/dữ liệu IHRMS, không đưa người/tên/số liệu trong ảnh vào demo.

Card có header ngăn bằng divider, bảng dùng hàng đọc được14px, hồ sơ có avatar chữ trang trí; KPI có icon và phạm vi số liệu. Bảng ứng viên theo giai đoạn chỉ nhóm các row của trang hiện tại theo registry trạng thái sẵn, có mô tả rõ phạm vi; giữ bảng danh sách, URL chi tiết và phân trang. Không thêm rating, kéo thả, chuyển trạng thái, tìm kiếm toàn cục, quỹ lương hay KPI không có context. Chữ body16px và control44px giữ nguyên. Card/connector viền nhẹ không được thay viền control hoặc focus.

`atoms_ui.css` chỉ screen, opt-in `.ui-page`; palette/shell dùng chung cho portal. Giấy/Excel HCNS không recolor. Đo lại bằng check_ui_contrast.py và browser thật ở hai theme; nhật ký là nơi duy nhất ghi kết quả triển khai.


### Cập nhật 14/10/2026 — Bộ lọc gắn kết quả và khối xử lý

Mẫu chuẩn: tiêu đề → dải trường và Áp dụng/Xóa lọc liền kề → số kết quả → bảng/lịch/báo cáo → phân trang, trong cùng `ui-results-card`. `ui-query-card` là vùng con `no-print`, không còn là thẻ độc lập; không ẩn toàn thẻ kết quả khi in. Chỉ một tiêu đề trực quan cho mỗi thẻ; caption bảng giữ tên truy cập bằng `ui-visually-hidden`. Nhân viên: số kết quả và ghi chú có hợp đồng/liên kết tạo hợp đồng cùng vùng metadata, tự xuống dòng khi hẹp. Báo cáo nhiều nguồn/danh mục giữ các panel con và tỷ lệ 60/40; phần chọn kỳ/hồ sơ nằm đầu vùng kết quả chung. Kích thước và hành vi dải trường giữ quy chuẩn liền kề đã chốt.

Quyết định: tiêu đề/trạng thái và tiện ích phụ → một panel Xử lý quyết định → giấy xem trước → lịch sử. Trình duyệt/Duyệt/Ghi nhận ban hành là thao tác chính theo quyền/trạng thái; Hủy/Từ chối thu gọn, mở lý do và nút xác nhận/Đóng ngay trong panel. Đóng giữ nội dung nháp trong DOM, trả focus về summary; form POST độc lập giữ CSRF và xác nhận. Khi backend từ chối dữ liệu, giữ tối đa 2000 ký tự ghi chú trong session người dùng cho đúng quyết định, lấy ra một lần ở trang đích; không lưu vào localStorage. File cần chọn lại sau lỗi; không đổi guard, trạng thái hay URL. Mọi quy tắc mới chỉ cho màn hình, panel xử lý không in.

CSS/JS thay đổi phải có URL phiên bản mới, kể cả stylesheet nạp sau đã bỏ override; tăng phiên bản cache service worker cùng đợt. Cổng kiểm thử gồm phiên cache cũ → reload thường, không yêu cầu xóa dữ liệu trình duyệt; ảnh và đo khoảng cách, cùng hồi quy PDF và luồng nghiệp vụ trên dữ liệu giả. Chi tiết thực thi/kết quả nằm duy nhất trong [nhật ký dự án](../docs/PROJECT_WORK_LOG.md).

## Hành chính

- Trang công văn, tài sản, kiểm kê, thanh lý, đặt phòng/xe, VPP và mua sắm dùng `portal/administration_base.html`, page header/field/table/badge/empty state chung. `administration_ui.css` chỉ áp dụng màn hình, dùng token và chia 60/40 cho hai vùng nội dung.
- Bảng nhiều cột nằm trong vùng `ui-scroll` có nhãn và tabindex; caption hỗ trợ đọc màn hình, th có scope, tên/mã giữ liên kết thật. Trang không tràn ở390px, bảng cuộn ngang khi cần. Nhãn luôn hiện và input/nút tối thiểu 44px, chữ 14px; không giảm font để ép cột.
- Công văn giữ nguyên số hiệu, tệp, ngày và quyền; dùng lại dải lọc hiện có với nút ngay sau trường. Không thêm lọc/phân trang/truy vấn hoặc mở quyền xuất báo cáo trong đợt UI.
- Trạng thái dùng ui_badge và nhãn chữ. Hủy/từ chối/thanh lý dùng dialog xác nhận chung; từng form POST/CSRF, submitter decision và điều kiện hiển thị theo quyền giữ nguyên. Chi tiết và lịch sử không che thông tin; hàng động mua sắm có nhãn và ID riêng.
- Template giấy/HCNS và khổ in không đổi. Khi sửa template hành chính chạy lại37 PDF hồi quy+BCC và xem ảnh/số đo; không suy từ HTTP200 hoặc CSS màn hình rằng bản in đúng. Các template sổ công văn cũ chưa có route được ghi nhận, không tự thêm URL/nghiệp vụ.

## Kế hoạch — lịch, đào tạo và bảng nhập KPI

- Lịch công tác giữ thành phần Hành chính; ngày lễ có nhãn chữ/ngày theo ui_date, không chỉ phân biệt bằng màu. Đào tạo dùng trạng thái ui_badge và thông báo rõ tài khoản chưa gắn hồ sơ; portal hiện chỉ đọc danh sách đã đăng ký.
- Form giao KPI dùng nhãn thường trực, error_summary và lưới form 12 cột; tỷ lệ 60/40 chỉ dành cho hai vùng nội dung của trang. Màn hình hẹp xếp theo thứ tự đọc. Không đổi người được giao, tên chỉ tiêu, kỳ, trọng số hoặc công thức.
- Bảng chấm KPI có caption, scope, vùng cuộn được focus; cột số ui-number căn phải và chữ số tabular. Mỗi ô thực tế có ID riêng và tên nhân viên/tiêu chí; 0 là số hợp lệ, năm trong kỳ giữ nguyên 2026.
- Dải lọc kỳ giữ ui-query-card/ui-query-bar/query_actions, nút ngay sau trường, Áp dụng/Enter, Xóa lọc khi có lọc và số kết quả. Không thêm lọc/sắp xếp/phân trang. Nút tối thiểu 44px, chữ 14px, sáng/tối và reduced-motion theo token hiện có.
- Không thêm route đăng ký đào tạo hoặc sửa giấy in. Khi cập nhật asset, tăng URL/cache và chạy hồi quy PDF chung/BCC trên nguồn cuối.

## Lưới form — quy chuẩn ngày 14/10/2026

`shared_components.css` là nguồn duy nhất khai báo cột cho `.ui-form-grid`: 12 cột bằng nhau, gap `--ui-space-4`, căn đỉnh. Tỷ lệ 60/40 chỉ dùng cho hai vùng nội dung của trang (`ui-layout-split`), không áp lên trường hoặc form. Không dùng `!important` hay `:has()` để suy đoán số cột.

Dùng `ui/field.html`: span 3 cho mã/ngày/tháng/số; 4 cho tên, họ, điện thoại, email và select thông thường; 6 cho họ tên đầy đủ hoặc trường dài; 12 cho địa chỉ, ghi chú, lý do, mô tả, chọn nhiều. Mặc định date/month/number là 3, text/email/tel/select là 4, textarea là 12; gán span rõ khi cần. Theo quyết định chủ dự án, được tăng span để hàng đầy 12 và giữ thứ tự Tab/DOM; không đổi tên, required, giá trị, lựa chọn hay CSRF. Tablet 768–1023px: trường ngắn/vừa/dài chiếm 6 cột, trường cuối lẻ có thể dùng `tablet_span="12"`; dưới 768px tất cả chiếm 12 cột. Form nhập nhiều dòng giữ cấu trúc bảng.

Form dài chia `fieldset.ui-form-section` với legend 14px đậm, đường phân cách nhẹ, khoảng nhóm 24px. Hồ sơ nhân viên gồm Danh tính, Giấy tờ, Liên hệ, Công việc. Nhãn có for/id, luôn hiện trên ô; chú thích/lỗi nằm trong ô và được aria-describedby tham chiếu. Dự trữ hai dòng nhãn trong lưới để nhãn xuống dòng không làm lệch ô; hàng cao theo trường cao nhất, khoảng hàng 16px. Ô chiếm đủ chiều rộng cột, cao ít nhất 44px, chữ ít nhất 14px; textarea nhiều dòng. Không đặt giới hạn max-width riêng cho trường trong form.

Hàng nút `ui-form-actions` căn trái đường cột đầu, nút chính trước, Hủy sau, gap 8px và cách nhóm cuối 24px. Dưới 600px các nút chia đều; form dài trên mobile có thanh nút dính đáy, focus có khoảng cuộn tránh bị che. Nút nguy hiểm giữ xác nhận nghiệp vụ hiện có.

Khung `.ui-main` dùng độ rộng tối đa token và căn giữa; đo lề hai bên sai số tối đa 2px cả khi đổi trạng thái sidebar. Ô date/month vẫn dùng control native, lang vi và giá trị POST chuẩn; JS thêm `.ui-date-echo` với aria-live polite, ngày hiện thứ tiếng Việt cùng dd/mm/yyyy, tháng hiện tên tháng/năm, để trống khi chưa chọn. Không JS vẫn nhập được ngày. Echo và khối thao tác không in; giấy HCNS/BCC giữ bố cục độc lập.

Cổng bàn giao: audit căn lề toàn bộ route/vai trò/7 độ rộng/hai theme, form contract và truy vấn cùng DB giả, Edge workflows, PDF ảnh/số đo, cache cũ, full suite hai backend. Không dùng HTTP200 hoặc số trang PDF thay chứng cứ hình học/ảnh. Kết quả và phần chưa kiểm thử chỉ ghi tại [nhật ký dự án](../docs/PROJECT_WORK_LOG.md).
