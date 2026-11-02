# Review toàn dự án IHRMS — 02/11/2026

**Yêu cầu:** FULL, web/mobile/chatbot; **REVIEW**, không sửa nguồn/cấu hình/migration, không push/deploy/APK.

**HEAD đã review:** `bae845060a0880cac0f947c57a3c2a90fbafea8e`, nhánh `main`. Commit bàn giao chỉ thay báo cáo này và một mục nhật ký.

**Bằng chứng (E/):** `D:/IHRMS_Review_Exports/Full_Review_20261102/`. Bản đầy đủ của báo cáo và PROGRESS.md được lưu cùng thư mục này. Báo cáo cũ thực tế ở `docs/archive/reviews/Code_Review_Report_2026-10-08.md`.

## 1. Tóm tắt điều hành

| Finding mới so với báo cáo 08/10 | Cao | Trung bình | Thấp | Tổng |
|---|---:|---:|---:|---:|
| R2-01…R2-09 | 1 | 5 | 3 | 9 |

Tám mục có hành vi tái hiện trực tiếp; R2-07 xác nhận audit nhưng chưa tái hiện khai thác dependency. Finding cũ: **7 mục đóng, 10 mục chưa đóng hoàn toàn**, gồm chờ quyết định/sửa một phần/chưa sửa; không diễn giải thành mười lỗi đã được xác nhận theo chính sách mới.

Phân mức rủi ro theo quy ước lượt này cho **10 mục cũ còn mở**: 1 Cao (F-01, có điều kiện theo quyết định payroll), 2 Trung bình (F-04/F-05, chờ chính sách), 7 Thấp (F-08/F-09/F-12/F-13/F-14/F-16/F-17). Đây là phân mức để ưu tiên quyết định, không nâng nghi vấn thành lỗi.

Năm rủi ro ưu tiên:

1. **R2-01:** tỷ lệ bảo hiểm âm tạo lương sai, kỳ vẫn khóa được — mức Cao, đã tái hiện.
2. **F-01:** bộ chọn hưởng lương bỏ Probation/OnLeave; cần chủ dự án chốt quy tắc cho từng trạng thái.
3. **F-05:** Finance xuất được CCCD toàn công ty; chưa tìm thấy quyết định che/bỏ trường hoặc mã hóa cấp trường.
4. **R2-02:** SQLite có thể báo hết phiên mobile giả khi request đồng thời lưu phiên; nhiều UAT không hoàn tất.
5. **R2-04:** Excel kiểm kê giữ dữ liệu nhập thành công thức. F-04 tự duyệt và R2-07 dependency làm tăng rủi ro trước phát hành rộng.

**Sẵn sàng phát hành:** Web **chưa đạt** do R2-01 và chính sách dữ liệu còn mở. Mobile **chưa đạt**: gate tĩnh/export đạt nhưng bảy runner UAT đỏ, chưa kiểm thiết bị thật. Chatbot có kết quả local tích cực, nhưng chưa đủ chứng nhận triển khai thật: Graph/SharePoint, cache nhiều worker, retention, tải thực và server đích chưa kiểm. Không có kết luận review 100%, Bugbot/Sixth hoặc go-live.

## 2. Phạm vi và phương pháp

### 2.1 Nền và cô lập

- Git đầu lượt: status chỉ `?? .codex/`; branch main; fetch origin main exit 0; ahead/behind `0 0`; đã đọc log 10 commit và ba mục nhật ký mới nhất. Sau gián đoạn do Cancel nhầm, kiểm lại Git không có nguồn đổi.
- Đọc AGENTS, hướng dẫn review, báo cáo F cũ, RBAC, deployment, native UI, spec assistant và quyết định trong nhật ký. Dùng `ihrms-review`, thêm `diagnosing-bugs` khi điều tra lỗi phiên. Không dùng reviewer độc lập/Bugbot/Sixth.
- `E/source/` chứa 1.679 tệp tracked, có manifest SHA-256; mở lại kiểm hash trước và sau export, `snapshot-recheck.json` không khác biệt. Gate/build chạy trên bản sao để giữ worktree. Không sao chép .env/DB/media vận hành/tài khoản thật. Binary/reference/screenshot tracked được kiểm kê và sao cùng nguồn; chưa rà riêng tư bên trong mọi binary.
- Mọi Python/test đặt `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`. Probing dùng SQLite memory/file mới. SQL runner dùng Windows authentication tới `localhost\SQLEXPRESS`, kiểm tên DB từ master rồi tạo/hủy **test_ihrms_UUID**; không truy vấn DB nghiệp vụ.
- Mobile dùng lại QA có marker synthetic_only ở `E/mobile-qa/`, không chạy lại create/seed. Continuation đặt credential ngẫu nhiên trong bộ nhớ cho tài khoản giả; adapter `E/guards/sitecustomize.py` cung cấp credential cho runner mà không đọc/in DEMO_ACCOUNTS.txt. Không mượn danh tính thật.
- M365/push tắt, email locmem. Probing chặn socket ngoài loopback; continuation UAT chặn request trình duyệt ngoài loopback. Không gọi Graph/SharePoint/Firebase/Expo thật. Mạng chỉ dùng cho Git fetch và registry npm/PyPI được cho phép bổ sung.

| Thành phần | Phiên bản đã xác minh |
|---|---|
| Python / Django | 3.12.14 / 5.2.17 |
| Node / npm | v24.21.0 / 11.19.0 |
| JDK | Temurin 21.0.12.1+1 tại D:/IHRMS_BuildTools/jdk/bin/java.exe |
| SQLite | thư viện 3.53.1, memory/file QA mới |
| SQL Server | backend microsoft, SQLEXPRESS cục bộ, ODBC Driver 17, DB test dùng một lần |

`java -version` ban đầu không khởi động vì executable không có trong PATH: exit tiến trình **N/A**. Đường dẫn JDK rõ ràng sau đó exit 0; không sửa PATH hệ thống.

### 2.2 Độ phủ thực tế

| Nhóm | Đã đọc/thăm dò | Chưa rà sâu hoặc chưa chứng minh |
|---|---|---|
| Security/config/common | permissions, data_access, files/storage/middleware/admin/logging/settings; uploads và phần BaseAudit/admin; role/cookie/CSRF/private-file | mọi nhánh Admin/restore/xóa mềm; mã hóa/server; lịch sử Git chứa bí mật |
| Portal/HR/lifecycle | phần chính finance/hr/documents/office_procurement/assets; lifecycle views; URL/template liên quan; sweep và Edge business | từng dòng mọi view/template/HCNS và mọi trạng thái workflow |
| Payroll/leave/attendance/contract | công thức Payroll, cấu hình, leave services/models phần chính, attendance services, gia hạn; probe cấu hình âm/ngày hiệu lực | master rate pháp lý, mọi biên dữ liệu và probe mới trên SQL Server |
| Office/asset/procurement | booking clean/save, approval, inventory export, phần model; self-approval/Excel/form thiếu thời gian | toàn vòng đời/import/export/quét mã độc |
| Assistant/M365 | parser/db_search/services/views/history/download, boundary m365_search, JS/chat/purge; 202 test mỗi backend, fuzz/benchmark/Edge | toàn Graph client/fallback/ACL/tệp thật, tải thực |
| Mobile | API/session/workspace boundary, session/api/cache/push/config, một số screen/token; matrix/gate/8 UAT | toàn renderer/native UI, thiết bị/iOS/font scale/screen reader/deep link/push; luồng sau UAT đỏ |
| Activity/task/recruitment | activity permissions, phần task/candidate model/caller; suite/URL sweep | toàn model/service/form |
| KPI/planning/project/org/reporting | guard trung tâm, reporting views/services, fixture/caller; suite/sweep/inventory | chưa đọc sâu mọi model/service |
| Ops/CI/docs | runner test/QA, backup/mock, CI, mẫu nhật ký/hướng dẫn | mọi script/migration/Word/PDF, restore/server thực |

Có **25 phân hệ**; test-inventory.json có thêm dòng __pycache__ runtime, không phải phân hệ. AST đếm 965 method, discovery thực 975 case (cấu trúc test/kế thừa). Đây **không phải line/branch coverage**. Kiểm kê/sweep không thay đọc sâu toàn mã.

### 2.3 Vệ sinh repository

- `hygiene.json`: 1 tệp >1 MiB — PROJECT_WORK_LOG.md (1.219.056 byte tại HEAD review); 227 binary theo heuristic NUL, chủ yếu ảnh/template/reference. Không tự dọn.
- 27 vị trí gán credential-pattern trong test/probe; không match private-key/GitHub-token/AWS-access-ID regex đã dùng. Chỉ lưu vị trí/loại, không giá trị; không chứng nhận không có bí mật.
- 20 tệp BOM/mixed CRLF-LF; không thấy U+FFFD, pattern mojibake hoặc pattern `?` thay chữ Việt của bộ quét. BOM PowerShell không tự là lỗi. Không đổi lịch sử.
- ignore-probe.json: .env/.env.production, src/db.sqlite3, media và APK/JKS dưới mobile được ignore. Tên giả src/random.sqlite3, APK ở gốc và test.keystore ở gốc chưa được ignore. Chưa phát hiện các tệp tương ứng đang tracked; đây là khoảng trống phòng ngừa, không phải bằng chứng rò rỉ.

## 3. Kết quả kiểm thử

### 3.1 Phase 1: lệnh và exit code thật

Python là `D:/QLHCNS/venv/Scripts/python.exe`; CWD E/source, npm tại E/source/mobile, Git tại repo. JSON đầy đủ: commands.json, extra-commands.json, extra-commands-browser.json, resume-commands.json, audit-commands.json, framework-final-exits.json.

| Lệnh | Exit | Kết quả/giới hạn |
|---|---:|---|
| git diff --check | 0 | đầu lượt; kiểm lại tài liệu trước commit |
| python -m pip check | 0 | dependency consistency đạt |
| python src/manage.py check | 0 | system check đạt |
| python src/manage.py makemigrations --check --dry-run | 0 | no changes; lần đầu có warning history do DB_NAME=:memory: bị ghép thành path |
| python E/framework_checks.py check | 0 | kiểm lại NAME memory trực tiếp, không warning |
| python E/framework_checks.py makemigrations --check --dry-run | 0 | no changes, không warning; không áp migration |
| python ops/run_tests.py --backend sqlite | 0 | **975 test**, unittest 1.168,072s, **skip 7** |
| python ops/run_tests.py --backend sqlserver, lần chưa cấu hình | 2 | runner từ chối SQLite, lỗi thiết lập harness |
| cùng SQL runner, cấu hình local/test rõ ràng | 0 | **975 test**, unittest 1.414,947s, không skip; DB test đã hủy |
| python ops/check_work_log_encoding.py | 0 | trên bản sao; kiểm lại nhật ký cuối trước commit |
| python ops/check_mobile_kpi_limit.py | 0 | frontend/backend 30 |
| python ops/sync_mobile_tokens.py --check | 0 | token khớp |
| python ops/check_ui_contrast.py | 0 | audit tĩnh, không thay browser/overlay alpha |
| npm ci --offline --ignore-scripts --no-audit --no-fund | 1 | ENOTCACHED: thiếu zod-validation-error-4.0.2.tgz; có EPERM cleanup |
| npm ci --registry=https://registry.npmjs.org/ --no-audit --no-fund | 0 | bản sao; không sửa lockfile nguồn |
| npm run typecheck | 0 | đạt |
| npm run lint | 0 | đạt |
| npm run check:input | 0 | **23 helper cases**; không kiểm picker native; log mobile-check-input.log |
| npx --no-install expo export --platform web | 0 | source hiện tại, CLI offline, không dịch vụ Expo |
| python -m pip_audit -r requirements.txt --vulnerability-service pypi --cache-dir E/pip-audit-cache --disable-pip --no-deps --format json | 0 | không ghi nhận advisory trong dependency liệt kê |
| npm audit --package-lock-only --registry=https://registry.npmjs.org/ --json tại mobile | 1 | **27 mục: 2 high / 24 moderate / 1 low** |
| cùng npm audit tại root | 0 | không advisory ở lockfile root |

Offline npm/lần SQL chưa cấu hình là **môi trường**; warning memory là **harness**, đã kiểm lại. Mobile audit là **rủi ro dependency**; UAT đỏ giữ nguyên. Chưa có baseline đủ để gọi mọi finding mới là regression của commit mới nhất.

### 3.2 Bảy SQLite skip

Sáu skip decorator được discovery mới tại runtime-skip-inventory.json; Activity gọi self.skipTest trong method (activity/tests.py:519). Tổng khớp log **7**, không lấy từ nhật ký cũ:

1. apps.planning.tests.PlanningUniqueConstraintTests.test_company_wide_annual_budget_with_null_department_is_unique — SQL Server coi NULL bằng nhau cho unique index, SQLite cho nhiều NULL.
2. apps.activity.tests.ActivityProposalConcurrentDecisionTests.test_only_one_of_two_simultaneous_decisions_is_saved — cần row-lock concurrency SQL Server.
3. apps.office.tests.ConcurrentBookingTests.test_room_concurrent_approvals_preserve_one_reservation — cần SQL Server row locking.
4. apps.office.tests.ConcurrentBookingTests.test_vehicle_concurrent_approvals_preserve_one_reservation — cùng lý do.
5. apps.portal.tests_review_20261008.ConcurrentGroupAReviewFixTests.test_f07_two_simultaneous_leave_submissions_create_one_request — cùng lý do.
6. apps.portal.tests_review_20261008.ConcurrentGroupAReviewFixTests.test_f10_two_simultaneous_generated_codes_are_unique — cùng lý do.
7. apps.portal.tests_review_hardening.ConcurrentDispatchTests.test_two_simultaneous_entries_preserve_both_numbers_and_trackings — cùng lý do.

Cả bảy chạy trong SQL suite 975 test không skip. Probe mới không tự trở thành test của SQL suite.

### 3.3 UAT và backup

Mobile runner dùng `--directory E/mobile-qa --url http://127.0.0.1:8832 --output E/<runner>`; resume_mobile.py cung cấp credential giả/chặn mạng ngoài, không bỏ auth/validation. Lượt chờ export trước gián đoạn timeout 20 phút chưa chạy UAT, không tính đạt.

| Runner | Exit | Quan sát |
|---|---:|---|
| ops/run_browser_uat.py --backend sqlite --output-dir E/browser-business | 0 | **471 assertions / 37 ảnh / 0 pageerror**, DB hủy; HR/hợp đồng/nghỉ/Dashboard/readiness của runner |
| ops/run_mobile_uat.py | 1 | login/me thành công rồi mất phiên khi tải Trang chủ; chưa hết luồng |
| ops/run_mobile_home_uat.py | 0 | **36 cases**, 12 mô phỏng KPI chữ 200%, 0 pageerror; ba palette/hai vai/theme/ba rộng; **API đọc fixture**, login/quyền thật |
| ops/run_mobile_settings_uat.py | 1 | không giữ Trang chủ sau login; chưa chứng nhận settings/password |
| ops/run_mobile_c_uat.py | 1 | timeout tab Thêm; chưa đủ 18 cấu hình |
| ops/run_mobile_c2_uat.py | 1 | không thấy Xem đầy đủ đơn nghỉ, snapshot đã về login |
| ops/run_mobile_p2_review_uat.py | 1 | mất tab Việc của tôi khi điều hướng |
| ops/run_mobile_workspace_uat.py | 1 | không giữ Trang chủ sau login; chưa chứng nhận 16 nhóm |
| ops/run_mobile_employee_uat.py | 1 | không giữ Trang chủ sau login; chưa hết luồng |
| E/assistant_edge.py | 0 | **40 checks / 16 ảnh / 0 pageerror**, hai vai ×390/1440×sáng/tối; Enter, search thật + notice/XSS giả lập |
| E/tabbar_visual.py | 0 | probe đo DOM thành công và xác nhận R2-09; exit 0 không có nghĩa UI đạt |
| ops/backup/Test-BackupSafety.ps1 -Kind Full -Scenario Express/Standard/Failure | 0 / 0 / 0 | sqlcmd mock, không backup DB vận hành |
| cùng runner -Kind Log | 0 / 0 / 0 | mô phỏng tương ứng |

R2-02 có vòng HTTP độc lập: 75 tuần tự đều 200, đồng thời 35×401/40×200; xác nhận 25 tuần tự đều 200, đồng thời 11×401/14×200. Không quy mọi timeout C/P2 cho duy nhất nguyên nhân này; UI sau điểm lỗi còn chưa kiểm.

**Chưa chạy** run_layout_alignment_audit.py, run_print_layout_uat.py, run_form_contract_uat.py, run_asset_cache_uat.py. Không đổi CSS/template/form/asset và không có baseline hai phiên bản. Không tuyên bố 0 vi phạm toàn route/vai/7 rộng/theme, contact sheet before/after hay PDF chuẩn.

### 3.4 Khoảng trống hồi quy

Mọi phân hệ có test hiện hữu, nhưng case ít ở project/KPI/reporting/asset/contract không chứng minh đủ luồng. Thiếu test chuyên biệt cho cấu hình tỷ lệ âm/khóa kỳ; concurrent native session SQLite; salary tương lai; formula export; HR mất FK khi POST sai; booking Admin thiếu thời gian; salary N+1; tabbar desktop. Probe mới giữ ngoài repo theo REVIEW. Chưa có line/branch coverage; mọi format HCNS/import/migration dữ liệu cũ/native accessibility chưa được chứng minh.

## 4. Trạng thái F-01…F-17

Nhóm A truy vết commit **29773d0**; regression tests_review_20261008.py chạy trong cả hai suite mới. Path bên dưới đều tính từ src/apps trừ khi ghi khác, line ở HEAD hiện tại.

| Mã | Trạng thái | Bằng chứng và giới hạn |
|---|---|---|
| F-01 | **Chờ quyết định** | portal/views/finance.py:124; focused-results.json/F01: Active được chọn, Probation/OnLeave không; chưa tìm thấy quyết định payroll hai trạng thái. Dashboard đếm nhóm này không tự là quyết định trả lương |
| F-02 | **Đã sửa** | portal/views/documents.py:111/:165/:210 dùng manage_office; regression :101 và dynamic gate đạt |
| F-03 | **Đã sửa theo quyết định** | security/data_access.py:93 mở Incoming/Outgoing cho active login; RBAC phần đầu/nhật ký20/10 Áp dụng ma trận quyền tài liệu đã duyệt; selector/matrix khớp; **không báo dùng chung là vượt quyền** |
| F-04 | **Chờ quyết định** | portal/views/office_procurement.py:461; financial-probes.json/F04 Finance tự duyệt được; HR/Director self-leave là ngoại lệ cũ; chưa thấy quyết định maker-checker chung |
| F-05 | **Chờ quyết định** | security/permissions.py:71, reporting/services.py:105; Finance HTTP200/Excel chứa CCCD giả; hrm/models.py:27 CharField. Chưa có quyết định che/xóa hoặc mã hóa cấp trường; không suy ra TDE/disk |
| F-06 | **Đã sửa** | finance.py:178/:280 cảnh báo thiếu salary/chặn zero basic; regression :158/:186 đạt. R2-01 là cấu hình sai khác phạm vi F-06 |
| F-07 | **Đã sửa** | leave/services.py:30 atomic/Employee lock; regression tuần tự :212, concurrent :431 đạt SQL Server |
| F-08 | **Sửa một phần** | Task có Dashboard _my_work.html:19, mobile/workspace.py:24 thêm menu. Web base.html:53 vẫn gate Excel bằng is_admin_user, sidebar thiếu một số duyệt/mua sắm; nhật ký12/10 chưa xác nhận đóng |
| F-09 | **Chờ quyết định hợp nhất** | permissions.py:67/:106; docs/Viec_Cho_Chu_Du_An_Quyet_Dinh.md giữ hai hợp đồng; HTTP /reports và /portal/reports khớp guard, không tái hiện vượt quyền từ việc tồn tại hai quyền |
| F-10 | **Đã sửa** | portal/views/hr.py:134 retry3; regression collision :240/concurrent :465 đạt SQL; generator :377 vẫn quét mã, chưa chứng minh hiệu năng sequence |
| F-11 | **Đã sửa** | lifecycle/views.py:120 khóa case rồi item/check Pending/Open; regression idempotency :257 đạt; chưa probe mới mọi transition |
| F-12 | **Chưa sửa** | common/uploads.py:106; upload-probe.json HTML giả đuôi png/docx/zip được nhận. PDF quyết định kiểm riêng/CSP attachment giảm rủi ro; chưa thử mã độc |
| F-13 | **Chưa sửa** | security/files.py:61 tra11model/14FileField; chưa thấy thiết kế model-ID/index riêng; chưa benchmark quy mô thật, không kết luận đang chậm thực tế |
| F-14 | **Chờ quyết định** | security/data_access.py:151; m365/models.py:8 chưa trạng thái published/draft; cần chốt có nội dung hạn chế/bản nháp trước khi gọi là sai policy |
| F-15 | **Đã sửa** | portal/views/hr.py:431 lọc Active; regression :315 đạt, không chọn Terminated chỉ vì start_date mới |
| F-16 | **Sửa một phần** | reporting/views.py:101 validate/type/tên noi-bo; regression :354 đạt. report_dashboard vẫn đếm OfficialDispatch trực tiếp, chỉ số InternalDirective chưa visible scope; cần chốt chỉ số, chưa chứng minh lộ nội dung |
| F-17 | **Chưa sửa** | leave/services.py:31/LeaveRequest.clean chưa chặn trạng thái; focused-results.json: user active có Employee Resigned vẫn tạo đơn. Inventory chưa có route hủy Pending riêng; cần chốt policy nghỉ việc/hủy |

Các dòng “regression :n” ở bảng trỏ tới `src/apps/portal/tests_review_20261008.py:n`. Chưa suy quyết định mới từ quyền kỹ thuật hoặc checkbox tài liệu.

## 5. Finding mới

### R2-01 — Cao — Tỷ lệ bảo hiểm âm tạo lương sai, kỳ vẫn khóa được

- **Vị trí:** `src/apps/portal/views/finance.py:439`, `src/apps/payroll/models.py:476`, `:512`; kiểm khóa tại `src/apps/portal/views/finance.py:280`.
- **Trigger/tái hiện:** Finance POST form_type=insurance với employee_social_insurance_rate=-10, các tỷ lệ khác 0. Harness tạo đủ cấu hình/nhân viên giả, tính basic 1.000.000 rồi khóa qua view thật. `E/financial_probes.py`, `financial-probes.json`: POST302, rate=-10.00, gross=1.000.000, insurance=-100.000, net=1.100.000, **period=Locked**.
- **Tác động:** master data sai tạo số tiền sai cho mọi dòng sử dụng; tính lại cùng cấu hình sai không phát hiện invariant bị vi phạm.
- **Gợi ý:** kiểm server-side miền giá trị master data trước ghi và invariant kết quả tiền trước khóa; thêm regression calculate/lock. Không tự đổi tỷ lệ nghiệp vụ thực.
- **Chắc chắn:** **Đã tái hiện** SQLite; chưa chạy probe mới này trên SQL Server. Không cần quyết định để từ chối tỷ lệ âm; tỷ lệ pháp lý do Finance/chủ dự án duyệt.

### R2-02 — Trung bình — SQLite cạnh tranh ghi phiên thành lỗi hết phiên mobile giả

- **Vị trí:** `src/apps/mobile/middleware.py:15`, `:28`, `:61`; `mobile/src/session.tsx:42` xử lý401 bằng quên phiên.
- **Trigger:** cùng bearer giả gửi đồng thời me/attendance/leaves/notifications/leave-options, mỗi request ghi security_last_activity. `E/session_concurrency.py`, `session_concurrency_confirm.py`: vòng đầu tuần tự75×200, đồng thời35×401/40×200; xác nhận tuần tự25×200, đồng thời11×401/14×200.
- **Bằng chứng:** session-concurrency-confirm.json: phiên vẫn tồn tại/hash còn đúng;11 UpdateError có context database locked. Instrumentation chỉ ghi loại lỗi, không token; không vá nguồn.
- **Tác động:** UI có thể quay login dù phiên hợp lệ. Không quy mọi timeout C/P2 cho duy nhất nguyên nhân này.
- **Gợi ý:** phân biệt khóa DB/cập nhật phiên thất bại với phiên đã thu hồi; xử lý concurrency theo backend và thêm regression HTTP đồng thời, giữ chốt không hồi sinh phiên logout.
- **Chắc chắn:** **Đã tái hiện**, điều kiện SQLite. Chưa tái hiện SQL Server/native thật. Chủ dự án cần xác định phạm vi hỗ trợ SQLite, đồng thời ổn định QA trước dùng kết quả UAT.

### R2-03 — Trung bình — Lương tương lai được hiển thị là lương hiện tại

- **Vị trí:** `src/apps/mobile/views.py:192`; `mobile/src/app/personal-profile.tsx:34`; điều kiện cùng kiểu tại `src/apps/portal/views/finance.py:417`.
- **Tái hiện:** qua HR salary form đặt mức200 từ01/01/2099 khi mức100 còn hiệu lực tới31/12/2098. Form đánh phiên bản cũ Ended ngay. Mobile my-profile trả200/2099, UI ghi “Lương cơ bản hiện tại”. `focused-results.json/future-salary-real-form` chứa hai khoảng không chồng lấn; không chèn tắt validation.
- **Tác động:** thông tin hiện hành gây hiểu nhầm. Payroll có _effective_salary_map theo khoảng ngày riêng; **chưa có bằng chứng finding này tính sai lương kỳ hiện tại**.
- **Gợi ý:** chọn theo ngày hiệu lực/end_date tại ngày nghiệp vụ, kể cả phiên bản Ended do đặt mức tương lai; hoặc đổi nhãn nếu chủ ý là mức mới nhất khai báo.
- **Chắc chắn:** **Đã tái hiện** API mobile; web đọc mã cùng điều kiện, chưa browser case riêng. Chỉ cần quyết định nếu muốn đổi nghĩa “hiện tại”.

### R2-04 — Trung bình — Excel kiểm kê diễn giải dữ liệu nhập thành công thức

- **Vị trí:** `src/apps/portal/views/assets.py:248`, `:275`.
- **Tái hiện:** InventorySession giả office_name=`=1+1`; HR tải Excel qua route thật. financial-probes.json/inventory_export: HTTP200, A2 data_type=**f**, giữ công thức. Chỉ dùng openpyxl đọc ô; không mở Excel/thực thi công thức/mạng ngoài.
- **Tác động:** dữ liệu nhập được coi là công thức, tạo bề mặt formula injection khi người khác mở. Chưa chứng minh external-link/exfiltration exploit.
- **Gợi ý:** ghi trường văn bản không tin cậy bằng kiểu text ở mọi export, theo cơ chế reporting/services hiện có; test kiểu ô workbook.
- **Chắc chắn:** **Đã tái hiện** ô công thức; thực thi phụ thuộc ứng dụng/chính sách mở workbook. Không cần đổi quyền/nghiệp vụ.

### R2-05 — Thấp — POST sửa nhân viên thiếu phòng ban trả500

- **Vị trí:** `src/apps/portal/views/hr.py:176`, `:202`.
- **Tái hiện:** HR_MANAGER POST rỗng tới /portal/hr/employees/1/edit/ trên DB giả. _save_employee_form đổi instance trước validation; sau khi bắt lỗi, render đọc employee.department đã None. focused-results.json/employee-empty: RelatedObjectDoesNotExist, HTTP500. Đã kiểm lại không có transaction bọc của sweep.
- **Tác động:** mất form/thông báo validation khi thiếu trường; chưa thấy hồ sơ bị lưu sai trong ca này.
- **Gợi ý:** giữ instance render nhất quán sau POST sai hoặc dùng form validation; regression trường thiếu/FK sai.
- **Chắc chắn:** **Đã tái hiện**; không khẳng định form hợp lệ thường ngày luôn lỗi. Không cần quyết định.

### R2-06 — Thấp — Form Admin booking thiếu thời gian gây TypeError

- **Vị trí:** `src/apps/office/models.py:168`, `:202`.
- **Tái hiện:** superuser QA POST rỗng tới /admin/office/roombooking/add/ và vehiclebooking/add/. ModelForm gọi clean với None; end_time <= start_time gây TypeError. focused-results.json/admin-roombooking và admin-vehiclebooking: HTTP500.
- **Tác động:** không trả validation hữu ích; chưa tạo reservation sai trong ca này.
- **Gợi ý:** xử lý thiếu/sai trường trước so sánh, giữ kiểm overlap/khóa tài nguyên; test form Admin.
- **Chắc chắn:** **Đã tái hiện** HTTP SQLite, không phải lỗi overlap dữ liệu hợp lệ. Không cần quyết định.

### R2-07 — Trung bình — Advisory mobile chưa được audit đúng lockfile trong CI

- **Vị trí:** `mobile/package-lock.json:6087` (Expo CLI), `:11512` (zod); `.github/workflows/ci.yml:79`; audit root tại`:58`.
- **Bằng chứng:** E/audits.py và npm-audit-mobile.log:27mục,2high gồm zod/chuỗi Expo CLI,24moderate/1low,exit1. Root lockfile audit exit0 không bao phủ lockfile mobile riêng.
- **Tác động:** rủi ro dependency/toolchain chưa có gate tương ứng; mức high của npm không tự chứng minh khai thác runtime IHRMS.
- **Gợi ý:** đánh giá reachability, chọn nâng tương thích Expo và thêm audit đúng workspace; không force-fix/hạ SDK tự động.
- **Chắc chắn:** **Đọc mã, chưa tái hiện khai thác**; audit registry đã chạy thực. Chủ dự án chọn nâng phiên bản/chấp nhận rủi ro có thời hạn/ngưỡng gate.

### R2-08 — Trung bình — Danh sách lương N+1 phòng ban, chưa phân trang

- **Vị trí:** `src/apps/portal/views/finance.py:417`; `src/apps/portal/templates/portal/finance_salary_list.html:16`.
- **Tái hiện:** queryset select_related employee nhưng template đọc employee.department từng dòng. E/scope_perf.py, salary-query-growth.json:13dòng→13 SELECT phòng ban/26query tổng;26dòng→26 SELECT phòng ban/35query tổng. Tổng có overhead/warm middleware khác; số SELECT phòng ban tăng đúng theo dòng.
- **Tác động:** chi phí tăng theo toàn bộ danh sách; chưa đo latency/throughput ở quy mô thật. Nhật ký đã ghi N+1 này; đây là xác minh lại, không gán regression cho commit assistant mới nhất.
- **Gợi ý:** nạp phòng ban cùng queryset, phân trang và test query-growth.
- **Chắc chắn:** **Đã tái hiện** SQLite. Ưu tiên theo quy mô, không cần nới quyền.

### R2-09 — Thấp — Tabbar mobile hiện dạng thô trên desktop web

- **Vị trí:** `src/templates/base.html:226`, `src/templates/ui/mobile_tabbar.html:11`, `src/static/css/mobile_shell.css:38`, `:104`.
- **Tái hiện:** QA mở /assistant/ ở1440px; template luôn render, CSS layout chỉ có max-width1023 nhưng không ẩn selector ở desktop. E/tabbar_visual.py:390px display=grid;1440px display=block, cao180px. Ảnh tabbar-visual/1440.png và assistant desktop xác nhận link thô dưới nội dung.
- **Tác động:** điều hướng trùng/khoảng thừa, trái chú thích mobile-only. Không phải UI Expo native.
- **Gợi ý:** trạng thái ẩn mặc định desktop/bật ở breakpoint; khi FIX chạy layout/print gate theo AGENTS.
- **Chắc chắn:** **Đã tái hiện** DOM/ảnh Edge; chưa toàn route/vai/7rộng. Không cần đổi policy nếu giữ mobile-only.

## 6. Ma trận quyền động

### Web/Admin

url-inventory.json:662pattern,660concretize được; hai regex app-list/catch-all Admin chỉ kiểm kê. permission-matrix.csv:18.480GET/POST=660×14actor×2method. Actor gồm11mã vai hiện có, NO_ROLE, STAFF_ONLY, ANONYMOUS. SUPER_ADMIN fixture có is_superuser=True; SYS_ADMIN có is_staff. Chưa đủ mọi biến thể role-only/linked/unlinked/staff.

Int dùng1/string mẫu; nhiều object chưa fixture trả404 nên **không chứng minh IDOR mọi model/trạng thái**. Sweep test client không enforce CSRF để đo guard role; CSRF thật probe riêng. Sweep có transaction rollback; form disposal500 bị loại sau autocommit trả200 (outer transaction làm lỗi harness).

permission-expectations.json:182checks tại13entrypoint×14actor,0mismatch với guard/chính sách đọc đã duyệt; chưa oracle toàn660callback. Ba POST anonymous200 là form login Admin/portal và service-worker.js, chưa bằng chứng ghi nghiệp vụ trái phép. Không gọi HTTP200 là bypass.

Private-file:10truy cập,hai chủ thể×5vai; employee/manager theo cây, HR không mặc nhiên xem tệp nghỉ người khác cây, superuser giữ scope leave. Sai chủ404; được phép có sandbox/nosniff/no-store. IDOR mới chưa đủ từng contract/payroll/candidate/asset; phần đó dựa thêm suite và sweep.

### Mobile

19route API;532GET/POST trong matrix chung,152case token bổ sung(19×4mode×2method). Mode:no-token/expired/invalid/other-user(HR_OFFICER QA hợp lệ); không giả token thật. Method sai có thể405 trước auth.19callback csrf_exempt là bearer API, middleware thay session cookie. Cookie-only leaves/workspace401; cookie POST assistant/leave thiếu CSRF403; không coi exemption bearer là bypass khi cookie bị từ chối.

Đã đọc cấp/thu hồi/hash mật khẩu/expiry/idle, SecureStore native/in-memory web, cache files cleanup, HTTP private-host QA, payload/scope.48method test mobile chạy trong cả hai suite; chưa stress mọi race logout/token transfer hoặc deep link/cache trên thiết bị thật.

### Chatbot

chatbot-seven-types.json:91checks=13QAuser×7loại,0mismatch số fixture/quyền: công văn/quyết định/nghỉ/tài liệuApproved/ứng viên/tài sản/báo cáo hoạt động(SharePoint tắt→không DBresult). chatbot-scope.json có tập/result chi tiết ba selector. Tập nhỏ dưới giới hạn trả kết quả; không suy mọi tìm kiếm trả toàn bộ tập được phép.

SharePoint chỉ mock trong202test và đọc boundary origin/path/root/chữ ký/reauthorize download, chưa ACL thật. Incoming/Outgoing/activity_report dùng chung theo quyết định20/10; leave/decision theo scope riêng, không mở raw private folder theo tên.

20fuzz(20.000ký tự/control/NFC-NFD/ngày sai/năm0000-9999/ngoặc kép/nhiều mốc) trả200,không500/treo;chuỗi cắt500 theo code/spec. Không fuzz exhaustively Unicode.

assistant-benchmark.json:5lượt ask, mỗi lượt thực quét5000công văn+5000tài liệu+5000quyết định;318,824/300,361/345,663/356,501/339,450ms,median339,450ms. Instrument rank đếm candidates; có hoạt động QA khác, không đại diện SQLServer/Graph/multi-user/SLO.

## 7. Điểm làm tốt đã xác minh

- Hai backend975case; skip đối chiếu điều kiện, không thêm skip để xanh. F-02/06/07/10/11/15 có code guard/lock và regression thực; F-03 khớp policy mới.
- Cookie-only không authenticate mobile; CSRF web chặn; private leave ngoài cây404 kể cả HR/superuser.
- Source UAT/production có guard DEBUG/HTTPS/weakkey/wildcardhost, Axes/idle/no-store; không xác nhận cấu hình máy chủ đang dùng.
- Assistant textContent không thực thi chuỗi script/img ở ca Edge; notice/time/nguồn tắt đọc được sáng/tối390/1440.
- Home36cấu hình+12môphỏng chữ lớn có phạm vi KPI; không thay native font scaling.
- Sáu backupmock chứng minh lỗi sqlcmd/verification không bị báo thành công; retention sau backup kiểm. VERIFYONLY không thay restore drill.

## 8. Việc chưa kiểm và giới hạn

1. Graph/SharePoint/M365/Firebase/Expo/push thật bị cấm; mock/code không xác nhận consent/ACL/metadata/MIME/mạng thật.
2. Không kết nối server vận hành/IIS/TLS/ACL/backup/restore thật; chưa biết SHA deploy. Không đổi firewall/registry/ACL.
3. Không APK/Android/iPhone/native screen reader/picker/secure-storage device test; không chứng nhận thiết bị thật.
4. Bảy UAT mobile đỏ, phần sau điểm lỗi chưa đạt; không dùng kết quả lịch sử thay thế.
5. Chưa đọc từng nhánh mọi migration/HCNS/admin/import/service/template của25phân hệ; không review100%.
6. Chưa layout full-route/role/7widths/2themes, PDFmẫu chuẩn/form-contract/cache2phiên bản/contactsheet before-after.
7. SQLite bench/concurrency mới không chứng minh SQL/Graph/quy mô production; SQL suite hiện hữu không thay probe mới.
8. national_id là CharField không mã hóa cấp trường ORM; chưa kiểm TDE/disk/backup encryption/key lifecycle/ACL.
9. SearchQueryLog lưu câu hỏi tự do có thể chứaPII,không result;session giữ20lượt đầy đủ và invalidates theo policy/role/cây. Retention/chu kỳ chưa chốt; không purge --apply.
10. Assistant throttle30/phút dùng cache default từng process, chưa shared cache/multiworker test; rủi ro đã ghi nhật ký, không finding disclosure mới.
11. Audit chỉ database advisory thời điểm chạy/dependency liệt kê; chưa exploit reachability/zero-day.
12. Đọc CI4job(backend/frontend/mobile/backup-command-tests),chưa truy vấn/chứng nhận Actions SHA. Hướng dẫn có chỗ còn “ba job”; cần đợt docs riêng.

Đối chiếu mẫu nhật ký với git show --stat bae8450/b744a12/29773d0 thấy code/test/spec/log tương ứng; không xác minh mọi UAT lịch sử hoặc dùng lại số test/ảnh cũ làm kết quả mới.

## 9. Thứ tự xử lý và bàn giao

**FIX riêng ưu tiên:** R2-01/regression khóa kỳ;R2-02/concurrent-session-revocation rồi chạy lại7UATđỏ;R2-04text export. Tiếp theo R2-03/05/06/08/09 với gate tương ứng. Không viết bản vá trong REVIEW.

**Chủ dự án quyết:** F-01Probation/OnLeave;F-04maker-checker;F-05CCCD/mã hóa;F-08/09navigation/reporting;F-14CompanyMedia draft;F-16chỉ số tổng;F-17nghỉ việc/hủy đơn;phạm viSQLite;dependencyR2-07;cachechung/retentionassistant.

**Ghi nhận:** F-12magicbytes/malware;F-13file-query design khi có số liệu;test khoảng trống thay vì chỉ đếm tổngcase. Sau FIX chạy nguồn cuối/browser luồng ảnh hưởng và UI/print gate bắt buộc; SIT/restore/nativeQA riêng trước nghiệm thu tương ứng.

### Chỉ mục bằng chứng

- phase01.py/commands.json/manifest.json/hygiene.json: nền/gate. Không chạy lại toàn phase01 vào thư mục hiện có để tránh ghi đè/làm lại.
- probe.py/permission-matrix.csv/mobile-token-matrix.json/url-inventory.json/permission-expectations.json: memoryDB/tài khoản giả/rollback;không dùng server thật.
- focused.py/financial_probes.py/scope_perf.py và JSON cùng tên: finding tái hiện. Chạy PythonUTF8=1/PYTHONIOENCODING=utf-8 với interpretervenv;script đặt memoryDB trực tiếp. Không dùng configuredDB.
- session_concurrency*.py và JSON: fileDBmới dùng tên cố định cho lượt đã chạy; nếu lặp phải chọn tênDB/output mới, không chạy vào file đã có.
- resume_mobile.py/resume-commands.json/guards/mobile-qa/cácthưmụcrunner: reuseQA,no reseed. Credential bộ nhớ đã kết thúc; lặp cần cấp credential giả mới/adapter,không đọcfileaccounts/mượnphiênthật.
- assistant-edge/tabbar-visual/browser-business/run_mobile_home_uat:ảnh/JSON mới. Đã xem tay assistant390tối,assistant1440sáng,Home390tối;chưa xem tất cả ảnh.
- audit-commands.json/pip-audit.log/npm-audit-mobile.log/npm-audit-root.log:registry audit;không token/password.
- PROGRESS.md/summary.json/delivery.json(saucommit):checkpoint/kếtquả/SHA. Thư mục chứa DB/media/marker **giả** để tái hiện,không backup dữ liệu vận hành.
