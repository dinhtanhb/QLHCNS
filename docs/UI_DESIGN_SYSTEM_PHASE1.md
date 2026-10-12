# Design system UI IHRMS — Giai đoạn 1

[MASTER](../design-system/MASTER.md) đã được chủ dự án duyệt ngày 12/10/2026 kèm điều kiện Giai đoạn 2. Kiểm kê, lệnh chạy, kết quả và phần còn mở chỉ ghi tại [PROJECT_WORK_LOG](PROJECT_WORK_LOG.md).

[`src/static/css/ui_tokens.css`](../src/static/css/ui_tokens.css) là bộ CSS variables chính thức; đã đổi tên từ proposed trong Giai đoạn 2. Aliases `ihrms-*`, Tailwind và Bootstrap chỉ trỏ một chiều tới các tokens trong screen adapters. Không áp alias mới lên bản in HCNS. Base và admin tải tokens local; thứ tự cascade được mô tả trong MASTER.

Khi đã duyệt, component dùng `--ui-bg`, `--ui-surface`, `--ui-text`, `--ui-text-muted`, `--ui-border`; nút primary dùng `--ui-brand` cùng `--ui-on-brand`, hover/active dùng biến tương ứng. Badge/alert dùng bộ `--ui-{success,warning,danger,info}-{text,bg,border}`; errors dùng aliases `--ui-error-*`. Không ghép màu tùy ý hoặc dùng divider làm viền input.

Theme selector: `html[data-theme="light|dark"]`; CSS fallback theo OS khi chưa có attribute, explicit light/dark luôn thắng. JS chạy trước styles và theo OS khi chưa lưu lựa chọn. Typography `"Segoe UI", system-ui, -apple-system, Roboto, Arial, sans-serif`, body 16px, bảng 14px, caption 12px; spacing theo 4/8px; control min 44px. Focus ring cần khoảng nền quanh nút filled và không bị sticky header che. Reduced motion dùng các motion variables.

Giai đoạn 2 chuyển base/navigation; nội dung trang con giữ nguyên. Không áp dụng tokens toàn cục cho giấy tờ HCNS/print. Sidebar/chart có tokens riêng, xem MASTER. Cuối giai đoạn cần chủ dự án xem light/dark, desktop/mobile rồi quyết định push; Codex không push/deploy.

Chạy `python ops/check_ui_contrast.py` bằng Python hệ thống (stdlib, không cài gói). `python ops/check_ui_contrast.py --write-doc` cập nhật bảng dưới. Exit 1 nếu bất kỳ cặp đã quy định không đạt. Công thức luminance sRGB WCAG, so ngưỡng bằng giá trị đầy đủ trước làm tròn; bảng ghi từng cặp gồm sidebar/chart. Ngoài danh sách phải đo lại khi sử dụng; scrim/bóng alpha chưa được bảng này chứng nhận. `--ui-divider` chỉ trang trí, không là viền control. Không dùng các màu khác ngoài contract mà suy ra chúng đã được đo.

Đã đọc cmap của `C:/Windows/Fonts/segoeui.ttf`, `seguisb.ttf` và `segoeuib.ttf`: regular/semibold/bold đều có 155 codepoint kiểm tra (vowel/tonal combinations tiếng Việt NFC, đ/Đ, dấu tổ hợp và ₫). Đây là kiểm tra có glyph trên máy này, chưa phải visual QA/NFD shaping trên máy đích hoặc xác nhận mọi fallback. Chưa tuyên bố giao diện đạt WCAG.


<!-- UI_CONTRAST_BEGIN -->
| Theme | Chữ/UI | Nền | Màu trước | Màu nền | Tỷ lệ | Ngưỡng | Kết quả |
|---|---|---|---|---|---:|---:|---|
| light | `--ui-text` | `--ui-bg` | `#0f172a` | `#f8fafc` | 17.063:1 | 4.5:1 | Đạt |
| light | `--ui-text-muted` | `--ui-bg` | `#475569` | `#f8fafc` | 7.243:1 | 4.5:1 | Đạt |
| light | `--ui-link` | `--ui-bg` | `#6d28d9` | `#f8fafc` | 6.791:1 | 4.5:1 | Đạt |
| light | `--ui-border` | `--ui-bg` | `#64748b` | `#f8fafc` | 4.548:1 | 3:1 | Đạt |
| light | `--ui-focus` | `--ui-bg` | `#6d28d9` | `#f8fafc` | 6.791:1 | 3:1 | Đạt |
| light | `--ui-text` | `--ui-surface` | `#0f172a` | `#ffffff` | 17.853:1 | 4.5:1 | Đạt |
| light | `--ui-text-muted` | `--ui-surface` | `#475569` | `#ffffff` | 7.578:1 | 4.5:1 | Đạt |
| light | `--ui-link` | `--ui-surface` | `#6d28d9` | `#ffffff` | 7.105:1 | 4.5:1 | Đạt |
| light | `--ui-border` | `--ui-surface` | `#64748b` | `#ffffff` | 4.759:1 | 3:1 | Đạt |
| light | `--ui-focus` | `--ui-surface` | `#6d28d9` | `#ffffff` | 7.105:1 | 3:1 | Đạt |
| light | `--ui-text` | `--ui-surface-raised` | `#0f172a` | `#f1f5f9` | 16.296:1 | 4.5:1 | Đạt |
| light | `--ui-text-muted` | `--ui-surface-raised` | `#475569` | `#f1f5f9` | 6.917:1 | 4.5:1 | Đạt |
| light | `--ui-link` | `--ui-surface-raised` | `#6d28d9` | `#f1f5f9` | 6.485:1 | 4.5:1 | Đạt |
| light | `--ui-border` | `--ui-surface-raised` | `#64748b` | `#f1f5f9` | 4.344:1 | 3:1 | Đạt |
| light | `--ui-focus` | `--ui-surface-raised` | `#6d28d9` | `#f1f5f9` | 6.485:1 | 3:1 | Đạt |
| light | `--ui-text` | `--ui-hover-bg` | `#0f172a` | `#f1f5f9` | 16.296:1 | 4.5:1 | Đạt |
| light | `--ui-text-muted` | `--ui-hover-bg` | `#475569` | `#f1f5f9` | 6.917:1 | 4.5:1 | Đạt |
| light | `--ui-link` | `--ui-hover-bg` | `#6d28d9` | `#f1f5f9` | 6.485:1 | 4.5:1 | Đạt |
| light | `--ui-border` | `--ui-hover-bg` | `#64748b` | `#f1f5f9` | 4.344:1 | 3:1 | Đạt |
| light | `--ui-focus` | `--ui-hover-bg` | `#6d28d9` | `#f1f5f9` | 6.485:1 | 3:1 | Đạt |
| light | `--ui-on-brand` | `--ui-brand` | `#ffffff` | `#6d28d9` | 7.105:1 | 4.5:1 | Đạt |
| light | `--ui-on-brand` | `--ui-brand-hover` | `#ffffff` | `#5b21b6` | 8.983:1 | 4.5:1 | Đạt |
| light | `--ui-on-brand` | `--ui-brand-active` | `#ffffff` | `#4c1d95` | 10.954:1 | 4.5:1 | Đạt |
| light | `--ui-link` | `--ui-brand-soft` | `#6d28d9` | `#f5f3ff` | 6.478:1 | 4.5:1 | Đạt |
| light | `--ui-selected-text` | `--ui-selected-bg` | `#4c1d95` | `#ede9fe` | 9.227:1 | 4.5:1 | Đạt |
| light | `--ui-disabled-text` | `--ui-disabled-bg` | `#475569` | `#e2e8f0` | 6.147:1 | 4.5:1 | Đạt |
| light | `--ui-disabled-border` | `--ui-disabled-bg` | `#64748b` | `#e2e8f0` | 3.860:1 | 3:1 | Đạt |
| light | `--ui-border` | `--ui-selected-bg` | `#64748b` | `#ede9fe` | 4.008:1 | 3:1 | Đạt |
| light | `--ui-focus` | `--ui-selected-bg` | `#6d28d9` | `#ede9fe` | 5.984:1 | 3:1 | Đạt |
| light | `--ui-success-text` | `--ui-success-bg` | `#166534` | `#f0fdf4` | 6.812:1 | 4.5:1 | Đạt |
| light | `--ui-success-border` | `--ui-success-bg` | `#166534` | `#f0fdf4` | 6.812:1 | 3:1 | Đạt |
| light | `--ui-success-border` | `--ui-surface` | `#166534` | `#ffffff` | 7.130:1 | 3:1 | Đạt |
| light | `--ui-warning-text` | `--ui-warning-bg` | `#854d0e` | `#fffbeb` | 6.607:1 | 4.5:1 | Đạt |
| light | `--ui-warning-border` | `--ui-warning-bg` | `#854d0e` | `#fffbeb` | 6.607:1 | 3:1 | Đạt |
| light | `--ui-warning-border` | `--ui-surface` | `#854d0e` | `#ffffff` | 6.851:1 | 3:1 | Đạt |
| light | `--ui-danger-text` | `--ui-danger-bg` | `#991b1b` | `#fef2f2` | 7.597:1 | 4.5:1 | Đạt |
| light | `--ui-danger-border` | `--ui-danger-bg` | `#991b1b` | `#fef2f2` | 7.597:1 | 3:1 | Đạt |
| light | `--ui-danger-border` | `--ui-surface` | `#991b1b` | `#ffffff` | 8.310:1 | 3:1 | Đạt |
| light | `--ui-info-text` | `--ui-info-bg` | `#075985` | `#f0f9ff` | 7.095:1 | 4.5:1 | Đạt |
| light | `--ui-info-border` | `--ui-info-bg` | `#075985` | `#f0f9ff` | 7.095:1 | 3:1 | Đạt |
| light | `--ui-info-border` | `--ui-surface` | `#075985` | `#ffffff` | 7.563:1 | 3:1 | Đạt |
| light | `--ui-error-text` | `--ui-error-bg` | `#991b1b` | `#fef2f2` | 7.597:1 | 4.5:1 | Đạt |
| light | `--ui-error-border` | `--ui-error-bg` | `#991b1b` | `#fef2f2` | 7.597:1 | 3:1 | Đạt |
| light | `--ui-error-border` | `--ui-surface` | `#991b1b` | `#ffffff` | 8.310:1 | 3:1 | Đạt |
| light | `--ui-sidebar-text` | `--ui-sidebar-bg` | `#0f172a` | `#ffffff` | 17.853:1 | 4.5:1 | Đạt |
| light | `--ui-sidebar-border` | `--ui-sidebar-bg` | `#64748b` | `#ffffff` | 4.759:1 | 3:1 | Đạt |
| light | `--ui-focus` | `--ui-sidebar-bg` | `#6d28d9` | `#ffffff` | 7.105:1 | 3:1 | Đạt |
| light | `--ui-sidebar-text` | `--ui-sidebar-hover-bg` | `#0f172a` | `#f1f5f9` | 16.296:1 | 4.5:1 | Đạt |
| light | `--ui-sidebar-border` | `--ui-sidebar-hover-bg` | `#64748b` | `#f1f5f9` | 4.344:1 | 3:1 | Đạt |
| light | `--ui-focus` | `--ui-sidebar-hover-bg` | `#6d28d9` | `#f1f5f9` | 6.485:1 | 3:1 | Đạt |
| light | `--ui-sidebar-active-text` | `--ui-sidebar-active-bg` | `#4c1d95` | `#ede9fe` | 9.227:1 | 4.5:1 | Đạt |
| light | `--ui-sidebar-marker` | `--ui-sidebar-active-bg` | `#6d28d9` | `#ede9fe` | 5.984:1 | 3:1 | Đạt |
| light | `--ui-chart-series` | `--ui-bg` | `#6d28d9` | `#f8fafc` | 6.791:1 | 3:1 | Đạt |
| light | `--ui-chart-series-soft` | `--ui-bg` | `#5b21b6` | `#f8fafc` | 8.585:1 | 3:1 | Đạt |
| light | `--ui-chart-series-strong` | `--ui-bg` | `#4c1d95` | `#f8fafc` | 10.470:1 | 3:1 | Đạt |
| light | `--ui-chart-grid` | `--ui-bg` | `#64748b` | `#f8fafc` | 4.548:1 | 3:1 | Đạt |
| light | `--ui-chart-axis` | `--ui-bg` | `#475569` | `#f8fafc` | 7.243:1 | 4.5:1 | Đạt |
| light | `--ui-chart-label` | `--ui-bg` | `#0f172a` | `#f8fafc` | 17.063:1 | 4.5:1 | Đạt |
| light | `--ui-chart-series` | `--ui-surface` | `#6d28d9` | `#ffffff` | 7.105:1 | 3:1 | Đạt |
| light | `--ui-chart-series-soft` | `--ui-surface` | `#5b21b6` | `#ffffff` | 8.983:1 | 3:1 | Đạt |
| light | `--ui-chart-series-strong` | `--ui-surface` | `#4c1d95` | `#ffffff` | 10.954:1 | 3:1 | Đạt |
| light | `--ui-chart-grid` | `--ui-surface` | `#64748b` | `#ffffff` | 4.759:1 | 3:1 | Đạt |
| light | `--ui-chart-axis` | `--ui-surface` | `#475569` | `#ffffff` | 7.578:1 | 4.5:1 | Đạt |
| light | `--ui-chart-label` | `--ui-surface` | `#0f172a` | `#ffffff` | 17.853:1 | 4.5:1 | Đạt |
| light | `--ui-chart-series` | `--ui-surface-raised` | `#6d28d9` | `#f1f5f9` | 6.485:1 | 3:1 | Đạt |
| light | `--ui-chart-series-soft` | `--ui-surface-raised` | `#5b21b6` | `#f1f5f9` | 8.199:1 | 3:1 | Đạt |
| light | `--ui-chart-series-strong` | `--ui-surface-raised` | `#4c1d95` | `#f1f5f9` | 9.999:1 | 3:1 | Đạt |
| light | `--ui-chart-grid` | `--ui-surface-raised` | `#64748b` | `#f1f5f9` | 4.344:1 | 3:1 | Đạt |
| light | `--ui-chart-axis` | `--ui-surface-raised` | `#475569` | `#f1f5f9` | 6.917:1 | 4.5:1 | Đạt |
| light | `--ui-chart-label` | `--ui-surface-raised` | `#0f172a` | `#f1f5f9` | 16.296:1 | 4.5:1 | Đạt |
| dark | `--ui-text` | `--ui-bg` | `#f8fafc` | `#0f172a` | 17.063:1 | 4.5:1 | Đạt |
| dark | `--ui-text-muted` | `--ui-bg` | `#cbd5e1` | `#0f172a` | 12.024:1 | 4.5:1 | Đạt |
| dark | `--ui-link` | `--ui-bg` | `#c4b5fd` | `#0f172a` | 9.670:1 | 4.5:1 | Đạt |
| dark | `--ui-border` | `--ui-bg` | `#94a3b8` | `#0f172a` | 6.963:1 | 3:1 | Đạt |
| dark | `--ui-focus` | `--ui-bg` | `#c4b5fd` | `#0f172a` | 9.670:1 | 3:1 | Đạt |
| dark | `--ui-text` | `--ui-surface` | `#f8fafc` | `#1e293b` | 13.982:1 | 4.5:1 | Đạt |
| dark | `--ui-text-muted` | `--ui-surface` | `#cbd5e1` | `#1e293b` | 9.853:1 | 4.5:1 | Đạt |
| dark | `--ui-link` | `--ui-surface` | `#c4b5fd` | `#1e293b` | 7.924:1 | 4.5:1 | Đạt |
| dark | `--ui-border` | `--ui-surface` | `#94a3b8` | `#1e293b` | 5.705:1 | 3:1 | Đạt |
| dark | `--ui-focus` | `--ui-surface` | `#c4b5fd` | `#1e293b` | 7.924:1 | 3:1 | Đạt |
| dark | `--ui-text` | `--ui-surface-raised` | `#f8fafc` | `#334155` | 9.897:1 | 4.5:1 | Đạt |
| dark | `--ui-text-muted` | `--ui-surface-raised` | `#cbd5e1` | `#334155` | 6.974:1 | 4.5:1 | Đạt |
| dark | `--ui-link` | `--ui-surface-raised` | `#c4b5fd` | `#334155` | 5.609:1 | 4.5:1 | Đạt |
| dark | `--ui-border` | `--ui-surface-raised` | `#94a3b8` | `#334155` | 4.038:1 | 3:1 | Đạt |
| dark | `--ui-focus` | `--ui-surface-raised` | `#c4b5fd` | `#334155` | 5.609:1 | 3:1 | Đạt |
| dark | `--ui-text` | `--ui-hover-bg` | `#f8fafc` | `#334155` | 9.897:1 | 4.5:1 | Đạt |
| dark | `--ui-text-muted` | `--ui-hover-bg` | `#cbd5e1` | `#334155` | 6.974:1 | 4.5:1 | Đạt |
| dark | `--ui-link` | `--ui-hover-bg` | `#c4b5fd` | `#334155` | 5.609:1 | 4.5:1 | Đạt |
| dark | `--ui-border` | `--ui-hover-bg` | `#94a3b8` | `#334155` | 4.038:1 | 3:1 | Đạt |
| dark | `--ui-focus` | `--ui-hover-bg` | `#c4b5fd` | `#334155` | 5.609:1 | 3:1 | Đạt |
| dark | `--ui-on-brand` | `--ui-brand` | `#2e1065` | `#c4b5fd` | 8.254:1 | 4.5:1 | Đạt |
| dark | `--ui-on-brand` | `--ui-brand-hover` | `#2e1065` | `#ddd6fe` | 10.974:1 | 4.5:1 | Đạt |
| dark | `--ui-on-brand` | `--ui-brand-active` | `#2e1065` | `#a78bfa` | 5.599:1 | 4.5:1 | Đạt |
| dark | `--ui-link` | `--ui-brand-soft` | `#c4b5fd` | `#2e1065` | 8.254:1 | 4.5:1 | Đạt |
| dark | `--ui-selected-text` | `--ui-selected-bg` | `#ddd6fe` | `#2e1065` | 10.974:1 | 4.5:1 | Đạt |
| dark | `--ui-disabled-text` | `--ui-disabled-bg` | `#cbd5e1` | `#334155` | 6.974:1 | 4.5:1 | Đạt |
| dark | `--ui-disabled-border` | `--ui-disabled-bg` | `#94a3b8` | `#334155` | 4.038:1 | 3:1 | Đạt |
| dark | `--ui-border` | `--ui-selected-bg` | `#94a3b8` | `#2e1065` | 5.943:1 | 3:1 | Đạt |
| dark | `--ui-focus` | `--ui-selected-bg` | `#c4b5fd` | `#2e1065` | 8.254:1 | 3:1 | Đạt |
| dark | `--ui-success-text` | `--ui-success-bg` | `#86efac` | `#052e16` | 10.616:1 | 4.5:1 | Đạt |
| dark | `--ui-success-border` | `--ui-success-bg` | `#86efac` | `#052e16` | 10.616:1 | 3:1 | Đạt |
| dark | `--ui-success-border` | `--ui-surface` | `#86efac` | `#1e293b` | 10.418:1 | 3:1 | Đạt |
| dark | `--ui-warning-text` | `--ui-warning-bg` | `#fde68a` | `#451a03` | 12.026:1 | 4.5:1 | Đạt |
| dark | `--ui-warning-border` | `--ui-warning-bg` | `#fde68a` | `#451a03` | 12.026:1 | 3:1 | Đạt |
| dark | `--ui-warning-border` | `--ui-surface` | `#fde68a` | `#1e293b` | 11.746:1 | 3:1 | Đạt |
| dark | `--ui-danger-text` | `--ui-danger-bg` | `#fca5a5` | `#450a0a` | 8.506:1 | 4.5:1 | Đạt |
| dark | `--ui-danger-border` | `--ui-danger-bg` | `#fca5a5` | `#450a0a` | 8.506:1 | 3:1 | Đạt |
| dark | `--ui-danger-border` | `--ui-surface` | `#fca5a5` | `#1e293b` | 7.708:1 | 3:1 | Đạt |
| dark | `--ui-info-text` | `--ui-info-bg` | `#7dd3fc` | `#082f49` | 8.324:1 | 4.5:1 | Đạt |
| dark | `--ui-info-border` | `--ui-info-bg` | `#7dd3fc` | `#082f49` | 8.324:1 | 3:1 | Đạt |
| dark | `--ui-info-border` | `--ui-surface` | `#7dd3fc` | `#1e293b` | 8.774:1 | 3:1 | Đạt |
| dark | `--ui-error-text` | `--ui-error-bg` | `#fca5a5` | `#450a0a` | 8.506:1 | 4.5:1 | Đạt |
| dark | `--ui-error-border` | `--ui-error-bg` | `#fca5a5` | `#450a0a` | 8.506:1 | 3:1 | Đạt |
| dark | `--ui-error-border` | `--ui-surface` | `#fca5a5` | `#1e293b` | 7.708:1 | 3:1 | Đạt |
| dark | `--ui-sidebar-text` | `--ui-sidebar-bg` | `#f8fafc` | `#1e293b` | 13.982:1 | 4.5:1 | Đạt |
| dark | `--ui-sidebar-border` | `--ui-sidebar-bg` | `#94a3b8` | `#1e293b` | 5.705:1 | 3:1 | Đạt |
| dark | `--ui-focus` | `--ui-sidebar-bg` | `#c4b5fd` | `#1e293b` | 7.924:1 | 3:1 | Đạt |
| dark | `--ui-sidebar-text` | `--ui-sidebar-hover-bg` | `#f8fafc` | `#334155` | 9.897:1 | 4.5:1 | Đạt |
| dark | `--ui-sidebar-border` | `--ui-sidebar-hover-bg` | `#94a3b8` | `#334155` | 4.038:1 | 3:1 | Đạt |
| dark | `--ui-focus` | `--ui-sidebar-hover-bg` | `#c4b5fd` | `#334155` | 5.609:1 | 3:1 | Đạt |
| dark | `--ui-sidebar-active-text` | `--ui-sidebar-active-bg` | `#ddd6fe` | `#2e1065` | 10.974:1 | 4.5:1 | Đạt |
| dark | `--ui-sidebar-marker` | `--ui-sidebar-active-bg` | `#c4b5fd` | `#2e1065` | 8.254:1 | 3:1 | Đạt |
| dark | `--ui-chart-series` | `--ui-bg` | `#c4b5fd` | `#0f172a` | 9.670:1 | 3:1 | Đạt |
| dark | `--ui-chart-series-soft` | `--ui-bg` | `#ddd6fe` | `#0f172a` | 12.857:1 | 3:1 | Đạt |
| dark | `--ui-chart-series-strong` | `--ui-bg` | `#a78bfa` | `#0f172a` | 6.560:1 | 3:1 | Đạt |
| dark | `--ui-chart-grid` | `--ui-bg` | `#94a3b8` | `#0f172a` | 6.963:1 | 3:1 | Đạt |
| dark | `--ui-chart-axis` | `--ui-bg` | `#cbd5e1` | `#0f172a` | 12.024:1 | 4.5:1 | Đạt |
| dark | `--ui-chart-label` | `--ui-bg` | `#f8fafc` | `#0f172a` | 17.063:1 | 4.5:1 | Đạt |
| dark | `--ui-chart-series` | `--ui-surface` | `#c4b5fd` | `#1e293b` | 7.924:1 | 3:1 | Đạt |
| dark | `--ui-chart-series-soft` | `--ui-surface` | `#ddd6fe` | `#1e293b` | 10.536:1 | 3:1 | Đạt |
| dark | `--ui-chart-series-strong` | `--ui-surface` | `#a78bfa` | `#1e293b` | 5.375:1 | 3:1 | Đạt |
| dark | `--ui-chart-grid` | `--ui-surface` | `#94a3b8` | `#1e293b` | 5.705:1 | 3:1 | Đạt |
| dark | `--ui-chart-axis` | `--ui-surface` | `#cbd5e1` | `#1e293b` | 9.853:1 | 4.5:1 | Đạt |
| dark | `--ui-chart-label` | `--ui-surface` | `#f8fafc` | `#1e293b` | 13.982:1 | 4.5:1 | Đạt |
| dark | `--ui-chart-series` | `--ui-surface-raised` | `#c4b5fd` | `#334155` | 5.609:1 | 3:1 | Đạt |
| dark | `--ui-chart-series-soft` | `--ui-surface-raised` | `#ddd6fe` | `#334155` | 7.457:1 | 3:1 | Đạt |
| dark | `--ui-chart-series-strong` | `--ui-surface-raised` | `#a78bfa` | `#334155` | 3.805:1 | 3:1 | Đạt |
| dark | `--ui-chart-grid` | `--ui-surface-raised` | `#94a3b8` | `#334155` | 4.038:1 | 3:1 | Đạt |
| dark | `--ui-chart-axis` | `--ui-surface-raised` | `#cbd5e1` | `#334155` | 6.974:1 | 4.5:1 | Đạt |
| dark | `--ui-chart-label` | `--ui-surface-raised` | `#f8fafc` | `#334155` | 9.897:1 | 4.5:1 | Đạt |
<!-- UI_CONTRAST_END -->
