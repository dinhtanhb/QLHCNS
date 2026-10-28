# Kế hoạch đổi dải màu IHRMS theo màu chủ đạo logo VietHealth

**Ngày lập:** 26/10/2026 · **Trạng thái:** phần đổi palette đã triển khai; P5 là tùy chọn riêng · **Nhánh:** `main`

Đối chiếu ngày 28/10/2026: D1-A, D2-B, D3-A, D4-A, D5-B, D6-A đã được chốt trong [nhật ký](PROJECT_WORK_LOG.md). Mặc định hiện tại là VietHealth; Chàm Đông và Than Ấm được giữ làm dải dự phòng qua cấu hình máy chủ `UI_PALETTE`, không phải bị xóa khỏi mã. Hợp đồng hiện hành ở [UI_DESIGN_SYSTEM.md](UI_DESIGN_SYSTEM.md). Các bảng “hiện tại/đề xuất”, bước triển khai và checkbox phía dưới là kế hoạch gốc để truy vết, không phải danh sách việc phải chạy lại. Cổng hiện tại đo 660 cặp trên ba palette; các lỗi in có sẵn và giới hạn kiểm thử được ghi trong nhật ký, không coi mọi cổng đã xanh. Giữ tài liệu vì P5 tùy chọn chưa được xác nhận hoàn tất; không suy ra quyền triển khai P5 từ việc dọn tài liệu.
**Bản xem trước trực quan:** [`outputs/palette-viethealth-20261026/index.html`](../outputs/palette-viethealth-20261026/index.html)

---

## 1. Mục tiêu

Đưa dải màu giao diện về đúng nhận diện VietHealth: **xanh lá là màu chủ đạo**, đỏ là màu nhấn phụ, nền trung tính pha nhẹ theo màu chủ đạo. Thay hoàn toàn palette **Chàm Đông (indigo)** đang dùng từ 21/10/2026.

Ba ràng buộc không thương lượng:

1. Không đổi nghiệp vụ, route, quyền dữ liệu, bản in HCNS.
2. Không nới bất kỳ cổng kiểm nào; mọi cặp màu phải tự đạt ngưỡng hiện hành.
3. Chỉ sửa nơi khai báo màu — hệ thống đã token hoá 100%, không có hex trong template hay JS.

---

## 2. Màu đo được từ logo

Đo trực tiếp trên `src/static/img/logo.png` (3476×1097) và trên ảnh chủ dự án gửi, đếm theo điểm ảnh đục:

| Vai trò trong logo | Mã màu | Tỷ lệ điểm ảnh | Ghi chú |
|---|---|---:|---|
| Xanh lá (biểu tượng + chữ "Health") | `#279048` | 17,7 % | **màu chủ đạo** |
| Đỏ (chữ "Viet") | `#CE181F` | 5,9 % | màu nhấn phụ |
| Trắng | `#FFFFFF` | 55,8 % | nền |

Hai mã này khớp nhau giữa ảnh chụp và tệp logo trong repo (lệch ≤ 1 đơn vị mỗi kênh do nén JPEG).

**Vấn đề kỹ thuật phải xử lý:** chữ trắng trên nền `#279048` chỉ đạt **4,06:1** — dưới ngưỡng 4,5:1 mà cổng `check_ui_contrast.py` bắt buộc. Vì vậy **không dùng nguyên mã logo làm màu nút**. Cần một bậc đậm hơn cho bề mặt có chữ, còn mã gốc giữ cho phần trang trí (biểu tượng, thanh tiến độ, lát biểu đồ).

Đo các bậc ứng viên (chữ trắng trên nền xanh):

| Mã | Trắng trên nền | Xanh làm chữ trên nền trang | Kết luận |
|---|---:|---:|---|
| `#279048` (logo gốc) | 4,06:1 ✗ | 4,06:1 ✗ | chỉ dùng trang trí |
| `#1F7A3D` | **5,37:1 ✓** | 4,74:1 ✓ | **chọn làm `--ui-brand`** |
| `#1D7437` | 5,82:1 ✓ | 5,14:1 ✓ | phương án dư biên |
| `#17652F` | 7,15:1 ✓ | 6,38:1 ✓ | `--ui-brand-hover` |
| `#0F4F24` | 9,70:1 ✓ | — | `--ui-brand-active` |

---

## 3. Nguyên tắc chuyển đổi

1. **Giữ nguyên cấu trúc token.** Không thêm/bớt tên biến, chỉ đổi giá trị. 63 chỗ dùng `var(--ui-brand)`, 29 chỗ `--ui-brand-hover`, 27 chỗ `--ui-link` trong 27 tệp CSS sẽ tự đổi theo — không sửa từng chỗ.
2. **Tách "màu logo" khỏi "màu hành động".** `#279048` dùng cho dấu hiệu trang trí; `#1F7A3D` cho nút/link/focus. Hai mã gần như không phân biệt bằng mắt nhưng khác nhau về ngưỡng tương phản.
3. **Nền trung tính pha xanh lá, không pha xanh dương.** Nền `#E7ECF4` (xanh lạnh) cạnh thương hiệu xanh lá sẽ lệch tông; đổi sang `#EDF2EE`.
4. **Đỏ của logo chỉ dùng cho ngữ nghĩa nguy hiểm.** Không dùng đỏ làm màu nhấn trang trí, không tô đỏ tiêu đề.
5. **Bốn màu ngữ nghĩa giữ nguyên giá trị** trừ đỏ (xem quyết định D2). Success/warning/info đã được đo và duyệt, không có lý do đổi.

---

## 4. Bảng ánh xạ token — nền sáng

| Token | Hiện tại (Chàm Đông) | Đề xuất (VietHealth) | Ghi chú |
|---|---|---|---|
| `--ui-bg` | `#E7ECF4` | `#EDF2EE` | nền trang, pha xanh lá |
| `--ui-surface` | `#FFFFFF` | `#FFFFFF` | giữ |
| `--ui-surface-raised` | `#F4F6FB` | `#F5F8F5` | |
| `--ui-surface-tint` | `#F4F6FB` | `#F5F8F5` | |
| `--ui-text` | `#101828` | `#101828` | giữ, trung tính |
| `--ui-text-muted` | `#475467` | `#475467` | giữ |
| `--ui-border` | `#667085` | `#667085` | giữ (viền control ≥ 3:1) |
| `--ui-divider` | `#E8ECF3` | `#E4EBE6` | |
| `--ui-card-border` | `#DFE4EE` | `#DCE4DE` | viền trang trí |
| `--ui-brand` | `#3A4FD0` | `#1F7A3D` | **màu chủ đạo** |
| `--ui-brand-hover` | `#2F42B5` | `#17652F` | |
| `--ui-brand-active` | `#26349B` | `#0F4F24` | |
| `--ui-brand-soft` | `#EEF1FD` | `#E9F5EE` | |
| `--ui-brand-600` | `#3A4FD0` | `#1F7A3D` | |
| `--ui-brand-700` | `#2F42B5` | `#17652F` | |
| `--ui-on-brand` | `#FFFFFF` | `#FFFFFF` | giữ |
| `--ui-link` | `#3A4FD0` | `#1F7A3D` | |
| `--ui-focus` | `#3A4FD0` | `#1F7A3D` | |
| `--ui-hover-bg` | `#EEF1FD` | `#E9F5EE` | |
| `--ui-selected-bg` | `#E6EAFC` | `#D9EEE2` | |
| `--ui-selected-text` | `#2F42B5` | `#17652F` | |
| `--ui-disabled-bg` | `#E3E8F2` | `#E3E8E4` | |
| `--ui-sidebar-hover-bg` | `#EEF1FD` | `#E9F5EE` | |
| `--ui-sidebar-hover-text` | `#2F42B5` | `#17652F` | |
| `--ui-sidebar-active-bg` | `#E6EAFC` | `#D9EEE2` | |
| `--ui-sidebar-active-text` | `#2F42B5` | `#17652F` | |
| `--ui-sidebar-marker` | `#3A4FD0` | `#1F7A3D` | vạch 3px bên trái |
| `--ui-sidebar-focus` | `#3A4FD0` | `#1F7A3D` | |
| `--ui-sidebar-divider` | `#E8ECF3` | `#E4EBE6` | |
| `--ui-danger-text` | `#B42318` | `#CE181F` | nếu chọn D2-B |
| `--ui-danger-border` | `#B42318` | `#CE181F` | nếu chọn D2-B |

`--ui-sidebar-bg` vẫn trắng, `--ui-sidebar-text` vẫn `#1D2939`.

## 5. Bảng ánh xạ token — nền tối

| Token | Hiện tại | Đề xuất | Ghi chú |
|---|---|---|---|
| `--ui-bg` | `#080C18` | `#08120D` | đen pha xanh lá |
| `--ui-surface` | `#131A2E` | `#111A14` | |
| `--ui-surface-raised` | `#1B2440` | `#18241C` | |
| `--ui-surface-tint` | `#18203A` | `#18241C` | |
| `--ui-text` | `#EEF2FF` | `#EEF5F0` | |
| `--ui-text-muted` | `#A5B0C9` | `#A3B5A9` | |
| `--ui-border` | `#7D8AB0` | `#7C8F82` | |
| `--ui-divider` | `#1E2740` | `#1C2A21` | |
| `--ui-brand` | `#93A7FF` | `#6EE7A0` | xanh lá sáng |
| `--ui-brand-hover` | `#B3C2FF` | `#8FF0B8` | |
| `--ui-brand-active` | `#6C85F7` | `#4CC97F` | |
| `--ui-brand-soft` | `#18203A` | `#14261A` | |
| `--ui-on-brand` | `#0B1020` | `#0B1020` | chữ tối trên nền sáng |
| `--ui-selected-bg` | `#1D2A52` | `#1D3A26` | |
| `--ui-selected-text` | `#C7D2FE` | `#B6F2CD` | |
| `--ui-sidebar-bg` | `#0D1322` | `#0B140F` | |
| `--ui-sidebar-text` | `#CDD5EA` | `#CFE0D5` | |
| `--ui-sidebar-hover-bg` | `#1B2440` | `#16241B` | |
| `--ui-sidebar-active-bg` | `#1D2A52` | `#1B3324` | |
| `--ui-sidebar-active-text` | `#C7D2FE` | `#B6F2CD` | |
| `--ui-sidebar-marker` | `#93A7FF` | `#6EE7A0` | |
| `--ui-card-border` | `#2A3552` | `#26382C` | |

Bốn màu ngữ nghĩa nền tối (`#86EFAC`, `#FDE68A`, `#FCA5A5`, `#93C5FD`) giữ nguyên — chúng đã đạt 10–15:1 trên nền mới.

---

## 6. Kết quả kiểm tương phản (đo bằng chính cổng của dự án)

Chạy `ops/check_ui_contrast.py` với tệp token ứng viên:

| Bản | Số cặp | Chữ nhỏ nhất | UI nhỏ nhất | Lỗi |
|---|---:|---:|---:|---:|
| Hiện tại (Chàm Đông) | 220 | 5,201:1 | 4,049:1 | 0 |
| **Đề xuất (VietHealth)** | 220 | **4,741:1** | **4,010:1** | **0** |
| Đề xuất — nền tối | 110 | 7,410:1 | 3,624:1 | 0 |

Cặp chữ mỏng nhất sau khi đổi: `--ui-link` trên `--ui-bg` = 4,74:1 (hiện tại 5,52:1). Vẫn trên ngưỡng 4,5 nhưng biên mỏng hơn — nếu muốn dư biên, dùng `#1D7437` cho `--ui-brand`/`--ui-link` (được 5,14:1), đánh đổi bằng màu nút đậm hơn logo một bậc.

---

## 7. Phạm vi tệp phải sửa

| Tệp | Thay đổi | Khối lượng |
|---|---|---|
| `src/static/css/ui_tokens.css` | 2 khối light/dark, ~45 giá trị | M |
| `src/static/manifest.json` | `background_color`, `theme_color` | S |
| `src/apps/portal/reporting_slides.py` | `TEAL`, `MINT`, `PAPER`, `LINE` (4 hằng) | S |
| `src/apps/portal/reporting_dashboard.py` | `BLUE`, `LIGHT` (2 hằng) | S |
| `src/apps/portal/test_report_palette.py` | chỉ docstring (test tự suy từ token) | S |
| `DESIGN.md` | mục Màu + mục Palette | S |
| `docs/UI_DESIGN_SYSTEM.md` | bảng tương phản sinh bằng `--write-doc` | S |
| `docs/PROJECT_WORK_LOG.md` | mục nhật ký đợt | S |
| `outputs/palette-viethealth-20261026/` | báo cáo + contact sheet | M |

**Không phải sửa:** 27 tệp CSS còn lại, toàn bộ template, toàn bộ JS. Không có một mã hex nào trong `src/templates/` và `src/static/js/`.

## 8. Việc KHÔNG đổi

- **`.hcns-paper`** trong `design_tokens.css` giữ palette tím đóng băng — đây là palette giấy/in HCNS cố ý tách khỏi giao diện, có ghi chú trong mã.
- **`print_forms.css`** (kể cả `--timesheet-print-weekend: #5B9BD5`) — bản in độc lập với màn hình.
- **`hcns_forms.css`** — xám giấy, không theo thương hiệu.
- **Logo và icon PWA** — đã đúng xanh `#279048`. Chỉ cân nhắc đổi nền icon PWA từ `#EFF6FF` (xanh dương nhạt) sang `#E9F5EE` cho khớp; việc này tách thành mục tùy chọn P5.

---

## 9. Sáu quyết định cần chủ dự án chốt

| # | Vấn đề | Phương án | Đề xuất |
|---|---|---|---|
| **D1** | Xanh thương hiệu trùng họ với xanh "thành công" | **A.** Giữ success `#067647` (rêu đậm) — khác sắc độ, luôn kèm icon+chữ theo DESIGN.md<br>**B.** Đổi success sang teal `#0F766E` để tách hẳn<br>**C.** Dùng chung màu thương hiệu cho success | **A** — không phát sinh việc, đúng quy tắc "trạng thái luôn có chữ + icon" |
| **D2** | Đỏ của logo có thành màu nguy hiểm? | **A.** Giữ `#B42318` (6,57:1) — an toàn, quen mắt<br>**B.** Dùng đúng đỏ logo `#CE181F` (5,56:1) — đồng bộ nhận diện<br>**C.** Trung gian `#C0171F` (6,21:1) | **B** — đúng yêu cầu "theo màu logo", vẫn dư ngưỡng |
| **D3** | Nền trung tính | **A.** Pha xanh lá `#EDF2EE`<br>**B.** Giữ xanh dương lạnh `#E7ECF4` | **A** — nền lạnh cạnh thương hiệu lá sẽ lệch tông |
| **D4** | Nền tối | **A.** Đen pha xanh lá `#08120D`<br>**B.** Giữ navy `#080C18` | **A** — navy hiện tại ngả xanh dương mạnh, chọi với xanh lá |
| **D5** | Màu biểu đồ thứ 4 (`--ui-chart-4`) | **A.** Giữ `--ui-chart-series-soft` = xanh đậm hơn (hai lát xanh trong donut 6 phần)<br>**B.** Đổi sang teal `#0F766E` để tách hẳn | **B** — donut "Cơ cấu loại hợp đồng" có 6 lát, hai xanh cạnh nhau sẽ khó đọc |
| **D6** | Biên tương phản của link | **A.** `#1F7A3D` (4,74:1) — sát logo nhất<br>**B.** `#1D7437` (5,14:1) — dư biên | **A** — 4,74 vẫn đạt; chỉ đổi sang B nếu muốn dư |

Trả lời gọn theo mẫu: `D1-A, D2-B, D3-A, D4-A, D5-B, D6-A`.

---

## 10. Phân đợt thực hiện

### P0 — Chốt quyết định và duyệt bằng mắt
- Mở `outputs/palette-viethealth-20261026/index.html`, xem cả nền sáng và nền tối, bấm đổi theme.
- Chốt D1–D6.
- **Cổng ra:** chủ dự án xác nhận bằng lời; không sửa mã.

### P1 — Đổi token (một tệp)
- Sửa 2 khối trong `ui_tokens.css` theo bảng mục 4–5 và các lựa chọn đã chốt.
- Chạy `ops/check_ui_contrast.py` — phải **0 lỗi**.
- **Cổng ra:** 220 cặp đạt; chưa commit.

### P2 — Đồng bộ nơi ngoài CSS
- `manifest.json`: `background_color` → `#EDF2EE`, `theme_color` → `#1F7A3D`.
- `reporting_slides.py`, `reporting_dashboard.py`: cập nhật hằng số theo token mới.
- Cập nhật docstring `test_report_palette.py`.
- Chạy `python manage.py test apps.portal.test_report_palette` — phải xanh (test này tự suy giá trị từ `ui_tokens.css`, đỏ nghĩa là quên đồng bộ).
- **Cổng ra:** báo cáo Excel/PowerPoint không còn màu indigo.

### P3 — Chạy ma trận cổng đo
Bắt buộc theo `AGENTS.md` vì đổi CSS dùng chung:

| Lệnh | Ngưỡng |
|---|---|
| `ops/run_tests.py --backend sqlite` | toàn bộ xanh |
| `ops/check_ui_contrast.py` | 0 lỗi |
| `ops/run_layout_alignment_audit.py` | 0 vi phạm ngoài `layout_waivers.json` |
| `ops/run_dashboard_layout_uat.py` | 0 lỗi (9 tài khoản × 6 bề rộng × 2 nền) |
| `ops/run_browser_uat.py --layout-only` | 0 lỗi |
| `ops/run_print_layout_uat.py` | 0 lỗi, PDF không đổi |
| `ops/run_asset_cache_uat.py` | 0 lỗi (đổi CSS không đổi tên tệp) |

- **Cổng ra:** toàn bộ 0 lỗi; chụp contact sheet 1756px và 390px, cả hai nền.

### P4 — Tài liệu và báo cáo
- `DESIGN.md`: thay mục palette Chàm Đông bằng VietHealth, ghi ngày và lý do.
- `docs/UI_DESIGN_SYSTEM.md`: chạy `check_ui_contrast.py --write-doc` để sinh lại bảng.
- Dựng `outputs/palette-viethealth-20261026/report.html` với ảnh trước/sau từng mô-đun.
- Ghi `docs/PROJECT_WORK_LOG.md`.
- **Cổng ra:** tài liệu không còn câu "palette Chàm Đông đang dùng" (trừ nhật ký lịch sử).

### P5 — Tùy chọn, tách riêng
- Đổi nền icon PWA `#EFF6FF` → `#E9F5EE`.
- Đưa logo VietHealth vào topbar (hiện topbar chỉ có chữ "IHRMS"; logo đang dùng ở trang đăng nhập và ba mẫu in).

---

## 11. Rủi ro và cách giảm

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| Quên đồng bộ bảng màu báo cáo Excel/PowerPoint | Trung bình | `test_report_palette.py` đỏ ngay; chạy ở P2 trước khi chạy ma trận |
| Donut 6 lát có hai màu xanh khó phân biệt | Trung bình | Quyết định D5 |
| Chữ trắng trên nút xanh lá không đạt AA | Cao nếu dùng mã logo gốc | Đã tách `#279048` (trang trí) khỏi `#1F7A3D` (nút); cổng đo chặn |
| Ảnh chụp tài liệu cũ vẫn màu indigo | Thấp | Chụp lại contact sheet ở P3, ghi rõ ngày |
| Cache trình duyệt giữ CSS cũ | Thấp | `?v=` đã có sẵn cho CSS in; các CSS khác dùng `asset` tag |
| Người dùng quen màu indigo thấy lạ | Thấp | Bản xem trước P0 để duyệt trước khi đổi |

---

## 12. Định nghĩa hoàn thành

- [ ] D1–D6 được chốt và ghi trong nhật ký.
- [ ] `ui_tokens.css` chỉ còn họ màu VietHealth; không còn mã indigo nào trong khối light/dark.
- [ ] `check_ui_contrast.py`: 220 cặp, 0 lỗi, chữ nhỏ nhất ≥ 4,5:1.
- [ ] `test_report_palette` xanh; báo cáo xuất ra đúng màu mới.
- [ ] Sáu cổng ở P3 đều 0 lỗi.
- [ ] Contact sheet 1756/390, sáng/tối, kèm ảnh trước/sau.
- [ ] `DESIGN.md` và `docs/UI_DESIGN_SYSTEM.md` đã cập nhật.
- [ ] Commit + push `origin/main`, CI xanh.

## 13. Ước lượng khối lượng

| Đợt | Khối lượng | Ghi chú |
|---|---|---|
| P0 | S | chỉ duyệt bằng mắt |
| P1 | S | một tệp, ~45 giá trị |
| P2 | S | 4 tệp, 6 hằng số |
| P3 | L | chiếm phần lớn thời gian: 6 cổng, 9 tài khoản × 6 bề rộng × 2 nền |
| P4 | M | tài liệu + báo cáo + ảnh |
| P5 | S | tùy chọn |

Điểm nghẽn là P3, không phải việc đổi màu. Đổi màu xong trong một lượt sửa; kiểm chứng mới là phần dài.
