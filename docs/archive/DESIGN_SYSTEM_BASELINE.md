# Baseline Đánh giá Hệ Thống Thiết Kế & Token CSS (IHRMS)

- **Số tệp CSS quét**: 20 tệp
- **Tổng dung lượng CSS**: 156.1 KB
- **Số lượng `!important`**: 82
- **Selector bám `.portal-app .ui-main`**: 165
- **Số selector chứa ID (`#...`)**: 1
- **Số bộ chọn `:has()`**: 22
- **Mã màu hex ngoài token**: 19
- **Số giá trị `font-size` phân biệt**: 38
- **Số giá trị `font-size` lệch thang**: 11 (1.0625rem, 1.375rem, 10pt, 10px, 11pt, 12pt, 14pt, 15pt, 16pt, 8pt...)
- **Số kiểu `padding` phân biệt**: 63
- **Số kiểu `gap` phân biệt**: 29
- **Số giá trị `border-radius` phân biệt**: 19
- **Thuộc tính `style="..."` trong template**: 17

## Đa định nghĩa thành phần nền (Single-source violations)

### Thành phần `.ui-button` (33 định nghĩa)
- `src/static/css/administration_ui.css:27 (.ui-administration form > .ui-button)`
- `src/static/css/administration_ui.css:27 (.ui-administration .ui-button)`
- `src/static/css/finance_ui.css:5 (.ui-finance .ui-finance-form .ui-button)`
- `src/static/css/finance_ui.css:21 (.ui-finance .ui-button)`
- `src/static/css/home_dashboard.css:48 (.home-dashboard .ui-button)`
- `src/static/css/home_dashboard.css:49 (.home-dashboard .ui-button--primary)`
- ... và 27 định nghĩa khác

### Thành phần `.ui-field` (58 định nghĩa)
- `src/static/css/administration_ui.css:12 (.ui-administration .ui-admin-form-inline > .ui-field)`
- `src/static/css/administration_ui.css:13 (.ui-administration .ui-field :is(input,select,textarea))`
- `src/static/css/administration_ui.css:14 (.ui-administration .ui-field textarea)`
- `src/static/css/administration_ui.css:14 (.ui-administration .ui-field input[type=file])`
- `src/static/css/administration_ui.css:19 (.ui-administration .ui-table .ui-field)`
- `src/static/css/headcount_report.css:7 (.headcount-report .ui-query-bar .ui-field label)`
- ... và 52 định nghĩa khác

### Thành phần `.ui-card` (20 định nghĩa)
- `src/static/css/administration_ui.css:21 (.ui-administration .ui-card)`
- `src/static/css/atoms_ui.css:11 (.portal-app .ui-main .ui-page .ui-card)`
- `src/static/css/atoms_ui.css:13 (.portal-app .ui-main .ui-page .ui-card > .ui-card-title:first-child)`
- `src/static/css/atoms_ui.css:14 (.portal-app .ui-main .ui-page .ui-card > .ui-scroll)`
- `src/static/css/atoms_ui.css:18 (.portal-app .ui-main .ui-page .ui-card.ui-kpi)`
- `src/static/css/finance_ui.css:18 (.ui-finance .ui-card-title)`
- ... và 14 định nghĩa khác

### Thành phần `.ui-badge` (14 định nghĩa)
- `src/static/css/administration_ui.css:6 (.ui-administration .ui-badge)`
- `src/static/css/administration_ui.css:6 (.ui-administration .ui-badge > span)`
- `src/static/css/atoms_ui.css:37 (.portal-app .ui-main .ui-page .ui-badge)`
- `src/static/css/home_dashboard.css:83 (.home-dashboard .ui-badge)`
- `src/static/css/home_dashboard.css:163 (.home-dashboard .home-decisions .ui-badge)`
- `src/static/css/personal_ui.css:33 (.ui-personal .timesheet-document .ui-badge)`
- ... và 8 định nghĩa khác

### Thành phần `.ui-table` (42 định nghĩa)
- `src/static/css/administration_ui.css:3 (.portal-app .ui-main .ui-page.ui-administration .ui-table)`
- `src/static/css/administration_ui.css:5 (.portal-app .ui-main .ui-page.ui-administration .ui-table:has(th:nth-child(7)))`
- `src/static/css/administration_ui.css:16 (.ui-administration .ui-table)`
- `src/static/css/administration_ui.css:17 (.ui-administration .ui-table :is(td,th))`
- `src/static/css/administration_ui.css:19 (.ui-administration .ui-table .ui-field)`
- `src/static/css/administration_ui.css:19 (.ui-administration .ui-table :is(th,td):last-child .ui-admin-form-inline)`
- ... và 36 định nghĩa khác

## Mục tiêu chất lượng sau chuẩn hóa (Target Thresholds)

| Chỉ số | Hiện tại (Baseline) | Ngưỡng mục tiêu |
|---|---|---|
| Giá trị font-size phân biệt | 38 | ≤ 9 (100% trong thang) |
| font-size lệch thang | 11 | 0 |
| `!important` | 82 | ≤ 10 (chú thích lý do) |
| Tiền tố `.portal-app .ui-main` | 165 | 0 (nhờ `@layer`) |
| Hex literal ngoài token | 19 | 0 |
| Định nghĩa nút `.ui-button` | 33 | 1 khối chuẩn duy nhất |
| Định nghĩa ô `.ui-field` | 58 | 1 khối chuẩn duy nhất |