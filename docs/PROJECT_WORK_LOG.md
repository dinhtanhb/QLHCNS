# Nhật ký công việc IHRMS

## 2026-10-12 — UI Giai đoạn 4: thành phần dùng chung và bốn trang mẫu

**Phạm vi/ủy quyền:** chủ dự án yêu cầu Giai đoạn 4 trước Giai đoạn 3, ưu tiên hơn điều kiện G2–3 trong prompt. G2 đã commit/push; G3 chưa triển khai. Chỉ `main`; đầu đợt fetch thành công, ahead/behind `0/0`. Giữ mục backup cũ đang dirty ngoài commit. Được commit riêng `ui: shared components`, không push/deploy. Không sửa model/migration/view/URL/field/logic/guard/dữ liệu thật; chưa rollout toàn app, không thêm dependency. MASTER/tokens > DESIGN > mặc định skill; không dùng UI Styling/shadcn.

**Đã đọc:** AGENTS, hướng dẫn review (FIX), nhật ký, ma trận RBAC, DESIGN/MASTER, UI_DESIGN_SYSTEM_PHASE1, tokens, partial phân trang và template/view các trang mẫu. Áp dụng bốn đích: `/portal/finance/periods/`, `/portal/reports/`, `/portal/hr/employees/`, `/portal/hr/employees/<pk>/`.

**Skill UI UX Pro Max:** dùng Python hệ thống chạy `C:/Users/dinht/.agents/skills/ui-ux-pro-max/scripts/search.py`, tất cả exit 0. Các query `--domain ux -n 1`: `data table keyboard focus` → Focus States chưa sát, retry `data table accessible` → Table Handling; `filter bar labels` → Chip Collection Reflow chưa sát, retry `filter form labels` → Form Labels; `form layout labels` → Form Labels; `modal confirm focus trap` và retry `modal dialog focus management` chỉ có Focus States, không có guidance modal cụ thể đã xác minh; dùng native dialog và thử Edge. `badge status color text` → Contextual Live Badge Updates chưa sát, retry `color not only badge` → Color Only; `toast notifications` → Toast Notifications; `pagination navigation` → Sticky Navigation chưa sát, retry `pagination previous next` không match; tái sử dụng partial và guidance chung có kiểm tra GET. `loading empty error states` → Empty States; `loading feedback` → Loading Indicators; `error summary validation` → Focusable Error Summary. Query stack `form modal table accessibility --stack html-tailwind -n 1` không match, retry `accessible modals` chỉ có Z-Index: giữ layer token, không thêm z-class tùy ý. Không coi exit 0 là match. Gợi ý timer toast bị giới hạn bởi MASTER: không tự đóng lỗi hoặc thông báo có hành động. Không thêm sort/library/API/notification payload. JSON kết quả ở TEMP.

**Tệp và cách triển khai:**

- `src/static/css/shared_components.css` opt-in `.ui-page`: h1 24px/700; card title 18px/600, padding/gap 24px; control/button 44px; field/fieldset/error summary; bảng 14px/600, padding12×16, sticky header/hover/focus/colgroup, số và thao tác căn phải; detail2 cột/1 mobile; KPI label14px, số24px, cùng vị trí khi nhãn2 dòng; badge/modal. Thêm token table/dialog/component-heading trong `ui_tokens.css`, không đổi palette. Chỉ bốn trang mẫu dùng layout mới.
- `src/templates/ui/` có page_header, field (manual/BoundField/select), error_summary, badge, empty_state, alert, kpi, detail_item, confirm_dialog. `ui_components.py` có ui_vnd/ui_date/ui_badge/ui_bound_field, không query. VND delegate floatformat0g giữ rounding hiển thị cũ; ngày dd/MM/yyyy, datetime aware theo timezone; input/query vẫn ISO, không đổi storage/calc.
- `src/apps/common/ui_status.py` là registry32 nhóm/118 status/condition, nhãn đúng choices, text+SVG+tone. Test đối chiếu mọi choices hiện hành. Draft/Open/Locked/Active/Cancelled/Resigned/Rejected/... giữ neutral khi chưa có ý nghĩa cảnh báo rõ. Attendance Absent/HalfDay, Contract Expired/Terminated, Candidate Rejected/Offer Declined... chưa tự suy mức nguy hiểm; chủ dự án có thể quyết tone ở G5. Code mới chưa rõ dùng neutral và nhãn fallback an toàn. Registry đầy đủ ở `docs/UI_SHARED_COMPONENTS_PHASE4.md`.
- `shared_components.js`: form opt-in `data-ui-form` kiểm tra native constraints, aria-invalid/describedby, lỗi cạnh field và summary/link/focus, giữ giá trị client; thông báo constraint bằng tiếng Việt, tránh lỗi trùng giữa number source/proxy. Confirm opt-in `data-ui-confirm`: native dialog + Tab/Shift+Tab trap, focus Quay lại, Escape/hủy/return focus, requestSubmit với đúng submitter. Mẫu HR ghi kỷ luật dùng confirm; action/method/names/CSRF/guard vẫn cũ. Tone danger mặc định cho thao tác nguy hiểm; duyệt có thể chọn brand qua `data-ui-confirm-tone="primary"`.
- Payroll có nhãn Tháng/Năm, nút không co, bảng width chủ động/badge/empty trong card. Report dùng KPI/card/table chung, giữ chart/label/bảng dữ liệu/export/query. HR list có label q, Áp dụng/Xóa lọc/count, rowaction native details giữ URL/guard, bảng cuộn có label/tabindex. HR detail chia nhóm DL2/1 cột, bảy form trong source có label/fieldset/error summary, giữ submitter/fields. `_pagination.html` chỉ bật mới với `standard=True` ở HR list; nhánh cũ giữ nguyên cho các trang khác. Base load CSS/JS chung; token asset phase4/serviceworker v8, HTML vẫn network-only.
- `docs/UI_SHARED_COMPONENTS_PHASE4.md` mô tả cách dùng từng component; `docs/ui_components_source.html` và generated `ui_components.html` là kitchen sink HTML tĩnh. `ops/render_ui_components.py` cấu hình render-only, không DB/.env/URL production. `ops/check_ui_shared_components.cjs` là Node stdlib/Edge checker, credential JSON giả ở TEMP, không in/ghi credential vào nguồn.

**Giữ nghiệp vụ/query:** CaptureQueriesContext trên DB giả trước/sau: Payroll13→13, Report99→99, HR list(q=giả)8→8, HR detail19→19. Không thêm query/view/context hoặc nới quyền. Parser đối chiếu render `git show HEAD` với cùng context: Payroll1form, Report1form, HRlist1form, HRdetail5form hiện có dữ liệu; action/method/tên field/submitter đều trùng. Hai form điều kiện khác trong source chỉ xuất hiện khi có hợp đồng. Report99 query là vấn đề có sẵn, không tối ưu backend ở đợt UI. Form view cũ redirect/message khi server lỗi vẫn giữ; helper chỉ render field errors nếu có bound form thật. Client invalid không POST/không mất giá trị, không persist dữ liệu HR ở localStorage.

**Ảnh và thử tương tác:** preview localhost8879 trên SQLite/media/email/logs riêng `C:/Users/dinht/AppData/Local/Temp/ihrms-ui-phase4-20261012`, toàn dữ liệu/tài khoản giả, M365 tắt và email locmem. Không dùng dữ liệu thật/admin từ ảnh người dùng. Before32 và after32 ảnh bốn trang×360/768/1024/1440×light/dark; PNG ngoài Git tại `<TEMP>/ihrms-ui-phase4-20261012/screenshots/`, browser JSON/log cùng thư mục. Sau thử POST đã phục hồi chỉ DB tạm từ fake baseline và seed lại26 nhân viên để ảnh trước/sau so cùng records. Có ảnh modal light/dark và kitchen360/1440×light/dark. Đã xem Payroll dark desktop, Report light desktop, HR list dark mobile và HR detail dark desktop; sau xem chỉnh căn row heading/actions/number và vị trí số KPI.32 after cases không page overflow.

`node ops/check_ui_shared_components.cjs <TEMP>/ihrms-ui-phase4-20261012/account.json` với `UI_TEST_THEME=light` rồi dark: SHARED_UI_EXIT=0 cả hai; sau chuẩn hóa message tiếng Việt đã rerun hai theme cuối, exit0. Pointer/keyboard kiểm tra invalid summary/link, range13 giữ dữ liệu/no POST, pagination q/page2, table tabindex, confirm trước POST, focus Quay lại, Tab/Shift+Tab, Escape/cancel no POST/return focus, confirm1POST với CSRF/discipline_type/discipline_date, requestSubmit giữ `next=hcns`. Lượt đầu native Tab thoát tới browser chrome, đã thêm trap và rerun đạt. Chỉ ghi record/email vào fixture giả. Evidence dialog được sao chép vào thư mục screenshots.

`node <TEMP>/ihrms-ui-phase4-20261012/kitchen_browser.cjs`: KITCHEN_EXIT=0;4 layouts không overflow,118 badge text/background≥4.5:1 cho cả hai theme. Kitchen demo confirm không gửi vào nghiệp vụ và Escape đóng được. Sửa wrap nhãn kỹ thuật dài trong tài liệu; lỗi regex escape của harness đo màu đã sửa. Đây không phải chứng nhận WCAG/compositing toàn app.

**Kiểm tra/gate:**

- `venv/Scripts/python.exe <TEMP>/ihrms-ui-phase4-20261012/parse.py`: tất cả template parse; check0issues; makemigrations --check --dry-run No changes detected, exit0. Không thêm migration.
- `npm run build:css`: exit0,206ms lượt đầu; dùng node_modules có sẵn. `node --check src/static/js/shared_components.js`, `node --check ops/check_ui_shared_components.cjs`: exit0.
- Focused `venv/Scripts/python.exe ops/run_tests.py --backend sqlite apps.common.tests_ui_components apps.portal.tests_shared_components apps.portal.tests_mobile apps.portal.tests_report_dashboard`:20tests/9.628s, OK/exit0 sau sửa hai lỗi test mới (fixture positional arg và thứ tự thuộc tính HTML).
- Corrected `venv/Scripts/python.exe ops/run_tests.py --backend sqlite apps.portal.tests.PortalSensitiveWorkflowTests.test_employee_action_menu_has_working_native_dropdown_markup apps.common.tests_ui_components apps.portal.tests_shared_components`:9tests/6.220s, OK/exit0. Giữ assertion details native, edit URL, không toggleMenu JS.
- Full SQLite lượt đầu432tests/452.745s fail1/skip7; SQL Server lượt đầu432tests/484.925s fail1/exit1 do assertion class dropdown cũ. Đã cập nhật sang ui-row-menu; đọc file exit riêng, không lấy exit wrapper Get-Content. Hai backend chạy lại tuần tự trên DB/media cô lập: SQLite432tests/453.037s, OK/skip7/exit0; SQL Server432tests/497.527s, OK/không skip/exit0, backend microsoft, DB test UUID riêng; runner đã hủy DB thử.
- `venv/Scripts/python.exe -m pip check`: No broken requirements found, exit0. `python ops/check_ui_contrast.py`:168cặp,0failures, min light text6.147/UI3.860; dark text5.599/UI3.805. Token contrast không chứng minh toàn app.
- `venv/Scripts/python.exe ops/run_tests.py --backend sqlite apps.common.tests_ui_components`:5tests/0.056s, OK/exit0 sau bổ sung assertion hidden field không sinh label; checkbox/radio giữ loại và kích thước riêng.
- `node --test src/frontend/ui_numbers.test.cjs src/frontend/theme.test.cjs`:5/5PASS. `git diff --check`: exit0; cảnh báo LF→CRLF ở generated Tailwind chỉ do checkout. Khi stage tệp mới phát hiện một trailing whitespace trong JS (diff trước stage chưa xét untracked); đã xóa và staged diff check lại exit0 trước amend commit của chính đợt này. Mỗi backend có4 RuntimeWarning VehicleBooking datetime thiếu timezone trong fixture; không có lỗi xoay log/PermissionError ở hai lượt cuối. Log Axes/validation ERROR thuộc ca negative. Warning ghi riêng, không vào diff UI.

**Biến thể Giai đoạn5 cần gộp (kiểm kê75 template có table/input/select, chưa đổi ở đợt này):**

- Bảng Tailwind thường (`finance_salary_list`, `finance_dependent_list`, `hr_contract_list`, `hr_candidate_list`, `asset_admin_list`, `procurement_request_list`): py2/pr4 hoặc px4/py3, caption/scope/colwidth/actions khác nhau → ui-table/card/scroll/colgroup/number/actions.
- Grid lương editable (`finance_payroll_run`): formid pf<pk>, inputformattribute, number proxy và lock/payroll guard → đổi UI giữ linePOST/field/locking.
- Ma trận bảng công (`timesheet_month`, `timesheet_approval_list`, `report_timesheet`), định biên/ngân sách (`report_headcount`, `report_budget`): nhiều cột/inline form/print → vùng cuộn cólabel/focus, header khôngche focus, giữ phép tính/in.
- Nhiều bảng report (`report_personnel_changes`4bảng, `report_hub`): caption/scope/colwidth/number chung.
- Form (`hr_employee_form`, `hr_contract_form`, `finance_tax_config`, `task_create`, `dispatch_create`, `leave_create`, `recruitment_create`): label/placeholder/width/padding còn khác → field/group/summary/một primary theo guard.
- Bộ lọc GET (`room_booking_list`, `vehicle_booking_list`, `office_incoming_list`, `office_outgoing_list`, `document_list`, `asset_list`): giữ name/query → filterbar/count/reset/pagination.
- Action details/menu/custom buttons và badge if-status của Leave/Recruitment/Dispatch/Payroll/Asset → row-menu/button44, confirmPOST/CSRF/guard, ui_badge đúng family.
- Profile/chi tiết (`profile`, `dispatch_detail`, `task_detail`, `hr_candidate_detail`): grid2/3 cột label-value → detail2 desktop/1 mobile/cardgroups.
- HCNS editor (`document/hcns/draft`, hcns-table-editor): có chrome riêng; có thể reuse control/error, không recolor hoặc re-layout paper.
- Print (`inventory_session_print`, `disposal_*_print`, HCNS document/appointment): layout-authoritative, không áp ui-table vào paper/in khi chưa đối chiếu mẫu.
- `_pagination.html` legacy và base ui-alert: opt-in từng loại, giữ query/role/guard, không auto-dismiss lỗi.

**Bàn giao/việc còn mở:** chưa UAT Edge trên dữ liệu thật/screen reader/in vật lý/mọi trạng thái; không chứng nhận WCAG. Chủ dự án xem bốn trang/kitchen sink/status mapping trước quyết định push. Không push/deploy; các gate đã đạt. Rà privacy/scope38 tệp không phát hiện mẫu credential mới, DB/media/tệp thật; không có model/view/migration/config trong diff. Tạo commit `ui: shared components` trên main (SHA xem Git log để tránh tự tham chiếu), không push/deploy. Preview giả tắt sau kiểm tra, ảnh/log giữ ngoài Git. Giữ mục backup cũ ngoài index. G3 chưa làm theo thứ tự đã chọn.

## 2026-10-12 — UI: định dạng số Việt Nam, sửa dark mode, Trung tâm và control thống nhất

**Yêu cầu/phạm vi:** tiếp nhận bốn phản hồi UI và ảnh của chủ dự án; chủ dự án chọn số Việt Nam `5.000.000`, `0,07`. FIX phần giao diện, số hiển thị và nhãn nguồn, chỉ `main`; đầu đợt branch main, fetch origin/main thành công, ahead/behind 8/0. Giữ nguyên mục backup đang dirty trong log. Không thay quyền, URL/field name, cách tính hoặc dữ liệu nghiệp vụ. Sau kiểm tra, chủ dự án yêu cầu rõ commit và push trước Giai đoạn3; quyền push này thay chỉ dẫn không push trong prompt chung đính kèm. Không deploy.

**Skill:** đọc UI UX Pro Max tại `C:/Users/dinht/.agents/skills/ui-ux-pro-max/SKILL.md`, DESIGN và MASTER; không UI Styling/shadcn. `python C:/Users/dinht/.agents/skills/ui-ux-pro-max/scripts/search.py "form input consistency" --domain ux -n 1` → Input Types; `"color contrast dark" --domain ux -n 1` → Color Contrast; exit 0. Giữ native number để validation/dữ liệu chuẩn, thêm lớp hiển thị local; không thêm dependency.

**Đã sửa:**

- `src/apps/common/number_format.py`, builtin filter `common/templatetags/ui_numbers.py`, cấu hình template builtin và NUMBER_GROUPING=3: số hiển thị Việt Nam, Decimal chính xác, không dùng binary float để parse số phân nhóm. Bổ sung filter ở phần text hiển thị các template; floatformat có `g` để phân nhóm. Các thuộc tính input/URL/JSON/CSS và năm/tháng/mã giữ dạng máy; `floatformat:u` cho numeric input value. `reporting_dashboard.py`, `payroll/payslip_pdf.py`, chuỗi `__str__` payroll và dung lượng upload trong thông báo đổi separator hiển thị; không đổi phép tính hoặc dữ liệu numeric Excel. HCNS rendering số Việt Nam đã có, giữ nguyên.
- `src/static/js/ui_numbers.js`: proxy text/inputmode decimal hiển thị Việt Nam, native input giữ name/min/max/step/required và POST chuẩn. Hỗ trợ readonly/disabled ban đầu, reset, dòng động, nhập số âm/0/lẻ, label liên kết, lỗi validation; từ chối sai phân nhóm `12.34`. Không chuyển trường năm/tháng. Hook reference-fill trong `hcns_forms.js` cập nhật proxy khi điền từ nguồn; tăng cache version JS. Native source ẩn hình thức ở tọa độ fixed để không tạo overflow từ bảng cuộn.
- `ui_controls.css`, adapter Admin: input/select một dòng 44px, nút min44px/14px/bo8px/padding token, flex wrap/gap, không co nút; textarea/checkbox/radio giữ loại riêng. Form kỳ lương cân hàng desktop, mobile wrap. Bảng có header không bẻ từng ký tự và cuộn vùng riêng. File name dài wrap riêng.
- Dark mode: CSS HCNS editor/catalog được token hóa ngay nguồn; selector đủ ưu tiên cho editor/label/table/control, không còn nền trắng với chữ sáng. `ui_controls.css` load sau page CSS trong head; selector thắng stylesheet HCNS ở body. Surface báo cáo/card/nút phụ dùng token, không glow. Tăng cache-busting page CSS/JS và service-worker v7 + precache control/number assets; lỗi ảnh báo cáo còn palette cũ nghi do cache, ảnh nguồn hiện hành sau refresh đã được kiểm chứng. Không khẳng định đã kiểm tra cache trên trình duyệt thật của chủ dự án.
- “công ty” → “Trung tâm” trong toàn nguồn `.py/.html/.js/.json` hiện hành: nhãn portal, Admin verbose_name/help_text/choice labels, thông báo, seed/fixture và blank reference text. Giữ identifiers như company_email/CompanyKPI/CompanyMedia/Company choice code, không đổi dữ liệu đã lưu, không sửa migration lịch sử hay file tham khảo Word/Excel gốc.
- Metadata migrations `hrm/0006`, `kpi/0002`, `m365/0003`, `office/0007`, `planning/0002` để model label khớp state. `sqlmigrate` trên cấu hình SQLite tạm: không ALTER/CREATE/DROP TABLE, UPDATE/DELETE cho cả năm migration. Không migrate DB nghiệp vụ; test/preview áp dụng trên DB dùng một lần.
- DESIGN và MASTER ghi quy chuẩn số/control đã triển khai; không đổi bộ token brand.

**Tái hiện/ảnh/bằng chứng:** preview tại localhost:8878 trên SQLite riêng `C:/Users/dinht/AppData/Local/Temp/ihrms-ui-2c-20261012/preview.sqlite3`, tài khoản/nhân sự/ứng viên/lương giả, media/email/logs riêng, M365 tắt. Không dùng admin/dữ liệu thật trong ảnh user để chạy POST. Edge headless CDP, cache/service worker bypass; `visual_browser.cjs` cùng thư mục TEMP: bảy trang Trang chủ, Báo cáo điều hành, Kỳ lương, Nhân viên, Thang lương HCNS, Hoạt động dự án, Thuế/BH ×360/1440×light/dark. Không page overflow; thang lương editor min44px và màu dark neutral, số raw/display khớp. Nhập `5.123.456,07` → FormData `5123456.07` chính xác; malformed grouping từ chối rồi sửa hợp lệ; năm native không nhóm; actual POST xem trước trả lại và hiển thị đúng `5.123.456,07`. Form Admin lương `.app-main` (markup AdminLTE hiện hành, không dùng content-wrapper cũ) có proxy số/control44px; sau xem ảnh phát hiện nền app-main và Select2 còn trắng, đã sửa selector ưu tiên và kiểm tra lại main/Select2 background/text ở hai theme/hai độ rộng, VISUAL_EXIT=0. Sidebar pointer/keyboard/collapse/drawer/Escape/reduced-motion giữ hoạt động. Màu paper HCNS khớp baseline 2b, CSS từ `.hcns-paper` tới cuối file giữ nguyên. 39 ảnh PNG (28 trang portal, 4 Admin lương, 5 sidebar, 2 chart-detail) tại `<TEMP>/ihrms-ui-2c-20261012/screenshots/`; JSON `visual-report.json`. Đã xem trực quan thang lương dark desktop, báo cáo dark desktop, hoạt động dark mobile và kỳ lương light desktop; sau xem đã sửa wrap tiêu đề bảng mobile và chụp lại.

`venv/Scripts/python.exe <TEMP>/ihrms-ui-2c-20261012/smoke_pages.py`: superuser giả GET 43 đích sidebar, không 4xx/5xx; đây không thay cho review guard mọi role. Scan nguồn hiện hành `.py/.html/.js/.json` (trừ migration lịch sử) không còn `công ty`. Audit Edge text render từ 43 URL ×2theme =86 lượt/2196 mẫu text, tìm3 nút trắng trên nền sáng dark (In bảng công, Lọc công văn đến/đi); đã sửa adapter nút xám và audit lại0 mẫu dưới ngưỡng. Script `audit_browser.cjs`, kết quả `rendered-contrast.json` trong TEMP. Phép đo leaf text/ancestor background, bỏ paper/SVG/hidden và không đo mọi compositing/ảnh/focus/state: không chứng nhận WCAG.

**Kiểm tra:**

- `npm run build:css`: exit0 (117ms lượt cuối), node_modules hiện có, không install.
- `node --test src/frontend/ui_numbers.test.cjs src/frontend/theme.test.cjs`: 5/5 PASS. Lượt đầu theme test fail3 vì fixture cũ thiếu matchMedia; cập nhật fixture, rerun đạt. Test số gồm Decimal digit round-trip lớn, âm/0/lẻ, phân nhóm sai.
- `venv/Scripts/python.exe ops/run_tests.py --backend sqlite apps.common.tests_ui_numbers apps.portal.tests_app_shell apps.document.tests_hcns`: 23 tests, 25.293s, OK exit0.
- Focused sau sửa expectation version CSS: `venv/Scripts/python.exe ops/run_tests.py --backend sqlite apps.common.tests_ui_numbers apps.portal.tests_report_dashboard apps.portal.tests.PortalSensitiveWorkflowTests.test_project_task_menu_is_listed_under_project_activities`: 8 tests, 5.731s, OK exit0.
- `venv/Scripts/python.exe <TEMP>/ihrms-ui-2c-20261012/parse_templates.py`: parsed89 templates; `makemigrations --check --dry-run` No changes detected. System check no issues.
- `venv/Scripts/python.exe -m pip check`: No broken requirements found. `python ops/check_ui_contrast.py`:168 cặp,0 failures, min light text6.147/UI3.860, dark text5.599/UI3.805. Token đo không chứng minh cả app đạt WCAG.
- `venv/Scripts/python.exe ops/run_tests.py --backend sqlite apps.common` sau chuẩn hóa thông báo upload:5 tests/0.032s,OK/exit0.
- `venv/Scripts/python.exe ops/run_tests.py --backend sqlite apps.common.tests_ui_numbers`:2 tests/0.003s,OK/exit0; thêm assertion upload1,5MB vượt ngưỡng1MB trong cùng regression số, không ghi tệp.
- `git diff --check`: exit0, warning Git LF→CRLF ở generated Tailwind ghi riêng.
- Lượt full SQLite đầu:424 tests/436.136s, fail2/skip7 vì expectation version home/report CSS cũ; đã cập nhật theo assetversion2c. SQL Server lượt đầu:424 tests/440.883s, fail2/exit1 do cùng expectation version CSS cũ; trước đó đọc nhầm exit0 của lệnh tổng hợp Get-Content, đã đính chính cho chủ dự án. Full SQLite chạy lại:424 tests/438.248s, OK/skip7/exit0; SQL Server chạy lại:424 tests/457.389s,OK/không skip/exit0; backend microsoft, DB test UUID riêng, runner đã Destroying test database. Hai backend chạy tuần tự. Mỗi backend có4 RuntimeWarning VehicleBooking naive datetime; không test failure ở lượt cuối.

**Warning/giới hạn:** bốn RuntimeWarning VehicleBooking naive datetime trong fixture; Axes warning/login-lockout/validation errors thuộc ca cố ý từ chối, đánh giá theo runner. Chưa UAT Edge tương tác trên dữ liệu thật, chưa kiểm toàn bộ trạng thái form/role hoặc in vật lý; không tuyên bố WCAG toàn app. Nội dung giấy HCNS vẫn nền trắng/chữ đen theo mẫu, khác chrome editor dark. Dữ liệu lịch sử trong DB vẫn có thể chứa “công ty”; không tự rewrite.

**Bàn giao:** ngày12/10/2026 chủ dự án cho phép commit/push bản sửa hiện tại trên main trước Giai đoạn3. Rà diff, xác nhận source/metadata migration chỉ thay hiển thị; privacy/path scan127 tệp không chứa DB/media/tệp thật hoặc mẫu credential mới; git diff --check exit0. Commit mã `19e1bb037d3a4b28658e9b80587119dd2346355d` — `fix(ui): unify number formats dark mode and controls`; `git push origin main` exit0, remote main từ d1af082 lên commit này (gồm8 commit UI đang chờ trước đó). `git ls-remote --heads origin refs/heads/main` xác nhận SHA trùng HEAD. Kết quả này được ghi trong commit tài liệu bàn giao kế tiếp; SHA cuối xem Git log. Chưa bắt đầu sửa Giai đoạn3. Không deploy. Preview giả đã tắt sau kiểm tra; ảnh/log giữ trong TEMP để xem lại. Mục backup cũ vẫn nguyên trong working tree.

**Chủ dự án cần làm sau bàn giao:** khởi động lại ứng dụng để nạp template builtin/metadata label; ở môi trường được phép triển khai chạy `venv\Scripts\python.exe src\manage.py migrate` cho năm migration metadata theo quy trình backup hiện có (Codex chưa chạy DB nghiệp vụ), rồi Ctrl+F5 để tải assets v2c/serviceworker7 và kiểm tra các trang đã chụp. Nếu bản in giấy có yêu cầu bố cục mới, cần đối chiếu riêng với mẫu gốc; đợt này không recolor/re-layout giấy.

## 2026-10-12 — UI/UX Đợt 2b: menu, màu light/dark và quy chuẩn Giai đoạn 4

**Phạm vi:** A–C theo phản hồi chủ dự án; D chỉ tài liệu. Skill UI UX Pro Max; không UI Styling/shadcn, không dependency mới. Chỉ `main`, đầu đợt fetch `origin/main` thành công, ahead/behind 4/0. Giữ nguyên DESIGN mới được chủ dự án cung cấp (được yêu cầu commit ở nhóm docs) và mục backup chưa commit trong log (không đưa vào commit đợt này). Không sửa model/migration/view/URL/field/guard, không dữ liệu thật, không push/deploy.

**Tệp thay đổi:** `DESIGN.md`, `design-system/MASTER.md`, `docs/PROJECT_WORK_LOG.md`, `docs/UI_DESIGN_SYSTEM_PHASE1.md`, `ops/check_ui_contrast.py`, `ops/check_ui_menu_links.cjs`, `src/apps/activity/templates/activity/dashboard.html`, `src/apps/portal/templates/portal/dashboard.html`, `src/apps/portal/templates/portal/finance_period_list.html`, `src/apps/portal/templates/portal/leave_list.html`, `src/apps/portal/templates/portal/report_hub.html`, `src/apps/portal/tests_app_shell.py`, `src/apps/portal/tests_mobile.py`, `src/frontend/tailwind.input.css`, `src/static/css/admin.css`, `src/static/css/app_shell.css`, `src/static/css/design_tokens.css`, `src/static/css/hcns_forms.css`, `src/static/css/home_dashboard.css`, `src/static/css/ihrms.css`, `src/static/css/report_dashboard.css`, `src/static/css/tailwind.css`, `src/static/css/theme.css`, `src/static/css/ui_tokens.css`, `src/static/js/app_shell.js`, `src/static/js/service-worker.js`, `src/static/js/theme.js`, `src/templates/base.html`, `src/templates/reporting/dashboard.html`.

**A — điều hướng:** bỏ SVG mũi tên ở toàn bộ link con; đường nối dọc, chữ thụt vào và active đậm. Hover/focus-visible có nền nhạt, marker 3px, viền trang trí 1px và bóng card; pointer không có keyboard ring. Nhóm đang thu gọn mở lại sidebar khi kích hoạt để link con dạng chữ không thành vùng trống. Giữ chevron, aria-current, drawer/keyboard/reduced-motion. Ngoại lệ hover được ghi trong DESIGN và MASTER.

**B — màu:** ánh xạ palette Tailwind/alias cũ về token; CSS admin, theme, dashboard, report, HCNS editor dùng surface/border slate. KPI mặc định màu chữ; warning/danger có nhãn và chỉ khi > 0. Bốn chuỗi hires/departures/transfers/promotions có token phân biệt, chú giải chữ và bảng số liệu. Track trung tính; `data-empty=true` không vẽ thanh. Tăng phiên bản assets/service worker để tránh CSS/JS cache cũ. Chỉnh nhỏ form kỳ lương cho phép wrap và giữ nút không co chữ. `npm run build:css` (node_modules hiện có), exit 0; không cài package. Giữ palette giấy/in trước đợt 2b tại `.hcns-paper` và `@media print`.

**C — tái hiện trước sửa và phân loại:** dùng SQLite/media/email/logs tạm, 8 ca Edge gồm sáu role yêu cầu và superuser có/không staff; các tài khoản không gắn employee. Href thực tế luôn `/admin/`, `/reports/`, `/portal/reports/`. Trước sửa, link user menu hiển thị nhưng click bằng Input.dispatchMouseEvent không tạo request document, URL vẫn `/portal/`, dropdown bị ẩn; sidebar report hoạt động. HTTP trực tiếp đúng guard bên dưới. Đối chiếu `git show 76021d8:src/templates/base.html` trước G2: đóng ngoài click, chưa có focusout microtask. G2 `app_shell.js` queueMicrotask đóng popup giữa blur/focus Chromium, làm mất click. Đã sửa (a) bằng relatedTarget và defer macrotask khi null; không đổi href/guard. Bảng HTTP đầu tiên (302 được thu từ redirectResponse, không nhầm final 200):

| Vai trò, chưa gắn hồ sơ | Staff | Trực tiếp admin / Excel / điều hành | Click trước sửa | Click sau sửa |
|---|---|---|---|---|
| EMPLOYEE | Không | 302 / 403 / 302 | Cả 3 ẩn | Cả 3 ẩn |
| DEPT_MANAGER | Không | 302 / 403 / 302 | Cả 3 ẩn | Cả 3 ẩn |
| HR_OFFICER | Không | 302 / 200 / 302 | Cả 3 ẩn | Cả 3 ẩn |
| HR_MANAGER | Không | 302 / 200 / 200 | Admin, Excel: không request; điều hành 200 | 302 / 200 / 200 |
| DIRECTOR | Không | 302 / 200 / 200 | Admin, Excel: không request; điều hành 200 | 302 / 200 / 200 |
| SYS_ADMIN | Có | 200 / 200 / 302 | Admin, Excel: không request; điều hành ẩn | 200 / 200 / ẩn |
| superuser | Có | 200 / 200 / 200 | Admin, Excel: không request; điều hành 200 | 200 / 200 / 200 |
| superuser | Không | 302 / 200 / 200 | Admin, Excel: không request; điều hành 200 | 302 / 200 / 200 |

FINANCE_OFFICER bổ sung (HTTP trực tiếp): 302 / 200 / 302. Không đánh giá quyền dựa vào screenshot. (b) khác biệt sẵn có: HR_OFFICER được `/reports/` nhưng guard menu `view_admin_menu` không hiện; SYS_ADMIN được `/reports/` nhưng `view_reports` chặn `/portal/reports/` và link sidebar ẩn. (c) Django Admin yêu cầu active + is_staff: HR_MANAGER/DIRECTOR/superuser không staff được chuyển `/admin/login/?next=/admin/`. Guard `src/apps/reporting/views.py::_can_view_reports` dùng `view_report_center`; `src/apps/portal/views/reports_planning.py::report_hub` dùng `view_reports` và redirect khi không có quyền; ma trận `src/apps/security/permissions.py` không thay đổi. Đề xuất tối thiểu để chủ dự án quyết riêng (F-08/F-09): menu Excel theo `has_permission(user, "view_report_center")`, menu Admin theo `user.is_active and user.is_staff`, giữ nguyên view guard. Nếu muốn SYS_ADMIN có báo cáo điều hành, cần quyết định thêm role đó vào `view_reports` ở đợt quyền riêng; UI không tự nới quyền. Chỉ cấp is_staff cho tài khoản thực sự được phép vào Admin. Chưa áp dụng các đề xuất này, chưa ẩn/vô hiệu link ở đợt UI. Guard hiện tại: Excel `return has_permission(request.user, "view_report_center")`, không có quyền trả `HttpResponseForbidden`; điều hành `return has_permission(request.user, "view_reports")`, không có quyền `messages.error(...)` rồi `redirect("portal:dashboard")`.

**Test hồi quy C:** `test_unlinked_account_menu_targets_keep_existing_http_permissions` trong `src/apps/portal/tests_app_shell.py` kiểm tra direct HTTP + guard menu sáu role và superuser. `venv/Scripts/python.exe ops/run_tests.py --backend sqlite apps.portal.tests_app_shell`: 5 tests, 34.383s, OK, exit 0. `node ops/check_ui_menu_links.cjs <TEMP>/ihrms-ui-phase2b-20261012/menu-cases.json`: cả 8 ca PASS, MENU_CLICK_EXIT=0; dùng Edge headless click tọa độ thật, cache tắt và HTTP redirectResponse. Input thông tin đăng nhập giả nằm ngoài Git; script không in credential.

**Skill local:** `python C:/Users/dinht/.agents/skills/ui-ux-pro-max/scripts/search.py "focus visible keyboard pointer" --domain ux -n 1` → Focus States; `"navigation hover feedback" --domain ux -n 1` → Hover States. Query `"chart color labels comparison" --domain chart -n 1` trả Radar chưa sát, retry `"compare categories" --domain chart -n 1` → Compare Categories/Grouped Bar. Chỉ dùng hướng dẫn focus/feedback và không dựa riêng vào màu; giữ chart/bảng hiện có, không thêm sort/library/logic từ gợi ý skill. Các lệnh exit 0.

**Đo và ảnh:** `python ops/check_ui_contrast.py --write-doc`: 168 cặp, 0 failures; light 84 cặp, min text 6.147:1/UI 3.860:1; dark 84 cặp, min text 5.599:1/UI 3.805:1. Bảng đầy đủ trong `docs/UI_DESIGN_SYSTEM_PHASE1.md`, gồm hover/active chữ ≥4.5:1 cả hai theme. Cụ thể hover và active cùng cặp: light `#4c1d95` / `#ede9fe` = 9.227:1; dark `#ddd6fe` / `#2e1065` = 10.974:1. Viền hover mờ/bóng chỉ trang trí, không tuyên bố đạt 3:1. `node <TEMP>/ihrms-ui-phase2b-20261012/visual_browser.cjs`: VISUAL_EXIT=0, 16 ảnh bốn trang home/executive-report/payroll/hr-list × 360/1440 × light/dark; thêm ảnh sidebar hover/focus. Kiểm tra không overflow, bốn màu + bảng dữ liệu, KPI 0 neutral, thanh 0 ẩn, toàn bộ `.ui-nav-panel .ui-nav-link` không có SVG (assert tập link không rỗng; đã sửa selector test cũ trước chạy cuối), pointer không focus-visible/bàn phím có focus-visible, collapsed submenu, drawer/Escape, reduced-motion=0ms. So sánh màu `.hcns-paper` light/dark với browser-report trước đợt 2b: khớp. Đối chiếu `git show 42ca287:src/static/css/hcns_forms.css`: phần CSS từ `.hcns-paper` tới adapter screen và phần `@page`/print giữ nguyên sau chuẩn hóa newline; scan RGB mở rộng trước sửa không có biến thể tím ngoài bảng gốc. Scan cuối có 140 dòng khớp, chỉ tại ui_tokens/design_tokens (nguồn chuẩn, alias mapping và palette giấy/in). Đã xem trực quan ảnh report dark, home mobile dark, payroll mobile light và sidebar hover dark, payroll desktop dark, HR list mobile dark và home desktop light. Ảnh/bằng chứng ở `C:/Users/dinht/AppData/Local/Temp/ihrms-ui-phase2b-20261012/screenshots/`, JSON/log cùng thư mục. Không đưa dữ liệu giả/DB/profile vào Git.

**Kiểm tra cuối đợt:**

- `venv/Scripts/python.exe -m pip check`: No broken requirements found, exit 0.
- `venv/Scripts/python.exe <TEMP>/ihrms-ui-phase2b-20261012/django_checks.py`: chạy `check` và `makemigrations --check --dry-run` trên cấu hình SQLite/media/logs tạm; System check no issues; No changes detected; exit 0.
- `git diff --check`: exit 0 sau bỏ blank EOF; cảnh báo Git LF→CRLF chỉ do cấu hình checkout. `node --check ops/check_ui_menu_links.cjs`, `node --check src/static/js/app_shell.js`, `node --check src/static/js/theme.js`: exit 0.
- `venv/Scripts/python.exe ops/run_tests.py --backend sqlite`: 422 tests trong 401.384s, OK (skipped=7), exit 0, DB/media cô lập. Bảy ca bỏ qua thuộc kiểm tra row locking/concurrency chỉ chạy trên SQL Server.
- `venv/Scripts/python.exe ops/run_tests.py --backend sqlserver`: 422 tests trong 402.418s, OK, không skip, exit 0; backend microsoft, DB test UUID riêng, runner đã Destroying test database. Chạy tuần tự sau SQLite.
- Browser final: `node ops/check_ui_menu_links.cjs <TEMP>/ihrms-ui-phase2b-20261012/menu-cases.json` và `node <TEMP>/ihrms-ui-phase2b-20261012/visual_browser.cjs`: exit 0, 8 ca pointer PASS và VISUAL_EXIT=0. Có 23 ảnh (16 ảnh trang, 5 sidebar, 2 chi tiết chart mobile).

**Warning riêng:** SQLite có 4 RuntimeWarning DateTimeField VehicleBooking.start_time/end_time nhận naive datetime trong fixture 05/10/2026, không có test failure. Log Axes WARNING/ERROR từ ca cố ý login/validation bị từ chối; không tính là failure khi runner OK. PowerShell NativeCommandError quanh dòng Creating test database là wrapper stderr, đánh giá theo exit của Python và runner, không lấy nhãn đó làm kết luận lỗi. SQL Server có cùng 4 RuntimeWarning naive datetime VehicleBooking; không có failure, không sửa fixture/backend ở đợt UI.

**D — tài liệu:** chép mẫu bố cục chuẩn (h1 24px/700, card 18px/600/padding24, control44px, bảng14px/600/padding12×16, empty/detail) vào DESIGN và MASTER; chưa rollout toàn app.

**Bảng kiểm kê màu:** 203 dòng khớp trước sửa trong 11 tệp; quét CSS/template/JS gồm inline/SVG/canvas, các hex được yêu cầu, biến `--ihrms-*` và RGB/RGBA tím. Dòng trong bảng là dòng nguồn trước đợt 2b; file generated được truy về source. Raw brand chỉ giữ ở nguồn chuẩn ui_tokens (bắt buộc có giá trị gốc), không phân tán. Legacy alias định nghĩa ở root chỉ trỏ `--ui-*`; raw palette cũ chỉ giữ cho giấy/in. Scan sau sửa không còn mã tím/legacy call trong source màn hình (ngoài định nghĩa token/alias); bảng sau đây liệt kê từng dòng gốc.

| Tệp | Dòng trước sửa | Giá trị trước sửa | Token thay thế / lý do giữ |
|---|---:|---|---|
| `src/frontend/tailwind.input.css` | 9 | `#f5f3ff` | `--ui-bg` |
| `src/frontend/tailwind.input.css` | 10 | `#ede9fe` | `--ui-surface-raised` |
| `src/frontend/tailwind.input.css` | 11 | `#ddd6fe` | `--ui-divider` |
| `src/frontend/tailwind.input.css` | 12 | `#c4b5fd` | `--ui-border` |
| `src/frontend/tailwind.input.css` | 15 | `#4c1d95` | `--ui-text-muted` |
| `src/frontend/tailwind.input.css` | 16 | `#4c1d95` | `--ui-text` |
| `src/frontend/tailwind.input.css` | 17 | `#2e1065` | `--ui-text` |
| `src/frontend/tailwind.input.css` | 18 | `#2e1065` | `--ui-text` |
| `src/frontend/tailwind.input.css` | 19 | `#f5f3ff` | `--ui-bg` |
| `src/frontend/tailwind.input.css` | 20 | `#ede9fe` | `--ui-surface-raised` |
| `src/frontend/tailwind.input.css` | 21 | `#ddd6fe` | `--ui-divider` |
| `src/frontend/tailwind.input.css` | 22 | `#c4b5fd` | `--ui-border` |
| `src/frontend/tailwind.input.css` | 25 | `#4c1d95` | `--ui-text-muted` |
| `src/frontend/tailwind.input.css` | 26 | `#4c1d95` | `--ui-text` |
| `src/frontend/tailwind.input.css` | 27 | `#2e1065` | `--ui-text` |
| `src/frontend/tailwind.input.css` | 28 | `#2e1065` | `--ui-text` |
| `src/frontend/tailwind.input.css` | 29 | `#f5f3ff` | `--ui-surface-raised` |
| `src/frontend/tailwind.input.css` | 30 | `#ede9fe` | `--ui-surface-raised` |
| `src/frontend/tailwind.input.css` | 31 | `#ddd6fe` | `--ui-border` |
| `src/frontend/tailwind.input.css` | 32 | `#c4b5fd` | `--ui-brand` |
| `src/frontend/tailwind.input.css` | 33 | `#a78bfa` | `--ui-brand` |
| `src/frontend/tailwind.input.css` | 34 | `#8b5cf6` | `--ui-brand` |
| `src/frontend/tailwind.input.css` | 35 | `#6d28d9` | `--ui-brand` |
| `src/frontend/tailwind.input.css` | 36 | `#5b21b6` | `--ui-brand` |
| `src/frontend/tailwind.input.css` | 37 | `#4c1d95` | `--ui-brand-hover` |
| `src/frontend/tailwind.input.css` | 38 | `#2e1065` | `--ui-brand-active` |
| `src/frontend/tailwind.input.css` | 39 | `#f5f3ff` | `--ui-surface-raised` |
| `src/frontend/tailwind.input.css` | 40 | `#ede9fe` | `--ui-surface-raised` |
| `src/frontend/tailwind.input.css` | 41 | `#ddd6fe` | `--ui-border` |
| `src/frontend/tailwind.input.css` | 42 | `#c4b5fd` | `--ui-brand` |
| `src/frontend/tailwind.input.css` | 43 | `#a78bfa` | `--ui-brand` |
| `src/frontend/tailwind.input.css` | 44 | `#8b5cf6` | `--ui-brand` |
| `src/frontend/tailwind.input.css` | 45 | `#6d28d9` | `--ui-brand` |
| `src/frontend/tailwind.input.css` | 46 | `#5b21b6` | `--ui-brand` |
| `src/frontend/tailwind.input.css` | 47 | `#4c1d95` | `--ui-brand-hover` |
| `src/frontend/tailwind.input.css` | 48 | `#2e1065` | `--ui-brand-active` |
| `src/frontend/tailwind.input.css` | 49 | `rgb(76 29 149 / .08)` | `--ui-bg`, `--ui-surface-raised`, `--ui-divider`, `--ui-border`, `--ui-text-muted`, `--ui-text`, `--ui-brand`, `--ui-brand-hover`, `--ui-brand-active`, `--ui-shadow-card` |
| `src/static/css/admin.css` | 12 | `#4c1d95` | `--ui-brand` |
| `src/static/css/admin.css` | 13 | `#4c1d95` | `--ui-brand` |
| `src/static/css/admin.css` | 33 | `#5b21b6` | `--ui-brand-hover`, `--ui-surface` |
| `src/static/css/admin.css` | 34 | `#5b21b6` | `--ui-brand-hover`, `--ui-surface` |
| `src/static/css/admin.css` | 45 | `--ihrms-text` | `--ui-text` |
| `src/static/css/admin.css` | 46 | `--ihrms-surface` | `--ui-bg` |
| `src/static/css/admin.css` | 48 | `--ihrms-primary-strong` | `--ui-link` |
| `src/static/css/admin.css` | 49 | `--ihrms-primary-hover` | `--ui-brand-hover` |
| `src/static/css/admin.css` | 50 | `--ihrms-primary-strong` | `--ui-link` |
| `src/static/css/admin.css` | 52 | `--ihrms-primary-soft`, `--ihrms-primary-strong` | `--ui-surface-raised`, `--ui-link` |
| `src/static/css/admin.css` | 53 | `--ihrms-primary-soft`, `--ihrms-raised-shadow` | `--ui-surface-raised`, `--ui-shadow-card` |
| `src/static/css/admin.css` | 55 | `--ihrms-primary-strong` | `--ui-link` |
| `src/static/css/admin.css` | 56 | `--ihrms-primary-hover` | `--ui-brand-hover` |
| `src/static/css/admin.css` | 57 | `--ihrms-border`, `--ihrms-primary-soft`, `--ihrms-text` | `--ui-surface-raised`, `--ui-border`, `--ui-text` |
| `src/static/css/admin.css` | 58 | `#c4b5fd`, `--ihrms-border`, `--ihrms-text` | `--ui-border`, `--ui-text` |
| `src/static/css/admin.css` | 60 | `--ihrms-border`, `rgb(76 29 149 / .08)` | `--ui-border` |
| `src/static/css/admin.css` | 61 | `--ihrms-focus`, `rgb(91 33 182 / .2)` | `--ui-focus` |
| `src/static/css/admin.css` | 62 | `--ihrms-primary-strong` | `--ui-link` |
| `src/static/css/admin.css` | 63 | `--ihrms-focus` | `--ui-focus` |
| `src/static/css/design_tokens.css` | 4 | `#8b5cf6`, `--ihrms-primary` | `--ui-brand`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 5 | `#4c1d95`, `--ihrms-primary-strong` | `--ui-link`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 6 | `#5b21b6`, `--ihrms-primary-hover` | `--ui-brand-hover`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 7 | `#ddd6fe`, `--ihrms-primary-soft` | `--ui-surface-raised`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 8 | `#f5f3ff`, `--ihrms-surface` | `--ui-bg`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 9 | `#2e1065`, `--ihrms-heading` | `--ui-text`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 10 | `#2e1065`, `--ihrms-text` | `--ui-text`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 11 | `#4c1d95`, `--ihrms-muted` | `--ui-text-muted`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 12 | `#5b21b6`, `--ihrms-border` | `--ui-border`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 13 | `#5b21b6`, `--ihrms-focus` | `--ui-focus`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 14 | `--ihrms-content-width` | `--ui-content-max-width`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 15 | `#4c1d95`, `--ihrms-action-bg` | `--ui-brand`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 16 | `#4c1d95`, `--ihrms-header-bg` | `--ui-surface`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 17 | `--ihrms-raised-shadow`, `rgb(76 29 149 / .10)` | `--ui-shadow-card`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 22 | `--ihrms-content-width` | `--ui-content-max-width`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 23 | `--ihrms-primary` | `--ui-brand`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 24 | `--ihrms-primary-strong` | `--ui-link`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 25 | `--ihrms-primary-hover` | `--ui-brand-hover`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 26 | `--ihrms-primary-soft` | `--ui-surface-raised`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 27 | `--ihrms-surface` | `--ui-bg`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 28 | `--ihrms-heading` | `--ui-text`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 29 | `--ihrms-text` | `--ui-text`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 30 | `--ihrms-muted` | `--ui-text-muted`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 31 | `--ihrms-border` | `--ui-border`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 32 | `--ihrms-focus` | `--ui-focus`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 33 | `--ihrms-action-bg` | `--ui-brand`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 34 | `--ihrms-header-bg` | `--ui-surface`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/design_tokens.css` | 35 | `--ihrms-raised-shadow` | `--ui-shadow-card`; palette cũ chỉ giữ trong `.hcns-paper` và `@media print` để bảo toàn giấy/in. |
| `src/static/css/hcns_forms.css` | 2 | `--ihrms-heading` | `--ui-text` |
| `src/static/css/hcns_forms.css` | 7 | `--ihrms-primary-strong` | `--ui-link` |
| `src/static/css/hcns_forms.css` | 76 | `--ihrms-muted` | `--ui-text-muted` |
| `src/static/css/hcns_forms.css` | 77 | `--ihrms-primary-soft`, `--ihrms-surface` | `--ui-surface`, `--ui-border` |
| `src/static/css/hcns_forms.css` | 78 | `--ihrms-border`, `--ihrms-primary-strong`, `--ihrms-raised-shadow` | `--ui-border`, `--ui-link`, `--ui-shadow-card` |
| `src/static/css/hcns_forms.css` | 79 | `--ihrms-primary-soft` | `--ui-surface-raised` |
| `src/static/css/hcns_forms.css` | 80 | `--ihrms-primary-hover` | `--ui-brand-hover` |
| `src/static/css/hcns_forms.css` | 82 | `--ihrms-primary-soft`, `--ihrms-raised-shadow` | `--ui-border`, `--ui-shadow-card` |
| `src/static/css/hcns_forms.css` | 83 | `--ihrms-border` | `--ui-border` |
| `src/static/css/hcns_forms.css` | 84 | `--ihrms-primary-strong` | `--ui-link` |
| `src/static/css/hcns_forms.css` | 86 | `--ihrms-primary-soft` | `--ui-border` |
| `src/static/css/hcns_forms.css` | 87 | `--ihrms-surface` | `--ui-surface` |
| `src/static/css/hcns_forms.css` | 88 | `--ihrms-focus` | `--ui-focus` |
| `src/static/css/home_dashboard.css` | 2 | `--ihrms-text` | `--ui-text` |
| `src/static/css/home_dashboard.css` | 5 | `--ihrms-primary-soft` | `--ui-surface-raised` |
| `src/static/css/home_dashboard.css` | 7 | `--ihrms-raised-shadow` | `--ui-shadow-card` |
| `src/static/css/home_dashboard.css` | 15 | `--ihrms-border` | `--ui-border` |
| `src/static/css/home_dashboard.css` | 17 | `rgb(76 29 149 / .08)` | `--ui-border`, `--ui-surface`, `--ui-shadow-card` |
| `src/static/css/home_dashboard.css` | 23 | `--ihrms-muted` | `--ui-text-muted` |
| `src/static/css/home_dashboard.css` | 30 | `--ihrms-primary-hover` | `--ui-brand-hover` |
| `src/static/css/home_dashboard.css` | 39 | `--ihrms-primary` | `--ui-brand` |
| `src/static/css/ihrms.css` | 10 | `--ihrms-border` | `--ui-border` |
| `src/static/css/ihrms.css` | 14 | `--ihrms-text` | `--ui-text` |
| `src/static/css/ihrms.css` | 15 | `rgb(76 29 149 / 0.08)` | `--ui-text`, `--ui-shadow-card` |
| `src/static/css/ihrms.css` | 24 | `--ihrms-border` | `--ui-border` |
| `src/static/css/ihrms.css` | 33 | `--ihrms-focus` | `--ui-focus` |
| `src/static/css/ihrms.css` | 34 | `--ihrms-focus` | `--ui-focus` |
| `src/static/css/ihrms.css` | 36 | `rgb(91 33 182 / 0.2)` | `--ui-shadow-card` |
| `src/static/css/ihrms.css` | 40 | `--ihrms-surface` | `--ui-bg` |
| `src/static/css/ihrms.css` | 41 | `--ihrms-muted` | `--ui-text-muted` |
| `src/static/css/ihrms.css` | 46 | `--ihrms-primary-hover` | `--ui-brand-hover` |
| `src/static/css/ihrms.css` | 57 | `--ihrms-border`, `--ihrms-raised-shadow` | `--ui-border`, `--ui-shadow-card` |
| `src/static/css/ihrms.css` | 132 | `--ihrms-primary-soft` | `--ui-surface-raised` |
| `src/static/css/ihrms.css` | 133 | `--ihrms-primary-hover` | `--ui-brand-hover` |
| `src/static/css/ihrms.css` | 138 | `--ihrms-raised-shadow` | `--ui-shadow-card` |
| `src/static/css/ihrms.css` | 142 | `--ihrms-primary-strong` | `--ui-link` |
| `src/static/css/ihrms.css` | 143 | `--ihrms-surface` | `--ui-bg` |
| `src/static/css/ihrms.css` | 153 | `--ihrms-primary-soft` | `--ui-surface-raised` |
| `src/static/css/ihrms.css` | 154 | `--ihrms-primary-strong` | `--ui-link` |
| `src/static/css/ihrms.css` | 159 | `--ihrms-primary-soft` | `--ui-surface-raised` |
| `src/static/css/ihrms.css` | 160 | `--ihrms-primary-strong` | `--ui-link` |
| `src/static/css/ihrms.css` | 186 | `--ihrms-primary` | `--ui-brand` |
| `src/static/css/ihrms.css` | 193 | `--ihrms-primary` | `--ui-brand` |
| `src/static/css/report_dashboard.css` | 2 | `--ihrms-text` | `--ui-text` |
| `src/static/css/report_dashboard.css` | 5 | `--ihrms-heading` | `--ui-text` |
| `src/static/css/report_dashboard.css` | 6 | `--ihrms-muted` | `--ui-text-muted` |
| `src/static/css/report_dashboard.css` | 8 | `--ihrms-text` | `--ui-text` |
| `src/static/css/report_dashboard.css` | 11 | `--ihrms-border` | `--ui-border` |
| `src/static/css/report_dashboard.css` | 12 | `--ihrms-primary-strong`, `rgb(76 29 149 / .16)` | `--ui-link` |
| `src/static/css/report_dashboard.css` | 13 | `--ihrms-primary-hover` | `--ui-brand-hover` |
| `src/static/css/report_dashboard.css` | 14 | `--ihrms-primary-strong`, `--ihrms-raised-shadow` | `--ui-link`, `--ui-shadow-card` |
| `src/static/css/report_dashboard.css` | 15 | `--ihrms-primary-soft` | `--ui-surface-raised` |
| `src/static/css/report_dashboard.css` | 16 | `--ihrms-focus` | `--ui-focus` |
| `src/static/css/report_dashboard.css` | 17 | `--ihrms-text` | `--ui-text` |
| `src/static/css/report_dashboard.css` | 18 | `--ihrms-muted` | `--ui-text-muted` |
| `src/static/css/report_dashboard.css` | 20 | `--ihrms-border`, `rgb(76 29 149 / .08)` | `--ui-border` |
| `src/static/css/report_dashboard.css` | 21 | `--ihrms-muted` | `--ui-text-muted` |
| `src/static/css/report_dashboard.css` | 22 | `--ihrms-primary-hover` | `--ui-brand-hover` |
| `src/static/css/report_dashboard.css` | 30 | `--ihrms-primary-soft`, `--ihrms-raised-shadow` | `--ui-surface-raised`, `--ui-shadow-card` |
| `src/static/css/report_dashboard.css` | 31 | `--ihrms-heading` | `--ui-text` |
| `src/static/css/report_dashboard.css` | 32 | `--ihrms-border` | `--ui-border` |
| `src/static/css/report_dashboard.css` | 36 | `--ihrms-primary-hover` | `--ui-brand-hover` |
| `src/static/css/report_dashboard.css` | 37 | `--ihrms-muted` | `--ui-text-muted` |
| `src/static/css/report_dashboard.css` | 38 | `--ihrms-text` | `--ui-text` |
| `src/static/css/report_dashboard.css` | 40 | `--ihrms-text` | `--ui-text` |
| `src/static/css/report_dashboard.css` | 41 | `--ihrms-primary-strong` | `--ui-link` |
| `src/static/css/report_dashboard.css` | 44 | `--ihrms-border` | `--ui-border` |
| `src/static/css/report_dashboard.css` | 46 | `--ihrms-primary-soft` | `--ui-surface-raised` |
| `src/static/css/report_dashboard.css` | 49 | `--ihrms-text` | `--ui-text` |
| `src/static/css/report_dashboard.css` | 50 | `--ihrms-primary-soft`, `rgb(76 29 149 / .12)` | `--ui-surface-raised` |
| `src/static/css/report_dashboard.css` | 51 | `--ihrms-primary` | `--ui-brand` |
| `src/static/css/report_dashboard.css` | 52 | `--ihrms-heading` | `--ui-text` |
| `src/static/css/report_dashboard.css` | 55 | `--ihrms-primary-strong` | `--ui-link` |
| `src/static/css/report_dashboard.css` | 58 | `#ede9fe` | `--ui-border`, `--ui-surface`, `--ui-text-muted`, `--ui-text`, `--ui-danger-text`, `--ui-warning-text`, `--ui-success-text` |
| `src/static/css/report_dashboard.css` | 59 | `--ihrms-muted` | `--ui-text-muted` |
| `src/static/css/report_dashboard.css` | 60 | `--ihrms-primary-hover` | `--ui-brand-hover` |
| `src/static/css/tailwind.css` | 2 | `#2e1065`, `#4c1d95`, `#5b21b6`, `#6d28d9`, `#8b5cf6`, `#c4b5fd`, `#ddd6fe`, `#ede9fe`, `#f5f3ff` | Sinh lại từ `src/frontend/tailwind.input.css`; palette `--color-*` → `--ui-*`, surface/slate và semantic. |
| `src/static/css/theme.css` | 24 | `--ihrms-surface`, `--ihrms-text` | `--ui-bg`, `--ui-text` |
| `src/static/css/theme.css` | 25 | `--ihrms-header-bg` | `--ui-surface` |
| `src/static/css/theme.css` | 31 | `--ihrms-raised-shadow`, `--ihrms-text` | `--ui-text`, `--ui-shadow-card` |
| `src/static/css/theme.css` | 37 | `--ihrms-primary-soft` | `--ui-surface-raised` |
| `src/static/css/theme.css` | 39 | `--ihrms-text` | `--ui-text` |
| `src/static/css/theme.css` | 41 | `--ihrms-muted` | `--ui-text-muted` |
| `src/static/css/theme.css` | 45 | `--ihrms-action-bg`, `--ihrms-border` | `--ui-brand`, `--ui-border` |
| `src/static/css/theme.css` | 62 | `--ihrms-header-bg` | `--ui-surface` |
| `src/static/css/theme.css` | 63 | `--ihrms-text` | `--ui-text` |
| `src/static/css/theme.css` | 69 | `--ihrms-text` | `--ui-text` |
| `src/static/css/theme.css` | 71 | `--ihrms-primary-strong` | `--ui-link` |
| `src/static/css/theme.css` | 72 | `--ihrms-text` | `--ui-text` |
| `src/static/css/theme.css` | 74 | `--ihrms-text` | `--ui-text` |
| `src/static/css/theme.css` | 75 | `--ihrms-text` | `--ui-text` |
| `src/static/css/theme.css` | 76 | `--ihrms-action-bg`, `--ihrms-border` | `--ui-brand`, `--ui-border` |
| `src/static/css/ui_tokens.css` | 62 | `#6d28d9` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 63 | `#5b21b6` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 64 | `#4c1d95` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 66 | `#f5f3ff` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 67 | `#6d28d9` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 68 | `#6d28d9` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 71 | `#ede9fe` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 72 | `#4c1d95` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 119 | `#c4b5fd` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 120 | `#ddd6fe` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 121 | `#a78bfa` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 122 | `#2e1065` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 123 | `#2e1065` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 124 | `#c4b5fd` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 125 | `#c4b5fd` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 128 | `#2e1065` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 129 | `#ddd6fe` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 167 | `#c4b5fd` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 168 | `#ddd6fe` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 169 | `#a78bfa` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 170 | `#2e1065` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 171 | `#2e1065` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 172 | `#c4b5fd` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 173 | `#c4b5fd` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 176 | `#2e1065` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/static/css/ui_tokens.css` | 177 | `#ddd6fe` | Giữ tại nguồn token chuẩn duy nhất; brand/selected/link/focus, không phải màu rải rác. |
| `src/templates/base.html` | 8 | `#4c1d95` | `theme-color` lấy `--ui-bg` bằng `theme.js`, theo light/dark. |

**Chưa kiểm tra:** UAT Edge tương tác trên dữ liệu/vai trò thật; in vật lý/đối chiếu từng mẫu HCNS; toàn bộ màn hình/luồng nghiệp vụ và chứng nhận WCAG. Headless/đo token không thay cho các bước này. Không push/deploy. Commit trên `main`: `97e4cf38452b5ae180696fbadc1ce4fd95478536` — `fix(ui): menu links`; `c8ba1931e5c256d5bc13ef96e7075cce3aefa8f9` — `ui: nav polish`; `3d6d3822060a7549182990b66888e554224bb6db` — `ui: unify colors light/dark`. Phần DESIGN mới của chủ dự án, MASTER và mục nhật ký này nằm trong commit `docs: ui design rules` (SHA xem Git log để tránh tự tham chiếu). Không push/deploy; giữ mục backup cũ chưa commit ngoài đợt này.

## 2026-10-12 — UI/UX Giai đoạn 2: nền tảng chính thức và khung ứng dụng

**Phạm vi/đầu đợt:** dùng UI UX Pro Max đã đọc ở đợt trước; không dùng UI Styling/shadcn. Đọc AGENTS, hướng dẫn review, RBAC, MASTER, tokens, nhật ký và DESIGN mới do chủ dự án cập nhật. DESIGN không còn định hướng Neumorphism; giữ nguyên thay đổi cục bộ ở DESIGN và mục backup nhật ký, loại khỏi staging. `main`, `git fetch origin main` exit 0, `git rev-list --left-right --count HEAD...origin/main` = `2 0` (hai commit Giai đoạn 0–1 chưa push), không phân kỳ. Không push/deploy, không thay nghiệp vụ/URL/field/model/migration/RBAC.

**Phần A — nền tảng:** đổi MASTER sang đã duyệt bởi chủ dự án theo yêu cầu 12/10/2026; cập nhật font stack đầy đủ và liên kết tên chính thức `ui_tokens.css`. CSS fallback OS dark chỉ với `:root:not([data-theme])`, explicit preference thắng. Bổ sung tokens sidebar/chart tham chiếu semantic light/dark. `design_tokens.css` import bộ chính thức và map `ihrms-*`/Tailwind một chiều trong screen; defaults print giữ nguyên. Theme bỏ root overrides tím cũ, Bootstrap theo ui tokens; admin adapter sửa paired foreground/background để tránh chữ trắng trên brand sáng dark. Base import tokens sau legacy/theme; phần B thêm CSS khung cuối cascade. Không recolor giấy HCNS.

**Đo có thể chạy lại:** `python ops/check_ui_contrast.py --write-doc`, bảng từng cặp lưu trong `docs/UI_DESIGN_SYSTEM_PHASE1.md`; script Python standard library không dependency. Exit 0: 136 cặp, light text min 6.147:1/UI min 3.860:1; dark text min 5.599:1/UI min 3.805:1. `git diff --check` exit 0; tìm liên kết proposed trong docs/nguồn hiện hành không còn (rg exit 1). Đây là đo contract, chưa chứng nhận UI/WCAG. Phần A commit riêng `ui: finalize tokens and design docs`; kiểm tra full backend chạy cuối Giai đoạn 2.

**Phần B — khung:** thay nav ngang bằng sidebar 256px/72px ở >=1024px, drawer có overlay dưới 1024px, không bottom bar. LocalStorage chỉ lưu theme/trạng thái thu gọn, luôn try/catch; storage bị chặn vẫn dùng được. Accordion mở theo route/query hiện tại; Báo cáo cùng kiểu các nhóm khác và giữ link hub gốc. Tooltip cho tên khi thu gọn dùng hover/focus, Esc đóng. Topbar có tên hệ thống, nút điều hướng, chuông + nhãn số chưa đọc, user disclosure, POST logout/CSRF, SVG theme; breadcrumb lấy block title đã render (hoặc h1 nếu title mặc định), không thêm context/view hoặc bịa cấp cha. Skip-link/landmarks và main focus target; Django messages dùng mức số, SVG, status/alert và không tự đóng để tránh mất thông báo. Đây là alerts tồn tại trong trang, không phải toast tự biến mất khi chưa có bản lưu. Chưa thiết kế lại nội dung trang con; greeting emoji, KPI/số 0/biểu đồ cũ còn nguyên và thuộc giai đoạn sau.

CSS khung tải sau CSS trang con; bổ sung compatibility cho font/nền/control/filled buttons, bảng và grid KPI khi sidebar chiếm bề ngang. Bỏ CSS/JS nav ngang cũ, cập nhật cache namespace static v5; không cache HTML/dữ liệu nghiệp vụ. Aliases width cũng trỏ một chiều sang ui trong screen. Thêm token transparent cho placeholder active marker, không rải màu/spacing/radius mới trong CSS khung. Không đổi CSS HCNS/print source, backend hoặc quyền.

**Kết quả skill Phần B:** tất cả lệnh Python hệ thống với prefix `python C:/Users/dinht/.agents/skills/ui-ux-pro-max/scripts/search.py`, exit 0. `"sidebar keyboard navigation" --domain ux -n 1` → Keyboard Navigation; `"topbar navigation"` → Sticky Navigation; `"breadcrumb hierarchy"` → Breadcrumbs; `"user menu keyboard"` → Keyboard Navigation. `"responsive navigation"` cho Sticky Navigation chưa sát mobile, retry `"mobile first" --domain ux -n 1` → Mobile First. `"notification dropdown" --domain ux -n 1` 0 matches; retry `"toast notifications" --domain ux -n 1` chỉ có Toast Notifications, không tìm được guidance dropdown cụ thể: giữ link chuông tới danh sách sẵn có, không bịa notification payload/context. `"dark mode toggle" --domain ux -n 1` 0 matches; retry `"dark mode" --domain style -n 1` → OLED, bỏ vì MASTER yêu cầu hai theme và không glow. Toggle theo quy tắc đã duyệt, không tuyên bố dataset đã xác nhận mẫu đó. Không thêm dependency/CDN/font/icon library.

**Bảo toàn menu:** source trước có 44 links (có mục dùng chung trùng URL); giữ nguyên multiset URL/query và guard. Regression độc lập đối chiếu inventory cho 11 vai trò x có/không employee (22 tình huống), gồm đủ EMPLOYEE/DEPT_MANAGER/HR_OFFICER/HR_MANAGER/DIRECTOR/SYS_ADMIN và thêm Finance/Super Admin/Project Manager/Coordinator/CBDA; không mục nào xuất hiện/mất đi trong các tình huống đó. Header giữ `/admin/` và `/reports/` dưới `is_admin_user`, profile/notifications/logout dưới `user.is_authenticated`; không sửa guard kể cả khác biệt với ma trận tài liệu. Đây là kiểm hiển thị, không phải review lại quyền truy cập backend. Mọi guard bên dưới còn có điều kiện ngoài cùng `user.is_authenticated`:

- Trang chủ (`{{ u_dash }}`): `user.is_authenticated` (không guard bổ sung).
- Hồ sơ cá nhân (`{% url 'portal:profile' %}`): `user.is_authenticated` (không guard bổ sung).
- Yêu cầu cập nhật hồ sơ (`{% url 'portal:profile_change_request_list' %}`): `user.is_authenticated` (không guard bổ sung).
- Sơ đồ tổ chức (`{% url 'portal:org_chart' %}`): `user.is_authenticated` (không guard bổ sung).
- Bảng công (`{% url 'portal:timesheet_month' %}`): `user.is_authenticated` (không guard bổ sung).
- Nghỉ phép (`{% url 'portal:leave_list' %}`): `user.is_authenticated` (không guard bổ sung).
- KPI (`{% url 'portal:kpi_my_list' %}`): `user.is_authenticated` (không guard bổ sung).
- Phiếu lương (`{% url 'portal:payslip_list' %}`): `user.is_authenticated` (không guard bổ sung).
- Nhân viên & hồ sơ (`{% url 'portal:hr_employee_list' %}`): `can_manage_hr or can_approve or can_approve_timesheet or can_approve_document or can_approve_activity_proposals or can_approve_personnel_decision`; `can_manage_hr`.
- Hợp đồng (`{% url 'portal:hr_contract_list' %}`): `can_manage_hr or can_approve or can_approve_timesheet or can_approve_document or can_approve_activity_proposals or can_approve_personnel_decision`; `can_manage_hr`.
- Checklist tiếp nhận/nghỉ việc (`{% url 'portal:lifecycle_case_list' %}`): `can_manage_hr or can_approve or can_approve_timesheet or can_approve_document or can_approve_activity_proposals or can_approve_personnel_decision`; `can_manage_hr`.
- Biểu mẫu HCNS (`{% url 'portal:hcns_catalog' %}`): `can_manage_hr or can_approve or can_approve_timesheet or can_approve_document or can_approve_activity_proposals or can_approve_personnel_decision`; `can_manage_hr`.
- Quyết định nhân sự (`{% url 'portal:personnel_decision_list' %}`): `can_manage_hr or can_approve or can_approve_timesheet or can_approve_document or can_approve_activity_proposals or can_approve_personnel_decision`; `can_manage_hr or can_approve_personnel_decision`.
- Duyệt cập nhật hồ sơ (`{% url 'portal:profile_change_request_list' %}`): `can_manage_hr or can_approve or can_approve_timesheet or can_approve_document or can_approve_activity_proposals or can_approve_personnel_decision`; `can_approve or can_approve_timesheet or can_approve_document or can_approve_activity_proposals or can_manage_hr`; `can_manage_hr`.
- Duyệt nghỉ phép (`{% url 'portal:leave_approval_list' %}`): `can_manage_hr or can_approve or can_approve_timesheet or can_approve_document or can_approve_activity_proposals or can_approve_personnel_decision`; `can_approve or can_approve_timesheet or can_approve_document or can_approve_activity_proposals or can_manage_hr`; `can_approve`.
- Duyệt chấm công (`{% url 'portal:timesheet_approval_list' %}`): `can_manage_hr or can_approve or can_approve_timesheet or can_approve_document or can_approve_activity_proposals or can_approve_personnel_decision`; `can_approve or can_approve_timesheet or can_approve_document or can_approve_activity_proposals or can_manage_hr`; `can_approve_timesheet`.
- Duyệt tài liệu (`{% url 'portal:document_approval_list' %}`): `can_manage_hr or can_approve or can_approve_timesheet or can_approve_document or can_approve_activity_proposals or can_approve_personnel_decision`; `can_approve or can_approve_timesheet or can_approve_document or can_approve_activity_proposals or can_manage_hr`; `can_approve_document`.
- Duyệt đề xuất hoạt động (`{% url 'portal:activity_proposal_approval_list' %}`): `can_manage_hr or can_approve or can_approve_timesheet or can_approve_document or can_approve_activity_proposals or can_approve_personnel_decision`; `can_approve or can_approve_timesheet or can_approve_document or can_approve_activity_proposals or can_manage_hr`; `can_approve_activity_proposals`.
- Quy trình tuyển dụng (`{% url 'portal:recruitment_hub' %}`): `can_manage_hr or can_request_recruitment or can_approve_recruitment`.
- Đề xuất tuyển dụng (`{% url 'portal:recruitment_list' %}`): `can_manage_hr or can_request_recruitment or can_approve_recruitment`; `can_request_recruitment or can_approve_recruitment`.
- Ứng viên (`{% url 'portal:hr_candidate_list' %}`): `can_manage_hr or can_request_recruitment or can_approve_recruitment`; `can_manage_hr`.
- Biểu mẫu tuyển dụng (`{% url 'portal:hcns_catalog' %}?group=recruitment`): `can_manage_hr or can_request_recruitment or can_approve_recruitment`; `can_manage_hr`.
- Chạy lương hàng tháng (`{% url 'portal:finance_period_list' %}`): `can_manage_finance or can_use_salary_scale_form`; `can_manage_finance`.
- Lương cơ bản NV (`{% url 'portal:finance_salary_list' %}`): `can_manage_finance or can_use_salary_scale_form`; `can_manage_finance`.
- Người phụ thuộc (`{% url 'portal:finance_dependent_list' %}`): `can_manage_finance or can_use_salary_scale_form`; `can_manage_finance`.
- Cấu hình Thuế/BH (`{% url 'portal:finance_tax_config' %}`): `can_manage_finance or can_use_salary_scale_form`; `can_manage_finance`.
- Thang bảng lương (`{% url 'portal:hcns_draft' 'salary-scale' %}`): `can_manage_finance or can_use_salary_scale_form`; `can_use_salary_scale_form`.
- Tài liệu đã ban hành (`{% url 'portal:document_list' %}`): `user.is_authenticated` (không guard bổ sung).
- Công văn đến (`{% url 'portal:dispatch_list' %}?type=Incoming`): `user.is_authenticated` (không guard bổ sung).
- Công văn đi (`{% url 'portal:dispatch_list' %}?type=Outgoing`): `user.is_authenticated` (không guard bổ sung).
- Tài sản của tôi (`{% url 'portal:asset_list' %}`): `can_view_asset`.
- Quản lý Tài sản (`{% url 'portal:asset_admin_list' %}`): `can_view_asset`.
- Kiểm kê Tài sản (`{% url 'portal:inventory_session_list' %}`): `can_view_asset`.
- Thanh lý Tài sản (`{% url 'portal:disposal_request_list' %}`): `can_view_asset`.
- Phòng họp (`{% url 'portal:room_booking_list' %}`): `user.is_authenticated` (không guard bổ sung).
- Đặt xe (`{% url 'portal:vehicle_booking_list' %}`): `user.is_authenticated` (không guard bổ sung).
- VPP (`{% url 'portal:supply_request_list' %}`): `user.is_authenticated` (không guard bổ sung).
- Lịch công tác (`{% url 'portal:event_list' %}`): `user.is_authenticated` (không guard bổ sung).
- Đào tạo (`{% url 'portal:training_my_list' %}`): `user.is_authenticated` (không guard bổ sung).
- Quản lý ngày lễ (`{% url 'portal:holiday_list' %}`): `can_manage_calendar`.
- Báo cáo (`{{ u_report }}`): `can_view_reports`.
- Theo dõi hoạt động (`{% url 'portal:activity_dashboard' %}`): `can_view_activity_dashboard`.
- Lịch hoạt động (`{% url 'portal:activity_calendar' %}`): `can_view_activity_dashboard`.
- Giao việc & hoàn tất (`{% url 'portal:task_list' %}`): `can_view_activity_dashboard`.

**Test mới/cập nhật:** `tests_app_shell.py` có bốn regression: multiset menu/role/employee, render anonymous/chưa gắn hồ sơ, route/query active (Incoming/Outgoing/default) và mức messages có extra tags. `tests_mobile.py` cập nhật contract breakpoint 1024px, aria-controls sidebar và cache v5; không skip/giảm assertion để làm đẹp kết quả. Lần focused đầu 44 test/68.913s đạt nhưng import class fixture làm lặp test nghiệp vụ; đã chuyển sang import module, focused cuối trước full chạy 11 test/20.098s, exit 0. Bổ sung assertion cho Incoming mặc định sau đó, sẽ chạy lại focused để chốt. Script browser còn xác nhận ca này sau sửa JS giữ lựa chọn current từ server.

**Kiểm tra browser thực tế:** Edge headless cài sẵn, profile riêng; Node 24.21.0 dùng CDP built-in, không cài Playwright/Puppeteer. Server `127.0.0.1:8876` dùng SQLite mới trong TEMP, dữ liệu giả có dấu tiếng Việt, media/email/logs cô lập, M365 tắt; không dùng DB nghiệp vụ. 16 ảnh dashboard + HR list ở 360/768/1024/1440px light/dark và 2 ảnh drawer 360 light/dark tại `C:/Users/dinht/AppData/Local/Temp/ihrms-ui-phase2-20261012/screenshots/`; đã mở xem ảnh desktop, mobile dark, HR list và drawer bằng công cụ ảnh. Script TEMP `ui_browser.cjs` cuối exit 0; tất cả 16 tổ hợp không tràn ngang trang. Drawer Esc/overlay/nút đóng, Tab/Shift+Tab trap, inert nền, trả focus; collapse 72px/lưu qua reload/tooltip focus+Esc; menu account Esc; auto-open nhóm; OS fallback/reduced motion/explicit override; storage bị chặn; vùng chạm shell >=44px đều đạt. Đã sửa trả focus luôn về nút mở; lỗi kiểm thử ban đầu do chưa đợi breakpoint ổn định, đã sửa chờ rồi chạy lại. Breadcrumb đã chỉnh ưu tiên page title thay greeting.

Đo cuối `python ops/check_ui_contrast.py --write-doc` exit 0: 140 cặp, thêm border/focus trên selected background thực dùng; light/dark min như Phần A. `node --check src/static/js/app_shell.js`, `node --check src/static/js/theme.js` exit 0; tìm hex/remote URL trong CSS/JS shell/icon mới không có (rg exit 1). `git diff --check` exit 0. Font/dữ liệu/formats/quyền nghiệp vụ không đổi.

**Phần chưa xác nhận:** chưa UAT Edge tương tác thủ công, screen reader, browser zoom 200% thực (chỉ mô phỏng viewport CSS tương đương), nâng cache từ phiên cũ (CDP bypass service worker để thử nguồn hiện tại), toàn bộ trang con/vai trò trong browser hoặc toàn ứng dụng WCAG. Đã kiểm màu foreground/background giấy annual-leave HCNS giống nhau giữa light/dark, và print media ẩn header/sidebar; chưa kiểm tất cả biểu mẫu in/Word/Excel/PDF. Không có finding nghiệp vụ/phân quyền mới được xác nhận trong phạm vi UI này; không coi đó là đã review backend.

**Gate/bàn giao:** pip check, Django check, migration drift dùng SQLite/SECRET_KEY/DB_NAME tạm đều exit 0; môi trường được khôi phục, không có migration mới. Hai full backend chạy lần lượt bằng `venv/Scripts/python.exe ops/run_tests.py --backend sqlite` và `--backend sqlserver`; kết quả cuối/exit code/cảnh báo logging được cập nhật trước commit Phần B. Phần A đã commit `d4c19ccf1632ecdc4f8425c97e2d8c0c188138b2`; Phần B sẽ commit riêng `ui: app shell (sidebar/topbar/drawer)`. Không push/deploy, không tự sang giai đoạn kế. Chủ dự án xem ảnh và giao diện thật bằng dữ liệu giả, duyệt khung, chốt thay đổi DESIGN đang local và quyết định push.

**Kết quả chốt sau chạy lại:** hai full suite lượt đầu có 4 failures do assertions bám nhãn ngay trước `</a>` trong markup menu cũ: SQLite 421 test/436.249s (skip 7), SQL Server 421 test/452.346s; exit 1. Đã đổi assertions lịch hoạt động sang link có đúng URL+nhãn và quyết định nhân sự sang số link đúng URL theo vai trò; giữ toàn bộ guard/access assertions, không sửa backend/skip để qua gate. Chạy lại focused `venv/Scripts/python.exe ops/run_tests.py --backend sqlite apps.portal.tests_app_shell apps.portal.tests_mobile apps.portal.tests_recruitment_accounting_navigation apps.activity.tests.ActivityDashboardPermissionTests.test_cbda_calendar_shows_assigned_activities_for_selected_month`: 16 test/34.134s, OK, exit 0. Sau đó full SQLite 421 test/371.866s, `OK (skipped=7)`, exit 0; full SQL Server 421 test/356.775s, `OK`, không skip, exit 0. DB SQL test disposable có UUID và runner báo destroy. Skip SQLite dành cho row-lock/concurrency/NULL uniqueness SQL Server. Logs lượt cuối ở TEMP `ihrms-ui-phase2-20261012/full-*-corrected.log`; tìm `WinError 32|Logging error` không có (rg exit 1), không sửa/copy log nghiệp vụ vào Git.

**Rà cuối và tiếp tục:** sau yêu cầu tiếp tục, xác nhận `main`, fetch exit 0 và `3 0` trước commit B (origin chưa có ba commit local). Shell mặc định vẫn lỗi khởi tạo; đường thực thi xét duyệt hoạt động trở lại sau lần auto-review lỗi hạn mức ở lượt trước. `python ops/check_ui_contrast.py`, hai `node --check`, `git diff --check`, `git diff --cached --check` đều exit 0. Snapshot đối chiếu xác nhận DESIGN nguyên byte và nội dung nhật ký có sẵn không bị sửa, loại khỏi staging. Rà staged chỉ UI/test/docs, không có secret pattern phổ biến hoặc backend/model/migration/dependency. Server preview PID do đợt này tạo đã đóng sau khi đối chiếu command line `ui_server.py` trong TEMP; ảnh/DB/media/scripts preview giữ ngoài Git. Commit B có tiêu đề `ui: app shell (sidebar/topbar/drawer)`, SHA lấy bằng `git log -2 --oneline`; không push/deploy. Dừng Giai đoạn 2, chờ chủ dự án xem và duyệt giao diện.


## 2026-10-12 — UI/UX Giai đoạn 0–1: kiểm kê và design system (UI UX Pro Max)

**Phạm vi/Git:** UI và tài liệu trên `main`; ban đầu chỉ `M docs/PROJECT_WORK_LOG.md` (mục backup có sẵn được giữ nguyên và không đưa vào commit đợt này). `git fetch origin main` exit 0, `git rev-list --left-right --count HEAD...origin/main` = `0 0`. Đã đọc AGENTS, hướng dẫn review, nhật ký, ma trận RBAC và toàn bộ `C:/Users/dinht/.agents/skills/ui-ux-pro-max/SKILL.md`. Không dùng UI Styling/shadcn, không thêm dependency, không push/deploy. Shell mặc định lỗi `helper_unknown_error: setup refresh had errors`; Node REPL thoát; đường shell dự phòng được xét duyệt hoạt động.

**Giai đoạn 0 — kiểm kê:** 88 HTML templates, 15 static assets. Base thật là `src/templates/base.html`; không có `portal/base.html` (lần đọc nhầm đường dẫn đã được sửa). Portal chứa phần lớn phân hệ trong một thư mục; activity, lifecycle và document/HCNS có template riêng. Đây là kiểm kê nguồn, chưa UAT từng trang.

- `activity` (6 templates): `src/apps/activity/templates/activity/activity_form.html`, `src/apps/activity/templates/activity/calendar.html`, `src/apps/activity/templates/activity/dashboard.html`, `src/apps/activity/templates/activity/proposal_approval_list.html`, `src/apps/activity/templates/activity/proposal_detail.html`, `src/apps/activity/templates/activity/proposal_email_draft.html`.
- `document` (4 templates): `src/apps/document/templates/document/hcns/appointment_document.html`, `src/apps/document/templates/document/hcns/catalog.html`, `src/apps/document/templates/document/hcns/document.html`, `src/apps/document/templates/document/hcns/draft.html`.
- `lifecycle` (3 templates): `src/apps/lifecycle/templates/lifecycle/case_create.html`, `src/apps/lifecycle/templates/lifecycle/case_detail.html`, `src/apps/lifecycle/templates/lifecycle/case_list.html`.
- `portal` (70 templates): `src/apps/portal/templates/portal/_pagination.html`, `src/apps/portal/templates/portal/asset_admin_list.html`, `src/apps/portal/templates/portal/asset_list.html`, `src/apps/portal/templates/portal/attendance_list.html`, `src/apps/portal/templates/portal/dashboard.html`, `src/apps/portal/templates/portal/dispatch_create.html`, `src/apps/portal/templates/portal/dispatch_detail.html`, `src/apps/portal/templates/portal/dispatch_list.html`, `src/apps/portal/templates/portal/disposal_decision_print.html`, `src/apps/portal/templates/portal/disposal_execution_print.html`, `src/apps/portal/templates/portal/disposal_minutes_print.html`, `src/apps/portal/templates/portal/disposal_request_detail.html`, `src/apps/portal/templates/portal/disposal_request_form.html`, `src/apps/portal/templates/portal/disposal_request_list.html`, `src/apps/portal/templates/portal/disposal_request_print.html`, `src/apps/portal/templates/portal/document_approval_list.html`, `src/apps/portal/templates/portal/document_list.html`, `src/apps/portal/templates/portal/event_list.html`, `src/apps/portal/templates/portal/finance_dependent_list.html`, `src/apps/portal/templates/portal/finance_payroll_run.html`, `src/apps/portal/templates/portal/finance_period_list.html`, `src/apps/portal/templates/portal/finance_salary_list.html`, `src/apps/portal/templates/portal/finance_tax_config.html`, `src/apps/portal/templates/portal/holiday_list.html`, `src/apps/portal/templates/portal/hr_candidate_detail.html`, `src/apps/portal/templates/portal/hr_candidate_form.html`, `src/apps/portal/templates/portal/hr_candidate_list.html`, `src/apps/portal/templates/portal/hr_contract_form.html`, `src/apps/portal/templates/portal/hr_contract_list.html`, `src/apps/portal/templates/portal/hr_employee_detail.html`, `src/apps/portal/templates/portal/hr_employee_form.html`, `src/apps/portal/templates/portal/hr_employee_list.html`, `src/apps/portal/templates/portal/inventory_session_detail.html`, `src/apps/portal/templates/portal/inventory_session_list.html`, `src/apps/portal/templates/portal/inventory_session_print.html`, `src/apps/portal/templates/portal/kpi_assign_create.html`, `src/apps/portal/templates/portal/kpi_my_list.html`, `src/apps/portal/templates/portal/kpi_score_list.html`, `src/apps/portal/templates/portal/leave_approval_list.html`, `src/apps/portal/templates/portal/leave_create.html`, `src/apps/portal/templates/portal/leave_list.html`, `src/apps/portal/templates/portal/notification_list.html`, `src/apps/portal/templates/portal/office_incoming_list.html`, `src/apps/portal/templates/portal/office_outgoing_list.html`, `src/apps/portal/templates/portal/org_chart.html`, `src/apps/portal/templates/portal/org_chart_node.html`, `src/apps/portal/templates/portal/payslip_list.html`, `src/apps/portal/templates/portal/personnel_decision_detail.html`, `src/apps/portal/templates/portal/personnel_decision_list.html`, `src/apps/portal/templates/portal/procurement_request_list.html`, `src/apps/portal/templates/portal/profile.html`, `src/apps/portal/templates/portal/profile_change_request_form.html`, `src/apps/portal/templates/portal/profile_change_request_list.html`, `src/apps/portal/templates/portal/recruitment_create.html`, `src/apps/portal/templates/portal/recruitment_hub.html`, `src/apps/portal/templates/portal/recruitment_list.html`, `src/apps/portal/templates/portal/report_budget.html`, `src/apps/portal/templates/portal/report_headcount.html`, `src/apps/portal/templates/portal/report_hub.html`, `src/apps/portal/templates/portal/report_personnel_changes.html`, `src/apps/portal/templates/portal/report_timesheet.html`, `src/apps/portal/templates/portal/room_booking_list.html`, `src/apps/portal/templates/portal/supply_request_list.html`, `src/apps/portal/templates/portal/task_create.html`, `src/apps/portal/templates/portal/task_detail.html`, `src/apps/portal/templates/portal/task_list.html`, `src/apps/portal/templates/portal/timesheet_approval_list.html`, `src/apps/portal/templates/portal/timesheet_month.html`, `src/apps/portal/templates/portal/training_my_list.html`, `src/apps/portal/templates/portal/vehicle_booking_list.html`.
- `shared` (5 templates): `src/templates/admin/base_site.html`, `src/templates/admin/common/audit_change_list.html`, `src/templates/base.html`, `src/templates/registration/login.html`, `src/templates/reporting/dashboard.html`.
- Static đầy đủ: `src/static/css/admin.css`, `src/static/css/design_tokens.css`, `src/static/css/hcns_forms.css`, `src/static/css/home_dashboard.css`, `src/static/css/ihrms.css`, `src/static/css/report_dashboard.css`, `src/static/css/tailwind.css`, `src/static/css/theme.css`, `src/static/img/ihrms-pwa-192.png`, `src/static/img/ihrms-pwa-512.png`, `src/static/img/logo.png`, `src/static/js/hcns_forms.js`, `src/static/js/service-worker.js`, `src/static/js/theme.js`, `src/static/manifest.json`.
- Literal màu/cỡ chữ: `src/apps/portal/templates/portal/timesheet_month.html` dòng 27, 38 (2 dòng khớp regex; không phải số finding).
- Literal màu/cỡ chữ: `src/static/css/admin.css` dòng 12, 13, 15, 27, 33, 34 (13 dòng khớp regex; không phải số finding).
- Literal màu/cỡ chữ: `src/static/css/design_tokens.css` dòng 3, 4, 5, 6, 7, 8 (13 dòng khớp regex; không phải số finding).
- Literal màu/cỡ chữ: `src/static/css/hcns_forms.css` dòng 2, 3, 4, 5, 6, 7 (49 dòng khớp regex; không phải số finding).
- Literal màu/cỡ chữ: `src/static/css/home_dashboard.css` dòng 16, 17, 24, 28, 29, 31 (8 dòng khớp regex; không phải số finding).
- Literal màu/cỡ chữ: `src/static/css/ihrms.css` dòng 27, 31, 33, 50, 65, 77 (19 dòng khớp regex; không phải số finding).
- Literal màu/cỡ chữ: `src/static/css/report_dashboard.css` dòng 5, 6, 8, 11, 12, 14 (27 dòng khớp regex; không phải số finding).
- Literal màu/cỡ chữ: `src/static/css/theme.css` dòng 5, 6, 8, 10, 13, 14 (48 dòng khớp regex; không phải số finding).
- Literal màu/cỡ chữ: `src/templates/base.html` dòng 8 (1 dòng khớp regex; không phải số finding).

**Thành phần lặp và hard-code:** card/KPI tại `portal/dashboard.html`, `portal/report_hub.html`, `activity/dashboard.html`; bảng/badge/empty state và bộ lọc trong các `*_list.html`; form tại `*_create.html`, `*_form.html`, profile, finance; phân trang dùng `portal/_pagination.html`. `task_list.html` có tabs scope GET và row `onclick` chưa có link bàn phím tương đương. Base chứa alert/messages, dropdown/user menu/mobile menu và JS inline. Cảnh báo chưa gắn hồ sơ ở dashboard hiện chỉ có câu văn; greeting emoji và ký tự theme đang tồn tại, chưa đổi.

`src/static/css/design_tokens.css` đã có tokens tím, được `ihrms.css` import; `theme.css` override qua `html[data-theme="dark"]`; `js/theme.js` lưu lựa chọn `ihrms-theme`. Màu/cỡ chữ hard-code rải trong CSS theme/admin/dashboard/HCNS, template admin/login/report và Tailwind utilities. `tailwind.css` là output build, không sửa trực tiếp. Print HCNS cần giữ layout riêng. Dashboard đã có guards `employee`, `is_management_view`, `can_view_asset`, `show_project_activity_summary`; đề xuất theo vai trò phải giữ nguyên guard, scope dữ liệu và RBAC hiện có.

**Mốc trước:** chưa chụp ảnh trang chính bằng dữ liệu giả; chưa khởi động ứng dụng với DB/media thật. Chưa kiểm tra browser, 360px, keyboard, screen reader hoặc WCAG. Giai đoạn 0 không sửa mã giao diện.

**Ánh xạ phân hệ trong portal:** Cá nhân (`profile*`, `attendance_list`, `timesheet_month`, `leave*`, `payslip_list`, `kpi_my_list`, `training_my_list`, `task*`); Nhân sự (`hr_employee*`, `hr_contract*`, `personnel_decision*`, `org_chart*`, lifecycle); Tuyển dụng (`recruitment*`, `hr_candidate*`); Kế toán (`finance*`); Hành chính (`office*`, `document*`, `asset*`, `inventory*`, `disposal*`, `procurement*`, `supply*`, `room_booking*`, `vehicle_booking*` và HCNS); Kế hoạch (`event_list`, `holiday_list`, `kpi_assign_create`, `kpi_score_list`); Báo cáo (`report*`, `src/templates/reporting/dashboard.html`); Dự án (activity + `dispatch*`, task overview). Cách nhóm này là kiểm kê đường dẫn/template dùng chung, không suy ra quyền từ tên phân hệ.

**Giai đoạn 1 — đã tạo:** `design-system/MASTER.md`, `src/static/css/ui_tokens_proposed.css`, `docs/UI_DESIGN_SYSTEM_PHASE1.md`. Chỉ thêm variables `--ui-*`, chưa import; `rg -n 'ui_tokens_proposed|--ui-' src/templates src/apps --glob '*.html' --glob '*.py'` exit 1 (không tìm thấy). Không đổi base, template, view, URL/form fields, model, migration hoặc quyền. Skill lưu mặc định `design-system/ihrms/MASTER.md`; bản đã rà được chuẩn hóa về đường dẫn yêu cầu `design-system/MASTER.md`, không giữ hai nguồn quy tắc.

**Lệnh skill đã chạy (Python hệ thống 3.12.14, không cài gói):** prefix `python C:/Users/dinht/.agents/skills/ui-ux-pro-max/scripts/search.py`. Lệnh mô tả đầy đủ `"HR management portal, internal enterprise dashboard, Vietnamese, data-dense, trustworthy, professional, light and dark mode, accessible" --design-system -p IHRMS` exit 0 nhưng gợi ý Enterprise Gateway/OLED/Fira/Contact Sales chưa phù hợp. Truy vấn lại `"internal HR enterprise dashboard accessible" --design-system -p IHRMS` exit 0: giữ Accessible & Ethical, hai theme; bỏ phần marketing của pattern. Lưu bằng `"internal HR enterprise dashboard accessible" --design-system --persist -p IHRMS --output-dir D:/QLHCNS`, exit 0.

Các tìm kiếm bổ sung đều exit 0 (exit 0 không có nghĩa kết quả khớp):
- `"dashboard KPI pending approvals" --domain ux -n 2`: 0 matches; retry `"dashboard KPI" --domain style -n 1`: Data-Dense Dashboard được chọn.
- `"sidebar navigation collapse" --domain ux -n 2`: Sticky Navigation chưa đúng collapse; retry `"sidebar keyboard navigation" --domain ux -n 1`: Keyboard Navigation phù hợp. Cơ chế collapse/drawer là quyết định thiết kế theo yêu cầu, không giả định dataset trả đầy đủ.
- `"data table filter sorting" --domain ux -n 2`: Table Handling phù hợp; bỏ Bulk Actions vì không được thêm nghiệp vụ.
- `"long form validation" --domain ux -n 2`: Submit Feedback; bổ sung `"error summary validation" --domain ux -n 1`: Focusable Error Summary được chọn.
- `"empty state guidance" --domain ux -n 2`: Empty States được chọn.
- `"toast notification status" --domain ux -n 2`: Toast Notifications được chọn với ngoại lệ persistent cho lỗi/hành động; không auto-dismiss thông tin quan trọng.
- `"department comparison bar" --domain chart -n 2`: top Radar không phù hợp; retry `"compare categories" --domain chart -n 1`: Bar Chart được chọn, có bảng/tóm tắt thay thế.
- `"semantic status enterprise" --domain color -n 2`: top IoT chưa phù hợp; retry `"enterprise SaaS" --domain color -n 1`: Micro SaaS vẫn không đúng bộ semantic HR. Không dùng palette này; bốn màu semantic là quyết định riêng có đo tương phản, không nói dataset đã xác nhận.
- `"dark mode contrast" --domain ux -n 2`: hướng dẫn contrast chung; bổ sung `"dark mode" --domain style -n 1`: OLED không đáp ứng hai theme nên không dùng. Hai palette được thiết kế/đo riêng.
- `"mobile responsive navigation" --domain ux -n 2`: Mobile First/Viewport Meta phù hợp.

**Quyết định và ngoại lệ:** giữ một hue tím theo nhận diện hiện có, neutral slate, success/warning/danger/info; bỏ navy/blue CTA, OLED-only, Fira Code văn bản thường, Plus Jakarta Sans/Google Fonts remote, glow/carousel và dependency chart/GSAP. Giữ hệ font local Segoe UI; body 16px, bảng 14px, caption 12px, control/row tối thiểu 44px thay row 36px/chữ thân 12px của Data-Dense. Desktop sidebar theo tám phân hệ, mobile drawer từ 360px; giữ guard/RBAC, chỉ mô tả dashboard theo dữ liệu đang có. `DESIGN.md` hiện yêu cầu violet/system sans/neumorphism; MASTER giữ violet/system sans nhưng đề xuất border/bóng nhẹ thay neumorphism mạnh để đọc dữ liệu rõ hơn. Chưa sửa DESIGN.md, cần thống nhất sau duyệt.

**Đo tokens và glyph:** `python "$env:TEMP/ihrms-ui-phase01-20261012/verify_tokens.py"` cuối cùng exit 0; checker tạm dùng standard library, sRGB luminance, kiểm 84 cặp light/dark: text min 5.599:1 (ngưỡng 4.5), UI/focus/border min 3.860:1 (ngưỡng 3). Aliases resolve theo CSS inheritance; không URL/import/opacity trong proposal. Cmap Segoe UI regular/semibold/bold (`segoeui.ttf`, `seguisb.ttf`, `segoeuib.ttf`) có đủ 155 codepoint tiếng Việt NFC, dấu tổ hợp, đ/Đ và ₫. Ban đầu checker chưa merge root aliases vào dark (KeyError) và thử sai tên semibold (FileNotFoundError); đã sửa checker theo inheritance và đường dẫn thật, chạy lại đạt. Script/measurement/snapshot nhật ký chỉ ở TEMP, không Git. Script kiểm kê lần đầu lỗi check-ignore do outputs không bị ignore; đã chuyển tệp do Codex tạo sang TEMP và ghi lại kiểm kê bằng UTF-8. Chưa xác nhận fallback/shaping/glyph máy đích; chưa đo scrim alpha trên trang thực hoặc toàn bộ WCAG.

**Kiểm tra framework đã chạy:** `venv/Scripts/python.exe -m pip check` exit 0 (No broken requirements); `venv/Scripts/python.exe src/manage.py check` exit 0 (0 issues); `venv/Scripts/python.exe src/manage.py makemigrations --check --dry-run` exit 0 (No changes detected). Framework checks dùng `DB_ENGINE=django.db.backends.sqlite3`, SECRET_KEY sinh tạm không in, DB_NAME tạm trong TEMP, khôi phục env sau kiểm tra. `git diff --check` và `git diff --cached --check` exit 0. Kiểm links/UTF-8/no-import của tài liệu mới exit 0 sau sửa encoding đọc tệp trong checker; mã sản phẩm không cần sửa.

**Hai backend đã chạy thực tế:** `venv/Scripts/python.exe ops/run_tests.py --backend sqlite` exit 0, phát hiện/chạy 417 test trong 447.935 giây, `OK (skipped=7)`; các skip là SQL Server row locking/concurrency và NULL uniqueness, đối chiếu decorators trong office/activity/planning/portal tests. `venv/Scripts/python.exe ops/run_tests.py --backend sqlserver` exit 0, backend `microsoft`, 417 test trong 537.867 giây, `OK`, không skip; runner tạo DB `test_ihrms_<UUID>` disposable, báo destroy ở cuối, media tạm và M365 tắt. Không dùng số test cũ làm bằng chứng.

**Giới hạn logging:** hai suite được chạy đồng thời khi chưa kiểm tra shared log; cả hai có `PermissionError [WinError 32]` lúc rotate `Logs/app.log` do file đang mở bởi process khác. Assertions và exit codes vẫn đạt; chưa xác nhận logging rotation ổn định, không sửa settings/runner ngoài phạm vi UI. Nếu cần tái kiểm logging, đóng các process test trước, chạy lần lượt hai lệnh backend ở trên; nếu vẫn lỗi do ứng dụng đang chạy, người phụ trách cấu hình log directory riêng cho môi trường test trong nhiệm vụ hạ tầng riêng, không xóa/move operational log hoặc dừng ứng dụng thật trong đợt UI này. Không coi kết quả suite này là kiểm thử browser/production.

**Commit/bàn giao:** Giai đoạn 0 `0a8cee85cef5966c3cc9b74b9663e38d93a31b3f` chỉ chứa kiểm kê nhật ký. Giai đoạn 1 gom MASTER/tokens/hướng dẫn và cập nhật cùng mục nhật ký trong commit `feat(ui): define proposed accessible IHRMS design system`; xem SHA bằng `git log -2 --oneline`. Stage riêng nội dung đợt này, giữ nguyên mục backup ngoài index. Không push/deploy. Chủ dự án cần duyệt MASTER/tokens, quyết định thống nhất DESIGN.md trước Giai đoạn 2; kiểm thử browser dữ liệu giả ở 360/768/1024/1440px, keyboard/screen reader, zoom 200%, reduced motion, từng vai trò và print HCNS sau khi áp dụng. Không tuyên bố đã đạt WCAG hoặc đã UAT giao diện.


Đây là **nơi ghi nhận tập trung duy nhất** các đợt thay đổi lớn, thao tác kiểm tra, quyết định và việc cần chủ dự án thực hiện. Cập nhật tiếp vào tệp này thay vì tạo log mới cho từng lần làm việc. Không ghi secrets, dữ liệu cá nhân hoặc nội dung `.env`.

## 2026-10-09 — Lập cổng rủi ro và kế hoạch UAT trên máy chủ công ty đến 16/10

**Mục tiêu/phạm vi:** theo yêu cầu chủ dự án, viết rõ rủi ro khi triển khai IHRMS lên máy chủ công ty có Internet và lộ trình một tuần để có thể bắt đầu UAT dữ liệu giả từ 16/10/2026; không cấu hình hay triển khai máy chủ trong lượt này. Tài liệu mới: `docs/Ke_Hoach_UAT_May_Chu_Cong_Ty_2026-10-16.md`; đối chiếu `docs/Server_Trial_Readiness_2026-09-27.md`, `docs/08_Deployment_Standards.md`, settings và CI hiện có cùng tài liệu chính thức Django/Microsoft.

**Đã kiểm tra:** `main` đồng bộ `origin/main`; working tree có sẵn thay đổi chưa commit ở `docs/PROJECT_WORK_LOG.md` và `ops/reset_qa_data.py`, được giữ nguyên. `NUL` do chủ dự án báo đã xóa; kiểm tra cả đường dẫn thường và đường dẫn Windows mở rộng xác nhận tệp không còn. Đọc settings runtime an toàn, không in secret: SQL Server `qlhcns`, `APP_ENV=development`, `DEBUG=True`, HTTPS enforcement tắt, M365 storage bật. Kiểm tra bản backup ở gốc `D:\QLHCNS-Backups` vẫn tồn tại và ACL còn quyền `Authenticated Users`/`Users` rộng. Chưa có bằng chứng trong lượt này rằng secret M365 từng lộ đã được thu hồi hoặc máy chủ công ty đã được cấu hình.

**Kết quả:** tài liệu phân loại rủi ro HTTP/debug, secret/Graph/SharePoint, SQL và backup, mạng Internet, SMTP/tác dụng phụ nghiệp vụ, thiếu dữ liệu phân quyền chéo phòng và rollback; đưa mô hình tách UAT, lịch 09–16/10 theo người phụ trách, cổng GO/NO-GO và quy trình quay lui. Chỉ đề xuất GO cho UAT với dữ liệu giả khi IT/DBA/chủ dự án xác nhận đủ điều kiện; không coi là phê duyệt production hoặc dữ liệu thật. Kiểm tra tài liệu và `git diff --check` ở cuối đợt; không chạy test ứng dụng vì chỉ bổ sung tài liệu.

**Nhánh/commit và việc còn mở:** `main`, chưa commit/push trong lượt này. Chủ dự án cần chốt hostname/VM/SQL UAT, nhóm tester, phạm vi thử M365/email, người giữ backup/secret, người có quyền rollback và người ký GO/NO-GO. IT cần xác minh thu hồi secret cũ, khóa ACL backup gốc, chuẩn bị TLS/firewall/DB và môi trường tích hợp UAT riêng trước ngày 12/10. Nếu thiếu một điều kiện chặn, lùi lịch test thay vì dùng cấu hình phát triển trên máy chủ.

## 2026-10-09 — Dọn tệp thừa và UAT Edge 11 vai trò

**Mục tiêu/phạm vi:** theo yêu cầu tiếp theo, dọn đúng hai tệp chưa theo dõi và kiểm thử đăng nhập/quy trình nghiệp vụ trong trình duyệt bằng tài khoản QA ở SQL Server local `qlhcns`. Xác nhận `main` đồng bộ `origin/main` và không có thay đổi tracked trước khi làm.

**Đã làm:** kiểm tra `src/qlhcns` là tệp 0 byte, xóa bằng `apply_patch`; xác nhận không còn trong `git status`. Kiểm tra `NUL` thực ra không rỗng (38.707 byte), chỉ chứa CSS Tailwind sinh nhầm; cơ chế chạy lệnh chặn xóa tệp mang tên dành riêng của Windows, còn `apply_patch` không nhận diện được đường dẫn `NUL`. Không xóa vòng qua công cụ. Dựng Django cục bộ chỉ trên `127.0.0.1:8001`, mở Edge; sau khi chủ dự án báo đã bật quyền chọn tệp, nạp CSV QA vào bộ nhớ tab qua HTML hỗ trợ tạm (không upload CSV lên máy chủ), chuyển tài khoản bằng POST login với CSRF. HTML tạm đã xóa, tab QA đóng và server dừng; không ghi CSV/mật khẩu vào repo hay nhật ký. Bổ sung `ops/reset_qa_data.py` để sau khi tạo tài khoản gán một QA `DEPT_MANAGER` làm quản lý phòng ban đầu tiên, giúp kiểm thử luồng giới hạn phạm vi; áp dụng cùng gán vào DB QA hiện tại sau khi xác nhận vị trí quản lý đang trống.

**Kiểm tra và kết quả:** trước khi bật quyền Edge, đăng nhập qua Django Test Client bằng POST `/portal/login/` thành công cho **11/11 vai trò** với một tài khoản QA/vai trò; GET bảy đường dẫn mỗi vai trò (`/portal/`, hồ sơ, nghỉ phép, báo cáo, tuyển dụng, nhân viên HR, phiếu lương) không phát sinh exception. HTTP 302 tại Báo cáo với vai trò không được cấp quyền là chuyển hướng có chủ đích, không phải lỗi. Sau khi chủ dự án bật quyền, **Edge đăng nhập thành công 11/11 vai trò**, Trang chủ hiện đúng vai trò/menu và trang nghiệp vụ đại diện mỗi vai trò tải được: admin (SUPER/SYS), Báo cáo (Director), hồ sơ HR, tuyển dụng (HR Officer/Dept Manager), Thang bảng lương (Finance), Phiếu lương (Employee), tiến độ dự án (Project Manager/Coordinator/CBDA). Xác nhận menu HR Manager có năm mục duyệt; truy cập trực tiếp Thang bảng lương được cho Director/Finance, bị từ chối với Employee/HR Manager/Project Manager. Luồng QA thực tế trên Edge: Employee tạo đơn nghỉ không lương giả lập 19–20/10/2026 → HR Manager duyệt → Employee thấy `Approved`; Dept Manager tạo đề xuất tuyển dụng giả lập `QA-UAT-20261009-01` → HR Manager duyệt → trạng thái `Approved`. ORM kiểm tra lại manager scope và hai trạng thái đều đúng. `venv\Scripts\python.exe -m py_compile ops\reset_qa_data.py`, `git diff --check` và `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.portal.tests_recruitment_accounting_navigation apps.portal.tests.PortalSensitiveWorkflowTests.test_project_task_menu_is_listed_under_project_activities` (4/4) đạt. Không tái chạy toàn bộ 408 test sau thay đổi nhỏ trong dữ liệu mẫu.

**Nhánh/commit và việc còn mở:** `main`, mục nhật ký và thay đổi script chưa commit/push; đợt này không có yêu cầu commit/push mới. Hai bản ghi giả lập đã duyệt vẫn ở `qlhcns` để chủ dự án đối chiếu UAT; không xóa tự động. Chưa kiểm tra đầy đủ tất cả thao tác của 11 vai trò, quyền liên phòng ban, SharePoint/email thực hoặc đăng nhập bằng toàn bộ 33 tài khoản; vì các QA Employee chủ yếu cùng một phòng ban nên cần bộ dữ liệu phân tán hơn trước khi đánh giá phạm vi dữ liệu. Cần người dùng có quyền trên filesystem xóa chính xác `D:\QLHCNS\NUL` (tệp CSS sinh nhầm) bằng đường dẫn Windows mở rộng; công cụ hiện tại chặn thao tác. Không xóa tệp khác hoặc dùng `git clean` diện rộng. Có thể tắt lại quyền `Allow access to file URLs` của tiện ích Edge sau UAT nếu không còn cần chọn tệp.

## 2026-10-09 — Reset dữ liệu QA SQL Server và tạo 33 tài khoản theo vai trò

**Mục tiêu/phạm vi:** theo xác nhận trực tiếp của chủ dự án, xóa toàn bộ dữ liệu nghiệp vụ trong DB local `qlhcns` (gồm bản ghi soft-delete), giữ schema và 28 bảng danh mục/cấu hình; tạo 3 tài khoản/hồ sơ nhân viên giả lập cho mỗi một trong 11 vai trò. Không động đến SharePoint, email, media hoặc DB khác ngoài bản phục hồi thử riêng.

**Sao lưu trước khi xóa:** xác nhận `main` đồng bộ `origin/main` trước khi làm; DB cấu hình là SQL Server `qlhcns` với 107 bảng. Tạo bản `.bak` `COPY_ONLY, CHECKSUM` và chạy `RESTORE VERIFYONLY`; bản backup cuối tại `D:\QLHCNS-Backups\private_sql_20261009\qlhcns_pre_reset_final_20261009_153550_98abda43.bak` (23.290.368 byte, SHA-256 `1FD87CC25C3851E18512D031F44C0A8221F06EEF3C71D96C8EDD446858E1C87A`). Thư mục riêng bỏ kế thừa ACL, chỉ tài khoản hiện tại, Administrators, SYSTEM và dịch vụ SQL Server được truy cập. Bản backup đầu ở gốc `D:\QLHCNS-Backups\qlhcns_pre_test_cleanup_20261009_152517_ec440de3.bak` vẫn còn ACL kế thừa quyền đọc rộng; tài khoản hiện tại không sở hữu nên lệnh đổi ACL/takeown bị từ chối. Cần quản trị viên hạ tầng khóa quyền hoặc chuyển/xóa bản đầu sau khi xác nhận bản backup cuối phục hồi được; bản cuối đã được `RESTORE VERIFYONLY` xác nhận.

**Quy trình:** thêm `ops/reset_qa_data.py` với allowlist đúng hai DB `qlhcns`/`qlhcns_reset_preview_20261009`, kiểm tra đủ 107 bảng và 11 vai trò, giữ 28 bảng cấu hình, dọn 79 bảng còn lại trong transaction, làm rỗng FK nullable từ danh mục sang dữ liệu nghiệp vụ và kiểm tra lại constraint. Trước khi áp dụng gốc, phục hồi backup vào `qlhcns_reset_preview_20261009`, chạy reset ở bản thử thành công: 33 user, 33 nhân viên, 3 user/vai trò, các bảng Project/Task/OfficialDispatch rỗng, 0 FK/check constraint untrusted. Sau đó áp dụng cùng quy trình vào `qlhcns`; kiểm tra tương tự đạt. Bản thử đã được xóa sau khi xác nhận đúng tên DB và đường dẫn data/log; DB gốc còn nguyên schema. Mật khẩu ngẫu nhiên lưu ngoài Git ở `D:\QLHCNS-Backups\private_sql_20261009\qa-credentials-20261009.csv`; 33/33 hash khớp, 6 staff và 3 superuser. Không ghi mật khẩu vào nhật ký/Git/chat. Tạo thêm baseline backup sau reset tại `D:\QLHCNS-Backups\private_sql_20261009\qlhcns_qa_baseline_20261009_154006_ed817182.bak` (23.224.832 byte, SHA-256 `5B89FA2BA46F6CD59E92214DD26B6384801534ABE422411506A0A97F5C958883`), `RESTORE VERIFYONLY` đạt.

**Kiểm tra và giới hạn:** bản sửa bỏ lương khỏi Trang chủ của đợt trước được giữ nguyên; `ops/reset_qa_data.py` biên dịch Python đạt. Full SQLite trước reset phát hiện 408 test và kết thúc exit 0. Full SQL Server cô lập đạt **408/408** trong 381.214 giây, DB `test_ihrms_e58372a444ca4cdc839cec55cbc93034` đã được runner xóa; xác nhận không còn DB `test_ihrms_*` và DB `qlhcns` vẫn có 33 user/33 nhân viên. `git diff --check` đạt. Chưa kiểm thử đăng nhập trình duyệt từng vai trò, workflow ghi dữ liệu, SharePoint thật hoặc restore drill đầy đủ của bản backup cuối ngoài `RESTORE VERIFYONLY`. File CSV của lần thử vẫn ở thư mục riêng nhưng không thuộc DB đang dùng; không dùng nhầm với CSV chính thức.

**Nhánh/commit/push:** `main`; mã reset và thay đổi Trang chủ được commit tại `28f763b`, push `origin/main` thành công. ZIP mã nguồn của commit đó tại `D:\QLHCNS-Backups\private_sql_20261009\IHRMS-source-28f763b.zip` (5.542.337 byte, 635 mục, SHA-256 `01A8EF736B671B835E3ABEBB51774EC5459889C563B24DC9A2A93842DCE0100B`), đã kiểm tra không chứa `.env`, DB, bản `.bak` hoặc CSV tài khoản và ACL được giới hạn. **Hành động chủ dự án:** bảo quản file CSV tài khoản như bí mật; đổi mật khẩu trước khi dùng ngoài QA, khóa ACL bản backup đầu ở thư mục gốc bằng tài khoản có quyền quản trị, rồi xác nhận UAT bằng từng vai trò.

## 2026-10-09 — Bỏ thông tin lương nhạy cảm khỏi Trang chủ

**Mục tiêu/phạm vi:** không hiển thị “Lương kỳ gần nhất” trên Trang chủ; nhân viên xem lương tại Cá nhân → Phiếu lương. Không thay đổi phép tính lương, dữ liệu, phân quyền hay phát hành phiếu.

**Tệp/thay đổi:** `src/apps/portal/templates/portal/dashboard.html` bỏ thẻ lương và xếp hai KPI cá nhân còn lại thành hai cột ở màn hình rộng. `src/apps/portal/views/core.py` bỏ truy vấn `latest_payroll` không còn dùng; không đưa dữ liệu lương vào context Trang chủ. Menu Phiếu lương ở `src/templates/base.html` và view `payslip_list` giữ nguyên: chỉ hiển thị phiếu đã phát hành của kỳ đã chốt cho nhân viên đăng nhập. `src/apps/portal/tests.py` bổ sung kiểm tra Trang chủ không có KPI/context lương nhưng vẫn có đường vào Phiếu lương.

**Kiểm tra:** xác nhận nhánh `main` đồng bộ `origin/main` (0/0), giữ nguyên thay đổi nhật ký có sẵn trước lượt này. `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.portal.tests.PortalSensitiveWorkflowTests.test_employee_sees_only_issued_payslips_from_locked_periods apps.portal.tests.PortalSensitiveWorkflowTests.test_project_task_menu_is_listed_under_project_activities` đạt 2/2; system check không cảnh báo. `rg` xác nhận không còn tham chiếu `latest_payroll` trong mã ứng dụng. `git diff --check` đạt. Chưa chạy full suite/SQL Server hoặc UAT trình duyệt trong lượt này.

**Nhánh/commit:** `main`, thay đổi được commit cùng reset QA tại `28f763b`. **Còn mở/hành động chủ dự án:** tải lại Trang chủ, xác nhận chỉ còn hai KPI cá nhân và xem thử Cá nhân → Phiếu lương bằng tài khoản phù hợp; báo lại nếu bố cục hoặc quyền thực tế khác dự kiến.

## 2026-10-09 — Đồng bộ bố cục và màu Trang chủ/Báo cáo với tiến độ dự án

**Mục tiêu/phạm vi:** căn lại lưới KPI Trang chủ, làm rõ KPI đầu trang Báo cáo, giữ hàng nhãn/số nhất quán và áp dụng bảng màu của trang Theo dõi tiến độ dự án cho hai dashboard này. Không đổi số liệu, quyền truy cập, xuất tệp hay cấu trúc dữ liệu.

**Thay đổi:** thêm `src/static/css/home_dashboard.css` cho thẻ trắng viền rõ, chiều cao/vùng nhãn đồng đều, số neo ở đáy; điều chỉnh `dashboard.html` để nạp CSS và đưa kỳ lương vào vùng nhãn, giữ giá trị lương cùng hàng với KPI khác. Sau phản hồi qua hai bản demo, chủ dự án chọn phương án **Thẻ gọn một hàng**: giảm chiều cao/padding KPI, cố định sáu ô tổng quan và năm ô dự án trên một hàng ở màn hình rộng, xếp lại thành ba/hai/một cột theo breakpoint ở màn hình hẹp; thêm khoảng cách trước tiêu đề Tiến độ hoạt động dự án. Sửa `report_dashboard.css` để bỏ khối xanh/chữ trắng khó đọc, dùng nền trắng/chữ đậm, thẻ KPI đồng chiều cao, màu xanh–lục–đỏ–hổ phách như trang tiến độ và giới hạn chiều rộng nội dung. Theo yêu cầu tiếp theo, áp dụng cùng mẫu gọn cho Báo cáo: sáu KPI tổng quan trên một hàng ở màn hình rộng, bỏ viền khung bao chồng lên viền thẻ, thu chiều cao KPI trong từng nhóm và nới khoảng cách giữa tổng quan/biểu đồ/các nhóm; thu về ba/hai/một cột khi màn hình hẹp. Gắn phiên bản URL CSS ở hai template để trình duyệt/service worker lấy bản mới. Bổ sung assertion render CSS ở hai test hiện có.

**Kiểm tra:** trước khi sửa xác nhận `main`, chỉ có thư mục `outputs/` untracked của người dùng, fetch `origin/main` và lệch 0/0; giữ nguyên `outputs/`. Lượt chỉnh tiếp theo cũng xác nhận `main` đồng bộ `origin/main`, giữ nguyên mọi sửa đổi chưa commit. `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.portal.tests_report_dashboard` đạt 5/5; sau lượt tinh chỉnh Báo cáo chạy lại cùng lệnh, đạt 5/5. Chạy `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.portal.tests.PortalSensitiveWorkflowTests.test_project_task_menu_is_listed_under_project_activities apps.portal.tests_report_dashboard.ReportDashboardTests.test_report_hub_renders_all_available_sections_and_export_actions` đạt 2/2; Django system check trong runner không cảnh báo. `git diff --check` đạt. Chưa kiểm tra bằng trình duyệt có đăng nhập hoặc chụp màn hình ở các độ rộng nên chưa xác nhận pixel-perfect trong môi trường người dùng.

**Nhánh/commit:** `main`. Trong lúc kiểm thử, một thao tác khác đã commit/push các thay đổi giao diện ở `988324d` và cập nhật tiếp ở `5c2caae`; đã xác nhận `origin/main` trỏ tới `5c2caae`. Các commit đó không do lượt kiểm thử này tạo. Mục nhật ký bổ sung trạng thái này hiện chưa commit/push. **Còn mở/hành động chủ dự án:** tải lại Trang chủ và Báo cáo (nếu tab cũ vẫn giữ CSS, dùng Ctrl+F5) rồi kiểm tra trên kích thước màn hình thực tế; gửi ảnh nếu còn thẻ lệch hoặc chữ mờ. Không cần thay đổi cấu hình hay dữ liệu.
## 2026-10-09 — Khởi tạo SQL Server local sau clone và xác minh HEAD mới

**Mục tiêu/phạm vi:** tiếp tục bootstrap clone sau khi chủ dự án bật TCP/IP, restart SQL Server và tạo database `qlhcns`. Chỉ áp dụng schema lên DB mới đã kiểm tra trống; không thay đổi dữ liệu nghiệp vụ, không sửa nội dung `.env`, không deploy.

**Git/dependency:** xác nhận `main`, working tree chỉ có CSS generated từ lượt build trước; fetch thấy `origin/main` mới hơn 2 commit. Stash riêng CSS generated, fast-forward tới `6859e3c`, build lại `npm run build:css` theo source mới và bỏ stash sau khi xác nhận utility được giữ. Cài requirements mới có `python-docx==1.2.0`, `python-pptx==1.0.2`. Cuối đợt `main` đồng bộ `origin/main`; CSS generated `src/static/css/tailwind.css` và nhật ký này là hai thay đổi local chưa commit.

**Database/môi trường:** xác nhận instance `SQLEXPRESS` chạy, TCP/IP bật, cổng động hiện tại `59299`; SQL Browser đang Stopped/Disabled. Cấu hình `.env` dùng `localhost\SQLEXPRESS`, vì vậy kết nối TCP theo cấu hình đó bị từ chối. Dùng override chỉ trong từng tiến trình (`DB_HOST=localhost`, `DB_PORT=59299`) để kết nối; giữ nguyên `.env` và secrets. DB `qlhcns` xác nhận có 0 bảng trước migrate; chạy `manage.py check` đạt, `manage.py migrate --noinput` áp dụng toàn bộ migration, sau đó xác nhận **107 bảng** và `migrate --check` exit 0. Chưa tạo superuser hoặc khởi động server.

**Kiểm tra:** do hai package mới chưa có trong virtualenv ở lượt SQL Server đầu, test dashboard báo ImportError `No module named 'docx'`; cài requirements mới và focused `apps.portal.tests_report_dashboard` đạt **5/5**. Full suite SQL Server trên HEAD `6859e3c` đạt **408/408**, không lỗi; dùng runner với DB test `test_ihrms_<UUID>` riêng, M365 tắt, runner đã hủy DB sau khi chạy. Xác nhận không còn DB `test_ihrms_*`; Django system check đạt, `pip check` không có dependency lỗi, `git diff --check` đạt (còn cảnh báo newline CRLF chuẩn của file CSS trên Windows).

**Tài khoản QA và nghiệp vụ:** theo 11 role code đang khai báo trong `src/apps/security/permissions.py`, tạo 3 account cho mỗi role (**33 users/33 synthetic employees**) trong `qlhcns`, kèm 1 tổ chức và 3 phòng ban/vị trí QA. Prefix username `qa20261009_`, employee code `QA20261009-`; mọi email dùng miền `.example.invalid`. Xác nhận 3 user/role, mật khẩu hash khớp CSV, account active, kiểm tra toàn bộ `PERMISSION_MATRIX` cho từng tài khoản và authentication backend; 33/33 truy cập `/portal/`, `/portal/profile/` và boundary của `/admin/` đúng dự kiến. Ba `SUPER_ADMIN` là Django superuser; ba `SYS_ADMIN` là staff không-superuser; role còn lại không có cờ staff. Credential CSV ở `%TEMP%\IHRMS_QA_Accounts_20261009.csv`, mật khẩu ngẫu nhiên, ACL bỏ kế thừa và chỉ cho user hiện tại/SYSTEM/Administrators đọc. Không chứa credentials trong repo hoặc log.

**Giới hạn kiểm thử:** full **408/408** là suite tự động toàn dự án trên SQL Server bằng DB disposable, không phải UAT trình duyệt cho mọi thao tác và không chạy từng workflow qua từng account QA. Smoke test 33 account kiểm tra authentication, permission matrix và hai trang portal cơ bản. M365/SharePoint thật không được gọi. Mã permission hiện có 11 role nhưng tài liệu RBAC và docstring `Role` còn ghi 8; không chỉnh tài liệu/mã role trong phạm vi này.

**Còn mở/hành động chủ dự án:** `.env` chưa được chỉnh nên lệnh Django thông thường vẫn cần giải quyết SQL Browser/cổng: đặt cổng TCP static cho `SQLEXPRESS` rồi cấu hình `DB_HOST=localhost`, `DB_PORT=<cổng static>` trong `.env`, hoặc bật SQL Browser để phân giải tên instance. Cổng `59299` hiện tại là cổng động và có thể đổi sau restart. Sau đó tạo tài khoản bằng `venv\Scripts\python.exe src\manage.py createsuperuser` và chạy server nếu cần. Không kiểm thử tích hợp M365/SharePoint thật.

**Commit/push:** không tạo commit/push; HEAD tại thời điểm hoàn tất là `6859e3c`.

## 2026-10-07 — Tạo tài liệu mô tả thiết kế giao diện quản trị

**Mục tiêu/phạm vi:** tạo tài liệu riêng trong `docs/` để mô tả nguồn cấu hình giao diện admin của IHRMS và làm tài liệu tham khảo khi áp dụng ý tưởng cho QLHD, `nhaplieu_app`. Chỉ cập nhật tài liệu, không đổi mã ứng dụng hoặc cấu hình.

**Tệp liên quan:** thêm `docs/ADMIN_UI_DESIGN.md`, nêu cấu hình Jazzmin/AdminLTE 3 trong `src/config/settings.py`, phân biệt Django Admin với portal tại `src/templates/base.html` và CSS liên quan, đồng thời ghi nguyên tắc tái sử dụng cùng lưu ý về framework, app/model/URL và quyền ở dự án đích.

**Kiểm tra:** xác nhận nhánh `main`, working tree sạch trước khi sửa và đồng bộ `origin/main`; đối chiếu nội dung với cấu hình `JAZZMIN_SETTINGS`, `JAZZMIN_UI_TWEAKS` và các template/static liên quan. `git diff --check` đạt. Đây là thay đổi tài liệu nên không chạy test ứng dụng.

**Commit/push:** chưa commit/push. **Việc còn mở:** chưa đánh giá framework, phiên bản giao diện hay yêu cầu thương hiệu riêng của QLHD và `nhaplieu_app`; cần khảo sát hai dự án trước khi chuyển thiết kế thành thay đổi mã.

## 2026-10-07 — Thêm và chạy subagent review IHRMS ở chế độ FULL/FIX

**Mục tiêu/phạm vi:** thêm subagent cấp dự án dành cho Cursor/Codex, tách biệt với agent Sixth hiện có. Agent hỗ trợ review `FULL`/`CHANGES`, mặc định `REVIEW`, và chỉ chuyển sang `FIX`, commit hoặc push khi nhiệm vụ cho phép rõ ràng.

**Tệp/thay đổi:** thêm `.cursor/agents/ihrms-reviewer.md` với quy trình đọc `AGENTS.md` và hướng dẫn review, bảo vệ thay đổi cục bộ, kiểm tra RBAC/luồng nghiệp vụ/toàn vẹn dữ liệu/SQL Server, dùng DB và media cô lập, yêu cầu bằng chứng kiểm thử và giới hạn dữ liệu nhạy cảm. Không thay đổi mã ứng dụng, schema hay dữ liệu nghiệp vụ.

**Lần tạo subagent:** xác nhận nhánh `main` đồng bộ `origin/main` và working tree sạch trước khi tạo; kiểm tra frontmatter YAML, tên agent và `git diff --check`. Chưa chạy subagent ở bước tạo; chưa commit/push.

**FULL/FIX đã thực hiện:** dùng chính subagent mới để kiểm kê 23 app cùng `src/config`, migration, template/static, `ops` và hai workflow CI; đọc charter, thiết kế bảo mật/CSDL, ma trận RBAC, workflow và chuẩn kiểm thử. Rà các luồng HR, chấm công/nghỉ/lương/hợp đồng, tuyển dụng, tài sản/văn phòng/mua sắm, task/KPI/activity/lifecycle, tài liệu HCNS/private file, báo cáo, M365/storage, cấu hình production và backup. Đây là review trực tiếp theo rủi ro và kiểm thử tự động, không phải Sixth/Bugbot hoặc UAT trình duyệt.

**Finding và thay đổi:** (P2) chín điểm trong portal lấy `timezone.now().date()`, tức ngày UTC, làm kỳ chấm công, ngày phụ lục hợp đồng, ngày đề nghị VPP/mua sắm và bộ lọc bốn báo cáo có thể lùi một ngày trong khoảng 00:00–06:59 giờ Việt Nam; đã đổi sang ngày địa phương. Review chéo sau subagent còn phát hiện số đề nghị `VPP/MS` và số phụ lục tự sinh `GH` vẫn định dạng từ UTC, khiến mã và ngày trên cùng bản ghi có thể lệch nhau; đã dùng chung một `timezone.localtime()` cho cả mã và ngày. (P2) HR Officer/HR Manager có quyền `approve_profile_change_request` và có thể duyệt nhưng tài khoản chưa liên kết Employee lại bị chặn ở danh sách/tải chứng từ; đã cho quyền duyệt xem hồ sơ chờ và tệp tương ứng, giữ nguyên giới hạn nhân viên thường chỉ xem hồ sơ của mình. (P3) thư mục upload dùng ngày hệ điều hành thay vì múi giờ Django; đã dùng `timezone.localdate()`. Bỏ khóa Jazzmin `dark_mode_theme=None` đã deprecated và bị bỏ qua. Thêm bốn regression test bao phủ mốc 00:30 giờ Việt Nam, ngày và mã tự sinh của bản ghi, đường dẫn tệp và HR reviewer chưa gắn Employee; không đổi schema hay quy tắc lương/phép.

**Kiểm tra thực tế:** tập trung SQLite `apps.common.tests apps.hrm.tests apps.portal.tests_review_hardening` đạt **38 tests, 37 đạt/1 skip SQL Server-only**. Lần SQL tập trung đầu phát hiện fixture mới có NationalID dài quá giới hạn (chỉ lỗi test), đã rút ngắn; bốn test mới chạy lại SQL Server đạt **4/4**. Full cuối `ops/run_tests.py --backend sqlite` đạt **386 tests, 382 đạt/4 skip SQL Server-only**, 151.729 giây; full `--backend sqlserver` đạt **386/386**, 190.222 giây, DB `test_ihrms_b8bf5267fa1f4476b683dcd3f3299b1a` đã được runner xóa. Sau tinh chỉnh guard danh sách cuối, riêng sáu test profile request chạy lại đạt **6/6 trên từng backend**. Logs `%TEMP%\ihrms-subagent-fullfix-{sqlite,sqlserver}-20261007.log`. `manage.py check`, migration drift, compile Python, parse YAML, `git diff --check` đạt; `check --deploy` với production giả lập bật HTTPS/HSTS không cảnh báo. `pip check`, `pip-audit`, `npm audit`, build CSS đạt; backup mock Full/Log × Express/Standard/Failure đạt 6/6, không phải restore thật. Bandit không có trong virtualenv (`No module named bandit`) nên không ghi là đã chạy.

**Bảo vệ dữ liệu/trạng thái:** mọi test dùng SQLite memory hoặc SQL Server database/media dùng một lần, M365 tắt; không đọc/ghi dữ liệu nghiệp vụ gốc, không migrate/deploy, không gửi email/SharePoint. Giữ nguyên thay đổi cục bộ định nghĩa subagent và mục nhật ký ban đầu. Theo yêu cầu, chưa commit/push. Chưa kiểm thử UAT trình duyệt, M365/SharePoint thật, Word/Excel desktop, IIS, tải lớn hoặc restore backup thật; không kết luận hết lỗi 100%.

## 2026-10-07 — FIX: hoàn thiện các finding review sau commit 68a5228

**Mục tiêu/phạm vi:** xác minh và sửa toàn bộ finding đã nêu cho cấu hình M365, ngày báo cáo, phạm vi RBAC, booking đồng thời, audit quyết định, lỗi im lặng và CSS in. Làm trên `main`, bắt đầu từ `68a5228`, giữ dữ liệu nghiệp vụ nguyên trạng. Test dùng SQLite memory/SQL Server `test_ihrms_<UUID>` và media tạm; không migrate/deploy DB đang dùng, không gọi M365 hoặc gửi email.

**Thay đổi:** thêm `config.env.env_flag()` và dùng chung cho các cờ boolean; hỗ trợ `DB_EXTRA_PARAMS` để job SQL Server CI dùng ODBC 18 an toàn trong container. Báo cáo/dashboards dùng `timezone.localdate()`, test khóa ngày cố định. Thêm helper phạm vi phòng ban/nhân viên tại `security.data_access`, áp cho tuyển dụng, giao việc, KPI và sự kiện; chặn trưởng phòng tạo sự kiện toàn công ty bằng phòng ban trống. Booking Approved chỉ full-clean khi thay đổi trường ảnh hưởng xung đột, khóa tài nguyên chung và đổi tài nguyên mất thành `ValidationError`; view không full-clean kép. Quyết định mới ghi cả `created_by`/`modified_by`, bỏ câu `form.errors` vô tác dụng và escape `page_css` ở cả trang soạn/chi tiết.

**Kiểm thử mới/hardening:** thêm test parse `True/true/TRUE/1/t`, false/rỗng/giá trị lạ/default; báo cáo hợp đồng mock ngày địa phương; audit quyết định; tài nguyên booking không tồn tại; trưởng phòng không thể tạo sự kiện toàn công ty. Thêm workflow `.github/workflows/sqlserver-regression.yml` chạy full suite lúc 00:30 thứ Hai giờ Việt Nam và thủ công; cập nhật `docs/07_Testing_Standards.md` để phân biệt SQLite với kiểm tra khóa SQL Server.

**Kết quả cục bộ:** tập trung SQLite **105 tests, 102 đạt/3 skip SQL Server-only, 0 lỗi**; tập trung SQL Server **105/105 đạt**; regression scope cuối **57 tests, 56 đạt/1 skip SQL Server-only**. Full cuối SQLite **382 tests, 378 đạt/4 skip SQL Server-only, 0 lỗi**, 192.297 giây; full cuối SQL Server **382/382 đạt**, 209.348 giây, DB test đã xóa. `manage.py check`, `makemigrations --check --dry-run`, compile Python, parse YAML và `git diff --check` đạt. `check --deploy` với cấu hình production giả chỉ còn cảnh báo HSTS chưa bật, phù hợp chính sách chờ IT xác nhận toàn bộ host HTTPS. `pip check`, `pip-audit`, `npm audit`, build CSS đạt; 6/6 backup mock đạt (không phải restore SQL thật). Logs nằm trong `%TEMP%` với tiền tố `ihrms-review-fix-*20261007.log`.

**Commit/push/CI:** mã và kiểm thử được commit tại `80bb98f` (`fix: harden scoped workflows and SQL Server regression`) và đã push thành công lên `origin/main`. GitHub Actions chưa xác minh được cho SHA này: `gh run list` và `gh workflow list` trả HTTP 401 `Bad credentials`; trình điều khiển trình duyệt cũng báo Chrome không khả dụng nên không thể dùng phiên web thay thế. Sau khi xác thực lại GitHub CLI, chạy `gh auth login -h github.com`, rồi `$sha = (git rev-parse HEAD).Trim(); gh run list --branch main --commit $sha --limit 5`; có thể kích hoạt job định kỳ bằng `gh workflow run sqlserver-regression.yml --ref main` và theo dõi bằng `gh run watch <RUN_ID> --exit-status`.

**Còn mở:** workflow SQL Server mới chỉ được parse và full suite đã chạy trên SQL Server cục bộ; trạng thái GitHub Actions đúng SHA sẽ được xác nhận sau push. Chưa deploy, chưa kiểm thử M365/SharePoint thật, IIS, restore backup thật hoặc UAT dữ liệu ẩn danh. Cảnh báo Jazzmin `dark_mode_theme` deprecated vẫn xuất hiện nhưng không gây lỗi test và không thuộc finding này.

## 2026-10-06 — Kiểm thử demo toàn hệ thống và cập nhật hướng dẫn

**Mục tiêu/phạm vi:** theo yêu cầu cho phép tự test demo toàn bộ tính năng, lập báo cáo và cập nhật hướng dẫn. Chạy lại toàn bộ suite trên cả hai backend cô lập; xác nhận thêm các luồng browser đã đăng nhập cho 26 biểu mẫu HCNS, xuất tệp và thao tác từ NV & Hồ sơ. Không dùng dữ liệu nghiệp vụ thật, không gửi email, không migrate/deploy và không commit/push.

**Môi trường/bảo vệ dữ liệu:** nhánh `main`, HEAD `9fa7760`; giữ nguyên các thay đổi local hiện có và file untracked `src/qlhcns`. `ops/run_tests.py` dùng SQLite memory hoặc SQL Server `test_ihrms_<uuid>` dùng một lần, media tạm, email memory và M365 tắt. Browser dùng Edge headless với DB/media giả cô lập. Không đưa dữ liệu giả, tệp tải hay harness browser ngoài Git vào repository.

**Kết quả:** `venv\Scripts\python.exe ops\run_tests.py --backend sqlite` đạt **376 tests, 372 đạt/4 skip SQL Server-only, 0 lỗi**, 332.176 giây; log `%TEMP%\ihrms-demo-full-sqlite-20261006.log`. Cùng lệnh `--backend sqlserver` đạt **376/376, 0 skip/0 lỗi**, 282.505 giây; DB test đã bị runner xóa, log `%TEMP%\ihrms-demo-full-sqlserver-20261006.log`. Edge có đăng nhập: `live_browser_tests` đạt 1/1 cho 26 mẫu (preview/tải, dropdown, tự điền, in/mobile, cache cũ, validation/CSRF, 0 JavaScript error); `workflow_browser_tests dropdown_browser_tests` đạt 2/2 cho luồng nâng lương/bổ nhiệm/điều chuyển, khen thưởng/kỷ luật, hợp đồng và 26 xuất mẫu. Logs `%TEMP%\ihrms-demo-live-browser-final-20261006.log` và `ihrms-demo-workflow-browser-final-20261006.log`.

**Điều chỉnh harness:** hai assertion browser cũ giả định ô nhân viên/tài sản là text input. Mã hiện tại chủ đích dùng dropdown nên harness tạm được chỉnh để chọn option, tạo một tài sản giả và để trống mẫu ứng viên khi chưa chọn ứng viên. Không thay đổi mã sản phẩm hoặc quy tắc nghiệp vụ.

**Tài liệu cập nhật:** thêm `docs/Bao_Cao_Kiem_Thu_Demo_2026-10-06.md` (phạm vi, kết quả, giới hạn tích hợp) và `docs/Huong_Dan_Kiem_Thu_Demo_IHRMS.md` (kịch bản theo vai trò, biểu mẫu/xuất tệp và cách ghi nhận UAT). Phần còn cần chủ dự án xác nhận trên SIT/UAT: Word/Excel desktop, Outlook/M365/SharePoint, IIS/HTTPS/SQL Server vận hành, backup/restore, phân quyền lưu trữ, tải lớn/máy in và quy tắc báo cáo BHXH/PIT/chi phí phòng ban. Không kết luận “hết lỗi 100%” từ demo cô lập.

## 2026-10-06 — FULL/FIX: review toàn dự án và vòng kiểm thử hồi quy

**Mục tiêu/phạm vi:** theo yêu cầu “review toàn dự án, kiểm thử, fix lỗi, kiểm thử, fix lỗi”, review trực tiếp mã hiện tại, không chỉ diff. Đọc hướng dẫn review và định nghĩa Sixth để áp dụng quy trình; không tuyên bố đã chạy Sixth/Bugbot. Yêu cầu FIX mới của chủ dự án cho phép sửa lỗi, thay cho giới hạn chỉ đọc của yêu cầu `review-agent` trước đó.

**Git và bảo vệ dữ liệu:** xác nhận `main`, fetch `origin/main`, HEAD `9fa7760`, lệch 0/0 trước đợt. Chỉ giữ thay đổi thuộc nhiệm vụ; tệp untracked `src/qlhcns` có sẵn được giữ nguyên. Không sửa bản ghi nghiệp vụ gốc, không migrate DB đang dùng, không gửi thư hoặc ghi SharePoint. Các test dùng runner `ops/run_tests.py`: SQLite memory hoặc SQL Server `test_ihrms_<uuid>` dùng một lần, media tạm, email memory, M365 tắt. Browser dùng một SQLite/media mới trong `%TEMP%`, bind `127.0.0.1:8049`, dữ liệu giả; server đã dừng sau kiểm tra. Chưa commit/push/deploy.

**Phạm vi đã rà:** kiểm kê đủ 23 app: organization, hrm, recruitment, attendance, leave, payroll, contract, document/HCNS, asset, office, procurement, planning, project, activity, task, kpi, lifecycle, notification, m365, reporting, security, common, portal. Đọc các luồng chính/caller/guard về quyền theo vai trò và phòng ban, private files, HR effective-date, nguồn/snapshot HCNS, trạng thái/phê duyệt, chấm công/nghỉ, tính/khóa lương, tài sản/cấp phát, tuyển dụng, báo cáo, lifecycle, hoạt động dự án và thông báo; rà cấu hình, storage/Graph, admin dùng chung, CI, scheduler/backup, template/static. Kiểm tra AST của 306 tệp Python và biên dịch 86 template: đạt; resolver nạp 629 route, trong đó 142 route portal/reports/private-files. Đây là kiểm kê và rà theo rủi ro kèm test hiện có, không phải bằng chứng đã đọc từng dòng hoặc UAT mọi thao tác trong 23 app.

**8 lỗi xác nhận được đã sửa:**

- P1 — Lưu nháp QĐ dùng instance cũ có thể ghi đè trạng thái vừa trình duyệt: lấy lại bản ghi bằng `select_for_update` trong transaction, kiểm tra Draft/Rejected và mẫu trước khi cập nhật; từ chối bằng lỗi form 422, giữ snapshot/lịch sử hiện tại.
- P2 — Số QĐ 101 ký tự qua form rồi ném `ValidationError` 500 khi lưu CSDL: giới hạn form 100 ký tự đồng nhất model và chuyển lỗi model thành lỗi form, không ghi nháp khi lỗi.
- P2 — Sửa QĐ đã lưu làm mất nguồn `salary_id` và nhãn bản ghi: đọc selector đã allowlist từ snapshot, giữ nguyên provenance, không đọc lại giá trị lương nguồn để thay snapshot; đổi nhân viên thì reset nguồn về đúng employee mới.
- P2 — Trang chi tiết QĐ thiếu CSS HCNS và cấu hình `@page`, lịch sử lọt vào bản in: dùng CSS/profile/JS đặt tên PDF như trang soạn, ẩn lịch sử khi in.
- P1 — Trưởng phòng sửa POST để tạo đề xuất tuyển dụng ngoài phòng được quản lý: lấy department từ queryset đã giới hạn phía server, không tin ID người gửi.
- P2 — Trưởng phòng chưa gắn employee thấy danh sách phòng/nhân viên ngoài phạm vi ở tuyển dụng/giao việc: trả queryset rỗng, không cho tạo đề xuất.
- P2 — Excel hợp đồng “sắp hết hạn” bao gồm hợp đồng đã quá hạn nhưng còn Active: lọc từ hôm nay đến mốc N ngày và dùng cùng ngày tham chiếu để tính số ngày còn lại.
- P1 — Duyệt hai booking khác nhau chỉ khóa dòng booking, thiếu khóa chung phòng/xe: khóa tài nguyên trước booking tại portal, kiểm tra lại resource và trạng thái; model save của bản Approved khóa tài nguyên và kiểm tra lại xung đột, bao phủ cả Admin/save trực tiếp.

**Tệp thay đổi:** `src/apps/document/hcns/{catalog.py,views.py}`, `src/apps/document/tests_hr_workflow.py`, `src/apps/portal/templates/portal/personnel_decision_detail.html`, `src/apps/portal/views/{recruitment.py,tasks_kpi.py,office_procurement.py}`, `src/apps/portal/tests_review_hardening.py`, `src/apps/reporting/{services.py,tests.py}`, `src/apps/office/{models.py,tests.py}`, CSS build `src/static/css/tailwind.css`, nhật ký này. Không đổi schema; `makemigrations --check --dry-run` cuối báo No changes detected.

**Các vòng kiểm tra đã xác nhận:** `venv\Scripts\python.exe ops/run_tests.py --backend sqlite apps.document.tests_hr_workflow`: 30/30 đạt. Hai test phạm vi tuyển dụng mới tái hiện FAIL trước sửa; sau sửa toàn `apps.portal.tests_review_hardening`: 22 tests, 21 đạt/1 skip. `apps.reporting.tests`: 4/4 đạt sau sửa lỗi fixture đọc nhầm hàng đầu Excel; `apps.office.tests` vòng tập trung trước khi bổ sung hai test concurrency: 9/9 đạt. `--backend sqlserver apps.office.tests.ConcurrentBookingTests`: 2/2 đạt, hai thread duyệt đồng thời cùng phòng/xe, chỉ một Approved và một Pending, DB test đã được runner xóa. Vòng full SQLite đầu: 370 tests, 368 đạt/2 skip, 0 lỗi, 398.044 giây; chưa chứa toàn bộ các sửa bổ sung sau đó.

**Gate khác:** `venv\Scripts\python.exe -m pip check`: No broken requirements found; `-m pip_audit -r requirements.txt`: No known vulnerabilities found. `npm ci --ignore-scripts`, `npm audit --audit-level=low`: 0 vulnerabilities; `npm run build:css`: đạt, build lại CSS sau toàn bộ thay đổi để cập nhật class của trang quản lý. `check` và `makemigrations --check --dry-run` bằng settings SQLite `:memory:` + SECRET_KEY tạm: không lỗi/không drift. Lần check ban đầu dùng env DB_NAME=:memory: bị settings nối thành đường dẫn nên báo warning unable to open database file; đã chạy lại với override NAME đúng và không còn warning. `ops/backup/Test-BackupSafety.ps1 -Kind Full|Log -Scenario Express|Standard|Failure`: 6/6 đạt, chỉ mock sqlcmd, không phải restore SQL thật. `git diff --check`: đạt.

**Browser/print:** Edge headless đăng nhập phiên giả trên sandbox, trang chi tiết QĐ: header grid hai cột, CSS/profile trang giấy nạp đúng, Word tải thành công và đúng filename snapshot, nút In gọi print/đổi title đúng tên tệp, afterprint khôi phục title; print media ẩn menu/lịch sử và bỏ padding main. PDF một trang A4 theo lề nguồn; render bằng Poppler và kiểm tra ảnh trực quan: không có nội dung workflow/menu, vùng ký/nơi nhận tách hai cột. Viewport 390×844 không tràn ngang, 0 pageerror. Harness và ảnh/PDF nằm ngoài Git trong `%TEMP%`; không phải UAT Word desktop/máy in.

**Vòng full cuối:** `venv\Scripts\python.exe ops/run_tests.py --backend sqlite`: **376 tests, 372 đạt/4 skip dành riêng SQL Server, 0 lỗi**, 356.113 giây, exit 0; SQLite/media tạm đã dọn. `venv\Scripts\python.exe ops/run_tests.py --backend sqlserver`: **376/376 đạt, 0 skip/0 lỗi**, 455.945 giây, exit 0; DB SQL Server dùng một lần và media được runner xóa. Logs `%TEMP%\ihrms-fullfix-sqlite-final.log`, `%TEMP%\ihrms-fullfix-sqlserver-final.log`. Vòng full SQL Server trước các bổ sung cuối đạt **372/372**, 504.373 giây, DB tạm được xóa. Một smoke test endpoint ngoài Git sau sửa booking cũng đạt: HR duyệt được yêu cầu đầu, yêu cầu trùng phòng/xe còn Pending, 1/1, log `%TEMP%\ihrms-fullfix-booking-endpoints.log`. Bổ sung tổng cộng 10 test hồi quy trong repository; toàn bộ 14 tệp thay đổi đã review lại, Python parse và `git diff --check` cuối đạt. Còn warning Jazzmin về tùy chọn `dark_mode_theme=None` đã deprecated/ignored; không có lỗi framework hoặc test, chưa đổi lựa chọn theme trong đợt này.

**Còn mở/phần chưa kiểm thử:** chưa chạy UAT với dữ liệu thật, Word/Excel desktop, máy in vật lý, load test, restore backup thật, Microsoft Graph/SharePoint/email ngoài môi trường mock, CI remote của working tree chưa commit. Báo cáo BHXH, PIT theo năm và phân bổ chi phí lương đang là scaffold fail-closed chờ mẫu/quy tắc Kế toán xác nhận, không tự bổ sung quy tắc tài chính trong đợt sửa lỗi. Không cam kết dự án hết lỗi 100%. Chủ dự án restart QLHCNS ở cổng 8001, Ctrl+F5 và test thực tế các luồng QĐ/lương, tuyển dụng theo phòng và duyệt phòng/xe; trước triển khai, làm backup và release procedure hiện hành. Các thay đổi đợt này không cần migration mới.

## 2026-10-06 — Quản lý quyết định nhân sự chính thức

**Mục tiêu/phạm vi:** bổ sung bản ghi quyết định HCNS có snapshot nội dung, trạng thái Draft → PendingApproval → Approved → Issued, lịch sử thao tác, trang danh sách/chi tiết, tải lại Word và lưu PDF đã ký để ban hành. Không tự áp dụng quyết định lên hồ sơ lương/nhân viên; không thay luồng tài liệu chung.

**Git:** làm trên `main`; xác nhận nhánh đồng bộ `origin/main` trước khi sửa. Working tree ban đầu sạch. File untracked `src/qlhcns` không thuộc nhiệm vụ được giữ nguyên, không stage.

**Tệp/phân hệ:** `src/apps/document/models.py`, migration `0005_personnel_decision_workflow.py`, `src/apps/document/hcns/{views.py,choices.py}`, `src/apps/common/uploads.py`, `src/apps/security/{permissions.py,data_access.py,files.py}`, `src/apps/portal/urls.py`, `src/templates/base.html`, form/templates HCNS và hai template quản lý quyết định. Thêm `PersonnelDecision` và lịch sử append-only theo action, snapshot JSON gồm dữ liệu đã kiểm tra và preview, trạng thái; endpoint lưu/mở lại nháp, tìm/lọc, trình duyệt, duyệt/từ chối, hủy, ban hành và tải Word. Người trình không tự duyệt; từ chối cần lý do; ban hành cần PDF có phần mở đầu `%PDF-`, giới hạn 20 MB, lưu private storage và chỉ tải qua `private_file`. HR xem toàn bộ; người duyệt xem hồ sơ chờ hoặc hồ sơ mình đã xử lý. Cập nhật `docs/Huong_Dan_Bieu_Mau_HCNS.md` và `docs/11_Workflow_Definition.md`.

**Kiểm tra đã chạy:** `venv\Scripts\python.exe src\manage.py check` (SQLite với SECRET_KEY tạm): đạt; `venv\Scripts\python.exe src\manage.py makemigrations --check --dry-run`: `No changes detected`; ban đầu `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.document.tests_hr_workflow`: **26/26 đạt**; `venv\Scripts\python.exe ops\run_tests.py --backend sqlserver apps.document.tests_hr_workflow`: **26/26 đạt**, runner dùng DB test riêng và đã xóa; `venv\Scripts\python.exe ops\run_tests.py --backend sqlite`: **366 tests, 364 đạt, 2 skip, 0 lỗi**. Diagnostics không phát hiện lỗi. Browser sandbox ghi bên dưới; chưa thử Microsoft Word desktop/UAT.

**Bản chạy thử cục bộ:** tạo `D:\QLHCNS-Test` từ working tree hiện tại, giữ đủ thay đổi tính năng; loại `.env`, `.git`, virtualenv, DB/media/staticfiles, backup, `docs/templates/` và `src/qlhcns`. Trong bản sao, tạo SQLite mới, áp dụng toàn bộ migration gồm `document.0005`, tắt M365 và nạp dữ liệu giả. Server chỉ bind `127.0.0.1:8011`. Đã đăng nhập HR trên browser, mở trang quản lý, soạn/lưu `DEMO-QD-001` và xác nhận bản nháp xuất hiện trong danh sách/chi tiết; không trình duyệt hoặc ban hành dữ liệu demo.

**Điều hướng follow-up:** sắp xếp lại `src/templates/base.html` và bản tương ứng trong sandbox. Chuyển Biểu mẫu HCNS khỏi Cá nhân vào Nhân sự; thêm link cấp đầu “Quyết định nhân sự” cho HR/người duyệt; đổi “Duyệt & Xử lý” thành “Cần duyệt”; nhóm Hành chính thành Văn bản, Tài sản, Đặt chỗ & đề nghị; đổi Kế toán thành Tài chính, đưa ngày lễ về Kế hoạch và rút “Hoạt động dự án” thành “Dự án”. Browser xác nhận HR nhìn thấy quyết định trực tiếp và Biểu mẫu trong Nhân sự; Giám đốc thấy quyết định/Cần duyệt nhưng không thấy menu Nhân sự; mobile mở menu không tràn ngang. Đã restart server sandbox để nạp template. Người dùng có thể đã tiếp tục thao tác demo sau lần xác nhận ban đầu; tác vụ follow-up này không chuyển trạng thái bản ghi.

**Commit/push/CI:** các commit quyết định/menu `b6bfb60`, log `8345d4d`/`a09414b`, follow-up thông báo `c1ea248`, log `0d78fec`/`b553b37` đã push lên `main`. GitHub Actions của SHA cuối `b553b377434832e4aa0d2e2bfbcfa25c1358be8f` chưa xác minh được: `gh run list --branch main --commit <SHA> --limit 10` trả HTTP 401 `Bad credentials`; browser chưa đăng nhập repo private nên Actions trả 404. Sau khi xác thực, chạy `$sha = (git rev-parse HEAD).Trim(); gh run list --branch main --commit $sha --limit 5`, rồi `gh run view <RUN_ID> --json headSha,status,conclusion,jobs,url` để xác nhận cả `backend`, `frontend`, `backup-command-tests`.

**Còn mở / hành động chủ dự án:** migration **chưa áp dụng** vào database cấu hình, SIT/UAT hoặc Production. Trước triển khai cần backup theo quy trình, xác nhận đích, áp dụng `document.0005_personnel_decision_workflow` bằng release/migration procedure hiện hành, kiểm tra menu “Quản lý quyết định”, tạo nháp, duyệt/từ chối, tải PDF ký và phân quyền tải tệp. Nếu dùng SQL Server, xác nhận mapping `JSONField`/migration trên DB đích. Chưa deploy.

**Thông báo chuông follow-up:** nối notification nội bộ vào sự kiện trình duyệt, duyệt, từ chối và ban hành. Người duyệt nhận yêu cầu; submitter nhận phản hồi có ghi chú; nhân viên và submitter nhận thông báo ban hành. Thông báo chỉ nêu số quyết định, đối tượng/trạng thái/ghi chú và link, không chứa snapshot hay mức lương; không gửi email. Nhân viên được thông báo chỉ truy cập trang bản đã ban hành và private PDF, không thấy Word nháp/lịch sử duyệt/nhãn bản soạn thảo. Lưu và sửa nháp, hủy không phát chuông.

**Kiểm tra follow-up:** `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.document.tests_hr_workflow`: **26/26 đạt**; `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.document.tests_hr_workflow apps.notification.tests apps.security.tests_data_protection apps.portal.tests_review_hardening`: **75 tests, 74 đạt, 1 skip, 0 lỗi**; full suite `venv\Scripts\python.exe ops\run_tests.py --backend sqlite`: **366 tests, 364 đạt, 2 skip, 0 lỗi**; `venv\Scripts\python.exe ops\run_tests.py --backend sqlserver apps.document.tests_hr_workflow apps.notification.tests apps.security.tests_data_protection`: **55/55 đạt**; sau chỉnh template cuối workflow trên SQLite và SQL Server đều **26/26 đạt**. Browser `D:\QLHCNS-Test` xác nhận HR trình `BELL-QD-TEST`, Giám đốc nhận badge/link và duyệt, HR nhận thông báo trả lời rồi ban hành PDF DEMO, nhân viên nhận chuông và chỉ thấy trạng thái/PDF, không thấy preview Word/history. Đã xóa riêng `BELL-QD-TEST`, bốn notification gắn với bản ghi và PDF demo; dữ liệu sandbox có trước vẫn còn. Chưa thử Microsoft Word desktop/UAT.

**Commit/push thông báo:** `c1ea248` (`feat(document): notify personnel decision workflow`) và các commit log `0d78fec`, `b553b37` đã push. Tệp `src/qlhcns` tiếp tục nằm ngoài Git.

## 2026-10-06 — Chuẩn hóa tên mọi tệp export được tạo mới

**Mục tiêu/phạm vi:** FIX điểm xuất của 26 biểu mẫu HCNS, ba báo cáo Excel, kiểm kê trực tiếp và phiếu lương PDF. Thống nhất `LoạiTàiLiệu_MãHồSơ_YYYYMMDD.ext`, ví dụ `QD_NangLuong_VH-999_20261006.docx`. Không đổi nội dung bản xuất, schema hoặc bản ghi nghiệp vụ. Tệp đính kèm đã lưu vẫn giữ tên hiện có khi tải lại.

**Git:** xác nhận `main`, fetch `origin/main`, `HEAD...origin/main` là `0 0`; giữ các thay đổi cục bộ của đợt trước. Không commit/push/deploy, không đưa DB/tài liệu gốc/QA/bí mật vào Git.

**Tệp và thay đổi:** thêm `src/apps/common/export_names.py`, `src/apps/document/hcns/filenames.py`, `src/apps/document/tests_export_names.py`; cập nhật HCNS `views.py`, `prefill.py`, template draft, `src/static/js/hcns_forms.js`, `portal/views/{assets,finance}.py`, `reporting/views.py` và hướng dẫn biểu mẫu. Chuẩn hóa tên không dấu/ký tự an toàn trên Windows, giới hạn độ dài thành phần; tiền tố riêng cho cả 26 mẫu, quyết định bổ nhiệm đổi theo hành động, tài sản đổi theo Thanh lý/Tiêu hủy. Mã nhân viên/ứng viên lấy từ đối tượng đã được kiểm tra quyền hoặc lựa chọn hợp lệ; đổi dropdown thì không giữ mã người trước. Không đoán mã từ họ tên. Dùng ngày của tài liệu (quyết định dùng ngày lập/ngày ký dự kiến, không dùng ngày hiệu lực/ngày tải); thiếu mã/ngày được ghi rõ. Báo cáo dùng phạm vi và ngày xuất, kiểm kê dùng đợt/ngày kiểm kê, phiếu lương dùng mã NV/kỳ/ngày phát hành. Hiển thị tên trên trang và đặt tiêu đề khi in để trình duyệt gợi ý cùng tên PDF, JS tăng cache version `20261006-6`.

**Review/sửa qua kiểm thử:** vòng đầu phát hiện tiền tố miễn nhiệm bị lấy nhầm mặc định vì đọc trường từ bản in đã lược bỏ loại QĐ; chuyển sang giá trị form đã kiểm tra. Sửa fixture kiểm thử thiếu ngày kỳ lương. Review tiếp đổi việc lấy mã nguồn sang metadata của bước prefill đã kiểm tra quyền, tránh thêm điều kiện quyền xuất danh bạ vào luồng đọc đơn nghỉ hợp lệ của quản lý phòng ban; có hồi quy riêng cho trường hợp này. Không thay đổi quyền nghiệp vụ.

**Kiểm tra:** `venv\Scripts\python.exe ops/run_tests.py --backend sqlite apps.document.tests_export_names apps.document.tests_hcns apps.document.tests_hcns_choices apps.document.tests_hr_workflow layout_browser_tests` (thêm thư mục harness tạm vào `PYTHONPATH`): **38/38 đạt**, 127.256 giây, exit 0; log `%TEMP%\hcns-export-names-sqlite-final.log`. Edge đăng nhập, preview/in PDF/tải 26 mẫu, xác nhận suggested filename bằng tên trên preview và sự kiện trước/sau in đặt/khôi phục tiêu đề; dropdown/tự điền/mobile/0 lỗi JavaScript. `--backend sqlserver apps.document.tests_export_names`: **8/8 đạt** trước chỉnh metadata cuối. Hai vòng xác nhận cuối cho metadata/quyền quản lý phòng ban ghi tiếp tại mục này. Harness ở `%TEMP%\ihrms-hcns-layout-20261006`, không trong Git; mọi dữ liệu/DB/media kiểm thử tách biệt. `git diff --check` đạt. Không chạy FULL suite hoặc CI trong đợt này.

**Xác nhận cuối:** `venv\Scripts\python.exe ops/run_tests.py --backend sqlite apps.document.tests_export_names`: **9/9 đạt**, exit 0; cùng label trên SQL Server **9/9 đạt**, exit 0, DB test đã xóa. Logs `%TEMP%\hcns-export-names-tests-final.log` và `hcns-export-names-sqlserver-final.log`. Kiểm tra đổi NV so với nguồn cũ, ngày ký khác ngày hiệu lực, hành động miễn nhiệm, mã UV/nguồn GET, ký tự cấm/Unicode/tên dài, ba báo cáo, kiểm kê, ngày phát hành phiếu lương theo giờ Việt Nam và mã nguồn đơn nghỉ đã được phép đọc. Các lượt phụ trước đó có lỗi fixture gán hai tài khoản cho một NV và kỳ vọng quản lý phòng ban được xuất trực tiếp dù form nguồn hiện tại không cho lựa chọn người ngoài phạm vi; đã sửa fixture và kỳ vọng về kiểm tra đọc nguồn, không mở rộng quyền hoặc sửa quy tắc nghiệp vụ. Browser trong các lượt phụ vẫn đạt cả 26 mẫu; chạy thêm một lượt browser độc lập để có log riêng cho kết quả cuối.

**Bàn giao/còn mở:** cần `Ctrl+F5` ở cổng 8001, chọn nhân viên và nhập ngày lập đúng ngày ký dự kiến, cập nhật preview rồi tải Word/Excel để kiểm tra tên. Ngày ký chưa được lưu riêng trong các mẫu nhân sự, tên dùng ngày hiển thị trên văn bản, không chứng minh đã ký. Chưa thao tác hộp thoại Save PDF của hệ điều hành; trình duyệt có thể thêm số thứ tự khi tệp trùng và cho đổi tên thủ công. Không tự xóa/ghi đè tệp đã tải. Chưa UAT dữ liệu thật, chưa commit/push/deploy.

## 2026-10-06 — Đối chiếu và sửa bố cục toàn bộ 26 biểu mẫu HCNS

**Mục tiêu/phạm vi:** FIX và review bố cục xem trước, in/PDF từ trình duyệt và xuất Word/Excel của 26 mẫu đã cung cấp. Đọc hướng dẫn review dự án; không coi đây là FULL review toàn dự án hoặc một lần chạy reviewer Sixth/Bugbot. Không đổi schema, không sửa dữ liệu nghiệp vụ thật.

**Git:** xác nhận `main`, fetch `origin/main`, so sánh `HEAD...origin/main` là `0 0` trước đợt sửa; giữ nguyên working tree của các đợt trước. Chưa commit/push/deploy; tài liệu gốc riêng tư tại `docs/templates/` và tệp QA trong `%TEMP%` không được đưa vào Git.

**Tệp/phân hệ:** `src/apps/document/hcns/{layouts.py,layout_profiles.json,rendering.py,exports.py}`, các template HCNS `document.html`, `appointment_document.html`, `draft.html`, catalog; `src/static/css/hcns_forms.css`, `src/apps/document/tests_hcns_layouts.py`, `docs/Huong_Dan_Bieu_Mau_HCNS.md`. Profile chỉ lưu thông số bố cục/phông/cột, không sao chép hồ sơ cá nhân hoặc chữ ký từ mẫu.

**Đã sửa:** tách bố cục giấy khỏi tiêu đề ô nhập, bỏ thông tin hồ sơ nguồn/hướng dẫn khỏi nội dung in. Quyết định dùng đầu trang hai cột, trích yếu, căn cứ nghiêng, điều liền dòng, nơi nhận/vùng ký hai cột; quyết định tài sản đặt bảng sau Điều 1. Đơn nghỉ, thông tin cán bộ, checklist, phỏng vấn, bàn giao, TOR và ba mẫu xử lý tài sản dùng thứ tự nội dung/vùng ký riêng theo mẫu. Phiếu đánh giá dùng bảng thông tin và nhóm nhiệm vụ với sáu mức tần suất/chất lượng, tiêu đề gộp lặp khi sang trang. HTML/Word giữ tỷ lệ cột, lề, khổ giấy và cỡ chữ theo từng nguồn. Bốn Excel có tiêu đề/ô gộp/vùng in/hàng lặp riêng; tổng và trung bình sát nhóm điểm, giữ công thức trung bình cả phỏng vấn lẫn kiểm tra theo mã ứng viên. Sửa lỗi chiều cao hàng bị tính theo độ dài công thức, cột ghi chú bàn giao quá hẹp và tiêu đề bảng kiểm kê xuống dòng trong cột STT. Giữ dữ liệu theo dõi, đầy đủ dòng nguồn, công thức chống thiếu điểm và bảo vệ formula injection; không chạy macro nguồn.

**Kiểm tra tự động:** `venv\Scripts\python.exe ops/run_tests.py --backend sqlserver apps.document.tests_hcns apps.document.tests_hcns_choices apps.document.tests_hr_workflow apps.document.tests_hcns_layouts`: **35/35 đạt**, DB SQL Server kiểm thử dùng một lần đã được runner xóa; log `%TEMP%\hcns-layout-release-sqlserver.log`. Cùng bốn labels và `layout_browser_tests workflow_browser_tests` trên SQLite: **37/37 đạt**, log `%TEMP%\hcns-layout-release-sqlite-browser.log`; có đăng nhập Edge tự động, 26 editor/preview, in PDF và tải 26 tệp, tự điền/dropdown/dòng tài sản thêm mới/mobile/0 lỗi JavaScript và luồng nâng lương/bổ nhiệm/điều chuyển tương lai → soạn QĐ → Word, khen thưởng/kỷ luật/chọn nhân viên hợp đồng. Hai harness browser nằm ngoài Git, chạy bằng `$env:PYTHONPATH=Join-Path $env:TEMP 'ihrms-hcns-layout-20261006'`. Các kết quả trên có trước các chỉnh sửa nhỏ cuối về độ rộng cột/vùng ký; vòng xác nhận cuối ghi tiếp ngay trong mục này. System check không có lỗi; `git diff --check` đạt. Không chạy lại toàn bộ suite ngoài phạm vi HCNS trong đợt này.

**QA hình ảnh và công thức:** xuất 22 DOCX và 4 XLSX với dữ liệu giả; chạy `render_docx.py` của Documents cho cả 22 Word, dựng 30 trang PNG/PDF và kiểm tra trực quan từng trang (TOR hai trang, phiếu đánh giá năm trang). Dựng PDF bằng LibreOffice cho bốn Excel và kiểm tra các trang, sửa rồi dựng lại các trang lỗi; bản bàn giao nghỉ việc sau sửa giữ một trang với nhãn ghi chú đầy đủ. Tính lại hai bảng điểm giả bằng LibreOffice rồi đọc cached values: người chấm 10/0 cho tổng phỏng vấn 60/0, trung bình 30; tổng bài kiểm tra 20/0, trung bình 10; tổng cộng 40. Thiếu một điểm bài kiểm tra thì trung bình bài kiểm tra/tổng cộng để trống; không có ô lỗi Excel. QA và manifest nguồn chỉ nằm tại `%TEMP%\ihrms-hcns-layout-20261006`.

**Xác nhận cuối:** chạy lại lệnh SQLite với cả sáu labels trên: **37/37 đạt**, 83.053 giây, exit 0, log `%TEMP%\hcns-layout-release-final.log`, cả hai harness Edge đạt. Sau sửa gộp tiêu đề kiểm kê cuối, chạy `venv\Scripts\python.exe ops/run_tests.py --backend sqlite apps.document.tests_hcns_layouts` và cùng label với `--backend sqlserver`: **6/6 đạt trên mỗi backend**, exit 0, system check sạch; logs `%TEMP%\hcns-layout-final-structure.log` và `hcns-layout-final-sqlserver-structure.log`. Đã dựng lại PDF kiểm kê và xác nhận nhãn bảng nằm trên một dòng, không dồn vào cột STT. Review theo tiêu chí `review-agent`: các lỗi bố cục xác nhận được đã sửa; chưa phát hiện lỗi cần sửa thêm trong phạm vi này, không phải kết luận cho toàn dự án.

**Bàn giao/còn mở:** chưa kiểm thử Microsoft Word/Excel desktop, máy in vật lý hoặc UAT với hồ sơ thật, không cam kết trùng từng pixel giữa các bộ máy in. Giữ nhãn BẢN SOẠN THẢO; các mục chưa có nguồn, ngày ký/số quyết định/người ký và nội dung căn cứ cần người soạn xác nhận. Chủ dự án khởi động lại ứng dụng nếu không có autoreload, mở cổng 8001, `Ctrl+F5`, kiểm tra mẫu với hồ sơ thực tế và bản xuất Office trước khi ký; in PDF trình duyệt ở 100%, tắt đầu/chân trang trình duyệt. Chưa commit/push/deploy.

## 2026-10-06 — Dropdown dùng chung cho toàn bộ biểu mẫu HCNS

**Mục tiêu/phạm vi:** FIX và rà cả 26 trang biểu mẫu; thay các trường có hồ sơ/danh mục thành dropdown như QĐ bổ nhiệm, giữ thông tin nghiệp vụ đã ghi nhận và bản xuất đúng tên/nhãn. Không đổi schema, không sửa dữ liệu thật, không phải FULL review toàn dự án.

**Git:** xác nhận `main`, fetch `origin/main`, so sánh `HEAD...origin/main` là `0 0`; giữ nguyên toàn bộ working tree của các đợt trước. Chưa commit/push/deploy; mẫu gốc riêng tư vẫn ngoài Git.

**Tệp/phần đã cập nhật:** thêm `src/apps/document/hcns/choices.py` làm bộ chọn dùng chung, nối vào `forms.py`, `views.py`, `prefill.py`; `appointment.py` dùng lại bộ chọn chung, giữ layout riêng. Cập nhật template draft, `src/static/js/hcns_forms.js`, `tests_hcns.py`, `tests_hr_workflow.py`; thêm `tests_hcns_choices.py` và cập nhật hướng dẫn biểu mẫu. CSS/JS tăng cache version `20261006-4`.

**Đã làm:** dropdown nhân viên, người ký/quản lý/người nhận/người phỏng vấn, chức vụ/phòng ban/chức vụ mới, dự án, ứng viên, mã/tên thiết bị và loại thiết bị; giới tính, vai trò/hình thức tham gia, tình trạng kiểm kê dùng danh mục hiện có. Cả bảng chi tiết và dòng thêm mới dùng cùng cơ chế. Chọn nhân viên điền các slot tương ứng từ hồ sơ; đổi người xóa dữ liệu nghiệp vụ và mục chưa có nguồn của người trước. Chọn người bàn giao/quản lý điền chức vụ; chọn ứng viên điền liên hệ và liên kết mã/tên trong bảng điểm; chọn thiết bị điền thuộc tính. Phiếu phỏng vấn không coi nguồn nhân viên là ứng viên. Dữ liệu nguồn chọn sẵn bằng ID, xử lý người/ứng viên/tài sản trùng tên; bản xuất chuyển ID thành tên/nhãn. Nguồn bản lương/bổ nhiệm/điều chuyển giữ đúng dữ liệu và ngày hiệu lực; đổi chủ hồ sơ khi preview thì cập nhật selector/nhãn nguồn. Các trường chưa có danh mục hoặc là nội dung tự do vẫn cho nhập.

**Review/quyền truy cập:** máy chủ kiểm tra ModelChoiceField từ queryset được phép, không chấp nhận tên tự gõ thay cho ID, hồ sơ đã xóa, ID giả hoặc mã/tên thuộc hai hồ sơ khác nhau. Dữ liệu JS chỉ chứa slot cần cho mẫu; không chứa lương của danh bạ. Nhân viên không nhận danh bạ HR. Người chỉ có quyền tài sản nhận thêm đúng thành viên đã ghi trong nguồn kiểm kê được phép đọc, chỉ metadata chức vụ; không mở quyền xuất thông tin cá nhân hay toàn bộ danh bạ. Điều kiện/danh mục nguồn lỗi hiển thị thông báo an toàn thay vì xuất sai hoặc crash. Không tự chọn người ký/phê duyệt từ nguồn.

**Kiểm tra cuối:** `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.document.tests_hcns apps.document.tests_hr_workflow apps.document.tests_hcns_choices`: **29/29 đạt**; lệnh cùng labels với `--backend sqlserver`: **29/29 đạt**, DB SQL thử được runner xóa. Gồm GET/prefill và export 26 mẫu, ID ra đúng tên trong Word, trùng tên, ứng viên nguồn, đổi selector, nguồn lương tương lai, các thao tác NV & Hồ sơ, từ chối giả mạo/đã xóa/ngoài quyền, mã-tên không khớp, thành viên kiểm kê với người không có quyền danh bạ, nguồn 51 tài sản, số 0/điểm và dữ liệu tự do chống XSS/formula injection. Log `%TEMP%\ihrms-hcns-dropdown-sqlite-final.log` và `ihrms-hcns-dropdown-sqlserver-final.log`. System check không có lỗi; `git diff --check` đạt. Không chạy lại toàn bộ test ngoài HCNS trong đợt này; kết quả hồi quy toàn dự án của đợt trước được ghi riêng, không coi là bằng chứng mã cuối của đợt dropdown.

**Browser:** `$env:PYTHONPATH=Join-Path $env:TEMP 'ihrms-hcns-layout-20261006'; venv\Scripts\python.exe ops\run_tests.py --backend sqlite dropdown_browser_tests`: vòng đầu **1/1 đạt**, Edge đăng nhập mở 26 editor, chọn dropdown và tải 26 tệp Word/Excel; tự điền nhân viên/ứng viên, liên kết mã ứng viên, chọn tài sản trên dòng thêm mới, mobile, 0 lỗi JavaScript. Vòng cuối cùng runner với labels `dropdown_browser_tests workflow_browser_tests`: **2/2 đạt**, xác nhận lại tất cả dropdown/export cùng luồng Thao tác → lưu nâng lương/bổ nhiệm/điều chuyển tương lai → QĐ và tải Word, khen thưởng/kỷ luật, chọn nhân viên khi tạo hợp đồng. Harness và dữ liệu giả nằm ngoài Git ở `%TEMP%\ihrms-hcns-layout-20261006`, log `%TEMP%\ihrms-hcns-dropdown-browser-final.log`.

**Bàn giao/còn mở:** tải lại trang cổng 8001 (Ctrl+F5 nếu còn cache), chọn nhân viên hoặc đúng hồ sơ nghiệp vụ, kiểm tra dropdown và các slot tự điền, bổ sung mục trống trước xuất. Cần tạo hồ sơ/danh mục còn thiếu tại phân hệ nguồn trước khi chọn. Chưa UAT dữ liệu thật, chưa CI/commit/push/deploy; chưa chạy toàn bộ suite trên SQL Server. Bộ mẫu còn thiếu QĐ khen thưởng/kỷ luật, hợp đồng và phụ lục như mục luồng nghiệp vụ bên dưới.

## 2026-10-06 — Luồng NV & Hồ sơ sang quyết định HCNS

**Mục tiêu/phạm vi:** FIX và review các thao tác bắt đầu tại Nhân sự → NV & Hồ sơ: thêm/sửa nhân viên, điều chuyển, bổ nhiệm, khen thưởng, kỷ luật, nâng lương, tạo/gia hạn hợp đồng và phụ lục; nối biểu mẫu với bản ghi nghiệp vụ đã lưu. Không coi đây là FULL review toàn mã nguồn.

**Git:** xác nhận `main`; fetch `origin/main`, `HEAD...origin/main` là `0 0`; giữ nguyên các thay đổi cục bộ của các đợt trước. Chưa commit/push/deploy, không đưa mẫu nguồn riêng tư, DB, `.env` hoặc dữ liệu thật vào Git.

**Đã làm:** `portal/views/hr.py`, các template employee list/detail và contract form; `document/hcns/{prefill,appointment,views}.py`, template draft, `tests_hr_workflow.py` và hướng dẫn biểu mẫu. Thêm nút Ghi nhận và soạn quyết định cho nâng lương/điều chuyển/bổ nhiệm, giữ nút lưu thông thường. Lịch sử liên kết đúng dòng lương, bổ nhiệm, điều chuyển qua selector riêng. Prefill giữ mức lương/ngày hiệu lực hoặc chức vụ cũ/mới/phòng ban đích theo dòng được chọn, kể cả thay đổi tương lai; bản lương đã kết thúc vẫn có thể soạn lại. Chức vụ cũ/mới đã ngừng sử dụng vẫn chọn được khi nằm trong nguồn được phép; danh mục đã xóa bị từ chối. Nguồn và lý do hiển thị để đối chiếu, các giá trị khác tham khảo hồ sơ hiện tại, không giả định đã lưu snapshot toàn hồ sơ. Xem/soạn/xuất không tự ghi nghiệp vụ.

**Lỗi đã sửa khi rà:** history và phụ lục dùng `full_clean()` trước lưu, từ chối ngày/danh mục bắt buộc sai; action không tồn tại báo lỗi. Nâng lương không cho lùi/trùng ngày làm ngày kết thúc của mức trước nhỏ hơn ngày bắt đầu; lỗi trong transaction không làm mất mức lương cũ. Prefill lương hiện hành xét khoảng ngày của cả Active/Ended vì nâng lương tương lai đã đóng trạng thái dòng trước nhưng khoảng hiệu lực vẫn còn áp dụng hôm nay. Thông báo điều chuyển/bổ nhiệm không khẳng định thay đổi tương lai đã áp dụng ngay. Gia hạn từ chối thiếu ngày, ngày bằng/trước hạn hiện có và hợp đồng không xác định thời hạn; lỗi rollback phụ lục. Tạo hợp đồng từ hồ sơ chọn sẵn nhân viên. Bổ sung xem/ghi nhận phụ lục ngay dưới từng hợp đồng.

**Kiểm tra:** runner cô lập DB/media, dữ liệu giả. `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.document.tests_hr_workflow apps.document.tests_hcns`: vòng đầu 22/22 đạt; thêm ca hợp đồng/phụ lục thành 23 test. `--backend sqlserver apps.document.tests_hr_workflow apps.document.tests_hcns`: vòng cuối **23/23 đạt**, gồm ca lương hiện hành trước thay đổi tương lai; DB SQL thử được runner xóa. `venv\Scripts\python.exe ops\run_tests.py --backend sqlite`: **342 test, 340 đạt, 2 bỏ qua, 0 thất bại**, 414,967 giây. Hai ca bỏ qua yêu cầu SQL Server: `ConcurrentDispatchTests` (khóa dòng) và `PlanningUniqueConstraintTests.test_company_wide_annual_budget_with_null_department_is_unique` (unique với NULL). Đã chạy `venv\Scripts\python.exe ops\run_tests.py --backend sqlserver apps.portal.tests_review_hardening.ConcurrentDispatchTests apps.planning.tests.PlanningUniqueConstraintTests.test_company_wide_annual_budget_with_null_department_is_unique`: **2/2 đạt**, không bỏ qua; log `%TEMP%\ihrms-hr-workflow-sql-skipped.log`, runner xóa DB SQL thử. Các điều chỉnh cuối ở prefill/nhãn nguồn được xác nhận lại bằng focused SQL và Edge trên mã cuối. Chưa chạy toàn bộ 342 test trên SQL Server. `git diff --check` đạt, không đổi schema/migration.

**Browser đã chạy:** `$env:PYTHONPATH=Join-Path $env:TEMP 'ihrms-hcns-layout-20261006'; venv\Scripts\python.exe ops\run_tests.py --backend sqlite workflow_browser_tests`: 1/1 đạt cả vòng đầu và vòng cuối. Edge đăng nhập bằng dữ liệu giả đi từ menu Thao tác → nâng lương → bản soạn đúng số tiền/ngày và tải Word; bổ nhiệm/điều chuyển tương lai giữ đích mới; khen thưởng/kỷ luật lưu; tạo hợp đồng chọn sẵn đúng nhân viên; nút trên mobile hiện; 0 lỗi JavaScript. Harness ở `%TEMP%\ihrms-hcns-layout-20261006\workflow_browser_tests.py` và `workflow_browser.cjs`, ngoài Git. Các log ngoài Git: `%TEMP%\ihrms-hr-workflow-browser-final.log`, `ihrms-hr-workflow-sql-final.log`, `ihrms-hr-workflow-full.log`.

**Còn mở/bàn giao:** chưa UAT hồ sơ thật, chưa kiểm tra CI hay triển khai. Bộ 26 mẫu chưa có quyết định khen thưởng/kỷ luật và mẫu hợp đồng/phụ lục gia hạn; giao diện nói rõ, không gán nhầm biểu mẫu. Chủ dự án bổ sung bản mẫu trắng vào `docs/templates/hcns/` nếu cần layout/export cho các thủ tục này; không thêm chữ ký/dữ liệu thật vào Git. Tải lại cổng 8001, chọn nhân viên → Thao tác → nhập thông tin → Ghi nhận và soạn quyết định; xác nhận số/ngày quyết định, người ký và các điều trước khi xuất. Mẫu điều chỉnh vị trí và mức lương kết hợp nhiều nghiệp vụ, cần sửa điều tương ứng nếu chỉ điều chuyển phòng ban. Mọi kết quả tự động ở trên là test cô lập, không đồng nghĩa cam kết 100% nghiệp vụ thực tế.

## 2026-09-24 — Tích hợp lưu tệp SharePoint

**Mục tiêu:** cho phép các nghiệp vụ cần tệp đính kèm sử dụng SharePoint qua Microsoft Graph, đồng thời giữ storage cục bộ khi tích hợp bị tắt.

**Đã làm:** thêm Graph client và storage adapter migration-stable; nối storage vào document, nghỉ phép, công văn và CV ứng viên; thêm migrations, kiểm tra tệp upload và test M365. Cấu hình mẫu và dependency được cập nhật. Thay đổi được commit dưới `475c3e7` (`feat: integrate SharePoint file storage`) trên `chore/django-5.2-upgrade`.

**Kiểm tra:** người dùng xác nhận smoke test SharePoint thật gồm upload, đọc/xem và xóa tệp thử; các thư viện/thư mục nghiệp vụ đã được kiểm tra. Trong bản sao sạch, `manage.py check` đạt, `makemigrations --check --dry-run` báo không có thay đổi, `apps.m365.tests` đạt 5/5. Không coi đây là xác nhận cho email, Teams, SSO, đồng tác giả Office hoặc OneDrive cá nhân.

**Còn mở:** trước production, IT xác nhận quyền Graph tối thiểu, ACL/retention/audit của thư viện và quy trình xử lý gián đoạn SharePoint. Không đưa secrets vào repo.

## 2026-09-24 — Cập nhật Review, cẩm nang và tập huấn

**Mục tiêu:** đồng bộ tài liệu với trạng thái đã clone GitHub sạch, Django 5.2.17, kết nối SQL Server ở môi trường kiểm tra và smoke test SharePoint.

**Đã cập nhật:** `docs/Production_Readiness_Review_2026-09-23.md` nêu bằng chứng còn thiếu trước go-live; `HUONG_DAN_SU_DUNG_IHRMS.md` thêm thao tác tệp SharePoint và báo sự cố; `TAP_HUAN_IHRMS.md` thêm bài thực hành với tệp giả; `Review_23092026_recovered.md` được đánh dấu là snapshot lịch sử; liên kết M365 trong `.env.example` được sửa sang tài liệu hiện hữu. Commit nội dung là `377ca0d` (`docs: refresh IHRMS readiness and training guides`), sau đó merge và push lịch sử remote an toàn ở `989cae9`.

**Kiểm tra:** UTF-8 hợp lệ; `git diff --check` sạch; `manage.py check` đạt; `makemigrations --check --dry-run` báo không có thay đổi; 86 test đạt trên SQLite khi gọi module test rõ ràng. Lệnh test không kèm module tự tìm thấy 0 test; phải tiếp tục dùng lệnh có labels hoặc sửa test discovery/CI. Còn cảnh báo `RequestsDependencyWarning` về phiên bản `urllib3`/`chardet` trong môi trường test.

**Chưa hoàn tất:** bản Word `docs/HUONG_DAN_SU_DUNG_IHRMS.docx` chưa đồng bộ với Markdown vì môi trường thực thi hiện tại không có bộ dựng/render DOCX dùng cho kiểm tra từng trang.

**Việc cần chủ dự án/IT làm:** nếu cần bản Word mới, bảo đảm máy/môi trường làm việc có Python package `python-docx` cùng LibreOffice và renderer `render_docx.py` theo skill Documents; sau đó yêu cầu cập nhật Word, kiểm tra toàn bộ ảnh trang render và ghi kết quả tại đây. Không cần di chuyển hoặc sao chép `SKILL.md` vào repo.

## Công cụ Word trên máy Windows

**Đã kiểm tra:** Python 3.12.14 có sẵn; `python-docx` và `pdf2image` chưa có trong Python hiện hành; LibreOffice đã cài ở `C:\Program Files\LibreOffice\program` và `soffice.com --headless --version` trả về 26.2.5.2. `pdftoppm`/Poppler chưa có trong PATH. Renderer đã có sẵn trong gói Documents của Codex tại `%USERPROFILE%\.codex\plugins\cache\openai-primary-runtime\documents\<phiên-bản>\skills\documents\render_docx.py`; không cần tạo hoặc chép file đó vào dự án.

**Cách chuẩn bị môi trường riêng, không đụng virtualenv IHRMS:** mở PowerShell mới và chạy:

```powershell
$docTools = Join-Path $env:LOCALAPPDATA 'IHRMS-DocTools'
py -3.12 -m venv $docTools
$docPy = Join-Path $docTools 'Scripts\python.exe'
& $docPy -m pip install --upgrade pip
& $docPy -m pip install python-docx pdf2image
```

`python-docx` phục vụ đọc/sửa file Word; renderer gọi `pdf2image` để biến trang PDF trung gian thành ảnh. Trên Windows, `pdf2image` cũng cần Poppler (`pdftoppm`/`pdfinfo`) ngoài LibreOffice. Cách nhanh là `winget install --id oschwartz10612.Poppler`; hoặc tải gói Windows từ `https://github.com/oschwartz10612/poppler-windows/releases/`, giải nén và thêm thư mục chứa `pdftoppm.exe` vào PATH. Đóng/mở lại PowerShell rồi xác nhận `pdftoppm -h` và `pdfinfo -v` chạy được.

Xác nhận Python packages sau cài đặt:

```powershell
& $docPy -c "import docx, pdf2image; print('python-docx/pdf2image: OK')"
```

**Render file để kiểm tra:**

```powershell
$lo = 'C:\Program Files\LibreOffice\program'
$env:Path = "$lo;$env:Path"
$renderer = Get-ChildItem (Join-Path $env:USERPROFILE '.codex\plugins\cache\openai-primary-runtime\documents') -Recurse -File -Filter render_docx.py |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1 -ExpandProperty FullName
$docx = 'D:\QLHCNS\docs\HUONG_DAN_SU_DUNG_IHRMS.docx'
$renderDir = 'D:\QLHCNS-docx-render'
New-Item -ItemType Directory -Force -Path $renderDir | Out-Null
& $docPy $renderer $docx --output_dir $renderDir --emit_pdf
```

Kết quả gồm `page-1.png`, `page-2.png`, ... và PDF trong `D:\QLHCNS-docx-render`; mở và xem **tất cả** ảnh trang trước khi giao bản Word. Thư mục render nằm ngoài repository nên không bị commit. Nếu lệnh báo thiếu `soffice.exe`, Poppler hoặc package Python, ghi lại toàn bộ thông báo lỗi nhưng không gửi secrets; Codex sẽ xử lý tiếp theo lỗi cụ thể.

## Cổng còn lại trước vận hành thật

- Chạy `check --deploy` với cấu hình production thật; xác nhận HTTPS, host/CSRF, cookies, secret, static, logging và IIS/reverse proxy.
- Chạy toàn bộ test trên SQL Server; hiện 86 test gần nhất là trên SQLite, chưa chứng minh tương thích đầy đủ trên backend SQL Server.
- Finance đối soát công thức lương/thuế/bảo hiểm với bộ số mẫu đã được phê duyệt; HR, quản lý và nhân viên hoàn tất UAT trên dữ liệu ẩn danh.
- Thiết lập backup SQL Server và tệp hồ sơ ở nơi độc lập; diễn tập restore, đo thời gian và xác nhận RPO/RTO với công ty.
- IT rà quyền tài khoản, SharePoint ACL/retention/audit và lịch vận hành; diễn tập go-live/rollback trước khi mở cho toàn công ty.

## Mẫu mục nhật ký cho đợt sau

### YYYY-MM-DD — Tên thay đổi

**Mục tiêu/phạm vi:**
**Phân hệ/tệp:**
**Đã làm và quyết định:**
**Kiểm tra (lệnh, môi trường, kết quả):**
**Nhánh/commit/push:**
**Chưa làm hoặc chưa xác nhận:**
**Chủ dự án cần làm:** bước cụ thể, người phụ trách và kết quả cần gửi lại.

## 2026-09-27 — Cải thiện trải nghiệm mobile và PWA portal (Yêu cầu 3–6)

**Mục tiêu/phạm vi:** giúp portal hoạt động thuận tiện trên điện thoại, thay CSS Tailwind CDN bằng bản build nội bộ, và cho phép cài lối tắt PWA online-only. Sao lưu trước đợt sửa: `D:\QLHCNS-Backup-before-mobile-requirements-3-6-20260927-183513.bundle` (bundle Git chứa các refs tại thời điểm trước sửa).

**Đã làm:** bọc 21 bảng trong 18 template được review yêu cầu bằng vùng cuộn ngang; giữ nguyên bốn template in và thêm quy tắc in để wrapper không cắt nội dung. Chuyển menu portal sang hamburger dưới 768px, giữ menu ngang từ 768px và giữ điều kiện phân quyền, ARIA, click ngoài và Escape. Thêm Tailwind CLI 3.4.17, lockfile, lệnh build/watch và CSS đã build `src/static/css/tailwind.css`; bỏ Tailwind Play CDN. Thêm manifest `/portal/`, biểu tượng 192/512 từ biểu trưng sẵn có và service worker chỉ cache cùng origin `/static/`; không cache HTML hoặc dữ liệu nghiệp vụ. Bổ sung test hồi quy và hướng dẫn build/mobile/PWA tại `docs/06_Frontend_Standards.md`.

**Kiểm tra:** `python src/manage.py check` đạt; `python src/manage.py makemigrations --check --dry-run` báo không có thay đổi; `python src/manage.py test apps.portal.tests_mobile` đạt 5/5; `python src/manage.py findstatic css/tailwind.css manifest.json img/ihrms-pwa-192.png --verbosity 2` tìm thấy các asset. `npm ci` thành công; `npm run build:css` sinh CSS 33 KB (có cảnh báo Browserslist data cũ, không chặn build). Trình duyệt kiểm tra tại 375px, 768px và 1024px: mobile có thể mở/đóng hamburger, menu con và cuộn bảng nằm trong khung không làm rộng trang; từ 768px menu hamburger ẩn và nav ngang hiện; dropdown desktop vẫn đóng bằng Escape/click ngoài. Kết nối cấu hình hiện tại nhận diện SQL Server (`microsoft`), nhưng test mobile không truy vấn DB; không chạy migration hay ghi dữ liệu nghiệp vụ.

**Git/trạng thái:** nhánh `chore/django-5.2-upgrade`; thay đổi mobile ở commit cục bộ `67314ee` (`feat: improve portal mobile experience`), chưa push. Tệp chưa theo dõi `docs/Huong_Dan_Setup_TaskScheduler_SIT_UAT.md` đã có từ trước và được giữ nguyên, không thuộc thay đổi này.

**Còn mở:** PWA chỉ có thể cài qua HTTPS hoặc localhost trên trình duyệt hỗ trợ; service worker chỉ tăng tốc asset và không tạo chế độ offline cho dữ liệu. Khi sửa Tailwind class, chạy `npm ci` rồi `npm run build:css` trước `collectstatic`.


## 2026-09-24 ? Word guide synchronization and rendering setup

**Scope:** synchronize the DOCX user guide to Markdown version 1.1 and verify its rendered layout.

**Completed:** created the isolated Python environment at `%LOCALAPPDATA%\IHRMS-DocTools`; installed `python-docx 1.2.0` and `pdf2image 1.17.0`; installed Poppler 25.07.0 with winget. LibreOffice 26.2.5.2 was already installed. Rebuilt `docs/HUONG_DAN_SU_DUNG_IHRMS.docx` from `HUONG_DAN_SU_DUNG_IHRMS.md`; retained the previous DOCX outside the repository.

**Verification:** both Python package imports passed; LibreOffice, `pdftoppm`, and `pdfinfo` ran. Rendered the DOCX to PDF and four page images; visually inspected all four pages for Vietnamese glyphs, table fit, list numbering, and pagination. QA output is outside the repository at `D:\QLHCNS-docx-render-final`.

**Open:** the document changes have not been committed or pushed. Re-render after future content updates.

## 2026-09-25 — Hoạt động dự án: giao Task, báo cáo, nhắc hạn

**Phạm vi đã chốt:** theo dõi công việc dự án, nhắc việc và dashboard; không triển khai ngân sách, chứng từ tài chính hoặc quyết toán trong đợt này. Khi liên kết công văn đi đã phát hành với Hoạt động, tạo một Task báo cáo cho CBDA chính, hạn 10 ngày làm việc tính từ ngày sau ngày công văn. Người dùng xác nhận dùng lịch làm việc công ty. Hiện áp dụng thứ Hai–thứ Sáu, trừ ngày lễ đã khai báo trong IHRMS; chưa có ngoại lệ ngày làm việc thứ Bảy.

**Sao lưu trước thay đổi:** tạo `D:\QLHCNS-Backup-before-activity-implementation-20260925` trước khi tiếp tục chỉnh code. Bản sao loại trừ `.git`, virtualenv, media, log, `.env` và database. Các sửa đổi đã có trước đó của người dùng được giữ nguyên; không sửa cấu hình bí mật hoặc chạy migration lên SQL Server.

**Đã làm:** thêm miền `apps.activity`, gắn Activity với Project/CBDA/điều phối viên/công văn đi; sinh Task duy nhất với hạn theo ngày làm việc; yêu cầu tệp báo cáo trước khi hoàn tất; lưu qua storage SharePoint `activity_reports`; thêm phân quyền vai trò, dashboard theo tháng và giới hạn xem CBDA; thêm lệnh `send_activity_report_reminders` cùng script Task Scheduler Windows có log. Cập nhật roadmap theo phạm vi theo dõi công việc và vai trò sử dụng.

**Kiểm tra:** dùng Python `D:\QLHCNS\venv\Scripts\python.exe`, đặt `DB_ENGINE=django.db.backends.sqlite3` trong tiến trình kiểm tra rồi khôi phục biến môi trường. `manage.py check` đạt; `makemigrations --check --dry-run` báo `No changes detected`; 94 test thuộc asset, common, HRM, leave, payroll, security, M365 và activity đạt trên test database SQLite tạm. Trong đó có 8 test mới cho luồng hoạt động. Có cảnh báo môi trường `RequestsDependencyWarning` về urllib3/chardet; không làm test thất bại. Chưa chạy migration/test trên SQL Server, không xác nhận upload SharePoint thật trong lượt này và chưa đăng ký Scheduled Task trên máy chủ.

**Nhánh/commit:** `chore/django-5.2-upgrade`, `b08631b` (`feat: add NGO activity task tracking`).

**Còn mở / chủ dự án hoặc IT cần làm:** (1) review và commit các file của tính năng sau khi xem `git status` vì nhánh hiện có cả thay đổi khác của người dùng; (2) xác nhận người dùng và gán role PROJECT_MANAGER / PROJECT_COORDINATOR / CBDA; (3) trên máy ứng dụng đăng ký Task Scheduler hằng ngày lúc 08:00 chạy `ops\scheduler\Run-ActivityReportReminders.ps1`, sau đó kiểm tra log và thông báo; (4) chạy UAT trên SQL Server SIT đã xác nhận là môi trường thử nghiệm, rồi thực hiện upload/xem/tải báo cáo giả trên SharePoint; (5) nếu thứ Bảy là ngày làm việc của công ty, cần bổ sung quy tắc lịch làm việc thay vì giả định Mon–Fri. Không chạy `migrate` lên database hiện tại cho đến khi người phụ trách xác nhận SIT và lịch triển khai.

## 2026-09-25 — Điều chỉnh cảnh báo trùng lịch

**Phạm vi:** khớp yêu cầu cảnh báo trùng lịch CBDA mà không chặn điều phối viên lưu hoạt động. Trang quản trị hiện lưu hoạt động và hiển thị cảnh báo kèm hoạt động bị trùng; đã thêm test để xác nhận trùng lịch được phát hiện trong khi bản ghi vẫn hợp lệ. Cập nhật roadmap.

**Kiểm tra:** `manage.py check` đạt; `makemigrations --check --dry-run` không phát hiện thay đổi model; toàn bộ 95 test thuộc asset, common, HRM, leave, payroll, security, M365 và activity đạt trên SQLite test database tạm. Không chạy migration hoặc test ghi lên SQL Server/SharePoint.

**Commit:** `6405e78` (`fix: warn without blocking overlapping activities`).

## 2026-09-25 — Giao diện Hoạt động dự án và tạo bảng trên SQL Server

**Phạm vi:** hoàn thiện các trang tạo/chỉnh sửa/dashboard cho Hoạt động dự án và tạo schema dữ liệu trong database IHRMS hiện có. Không tạo database SQL Server riêng; mô-đun dùng chung database `qlhcns` theo kiến trúc Django hiện tại.

**Sao lưu trước thay đổi:** tạo `D:\QLHCNS-Backup-before-activity-ui-20260925`; sao chép mã nguồn và tài liệu, loại trừ `.git`, `.env`, database cục bộ, virtualenv, media/log và các thư mục backup.

**Đã làm:** thêm form tạo/chỉnh sửa hoạt động trong cổng `/portal/project-activities/`; dashboard có nút tạo và liên kết chỉnh sửa; giới hạn quyền theo role. Quản lý dự án/Điều phối viên được xem công văn đi để liên kết hoạt động; quyền xem trong sổ công văn của hai role này chỉ giới hạn loại Công văn đi. CBDA không được tạo hoạt động. Cảnh báo trùng lịch vẫn cho phép lưu. Sửa liên kết từ sổ cũ `office.OutgoingDocument` sang công văn thật đang dùng `document.OfficialDispatch`, dùng ngày gửi để tính hạn, người ký làm người giao dự phòng. Thêm migration `activity.0004` và form/test.

**Database:** kết nối đã xác nhận là backend SQL Server, database `qlhcns`. Trước khi chạy migration, truy vấn chỉ đọc xác nhận `tblActivity` chưa tồn tại và các migration mới chưa được áp dụng. Sau đó `manage.py migrate` thành công với `activity.0001_initial`, `task.0002_activity_report_fields`, `activity.0003_seed_project_roles`, `activity.0004_alter_activity_outgoing_document`. Đã xác nhận bảng `tblActivity`, cột `ActivityID` và `report_file` trên `tblTask`, khóa ngoại tới `tblActivity`/`tblOfficialDispatch`, và các role PROJECT_MANAGER / PROJECT_COORDINATOR / CBDA đã có. `showmigrations` đánh dấu các migration đã chạy; `migrate --check` không còn migration chờ.

**Kiểm tra:** `manage.py check` đạt; `makemigrations --check --dry-run` báo không có thay đổi chưa tạo migration; 100 test (gồm 14 test mới của Activity) đạt trên SQLite test database tạm. Thực hiện smoke test thật cho storage `activity_reports`: upload, đọc lại đúng nội dung, xác nhận thư mục `BaoCaoHoatDong`, rồi xóa tệp thử thành công. Đây là kiểm tra storage, chưa thay cho UAT tải báo cáo qua giao diện. Xuất hiện cảnh báo môi trường `RequestsDependencyWarning` urllib3/chardet nhưng không ảnh hưởng kết quả.

**Còn mở:** người phụ trách gán role cho tài khoản UAT; thử tạo hoạt động, cảnh báo trùng lịch, liên kết công văn, kiểm tra Task/hạn, tải báo cáo qua Task và xem dashboard bằng từng vai trò. Windows Task Scheduler chưa đăng ký theo ưu tiên hiện tại; nếu thứ Bảy được tính là ngày làm việc, cần bổ sung lịch cấu hình trước UAT nghiệp vụ. Thư mục SharePoint `BaoCaoHoatDong` do người dùng báo đã tạo và smoke test storage đã xác nhận truy cập được.

**Nhánh/commit:** `chore/django-5.2-upgrade`, `02b58a3` (`feat: add project activity management screens`).

## 2026-09-25 — Bảo mật ứng dụng, log và quy trình backup SQL Server

**Phạm vi:** ghi nhận các thay đổi sẵn có trong workspace trước khi đẩy mã nguồn phân hệ Hoạt động dự án lên GitHub.

**Sao lưu:** tạo `D:\QLHCNS-Backup-before-shared-dashboard-20260925` trước khi tiếp tục. Loại trừ `.git`, `.env`, database cục bộ, virtualenv, media, log và các thư mục backup.

**Đã rà soát và đưa vào commit:** cấu hình HTTPS/cookie có bật theo biến `ENABLE_HTTPS_ENFORCEMENT`; logging có xoay vòng file; cập nhật ví dụ cấu hình, bản DOCX hướng dẫn và bộ script/checklist backup, backup transaction log, retention và diễn tập restore cho SQL Server Express. Không đưa thư mục backup thực tế `Backups/`, log backup, file rỗng `src/qlhcns` hoặc `.env` vào Git.

**Kiểm tra:** `D:\QLHCNS\venv\Scripts\python.exe src\manage.py check` đạt; `makemigrations --check --dry-run` báo `No changes detected`. Có cảnh báo dependency `RequestsDependencyWarning`, không làm thất bại kiểm tra. Nhật ký hiện có trong `Backups/backup-log.txt` ghi nhận full backup và transaction-log backup đã chạy thành công; Codex chỉ đọc log, không chạy backup trong đợt này.

**Nhánh/commit/push:** nhánh `chore/django-5.2-upgrade` đã được push; commit `8605eb1`.

**Đã hoàn tất:** phần Dashboard chung cho Hoạt động dự án được ghi ở mục nhật ký kế tiếp.


## 2026-09-24 — Đề xuất mở rộng IHRMS cho hoạt động dự án NGO/MEL

**Mục tiêu/phạm vi:** đánh giá yêu cầu lập kế hoạch tháng, điều phối CBDA, lịch, MEL, ngân sách và quyết toán; lập lộ trình code theo các cổng phê duyệt.

**Đã rà soát:** Project Charter, RBAC matrix, apps.project.Project, apps.task.Task, apps.planning.Event/AnnualBudget, apps.document.OfficialDispatch, các route/template giao việc/sự kiện và quyền hiện hành. Charter hiện loại Grant, ngân sách tài trợ, hoạt động phát triển cộng đồng và MEL khỏi phạm vi; model hiện chưa hỗ trợ workflow NGO đầy đủ.

**Đã tạo:** docs/NGO_Activity_Planning_MEL_Roadmap.md ghi nhận nhận xét hiện trạng, luồng mục tiêu, mô hình dữ liệu/tích hợp, quyền, dashboard, tiêu chí nghiệm thu, ước lượng 7–10 tuần và quyết định NGO cần chốt. Đây là đề xuất; chưa sửa code, Charter, migration hay cấu hình.

**Ranh giới kiến trúc được làm rõ:** miền Hoạt động dự án riêng; Hộp việc của tôi, thành phần giao việc/lịch, trao đổi, thông báo và nhắc hạn dùng chung; dashboard dự án riêng. KPI nhân sự và chỉ số MEL dùng mô hình, quyền, công thức và báo cáo riêng, chỉ tái sử dụng thành phần hiển thị. Chưa sửa code hoặc schema.

**Kiểm tra phần hành chính–nhân sự (24/09/2026):** Codex chạy `python src/manage.py check` (đạt), `makemigrations --check --dry-run` (No changes detected), và 86 test trên SQLite test database tạm (đạt). Codex xác nhận kết nối cấu hình hiện tại tới SQL Server bằng `connection.vendor=microsoft` và `SELECT 1`; chưa chạy test suite SQL Server vì chưa xác minh đó là database SIT riêng, an toàn cho Django tạo/xóa test database. Người dùng trước đó báo các luồng nghiệp vụ chạy bình thường; báo cáo này chưa phải UAT ký nhận.

**Còn mở:** Chưa đủ điều kiện go-live/pilot với dữ liệu thật. Cần test SQL Server SIT, `check --deploy` trên cấu hình máy chủ, UAT có biên bản, xác nhận backup/restore và quyền dữ liệu. Với phân hệ NGO, Ban Giám đốc cần phê duyệt mở rộng Charter; Chương trình/MEL/Tài chính/IT chốt RACI, SLA, xung đột lịch, tiền tệ, chứng từ, dữ liệu người tham gia và database SIT trước khi có schema/migration. Chủ dự án làm theo mục “Việc chủ dự án cần điều phối ở Cổng 0” trong roadmap; không gửi dữ liệu thụ hưởng định danh qua chat.

## 2026-09-25 — Tổng quan Hoạt động dự án trên Dashboard chung

**Mục tiêu/phạm vi:** hiển thị tiến độ dự án trong Dashboard trang chủ dành cho Ban Giám đốc, Quản lý dự án và Trưởng phòng; giữ dashboard hoạt động chuyên biệt hiện tại.

**Sao lưu trước thay đổi:** tạo `D:\QLHCNS-Backup-before-shared-dashboard-implementation-20260925`; không sao chép `.env`, database, virtualenv, media, log hoặc thư mục backup.

**Đã làm:** Dashboard chung có số hoạt động trong tháng, Task báo cáo hoàn thành, Task quá hạn, Task thiếu báo cáo và hoạt động chưa có Task, kèm liên kết sang dashboard hoạt động đúng tháng. Bổ sung quyền xem dashboard hoạt động cho `DEPT_MANAGER`; queryset của vai trò này chỉ gồm hoạt động thuộc dự án có phòng ban do nhân viên đó quản lý. Không thay đổi quyền quản lý/tạo hoạt động và không sửa schema.

**Kiểm tra:** `manage.py check` đạt; `makemigrations --check --dry-run` báo `No changes detected`; `manage.py test apps.activity.tests apps.security.tests --verbosity 1` đạt: 34 test trên SQLite test database tạm. `RequestsDependencyWarning` về urllib3/chardet vẫn xuất hiện nhưng không ảnh hưởng kết quả. Không chạy migrate hay test database trên SQL Server.

**Nhánh/commit/push:** `chore/django-5.2-upgrade`; commit `8312f09` đã push.

**Đã hoàn tất:** mục tổng quan hoạt động dự án đã được bổ sung vào Dashboard chung; phần giao diện/lịch mở rộng được ghi ở mục nhật ký kế tiếp.

## 2026-09-25 — Đồng nhất biểu mẫu và lịch Hoạt động dự án

**Mục tiêu/phạm vi:** làm rõ viền các ô nhập/chọn trên giao diện portal; dùng danh mục `docs/ActCode.md` cho Mã hoạt động; bổ sung lọc theo CBDA và trang lịch tháng.

**Sao lưu trước thay đổi:** tạo `D:\QLHCNS-Backup-before-activity-ui-filters-calendar-20260925`, loại trừ `.git`, `.env`, database, virtualenv, media, log và các thư mục backup.

**Đã làm:** thêm stylesheet dùng chung `src/static/css/ihrms.css` và nạp từ template gốc để chuẩn hóa viền, nền, bo góc và trạng thái focus cho input/select/textarea/file trên portal. Đưa danh mục 18 mã/tên từ `docs/ActCode.md` vào dropdown; tên tự điền và máy chủ xác định lại theo mã khi lưu. Dashboard Hoạt động có lọc CBDA; thêm lịch theo tháng hiển thị ngày diễn ra và hạn báo cáo, với cùng bộ lọc. CBDA chỉ thấy hoạt động được phân công theo quyền hiện tại. Thêm liên kết lịch vào điều hướng. Không sửa database/schema.

**Kiểm tra:** `manage.py check` đạt; `makemigrations --check --dry-run` báo `No changes detected`; 36 test `apps.activity.tests` và `apps.security.tests` đạt trên SQLite test database tạm; chạy lại riêng test render form tạo hoạt động đạt. Có cảnh báo `RequestsDependencyWarning` urllib3/chardet, không làm test thất bại. `findstatic css/ihrms.css` tìm thấy stylesheet. Không chạy migration hay test lên SQL Server.

**Nhánh/commit/push:** `chore/django-5.2-upgrade`; thay đổi đã được push lên GitHub.

**Còn mở:** đăng nhập bằng CBDA và tài khoản quản lý để kiểm tra trực quan trên trình duyệt; cập nhật danh mục mã hoạt động đồng bộ khi danh sách nghiệp vụ thay đổi.
## 2026-09-25 — Chuyển email xin duyệt hoạt động sang SMTP

**Phạm vi:** Công ty nhận thư bằng POP3 và nhân viên dùng Microsoft Outlook; ứng dụng IHRMS gửi thư qua SMTP của nhà cung cấp email. Microsoft Graph tiếp tục được dùng riêng cho SharePoint.

**Sao lưu trước thay đổi lớn:** `D:\QLHCNS-Backup-before-smtp-email-20260925`; đã tạo bản sao sạch, loại trừ `.git`, `.env`, database, virtualenv, media, log và thư mục backup.

**Đã làm:** bổ sung hồ sơ đề xuất có phiên bản gắn với Activity, lưu cặp Excel/PDF cho đề xuất và dự trù kinh phí lên SharePoint; CBDA tải/cập nhật hồ sơ, ĐPV chọn Giám đốc và gửi hai PDF để xin duyệt, Giám đốc được chỉ định ghi nhận phê duyệt/yêu cầu chỉnh sửa trên IHRMS. Thay luồng gửi từ Microsoft Graph `sendMail` sang Django SMTP. Người nhận là email công ty của Giám đốc; From lấy từ `DEFAULT_FROM_EMAIL`/tài khoản SMTP và Reply-To là email công ty của ĐPV. Không sinh mẫu Excel/PDF tự động ở giai đoạn này. Cấu hình SMTP nằm trong `.env.example`; không lưu thông tin đăng nhập thật trong mã nguồn. POP3 không được dùng để gửi email. SharePoint vẫn dùng Graph.

**Kiểm tra:** `manage.py check` đạt; `makemigrations --check --dry-run` báo `No changes detected`; 109 test của asset/common/hrm/leave/payroll/security/activity/m365 đạt trên SQLite test database tạm, bao gồm test SMTP giả lập xác nhận người gửi/người nhận/Reply-To và hai tệp PDF đính kèm. Không gửi email thật; chưa kiểm tra máy chủ SMTP của công ty vì chưa có thông số nhà cung cấp. Cảnh báo RequestsDependencyWarning vẫn xuất hiện nhưng không làm test thất bại.

**Cấu hình còn cần từ IT/nhà cung cấp email:** SMTP host, port, phương thức mã hóa (STARTTLS hoặc SSL), tài khoản gửi được phép dùng và địa chỉ From được ủy quyền. Quản trị viên nhập các giá trị vào `D:\QLHCNS\.env`; không gửi mật khẩu qua chat. Sau đó cần kiểm thử gửi tới một địa chỉ nội bộ. POP3 không cần cấu hình cho chức năng gửi thư này.

**Migration:** không có thay đổi schema; không chạy migration lên SQL Server.

**Nhánh/commit/push:** `chore/django-5.2-upgrade`; commit `4998a91` đã push.

## 2026-09-25 — Áp dụng migration hồ sơ đề xuất trên SQL Server

**Sự cố:** trang `/portal/project-activities/1/proposal/` báo SQL Server không tìm thấy `tblActivityProposal`.

**Nguyên nhân và xử lý:** cấu hình ứng dụng đang kết nối SQL Server database `qlhcns`; migration `activity.0005_activityproposal` chưa được áp dụng. Kiểm tra `migrate activity --plan` chỉ định tạo bảng `ActivityProposal`, sau đó chạy `manage.py migrate activity`. Migration hoàn tất; `showmigrations activity` xác nhận `0005` đã áp dụng.

**Xác minh:** truy vấn `ActivityProposal.objects.count()` chạy được trên SQL Server và hiện có 0 hồ sơ. Không sửa dữ liệu hiện có hoặc tạo migration mới. Cảnh báo RequestsDependencyWarning vẫn xuất hiện nhưng lệnh migration và truy vấn đều thành công.

**Còn mở:** tải lại trang hồ sơ đề xuất để xác nhận giao diện hoạt động; các tệp đính kèm vẫn cần cấu hình SMTP trước khi gửi email thật.

## 2026-09-25 — Sửa lỗi form upload hồ sơ đề xuất

**Sự cố:** POST upload Excel/PDF trả `NoReverseMatch` vì template tạo URL tải tệp với `package_id=None` khi form không hợp lệ và hồ sơ phiên bản mới chưa có bản ghi lưu.

**Thay đổi:** `src/apps/activity/views.py` chỉ truyền hồ sơ đã có khóa chính vào khu vực hiển thị liên kết file. Form không hợp lệ vẫn được render cùng thông báo lỗi; không tạo hồ sơ rỗng. Bổ sung test hồi quy trong `src/apps/activity/tests.py` với phần mở rộng PDF sai.

**Kiểm tra:** 6 test `ActivityProposalWorkflowTests` đạt; `manage.py check` đạt; `makemigrations --check --dry-run` báo `No changes detected`. Bộ test dùng storage cục bộ giả lập; chưa thực hiện upload SharePoint thật trong lần sửa này.

**Còn mở:** thử tải lại bộ hồ sơ với hai tệp `.pdf`. Excel chỉ dùng để lập hồ sơ tại máy cá nhân, không cần tải lên IHRMS.

## 2026-09-25 — Chỉ tải PDF cho hồ sơ xin duyệt hoạt động

**Yêu cầu:** người dùng xác nhận Excel chỉ được hoàn thiện tại máy cá nhân; IHRMS cần nhận hai PDF để lưu trên SharePoint và đính kèm email xin duyệt.

**Thay đổi:** form chỉ nhận `proposal_pdf` và `budget_pdf`; trang chỉ hiển thị hai PDF; gửi email chỉ yêu cầu và đính kèm hai PDF. Excel không còn bắt buộc hoặc tải lên. Các cột Excel cũ trong `tblActivityProposal` được giữ nguyên để bảo toàn metadata/file tham chiếu cũ; không cần migration.

**Kiểm tra:** 7 test `ActivityProposalWorkflowTests` đạt, gồm xác nhận Điều phối viên thấy nút gửi sau khi chỉ có hai PDF và form không hiện ô Excel; `manage.py check` đạt; `makemigrations --check --dry-run` báo `No changes detected`; `git diff --check` đạt. Chưa chạy upload thật lên SharePoint.

**Sao lưu:** `D:\QLHCNS-Backup-before-pdf-only-20260925`, bản sao sạch tạo trước khi sửa.

**Còn mở:** thử tải hai PDF lên SharePoint và xác nhận nút gửi xuất hiện khi đăng nhập đúng vai trò Điều phối viên được phân công/Quản lý dự án/Quản trị viên. Gửi email thật vẫn cần SMTP được cấu hình.

## 2026-09-25 — Soạn email xin duyệt trong Outlook để người dùng tự gửi

**Lý do:** nhà cung cấp POP3/SMTP từ chối xác thực SMTP; Điều phối viên yêu cầu tự xem, sửa thư, thêm CC và bấm gửi trong Outlook.

**Sao lưu trước thay đổi lớn:** `D:\QLHCNS-Backup-before-outlook-compose-20260925`; bản sao sạch tạo trước khi sửa, loại trừ `.git`, `.env`, database, virtualenv, media, log và backup.

**Thay đổi:** bỏ gửi thư SMTP phía server và cấu hình SMTP khỏi `settings.py`/`.env.example`. IHRMS tạo liên kết `mailto:` mở thư nháp trong ứng dụng email mặc định, điền To/Subject/body; hiển thị email ĐPV dự kiến, cho người dùng tự kiểm tra From/To, thêm CC và sửa nội dung. Hai PDF được tải qua liên kết có kiểm tra quyền rồi người dùng tự đính kèm trong Outlook. Sau khi gửi thật, người dùng đánh dấu/xác nhận trong IHRMS; trạng thái `Submitted` dựa trên xác nhận đó, không phải xác nhận SMTP.

**Giới hạn client email:** `mailto:` không thể ép chọn tài khoản From hoặc gắn file đính kèm. Windows cần liên kết mailto với Outlook; người dùng chọn/kiểm tra From và đính kèm hai PDF đã tải. Nếu Outlook chưa được đặt làm ứng dụng mailto mặc định, cần chọn Outlook trong Windows Default apps.

**Kiểm tra:** 7 test `ActivityProposalWorkflowTests` đạt; `manage.py check` đạt; `makemigrations --check --dry-run` báo `No changes detected`; `git diff --check` đạt. Test xác nhận To/Subject/body, tải PDF, không ghi nhận đã gửi trước xác nhận; chưa tự mở giao diện Outlook trên máy người dùng.

**Còn mở:** thử nút “Soạn thư trong Outlook”, tải và đính kèm hai PDF, kiểm tra tài khoản From và người nhận, tự bấm Gửi rồi xác nhận trong IHRMS.

## 2026-09-25 — Hàng chờ duyệt đề xuất hoạt động và thông báo trong IHRMS

**Nhu cầu:** Giám đốc dự án cần mở hồ sơ từ menu IHRMS thay vì bắt buộc tìm email; khi yêu cầu chỉnh sửa hoặc phê duyệt, người gửi cần biết kết quả ngay trong hệ thống.

**Thay đổi:** Thêm quyền riêng `approve_activity_proposals` cho vai trò Giám đốc, mục **Duyệt đề xuất hoạt động** trong menu **Duyệt & Xử lý**, kèm số hồ sơ chờ duyệt. Trang hàng chờ chỉ liệt kê đề xuất có trạng thái `Submitted` và được giao đúng cho tài khoản đang đăng nhập. Từ danh sách, quản lý mở hồ sơ, xem hai PDF, chọn phê duyệt/yêu cầu chỉnh sửa và nhập ý kiến.

Khi Điều phối viên xác nhận đã gửi thư Outlook, IHRMS tạo thông báo cho Giám đốc được chọn. Sau khi Giám đốc quyết định, IHRMS tạo thông báo cho nhân viên gửi hồ sơ, chứa ý kiến và liên kết mở lại hồ sơ. Người nhận xem thông báo qua chuông và trang **Thông báo** hiện có. Email vẫn có thể dùng để báo tin/mở hồ sơ; hàng chờ menu là đường vào độc lập.

**Kiểm tra:** 8 test `apps.activity.tests.ActivityProposalWorkflowTests` đạt; `manage.py check` đạt; `makemigrations --check --dry-run` báo `No changes detected`; `git diff --check` đạt. Chưa cần migration. Test xác nhận quyền hàng chờ, thông báo khi gửi, thông báo yêu cầu chỉnh sửa và liên kết hồ sơ.

**Sao lưu trước thay đổi:** `D:\QLHCNS-Backup-before-activity-approval-inbox-20260925`.

**Còn cần xác minh trên giao diện thật:** đăng nhập vai trò Giám đốc để kiểm tra mục menu/số chờ và xử lý hồ sơ; đăng nhập Điều phối viên để mở chuông/thông báo và xác nhận nội dung ý kiến hiển thị.

## 2026-09-25 — Hiển thị phản hồi đề xuất trên danh sách hoạt động và gửi cho CBDA/ĐPV

**Phản hồi người dùng:** Giám đốc đã yêu cầu chỉnh sửa nhưng tài khoản Điều phối viên và CBDA không thấy thông báo; danh sách hoạt động cũng chưa thể hiện trạng thái hồ sơ.

**Nguyên nhân:** thông báo trước đó chỉ gửi cho tài khoản đã xác nhận gửi Outlook (`submitted_by`), trong khi CBDA lập hồ sơ có thể là người khác. Dashboard hoạt động chỉ hiển thị Task và tệp báo cáo, chưa lấy phiên bản đề xuất mới nhất nên trạng thái/ý kiến yêu cầu sửa bị khuất.

**Thay đổi:** Khi Giám đốc yêu cầu chỉnh sửa, tạo thông báo cho người gửi, người tạo hồ sơ, CBDA phụ trách và ĐPV; loại bỏ nhân viên trùng để mỗi người chỉ nhận một thông báo. Dashboard hoạt động nay hiển thị trạng thái hồ sơ gần nhất và nội dung Giám đốc yêu cầu chỉnh sửa ngay dưới tên hoạt động. Trạng thái hồ sơ được tải theo hoạt động trong cùng truy vấn tổng hợp; không thay đổi cấu trúc CSDL.

**Kiểm tra:** 8 test `ActivityProposalWorkflowTests` đạt trên SQLite kiểm thử; test xác nhận cả CBDA và ĐPV nhận thông báo, trạng thái/ý kiến hiển thị ở dashboard. `manage.py check`, `makemigrations --check --dry-run` và `git diff --check` đều đạt.

**Lưu ý dữ liệu cũ:** thông báo trong hệ thống không tự tạo ngược cho quyết định đã ghi nhận trước thay đổi này. Tuy nhiên, trạng thái và ý kiến đã lưu sẽ hiển thị trong dashboard khi hoạt động thuộc tháng đang xem; mở **Đề xuất & dự trù** cũng thấy lịch sử quyết định. Nếu quyết định hiện tại được tạo trước bản cập nhật, Giám đốc có thể mở lại hồ sơ và ghi nhận lại phản hồi sau khi cập nhật nếu cần gửi thông báo mới.

## 2026-09-25 — Chỉnh lịch hoạt động vừa chiều rộng màn hình

**Yêu cầu:** xem trọn lịch hoạt động mà không phải kéo ngang.

**Thay đổi:** bỏ chiều rộng tối thiểu 980px và vùng cuộn ngang; lưới bảy ngày co theo khung màn hình. Thu gọn khoảng đệm/cỡ chữ trên màn hình nhỏ, cho mã/tên hoạt động xuống dòng và ẩn tên CBDA trong thẻ lịch ở cỡ điện thoại để ngày trong tuần và hoạt động vẫn đọc được. Trên màn hình từ cỡ tablet trở lên tiếp tục hiện CBDA phụ trách.

**Kiểm tra:** test lịch CBDA đạt; `manage.py check` và `git diff --check` đạt. Đây là thay đổi template, không cần migration.

## 2026-09-25 — Tách Hoạt động dự án thành menu điều hướng riêng

**Yêu cầu:** gom các chức năng theo dõi/lịch hoạt động dự án thành một khu vực điều hướng riêng ở cuối thanh menu, không để lẫn trong menu Cá nhân.

**Thay đổi:** bỏ hai liên kết Hoạt động dự án khỏi menu Cá nhân và thêm menu riêng **Hoạt động dự án** sau cùng, sau Báo cáo. Menu có lối vào **Theo dõi hoạt động** và **Lịch hoạt động**; chỉ tài khoản có quyền xem dashboard hoạt động mới nhìn thấy menu này. Mục duyệt đề xuất vẫn nằm trong **Duyệt & Xử lý** theo đúng chức năng phê duyệt.

**Kiểm tra:** test lịch CBDA xác nhận menu và các lối vào được render; `manage.py check` và `git diff --check` đạt. Không có thay đổi database.

## 2026-09-25 — Đồng bộ cẩm nang, giáo án, roadmap, changelog và skills

**Mục tiêu:** để hướng dẫn người dùng và quy trình hỗ trợ nội bộ khớp với giao diện/luồng Hoạt động dự án vừa triển khai; loại bỏ chỉ dẫn kỹ thuật cũ có thể làm lệch thao tác sau này.

**Tài liệu cập nhật:**
- `HUONG_DAN_SU_DUNG_IHRMS.md`: menu riêng Hoạt động dự án; các bước CBDA chuẩn bị hai PDF, ĐPV soạn/gửi Outlook và xác nhận trong IHRMS, Giám đốc vào hàng chờ để quyết định; nơi nhận thông báo và cách xem trạng thái/ý kiến; nhắc về dashboard lọc theo tháng, file Excel và giới hạn phạm vi tài chính.
- `TAP_HUAN_IHRMS.md`: thêm bài thực hành 45 phút theo ba vai trò CBDA/ĐPV/Giám đốc, hộp thư demo, thông báo và trường hợp quyết định cũ.
- `docs/NGO_Activity_Planning_MEL_Roadmap.md`: cập nhật phạm vi hiện tại, quy trình Outlook/approval, dashboard/menu và các hạng mục UAT/Task Scheduler còn mở.
- `docs/CHANGELOG.md`: ghi nhận các bổ sung hiện tại và dẫn về work log làm nguồn lịch sử chi tiết duy nhất.
- `README.md`: cập nhật Django 5.2, các tài liệu người dùng và giới thiệu đúng phạm vi module.
- `.agents/skills/ihrms-project/SKILL.md`, `.agents/skills/ihrms-operations/SKILL.md`: bỏ thông tin lỗi thời về gitlink/Django 5.0/SQLite đang là backend duy nhất; hướng dẫn kiểm tra backend và mô tả đúng lưu trữ SharePoint, gửi thư Outlook thủ công, hàng chờ/notification và giới hạn module.

**Kiểm tra:** các file đọc/ghi UTF-8; `git diff --check` đạt. Đây là cập nhật Markdown, không thay đổi code/schema và không cần migration.

**Nhánh/commit:** `chore/django-5.2-upgrade`; các commit code nền trước đó `482bc44`, `218494c`, `935b5de`, `309e4fd`. Đợt tài liệu này sẽ được commit riêng sau khi rà soát diff.

**Còn mở:** chủ dự án/đầu mối nghiệp vụ cần rà lại SOP/giờ hạn/người duyệt theo chính sách NGO nội bộ trước khi phát hành tài liệu tập huấn chính thức. Kịch bản email thật và vận hành nhắc hạn Windows Task Scheduler vẫn cần UAT/IT xác nhận; nội dung tài liệu phân biệt rõ các bước này với chức năng đã kiểm tra.

## 2026-09-25 — Sửa lỗi nhắc hạn activity, bổ sung test bảo mật và lập kế hoạch HRMS

**Mục tiêu:** xử lý bug báo cáo từ Claude, khóa hồi quy cho các luồng nhạy cảm trong portal, đồng thời chia 4 hạng mục HRMS còn lại thành lộ trình có cổng nghiệp vụ/kỹ thuật.

**Sao lưu:** tạo `D:\QLHCNS-Backup-before-review-followup-20260925` trước khi làm; chứa bản sao mã nguồn/tài liệu đã tracked, không chứa `.git`, `.env`, virtualenv, database, media, log, cache hoặc dữ liệu người dùng. Giữ nguyên các mục chưa tracked sẵn có `Backups/` và `src/qlhcns`.

**Thay đổi mã:** thêm `from django.conf import settings` vào `src/apps/activity/services.py` để lệnh nhắc hạn không lỗi `NameError`. Thay placeholder `src/apps/portal/tests.py` bằng 5 regression tests cho quy tắc tự duyệt nghỉ theo vai trò, khóa kỳ lương, HR officer duyệt thanh lý tài sản và giới hạn xem phiếu lương chưa phát hành. Đây là test bảo vệ hành vi hiện có; không đổi chính sách nghiệp vụ.

**Tài liệu:** tạo [`docs/HRMS_Next_Features_Plan.md`](HRMS_Next_Features_Plan.md) với phân tích hiện trạng, phạm vi, kiến trúc, tiêu chí nghiệm thu và dữ liệu cần chủ dự án/IT/HR/Kế toán xác nhận cho: thông báo duyệt/nhắc việc, checklist onboarding/offboarding liên kết tài sản, báo cáo tuân thủ/chi phí lương, sơ đồ tổ chức/yêu cầu tự cập nhật hồ sơ. Thêm liên kết từ README.

**Quyết định biểu mẫu:** đầu bài ghi D02-TS; tài liệu BHXH hiện hành tham khảo D02-LT thay thế, vì vậy yêu cầu Kế toán/đơn vị dịch vụ BHXH xác nhận phiên bản trước khi code. Quyết toán PIT cũng cần xác nhận biểu mẫu/phụ lục hiện hành theo năm; không tự động nộp hồ sơ. Email: quyền Graph lưu SharePoint không đồng nghĩa quyền gửi Exchange; công ty dùng POP3/Outlook nên email tự động phải chờ IT xác nhận Graph Mail.Send hoặc SMTP relay. Giai đoạn đầu ưu tiên thông báo trong ứng dụng và outbox có thể tắt email.

**Kiểm tra:** `apps.asset.tests`, `apps.common.tests`, `apps.hrm.tests`, `apps.leave.tests`, `apps.payroll.tests`, `apps.security.tests`, `apps.activity.tests`, `apps.portal.tests`: 112/112 pass trên SQLite. `apps.m365.tests`: 5/5 pass trên SQLite; tổng các module đã gọi là 117/117. `manage.py check` sạch; `makemigrations --check --dry-run` báo không có thay đổi; `git diff --check` sạch. Lệnh `manage.py test` không có nhãn vẫn tự tìm 0 test trong cấu hình này, nên cần tiếp tục gọi module test rõ ràng hoặc sửa test discovery/CI riêng. Pyflakes chưa chạy được vì package chưa cài. SQL Server chưa được kiểm thử trong đợt này. Môi trường phát ra `RequestsDependencyWarning` do phiên bản dependency; không ảnh hưởng kết quả test nhưng cần xử lý riêng.

**Phạm vi chưa làm:** chưa code 4 tính năng mới; tài liệu là kế hoạch triển khai theo commit nhỏ. Chưa chạy test suite trên SQL Server SIT. Các biểu mẫu pháp lý, quy tắc phân bổ chi phí và chính sách email cần được người phụ trách xác nhận trước khi phát triển tương ứng.

**Nhánh/commit:** `chore/django-5.2-upgrade`; ghi commit sau khi rà soát diff. Chưa push trong đợt này.

## 2026-09-26 — Chuẩn hóa menu điều hướng toàn cổng IHRMS

**Yêu cầu:** sửa menu các trang bị co hẹp, làm chữ tiêu đề xuống dòng như ảnh người dùng gửi; giữ trải nghiệm nhất quán giữa các trang.

**Sao lưu trước khi sửa:** `D:\QLHCNS-Backup-before-menu-fix-20260926-091916` (356 tệp; loại `.git`, `.env`, virtualenv, database, media/cache). Sao lưu bao gồm cả trạng thái làm việc hiện thời; không thay đổi hoặc đưa các mục chưa theo dõi hiện hữu `Backups/`, `src/qlhcns` vào Git.

**Thay đổi:** cập nhật template dùng chung `src/templates/base.html` và stylesheet `src/static/css/ihrms.css`. Mở rộng khung menu vượt giới hạn 1024px cũ; các mục giữ nhãn trên một dòng và thanh điều hướng xuống hàng giữa các nhóm khi viewport hẹp. Menu xổ xuống có giới hạn chiều cao, cuộn dọc khi dài; nút có trạng thái ARIA, đóng khi click ngoài hoặc nhấn Escape và trả focus về nút mở. Các trang kế thừa `base.html` gồm cổng portal, dashboard reporting và hoạt động dự án nên cùng nhận kiểu menu này.

**Sửa kiểm thử phát hiện trong lúc xác minh:** dữ liệu CCCD giả trong regression tests portal được rút còn 20 ký tự để tương thích SQL Server; test nhắc hạn activity dùng ngày thứ Hai cố định và mô phỏng thời điểm tạo thông báo, không còn phụ thuộc thứ/ngày chạy thực tế.

**Kiểm tra:** `manage.py check` đạt. Chạy `manage.py test apps.asset.tests apps.common.tests apps.hrm.tests apps.leave.tests apps.payroll.tests apps.security.tests apps.activity.tests apps.portal.tests apps.m365.tests --verbosity 1` trực tiếp với SQL Server; 117/117 pass trên database test và Django tự hủy database test sau khi chạy. `git diff --check` đạt. Môi trường vẫn hiện `RequestsDependencyWarning` do các phiên bản urllib3/chardet; không làm test thất bại.

**Còn mở:** cần kiểm tra trực quan menu trên trình duyệt với các độ rộng màn hình thực tế trước khi triển khai cho nhân viên.

**Nhánh/commit:** `chore/django-5.2-upgrade`, commit `5ddb3a7` (`fix: make portal navigation responsive and accessible`); chưa push.

## 2026-09-26 — Căn lại khung menu theo bố cục trang

**Phản hồi:** menu vẫn lệch trái so với logo và nội dung do khung điều hướng rộng 1280px trong khi header/nội dung dùng khung `max-w-5xl` (1024px).

**Sửa:** đồng bộ `.portal-nav-inner` về 64rem và lề ngang 1.5rem như header/nội dung, kể cả màn hình nhỏ; vẫn giữ nguyên cơ chế không ngắt chữ trong nhãn và xuống hàng giữa các mục khi thiếu chỗ.

**Kiểm tra:** `manage.py check`, `makemigrations --check --dry-run` và `git diff --check` đạt; không thay đổi dữ liệu/schema.

**Nhánh/commit:** `chore/django-5.2-upgrade`; ghi commit sau rà soát. Chưa push.

## 2026-09-26 — Bản nháp Outlook cho thông báo nghiệp vụ (hạng mục 1)

**Mục tiêu/phạm vi:** bổ sung nhật ký outbox cho email cần người dùng xem lại và gửi thủ công bằng Outlook desktop; không gửi SMTP/Graph tự động. Tích hợp với quyết định nghỉ phép, khóa kỳ lương và duyệt công văn/tài liệu. Tách hàm tạo `mailto:` dùng chung cho thông báo hoạt động.

**Tệp/phân hệ:** `apps/common/email_draft.py`; `apps/notification` (model, service, migration, tests); `apps/portal` (luồng thông báo, xác nhận đã gửi, template/URL); `apps/activity/services.py`.

**Đã làm:** thêm bảng `tblNotificationEmailOutbox`, khóa idempotency, trạng thái Draft/Sent và thông tin người xác nhận; hiển thị link mở Outlook và nút xác nhận trong trang thông báo; không đưa dữ liệu lương/chi tiết nhạy cảm vào thư. Mỗi sự kiện nghiệp vụ tạo thông báo trong ứng dụng và bản nháp tương ứng trong cùng transaction. Backup trước thay đổi: `D:\QLHCNS-Backup-before-4-features-20260926-101643`.

**Kiểm tra:** trên SQL Server qua Django test database: `manage.py test apps.notification.tests apps.portal.tests apps.activity.tests --verbosity 1` — 40/40 pass; test DB được Django xóa sau khi chạy. `manage.py check` đạt; `makemigrations --check --dry-run` báo không có thay đổi chưa migration; `git diff --check` đạt. Môi trường có `RequestsDependencyWarning` nhưng không ảnh hưởng kết quả.

**An toàn/vận hành:** máy chủ không gửi thư. Người nhận mở Outlook, kiểm tra/sửa/gửi thật, rồi xác nhận đã gửi trong IHRMS. Chưa kiểm thử bằng Outlook desktop tương tác.

**Commit:** `bdfa3a9` (`feat: add Outlook draft notification outbox`) trên `chore/django-5.2-upgrade`.

**Còn mở:** triển khai hạng mục 4 (sơ đồ tổ chức và yêu cầu tự cập nhật hồ sơ), kế tiếp checklist onboarding/offboarding. Hạng mục báo cáo chỉ tạo khung kỹ thuật fail-closed theo chỉ đạo “chưa xuất báo cáo”, chờ Kế toán xác nhận biểu mẫu và quy tắc phân bổ.
## 2026-09-26 — Sơ đồ tổ chức và yêu cầu cập nhật hồ sơ (hạng mục 4)

**Mục tiêu/phạm vi:** cung cấp sơ đồ nhân sự nội bộ và quy trình nhân viên đề nghị thay đổi email cá nhân, số điện thoại hoặc địa chỉ; Nhân sự duyệt, từ chối hoặc yêu cầu bổ sung. Hồ sơ Employee chỉ thay đổi sau khi duyệt.

**Tệp/phân hệ:** `apps/hrm` (model + migration + tests); `apps/portal` (views, URLs, mẫu sơ đồ/form/danh sách); `apps/security/permissions.py`; `templates/base.html`.

**Đã làm:** sơ đồ dựng cây từ nhân viên Active, không truy vấn N+1, không hiển thị liên hệ riêng, chịu được dữ liệu quản lý có vòng lặp; yêu cầu thay đổi dùng whitelist kiểm tra cả phía server/model, lưu snapshot để chặn duyệt nếu giá trị đã đổi, khóa transaction khi duyệt, thông báo kết quả, giới hạn xem/tải chứng từ cho chính nhân viên hoặc Nhân sự. Migration mới chỉ tạo bảng `tblEmployeeProfileChangeRequest`, không sửa bảng nhân viên. Backup trước giai đoạn: `D:\QLHCNS-Backup-before-feature4-20260926-102541`.

**Kiểm tra:** trên SQL Server test database: `manage.py test apps.hrm.tests apps.portal.tests --verbosity 1` — 13/13 pass; Django tự xóa test database. `manage.py check` đạt; `makemigrations --check --dry-run` báo không có thay đổi chưa migration; `git diff --check` đạt.

**Commit:** `8230782` (`feat: add org chart and profile change approvals`) trên `chore/django-5.2-upgrade`.

**Còn mở:** checklist onboarding/offboarding là hạng mục tiếp theo. HR cần rà soát whitelist (hiện ba trường có sẵn trên Employee) và nội dung/chủ sở hữu checklist; báo cáo tuân thủ sẽ chỉ có stub kỹ thuật fail-closed, chưa tạo báo cáo theo chỉ đạo.
## 2026-09-26 — Checklist onboarding/offboarding (hạng mục 2)

**Mục tiêu/phạm vi:** tạo checklist theo mẫu cho tiếp nhận/nghỉ việc bằng thao tác tường minh của HR; gán đầu việc theo vai trò, cập nhật hoàn tất/bỏ qua có lý do, nhắc các mục quá hạn và đưa số cảnh báo lên trang chủ. Không tự mở checklist khi hồ sơ nhân viên được tạo/lưu.

**Tệp/phân hệ:** app mới `apps/lifecycle` (4 model, service, views, admin, templates, command `send_lifecycle_reminders`, migration); tích hợp quyền, menu, dashboard và URL portal.

**Đã làm:** mẫu được chụp thành các dòng checklist độc lập để sửa mẫu không làm đổi case cũ; khóa `triggering_event_ref` chống mở trùng; chỉ người được giao hoặc HR cập nhật; người khác không xem case; liên kết lịch sử cấp phát/thu hồi AssetAllocation có sẵn, không sửa/xóa lịch sử. Nhắc hạn tạo thông báo trong ứng dụng và chống gửi trùng trong cùng ngày. Template checklist được HR/SysAdmin cấu hình qua Django Admin; HR mở hồ sơ qua menu Nhân sự. Backup trước giai đoạn: `D:\QLHCNS-Backup-before-feature2-20260926-103045`.

**Kiểm tra:** SQL Server test database: `manage.py test apps.lifecycle.tests apps.portal.tests apps.hrm.tests --verbosity 1` — 19/19 pass; test database bị Django xóa sau chạy. `manage.py check` đạt; `makemigrations --check --dry-run` không còn thay đổi chưa migration.

**Vận hành:** cần áp dụng migration `lifecycle.0001_initial` khi triển khai. Task Scheduler chưa được cấu hình theo quyết định ưu tiên trước đây; quản trị viên có thể gọi `python src\manage.py send_lifecycle_reminders` thủ công, và cần lên lịch hằng ngày khi sẵn sàng.

**Commit:** `0558999` (`feat: add onboarding and offboarding checklists`) trên `chore/django-5.2-upgrade`.

**Còn mở:** HR cần tạo/xác nhận hai bộ checklist chuẩn, vai trò chịu trách nhiệm, ngày hạn cho từng mục; đây là cấu hình nghiệp vụ chưa được cung cấp nên chưa seed dữ liệu mặc định. Tiếp theo là khung báo cáo tuân thủ fail-closed, không xuất file/báo cáo.
## 2026-09-26 — Khung kỹ thuật báo cáo tuân thủ (hạng mục 3)

**Mục tiêu/phạm vi:** chuẩn bị điểm mở rộng cho báo cáo BHXH, quyết toán PIT và chi phí lương theo phòng ban theo chỉ đạo “chỉ làm khung kỹ thuật, chưa xuất báo cáo”.

**Tệp/phân hệ:** `apps/reporting/services.py`, `apps/reporting/tests.py`, `apps/security/permissions.py`.

**Đã làm:** thêm exception `ComplianceReportNotConfigured`, ba hàm placeholder đều dừng rõ ràng cho đến khi Kế toán xác nhận biểu mẫu/mapping/quy tắc phân bổ, và khai báo quyền dự kiến `export_compliance_report`. Không thêm endpoint, không tính số liệu, không sinh hoặc lưu file, không migration. Backup trước giai đoạn: `D:\QLHCNS-Backup-before-feature3-20260926-103639`.

**Kiểm tra:** bộ test tích hợp trên SQL Server test database: 57/57 pass; gồm notification, portal, activity, HRM, lifecycle và reporting. Django tự xóa test database. `manage.py check` đạt; `makemigrations --check --dry-run` báo không có thay đổi; `git diff --check` đạt.

**Còn mở:** Kế toán cung cấp mẫu BHXH đúng phiên bản, mẫu PIT theo năm và quy tắc phân bổ chi phí theo phòng ban. Sau khi có xác nhận, mới xây mapping, endpoint có phân quyền/audit snapshot và bộ đối chiếu số liệu; hiện chưa có báo cáo nghiệp vụ để sử dụng.

**Commit:** `828506e` (`chore: scaffold compliance reports behind finance gate`) trên `chore/django-5.2-upgrade`.
## 2026-09-26 — Kết quả hồi quy toàn bộ sau 4 hạng mục

**Phát hiện và sửa:** test quyền cũ giả định nhân viên thường không được cấp bất kỳ quyền nào. Cập nhật kiểm thử để cho phép đúng hai quyền tự phục vụ mới (`submit_profile_change_request`, `view_own_lifecycle_items`) và vẫn xác nhận nhân viên không có quyền duyệt yêu cầu hoặc quản lý checklist.

**Kiểm tra cuối:** trên SQL Server test database, `manage.py test apps.asset.tests apps.common.tests apps.hrm.tests apps.leave.tests apps.payroll.tests apps.security.tests apps.activity.tests apps.portal.tests apps.m365.tests apps.notification.tests apps.lifecycle.tests apps.reporting.tests --verbosity 1` — 140/140 pass. Test database tự được xóa. `manage.py check` đạt; `makemigrations --check --dry-run` báo không thay đổi; `git diff --check` đạt. Cảnh báo `RequestsDependencyWarning` vẫn hiện trong môi trường nhưng test thành công.

**Ghi chú:** thay đổi test activity hiện hữu của chủ dự án (`src/apps/activity/tests.py`) và các mục chưa theo dõi khác vẫn được giữ nguyên, không đưa vào các commit triển khai.

## 2026-09-26 — Cập nhật cẩm nang sử dụng và giáo án tập huấn

**Mục tiêu/phạm vi:** cập nhật tài liệu người dùng sau bốn hạng mục HRMS mới, phân biệt rõ chức năng đã triển khai với phần còn chờ cấu hình hoặc xác nhận nghiệp vụ.

**Tệp:** `HUONG_DAN_SU_DUNG_IHRMS.md`, `TAP_HUAN_IHRMS.md`.

**Đã cập nhật:** cẩm nang có hướng dẫn yêu cầu đổi hồ sơ, sơ đồ tổ chức, duyệt yêu cầu, bản nháp Outlook gửi thủ công, mở/giao/theo dõi checklist và điều kiện vận hành nhắc hạn; ghi rõ báo cáo BHXH/PIT/chi phí phòng ban chưa xuất được. Giáo án có bài thực hành theo vai trò cho hồ sơ cá nhân/sơ đồ, checklist và quy trình xác nhận email; thêm nội dung chuẩn bị mẫu, bảo vệ dữ liệu demo và các phần chưa bật. Tài liệu yêu cầu HR thống nhất mẫu checklist trước khi cấu hình và dùng nghiệp vụ.

**Kiểm tra:** rà soát văn bản UTF-8 và `git diff --check`; không thay đổi code/schema nên không chạy test ứng dụng.

**Commit:** chưa commit trong lượt cập nhật tài liệu này.

**Còn mở:** HR cần hoàn thiện mẫu checklist và whitelist chính thức; Kế toán cần xác nhận mẫu/qui tắc báo cáo; IT quyết định cấu hình Task Scheduler. Hướng dẫn chỉ mô tả phần mềm và không thay thế SOP được công ty phê duyệt.

## 2026-09-26 — Sửa lỗi Unicode khi output management command bị redirect

**Lỗi/nguyên nhân:** khi một lệnh Django chạy trên Windows mà stdout/stderr bị chuyển hướng khỏi console thật, Python có thể dùng code page hệ thống như cp1252. Ký tự tiếng Việt không mã hóa được sẽ làm command dừng với `UnicodeEncodeError`.

**Đã sửa:** `src/manage.py` cấu hình stdout và stderr sang UTF-8 với `errors='replace'` trước khi Django khởi chạy, áp dụng chung cho mọi management command đi qua tệp này. `ops/scheduler/Run-ActivityReportReminders.ps1` cũng đặt `PYTHONIOENCODING=utf-8` và `PYTHONUTF8=1`, nhất quán với script nhắc lifecycle hiện có. Rà `src/config/wsgi.py` và `src/config/asgi.py`: không có lệnh in log trực tiếp ra stdout/stderr nên không cần chỉnh ở đó.

**Kiểm tra:** thử redirect với `PYTHONIOENCODING=cp1252`, rồi chạy `venv\Scripts\python.exe src\manage.py shell -c "print(...)"` và xác nhận tệp UTF-8 chứa đúng chuỗi tiếng Việt — đạt, không có `UnicodeEncodeError`. `python -m py_compile src/manage.py` và `git diff --check` đạt. Lệnh tổng quát `venv\Scripts\python.exe src\manage.py test` tự tìm thấy 0 test trong cấu trúc `src/apps`; đã chạy toàn bộ 23 module test tường minh — 148/148 pass, test database được xóa. Cảnh báo `RequestsDependencyWarning` vẫn xuất hiện nhưng không làm test thất bại.

**Commit:** chưa commit trong lượt sửa này.

**Còn mở:** không còn thay đổi code đã biết; Task Scheduler production cần chạy script đã cập nhật khi triển khai bản mới.

## 2026-09-26 — Làm rõ checklist, sơ đồ tổ chức và menu giao việc

**Mục tiêu:** phân định trải nghiệm checklist giữa HR và nhân viên; làm sơ đồ tổ chức dễ đọc/tìm kiếm; giúp người dùng thấy rõ lối vào giao việc và cập nhật hoàn tất.

**Đã thực hiện:** checklist được ghi rõ là HR mở/quản lý hồ sơ onboarding/offboarding, còn nhân viên và người thuộc các vai trò dự án chỉ xem/cập nhật phần việc được giao. Bổ sung quyền xem checklist cá nhân cho Director, Project Manager, Project Coordinator và CBDA; quyền quản lý toàn bộ vẫn riêng cho HR. Sơ đồ tổ chức hiển thị số nhân viên/phòng ban, chức vụ, phòng ban, quản lý trực tiếp, số báo cáo trực tiếp; có tìm kiếm theo tên/chức vụ/phòng ban và giữ hiển thị nhánh cha phù hợp. Đưa liên kết tác vụ ra menu **Kế hoạch** với nhãn **Giao việc & hoàn tất**.

**Backup trước thay đổi:** `D:\QLHCNS-Backup-before-orgchart-checklist-menu-20260926-181546`.

**Kiểm tra:** `venv\Scripts\python.exe src\manage.py test apps.security.tests apps.lifecycle.tests apps.portal.tests --verbosity 1` — 33 test pass trên SQL Server test database; `manage.py check` đạt; `makemigrations --check --dry-run` không có thay đổi; `git diff --check` đạt. Không phát sinh migration.

**Còn mở:** kiểm tra trực quan sơ đồ trên trình duyệt với tài khoản thật và xác nhận HR/CBDA thấy đúng nhãn menu sau khi triển khai.

## 2026-09-26 — Phân định checklist HCNS, menu hoạt động dự án và sơ đồ tổ chức

**Mục tiêu:** làm rõ checklist nhân sự là thủ tục nội bộ của HCNS; bỏ menu trùng; đưa công việc dự án về đúng nhóm; sửa thao tác hồ sơ nhân viên và giúp sơ đồ vừa màn hình.

**Đã thực hiện:** checklist đổi tên thành “Checklist thủ tục nhân sự”, mô tả rõ phạm vi giấy tờ/tiếp nhận/nghỉ việc; menu chỉ còn trong **Nhân sự**. Quyền truy cập và giao đầu việc bị giới hạn vào vai trò `HR_OFFICER`/`HR_MANAGER`; người dùng dự án/nhân viên thường không thể mở checklist dù biết URL. Menu **Giao việc & hoàn tất** được đặt trong nhóm **Hoạt động dự án**. Nút **Thao tác** trong danh sách hồ sơ dùng HTML `<details>/<summary>` thay vì gọi hàm JavaScript không tồn tại; các mục liên kết tới đúng phần Điều chuyển/Bổ nhiệm/Lương/Hợp đồng/Sửa hồ sơ. Sơ đồ tổ chức dùng chiều rộng lớn hơn, tự thu để vừa chiều ngang cửa sổ và có nút thu/phóng cùng “Vừa màn hình”. Hướng dẫn sử dụng và hướng dẫn test nhanh đã đồng bộ vị trí menu và ranh giới giữa checklist HCNS với task dự án.

**Backup trước thay đổi:** `D:\QLHCNS-Backup-before-clarify-HR-checklist-menu-orgchart-20260926-183154`.

**Kiểm tra:** `venv\Scripts\python.exe src\manage.py test apps.security.tests apps.lifecycle.tests apps.portal.tests --verbosity 1` — 36/36 test pass trên SQL Server test database; database kiểm thử được Django xóa sau chạy. `manage.py check` đạt; `makemigrations --check --dry-run` không có thay đổi; `git diff --check` đạt. Có cảnh báo dependency Requests/urllib3 đã tồn tại trong môi trường nhưng không làm test thất bại.

**Còn mở:** cần đăng nhập bằng tài khoản HCNS và CBDA trên trình duyệt để xác nhận menu theo vai trò; nếu muốn dùng test SQL Server mới nhất, khởi động lại server ứng dụng để nạp template/CSS cập nhật.

## 2026-09-26 — Sửa danh sách giao việc dự án và lỗi mở form sửa nhân viên

**Mục tiêu:** giải thích và hiển thị đúng Task báo cáo hoạt động cho CBDA/Điều phối viên/Quản lý dự án; sửa lỗi `VariableDoesNotExist` khi vào Sửa hồ sơ.

**Đã thực hiện:** danh sách Task dự án nay bao gồm task giao cho người dùng và các task gắn với hoạt động trong phạm vi họ được xem; CBDA chỉ thấy hoạt động của mình, Điều phối viên/Quản lý dự án thấy phạm vi được phép. Trang cho biết task tự tạo khi liên kết công văn đi, người giao là Điều phối viên (hoặc người ký nếu hồ sơ thiếu Điều phối viên), người nhận là CBDA phụ trách chính, hạn 10 ngày làm việc; CBDA cần tải báo cáo SharePoint trước khi hoàn thành. Form nhân viên luôn nhận đầy đủ các khóa dữ liệu khởi tạo kể cả khi sửa hồ sơ; bổ sung test GET trang sửa. Cẩm nang và hướng dẫn test nhanh đã chỉ rõ người giao và điều kiện task xuất hiện.

**Backup trước thay đổi:** `D:\QLHCNS-Backup-before-task-visibility-edit-form-fix-20260926-191000`.

**Kiểm tra:** `venv\Scripts\python.exe src\manage.py test apps.portal.tests apps.activity.tests --verbosity 1` — 38/38 test pass trên SQL Server test database; test database được Django xóa sau chạy. `manage.py check` đạt; `makemigrations --check --dry-run` không có thay đổi; `py_compile` và `git diff --check` đạt.

**Còn mở:** không cần thao tác giao Task báo cáo bằng tay. Để xác nhận trên dữ liệu thật, cần một hoạt động có CBDA phụ trách và công văn đi được liên kết; khi đó Task sẽ hiện cho CBDA và nhóm quản lý dự án.

## 2026-09-26 — Sửa ngày bắt đầu và hoàn thành của Giao việc

**Vấn đề:** Task trước đây lưu ngày bắt đầu và hạn hoàn thành nhưng không có ngày hoàn thành thực tế; giao việc và đánh dấu hoàn thành cùng ngày khiến giao diện không thể hiện rõ ba mốc thời gian.

**Đã sửa:** ngày bắt đầu mặc định là ngày tạo Task; khi chuyển trạng thái sang Hoàn thành, hệ thống ghi ngày hiện tại vào `CompletedDate`, và xóa ngày này nếu Task được chuyển lại trạng thái chưa hoàn thành. Danh sách và chi tiết Task hiển thị riêng ngày bắt đầu, hạn và ngày hoàn thành theo định dạng ngày/tháng/năm. Thêm migration `task.0003_task_completed_date`; Task đã hoàn thành trước migration được điền ngày gần đúng từ thời điểm sửa cuối cùng.

**Sao lưu:** `D:\QLHCNS-Backup-before-task-completion-date-20260926-192500` (tạo trước khi sửa mã).

**Kiểm tra:** migration đã áp dụng trên SQL Server (`task.0003_task_completed_date` đã được đánh dấu áp dụng); `manage.py check` đạt; `makemigrations --check --dry-run` không phát hiện thay đổi thiếu migration; 40 test của `apps.portal.tests` và `apps.activity.tests` đạt; `git diff --check` sạch. Có cảnh báo dependency Requests/urllib3 hiện hữu trong môi trường chạy test.

**Lưu ý dữ liệu cũ:** ngày hoàn thành của Task cũ là ước tính từ lần cập nhật cuối, không nhất thiết là ngày người dùng thực sự bấm Hoàn thành. Task mới ghi nhận ngày thực tế khi chuyển trạng thái.

## 2026-09-26 — Đồng bộ hạn Task theo lịch hoạt động

**Quy tắc được người dùng xác nhận:** Công văn đi đã phát hành kích hoạt việc giao Task; ngày bắt đầu Task bằng ngày bắt đầu hoạt động, hạn là 10 ngày làm việc sau ngày kết thúc hoạt động. Khi lịch đổi, cập nhật Task hiện có thay vì tạo bản trùng.

**Đã sửa:** `create_task_for_activity` tạo và đồng bộ ngày Task theo lịch hoạt động; nếu lịch đổi, thông báo trong IHRMS tới CBDA và người giao. Task đã đánh dấu hoàn thành trước ngày kết thúc mới được mở lại, xóa ngày hoàn thành và bỏ liên kết tệp báo cáo cũ nhưng không xóa tệp khỏi SharePoint. Không cho hoàn thành Task báo cáo trước ngày kết thúc hoạt động. Cập nhật hướng dẫn giao việc, form và roadmap.

**Dữ liệu kiểm thử đã đồng bộ:** hoạt động 01/10–31/10/2026 có Task bắt đầu 01/10, hạn 13/11/2026 theo lịch ngày làm việc trong DB, trạng thái Todo. Task hoàn thành sớm ngày 26/09 được mở lại; liên kết báo cáo cũ được gỡ, tệp vật lý vẫn giữ trên SharePoint.

**Sao lưu trước sửa:** `D:\QLHCNS-Backup-before-activity-task-date-policy-20260926-201500`.

**Kiểm tra:** 42 test của `apps.activity.tests` và `apps.portal.tests` đạt; `manage.py check` đạt; `makemigrations --check --dry-run` không phát hiện thay đổi schema. `git diff --check` sạch. Cảnh báo RequestsDependencyWarning hiện hữu vẫn xuất hiện khi chạy Python.

## 2026-09-27 — Chỉnh bố cục Bảng chấm công và bản in

**Phạm vi:** `src/apps/portal/templates/portal/timesheet_month.html`.

**Đã sửa:** năm ô nhập ngày nghỉ có cùng chiều rộng 4rem, nằm sát nhãn và giữ nguyên khi in; dòng giờ chuẩn gộp thành một ô, in công thức và kết quả `= 168h` (tự bỏ số thập phân .00); bỏ nhãn `(Ký, họ tên)` nhưng giữ khoảng trống ký và tên người ký. Bản in được định dạng A4, giữ hai cột tóm tắt/chữ ký như bố cục trang và ẩn điều khiển màn hình.

**Sao lưu trước sửa:** `D:\QLHCNS-Backup-before-timesheet-layout-20260927-093000`.

**Kiểm tra:** `manage.py check` đạt; render template với mẫu 21 ngày × 8 giờ xác nhận kết quả `= 168h` và không còn `(Ký, họ tên)`; `git diff --check` sạch. Không sửa schema/database.


## 2026-09-27 - Timesheet print refinements

**Changes:** Made the complete required-hours row bold, including the calculation and = 168h; formatted required days and hours to one decimal place; kept all five leave labels on a single line in print mode.

**Backup before edits:** D:\QLHCNS-Backup-before-timesheet-print-tweaks-20260927-085753.

**Checks:** Django system check passed; template render confirmed the full bold formula 21,0 ngay x 8,0h = 168h, all five leave rows, and no-wrap print CSS; git diff --check passed. No database changes. The existing Requests/urllib3 dependency warning remains.

## 2026-09-27 — Sửa lỗi quyền xem Task và phòng ban ngừng hoạt động

**Phạm vi:** `src/apps/portal/views.py`, `src/apps/portal/tests.py`, `src/apps/portal/templates/portal/task_list.html`, `src/apps/portal/templates/portal/hr_employee_form.html`.

**Nguyên nhân và cách sửa:** danh sách Task trước đây chỉ có phạm vi “được giao cho tôi”; trang chi tiết Task không nhận diện người giao ở các Task không gắn hoạt động. Thêm lọc `?scope=assigned_by_me` và hai tab “Việc của tôi” / “Việc tôi đã giao” (tab giao việc chỉ hiện khi tài khoản có quyền `assign_task`). Người giao được xem đúng Task do họ giao; không cấp quyền xem Task của người khác. Với Task thuộc hoạt động, quyền xem hoạt động hiện có vẫn được giữ.

Form sửa nhân viên trước đây chỉ nạp phòng ban đang hoạt động. Khi phòng ban hiện tại đã ngừng hoạt động, trình duyệt có thể tự chọn phòng ban hoạt động đầu tiên và làm thay đổi dữ liệu khi HR chỉ định sửa trường khác. Form giờ vẫn nạp và chọn sẵn phòng ban hiện tại, đồng thời hiển thị cảnh báo để HR chủ động điều chuyển nếu cần. Rà soát các bộ lọc phòng ban còn lại: form tạo nhân viên và công văn là tạo mới; form hồ sơ nhân viên dùng danh sách phòng ban cho điểm đến điều chuyển, nên không phải cùng trường hợp sửa giá trị hiện tại.

**Kiểm tra:** thêm test lọc tab Task, quyền xem của người giao và chặn nhân viên không liên quan; thêm `test_edit_employee_with_deactivated_department_keeps_department_unless_explicitly_changed` xác nhận GET hiển thị phòng ban cũ được chọn và POST chỉ đổi điện thoại vẫn giữ nguyên phòng ban. Chạy `python src/manage.py test apps.portal.tests apps.hrm.tests apps.task.tests` trên backend SQL Server với test database cô lập: 23/23 đạt; test database được Django xóa sau khi chạy. `manage.py check` đạt; `makemigrations --check --dry-run` không có thay đổi; `git diff --check` sạch. Không sửa schema và không cập nhật database thật. Cảnh báo Requests/urllib3 hiện hữu vẫn xuất hiện.

**Sao lưu:** checkpoint được cung cấp: `D:\QLHCNS-Backup-before-task-visibility-edit-form-fix-20260926-191000`; bản sao mã nguồn hiện trạng ngay trước sửa: `D:\QLHCNS-Backup-current-before-task-visibility-edit-form-fix-20260927-090538`.

**Commit:** `9ef726f` trên nhánh `chore/django-5.2-upgrade`; chưa push.

## 2026-09-27 - Hiện đủ phạm vi giao việc và dùng đúng lịch hoạt động

**Phạm vi:** `src/apps/portal/` và `src/apps/activity/`; hướng dẫn sử dụng, test nhanh, roadmap MEL.

**Đã sửa:** Trang công việc hiển thị hai tab **Việc của tôi** và **Việc tôi đã giao** cho người có quyền xem Dashboard hoạt động dự án hoặc quyền giao việc. Quyền tạo/giao Task mới vẫn giữ nguyên, không được cấp thêm theo việc hiển thị tab. Nội dung hướng dẫn trên trang và form hoạt động đã làm rõ: ngày công văn chỉ kích hoạt việc tạo/giao Task; ĐPV/quản lý tự nhập ngày bắt đầu, ngày kết thúc; hạn báo cáo là 10 ngày làm việc sau ngày kết thúc, bỏ Thứ Bảy, Chủ Nhật và ngày nghỉ đã khai báo. Thuật toán hiện có đã theo quy tắc này; bổ sung kiểm thử để ngăn ngày phát hành công văn bị dùng làm mốc lịch.

**Đối chiếu dữ liệu thật chỉ đọc:** ACT-1 đang có lịch 26/09–27/09/2026 nhưng Task cũ giữ 18/06–02/07 và đã Hoàn thành; đồng bộ sẽ mở lại Task, bỏ ngày hoàn thành và gỡ liên kết tệp báo cáo khỏi Task (tệp vật lý SharePoint không bị xóa). ACT-2 có lịch 19/09–20/09 nhưng Task cũ cũng giữ ngày tháng 6–7; ACT-3 có lịch 01/10–31/10 và Task hiện đã đúng 01/10–13/11. Không tự cập nhật các bản ghi thật trong lượt này để tránh thay đổi trạng thái nghiệp vụ và liên kết báo cáo ngoài ý muốn.

**Sao lưu trước thay đổi:** `D:\QLHCNS-Backup-before-project-task-tab-and-date-clarification-20260927-091906`.

**Kiểm tra:** `venv\Scripts\python.exe src\manage.py test apps.portal.tests apps.activity.tests` — 46/46 test đạt trên SQL Server test database; Django system check đạt; `makemigrations --check --dry-run` không phát hiện migration thiếu; `git diff --check` đạt. Cảnh báo Requests/urllib3 hiện hữu vẫn xuất hiện khi chạy Python.

**Còn mở:** Cần người phụ trách xác nhận có muốn đồng bộ ACT-1 và ACT-2 trên dữ liệu thật. ACT-1 sẽ bị mở lại và cần tải/đính kèm báo cáo lại trong IHRMS; tệp đang có trên SharePoint vẫn giữ nguyên. Không cần đồng bộ ACT-3.

**Commit triển khai:** `a9cd9ed` trên nhánh `chore/django-5.2-upgrade`; chưa push.

## 2026-09-27 - Tách danh sách giám sát khỏi việc cá nhân

**Nguyên nhân:** Bộ lọc `assigned_to_me` cộng thêm mọi Task trong hoạt động mà người dùng có quyền giám sát. Do đó Ban Giám đốc thấy Task giao cho CBDA dưới tab **Việc của tôi**, dù họ không phải người nhận việc.

**Đã sửa:** Tài khoản có quyền giám sát vào mặc định tab **Theo dõi hoạt động**, liệt kê Task trong phạm vi dự án được phép xem. **Việc của tôi** chỉ lọc `assigned_to_employee` của người đăng nhập; **Việc tôi đã giao** chỉ lọc `assigned_by_employee` của người đăng nhập. Thêm kiểm thử hồi quy với Giám đốc, Điều phối viên và CBDA; cập nhật hướng dẫn sử dụng/test nhanh.

**Sao lưu trước sửa:** `D:\QLHCNS-Backup-before-task-scope-separation-files-20260927-093000`.

**Kiểm tra:** `venv\Scripts\python.exe src\manage.py test apps.portal.tests apps.activity.tests` — 47/47 test đạt trên SQL Server test database; Django system check đạt; không có migration thiếu; `git diff --check` đạt. Không thay đổi dữ liệu thật.

**Commit triển khai:** `6917ed3` trên nhánh `chore/django-5.2-upgrade`; chưa push.

## 2026-09-27 - Bổ sung test vai trò giao việc và giới hạn trưởng phòng

**Yêu cầu đã thực hiện:** Bổ sung test cho DEPT_MANAGER, HR_MANAGER, PROJECT_MANAGER và EMPLOYEE; đồng thời xử lý câu hỏi nghiệp vụ về quyền xem Task không thuộc hoạt động dự án.

**Quyết định nghiệp vụ do người dùng xác nhận:** DEPT_MANAGER chỉ được xem Task của nhân viên thuộc các phòng ban mình quản lý. Task gắn hoạt động dự án vẫn tuân theo quyền xem hoạt động hiện có.

**Đã sửa/test:** DEPT_MANAGER giao Task cho nhân viên trong phòng mình, thấy Task ở **Việc tôi đã giao** và mở được chi tiết; yêu cầu POST giả mạo người nhận ở phòng khác bị chặn, và trưởng phòng không xem được chi tiết Task ngoài phạm vi. HR_MANAGER vẫn giao/xem Task liên phòng. PROJECT_MANAGER có các tab/phạm vi giám sát đúng; EMPLOYEE thường chỉ thấy Task giao cho mình, không thấy tab giao/giám sát, nút tạo Task hay cột dự án. Đã áp dụng kiểm tra phòng ban ở phía máy chủ khi tạo Task, không chỉ lọc lựa chọn trong giao diện.

**Sao lưu:** `D:\QLHCNS-Backup-before-task-role-regression-tests-20260927-094500`.

**Kiểm tra:** `venv\Scripts\python.exe src\manage.py test apps.portal.tests` — 21/21 test đạt trên SQL Server test database; `manage.py check` đạt; `makemigrations --check --dry-run` không phát hiện migration thiếu; `git diff --check` đạt. Cảnh báo Requests/urllib3 hiện hữu; một lần POST ngoài phòng bị từ chối có log bảo mật như mong đợi.

**Còn mở:** Không còn câu hỏi về phạm vi quyền trưởng phòng; quyết định giới hạn theo các phòng ban được quản lý đã được áp dụng.

**Commit triển khai:** `875ab08` trên nhánh `chore/django-5.2-upgrade`; chưa push.

## 2026-09-27 - Kiểm tra và đóng gói trước khi đẩy GitHub

**Phạm vi chuẩn bị:** các thay đổi đang có trong workspace gồm test hồi quy chấm công, xử lý UTF-8 cho output Windows/Task Scheduler, cập nhật giáo án, hướng dẫn IT và bộ tài liệu đặc tả/UAT/checklist. Các file dự án được rà soát và đưa vào commit; không đưa thư mục sao lưu SQL Server, `Backups/backup-log.txt`, tệp rỗng cục bộ `src/qlhcns` hay `.env` lên Git.

**Điểm nghiệp vụ còn chờ:** bản yêu cầu Task cập nhật có thêm câu hỏi DEPT_MANAGER mặc định vào **Theo dõi hoạt động** hay **Việc của tôi**. Đã gửi câu hỏi cho người phụ trách; giữ nguyên hành vi hiện tại và chưa thêm test/quy tắc mặc định mới cho đến khi có câu trả lời.

**Kiểm tra trước đẩy:** lệnh tổng quát `manage.py test` tự tìm thấy 0 test do cấu trúc module nằm dưới `src/apps`; đã chạy tường minh 23 module test — 172/172 pass trên SQL Server test database, DB test được Django xóa. `manage.py check` đạt; `makemigrations --check --dry-run` không phát hiện migration thiếu; `git diff --check` đạt. Cảnh báo Requests/urllib3 vẫn hiện hữu nhưng không làm test thất bại.

**Commit và push:** commit `2a0ef19` (`chore: package tests and operational documentation`) chứa 11 tệp mã nguồn/tài liệu đã rà soát. Đã đẩy nhánh `chore/django-5.2-upgrade` lên `origin` thành công, cập nhật từ `4610ec5` đến `2a0ef19`; gồm 22 commit đã có trên nhánh và commit đóng gói mới. Thư mục sao lưu SQL Server và tệp rỗng `src/qlhcns` tiếp tục chỉ ở máy cục bộ.

## 2026-09-27 - Giới hạn quyền xem và quản lý tài sản

**Yêu cầu:** Chỉ HR, Kế toán, Điều phối viên dự án và Ban Giám đốc được xem phần Tài sản; CBDA, trưởng phòng và nhân viên khác không cần dùng phân hệ này.

**Đã triển khai:** Thêm quyền `view_asset` riêng cho `DIRECTOR`, `HR_MANAGER`, `HR_OFFICER`, `FINANCE_OFFICER`, `PROJECT_COORDINATOR` và quản trị hệ thống. HR/quản trị hệ thống giữ quyền quản lý; Kế toán, ĐPV và Giám đốc có quyền chỉ đọc, còn quyền duyệt thanh lý của Giám đốc tiếp tục theo kiểm tra hiện hành. Ẩn các mục Tài sản trong menu Cá nhân/Hành chính và số liệu tài sản trên dashboard đối với vai trò ngoài danh sách; chặn URL trực tiếp; ẩn biểu mẫu và chặn POST chỉnh sửa với người chỉ có quyền xem. Mở quyền đọc tương ứng trong Django Admin, cập nhật ma trận RBAC và thêm test vai trò/truy cập.

**Sao lưu trước sửa:** `Backups/source-before-asset-access-20260927.zip` (snapshot các tệp liên quan từ HEAD; chỉ lưu cục bộ, không đưa vào Git).

**Kiểm tra:** `venv\Scripts\python.exe src\manage.py test apps.security.tests apps.portal.tests apps.asset.tests` — 49/49 test đạt trên SQL Server test database; `manage.py check` đạt; `makemigrations --check --dry-run` báo không có migration mới; `git diff --check` đạt. Không chạy migration hay thay đổi dữ liệu ứng dụng.

**Cảnh báo còn hiện:** `RequestsDependencyWarning` về phiên bản urllib3; không ảnh hưởng kết quả kiểm thử.

**Commit triển khai:** `8e6db7b` (`feat: restrict asset access by role`) trên `chore/django-5.2-upgrade`; đã commit cục bộ, chưa push.


## 2026-09-27 - Rà soát và chuẩn bị đưa IHRMS lên máy chủ chạy thử

**Yêu cầu/phạm vi:** Rà soát mã nguồn, cấu hình, README, tài liệu vận hành, skills và tệp dư; chuẩn bị hồ sơ triển khai SIT trên Windows/SQL Server. Đây là chuẩn bị chạy thử, không triển khai production.

**Sao lưu đầy đủ trước khi sửa/xóa:** `D:\\QLHCNS-FullBackup-before-server-trial-20260927`. Đã sao chép toàn bộ dự án, gồm cả `.env`, Git, venv, Backups, Logs và dữ liệu cục bộ. Robocopy: 11.057 tệp, 120.039.816 byte, 0 lỗi và 0 sai khác. Bản sao chứa secrets/dữ liệu máy local; chỉ lưu nội bộ, không đưa lên Git.

**Đã rà soát/cập nhật:** README viết lại theo cấu trúc thật `src/`, trạng thái module/tích hợp và cảnh báo rõ `runserver` chỉ dùng phát triển; thêm [runbook Server Trial](Server_Trial_Readiness_2026-09-27.md) có điều kiện IT cần cấp, lệnh Windows, test, backup/restore và giới hạn SIT; chuyển trạng thái tài liệu triển khai thành “reference baseline”, không còn khẳng định máy chủ đã được phê duyệt. Mẫu `.env.example` mặc định `DEBUG=False`, thêm cấu hình CSRF/HSTS cho proxy và dùng tên DB mẫu `ihrms_sit` để tránh trỏ nhầm DB production. `settings.py` bổ sung parse host/origin, HSTS cấu hình theo môi trường và `STATIC_ROOT`. Ghim Waitress 3.0.2 cho WSGI Windows và chardet 5.2.0 để hết RequestsDependencyWarning; thêm `Backups/` và `Logs/` vào Git ignore.

**Đã dọn:** Xóa snapshot cây thư mục sinh tự động `source_tree.txt` (không có liên kết tham chiếu) và tệp rỗng 0 byte `src/qlhcns`. Giữ nguyên `.env`, SQL backup, Logs, tài liệu nghiệp vụ/lịch sử và skills vì chứa cấu hình hoặc hồ sơ cần quản lý.

**Kiểm tra:** 177 test trên SQL Server test database tạm đạt; Django test runner đã tạo rồi xóa test DB. `manage.py check`, `makemigrations --check --dry-run`, `pip check` và `git diff --check` đạt. `collectstatic --noinput` gom 219 tệp; có cảnh báo hai JavaScript trùng tên giữa Jazzmin và Django, `findstatic` cho thấy bản Jazzmin được ưu tiên. Waitress lắng nghe loopback `127.0.0.1:8001`; GET `/portal/` trả HTTP 200. `check --deploy` trên cấu hình local có 5 cảnh báo do local chưa bật TLS/key an toàn; thử cấu hình SIT tạm với DEBUG tắt, key mới và HTTPS proxy bật chỉ còn cảnh báo HSTS (cố ý để 0 tới khi IT xác nhận domain/subdomain). Test và smoke test không thay đổi DB nghiệp vụ hay SharePoint thật.

**Còn cần IT/chủ dự án:** Cấp Windows Server SIT, SQL database/tài khoản SIT riêng, hostname/chứng chỉ TLS, cấu hình reverse proxy và static mapping, Graph/SharePoint folder cùng ACL thử nghiệm, tài khoản vai trò và người phụ trách restore. Chạy lại test/check trên máy đích và ký UAT trước khi xem xét go-live. Windows Task Scheduler cho nhắc hạn vẫn chưa triển khai theo ưu tiên đã thống nhất.

**Commit:** `c12eae7` (`chore: prepare Windows server trial deployment`) on `chore/django-5.2-upgrade`; local commit, not pushed.

## 2026-09-27 - Bổ sung kiểm thử theo review (Yêu cầu 1 và 2)

**Phạm vi:** Đọc `Ket_Qua_Review_va_Yeu_Cau_Codex_2026-09-27.md` và chỉ thực hiện hai yêu cầu đầu: bổ sung kiểm thử cho 10 app chưa có test và viết kiểm thử hồi quy cho I3–I8, I11. Theo yêu cầu trong tài liệu, khi test phơi bày lỗi nghiệp vụ thì ghi nhận để báo lại, không tự ý sửa logic, đặc biệt với chính sách lương. Không sửa mã nghiệp vụ, schema hoặc migration.

**Sao lưu trước thay đổi:** Git bundle `D:\QLHCNS-Backup-before-review-regression-tests-20260927-174456.bundle`; đã xác minh bundle đọc được bằng `git bundle verify`.

**Đã bổ sung:** Thay các test placeholder trong `contract`, `document`, `kpi`, `office`, `organization`, `planning`, `procurement`, `project`, `recruitment`, `task`; thêm hồi quy liên quan trong `asset`, `leave`, `payroll`, `portal`. Tổng cộng 14 module test được cập nhật. Các kiểm thử bao quát ràng buộc dữ liệu, xác thực tệp, quyền truy cập/thao tác và các tình huống được đánh mã I3–I8, I11.

**Kết quả test trên SQL Server:** Chạy tường minh toàn bộ 23 module test của dự án bằng Django test runner; 224 test, 3 failures và 1 error. Database test cô lập được runner tạo rồi xóa. `manage.py check` không có lỗi; `makemigrations --check --dry-run` báo không có thay đổi; cú pháp 14 tệp Python được phân tích thành công; `git diff --check` đạt.

**Lỗi được test xác nhận, chưa sửa theo phạm vi đã thống nhất:**

- I3: giờ cuối tuần do nhân viên nhập vẫn được cộng nghỉ bù khi bảng công tháng còn Pending.
- I6: tạo kỳ lương bỏ nhân viên có ngày nghỉ việc nằm trong kỳ vì truy vấn hiện chỉ lấy nhân viên còn trạng thái Active. Cần xác nhận quy tắc nghiệp vụ lương trước khi đổi cách chọn người hoặc tính lương.
- Phân quyền hợp đồng: danh sách hợp đồng trả hợp đồng của nhân viên khác trong context cho tài khoản EMPLOYEE.
- Mua sắm: route danh sách gọi template `portal/procurement_request_list.html` nhưng template không tồn tại, làm trang lỗi khi truy cập.

**Các hồi quy đạt:** I4 chia yêu cầu nghỉ qua tháng/năm; I5 ngăn cấp trùng tài sản và không chuyển tài sản về sẵn sàng nếu còn lượt cấp đang hoạt động; I7 chọn mức lương theo ngày hiệu lực; I8 tạo/hiển thị Payslip khi chốt kỳ; I11 không cho hoàn tất kiểm kê khi còn dòng chưa đếm và không cho sửa dòng đã hoàn tất. Test các ràng buộc có giá trị phòng ban NULL của ngân sách cũng đạt trên SQL Server.

**Trạng thái:** Chỉ có thay đổi trong các tệp `tests.py`; chưa commit hoặc push. `docs/Huong_Dan_Setup_TaskScheduler_SIT_UAT.md` đang là tệp untracked có sẵn trong workspace, được giữ nguyên và không đưa vào phạm vi thay đổi này.

## 2026-09-27 - Xử lý I3, quyền xem hợp đồng và trang mua sắm

**Yêu cầu/diễn giải:** Nhân viên dự án cộng đồng làm việc thường xuyên vào Thứ Bảy, Chủ Nhật; giờ làm phải được ghi nhận, nhưng chỉ được quy đổi thành nghỉ bù khi bảng chấm công tháng được duyệt. I6 về lương giữa kỳ tiếp tục chờ xác nhận quy tắc nghiệp vụ.

**Sao lưu trước sửa:** `D:\QLHCNS-Backup-before-I3-contract-procurement-20260927-181613.bundle`; `git bundle verify` xác nhận bundle chứa lịch sử Git đầy đủ.

**Đã sửa:** `compensatory_days_earned()` chỉ lấy giờ từ những tháng có `MonthlyAttendanceSummary` ở trạng thái Approved. Giờ T7/CN/ngày lễ vẫn được tích lũy theo quy tắc tối đa 1 ngày cho mỗi ngày làm và làm tròn xuống nửa ngày; tháng Pending hoặc chưa có bản tổng hợp chưa được cộng vào quỹ nghỉ bù. Danh sách hợp đồng lao động trả HTTP 403 cho tài khoản không có quyền `manage_hr`; HR vẫn xem được danh sách. Tạo template `portal/procurement_request_list.html` để hiển thị danh sách theo quyền hiện có, form tạo đề nghị, thao tác duyệt/từ chối và đánh dấu đã mua.

**Kiểm thử:** Các test tập trung `apps.leave.tests`, `apps.contract.tests`, `apps.procurement.tests` đạt 44/44 trên SQL Server test database. Toàn bộ 23 module của bộ test SIT đạt 226/227; test duy nhất còn thất bại là I6 (nhân viên nghỉ việc giữa kỳ chưa được đưa vào kỳ lương), giữ nguyên để chờ xác nhận, không sửa logic lương. Test database tạm đã được Django tạo rồi xóa. `manage.py check`, `makemigrations --check --dry-run`, cú pháp Python và `git diff --check` đạt; không phát sinh migration.

**Phạm vi tệp:** Thay đổi logic nghỉ bù, chặn quyền danh sách hợp đồng, template mua sắm và test tương ứng. Không thay đổi cấu trúc database. Tệp untracked `docs/Huong_Dan_Setup_TaskScheduler_SIT_UAT.md` tiếp tục được giữ nguyên, không thuộc thay đổi này.

## 2026-09-27 - Sửa khẩn I6: tạo bảng lương cho người nghỉ giữa kỳ

**Mục tiêu/phạm vi:** Sửa lỗi I6 đã có trước đợt responsive/mobile/PWA, được test hồi quy phát hiện trong Yêu cầu 2. Nhân viên đã nghỉ nhưng `leave_date` nằm trong kỳ lương vẫn cần có dòng lương cho phần thời gian làm việc; không thay đổi công thức tính lương hoặc dashboard.

**Sao lưu trước sửa:** `D:\QLHCNS-Backup-before-I6-payroll-20260927.zip`, sao chép từ snapshot mã nguồn mới nhất trước thay đổi. SHA-256: `692ddb3b26e9cf8b1a540882ce2f693aad69ca604630f008c9abc70c02e97775`.

**Nguyên nhân và thay đổi:** Test I6 thất bại trước sửa trên SQL Server test database. Hai truy vấn riêng ở trang chạy lương và thao tác tạo dòng đều chỉ lấy `employment_status="Active"`, nên loại nhân viên đã nghỉ trong kỳ khỏi cả danh sách thiếu và quá trình tạo. Thêm `_employees_payable_for_period(period)` dùng chung: lấy nhân viên Active hoặc có `leave_date` trong khoảng bao gồm cả ngày đầu/cuối kỳ; dùng helper tại cả hai vị trí. Giữ nguyên loại trừ người đã nghỉ trước kỳ, bảo toàn nhánh Active có ngày nghỉ trong tương lai và bộ lọc dòng đã tồn tại để không tạo trùng. Không sửa `Payroll.calculate()`; phép tính tỷ lệ ngày công vốn đã có test riêng.

**Kiểm thử:** Test trước sửa tái hiện FAIL. Sau sửa, chạy rõ 23 module test của dự án bằng Django test runner trên SQL Server test database tạm: 230/230 đạt; database kiểm thử do runner tạo và xóa. Kiểm thử mới bao gồm nghỉ đúng ngày đầu/cuối kỳ, nghỉ trước kỳ, nhân viên Active có ngày nghỉ tương lai, danh sách xem trước, chạy tạo lần hai không sinh trùng. Test `PartialMonthSalaryTests` xác nhận phép tính lương theo ngày công vẫn giữ đúng. `manage.py check`, `makemigrations --check --dry-run` và `git diff --check` đạt; không có migration và không ghi dữ liệu nghiệp vụ. Lưu ý `manage.py test` không kèm label trong repo phát hiện 0 test, vì vậy cần gọi tường minh các module test.

**Chưa thực hiện:** Chưa thao tác tay trên giao diện với nhân viên thử nghiệm. Finance/chủ dự án cần xác nhận một lượt ở SIT/UAT bằng kỳ lương chưa khóa và nhân viên test nghỉ giữa kỳ: kiểm tra người đó ở danh sách còn thiếu, tạo dòng, chạy chức năng tính lương, đối chiếu ngày công/lương tỷ lệ, sau đó chạy tạo lại để xác nhận không trùng. Không thử bằng kỳ lương hoặc hồ sơ thật đang vận hành.

**Commit:** `ebc900f` (`fix: include mid-period leavers in payroll generation`) trên `chore/django-5.2-upgrade`; commit cục bộ, chưa push. Nhật ký này được commit riêng ngay sau đó. Tệp untracked `docs/Huong_Dan_Setup_TaskScheduler_SIT_UAT.md` vẫn được giữ nguyên.

## 2026-09-28 - Chuẩn hóa phát hiện/chạy test và đánh dấu khác biệt unique NULL

**Phạm vi:** xử lý hai mục trong `Yeu_Cau_Codex_Nho_Test_Ngan_Sach_Va_Lenh_Chay_Test.md`; giữ nguyên model và constraint ngân sách SQL Server, đồng thời thống nhất cách chạy toàn bộ test.

**Đã làm:** test `PlanningUniqueConstraintTests.test_company_wide_annual_budget_with_null_department_is_unique` được đánh dấu chỉ chạy khi `connection.vendor == "microsoft"`, với lý do rõ ràng: SQL Server và SQLite có hành vi khác nhau đối với NULL trong unique index; đây không phải lỗi dữ liệu ngân sách trên SQL Server. Thêm `ops/Run-Tests.ps1`: tự vào `src`, ưu tiên Python trong `venv`, chạy full discovery, in số test và trả lỗi nếu không tìm thấy test hoặc test thất bại. README, hướng dẫn SIT, runbook readiness và review readiness chỉ về cách chạy chuẩn; xác nhận `apps.portal.tests_mobile` nằm trong bộ discovery đầy đủ. Giữ nguyên các con số test của nhật ký lịch sử.

**Kiểm tra:** `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\Run-Tests.ps1` chạy trên SQL Server test database tạm; phát hiện và chạy 235 test, tất cả đạt; runner tạo rồi xóa test database. Với `DB_ENGINE=django.db.backends.sqlite3`, chạy riêng test NULL cho kết quả `skipped=1` cùng lý do mong đợi; dùng SQLite test database in-memory, không tạo file DB. Xác nhận thêm lệnh trực tiếp `python src\manage.py test` từ repo root báo `Found 0 test(s)` nhưng exit code 0 — wrapper tránh báo xanh giả bằng cách chuyển vào `src` và kiểm tra count. `manage.py check`, `makemigrations --check --dry-run`, `py_compile` và `git diff --check` đạt; không có thay đổi model/migration hay dữ liệu nghiệp vụ.

**Tệp:** `src/apps/planning/tests.py`, `ops/Run-Tests.ps1`, `README.md`, `docs/Huong_Dan_Setup_TaskScheduler_SIT_UAT.md`, `docs/Server_Trial_Readiness_2026-09-27.md`, `docs/Production_Readiness_Review_2026-09-23.md`.

**Git:** các thay đổi được yêu cầu gộp trong một commit trên `chore/django-5.2-upgrade`; chưa push. Tệp hướng dẫn SIT/UAT vốn untracked được cập nhật và đưa vào commit theo yêu cầu sửa tài liệu.

## 2026-09-28 - Rà soát và đẩy bản mới nhất lên GitHub

**Phạm vi rà soát:** năm commit local từ `67314ee` đến `31bf46c` trên `chore/django-5.2-upgrade`: giao diện mobile/PWA, sửa tạo bảng lương cho nhân viên nghỉ giữa kỳ, test regression, quy trình phát hiện test và tài liệu SIT/UAT. Đã kiểm tra diff mã nguồn, test, cấu hình frontend và danh sách tệp trước khi đẩy. Không phát hiện `.env`, database, credentials hoặc khóa riêng được theo dõi trong Git.

**Kiểm tra:** `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\Run-Tests.ps1` — 235/235 test đạt trên SQL Server test database tạm; runner tạo và xóa database. `manage.py check` đạt; `makemigrations --check --dry-run` báo không có thay đổi. Build Tailwind tái tạo cùng SHA-256 với CSS đã commit; `npm audit --audit-level=high` báo 0 lỗ hổng; `git diff --check` đạt.

**Đã push:** sau khi fetch xác nhận remote không có commit mới, đẩy nhánh `chore/django-5.2-upgrade` từ `92ea2d4` lên `31bf46c` thành công. Checklist go-live mới được thêm tại `docs/Checklist_Go_Live_IHRMS.md`; mục 1.1 đã đánh dấu hoàn tất. Checklist và mục nhật ký này được commit/push cùng nhau trong commit tài liệu sau đợt rà soát.

## 2026-09-28 - Tách portal views thành package theo domain

**Mục tiêu:** giảm kích thước `src/apps/portal/views.py` (3.593 dòng) bằng cách tách mã theo nhóm nghiệp vụ, không đổi URL, quyền truy cập hay logic nghiệp vụ.

**Backup trước sửa:** `D:\QLHCNS-Backups\portal-views-refactor-before-20260928-203029` gồm ZIP mã nguồn tại commit `2946460` và Git bundle lịch sử đầy đủ; ZIP CRC và `git bundle verify` đều đạt. Bản module cũ được giữ riêng trong thư mục backup.

**Đã làm:** chuyển thành package `src/apps/portal/views/` với `common.py` và 10 module domain: `core`, `attendance`, `tasks_kpi`, `documents`, `recruitment`, `reports_planning`, `office_procurement`, `hr`, `finance`, `assets`. `views/__init__.py` re-export toàn bộ 152 hàm để giữ cách URL và import hiện có. Cập nhật các đường dẫn mock trong test sang module sở hữu hàm. Cập nhật TechSpec để dùng cấu trúc mới. Không sửa model, migration, URL pattern, template, phân quyền hoặc thân hàm nghiệp vụ.

**Kiểm tra:** so sánh AST xác nhận 152/152 hàm giữ nguyên; `compileall` và `manage.py check` đạt; `makemigrations --check --dry-run` báo không có thay đổi. `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\Run-Tests.ps1` — 235/235 test đạt trên SQL Server test database tạm, database được tạo rồi xóa. `git diff --check` đạt.

**Git:** commit `refactor: split portal views into domain modules` trên `chore/django-5.2-upgrade`; push chưa thực hiện.

## 2026-09-28 - Sắp xếp tài liệu lưu trữ và dọn file sinh tự động

**Phạm vi:** rà soát vị trí mã nguồn, tài liệu, cấu hình và file cục bộ trước khi chuẩn bị môi trường chạy thử.

**Backup trước dọn:** `D:\QLHCNS-Backups\project-cleanup-before-20260928-205412` gồm ZIP mã nguồn tại `8bb820d` và Git bundle đầy đủ refs; ZIP có 492 mục. SHA-256 ZIP: `7548184F2F60C174BA819174DC7B2B77BB26BA10CC55B33EA4F1469498936D9F`; bundle: `5ED521A904717F294BB85F983ECD3E5E90A354E9F5055D3218C07C9BDD02A846`. `.env`, database, media, Backups/Logs, venv, node_modules và cấu hình VS Code không nằm trong backup và được giữ nguyên tại chỗ.

**Đã sắp xếp:** chuyển review lịch sử vào `docs/archive/reviews/` và prompt khởi tạo dự án vào `docs/archive/prompts/`; cập nhật các liên kết nội bộ. Mã Django nằm ở vị trí chuẩn `src/apps/`. Bỏ thư mục gốc `apps/` rỗng, thư mục sai chính tả `promts/` sau khi chuyển tệp, và 57 thư mục `__pycache__` chỉ chứa 249 file `.pyc` sinh tự động.

**Đã giữ lại:** hướng dẫn hiện hành, dữ liệu/cấu hình cục bộ, tệp uploads, staticfiles, backup SQL, logs, môi trường Python/npm và `.vscode/settings.json`; không xóa bản sao dữ liệu nào chưa xác định an toàn.

**Kiểm tra:** `manage.py check` đạt; `makemigrations --check --dry-run` báo không có thay đổi; 43 tệp Markdown được quét, mọi liên kết nội bộ đều tồn tại; `git diff --check` đạt. Không thay đổi mã ứng dụng, model hay migration.

## 2026-10-01 - Sao lưu và đối chiếu nhánh master, commit review 2

**Mục tiêu:** theo yêu cầu chủ dự án, sao lưu bản hiện tại trước; kiểm tra `origin/master` tại `ef93f4a` (`review 2`) và chỉ cập nhật nếu đó là bản sửa/review phù hợp. Bản ban đầu là `51a0807` trên `chore/django-5.2-upgrade`, khớp upstream và working tree sạch. Đã chạy `git fetch origin` để xác nhận remote; không dựa riêng vào ảnh hoặc thông tin người dùng báo cáo.

**Sao lưu đã xác nhận:** `D:\QLHCNS-Backups\before-review2-20261001-213243` chứa:

- `source-51a0807.zip`: `git archive --format=zip --output <zip> HEAD`, 494 mục; Python `zipfile.testzip()` xác nhận CRC đạt. Đã kiểm tra danh sách ZIP không có `.env`, database SQLite, `.bak`, khóa `.pem`/`.key`, venv, node_modules hay `src/media/`.
- `repository.bundle`: `git bundle create <bundle> --branches --remotes --tags HEAD`; `git bundle verify <bundle>` đạt, chứa lịch sử đầy đủ của các ref đã chọn, không đưa ref nội bộ Codex vào bundle.
- Nhánh khôi phục cục bộ `backup/before-review2-20261001-213243` trỏ tới `51a0807`; `BACKUP_INFO.txt` mô tả phạm vi. Đây là sao lưu mã nguồn/lịch sử Git, không phải sao lưu database, uploads hoặc secrets cục bộ.
- SHA-256 ZIP: `17ED14D778B5B34844522D3A167986DF6DC7FF5A59F61FDF80A7839950FA8366`; bundle: `CA6BB4D48E3AE48CABFF308A96A3EF601E9B4F1CF6F2CBC90B2C035954C4F1A9`.

**Cách kiểm tra:** tạo worktree tách biệt bằng `git worktree add --detach D:\QLHCNS-Review2-audit ef93f4a`. Dùng `git show`, `git diff`, `git merge-base` và đọc trực tiếp mã nguồn, báo cáo `docs/Code_Review_Report_2026-10-01.md`, quyền HR/KPI, workflow đặt xe, template HR và storage SharePoint ở hai bản. Không khởi tạo thư viện/gitlink bên ngoài.

**Kết quả đối chiếu và quyết định:**

- `ef93f4a` chỉ thêm báo cáo review 175 dòng và gitlink `.claude/skills/huashu-design`; không sửa mã ứng dụng, test hay dependency. `git diff --quiet 216e2ca ef93f4a -- src requirements.txt` trả 0: mã ứng dụng trên master vẫn giống mốc chung `216e2ca`.
- Có 61 commit trên nhánh hiện tại chưa nằm trong lịch sử master. So sánh hai cây bằng `git diff --shortstat HEAD origin/master` cho thấy 180 tệp khác nhau. Chuyển toàn bộ sang master sẽ bỏ các phần Hoạt động dự án, onboarding/offboarding, duyệt sửa hồ sơ, mobile/PWA, bộ test mở rộng, runbook vận hành và nhật ký dự án; đồng thời mất bản sửa tạo lương cho nhân viên nghỉ giữa kỳ và kiểm quyền danh sách hợp đồng.
- Báo cáo có phát hiện đúng còn áp dụng cho bản hiện tại: `hr_candidate_list`/`hr_candidate_detail` thiếu kiểm quyền HR; `kpi_score_update` thiếu giới hạn phòng của trưởng phòng; `SharePointStorage.exists()` trả False khi Graph báo lỗi; tăng số sổ công văn chưa khóa dòng. Đây là kết quả đọc mã, chưa chạy khai thác hay gọi dịch vụ thật.
- Một số nhận xét sai ngay trên mã được review: I15 nói tạo đặt xe không `full_clean()`/tự Approved, trong khi view đã gọi `full_clean()` và đặt Pending; I8 nói form nâng lương/gia hạn nằm ngoài điều kiện HR, trong khi cả hai nằm trong `{% if can_manage_hr %}`. C2 về danh sách hợp đồng đã được sửa trên nhánh hiện tại. I14 về unique NULL không thể áp dụng chung cho SQL Server: bản hiện tại có test riêng theo backend; đợt này không xác nhận SQL Server.
- **Giữ nhánh và mã ứng dụng hiện tại; không merge/cherry-pick/chuyển sang master.** Báo cáo review có giá trị tham khảo từng phát hiện sau xác minh, chưa đủ căn cứ để thay thế bản hiện tại hoặc áp dụng toàn bộ khuyến nghị.

**Kiểm tra thực tế trong đợt này:** dùng `D:\QLHCNS\venv\Scripts\python.exe` với runner ngoài repository tại `D:\QLHCNS-Backups\before-review2-20261001-213243\run_isolated_audit.py`. Runner chạy từ `src`, dùng khóa giả ngẫu nhiên, SQLite test database in-memory, tắt SharePoint; không dùng secrets thật hay ghi database nghiệp vụ. Log nằm cùng thư mục backup. Các lệnh chính xác (thay `<root>` bằng một trong hai đường dẫn dưới đây):

```powershell
& D:\QLHCNS\venv\Scripts\python.exe D:\QLHCNS-Backups\before-review2-20261001-213243\run_isolated_audit.py <root> test
& D:\QLHCNS\venv\Scripts\python.exe D:\QLHCNS-Backups\before-review2-20261001-213243\run_isolated_audit.py <root> check
& D:\QLHCNS\venv\Scripts\python.exe D:\QLHCNS-Backups\before-review2-20261001-213243\run_isolated_audit.py <root> migrations
```

- `<root> = D:\QLHCNS-Review2-audit`: 86/86 test đạt; Django `check` đạt; `makemigrations --check --dry-run` không có thay đổi.
- `<root> = D:\QLHCNS`: phát hiện/chạy 235 test trong 98,016 giây; 233 đạt, 1 thất bại, 1 bỏ qua (unique NULL chỉ dành cho SQL Server). Không ghi nhận toàn bộ suite đạt.
- Test thất bại là `ActivityDashboardPermissionTests.test_department_manager_sees_only_activities_in_managed_departments`: mong 1 hoạt động nhưng nhận 2. Fixture tạo hai hoạt động trong cùng phòng vào 01/10/2026; test chỉ đổi một hoạt động theo `date.today()`. Khi hiện tại là tháng 10/2026, dashboard đếm đúng cả hai hoạt động cùng phòng, khác kỳ vọng test. Chạy runner `D:\QLHCNS dateprobe` cố định cả ngày test và `timezone.localdate()` ở 28/09/2026 cho kết quả 1/1 đạt; xác nhận test phụ thuộc lịch, không phải bằng chứng thấy hoạt động phòng khác. Chưa sửa fixture hoặc logic nghiệp vụ trong đợt kiểm tra này.
- Django `check` bản hiện tại đạt; `makemigrations --check --dry-run` không có thay đổi. Lần đầu runner gặp cảnh báo đường dẫn SQLite `:memory:` bị ghép với BASE_DIR; đã sửa runner để đặt NAME trực tiếp và chạy lại kiểm tra migration cả hai bản, không còn cảnh báo đó.
- Runner `D:\QLHCNS-Review2-audit deploy` chạy `check --deploy` với cấu hình giả an toàn: còn W004/W008/W012/W016 (4 cảnh báo HTTPS/cookie). Không dùng kết quả cấu hình giả này để kết luận máy triển khai thật đã hoặc chưa cấu hình xong. Lần in log test hiện tại bị lỗi encoding console sau khi log đầy đủ đã được ghi; đã đọc kết quả từ log và sửa runner dùng UTF-8, không coi lỗi in log là lỗi ứng dụng.
- `git diff --check` đạt sau khi cập nhật nhật ký. Không chạy SQL Server, migration trên database nghiệp vụ, UAT giao diện hoặc kết nối SharePoint thật trong đợt này.

**Tệp thay đổi và Git:** chỉ cập nhật `docs/PROJECT_WORK_LOG.md` trên `chore/django-5.2-upgrade`; lưu bằng commit cục bộ `docs: record backup and review 2 assessment`, chưa push. Mã ứng dụng vẫn ở nội dung `51a0807`. Worktree review và backup được giữ bên ngoài thư mục dự án để truy vết.

**Việc còn mở / bước tiếp theo:** ưu tiên vá quyền xem ứng viên, scope KPI, xử lý lỗi xác định tồn tại tệp SharePoint và khóa tăng số công văn sau khi tái hiện bằng regression test; sửa fixture activity để không phụ thuộc tháng chạy. Khi sửa xong, chạy full suite trên SQLite và SQL Server test database cô lập rồi UAT theo vai trò. Đợt này không có thao tác triển khai đang chờ chủ dự án thực hiện. Nếu cần quay lại bản mã nguồn trước kiểm tra: lưu/commit mọi thay đổi mới, rồi chạy `git -C D:\QLHCNS switch backup/before-review2-20261001-213243`; lệnh chỉ đổi mã nguồn Git, không khôi phục database/uploads/secrets.

## 2026-10-02 - Hợp nhất các nhánh về main và thống nhất nhánh vận hành

**Yêu cầu:** kiểm tra commit mới nhất trong các nhánh QLHCNS, hợp nhất về main; chủ dự án làm việc một mình và yêu cầu từ nay chỉ phát triển/kiểm thử/chạy trên main. Quyết định này thay thế lựa chọn giữ nhánh nâng cấp ở nhật ký ngày 01/10.

**Đối chiếu trực tiếp GitHub:** main ban đầu ở `8258a3ed055775b25cb20f757acc95172c7865d0`; master ở `ef93f4ad11dfbdb5cfdefaa280cc1c3d2dc8b2b8` (review 2, 01/10); chore/django-5.2-upgrade ở `95ea51889bd2affcd947121a8bebe09632409500` (rà soát chưa hoàn tất, 02/10). Master có 1 commit mới, chỉ thêm báo cáo review và gitlink .claude/skills/huashu-design. Nhánh nâng cấp có 63 commit chưa thuộc lịch sử main và phía main có 1 merge commit riêng. Không có CI check-runs trên commit nâng cấp tại thời điểm kiểm tra.

**Đã hợp nhất:** PR #3 bằng merge commit `dd3f85e27725bf051d0a5b9e5e5bba736eb3a20d`, sau đó PR #4 (master -> main) bằng `c8bb44f641235a2877a3de0bc337a7fa43228085`. Cả hai GitHub xác nhận merge thành công, không xung đột; giữ lịch sử, không force-push. Đối chiếu cây merge PR #3 với cây nhánh nâng cấp không có khác biệt. Sau PR #4, khác biệt so với bản nâng cấp chỉ là báo cáo review và gitlink thiết kế; mã ứng dụng giữ nguyên. Không khởi tạo gitlink kỹ năng bên ngoài. Các nhánh cũ được giữ để tra cứu và không dùng cho công việc tiếp theo.

**Tài liệu thay đổi:** AGENTS.md ghi quy tắc chỉ phát triển, kiểm thử, chạy và triển khai trên main; README.md bổ sung cách đồng bộ main; mục nhật ký này lưu kết quả và giới hạn xác nhận.

**Kiểm tra đã chạy thực tế:** lấy mã tại SHA cố định qua GitHub vào bản kiểm tra riêng trên Linux/Python 3.12; cài các phiên bản trong requirements.txt vào virtualenv riêng. Clone Git trực tiếp không có credential của kho private, nên dùng kết nối GitHub đã được cấp quyền để đọc và hợp nhất. Không dùng .env, dữ liệu nhân sự, database nghiệp vụ hay SharePoint thật.
- `python ops/run_tests.py --backend sqlite`: phát hiện 258 test, 256 đạt, 2 bỏ qua, exit code 0; chạy trong 21,962 giây với database in-memory, media tạm và SharePoint tắt. Hai test chỉ dành SQL Server: unique NULL của ngân sách và khóa dòng khi cấp số công văn đồng thời.
- Lần chạy đầu có 1 lỗi vì bản lấy mã còn thiếu ảnh PWA; đã lấy đúng hai ảnh gốc từ GitHub và chạy lại toàn bộ suite đạt như trên. Không sửa mã/test để bỏ qua lỗi.
- Django `check`: không có lỗi; `makemigrations --check --dry-run`: No changes detected; `pip check`: No broken requirements found. Kiểm tra Django dùng cấu hình giả và database in-memory, không ghi database vận hành.

**Giới hạn và việc còn mở:** chưa chạy SQL Server, Edge/UAT giao diện, SharePoint thật hoặc triển khai máy chủ; commit 95ea5188 ghi rõ đợt rà soát tổng thể chưa hoàn tất. Đợt này hoàn thành hợp nhất nhánh, không xác nhận nghiệm thu toàn bộ dự án. SQL Server/Windows của chủ dự án không truy cập được từ môi trường này.

**Chủ dự án cập nhật máy Windows:** tại D:\\QLHCNS, chạy `git status` trước. Nếu working tree sạch, chạy lần lượt `git fetch origin`, `git switch main`, `git pull --ff-only origin main`. Nếu có thay đổi chưa commit hoặc không fast-forward, giữ nguyên và đối chiếu; không reset/clean/force-push. Sau khi xác nhận database test/SIT cô lập, chạy `powershell -NoProfile -ExecutionPolicy Bypass -File .\\ops\\Run-Tests.ps1 -Backend sqlserver` để xác nhận hai kiểm thử đặc thù và full suite. Không tự chạy migration trên database nghiệp vụ trong đợt này.

## 2026-10-02 - Kiểm thử 3 tình huống công việc bằng HTTP; Edge chưa khả dụng

**Yêu cầu:** nếu có thể, test trực tiếp Microsoft Edge với 2–3 tình huống giả định đúng nghiệp vụ, gồm lưu/sửa/xóa, và báo kết quả.

**Khả năng truy cập đã kiểm tra:** inventory điều khiển trình duyệt chỉ có Chrome với tab about:blank, không có Edge hay native app; môi trường Linux không tìm thấy executable microsoft-edge/microsoft-edge-stable. Không kết nối tới Edge trên máy Windows của chủ dự án. Vì vậy không chạy kiểm thử giao diện trên Edge và không dùng kết quả HTTP để tuyên bố Edge đã đạt. Không mở Chrome thay thế, không chạm database thật.

**Mã nguồn và thay đổi:** xác nhận GitHub main tại `ae537c8c594308cd5ba12acdd02f11ac56de5920`, kiểm thử trên bản nguồn của main. Thêm `src/apps/portal/tests_business_scenarios.py` để lưu 3 kịch bản có thể chạy lại, chỉ đổi test và nhật ký; không sửa nghiệp vụ/model/migration. Django Client bật enforce_csrf_checks; GET form lấy CSRF cookie rồi POST có token, fixture đăng nhập bằng force_login. Không kiểm thử màn hình đăng nhập, thao tác chuột, JavaScript, bố cục hoặc tải tài liệu trên trình duyệt.

**Kết quả từng tình huống, tất cả đạt:**
1. HR_MANAGER mở form và tạo nhân viên giả định -> đọc trang chi tiết -> mở form sửa điện thoại/địa chỉ -> xác nhận dữ liệu lưu trong database và HTML trả về, created_by/modified_by đúng. POST hồ sơ trùng mã/CCCD/email bị từ chối, không thêm bản ghi; EMPLOYEE POST sửa hồ sơ bị chặn, dữ liệu không đổi.
2. EMPLOYEE lưu dòng chấm công 8 giờ -> xác nhận nội dung xuất hiện trong trang tháng -> lưu tổng hợp tháng với 1 ngày nghỉ ốm -> sửa thành 2 ngày, giữ Pending. Tài khoản khác POST xóa dòng nhận 404; GET xóa nhận 405; chủ sở hữu POST xóa được. Bản ghi bị xóa mềm, còn trong all_objects và biến mất khỏi trang tháng. Phần sửa là tổng hợp tháng, không phải sửa trực tiếp dòng giờ công.
3. EMPLOYEE có quỹ phép giả định 12 ngày gửi phép năm 02–03/11/2026 -> Pending, total_days = 2 -> đơn trùng ngày bị chặn, không tạo thêm bản ghi. EMPLOYEE tự POST duyệt bị chặn; HR_MANAGER duyệt đúng quyền -> Approved và 1 LeaveApproval; duyệt lại nhận 404, không tạo lịch sử trùng; nhân viên thấy trạng thái Đã duyệt.

**Kiểm tra đã chạy:** runner tạm chạy đúng 3 kịch bản HTTP, 3/3 đạt. Sau khi lưu module test, chạy từ gốc repository `python ops/run_tests.py --backend sqlite`: phát hiện 261 test, 259 đạt, 2 bỏ qua vì cần SQL Server, exit code 0, 23,184 giây; Django system check không có lỗi. Database in-memory tạo/xóa bởi test runner, media tạm, SharePoint tắt, email locmem; chỉ dữ liệu giả. Log ERROR do cố tình gửi trùng hồ sơ/đơn nghỉ hoặc giả lập lỗi rollback là đường kiểm thử âm, suite vẫn đạt.

**Cách chạy lại 3 tình huống trên Windows:** tại D:\\QLHCNS sau khi đồng bộ main, chạy `powershell -NoProfile -ExecutionPolicy Bypass -File .\\ops\\Run-Tests.ps1 -Backend sqlite -Labels apps.portal.tests_business_scenarios`. Đây vẫn là kiểm thử HTTP, không phải kiểm thử Edge.

**Việc chưa xác nhận và cách hoàn tất:** môi trường này thiếu Microsoft Edge và quyền truy cập máy Windows, nên còn UAT Edge/SQL Server thật. Để kiểm tra Edge, trên máy Windows chạy bản main với database test/SIT riêng; mở /portal/ trong Edge, dùng tài khoản giả định HR_MANAGER và EMPLOYEE, thao tác lần lượt theo ba tình huống trên, tải lại trang sau khi lưu/sửa/xóa và đối chiếu trạng thái/dữ liệu. Không xóa hồ sơ nhân sự thật hoặc duyệt đơn thật. SQL Server cần database test cô lập và chạy lại full suite; không ghi nhận là đã chạy trong đợt này.


## 02/10/2026 — Gia cố bảo vệ dữ liệu nhạy cảm trên main

**Mục tiêu/phạm vi:** kiểm tra mã nguồn tại main `89d5d6f`, tái hiện lỗi truy cập, vá ứng dụng và dependency. Không chạy migration hay thao tác trên database thật.

**Đã làm:** thêm private download có allowlist model/FileField, kiểm tra quyền trước đọc local/Graph, chặn raw media trong Django; giới hạn phân quyền/reset mật khẩu của SYS_ADMIN và ẩn CCCD/MST/BHXH trong Admin cho SYS/DEPT; sửa bypass xóa/khôi phục hàng loạt và action tạo Task của người chỉ xem; bỏ salary/contract context khỏi HR detail cho người không có quyền; tách quyền export, áp dụng scope/độ mật cho Excel công văn, ghi chuỗi Excel dạng text; throttle đăng nhập persistent username/IP 5 lần/30 phút; idle timeout/no-store; production config guard và ép TLS/kiểm tra chứng chỉ SQL Server; lọc exception log; metadata audit login/logout/download/export cùng migration security/0003. Nâng dotenv/requests/msal/cryptography và thêm axes. Thêm kiểm tra URL tài liệu tránh javascript/data/raw media; tài khoản có staff/group/permission cũng nằm ngoài phạm vi reset mật khẩu SYS_ADMIN. Các test đăng nhập cũ chuyển sang HTTP thật để chạy qua backend chống brute-force.

**Tái hiện trước vá:** `python ops/run_tests.py --backend sqlite apps.security.tests_data_protection`: 7 test thất bại đúng các lỗi kiểm soát. Salary/contract ở đây là dữ liệu truyền vào template context; không khẳng định đã lộ trong HTML trước vá (template có điều kiện riêng).

**Kiểm chứng:** toàn bộ suite sau vá/dependency và URL/scope cuối: 281 test, 279 đạt, 2 bỏ qua do chỉ dành SQL Server; 20 regression security đạt. Lệnh `python ops/run_tests.py --backend sqlite` chạy DB/media dùng một lần; 3 kịch bản nghiệp vụ lưu/sửa/xóa HR, chấm công, nghỉ phép vẫn đạt. `manage.py check` không vấn đề; `makemigrations --check --dry-run` không thay đổi; `pip check` đạt. `pip-audit -r requirements.txt` quét 25 dependencies, không phát hiện vulnerability đã biết. Nhóm security + M365 chạy riêng: 24 test đạt; URL SharePoint không gọi Graph lấy web URL. Production guard 4 tình huống cấu hình đạt (hợp lệ, HTTP, key yếu, wildcard host); kiểm tra cấu hình SQL Server production có Encrypt=yes;TrustServerCertificate=no (không mở kết nối). Dữ liệu tổng hợp, không dùng hồ sơ thật.

**Giới hạn còn mở:** không test Microsoft Edge (môi trường chỉ có browser cloud), không có SQL Server/IIS/SharePoint thật. Chưa mã hóa cấp trường; chưa xác nhận TLS/TDE/backup/ACL server, MFA/SSO, single-session hoặc audit bất biến. Quét dependency không thay thế pentest; không kết luận đủ an toàn production.

**Triển khai cần người phụ trách máy chủ thực hiện:**

1. Sao lưu database và tệp; xác minh khôi phục ở SIT. Dừng app, cập nhật chỉ main: `git switch main`, `git pull --ff-only origin main` (giữ các chỉnh sửa cục bộ; không reset).
2. Trong virtualenv của app, tại gốc repo: `python -m pip install -r requirements.txt`; `python -m pip check`.
3. Tại src trên SIT trước: `python manage.py migrate --plan`, rà plan rồi `python manage.py migrate` để thêm bảng axes và tblSecurityEvent; `python manage.py check`. Xác nhận trên SQL Server trước khi áp dụng production.
4. IIS bỏ alias/virtual directory raw media; backend chỉ nội bộ; proxy ghi lại X-Forwarded-Proto; đặt `APP_ENV=production`, `DEBUG=False`, `ENABLE_HTTPS_ENFORCEMENT=True`, secret riêng đủ mạnh và ALLOWED_HOSTS cụ thể. SQL Server cần chứng chỉ TLS tin cậy, tên DB_HOST khớp chứng chỉ; production ép Encrypt=yes/TrustServerCertificate=no và từ chối kết nối nếu cert không hợp lệ. Chạy `python manage.py check --deploy`, xử lý cảnh báo theo cấu hình HTTPS thực.
5. Kiểm thử Edge bằng tài khoản thử: người khác tải tệp nghỉ phép bị chặn; SYS không nâng quyền/xuất CCCD; Finance không xóa kỳ Locked; login sai 5 lần rồi khóa, hết 30 phút đăng nhập lại; HR vẫn xuất/đọc tệp đúng quyền; URL /media không trả file. Không thử brute-force trên tài khoản thật.
6. DBA/IT xác nhận mã hóa SQL Server/backup, TLS, MFA và SharePoint ACL; tài khoản database/service chỉ có quyền cần thiết. Duy trì backup rollback cho lần triển khai.

**Nhánh/commit:** thay đổi đưa trực tiếp main; tra commit tương ứng với mục nhật ký này trong lịch sử main.

## 02/10/2026 — Vá các đề xuất review được chủ dự án duyệt trên main

**Ủy quyền/phạm vi:** sau đợt review chỉ đọc trên main `2003d97`, chủ dự án trả lời “duyệt đề xuất”. Thực hiện các nhóm P1 trước, kiểm thử riêng đạt rồi chuyển nhóm; tiếp tục P2. Dùng kết nối GitHub cho kho private và bản nguồn kiểm thử riêng; không phải checkout Windows của chủ dự án. Chỉ cập nhật main, giữ lịch sử và không force-push. Không sửa công thức/rate/quy tắc làm tròn lương, không chạm database/media/SharePoint thật.

**P1 đã sửa:**
- Payroll thêm `calculated_at`/`calculation_signature` (migration payroll/0004). Khóa kỳ chỉ khi có đủ nhân viên cần trả lương, mỗi dòng đã tính và đầu vào/kết quả khớp tính lại với dữ liệu công/nhân sự/config hiện hành; phát hành phiếu sau kiểm tra. Tạo/tính/sửa dòng Portal và Admin khóa/recheck kỳ trong giao dịch. Admin không đổi status kỳ bằng form để bỏ qua kiểm tra. Nhân viên vào làm sau cuối kỳ không nằm trong danh sách cần trả lương. Số học từ prorated salary tới Net đối chiếu nguyên vẹn với main trước vá. Dòng cũ của kỳ Open cần tính lại trước chốt; không đánh dấu giả là đã tính. Kỳ Locked cũ không tự tính hoặc thay đổi số liệu.
- Chấm công kiểm tra 0–24 giờ/dòng và tổng một nhân viên/ngày qua các dự án không quá 24; chặn thêm/sửa/xóa/khôi phục giờ khi tháng Approved hoặc kỳ Locked. Tổng hợp tháng không nhận số âm; sửa dữ liệu đã duyệt bị chặn, trạng thái đọc lại sau khóa. Các giao dịch dùng thứ tự khóa kỳ rồi nhân viên; việc mở lại Pending chỉ có thể thực hiện qua thao tác nghiệp vụ có kiểm soát ở tầng server, không có form Admin/POST nhân viên để tự mở lại. Migration attendance/0008 thêm validators.
- Admin dùng scope đối tượng và queryset FK phòng ban/nhân viên cho DEPT_MANAGER; chặn POST chọn ngoài phạm vi ở Task/KPI/Event/công văn, bổ sung scope Timesheet Admin. Duyệt phép Admin khóa/recheck Pending, kiểm tra người duyệt/phạm vi, cấm trưởng phòng tự duyệt, ghi quyết định và audit trong cùng transaction; form không sửa status để bỏ qua action.
- Portal/Admin xuất VPP dùng chung `office.services.issue_supply_request`: khóa đề nghị và vật tư theo thứ tự, cộng gộp dòng trùng, kiểm tra đủ tồn toàn bộ trước trừ, không xuất lại trạng thái Issued. Migration office/0005 thêm CHECK không tồn âm, số đề nghị dương, số đã cấp trong khoảng hợp lệ; không tự sửa dữ liệu cũ.
- Xóa mềm/khôi phục cấp phát tài sản đồng bộ trạng thái tài sản dưới khóa; khôi phục kiểm tra overlap/tài sản sẵn sàng. Queryset restore kiểm tra full_clean và hooks trong transaction; lỗi khôi phục hàng loạt rollback và hiện thông báo. Admin xử lý ValidationError/IntegrityError lúc ghi thành thông báo có kiểm soát.
- Backup Full/Log dùng helper PowerShell: database bắt buộc, sqlcmd `-b -V 11 -x`, edition-aware compression (Express/Web dùng NO_COMPRESSION), CHECKSUM + RESTORE VERIFYONLY, xác nhận file/SHA256 trước ghi thành công/retention; không ghi đè file sẵn có. Copy Weekly/Monthly kiểm tra hash, retention theo prefix đúng database; log giữ tối thiểu 30 ngày để khớp cửa sổ Daily. Setup-RecoveryModel.sql bỏ COMPRESSION cho Express. VERIFYONLY không thay thế restore drill.

**P2 đã sửa:** ngày timesheet sai trả redirect/thông báo thay vì 500. GraphAPIError có HTTP status/Retry-After, không trả URL/payload upstream; private download/attachment hồ sơ/activity dùng chung response có kiểm tra quyền, 404 cho tệp thiếu, 503 có Retry-After khi dịch vụ lỗi. PDF phiếu lương kiểm tra Payroll/Period/Employee chưa xóa. Axes giữ khóa username 5 lần/30 phút, IP ngưỡng riêng mặc định 50 (`AXES_IP_FAILURE_LIMIT`); đăng nhập đúng của đồng nghiệp không xóa failures của tài khoản khác cùng IP. CI `.github/workflows/ci.yml` chạy backend/migrations/dependency audit, frontend audit/build và backup harness trên main, token contents:read và không checkout gitlink. Runner test đặt APP_ENV=test để cấu hình production không ngăn việc cô lập HTTPS/storage của test. Thêm `python src/manage.py audit_review_integrity`: chỉ đọc, in số lượng dữ liệu cũ sai, exit lỗi nếu phát hiện; không in danh tính và không tự sửa.

**Kiểm chứng thực tế:**
- Nhóm lương 30 test đạt; chấm công/common + 3 tình huống HTTP + invalid input 17 đạt; quyền/leave/security 57 đạt; office/stock 8 đạt; asset/common 9 đạt; P2/M365/security/activity 60 đạt. Sau bổ sung ca biên, 33 regression mới ở `apps.portal.tests_approved_review` đều đạt.
- `python ops/run_tests.py --backend sqlite` trên mã ứng dụng cuối: 314 test, **312 đạt, 2 bỏ qua**, exit 0, 48,669 giây; database in-memory/media dùng một lần, M365 tắt, email locmem, dữ liệu giả. Hai test bỏ qua yêu cầu SQL Server (unique NULL và khóa cấp số công văn). 3 tình huống HTTP có CSRF lưu/sửa/xóa HR, công, nghỉ phép vẫn đạt. Fixture thông báo/phiếu lương bổ sung lương đã tính trước chốt; fixture nghỉ bù nhập trong Pending rồi duyệt; giữ nguyên assertions/công thức.
- Sau sửa runner APP_ENV, chạy 3 kịch bản HTTP với APP_ENV=production từ bên ngoài để xác nhận runner tự chuyển cấu hình test; 3/3 đạt, exit 0. Không dùng kết quả HTTP để xác nhận UI/Edge.
- PowerShell 7.4.13 chạy **6/6** ca Full/Log × Express/Standard/Failure bằng `ops/backup/Test-BackupSafety.ps1`: sqlcmd giả lập, chỉ tệp tạm; parse scripts, kiểm tra flags/compression, lỗi verification trả exit 1/giữ backup cũ, success không dọn backup DB khác. Không chạy SQL thật.
- Python syntax/AST đạt; `makemigrations --check --dry-run`: No changes detected; `pip check`: đạt; pip-audit requirements 25 dependencies không có lỗ hổng đã biết; npm audit 0 vulnerabilities; Tailwind build đạt (caniuse-lite cũ chỉ cảnh báo build). actionlint 1.7.12 kiểm tra CI không có lỗi. CI đã kiểm tra cấu hình tại đây; trạng thái chạy GitHub phải xem tại Actions của commit, không coi test local là kết quả Actions.
- `check --deploy` với cấu hình production giả, HTTPS/cookie/host/secret riêng và HSTS=31536000: chỉ còn W005/W021 (subdomain/preload); không tắt check. Chỉ bật hai tùy chọn khi IT xác nhận toàn bộ phạm vi HTTPS. Mặc định HSTS trong .env.example vẫn 0 cho SIT, cần cấu hình riêng trước production.

**Giới hạn/release gate:** chưa có SQL Server/IIS/Edge/SharePoint thật; SQLite không chứng minh khóa/race SQL Server. Không migration/triển khai live. Chưa xác nhận restore/backup encryption/ACL/TLS/MFA hay mã hóa cấp trường; CCCD/MST/BHXH/lương vẫn cần thiết kế quản lý khóa và migration được phê duyệt nếu triển khai mã hóa cấp trường. Không kết luận “không còn lỗi” hoặc đủ an toàn production. HR/Finance vẫn phải duyệt master rates và số liệu lương; không thay đổi rate pháp lý trong đợt này.

**Trình tự người phụ trách Windows/SIT cần làm:**
1. Giữ mọi chỉnh sửa local; `git status`, `git fetch origin`, `git switch main`, `git pull --ff-only origin main`. Cài requirements vào virtualenv riêng. Chuẩn bị database/uploads SIT cô lập, backup có thử restore; không trỏ thao tác thử vào dữ liệu thật.
2. Trên database SIT đã có schema cũ: `python src/manage.py audit_review_integrity`. Lệnh chỉ đọc nhưng cần kết nối đúng database; nếu exit lỗi, HR/Finance/IT phải đối chiếu và phê duyệt sửa dữ liệu cũ. Không bỏ CHECK hoặc tự set tồn/số giờ để qua migration. Kiểm tra cả bản ghi đã xóa đối với stock/lines vì CHECK áp dụng toàn bảng.
3. `python src/manage.py migrate --plan`, rà plan (bao gồm payroll/0004, attendance/0008, office/0005 và migration security/axes nếu chưa áp dụng); chỉ chạy `python src/manage.py migrate` tại SIT sau khi xác nhận dữ liệu/backup. Tính lại các dòng Open rồi kiểm tra chốt/phiếu, không sửa kỳ Locked lịch sử.
4. Chạy `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\Run-Tests.ps1 -Backend sqlserver` với cấu hình SIT; kiểm tra khóa kỳ đồng thời tính/sửa, duyệt công đồng thời nhập/xóa, hai lần xuất kho, cấp phát/xóa/restore đồng thời. UAT Edge ít nhất 3 kịch bản HTTP tương ứng và thử tải tệp local/SharePoint đúng/sai quyền, Graph outage. Rà Admin scope theo HR/Dept/Finance.
5. Cập nhật Task Scheduler backup để truyền đúng `-Database`, dùng tài khoản/ACL và đích độc lập được bảo vệ; chạy job thật, xác nhận failures và restore drill tại SQL Server test. SQL script khởi tạo vẫn dùng ví dụ qlhcns/path D:, phải đối chiếu trước chạy. Backup SQL không bao gồm media: IT phải có kế hoạch sao lưu/restore SharePoint/local uploads cùng DB.
6. Chỉ triển khai production trong cửa sổ/rollback được duyệt sau SQL Server + UAT + restore + bảo mật môi trường đạt. Nhật ký commit nằm cùng thay đổi trên main, tra SHA trong lịch sử GitHub.

**Đối chiếu GitHub sau push / sửa CI checkout:** bản vá ứng dụng ở `58a013efa735522edd3cdd610083520182944a44`. CI lần 1 (run 36996903447) dừng cả 3 job tại checkout, chưa chạy test: `fatal: No url found for submodule path '.claude/skills/huashu-design' in .gitmodules`. Đây là gitlink đã nhập từ master trong PR #4; cả `submodules:false` vẫn không ngăn checkout action duyệt gitlink khi dọn auth. Gỡ duy nhất tham chiếu gitlink hỏng trong commit tiếp theo cùng main để clone/CI hoạt động; lịch sử giữ bản trước, không tải/khởi tạo/xóa thư mục kỹ năng của người dùng hay thay mã ứng dụng. Trạng thái CI lần chạy tiếp theo phải đối chiếu tại Actions; kết quả local 314 test không thay đổi bởi sửa metadata này.

**CI lần 2:** sau gỡ gitlink (`fb731909`), checkout và frontend đạt. Log job backup xác nhận cả 6 ca PASS nhưng shell Actions thoát 1 do LASTEXITCODE còn lại từ child process cố ý fail. Sửa riêng harness để reset exit code sau khi mọi assertion đã đạt; không thay script backup thật hay bỏ kiểm tra failure. Kiểm tra lại toàn bộ 6 ca trong cùng shell theo cách Actions kết thúc bằng LASTEXITCODE trước push. Job backend chạy test riêng; không coi trạng thái còn chạy là đạt.

**Xác nhận CI lần 3 (02/10/2026):** đã đọc trạng thái jobs và log thực tế của [Actions run 36997497582](https://github.com/dinhtanhb/QLHCNS/actions/runs/36997497582), commit `a6b4ecd3aca33dc130c637393f1d1240f8eca1ec` trên main: completed/success, cả backend, frontend và backup-command-tests đều success. Backend chạy 314 test trong 55,477 giây, 312 đạt và 2 bỏ qua vì cần SQL Server; check/migration/pip check/pip-audit đạt. Frontend npm audit không có lỗ hổng đã biết và build CSS đạt. Backup log xác nhận cả 6 ca Full/Log × Express/Standard/Failure PASS, job exit thành công sau sửa harness. Đây là kết quả GitHub Actions, không chỉ kiểm tra local. Đợt tiếp tục chỉ đối chiếu bằng chứng và cập nhật nhật ký, không sửa thêm ứng dụng hoặc migration. Chưa có kết nối tới Windows/SIT SQL Server/IIS/Edge/SharePoint để hoàn tất các bước nghiệm thu thật nêu trên; không áp dụng migration hay triển khai production. Tiếp theo người phụ trách thực hiện audit dữ liệu chỉ đọc, migration trên SIT, full suite SQL Server, UAT Edge và restore drill theo trình tự đã ghi; gửi kết quả/lỗi đã loại bí mật để tiếp tục xử lý.

## 02/10/2026 — Kiểm thử trên SQL Server và Edge với bản sao dữ liệu tại máy Windows

**Mục tiêu/phạm vi:** theo yêu cầu của chủ dự án, chỉ làm trên `main`; xác định môi trường bằng thao tác đọc trước, kiểm tra dữ liệu trước migration, chạy test SQL Server và thử ba tình huống nghiệp vụ trên Edge. Đã đọc `AGENTS.md` và nhật ký trước khi làm. `git fetch origin main` xác nhận working tree ban đầu sạch, `main` khớp `origin/main` tại `2cc0e3b`; không đổi nhánh, reset hoặc ghi đè dữ liệu gốc.

**Môi trường đã xác nhận:** Python `venv` 3.12.14, Django 5.2.17, pyodbc 5.2.0; dịch vụ SQL Server Express và ODBC Driver 17/18 có sẵn; Microsoft Edge có thể điều khiển qua tiện ích trình duyệt. Django hiện kết nối Windows authentication tới database `qlhcns` trên SQL Server Express cục bộ; không in credential hay nội dung `.env`. `pip install -r requirements.txt` bổ sung/cập nhật dependency chỉ trong `venv`; `pip check` và `manage.py check` đạt. Database gốc có 73 migration đã áp dụng và không có hồ sơ `UAT-*` sau kiểm thử.

**Kiểm tra chỉ đọc và bản sao:** `venv\Scripts\python.exe src\manage.py audit_review_integrity` trên database gốc: cả 5 nhóm sai lệch đều 0, exit 0. `migrate --plan` trên gốc liệt kê attendance/0008, axes/0001–0010, office/0005, payroll/0004, security/0003; không áp dụng migration lên gốc. Tạo database riêng `qlhcns_codex_uat_20261002` qua `BACKUP ... WITH COPY_ONLY, CHECKSUM` và `RESTORE VERIFYONLY` (đạt), `RESTORE DATABASE` với data/log file riêng. Sao chép 6 tệp media vào thư mục thử riêng; số lượng, tổng byte và SHA-256 từng tệp khớp nguồn. Audit trên bản sao cũng 5/5 bằng 0. `manage.py migrate --noinput` trên bản sao áp dụng toàn bộ migration còn thiếu, `migrate --plan` sau đó không còn việc; `makemigrations --check --dry-run`: No changes detected; `manage.py check` đạt. Không sửa/xóa bản ghi nghiệp vụ gốc.

**Edge trên bản sao:** chạy Django chỉ ở `127.0.0.1:8765` với DB/media bản sao, tắt M365; dùng hostname `localhost` để tách cookie khỏi phiên `127.0.0.1` có sẵn. Tạo tài khoản/hồ sơ UAT giả trên bản sao.

1. HR tạo hồ sơ giả qua form Edge, mở trang chi tiết, sửa điện thoại/địa chỉ; điều hướng và giá trị điện thoại hiển thị sau lưu. Đối chiếu SQL xác nhận hồ sơ và điện thoại đã lưu. Không thử xóa hồ sơ gốc.
2. Nhân viên thêm dòng công 8 giờ trên Edge, thấy dòng tại bảng tháng; lưu số ngày nghỉ ốm 1 rồi sửa 2, SQL xác nhận `2.0`/Pending. Phát hiện 5 ô `type=number` ban đầu render số thập phân bằng dấu phẩy (`2,0`), Edge hiển thị rỗng. Sửa template bằng `unlocalize`, khởi động lại server và xác nhận Edge có `value=2.0`, bốn ô còn lại `0.0`. Nút Xóa mở JavaScript `confirm()`, nhưng công cụ điều khiển Edge timeout khi chấp nhận hộp thoại qua hai lần thử; không tuyên bố thao tác xóa bằng Edge đã đạt. Thay vào đó POST xóa qua Django Client có CSRF trên bản sao trả 302, SQL xác nhận xóa mềm và Edge sau tải lại không còn dòng.
3. Nhân viên gửi đơn phép năm giả 2 ngày trên Edge, thấy Pending và quỹ phép chờ duyệt 2; đăng nhập HR giả và duyệt trên Edge. SQL xác nhận Approved và đúng 1 bản ghi duyệt. Không thao tác trên đơn nghiệp vụ gốc.

**Sửa mã và kiểm tra:** `src/apps/portal/templates/portal/timesheet_month.html` dùng `unlocalize` cho 5 giá trị số; `src/apps/portal/tests_business_scenarios.py` thêm assertion HTML `value="2.0"`. Lần chạy SQL Server đầu tiên phát hiện 314 test, 20 lỗi dây chuyền vì `response.close()` trong một `TestCase` bảo mật phát tín hiệu `request_finished` và đóng kết nối SQL đang trong transaction. `src/apps/security/tests_data_protection.py` chỉ đóng các resource closer của response để giải phóng tệp mà không đóng kết nối; ca đơn lẻ đạt sau sửa. Lệnh cuối `venv\Scripts\python.exe ops\run_tests.py --backend sqlserver` với `DB_NAME=qlhcns_codex_uat_20261002`: **314/314 đạt**, exit 0, 290,589 giây; runner tạo/xóa database test tạm, không dùng DB gốc để ghi. Cả ba kịch bản HTTP báo PASS. `git diff --check` đạt. Không sửa model hay migration.

**Dọn dẹp/giới hạn:** đã dừng server UAT, xác nhận cổng 8765 không còn lắng nghe; xóa database bản sao và 6 tệp media sao chép sau khi kiểm thử, xác nhận DB gốc còn tồn tại và không còn database `test_ihrms_*`. Tệp backup `C:\Program Files\Microsoft SQL Server\MSSQL16.SQLEXPRESS\MSSQL\DATA\qlhcns_codex_uat_20261002.bak` còn nằm trong thư mục SQL Server vì tiến trình hiện tại bị từ chối quyền xóa; tệp này chứa bản sao dữ liệu và không thuộc Git. Người quản trị máy cần mở PowerShell **Run as administrator**, xác minh đúng đường dẫn/tên tệp rồi chạy `Remove-Item -LiteralPath 'C:\Program Files\Microsoft SQL Server\MSSQL16.SQLEXPRESS\MSSQL\DATA\qlhcns_codex_uat_20261002.bak'`; nếu vẫn bị từ chối, DBA dùng tài khoản có quyền với thư mục SQL DATA để xóa chính tệp đó. Nếu cần nghiệm thu nút Xóa hoàn toàn trên Edge, dựng lại DB SIT cô lập với dữ liệu giả, bấm Xóa và chấp nhận `confirm()`, rồi kiểm tra dòng biến mất; công cụ lần này không xử lý được hộp thoại. Chưa kiểm tra đồng thời/race, IIS hoặc SharePoint thật và chưa triển khai production.

**Git:** làm trên `main`; các sửa đổi mã và mục nhật ký này còn ở working tree, chưa commit/push. Log kiểm thử tổng hợp nằm ngoài repo tại `D:\QLHCNS-Backups\codex-uat-20261002-final-sql-tests.log`.

## 02/10/2026 — Đẩy kết quả UAT và chặn số tiền âm trong bảng lương

**Mục tiêu/phạm vi:** theo yêu cầu tiếp tục trên `main`, commit/push kết quả UAT trước rồi rà soát, sửa lỗi có thể tái hiện. Đã đọc `AGENTS.md` và nhật ký, `git fetch origin main` xác nhận local và `origin/main` cùng ở `2cc0e3b`, giữ nguyên bốn tệp thay đổi từ đợt UAT. Không ghi dữ liệu lên database nghiệp vụ gốc.

**Git đợt UAT:** `git diff --cached --check` đạt; commit `65f9ca6aceb5bfa7251e7c1b4fd305c7b98c340e` (`fix: stabilize SQL Server test and timesheet number inputs`) gồm template chấm công, hai tệp kiểm thử và nhật ký đợt trước; `git push origin main` thành công, fetch lại xác nhận `main` khớp `origin/main`, working tree sạch trước khi sửa tiếp.

**Lỗi tái hiện và sửa:** báo cáo review cũ có nhiều mục đã được sửa trong mã hiện tại. Mục tiền nhập tay âm còn tái hiện: `Payroll.full_clean()` cho qua sáu trường tiền âm, `EmployeeSalary.full_clean()` cho qua lương cơ bản âm. Đã chạy ca kiểm thử mới trước sửa và thấy 7 subtest thất bại đúng lỗi. Trong `src/apps/payroll/models.py`, thêm kiểm tra số tiền không âm cho sáu trường nhập `Payroll` khi `full_clean()` và trước `calculate()`, cùng kiểm tra `EmployeeSalary.current_basic_salary`; `src/apps/payroll/tests.py` thêm ca hồi quy. Kiểm tra chỉ đọc trên database gốc cho thấy sáu trường `Payroll` không có giá trị âm. Không thêm migration hay thay đổi công thức tính. Bản sửa thử đầu tiên còn chặn mức miễn thuế tăng ca nhập lớn hơn tiền tăng ca; SQL Server test hiện hữu chỉ ra quy tắc đang dùng là lấy mức nhỏ hơn khi tính, nên đã bỏ phần chặn đó và giữ nguyên quy tắc nghiệp vụ.

**Kiểm tra sau sửa:** `venv\Scripts\python.exe src\manage.py check`: 0 lỗi; `venv\Scripts\python.exe src\manage.py makemigrations --check --dry-run`: No changes detected; `git diff --check`: đạt. `venv\Scripts\python.exe ops\run_tests.py --backend sqlite`: 317 test, 315 đạt, 2 bỏ qua vì cần SQL Server, exit 0; cả 3 tình huống HTTP PASS. `venv\Scripts\python.exe ops\run_tests.py --backend sqlserver`: 317/317 đạt, exit 0, database test SQL Server tạm do runner tạo và xóa; cả 3 tình huống HTTP PASS. Không dùng test này để tuyên bố đã thao tác nút xác nhận xóa trên Edge.

**Việc còn mở:** chưa xác nhận toàn bộ lỗi thiết kế/hiệu năng trong báo cáo review cũ đã hết; chưa thử race thực tế, IIS/SharePoint production và hộp thoại `confirm()` của nút Xóa trên Edge. Tệp backup SQL của đợt UAT còn cần người quản trị xóa theo đường dẫn và lệnh ở mục ngay trên; không đưa tệp đó vào Git. Không chạy migration hoặc triển khai production trên database gốc. Mã sửa đã được commit/push trên `main` ở `447508a389da49d4110f7c674b32a33dbc80b442`; fetch lại xác nhận remote trùng local. Lệnh `gh run list --commit 447508a389da49d4110f7c674b32a33dbc80b442` bị GitHub API trả 401 Bad credentials, nên chưa xác nhận CI của commit này; người phụ trách mở GitHub Actions của commit trên bằng tài khoản có quyền, đối chiếu trạng thái backend/frontend/backup-command-tests và cung cấp log nếu job lỗi.

## 05/10/2026 — Khôi phục đăng nhập SQL Server và sửa trạng thái đặt xe trên main

**Mục tiêu/phạm vi:** xử lý lỗi POST `/portal/login/` báo thiếu `axes_accessattempt`, rà các migration đang chờ và lỗi chức năng xác nhận được khi review. Xác nhận `main` khớp `origin/main` sau `git fetch origin main`; giữ nguyên `.sixth/` và `_review_probe.py` chưa được theo dõi.

**Nguyên nhân và sao lưu:** kiểm tra chỉ đọc trên SQL Server đang cấu hình cho thấy bảng `axes_accessattempt` chưa có và 0/10 migration Axes đã áp dụng; `security.0003` tạo `tblSecurityEvent` cũng còn chờ, trong khi signal đăng nhập ghi vào bảng đó. Tạo backup COPY_ONLY/CHECKSUM tại `C:\Program Files\Microsoft SQL Server\MSSQL16.SQLEXPRESS\MSSQL\Backup\ihrms_before_axes_20261005_103326_21d08a48.bak`; `RESTORE VERIFYONLY WITH CHECKSUM` đạt. Backup chứa dữ liệu nghiệp vụ, ở ngoài Git và cần giữ theo chính sách lưu trữ/khôi phục của quản trị SQL Server.

**Đã làm trên SQL Server gốc:** chạy `venv\Scripts\python.exe src\manage.py migrate axes --noinput` (10/10 OK), `migrate security --noinput` (security.0003 OK), rồi `migrate --noinput` (attendance.0008, office.0005 và .0006, payroll.0004 đều OK). Trước khi áp dụng các ràng buộc nghiệp vụ, `audit_review_integrity` chỉ đọc báo 0 sai lệch ở cả 5 nhóm; sau migration vẫn 0. `migrate --plan` không còn thao tác; `manage.py check` đạt; `makemigrations --check --dry-run` báo No changes detected. Không tạo/xóa bản ghi nghiệp vụ gốc để thử nghiệm.

**Sửa mã:** `VehicleBooking` trước đây chỉ cho `Approved`/`Cancelled`, nhưng form tạo gửi `Pending` và luồng duyệt có `Rejected`; mọi yêu cầu mới bị `full_clean()` từ chối. Bổ sung bốn trạng thái hợp lệ, mặc định `Pending`, migration `office.0006`, và hai kiểm thử tổng hợp cho model/HTTP tạo yêu cầu. Kiểm thử riêng `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.office.tests` và `--backend sqlserver apps.office.tests`: mỗi backend 8/8 đạt, SQL Server dùng database thử tạm. `pip check` không có dependency hỏng; `git diff --check` đạt.

**Kiểm thử toàn bộ:** `venv\Scripts\python.exe ops\run_tests.py --backend sqlite`: 319 test, 317 đạt, 2 bỏ qua do chỉ dành SQL Server, exit 0; log `D:\QLHCNS-Backups\review-20261005-full-sqlite.log`. `venv\Scripts\python.exe ops\run_tests.py --backend sqlserver`: 319/319 đạt, exit 0 trên database tạm do runner tạo/xóa; log `D:\QLHCNS-Backups\review-20261005-full-sqlserver.log`. Cả ba kịch bản HTTP HR, chấm công và nghỉ phép PASS trên hai backend. Log có cảnh báo cấu hình Jazzmin `dark_mode_theme` đã deprecated, không làm test thất bại. Bugbot không khả dụng trong môi trường công cụ hiện tại; review mã và luồng liên quan được thực hiện thủ công.

**Việc còn mở/hành động của chủ dự án:** sau khi cập nhật mã lên máy đang chạy, dùng tài khoản thử để xác nhận đăng nhập và tạo/duyệt/từ chối đặt xe qua trình duyệt; đối chiếu với kết quả HTTP tự động. Chưa kiểm thử giao diện Edge trong lượt này hoặc mọi lỗi thiết kế/hiệu năng của toàn dự án. Backup SQL ở đường dẫn trên cần DBA giữ/luân chuyển theo quy định; không đưa vào Git. `gh run list --commit 6429d2f8769b58f41c4900358508515600eb65d9 --limit 10` trả HTTP 401 Bad credentials; chủ dự án mở GitHub Actions của commit này bằng tài khoản có quyền, đối chiếu các job và cung cấp log nếu job lỗi. Không ghi CI là đạt khi chưa xem được kết quả.

**Nhánh/commit:** mã sửa ở `main` commit `6429d2f8769b58f41c4900358508515600eb65d9`; `git push origin main` thành công và `git fetch origin main` xác nhận local/remote trùng nhau tại commit đó. Mục nhật ký này được commit riêng trong cùng đợt.

## 05/10/2026 — Sửa GitHub Actions frontend và kiểm tra lại toàn bộ trên main

**Mục tiêu/phạm vi:** theo yêu cầu chạy lại kiểm thử và làm GitHub Actions hết lỗi trên `main`. Đầu đợt xác nhận local `main` khớp `origin/main` tại `e652db0`, chỉ có `.sixth/` và `_review_probe.py` chưa theo dõi; giữ nguyên hai mục đó. Skill `review-bugbot` yêu cầu subagent loại `bugbot`, nhưng môi trường công cụ không cung cấp loại này; review thủ công các thay đổi và luồng CI, không ghi nhận là Bugbot đã chạy.

**Nguyên nhân CI đã xác nhận:** mở GitHub Actions bằng Edge có phiên đăng nhập, run #9 của commit `e652db0` thất bại ở job `frontend`, còn `backend` và `backup-command-tests` đạt. Log `npm audit --audit-level=low` báo 5 cảnh báo high do `braces` trong cây Tailwind CSS 3.4.17; advisory GHSA-vfj7-8cjw-p6xm chưa có bản vá cho `braces` 3.x. `gh auth status` xác nhận token CLI trong keyring không hợp lệ; trạng thái CI được đọc trên trang GitHub, không suy từ CLI.

**Thay đổi:** nâng Tailwind và CLI lên 4.3.0 pin chính xác, lockfile sử dụng `@parcel/watcher` 2.6.0 không còn cây `braces`; chuyển CSS đầu vào sang `@import`/`@source` của Tailwind 4, build lại CSS và bỏ cấu hình v3 không còn dùng. Cập nhật hướng dẫn frontend. CI nâng `actions/setup-node` từ v4 lên v6 để bỏ cảnh báo runtime Node 20. Bộ thử backup chọn đúng shell của môi trường hiện tại (`powershell.exe` trên Windows PowerShell, `pwsh` trên PowerShell Core); kịch bản Failure trước đó không chạy được ở máy Windows này.

**Kiểm tra đã chạy:** `npm ci`, `npm audit --audit-level=low` (0 vulnerability), `npm run build:css` đều exit 0. Đối chiếu selector CSS: 417 selector lớp có trong template và CSS v3 đều hiện diện sau build v4; kiểm tra này không thay thế xác nhận bố cục trình duyệt. `python -m pip check`, `python -m pip_audit -r requirements.txt` (No known vulnerabilities found), `manage.py check`, `makemigrations --check --dry-run` đạt. Cả 6 kịch bản mô phỏng `ops/backup/Test-BackupSafety.ps1` (Full/Log × Express/Standard/Failure) PASS; không kiểm thử backup/restore SQL thật bằng bộ này.

**Kiểm thử toàn bộ và CI mới:** `venv\Scripts\python.exe ops\run_tests.py --backend sqlite`: 319 test, 317 đạt, 2 bỏ qua do dành riêng SQL Server, exit 0; log `D:\QLHCNS-Backups\review-20261005-ci-sqlite.log`. `venv\Scripts\python.exe ops\run_tests.py --backend sqlserver`: 319/319 đạt, exit 0; log `D:\QLHCNS-Backups\review-20261005-ci-sqlserver.log`. Cả ba kịch bản HTTP HR, chấm công, nghỉ phép PASS trên hai backend; runner đã xóa database SQL Server tạm, kiểm tra chỉ đọc xác nhận còn 0 database `test_ihrms_%`. Có cảnh báo Jazzmin `dark_mode_theme` deprecated trong log, không làm test thất bại. Đã xác nhận trực tiếp trên Edge [GitHub Actions run #11](https://github.com/dinhtanhb/QLHCNS/actions/runs/37261635104) của commit `39f132e023b5d5c9360cb1689c8b224849cb00a7`: Status Success; backend, frontend và backup-command-tests đều thành công, không có annotation error/warning; còn 3 notice về lịch chuyển ubuntu-latest sang Ubuntu 26.

**Nhánh/commit và việc còn mở:** `main`, mã sửa ở `39f132e023b5d5c9360cb1689c8b224849cb00a7`, đã push và fetch xác nhận origin/main khớp local. Commit trung gian `e0e8fa8` chỉ xóa cấu hình v3 do lệnh stage gặp pathspec của tệp đã xóa; các thay đổi còn lại đã được đưa ngay vào commit kế tiếp `39f132e`. Run #10 của commit trung gian đã lỗi frontend và được yêu cầu hủy để giải phóng hàng đợi cho run #11; không coi run trung gian là kết quả nghiệm thu. Chưa kiểm thử trực quan bố cục Edge sau nâng Tailwind, chưa xác nhận production IIS/SharePoint. Chủ dự án cần chạy `npm ci`, `npm run build:css`, rồi `venv\Scripts\python.exe src\manage.py collectstatic --noinput` theo quy trình triển khai trên máy chủ và kiểm tra bố cục các màn hình đang dùng; việc collectstatic/triển khai production không nằm trong đợt kiểm thử này.

## 05/10/2026 — Chuẩn hóa reviewer Sixth và hướng dẫn review dùng lại

**Mục tiêu/phạm vi:** đánh giá `.sixth/agents/code-review.md` và cập nhật hướng dẫn theo yêu cầu chủ dự án. `git status`, nhánh và `git fetch origin main` xác nhận `main` ở `164ffd30bc973b40cf4ca68ab6dfa9aa1a1738d8`, khớp remote (ahead/behind 0/0). Ban đầu `.sixth/` và `_review_probe.py` chưa theo dõi. Chỉ sửa file reviewer được yêu cầu; không sửa probe. `code-reviewr.md` không tồn tại trên đĩa dù người dùng đang có tab IDE tương ứng.

**Đánh giá và thay đổi:** reviewer cũ có quy trình đọc caller/test và xác minh finding phù hợp, nhưng chủ yếu review diff sau tính năng, thiếu quy tắc IHRMS, bảo vệ dữ liệu, hai backend và xác nhận CI. Đã sao lưu bản gốc ngoài Git tại `D:\QLHCNS-Backups\review-agent-guide-20261005`. Cập nhật reviewer với FULL/CHANGES và REVIEW/FIX, checklist luồng nghiệp vụ, main, dữ liệu giả/DB-media cô lập, bằng chứng finding, quyền sửa/commit/push theo nhiệm vụ và cách báo phần chưa kiểm thử. Tạo `docs/Huong_Dan_Review_Du_An.md` có mẫu yêu cầu cho Sixth hoặc thực hiện trực tiếp, các lệnh chuẩn, điều kiện hoàn tất và giới hạn Bugbot. README/AGENTS chỉ liên kết tới hướng dẫn; nhật ký đợt chỉ ghi tại đây.

**Kiểm tra thực tế:** đối chiếu mã extension Sixth AI 0.3.7 đang cài, xác nhận loader `.sixth/agents`, schema permissions, trust prompt và công cụ `launch_agent`; agent nền nhận task riêng, không nhận toàn bộ chat. Dùng Node VM chỉ chạy hàm parser `x0r` trích từ extension (không khởi động extension): file mới được nhận là `code-review`, source project, đủ 6 quyền bao gồm read mặc định. Python kiểm tra liên kết local, UTF-8 và code fence của bốn file hướng dẫn: PASS. `git diff --check`: exit 0. Đối chiếu lệnh với `ops/run_tests.py`, `ops/Run-Tests.ps1` và `.github/workflows/ci.yml`; không chạy full suite/build/audit mới vì đợt này chỉ sửa hướng dẫn, không sửa ứng dụng, dependency hoặc workflow.

**Việc còn mở/bàn giao:** chưa thử gọi agent Sixth qua UI nên không coi parser PASS là run review đã thành công. Chủ dự án mở Sixth AI trong workspace, dùng mẫu FULL/REVIEW ở hướng dẫn, yêu cầu agent `code-review`, xử lý trust prompt nếu xuất hiện rồi xác nhận có run riêng/kết quả. Nếu không có agent Sixth trong công cụ đang dùng, đính kèm hai file và yêu cầu review trực tiếp; ghi đúng cách đã thực hiện. Không áp dụng migration hay ghi dữ liệu nghiệp vụ trong đợt này.

**Git trong lượt tiếp tục:** chủ dự án yêu cầu commit/push toàn bộ. Fetch lại xác nhận main không phân kỳ với origin/main. Kiểm tra toàn bộ tệp mới: chỉ có reviewer, hướng dẫn và `_review_probe.py`; probe dùng cấu hình test/SQLite, khóa mẫu riêng cho probe và instance giả, không gọi save. Chạy `venv\Scripts\python.exe _review_probe.py` lần đầu lỗi encoding cp1252; chạy lại với `PYTHONIOENCODING=utf-8` hiển thị đủ trạng thái rồi exit 1 vì `clean_fields()` kiểm tra FK trên SQLite thiếu bảng `tblVehicle`. Không ghi probe đạt và không migrate/tạo fixture trên DB cấu hình để chữa lỗi này. Giữ probe nguyên trạng theo yêu cầu đưa toàn bộ lên Git; nếu cần chạy lại độc lập, phải có SQLite cô lập đã migrate và fixture giả tương ứng hoặc chuyển probe thành test dùng runner chuẩn. Không đưa .env, DB, backup hoặc dữ liệu thật. SHA commit và đối chiếu remote sau push được báo trong kết quả bàn giao.

## 2026-10-06 — Layout và export bộ biểu mẫu HCNS

**Mục tiêu/phạm vi:** tham khảo 26 tệp chủ dự án đã đặt tại `docs/templates/hcns/`; xây dựng màn hình soạn, xem trước/in và export tương ứng. Chỉ làm trên `main`; đầu đợt working tree có thư mục mẫu chưa theo dõi, `git fetch origin main` và `git rev-list --left-right --count HEAD...origin/main` xác nhận `0 0`. Không sửa các tệp mẫu gốc, không đưa chúng vào commit, không ghi bản ghi nghiệp vụ thật.

**Đã làm:** thêm `src/apps/document/hcns/` (catalog 26 layout, nội dung mẫu trắng trích chọn, form/formset validation, prefill theo quyền, render, DOCX/XLSX export và views); ba template tại `src/apps/document/templates/document/hcns/`; CSS/JS riêng; `src/apps/document/tests_hcns.py`. Thêm `/portal/hcns-forms/` và menu Biểu mẫu HCNS; nối liên kết ở chi tiết nhân viên, ứng viên, đơn nghỉ, hồ sơ vòng đời, kiểm kê, đề nghị thanh lý và danh sách lương cơ bản. Thêm `docs/Huong_Dan_Bieu_Mau_HCNS.md` hướng dẫn sử dụng; kết quả chỉ ghi tại mục nhật ký này.

**Nội dung và quy tắc:** Word cho hồ sơ/văn bản, Excel cho thang bảng lương, bảng kiểm bàn giao, tổng hợp điểm tuyển dụng và kiểm kê/nhãn tài sản. PDF qua hộp thoại in của trình duyệt, không thêm dịch vụ chuyển đổi phía máy chủ. Giữ 60 tiêu chí đánh giá, 12 câu hỏi phỏng vấn thôi việc và bốn TOR; không đưa dòng nhân viên/ứng viên/tài sản đã điền hoặc chữ ký trong mẫu gốc vào mã. `BangLuong.xlsx` là thang bảng lương chứa giá trị, không có công thức; không thay payroll. Chủ dự án **đã xác nhận trong chat** tính trung bình cả điểm phỏng vấn và điểm bài kiểm tra theo ứng viên; đã triển khai cho bản xem trước và công thức Excel. Điểm thiếu không thành 0; không tự ra kết quả tuyển dụng. Bảng kiểm nghỉ việc thay yêu cầu ghi password bằng xác nhận bàn giao quyền truy cập qua quy trình IT, không thu thập mật khẩu. Xuất kiểm kê `.xlsx` không macro; hồ sơ vượt giới hạn soạn được xem/xuất đầy đủ. Bản xuất là bản soạn thảo, không tự duyệt/gửi đơn/đổi lương/chấm dứt hợp đồng/thanh lý tài sản; không lưu draft vào DB. Layout bám cấu trúc và nội dung mẫu, không cam kết sao chép nguyên từng pixel hoặc giữ logo, ảnh và chữ ký của tệp gốc.

**Quyền và bảo vệ dữ liệu:** login và quyền kiểm tra tại máy chủ; employee prefill yêu cầu chính chủ hoặc cả quyền xem toàn bộ + xuất dữ liệu nhân sự; tuyển dụng yêu cầu HR; lương/quyết định dùng quyền nghiệp vụ tương ứng; asset/leave áp dụng quyền/phạm vi hiện có. Không cấp quyền nhân sự bằng `is_staff`. Loại nghỉ phải khớp mẫu `AL/UL/CO`, hồ sơ xóa bị loại. Văn bản HTML escape, chuỗi Excel được lưu kiểu text để chặn formula injection, tiêu chí/nhãn cố định do máy chủ quyết định, giới hạn số dòng và điểm. Audit chỉ ghi loại mẫu; trang/export `never_cache`; dữ liệu nguồn không hợp lệ báo lỗi an toàn.

**Kiểm tra đã chạy:**

- `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.document.tests_hcns`: bản cuối đạt **9/9**, exit 0; gồm cả 26 GET layout/POST export, đăng nhập/quyền và phạm vi hồ sơ, dữ liệu nhập, điểm thiếu/0, chống tamper/XSS/formula injection, kiểm kê 51 dòng không cắt dữ liệu, xử lý nguồn lỗi. DB/media do runner cô lập.
- `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.document apps.portal apps.lifecycle apps.reporting apps.security.tests_data_protection`: **136 ca, 135 đạt, 1 skip**, exit 0. Ca skip tại `src/apps/portal/tests_review_hardening.py` yêu cầu SQL Server row locking. Bộ hồi quy này chạy trước các tinh chỉnh cuối về khoảng cách in, công thức kiểm tra điểm thiếu và nguồn dữ liệu lỗi; đã chạy lại bộ HCNS tập trung trên mã cuối.
- SQL Server: `venv\Scripts\python.exe ops\run_tests.py --backend sqlserver apps.document.tests_hcns`; bản cuối đạt **9/9**, exit 0; runner tạo DB `test_ihrms_<UUID>` riêng và xóa sau khi chạy. Trước khi bổ sung ca nguồn lỗi cũng đã đạt 8/8; không dùng kết quả cũ thay cho lần xác nhận mã cuối.
- `manage.py check` và `manage.py makemigrations --check --dry-run` với `DB_ENGINE=django.db.backends.sqlite3`, `DB_NAME` trỏ tới tệp SQLite tạm ngoài repo, `SECRET_KEY` tạm và `APP_ENV=test`: exit 0, không có lỗi framework và không có migration mới. Lần cấu hình kiểm tra ban đầu tạo tệp rỗng `src/qlhcns` do tên DB kế thừa cấu hình; đã xác minh tệp 0 byte sinh trong đợt này và xóa riêng tệp đó. Thử `DB_NAME=:memory:` qua settings hiện tại báo đường dẫn không mở được trên Windows; đã chuyển sang đường dẫn tuyệt đối tạm và chạy lại đạt. Không migrate DB thật.
- Edge headless qua Playwright trên **26 HTML editor đã render cô lập**, viewport 1280×900 và 375×812: không tràn ngang trang; thêm/xóa dòng, đánh lại chỉ số formset, chặn in preview cũ và ẩn editor khi in đạt. Đây là kiểm tra HTML/JS/static; không phải browser UAT đăng nhập trên ứng dụng đang dùng.
- Xuất 26 tệp bằng dữ liệu giả vào `%TEMP%`, mở/chuyển PDF bằng LibreOffice và render trang PNG bằng Poppler; kiểm tra bố cục, chỉnh vùng ký tránh trang riêng, mở rộng tiêu đề/cột Excel. Đã chạy `render_docx.py` với mẫu đơn nghỉ để xác minh renderer; các mẫu còn lại render trực tiếp qua LibreOffice/Poppler. Trang quyết định, đơn nghỉ, bàn giao và phiếu phỏng vấn mẫu trắng gọn trên một trang; đánh giá/TOR nhiều trang. Không kết luận dữ liệu dài bất kỳ sẽ có cùng số trang.
- Hai workbook điểm giả được LibreOffice tính lại, rồi đọc cached values bằng `openpyxl`: trường hợp 10 và 0 cho TB phỏng vấn=30, TB kiểm tra=10, tổng=40; thiếu một điểm kiểm tra cho TB kiểm tra/tổng trống. Không có ô lỗi công thức. Không xác nhận engine Microsoft Excel thật.
- `git diff --check` đạt. Nội dung JSON trích chọn không có email, chuỗi định danh dài hoặc nhãn password; các tệp gốc vẫn chưa theo dõi. Không tăng dependency, không migration schema, không commit/push/deploy trong nhiệm vụ này.

**Vòng test/fix/review theo ủy quyền tiếp tục của chủ dự án:** review trực tiếp phạm vi CHANGES/FIX cho bộ biểu mẫu và caller, không ghi nhận đã chạy Sixth/Bugbot hoặc review FULL mọi dòng mã. Sửa bốn trường hợp đã xác nhận: dòng chỉ có số 0 bị loại do so sánh với `False`; nguồn chưa kiểm tra quan hệ ngày/giờ bắt đầu-kết thúc; đơn nghỉ thường được dùng điền quyết định thai sản; ký tự XML cấm `U+FFFE/U+FFFF` có thể làm DOCX không đọc được. Bổ sung kiểm thử hồi quy, chặn nguồn không khớp `ML`, cập nhật hướng dẫn quyền/nguồn và build lại `src/static/css/tailwind.css`. Một assertion mới ban đầu tìm lý do nghỉ trong quyết định thai sản, trong khi mẫu chỉ có nhân viên và khoảng ngày; đã sửa assertion theo trường thực tế rồi chạy lại, không thay nội dung mẫu để làm test đạt.

**Xác minh bổ sung:** `pip check`, `npm run build:css`, `manage.py check`, `makemigrations --check --dry-run` trên SQLite tạm đều exit 0; không phát sinh migration. Bộ HCNS SQLite trên mã cuối **11/11 đạt**. Chạy lại QA static Edge sau build: 26 mẫu ở desktop/mobile, thêm/xóa/đánh lại chỉ số dòng, chặn nút in preview cũ và ẩn editor khi in đều đạt. Thêm kiểm tra **Edge có đăng nhập trên StaticLiveServerTestCase với DB/media giả cô lập**: cả 26 mẫu GET → POST preview → POST tải tệp thành công; thêm/xóa dòng tài sản và dữ liệu preview qua HTTP đúng; khoảng ngày sai trả 422; POST thiếu CSRF trả 403; không có lỗi JavaScript. Lệnh harness: `$env:PYTHONPATH=Join-Path $env:TEMP 'ihrms-hcns-layout-20261006'; venv\Scripts\python.exe ops\run_tests.py --backend sqlite live_browser_tests` (harness `live_browser_tests.py`/`live_browser.cjs` nằm ngoài repo tại thư mục tạm này, cần giữ chúng hoặc tái tạo trước khi chạy lại). Log và 26 tệp tải giả ở cùng thư mục tạm. Microsoft Word mở read-only được **22/22 DOCX**, Microsoft Excel mở và calculate read-only được **4/4 XLSX**; không sửa/lưu mẫu gốc. Excel thật tính hai workbook điểm giả: đủ điểm/0 → 30,10,40; thiếu điểm → 30,trống,trống, đúng kỳ vọng. Đây là kiểm tra Office bằng COM, chưa thay thế kiểm tra trình bày bằng mắt của người sử dụng.

**Còn mở và bước chủ dự án thực hiện:** mở `Biểu mẫu HCNS` trong menu ứng dụng, thử 2–3 hồ sơ với tài khoản HR/Kế toán/nhân viên phù hợp; chọn mẫu → nhập → cập nhật preview → tải Word/Excel hoặc In/lưu PDF. Nhập phần chưa có trong DB (quốc tịch, trình độ, tài khoản ngân hàng, người nhận bàn giao, căn cứ, nội dung quyết định...). Kiểm tra nội dung, căn cứ/thẩm quyền ký, địa bàn/dự án trong TOR và trình bày bằng Microsoft Word/Excel trước khi ký. Chưa chạy UAT trên dữ liệu thật, chưa kiểm tra M365/IIS/deploy/CI; chưa có lưu draft, ký số hoặc điền tự động theo bản ghi quyết định/lịch sử lương. Khi sửa/thêm nhóm người chấm trong Excel cần xuất lại từ trang soạn để cập nhật công thức nhóm. Không dùng bộ mẫu này để tự suy diễn biểu mẫu BHXH/TNCN chưa được Kế toán xác nhận. Không cam kết không còn lỗi chỉ từ tỷ lệ test đạt. Không commit/push/deploy trong vòng tiếp tục này.

**Hồi quy toàn dự án trong vòng tiếp tục:** `venv\Scripts\python.exe ops\run_tests.py --backend sqlite`: **328 ca, 326 đạt, 2 skip**, exit 0 (419,456 giây); `--backend sqlserver`: **330/330 đạt**, exit 0 (388,160 giây), runner đã xóa DB tạm sau chạy. Hai skip SQLite là kiểm tra row locking (`portal/tests_review_hardening.py:276`) và unique index với NULL (`planning/tests.py:67`), đều được chạy trên SQL Server. Ba kịch bản HTTP nhân sự/chấm công/nghỉ phép PASS trên cả hai backend. Hai bộ bắt đầu trước các thay đổi cuối; SQLite phát hiện 9 ca HCNS, SQL Server phát hiện 11. Sau tinh chỉnh ký tự XML và bổ sung assertion nguồn ML đã chạy lại bộ HCNS trên mã cuối, không dùng kết quả full cũ thay cho xác nhận thay đổi cuối. Log ngoài Git: `%TEMP%\ihrms-hcns-layout-20261006\full-sqlite-review.log`, `full-sqlserver-review.log`, `focused-final.log`, `live-browser.log`; cảnh báo Jazzmin deprecated đã tồn tại, không phải lỗi test. Không có test thất bại trong hai bộ hồi quy.

**Chốt mã cuối:** `venv\Scripts\python.exe ops\run_tests.py --backend sqlserver apps.document.tests_hcns`: **11/11 đạt**, exit 0; log `focused-sqlserver-final.log` cùng thư mục tạm, DB thử riêng đã bị runner xóa. Truy vấn chỉ đọc `SELECT COUNT(*) FROM sys.databases WHERE name LIKE 'test[_]ihrms[_]%'` xác nhận còn **0** DB thử. Như vậy bộ HCNS cuối đạt 11/11 trên cả hai backend; review lại không còn finding đã xác nhận chưa xử lý trong phạm vi này. `git diff --check` đạt; nhánh vẫn `main`, đối chiếu HEAD/origin/main `0 0`, thay đổi chưa commit được giữ nguyên. Chưa có bằng chứng CI cho mã chưa commit và không suy diễn CI là đạt.

## 2026-10-06 — Đặt cổng phát triển mặc định QLHCNS là 8001

**Mục tiêu/phạm vi:** theo yêu cầu chủ dự án, tránh mở nhầm `nhaplieu_app` đang giữ cổng 8000. Xác nhận `main`, giữ toàn bộ thay đổi HCNS chưa commit; `git fetch origin main` và đối chiếu HEAD/origin/main đạt `0 0`.

**Đã làm:** thêm command `src/apps/common/management/commands/runserver.py`, kế thừa command staticfiles của Django và đặt `default_port = "8001"`. Đưa `apps.common` trước `django.contrib.staticfiles` trong `src/config/settings.py` để Django chọn command riêng. Cập nhật URL và cách chọn cổng khác trong README. Lệnh `venv\Scripts\python.exe src\manage.py runserver` dùng `127.0.0.1:8001`; tham số cổng/địa chỉ rõ ràng vẫn được ưu tiên.

**Kiểm tra/kết quả:** chạy Python với cấu hình SQLite tạm/APP_ENV=test, xác nhận command resolver chọn `apps.common`; dùng parser và `handle()` thật, mock riêng `run()` để không mở server hay ghi DB: không truyền cổng → 127.0.0.1:8001, truyền 8002 → 127.0.0.1:8002, truyền 127.0.0.1:8010 → đúng địa chỉ/cổng, cả ba PASS; tùy chọn staticfiles vẫn hiện diện. `venv\Scripts\python.exe src\manage.py check` trên cấu hình tạm: exit 0, không có lỗi. `git diff --check` đạt. Không chạy lại full-suite vì thay đổi chỉ là cổng phát triển và đã kiểm tra đúng luồng command; không dùng kết quả full-suite HCNS trước đó để tuyên bố đã chạy lại sau thay đổi này.

**Bàn giao:** chủ dự án dừng và khởi động lại tiến trình QLHCNS bằng lệnh trên rồi mở http://127.0.0.1:8001/portal/. Tiến trình đang chạy không tự đổi cổng; nếu lệnh khởi động có cổng 8000 explicit thì bỏ tham số hoặc đổi thành 8001. Chưa mở server thực tế trong lượt này, không dừng nhaplieu_app, không sửa cấu hình IIS/Waitress hay dữ liệu nghiệp vụ, không commit/push.

## 2026-10-06 — Sửa UAT quyết định tiếp nhận/bổ nhiệm/miễn nhiệm

**Mục tiêu/phạm vi:** theo phản hồi và ảnh chụp của chủ dự án, thay ô nhập danh mục bằng dropdown, tự điền chức vụ/phòng ban theo cán bộ, tự đổi lương thành chữ và sửa layout theo `VH_QD bo nhiem, mien nhiem.doc`. Đầu đợt xác nhận `main`, `git fetch origin main`/HEAD đối chiếu remote `0 0`; giữ toàn bộ phần HCNS/cổng 8001 chưa commit. Review trực tiếp CHANGES/FIX trong phạm vi này.

**Đã làm:** thêm `hcns/appointment.py` với danh sách chọn và bố cục riêng; `hcns/money.py` đọc tiền Việt; cập nhật catalog/form/prefill/view/render/export, thêm template `appointment_document.html`, sửa template draft/document và CSS/JS HCNS. Họ tên/người ký lấy hồ sơ chưa xóa, nhãn gồm tên/mã/chức vụ; danh sách cán bộ theo chính chủ hoặc cả quyền xem toàn bộ và xuất nhân sự, không mở quyền mới. ModelChoiceField kiểm tra ID ở máy chủ, từ chối ID không tồn tại/đã xóa và chuỗi tùy ý. Chọn cán bộ tự điền vị trí/phòng ban bằng JS; máy chủ bổ sung từ hồ sơ khi để trống, cho phép chọn lại danh mục và chức vụ mới. Dữ liệu JSON chỉ có ID cán bộ/vị trí/phòng ban; truy vấn danh sách chỉ lấy các trường cần dùng, không gửi CCCD/email/lương. Source label theo cán bộ được chọn trên POST, tránh giữ nhãn người cũ.

**Tiền và nội dung:** nhập số đồng nguyên, lương bằng chữ tự cập nhật tại client và được tính lại ở server, field disabled/readonly không nhận nội dung bằng chữ do POST giả mạo. Quy tắc áp dụng cả quyết định điều chỉnh lương có cùng trường; điểm tuyển dụng và bảng lương không bị đổi. Lương trống giữ trống, 0 là “Không đồng chẵn”; xử lý nhóm nghìn/triệu/tỷ, lăm/mốt/linh. Lần thử đầu phát hiện chỉ đổi thuộc tính decimal_places không thay validator cũ, khiến số lẻ lọt tới bộ đọc tiền; đã tạo DecimalField đồng nguyên đúng validator, bổ sung hồi quy rồi chạy lại đạt. Không đổi schema/điều chỉnh lương thật. Nội dung căn cứ và bốn điều của mẫu tiếp nhận được phục hồi từ phần mẫu trắng; không đưa tên/chữ ký/dòng ví dụ thật trên trang thứ hai vào mã. Tiêu đề V/v/Điều 1 mặc định theo hành động, nội dung tự sửa vẫn do người soạn kiểm tra trước ký.

**Layout:** tổ chức bên trái/quốc hiệu bên phải, số/ngày dưới từng khối; tiêu đề “QUYẾT ĐỊNH” 16pt và V/v 14pt; Times New Roman 12pt cho thân, căn cứ nghiêng/thụt dòng, nhãn Điều cùng dòng và thụt treo, nơi nhận trái/chữ ký phải và tên người ký dưới khoảng ký. A4, lề trái 25mm, trên/dưới/phải 20mm; Word và browser print cùng quy tắc. Giữ dòng cảnh báo bản soạn thảo như khác biệt có chủ ý. Không còn các nhãn “Nội dung căn cứ”, “Danh sách nơi nhận” hoặc metadata lặp trong bản in mẫu này. Các mẫu quyết định khác chưa thay layout trong lượt này. Cập nhật `docs/Huong_Dan_Bieu_Mau_HCNS.md` cùng đợt.

**Kiểm tra trên mã cuối:** `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.document.tests_hcns apps.portal.tests_mobile`: **19/19 đạt**; `--backend sqlserver apps.document.tests_hcns`: **14/14 đạt**, runner xóa DB/media thử riêng. Bộ HCNS riêng trước đó cũng đạt 14/14 trên SQLite. Bao gồm 26 layout/export, chọn/prefill cán bộ, export DOCX hai bảng header/footer, hành động miễn nhiệm, từ chối reference giả/xóa/số lẻ, chống sửa lương bằng chữ, các quy tắc tiền và hồi quy quyền/nguồn/điểm. `manage.py check`, `makemigrations --check --dry-run` với SQLite tạm: exit 0, không có migration. `git diff --check` đạt.

**Browser/Word QA:** harness ngoài repo `%TEMP%\ihrms-hcns-layout-20261006\live_browser_tests.py`/`live_browser.cjs`, chạy bằng `$env:PYTHONPATH=Join-Path $env:TEMP 'ihrms-hcns-layout-20261006'; venv\Scripts\python.exe ops\run_tests.py --backend sqlite live_browser_tests`, PASS. Edge có đăng nhập trên StaticLiveServerTestCase/DB giả: 26 mẫu POST preview/tải tệp; dropdown và auto vị trí/phòng ban, 9 trường hợp đọc tiền JS, giữ cán bộ/người ký/tiền sau POST, không tràn ngang mobile, in không editor, thiếu CSRF bị chặn và không lỗi JavaScript. Vòng browser đầu sau chỉnh layout/in chạy trước tinh chỉnh nhãn dropdown/truy vấn `.only`; vòng cuối bổ sung kiểm tra cache dưới đây. Renderer `render_docx.py` ban đầu không tìm thấy soffice trên PATH; bổ sung đường dẫn LibreOffice rồi chạy thành công. Render mẫu tham khảo, xuất tài liệu giả bằng mã hiện tại và render/đọc PNG Word, render/đọc PNG bản in browser: đều sạch, bản thử một trang. Không suy diễn mọi nội dung dài đều một trang. Artifact contract/PNG/PDF/log chỉ ở thư mục tạm, không đưa Git; log `appointment-final-regression.log`, `appointment-sqlserver-final.log`, `appointment-browser-final.log`. Chưa chạy lại full-suite toàn dự án sau sửa UAT này, không dùng số 330/330 cũ làm kết quả mã cuối.

**Chốt cache và danh mục nguồn:** service worker hiện dùng cache-first cho static nên chỉ tải lại trang có thể vẫn chạy CSS/JS cũ. Thêm phiên bản URL `?v=20261006-2` cho CSS/JS HCNS trong template draft/catalog; giữ phạm vi thay đổi tại biểu mẫu. Chạy lại harness Edge sau tinh chỉnh nhãn/truy vấn và version URL, chủ động đặt CSS ẩn preview/JS lỗi vào cache các URL HCNS cũ trong browser test cô lập: cả 26 mẫu, dropdown, đổi tiền, mobile/in vẫn PASS, không lỗi JS; log `appointment-browser-cache.log`. Review thêm chặn fallback tới phòng ban/chức vụ đã xóa trong hồ sơ cán bộ, bổ sung hồi quy POST với cả hai danh mục đã xóa. Các bước xử lý source cuối được kiểm tra lại bằng 19/19 SQLite và 14/14 SQL Server, không chỉ dùng browser chạy trước chỉnh sửa source để xác nhận.

**Bàn giao/còn mở:** chủ dự án tải lại trang QLHCNS cổng 8001, mở mẫu quyết định, chọn cán bộ/người ký, chọn hành động/chức vụ mới, nhập ngày hiệu lực và lương rồi cập nhật preview/tải Word/in. Đối chiếu hồ sơ thực tế, nội dung các điều/căn cứ/thẩm quyền ký trước sử dụng. Với người chưa có hồ sơ cần tạo qua Nhân sự trước khi chọn. Chưa thực hiện UAT trên dữ liệu thật/triển khai IIS/M365/CI; không migration DB gốc, không commit/push. Không có finding đã xác nhận chưa xử lý trong phạm vi lượt này.

## 2026-10-06 — Điền nhân viên đã chọn vào mọi mẫu HCNS

**Mục tiêu/phạm vi:** theo phản hồi chủ dự án, lựa chọn tại trang danh sách phải được giữ khi mở mẫu và các trường tương ứng trong mẫu phải lấy đủ dữ liệu đang có. `main` và working tree kiểm tra trước sửa, fetch/đối chiếu origin/main `0 0`, giữ mọi thay đổi HCNS/cổng 8001 trước đó.

**Đã làm:** cập nhật `hcns/prefill.py`, `views.py`, `appointment.py`, template catalog/draft, JS HCNS và `tests_hcns.py`. Dropdown trang danh sách submit ngay khi đổi; nút Chọn hồ sơ vẫn hoạt động. Cả 26 card mang `employee_id`, nút về danh sách giữ nhân viên, không chỉ giới hạn ba nhóm personnel/decision/leave. Máy chủ tiếp tục kiểm tra quyền trước đọc dữ liệu nguồn. Ánh xạ theo trường thực sự có trong mẫu và lọc dữ liệu dư khỏi initial: họ tên/vị trí/phòng ban, ngày vào/nghỉ, ngày sinh/giới tính/năm sinh, điện thoại/email/địa chỉ, CCCD/thuế/BHXH và quản lý/vị trí quản lý. Sửa thiếu liên hệ trong bảng bàn giao nghỉ việc; dropdown bổ nhiệm được chọn đúng ID và chức vụ hiện tại/chức vụ mới được điền tham khảo. Hồ sơ vòng đời dùng cùng ánh xạ. Không thêm trường/model/migration.

**Nguồn bổ sung và giới hạn:** mẫu có salary/salary_note lấy đúng một bản ghi EmployeeSalary Active đã hiệu lực và chưa kết thúc tại ngày mở, chỉ khi có quyền view_employee_compensation; không chọn lương tương lai, đã xóa hoặc tự giải quyết nhiều mức chồng lấn. Chuẩn hóa Decimal đồng nguyên để lương bằng chữ tự tính đúng. Quyết định chấm dứt lấy số hợp đồng khi có đúng một Contract Active trong hạn; không lấy ngày bắt đầu làm ngày ký. Chức vụ/lương hiện hành là tham khảo, quyết định mới cần xác nhận. Không tự điền ngân hàng/trình độ/quốc tịch/ngày cấp giấy tờ vì Employee hiện không có các trường đó; không suy đoán ngày nghỉ/ngày hiệu lực/người ký, mã ứng viên, điểm, thành viên hội đồng hay tài sản đề nghị thanh lý. Mẫu không có slot nhân viên giữ lựa chọn để chuyển mẫu và hiển thị nhãn nguồn, không chèn thêm dữ liệu không thuộc mẫu. Chuyển cán bộ trong dropdown bổ nhiệm reset chức vụ mới theo cán bộ và xóa lương/bằng chữ của người trước, tránh mang nhầm dữ liệu; có thể mở lại từ catalog để lấy lương tham khảo của người mới. Version CSS/JS HCNS `20261006-3` tránh service-worker cache cũ. Cập nhật hướng dẫn sử dụng cùng đợt.

**Kiểm tra/kết quả:** `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.document.tests_hcns` và `--backend sqlserver apps.document.tests_hcns`: mã cuối **16/16 đạt trên mỗi backend**, exit 0, DB/media thử cô lập; SQL runner xóa DB thử. Ca mới kiểm tra cả 26 card/GET/prefill/GET export, đúng tên/contact/ngày/manager/danh mục theo slot, giữ link quay lại, quyền truy cập hồ sơ khác, nguồn lương hiện hành/tương lai/chồng lấn, hợp đồng và trường không có dữ liệu. `manage.py check`, `makemigrations --check --dry-run` trên SQLite tạm đạt, không có migration. Log `%TEMP%\ihrms-hcns-layout-20261006\employee-prefill-sqlite.log`, `employee-prefill-sqlserver.log`; không ghi dữ liệu thật.

**Browser:** harness test cô lập ngoài Git chạy bằng `$env:PYTHONPATH=Join-Path $env:TEMP 'ihrms-hcns-layout-20261006'; venv\Scripts\python.exe ops\run_tests.py --backend sqlite live_browser_tests`. Edge có đăng nhập đã xác nhận đổi dropdown tự áp dụng, 26 link chứa nhân viên, mọi slot họ tên/contact tương ứng có giá trị, link quay lại giữ lựa chọn, 26 POST preview và tải tệp thành công; cache cũ bị bypass, chức năng điểm/lương/dropdown/mobile/in và CSRF vẫn đạt, không lỗi JavaScript. Log vòng đầu `employee-prefill-browser.log`; vòng cuối xác nhận thêm đổi cán bộ reset chức vụ mới/lương trong `employee-prefill-browser-final.log`. Harness và tệp tải chỉ có dữ liệu giả, nằm ngoài repo. Không coi đây là UAT với hồ sơ thật hoặc full-suite toàn dự án sau thay đổi.

**Bàn giao:** tải lại trang cổng 8001, chọn nhân viên rồi mở mẫu; kiểm tra các trường tự điền, bổ sung mục trống/xác nhận lương và chức vụ mới trước xuất. Chọn Mẫu trắng để bỏ lựa chọn. Chưa commit/push/deploy/CI, không sửa DB nghiệp vụ hay mẫu gốc. Phần chưa có nguồn lưu trữ được ghi rõ trong hướng dẫn, cần chủ dự án bổ sung trực tiếp trên bản soạn.

## 2026-10-08 — Dọn cấu trúc repository và sao lưu trước thay đổi

**Mục tiêu/phạm vi:** theo yêu cầu chủ dự án, kiểm kê các tệp ở thư mục gốc, sắp xếp tệp chẩn đoán review vào đúng nhóm vận hành, tạo bản sao trước thay đổi, rồi commit/push trên `main`. Trước khi làm, `git status --short` sạch; `git fetch origin main` và `git rev-list --left-right --count HEAD...origin/main` xác nhận local/remote không phân kỳ (`0 0`) tại `05f2591871ef22fd9e0128ff2f735211e8af69a7`. Không di chuyển `.env`, database, media, `venv`, `node_modules`, `Logs` hoặc các thư mục backup vận hành; hai tài liệu hướng dẫn ở thư mục gốc được giữ nguyên vì README và tài liệu tập huấn đang liên kết trực tiếp.

**Bản sao:** tạo `D:\QLHCNS\Backups\source-before-cleanup-20261008.bundle` bằng `git bundle create --all`; `git bundle verify` xác nhận bundle hợp lệ và chứa toàn bộ lịch sử. SHA-256 của bundle là `8B9D8E0085F7E0DE663C7253D68380B4CB3DF25B63859805545E57938B9342EE`. `Backups/` thuộc `.gitignore`, nên bản sao chỉ nằm cục bộ và không được đưa lên GitHub.

**Đã làm:** chuyển `_review_probe.py` khỏi thư mục gốc thành `ops/probes/booking_status_validation.py`; cập nhật cách xác định `PROJECT_ROOT` để đường dẫn `src` vẫn đúng sau khi di chuyển. Thêm `ops/probes/README.md` nêu rõ đây là probe thủ công, không thay cho regression test, chỉ được dùng với DB test cô lập và dữ liệu giả. Git nhận thay đổi là rename; không xóa nội dung chẩn đoán, không thay đổi mã ứng dụng, schema hay dữ liệu nghiệp vụ.

**Kiểm tra/kết quả:** `venv\Scripts\python.exe -m py_compile ops\probes\booking_status_validation.py`, `venv\Scripts\python.exe src\manage.py check` với `DB_ENGINE=django.db.backends.sqlite3`, `APP_ENV=test` và `SECRET_KEY` tạm, cùng `git diff --check` đều exit 0. Đối chiếu lại thư mục gốc xác nhận không còn probe tạm. Không chạy chính probe vì nó vẫn cần database SQLite đã migrate và fixture giả; không dùng DB cấu hình để làm cho probe chạy. Không chạy full suite vì chỉ sắp xếp script chẩn đoán ngoài runtime ứng dụng.

**Nhánh/commit và phần còn mở:** thay đổi cấu trúc ở commit `ec6d2f62fad3fd0cacdf01b3df04a9531d099173` trên `main`; commit nhật ký và trạng thái push được xác nhận trong bàn giao cuối đợt. Các finding RBAC/menu từ lượt review trước không thuộc phạm vi dọn file và chưa được sửa trong đợt này. Nếu probe cần dùng lâu dài, bước tiếp theo là chuyển tình huống tương ứng thành Django test dùng `ops/run_tests.py` và fixture cô lập.

**Tiếp tục sắp xếp tài liệu:** sau phản hồi của chủ dự án, chuyển `HUONG_DAN_SU_DUNG_IHRMS.md` và `TAP_HUAN_IHRMS.md` từ thư mục gốc vào `docs/` tại commit `52ec2b4af9d1e4b4e2b2b6552367238aed29ec84`. Cập nhật liên kết trong `README.md`, skill `ihrms-operations`, checklist go-live, production-readiness review và liên kết nội bộ giữa hai tài liệu. Script kiểm tra toàn bộ liên kết Markdown cục bộ trong năm tài liệu đầu mối xác nhận mọi đích đều tồn tại; `git diff --check` đạt. Các nhắc lại đường dẫn cũ trong phần lịch sử của nhật ký được giữ nguyên để không viết lại bằng chứng của các đợt trước. Đây là thay đổi tài liệu, không chạy full suite ứng dụng. Bản ZIP tạo trước bước này vẫn là snapshot an toàn trước khi di chuyển; một ZIP mới theo commit cuối được tạo ngoài repository sau khi push để gửi review.

## 2026-10-08 — Review tĩnh toàn mã nguồn (FULL/REVIEW), chưa sửa

**Mục tiêu/phạm vi:** theo yêu cầu chủ dự án, tiếp tục lượt review RBAC/menu còn dở, mở rộng ra toàn bộ `src/apps`, lưu lịch sử và soạn yêu cầu cho Codex sửa. Chế độ REVIEW: không sửa mã, không commit/push, không ghi dữ liệu. Nguồn là bản ZIP `QLHCNS-source-20261008-0004f7e047ed.zip` (mã băm ghi trong ZIP `0004f7e047ed99db4c8e9a7f6d39539f3298f5c2`), không phải checkout Git nên **chưa xác nhận** `main`/`HEAD...origin/main`. Liên kết chia sẻ cuộc hội thoại trước không tải được nội dung; phần review dở được xác định từ ghi chú "finding RBAC/menu chưa sửa" trong nhật ký ngày 2026-10-08 phía trên.

**Đã làm (đọc mã tĩnh, không chạy ứng dụng):** đối chiếu 150 route `portal/urls.py` với guard của view bằng script AST; so khớp menu `base.html` với `PERMISSION_MATRIX`; đọc kỹ `security/*`, các view nghỉ phép, lương, công văn, nhân sự, mua sắm/văn phòng, lifecycle, reporting, `leave/models.py`, upload và cấu hình production; quét toàn `src/` các mẫu rủi ro (`csrf_exempt`, `mark_safe`, SQL thô, `eval/exec`, `subprocess`, `float()` tiền) — không phát hiện vi phạm. Chi tiết, mức đã rà và danh sách phần chưa rà sâu ở [báo cáo review](Code_Review_Report_2026-10-08.md).

**Kết quả (xác nhận bằng đọc mã, chưa tái hiện bằng test):** 17 finding. P1: F-01 bảng lương bỏ sót nhân viên Thử việc/Nghỉ dài hạn (cần chủ dự án quyết định). P2: F-02 quyền quản lý công văn dùng nhầm `approve_leave`; F-03 phạm vi xem công văn đến rộng hơn ma trận; F-04 thiếu tách người đề nghị/người duyệt; F-05 xuất Excel nhân sự kèm CCCD cho Kế toán; F-06 tạo dòng lương cơ bản 0 im lặng; F-07 tạo đơn nghỉ phép không chống gửi đúp/đồng thời. P3: F-08…F-17 (menu thiếu đường vào, hai quyền báo cáo song song, sinh mã nhân viên, lifecycle không khóa dòng, upload chỉ kiểm tra đuôi, `private_file` hiệu năng, `CompanyMedia`, gia hạn hợp đồng, xuất công văn, nghỉ phép nhỏ).

**Kiểm tra chưa thực hiện và lý do:** môi trường review không có Django, không có mạng → chưa chạy `manage.py check`, `makemigrations --check`, test SQLite/SQL Server, `pip-audit`, `npm audit`, CI. Không dùng số test cũ làm kết quả. Không có bằng chứng Bugbot/Sixth đã chạy. Chưa rà sâu: `document/hcns/*`, `activity/*` ngoài guard, `m365/*`, `notification/*`, `planning`, `kpi`, `task`, model `asset`/`recruitment`, công thức `payroll/models.py`, `attendance/services.py`, migrations, `ops/*`, `src/frontend`, template ngoài `base.html`.

**Nhánh/commit:** chưa có commit/push cho đợt này; các tệp mới: `docs/Code_Review_Report_2026-10-08.md`, `docs/Yeu_Cau_Codex_Sua_Review_2026-10-08.md` và mục nhật ký này.

**Việc còn mở / chủ dự án cần làm:** (1) chốt chính sách cho F-01, F-03, F-04, F-05 (điền vào mục "Nhóm B" của yêu cầu Codex); (2) giao `docs/Yeu_Cau_Codex_Sua_Review_2026-10-08.md` cho Codex, nhóm A có thể chạy ngay; (3) đặt hai tệp mới và mục nhật ký này vào `D:\QLHCNS\docs`, chạy `git status`/`git diff --check` rồi commit theo ý chủ dự án; (4) lên lịch review tiếp phần "chưa rà sâu" và chạy đủ bộ kiểm tra trên Windows (SQLite + SQL Server).

## 2026-10-08 — Sửa Nhóm A của review mã nguồn

**Mục tiêu/phạm vi:** đọc `docs/Yeu_Cau_Codex_Sua_Review_2026-10-08.md` và đối chiếu từng finding với mã hiện tại trước khi sửa. Đầu đợt xác nhận nhánh `main`, working tree có ba thay đổi tài liệu của lượt review ngay trước (`docs/PROJECT_WORK_LOG.md` và hai tệp review/yêu cầu), local khớp `origin/main` (`0 0`); giữ nguyên và đưa các tài liệu cùng phạm vi vào đợt này. Cả bảy finding F-02, F-06, F-07, F-10, F-11, F-15, F-16 đều tái hiện đúng từ mã. Lần chạy test hồi quy đầu trên mã cũ cho 7 failure đúng finding và 1 error do fixture F-07 dùng sai tên trường; đã sửa fixture thành `allocated_days` trước khi chốt bộ test. Không sửa Nhóm B/C, không migration, không ghi dữ liệu nghiệp vụ thật.

**Đã sửa:** F-02 thống nhất quyền quản lý công văn bằng `manage_office` cho danh sách/cập nhật/tạo; không giữ ngoại lệ `is_staff` vì tài liệu quyền hiện hành quy định `is_staff` chỉ dành cho Django Admin, không phải quyền nghiệp vụ. F-06 chỉ tạo dòng lương cho nhân viên có `EmployeeSalary` hiệu lực tại đầu kỳ, hiển thị rõ danh sách thiếu lương và không cho khóa kỳ còn dòng lương cơ bản bằng 0. F-07 đặt kiểm tra trùng ngày/quỹ phép và lưu đơn trong `atomic()` với khóa dòng `Employee`. F-10 thử lại tối đa ba lần khi mã tự sinh dạng `VH0001` va chạm unique, giữ nguyên định dạng. F-11 khóa case rồi item trong một transaction, kiểm tra lại trạng thái trước cập nhật và chỉ đóng case khi không còn item Pending. F-15 chỉ gia hạn hợp đồng `Active` mới nhất và báo rõ khi không có. F-16 kiểm tra loại công văn theo choices, mặc định `Incoming`, đặt tên `noi-bo` cho `InternalDirective`. Điều chỉnh fixture lương trong hai bộ test cũ để phản ánh quy tắc mới: nhân viên phải có mức lương hiệu lực mới được sinh bảng lương.

**Test hồi quy mới:** `src/apps/portal/tests_review_20261008.py` có 10 test: ma trận sáu vai trò cho F-02; generate/lock lương F-06; gửi trùng tuần tự và đồng thời F-07; va chạm mã tuần tự và đồng thời F-10; khóa/idempotency lifecycle F-11; hợp đồng đã chấm dứt F-15; validate/tên tệp F-16. Hai test đồng thời chỉ chạy trên SQL Server thật qua database tạm của runner; SQLite bỏ qua đúng điều kiện backend. Bộ mục tiêu sau sửa đạt 10/10 trên SQL Server và 8/8 + 2 skipped trên SQLite. Bộ liên quan `apps.portal apps.lifecycle apps.document.tests_export_names` đạt 125/125, 1 skipped trên SQLite.

**Kiểm tra bắt buộc trên mã cuối:** `git diff --check` exit 0; `venv\Scripts\python.exe -m pip check` exit 0, không có dependency hỏng; `manage.py check` với `APP_ENV=test`, `SECRET_KEY` tạm và SQLite tạm exit 0; `manage.py makemigrations --check --dry-run` exit 0, `No changes detected`. `venv\Scripts\python.exe ops\run_tests.py --backend sqlite`: 396 test, 390 đạt và 6 skipped theo điều kiện, exit 0. `venv\Scripts\python.exe ops\run_tests.py --backend sqlserver`: 396/396 đạt, exit 0; runner tạo/xóa database tạm `test_ihrms_364c02a7461742e1850b7e759f7ba762`. Cả hai backend báo ba kịch bản HTTP PASS. Có cảnh báo timezone từ fixture đặt xe cũ, không làm test thất bại và không thuộc Nhóm A.

**Nhánh/commit và việc còn mở:** làm trên `main`; commit được tạo sau khi hoàn tất mục nhật ký này, không push/deploy theo yêu cầu. Chủ dự án cần quyết định Nhóm B trước khi làm tiếp: F-01 trạng thái `Probation`/`OnLeave` trong lương và các danh sách; F-03 phạm vi xem công văn đến; F-04 chính sách tự duyệt; F-05 quyền xuất/che CCCD; sau đó mới chốt F-08/F-09 về quyền báo cáo và nhóm menu. Chưa chạy UAT Edge/IIS/CI hoặc kiểm thử với dữ liệu thật; kết quả hiện tại là test tự động trên DB/media cách ly. Chủ dự án kiểm tra commit rồi tự quyết định thời điểm push.

## 2026-10-08 — Thêm nút quay nhanh từ trang quản trị về giao diện sử dụng

**Mục tiêu/phạm vi:** theo ảnh và yêu cầu của chủ dự án, làm đường quay về portal dễ nhìn và thao tác nhanh trên thanh điều hướng Django Admin/Jazzmin. Xác nhận đang ở `main`, working tree sạch trước sửa và local đang đi trước `origin/main` một commit của đợt sửa Nhóm A; không sửa hoặc push commit đó trong lượt này.

**Đã làm:** đổi nhãn liên kết top menu hiện có thành “Về giao diện sử dụng”, giữ đích nội bộ `/portal/` và không mở cửa sổ mới. Thêm `src/static/css/admin.css` qua cấu hình `custom_css` của Jazzmin để liên kết hiển thị như nút xanh nổi bật có mũi tên quay lại, trạng thái hover/focus rõ và kích thước gọn trên màn hình nhỏ. CSS chỉ tác động liên kết `/portal/` trong nhóm menu trái của navbar quản trị, không đổi quyền truy cập hay luồng đăng nhập. Thêm `src/apps/portal/tests_admin_navigation.py` kiểm tra trang admin thực sự render đúng nhãn/URL và nạp stylesheet tùy chỉnh.

**Kiểm tra/kết quả:** `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.portal.tests_admin_navigation`: 2/2 đạt, exit 0, DB/media thử cô lập. `manage.py check` với `APP_ENV=test`, `SECRET_KEY` tạm và SQLite tạm: 0 lỗi. `manage.py findstatic css/admin.css --verbosity 0` tìm thấy đúng `D:\QLHCNS\src\static\css\admin.css`. `git diff --check` đạt. Chưa chạy full suite, SQL Server, CI hoặc UAT trình duyệt vì thay đổi chỉ là cấu hình/template output và CSS quản trị; khi triển khai cần chạy `collectstatic` theo quy trình hiện hành và tải lại trang admin không dùng cache.

**Nhánh/commit:** thực hiện trên `main`; thay đổi được đưa vào cùng commit bàn giao với đợt tách Tuyển dụng/phân quyền Thang bảng lương sau khi chủ dự án yêu cầu commit và push.

## 2026-10-08 — Tách mảng Tuyển dụng và giới hạn biểu mẫu Thang bảng lương

**Mục tiêu/phạm vi:** theo yêu cầu chủ dự án, tách Tuyển dụng khỏi menu Nhân sự, bổ sung trang quy trình và lối vào biểu mẫu riêng; chuyển Thang bảng lương sang nhóm Kế toán và chỉ cho Kế toán/Ban giám đốc xem, xuất. Trước sửa xác nhận nhánh `main`, local đi trước `origin/main` một commit và working tree có thay đổi của nút quay về giao diện sử dụng; toàn bộ thay đổi có sẵn được giữ nguyên. Không đổi schema hay dữ liệu nghiệp vụ.

**Đã làm:** thêm nhóm menu cấp đầu **Tuyển dụng** gồm Quy trình tuyển dụng, Đề xuất tuyển dụng, Ứng viên và Biểu mẫu tuyển dụng; gỡ hai lối vào tuyển dụng khỏi menu Nhân sự. Trang quy trình mới mô tả sáu bước mà hệ thống hiện hỗ trợ: đề xuất nhu cầu, duyệt, tiếp nhận ứng viên, phỏng vấn/đánh giá, offer và chuyển thành nhân viên. Quyền trang giữ nguyên phạm vi nghiệp vụ hiện có: HR Manager, HR Officer và Trưởng phòng; mỗi nút thao tác chỉ hiển thị khi có quyền tương ứng.

**Phân quyền Thang bảng lương:** khai báo quyền riêng `use_salary_scale_form` cho `FINANCE_OFFICER` và `DIRECTOR`; superuser tiếp tục có toàn quyền theo cơ chế chung. Menu đổi nhãn thành **Kế toán**: Kế toán thấy các chức năng lương hiện có và Thang bảng lương; Ban giám đốc chỉ thấy biểu mẫu này, không được mở các trang vận hành payroll. HR Manager, HR Officer, System Admin, Trưởng phòng và Nhân viên không thấy mẫu trong menu/catalog và bị chặn 403 khi mở URL trực tiếp. Cập nhật ma trận RBAC và hướng dẫn biểu mẫu cùng đợt.

**Kiểm tra/kết quả:** bộ test hồi quy mới `apps.portal.tests_recruitment_accounting_navigation` ban đầu thất bại trên mã cũ do chưa có menu/route Tuyển dụng và HR vẫn mở được Thang bảng lương; sau sửa đạt 3/3. Nhóm biểu mẫu + phân quyền đạt 19/19 SQLite; nhóm tuyển dụng/phân quyền/admin đạt 9/9 SQLite; nhóm biểu mẫu/tuyển dụng/phân quyền đạt 23/23 trên SQL Server tạm `test_ihrms_9818325650144b1b9bf06159520c7990`. Full suite SQLite lần đầu phát hiện một test cũ còn dùng HR để xuất `salary-scale`; đã chuyển riêng ca này sang fixture Kế toán, test hẹp đạt 6/6 và full suite cuối đạt **401 test, 395 đạt, 6 skipped**, exit 0. `manage.py check`, `makemigrations --check --dry-run`, `pip check` và `git diff --check` đều đạt; không có migration.

**Còn mở/bàn giao:** chưa UAT trên trình duyệt với tài khoản nghiệp vụ thật, chưa chạy full suite SQL Server/CI và không deploy. Chủ dự án nên tải lại portal, đăng nhập lần lượt bằng tài khoản HR, Trưởng phòng, Kế toán và Ban giám đốc để xác nhận nhãn/menu và nội dung quy trình phù hợp cách gọi nội bộ. Đợt này được commit/push trên `main` sau khi chủ dự án yêu cầu; SHA và trạng thái remote được xác nhận trong bàn giao cuối.

## 2026-10-09 — Làm lại dashboard Báo cáo và xuất Excel/Word/PowerPoint

**Mục tiêu/phạm vi:** làm lại trang Báo cáo thành dashboard điều hành tổng hợp theo khoảng ngày, bao phủ các mảng đang có trên hệ thống và bổ sung ba định dạng xuất. Đầu đợt xác nhận nhánh `main`, working tree chỉ có thư mục `outputs/` không thuộc phạm vi và local khớp `origin/main` (`0 0`); giữ nguyên thư mục này. Không thay đổi schema, quyền nghiệp vụ hiện hành hoặc dữ liệu thật.

**Đã làm:** thay trang `portal/report_hub.html` bằng dashboard responsive có bộ lọc ngày, sáu chỉ số tổng quan, biểu đồ biến động nhân sự theo tháng, phễu tuyển dụng và các nhóm Nhân sự, Tuyển dụng, Chấm công/nghỉ phép, Hành chính, Tài sản/mua sắm, Công việc/KPI, Hợp đồng/lương, Hồ sơ/quyết định nhân sự, Kế hoạch/ngân sách/đào tạo/sự kiện, Dự án/hoạt động. Dữ liệu được tổng hợp tập trung trong `portal/reporting_dashboard.py` và dùng chung cho HTML cùng ba định dạng xuất; không đưa định danh cá nhân, CCCD, liên hệ hoặc số tiền lương vào báo cáo. Thêm endpoint tải Excel `.xlsx`, Word `.docx` và slide `.pptx`; giữ cùng quyền xem báo cáo hiện có (HR Manager, Ban giám đốc và superuser), trả 403 khi không có quyền, kiểm tra khoảng ngày tối đa 1095 ngày và ghi `SecurityEvent` khi xuất thành công. Excel có ba sheet và hai biểu đồ gốc; Word dùng trang ngang và bảng theo nhóm; PowerPoint 16:9 có 12 slide, hai biểu đồ gốc và các bảng tóm tắt. Bổ sung `python-docx==1.2.0`, `python-pptx==1.0.2` và test hồi quy `tests_report_dashboard.py`.

**Kiểm tra/kết quả:** `venv\Scripts\python.exe src\manage.py check` đạt, 0 lỗi. `venv\Scripts\python.exe src\manage.py test apps.portal.tests_report_dashboard --verbosity 1` đạt **5/5** sau thay đổi cuối; kiểm tra render, quyền, tham số, ba MIME/tệp có thể mở và audit xuất. Cùng 5 test đạt trên SQL Server dùng database tạm `test_ihrms_4e00dba9b4b64fddabc14548c9931a9d`, runner đã xóa database sau kiểm tra. `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.portal.tests_report_dashboard apps.portal.tests_review_hardening apps.portal.tests_mobile` đạt **35 test, 1 skipped**. Full `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.portal` đạt **120 test, 3 skipped**, exit 0. `makemigrations --check --dry-run` báo `No changes detected`; `pip check` và `git diff --check` đạt. Mẫu tổng hợp chỉ đọc được tạo trong thư mục tạm: Excel mở bằng openpyxl có 3 sheet/2 chart, Word mở bằng python-docx có 10 bảng, PowerPoint mở bằng python-pptx có 12 slide/2 chart; kiểm tra hình học không có shape vượt khung slide.

**Phần chưa kiểm thử/bàn giao:** chưa render trực quan Word/PowerPoint vì bộ công cụ tài liệu không tìm thấy LibreOffice đóng gói; chưa UAT trang Báo cáo trong Edge đã đăng nhập, chưa chạy full suite SQL Server/CI và chưa kiểm tra số liệu với dữ liệu nghiệp vụ đại diện. Chủ dự án cần cài dependency từ `requirements.txt`, tải lại ứng dụng, đăng nhập tài khoản HR Manager/Ban giám đốc để đối chiếu từng chỉ số và mở ba tệp xuất bằng Microsoft Office. Không commit/push/deploy trong đợt này vì chưa được yêu cầu.

## 2026-10-09 — Bugbot giao diện, đồng bộ kiểu chữ/màu và dọn tệp tạm

**Mục tiêu/phạm vi:** theo yêu cầu rà lại bố cục, font, màu, giao diện toàn dự án và sửa mã; chủ dự án chọn Bugbot. Đầu đợt xác nhận `main`, local khớp `origin/main` (`0 0`); giữ nguyên thay đổi dashboard/export chưa commit và thư mục `outputs/` từ lượt trước. Bugbot chạy review diff hiện tại, phát hiện bốn finding: mất link Ngân sách (P1), biểu đồ thiếu số liệu cho trình đọc màn hình (P2), vùng cuộn mobile không nhận focus (P2), nhãn 10–12px (P3). Phần rà thêm đọc `base.html`, CSS chung, các template công văn/phiếu lương, tiêu chuẩn frontend và đặc tả UI; chưa tuyên bố đã UAT tất cả màn hình.

**Bản sao trước sửa:** tạo `D:\QLHCNS-Backups\QLHCNS-before-ui-cleanup-20261009-090318.zip` (15.229.192 byte, 1.299 mục), SHA-256 `97F11BA577D0CD209AD2DB99DC0BC34D7ED75D58F6C2108D8C4A8DEB3A18A041`. Danh sách ZIP đã được kiểm tra không có `.env`, database, media, `venv`, `node_modules` hoặc `outputs`; bản sao nằm ngoài repository. Không chép nội dung bí mật từ cấu hình cục bộ vào tài liệu hoặc Git.

**Đã sửa:** khôi phục link riêng “Xem ngân sách” và đổi link còn lại thành “Xem định biên”; đưa CSS Báo cáo khỏi template sang `src/static/css/report_dashboard.css`, bổ sung token màu/font dùng chung trong `ihrms.css` và `extra_css` trong layout gốc. Biểu đồ tháng có vùng cuộn focusable và bảng số liệu truy cập bằng bàn phím; phễu tuyển dụng là danh sách có nhãn/số đọc được. Tăng cỡ chữ của nhãn quan trọng ở Dashboard, header, công văn và phiếu lương; bỏ hiệu ứng nhấp nháy của mức Hỏa tốc. Thêm regression HTML cho link và khả năng truy cập. Tạo [UI_DESIGN_SYSTEM.md](UI_DESIGN_SYSTEM.md), liên kết từ README và gắn chú thích hiện trạng vào tiêu chuẩn frontend/đặc tả UI; sửa tài liệu Tailwind từ 3 thành đúng 4.3.0 đang ghim. Build lại `tailwind.css`.

**Dọn tệp:** xác nhận `.tmp-ihrms-dashboard` chỉ chứa một junction `node_modules` trỏ tới cache công cụ ngoài dự án và không có tham chiếu trong mã. Lệnh xóa junction bị chính sách máy từ chối; đã chuyển nguyên thư mục sang `%TEMP%\ihrms-dashboard-junction-20261009`, nên workspace sạch mục tạm này và có thể khôi phục. Không xóa `outputs/` vì đó là sản phẩm chưa theo dõi từ lượt trước và chưa có bằng chứng là tệp thừa.

**Kiểm tra/kết quả:** `venv\Scripts\python.exe src\manage.py test apps.portal.tests_report_dashboard --verbosity 1` đạt 5/5 trên SQLite; cùng 5 test đạt với `ops\run_tests.py --backend sqlserver` trên DB tạm `test_ihrms_f3f363b2644846909c05cf100cd7d9c0`, runner đã xóa DB tạm. `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.portal` đạt 120 test, 3 skipped, exit 0. `manage.py check` đạt 0 lỗi; `makemigrations --check --dry-run` báo không đổi schema; `findstatic css/report_dashboard.css` tìm thấy asset; `npm run build:css` đạt với Tailwind 4.3.0; `git diff --check` đạt. Phép thử parse CSS tùy chọn qua Node không chạy được vì `postcss` không được cài làm dependency độc lập; build Tailwind vẫn thành công. Chưa có UAT trình duyệt xác thực ở 375/768/1440px, kiểm tra zoom 200%, so khớp số liệu thật hoặc full suite SQL Server sau đợt UI này. Chủ dự án cần tải lại portal, mở Báo cáo và các màn hình công văn/phiếu lương trên các cỡ màn hình, thử bàn phím, rồi đối chiếu xuất Office. Chưa commit/push/deploy trong đợt này.

## 2026-10-09 — Tách thư mục SharePoint cho Công văn đến và Công văn đi

**Mục tiêu/phạm vi:** người dùng báo cả hai loại công văn đều vào `CongVan`. Đối chiếu mã xác nhận `OfficialDispatch.attachment` dùng chung `upload_to_dispatches` và `ConfiguredStorage("dispatches")`, mặc dù settings đã có `incoming_docs=CongVanDen` và `outgoing_docs=CongVanDi`. Làm trên `main`, local khớp `origin/main` (`0 0`); giữ nguyên các thay đổi dashboard/UI và `outputs/` chưa commit. Không đổi schema hoặc di chuyển tệp nghiệp vụ thật.

**Đã sửa:** `upload_to_dispatches` chọn tiền tố `incoming_docs` hoặc `outgoing_docs` theo `dispatch_type`; `ConfiguredStorage` định tuyến hai tiền tố qua cấu hình thư mục tương ứng trong cùng thư viện SharePoint. Văn bản nội bộ tiếp tục vào `CongVan`. Đường dẫn đã lưu có tiền tố `CongVan`, `CongVanDen`, `CongVanDi` được nhận dạng idempotent để mở lại đúng nơi; tệp cũ ở `CongVan` không tự chuyển và không bị đổi tên DB. Giữ nguyên hàm `upload_to_dispatches` và adapter storage để migration hiện có không drift. Bổ sung kiểm thử đường dẫn/saving/mở tệp cũ, cập nhật `.env.example`, chú thích settings, tài liệu sử dụng và storage docstring.

**Kiểm tra/kết quả:** test mới thất bại đúng hai nhánh Incoming/Outgoing trên mã cũ, sau sửa đạt. `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.m365.tests apps.document.tests apps.portal.tests_review_hardening`: 37 test, 1 skipped, exit 0. `venv\Scripts\python.exe ops\run_tests.py --backend sqlserver apps.m365.tests apps.document.tests`: 11 test, exit 0; DB thử `test_ihrms_dc16d7cc87bb4c4b80b6f32a46ab7cea` đã được runner xóa. `manage.py check` đạt 0 lỗi, `makemigrations --check --dry-run` báo `No changes detected`, `git diff --check` đạt. Test SharePoint dùng mock, không truy cập site/tệp thật.

**Còn mở/hành động chủ dự án:** khởi động lại ứng dụng sau cập nhật mã, tạo một Công văn đến và một Công văn đi với tệp thử không nhạy cảm, kiểm tra chúng nằm đúng `CongVanDen`/`CongVanDi` và mở lại qua IHRMS; mở thêm một công văn cũ ở `CongVan`. Nếu có cấu hình `M365_FOLDER_INCOMING`/`M365_FOLDER_OUTGOING` tùy chỉnh, kiểm tra tên thư mục thực tế theo cấu hình đó. Chưa commit/push/deploy, chưa thực hiện smoke test SharePoint thật.

**Bàn giao Git sau yêu cầu commit/push:** 25 tệp mã, CSS, test và tài liệu của ba mục ngày 09/10 được commit trên `main` tại `442b8482e180cc2e0d655d65d0319e4a4adb0f8d` và push thành công; `git ls-remote origin refs/heads/main` khớp SHA này ngay sau push. `outputs/` vẫn untracked và không được stage; `.env`, backup, DB/media và secret không nằm trong commit. Lệnh `gh run list --branch main --commit 442b8482e180cc2e0d655d65d0319e4a4adb0f8d --limit 5` trả HTTP 401 Bad credentials, nên chưa xác nhận ba job Actions cho commit này. Chủ dự án cần đăng nhập lại GitHub CLI bằng tài khoản có quyền hoặc mở Actions của repository và kiểm tra đúng SHA cùng trạng thái `backend`, `frontend`, `backup-command-tests`. Mục nhật ký bàn giao này được commit/push tiếp sau commit mã; SHA cuối được báo trong phản hồi.

## 2026-10-10 — Căn menu/KPI và áp dụng DESIGN.md toàn giao diện

**Mục tiêu/phạm vi:** sửa menu lệch khung, căn giữa giá trị toàn bộ thẻ KPI hiện có, mở rộng theme sang toàn portal và quản trị. Xác nhận `main`, fetch origin và `HEAD...origin/main` là `0 0` lúc bắt đầu; bảo toàn các thay đổi UI/UAT/bốn finding chưa commit. Không thay đổi nghiệp vụ, phân quyền, schema, dữ liệu thật hay `.env`.

**Đã làm:** menu trước đó rộng 80rem nhưng header/main mặc định 64rem; nay ba vùng dùng chung token chiều rộng, gồm ngoại lệ trang sơ đồ tổ chức rộng. Tách `design_tokens.css` dùng chung portal/Jazzmin; theme Tailwind ánh xạ blue/indigo và gray/slate sang palette DESIGN.md, giữ màu thành công/cảnh báo/lỗi. Font system, weight nhấn mạnh 600, card raised nhẹ, input inset, focus rõ và reduced-motion. Áp dụng adapter cho Jazzmin, HCNS và sơ đồ tổ chức; bảng giữ phẳng, bản giấy/Word/Excel giữ bố cục nghiệp vụ. KPI Trang chủ, Báo cáo, tiến độ dự án, số dư phép và trung tâm báo cáo dùng căn giữa/tabular-nums; không thay đổi căn cột số trong bảng. Đổi phiên bản URL CSS và cache static PWA để tránh CSS cũ; vẫn không cache HTML/dữ liệu nghiệp vụ. Login có label gắn với input/autocomplete. Cập nhật `docs/UI_DESIGN_SYSTEM.md`, test phiên bản CSS/menu và thêm regression token/menu/KPI.

**Kiểm tra đã xác nhận:** `npm run build:css`, `venv\Scripts\python.exe src\manage.py check` đạt. Edge trên DB SQLite preview riêng, dữ liệu giả lập, SMTP locmem và M365 tắt: header/nav/main cùng left 436.5px và width 1024px ở viewport desktop; mọi số KPI Trang chủ/Báo cáo/tiến độ đã kiểm tra có computed text-align center. Xem thêm HCNS và Jazzmin; sửa chữ người dùng/sidebar trắng trên nền tím để tránh chìm. Mobile 390px và tablet 768px không tràn ngang toàn trang (scrollWidth lần lượt 375/753px), menu dùng được và đã khôi phục viewport. Screenshot minh chứng lưu ngoài repo trong thư mục preview tạm, không chứa dữ liệu thật. Test mới bắt class KPI gắn nhầm thẻ cha, đã sửa và test mobile đạt 6/6 SQLite. Các lượt full ban đầu bắt assertion phiên bản CSS/nhãn checklist cũ; đã cập nhật theo UI mới. Full suite cuối bằng `venv\Scripts\python.exe ops\run_tests.py --backend sqlite` đạt 416 test, 7 skipped theo backend, exit 0; cùng lệnh với `--backend sqlserver` đạt 416/416, exit 0. DB test tạm được runner xóa; cả hai backend báo ba kịch bản HTTP PASS. Các lượt lỗi ban đầu không được coi là đạt. `node --check src/static/js/service-worker.js` và `git diff --check` đạt (Git chỉ cảnh báo LF/CRLF). Khung rộng org chart cũng xác nhận cả ba vùng cùng width 1536px. Tính tương phản năm cặp chữ/nền chính đạt 4.94–13.89:1; ô tìm kiếm có outline tím 2px/offset 2px. Bản giấy HCNS xác nhận Times New Roman, chữ đen; nút primary chữ trắng/nền #4c1d95.

**Bàn giao/còn mở:** chưa commit/push/deploy. Theme đã áp dụng qua nguồn CSS chung cho toàn giao diện, nhưng chưa UAT trực quan từng trang/11 vai trò, zoom 200%, tương tác quản trị toàn bộ hay tích hợp Office/SharePoint thật. Chủ dự án khởi động lại ứng dụng để nạp template mới; khi triển khai chạy `venv\Scripts\python.exe src\manage.py collectstatic --noinput`, mở lại portal và Ctrl+F5 để nhận CSS/cache mới. Không cần xóa cookie/dữ liệu nghiệp vụ. Tiếp tục UAT theo kế hoạch trên bản sao cô lập; các điều kiện GO/NO-GO và migration từ lượt trước không thay đổi.

## 2026-10-10 — Chế độ sáng/tối và bàn giao các thay đổi đang chờ

**Mục tiêu/phạm vi:** thêm hai chế độ sáng/tối và commit/push theo yêu cầu chủ dự án. Xác nhận nhánh `main`, fetch origin và so sánh `HEAD...origin/main` là `0 0`; giữ nguyên, đưa vào bàn giao các thay đổi giao diện DESIGN.md, menu/KPI và bốn sửa lỗi UAT từ các mục trước. Không sửa `.env`, không reset dữ liệu, không áp dụng migration vào DB nghiệp vụ.

**Đã làm:** thêm `src/static/js/theme.js`, `src/static/css/theme.css`, override `src/templates/admin/base_site.html`; nút chuyển ở header portal/đăng nhập và navbar quản trị, mặc định sáng, chỉ lưu lựa chọn giao diện trong localStorage, đồng bộ tab, xử lý storage bị chặn. CSS tối dùng bảng màu tím, tương phản chữ/KPI và màu trạng thái sáng hơn; adapter Bootstrap cho quản trị, không đổi định dạng xuất Office và giấy HCNS. Theme được đọc trước stylesheet để giảm nháy nền, cache service worker tăng phiên bản và chỉ cache static. Thêm unit test JavaScript và regression Django, cập nhật `docs/UI_DESIGN_SYSTEM.md`.

**Kiểm tra:** `npm run build:css` đạt; `node --test src/frontend/theme.test.cjs` đạt 3/3 (lưu lựa chọn, storage bị chặn, dữ liệu không hợp lệ/đồng bộ tab); `ops/run_tests.py --backend sqlite apps.portal.tests_mobile` đạt 7/7. `node --check` cho theme/service worker và `git diff --check` đạt. Edge trên SQLite preview riêng, dữ liệu giả, M365 tắt/email locmem: xác nhận Trang chủ, Báo cáo và quản trị chuyển sáng/tối, tải lại vẫn giữ lựa chọn; mobile 390px không tràn ngang, khôi phục viewport sau kiểm tra. Đã sửa các nền Bootstrap còn trắng khi rà trực quan. Không coi các lượt full suite bị mất phiên công cụ lúc chuyển lượt chat là kết quả đạt; chạy lại có log ngoài repository để xác minh trước bàn giao.

**Kiểm tra cuối trước commit:** `venv\Scripts\python.exe ops\run_tests.py --backend sqlite` chạy đủ 417 test, đạt với 7 skipped theo backend, exit 0. Cùng lệnh với `--backend sqlserver` đạt 417/417, exit 0, DB tạm `test_ihrms_6ed83684777c47fa8329c6365b20000c` được runner xóa. Cả hai backend báo ba kịch bản HTTP PASS. `manage.py check`, `makemigrations --check --dry-run` trên SQLite preview riêng và `pip check` đạt; không có migration phát sinh ngoài `procurement.0002` đã chuẩn bị từ lượt trước.

**Nhánh/commit:** bản mã và tài liệu chờ bàn giao đã commit `d16d280` trên `main` và push thành công lên `origin/main`. Bổ sung dòng xác nhận này bằng commit tài liệu cùng đợt; SHA HEAD/remote cuối được đối chiếu trong phản hồi bàn giao. Các ghi chú “chưa commit/push” ở mục trước là trạng thái lịch sử lúc kết thúc từng lượt, nay được thay thế bởi bàn giao này.

**Bàn giao/còn mở:** kiểm tra danh sách tệp và mẫu bí mật không phát hiện `.env`, DB, CSV tài khoản, backup hoặc khóa riêng trong phạm vi đưa vào Git. Chưa deploy hoặc xác nhận CI/UAT đủ 11 vai trò/từng màn hình/Office/SharePoint thật. Migration `procurement.0002` vẫn chưa áp dụng vào DB `qlhcns`; DBA thực hiện trên bản sao UAT sau backup/restore và kiểm tra dữ liệu như kế hoạch. Khi triển khai, khởi động lại ứng dụng, chạy `venv\Scripts\python.exe src\manage.py collectstatic --noinput`, Ctrl+F5 để nhận CSS mới; dùng nút mặt trăng/mặt trời trên header để chọn mode.

## 2026-10-10 — Gom menu Nhân sự và thử UI theo DESIGN.md

**Mục tiêu/phạm vi:** gom Cần duyệt và Quyết định nhân sự vào Nhân sự; thử thiết kế theo `DESIGN.md` cho khung portal, Trang chủ và dashboard Báo cáo. Làm trên `main`, đã fetch origin và xác nhận `HEAD...origin/main` là `0 0`; bảo toàn các thay đổi bốn finding/UAT đang có. Không sửa dữ liệu thật, schema, quyền backend hay `.env`.

**Đã làm:** `src/templates/base.html` bỏ hai mục điều hướng cấp một, gom Nhân sự thành “Hồ sơ & quá trình” và “Cần duyệt & xử lý”. Điều kiện hiển thị menu bao gồm người chỉ có quyền duyệt; từng link vẫn theo quyền cũ, Tuyển dụng và Kế toán giữ riêng. `src/static/css/ihrms.css`, `home_dashboard.css`, `report_dashboard.css` dùng bảng màu tím, system font, card raised nhẹ, form inset, focus và reduced-motion; giữ màu trạng thái và hàng KPI cân đối. Nút chính dùng primaryStrong thay vì primary nhạt để chữ trắng rõ. Build lại `tailwind.css`; cập nhật `docs/UI_DESIGN_SYSTEM.md` để đồng nhất với DESIGN.md và nêu rõ phạm vi bản thử. Thêm regression role/menu trong `tests_recruitment_accounting_navigation.py`.

**Kiểm tra:** `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.portal.tests_recruitment_accounting_navigation apps.portal.tests_report_dashboard apps.portal.tests_mobile` đạt 14/14, exit 0. Cùng bộ test với `--backend sqlserver` đạt 14/14, exit 0; DB SQL Server test tạm đã được runner xóa. `npm run build:css` đạt; `git diff --check` không có lỗi whitespace (chỉ cảnh báo chuyển LF/CRLF). Edge đăng nhập tài khoản HR_MANAGER giả lập trên SQLite preview riêng, SMTP locmem và M365 tắt: đã xem Trang chủ, submenu Nhân sự và Báo cáo trên desktop; kiểm tra mobile viewport 390px, menu nằm trong vùng nội dung, không tràn ngang (scrollWidth 375px), Escape đóng submenu và trả focus về nút Nhân sự. Khôi phục viewport sau kiểm tra. Không dùng session/dữ liệu nghiệp vụ thật.

**Còn mở/bàn giao:** đây là bản UI thử trong mã, chưa chuyển đổi toàn bộ form nghiệp vụ, org chart, Jazzmin hay bản in; chưa UAT trực quan đủ 11 vai trò, zoom 200%, toàn bộ breakpoint và Office/SharePoint thật. Chưa commit/push/deploy. Chủ dự án mở Trang chủ/Báo cáo, hard refresh (Ctrl+F5) và đánh giá bảng màu/bóng nổi trước khi nhân rộng sang các màn hình còn lại. Bốn finding và migration từ mục bên dưới vẫn giữ nguyên trạng thái bàn giao riêng.

## 2026-10-09–10 — Khắc phục bốn finding trước UAT máy chủ

**Mục tiêu/phạm vi:** theo yêu cầu xử lý bốn vấn đề của lượt review FULL ngay trước: guard cấu hình UAT, an toàn script reset QA, quyết định hồ sơ hoạt động đồng thời, và dữ liệu đề nghị mua sắm. Xác nhận nhánh `main`, local khớp `origin/main` (`0 0`) lúc bắt đầu; giữ nguyên phần sửa sẵn có trong `docs/PROJECT_WORK_LOG.md`, `ops/reset_qa_data.py` và bản kế hoạch UAT chưa theo dõi. Không reset DB, không dùng dữ liệu thật, không sửa `.env`.

**Đã làm:** `APP_ENV=uat` nay bắt buộc tắt DEBUG, ép HTTPS, dùng secret mạnh và hostname cụ thể như production; runner test dùng `APP_ENV=test` vẫn cô lập. Script `ops/reset_qa_data.py` chỉ cho chạy với `APP_ENV=test`, từ chối DB tên chung `qlhcns`, chỉ chấp nhận tên bản sao QA/UAT rõ ràng, tệp `.bak` không rỗng ngoài repo và extended property `IHRMS_DISPOSABLE_QA=YES` trước khi có thể xóa; việc tệp tồn tại **không** chứng minh restore thành công. Quyết định hồ sơ hoạt động được khóa dòng và kiểm tra lại trạng thái trong transaction, thông báo gửi sau khi lưu thành công. Đề nghị mua sắm kiểm tra số dòng, tên, số lượng, đơn giá phía server; model có validator và migration `procurement.0002` thêm check constraint không cho số lượng <=0/đơn giá âm. Cập nhật kế hoạch UAT yêu cầu khai báo `APP_ENV=uat` rõ ràng.

**Kiểm tra đã xác nhận:** test tập trung mua sắm/duyệt đạt 14/14 SQLite và 15/15 SQL Server; test guard UAT đạt 1/1 SQLite; test tranh chấp duyệt SQL Server cùng guard đạt 3/3. Sau migration, test tập trung mua sắm/guard đạt 9/9 trên cả SQLite và SQL Server; sau khi siết `APP_ENV=test`, test guard đạt 2/2 SQLite. Full suite trên mã cuối bằng `ops/run_tests.py` đạt **414/414 SQL Server**, exit 0, trên DB tạm `test_ihrms_9e491a4c290040c289aec784e979204a` đã xóa; **414 SQLite**, 7 skipped theo backend, exit 0. Cả hai backend báo ba kịch bản HTTP PASS. `manage.py check`, `makemigrations --check --dry-run`, `pip check`, `git diff --check` đều đạt; `migrate procurement --plan` chỉ liệt kê `0002`. Truy vấn chỉ đọc trên DB `qlhcns` đếm 0 hạng mục mua sắm có số lượng <=0 hoặc đơn giá âm. Thử `--apply` với DB tên `qlhcns` bị chặn trước mọi ghi. Kiểm tra `check --deploy` trên cấu hình UAT giả lập còn duy nhất cảnh báo HSTS W004 do chủ ý chưa bật HSTS trước khi IT xác nhận HTTPS mọi hostname; đây không phải kiểm tra trên máy chủ thật. Test có cảnh báo timezone từ fixture đặt xe cũ, không làm thất bại.

**Nhánh/commit, việc còn mở và hành động chủ dự án:** chưa commit/push/deploy vì yêu cầu lần này là sửa và kiểm thử; migration `0002` **chưa áp dụng** lên DB `qlhcns`. Trước triển khai UAT, DBA kiểm tra dữ liệu mua sắm không hợp lệ trên DB đích, backup và restore thử, rồi mới chạy migration trên bản sao UAT được duyệt. IT đặt `APP_ENV=uat` cùng TLS/hostname/secret riêng và chạy `check --deploy` trên máy chủ; không copy/chạy script reset QA trên máy chủ UAT. Chưa xác nhận secret M365 cũ được thu hồi, tích hợp thật, CI theo SHA hoặc GO/NO-GO hạ tầng.
