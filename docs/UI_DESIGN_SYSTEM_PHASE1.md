# Design system UI IHRMS — Giai đoạn 1

Đề xuất chờ duyệt: [MASTER](../design-system/MASTER.md). Kiểm kê, lệnh chạy, kết quả và phần còn mở chỉ ghi tại [PROJECT_WORK_LOG](PROJECT_WORK_LOG.md).

[`src/static/css/ui_tokens_proposed.css`](../src/static/css/ui_tokens_proposed.css) là bộ CSS variables riêng, **chưa được import vào giao diện**. Không sửa tokens hiện hành, template, view, URL, model, migration hoặc RBAC trong Giai đoạn 0–1.

Khi đã duyệt, component dùng `--ui-bg`, `--ui-surface`, `--ui-text`, `--ui-text-muted`, `--ui-border`; nút primary dùng `--ui-brand` cùng `--ui-on-brand`, hover/active dùng biến tương ứng. Badge/alert dùng bộ `--ui-{success,warning,danger,info}-{text,bg,border}`; errors dùng aliases `--ui-error-*`. Không ghép màu tùy ý hoặc dùng divider làm viền input.

Theme selector tương thích JS hiện có: `html[data-theme="light|dark"]`. Typography dùng font hệ thống, body 16px, bảng 14px, caption 12px; spacing theo 4/8px; control min 44px. Focus ring cần khoảng nền quanh nút filled và không bị sticky header che. Reduced motion chỉ được tôn trọng khi component dùng các motion variables; tệp này không tự điều khiển animation sẵn có.

Giai đoạn 2 cần lần lượt chuyển base/navigation rồi component dùng chung, kiểm tra CSS cascade với Tailwind/theme/admin, dữ liệu giả và từng vai trò. Không áp dụng tokens toàn cục cho giấy tờ HCNS/print. Chủ dự án cần duyệt màu tím trên neutral slate, font hệ thống, sidebar desktop/drawer mobile và contracts trong MASTER trước khi triển khai.

Đo local bằng công thức luminance sRGB WCAG: 84 cặp của hai theme đạt ngưỡng đã đặt; text thấp nhất 5.599:1, control/focus/border thấp nhất 3.860:1. Phạm vi: text/muted/link trên bg/surface/raised/hover, border/focus trên bốn nền này, on-brand trên ba trạng thái brand, link trên brand-soft, selected, disabled, semantic/error text trên nền tương ứng và border trên nền tương ứng/surface. Ngoài danh sách này phải đo lại khi sử dụng; scrim/bóng alpha chưa đo trên trang thật.

Đã đọc cmap của `C:/Windows/Fonts/segoeui.ttf`, `seguisb.ttf` và `segoeuib.ttf`: regular/semibold/bold đều có 155 codepoint kiểm tra (vowel/tonal combinations tiếng Việt NFC, đ/Đ, dấu tổ hợp và ₫). Đây là kiểm tra có glyph trên máy này, chưa phải visual QA/NFD shaping trên máy đích hoặc xác nhận mọi fallback. Chưa tuyên bố giao diện đạt WCAG.
