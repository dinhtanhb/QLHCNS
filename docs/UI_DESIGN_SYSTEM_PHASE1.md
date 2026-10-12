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
| light | `--ui-text` | `--ui-bg` | `#0c233b` | `#f4f7f5` | 14.759:1 | 4.5:1 | Đạt |
| light | `--ui-text-muted` | `--ui-bg` | `#4b6171` | `#f4f7f5` | 5.995:1 | 4.5:1 | Đạt |
| light | `--ui-link` | `--ui-bg` | `#0b7461` | `#f4f7f5` | 5.283:1 | 4.5:1 | Đạt |
| light | `--ui-border` | `--ui-bg` | `#627d78` | `#f4f7f5` | 4.121:1 | 3:1 | Đạt |
| light | `--ui-focus` | `--ui-bg` | `#0b7461` | `#f4f7f5` | 5.283:1 | 3:1 | Đạt |
| light | `--ui-text` | `--ui-surface` | `#0c233b` | `#ffffff` | 15.919:1 | 4.5:1 | Đạt |
| light | `--ui-text-muted` | `--ui-surface` | `#4b6171` | `#ffffff` | 6.467:1 | 4.5:1 | Đạt |
| light | `--ui-link` | `--ui-surface` | `#0b7461` | `#ffffff` | 5.699:1 | 4.5:1 | Đạt |
| light | `--ui-border` | `--ui-surface` | `#627d78` | `#ffffff` | 4.445:1 | 3:1 | Đạt |
| light | `--ui-focus` | `--ui-surface` | `#0b7461` | `#ffffff` | 5.699:1 | 3:1 | Đạt |
| light | `--ui-text` | `--ui-surface-raised` | `#0c233b` | `#f0f5f2` | 14.439:1 | 4.5:1 | Đạt |
| light | `--ui-text-muted` | `--ui-surface-raised` | `#4b6171` | `#f0f5f2` | 5.865:1 | 4.5:1 | Đạt |
| light | `--ui-link` | `--ui-surface-raised` | `#0b7461` | `#f0f5f2` | 5.169:1 | 4.5:1 | Đạt |
| light | `--ui-border` | `--ui-surface-raised` | `#627d78` | `#f0f5f2` | 4.032:1 | 3:1 | Đạt |
| light | `--ui-focus` | `--ui-surface-raised` | `#0b7461` | `#f0f5f2` | 5.169:1 | 3:1 | Đạt |
| light | `--ui-text` | `--ui-hover-bg` | `#0c233b` | `#edf4f0` | 14.251:1 | 4.5:1 | Đạt |
| light | `--ui-text-muted` | `--ui-hover-bg` | `#4b6171` | `#edf4f0` | 5.789:1 | 4.5:1 | Đạt |
| light | `--ui-link` | `--ui-hover-bg` | `#0b7461` | `#edf4f0` | 5.102:1 | 4.5:1 | Đạt |
| light | `--ui-border` | `--ui-hover-bg` | `#627d78` | `#edf4f0` | 3.980:1 | 3:1 | Đạt |
| light | `--ui-focus` | `--ui-hover-bg` | `#0b7461` | `#edf4f0` | 5.102:1 | 3:1 | Đạt |
| light | `--ui-on-brand` | `--ui-brand` | `#ffffff` | `#0b7461` | 5.699:1 | 4.5:1 | Đạt |
| light | `--ui-on-brand` | `--ui-brand-hover` | `#ffffff` | `#085e50` | 7.700:1 | 4.5:1 | Đạt |
| light | `--ui-on-brand` | `--ui-brand-active` | `#ffffff` | `#064c41` | 9.916:1 | 4.5:1 | Đạt |
| light | `--ui-link` | `--ui-brand-soft` | `#0b7461` | `#edf7f2` | 5.207:1 | 4.5:1 | Đạt |
| light | `--ui-selected-text` | `--ui-selected-bg` | `#085e50` | `#dff0e8` | 6.515:1 | 4.5:1 | Đạt |
| light | `--ui-disabled-text` | `--ui-disabled-bg` | `#4b6171` | `#dce7e1` | 5.100:1 | 4.5:1 | Đạt |
| light | `--ui-disabled-border` | `--ui-disabled-bg` | `#627d78` | `#dce7e1` | 3.506:1 | 3:1 | Đạt |
| light | `--ui-border` | `--ui-selected-bg` | `#627d78` | `#dff0e8` | 3.761:1 | 3:1 | Đạt |
| light | `--ui-focus` | `--ui-selected-bg` | `#0b7461` | `#dff0e8` | 4.821:1 | 3:1 | Đạt |
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
| light | `--ui-sidebar-text` | `--ui-sidebar-bg` | `#d6e5ee` | `#0c233b` | 12.357:1 | 4.5:1 | Đạt |
| light | `--ui-sidebar-border` | `--ui-sidebar-bg` | `#8aa6ad` | `#0c233b` | 6.169:1 | 3:1 | Đạt |
| light | `--ui-sidebar-focus` | `--ui-sidebar-bg` | `#6ee7c8` | `#0c233b` | 10.557:1 | 3:1 | Đạt |
| light | `--ui-sidebar-text` | `--ui-sidebar-hover-bg` | `#d6e5ee` | `#133a43` | 9.511:1 | 4.5:1 | Đạt |
| light | `--ui-sidebar-border` | `--ui-sidebar-hover-bg` | `#8aa6ad` | `#133a43` | 4.748:1 | 3:1 | Đạt |
| light | `--ui-sidebar-focus` | `--ui-sidebar-hover-bg` | `#6ee7c8` | `#133a43` | 8.126:1 | 3:1 | Đạt |
| light | `--ui-sidebar-active-text` | `--ui-sidebar-active-bg` | `#ffffff` | `#174b43` | 9.887:1 | 4.5:1 | Đạt |
| light | `--ui-sidebar-marker` | `--ui-sidebar-active-bg` | `#6ee7c8` | `#174b43` | 6.557:1 | 3:1 | Đạt |
| light | `--ui-sidebar-hover-text` | `--ui-sidebar-hover-bg` | `#ffffff` | `#133a43` | 12.252:1 | 4.5:1 | Đạt |
| light | `--ui-sidebar-marker` | `--ui-sidebar-hover-bg` | `#6ee7c8` | `#133a43` | 8.126:1 | 3:1 | Đạt |
| light | `--ui-sidebar-muted` | `--ui-sidebar-bg` | `#a9bdc9` | `#0c233b` | 8.194:1 | 4.5:1 | Đạt |
| light | `--ui-sidebar-focus` | `--ui-sidebar-active-bg` | `#6ee7c8` | `#174b43` | 6.557:1 | 3:1 | Đạt |
| light | `--ui-chart-series` | `--ui-bg` | `#0b7461` | `#f4f7f5` | 5.283:1 | 3:1 | Đạt |
| light | `--ui-chart-series-soft` | `--ui-bg` | `#085e50` | `#f4f7f5` | 7.139:1 | 3:1 | Đạt |
| light | `--ui-chart-series-strong` | `--ui-bg` | `#064c41` | `#f4f7f5` | 9.193:1 | 3:1 | Đạt |
| light | `--ui-chart-grid` | `--ui-bg` | `#627d78` | `#f4f7f5` | 4.121:1 | 3:1 | Đạt |
| light | `--ui-chart-hire` | `--ui-bg` | `#0b7461` | `#f4f7f5` | 5.283:1 | 3:1 | Đạt |
| light | `--ui-chart-departure` | `--ui-bg` | `#991b1b` | `#f4f7f5` | 7.704:1 | 3:1 | Đạt |
| light | `--ui-chart-transfer` | `--ui-bg` | `#075985` | `#f4f7f5` | 7.012:1 | 3:1 | Đạt |
| light | `--ui-chart-promotion` | `--ui-bg` | `#166534` | `#f4f7f5` | 6.611:1 | 3:1 | Đạt |
| light | `--ui-chart-axis` | `--ui-bg` | `#4b6171` | `#f4f7f5` | 5.995:1 | 4.5:1 | Đạt |
| light | `--ui-chart-label` | `--ui-bg` | `#0c233b` | `#f4f7f5` | 14.759:1 | 4.5:1 | Đạt |
| light | `--ui-chart-series` | `--ui-surface` | `#0b7461` | `#ffffff` | 5.699:1 | 3:1 | Đạt |
| light | `--ui-chart-series-soft` | `--ui-surface` | `#085e50` | `#ffffff` | 7.700:1 | 3:1 | Đạt |
| light | `--ui-chart-series-strong` | `--ui-surface` | `#064c41` | `#ffffff` | 9.916:1 | 3:1 | Đạt |
| light | `--ui-chart-grid` | `--ui-surface` | `#627d78` | `#ffffff` | 4.445:1 | 3:1 | Đạt |
| light | `--ui-chart-hire` | `--ui-surface` | `#0b7461` | `#ffffff` | 5.699:1 | 3:1 | Đạt |
| light | `--ui-chart-departure` | `--ui-surface` | `#991b1b` | `#ffffff` | 8.310:1 | 3:1 | Đạt |
| light | `--ui-chart-transfer` | `--ui-surface` | `#075985` | `#ffffff` | 7.563:1 | 3:1 | Đạt |
| light | `--ui-chart-promotion` | `--ui-surface` | `#166534` | `#ffffff` | 7.130:1 | 3:1 | Đạt |
| light | `--ui-chart-axis` | `--ui-surface` | `#4b6171` | `#ffffff` | 6.467:1 | 4.5:1 | Đạt |
| light | `--ui-chart-label` | `--ui-surface` | `#0c233b` | `#ffffff` | 15.919:1 | 4.5:1 | Đạt |
| light | `--ui-chart-series` | `--ui-surface-raised` | `#0b7461` | `#f0f5f2` | 5.169:1 | 3:1 | Đạt |
| light | `--ui-chart-series-soft` | `--ui-surface-raised` | `#085e50` | `#f0f5f2` | 6.984:1 | 3:1 | Đạt |
| light | `--ui-chart-series-strong` | `--ui-surface-raised` | `#064c41` | `#f0f5f2` | 8.994:1 | 3:1 | Đạt |
| light | `--ui-chart-grid` | `--ui-surface-raised` | `#627d78` | `#f0f5f2` | 4.032:1 | 3:1 | Đạt |
| light | `--ui-chart-hire` | `--ui-surface-raised` | `#0b7461` | `#f0f5f2` | 5.169:1 | 3:1 | Đạt |
| light | `--ui-chart-departure` | `--ui-surface-raised` | `#991b1b` | `#f0f5f2` | 7.538:1 | 3:1 | Đạt |
| light | `--ui-chart-transfer` | `--ui-surface-raised` | `#075985` | `#f0f5f2` | 6.860:1 | 3:1 | Đạt |
| light | `--ui-chart-promotion` | `--ui-surface-raised` | `#166534` | `#f0f5f2` | 6.468:1 | 3:1 | Đạt |
| light | `--ui-chart-axis` | `--ui-surface-raised` | `#4b6171` | `#f0f5f2` | 5.865:1 | 4.5:1 | Đạt |
| light | `--ui-chart-label` | `--ui-surface-raised` | `#0c233b` | `#f0f5f2` | 14.439:1 | 4.5:1 | Đạt |
| dark | `--ui-text` | `--ui-bg` | `#eef6f8` | `#0e1827` | 16.267:1 | 4.5:1 | Đạt |
| dark | `--ui-text-muted` | `--ui-bg` | `#b9cad5` | `#0e1827` | 10.582:1 | 4.5:1 | Đạt |
| dark | `--ui-link` | `--ui-bg` | `#63dbc2` | `#0e1827` | 10.557:1 | 4.5:1 | Đạt |
| dark | `--ui-border` | `--ui-bg` | `#8aaba6` | `#0e1827` | 7.175:1 | 3:1 | Đạt |
| dark | `--ui-focus` | `--ui-bg` | `#63dbc2` | `#0e1827` | 10.557:1 | 3:1 | Đạt |
| dark | `--ui-text` | `--ui-surface` | `#eef6f8` | `#162536` | 14.181:1 | 4.5:1 | Đạt |
| dark | `--ui-text-muted` | `--ui-surface` | `#b9cad5` | `#162536` | 9.225:1 | 4.5:1 | Đạt |
| dark | `--ui-link` | `--ui-surface` | `#63dbc2` | `#162536` | 9.203:1 | 4.5:1 | Đạt |
| dark | `--ui-border` | `--ui-surface` | `#8aaba6` | `#162536` | 6.255:1 | 3:1 | Đạt |
| dark | `--ui-focus` | `--ui-surface` | `#63dbc2` | `#162536` | 9.203:1 | 3:1 | Đạt |
| dark | `--ui-text` | `--ui-surface-raised` | `#eef6f8` | `#223648` | 11.350:1 | 4.5:1 | Đạt |
| dark | `--ui-text-muted` | `--ui-surface-raised` | `#b9cad5` | `#223648` | 7.383:1 | 4.5:1 | Đạt |
| dark | `--ui-link` | `--ui-surface-raised` | `#63dbc2` | `#223648` | 7.365:1 | 4.5:1 | Đạt |
| dark | `--ui-border` | `--ui-surface-raised` | `#8aaba6` | `#223648` | 5.006:1 | 3:1 | Đạt |
| dark | `--ui-focus` | `--ui-surface-raised` | `#63dbc2` | `#223648` | 7.365:1 | 3:1 | Đạt |
| dark | `--ui-text` | `--ui-hover-bg` | `#eef6f8` | `#223648` | 11.350:1 | 4.5:1 | Đạt |
| dark | `--ui-text-muted` | `--ui-hover-bg` | `#b9cad5` | `#223648` | 7.383:1 | 4.5:1 | Đạt |
| dark | `--ui-link` | `--ui-hover-bg` | `#63dbc2` | `#223648` | 7.365:1 | 4.5:1 | Đạt |
| dark | `--ui-border` | `--ui-hover-bg` | `#8aaba6` | `#223648` | 5.006:1 | 3:1 | Đạt |
| dark | `--ui-focus` | `--ui-hover-bg` | `#63dbc2` | `#223648` | 7.365:1 | 3:1 | Đạt |
| dark | `--ui-on-brand` | `--ui-brand` | `#092b26` | `#63dbc2` | 8.982:1 | 4.5:1 | Đạt |
| dark | `--ui-on-brand` | `--ui-brand-hover` | `#092b26` | `#8ee7d4` | 10.491:1 | 4.5:1 | Đạt |
| dark | `--ui-on-brand` | `--ui-brand-active` | `#092b26` | `#38c5a6` | 7.007:1 | 4.5:1 | Đạt |
| dark | `--ui-link` | `--ui-brand-soft` | `#63dbc2` | `#123c35` | 7.219:1 | 4.5:1 | Đạt |
| dark | `--ui-selected-text` | `--ui-selected-bg` | `#a6f2df` | `#174b43` | 7.716:1 | 4.5:1 | Đạt |
| dark | `--ui-disabled-text` | `--ui-disabled-bg` | `#b9cad5` | `#223648` | 7.383:1 | 4.5:1 | Đạt |
| dark | `--ui-disabled-border` | `--ui-disabled-bg` | `#8aaba6` | `#223648` | 5.006:1 | 3:1 | Đạt |
| dark | `--ui-border` | `--ui-selected-bg` | `#8aaba6` | `#174b43` | 3.982:1 | 3:1 | Đạt |
| dark | `--ui-focus` | `--ui-selected-bg` | `#63dbc2` | `#174b43` | 5.858:1 | 3:1 | Đạt |
| dark | `--ui-success-text` | `--ui-success-bg` | `#86efac` | `#052e16` | 10.616:1 | 4.5:1 | Đạt |
| dark | `--ui-success-border` | `--ui-success-bg` | `#86efac` | `#052e16` | 10.616:1 | 3:1 | Đạt |
| dark | `--ui-success-border` | `--ui-surface` | `#86efac` | `#162536` | 11.062:1 | 3:1 | Đạt |
| dark | `--ui-warning-text` | `--ui-warning-bg` | `#fde68a` | `#451a03` | 12.026:1 | 4.5:1 | Đạt |
| dark | `--ui-warning-border` | `--ui-warning-bg` | `#fde68a` | `#451a03` | 12.026:1 | 3:1 | Đạt |
| dark | `--ui-warning-border` | `--ui-surface` | `#fde68a` | `#162536` | 12.472:1 | 3:1 | Đạt |
| dark | `--ui-danger-text` | `--ui-danger-bg` | `#fca5a5` | `#450a0a` | 8.506:1 | 4.5:1 | Đạt |
| dark | `--ui-danger-border` | `--ui-danger-bg` | `#fca5a5` | `#450a0a` | 8.506:1 | 3:1 | Đạt |
| dark | `--ui-danger-border` | `--ui-surface` | `#fca5a5` | `#162536` | 8.184:1 | 3:1 | Đạt |
| dark | `--ui-info-text` | `--ui-info-bg` | `#7dd3fc` | `#082f49` | 8.324:1 | 4.5:1 | Đạt |
| dark | `--ui-info-border` | `--ui-info-bg` | `#7dd3fc` | `#082f49` | 8.324:1 | 3:1 | Đạt |
| dark | `--ui-info-border` | `--ui-surface` | `#7dd3fc` | `#162536` | 9.316:1 | 3:1 | Đạt |
| dark | `--ui-error-text` | `--ui-error-bg` | `#fca5a5` | `#450a0a` | 8.506:1 | 4.5:1 | Đạt |
| dark | `--ui-error-border` | `--ui-error-bg` | `#fca5a5` | `#450a0a` | 8.506:1 | 3:1 | Đạt |
| dark | `--ui-error-border` | `--ui-surface` | `#fca5a5` | `#162536` | 8.184:1 | 3:1 | Đạt |
| dark | `--ui-sidebar-text` | `--ui-sidebar-bg` | `#d6e5ee` | `#0c233b` | 12.357:1 | 4.5:1 | Đạt |
| dark | `--ui-sidebar-border` | `--ui-sidebar-bg` | `#8aa6ad` | `#0c233b` | 6.169:1 | 3:1 | Đạt |
| dark | `--ui-sidebar-focus` | `--ui-sidebar-bg` | `#6ee7c8` | `#0c233b` | 10.557:1 | 3:1 | Đạt |
| dark | `--ui-sidebar-text` | `--ui-sidebar-hover-bg` | `#d6e5ee` | `#133a43` | 9.511:1 | 4.5:1 | Đạt |
| dark | `--ui-sidebar-border` | `--ui-sidebar-hover-bg` | `#8aa6ad` | `#133a43` | 4.748:1 | 3:1 | Đạt |
| dark | `--ui-sidebar-focus` | `--ui-sidebar-hover-bg` | `#6ee7c8` | `#133a43` | 8.126:1 | 3:1 | Đạt |
| dark | `--ui-sidebar-active-text` | `--ui-sidebar-active-bg` | `#ffffff` | `#174b43` | 9.887:1 | 4.5:1 | Đạt |
| dark | `--ui-sidebar-marker` | `--ui-sidebar-active-bg` | `#6ee7c8` | `#174b43` | 6.557:1 | 3:1 | Đạt |
| dark | `--ui-sidebar-hover-text` | `--ui-sidebar-hover-bg` | `#ffffff` | `#133a43` | 12.252:1 | 4.5:1 | Đạt |
| dark | `--ui-sidebar-marker` | `--ui-sidebar-hover-bg` | `#6ee7c8` | `#133a43` | 8.126:1 | 3:1 | Đạt |
| dark | `--ui-sidebar-muted` | `--ui-sidebar-bg` | `#a9bdc9` | `#0c233b` | 8.194:1 | 4.5:1 | Đạt |
| dark | `--ui-sidebar-focus` | `--ui-sidebar-active-bg` | `#6ee7c8` | `#174b43` | 6.557:1 | 3:1 | Đạt |
| dark | `--ui-chart-series` | `--ui-bg` | `#63dbc2` | `#0e1827` | 10.557:1 | 3:1 | Đạt |
| dark | `--ui-chart-series-soft` | `--ui-bg` | `#8ee7d4` | `#0e1827` | 12.329:1 | 3:1 | Đạt |
| dark | `--ui-chart-series-strong` | `--ui-bg` | `#38c5a6` | `#0e1827` | 8.234:1 | 3:1 | Đạt |
| dark | `--ui-chart-grid` | `--ui-bg` | `#8aaba6` | `#0e1827` | 7.175:1 | 3:1 | Đạt |
| dark | `--ui-chart-hire` | `--ui-bg` | `#63dbc2` | `#0e1827` | 10.557:1 | 3:1 | Đạt |
| dark | `--ui-chart-departure` | `--ui-bg` | `#fca5a5` | `#0e1827` | 9.388:1 | 3:1 | Đạt |
| dark | `--ui-chart-transfer` | `--ui-bg` | `#7dd3fc` | `#0e1827` | 10.687:1 | 3:1 | Đạt |
| dark | `--ui-chart-promotion` | `--ui-bg` | `#86efac` | `#0e1827` | 12.689:1 | 3:1 | Đạt |
| dark | `--ui-chart-axis` | `--ui-bg` | `#b9cad5` | `#0e1827` | 10.582:1 | 4.5:1 | Đạt |
| dark | `--ui-chart-label` | `--ui-bg` | `#eef6f8` | `#0e1827` | 16.267:1 | 4.5:1 | Đạt |
| dark | `--ui-chart-series` | `--ui-surface` | `#63dbc2` | `#162536` | 9.203:1 | 3:1 | Đạt |
| dark | `--ui-chart-series-soft` | `--ui-surface` | `#8ee7d4` | `#162536` | 10.748:1 | 3:1 | Đạt |
| dark | `--ui-chart-series-strong` | `--ui-surface` | `#38c5a6` | `#162536` | 7.178:1 | 3:1 | Đạt |
| dark | `--ui-chart-grid` | `--ui-surface` | `#8aaba6` | `#162536` | 6.255:1 | 3:1 | Đạt |
| dark | `--ui-chart-hire` | `--ui-surface` | `#63dbc2` | `#162536` | 9.203:1 | 3:1 | Đạt |
| dark | `--ui-chart-departure` | `--ui-surface` | `#fca5a5` | `#162536` | 8.184:1 | 3:1 | Đạt |
| dark | `--ui-chart-transfer` | `--ui-surface` | `#7dd3fc` | `#162536` | 9.316:1 | 3:1 | Đạt |
| dark | `--ui-chart-promotion` | `--ui-surface` | `#86efac` | `#162536` | 11.062:1 | 3:1 | Đạt |
| dark | `--ui-chart-axis` | `--ui-surface` | `#b9cad5` | `#162536` | 9.225:1 | 4.5:1 | Đạt |
| dark | `--ui-chart-label` | `--ui-surface` | `#eef6f8` | `#162536` | 14.181:1 | 4.5:1 | Đạt |
| dark | `--ui-chart-series` | `--ui-surface-raised` | `#63dbc2` | `#223648` | 7.365:1 | 3:1 | Đạt |
| dark | `--ui-chart-series-soft` | `--ui-surface-raised` | `#8ee7d4` | `#223648` | 8.602:1 | 3:1 | Đạt |
| dark | `--ui-chart-series-strong` | `--ui-surface-raised` | `#38c5a6` | `#223648` | 5.745:1 | 3:1 | Đạt |
| dark | `--ui-chart-grid` | `--ui-surface-raised` | `#8aaba6` | `#223648` | 5.006:1 | 3:1 | Đạt |
| dark | `--ui-chart-hire` | `--ui-surface-raised` | `#63dbc2` | `#223648` | 7.365:1 | 3:1 | Đạt |
| dark | `--ui-chart-departure` | `--ui-surface-raised` | `#fca5a5` | `#223648` | 6.550:1 | 3:1 | Đạt |
| dark | `--ui-chart-transfer` | `--ui-surface-raised` | `#7dd3fc` | `#223648` | 7.456:1 | 3:1 | Đạt |
| dark | `--ui-chart-promotion` | `--ui-surface-raised` | `#86efac` | `#223648` | 8.854:1 | 3:1 | Đạt |
| dark | `--ui-chart-axis` | `--ui-surface-raised` | `#b9cad5` | `#223648` | 7.383:1 | 4.5:1 | Đạt |
| dark | `--ui-chart-label` | `--ui-surface-raised` | `#eef6f8` | `#223648` | 11.350:1 | 4.5:1 | Đạt |
<!-- UI_CONTRAST_END -->
