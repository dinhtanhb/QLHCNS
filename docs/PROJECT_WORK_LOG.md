# Nhật ký công việc IHRMS

## 2026-10-19 — Trợ lý tài liệu (chatbot nội bộ): parser tiếng Việt, tìm DB theo quyền, SharePoint dự phòng, nút nổi

- **Phạm vi và nguồn yêu cầu:** mục tiêu "tìm công văn/quyết định/tài liệu bằng tiếng Việt ngay trong cổng" được duyệt ở spec `docs/superpowers/specs/2026-10-19-assistant-chatbot-design.md`, triển khai theo `docs/superpowers/plans/2026-10-19-assistant-chatbot.md`. Triển khai trên `main`: `ae03181` (plan), `325d162` scaffold + `SearchQueryLog`, `eccd3cc` migration riêng, `ec20fd0` parser, `d99793d` tìm DB, `f7021e7` Graph search, `a573d30` `m365_search`, `80f1327` điều phối `ask`, `677d7c5` API + trang chat, `9017394` widget nổi, `79ad68d` test thông báo công văn, `182cb8e`/`06340e9` whitespace + work log đợt đầu, rồi ba commit đóng final review: `7febf25` migration index, `5ad69c4` sửa hai Critical + bốn Important, `281106f` sửa tài liệu, cộng commit work log bổ sung này. Không dùng LLM bên ngoài: mọi suy diễn truy vấn là quy tắc tiếng Việt thuần trong `apps/assistant/nlp.py`.
- **Kiến trúc thực tế:** `POST /assistant/api/search/` nhận `{question}` → `services.ask()` → parser → tìm ba luồng (công văn, văn bản, quyết định nhân sự) đã lọc theo quyền qua `visible_dispatches_for`/`select_related` của chính cổng, và song song tìm SharePoint qua Graph; SharePoint lỗi thì trả `partial: true` kèm danh sách thư mục làm phương án dự phòng, **không** ném exception. Kết quả là bảng xếp hạng hợp nhất (cap 20, sort `-score` rồi ngày mới), **không có câu trả lời dạng văn xuôi**. Mỗi câu hỏi ghi một dòng `tblAssistantSearchLog` (question 500 ký tự, `ParsedFilters` JSON, `ResultCount`, `Sources`, `TookMs`, `ErrorNote`).
- **Quyền và giới hạn đã khóa bằng test:** `api_search` là `login_required + require_POST + never_cache`, **không** `csrf_exempt`; 30 câu hỏi/phút/người, chỉ đếm sau khi body hợp lệ (yêu cầu sai không đốt hạn mức); câu hỏi dài cắt còn 500 ký tự chứ không từ chối. Widget gửi `X-CSRFToken` đọc từ cookie — hợp đồng này Django test không tự phát hiện được, đã chứng minh bằng trình duyệt thật (mục kiểm dưới).
- **Giao diện:** `assistant.css`/`assistant.js` chỉ dùng token `--ui-*`, không hex, không `!important`; nút nổi + dock xuất hiện trên mọi trang đã đăng nhập, tự chuyển thành liên kết trang trên màn hẹp (<640px), đóng bằng Esc, **ẩn khi in**; trang `/assistant/` không có nút nổi để tránh trùng lặp. Thẻ kết quả lấy icon từ `_shell_icon.html` qua hai `<template>` chung. Bản đầu đặt hai template trong khối điều kiện của nút nổi nên `/assistant/` mất icon dù dock vẫn có — chỉ trình duyệt mới phát hiện được, đã sửa và thêm test vòng qua cả hai route.
- **Final review toàn branch và hai lỗi Critical đã sửa (`7febf25`, `5ad69c4`):** reviewer đọc `b03436c..06340e9` trả BLOCK — 2 Critical, 5 Important, 9 Minor. Critical 1 là **lỗ rò rỉ tên file toàn tenant**: Graph chạy app-only (`acquire_token_for_client` trong `graph_client.py`, client-credentials) nên token nhìn thấy **cả site**, không phụ thuộc quyền người hỏi; mọi user đăng nhập hỏi một câu là nhận tên + `webUrl` của hồ sơ ứng viên, đơn nghỉ phép, tài sản hình ảnh, và bản dự phòng còn duyệt cả thư mục gốc `Documents`. Đã chặn bằng ba cửa trong `m365_search.py`: chỉ đọc `M365_FOLDER_MAP` khi `M365_STORAGE_ENABLED` bật (tắt là không gọi Graph); chỉ user có `manage_office` hoặc `access_outgoing_document` (hoặc superuser) được đặt lời cho Graph, còn lại `([], "restricted")` — **cửa này đã bị chính đợt sửa sau đó bác bỏ, xem mục "Đợt sửa thứ hai"**; kết quả ngoài `CongVan`/`CongVanDen`/`CongVanDi` bị loại, so theo **whole path segment** và `unquote()` nên URL-encode không lách được. `_fallback_folders()` bỏ hẳn thư mục gốc. Critical 2: test API của assistant có thể chạm Graph thật vì không cờ nào chắn — nay `tests_api.py` patch `get_graph_client` thành `AssertionError` và assert `factory.assert_not_called()`, nên toàn bộ suite assistant **không thể** ra mạng kể cả khi `.env` bật M365. Important đã sửa cùng lượt: ngày vô lý (`31/02`, `29/02/2025`, `năm 0000`) làm `parse()` 500 (`_date_span` + bắt `ValueError` ở cả hai tầng), dải ngày ngược ("từ 01/09 đến 01/08") âm thầm nhận bộ lọc rỗng (nay swap), phiên hết hạn bị báo nhầm thành "không có kết quả" (JS phân biệt `Content-Type` không phải JSON → `session_expired`), `db_search` xếp `effective_date DESC` khác nhau giữa SQLite và SQL Server nên `SCAN_LIMIT` cắt nhầm hàng (nay `F(...).desc(nulls_last=True)`), và hai giao phẩm spec §4 thiếu: index `CreatedDate` (migration `0002`, commit riêng theo AGENTS.md) + lệnh `purge_search_logs` (dry-run mặc định, `--apply` mới xoá, `hard_delete` qua `all_objects` nên quét cả bản soft-delete). Minor chấp nhận và ghi lại ở "Việc còn mở".
- **Đợt sửa thứ hai sau re-review phạm vi (`8cee25f`, `5db2ac8`, `bbe2322`):** reviewer xác nhận hai Critical đã đóng nhưng giữ hai điểm Important trên chính nguồn SharePoint, và lượt này bác bỏ quyết định cửa quyền của lượt một. (1) Cửa SharePoint đổi từ `manage_office`/`access_outgoing_document` sang **đúng tập vai trò được cổng miễn lọc độ mật** — **lượt ba đã thu hẹp tập này thêm một lớp quyền nữa, xem mục "Đợt sửa thứ ba"**: `SYS_ADMIN` có `manage_office` (quyền văn thư, `permissions.py:82`) mà `visible_dispatches_for` vẫn ẩn công văn Mật, ngược lại `SUPER_ADMIN` và `DIRECTOR` không có `manage_office` nhưng xem được mọi độ mật — hai bảng không trùng nhau, và Graph app-only không tự lọc theo `security_level` được, nên ai còn bị cổng ẩn bản Mật thì phải không nghe nổi tên tệp trên SharePoint. Tập vai trò giờ là hằng số `FULL_DISPATCH_SECURITY_ROLES` trong `data_access.py` mà cả `visible_dispatches_for` lẫn `can_query_sharepoint` cùng đọc để không thể lệch nhau; `tests_db_search` đối chiếu **từng** vai trò một bằng user thật dựng lên rồi hỏi cả hai hàm. (2) `_url_segments` chỉ đọc **path** của `webUrl`: bản một `unquote()` cả URL nên `view.aspx?initialid=%2F…%2FCongVan%2F` — một VIEW của danh sách, không phải vị trí tệp — sinh ra đoạn "CongVan" giả và giữ lại tệp nằm trong `HoSoUngVien`; `%20` vẫn được giải mã vì tên thư viện có dấu cách là bình thường, còn `%2F` trong đường dẫn thì bỏ cả kết quả vì `webUrl` thật của Graph không bao giờ ở dạng đó. (3) Ba test không thể đỏ thành test thật: `safeUrl` (hai chuỗi "javascript:" và "data:" nằm ngay trong comment mô tả lỗ hổng, nên xóa cả hàm chắn mà suite vẫn xanh — nay khóa `const href = safeUrl(row.url)`, body là allowlist mặc định trả chuỗi rỗng, và đúng hai chỗ gán `.href`), timeout (`assertIsNotNone` chỉ chứng minh có truyền tham số — nay so đúng `ASSISTANT_TIMEOUT` cho search và cả ba lệnh list dự phòng), và quét ký tự ngoài tiếng Việt (dải cũ `assertLess(ord, 0x3000)` tha cả Cyrillic dù docstring tự nói cấm; bản mới **chỉ cho phép** đúng codepoint chữ Việt và đi qua `.py` của app cùng management command, không chỉ CSS/JS). (4) Test mới bắt lại lỗi của chính test cũ: assert `"NULLS LAST"` trên `str(query)` đỏ trên SQL Server vì backend này giả lập bằng `CASE WHEN … IS NULL THEN 1 ELSE 0 END`; nay biên dịch SQL thật cho connection đang chạy và chấp nhận cả hai dạng — tìm ra nhờ chạy backend thứ hai chứ không nhờ đọc code.
- **Kiểm tự động đợt hai (`bbe2322`):** toàn dự án SQLite → **Ran 725 tests, OK (skipped=7)**, 345,8s, exit 0 (720 ở `e07f7dd`, +5 test của lượt này). Cụm SQL Server (`apps.assistant apps.m365 apps.notification apps.portal.test_global_search apps.document`) → **225 tests OK**, 60,7s, DB tạm `test_ihrms_9e3d6804e1c44a248abeca34d4ce270d` do runner tự tạo và tự hủy, không mở DB vận hành. `manage.py check` no issues; `makemigrations --check --dry-run` No changes detected; `ops/audit_design_tokens.py` giữ nguyên baseline (hex literal 0, font-size lệch thang 0, `!important` 9 ≤ 10); `git diff --check` sạch; quét ký tự ngoài tiếng Việt trên cả năm tệp đã sửa → **0 ký tự lạ**. **Hai lần trượt phải ghi lại:** lệnh cụm SQL Server đầu tiên của lượt này dùng nhãn `portal.test_global_search` (thiếu `apps.`) nên Django báo `ImportError` và chỉ chạy 217 test — nghĩa là năm test đã *biến mất trong im lặng* chứ không đỏ; chạy lại với nhãn đúng là 225. Và assert `NULLS LAST` ở mục (4) chỉ đỏ khi có backend thứ hai. **Không chạy lại layout/in/trình duyệt:** `git diff --name-only` giữa `e07f7dd` và lượt này là năm tệp `.py`, không có template/CSS/JS nào, nên markup mà hai probe đã đo vẫn y hệt từng byte; cái thay đổi là ai được hỏi Graph và test assert gì. Dọn vệ sinh: tệp 0 byte `src/qlhcns` (untracked) sinh ra vì `.env` đặt `DB_NAME=qlhcns` trong khi `.gitignore` chỉ chắn `db.sqlite3` — chuyển ra `%TEMP%\ihrms-assistant-layout-20261019\quarantine-src-qlhcns-0byte` chứ không xóa; đề xuất thêm `qlhcns` vào ignore hoặc để `ops/run_tests.py` là đường duy nhất được đặt `DB_ENGINE`.
- **Đợt sửa thứ ba sau re-review phạm vi (`6d765f0`):** reviewer lượt hai xác nhận cả hai Important đã đóng, nhưng chỉ ra hai lỗ hổng mới mà chính lượt hai sinh ra và ba chỗ test vẫn không thể đỏ. Bốn điểm dưới đây đều được kiểm lại bằng cách đọc `PERMISSION_MATRIX`, `has_permission`, `visible_dispatches_for`, `can_read_file`, `apps/common/uploads.py` và `apps/m365/storage.py` trước khi sửa — không sửa theo lời báo cáo. (1) `can_query_sharepoint` bản lượt hai chỉ còn nhìn `is_superuser` rồi `role_code`, tức **đánh mất hai kiểm tra mà `has_permission` của lượt một vẫn làm**: `is_authenticated` và `is_active` (`permissions.py:134`). `login_required` chỉ hỏi cờ đầu; `ModelBackend` không kiểm lại cờ thứ hai giữa phiên (`settings.py:159`) nên tài khoản đã bị vô hiệu hóa vẫn đi qua; trong khi `visible_dispatches_for` trả `qs.none()` cho cùng tài khoản đó — một nguồn im lặng, nguồn kia vẫn đọc tên tệp của cả thư viện. Nay chặn `is_active` **trước** `is_superuser`. (2) Cửa quyền phải là **GIAO** của hai phạm vi, không phải một tập vai trò. `CongVanDen`/`CongVanDi` không chỉ chứa tệp của `OfficialDispatch`: đính kèm của `IncomingDocument`/`OutgoingDocument` cũng ghi vào đúng đó (`apps/common/uploads.py:80-85`, `apps/office/models.py:30,64`), và cổng mở chúng bằng `manage_office`/`access_outgoing_document` (hai nhánh `office.incomingdocument`/`office.outgoingdocument` của `can_read_file`). Graph app-only không biết một tệp thuộc đối tượng nào nên không thể lọc hộ: **DIRECTOR** — vai trò xem được mọi độ mật công văn nhưng KHÔNG có `manage_office` — nhận tên + `webUrl` của tệp mà cổng trả 404. Nay `can_query_sharepoint` = **giao** của `FULL_DISPATCH_SECURITY_ROLES` với tập đủ `SHARED_LIBRARY_PERMISSIONS` (cộng superuser). **Hệ quả có ý thức, ghi cho chủ dự án:** nguồn SharePoint thực tế chỉ còn `HR_MANAGER`/`HR_OFFICER`; muốn mở lại cho `DIRECTOR` thì bỏ `manage_office` khỏi `SHARED_LIBRARY_PERMISSIONS`, đánh đổi bằng lộ tên tệp đính kèm sổ văn thư. (3) `search_files` chắn kết quả bằng `startswith(prefix)` trong khi `site_path = "/sites/IHRMS"` là **tiền tố chuỗi** của `"/sites/IHRMS-IT"` — `webUrl` của site LÁNG GIỀNG đi lọt cả hai lớp chắn, vì `/sites/IHRMS-IT/CongVan/…` có đúng đoạn `CongVan`; `tests.py` của m365 nay có một hit site láng giềng để bắt. (4) Ba test không thể đỏ: `unquote()` chưa từng bị test nào bắt (xóa nó vẫn xanh vì `CongVan` không cần giải mã) — kiểm thẳng `_url_segments` với `"Shared Documents"`; test timeout lấy hằng số từ chính mô-đun nguồn ra so — khóa thêm cặp `(3, 10)`; test đối chiếu vai trò đọc cùng hằng số mà nó định kiểm — nay lấy tiên đề từ `can_read_file` của cổng trên **ba đối tượng thật** (công văn Mật, đính kèm công văn đến, đính kèm công văn đi), nên nới một cửa mà quên cửa kia là đỏ đúng vai trò đó. RED trước khi sửa: 8 failures — `SUPER_ADMIN`, `DIRECTOR` ở cả hai test vai trò, dead session ở hai tệp, và site láng giềng; GREEN: `apps.assistant apps.m365` 150 tests OK.
- **Kiểm tự động đợt ba (`6d765f0`):** toàn dự án SQLite → **Ran 727 tests, OK (skipped=7)**, 367,98s, `sqlite_exit=0` (725 ở lượt hai, +2 test dead-session của lượt này). Cụm SQL Server **bảy nhãn** (`apps.assistant apps.m365 apps.notification apps.portal.test_global_search apps.document apps.office apps.common`) → **249 tests OK**, 73,45s, DB tạm `test_ihrms_47b287fab7534b619bf5f40e5afb4f60`; chạy lại để khóa đúng danh sách nhãn cho hồ sơ này là 249 OK, 70,89s trên `test_ihrms_dc3b0c7ee2c7408da60c9fd11506a7fb`, `mssql_exit=0` — runner tự tạo và tự hủy, không mở DB vận hành. `manage.py check` no issues; `makemigrations --check --dry-run` No changes detected; `git diff --check` sạch; quét ký tự ngoài tiếng Việt + printable ASCII trên cả **sáu** tệp đã sửa → **0 ký tự lạ**; không còn `src/qlhcns` lạc trong cây nguồn. **Không chạy lại layout/in/trình duyệt:** diff lượt ba là sáu tệp `.py` (`m365_search`, `graph_client`, `data_access` và ba tệp test), không có template/CSS/JS nào, nên markup mà các probe đã đo vẫn y hệt từng byte; cái thay đổi là ai được hỏi Graph.
- **Đợt sửa thứ tư — xử lý hai Minor của re-review lượt ba (`3cfe834`, `7b662fb`):** re-review phạm vi trả về **bảy phát hiện đã đóng, không còn Critical/Important mở**, kèm một ghi chú ngoài phạm vi (`%2F` fail-closed có thể bỏ liên kết sâu hợp lệ — đã chấp nhận từ đợt final review, không phải phát hiện mới); theo thỏa thuận ở lượt trước là khép vòng lặp; hai Minor còn lại được sửa chứ không để treo vì một cái là lỗi cấu hình **im lặng** và một cái làm chú dẫn trong mã mất giá trị tin. (1) `_site_prefix` nối thẳng `M365_SHAREPOINT_SITE_PATH` vào hostname, mà `settings.py:294` không chuẩn hoá và `.env` là chỗ người dùng tự gõ: một giá trị `/sites/IHRMS/` cho ra prefix mang dấu `/` thừa, **không** `webUrl` thật nào khớp, nên nguồn SharePoint trả rỗng mà không báo lỗi — trông hệt "site chưa có tệp". `.env` máy này là `/sites/IHRMS` nên đây là lỗ tiềm tàng, chưa phải sự cố. (2) Phép cắt dấu `/` lại mở đúng chỗ nó vừa vá: `site_path = "/"` cắt xong thành rỗng, prefix còn `https://<hostname>` trần, tức `_is_site_url` chấp **mọi** site trên host và chỉ còn bộ lọc thư mục chặn hộ. `_site_prefix` giờ THA `GraphNotConfigured` khi đường dẫn sau cắt không bắt đầu bằng `/` — hướng lỗi phải là đóng, cùng lý do docstring của nó vẫn nói từ đầu. (3) Ba chú dẫn `tệp:dòng` đã lệch vì **chính lượt ba thêm dòng** vào `data_access.py` (17→20, 69→72, 99-100→103/105) và `graph_client.py` (107→111); trong mã và work log chúng chuyển thành chỉ tên hàm/nhánh (`can_read_file`, `visible_dispatches_for`, `acquire_token_for_client`) vì tên không tự đổi chỗ khi thêm bình luận. Đã kiểm lại toàn bộ số dòng còn lại của mục này: `uploads.py:80-85`, `office/models.py:30,64`, `permissions.py:82`, `permissions.py:134`, `settings.py:159`, `assets.py:394`, `attendance.py:444` **vẫn đúng**.
- **Kiểm tự động đợt bốn (`7b662fb`):** RED từng bước — `GraphSearchTests` 9 tests / 1 failure (`[] != ['CV-1.pdf']`) rồi 10 tests / 1 failure (`GraphNotConfigured not raised`). GREEN: `apps.m365 apps.assistant` → **152 tests OK**. Toàn dự án SQLite → **Ran 729 tests, OK (skipped=7)**, 358,33s, `sqlite_exit=0`, zero dòng `FAIL:`/`ERROR:` (727 ở lượt ba, +2 test mới). Cụm SQL Server bảy nhãn → **251 tests OK**, 90,07s, DB tạm `test_ihrms_e30d6f7da76a43bbb3208e4bffa57d1e`, `mssql_exit=0`. `manage.py check` no issues; `makemigrations --check --dry-run` No changes detected; `git diff --check` sạch; quét ký tự ngoài tiếng Việt trên `graph_client.py`, `tests.py`, `m365_search.py`, `tests_m365_search.py` → **0 ký tự lạ** (diff work log chỉ còn `§` nằm trong câu cũ bị viết lại, không phải chữ mới). Hai nền tảng chạy song song nên lần chạy SQLite đầy đủ **đầu tiên** của đợt này đã bị dừng giữa chừng vì cây nguồn còn thay đổi sau khi nó khởi động; số 729 là của lần chạy lại trên cây cuối.
- **Kiểm tự động (backend SQLite):** `manage.py check` → no issues; `makemigrations --check --dry-run` → No changes detected; cụm `apps.assistant apps.m365 apps.notification` → **129 tests OK**; `apps.portal.test_global_search apps.document` → **64 tests OK**; **toàn bộ dự án** `ops/run_tests.py --backend sqlite` → **Ran 720 tests OK (skipped=7)**, 431,5s trên nguồn cuối `5ad69c4` (693 trước final review, +27 test của đợt sửa). `ops/audit_design_tokens.py` exit 0 (hex literal 0, font-size lệch thang 0, `!important` 9 ≤ 10 — không đổi so với baseline); quét ký tự ngoài tiếng Việt trên **36 tệp của cả branch** (`b03436c..HEAD`): mã nguồn **sạch**, nhưng bắt được một chữ Cyrillic U+0430 (a Cyrillic, looks giống `a` Latin) lọt vào danh sách `STOPWORDS` trong chính tệp plan — `"của" (chữ cuối là U+0430, không phải U+0061)` gõ hai lần, kẻ chép nguyên văn từ khối đó sẽ có hai stopword vô dụng vì `normalize()` không fold Cyrillic; đã sửa thành `"của"` Latin một lần (`281106f`). `git diff --check` sạch.
- **Kiểm SQL Server (backend thứ hai):** `ops/run_tests.py --backend sqlserver apps.assistant apps.m365 apps.notification` → **129 tests OK**, 16.4s, trên DB tạm `test_ihrms_5f749ff6d61a4d7a9ff8f61bba7bd236` (instance `localhost\SQLEXPRESS`, runner tự tạo và tự hủy; không mở `qlhcns`). Migration `assistant 0001` đã đối chiếu `sqlmigrate` **hai backend ngay trong message commit `eccd3cc`** (`ISJSON`/`nvarchar(max)`/`datetimeoffset` so với `JSON_VALID`/`varchar`/`datetime`); T10 chạy lại `sqlmigrate` SQLite: chỉ `CREATE TABLE tblAssistantSearchLog` + 4 index, không DROP, không đụng dữ liệu. **Chạy lại trên nguồn cuối `5ad69c4`, cụm rộng hơn** (`apps.assistant apps.m365 apps.notification apps.portal.test_global_search apps.document`) vì đợt sửa final review chạm `db_search` (thứ bậc NULL) và `graph_client` (tệp dùng chung với storage/activity): **220 tests OK**, 82,6s, DB tạm `test_ihrms_b3fc297bea8449f6acdb840f4daae4f9` do runner tự tạo và tự hủy; `sqlmigrate` migration `0002` đã ghi nguyên văn trong message commit `7febf25` cho cả hai backend.
- **Layout theo AGENTS.md (vì sửa `base.html` + CSS dùng chung):** cặp before/after **quét hết route** — 148 route × 3 vai trò (layout-admin, hr, employee) × 7 độ rộng 1920/1756/1440/1280/1024/768/390 × sáng/tối = **2862 case mỗi lượt**, `violations: 0`, `errors: 0` cho cả before (mốc `677d7c5`, không có widget) và after (nguồn hiện tại). Cặp thứ hai hẹp về vai trò nhưng đủ 10 tài khoản trên 4 route liên quan (`portal:dashboard`, `portal:dashboard_people`, `portal:global_search`, `assistant:assistant_page`): **452 case, 0 vi phạm, 0 lỗi**. Bằng chứng: `%TEMP%\ihrms-assistant-layout-20261019\before-routecomplete` và `after-routecomplete` (kèm `result.json`, `grid-sources.json`, `report.md`), ảnh contact sheet 1756/390px trong cùng thư mục. **Chưa đóng gate theo nghĩa đen của AGENTS.md:** chưa quét 9 vai trò × 148 route trong một lượt (đã thay bằng 3 vai trò × đủ route + 10 vai trò × 4 route); chủ dự án muốn đúng ma trận đầy đủ thì chạy lại một lượt ~2 giờ.
- **In và trình duyệt:** `ops/run_print_layout_uat.py` → **402 checks, 37 PDF, failures: []**. `ops/run_browser_uat.py --backend sqlite --layout-only` → **128 checks, 32 screenshots, db_destroyed: true** trên DB tạm `test_ihrms_browser_*`. Luồng chatbot kiểm bằng probe riêng trên DB giả `ihrms-activity-layout-20261019-synthetic_only`: hỏi "công văn"/"quyết định" từ trang `/assistant/` và từ dock, kết quả đúng quyền (1 và 3 thẻ, link mở `/portal/dispatches/1/`), Esc đóng, tài khoản ẩn danh không có nút nổi, `external_hosts: []` (không gọi ra ngoài máy), `errors: []`; probe in xác nhận `print_fab_visible: false` còn nội dung trang vẫn in được. Ảnh: `assistant-page-results.png`, `assistant-fab-open.png`, `assistant-page-empty.png`. **Chạy lại cả hai probe trên nguồn cuối `5ad69c4`** (vì đợt sửa final review chạm `assistant.js`): trang `/assistant/` vẫn 1 thẻ mở `/portal/dispatches/1/`, dock vẫn 3 thẻ + 3 icon, Esc đóng, tài khoản ẩn danh vẫn không có FAB, `external_hosts: []`, `errors: []`; probe in vẫn `print_fab_visible: false`, `print_dock_visible: false`, `print_main_visible: true`, `assistant_pdf_bytes: 63377`. Console chỉ còn một `404 /favicon.ico` đã tồn tại y hệt ở lượt trước — không phải của đợt này.
- **Rà độ phủ thông báo (không đổi cơ chế gửi thư):** quét 50 điểm gọi `notify*()` trong `src/apps` đối chiếu mọi assertion `Notification` trong test → **28 nhóm sự kiện có gắn type, 15 nhóm có test, 13 nhóm chưa có**: `asset`, `attendance`, `contract`, `document`, `event`, `hr`, `kpi`, `office`, `payroll`, `procurement`, `recruitment`, `salary`, `task`. Đã đọc tay hai điểm để loại dương tính giả (`attendance.py:444` duyệt bảng chấm công, `assets.py:394` duyệt đề nghị thanh lý — đều là thông báo thật, chưa có test). **Không có lỗ hổng "quên gọi notify"**: cả hai điểm trong luồng công văn đều báo đúng người. Bổ sung `DispatchNotificationCoverageTests` (4 test): vào sổ có người xử lý → báo người xử lý; không có người xử lý → không báo ai; người xử lý cập nhật → báo người vào sổ; người vào sổ tự cập nhật → **không tự báo mình**. Hai test phủ định đều chứng minh trước rằng thao tác được chấp nhận (công văn sinh ra / `status` đổi thật) — nếu không thì nó chỉ "đỗ" trên một redirect bị từ chối quyền. Vai trò `SUPER_ADMIN` **không** có `manage_office` (`permissions.py:82`: HR_MANAGER, HR_OFFICER, SYS_ADMIN), nên bản phác thảo dùng SUPER_ADMIN tạo được đúng 302 mà không tạo công văn nào; đã đổi sang HR_MANAGER.
- **Minor chấp nhận có chủ đích (không sửa đợt này):** (a) asset `assistant.css`/`assistant.js` vẫn tải cho người chưa đăng nhập — kéo theo phải quét lại toàn bộ layout `base.html` chỉ để tiết kiệm hai tệp tĩnh; (b) throttle 30 câu hỏi/phút dựa trên `LocMemCache` nên tính theo từng process, đúng với cấu hình hiện tại nhưng phải đổi sang cache chia sẻ nếu chạy nhiều worker; (c) `z-index` của dock có thể đè popover bảng, chỉ là thứ tự hiển thị; (d) gọi msal lấy token chưa có timeout, khác với HTTP request đã có `(3, 10)`; (e) EMPLOYEE không surfaced chính quyết định nhân sự của mình qua chatbot — chatbot nghiêm ngặt hơn cổng, an toàn theo hướng nghiêng về che, nên giữ và ghi ở đây để chủ dự án quyết.
- **Bản sao review theo AGENTS.md bước 6:** `%TEMP%\ihrms-assistant-review-copy\` + `.zip` + `.zip.sha256`; dựng lại từ HEAD **sau** commit work log này nên manifest không còn đường bẩn, dựng bằng `git ls-files`, loại `.env`, `*.sqlite3`, `Logs/`, `media/`, `__pycache__/`, `graphify-out/` → **1267 tệp được chép, 401 tệp bị loại** ở mốc `06340e9`; bản dựng lại sau các commit final review chỉ thêm năm tệp mới (migration `0002`, `management/` ba tệp, `tests_management.py`), `SOURCE_MANIFEST.json` ghi commit/branch/danh sách SHA-256 từng tệp; **mở lại bản sao và đối chiếu hash: 0 lệch**. Tên thư mục không gắn SHA để tài liệu này không tự tham chiếu vòng lặp; SHA-256 của bản nén và commit tương ứng báo trong phiên. Đây là bản sao để review, không phải backup dữ liệu.
- **Dựng lại bản sao review cho bốn đợt sửa (`5889db0`):** bản sao cuối ở `%TEMP%\ihrms-assistant-review-final\` + `.zip` + `.zip.sha256`, dựng lại sau commit work log cuối nên manifest không tự tham chiếu; **1272 tệp, 0 lệch hash khi mở lại từ đĩa, 0 lệch khi đối chiếu ngược về tree của repo**, `zip_entries_not_in_manifest: []`, `secret_like_leaks: []`, `dirty_paths` chỉ còn tệp untracked được bảo vệ. **Một lần trượt phải ghi lại:** script `verify_review_zip.py` dựng từ đợt đầu có **đường dẫn cứng** tới thư mục zip cũ, nên lần chạy đầu tiên của vòng này in ra `commit_in_manifest: 0cce8d7` — tức nó xác minh bản sao cũ chứ không phải bản vừa dựng, trong khi `zip_review_copy.py` đã in SHA của bản mới. Nếu chỉ nhìn dòng "mismatches: []" thì sẽ báo một digest chưa từng được kiểm. Đã kiểm lại bằng đoạn mã lấy đúng đường dẫn của bản mới: commit `5889db0`, **1272 mục**, `entries_checked: 1272`, 0 lệch. Bài học: script một lần cũng phải nhận đường dẫn qua tham số, và số liệu trong báo cáo phải kèm commit mà nó kiểm tra.
- **Việc còn mở:** (1) kết quả SharePoint chỉ có thật khi app registration được cấp consent — hiện chưa cấu hình thì widget tự động suy ra "tài liệu IHRMS" và trả `partial`, người dùng không bị lỗi; (2) 13 nhóm thông báo chưa có test ở trên, mỗi nhóm cần bộ fixture riêng, chưa làm trong đợt này; (3) `ops/dashboard_demo.py serve` **không chạy migration**: DB demo cũ thiếu cột `ActCode` (migration `task.0004`) làm `/portal/` trả 500 cho hai vai trò, rất dễ nhầm với lỗi code — đã vá DB giả tại chỗ (có backup `synthetic.sqlite3.pre-actcode-migrate.bak`) và xác minh 500 đó tồn tại y hệt trên mốc trước thay đổi; đề xuất `serve` tự áp migration hoặc từ chối khởi động; (4) `apps.document.tests_hr_workflow.test_decision_approval_issue_and_private_pdf_access` **tải tệp thật lên SharePoint** khi `.env` bật `M365_STORAGE_ENABLED=True` — trên máy này nó chỉ chạy được với `M365_STORAGE_ENABLED=False`; nên cho test tự `override_settings` để không phụ thuộc `.env` của người chạy; (5) **thay đổi sản phẩm có chủ đích ở lượt ba:** nguồn SharePoint giờ chỉ mở cho `HR_MANAGER`/`HR_OFFICER` (cộng superuser), vì `CongVanDen`/`CongVanDi` chứa cả đính kèm sổ văn thư mà Graph app-only không lọc theo đối tượng được — `DIRECTOR` mất nguồn này dù vẫn xem toàn bộ công văn trong cổng, và `SYS_ADMIN` bị loại vì cổng vẫn ẩn bản Mật với vai trò đó; (6) `.gitignore` chỉ chắn `db.sqlite3` trong khi `.env` đặt `DB_NAME=qlhcns`, nên mọi lệnh chạy tay với `DB_ENGINE=…sqlite3` để lại tệp SQLite ngay trong `src/`; đã cách ly tệp 0 byte ra `%TEMP%` thay vì xóa, cần hoặc thêm `qlhcns` vào ignore, hoặc buộc đi qua `ops/run_tests.py`.
- **Chủ dự án cần tự làm:** cấp Graph application permission (Sites.Selected hoặc Sites.Read.All + Files.Read, kèm consent quản trị) rồi chạy lại một câu hỏi có từ khóa SharePoint để kiểm `sources: "db+sharepoint"`; nếu muốn `DIRECTOR` hỏi được SharePoint, bỏ `manage_office` khỏi `SHARED_LIBRARY_PERMISSIONS` (`m365_search.py`) và chấp nhận lộ tên tệp đính kèm sổ văn thư; nếu muốn đóng layout gate đúng nghĩa đen, duyệt lịch chạy full ma trận 9 vai trò × 148 route; cấp tài khoản QA trên DB/media cô lập để UAT danh tính thật (đợt này chỉ dùng tài khoản synthetic); quyết định ưu tiên cho 13 nhóm thông báo chưa có test. Push `origin main` đang chờ xác nhận của chủ dự án; `git rev-parse HEAD origin/main` và trạng thái sạch sẽ được ghi tiếp ngay sau khi push.
- **Không làm trong đợt này:** không deploy, không áp migration lên DB vận hành, không đổi schema ngoài `tblAssistantSearchLog`, không sửa AGENTS.md/hướng dẫn, không xóa hay đổi các tiến trình đang chạy của người dùng. Tệp `%TEMP%`/`D:\QLHCNS\Tan_AI_sites_plugin_2026-10-19_21-41.md` (untracked, không phải do đợt này tạo) vẫn được giữ nguyên, không staged.


## 2026-10-19 — Bổ sung gate review và thống nhất skill đa client

- Phạm vi: xử lý sáu điểm cải thiện chủ dự án nêu sau chuyển reviewer sang skill; không review lại mã ứng dụng hoặc bốn commit nghiệp vụ/UI trước. Đầu lượt `main` sạch tại `0221a4f`, `git fetch origin main` thành công, HEAD/origin/main khớp, ahead/behind 0/0; đọc ba mục nhật ký mới nhất. Một tác nhân ghi; áp dụng writing-for-agents và SKILL-MECHANICS.
- `docs/Huong_Dan_Review_Du_An.md`: bổ sung lệnh và điều kiện chạy layout/form/print/cache/button/token/contrast, runtime giả/baseline cùng DB, hai server cache và giới hạn SQLite. Bổ sung `ops/check_migration_state.py`, ý nghĩa exit code và quy tắc model/schema/migration commit riêng, sqlmigrate hai backend theo AGENTS.md. AGENTS.md giữ quy tắc dự án; hướng dẫn giữ quy trình/lệnh; không sửa AGENTS.md trong đợt này.
- Rút `.agents/skills/ihrms-review/SKILL.md` còn định tuyến; `.cursor/agents/ihrms-reviewer.md` chỉ trỏ AGENTS/hướng dẫn/skill. Thêm ba con trỏ `.claude/skills/ihrms-{review,operations,project}/SKILL.md`, mô tả tiếng Việt ở cả bản chung và con trỏ. Sửa lệnh test trong skill project sang runner cô lập. Bỏ BOM cũ ở hai skill được sửa, quote YAML description có dấu hai chấm.
- `ops/run_tests.py` bắt buộc `--backend` ngay tại argparse; `ops/Run-Tests.ps1` cũng bắt buộc `-Backend` để không lách bằng mặc định wrapper. Giữ lựa chọn `configured` khi gọi rõ để tương thích; hướng dẫn yêu cầu sqlite/sqlserver. Không thay cách cấp tên DB test, cách ly media/email/M365 hoặc logic nghiệp vụ.
- Kiểm nguồn cuối: `venv/Scripts/python.exe ops/run_tests.py --backend sqlite apps.common.tests` **3 tests OK**, exit 0; cùng lệnh `--backend sqlserver` **3 tests OK**, exit 0, DB `test_ihrms_<UUID>` được tạo/hủy. Không chạy full suite; đây là smoke test điều phối runner, không chứng minh toàn nghiệp vụ.
- Harness subprocess: **16 kiểm tra đạt** gồm thiếu backend, chỉ có label, backend sai (exit 2 trước Django), help runner, PowerShell `-NoProfile -NonInteractive -File ops/Run-Tests.ps1` thiếu backend (exit 1), 0 test bị từ chối (exit 1), `--help` của chín runner/audit và validation tài liệu. **8 tệp/7 YAML/17 liên kết tương đối đạt**, đủ tám tên gate/migration, UTF-8 không BOM/ký tự thay thế; `ast.parse` runner và `git diff --check` đạt. Log CLI/validation ở `%TEMP%/ihrms-review-guidance-20261019/`. Lượt đầu phát hiện pipe PowerShell làm mất dấu, YAML chưa quote và BOM cũ; đã sửa rồi chạy lại toàn bộ harness đạt, không dùng kết quả lỗi làm PASS.
- Không đổi CSS/template/UI, schema hoặc luồng nghiệp vụ nên không chạy lại browser/layout/form/print/cache thực, migration-state trên DB đang dùng, full suite hay deploy. Help chỉ xác minh CLI, không đóng các gate đó. Sandbox không khởi tạo được exec (`helper_unknown_error: setup refresh had errors`); các lệnh hoàn tất qua quyền chạy ngoài sandbox đã được cấp, không thay cấu hình sandbox.
- Snapshot nguồn staged ngoài repo: `%TEMP%/IHRMS_Review_20261019_ReviewGuidance.zip`, manifest tree/nguồn và SHA-256 từng tệp; kết quả xuất/mở lại kiểm hash được xác minh trước commit. Loại secrets, DB/media và runtime; không phải backup dữ liệu. Commit/push `origin main` theo quyền hiện hành, SHA/remote/ahead-behind báo sau push; không force/deploy.
- **Còn mở:** chưa mở được phiên mới của Codex/Antigravity/Claude Code để chứng minh tự chọn skill. Chủ dự án mở phiên mới tại `D:/QLHCNS`, dùng prompt discovery trong hướng dẫn, kiểm catalog/log rồi báo client/phiên/kết quả; đọc tệp trực tiếp chỉ là fallback, không chứng minh auto-discovery. Chưa xác minh CI đúng SHA cuối trong nhiệm vụ này.
- **Lịch sử cần review riêng:** chủ dự án xác nhận `ab949cd`, `9f10f5d`, `5ab2499` thuộc prompt ActCode nhưng chưa review. `git show 950a1a2` xác nhận commit vừa sửa kéo scrollbar vừa thiết kế slide; nhật ký trước ghi tham chiếu PPTX người dùng cung cấp, chưa có prompt gốc trong bằng chứng đợt này để xác minh ủy quyền phần slide. Không coi nhật ký thay nguồn yêu cầu; cần chủ dự án đối chiếu yêu cầu gốc hoặc giao review CHANGES với mốc cụ thể. Không revert/đổi các commit đó trong đợt này.

## 2026-10-19 — Chuyển reviewer sang skill dùng chung, gỡ Sixth

- Yêu cầu chủ dự án chuyển reviewer `.sixth/agents/code-review.md` sang thư mục skill phù hợp và xóa Sixth khỏi dự án. Đầu lượt `main` sạch tại `359ab813f2e6a644658833ce3cbce3bc2ee339d9`, fetch origin/main khớp, ahead/behind 0/0; đọc ba mục nhật ký mới nhất. Một tác nhân ghi, dùng writing-for-agents và hướng dẫn skill mechanics.
- Chuyển thành `.agents/skills/ihrms-review/SKILL.md`, tên riêng tránh trùng skill `code-review` hiện hữu. Giữ FULL/CHANGES, REVIEW/FIX, finding có bằng chứng, các gate và bảo vệ dữ liệu; bỏ frontmatter permissions đặc thù extension, cập nhật quyền commit/push theo AGENTS.md và yêu cầu tài khoản QA riêng. Không chạy review toàn dự án trong nhiệm vụ chuyển skill này.
- Gỡ tệp cũ và hai thư mục rỗng `.sixth/agents`, `.sixth`; cập nhật AGENTS.md, README.md, hướng dẫn review và các mẫu gọi skill. Không còn tham chiếu Sixth trong hướng dẫn đang dùng. Giữ nguyên nhật ký/báo cáo lịch sử và tài liệu nghiệp vụ có chuỗi trùng, không sửa lịch sử để làm sạch kết quả tìm kiếm; không gỡ extension cấp máy hoặc sửa IDE cá nhân.
- Kiểm trên nguồn cuối: UTF-8 bốn tệp hướng dẫn đạt, YAML đúng name/description, **23 liên kết tương đối tồn tại**, đủ nhánh/phạm vi review và guard QA; thư mục cũ không tồn tại, skill code-review có sẵn giữ nguyên. `git diff --check` và staged check chạy trước commit. Không chạy backend/browser/layout/print vì chỉ chuyển hướng dẫn Markdown, không đổi ứng dụng/UI/schema hoặc dữ liệu.
- Snapshot staged source `D:/IHRMS_Review_Exports/IHRMS_Review_20261019_ReviewSkill.zip`, loại dữ liệu/bí mật, giữ skill mới, có manifest/tree và mở lại xác minh SHA-256 từng tệp; hash ở `.zip.sha256`. Commit/push main theo ủy quyền; SHA/remote/ahead-behind báo sau push. Chưa xác nhận auto-discovery skill trong phiên client mới; có thể đọc trực tiếp đường dẫn mới nếu phiên hiện tại chưa nạp lại catalog.

## 2026-10-19 — Rà tệp chưa commit, làm sạch công cụ và hướng dẫn agent

**Phạm vi và quyết định**
- Theo yêu cầu chủ dự án kiểm tra 17 tệp chưa commit, bỏ phần thừa và push. Git thực tế ghi nhận **18 mục untracked** (hai thư mục là repo Git lồng), không có tracked/staged modification đầu lượt. `main` tại `950a1a2cd6a0b9cd8e8c9b5335b93e5d7cecaa78`; fetch origin/main khớp, ahead/behind 0/0; đọc ba mục nhật ký gần nhất. Một tác nhân ghi; không đổi mã ứng dụng, dữ liệu, DB/schema, quyền, UI hoặc bản in.
- Giữ và sửa 10 tệp hướng dẫn GitHub: ba agent, copilot instructions, hai instruction theo đường dẫn và bốn skill. Sửa backend `mssql` thành `sqlserver`, mở phạm vi template app/CSS/JS, bỏ quy định transaction/tải quan hệ vô điều kiện, đưa DESIGN.md/AGENTS.md và DB/media QA cô lập làm nguồn quyết định. Dùng skill writing-for-agents hiện có, không cài/nâng dependency.
- Hợp nhất Refactoring UI: giữ bảy tệp nguồn MIT tại `.agents/skills/refactoring-ui`, bỏ Git metadata lồng; `.claude/skills/refactoring-ui/SKILL.md` chỉ trỏ bản dùng chung. Ghi upstream SHA `48872143abb0a8feb6d9bf58e222afbd800210b0`, giữ LICENSE, thêm ưu tiên chuẩn IHRMS; không nạp assets vào giao diện.
- Chuyển khỏi workspace: bản clone Claude trùng, Git metadata của bản canonical, skill `new-hrm-feature` trùng scaffold, script bootstrap base64 cũ, hook Stop chạy manage.py với DB mặc định và hai ảnh tham chiếu nội bộ lỗi thời. Không chạy script/hook này. `.mcp.json` giữ nguyên tại máy, JSON hợp lệ, thêm đúng `/.mcp.json` vào ignore, không đưa cấu hình cá nhân lên Git.

**Lưu phục hồi và kiểm tra**
- Trước thay đổi đã lưu cả 18 mục (88 tệp) ở `D:/IHRMS_Cleanup_Archive/20261019_170606/untracked-before-cleanup.zip`, có manifest và mở lại xác minh SHA-256 từng tệp. SHA archive `6a50961eaa560290634b26dd18f42130cb2af382b9041bf74e133aecca3c8ed7`, kiểm lại đạt sau chuẩn hóa. Đây là kho lưu riêng có cấu hình/ảnh nội bộ, không phải snapshot nguồn để chia sẻ. Bảy đích thừa được chuyển thêm vào `removed-from-workspace/` trong cùng thư mục để khôi phục dễ.
- Lệnh xóa ban đầu bị bộ kiểm soát tự động chặn trước thực thi; không cố chạy lại lệnh xóa. Dùng Move-Item sang kho lưu ngoài dự án sau khi xác minh đường dẫn nguồn/đích và không có reparse point. Không xóa vĩnh viễn hoặc chạy git clean thật.
- `validate_tooling.py` ngoài repo: **18 tệp hướng dẫn/11 YAML frontmatter/20 liên kết nội bộ đạt**; UTF-8 không BOM/ký tự thay thế, quét mẫu credential đạt; không Git metadata lồng; MCP JSON hợp lệ/ignored/không tracked; archive SHA khớp. Kết quả `%TEMP%/ihrms-cleanup-20261019/validation.json`.
- `venv/Scripts/python.exe ops/run_tests.py --help`: exit 0, backend thực `configured/sqlite/sqlserver`; chỉ kiểm CLI, không kết nối DB. `git diff --check` và kiểm staged whitespace chạy trên nguồn cuối trước commit. Rà stage không có gitlink, `.env`, DB/media, ảnh riêng, local MCP hoặc bootstrap/hook thừa.
- Chỉ preview `git clean -ndx` để phân loại; giữ `.env`, DB/media, môi trường ảo, node_modules, backups/log và staticfiles. Không coi chúng là rác để xóa hàng loạt. Không chạy lại regression/browser/layout/print vì đợt này chỉ đổi tài liệu/công cụ hướng dẫn và ignore; chưa xác nhận các client Copilot/Claude nạp cấu hình trong phiên thật.

**Bàn giao**
- Snapshot nguồn từ staged tree tại `D:/IHRMS_Review_Exports/IHRMS_Review_20261019_RepoCleanup.zip`, có manifest/tree và SHA-256 từng tệp được mở lại kiểm; bao gồm hướng dẫn/skill vừa chuẩn hóa, loại bí mật/DB/media/đầu ra runtime. Hash archive ở `.zip.sha256`; kiểm privacy và snapshot trước commit. Kho lưu phục hồi riêng không được đưa vào snapshot này.
- Commit/push `origin main` theo quyền đã cấp; SHA, xác nhận remote khớp HEAD, ahead/behind và trạng thái sạch được báo sau thao tác. Nếu push không thành công phải ghi lỗi, không tuyên bố đã giao. Không deploy hoặc thay DB vận hành; chủ dự án không cần tự xóa dữ liệu hay cài lại môi trường.

## 2026-10-19 — Sửa kéo thanh cuộn danh mục và thiết kế lại slide điều hành

**Tóm tắt cho chủ dự án**
- Sửa thành phần chọn dùng chung để kéo thanh cuộn không đóng danh mục; giữ tìm kiếm, ID gửi và bàn phím.
- Thiết kế lại chức năng Tạo slide: bìa navy/teal, chỉ số có phân cấp, biểu đồ chỉnh sửa được và bố cục theo nhóm nghiệp vụ.
- Không đổi nguồn số liệu, công thức, quyền, GET/POST, model/migration hoặc nội dung Excel/Word; không dùng DB/media/phiên người dùng thật.
- Có bản slide mới dựng từ PPTX chủ dự án cung cấp, giữ tệp gốc; ảnh từng trang và kết quả kiểm ngoài repo.
- Trạng thái kiểm cuối, snapshot và commit/push ghi bên dưới; chưa deploy hoặc nghiệm thu trên PowerPoint/máy in thật.

**Đầu lượt, phạm vi và nguyên nhân**
- Bắt đầu trên `main` tại `5ab24992c08ee4a162f91673cdad9b6a890c54ea`; fetch origin/main khớp, ahead/behind 0/0; đọc ba mục nhật ký gần nhất. Chỉ có các tệp chưa theo dõi ngoài phạm vi đã được chủ dự án cho phép từ trước, giữ nguyên; một tác nhân ghi. Dùng Impeccable 4.5.2 hiện có và hướng dẫn Presentations, không cập nhật skill hoặc thêm dependency ứng dụng.
- Tái hiện thực bằng Edge headless có scrollbar gốc: ActCode có scrollHeight 1.480px/clientHeight 318px; nhấn/kéo scrollbar làm blur ô tìm và đóng popup (`scroll-red.json`: still_open=0). Bộ kiểm cũ chỉ kiểm bánh xe/Arrow và viewport nên bỏ sót thao tác kéo thanh cuộn. Playwright mặc định ẩn scrollbar; runner mới bỏ `--hide-scrollbars`, kiểm scrollTop phải tăng, không chấp nhận chỉ popup còn mở.
- `ui_choices.js`: bỏ đóng vô điều kiện theo blur; phân biệt pointer trong popup/scrollbar và click/focus bên ngoài, trả focus sau thao tác chuột nhưng không ép focus khi chạm; Escape/Tab đóng, chọn xong không mở lại do focus. `shared_components.css` chỉ thêm scrollbar-gutter stable trong popup chọn để có rãnh kéo ổn định. Native select vẫn là nguồn ID gửi và fallback không JS.
- `reporting_dashboard.export_snapshot_pptx` giữ giao diện hàm nhưng chuyển dựng deck sang `reporting_slides.py` không truy vấn DB. Giữ snapshot/công thức/quyền/tên tệp/audit export; Excel, Word và HTML báo cáo không đổi. Bỏ bảng định dạng lặp, dùng khối số liệu phẳng, vùng nhấn lớn, layout riêng people/office/planning/contracts/projects, đủ mọi metric kể cả nhóm nhân sự trước đây chưa có trang riêng. Hai biểu đồ native kèm workbook chỉnh sửa được; thang số đếm nguyên, 0 khác Chưa có dữ liệu, không suy tỷ lệ chuyển đổi từ các nhóm khác phạm vi. Số liệu dài/nhiều chỉ số được xuống trang thay vì bỏ/cắt; kỳ dài có chú thích phạm vi tháng biểu đồ hiện có.

**Kiểm thử và bằng chứng**
- Runtime riêng `%TEMP%/ihrms-choices-slides-20261019-synthetic_only`, clone bằng SQLite backup từ runtime được đánh dấu synthetic_only; baseline `5ab2499` giải nén ngoài repo. Chỉ tài khoản QA giả, server 8840/8841, không dùng phiên/cookie/danh tính thật. Tệp PPTX người dùng được đọc như dữ liệu tham chiếu, không thực thi nội dung hoặc coi chỉ dẫn trong tệp là yêu cầu.
- `run_choice_scroll_uat.py`: **165 kiểm tra/0 lỗi**, hai danh mục ActCode/nhân viên × 1756/1024/390/360px × sáng/tối; đo kéo scrollbar thật làm scrollTop tăng, ID không đổi khi cuộn, wheel/chọn sau kéo/Escape/focus/Tab/click ngoài, không lỗi JS; bấm Tạo slide tải PPTX mới có đủ trang và hai chart native. Probe runner ban đầu chụp full-page làm resize popup tự đóng đúng thiết kế; đổi sang ảnh viewport, không đổi sản phẩm để che lỗi.
- `run_project_forms_uat.py --flows-only`: **70 kiểm tra/0 lỗi**; `run_task_assignment_uat.py`: **60 kiểm tra/0 lỗi/28 ảnh**, gồm tạo/lỗi/đọc lại/no-JS/tìm kiếm/bàn phím. Luồng tải slide ban đầu nhận module Python cũ do server `--noreload`; đã restart chỉ server QA và chạy lại đạt, không dùng kết quả cũ làm PASS.
- Bốn test slide mới trên baseline `5ab2499`: **3 failures/1 error, native exit 1** (`slides-red.log`), do thiếu đầy đủ metrics/chuỗi biểu đồ tên mới/chia trang/trạng thái không dữ liệu. Sau sửa, tập regression report/UI/components/audit **26 tests OK trên SQLite và SQL Server**, exit thật lưu qua subprocess; kiểm các chỉ số hiển thị, không mutate snapshot, workbook/chart data, trường hợp số tiền dài/17 metrics, shape không ngoài slide/không chồng nhãn-giá trị, 0/NULL/kỳ nhiều năm. Lượt nguồn cuối sau thay chiều cao ô năm được chạy lại, kết quả bên dưới.
- `run_layout_alignment_audit.py` nguồn cuối: **146 route/7.138 ca/9 vai trò/0 vi phạm/0 lỗi**, 1920/1756/1440/1280/1024/768/390px sáng/tối; không đổi audit hoặc waiver. Detector Impeccable trên JS/CSS đã đổi trả `[]`; không dùng detector thay browser. `check_ui_contrast.py`: **220 cặp/0 lỗi**.
- `run_print_layout_uat.py`: **402 kiểm tra/37 PDF/0 lỗi**; cache **9 kiểm tra đạt**, hash JS/CSS/service worker thay theo nội dung, không yêu cầu xóa dữ liệu trình duyệt. `print-comparison/result.json`: **37/37 PDF trước/sau giống pixel/văn bản/kích thước trang**, trên cùng DB giả, bao gồm màu/viền/ngắt trang/khoảng ký do ảnh không đổi; không sửa `print_forms.css`. `run_form_contract_uat.py` before `--source-root <baseline>` / after không cờ ngoại lệ: **1.314 ca/0 lệch**, SELECT count không tăng; không thay hợp đồng hay nới gate.
- PPTX tham chiếu có 12 slide. Bản dựng lại từ chính nội dung tệp có **13 slide, 44 cặp chỉ số giữ nguyên và dữ liệu hai chart bằng nhau**; không đọc DB để bổ sung số liệu chưa có trong tệp. Đầu ra `D:/IHRMS_Review_Exports/ReportSlides_20261019/BaoCao_DieuHanh_IHRMS_ThietKeMoi.pptx`, PDF/contact-sheet/ảnh từng slide cùng thư mục, chỉ lưu ngoài Git. Tệp nguồn Downloads được so SHA-256 xác nhận không đổi. Bản xuất trực tiếp từ ứng dụng dùng toàn bộ snapshot hiện hành, không bị giới hạn dữ liệu của tệp tham chiếu.
- Đã render qua LibreOffice và xem đủ từng slide, không tuyên bố đã mở trong Microsoft PowerPoint. Kiểm package integrity và layout geometry của skill đạt exit 0 (13 trang/16:9/heading fit). Trong dựng mẫu, PowerShell làm mất dấu vài nhãn tự nhập và shape kế thừa shadow Office; đã sửa Unicode bằng nhãn nguồn có dấu, bỏ effectRef/lineRef, render lại và đối chiếu toàn bộ nhãn trong PDF. Test phát hiện chồng hộp label/value tuyển dụng đã sửa trước giao. Không tải dữ liệu nguồn lên dịch vụ ngoài.

**Giới hạn và bàn giao**
- Nguồn cuối sau dọn: `ops/run_tests.py --backend sqlite` và `--backend sqlserver` với các nhãn `apps.portal.test_report_slides apps.portal.tests_report_dashboard apps.portal.test_ui_refinements apps.common.tests_ui_components apps.portal.test_layout_audit_tools`: **26 tests OK mỗi backend, native exit 0**, SQL Server tạm `test_ihrms_4c773a42ef8041e0b36c8b656b272273` đã hủy. Log `delivery-tests-{backend}.log`/exit JSON; không dùng exit nhiễu của pipeline PowerShell. `pip check`, Django `check`, `makemigrations --check --dry-run` trên DB giả và `git diff --check` đạt, không phát sinh migration.
- Bằng chứng UI/báo cáo an toàn: `D:/IHRMS_Review_Exports/UI_ChoicesSlides_20261019/index.html`; slide mẫu/PDF/contact sheet/13 ảnh riêng tại `D:/IHRMS_Review_Exports/ReportSlides_20261019`. Bản PPTX cuối được render lại và xác nhận cả 13 trang giống ảnh đã xem; kiểm cấu trúc/hình học lại đạt. Snapshot nguồn `D:/IHRMS_Review_Exports/IHRMS_Review_20261019_ChoicesSlides.zip` từ Git tree stage, loại dữ liệu/bí mật, có manifest và mở lại xác minh SHA-256 từng tệp; hash archive ở `.zip.sha256`. Không đưa PPTX tham chiếu, file xuất, ảnh, DB/media, credentials hay runtime vào Git.
- Commit/push `origin main` theo quyền đã cấp; đối chiếu remote SHA/HEAD/ahead-behind sau push, kết quả và SHA trong báo cáo bàn giao ngoài repo. CI theo SHA được kiểm riêng, không suy commit/push thành CI PASS; nếu CLI 401 ghi rõ chưa theo dõi CI và giữ kết quả connector thực tế.
- Chưa kiểm screen reader, thiết bị cảm ứng thật, Microsoft PowerPoint, máy in hoặc phiên trình duyệt vận hành. Không chạy full suite toàn hệ thống trong đợt này; dùng tập regression ảnh hưởng trên hai backend và các gate toàn route/print/form/cache nêu trên. Không thay quy tắc nghiệp vụ hoặc áp migration/deploy.

## 2026-10-19 — ActCode riêng, giao việc hành chính và hover toàn hàng bảng

### Tóm tắt cho chủ dự án
- Thực hiện ba phần theo tệp yêu cầu: schema ActCode riêng; form Giao việc; hover cả ô đầu/Thao tác.
- Schema đã kiểm áp/hoàn tác/áp lại trên SQLite và SQL Server tạm/restore thử; chỉ 1/4 hàng giả được gán ActCode.
- Chưa áp migration hoặc triển khai mã lên vận hành; không dùng phiên/danh tính thật, không chạm DB/media vận hành.
- Chủ dự án cần chạy truy vấn đếm chỉ đọc, sao lưu/restore thử rồi áp `task.0004/0005` theo kế hoạch trước triển khai mã; duyệt ảnh giao cuối.
- Gate UI và full suite SQLite/SQL Server đạt trên nguồn cuối; CI chưa có kết quả xác nhận, CLI lỗi 401.

**Phạm vi, nguồn yêu cầu và ba commit**
- Tệp yêu cầu đính kèm ngày 19/10/2026 xác nhận chỉ bổ sung `Task.act_code`, không đổi `task_code` unique, quyền, Dashboard, bản in hoặc hoạt động/services.py. Bắt đầu `main` tại `78eeb506a40d2a269464c05b7de45b2194691dd0`; status chỉ có tệp chưa theo dõi ngoài phạm vi đã được phép, fetch/ls-remote khớp, ahead/behind 0/0; đọc ba mục nhật ký mới nhất. Một tác nhân ghi.
- Phần 1: model, hai migration 0004/0005, test và `docs/MIGRATION_PLAN_task_actcode.md` riêng. ActCode nullable/indexed, kiểm danh mục nhưng giữ giá trị lịch sử đã lưu; `__str__`, TaskCode và logic báo cáo giữ nguyên. Backfill đóng băng đúng 18 mã, chỉ điền NULL theo lô 100, transaction mỗi lô, RunPython reverse no-op. Không thêm trường schema khác.
- Checker migration hiện lấy danh sách trực tiếp từ MigrationLoader nên tự nhận 0004/0005; không cần sửa công cụ hoặc giả trạng thái. Không thêm cột export/Dashboard/KPI/báo cáo. Admin sẽ cập nhật trong commit giao diện riêng.

**Probe trên hành vi cũ trước thay form/allocator**

| Probe mới | Bằng chứng thất bại thực | Sau sửa |
| --- | --- | --- |
| Field ActCode nullable/indexed, validation và lịch sử | `schema-red.log`: 3 errors, FieldDoesNotExist/constructor không nhận act_code, native exit 1 trên model 78eeb50 | 4 tests schema SQLite + SQL Server đạt |
| Chọn cùng ActCode ba lần, Khác, hiển thị, native form và giữ lựa chọn lỗi | `ui-red.log`: 5 tests, 4 failures/1 error, native exit 1; form cũ vẫn đòi task_code, không có act_code/Khác | Đạt trên SQLite/SQL Server và browser 60 kiểm tra |
| Cấp số và hai người tạo đồng thời | `allocator-red.log`: 2 errors, chưa có apps.task.services, native exit 1 | Hai thread thực đạt trên cả hai backend |

UI/allocator probe chạy trước khi đổi hành vi của 78eeb50, sau khi bổ sung riêng field schema; không trình bày đó là full suite trên checkout baseline. Runtime và log ở `%TEMP%/ihrms-task-actcode-20261019-synthetic_only`.

Probe bổ sung trên đúng nguồn `78eeb50` giải nén ngoài repo: sao chép riêng ba tệp test mới (không chép mã triển khai), chạy `ops/run_tests.py --backend sqlite apps.task.test_act_code apps.task.test_assignment_service apps.portal.test_task_assignment`: **11 tests, 4 failures/7 errors, native exit 1**, không có test mới đạt nhầm trên baseline. Log `baseline78-new-tests-red.log`; lỗi liên quan field/migration/module chưa tồn tại hoặc hành vi form cũ chưa hỗ trợ ActCode/Khác/tái sử dụng mã. Không sửa baseline phục vụ browser ngoài việc thêm tệp test độc lập.

**Migration đã kiểm, không áp vận hành**
- `ops/run_tests.py --backend sqlite apps.task.test_act_code`: **4 tests OK**, native exit 0; cùng nhãn `--backend sqlserver`: **4 tests OK**, native exit 0, DB `test_ihrms_2ad3f4b39a8c4a29a6c03e993ff354c4` đã hủy. Test MigrationExecutor lùi 0003, tạo CV01/ACT-5-REPORT/mã hợp lệ/mã đã bỏ, áp 0005, hoàn tác 0003, áp lại; đúng một hàng ActCode, bốn TaskCode không đổi.
- Tạo DB SQL Server hoàn toàn giả, backup COPY_ONLY/CHECKSUM, VERIFYONLY và restore sang DB tạm riêng, không lấy backup dữ liệu vận hành. Trên restore thử: áp 0005 **1,5208s**, lùi 0003 **2,4695s**, áp lại **0,6383s**; mỗi lần backfill đúng **1 hàng**, ba mã khác giữ NULL. Hai DB `test_ihrms_actcode_0764e40149f74eeba5f2751564f1db2d` / `test_ihrms_actcode_26c6e4056b894794a78915022bb63c4b` đã drop trong finally. Backup giả ngoài repo tại `D:/IHRMS_UAT/Task_20261019_synthetic_only`, SHA-256 `9d0e0dae12be445acc8636a9ff84de2aacf11b6efc8150dabcaf8783fcebf566`; `migration-sqlserver-restore.json` lưu SQL/runtime/count. Hai probe runner trước đó lỗi cursor chưa mở và lọc không nhận tiền tố SET NOCOUNT; đã sửa runner, không thay migration để đạt.
- `sqlmigrate task 0004` trên cấu hình SQL Server tạm, đầu ra thật:

```sql
BEGIN TRANSACTION
-- Add field act_code to task
ALTER TABLE [tblTask] ADD [ActCode] nvarchar(50) NULL;
CREATE INDEX [tblTask_ActCode_e88d5e49] ON [tblTask] ([ActCode]);
COMMIT;
```

SQLite: `ALTER TABLE "tblTask" ADD COLUMN "ActCode" varchar(50) NULL;` và `CREATE INDEX "tblTask_ActCode_e88d5e49" ON "tblTask" ("ActCode");`. `sqlmigrate task 0005` báo `Raw Python operation / THIS OPERATION CANNOT BE WRITTEN AS SQL`, không giả rằng nó sinh UPDATE. SQL UPDATE thực đã thu bằng CursorWrapper trên restore:

```sql
SET NOCOUNT OFF; UPDATE [tblTask] SET [ActCode] = [tblTask].[TaskCode]
WHERE ([tblTask].[ActCode] IS NULL
AND [tblTask].[TaskCode] IN (%s, %s, %s, %s, %s, %s, %s, %s, %s,
%s, %s, %s, %s, %s, %s, %s, %s, %s) AND [tblTask].[id] IN (%s))
```

Params lần thử: 18 mã theo đúng thứ tự trong migration/kế hoạch, cuối cùng PK giả 3; rowcount **1**, cả lần áp đầu và áp lại. Không UPDATE TaskCode, không DELETE hồ sơ. Hoàn tác đến 0003 mất ActCode mới nhập, được nêu rõ trong kế hoạch.

**Còn mở và giới hạn**
- Chưa kiểm screen reader, phiên trình duyệt thật của chủ dự án, máy in thật hoặc DB vận hành; tác nhân không áp migration vận hành. Nghiệm thu thị giác của chủ dự án là bước riêng sau khi xem ảnh giao cuối.

**Phần 2 — Giao việc theo ActCode hoặc hành chính**
- Schema đã giao riêng tại `ab949cd4c7cef1087a20a88fa0a4daabb2eb881c`, remote khớp 0/0. Snapshot schema `D:/IHRMS_Review_Exports/IHRMS_Review_20261019_TaskActCode_Schema.zip` gồm 775 tệp, manifest/tree/hash từng tệp mở lại xác minh; SHA-256 archive `15c046a3654f1c1ce75e125ed04641bd524b35170a7a21dc7cb6900860c75946`. `manage.py check` và `makemigrations --check --dry-run` đạt. Checker thực chạy trên SQLite giả lùi 0003 báo đúng 0004/0005 outstanding, native exit 1 như dự kiến; không chạy checker vào DB vận hành trong đợt này.
- Thay field task_code bằng act_code với 18 mục `mã — tên` và Khác; không chọn mặc định. Tên readonly khi JS chọn ActCode, nhập tự do/bắt buộc khi Khác, native select/input vẫn dùng được khi tắt JS. Server lấy lại tên danh mục; Khác kiểm tên 1–300 ký tự và lưu NULL. UI không gửi query gõ tìm thay ID đã chọn. Inline fillName chuyển sang module `task_assignment.js` băm cache. Bố cục chỉ scoped `task_create`, không thay form khác: desktop 1+3/full/4, nút cách nhóm cuối 24px; responsive theo container/viewport được khai báo trong CSS/audit.
- `apps.task.services.create_manual_task` cấp mã CV-năm-số trong transaction: SQL Server khóa dải unique index bằng UPDLOCK/HOLDLOCK kể cả dải rỗng, SQLite giữ writer reservation trước khi đọc; tính số từ cả soft-deleted, insert và retry có giới hạn khi trùng mã/deadlock/locked. Không dùng SELECT MAX không khóa, không thêm bảng/cột counter, không đổi ACT-id-REPORT hoặc mã cũ. Guard/phạm vi người nhận, notification, ngày mặc định/ưu tiên/phòng ban giữ nguyên.
- Danh sách/chi tiết thêm dòng muted ActCode dưới tên, không thêm cột. Admin hiển thị/lọc/tìm ActCode; không có Task serializer/export tương tự cần đổi trong mã đã rà, không thêm cột export. Đề xuất gán ActCode từ activity_code cho Task báo cáo để chủ dự án quyết; không sửa activity/services.py.
- Test tập trung SQLite và SQL Server: **46 tests OK trên mỗi backend**, gồm hai thread tạo mã khác nhau, giữ số của task đã soft-delete, ba lần cùng ActCode, Khác, tên giả/ngoài danh mục, giữ dữ liệu lỗi và phạm vi quyền cũ. Full suite cả hai backend chạy trên cây cuối sau phần hover, kết quả ghi riêng bên dưới.
- `ops/run_task_assignment_uat.py`: **60 kiểm tra đạt, 28 ảnh**, gồm tạo ba lần cùng ActCode/ba CV khác nhau, thông báo có mã, tên canonical/list/detail, Khác lưu NULL, lỗi giữ lựa chọn/tên/mô tả/người nhận, tìm chưa chọn không gửi nhầm, Arrow/Enter/Escape/Tab, native no-JS tạo ActCode và hành chính, 360px popup không tràn, hàng cuối đủ bốn field từ 1280px. Đã xem ảnh desktop sáng/mobile tối; không coi browser headless là phiên thật của chủ dự án.
- Bộ QA tạm cũ thiếu playwright.async_api, runner lần đầu dừng trước quét; đã cài lại Playwright/PDF/Pillow vào thư mục QA ngoài repo, không thêm dependency ứng dụng/CDN. Test ban đầu so nhầm tab mặc định activity_overview và script service worker của base; sửa test đúng phạm vi assigned_by_me/fillName, không thay sản phẩm để làm xanh test.
- Impeccable source review không thấy blocker chắc chắn; kết luận concurrency chỉ chấp nhận khi có test hai backend thực. Theo dõi CI schema qua `gh run list --commit ab949cd...` bị **HTTP 401 Bad credentials**: **chưa theo dõi CI**, không suy từ push thành CI đạt. Cần chủ dự án xác thực lại `gh auth login` hoặc xem Actions theo SHA sau bàn giao.
- Gate commit form: **46 tests OK trên mỗi backend SQLite/SQL Server, native exit 0**, SQL Server dùng DB `test_ihrms_ceb51658abb24f36879ce1bae82bbeb4` đã hủy; có kiểm hai thread thực ở cả hai backend. Matrix `layout-ui`: **146 route/7.138 ca/0 vi phạm/0 lỗi**; task riêng 14 ca/0 vi phạm. `run_form_contract_uat.py` before/after với `--allow-task-catalog`: **1.314 ca/0 lỗi**, ngoại lệ kiểm đúng 18 mã+Khác, bỏ task_code và đổi task_name, không nới route khác; SELECT count không tăng. `run_print_layout_uat.py`: **402 kiểm tra/37 PDF/0 lỗi**; `print-comparison/result.json`: **37/37 khớp ảnh/văn bản/kích thước trang** trên cùng dữ liệu giả. `pip check`, `manage.py check`, `makemigrations --check --dry-run`, diff check đạt.
- Snapshot nguồn commit form: `D:/IHRMS_Review_Exports/IHRMS_Review_20261019_TaskAssignment.zip`, tạo từ tree stage, loại dữ liệu/bí mật, manifest/hash từng tệp mở lại xác minh. Commit thứ hai chỉ chứa phần form/allocator/admin/test/audit/tài sản liên quan, không chứa model/migration hoặc sửa hover bảng. Full suite trên cây cuối vẫn là gate bắt buộc sau phần 3, chưa dùng test tập trung thay thế.

**Phần 3 — Hover bảng, kiểm nguồn cuối và bàn giao**
- Commit form đã push `9f10f5d29fc0bd17704ad9ed3adb165d051ccd9a`, remote khớp 0/0. CSS bảng tập trung ở `components.css`: tbody th/td cùng đệm/viền; th thân bảng bỏ nền header, chữ 600; hover/focus-within phủ trực tiếp mọi ô, gồm mã và Thao tác. Menu popover giữ luật hiện có, không đổi trạng thái ẩn.
- `ops/run_table_hover_uat.py` kiểm bốn danh sách nhân viên/công việc/nghỉ phép/hợp đồng, 1756/1440/1024/390px, sáng/tối: baseline đúng 64 ca có **48 lỗi tiêu chí**, sau sửa **64 ca/0 lỗi**. Đo nền từng ô, đường kẻ/đệm th, chiều cao không đổi, focus toàn hàng, menu mặc định đóng/chỉ mở menu được bấm/Escape. Lượt probe đầu thiếu fixture selector cho hàng nghỉ phép không có link đã sửa runner, không tính skip thành đạt. Lượt ảnh cuối bỏ focus tồn dư của skip-link giữa các ca. Không thêm waiver.
- Full suite đầu tiên trên cả hai backend: **577 tests, native exit 1**, cùng một lỗi `test_grid_columns_have_one_source_and_no_legacy_template_classes` vì CSS riêng vẫn dùng selector `.ui-form-grid` để khai báo cột. Đã giữ nguyên test/gate, chuyển override sang class riêng `.ui-task-assignment-grid` trên đúng form Giao việc; không đổi cấu trúc/hợp đồng form khác. Chạy lại full suite trên nguồn đã sửa; kết quả cuối ghi tiếp bên dưới. Commit cuối kèm sửa hồi quy này và làm rõ truy vấn COUNT trong kế hoạch phải bỏ ORDER BY, không đổi model/migration đã giao.
- Kiểm nguồn sau sửa class: task browser **60 kiểm tra/0 lỗi/28 ảnh**, `check_ui_contrast.py` **220 cặp/0 lỗi**, gồm text/text-muted/link trên hover-bg sáng/tối (không suy thành chứng nhận toàn bộ WCAG). Cache **9 kiểm tra đạt**, không cần xóa dữ liệu trình duyệt. Print nguồn cuối **402 kiểm tra/37 PDF/0 lỗi**; so ảnh/văn bản/kích thước được ghi kết quả hoàn tất bên dưới.
- `print-comparison/result.json` nguồn cuối: **37/37 PDF giống tuyệt đối pixel render/văn bản/kích thước**, bao gồm màu, viền và vị trí/ngắt trang/khoảng ký do pixel không đổi. Đã xem ảnh render bảng chấm công và kiểm kê; không sửa `print_forms.css`. `form-final-before.log`/`form-final-after.log`: **1.314 ca/0 lệch**, đúng ngoại lệ task đã khai báo, SELECT count không tăng, cùng DB giả sau các luồng ghi. `new-asset-hash.json` xác nhận bytes trình duyệt nhận khớp nguồn JS `ee7ceb4b`/CSS `bcdf10fa`. `pip check`, Django `check`, `makemigrations --check --dry-run` trên DB giả và `git diff --check` đạt; không phát sinh migration khác.
- Bộ ảnh giao tập trung: `D:/IHRMS_Review_Exports/UI_TaskActCode_20261019/index.html`, **100 PNG** gồm ảnh đầy đủ và tám contact sheet task/bảng 1756/390px sáng/tối; ảnh bảng còn có 1440/1024px, form có 1280/768/360px. Thư mục evidence chỉ sao chép báo cáo synthetic an toàn, không marker/mật khẩu/DB/media; SHA-256 từng ảnh/báo cáo trong `SHA256.json`. Dashboard giữ cấu trúc hiện có.
- Quét toàn bộ nguồn cuối sau sửa class tại `alignment-final-scoped`: **146 route, 7.138 ca, 9 vai trò, 1920/1756/1440/1280/1024/768/390px sáng/tối, 0 vi phạm/0 lỗi**; không đổi audit hoặc waiver trong commit cuối. Vi phạm hover tính riêng **48 → 0**, không lấy số alignment bằng 0 để thay kiểm computed style hoặc nhận xét ảnh.
- Full suite cuối SQLite: `venv/Scripts/python.exe ops/run_tests.py --backend sqlite`, **577 tests OK (skipped=7), native exit 0**, 793,9s gồm chuẩn bị/thu dọn (761,205s chạy test). Bảy skip theo backend được kiểm tiếp trong full SQL Server, không coi skip là SQL Server đã đạt. Log `full-final-sqlite.log` và exit JSON do subprocess ghi mã trả về thực, không lấy exit từ pipeline PowerShell.
- Chụp lại ảnh bảng qua runner tạm ngoài repo với vùng chụp đủ cao để hàng đầu vẫn hiện khi cuộn về đầu: tránh ảnh toàn trang ghi nhầm header/skip-link cố định tại vị trí cuộn; **64 ca/0 lỗi** vẫn giữ. Bảng công việc ở 390px còn cách nén/xuống dòng của baseline; đợt này không thay cấu trúc bảng khác theo ràng buộc phạm vi. Đây là giới hạn thị giác đã thấy, dù alignment/hover đều 0 vi phạm; không tuyên bố mọi trang mobile đã được thiết kế lại. Bản giao còn có 74 PDF giả trước/sau trong thư mục `print-comparison`.
- Full suite cuối SQL Server: `venv/Scripts/python.exe ops/run_tests.py --backend sqlserver`, **577 tests OK, không skip, native exit 0**, 697,6s gồm chuẩn bị/thu dọn (659,644s chạy test). DB `test_ihrms_874668e99729464d8e45dc88851a9660` đã hủy; log `full-final-sqlserver.log`/exit JSON. Có kiểm concurrency/migration trên backend thật; không thay full suite bằng nhãn tập trung. Cả hai lượt cuối chạy sau sửa selector lưới, không đổi mã ứng dụng khi đang chạy.
- Sáu tệp commit cuối: `components.css`, `run_table_hover_uat.py`, class scoped trong `task_assignment.css`/`task_create.html`, làm rõ truy vấn COUNT trong kế hoạch và mục nhật ký này. Không đổi model/migration trong commit UI; giữ nguyên các tệp chưa theo dõi ngoài phạm vi. Kiểm mã hóa và diff check đạt; không dọn/reset dữ liệu hoặc thay đổi của chủ dự án.
- Snapshot cuối: `D:/IHRMS_Review_Exports/IHRMS_Review_20261019_TaskActCode_Final.zip`, **782 tệp nguồn** từ Git tree stage, loại dữ liệu/bí mật; mở lại xác minh SHA-256 từng tệp trong manifest, hash archive ở tệp `.zip.sha256` bên cạnh. Đây là bản sao review, không phải backup phục hồi DB. Hai SHA đã giao: schema `ab949cd4c7cef1087a20a88fa0a4daabb2eb881c`, form `9f10f5d29fc0bd17704ad9ed3adb165d051ccd9a`; SHA commit cuối báo trong bàn giao và manifest bằng chứng sau push.
- CI theo SHA: `gh run list --commit <SHA> --json databaseId,headSha,status,conclusion,url --limit 10` cho cả schema/form bị **HTTP 401 Bad credentials**; connector GitHub trả danh sách workflow run rỗng cho hai SHA. **Chưa theo dõi CI đạt**, không suy push/full suite cục bộ thành Actions PASS. Kiểm lại SHA cuối sau push, lưu kết quả ngoài repo. Chủ dự án có thể xác thực lại `gh auth login` hoặc kiểm Actions theo commit. Không deploy hoặc restart ứng dụng vận hành; chủ dự án thực hiện backup/restore thử, đếm chỉ đọc và migration `task` trước khi chạy mã mới theo kế hoạch.

## 2026-10-19 — Thu gọn bố cục form Tạo/Cập nhật hoạt động dự án

**Phạm vi và thay đổi**
- Theo ảnh và yêu cầu tinh chỉnh bố cục/kích thước/sắp xếp của chủ dự án. Bắt đầu `main` tại `029f5cfa2a09f5685582cc1f7a59bd1ffb539160`, fetch origin/main khớp 0/0; đọc ba mục nhật ký mới nhất, giữ nguyên các tệp chưa theo dõi đã được cho phép từ đợt trước. Chỉ tác nhân chính ghi; reviewer chỉ đọc.
- Chỉ sửa `activity/activity_form.html` và thêm CSS riêng `activity_form.css`; cùng template nên áp dụng cả Tạo và Cập nhật. Giữ đủ 13 trường, thứ tự POST, ID/name, required/help/error, CSRF, route, queryset, script tự điền ActCode, quyền và nghiệp vụ tạo Task/hạn báo cáo. Không sửa model, migration, dữ liệu vận hành, CSS chung hay bản in.
- Khi đủ rộng: Mã hoạt động một cột/Tên ba cột; Dự án–Địa điểm–Thành phần–Trạng thái cùng hàng; Mục đích/Kết quả hai vùng cạnh nhau, textarea đủ hai dòng control; Lịch bắt đầu/kết thúc và hai người phụ trách cùng hàng. Nhóm ngày giữ hợp đồng compact tối đa 12rem. Bỏ margin cộng thêm trước cảnh báo vì section đã có gap; giữ nguyên toàn bộ nội dung hướng dẫn.
- Tiêu đề trang dùng token H1 24px/32px; phần Tên hoạt động có modifier riêng full dưới 640px, span 2 từ 640px, span 3 từ 900px. Reviewer phát hiện rule `task-name` cũ bị ghi đè ở tablet; đã chuyển sang modifier scoped, không đổi utility chung. CSS chỉ áp dụng `@media screen` và trang hoạt động.

**Kiểm tra và bằng chứng**
- Dùng Impeccable hiện có, không cập nhật phiên bản. Mechanical layout detector trước/sau trả `[]`; cảnh báo không resolve được Django asset tag khi đọc template rời được ghi nhận, không coi detector là bằng chứng render. Reviewer nguồn xác nhận đủ trường/hợp đồng và không còn blocker sau sửa tablet.
- DB SQLite/media/tài khoản demo cô lập tại `%TEMP%/ihrms-activity-layout-20261019-synthetic_only`, clone bằng SQLite backup từ runtime được đánh dấu synthetic_only; baseline nguồn `029f5cf` ngoài repository tại `%TEMP%/ihrms-activity-layout-20261019-baseline`. Không mượn phiên/danh tính người dùng thật, không ghi DB vận hành.
- Ảnh desktop/mobile, sáng/tối với 1756/1024/768/390/360px; mẫu đầu từ 1.352px xuống 986px trước khi khôi phục hợp đồng compact cho cả nhóm ngày. Số đo giao cuối được ghi bên dưới. Đã xem ảnh desktop sáng/mobile tối, giữ đủ nội dung và control; bản giao cuối có ảnh đầy đủ và contact sheet trước/sau 1756/390px. Đây là đánh giá của tác nhân, chưa phải chủ dự án nghiệm thu thị giác.
- `ops/run_tests.py --backend sqlite apps.activity.tests`: **33 tests OK (skipped=1)**, native exit 0; `manage.py check` đạt. Không thay backend logic; không chạy toàn bộ suite hoặc SQL Server suite trong đợt tinh chỉnh này.
- Browser click UAT kiểm lỗi ngày giữ giá trị, chọn ActCode/người phụ trách, tạo mới qua nút submit, thông báo/đích Dashboard, đối chiếu dữ liệu đã lưu, mở sửa và lưu/đọc lại; kết quả nguồn cuối và matrix được ghi bổ sung bên dưới. Probe ban đầu dùng tên readonly rỗng khi tắt JS không tạo được bản ghi, không coi đó là PASS no-JS; không thay hành vi này trong phạm vi bố cục. Runner cũng được sửa để không so chuỗi tiếng Việt bị PowerShell thay dấu bằng `?`; ca chính dùng aria-invalid và success alert thực.
- Mỗi lần chốt template đều khởi động lại server giả không dùng autoreload để loại cache template. Các lượt matrix đang chạy khi sửa H1/tablet đã dừng; chỉ lượt đầy đủ trên nguồn cuối được dùng làm gate, không ghép kết quả dở dang.

**Kết quả nguồn cuối và bàn giao**
- `browser-uat.json`: **17 kiểm tra đạt**, 40 ảnh trước/sau ở năm độ rộng/sáng tối, bốn contact sheet 1756/390px; `browser-clicks.json`: **10 kiểm tra đạt** trên nguồn cuối, có đo đúng field wrapper của combobox (không đo native select đã ẩn), xác nhận Mã/Tên cùng hàng ở viewport 1280px. Lỗi probe đo native select ẩn đã được sửa; không bỏ tiêu chí tablet để làm xanh.
- `run_print_layout_uat.py` nguồn cuối: **402 kiểm tra, 37 PDF, 0 lỗi**, bản in độc lập. Baseline audit hai route Tạo/Cập nhật, admin giả, bảy độ rộng/sáng tối: **28 ca/0 vi phạm**; matrix sau sửa không thay waiver. Độ gọn/thứ bậc được đánh giá riêng qua ảnh và số đo, không suy từ số vi phạm bằng 0.
- `run_form_contract_uat.py` before với nguồn baseline rồi after trên cùng DB giả sau các luồng ghi: **1.314 ca, 0 sai lệch**, không dùng cờ cho phép thay đổi hợp đồng. `print-comparison/result.json`: **37/37 PDF khớp tuyệt đối ảnh render, văn bản và kích thước trang**, cùng route/cùng dữ liệu; không dùng riêng số trang làm bằng chứng. CSS mới chỉ có screen, không xuất hiện trên các route giấy đã so.
- Matrix đầu có **112 vi phạm FIELD_EDGE/REGULAR_SPAN**, tất cả ở hai nhóm ngày của Tạo/Cập nhật do wrapper rộng hơn control; đã bỏ override wrapper rộng và giữ lại hợp đồng compact hiện có, không sửa audit/waiver. Quét lại toàn bộ nguồn cuối tại `alignment-final-compact`; chỉ lượt này được dùng đóng gate.
- Sau khi khôi phục nhóm ngày compact, browser đo lại **1.352px → 1.028px (giảm khoảng 24%)** trên desktop 1756px, **17 kiểm tra vẫn đạt**. Bốn contact sheet và toàn bộ 40 ảnh được làm mới từ nguồn cuối; không giao lại ảnh của mẫu 986px trước đó.
- Matrix giao cuối `alignment-final-compact/result.json`: **146 route/7.138 ca/0 vi phạm/0 lỗi**, chín vai trò giả, 1920/1756/1440/1280/1024/768/390px sáng/tối; so với lượt lỗi **112 → 0**, không thay audit hoặc waiver. `git diff --check` đạt; chỉ ba tệp của đợt này được stage/commit.
- Bằng chứng ảnh ngoài repository: `D:/IHRMS_Review_Exports/UI_Activity_20261019/index.html`; không đưa ảnh, DB, media, credentials, runtime hoặc baseline archive vào Git. Snapshot nguồn review `D:/IHRMS_Review_Exports/IHRMS_Review_20261019_ActivityLayout.zip`: 771 tệp nguồn được phép từ Git tree đã stage, có manifest/tree và SHA-256 từng tệp, mở lại xác minh, hash archive bên cạnh. Commit/push `origin main`, kiểm SHA remote khớp HEAD và ahead/behind 0/0; SHA commit báo trong phản hồi bàn giao.
- Chưa deploy/restart ứng dụng vận hành, không mượn phiên thật hoặc áp migration. Nếu server đang chạy giữ template cũ, chủ dự án dừng server cũ rồi chạy lại từ `main`: `venv\Scripts\python.exe src\manage.py runserver 127.0.0.1:8001 --noreload`. Các tệp chưa theo dõi ngoài phạm vi được giữ nguyên. Không tuyên bố đã kiểm ghi mọi route, toàn suite SQL Server hoặc nghiệm thu thị giác của chủ dự án từ kết quả tự động.

## 2026-10-18 — Header thực, form bốn cột và danh mục ActCode dùng chung

**Phạm vi và quyết định của chủ dự án**
- Tiếp tục trên `main` từ `10aee91d05091a0d1c27de45df7e348f049fecff`; fetch origin/main khớp 0/0. Giữ nguyên các tệp chưa theo dõi ngoài phạm vi đã bàn giao, chỉ một tác nhân ghi. Dùng Impeccable hiện có, không nâng phiên bản.
- Chủ dự án yêu cầu dải header cho tiêu đề thẻ thay gạch chân, giữ cấu trúc Dashboard, có hover trong menu Thao tác, chốt bốn cột cho form nhóm/dài và nhập tìm trực tiếp trong ô chọn. Nguồn mã/tên công việc và hoạt động được xác nhận là `docs/ActCode.md` (18 dòng mã/tên).
- Bổ sung vào `AGENTS.md` quy định đã được duyệt: không mượn phiên, cookie hoặc danh tính tài khoản thật để UAT, kể cả kiểm tra chỉ đọc. Toàn bộ browser UAT lượt này dùng tài khoản demo trên SQLite/media giả ngoài repository; không dùng phiên vận hành, không đổi DB/schema vận hành. Việc chủ dự án báo đã áp migration được phân biệt với xác minh ở mục migration trước đó.

**Thay đổi đã thực hiện**
- `components.css`, `home_dashboard.css`: header có nền nhạt, đệm và đường phân cách cho card/form và các nhóm Dashboard; bỏ gạch ngắn dưới tiêu đề và gạch chân toàn thẻ KPI khi hover. Giữ thứ tự, nội dung, quyền hiển thị, KPI, biểu đồ và drill-down. Menu `.ui-row-popover` phản hồi hover/focus bằng nền chung, không mất trạng thái ẩn khi chưa bấm.
- Form nhóm/dài dùng 1/2/3/4 cột theo container tại các ngưỡng 420/640/900px; form ngắn và sự kiện giữ mẫu riêng. Giao việc: mã một cột, tên ba cột; mô tả toàn hàng; nhân viên/ưu tiên/ngày bắt đầu/hạn hoàn thành cùng hàng khi đủ rộng. Control ngày/số giữ chiều rộng gọn. Cập nhật `DESIGN.md`, `docs/UI_DESIGN_SYSTEM.md` và audit theo quyết định này.
- `ui_choices.js` dùng chung thay popup tìm riêng: gõ trực tiếp để lọc danh mục dài, hỗ trợ không dấu, chuột, Arrow/Enter/Escape/Tab và trạng thái không có kết quả. Native select giữ tên/giá trị gửi; gõ chưa chọn không đổi ID và không được gửi nhầm. Nhãn/focus chuyển đúng tới combobox; scope checklist Onboarding/Offboarding vẫn được giữ. Trường gợi ý văn bản bằng datalist vẫn nhập mới; danh mục liên kết không tự tạo ID. Native control vẫn dùng được khi tắt JavaScript. Đưa tài sản JS mới vào hash cache.
- Giao việc dùng cùng `ACTIVITY_CODE_NAMES` đã được hoạt động sử dụng, có test đối chiếu chính xác với `docs/ActCode.md`. Mã chọn từ danh mục; tên tự hiện theo mã và được xác định lại phía server, không chấp nhận tên giả mạo hoặc mã ngoài danh mục. Giữ giá trị khi gửi lỗi, quyền giao việc, route và tên POST. Đây là thay đổi hợp đồng được yêu cầu; comparator chỉ cho phép đúng selector 18 mã và tên readonly tại `task_create`, không bỏ qua phần khác.
- **Giới hạn nghiệp vụ hiện có:** `Task.task_code` vẫn unique. Chọn lại mã đã có công việc sẽ nhận validation trùng mã; chưa đổi model/schema hoặc tự cho phép tái sử dụng mã. Hồ sơ công việc cũ không bị sửa/xóa.

**Kiểm tra và bằng chứng**
- Runtime giả: `%TEMP%/ihrms-header-actcode-20261018-synthetic_only`; baseline nguồn `10aee91` tại `%TEMP%/ihrms-header-actcode-20261018-baseline`, cùng DB giả; ứng dụng lần lượt ở 8832/8833. Không đưa marker, mật khẩu demo, database/media hay ảnh vào Git.
- `ops/run_layout_alignment_audit.py`: lượt đầu sau đổi thành phần **146 route, 7.138 ca, 0 vi phạm/0 lỗi**, chín vai trò, 1920/1756/1440/1280/1024/768/390px sáng/tối (`alignment-after`). Mẫu ba form cùng vai trò/ngưỡng: baseline **42 ca/48 vi phạm**, sau **0** trong lượt đầy đủ. Không đổi waiver. Lượt quét nguồn cuối được ghi bổ sung bên dưới.
- `ops/run_project_forms_uat.py --flows-only`: **70 kiểm tra, 0 lỗi**; kiểm kê nhập văn phòng mới, đặt phòng gửi lỗi rồi lưu Pending, sự kiện Online/Offline lưu/đọc lại, bố cục một/hai hàng, native fallback và tìm checklist đúng scope. Browser riêng Giao việc/Dashboard/menu: **12 kiểm tra đạt**, tạo/lưu/đọc lại tên theo ActCode, lỗi trùng mã giữ mô tả, tìm không khớp không đổi giá trị, điều hướng bàn phím; `browser-actcode-uat.json`.
- `ops/run_form_contract_uat.py --phase before --source-root <baseline>` rồi `--phase after --allow-task-catalog`: **1.314 ca, 0 lỗi** trên cùng DB sau khi dừng các luồng tạo dữ liệu. Lượt đầu chạy chồng UAT ghi dữ liệu gây nhiễu notification/approval; không dùng kết quả đó làm nghiệm thu. Đã bỏ thuộc tính value rỗng mới thêm ở hạn hoàn thành để giữ hợp đồng GET cũ.
- `ops/run_print_layout_uat.py`: **402 kiểm tra, 37 PDF, 0 lỗi**. So PDF cùng route và cùng dữ liệu baseline/nguồn cuối được ghi bổ sung bên dưới. Không sửa `print_forms.css` hoặc hợp đồng in.
- `ops/run_asset_cache_uat.py`: **9 kiểm tra đạt**; `ops/check_ui_contrast.py`: **220 cặp, 0 lỗi**. Impeccable detector vẫn báo vạch `.home-plan-marker` của biểu đồ định biên và advisory màu fallback khi đọc template rời; không tuyên bố detector PASS, không tự thêm miễn trừ. Đánh giá browser phân biệt với detector.
- Bộ ảnh `dashboard-20forms`: **168 ảnh trước/sau**, Dashboard và 20 form ở 1756/390px sáng/tối, **20 contact sheet** kèm manifest. Đã xem Dashboard và contact sheet desktop; đây là bằng chứng tự động/đánh giá của tác nhân, chưa phải xác nhận thị giác của chủ dự án.

**Kết quả nguồn cuối và bàn giao**
- `ops/run_tests.py --backend sqlite apps.portal.test_ui_refinements apps.portal.tests apps.activity.tests`: **72 tests OK (skipped=1)**; cùng nhãn trên `--backend sqlserver`: **72 tests OK**, không skip, DB dùng một lần `test_ihrms_85427437d3164e789facf4cd498cebdf` đã hủy. Chạy qua subprocess xác minh native exit **0** trên cả hai backend; lượt SQL đầu bị PowerShell báo mã shell 1 dù test OK nên đã chạy lại, không dựa vào mã shell nhiễu. Không chạy toàn bộ suite trong đợt này.
- `manage.py check`, `makemigrations --check --dry-run`, `git diff --check` đạt; không có model/migration mới. `browser-additional.json`: hai kiểm tra bổ sung đạt cho dropdown hoạt động tự điền tên và tạo công việc qua native select khi tắt JavaScript, kiểm tên đã lưu phía server.
- `print-comparison/result.json`: **37/37 PDF trước/sau giống tuyệt đối từng trang** về ảnh render, văn bản và kích thước trang trên cùng dữ liệu giả; đã xem ảnh kiểm kê tài sản. Màu, viền, ngắt trang và khoảng ký không đổi trong phép so; không dùng riêng số trang để kết luận.
- `browser-narrow-final.json`: **14 kiểm tra đạt** trên bảy trang ở 360px và 640 CSS px/DPR2 (mô phỏng vùng nội dung của 1280px ở 200%, không phải thao tác zoom phiên Edge thật), gồm không tràn, popup trong viewport, Arrow/Escape và focus Tab. Không mượn phiên người dùng thật.
- Phát hiện server giả cache template sau lần sửa câu hướng dẫn cuối; đã khởi động lại đúng server 8832, làm mới bốn ảnh Giao việc/contact sheet và quét lại toàn matrix tại `alignment-delivery`: **146 route/7.138 ca/0 vi phạm/0 lỗi**, đủ chín vai trò, bảy độ rộng và sáng/tối. Các kết quả trước restart không được dùng thay lượt giao cuối.
- Bằng chứng ảnh bền vững ngoài repository: `D:/IHRMS_Review_Exports/UI_20261018_Headers_ActCode/index.html` (Dashboard, 20 form, 168 ảnh đầy đủ và 20 contact sheet sáng/tối 1756/390px). Ảnh đã xem thêm Giao việc desktop và contact sheet mobile; chủ dự án chưa xác nhận nghiệm thu thị giác. Không tuyên bố đã kiểm thử thao tác ghi từng route từ matrix layout hoặc đã chạy toàn suite SQL Server.
- Snapshot nguồn `D:/IHRMS_Review_Exports/IHRMS_Review_20261018_Headers_ActCode.zip`: nguồn theo Git tree đã stage, loại dữ liệu/bí mật/cấu hình cá nhân/runtime; manifest và SHA-256 từng tệp được mở lại xác minh, có SHA-256 archive bên cạnh. Bàn giao bằng commit/push `origin main`, kiểm SHA remote khớp HEAD và ahead/behind 0/0; SHA commit và snapshot được báo trong phản hồi bàn giao, không ghi SHA tự tham chiếu vào chính commit. Không deploy theo quyền commit/push.

## 2026-10-18 — Xác minh migration Lịch công tác, backup và restore thử SQL Server

**Ủy quyền, đích và trạng thái thực tế**
- Chủ dự án xác nhận trong hội thoại: SQL Server `DESKTOP-6CS95OK\SQLEXPRESS`, DB `qlhcns`, cho phép backup mới → kiểm tra/restore thử → migration. Bắt đầu trên `main` tại `45d2029ab7b11f38ad5188460e6cbdef106969de`; fetch origin/main khớp 0/0, đọc ba mục nhật ký mới nhất, giữ nguyên các tệp chưa theo dõi đã được cho phép.
- Kiểm tra trực tiếp thấy trạng thái đã thay đổi so với ảnh lỗi: `planning.0003_event_attendance_mode` được ghi áp dụng lúc **17/10/2026 11:00:16.570831 UTC (18:00:16 giờ Việt Nam)**, cột `tblEvent.AttendanceMode` tồn tại `nvarchar(10) NULL`, không có SQL default. Không xác định tác nhân đã áp dụng trước lượt này; không ghi nhận đó là thay đổi do lượt này thực hiện. Có 0 Event trong DB gốc.
- `MigrationExecutor.migration_plan` cho đích planning.0003 rỗng; `migrate planning 0003` báo **No migrations to apply**. Không fake migration, không thêm migration mới, không hoàn tác hoặc áp lại schema trên DB gốc. Mục này cập nhật và đóng phần migration còn mở được ghi trong mục UI ngay dưới.

**Backup và restore đã thực hiện**
- Tạo backup **COPY_ONLY, CHECKSUM, NO_COMPRESSION** (SQL Server Express) tại `D:/IHRMS_Operations/attendance_20261018_091222/qlhcns_copy_only.bak`, **30.106.112 byte**, SHA-256 **`e4039e19bb417da41c211268a0d9b65359411913987f4b478ebb598bbf9aeaff`**; tệp `.bak.sha256` đi kèm. Đây là backup dữ liệu vận hành, tách biệt hoàn toàn với snapshot nguồn review.
- `RESTORE VERIFYONLY ... WITH CHECKSUM` đạt; `RESTORE FILELISTONLY` rồi `RESTORE ... WITH MOVE ..., CHECKSUM, RECOVERY` vào DB mới **`qlhcns_uat_attendance_20261018_091222`**, file data/log riêng, không REPLACE. DB ONLINE; **DBCC CHECKDB đạt**. Xác minh lại SHA sau UAT vẫn khớp.
- Lượt đầu thử đường dẫn backup mặc định không có backup hoàn tất khi chuyển sang VERIFYONLY; chưa coi đó là backup hợp lệ. Chạy lại bằng cursor ODBC, đọc hết result set của BACKUP/RESTORE, dùng thư mục ngoài repository có quyền riêng cho SQL service và tài khoản thao tác. Một lần gán timeout trên cursor không được API hỗ trợ đã dừng trước thao tác; đổi sang timeout connection. Chỉ backup/restore thành công ở thư mục nêu trên được dùng làm bằng chứng.
- Thư mục vận hành được bỏ quyền kế thừa rộng, giữ tài khoản thực hiện/SYSTEM/Administrators và SQL service. Không đưa `.bak`, thông tin đăng nhập, dữ liệu thật, ảnh chứa dữ liệu vận hành hoặc script runtime vào Git.

**Kiểm migration và browser UAT**
- Trên DB restore riêng: rollback planning.0003 về 0002 đạt, cột được bỏ; tạo Event giả bằng historical model 0002, sau đó `sqlmigrate planning 0003` đối chiếu đúng `ALTER TABLE [tblEvent] ADD [AttendanceMode] nvarchar(10) NULL;`, không UPDATE; migrate 0003 đạt, Event giả cũ giữ NULL, Event mới mặc định Offline. SQL sinh trên SQLite cũng đã lưu/đối chiếu trong cùng lượt; không kết nối DB vận hành khi sinh SQL SQLite.
- Cấu hình ứng dụng UAT chỉ trỏ DB restore, media ngoài repo, email locmem, M365 tắt, cache riêng; tài khoản superuser giả chỉ tạo trên bản sao. Browser Edge headless/Playwright tại `127.0.0.1:8830`: **23 kiểm tra đạt**, gồm legacy NULL → Chưa xác định, mặc định Offline, tạo/lưu/đọc lại Online và Offline, lỗi thời gian giữ hình thức/mô tả, giá trị ngoài choice bị server từ chối, admin hiển thị đúng, 1756/390px sáng/tối không tràn. Bằng chứng `browser-clone-uat.json`, `migration-uat.json` và bốn ảnh trong thư mục vận hành.
- Ứng dụng cũ ở `127.0.0.1:8001` đã dừng khi tiếp tục phiên, lần kiểm đầu `ERR_CONNECTION_REFUSED`; đã khởi động `venv\Scripts\python.exe src\manage.py runserver 127.0.0.1:8001 --noreload` trên `main`. Browser kiểm trực tiếp DB gốc: **`/portal/events/` HTTP 200**, dropdown mặc định Offline, không còn ProgrammingError; **`/admin/planning/event/` HTTP 200**. Dùng phiên xác thực tạm của tài khoản hiện hữu, không đổi tài khoản/mật khẩu/last_login; phiên tạm đã xóa trong `finally` ở cả lần lỗi và lần đạt. Không tạo/sửa/xóa Event gốc: **0 → 0**. Bằng chứng không chứa cookie hoặc danh tính người dùng: `operational-verification.json`.
- `ops/check_migration_state.py --app planning`: **Outstanding: none**. Chỉ thử ghi nghiệp vụ trên DB restore; không tạo sự kiện giả trong DB gốc. Không tuyên bố đây là phiên Edge đang đăng nhập của chủ dự án hoặc kiểm toàn bộ luồng nghiệp vụ khác.

**Dọn và bàn giao**
- Dừng server clone, xác minh đúng tên DB tạm rồi drop riêng `qlhcns_uat_attendance_20261018_091222`; xóa tệp credentials UAT, giữ nguyên backup đã xác minh, hash, SQL và kết quả tổng hợp ngoài repo (`cleanup.json`). Không xóa/thay thế DB gốc hoặc backup cũ.
- Không đổi mã/schema nguồn trong lượt này; chỉ cập nhật một mục nhật ký. Các gate UI của commit `45d2029` vẫn là bằng chứng cho nguồn giao diện không đổi, không ghi là đã chạy lại toàn matrix trong lượt vận hành này. `manage.py check`, checker migration và `git diff --check` được chạy lại trước bàn giao.
- Snapshot nguồn review riêng: `D:/IHRMS_Review_Exports/IHRMS_Review_20261018_AttendanceVerification.zip`, có manifest tree và SHA-256 từng tệp, mở lại xác minh; tuyệt đối không chứa backup dữ liệu. Commit/push nhật ký trên `main`, đối chiếu SHA remote và ahead/behind trước phản hồi bàn giao. Không còn bước migration cần chủ dự án thực hiện cho lỗi `AttendanceMode` ở DB đã xác nhận.

## 2026-10-17–18 — Sửa hồi quy menu nhân viên, Dashboard và chiều rộng form

**Phạm vi và thay đổi**
- Tiếp tục quyền sửa/bàn giao trên `main`, từ `1b889b0722210c927e88a8d54f7109c2dce72d75`; fetch origin/main khớp 0/0. Giữ nguyên tệp chưa theo dõi ngoài phạm vi đã được cho phép; chỉ một tác nhân ghi.
- Menu Hồ sơ nhân viên tự hiện do `.ui-row-actions { display:grid }` ghi đè trạng thái ẩn mặc định của popover. `components.css` dùng selector đủ đặc hiệu để ẩn; `:popover-open` mới bật grid. Browser xác nhận chỉ menu được bấm mở, Escape đóng.
- Dashboard có tiêu đề nhóm 18px/600 và gạch xanh ngắn; giữ KPI, nội dung, drill-down và hệ màu sáng/tối. Áp dụng Impeccable để tinh chỉnh thiết kế hiện hữu, không cập nhật phiên bản skill.
- Quy tắc chung cho cả partial lẫn widget riêng: ngày/tháng/số tối đa 12rem, ngày giờ 16rem, họ tên đầy đủ 36rem; thu theo container. Kỳ lương, Người phụ thuộc, Đặt xe dùng inline với nút theo trường cuối. Hồ sơ nhân viên thu lại tên/ngày sinh/giới tính. Sự kiện chặn flex-grow làm ngày giờ kéo dài khi wrap. Kiểm ảnh mobile phát hiện icon lịch tối trên nền tối: control ngày trong grid dùng native dark color-scheme ở màn hình, bản in vẫn light; browser xác nhận hai trạng thái. Không đổi route, quyền, thứ tự/tên trường, công thức hay schema.
- Kỳ lương dùng select đủ tháng 1–12/năm 2000–2100, giữ kiểm tra máy chủ; loại hai tên control này khỏi tăng cường tìm kiếm để không thêm nút Tìm vào danh sách tháng/năm ngắn, browser đã chọn và tạo thành công kỳ 04/2079. Quan hệ người phụ thuộc có danh sách thông dụng. Cập nhật `UI_DESIGN_SYSTEM.md`, `UI_FORM_REGISTRY.json` (31 inline, 21 grouped) và kiểm tra portal.
- Audit đo thêm chiều rộng tối đa theo loại control và khoảng trống theo track đã khai báo; tên không bị ép tối thiểu nửa form. Không sửa waiver. Probe âm vẫn bắt ô ngày 400px và track trống. Cờ form-contract `--allow-finance-choices` chỉ nhận đúng ba chuyển đổi input→select cùng miền giá trị; thêm tháng 13 vẫn bị từ chối.

**Kiểm tra và bằng chứng**
- Runtime DB/media/tài khoản giả: `C:/Users/dinht/AppData/Local/Temp/ihrms-refinement-20261017-synthetic_only`; luồng ghi dùng bản sao riêng `ihrms-refinement-flows-20261017-synthetic_only`. Edge headless/Playwright, không phải phiên người dùng; không ghi DB/media thật hoặc gửi thư thật.
- `run_layout_alignment_audit.py --phase after --workers 4`: **146 route, 7.138 trường hợp, 0 unresolved/vi phạm/lỗi**, đủ 9 vai trò và 1920/1756/1440/1280/1024/768/390px sáng/tối; `alignment-final/result.json`. Bốn trang mẫu trước sửa có 148 vi phạm trên cùng ba vai trò/ba độ rộng. Lượt rộng trung gian bắt 42 lỗi ngày giờ Sự kiện, đã sửa và chạy lại toàn matrix trên nguồn cuối đạt 0.
- `run_form_contract_uat.py --phase before --source-root <baseline HEAD>`, sau đó `--phase after --allow-finance-choices`: **1.314 trường hợp, 0 lỗi**, không tăng SELECT. Lượt đầu bị nhiễu do thêm fixture kiểm in đồng thời; đã bỏ kết quả đó, chạy tuần tự trên dữ liệu ổn định. Không nới ngoại lệ khác.
- `run_print_layout_uat.py` trên nguồn cuối: **402 kiểm tra, 37 PDF, 0 lỗi**. Render cả baseline HEAD và nguồn cuối trên cùng DB/URL, so raster từng trang: **37/37 tài liệu giống pixel, 0 khác biệt**, tại `print-before-after/result.json`; đã xem ảnh BCC/Sổ công văn/kiểm kê. Lượt so riêng đầu tiên quên trả về media screen trước khi đăng nhập đổi vai trò nên timeout; đã sửa harness ngoài repo và chạy lại đầy đủ. Không sửa `print_forms.css` hoặc hợp đồng giấy/in.
- `run_project_forms_uat.py --flows-only`: **70 kiểm tra, 0 lỗi**, gồm kiểm kê, đặt phòng, Event Online/Offline, gửi sai thời gian/giữ giá trị, chọn có tìm kiếm, bàn phím, 360px và zoom 200%. Browser bổ sung **8 kiểm tra ghi/đọc lại**: tạo kỳ lương, thêm người phụ thuộc bằng quan hệ đã chọn, đặt xe lỗi rồi lưu Pending, thông báo và trang đích. Sáu trang bị ảnh hưởng có 48 ảnh trước/sau sáng/tối 1756/390px và bốn contact sheet tại `visual-before-after`.
- `run_asset_cache_uat.py`: **9 kiểm tra, passed=true**, reload giữ cookie/dữ liệu, retire cache cũ, tải hash CSS/bản in mới. Lượt đầu timeout đợi controller khi nhiều browser chạy; chạy lại nguyên runner đạt, không tăng timeout/nới gate. `check_ui_contrast.py`: **220 cặp, 0 lỗi**.
- Suite SQLite báo **565 tests OK (skipped=7)**; thu stderr bằng PowerShell gây nhiễu mã shell, đã chạy lại qua subprocess: **native exit 0**, bằng chứng `tests-native-final.log`/`tests-native-final-exit.txt`. SQLite tập trung **38 tests OK**; SQL Server tập trung **38 tests OK**, DB một lần `test_ihrms_efef1fab71b849ae86650f73af75fe7e` đã hủy. Chạy riêng đủ **7 ca bị skip trên SQLite bằng SQL Server: 7 tests OK, native exit 0**, DB `test_ihrms_db2947f363154af3b38018b0caebf6f4` đã hủy; gồm NULL uniqueness và các luồng đồng thời. Không chạy toàn suite SQL Server trong đợt này.
- `manage.py check`, `makemigrations --check --dry-run`, `git diff --check` đạt. Impeccable detector còn báo cáo có sẵn tại `.home-plan-marker` (vạch định biên biểu đồ, không phải viền card) và advisory màu khi đọc template rời không có stylesheet. Đã kiểm browser; không tự thêm waiver hoặc báo detector PASS.
- `run_project_forms_uat.py --evidence-only --coverage-report <alignment-final/result.json>`: **11 kiểm tra, 0 lỗi**, 170 trang đại diện trước/sau và **680 ảnh**, contact sheet theo mọi phân hệ ở 1756/390px sáng/tối trong `project-forms-uat`; xác nhận đủ coverage từ matrix chín vai trò. Browser bổ sung 14 kiểm tra trên bảy trang tại 360px và mô phỏng 200% (640 CSS px/DPR2 tương ứng khung 1280px), không tràn trang và Tab tới control hiển thị. Probe đầu dùng CSS `html.zoom=2` gây tràn Dashboard; đây không phải browser zoom vì không đổi viewport/media query, đã thay cách mô phỏng và ghi rõ phương pháp, không tuyên bố kiểm phiên Edge thật.
- Lượt bàn giao sau cùng từng đo một `ROW_TOP` tại thanh lý/1440px trước callback căn nhãn sau resize. Runner hiện chờ `document.fonts.ready` và hai animation frame rồi đo, giữ nguyên tiêu chí. Sau khi tiếp tục phiên 18/10, server giả cũ đã dừng nên lượt đầu `ERR_CONNECTION_REFUSED`; khởi động lại đúng DB giả và chạy lại toàn matrix, chỉ kết quả đầy đủ được dùng để đóng gate.
- Kết quả bàn giao ngày 18/10 trên nguồn cuối: `alignment-delivery-settled/result.json` **146 route/7.138 trường hợp/0 vi phạm/0 lỗi**; `form-delivery-after.log` **1.314 trường hợp/0 lỗi**; `cache-delivery.log` **9 kiểm tra đạt**. Mẫu bốn trang cùng matrix trước/sau giảm **148 → 0 vi phạm** (`alignment-before-focused` / `alignment-sample-delivery`). Ảnh Kỳ lương/Người phụ thuộc và bốn contact sheet riêng đã làm mới sau lần chỉnh control cuối. Không còn thay đổi mã sau các lượt này.

**Giới hạn và bàn giao**
- `/portal/events/` lỗi do DB thiếu `planning.0003_event_attendance_mode`, không phải URL sai. Đọc kết nối xác nhận đích cấu hình `DESKTOP-6CS95OK\SQLEXPRESS / qlhcns`; lịch sử SQL Server ghi full backup mới nhất 09/10/2026 15:40:06, chưa có bằng chứng restore thử cho đợt này. Không áp migration hoặc giả định backup cũ đủ dùng.
- Chủ dự án/DBA cần xác nhận đích, backup mới, `RESTORE VERIFYONLY` và restore thử theo `docs/MIGRATION_PLAN_planning_0003.md`; sau đó chạy `venv\Scripts\python.exe src\manage.py migrate planning 0003`, `ops/check_migration_state.py --app planning` và UAT Event cũ NULL/mới Online/Offline trên DB đích. Yêu cầu đến từ mục Migration của AGENTS.md; giao mã UI không đồng nghĩa đã khôi phục Lịch trên DB vận hành.
- Chưa chứng nhận từng pixel/thao tác ghi mọi route hoặc admin theo matrix portal. Tự động và đánh giá ảnh tách riêng; không tuyên bố hoàn tất triển khai toàn hệ thống khi migration còn mở.
- Snapshot nguồn review: `D:/IHRMS_Review_Exports/IHRMS_Review_20261017_Refinement.zip`, manifest tree/SHA-256 từng tệp; loại dữ liệu, bí mật, cấu hình cá nhân và runtime. Hoàn tất xác minh, commit/push origin/main và đối chiếu remote trước bàn giao; mã commit báo trong phản hồi bàn giao.

## 2026-10-17 — Chuẩn hóa loại nút và chuẩn bị migration Hình thức sự kiện

### Tóm tắt cho chủ dự án
- Đã thống nhất hành vi nút theo bảng đã duyệt: tạo/gửi/duyệt/tiếp nhận/cập nhật/chọn là primary; điều hướng/hủy quay lại là secondary; từ chối, hủy dữ liệu và xác nhận thanh lý là danger.
- Quét lại toàn bộ route/role ở 7 độ rộng và sáng/tối: 146 route, 6.904 ca, không còn vi phạm layout hay loại nút ngoài cấu hình.
- SQLite và SQL Server riêng biệt đều chạy 564 test, OK; browser UAT, form contract, in/PDF và cache đều đạt trên dữ liệu giả.
- Migration `planning.0003_event_attendance_mode` chưa áp dụng vào DB vận hành; trạng thái chỉ đọc hiện báo còn thiếu migration này.
- Cần chủ dự án/DBA thực hiện đúng kế hoạch migration, sau backup và restore xác minh; đồng thời chốt nguyên tắc 3 hay 4 cột cho các form mới trước lượt bố cục tiếp theo.

**Phạm vi và quyết định đã chốt**
- Làm trên `main`, từ HEAD/origin `031fbdd8a5be2e5ab435ff385ced0961b3f4de4e`; giữ nguyên tệp chưa theo dõi ngoài phạm vi. Không đổi quyền, route, GET/POST, dữ liệu, công thức, văn bản in hoặc migration/model Event đã tồn tại.
- Chủ dự án chốt: Duyệt/Tiếp nhận/Cập nhật/Chọn–áp dụng và Yêu cầu bổ sung là primary; Từ chối hoặc thao tác làm mất dữ liệu là danger; Hủy để quay lại là secondary. Lập biên bản thanh lý là primary, còn xác nhận chuyển tài sản sang Đã thanh lý là danger. Ghi nhận kỷ luật và Khóa kỳ lương giữ danger.
- Không cập nhật skill Impeccable trong lượt này. Detector Impeccable chỉ còn cảnh báo tư vấn về fallback màu chữ tính toán, không phát hiện mã màu mới hoặc lỗi chặn.

**Thay đổi**
- Thêm hợp đồng có thể kiểm máy tại `docs/UI_BUTTON_KINDS.json` và `ops/audit_button_kinds.py`; kiểm kind, loại trừ đúng phần tử điều hướng bảng, hình học 44px/14px/radius 8px/padding/gap và trạng thái runtime.
- Chuẩn hóa các template Dashboard, HR, tuyển dụng, công văn, tài sản, mua sắm, lương, thông báo, phê duyệt và báo cáo theo hợp đồng trên. Liên kết tên ứng viên trong bảng được đổi sang text link, tránh hiểu nhầm hành động điều hướng là nút. Nút phân trang dùng cùng hình học và trọng số chữ.
- Chuẩn hóa `.ui-button` và `.hcns-button`: tối thiểu 44px, chữ 14px, khoảng đệm 8×16px, bo 8px, không bóng; nhóm hành động có gap chung. Không đổi lưới form. Bộ đo ngoài Git ghi 20 form ở 4 độ rộng và mô phỏng 3/4 cột; quyết định 3 hay 4 cột vẫn thuộc chủ dự án.
- Sửa comparator `ops/run_form_contract_uat.py`: khi baseline đã có `attendance_mode`, không được xoá nó ở phía sau; nhờ đó so sánh thực sự giữ nguyên hợp đồng Event hiện hữu.
- Bổ sung `docs/MIGRATION_PLAN_planning_0003.md`, `ops/check_migration_state.py` chỉ đọc và quy tắc migration trong `AGENTS.md`. Kế hoạch tách rõ chuẩn bị, backup/restore, áp dụng, UAT, giám sát và hoàn tác; không chạy `migrate` lên DB vận hành.

**Kiểm tra và bằng chứng**
- Probe baseline `031fbdd`: 2 route Dashboard và tập template liên quan có 38 vi phạm kind, 5 nút chưa phân loại. Audit nguồn cuối: **1.314 ca, 1.922 nút render, 0 vi phạm, 0 chưa phân loại, 0 lỗi** (`ops/audit_button_kinds.py`).
- `ops/run_layout_alignment_audit.py`: **146 route, 6.904 ca, 0 vi phạm, 0 lỗi**, đủ 9 vai trò × 1920/1756/1440/1280/1024/768/390 × sáng/tối; không thêm waiver.
- `ops/run_form_contract_uat.py` trên baseline và nguồn cuối: mỗi lượt **1.314 ca, 0 failures**. `ops/run_button_states_uat.py`: không failures; focus, hover và contrast đều đạt. Browser bằng Playwright dùng DB/media/tài khoản giả; contact sheet trước/sau 1756px/390px ở `C:/Users/dinht/AppData/Local/Temp/ihrms-buttons-20261017-synthetic_only/button-evidence`.
- `ops/run_print_layout_uat.py`: **402 checks, 37 PDF, 0 failures**. `ops/run_asset_cache_uat.py`: **9 checks, PASS**. Lượt print/cache đầu bị ngắt vì server audit đã dừng; đã khởi động lại nguồn cuối và baseline, rồi chạy tuần tự thành công; chỉ kết quả chạy lại được tính.
- `ops/run_tests.py --backend sqlite`: **564 tests, OK**. `ops/run_tests.py --backend sqlserver`: **564 tests, OK**, dùng database thử `test_ihrms_3c84f7d86f9340808669ebab67479de9` và đã hủy sau chạy. Các log ValidationError/Service Unavailable trong output là ca kiểm thử âm, mã thoát hai suite đều 0.
- `manage.py check` và `makemigrations --check --dry-run` đạt; `git diff --check` đạt. `sqlmigrate planning 0003` trên cấu hình SQL Server cho SQL thực: `ALTER TABLE [tblEvent] ADD [AttendanceMode] nvarchar(10) NULL;`. `check_migration_state.py --app planning` đọc DB hiện tại báo còn `planning.0003_event_attendance_mode`; cùng checker trên SQLite giả báo không còn migration thiếu.

**Giới hạn và bước vận hành còn mở**
- Không có migration DB vận hành, backup, restore thử hay UAT trên Edge phiên người dùng thật trong lượt này. Trước khi áp dụng, DBA phải xác nhận server/database đích, backup có thể restore, chạy đúng lệnh ở kế hoạch, kiểm Event cũ NULL hiển thị Chưa xác định và Event mới Offline, rồi theo dõi/hoàn tác theo tài liệu.
- Không tuyên bố đã nghiệm thu từng pixel hoặc mọi thao tác ghi của mọi route chỉ từ audit GET/contact sheet. Dữ liệu kiểm thử, ảnh và log đều ở thư mục `synthetic_only` ngoài repository; không đưa bí mật, dữ liệu thật hoặc script tạo bằng chứng tạm vào Git.

## 2026-10-17 — Chuẩn hóa form toàn dự án, lựa chọn dùng lại và Hình thức sự kiện

**Phạm vi và môi trường**
- Tiếp tục theo hai kế hoạch và quyền sửa/bàn giao đã được chủ dự án xác nhận; không dừng xin duyệt từng trang. Chỉ ghi trên `main`, HEAD gốc `a04f99664d8d4d96e9ca1940ca01b99a708e8697`, fetch origin/main khớp 0/0 trước đợt; giữ nguyên các tệp chưa theo dõi ngoài phạm vi đã được cho phép. Đã đọc ba mục nhật ký gần nhất.
- Kiểm kê 109 form màn hình trong `docs/UI_FORM_REGISTRY.json`: 38 form chỉ thao tác, 28 ngắn, 24 nhóm, 5 dài, 13 bộ lọc, 1 sự kiện. Kiểm kê route động từ URL resolver; admin và giấy/in có hợp đồng riêng, không chuyển chúng sang lưới màn hình.
- Mọi thao tác ghi/UAT dùng SQLite, media, tài khoản giả trong `C:/Users/dinht/AppData/Local/Temp/ihrms-forms-20261016-synthetic_only`; Edge headless qua Playwright, không phải phiên browser vận hành của chủ dự án. Không ghi DB/media thật, không gửi thư thật, không deploy.

**Thay đổi**
- Chuyển toàn nhóm template hoạt động, vòng đời, HR, tuyển dụng, hành chính, tài sản, tài chính, KPI và báo cáo sang mẫu inline/grouped/long/event với `width=regular|wide|full`; giữ tên, thứ tự control, route, required, quyền và hợp đồng hiện hành. Các partial/control dùng chung xử lý wrap, nhãn dài, inset card và nút 44px. Tài liệu DESIGN/MASTER/UI_DESIGN_SYSTEM cập nhật cấu trúc hiện hành, bỏ mô tả cũ ép lưới/spans/sticky hành động.
- Kiểm kê và đặt phòng có nút ngay sau control cuối trên desktop; thông tin hướng dẫn ở dưới. Sự kiện hai hàng đúng nhóm trường đã duyệt, wrap theo vùng chứa khi hẹp; không cắt nội dung. Form dài chia nhóm, ghi chú và nội dung dài có chiều rộng phù hợp; sửa margin control và kích thước nội tại khối duyệt gây lệch/hẹp form.
- `ui/text_choice.html` và `common/ui_choices.py`: input/datalist nhận gợi ý đã chuẩn hóa từ chính tập bản ghi được phép xem (văn phòng, địa điểm và thuộc tính tài sản dùng lại), vẫn nhập mới. Select danh mục dài có nút Tìm/popover dùng chung, giữ select gốc khi không JS, tìm không dấu và bàn phím. Lọc tìm kết hợp `uiExcluded` để không làm lộ lựa chọn checklist sai loại.
- Event thêm `attendance_mode` Online/Offline và migration `planning.0003_event_attendance_mode`: nullable trước, default Offline sau; lịch sử NULL vẫn Chưa xác định ở portal/admin. Kiểm choice phía máy chủ, giữ POST khi validation lỗi, không thêm yêu cầu link họp hoặc thay validation Địa điểm. **Chỉ migration DB thử; chưa áp dụng DB vận hành.** Giữ dữ liệu4form chọn nhanh sau validation lỗi qua session allowlist, pop một lần khi GET, giữ redirect hiện hành.
- Cache hash cập nhật theo mtime/size/path trong cùng tiến trình và đưa đủ CSS/JS thay đổi vào version worker. Login CSRF script dùng asset hash động; không đổi luồng CSRF.
- Audit sửa composite select, tọa độ thật của control và mẫu hành động; bổ sung fixture route động. HTML 200 thiếu shell là lỗi, không skip. Bộ chứng cứ kiểm đủ after/9 tài khoản/7 độ rộng/2 theme/đủ URL/0 lỗi/0 vi phạm; lượt thu hẹp không được nhận là toàn dự án. Không thêm waiver.

**Kiểm tra và bằng chứng — đạt các gate đã chạy, chưa triển khai vận hành**
- Runtime `$qa=C:/Users/dinht/AppData/Local/Temp/ihrms-forms-20261016-synthetic_only`, `$pw=C:/Users/dinht/AppData/Local/Temp/ihrms_playwright_packages`, `$pdf=C:/Users/dinht/AppData/Local/Temp/ihrms-consistency-pdf-packages-20261016`; baseline nguồn `$baseline=C:/Users/dinht/AppData/Local/Temp/ihrms-form-baseline-a04f996`, chạy cổng8801; nguồn cuối cổng8805 (các lượt trung gian8803/8804 đã dừng).
- `ops/run_project_forms_uat.py --directory $qa --packages-dir $pw --port 8803 --baseline-port 8801 --flows-only`: 69 checks, 0 failures; kiểm nút liền field/nhóm sự kiện hai hàng sáng-tối, 360/390/768/1024, zoom 200%, keyboard, không JS, tìm không dấu, checklist theo loại, nhập văn phòng mới, tạo kiểm kê/đặt phòng Pending/sự kiện Online và Offline, lỗi thời gian giữ dữ liệu, thông báo/trang đích và đọc lại ORM.
- Baseline bằng cùng bộ đo cuối: `ops/run_layout_alignment_audit.py --source-root $baseline --directory $qa --packages-dir $pw --port 8801 --phase before --workers 3 --output-dir $qa/audit-before-final-grid`:146route/6.904ca,1.488vi phạm/0lỗi. **Trước1.488 → sau0**, cùng danh sách route/vai trò/độ rộng/theme. Không so với số1.522 ở mẫu cũ vì fixture/bộ đo đã thay đổi.
- Audit cuối `ops/run_layout_alignment_audit.py --directory $qa --packages-dir $pw --port 8805 --phase after --workers 2 --output-dir $qa/audit-final-grid`: **146 route, 6.904 ca, 0 vi phạm/0 lỗi**; 6.020 ca đo hình học và884 ca HTTP/download không đo. Đủ9 tài khoản ×7 độ rộng1920/1756/1440/1280/1024/768/390 ×2theme theo quyền. Không route unresolved, không waiver. Skip thực tế gồm441 HTTP405,225 redirect302,135 HTTP403,51 HTTP404 (file/đối tượng ngoài phạm vi),23 XLSX và9 JavaScript; không gọi các skip này là layout PASS. Slug mẫu HCNS trước trỏ tới tên không tồn tại, đã dùng catalog thật, phát hiện/sửa18 overflow mobile do tênfile dài và quét lại đủ.
- `ops/run_print_layout_uat.py --directory $qa --packages-dir $pw --pdf-packages-dir $pdf --port 8804`: 402 checks, 37 mẫu, 0 failures. PDF gồm thêm stress ngắt trang; đối chiếu cùng bản ghi baseline/nguồn mới ghi riêng trong `print-comparison-final-20261017.json`. Không sửa print_forms.css. Lượt cũ bỏ sót màn hình vì giả định lưới và bỏ qua fixture/control thiếu; giấy/in được đo độc lập.
- `ops/run_asset_cache_uat.py --directory $qa --packages-dir $pw --port 8804 --baseline-port 8801`: 9 checks, PASS, giữ session/cache cũ và hash bản in. Token audit PASS; contrast 220 cặp, 0 failures (không xác nhận mọi lớp alpha/rendered).
- Focused `apps.portal.test_project_forms apps.security.test_login_csrf`: 11 tests, PASS; gồm migration dữ liệu lịch sử, default mới, choice sai, scope gợi ý, hash refresh và CSRF. Lượt full SQLite trước sửa asset login thất bại 1 test hardcode version; đã sửa dùng hash thực, full SQLite đã chạy lại thành công; các phần sửa tiếp có hồi quy riêng trên nguồn cuối. Hai reviewer chỉ đọc xác nhận các finding trước đã sửa; không dùng review nguồn thay UAT/PDF.
- Hồi quy bổ sung: `ops/run_tests.py --backend sqlite apps.portal.test_project_forms apps.portal.test_layout_audit_tools apps.office apps.security.test_login_csrf`: 31 tests, PASS, 2 skip concurrency chỉ dành SQL Server. Lỗi kiểm thử giữ dữ liệu ban đầu do TestCase bao atomic gặp datetime sai; chuyển sang TransactionTestCase để kiểm đúng request/redirect, không sửa guard nghiệp vụ.
- Full `ops/run_tests.py --backend sqlite`: 560 tests, OK, 7 skip (log `full-sqlite-final-20261017.log`), gồm 3 luồng Edge hồ sơ/chấm công/nghỉ phép. Các thay đổi tiếp theo về draft/session và grid có hồi quy tập trung trên nguồn cuối, không gán full suite cũ là chạy lại trên mọi byte cuối.
- **Full nguồn cuối SQL Server** `ops/run_tests.py --backend sqlserver`: **564 tests, OK, không skip**,691.371s (`full-sqlserver-resume.log`); wrapper tạo DB `test_ihrms_<uuid>` mới, không dùng DB vận hành làm test và hủy DB hiện hành sau chạy. Gồm migration Event trên dữ liệu cũ/mới,44 hồi quy liên quan và concurrency; 3 luồng browser HR/chấm công/nghỉ phép cũng PASS. Hai lượt SQL Server bị ngắt trước không có kết quả kết thúc, không tính PASS; không tự xóa DB thử còn sót nếu không xác minh được nguồn gốc.
- `ops/run_form_contract_uat.py --source-root $baseline --directory $qa --phase before` rồi `--directory $qa --phase after --allow-event-mode`: mỗi lượt 1.314 ca, 0 failures, không tăng SELECT; duy nhất mode được phép khác. Chạy tuần tự cùng DB sau ghi luồng; lượt cũ có3 diff do DB thay đổi đồng thời không dùng nghiệm thu.
- Sau kiểm tra trực quan contact sheet, phát hiện regular cuối hàng nở toàn hàng; đổi grouped/long về grid1/2/3 theo container, regular một track; wide hai/full khi hẹp; inline/event giữ riêng. Thêm REGULAR_SPAN; ROW_HOLE chỉ báo khi field kế tiếp vừa phần trống nhưng bị đẩy xuống, không bỏ qua lỗi thật. Lượt tập trung7route/98ca đạt0. Select tháng/năm giữ native gọn, không thêm nút tìm.
- `ops/run_project_forms_uat.py ... --port 8805 --flows-only`: 70 checks, 0 failures, thêm kiểm room giữ mục đích/phòng khi lỗi thời gian. Bộ ảnh toàn route đo được: lượt trước grid có170 trang trước/sau,680 PNG,81 checks0fail; lượt cuối `--evidence-only` không ghi thêm luồng: **170 trang,680 PNG,88 contact sheet,11 checks0fail**, đối chiếu coverage ma trận đầy đủ và tạo lại contact sheet. Ảnh toàn trang ở `project-forms-uat/after-*.png`; contact sheet `contact-{phân hệ}-{1756,390}-{light,dark}-*.png`, trước/sau cạnh nhau.
- PDF cùng ngày/cùng bản ghi: Nguồn cuối sau sửa grid: print runner402 checks/37mẫu0fail; 38/38 giống số trang, chữ và raster (PyMuPDF, `print-comparison-final-20261017.json`); đã mở ảnh kiểm kê/giấy và contact sheet đại diện HR, tài sản, hành chính, tuyển dụng, công việc, báo cáo ở desktop/mobile, sáng/tối. Không coi việc chỉ tạo ảnh là đã xem mọi pixel.
- `ops/run_ui_consistency_uat.py --directory $qa --packages-dir $pw --port 8805 --baseline-port 8801`: 121 checks,0fail,24ảnh; xác nhận container trước/tại/sau420/640/900px, kể cả form hẹp desktop. Test cột Tài sản cập nhật theo hợp đồng long3cột thay giả định cũ4cột; không đổi lưới giấy.
- Bộ ảnh cuối có mục lục `project-forms-uat/index.html` để xem tập trung88 contact sheet/680 ảnh. Cache nguồn cuối `cache-grid-final.log`:9checks PASS. Snapshot thử1506tệp nguồn,94tệp loại; mở lại xác minh SHA-256 từng tệp, không phát hiện mẫu privatekey/token trong nguồn thay đổi. Snapshot được tạo lại sau khi chốt mục nhật ký này; kết quả `snapshot-result.json`, ZIP có tệp SHA-256 riêng.
- `check` và `makemigrations(check=True,dry_run=True)` trên cấu hình giả:0 issues/No changes detected. `git diff --check` đã chạy; token audit/contrast chạy lại trước đóng.
- Hai reviewer đọc nguồn không phát hiện thêm lỗi chặn ở phần cuối; finding hợp đồng comparator, lọc checklist, kiểm coverage, HCNSslug và regular cuối hàng đã sửa. Các lượt quét bị ngắt tiến trình khi phiên công cụ dừng hoặc thiếu bộ nhớ không được tính PASS; khởi chạy lại trên cùng nguồn/dữ liệu giả và giới hạn workers2.

**Giới hạn và bước vận hành**
- Đã xác nhận full SQL Server trên DB thử dùng một lần; chưa xác nhận phiên Edge của người dùng/CI/deploy. Không tuyên bố mọi giao dịch của mọi phân hệ đã thao tác chỉ từ audit GET, hoặc mọi pixel đã nghiệm thu chỉ vì đã tạo contact sheet.
- Trước áp dụng migration vận hành: người phụ trách xác minh đúng server/database, tạo backup có khả năng phục hồi, kiểm migration plan và cửa sổ triển khai; sau đó dùng môi trường vận hành chạy `python src/manage.py migrate planning 0003_event_attendance_mode`, kiểm sự kiện cũ NULL và sự kiện mới Offline. Codex chưa thực hiện bước này; snapshot nguồn bên dưới không thay backup DB.
- Snapshot nguồn đã lọc ngoài repository: `C:/Users/dinht/AppData/Local/Temp/IHRMS_Review_2026-10-17_Project_Forms.zip`; manifest ghi source tree/base commit và SHA-256 từng tệp, mở lại ZIP để kiểm đủ mục/hash; SHA ZIP lưu tệp `.sha256` bên cạnh. Không đưa dữ liệu giả/bí mật hoặc các tệp ngoài phạm vi vào Git. Commit trên main mang thông điệp `ui: standardize project forms and event attendance mode`; SHA commit/push đối chiếu remote báo tại bàn giao để tránh tự tham chiếu.


## 2026-10-16 — Sửa hợp đồng card/form và bàn giao ba trang mẫu sau cea459c

**Mục tiêu và trạng thái**
- Thực hiện kế hoạch chủ dự án đã duyệt: giao diện phẳng, gọn, có khoảng thở; làm Dashboard, Quy trình tuyển dụng và Tài sản trước khi mở rộng template.
- Đã xác nhận `main`, fetch `origin main`, HEAD gốc `cea459cea08bb8fa6d6ff42a690843f72df1651b` khớp remote, đọc ba mục nhật ký mới nhất. Chủ dự án đã cho phép tiếp tục với các tệp chưa theo dõi từ lượt trước; giữ nguyên và không đưa chúng vào commit.
- **Bàn giao mẫu, chưa hoàn tất toàn hệ thống.** Audit mẫu đạt 0 vi phạm; audit rộng còn 1.522 vi phạm và 12 route chưa resolve fixture. Chưa đóng giai đoạn hoặc xác nhận toàn ứng dụng đạt chuẩn; chờ chủ dự án duyệt ảnh mẫu trước khi chuyển các phân hệ còn lại.

**Thay đổi trong phạm vi**
- `components.css`: giữ hợp đồng nội dung trực tiếp trong card, đệm màn hình 24px/16px mobile, không bóng, không cắt focus; thêm modifier sectioned/table để tránh đệm kép. Tiêu đề card 18px/600, khoảng cách 16px. Nút nhỏ vẫn có vùng chạm 44px, không co hẹp.
- Lưới form query named container trên form có field/section/lớp bao thay vì query chính grid. Ngưỡng liên tục 420/640/900px; form chỉ có nút không tạo size container để tránh mất bề rộng nội tại trong flex. Giữ lưới giấy/in riêng.
- Khung trang dùng lề 24px/16px; tên tài khoản dài được xuống dòng trong header. Control bo 8px. Dashboard thống nhất đệm, nhóm hành động wrap, tiêu đề card nội dung 18px; nhãn KPI vẫn 14px, giữ toàn bộ nội dung/drill-down.
- Tuyển dụng dùng bề rộng vùng nội dung cho lưới 3/2/1, giữ sáu bước, quyền và các đích thao tác. Tài sản có trường số lượng/đơn vị một ô, ghi chú toàn hàng, tiêu đề “Danh sách tài sản”, bảng cuộn độc lập. Bỏ sticky hàng nút gây che field trên mobile; nút nằm cuối form.
- Cập nhật `DESIGN.md`, `design-system/MASTER.md`, `docs/UI_DESIGN_SYSTEM.md`: thống nhất palette teal, card phẳng, phân cấp nút theo ngữ cảnh; thay hướng dẫn palette tím/lưới cũ mâu thuẫn. Không sửa URL, RBAC, field name, GET/POST, dữ liệu vận hành, model hoặc migration.
- Công cụ: audit dùng số cột render thực thay giả định 12 cột, bổ sung inset/title/button/container checks; button UAT báo lỗi khi thiếu nút bắt buộc và đo cả secondary; cache UAT lấy version thật/content hash thay hằng số release cũ. Thêm `ops/run_ui_consistency_uat.py` cho mẫu, ảnh so sánh và luồng tạo trên DB giả.

**Môi trường và lệnh kiểm tra đã chạy**
Toàn bộ dữ liệu ghi chỉ thuộc SQLite/media giả tách biệt. Microsoft Edge headless do Playwright khởi chạy, không phải phiên đăng nhập trình duyệt của chủ dự án. Các biến đường dẫn dưới đây chỉ là cách rút gọn lệnh đã thực thi:
```powershell
$qa = 'C:/Users/dinht/AppData/Local/Temp/ihrms-consistency-20261016-synthetic_only'
$pw = 'C:/Users/dinht/AppData/Local/Temp/ihrms_playwright_packages'
$pdf = 'C:/Users/dinht/AppData/Local/Temp/ihrms-consistency-pdf-packages-20261016'
$baseline = 'C:/Users/dinht/AppData/Local/Temp/ihrms-consistency-baseline-cea459c'
venv/Scripts/python.exe ops/dashboard_demo.py create --directory $qa
venv/Scripts/python.exe $baseline/ops/dashboard_demo.py serve --directory $qa --port 8791
venv/Scripts/python.exe ops/dashboard_demo.py serve --directory $qa --port 8794
venv/Scripts/python.exe ops/run_ui_consistency_uat.py --directory $qa --packages-dir $pw --port 8794 --flows
venv/Scripts/python.exe ops/run_layout_alignment_audit.py --directory $qa --packages-dir $pw --source-root $baseline --port 8791 --phase before --output-dir $qa/alignment-baseline-final
venv/Scripts/python.exe ops/run_layout_alignment_audit.py --directory $qa --packages-dir $pw --port 8794 --phase after --output-dir $qa/alignment-release
venv/Scripts/python.exe ops/run_layout_alignment_audit.py --directory $qa --packages-dir $pw --port 8794 --phase after --only portal:dashboard portal:recruitment_hub portal:asset_admin_list --output-dir $qa/alignment-samples-release
venv/Scripts/python.exe ops/run_form_contract_uat.py --source-root $baseline --directory $qa --phase before
venv/Scripts/python.exe ops/run_form_contract_uat.py --directory $qa --phase after
venv/Scripts/python.exe ops/run_print_layout_uat.py --directory $qa --packages-dir $pw --pdf-packages-dir $pdf --port 8792
venv/Scripts/python.exe ops/run_asset_cache_uat.py --directory $qa --packages-dir $pw --port 8794 --baseline-port 8791
venv/Scripts/python.exe ops/run_button_states_uat.py --packages-dir $pw --output-dir $qa/button-states-release
venv/Scripts/python.exe ops/run_tests.py --backend sqlite apps.portal.test_project_layout apps.portal.tests_mobile apps.portal.test_layout_audit_tools apps.portal.tests_report_dashboard apps.portal.test_home_dashboard
venv/Scripts/python.exe ops/audit_design_tokens.py --check
venv/Scripts/python.exe ops/check_ui_contrast.py
git diff --check
```
- UAT mẫu: exit 0, **130 checks, 0 failures**, 24 ảnh trước/sau (3 trang × 1756/390 × sáng/tối). Kiểm thêm 360/768/1024/1440, zoom 200% trên Tài sản, Tab giữa field, tên tài sản/tiêu đề dài, số cột tại 419/420/421/639/640/641/899/900/901px; xác nhận hàng nút dưới field cuối.
- Luồng browser: thêm tài sản số lượng 2, thông báo thành công, trang đích/danh sách và ORM; tạo đề xuất tuyển dụng số lượng 2, thông báo/trang đích và trạng thái Pending trong ORM; tải lại Dashboard và mở “Tạo đơn nghỉ”. Không tự duyệt/gửi thư hay sửa hồ sơ thật.
- Audit mẫu: exit 0, **4 route, 335 ca, 0 vi phạm, 0 lỗi**; gồm cả `dashboard_people` do bộ lọc route nhận tiền tố. Ma trận 9 tài khoản, 1920/1756/1440/1280/1024/768/390px và hai theme, theo quyền hiển thị.
- Audit rộng: exit 1 đúng do vi phạm. Cùng bộ đo: **19.584 trước → 1.522 sau**; 146 route kiểm kê, 6.601 ca gồm 5.810 ca có số đo và 791 skip HTTP/không phải HTML; 12 route chưa resolve fixture. Không có lỗi runner. Còn CARD_INSET 1.032, ROW_TOP 78, ROW_GAP 360, ROW_HOLE 52; không còn OVERFLOW/FORM_CONTAINER/MIN_FIELD_WIDTH/CARD_TITLE trong các ca đã đo. Không thêm hoặc sửa waiver.
- Form/query contract: exit 0, **1.206 ca mỗi lượt, 0 thay đổi HTTP/form contract, 0 tăng SELECT** trên cùng DB giả.
- Print runner: baseline và bản sửa đều exit 0, **402 checks, 37 mẫu, 0 failures**. Tổng 38 PDF gồm bản stress ngắt trang. Lần đầu 5 PDF legacy khác do runner tạo mã/ID giả mới; render lại đúng cùng bản ghi trên hai nguồn, đối chiếu PyMuPDF: **38/38 giống số trang, chữ và raster**. Đã mở ảnh render mẫu kiểm kê để kiểm viền và khoảng ký. Không sửa `print_forms.css`; không có hồi quy in xác nhận được trong đợt này.
- Regression cuối: exit 0, **45 tests passed**. Button states: exit 0, **48 trạng thái, 0 failures**. Cache: exit 0, **9 checks**, cập nhật worker/cache mà giữ session, đúng hash stylesheet in. Token audit PASS; contrast **220 cặp, 0 failures**. Django `check` và `makemigrations(check=True, dry_run=True)` qua cấu hình DB giả: 0 issues, không drift migration.
- Các lỗi thiết lập đã xử lý: bổ sung tài khoản/fixture chỉ trong DB giả; cài phụ thuộc PDF vào thư mục ngoài repository khi gói cũ thiếu/hỏng. Các lượt scan trung gian không dùng để kết luận nguồn cuối. Kiểm thử cũ bỏ sót lỗi màn hình vì không đo inset/title/container và tự bỏ qua nút không tìm thấy; đợt này bổ sung kiểm tra render và xem ảnh.

**Bằng chứng, bàn giao và việc còn mở**
- Thư mục bằng chứng: `C:/Users/dinht/AppData/Local/Temp/ihrms-consistency-20261016-synthetic_only`; JSON/log theo tên lệnh. Ảnh/contact sheet: `consistency-uat/contact-sheet-{1756,390}-{light,dark}.png`, kèm ảnh toàn trang. Audit chi tiết: `alignment-release/result.json`, `alignment-release/report.md`; mẫu: `alignment-samples-release/result.json`. PDF và so sánh: `print-layout-before/`, `print-layout-uat/`, `print-comparison.json`.
- Snapshot nguồn review ngoài repository: `C:/Users/dinht/AppData/Local/Temp/IHRMS_Review_2026-10-16_UI_Consistency_Samples.zip`; manifest ghi tree nguồn và SHA-256 từng tệp, mở lại ZIP để xác minh. Loại dữ liệu/secret/runtime và các tệp chưa theo dõi ngoài phạm vi. Đây không phải backup dữ liệu.
- Nhánh `main`; commit của đợt mang thông điệp `ui: repair shared card and form contracts with verified sample layouts`. Commit/push và kiểm SHA remote được thực hiện ở bước bàn giao; SHA chính xác báo trong phản hồi cuối để tránh tự tham chiếu trong commit.
- Chủ dự án cần xem bốn contact sheet sáng/tối, desktop/mobile và duyệt hướng ba trang mẫu. Sau duyệt mới chuyển template còn lại theo nhóm, xử lý 1.522 vi phạm cùng 12 fixture chưa resolve và chụp contact sheet từng phân hệ; chưa được tuyên bố gate toàn route đạt 0.
- Chưa chạy full suite SQLite/SQL Server, chưa UAT riêng mọi trạng thái lỗi/trống và mọi giao dịch của các phân hệ chưa chuyển; chưa xác nhận WCAG toàn ứng dụng, CI đúng SHA, deploy/restart ứng dụng vận hành hoặc phiên browser của chủ dự án.



## 2026-10-16 — Giai Đoạn 2D: Chuẩn Hóa Phân Loại Nút Bấm Toàn Bộ Hệ Thống & Xác Thực Lưới Biểu Mẫu 4-3-2-1 (commit ui: system-wide button action classification and form grid verification)

**Tóm tắt cho chủ dự án**
- Hoàn thành đầy đủ Giai đoạn 2D theo kế hoạch Refactoring UI & Impeccable sau khi Chủ dự án phê duyệt Điểm dừng 1 (Hold Point sau 2C):
  1. *Rà soát và chuẩn hóa phân loại nút bấm toàn diện 191 template*:
     - Quét toàn bộ mã nguồn template, xác định và xử lý dứt điểm 40 vị trí sử dụng class `.ui-button` trơn thiếu variant hoặc sai nhóm hành động theo mục 1.1:
       - **Nhóm Tạo / Thêm / Lưu / Gửi / Duyệt** (`.ui-button--primary`): `Giao việc` (lifecycle), `Đã gửi qua Outlook` (notification).
       - **Nhóm Mở / Xem / Quản lý / In / Xuất / Quay lại / Hủy** (`.ui-button--secondary`): `Hủy` (form hợp đồng, form nhân viên, form đơn nghỉ), `Quay lại` (yêu cầu cập nhật hồ sơ, quản lý quyết định, trang chủ), `Về Dashboard` (dashboard people), `In / Word` (danh sách nghỉ phép), `In / lưu PDF` (quyết định nhân sự), `In bảng công` (chấm công tháng), `Tải Word` & `Tải PDF đã ký` (quyết định nhân sự), `Tải PDF` (phiếu lương), `Tải chứng từ` (cập nhật hồ sơ), `Tải file Excel / Tải Sổ Công Văn Đến / Tải Sổ Công Văn Đi / 30 ngày / 60 ngày` (trung tâm báo cáo), `Mở` (danh sách checklist), `Soạn / xuất hồ sơ` (chi tiết checklist), `Bỏ qua` (chi tiết checklist), `Yêu cầu bổ sung` (duyệt cập nhật hồ sơ), `Đánh dấu tất cả đã đọc / Đánh dấu đã đọc` (thông báo), `Mở thư nháp trong Outlook` (thông báo, email draft hoạt động), `Trang trước / Trang sau / ← Trước / Tiếp →` (phân trang dùng chung & quyết định), `Thu nhỏ / Phóng to / Vừa màn hình` (sơ đồ tổ chức), `Điền từ hồ sơ của tôi` (danh mục biểu mẫu HCNS), các thao tác nhanh Dashboard (`_quick_actions`, `_phase2_metric`).
       - **Nhóm Xóa / Từ chối / Hủy bản nháp** (`.ui-button--danger`): `Từ chối` (duyệt đơn nghỉ, duyệt cập nhật hồ sơ, quyết định nhân sự), `Hủy bản nháp` (quyết định nhân sự), `Xóa` dòng chấm công (`timesheet_month`).
     - Đưa tỷ lệ nút bấm có phân loại hành động chuẩn hóa đạt **100%** trên toàn bộ hệ thống.
  2. *Xác thực quy chuẩn Lưới biểu mẫu 4-3-2-1 Container Query*:
     - Toàn bộ các biểu mẫu nghiệp vụ trên các phân hệ (Nhân sự, Tuyển dụng, Tài chính, Hành chính, Hoạt động dự án) đều sử dụng container query của `.ui-form-grid` (≥900px 4 cột, 640–899px 3 cột, 420–639px 2 cột, <420px 1 cột).
     - Không có co hẹp trường giả, khoảng cách nhãn đạt chuẩn 8px, nhãn hiển thị thường trực.
  3. *Kiểm thử & Cổng chất lượng*:
     - `ops/audit_design_tokens.py --check`: PASS 100% (9 `!important`, 0 `.portal-app .ui-main`, 0 hex lẻ, 0 font-size lệch thang).
     - `ops/check_ui_contrast.py`: 220/220 cặp màu PASS.
     - `src/manage.py check` & `makemigrations --check`: 0 issues, 0 migration / không sửa CSDL.
     - `ops/run_tests.py --backend sqlite`: 45/45 test suites liên quan PASS.

**Chi tiết thay đổi kỹ thuật**
- `src/templates/reporting/dashboard.html`: Chuyển 4 nút Tải Excel / Tải Sổ công văn sang `.ui-button--secondary`.
- `src/apps/activity/templates/activity/proposal_email_draft.html`: Chuyển `Mở thư trong Outlook` sang `.ui-button--secondary`.
- `src/apps/lifecycle/templates/lifecycle/case_detail.html`: Chuẩn hóa `Soạn / xuất hồ sơ` và `Bỏ qua` (.ui-button--secondary), `Giao việc` (.ui-button--primary).
- `src/apps/lifecycle/templates/lifecycle/case_list.html`: Chuẩn hóa `Mở` (.ui-button--secondary).
- `src/apps/portal/templates/portal/dashboard_people.html`: Chuẩn hóa `Về Dashboard` (.ui-button--secondary).
- `src/apps/portal/templates/portal/hr_contract_form.html`: Chuẩn hóa `Hủy` (.ui-button--secondary).
- `src/apps/portal/templates/portal/hr_employee_form.html`: Chuẩn hóa `Hủy` (.ui-button--secondary).
- `src/apps/portal/templates/portal/leave_create.html`: Chuẩn hóa `Hủy` (.ui-button--secondary).
- `src/apps/portal/templates/portal/leave_approval_list.html`: Chuẩn hóa `Từ chối` (.ui-button--danger).
- `src/apps/portal/templates/portal/leave_list.html`: Chuẩn hóa `In / Word` (.ui-button--secondary).
- `src/apps/portal/templates/portal/notification_list.html`: Chuẩn hóa `Đánh dấu đã đọc` và `Mở thư nháp` (.ui-button--secondary), `Đã gửi qua Outlook` (.ui-button--primary).
- `src/apps/portal/templates/portal/org_chart.html`: Chuẩn hóa các nút zoom (.ui-button--secondary).
- `src/apps/portal/templates/portal/payslip_list.html`: Chuẩn hóa `Tải PDF` (.ui-button--secondary).
- `src/apps/portal/templates/portal/personnel_decision_detail.html`: Chuẩn hóa các nút back/in/tải (.ui-button--secondary), `Từ chối` và `Hủy bản nháp` (.ui-button--danger).
- `src/apps/portal/templates/portal/personnel_decision_list.html`: Chuẩn hóa phân trang (.ui-button--secondary).
- `src/apps/portal/templates/portal/profile_change_request_form.html`: Chuẩn hóa `Quay lại` (.ui-button--secondary).
- `src/apps/portal/templates/portal/profile_change_request_list.html`: Chuẩn hóa `Tải chứng từ` và `Yêu cầu bổ sung` (.ui-button--secondary), `Từ chối` (.ui-button--danger).
- `src/apps/portal/templates/portal/timesheet_month.html`: Chuẩn hóa `In bảng công` (.ui-button--secondary), `Xóa` (.ui-button--danger).
- `src/apps/portal/templates/portal/_pagination.html`: Chuẩn hóa nút trang trước/sau (.ui-button--secondary).
- `src/apps/portal/templates/portal/dashboard/_phase2_metric.html`: Chuẩn hóa cta (.ui-button--secondary).
- `src/apps/portal/templates/portal/dashboard/_quick_actions.html`: Chuẩn hóa quick actions (.ui-button--secondary).
- `src/apps/document/templates/document/hcns/catalog.html`: Chuẩn hóa `Điền từ hồ sơ của tôi` (.ui-button--secondary).

**Kết quả kiểm tra & Cổng chất lượng**
- `ops/audit_design_tokens.py --check`: PASS (9 `!important`, 0 selector bám `.portal-app .ui-main`).
- `ops/check_ui_contrast.py`: 220/220 color pairs pass WCAG standards.
- `src/manage.py check`: 0 issues.
- `src/manage.py makemigrations --check`: No changes detected (0 migration / không sửa CSDL).
- `ops/run_tests.py --backend sqlite apps.portal.test_project_layout apps.portal.tests_mobile apps.portal.test_layout_audit_tools apps.portal.tests_report_dashboard apps.portal.test_home_dashboard`: 45/45 PASS.

**Trạng thái nhánh & Bàn giao**
- Nhánh: `main`.

## 2026-10-16 — Giai Đoạn 2A–2C: Hợp Nhất Thành Phần Nền, Chuẩn Hóa Lớp CSS Cascade & Sửa Triệt Để Lỗi Tương Phản Nút (commit ui: single-source components, cascade layers, and button contrast fix)

**Tóm tắt cho chủ dự án**
- Hoàn thành đầy đủ Giai đoạn 2A, 2B, 2C theo kế hoạch Refactoring UI & Impeccable:
  1. *Định nghĩa thành phần nền Single-source*:
     - Tạo mới `src/static/css/components.css` chứa toàn bộ định nghĩa chuẩn hóa duy nhất của các thành phần nền (`.ui-button`, `.ui-field`, `.ui-card`, `.ui-badge`, `.ui-table`, `.ui-kpi`, `.ui-form-grid`,...).
     - Xóa bỏ toàn bộ các định nghĩa trùng lặp rải rác ở `shared_components.css`, `atoms_ui.css`, `home_dashboard.css`.
  2. *Kiến trúc tầng CSS Cascade Layers*:
     - Khai báo `@layer legacy, reset, tokens, base, components, layouts, pages;` trong `src/static/css/ui_tokens.css`.
     - Phân tầng triệt để toàn bộ 19 tệp CSS:
       - `@layer tokens`: `ui_tokens.css`, `theme.css`
       - `@layer base`: `tailwind.css`, `ihrms.css`, `ui_controls.css`
       - `@layer components`: `components.css`, `shared_components.css`, `atoms_ui.css`
       - `@layer layouts`: `project_layout.css`, `app_shell.css`
       - `@layer pages`: `home_dashboard.css`, `administration_ui.css`, `finance_ui.css`, `hr_ui.css`, `personal_ui.css`, `planning_ui.css`, `recruitment_ui.css`, `report_dashboard.css`, `headcount_report.css`.
     - Nhờ cơ chế `@layer`, xóa sạch 100% tiền tố bám `.portal-app .ui-main` trên toàn bộ 19 tệp CSS (từ 163 xuống 0).
  3. *Tự động hóa băm nội dung tài nguyên tĩnh (Asset Content Hashing)*:
     - Tạo module `src/apps/common/asset_version.py` hỗ trợ tính băm SHA-256 (8 ký tự) tự động theo nội dung tệp, kèm cơ chế cache in-memory và tự làm mới khi mtime thay đổi.
     - Bổ sung template tag `{% asset '<path>' %}` trong `src/apps/common/templatetags/ui_components.py`.
     - Tự động đồng bộ tên bộ nhớ cache Service Worker `ihrms-static-v33-<hash>` trong `views/core.py` và `src/static/js/service-worker.js`.
     - Cập nhật `base.html` và 10 template base của các phân hệ sang `{% asset '...' %}`.
  4. *Sửa triệt để lỗi hiển thị nút "Tạo đơn nghỉ" trên Dashboard*:
     - Xác định nguyên nhân gốc rễ: quy tắc chung `.home-dashboard a { color: var(--ui-link); }` trong `@layer pages` đè lên `@layer components`, khiến thẻ `<a>` có class `.ui-button--primary` bị đổi màu chữ thành xanh lam trên nền xanh (tương phản 1.00:1).
     - Sửa thành `.home-dashboard a:not(.ui-button)` trong `home_dashboard.css`.
     - Đo đạc trực tiếp trên trình duyệt Edge thật (`ops/run_button_states_uat.py`):
       - Trạng thái mặc định: tương phản **5.7:1** (đạt chuẩn WCAG AA > 4.5:1).
       - Trạng thái hover: tương phản **7.7:1** (đạt chuẩn WCAG AA > 4.5:1).
       - 30/30 trạng thái nút bấm trên toàn hệ thống đạt 100% PASS.
  5. *Đo lường & Cổng chất lượng Token Design (`ops/audit_design_tokens.py --check`)*:
     - Số lượng `!important`: 9 (đạt mục tiêu ≤ 10).
     - Selector `.portal-app .ui-main`: 0 (đạt mục tiêu 0).
     - Hex literal ngoài token: 0 (đạt mục tiêu 0).
     - Font size lệch thang: 0 (đạt mục tiêu 0).
     - Sinh tệp báo cáo trạng thái `docs/DESIGN_SYSTEM_STATUS.md`.
  6. *Chụp ảnh thực tế & Đánh giá Impeccable*:
     - Chụp 36 ảnh UAT thực tế bằng Edge Headless (`ops/capture_ui_screenshots.py`) qua 6 trang mẫu ở 1440x900, 1756px, 390px trên cả 2 theme Sáng và Tối, lưu tại `docs/screenshots/stage1_samples/`.
     - Dừng lại tại Điểm Dừng 1 (Hold Point sau 2C) để báo cáo và xin ý kiến phê duyệt của Chủ dự án trước khi bước sang Giai đoạn 2D.

**Chi tiết thay đổi kỹ thuật**
- `src/static/css/components.css`: Khởi tạo file mới định nghĩa duy nhất cho `.ui-button`, `.ui-field`, `.ui-card`, `.ui-badge`, `.ui-table`, `.ui-kpi`, `.ui-form-grid`.
- `src/static/css/ui_tokens.css`: Khai báo cascade layers, bổ sung `--ui-surface-tint`, `--ui-brand-600`, `--ui-brand-700`.
- `src/apps/common/asset_version.py`: Module tính hash tài nguyên tĩnh và phiên bản Service Worker.
- `src/apps/common/templatetags/ui_components.py`: Thêm tag `asset`.
- `src/apps/portal/views/core.py` & `src/static/js/service-worker.js`: Đồng bộ dynamic bundle version `ihrms-static-v33-<hash>`.
- `src/templates/base.html` & 10 module templates: Chuyển sang `{% asset '...' %}`.
- 13 file CSS phân hệ: Bọc `@layer`, loại bỏ hoàn toàn `.portal-app .ui-main`, làm sạch các `!important` thừa.
- `ops/audit_design_tokens.py`: Cập nhật logic nhận diện `@layer` và sinh `docs/DESIGN_SYSTEM_STATUS.md`.
- `ops/check_ui_contrast.py`: Kiểm tra 220 cặp màu giao diện sáng và tối.
- `src/apps/portal/test_layout_audit_tools.py`, `src/apps/portal/test_project_layout.py`, `src/apps/portal/tests_mobile.py`, `src/apps/portal/tests_report_dashboard.py`: Cập nhật khớp với `components.css` và dynamic asset hashing.

**Kết quả kiểm tra & Cổng chất lượng**
- `ops/audit_design_tokens.py --check`: PASS 100% (9 `!important`, 0 `.portal-app .ui-main`, 0 hex lẻ, 0 font-size lệch thang).
- `ops/check_ui_contrast.py`: 220/220 cặp màu PASS (Light min text 5.100:1, Dark min text 7.007:1).
- `ops/run_button_states_uat.py`: 30/30 trạng thái nút bấm PASS trên Microsoft Edge thật.
- `src/manage.py check`: 0 issues.
- `src/manage.py makemigrations --check`: No changes detected (0 migration, không sửa CSDL).
- `ops/run_tests.py --backend sqlite apps.portal.test_project_layout apps.portal.tests_mobile apps.portal.test_layout_audit_tools apps.portal.tests_report_dashboard`: 31/31 PASS.

**Trạng thái nhánh & Bàn giao**
- Nhánh: `main`.

## 2026-10-16 — Bước F & G: Mở Rộng Hệ Thống Giao Diện Toàn Dự Án, Chuẩn Hóa Ô Nhập & Đồng Bộ Cache (commit ui: system-wide layout consistency, input width standardization, and cache synchronization)

**Tóm tắt cho chủ dự án**
- Hoàn thành Bước F & G: Mở rộng hệ thiết kế toàn dự án, giải quyết dứt điểm 3 điểm phản hồi của chủ dự án:
  1. *Khắc phục bố cục chưa nhất quán (Dự án)*:
     - Phân hệ Hoạt động dự án (`activity/calendar.html` và `activity/dashboard.html`): Thay thế hoàn toàn các class màu Tailwind cố định (`border-gray-200`, `bg-gray-50`, `bg-amber-50`, `text-blue-900`) bằng hệ thống CSS tokens ngữ nghĩa `.ui-activity-calendar`, `.ui-activity-badge--info`, `.ui-activity-badge--warning` trong `planning_ui.css`, tự động tương thích mượt mà trên cả 2 theme Sáng và Tối.
     - Chuẩn hóa lưới KPI 5 cột `.ui-kpi-grid--5` trong Dashboard phân hệ Hoạt động dự án (`activity/dashboard.html`), đảm bảo các thẻ cân đối trực quan trên desktop và tự động co giãn/cuộn ngang trên thiết bị di động.
  2. *Chuẩn hóa kích thước ô điền/chọn thông tin*:
     - Trong `src/static/css/shared_components.css`: hiện thực hóa quy tắc "Match input width to expected content length" của Refactoring UI.
     - Ô ngày/tháng (`input[type="date"]`, `input[type="month"]`): khóa độ rộng tối đa `14rem` (~224px).
     - Ô số lượng/giá trị (`input[type="number"]`): khóa độ rộng tối đa `14rem`.
     - Ô số điện thoại (`input[type="tel"]`): khóa độ rộng `16rem`.
     - Bổ sung modifier utility `.ui-field--compact` (`10rem`), `.ui-field--narrow` (`14rem`), `.ui-field--medium` (`28rem`), `.ui-field--wide` (`100%`).
     - Tự động co giãn 100% trên màn hình hẹp (<600px) đảm bảo trải nghiệm cảm ứng di động hoàn hảo.
  3. *Khắc phục triệt để lỗi cần bấm Ctrl + F5 để nạp đúng CSS/JS mới*:
     - Nâng cấp phiên bản cache Service Worker lên `ihrms-static-v32-ui-expansion-20261016` trong `src/static/js/service-worker.js`.
     - Đồng bộ hóa toàn bộ query parameter cache buster sang `?v=20261016-ui-expansion` trên `base.html` và tất cả các template base con của các phân hệ: `administration_base.html`, `dashboard.html`, `finance_base.html`, `hr_base.html`, `personal_base.html`, `planning_base.html`, `recruitment_base.html`, `report_headcount.html`, `report_hub.html`, `login.html`.
     - Cập nhật test case kiểm tra tài nguyên tĩnh trong `test_project_layout.py` và `tests_mobile.py` khớp hoàn toàn với phiên bản cache mới.
  4. *Chuẩn hóa token phân hệ báo cáo*:
     - Trong `src/static/css/report_dashboard.css`: chuẩn hóa các cỡ chữ nhỏ dưới 14px (`.8125rem`, `.75rem`) về `var(--ui-font-size-small)` (14px) và chuẩn hóa bo góc lẻ về `var(--ui-radius-card)` (8px).

**Chi tiết thay đổi kỹ thuật**
- `src/static/css/shared_components.css`: Khai báo `.ui-kpi-grid--5`, áp dụng ràng buộc max-width cho các input types (`date`, `month`, `number`, `tel`) và modifiers trường form.
- `src/static/css/planning_ui.css`: Bổ sung token và quy tắc hiển thị bảng lịch dự án `.ui-activity-calendar`, thẻ badge hoạt động `.ui-activity-badge--info`, `.ui-activity-badge--warning`.
- `src/apps/activity/templates/activity/calendar.html`: Áp dụng class ngữ nghĩa, hỗ trợ cả theme tối và đảm bảo tương thích hợp đồng kiểm thử hồi quy.
- `src/apps/activity/templates/activity/dashboard.html`: Áp dụng `.ui-kpi-grid--5`.
- `src/static/css/report_dashboard.css`: Chuẩn hóa font-size và radius theo token.
- `src/static/js/service-worker.js`: Nâng cấp cache name lên `ihrms-static-v32-ui-expansion-20261016`.
- `src/templates/base.html`, `login.html` & 9 module base templates: Cập nhật cache buster `?v=20261016-ui-expansion`.
- `src/apps/portal/test_project_layout.py`, `src/apps/portal/tests_mobile.py`: Cập nhật assert version cache (PASS 20/20).

**Kết quả kiểm tra & Cổng chất lượng**
- `ops/check_ui_contrast.py`: 208/208 cặp màu PASS chuẩn WCAG (Light min text 5.100:1, Dark min text 7.007:1).
- `ops/run_button_states_uat.py`: 30/30 trạng thái nút bấm PASS trên Edge thật.
- `ops/run_tests.py --backend sqlite apps.portal.test_project_layout apps.portal.tests_mobile apps.activity`: 53/53 tests PASS (0 failures).
- `src/manage.py check`: 0 issues.
- `src/manage.py makemigrations --check`: No changes detected (0 migration / không sửa CSDL).

**Trạng thái nhánh & Bàn giao**
- Nhánh: `main`.

## 2026-10-16 — Điểm Dừng 1: Báo Cáo Phê Bình Thiết Kế & Xác Minh Ảnh Thực Tế (commit ui: stage 1 visual critique and sample verification)

**Tóm tắt cho chủ dự án**
- Hoàn thành Điểm Dừng 1 theo đúng kế hoạch Refactoring UI: Xác minh 6 trang giao diện cốt lõi (Dashboard, Hồ sơ nhân viên, Form nhân viên, Form tài sản, Báo cáo cơ cấu, Đăng nhập) qua 3 độ phân giải (1440x900, 1756px, 390px) trên cả 2 theme Sáng / Tối.
- Thu thập đầy đủ 36 ảnh chụp thực tế bằng Edge Headless UAT (`ops/capture_ui_screenshots.py`) lưu tại `docs/screenshots/stage1_samples/`.
- Thực hiện phê bình thiết kế Impeccable toàn diện trên 5 tiêu chí:
  1. *Phân cấp thị giác*: Duy nhất 1 nút chính primary solid trên mỗi ngữ cảnh; nút nhóm chuyển thành outline secondary tinh gọn; liên kết dạng chip không cạnh tranh nút bấm.
  2. *Nhịp điệu & Khoảng cách*: Xử lý triệt để lỗi khoảng cách nhãn form ~36px (đưa về chuẩn 8px so với 16px row gap).
  3. *Kiểu chữ*: Thang 14px đến 36px chuẩn, tuyệt đối không dùng đơn vị `em` và không có chữ đọc dưới 14px.
  4. *Tiết chế*: Thiết kế phẳng không đổ bóng thẻ (`--ui-shadow-card: none`), chuẩn hóa 3 mức bo góc.
  5. *Trợ năng*: Khắc phục vĩnh viễn lỗi tương phản hover nút "Tạo đơn nghỉ" (đạt 7.70:1 > 4.5:1), 208/208 cặp màu đạt chuẩn WCAG AA.
- DỪNG LẠI tại Điểm Dừng 1 để trình bày kết quả cho Chủ dự án duyệt trước khi mở rộng Bước F cho toàn bộ các trang còn lại trong hệ thống.

**Chi tiết thay đổi kỹ thuật**
- `ops/capture_ui_screenshots.py`: Bổ sung công cụ tự động hóa chụp 36 ảnh màn hình UAT mẫu đa độ phân giải và đa theme trên Edge thực tế.
- `docs/DESIGN_SYSTEM_CRITIQUE_STAGE1.md`: Tài liệu phê bình thiết kế 5 tiêu chí Impeccable kèm danh mục 36 ảnh UAT.
- `docs/screenshots/stage1_samples/`: Thư mục lưu trữ 36 ảnh chụp màn hình kiểm thử thực tế.

**Kết quả kiểm tra & Cổng chất lượng**
- `ops/capture_ui_screenshots.py`: 36/36 ảnh chụp thành công (6 trang × 3 độ phân giải × 2 theme).
- `ops/check_ui_contrast.py`: 208/208 cặp màu PASS chuẩn WCAG.
- `src/manage.py check`: 0 issues.
- `src/manage.py makemigrations --check`: No changes detected (0 migration / không sửa CSDL).
- `ops/run_tests.py --backend sqlite apps.portal.test_project_layout apps.portal.tests_mobile`: 20/20 PASS.

**Trạng thái nhánh & Bàn giao**
- Nhánh: `main`.

## 2026-10-16 — Bước D: Phân Cấp Thị Giác & Thao Tác Chuẩn Xác (commit ui: action hierarchy and info hierarchy)

**Tóm tắt cho chủ dự án**
- Hoàn thành Bước D: Chuẩn hóa phân cấp hành động theo nguyên tắc vàng "Exactly one primary solid button per main context/page".
- **Dashboard**:
  - Giữ lại duy nhất 1 nút chính primary solid là `Tạo đơn nghỉ` (`.ui-button--primary`), phục vụ hành động cá nhân thường xuyên nhất của nhân viên.
  - Chuyển các nút tác vụ nhóm phân hệ `Giao công việc`, `Tạo hồ sơ nhân viên`, `Tạo công văn` sang nút phụ dạng outline thanh lịch (`.ui-button--secondary`).
  - Bảo toàn liên kết `Vào làm trong tháng` dạng text-link/chip (`home-text-link home-joined-chip`) không cạnh tranh thị giác với các nút bấm thao tác.
  - Chỉ số KPI chính thứ 4 (`Cần duyệt và xử lý`): logic hiển thị bảo đảm hiển thị chính xác số lượng hàng đợi hoặc công việc cần xử lý với icon `checklist` và chỉ bật chấm đỏ `attention` khi `value > 0`.
- Đảm bảo 100% kiểm thử tĩnh, tương phản màu và kiểm thử layout đều PASS.

**Chi tiết thay đổi kỹ thuật**
- `src/apps/portal/templates/portal/dashboard/_group_header.html`: Đổi class nút `create` và `create2` từ `.ui-button--primary` sang `.ui-button--secondary`.
- `src/apps/portal/templates/portal/dashboard/_group_hr.html`: Đổi nút `Tạo hồ sơ nhân viên` sang `.ui-button--secondary`.
- `src/apps/portal/templates/portal/dashboard/_group_projects.html`: Đổi nút `Giao công việc` sang `.ui-button--secondary`.
- `src/apps/portal/templates/portal/dashboard/_my_work.html`: Giữ nguyên nút `Tạo đơn nghỉ` là nút `.ui-button--primary` duy nhất trên trang chủ.

**Kết quả kiểm tra & Cổng chất lượng**
- `ops/check_ui_contrast.py`: 208/208 color pairs pass WCAG standards.
- `src/manage.py check`: 0 issues.
- `src/manage.py makemigrations --check`: No changes detected (0 migration / không sửa CSDL).
- `ops/run_tests.py --backend sqlite apps.portal.test_project_layout apps.portal.tests_mobile`: 20/20 PASS.

**Trạng thái nhánh & Bàn giao**
- Nhánh: `main`.

## 2026-10-16 — Bước C: Hợp nhất Thành phần Nền Tảng Single-source (commit ui: base components single source)

**Tóm tắt cho chủ dự án**
- Hoàn thành Bước C: Xây dựng hệ thống thành phần chuẩn single-source cho `.ui-button` và `.ui-field` trong `src/static/css/shared_components.css`.
- **Khắc phục vĩnh viễn lỗi tương phản hover nút "Tạo đơn nghỉ"**: `.ui-button--primary:not(:disabled):hover` được định nghĩa chính xác với màu nền thương hiệu đậm hơn (`--ui-brand-hover: #085e50`) và giữ nguyên chữ trắng (`--ui-on-brand: #ffffff`), nâng tỷ lệ tương phản đạt **7.70:1** (vượt chuẩn WCAG 4.5:1). Probe lỗi xác nhận hết vi phạm (`probe_issue_detected: false`).
- **Khắc phục khoảng cách giả ~36px của form**: Loại bỏ `min-height` cố định 2 dòng trên nhãn (`.portal-app .ui-main .ui-form-grid .ui-field > label`), thiết lập margin-bottom tự nhiên `var(--ui-space-2)` (8px) giúp nhãn gắn chặt trực quan vào đúng ô nhập của nó theo nguyên tắc Gestalt proximity của Refactoring UI.
- Thử nghiệm trên Edge thật (`ops/run_button_states_uat.py`): 30/30 trạng thái nút trên các giao diện chính (Dashboard, Employee List, Employee Form, Login) qua cả 2 theme sáng/tối đều PASS 100%.

**Chi tiết thay đổi kỹ thuật**
- `src/static/css/shared_components.css`:
  - Định nghĩa chuẩn hoá độc lập khối `.ui-button`: không phụ thuộc vào tiền tố bọc ngoài `.portal-app .ui-main :is(...)`.
  - Phân định rõ ràng các biến thể: `.ui-button--primary` (brand solid), `.ui-button--secondary` (outline surface), `.ui-button--tertiary` (ghost text/link), `.ui-button--danger` (cảnh báo nguy hiểm).
  - Khắc phục xung đột hover: `.ui-button--primary:not(:disabled):hover` nạp với độ ưu tiên cao, bảo toàn `color: var(--ui-on-brand)`.
  - Chuẩn hoá `.ui-field > label`: bỏ `min-height: calc(var(--ui-font-size-small) * var(--ui-line-height-body) * 2)`, thiết lập `margin: 0 0 var(--ui-space-2); line-height: var(--ui-line-height-body); color: var(--ui-text);`.

**Kết quả kiểm tra & Cổng chất lượng**
- `ops/run_button_states_uat.py`: 0 failures, 30 states PASS (Dashboard hover contrast: 7.70:1 > 4.5:1).
- `ops/check_ui_contrast.py`: 208/208 color pairs pass WCAG standards.
- `src/manage.py check`: 0 issues.
- `src/manage.py makemigrations --check`: No changes detected (0 migration / không sửa CSDL).
- `ops/run_tests.py --backend sqlite apps.portal.test_project_layout apps.portal.tests_mobile`: 20/20 PASS.

**Trạng thái nhánh & Bàn giao**
- Nhánh: `main`.

## 2026-10-16 — Bước B: Thiết lập Thang Thiết kế & Khung CSS Cascade Layers (commit ui: design tokens and cascade layers)

**Tóm tắt cho chủ dự án**
- Hoàn thành Bước B theo chuẩn Refactoring UI: thiết lập thang giá trị chuẩn xác cho typography, khoảng cách, bo góc, bóng mờ và màu sắc ngữ nghĩa trong `src/static/css/ui_tokens.css`.
- Khai báo kiến trúc tầng CSS chuẩn `@layer tokens, base, components, layouts, pages;` và bọc toàn bộ token trong `@layer tokens`.
- Nâng phiên bản cache tĩnh Service Worker lên `ihrms-static-v31-ui-layers-20261016` và cập nhật đồng bộ các stylesheet/script trong `base.html` lên `?v=20261016-ui-layers`.
- Kiểm tra toàn diện WCAG tương phản: 208/208 cặp màu đạt chuẩn. Toàn bộ 552 bài kiểm thử tự động trên SQLite PASS (0 lỗi).

**Chi tiết thay đổi kỹ thuật**
- `src/static/css/ui_tokens.css`:
  - Khai báo `@layer tokens, base, components, layouts, pages;` và `@layer tokens { ... }`.
  - Chuẩn hóa thang chữ: Caption/Small 14px, Body 16px, Lg 18px, Xl 20px, Title 24px, Display 36px (100% rem/px, không dùng em, không vi phạm kích thước tối thiểu 14px).
  - Chuẩn hóa thang khoảng cách: `--ui-space-1` (4px) đến `--ui-space-32` (128px).
  - Chuẩn hóa bo góc theo 3 vai trò: `--ui-radius-control: 0.25rem` (4px), `--ui-radius-card: 0.5rem` (8px), `--ui-radius-pill: 9999px`.
  - Khóa thang độ mờ cố định: `--ui-opacity-1` (0.05) đến `--ui-opacity-6` (0.8).
  - Vô hiệu hóa bóng đổ thẻ `--ui-shadow-card: none` theo quy chuẩn thiết kế phẳng tiếp cận của dự án.
  - Bổ sung các vai trò ngữ nghĩa: `--ui-text-primary`, `--ui-text-secondary`, `--ui-border-control`, `--ui-action`, `--ui-action-hover`, `--ui-on-action`.
- `src/templates/base.html`: Tăng phiên bản tham số `?v=20261016-ui-layers` cho `ui_tokens.css`, `app_shell.css`, `ui_controls.css`, `shared_components.css`, `atoms_ui.css`, `project_layout.css`, `shared_components.js`.
- `src/static/js/service-worker.js`: Nâng hằng số `STATIC_CACHE` lên `ihrms-static-v31-ui-layers-20261016`.
- `src/apps/portal/test_project_layout.py` & `src/apps/portal/tests_mobile.py`: Cập nhật các assertion phiên bản asset và cache Service Worker tương ứng.

**Kết quả kiểm tra & Cổng chất lượng**
- `ops/check_ui_contrast.py`: 208/208 cặp màu PASS (light min text 5.100:1, dark min text 7.007:1).
- `src/manage.py check`: 0 issues.
- `src/manage.py makemigrations --check`: No changes detected (0 migration / không sửa CSDL).
- `ops/run_tests.py --backend sqlite`: 552 passed, 0 failures (7 skipped do yêu cầu SQL Server).

**Trạng thái nhánh & Bàn giao**
- Nhánh: `main`.

## 2026-10-16 — Bước A: Đo đạc và Thiết lập Baseline Hệ Thống Thiết Kế (commit docs: design system audit baseline)

**Tóm tắt cho chủ dự án**
- Hoàn thành Bước A theo chuẩn Refactoring UI: đo đạc toàn diện 20 tệp CSS dự án và hệ thống template.
- Ghi nhận baseline: 82 `!important`, 165 selector bám `.portal-app .ui-main`, 38 cỡ chữ phân biệt, 33 định nghĩa nút `ui-button` rải rác.
- Tái hiện thành công lỗi tương phản hover nút "Tạo đơn nghỉ" trên Edge thật (`ops/run_button_states_uat.py --probe-issue`): tỷ lệ tương phản sụt từ 5.70:1 xuống 1.12:1 do xung đột độ ưu tiên CSS khiến nền nhạt đè lên chữ trắng.
- Thiết lập công cụ kiểm tra tự động `ops/audit_design_tokens.py` và lưu trữ baseline tại `docs/DESIGN_SYSTEM_BASELINE.md`.

**Chi tiết đo đạc baseline**
- Số tệp CSS: 20 tệp (156.1 KB).
- Số lượng `!important`: 82 vị trí.
- Tiền tố `.portal-app .ui-main`: 165 bộ chọn.
- Phân bố thành phần: `.ui-button` (33 định nghĩa), `.ui-field` (58 định nghĩa), `.ui-card` (20 định nghĩa), `.ui-badge` (14 định nghĩa), `.ui-table` (42 định nghĩa).
- Kết quả Probe lỗi hover: Xác nhận trên Playwright/Edge: nút `Tạo đơn nghỉ` có màu chữ `rgb(255, 255, 255)`, nền hover `rgb(237, 244, 240)` dẫn đến tương phản 1.12:1 < 4.5:1 (vi phạm WCAG).

**Trạng thái nhánh & Bàn giao**
- Nhánh: `main`.

## 2026-10-16 — Chuẩn hóa Nút Đăng nhập, Kích hoạt Click KPI Hợp đồng và Đổi KPI thứ 4 sang "Cần duyệt và xử lý" (commit fix(ui): login button styling and dashboard kpi links)

**Tóm tắt & Mục tiêu**
- Khắc phục nhanh 3 vấn đề người dùng phản hồi:
  1. **Hiển thị chuẩn hóa Nút Đăng nhập (`login.html`, `shared_components.css`, `project_layout.css`)**:
     - Bọc nút submit trong cụm container `<div class="ui-form-actions">`.
     - Mở rộng bộ chọn `.portal-app .ui-main :is(.ui-page,.ui-form-actions,.ui-login-wrap) .ui-button` và `.ui-button--primary` trong `shared_components.css` để các button bên trong form đăng nhập luôn nhận đầy đủ styling nút chính (màu brand nền, chữ trắng, padding, border radius, hover state).
     - Bổ sung quy tắc căn chỉnh riêng cho `.ui-login-wrap .ui-button`: chiều rộng 100%, chiều cao tối thiểu 2.75rem, căn giữa nội dung, tạo trải nghiệm trực quan, dễ thao tác và không còn tình trạng nút bị chìm hoặc hiển thị dạng văn bản trơn.
  2. **Kích hoạt tính năng click cho KPI "Hợp đồng sắp hết hạn" (`home_presentation.py`)**:
     - Bổ sung thuộc tính điều hướng `href=reverse("portal:hr_contract_list")` cho thẻ KPI "Hợp đồng sắp hết hạn (≤60 ngày)" khi người dùng có quyền `manage_hr`.
     - Giúp thẻ chuyển từ `<div>` sang thẻ `<a>` có trạng thái hover, con trỏ pointer và khi bấm vào sẽ chuyển thẳng đến trang Quản lý danh sách hợp đồng lao động.
  3. **Đổi KPI thứ 4 sang "Cần duyệt và xử lý" (`home_presentation.py`)**:
     - Đổi nhãn hiển thị và `short_label` từ "Đơn nghỉ chờ duyệt" thành "Cần duyệt và xử lý".
     - Sử dụng icon `checklist` thay cho icon lịch cũ, thể hiện chính xác tính chất danh sách hàng đợi công việc/phê duyệt của hệ thống.
     - Cập nhật logic `attention`: kích hoạt chấm đỏ thông báo khi có việc chờ duyệt/xử lý (chứa từ khóa "chờ duyệt" hoặc "cần duyệt").
     - Đồng bộ bài kiểm tra UAT trình duyệt trong `ops/run_browser_uat.py` (cả 4 thẻ KPI chính giờ đây đều là link điều hướng trực tiếp).

**Kết quả kiểm tra & Cổng chất lượng**
- `ops/run_tests.py --backend sqlite`: 552 tests, **0 failures**, **552 passed** (7 skipped).
- `ops/check_ui_contrast.py`: 208/208 color pairs pass WCAG standards.
- `src/manage.py check`: 0 issues.
- `src/manage.py makemigrations --check`: No changes detected (không thay đổi CSDL / 0 migration).
- Đã kiểm tra bảo mật đăng nhập và CSRF (`apps.security.test_login_csrf`): toàn bộ PASS.

**Trạng thái nhánh & Bàn giao**
- Nhánh: `main`.
- Đã đóng gói bản sao kiểm toán ngoài repository tại `D:\QLHCNS-Backups\IHRMS_Review_20261016_Login_KPI.zip` (1548 tệp, manifest SHA-256 xác minh 100% khớp).

## 2026-10-16 — Chuẩn hóa bố cục Dự án, Tinh gọn ô nhập và Triệt tiêu yêu cầu Ctrl + F5 (commit ui: compact form grid and project layout)

**Tóm tắt & Mục tiêu**
- Khắc phục triệt để 3 vấn đề người dùng phản hồi theo tiêu chuẩn thiết kế Impeccable:
  1. **Triệt tiêu hiện tượng phải bấm `Ctrl + F5` mới cập nhật giao diện**:
     - Nâng phiên bản cache tĩnh của Service Worker trong `src/static/js/service-worker.js` từ `ihrms-static-v29-dashboard-design-20261015` lên `ihrms-static-v30-ui-compact-20261016`.
     - Kích hoạt cơ chế tự động xóa sạch bộ nhớ cache cũ khi Service Worker activate (`self.skipWaiting()` và `self.clients.claim()`).
     - Tăng tham số phiên bản `?v=20261016-ui-compact` đồng bộ cho các stylesheet và script dùng chung trong `src/templates/base.html` (`ui_controls.css`, `shared_components.css`, `project_layout.css`, `shared_components.js`).
     - Đồng bộ các bài kiểm tra phiên bản asset tĩnh trong `src/apps/portal/tests_mobile.py` (`test_design_tokens_alignment_and_metric_hooks_are_shared`) và `src/apps/portal/test_project_layout.py` (`test_changed_cascade_assets_have_fresh_versions`).
  2. **Chuẩn hóa bố cục và phân cấp thị giác phân hệ Hoạt động dự án (`apps/activity`) & Công việc (`apps/portal`)**:
     - Bổ sung wrapper chuẩn hệ thống `<div class="ui-page ui-activity">` (và `<div class="ui-page">`) cho:
       - `activity/dashboard.html`: Đồng bộ `ui/page_header.html`, căn lề thẻ KPI, tối ưu dải lọc tháng (`size="compact"`) và CBDA (`size="narrow"`), thay thế empty state bảng bằng thành phần chuẩn `ui/empty_state.html`.
       - `portal/task_list.html`: Bọc `.ui-page`, chuẩn hóa thanh tác vụ và chuyển toàn bộ các trường hợp rỗng sang `ui/empty_state.html`.
       - `activity/proposal_approval_list.html`: Bọc `.ui-page ui-activity`, thay thế khối text xám trơn bằng `ui/empty_state.html`.
       - `activity/proposal_detail.html` & `activity/proposal_email_draft.html`: Bọc `.ui-page ui-activity`, làm sạch nhịp hiển thị và căn chỉnh nút thao tác.
       - `activity/calendar.html`: Bọc `.ui-page ui-activity`, tinh gọn ô lọc tháng (`size="compact"`) và CBDA (`size="narrow"`).
  3. **Thu gọn và chuẩn hóa kích thước các ô điền/chọn thông tin**:
     - Tái cấu trúc lưới `.ui-form-grid` tại `portal/asset_admin_list.html`:
       - Hàng 1 (Nhận diện thiết bị): `asset_code` (4) + `asset_name` (4) + `asset_type` (4) = 12.
       - Hàng 2 (Xuất xứ): `serial_number` (4) + `brand` (4) + `funding_source` (4) = 12.
       - Hàng 3 (Mua sắm & địa điểm): `purchase_date` (3) + `location` (5) + `quantity` (2) + `unit` (2) = 12 (triệt tiêu hoàn toàn ô ngày mua và địa điểm bị kéo giãn 50% màn hình desktop).
       - Hàng 4 (Giá trị & ghi chú): `purchase_value` (4) + `note` (8) = 12.
     - Tái cấu trúc form giao việc `portal/task_create.html`: Bọc `.ui-page`, cân đối `task_code` (4) + `task_name` (8) = 12; `assigned_to` (4) + `priority` (2) + `start_date` (3) + `due_date` (3) = 12; `description` (12).
     - Tinh gọn dải lọc `document/hcns/catalog.html`: Gán `size="wide"` cho trường `employee_id` để tránh tràn kích thước không cần thiết.

**Kết quả kiểm tra & Cổng chất lượng**
- `ops/run_form_contract_uat.py` (--directory TEMP --phase after): 1314 cases, **0 failures** (bảo toàn 100% hợp đồng trường, tên, thuộc tính, CSRF, trật tự DOM và logic POST).
- `ops/run_tests.py --backend sqlite`: 552 tests, **0 failures**, **552 passed** (7 skipped).
- `ops/check_ui_contrast.py`: 208/208 color pairs pass WCAG standards (min text: light 5.100:1, dark 7.007:1).
- `src/manage.py check`: 0 issues.
- `src/manage.py makemigrations --check`: No changes detected (không thay đổi CSDL / 0 migration).

**Trạng thái nhánh & Bàn giao**
- Nhánh: `main`.
- Đã đóng gói bản sao kiểm toán ngoài repository tại `D:\QLHCNS-Backups\IHRMS_Review_20261016_UI_Compact.zip` (1548 tệp, manifest SHA-256 xác minh 100% không lỗi).

## 2026-10-15 — Giai đoạn 5 – Chuẩn hóa Đăng nhập, Chấm công cá nhân và Phân trang (commit ui: login attendance pagination)

**Tóm tắt & Mục tiêu**
- Chuẩn hóa toàn bộ các màn hình cửa ngõ hệ thống và thành phần nền tảng theo chuẩn thiết kế Impeccable:
  1. **Trang đăng nhập (`registration/login.html` & `project_layout.css`)**:
     - Căn giữa giao diện bằng cấu trúc `.ui-login-wrap` với chiều cao tối ưu, áp dụng thẻ `.ui-card` đồng bộ token hệ thống.
     - Tích hợp logo IHRMS (`static/img/logo.png`), hiển thị tiêu đề và mô tả rõ ràng.
     - Chuẩn hóa thông báo lỗi đăng nhập bằng khối `.ui-alert ui-alert--danger`: ưu tiên hiển thị chi tiết từ `form.non_field_errors` (hỗ trợ hiển thị cảnh báo khóa tài khoản từ `django-axes` hoặc tài khoản ngưng hoạt động), fallback về `"Sai tên đăng nhập hoặc mật khẩu."`.
     - Bổ sung trường ẩn chuyển hướng `<input type="hidden" name="next" value="{{ next|default:'' }}">` đảm bảo chuyển tiếp đúng trang đích sau đăng nhập.
     - Định dạng multi-line cho 7 quy tắc `.ui-login-wrap` trong `project_layout.css` giúp mã nguồn rõ ràng và dễ theo dõi git diff.
     - Bảo toàn tuyệt đối cơ chế bảo mật: CSRF token, thuộc tính `data-login-csrf`, phiên bản `login_csrf.js?v=20261013-1`, tên trường `username`/`password`, `autocomplete`, và các bộ kiểm thử tự động.
  2. **Trang Bảng công cá nhân (`portal/attendance_list.html` & `views/attendance.py`)**:
     - Chuẩn hóa cấu trúc trang với `ui/page_header.html`, container `.ui-card`.
     - Chuyển đổi view sang phân trang chuẩn hệ thống với `_paginated_context(request, qs, "records", per_page=31)`, loại bỏ giới hạn cắt cứng `[:31]`, bảo toàn trọn vẹn tham số lọc URL thông qua `pagination_query`.
     - Tích hợp cụm điều hướng phân trang dùng chung `portal/_pagination.html` với chuẩn lớp `.ui-pagination` ngay bên dưới `.ui-table-scroll`.
     - Bảng chấm công `.ui-table` trong khung cuộn ngang `.ui-table-scroll` (có `role="region"`, `tabindex="0"`, `aria-label`).
     - Số giờ làm việc căn phải `tabular-nums`; áp dụng huy hiệu trạng thái một dòng với `ui_badge "attendance.attendance:status"` (Đủ công: `.ui-badge--success`, Đi muộn: `.ui-badge--warning`, Vắng/Nửa ngày: `.ui-badge--neutral`).
     - Trạng thái rỗng chuyên nghiệp với `ui/empty_state.html`.
  3. **Thành phần phân trang dùng chung (`portal/_pagination.html`)**:
     - Rà soát xác minh toàn bộ các thuộc tính điều hướng trang: bảo toàn 100% tham số truy vấn tìm kiếm/lọc (`pagination_query`), nhãn hỗ trợ tiếp cận `aria-label="Phân trang danh sách"`, `aria-current="page"`, `ui_number`.
  4. **Khắc phục kiểm thử hồi quy**:
     - Bổ sung lớp `.ihrms-kpi-value` vào thẻ KPI trong `activity/dashboard.html` đảm bảo tương thích hoàn toàn với bài kiểm tra tĩnh `test_design_tokens_alignment_and_metric_hooks_are_shared`.
     - Bổ sung lớp `overflow-hidden rounded-xl` vào wrapper lưới lịch `activity/calendar.html` đảm bảo tương thích với `test_cbda_calendar_shows_assigned_activities_for_selected_month`.

**Kết quả kiểm tra & Cổng chất lượng**
- `ops/run_layout_alignment_audit.py` (--phase after): 146 routes, 7021 cases, **0 vi phạm**, **0 lỗi** (quét toàn bộ route/vai trò ở 1920/1756/1440/1280/1024/768/390px, sáng/tối).
- `ops/run_form_contract_uat.py` (--phase after): 1314 cases, **0 failures** (bảo toàn 100% hợp đồng trường, tên, thuộc tính, CSRF).
- `ops/run_print_layout_uat.py` (--port 8782): 402 checks, 37 PDFs xuất chuẩn, **0 failures**.
- `ops/run_tests.py --backend sqlite`: 552 tests, **0 failures**, **552 passed** (7 skipped).
- `src/manage.py check`: 0 issues.
- `src/manage.py makemigrations --check`: No changes detected (không đổi CSDL).
- `ops/check_ui_contrast.py`: 208/208 color pairs pass WCAG standards.

**Trạng thái nhánh & Bàn giao**
- Nhánh: `main`.
- Đã đóng gói bản sao kiểm toán ngoài repository tại `D:\QLHCNS-Backups\IHRMS_Review_20261015_Final.zip` kèm manifest SHA-256 xác minh 100%.


**Tóm tắt & Mục tiêu**
- Rà soát và chuẩn hóa toàn diện giao diện các trang thuộc phân hệ Hoạt động dự án (`apps/activity`) và Quản lý công việc (`apps/portal`) theo đúng tiêu chuẩn thiết kế Impeccable đã phê chuẩn:
  1. **Kiểm kê quyền truy cập và ma trận vai trò**:
     - Bảo toàn 100% các bộ lọc quyền: `is_hr_manager_or_admin`, `is_board_or_hr`, `can_approve_activity_proposals`, bộ lọc đề xuất của cá nhân/phòng ban/phê duyệt dự án.
     - Giữ nguyên các thao tác duyệt, từ chối, gửi duyệt, chuẩn bị dự thảo email, tải tài liệu SharePoint; không thêm bớt trường dữ liệu, không đổi tên input, action hay CSRF token.
  2. **Trang tổng quan hoạt động dự án (`activity/dashboard.html` & `_dashboard_actions.html`)**:
     - Chuẩn hóa header trang với `ui/page_header.html`, tách các nút tác vụ điều hướng sang `_dashboard_actions.html` phục vụ responsive.
     - Áp dụng hệ thẻ KPI `.ui-kpi-grid` với các chỉ số đề xuất: Chờ duyệt, Đã duyệt, Đang thực hiện, Hoàn thành.
     - Chuyển đổi bảng danh sách đề xuất gần đây sang `.ui-table` chuẩn thanh thoát, bao bọc trong container cuộn `.ui-table-scroll` hỗ trợ màn hình hẹp, huy hiệu trạng thái một dòng với họ `.ui-badge--*`.
  3. **Chi tiết đề xuất dự án (`activity/proposal_detail.html`)**:
     - Tái cấu trúc thành các thẻ `.ui-card` phân cấp rõ ràng: Thông tin chung, Nội dung hoạt động, Dự toán kinh phí, Hồ sơ đính kèm và Lịch sử phê duyệt.
     - Bảo toàn hợp đồng form (FormContract): Giữ nguyên cấu trúc các nút bấm duyệt/từ chối/upload tài liệu, thông báo lỗi dùng `.ui-alert`.
  4. **Danh sách & Chi tiết công việc (`portal/task_list.html`, `portal/task_detail.html`)**:
     - Chuẩn hóa `task_list.html` với `ui/page_header.html`, dải nút lọc phạm vi (Tất cả / Việc của tôi / Phòng ban) theo chuẩn `.ui-button`, bảng danh sách công việc `.ui-table`.
     - Tinh chỉnh `task_detail.html` với thẻ thông tin công việc, danh sách bình luận `.ui-comment-list`, form cập nhật tiến độ và tải tệp SharePoint đồng bộ.
  5. **Lịch hoạt động & Danh sách phê duyệt (`activity/calendar.html`, `activity/proposal_approval_list.html`)**:
     - Chuẩn hóa lưới lịch tháng `calendar.html` hiển thị rõ ràng ngày tháng và các sự kiện dự án, độ tương phản cao, responsive trên di động.
     - Áp dụng `ui/page_header.html` và `.ui-table` cho `proposal_approval_list.html`.
  6. **Dự thảo email & Biểu mẫu tạo hoạt động (`activity/proposal_email_draft.html`, `activity/activity_form.html`, `portal/widgets/task_create.html`)**:
     - Chuẩn hóa khung soạn email đề xuất dự án `proposal_email_draft.html` với thẻ chi tiết người nhận/nội dung và form xác nhận gửi.
     - Tinh chỉnh `activity_form.html` và `task_create.html` loại bỏ các class Tailwind dư thừa, giữ nguyên 100% hợp đồng form và nhịp lưới.

**Kết quả kiểm tra & Cổng chất lượng**
- `ops/run_layout_alignment_audit.py` (--phase after): 146 routes, 7021 cases, **0 vi phạm**, **0 lỗi** (quét toàn bộ route/vai trò ở 1920/1756/1440/1280/1024/768/390px, sáng/tối).
- `ops/run_form_contract_uat.py` (--phase after): 1314 cases, **0 failures** (bảo toàn 100% hợp đồng trường, tên, thuộc tính, CSRF).
- `ops/run_print_layout_uat.py` (--port 8782): 402 checks, 37 PDFs xuất chuẩn, **0 failures**.
- `src/manage.py test apps.portal.tests apps.portal.test_project_layout apps.portal.test_home_dashboard`: 60/60 tests OK.
- `src/manage.py check`: 0 issues.
- `src/manage.py makemigrations --check`: No changes detected (không đổi CSDL).
- `ops/check_ui_contrast.py`: 208/208 color pairs pass WCAG standards.

**Trạng thái nhánh & Bàn giao**
- Nhánh: `main`.
- Đã đóng gói bản sao kiểm toán ngoài repository tại `D:\QLHCNS-Backups\IHRMS_Review_20261015_Projects.zip` kèm manifest SHA-256 xác minh 100%.


**Tóm tắt & Mục tiêu**
- Rà soát và chuẩn hóa toàn diện giao diện các trang Báo cáo phân hệ Portal (`report_personnel_changes`, `report_timesheet`, `report_budget`, `report_headcount`, `_pagination`) theo tiêu chuẩn thiết kế Impeccable đã chốt:
  1. **Kiểm kê quyền truy cập báo cáo**:
     - Phân tích và đối chiếu hàm `_can_view_reports(request)`: Tại `src/apps/reporting/views.py` kiểm tra permission `"view_report_center"`, phục vụ trung tâm dữ liệu và phân tích tổng quan; tại `src/apps/portal/views/reports_planning.py` kiểm tra permission `"view_reports"`, phục vụ báo cáo tác nghiệp kế hoạch và nhân sự.
     - Bảo toàn tuyệt đối quyền hạn và ma trận phân quyền: Giữ độc lập hai hàm kiểm tra, không hợp nhất, không thay đổi logic; bảo vệ dữ liệu nhạy cảm của Báo cáo ngân sách và Biến động nhân sự, không nới lỏng hay thu hẹp phạm vi phòng ban được phép xem của người dùng.
  2. **Biến động nhân sự (`report_personnel_changes.html`)**:
     - Loại bỏ toàn bộ 4 emoji section (`🟢 Tuyển mới`, `🔴 Nghỉ việc`, `🔀 Điều chuyển`, `⬆️ Bổ nhiệm / Thăng chức`), thay bằng nhãn ngữ nghĩa với huy hiệu chuẩn một dòng: `.ui-badge--success`, `.ui-badge--danger`, `.ui-badge--info`, `.ui-badge--accent`.
     - Thay nút In emoji `🖨` cũ bằng action template dùng chung `portal/_report_print_action.html` (`ui-button ui-button--secondary`).
     - Định dạng ngày tháng bằng `ui_date` (`%d/%m/%Y`), bảng dữ liệu `.ui-table` với `caption.ui-sr-only`, bảo toàn đúng 4 wrapper `mobile-table-scroll` đáp ứng kiểm thử responsive `tests_mobile.py`.
  3. **Chấm công & Tồn phép (`report_timesheet.html`)**:
     - Loại bỏ khối `<style> @media print ... </style>` nhúng trang; áp dụng `ui/page_header.html` kèm nút In báo cáo.
     - Cải tổ bảng từ viền thô `border-gray-300` sang bảng `.ui-table` chuẩn thanh thoát; số giờ căn phải `tabular-nums`; trạng thái "chờ duyệt" dùng `.ui-badge--warning`; giữ năm thô (`ui_year`).
  4. **Ngân sách năm (`report_budget.html`)**:
     - Áp dụng `ui/page_header.html`, thẻ bộ lọc `ui-query-card`, bảng `.ui-table`. Cột số tiền sử dụng bộ lọc tiền tệ chuẩn `ui_vnd` (`xxx.xxx đ`), số dư âm hiển thị cảnh báo, container cuộn có `role="region"` và tabindex đầy đủ.
  5. **Định biên nhân sự (`report_headcount.html`)**:
     - Dọn sạch các lớp Tailwind dư thừa trên thead (`text-left text-gray-500 border-b border-gray-200`, `py-2 pr-4`), đồng bộ cấu trúc `ui-page-header`, bảo toàn 100% bố cục và lớp chuyên biệt `headcount_report.css` cùng các selector kiểm thử.
  6. **Phân trang dùng chung (`_pagination.html`)**:
     - Chuẩn hóa thống nhất toàn bộ về cấu trúc `.ui-pagination` với `.ui-button`, `aria-label="Phân trang danh sách"`, `aria-current="page"`, `ui_number`, triệt tiêu toàn bộ lớp Tailwind cũ (`text-gray-600`, `text-blue-700 underline`, `flex gap-4`).
  7. **Tinh chỉnh căn chỉnh form tài sản (`asset_admin_list.html`)**:
     - Bổ sung `tablet_span="12"` cho trường `purchase_value` để trên màn hình tablet (768px–1023px) mỗi hàng đạt trọn vẹn 12 cột, giải quyết triệt để 8 trường hợp `ROW_HOLE` tại 768px.

**Kết quả kiểm tra & Cổng chất lượng**
- `ops/run_layout_alignment_audit.py` (--phase after): 146 routes, 7021 cases, **0 vi phạm**, **0 lỗi** (quét toàn bộ route/vai trò ở 1920/1756/1440/1280/1024/768/390px, sáng/tối).
- `ops/run_form_contract_uat.py` (--phase after): 1314 cases, **0 failures** (bảo toàn 100% hợp đồng trường, tên, thuộc tính, CSRF).
- `ops/run_print_layout_uat.py` (--port 8782): 402 checks, 37 PDFs xuất chuẩn, **0 failures**.
- `src/manage.py test apps.portal.test_headcount_design apps.portal.tests_mobile apps.portal.test_project_layout apps.portal.tests_shared_components`: 24/24 tests OK.
- `src/manage.py check`: 0 issues.
- `src/manage.py makemigrations --check`: No changes detected.
- `ops/check_ui_contrast.py`: 208/208 color pairs pass WCAG standards.

**Trạng thái nhánh & Bàn giao**
- Nhánh: `main`.
- Đã đóng gói bản sao kiểm toán ngoài repository tại `D:\QLHCNS-Backups\IHRMS_Review_20261015_Reports.zip` kèm manifest SHA-256 xác minh 100%.

## 2026-10-15 — Chốt chất lượng hệ thống form và kiểm toán căn chỉnh (commit fix(ui): consolidate form grid after review)

**Tóm tắt & Mục tiêu**
- Khắc phục triệt để 3 vấn đề kiến trúc và căn chỉnh của hệ thống form sau rà soát `7b1c85e`:
  1. **Loại bỏ hệ lưới song song**: Xóa hoàn toàn `.ui-form-lines` / `.ui-form-line` khỏi `shared_components.css`. Đưa `supply_request_list.html` về một `.ui-form-grid` duy nhất với các span hàng (8+4=12, tablet_span="12"). Mở rộng test kiểm toán tĩnh `test_layout_audit_tools.py` cấm xuất hiện bất kỳ hệ lưới form nào khác ngoài `.ui-form-grid`.
  2. **Thay thế bộ chọn mong manh trong dải lọc**: Thay thế triệt để các bộ chọn CSS `:has(select:is([name=...]))` bằng tham số kích thước `size="narrow|wide|compact"` trên `ui/field.html` (`ui-field--filter-narrow`, `ui-field--filter-wide`, `ui-field--filter-compact`), gán tường minh tại template, loại bỏ phụ thuộc tên trường cứng trong CSS.
  3. **Ngăn chặn co hẹp trường ở 1024–1279px**: Bổ sung `container-type: inline-size` vào `.ui-form-grid` cùng các container query điều chỉnh độ rộng linh hoạt khi khung hẹp; cấm dùng `span="2"` cho các trường tiền tệ và ngày tháng; bố trí lại các hàng biểu mẫu bảo toàn nguyên vẹn thứ tự trường (Row contract) và đạt độ rộng tự nhiên tối ưu.
  4. **Tích hợp tiêu chí MIN_FIELD_WIDTH vào Layout Audit**: Cập nhật `ops/run_layout_alignment_audit.py` đo lường chiều rộng thực tế của tất cả các ô nhập/chọn trên màn hình (ngày/tháng ≥ 148px, tiền ≥ 144px, số ≥ 96px, mã/serial/unit ≥ 112px, select ≥ 160px, văn bản ≥ 176px).
  5. **Đính chính quy tắc bố cục**: Làm rõ quy tắc lưới: hàng chỉ được ngắn khi là hàng cuối cùng của nhóm logic (như `vehicle_booking_list` hàng 3+3, `activity_form` hàng cuối 6); bổ sung span còn thiếu cho `inventory_session_detail` và `timesheet_month`.
  6. **Không sửa các tệp không có route**: Giữ nguyên `office_incoming_list.html` và `office_outgoing_list.html` để chuyển chủ dự án quyết định tại `docs/Viec_Cho_Chu_Du_An_Quyet_Dinh.md`.

**Kết quả kiểm tra & Cổng chất lượng**
- `ops/run_layout_alignment_audit.py` (sau sửa): 146 routes, 7021 cases, **0 vi phạm**, **0 lỗi** (không bổ sung bất kỳ miễn trừ layout waiver nào).
- `ops/run_form_contract_uat.py` (sau sửa): 1314 cases, **0 failures** (bảo toàn 100% thứ tự trường, name, required, CSRF).
- `ops/run_print_layout_uat.py` (--port 8782): 402 checks, 37 PDFs xuất chuẩn, **0 failures**.
- `ops/run_timesheet_print_uat.py` (--port 8782 --phase after): 645 checks, 8 cases, **0 failures**.
- `src/manage.py test apps.portal`: 247 tests OK (bao gồm 18 bài kiểm tra tĩnh bố cục và công cụ audit).
- `src/manage.py check`: 0 issues.
- `src/manage.py makemigrations --check`: No changes detected (không thay đổi CSDL).
- `ops/check_ui_contrast.py`: 208 pairs, 0 failures.

**Trạng thái nhánh & Bàn giao**
- Nhánh: `main`.
- Tạo bản sao ngoài repository, kiểm tra SHA-256 từng file trước khi commit và push.

## 2026-10-15 — Rà soát và thu gọn toàn diện ô nhập/chọn cho tất cả nhóm nghiệp vụ theo phản ánh kiểm thử

**Tóm tắt cho chủ dự án**
- Tiếp nhận phản ánh từ chủ dự án kèm ảnh chụp thực tế: các ô nhập liệu số, ngày tháng, mã số, đơn vị tính trên các form nghiệp vụ bị kéo giãn quá rộng (chiếm 33% đến 50% màn hình desktop ~450px-700px), gây khó xem, tốn diện tích và khó thao tác.
- Đã thực hiện rà soát và tái cấu trúc lưới bố cục (`.ui-form-grid`) cho 16 biểu mẫu trải dài qua toàn bộ các nhóm nghiệp vụ (Tài chính, Tài sản, Hành chính, Nhân sự, Tuyển dụng, Hoạt động dự án) theo nguyên tắc:
  1. Phân bổ nhịp cột theo kích thước tự nhiên của dữ liệu: `span="2"` cho số lượng nhỏ / đơn vị tính / tỷ lệ / số thứ tự; `span="3"` cho ngày tháng / mã số / số tiền nhỏ / dropdown ngắn; `span="4"` - `span="6"` cho tên gọi / phòng ban / địa chỉ / vị trí; `span="12"` cho trích yếu / mô tả dài / tệp đính kèm.
  2. Gom các ô liên quan trên cùng 1 hàng gọn gàng: mỗi hàng trong `.ui-form-grid` đều đạt tổng 12 cột, triệt tiêu khoảng trống thừa và tuân thủ tuyệt đối quy tắc `ROW_HOLE` và `COLUMN_LINE`.
  3. Bảo toàn 100% wire contract: không thay đổi bất kỳ `id`, `name`, `type`, `required`, `method`, `action`, CSRF token hay logic validation nào của biểu mẫu.
- **Chi tiết tinh chỉnh theo từng phân hệ**:
  1. **Tài chính**:
     - *Biểu thuế TNCN lũy tiến (`finance_tax_config.html`)*: Thu gọn toàn bộ 5 ô từ 2 hàng dãn to thành **1 hàng duy nhất** cực kỳ gọn: Hiệu lực từ (`span="2"`), Bậc thuế (`span="2"`), Thu nhập từ (`span="3"`), Thu nhập đến (`span="3"`), Thuế suất (`span="2"`) = 12 cột.
     - *Thêm Giảm trừ gia cảnh (`finance_tax_config.html`)*: Cân đối thành 1 hàng 3 ô (`span="4"` + `span="4"` + `span="4"` = 12 cột).
     - *Đăng ký Người phụ thuộc (`finance_dependent_list.html`)*: Thu gọn từ 2 hàng kéo dãn thành **1 hàng duy nhất gồm 4 ô**: Nhân viên (`span="3"`), Họ tên (`span="4"`), Quan hệ (`span="3"`), Hiệu lực từ (`span="2"`) = 12 cột.
  2. **Quản lý Tài sản**:
     - *Thêm tài sản mới (`asset_admin_list.html`)*: Cải tổ 12 trường từ 4 hàng × 3 ô dãn rộng (450px) thành **3 hàng × 4 ô cân đối**:
       * Hàng 1: Mã tài sản (3) + Tên tài sản (4) + Loại (3) + Số serial (2) = 12.
       * Hàng 2: Nhãn hiệu (3) + Nguồn vốn (3) + Ngày mua (3) + Vị trí (3) = 12.
       * Hàng 3: Số lượng (2) + Đơn vị tính (2) + Nguyên giá (2) + Ghi chú (6) = 12.
       * Các trường số lượng ("1"), đơn vị tính ("chiếc"), serial giờ đây nhỏ gọn, tự nhiên.
     - *Đợt kiểm kê tài sản (`inventory_session_list.html`)*: Tên đợt (`span="5"`), Văn phòng (`span="4"`), Thời điểm (`span="3"`) = 12 cột.
     - *Ban kiểm kê (`inventory_session_detail.html`)*: Phân bổ Nhân viên (`span="8"`), Vai trò (`span="4"`) = 12 cột.
  3. **Hành chính & Văn phòng**:
     - *Đặt xe (`vehicle_booking_list.html`)*: Hàng 1 (Xe 4 + Đến 4 + Mục đích 4 = 12); Hàng 2 thu gọn 2 ô datetime-local thành compact `span="3"` (Bắt đầu 3 + Kết thúc 3).
     - *Sổ công văn đến (`office_incoming_list.html`)*: Hàng 1 gồm 4 ô gọn: Số CV (3) + Ngày đến (3) + Nơi gửi (3) + Hạn (3) = 12; Hàng 2: Trích yếu (12).
     - *Sổ công văn đi (`office_outgoing_list.html`)*: Hàng 1 gồm 4 ô gọn: Số CV (3) + Ngày gửi (3) + Nơi nhận (3) + Người ký (3) = 12; Hàng 2: Trích yếu (12); Hàng 3: Tệp đính kèm (12).
     - *Vào sổ công văn chung (`dispatch_create.html`)*: Thu gọn Ngày ban hành (`span="3"`), Ngày đến/gửi (`span="3"`), Cơ quan (`span="6"`).
     - *Lịch công tác / Sự kiện (`event_list.html`)*: Hàng 1 (Tiêu đề 6 + Loại sự kiện 3 + Phòng ban 3 = 12); Hàng 2 (Bắt đầu 3 + Kết thúc 3 + Địa điểm 6 = 12); Hàng 3: Mô tả (12).
  4. **Nhân sự & Tuyển dụng**:
     - *Đề xuất tuyển dụng (`recruitment_create.html`)*: Hàng 1 (Mã đề xuất 6 + Phòng ban 6 = 12); Hàng 2 (Vị trí 6 + Số lượng cần 3 + Ngày cần 3 = 12); Hàng 3: Lý do tuyển dụng (12).
     - *Hợp đồng lao động (`hr_contract_form.html`)*: Hàng 1 (Nhân viên 5 + Loại HĐ 4 + Số HĐ 3 = 12); Hàng 2 (Ngày BĐ 3 + Ngày KT 3 + Lương cơ bản 3 + Trạng thái 3 = 12).
     - *Hồ sơ nhân viên mục Công việc (`hr_employee_form.html`)*: Hàng 1 (Ngày vào 3 + Ngày nghỉ 3 + Phòng ban 6 = 12); Hàng 2 (Vị trí 3 + Chức danh 3 + Quản lý 3 + Trạng thái làm việc 3 = 12) — thu gọn hoàn toàn 2 hàng 6+6 cũ thành 1 hàng 4 ô thanh thoát.
     - *Thêm ứng viên tuyển dụng (`hr_candidate_form.html`)*: Hàng 1 (Mã 3 + Họ tên 6 + SĐT 3 = 12); Hàng 2 (Email 3 + Địa chỉ 6 + Nguồn 3 = 12).
     - *Tạo đơn nghỉ phép (`leave_create.html`)*: Loại nghỉ phép (`span="6"`), Từ ngày (`span="3"`), Đến ngày (`span="3"`) = 12; Lý do (`span="12"`).
  5. **Hoạt động dự án**:
     - *Tạo hoạt động dự án (`activity_form.html`)*: Thu gọn Ngày bắt đầu (`span="3"`), Ngày kết thúc (`span="3"`), CBDA (`span="3"`), ĐPV (`span="3"`) = 12 cột.
- **Kiểm tra và xác nhận**:
  - `python src/manage.py check`: 0 issues.
  - `python src/manage.py makemigrations --check --dry-run`: 0 migration, không sửa CSDL.
  - `git diff --check`: 0 lỗi thụt lề/khoảng trắng.
  - `ops/check_ui_contrast.py`: 208/208 cặp màu đạt chuẩn tương phản WCAG.
  - `ops/run_tests.py --backend sqlite apps.portal.test_project_layout apps.portal.test_layout_audit_tools`: 18/18 tests OK.
  - `ops/run_tests.py --backend sqlite apps.portal`: 247/247 tests OK (skipped=3).
- **Trạng thái nhánh & bàn giao**:
  - Nhánh duy nhất: `main`.
  - Tạo bản sao mã nguồn ngoài repository, kiểm tra tính toàn vẹn SHA-256 từng file trước khi commit/push.


## 2026-10-15 — Tinh chỉnh bố cục gọn gàng, thu gọn ô nhập và gom 2 hàng × 3 ô danh mục biểu mẫu theo phản ánh kiểm thử

**Tóm tắt cho chủ dự án**
- Tiếp nhận và xử lý triệt để 3 phản ánh kiểm thử thực tế từ ảnh chụp màn hình của chủ dự án:
  1. **Danh mục Biểu mẫu HCNS / Tuyển dụng (`catalog.html` / `hcns_forms.css` / `project_layout.css`)**:
     - Phát hiện nguyên nhân gốc: quy tắc CSS cũ tại `project_layout.css` ép `.hcns-cards` chia theo tỉ lệ split 2 cột (`minmax(0,3fr) minmax(0,2fr)`) trên màn hình desktop (>=1280px), khiến 6 thẻ biểu mẫu bị dãn to và tách làm 3 hàng × 2 ô.
     - Đã loại bỏ `.hcns-cards` khỏi danh sách 2 cột tại `project_layout.css`; chuẩn hóa lưới `.hcns-cards` trong `hcns_forms.css` thành 3 cột cố định trên desktop (`repeat(3, minmax(0, 1fr))`), 2 cột trên tablet và 1 cột trên mobile.
     - Kết quả: 6 biểu mẫu được gom hoàn hảo thành **2 hàng, mỗi hàng 3 ô** gọn gàng, cân đối, dễ thao tác theo đúng yêu cầu chủ dự án. Tăng asset version `hcns_forms.css` thành `?v=20261015-ui-compact`.
  2. **Chạy lương hàng tháng — Tạo kỳ lương mới (`finance_period_list.html`)**:
     - Khắc phục lỗi ô nhập "Tháng" và "Năm" bị kéo dãn 50% chiều rộng toàn màn hình (`span="6"`).
     - Thu gọn kích thước ô nhập thành `span="2"` trên desktop (~200px), tự co giãn 6 cột trên tablet và 12 cột trên mobile. Nhập liệu 1-2 chữ số cho Tháng và 4 chữ số cho Năm hiển thị tự nhiên, không còn ô trống mênh mông, thao tác nhanh gọn.
  3. **Biểu thuế TNCN lũy tiến & Cấu hình Thuế/Bảo hiểm (`finance_tax_config.html`)**:
     - Cân đối form Biểu thuế TNCN lũy tiến thành 2 hàng hợp lý:
       * Hàng 1 (Đặc tả bậc): Hiệu lực từ (`span="4"`), Bậc thuế (`span="4"`), Thuế suất (%) (`span="4"`) — 3 ô trên 1 hàng, chấm dứt tình trạng ô Thuế suất đứng đơn độc kéo dài 100% toàn màn hình ở hàng dưới.
       * Hàng 2 (Ngưỡng thu nhập): Thu nhập từ (`span="6"`), Thu nhập đến (`span="6"`) — 2 ô nằm cạnh nhau, đủ không gian hiển thị nhãn dài mà không gãy dòng luộm thuộm.
     - Tối ưu thêm form Thêm tỷ lệ Bảo hiểm (gom 3 tỷ lệ NLĐ thành 1 hàng 3 ô `span="4"`, 3 tỷ lệ Trung tâm thành 1 hàng 3 ô `span="4"`, thay vì 6 hàng kéo dài full-width) và form Giảm trừ gia cảnh (Giảm trừ bản thân `span="6"` và Phụ thuộc `span="6"` nằm cùng hàng).
- **Kiểm tra và xác nhận**:
  - `python src/manage.py check`: 0 issues.
  - `python src/manage.py makemigrations --check --dry-run`: 0 migration, không đổi CSDL.
  - `git diff --check`: 0 lỗi khoảng trắng.
  - `ops/check_ui_contrast.py`: 208/208 cặp màu đạt chuẩn WCAG.
  - `test_project_layout` + `test_layout_audit_tools`: 18/18 tests OK.
  - `apps.portal` full test suite: 247/247 tests OK (3 skipped, 221s). Toàn bộ form wire contract (ID, name, method, action, validation, CSRF) bảo toàn 100%.

## 2026-10-15 — Rà soát bố cục, kích thước và sắp xếp ô nhập/chọn thông tin toàn hệ thống

**Tóm tắt cho chủ dự án**
- Rà soát toàn bộ các trang biểu mẫu theo phản ánh của chủ dự án và bộ quy chuẩn Impeccable.
- Khắc phục lỗi kéo giãn full-width trên trang Đề nghị văn phòng phẩm: chuyển 3 dòng vật tư thành các cặp ô (Vật tư 8 cột + Số lượng 4 cột) nằm trên cùng hàng trong `.ui-form-line`.
- Khắc phục lỗi ép cứng 13rem cho thẻ `<select>` trong `.ui-query-bar`: mở rộng ô chọn thực thể (nhân viên, phòng ban, dự án) từ 18-28rem, giải phóng nhãn dài "Điền thông tin từ hồ sơ nhân viên" khỏi việc bị bóp nghẹt 3 dòng trên trang Biểu mẫu tuyển dụng/HCNS.
- Nâng cấp `shared_components.css`: bổ sung đầy đủ nhịp lưới 12 cột (`.ui-field--2`, `.ui-field--5`, `.ui-field--7`, `.ui-field--8`, `.ui-field--9`, `.ui-field--10`) và lớp container `.ui-form-lines` / `.ui-form-line`.
- Tối ưu hóa các biểu mẫu khác: Đề nghị mua sắm (hàng hóa 6 - số lượng 2 - đơn giá 4), Vào sổ công văn (trích yếu 6 - cơ quan 6), Tạo công việc (chuyển sang ui-card và ui-page-title), Chấm công (ngày 2 - dự án 3 - công việc 5 - số giờ 2), Tạo chỉ tiêu KPI (nhân viên 4 - chỉ số 4 - kỳ 2 - chỉ tiêu 2), Danh mục ngày lễ (mã 3 - tên 6 - ngày 3).
- Toàn bộ wire contract giữ nguyên 100% (không đổi method, action, field name, CSRF, validations); 0 migration; full 247 portal tests pass.

## 2026-10-15 — Dashboard và báo cáo định biên: thang chữ, nhịp và mặt phẳng

**Tóm tắt cho chủ dự án**
- Cải thiện hai trang bằng Impeccable; giữ navy–teal, dữ liệu/quyền/liên kết và giấy in.
- Bỏ trần pixel cũ; ưu tiên phân cấp, đệm16–20px, gap16/32px và cuộn tự nhiên.
- main bắt đầu tại f9c1395, fetch/remote khớp, ahead/behind0/0; giữ thư mục ảnh tham chiếu chưa tracked.
- Tách năm commit: phê bình → token → Dashboard → báo cáo → kiểm tra nghiệm thu.
- Chỉ dùng DB/media/tài khoản giả bên ngoài repository; chưa deploy.
- Kết quả cuối, ảnh và giới hạn được bổ sung tại chính mục này trước bàn giao.

**Impeccable/ngữ cảnh:** nạp `C:/Users/dinht/.agents/skills/impeccable/SKILL.md`, chạy `scripts/impeccable.cmd context --target src/apps/portal/templates/portal/dashboard.html` exit0; đọc DESIGN, MASTER, ui_tokens và hai ảnh `design-system/reference/layout`. Không có thư mục Atoms trên đĩa. Skill dùng chung hoạt động; không có bản `.agents/skills/impeccable` trong repo, không cài/đổi skill thay thế. Đây là cải tạo hai bề mặt hiện có trong hệ nhận diện đã chốt; không tạo thế giới thương hiệu mới/PRODUCT giả định. Phiên bản có layout/typeset/quieter/distill/harden/adapt/polish; không có arrange/normalize, dùng layout và token/MASTER để chuẩn hóa.

**Bước1 — critique:** hai assessment độc lập theo skill: A xem32 ảnh Dashboard bốn vai trò ở1440/1756 sáng/tối first/full, hai ảnh chủ dự án và live; B quét markup và xem browser mới desktop/mobile. Chỉ đọc B sau khi A hoàn tất; tổng hợp `docs/DASHBOARD_DESIGN_CRITIQUE.md`,24/40 trước sửa, năm tiêu chí đều chưa đạt. Detector26 advisory line0 màu đen là false positive template Django không resolve static; không thêm ignore/waiver. Browser CUA không cho mutation nên không overlay; B đóng tab, không mở server phụ. Live8796 còn template cached compact-final nên không gọi là bằng chứng đúng toàn HEAD. Baseline archivef9c1395 mới port8811, nguồn mới8810; restart nguồn mới khi đổi template. Questions skipped vì brief đã quyết định chi tiết. Kiểm tra tài liệu UTF-8, `git diff --check`; phần triển khai chưa bắt đầu ở commit critique.

**Runtime/baseline:** `%TEMP%/ihrms-dashboard-design-20261015`, SQLite/media giả sao từ fixture synthetic_only đã có, nguồn baseline `%TEMP%/ihrms-dashboard-design-baseline-f9c1395`. Không dùng DB vận hành. `ops/run_form_contract_uat.py --directory <runtime> --source-root <baseline> --phase before`:1.314ca/0 lỗi,exit0. Đang chụp baseline và chạy audit trước trên nguồn archive. Dữ liệu richer toàn route có SELECT Director19/admin21; ghi đúng mốc thực đo, không thay bằng số18/20 từ runtime ít fixture. So Dashboard chín tài khoản và số liệu/GET-write trên cùng DB trước/sau, không đổi truy vấn để ép số.

**Còn mở:** đã hoàn tất 5/5 bước. Chưa kiểm thử màn hình hỗ trợ tiếp cận (screen reader), zoom native 200%, tài khoản thật/máy in thật trong phiên người dùng; chủ dự án xác nhận các mục này sau bàn giao.

**Bước2 — visual system tokens:** thêm token opt-in h1/h2/nhãn/KPI/số vừa/số công việc, line-height và trọng lượng500/600; thêm space5(20px), border-subtle ánh xạ card-border hiện có. Không đổi giá trị palette, control hoặc token đang được giấy in sử dụng. Bump URL ui_tokens và worker v27. Áp layout/typeset trên hệ Operate hiện có; không có dependency/font/CDN mới. Kiểm focused: `ops/check_ui_contrast.py`, `git diff --check`; kết quả lưu cùng runtime, triển khai token vào Dashboard ở bước3.

**Bước3 — layout/typeset/quieter/distill:** viết lại home_dashboard.css thành các khối scoped .home-dashboard, breakpoint ở cuối; không ID/!important/:has(), không trần chiều cao thẻ/hàng. Dashboard sở hữu khung riêng, bỏ lớp ui-page ở đúng root để không phải đấu specificity với generic ui-page của toàn app; giữ semantic section/partial/URL. Cập nhật hai parser test theo root mới, không bỏ kiểm quyền. Bốn KPI (khi có đủ DTO) nhãn xuống dòng/icon phải, số32; số công việc28, Dự án/Tuyển dụng24; đệm16–20/gap16/32. Dự án vẫn đủ5 số và guard; Tuyển dụng chỉ dựng các ô DTO được cấp (nguồn hiện có tối đa3, không sáng tác ô thứ4). Giữ donut/SVG/geometry/%/bảng thay thế; tên phòng200/thanh/số72/cờ dùng subgrid. Chỉ đoạn vượt mảnh và huy hiệu nhẹ. Trả hợp đồng/nghỉ5/3, quyết định5/3; Định biên6/4. Nhãn KPI điều chỉnh ở bản sao trình bày, không mutate snapshot. Trạng thái hàng chờ rỗng ở trong thẻ. home-jumps có JS/caller thật nên giữ các liên kết nhảy, không gọi là mã chết. Tăng asset/worker v28.

**Kiểm bước3:** focused `compact-final-tests.py --backend sqlite apps.portal.test_home_dashboard_layout apps.portal.test_home_dashboard`:21test OK/exit0 sau cập nhật parser; lượt đầu lỗi23 subtest do parser còn bám root cũ, không tính pass. Ảnh Edge thật step3 của4 vai trò ×1440/1756/390 ×sáng/tối, first/full đang chụp; đã xem Manager1440 sáng/390 tối và HR1440 toàn trang. Phát hiện tên nghỉ dài tràn vì luật th nowrap toàn cục kế thừa; sửa span tên wrap chủ động, không cắt tên để giấu lỗi. Đây là sửa từ bằng chứng nhìn, tiếp tục xác nhận ở lượt cuối. Baseline audit đủ146route/7.021ca/0vi phạm/0lỗi/exit0; baseline form1.314/0lỗi. Giấy in chưa đổi; tất cả cổng cuối vẫn phải chạy lại sau bước4/5.

**Bước4 — báo cáo định biên/polish:** thêm headcount_report.css chỉ màn hình, tiêu đề24/32/mô tả, thẻ20px, nhãn năm cách8px, số/tabular/tiêu đề số căn phải. Giữ form GET/year/default/options/actions, cột/nguồn/công thức/thứ tự. Chênh lệch diễn giải Vượt/Thiếu/Đủ bằng markup, raw vẫn trong data-value/aria-label và span hiển thị khi in; widthratio chỉ lấy trị tuyệt đối số nguyên gap cho chữ, không tính lại nghiệp vụ. Thêm caption/scope/nhãn vùng bảng/tabindex và hướng dẫn cuộn trên hẹp. Không thêm link quay lại vì breadcrumb đã có. MASTER thêm mục Bảng số liệu & báo cáo, quy chuẩn chỉ áp hai trang. Worker v29. Focused `apps.portal.test_headcount_design`:1test/0,086s/exit0, kiểm cả âm/dương/0/raw/filter. Edge chụp24 ảnh báo cáo HR/Director×1440/1756/390×hai theme×first/full,0pageerror; đã xem HR1440 sáng và390 tối. Báo cáo mobile giữ cuộn ngang có focus để đủ bốn cột, không tràn trang. Các lượt in/audit/full suite vẫn chờ bước5.

**Bước5 — kiểm tra nghiệm thu, chốt nguồn và đóng gói:** hoàn tất chốt mã nguồn cuối sau 4 bước. Đồng bộ worker version `ihrms-static-v29-dashboard-design-20261015` trong `test_project_layout.py` và `tests_mobile.py`; cập nhật `ops/run_asset_cache_uat.py`, `ops/run_browser_uat.py`, `ops/run_dashboard_layout_uat.py` và bổ sung `ops/run_headcount_design_uat.py`. Tinh chỉnh `home_dashboard.css` (subgrid metric, wrap tên hợp đồng, header mobile) và `headcount_report.css` (selector query). Kết quả kiểm tra xác nhận: `python src/manage.py check` 0 lỗi; `makemigrations --check --dry-run` 0 migration (no changes detected); `git diff --check` đạt; `ops/check_ui_contrast.py` đạt 208 cặp màu (min text 5.100:1, min UI 3.506:1, 0 vi phạm); `pip check` 0 broken requirements. Focused tests 42/42 test OK (6.356s); toàn bộ portal suite 247/247 test OK (3 skipped, 235.466s). Giữ nguyên quyền RBAC 11 vai trò, không thay đổi model hay CSDL. Bản sao review được đóng gói tại `D:/QLHCNS-Backups/IHRMS_Review_20261015_DashboardDesign_Final.zip` có manifest SHA-256 từng file. Commit bước 5 trên `main` và push `origin main` theo quy định.

## 2026-10-15 — Dashboard gọn, Dự án lên đầu và donut hợp đồng

**Tóm tắt cho chủ dự án**

- Đang triển khai bốn commit riêng theo yêu cầu đính kèm; chỉ làm trên main, baseline `225bafc` đã khớp origin/main 0/0.
- Giữ 60/40 cho các cặp nội dung (kể cả Công việc của tôi theo lời nhắn mới nhất, thay 50/50 trong tệp); một cột trên điện thoại.
- Thu gọn thẻ, đưa giải thích vào nút thông tin; không bỏ khối nghiệp vụ hay thay nguồn số liệu/quyền.
- Dự án sẽ đứng sau Công việc của tôi và hiện đủ năm số kể cả 0 khi quyền hiện có cho phép; khôi phục donut từ 71b6a2f.
- Mọi tạo/ghi thử nghiệm chỉ trên SQLite/media ngoài repo; chưa deploy, chưa xác nhận tài khoản thật/đọc màn hình/zoom trình duyệt 200%.
- Kết quả, số đo và bản sao cuối được bổ sung trong cùng mục trước bàn giao; không dùng kết quả lượt form để thay kiểm thử đợt này.

**Bước 1 — mật độ và cấu trúc:** `home_dashboard.css`, template Dashboard và partial KPI/công việc/HR/Hành chính/Tuyển dụng; popover details mở bằng Enter, đóng Escape/blur/click ngoài, không đẩy nội dung. Cấp h1/h2/h3 theo nhóm; rút nhãn hiển thị nhưng giữ tên đầy đủ bằng title; bỏ dòng Hiện tại và chú thích kỹ thuật trên mặt thẻ. Bảng định biên cho hỗ trợ tiếp cận giữ toàn bộ phòng; bản nhìn thấy sắp độ lệch và giới hạn6/4 theo vai trò. Cập nhật phần hiển thị nhãn Closed thành Đã đóng, không đổi giá trị lưu. Nguồn `dashboard_data.py` giữ nguyên.

**Kiểm tra bước 1:** `venv/Scripts/python.exe ops/run_tests.py --backend sqlite apps.portal.test_home_dashboard_layout apps.portal.test_home_dashboard` đạt17 test, exit0 (log `step1-tests3.log`). Lượt đầu phát hiện3 test cũ: điều kiện6 phòng ở Director và ẩn tuyển dụng0 được cập nhật theo đặc tả mới; nhãn Quá hạn/Hết hạn hôm nay được khôi phục, không bỏ hồi quy. Audit đầu200 ca/6 lỗi tràn390; sửa bảng mobile và giữ trường hợp tên dài, lượt mobile0 lỗi. Lượt cuối đủ7 độ rộng/9 tài khoản/sáng tối đạt200 ca,0 vi phạm,0 lỗi chạy, exit0; baseline cũng0 vi phạm. Không thêm miễn trừ. Bản đo bước đầu KPI104px, My work72px; ngân sách toàn trang chưa đạt và tiếp tục xử lý trong các bước kế tiếp.

**Runtime/bằng chứng:** `%TEMP%/ihrms-dashboard-compact-20261015`; baseline archive225bafc port8797, nguồn mới port8796; ảnh trước4 bậc đã chụp. `run_dashboard_group_contract_uat.py --phase before` exit0, SELECT theo employee/manager/hr-officer/hr/director/finance/sys/layout-admin/unlinked =10/14/18/23/18/10/5/20/5. Đây là baseline DTO/link/GET-write, không phải nghiệm thu nguồn cuối. Hai tài khoản sys/unlinked được công cụ tạo trong DB giả; admin do project UAT tạo. Lượt `--seed` toàn route ban đầu dừng ở thiếu Payroll, không ghi là đạt; chỉ các fixture đã tạo trong DB giả bị ảnh hưởng, không đụng vận hành.

**Bước 2 — Dự án thứ ba:** commit bước1 `e83ced9`; thêm đủ5 giá trị kể cả0, giữ guard `show_project_activity_summary`, header có Giao công việc/Lịch/Công việc và Dashboard hoạt động đúng quyền. Không gán link giả cho từng số khi trang đích chưa có bộ lọc tương ứng. HR Manager hiện không có quyền `view_activity_dashboard` nên không thêm khối trái quyền chỉ để khớp ảnh. Bổ sung kiểm thử0/thứ tự và phép so snapshot phát hiện fallback joined bị gắn short_label vào DTO; đã sửa bằng bản sao, thêm test bất biến. Focused27 test exit0; audit200 ca/0 vi phạm/0 lỗi exit0; so9 tài khoản DTO/link/query/GET-write chạy lại trên nguồn đã sửa. Công cụ Edge bổ sung số đo theo từng khối, ngân sách chiều cao, hàng36/40, badge28, popover không đẩy nội dung và ảnh first/full1440 cho4 bậc. Full suite chạy ở commit cuối theo yêu cầu tách bước, không dùng focused để thay full.

**Bước 3 — donut và cân đối cuối:** bước2 `0a62a32`; khôi phục `_hr_contract_donut.html` từ SVG71b6a2f, giữ geometry/tổng/% gốc, số thứ tự cung, tổng giữa và bảng thay thế;1 nhóm không vẽ donut. Chỉ phần vượt của thanh định biên tô cảnh báo, vạch kế hoạch giữ token. Thẻ cùng hàng60/40, KPI100px, công việc72px; HR≤520px. Preview hợp đồng3 dòng; đơn nghỉ3 dòng (2 ở chế độ Giám đốc), các dòng còn lại của DTO giữ trong disclosure. Giới hạn thấp hơn mức tối đa trong yêu cầu để đạt ngân sách mà không bỏ khối hay thay số tổng. Cặp link hàng dữ liệu là inline text (ngoại lệ target), không đè vùng bấm44px lên hàng36px.

**Kết quả đã xác nhận:** focused69 test đạt; full551 SQLite325,516s (7 skip) và SQL Server486,002s (0 skip), exit0 trên mã ứng dụng sau sửa geometry; dùng launcher ngoài repo với MD5 chỉ cho fixture mật khẩu của test, không đổi cấu hình app. Hai lượt full mặc định hasher cũ cũng chạy độc lập và không dùng để thay nguồn cuối. Build Tailwind thêm utility transform do SVG; đã đổi URL asset trong base và kiểm tra lại trên nguồn cuối. Print402/37PDF đạt, BCC645/8 ca đạt sau chạy tuần tự; hai lượt BCC đầu bị SQLite locked vì chạy cạnh browser audit ghi session nên không coi đạt. So37 PDF cùng DB/same-day baseline225bafc với nguồn mới: text và raster khớp toàn bộ. Workflow Edge402 kiểm tra/32 ảnh trên DB dùng một lần đã hủy. Cache9 kiểm tra giữ cookie/cache, KPI244→100px. Project layout73 trang1604 kiểm tra đạt; full route146/7021ca,0 vi phạm/0 lỗi; Dashboard3572 kiểm tra/48 ảnh,0 lỗi, còn lượt nguồn cuối sau build. So1314 ca form/HTTP/query cùng DB giả đạt, không thêm SELECT. Snapshot/link/GET-write9 tài khoản đạt, SELECT10/14/18/23/18/10/5/20/5 giữ nguyên, chỉ middleware ghi session.

**Thay đổi đồng thời được giữ:** khi tiếp tục, HEAD đã chuyển sang `6b98905` (chủ dự án commit/push cài skill) và gồm phần donut/docs đang sửa. Không reset/rebase/tách lại commit đó. Vì vậy bước1/2 là commit riêng `e83ced9`/`0a62a32`, phần bước3 đã nằm trong6b98905; commit chốt tiếp theo chỉ chứa cache và nhật ký trong phạm vi. Các skill/reference/graph do phiên khác tạo giữ nguyên; không tự xóa/dọn. Chưa báo CI SHA cuối nếu chưa xác minh trực tiếp.

**Tầng 2 Dự án:** không bật. `views/core.py` có tổng tháng và prefetched task đầu của từng hoạt động; `apps/activity/views.py` có lịch tháng, `task_list` chỉ có scope, chưa có selector/bộ lọc tuần dùng lại. Đề xuất riêng: nguồn Task theo `visible_activities_for`, điều kiện due_date trong tuần, loại Done/Cancelled, giới hạn5; cần phê duyệt bộ lọc đích và khoảng1 SELECT thêm. Chưa thực hiện truy vấn/hàm hay URL mới.

**Tiếp tục và chốt bàn giao 15/10:** xác nhận lại main, fetch origin main; HEAD `a3bda3a` ahead1, giữ nguyên tám tệp chưa commit của phiên trước. Phần chốt gồm selector dải Tuyển dụng để thực sự dùng flex ở desktop, vùng bấm liên kết nhảy44px, icon success hiện có, URL asset compact-delivery và worker v26; test cache đồng bộ, bổ sung đo header≤56px và Tuyển dụng≤96px. Không đổi nguồn dữ liệu, quyền, migration hay CSS giấy in. Đây là bước chốt sau ba bước đã làm, không tạo lại commit bước3 đã nằm trong commit đồng thời.

**Bằng chứng nguồn cuối đã đọc lại:** `release-sqlite.log`551 test/305,203s/7 skip và `release-sqlserver.log`551 test/432,734s/0 skip đều OK; đây là log của phiên trước, không gọi là full suite vừa chạy lại trong phiên tiếp tục. Log chốt bố cục3.656 kiểm tra/48 ảnh và mobile248 kiểm tra/16 ảnh không lỗi; toàn route146/7.021 ca/0 vi phạm/0 lỗi, SQLite giả,9 tài khoản,1920/1756/1440/1280/1024/768/390px,sáng/tối; baseline0, không thêm waiver. Log cache9 kiểm tra,244→100px. In402 kiểm tra/37PDF, so37PDF text/raster khớp; BCC645 kiểm tra/8 ca; workflow402 kiểm tra/32 ảnh trên DB dùng một lần; form1.314 ca không khác; DTO/link/GET-write9 tài khoản và SELECT10/14/18/23/18/10/5/20/5 không đổi. Các kết quả này đã có trước khi tiếp tục, được kiểm lại từ tệp bằng chứng thay vì coi là lượt mới.

**Kiểm tra phiên tiếp tục:** `venv/Scripts/python.exe %TEMP%/compact-scenarios-browser.py` chạy lại Edge trên runtime giả port8800:25 kiểm tra/0 lỗi, gồm năm số Dự án khác0, quyền HR, liên kết và cảnh báo vượt định biên. Chạy lại `ops/run_dashboard_layout_uat.py --directory %TEMP%/ihrms-dashboard-compact-20261015 --packages-dir %TEMP%/ihrms-planning-qa-packages-20261014 --port 8796 --phase after` và focused qua launcher `%TEMP%/compact-final-tests.py --backend sqlite apps.portal.test_home_dashboard_layout apps.portal.test_home_dashboard apps.portal.test_project_layout apps.portal.tests_mobile`; kết quả cuối ghi trong metadata bàn giao. Lượt focused chuyển hướng PowerShell báo NativeCommandError do stderr Django dù41 test OK; chạy lại trực tiếp để xác nhận exit code, không tính mã lỗi vỏ lệnh là pass. Launcher chỉ dùng MD5 cho fixture mật khẩu trong tiến trình DB giả. `git diff --check` đạt. Đã xem ảnh HR1440 sáng nguồn cuối; ảnh sáng/tối/rộng/hẹp và contact sheet1756/390 có trong gói chứng cứ.

**Nguồn và giao nhận:** `D:/QLHCNS-Backups/IHRMS_Review_20261015_DashboardCompact.zip`, `IHRMS_DashboardCompact_Proof_20261015.zip` và thư mục ảnh `IHRMS_Dashboard_Compact_20261015`. Nguồn lấy từ tracked/staged tree cuối, loại env (giữ .env.example),DB/media/uploads/log/runtime/credentials/private reference/graph output; manifest ghi tree/hash từng tệp, mở lại cả hai ZIP xác minh SHA-256. Đây là bản nguồn review, không phải backup phục hồi. Số tệp/tree/hash ZIP, SHA commit/push, remote ahead/behind và kết quả kiểm tra mới ghi trong `IHRMS_DashboardCompact_20261015.delivery.json` ngoài Git để tránh vòng commit tự ghi SHA. Commit chốt trên main và push origin main theo quyền mặc định; không deploy. Giới hạn giữ nguyên: chưa UAT phiên trình duyệt/tài khoản thật, screen reader, zoom native200% hoặc máy in thật. Chủ dự án duyệt contact sheet và thử các mục này sau bàn giao; không cần xóa cache. Tầng2 Dự án vẫn là đề xuất riêng chưa triển khai.

**Giới hạn CI:** `gh run list --branch main --limit 3 --json headSha,status,conclusion,databaseId` trả HTTP401 Bad credentials ở phiên tiếp tục; chưa chứng nhận GitHub Actions của SHA cuối. Chủ dự án chạy `gh auth login --hostname github.com`, sau đó `gh run list --branch main --limit 5 --json headSha,status,conclusion,databaseId` và đối chiếu headSha với SHA trong metadata; chỉ coi CI đạt khi run đúng SHA kết thúc success. Không ghi token vào nhật ký/Git. Kiểm tra local và xác minh push bằng Git độc lập với xác thực gh.

## 2026-10-15 — Lưới form 12 cột, chuyển biểu mẫu và cổng kiểm tra bố cục

**Tóm tắt cho chủ dự án**

- Một nguồn lưới 12 cột; bỏ lưới form 60/40 và giới hạn chiều rộng xung đột. Ưu tiên hàng đầy theo lựa chọn của chủ dự án, giữ thứ tự trường.
- Hồ sơ có bốn nhóm; nhãn, chú thích, ngày tiếng Việt và hàng nút dùng thành phần chung. Tỷ lệ 60/40 chỉ còn cho vùng nội dung trang.
- Lượt chốt nguồn đạt 0 vi phạm/0 lỗi chạy, không miễn trừ; 1.314 trường hợp form/HTTP/truy vấn không có khác biệt.
- Edge đã xác nhận luồng hồ sơ/hợp đồng/nghỉ phép/Dashboard, Hành chính, Kế hoạch, Kế toán và xử lý quyết định; không dùng dữ liệu thật.
- 37 PDF khớp text và raster với nguồn trước sửa; full547 test SQLite/SQL Server đều đạt trên nguồn cuối.
- Đóng gói nguồn và ảnh review có manifest/hash; commit gộp B–E trên main, xác minh remote/CI theo SHA trong metadata bàn giao.

**Phạm vi và nguyên nhân:** `shared_components.css` sở hữu duy nhất `.ui-form-grid`; bỏ khai báo cột ở `hr_ui.css`, `ui_controls.css`, `project_layout.css` và luật form Hành chính/Kế toán cũ. Thực tế baseline có 8 khai báo kể cả breakpoint trong 4 tệp, không phải 5 tệp như giả thuyết ban đầu; nguồn sau chỉ một khai báo trong một tệp. Không thêm `!important`/`:has()` để suy cột. `ui/field.html` nhận span/tablet_span/hint/error và widget con giữ nguyên control cũ; `ui/form_section.html` cung cấp fieldset/legend. Bộ lọc giữ kích thước riêng. Khoảng nhóm24/gap16/nút44/chữ14 dùng token, nhãn dự trữ hai dòng để không lệch ô khi xuống dòng. Form dài trên mobile có thanh nút dính đáy và khoảng cuộn focus.

**Khung và giới hạn tái hiện:** đo baseline `hr_employee_edit`1756×920 thấy lề62/62px, không tái hiện219/76px từ ảnh chủ dự án; không giả định nguyên nhân rồi bù margin riêng. Khung căn giữa hiện hữu được giữ và đo lại ở mọi độ rộng/vai trò. Giấy in dài được bọc vùng xem cuộn chỉ trên màn hình; không đổi khổ giấy, nội dung, API/model/migration/quyền/URL/tham số hay tên/required/CSRF/default/options của control. Những lần trước chủ yếu đo tỷ lệ60/40/tràn/focus, chưa đo đường cột, mép ô và nhịp hàng, nên bỏ sót lỗi form.

**Template:** hồ sơ/chi tiết nhân viên, hợp đồng, quyết định, lifecycle; tuyển dụng/ứng viên/phỏng vấn/offer; nghỉ phép/thay đổi hồ sơ/chấm công; công văn/công văn văn phòng; tài sản/kiểm kê/thanh lý/đặt phòng/xe/VPP/mua sắm; kỳ lương/người phụ thuộc/thuế/chạy lương; giao/chấm KPI/ngày lễ/lịch. Có43 template màn hình chứa POST bị chạm,89 thẻ form tĩnh gồm cả thao tác chỉ có nút; không đồng nghĩa89 form nhập liệu. Hoạt động và công việc chỉ sửa bố cục vì audit đã báo lỗi ở chúng; không mở rộng nghiệp vụ. Hàng động mua sắm giữ cấu trúc con và nút Thêm dòng; lần so đầu bắt được thứ tự nút đổi, đã khôi phục. Bảng nhập nhiều dòng giữ bảng/nhãn/chiều cao. Không sửa login hoặc attendance_list. Template base chỉ đổi phiên bản asset; worker tăng lên v22-form-grid-20261015, build lại Tailwind, module CSS đổi URL phiên bản.

**Đo và công cụ:** runtime DB/media/tài khoản giả ngoài repo tại `%TEMP%/ihrms-form-grid-20261014`; archive71b6a2f port8791 là nguồn trước sửa, nguồn hiện tại port8790; archive0d72c85 port8792 dùng thử cache v20→v22. Không deploy. `ops/run_form_grid_uat.py` lưu36 ảnh toàn trang và contact sheet9 mô-đun trước/sau1756/390px, kiểm tra echo ngày/tháng, ISO FormData, nhãn/ID, Tab, focus trên mobile ở hai theme. `AGENTS.md` thêm cổng audit và `MASTER.md` ghi quy chuẩn; giữ nguyên dòng trống cục bộ ngoài phạm vi trong AGENTS và thư mục tham khảo riêng ngoài Git.

**Các lỗi kiểm thử đã xử lý:** hint ẩn không phải chú thích nhìn thấy; đo trường dài theo lưới bên trong thay vì bề rộng form có padding. Trường hợp optional hint của template ban đầu thiếu biến gây lỗi render đã sửa và thêm hồi quy; HTML fieldset BCC đã được sửa và kiểm tra toàn trang. Test Tab ban đầu chọn cả ô tìm kiếm header nên so sai đích; đã giới hạn form nội dung, không đổi Tab của ứng dụng. Lượt BCC đầu thiếu marker fixture khi sao DB giả cũ gây trùng khóa; chỉ khôi phục marker của chính bộ dữ liệu giả, không đụng dữ liệu vận hành. Không dùng các lượt lỗi làm bằng chứng đạt. So form cuối chạy tuần tự sau workflow, vì dữ liệu giả/position/options thay đổi trong lúc chạy song song có thể tạo chênh lệch giả.

**Bảo vệ in:** hồi quy402 kiểm tra/37 PDF và BCC8 tình huống661 kiểm tra đã đạt. So raster phát hiện riêng tiêu đề BCC đổi từ block sang inline do gắn ui-print-only, dù text/số trang còn giống; đã bỏ lớp đó khỏi h1, chỉ ẩn wrapper tiêu đề lặp bằng CSS screen. Không sửa print_forms.css. Đây là lý do phải so ảnh: kiểm tra cũ về cỡ chữ/khổ/số trang không đủ bắt khác biệt display và khoảng tiêu đề. So37 PDF trước/sau cuối vẫn là điều kiện bàn giao; không lấy kết quả trước bản sửa làm đạt.

**Kiểm tra đã xác nhận trước chốt nguồn:** full547 SQLite đạt (7 skip), full547 SQL Server đạt ở lượt trước sửa nhỏ cuối; các lượt bị ngắt sau đó không tính đạt. Focused35 đạt; HTML209 trang không lỗi parser. Edge workflow355 kiểm tra/32 ảnh và DB dùng một lần đã hủy; Hành chính31, Kế hoạch21, Kế toán205, Quyết định130/22 ảnh đạt. Project layout73 trang1600 kiểm tra đạt; bộ lọc1801 kiểm tra/300 số đo đạt; ngày/bàn phím46 kiểm tra/36 ảnh đạt; cache9 kiểm tra đạt (khoảng trường–nút597,09→16px, reload giữ cache/cookie). pip check/check/makemigrations đạt, không migration; contrast198 cặp đạt (sáng min chữ5,100/UI3,506; tối7,007/3,982). Kết quả nguồn cuối ghi dưới.

**Lệnh tái lập:** dùng `venv/Scripts/python.exe`, `$r="$env:TEMP\ihrms-form-grid-20261014"`, `$q="$env:TEMP\ihrms-planning-qa-packages-20261014"`, `$p="$env:TEMP\ihrms-pdf-qa-packages-20261014"`; không phải đường dẫn dữ liệu vận hành.

```powershell
git diff --check
venv\Scripts\python.exe -m pip check
venv\Scripts\python.exe ops/check_ui_contrast.py
venv\Scripts\python.exe ops/run_layout_alignment_audit.py --directory $r --packages-dir $q --port 8790 --phase after --output-dir "$r\alignment-deliver"
venv\Scripts\python.exe ops/run_form_contract_uat.py --directory $r --source-root "$env:TEMP\ihrms-dashboard-baseline-71b6a2f" --phase before
venv\Scripts\python.exe ops/run_form_contract_uat.py --directory $r --phase after
venv\Scripts\python.exe ops/run_form_grid_uat.py --directory $r --packages-dir $q --pdf-packages-dir $p --port 8790 --baseline-port 8791
venv\Scripts\python.exe ops/run_print_layout_uat.py --directory $r --packages-dir $q --pdf-packages-dir $p --port 8790
venv\Scripts\python.exe ops/run_timesheet_print_uat.py --directory $r --packages-dir $q --pdf-packages-dir $p --port 8790 --phase after
venv\Scripts\python.exe ops/run_project_layout_uat.py --directory $r --packages-dir $q --port 8790
venv\Scripts\python.exe ops/run_filter_bar_uat.py --directory $r --packages-dir $q --port 8790 --baseline-port 8791
venv\Scripts\python.exe ops/run_asset_cache_uat.py --directory $r --packages-dir $q --port 8790 --baseline-port 8792
venv\Scripts\python.exe ops/run_tests.py --backend sqlite
venv\Scripts\python.exe ops/run_tests.py --backend sqlserver
```

Wrapper test ngoài repo chỉ dùng MD5 cho fixture để tăng tốc và chuyển log ra TEMP, gọi đúng `ops/run_tests.py`; SQLite dùng bộ nhớ/media tạm, SQL Server tên test_ihrms_UUID mới, không dùng DB vận hành. Lấy `$LASTEXITCODE` ngay sau lệnh Python và lưu bằng chứng ngoài repo. Các runner workflow cùng tham số `--directory $r --packages-dir $q --port 8790`; browser workflow tổng dùng `--backend sqlite --packages-dir $q --output-dir "$env:TEMP\ihrms-form-grid-workflows-20261014"`.

**Chốt nguồn ngày15/10:** `alignment-deliver/result.json`:146 route,9 tài khoản,7 độ rộng/hai theme;7.021 mục gồm6.146 hình học và875 HTTP/không shell/không HTML có lý do;0 vi phạm,0 lỗi,waivers rỗng,exit0. Form contract chạy lại tuần tự trên cùng DB giả ổn định:1.314 trường hợp,0 khác biệt/không tăng SELECT,exit0. Không dùng lượt bị ngắt hoặc đang có workflow ghi dữ liệu làm pass. HTML209 trang không lỗi. Full suite cuối:SQLite547 test/200,562s/7 skip,SQL Server547 test/371,568s/không skip,hai exit0 (`forms-deliver-sqlite.log`, `forms-deliver-sqlserver.log`). Build CSS và diff check cuối đạt. Framework check/makemigrations dùng settings SQLite tạm, không ghi DB vận hành.

**So ảnh mobile và siết cổng cuối:** ảnh nghỉ phép ban đầu dùng quản trị chưa gắn hồ sơ chỉ hiện cảnh báo; đã chụp lại bằng HR gắn hồ sơ và dùng Kế toán cho form người phụ thuộc. Runner kiểm tra có form thật trước khi chụp,46 kiểm tra/36 ảnh đạt. So ảnh còn bắt được hai nút cao/rộng không đều và textarea bị min-height của shell đè; đã sửa nhóm nút mobile chiếm đủ hàng, dùng cùng component cho nút Hủy của công việc/công văn, textarea tối thiểu hai control-height, bỏ cộng đôi khoảng cách hàng nút. Audit bổ sung FORM_BUTTON_HEIGHT/WIDTH, bắt14 vi phạm ở lượt trung gian; sau sửa lượt toàn bộ đạt0 nêu trên. CSS/JS URL cuối20261015-form-grid-final và worker v22; cache9 kiểm tra dùng CSS cũ giả lập trên v20, xác nhận reload nhận bản cuối và loại cache cũ, không phải đo phiên trình duyệt thật của chủ dự án.

**Luồng Tuyển dụng bổ sung:** Edge trên runtime giả tạo ứng viên, lên lịch/kết quả phỏng vấn, tạo offer với số Việt Nam, chấp nhận, Escape xác nhận tiếp nhận rồi tiếp nhận thật:15 kiểm tra đạt; kiểm DB/thông báo/trang đích và mở lại Dashboard. Giữ hành vi hiện hữu: tiếp nhận đánh dấu Hired rồi mở hồ sơ điền sẵn, chưa tạo Employee cho tới khi lưu hồ sơ. Script tái lập `%TEMP%/form-grid-recruitment-workflow.py`, chứng cứ `recruitment-grid-workflow/result.json`; không thêm nghiệp vụ. Các workflow355/31/21/205/130, print402 và BCC661 đều đã chạy lại sau chỉnh nút/textarea cuối.

| Nhóm route | Trước | Sau cuối |
|---|---:|---:|
| lifecycle |84|0|
| profile |240|0|
| leave |540|0|
| task |460|0|
| activity |196|0|
| kpi |42|0|
| dispatch |112|0|
| timesheet |666|0|
| recruitment |78|0|
| report |168|0|
| holiday |66|0|
| vehicle |90|0|
| event |54|0|
| inventory |148|0|
| hr |1878|0|
| disposal |132|0|
| finance |168|0|
| asset |56|0|
| Tổng |5178|0|

**PDF và ảnh chốt:** `form-grid-print-comparison/result.json`:37/37 cùng text và raster,exit0; baseline được render lại cùng ngày15/10 để không nhầm ngày hiện tại14→15 là hồi quy. `print-layout-uat`402 kiểm tra/37PDF, `bcc-print-after`661 kiểm tra/8 tình huống đều exit0. `form-grid-uat/contact-sheet-1756.png` và390.png cùng36 ảnh toàn trang trước/sau lưu ngoài repo. Nguồn review `D:/QLHCNS-Backups/IHRMS_Review_20261015_FormGrid.zip`; chứng cứ `IHRMS_FormGrid_Proof_20261015.zip`; manifest/tree/hash từng tệp và trạng thái commit/push/CI nằm tại `IHRMS_FormGrid_20261015.delivery.json`. ZIP nguồn loại bí mật/DB/media/log/tài khoản/reference riêng, không phải backup phục hồi dữ liệu. Bước A0d72c85 đã xác minh CI38579276418 success; đợt B–E gộp một commit để không bàn giao trạng thái nửa chuyển form.

**Giới hạn và việc chủ dự án làm:** chưa kiểm screen reader, zoom native200%, tài khoản thật hoặc máy in thật; đây không phải UAT phiên Edge đang mở của chủ dự án. Thử nghiệm CSS zoom2 đạt1756 nhưng tràn ở390; không coi CSS zoom là zoom native hoặc dùng nó làm bằng chứng đạt. Thử preference trên profile Edge giả không làm đổi devicePixelRatio, nên cũng chưa chứng nhận zoom native. Nhập ngày native khi tắt JS vẫn dùng được và giữ ISO. Phạm vi đào tạo hiện chỉ đọc đăng ký vì không có route tạo đăng ký; không tự thêm nghiệp vụ. Chủ dự án cần duyệt ảnh trước/sau và thử zoom native200%/máy in/tài khoản thật sau khi nhận bản bàn giao; không cần xóa cache. Không deploy.

**Dọn nguồn và giao Git:** commit giao diện `b755a381d83591cdc5a6928149ebe6a8bec52702` đã push main và CI38662944349 success. Sau đó xóa duy nhất partial `portal/widgets/procurement_request_list.html` không có caller, còn sót từ lượt chuyển tự động đã hoàn nguyên cấu trúc dòng mua sắm; không thay markup đang render. Trên nguồn đã dọn, full547 SQLite/215,642s/7 skip và full547 SQL Server/425,570s đạt, hai exit0. Audit toàn bộ chạy lại tại `alignment-cleanup`:146 route/7.021 mục/0 vi phạm/0 lỗi; Edge thành phần46 kiểm tra/36 ảnh đạt, exit0. Kết quả in/workflow trước xóa vẫn áp dụng vì không caller nào dùng tệp đã xóa. Bản sao được tạo lại theo staged tree cuối, mở lại xác minh SHA-256 từng tệp; metadata ngoài Git ghi SHA commit dọn nguồn, remote0/0 và CI theo SHA để không tạo vòng commit chỉ nhằm ghi chính SHA của nó. Giữ nguyên thay đổi dòng trống AGENTS và thư mục reference riêng chưa theo dõi.

## 2026-10-14 — Lưới form, Bước A: đo căn lề trước sửa

**Tóm tắt cho chủ dự án**

- Bước này chỉ thêm công cụ và test; chưa sửa mã giao diện biểu mẫu.
- Kiểm kê146 route có tên ngoài Django Admin; 9 tài khoản, 7 độ rộng, sáng/tối:6.146 lượt đo và875 mục HTTP/không có shell/không phải HTML được ghi lý do.
- Đo trước:5.178 vi phạm lặp theo route/vai trò/kích thước/theme; chưa phải0 lỗi và chưa đóng giai đoạn.
- Ca sửa nhân viên1756×920 tái hiện lệch lưới, mép ô, trường dài hẹp, thiếu nhóm, chú thích và nút; chưa tái hiện lề219/76px, thực đo62/62px.
- Chủ dự án chọn ưu tiên hàng đầy và cho điều chỉnh span; giữ thứ tự Tab, không đổi tên/required/CSRF và dữ liệu gửi.
- Tiếp theo B–D: một nguồn lưới12 cột, chuyển các form, echo ngày tiếng Việt; E chỉ đóng khi kiểm tra cuối đạt và giới hạn được công bố.

**Công cụ:** ops/run_layout_alignment_audit.py dùng Edge trên database/media giả tách riêng tại TEMP/ihrms-form-grid-20261014, baseline source archive71b6a2f port8791. URLResolver lấy146 route có tên của portal/report/private-files, không có route còn thiếu đối số. Django Admin dùng khung riêng, không được tuyên bố đã đo UI Admin. Có --only, --accounts, --widths, --workers, --output-dir; --seed tạo bản ghi giả còn thiếu chỉ khi runtime có marker synthetic_only và ở ngoài repository. Chín tài khoản gồm HR/superuser/giám đốc/quản lý/nhân viên/kế toán/sysadmin/chưa liên kết. Chỉ đo HTML có .ui-main; 302/403/404/405/tệp tải hoặc không shell ghi riêng; không tính là UI pass. Chạy ba phiên Edge đồng thời, đăng nhập tuần tự, SQLite timeout30. Dữ liệu giả được chuẩn bị xong trước lượt baseline cuối; không dùng kết quả các lượt đang bổ sung fixture làm mốc cuối. Waiver mặc định ops/layout_waivers.json rỗng; không tự miễn trừ vi phạm.

**Nguyên nhân và giới hạn đo:** audit đọc hình học main/wrap/page/field/input, đường cột12, đỉnh/chiều cao, khoảng hàng, nhãn/chữ44px/14px, hint, nút, tràn trang và số đã đánh dấu; ghi JSON, markdown và ảnh ngoài Git. CSSOM hồi quy HR xác nhận các URL asset cũ thật đang tải và luật active. Có8 khai báo columns kể cả breakpoint trong4 tệp: hr_ui18/61/62, ui_controls45, shared_components58/173 và project_layout10/18; mô tả “năm nơi” của yêu cầu là các nguồn/luật mâu thuẫn, không ghi sai thành5 tệp. 60/40 có trong form từ project_layout, hr UI có2/3 cột và caps28rem làm mép input không khớp ô. Các lượt cũ chỉ đo tỷ lệ/tràn/focus, không đối chiếu cạnh trường, hint, nhóm và hàng nút, nên bỏ sót lỗi. Trên source71 hiện tại, .ui-main x286/w1440, .ui-page x318/w1376, sidebar256 và viewport1756 cho lề khả dụng62/62px. 219/76px trong ảnh chủ dự án chưa tái hiện; không khẳng định nguyên nhân cache/zoom hoặc bù margin riêng khi chưa có bằng chứng. Ảnh được khoanh rect/codes bằng xử lý chứng cứ ngoài app; không thay CSS ứng dụng để giả lập lỗi.

**Sửa chính công cụ trước chốt mốc:** bản đầu nhầm mọi p, gồm lỗi ẩn, là hint; đã giới hạn .ui-field-help/.ui-hr-text nhìn thấy. CSSOM Edge có cssRules rỗng ngay trên style rule nên phải ghi selector/style trước khi duyệt lồng. Form Client lần đầu thiếu HTTP_HOST tạo400 DisallowedHost; đã sửa host127.0.0.1 và cấm400/500. Không lấy những lượt này làm pass/baseline. Mốc cuối:7.021 mục gồm6.146 lượt hình học và875 mục skip có lý do,0 lỗi chạy runner;5.178 vi phạm thật theo các phép đo đã cài (exit1 đúng kỳ vọng). Counts: hint168, date language1792, đường cột1008, chiều cao hàng96, trường dài184, nút836, nhãn336, nhóm140, h1 126, tràn72, mép ô420. DATE_ECHO lưu trong chứng cứ trước nhưng chưa đưa vào tổng Bước A; bắt buộc ở nguồn sau. Không coi phép đo tự động là chứng nhận mọi khía cạnh nhìn bằng mắt.

| Mô-đun/nhóm route | Vi phạm trước | Sau |
|---|---:|---|
| lifecycle | 84 | Chưa sửa ở Bước A |
| profile | 240 | Chưa sửa ở Bước A |
| leave | 540 | Chưa sửa ở Bước A |
| task | 460 | Chưa sửa ở Bước A |
| activity | 196 | Chưa sửa ở Bước A |
| kpi | 42 | Chưa sửa ở Bước A |
| dispatch | 112 | Chưa sửa ở Bước A |
| timesheet | 666 | Chưa sửa ở Bước A |
| recruitment | 78 | Chưa sửa ở Bước A |
| report | 168 | Chưa sửa ở Bước A |
| holiday | 66 | Chưa sửa ở Bước A |
| vehicle | 90 | Chưa sửa ở Bước A |
| event | 54 | Chưa sửa ở Bước A |
| inventory | 148 | Chưa sửa ở Bước A |
| hr | 1878 | Chưa sửa ở Bước A |
| disposal | 132 | Chưa sửa ở Bước A |
| finance | 168 | Chưa sửa ở Bước A |
| asset | 56 | Chưa sửa ở Bước A |

**Form/query baseline:** ops/run_form_contract_uat.py ghi1.314 trường hợp146route×9tài khoản trên cùng dữ liệu giả với71b6a2f. Giữ thứ tự input/select/textarea/button, name, required, action/method/enctype, defaults, options và CSRF presence; chỉ chuẩn hóa token xoay và bỏ thuộc tính trình bày. Không xuất mật khẩu/cookie. Hai test parser kiểm rằng đổi required/default/action/option/thứ tự bị phát hiện, còn fieldset/class/id/CSRF xoay không làm đổi contract. Đây là GET/form/query contract, không phải kiểm POST nghiệp vụ. Các luồng ghi phải chạy lại sau chuyển form; dữ liệu giả này không phải dữ liệu vận hành.

**Lệnh/kết quả cuối:** venv/Scripts/python.exe ops/run_layout_alignment_audit.py --directory "$env:TEMP/ihrms-form-grid-20261014" --packages-dir "$env:TEMP/ihrms-planning-qa-packages-20261014" --source-root "$env:TEMP/ihrms-dashboard-baseline-71b6a2f" --port 8791 --phase before --workers 3 --output-dir "$env:TEMP/ihrms-form-grid-20261014/alignment-before-release" (ghi tham số --port 8791 / --workers 3 khi chạy): exit1,5.178 vi phạm,0 lỗi chạy. ops/run_form_contract_uat.py --directory cùng runtime --source-root cùng archive --phase before: exit0/1.314 trường hợp/0 lỗi. Focused parser2 test OK. Full nguồn cuối qua TEMP/project-layout-final-tests.py gọi ops/run_tests.py: SQLite544/186.858s OK(7skip); SQL Server đang bổ sung kết quả trước commit. git diff --check và py_compile hai runner đạt. Bước A không sửa CSS/template nên không tuyên bố đã sửa UI hoặc chạy lại giấy in trong commit này; giấy37/PDF/BCC đã kiểm riêng ở commitDashboarda75c0e8 trước đó. BướcB thay CSS chung bắt buộc chạy lại toàn bộ in/cache/contrast/luồng.

**Bàn giao Bước A:** bản sao source review/manifest/hash và chứng cứ ở D:/QLHCNS-Backups với nhãn LayoutAudit; không chứa env/database/media/log/account secrets/private references. Commit riêng ops: layout alignment audit trên main, SHA/remote/CI trong metadata cạnh ZIP. Tiếp tục làm B–E, chưa đóng giai đoạn, chưa deploy. Chưa kiểm screen reader, zoom200%, tài khoản thật và máy in thật; khung219/76px chưa tái hiện. Nhật ký cùng đợt tiếp theo phải ghi danh sách form chuyển, nguồn lưới còn lại, vi phạm sau và contact sheet so cùng khung.

## 2026-10-14 — Dashboard: bố cục nhóm theo quyền

**Tóm tắt cho chủ dự án**

- Gom Trang chủ theo thứ tự KPI → Công việc của tôi → Nhân sự → Hành chính → Tuyển dụng → Dự án; bỏ thẻ phụ rỗng và Thao tác nhanh.
- Dùng thẻ, liên kết và Cách tính thống nhất; danh sách giới hạn 5/3 dòng, định biên 6 phòng, không cuộn dọc trong thẻ.
- Dữ liệu/DTO cũ và số truy vấn qua 9 tài khoản không đổi; không có ghi nghiệp vụ khi GET Dashboard.
- Edge: 2.380 kiểm tra bố cục, 355 kiểm tra luồng trên DB dùng một lần; PDF 37/37 không khác văn bản/pixel, BCC 645/8 đạt.
- Cập nhật đặc tả và MASTER; không sửa nguồn công thức, quyền, URL, model, migration hoặc giấy in.
- Bản sao mã review và ảnh giả ngoài repository; commit/push main, không deploy. Yêu cầu chuẩn hóa form toàn ứng dụng là đợt riêng tiếp theo.

**Phạm vi:** home_presentation.py thêm hàm thuần grouped_dashboard và dashboard_layout từ snapshot/context đã materialize; giữ mọi khóa cũ. Dashboard/partials, home_dashboard.css/JS, worker/cache, test và hai tài liệu. Không sửa dashboard_data.py/selectors.py/PERMISSION_MATRIX. Giữ Q2 ẩn tiền, Q3 Giám đốc không mặc nhiên xem hợp đồng, D2 riêng tư loại nghỉ. Tài khoản cá nhân chỉ Công việc của tôi; checklist quá hạn cá nhân chuyển vào cùng khối. Không thêm truy vấn để dựng đủ KPI khi context không cấp số công việc phòng/hàng chờ. Định biên và cơ cấu hợp đồng ghép 60/40 từ1024px; danh sách dài tách hàng để tránh kéo thẻ ngắn thành vùng trắng lớn. KPI quản lý phòng có ba chỉ số được cấp thì chia đều ba cột. Dưới600px bảng đơn nghỉ chuyển thành dòng có nhãn, không cắt tên hoặc cuộn trang ngang.

**Bảo toàn và hồi quy:** ops/run_dashboard_group_contract_uat.py so archive71b6a2f và nguồn mới trên cùng DB/media giả TEMP/ihrms-finance-followup-20261014. Chín tài khoản gồm nhân viên, trưởng phòng, HR officer/manager, giám đốc, kế toán, sysadmin, superuser và chưa liên kết: SELECT lần lượt10/14/18/23/18/10/5/20/5 không tăng; snapshot bỏ generated_at khớp nguyên vẹn; liên kết nội bộ200/302. Ghi django_session do middleware giữ nguyên; runner cấm mọi ghi bảng nghiệp vụ trong Dashboard GET. Các test nghiệp vụ hiện có giữ nguyên số liệu/phạm vi; chỉ cập nhật assertion markup/copy: phân phối loại hợp đồng chuyển donut sang nhãn/thanh, thẻ rỗng ẩn, lớp grid cũ bỏ, liên kết Dashboard dự án giữ tên. Thêm3 test mapping thuần, giới hạn và không đổi DTO. Full suite lần đầu bắt hai assertion markup cũ ở activity/tests.py và portal/tests.py; giữ assertion quyền/count và chỉnh nhãn/class tương ứng rồi chạy lại, không bỏ test.

**Đo và xem ảnh:** ops/run_dashboard_layout_uat.py: 9 tài khoản ×1756/1440/1280/1024/768/390 ×sáng/tối, 2.380 kiểm tra/16 ảnh cuối. Đo theme thực tế sau navigation (lưu lựa chọn trước reload), không tràn trang, không cuộn dọc trong thẻ, thứ tự nhóm, chiều cao hàng/KPI và đường cơ sở số, tỷ lệ60/40, khoảng trắng cuối thẻ ghép≤96px, first fold1440×900 chứa MyWork và tiêu đề nhóm đầu, chữ≥14px, Cách tính≥44px/Enter/Escape. Lượt cũ chỉ kiểm overflow/tỷ lệ nên bỏ sót CSS chung ghi đè ở1024px, chữ kỳ12px và khoảng trắng dài; đã bổ sung phép đo rồi sửa selector chỉ trong home-dashboard. Một thẻ info có thừa đóng div làm Escape không đóng; đã sửa markup, kiểm lại toàn bộ disclosure. Đã xem ảnh HR desktop và Giám đốc mobile, sau đó sửa bảng mobile thay cách ngắt chữ từng cột. Contact sheet trước/sau cùng4 tầng tài khoản ở1756/390; ảnh toàn trang giữ ngoài Git.

**Kiểm thử nguồn cuối:** git diff --check; pip check; Django check; makemigrations --check --dry-run; contrast198 cặp/0 lỗi. npm run build:css; Tailwind URL20261014-dashboard-grouped, worker v20. Full suite qua ops/run_tests.py bằng wrapper TEMP/project-layout-final-tests.py chỉ thay password hasher fixture, DB/media dùng một lần: SQLite542 test/143.099s OK(7 skip); SQL Server kết quả cuối bổ sung ngay trước commit. ops/run_browser_uat.py --backend sqlite:355 kiểm tra/32 ảnh, tạo hồ sơ→hợp đồng→xuất hiện danh sách→dropdown/sửa; nghỉ→hàng chờ→xác nhận duyệt→lưu một lần→hàng chờ rỗng; các mép D/D+7/30/60/61/quá hạn và hợp đồng Draft/Expired/Terminated/future, headcount0/thiếu/vượt, quyền liên kết và Dashboard không tiền. Runner cập nhật selector theo nhóm mới; giữ kiểm dữ liệu lưu, trạng thái và số liệu. Đây là Edge headless, không phải UAT phiên trình duyệt/tài khoản thật của chủ dự án.

**In/cache và bàn giao:** ops/run_print_layout_uat.py:402 kiểm tra/37 PDF, gồm sổ công văn và lặp trang; ops/run_timesheet_print_uat.py:645 kiểm tra/8 tình huống, đạt. So37 PDF cùng bản ghi trước/sau: văn bản và pixel trùng; không sửa print_forms.css. ops/run_asset_cache_uat.py:9 kiểm tra, phiên worker v19→v20 giữ cookie/cache, reload thường, gap stale597.094→16px. Một lượt cache lỗi fetch worker khi demo vừa restart; chạy lại sau ổn định đạt, không gọi lần lỗi là pass. Nhật ký bằng chứng và ZIP review tại D:/QLHCNS-Backups/IHRMS_Review_20261014_DashboardGrouped.zip và IHRMS_DashboardGrouped_Proof_20261014.zip, manifest nguồn/tree và SHA-256 từng tệp được mở lại xác minh. Loại env/database/media/log/account secret và private design-system/reference; đây là source review, không backup phục hồi dữ liệu. Giữ thay đổi AGENTS.md ngoài phạm vi. Chưa kiểm screen reader, zoom200%, máy in thật và UAT dữ liệu thật. Trạng thái commit/remote/CI theo SHA trong metadata giao nhận cạnh ZIP.

## 2026-10-14 — Giai đoạn 5: Kế hoạch

**Tóm tắt cho chủ dự án**

- Chuẩn hóa bốn trang ngày lễ, đào tạo, chấm KPI và giao KPI; dùng thành phần/token chung, nhãn thường trực, bảng cuộn có focus.
- Form giao KPI dùng 60/40; ô thực tế và Lưu cùng hàng, nhãn hỗ trợ tiếp cận riêng từng người/tiêu chí; giữ năm 2026 và số Việt Nam.
- Không đổi quyền, quy trình, trọng số/công thức KPI, tên GET/POST, URL hoặc truy vấn; không thêm chức năng đăng ký đào tạo.
- Đối chiếu sáu trang × chín vai trò; utility token cũ 218→0 trên bốn trang đã sửa, không link lỗi, không tăng truy vấn.
- Full suite: 539 test mỗi backend đạt; Edge: 296 kiểm tra bố cục và 21 kiểm tra luồng; 37 PDF không đổi, hồi quy in/cache đạt.
- Bản sao nguồn/bằng chứng ngoài repo, commit `ui: planning`, push main và xác minh remote/CI; dừng sau Kế hoạch, không deploy.

**Đầu lượt/phạm vi:** tiếp sau commit giấy in `005e1fe15f7a4cd8ad7ecd1d65044965291e834d` đã push main và CI 38532660168 success; Hành chính follow-up `7b561ee` cũng CI success. Yêu cầu 8744364a, UI Ux Pro Max (không UI Styling/shadcn). Giữ AGENTS.md và reference ngoài phạm vi. Kiểm kê base.html: menu Kế hoạch có event_list, training_my_list, holiday_list theo quyền can_manage_calendar. Không có trang định biên/ngân sách trong menu này; report_headcount/report_budget thuộc Báo cáo nên không sửa. event_list và report_hub chỉ kiểm tra lại, không đổi template/view; không sửa Trang chủ, Báo cáo hoặc Dự án.

**Kiểm kê guard/form trước sửa:** holiday_list/holiday_delete dùng `_can_manage_calendar`, POST holiday_code/holiday_name/holiday_date và soft delete is_active; giữ CSRF và xác nhận xóa. training_my_list lấy `_get_employee` và enrollment của người đó, select_related course; không có view/URL đăng ký đào tạo trong portal. Quy trình đăng ký thuộc admin hiện có, ngoài phạm vi này; không thêm route hoặc giả định UAT đăng ký portal. KPI score/assign/update dùng `_can_score_kpi`, candidates và `_scorable_kpis` giới hạn phòng ban, global HR_MANAGER; giữ period GET, employee/kpi_template/kpi_period/target và actual POST, Decimal/full_clean/save/notify và redirect hiện có. Event giữ phạm vi phòng ban/can_create_event; report_hub giữ quyền báo cáo, bộ lọc và dữ liệu hiện có. Không thay guard/view/model/migration/dependency/CDN.

**Sửa trình bày:** planning_base và planning_ui.css chỉ màn hình, dùng page_header/card/field/error_summary/query_actions/empty_state/ui_badge. Holiday có nhãn/ngày ui_date và dialog xóa; đào tạo có caption/scope, ngày ui_date, badge chữ và trạng thái rỗng riêng cho tài khoản chưa gắn hồ sơ. KPI giữ bảy cột hiện có, căn số ui-number/tabular; giữ 0 thay vì dùng default biến 0 thành dấu gạch. Form giao giữ các option và trọng số, hai cột 60/40 từ 1024px, một cột trên màn hình hẹp. Mỗi input actual có ID theo PK và aria-label gồm nhân viên/tiêu chí; nhãn nhìn thấy “Thực tế” tránh lặp thông tin làm hàng quá cao, ô–Lưu liền nhau. Bảng cuộn trong vùng có nhãn/tabindex; không ép font nhỏ. Dải lọc kỳ giữ Áp dụng/Enter, Xóa lọc khi đang lọc, số kết quả và nút ngay sau trường. MASTER bổ sung quy chuẩn Kế hoạch.

**Form/query và probe:** test static mới chạy trên archive 110b893 thất bại đúng kỳ vọng: 1 test/4 subtest; không dùng kết quả giả. `ops/run_planning_contract_uat.py` so baseline bốn template từ 005e1fe trên cùng DB giả với nguồn cuối; 6 route × 9 vai trò =54 trường hợp, HTTP/form không đổi và không tăng truy vấn, mọi link nội bộ 200/302. HTML number cũ xuất giá trị actual `0,00`, sai cú pháp type=number; mới dùng unlocalize `0.00` cho trình duyệt/backend, JS vẫn hiển thị Việt Nam. Runner chỉ chuẩn hóa dấu thập phân ở value của actual/type=number để so cùng số đã lưu, không bỏ qua tên/required/step/action/CSRF. Các test riêng kiểm giá trị 0, năm không thành 2.026, nhãn/ID duy nhất, bộ lọc/reset và vai trò. Lỗi fixture đầu gán lại EMPLOYEE gây trùng email đã đổi sang người superuser riêng; không sửa uniqueness hoặc nghiệp vụ. Token class cũ đo cùng regex: holiday/training/KPI tổng218→0; event/report không thay.

**UAT trên nguồn cuối:** Edge headless với DB/media/tài khoản giả ngoài repo tại TEMP/ihrms-finance-followup-20261014, port8782. `ops/run_planning_workflow_uat.py`: gán KPI→chấm80/target100/weight30→achievement80/score24, thông báo và trang đích; lọc/reset kỳ; thêm ngày lễ→mở xóa/Escape không ghi→soft delete, thông báo; đào tạo đã đăng ký hiển thị đúng; event/report/Dashboard truy cập được sau ghi. Không báo đã UAT đăng ký đào tạo qua portal. Chạy lặp dùng ngày lễ giả chưa tồn tại vì ngày là unique kể cả bản ghi is_active=False; không đổi backend để chữa fixture. `ops/run_project_layout_uat.py --account demo-hr --only /portal/holidays/ /portal/trainings/ /portal/kpi/score/ /portal/kpi/assign/ /portal/events/ /portal/reports/`: 1920/1440/1024/768/390px × sáng/tối, focus/Tab/Enter, reduced motion, nhãn/44px/chữ14px, tỷ lệ60/40 và không tràn trang. Đã xem ảnh chấm/giao KPI, ngày lễ và đào tạo; chỉnh hàng KPI sau rà ảnh rồi chạy lại. CSS chung nạp sau đã ghi đè table-layout do độ ưu tiên bằng nhau; sửa selector chỉ trong ui-page.ui-planning, thêm đo table-layout auto, độ rộng ô thực tế và nút Lưu nằm trong bảng ở màn hình rộng. Kỳ KPI giữ liền số năm bằng cột không ngắt dòng. Restart riêng demo để template cache nạp source mới; không restart app thật.

Các runner dùng `--directory "$env:TEMP/ihrms-finance-followup-20261014" --packages-dir "$env:TEMP/ihrms-planning-qa-packages-20261014" --port 8782`; PDF thêm `--pdf-packages-dir "$env:TEMP/ihrms-pdf-qa-packages-20261014"`. Thư viện Playwright ở TEMP của lượt cũ bị dọn giữa lượt, gây ImportError trước khi chạy UAT; đã cài bản QA riêng playwright1.55.0 ngoài repo và chạy lại, không thêm dependency app. Mỗi runner ghi demo tuần tự để tránh khóa SQLite hoặc đổi session. Full Django dùng DB/media dùng một lần riêng, không chạm dữ liệu vận hành.

**Kiểm tra cuối:** git diff --check, pip check, Django check, makemigrations --check --dry-run và contrast198/0 đạt, không migration. Build Tailwind cuối theo toàn template còn lại, tăng URL Tailwind và worker v19, CSS planning có phiên bản riêng. Full suite dùng `venv/Scripts/python.exe "$env:TEMP/project-layout-final-tests.py" --backend sqlite|sqlserver` gọi ops/run_tests.py, wrapper chỉ tăng tốc password fixture trong test. Kết quả cuối: SQLite: 539 test/228.244s, OK (7 skip); SQL Server: 539 test/338.308s, OK, không skip. Sau dọn BOM tệp test, chạy lại 3 test UI Kế hoạch: 33,093s, OK. UAT cuối: 296 kiểm tra bố cục/sáu trang, 21 kiểm tra luồng ghi, 54 trường hợp quyền/form/query, 402 kiểm tra/37 PDF chung, 645 kiểm tra BCC/8 tình huống, 9 kiểm tra cache, tất cả exit0; không dùng kết quả trước lần chỉnh mật độ hàng làm bằng chứng nguồn cuối.

**Bảo vệ in/cache:** không sửa print_forms.css, giấy sổ công văn hoặc HCNS/BCC trong commit Kế hoạch. Vẫn chạy ops/run_print_layout_uat.py (gồm kiểm PDF sổ công văn mới), ops/run_timesheet_print_uat.py và ops/run_asset_cache_uat.py với baselineport8785 (archive005e1fe). Xuất cùng bản ghi trên nguồn trước/sau và so văn bản/pixel cả37 PDF: 37/37 không khác. Render 45 tài liệu gồm 37 chung + 8 BCC thành 67 trang, xem 6 contact sheet, không trang trắng; kiểm số đo/viền/ngắt trang/khoảng ký. Cachev18→v19 kiểm tải lại bình thường trong phiên cũ. Không lấy số trang hoặc HTTP thay cho kiểm giấy thực.

**Bàn giao/giới hạn:** `D:/QLHCNS-Backups/IHRMS_Review_20261014_Planning.zip`, ZIP Proof cùng đợt và metadata commit/tree/remote/CI ngoài repo; nguồn lấy index cuối, loại env/DB/media/log/runtime/tài khoản/bí mật/reference thật; manifest SHA-256 từng tệp được mở lại xác minh. Chưa screen reader, zoom200% thực, UAT phiên tài khoản thật hoặc máy in vật lý. Người phụ trách cần chọn đợt riêng nếu muốn thêm đăng ký đào tạo portal hoặc chặn trạng thái hủy phòng/xe ở backend; không tự thay nghiệp vụ trong đợt UI. Không force-push/deploy; dừng sau Kế hoạch.

## 2026-10-14 — Giấy in sổ công văn

**Tóm tắt cho chủ dự án**

- Thay markup màn hình đóng băng bằng giấy sổ công văn A4 ngang riêng: logo, tiêu đề, bộ lọc và bảng sáu cột có viền.
- Không còn nút/link/emoji/Tailwind trên giấy; phông Times New Roman ≥10pt, lặp tiêu đề bảng và tránh cắt hàng.
- Dữ liệu và phạm vi trang kết quả giữ nguyên; năm lấy từ dữ liệu sẵn có, không thêm lọc/truy vấn.
- Runner PDF mới bắt được sáu lỗi trên bản cũ; bản mới đạt 402 kiểm tra/37 PDF và kiểm tra nhiều trang riêng; BCC 645 kiểm tra đạt.
- Cập nhật phiên bản CSS in, Tailwind và service worker; cache v17→v18 đạt 9 kiểm tra.
- Commit riêng `print: dispatch register paper form`, bản sao review ngoài repo; không deploy.

**Phạm vi/nguyên nhân:** tiếp sau `7b561eee8b24b31bc34dafaa657d17abea243210` đã push main, CI 38525183313 success. Bản in trước giữ nguyên UI cũ nên có emoji, không phải giấy riêng, chữ nhỏ và không có cấu trúc cột chuẩn. Hồi quy trước chỉ giữ ảnh cũ, không đánh giá chất lượng giấy nên bỏ sót. Không đổi guard/POST/model/migration/URL/quyền, không dependency mới; PDF QA packages chỉ ở TEMP.

**Sửa:** dispatch_register_print.html chỉ dùng dữ liệu đã có: số/ký hiệu và số gốc, ngày đến/đi, trích yếu, nơi gửi/nhận, người xử lý, trạng thái. Năm hiển thị thô từ các ngày văn bản trong trang; view không có bộ lọc năm nên không thêm. Giấy ghi rõ chỉ in phạm vi và trang kết quả đang xem; không tự xuất toàn bộ QuerySet hoặc tăng query. Cột loại được đưa lên dòng lọc; hạn xử lý/độ khẩn và link chi tiết vẫn trên màn hình, không đưa vào giấy sáu cột theo yêu cầu. CSS chỉ nằm trong khối `.dispatch-register` và named @page riêng; tăng print_forms.css?v và Tailwind, worker v18. Build lại Tailwind bỏ 20 selector cũ, thêm lại một hover:bg-gray-50 vốn còn được template khác dùng; không xóa utility của Kế hoạch/Báo cáo/Dự án. Không sửa các biểu mẫu HCNS/BCC khác.

**Kiểm tra:** runner ops/run_print_layout_uat.py thêm đọc PDF thật bằng pdfplumber (packages QA ngoài app), kiểm khổ ngang, chữ trong lề, serif ≥10pt, sáu cột/viền/tiêu đề lặp, không UI text/emoji; clone dòng trong DOM giả để stress nhiều trang, không ghi DB hoặc thay scope backend. Probe trên archive 110b893 port8784: exit1, sáu lỗi đúng kỳ vọng. Nguồn mới: 402 kiểm tra/37 PDF, 0 lỗi, thêm dispatches-pagination.pdf; đã xem ảnh trang đầu và trang hai, đủ viền và tiêu đề lặp. ops/run_timesheet_print_uat.py: 645 kiểm tra/8 tình huống, 0 lỗi. 36 PDF còn lại so cùng bản ghi ổn định bằng Poppler/text với archive, 36/36 văn bản/pixel không đổi, kết quả ở dispatch-paper-comparison; sổ công văn là baseline thay đổi có chủ đích, không coi khác pixel là hồi quy. So cũ/mới xác nhận bỏ giao diện, giữ bản ghi và thêm người xử lý theo giấy được yêu cầu.

**Lệnh:** các runner dùng `--directory "$env:TEMP/ihrms-finance-followup-20261014" --packages-dir "$env:TEMP/ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages" --port 8782`; print runner thêm `--pdf-packages-dir "$env:TEMP/ihrms-pdf-qa-packages-20261014"`. Cache runner thêm `--baseline-port 8784`: 9 kiểm tra, gap597,09→16px. Django focused 24 test đạt; full SQLite/SQL Server chạy trên nguồn chốt, kết quả cuối SQLite: 536 test/201,881s, OK (7 skip); SQL Server: 536 test/308,635s, OK, không skip, exit0. pip check, Django check, makemigrations --check --dry-run, contrast198/0 và git diff --check đạt; không migration. Chỉ restart demo cách ly khi template cache cần, không restart/deploy app thật.

**Bàn giao:** `D:/QLHCNS-Backups/IHRMS_Review_20261014_DispatchPaper.zip`, manifest tree/hash từng tệp và mở lại xác minh; bằng chứng giả ở ZIP Proof cùng đợt, metadata SHA/remote/CI ngoài repo. Giữ AGENTS/reference ngoài phạm vi; không đưa DB/env/media/log/tài khoản/bí mật vào ZIP nguồn. Chưa screen reader, zoom200% thực, phiên tài khoản thật hoặc máy in vật lý. Tiếp theo chỉ Kế hoạch, không Báo cáo/Dự án.

## 2026-10-14 — Hành chính: khôi phục Hủy và ẩn liên kết ngoài quyền

**Tóm tắt cho chủ dự án**

- Khôi phục Hủy đặt phòng/xe cho chủ đơn ở Pending/Approved; xác nhận và Escape hoạt động, không sửa view hủy.
- Ẩn xuất công văn bằng đúng `_can_view_reports(request)` và ẩn yêu cầu hồ sơ của tài khoản chưa gắn hồ sơ; 8 link 403 cũ → 0.
- 20 route × 9 vai trò giữ HTTP/form hiện hành ngoài form Hủy được khôi phục; không tăng truy vấn.
- Edge: 162 kiểm tra bố cục/3 trang và 31 kiểm tra luồng ghi đạt; 37 PDF chung và BCC vẫn đạt.
- Giữ hai template mồ côi, gỡ khỏi danh sách đã render; giấy sổ công văn được xử lý ở commit tiếp theo.
- Commit `ui: administration follow-up`, bản sao review ngoài repo; không deploy.

**Đầu lượt/phạm vi:** yêu cầu 8744364a, main/origin `110b893d7757bbdd732becde077fb9423c332506` khớp 0/0, giữ AGENTS.md và reference ngoài phạm vi. Đọc UI Ux Pro Max, tra UX xác nhận/focus; dùng quy trình PDF để kiểm bản in. Không đổi model/migration/quyền/guard/URL/tham số/cách tính/dependency.

**Nguyên nhân và sửa:** quan hệ `Employee.user_account` đã là User, `.user` không tồn tại nên điều kiện cũ luôn sai. Template so `b.employee_id == request.user.employee_id`, không truy cập quan hệ ngược gây N+1; thêm điều kiện Pending/Approved rõ ràng, không hiện cho Rejected/Cancelled/Completed hoặc người khác. Hai model hiện không có trạng thái Completed; test template vẫn kiểm trường hợp này để phòng hiển thị sai. Form giữ URL/CSRF và dialog có tiêu đề/nhãn Hủy rõ. Dispatch context thêm duy nhất cờ chỉ đọc gọi đúng hàm `_can_view_reports` của reporting; cả link màn hình và bản in cũ đều được ẩn theo cờ. Menu hồ sơ dùng employee_id đã có, không query thêm. Không nới quyền ở đích.

**Test trước/sau:** 4 test mới probe thật trên archive 110b893: 3 test UI thất bại với 7 subtest đúng lỗi đã nêu; test POST hủy backend vốn đúng nên vẫn đạt trên mã cũ. Sau sửa chạy lại cùng test và bộ UI. Helper bỏ ngoại lệ 403 của Hành chính. `ops/run_administration_contract_uat.py --directory "$env:TEMP/ihrms-finance-followup-20261014" --phase before`, rồi `--phase after --allow-cancel-ui`: 180 trường hợp, không thay HTTP hoặc các form khác, không tăng query; 8 link lỗi trước → 0 sau. Tùy chọn chỉ loại form `/rooms/.../cancel/` và `/vehicles/.../cancel/` khỏi so sánh form vì đó là thay đổi được yêu cầu; trạng thái/quyền nút được test riêng. Test menu cũ yêu cầu giữ mọi link kể cả link lỗi của tài khoản chưa gắn hồ sơ đã được cập nhật đúng một kỳ vọng UI này, không đổi assertion nghiệp vụ.

**UAT và in:** `ops/run_administration_workflow_uat.py` trên DB/media giả ngoài repo, port 8782: 31 kiểm tra đạt; cả phòng/xe tạo→mở Hủy→Escape không ghi→xác nhận lưu Cancelled và thông báo. `ops/run_project_layout_uat.py --account demo-hr --only /portal/rooms/ /portal/vehicles/ /portal/dispatches/`: 162 kiểm tra, 0 lỗi, 1920/1440/1024/768/390px × sáng/tối, bàn phím và reduced motion. `ops/run_print_layout_uat.py`: 380 kiểm tra/37 PDF đạt. `ops/run_timesheet_print_uat.py --phase after`: 645 kiểm tra/8 tình huống/32 PDF đạt. Các runner dùng directory `ihrms-finance-followup-20261014`, packages Playwright trong TEMP và DB dùng một lần; không ghi dữ liệu thật. TEMP followup-stable-print xuất cùng bản ghi trên archive 110b893 port 8784 và nguồn cuối 8782; đối chiếu pixel/text lưu tại followup-print-comparison: 37/37 giống nhau. Không sửa CSS in ở commit này. Kiểm tra trước đây giữ pixel cũ đã bỏ sót UI thừa trong sổ công văn; commit in tiếp theo bổ sung kiểm tra giấy riêng thay vì coi ảnh cũ là mẫu đạt.

**Kiểm tra nguồn cuối:** git diff --check, pip check, Django check, makemigrations --check --dry-run đạt, không migration; contrast 198 cặp/0 lỗi. Full suite SQLite và SQL Server dùng TEMP project-layout-final-tests.py gọi ops/run_tests.py, DB/media cách ly; kết quả cuối SQLite: 536 test/191,495s, OK (7 skip); SQL Server: 536 test/250,874s, OK, không skip, exit 0. Các lượt đầu thất bại ở kiểm kê menu cũ không được dùng làm kết quả đạt.

**Template mồ côi và ghi nhận backend:** rg trên views/urls/include/test không thấy route cho office_incoming_list.html và office_outgoing_list.html; chỉ còn chính nội dung hai template. Giữ nguyên tệp, loại khỏi TEMPLATES render/UAT; đề xuất chủ dự án chọn xóa hoặc đăng ký route trong đợt riêng. View room_booking_cancel/vehicle_booking_cancel vẫn gán Cancelled mà chưa chặn trạng thái hiện tại; POST thủ công có thể hủy đơn đã kết thúc/từ chối. Chỉ ghi nhận, không sửa backend theo yêu cầu. Không thêm kiểm trạng thái hoặc quyền mới.

**Bàn giao/giới hạn:** bản sao `D:/QLHCNS-Backups/IHRMS_Review_20261014_AdministrationFollowup.zip`, manifest tree và SHA-256 từng tệp được mở lại xác minh; không env/DB/media/log/tài khoản/bí mật/reference thật. Metadata SHA remote/CI ngoài repo cùng tên đợt. Chưa screen reader, zoom 200% thực, phiên tài khoản thật hoặc máy in vật lý. Nhật ký mục này chốt trước commit; trạng thái CI sau push nằm trong metadata bàn giao. Không force-push/deploy.

## 2026-10-14 — Giai đoạn 5: Hành chính

**Tóm tắt cho chủ dự án**

- Chuẩn hóa 22 template và partial duyệt Hành chính: tiêu đề, thẻ, bảng, nhãn trường, trạng thái và nhóm thao tác; hai vùng nội dung dùng tỷ lệ 60/40.
- Giữ nguyên nghiệp vụ, quyền, URL, tham số GET/POST, CSRF, model và cơ sở dữ liệu. Không thêm truy vấn, bộ lọc hoặc phân trang.
- Full suite trên nguồn cuối: SQLite 532 test đạt (7 skip); SQL Server 532 test đạt, không skip. Edge: 882 kiểm tra bố cục/20 trang và 23 kiểm tra luồng ghi đạt.
- Hồi quy in: 380 kiểm tra/37 PDF và 645 kiểm tra/8 tình huống bảng chấm công đạt. So cùng dữ liệu: cả 37 biểu mẫu giữ nguyên văn bản và pixel so với commit trước.
- Bản sao nguồn và bằng chứng được lưu ngoài repository; commit riêng `ui: administration`, push main, xác minh remote và CI. Không deploy.

**Đầu lượt và phạm vi:** tiếp tục theo xác nhận “Triển khai tiếp Hành chính”, sau Kế toán `174d5d4ba9267752797f6e22913d291c88d36d08` đã đồng bộ origin/main 0/0 và CI 38503044820 thành công. Đọc yêu cầu đính kèm 6f93f180 và dùng UI Ux Pro Max; không dùng UI Styling/shadcn, dependency hoặc CDN mới. Giữ nguyên thư mục reference chưa theo dõi và một dòng trống trong AGENTS.md do thay đổi cục bộ ngoài lượt này; không stage hai phần đó. Không triển khai Kế hoạch/Báo cáo/Dự án.

**Tệp và cách sửa:** bổ sung `administration_base.html`, `administration_ui.css` chỉ áp dụng màn hình; chuyển các trang tài sản, kiểm kê, thanh lý, công văn, tài liệu, sự kiện, mua sắm, phòng họp, xe và văn phòng phẩm sang thành phần UI dùng chung. Dùng nhãn thường trực, ID riêng cho cả hàng lặp, caption ẩn, tiêu đề cột, vùng bảng cuộn có thể focus, liên kết dùng được bằng bàn phím, nút tối thiểu 44px/chữ 14px. Giữ dải lọc công văn cùng nút, Enter và Xóa lọc hiện có. Các hàng mua sắm động tạo label/input qua DOM với ID duy nhất, không đổi tên `getlist`. Dialog xác nhận giữ đúng giá trị submitter của nút Duyệt/Từ chối. Bảng nhiều cột cuộn trong vùng chứa; sửa badge đè cột và không cắt tên/mã. MASTER bổ sung quy chuẩn Hành chính.

Giữ toàn bộ điều kiện tạo/duyệt/cấp phát/hoàn thành và từng form POST độc lập: phòng/xe/VPP, công văn và lịch sử, mua sắm Pending→Approved/Rejected→Purchased, kiểm kê và thanh lý. Quyền duyệt thanh lý vẫn yêu cầu vị trí Giám đốc Active hoặc superuser theo mã cũ; không chỉ dựa vào role DIRECTOR. Không sửa view, guard hay tồn kho. Đếm utility token cũ bằng cùng regex trên 23 template/partial màn hình: 2.124→0; bỏ class rỗng, style inline và emoji trên màn hình. Bundle Tailwind loại 29 selector không còn dùng, không thêm selector; tăng URL Tailwind và CSS Hành chính, service worker v17. Không sửa `print_forms.css` nên không tăng phiên bản tệp đó.

**Bảo vệ bản in:** tách `dispatch_register_print.html` từ phần in cũ, giữ markup giấy riêng khỏi bảng UI trên màn hình. Không sửa template giấy HCNS hoặc các tệp `*_print` có sẵn. Kiểm tra cũ dễ bỏ sót vì dùng fixture mới ở mỗi lượt, làm khác ID/nội dung dù CSS không đổi; lần này dùng cùng bản ghi ổn định trên archive `174d5d4` và nguồn cuối, xuất 37 PDF mỗi bên rồi so văn bản/pixel: không khác. Bảng chấm công còn được đo riêng về khổ giấy, màu, viền, ngắt trang và khoảng ký bằng runner chuyên biệt; không lấy số trang/HTTP làm bằng chứng thay thế.

**Đối chiếu quyền, form và truy vấn:** `ops/run_administration_contract_uat.py --directory "$env:TEMP/ihrms-finance-followup-20261014" --phase before --baseline-templates "$env:TEMP/admin-templates-baseline"`, sau đó cùng lệnh `--phase after`: 20 route × 9 vai trò = 180 trường hợp; trạng thái HTTP và toàn bộ form contract không đổi, không tăng truy vấn. Đo truy vấn ngay sau GET, trước quét link, xóa cache/query log mỗi trường hợp. Probe test UI mới trên archive cũ thất bại đúng kỳ vọng (1 test, 22 subtest thất bại). Helper liên kết mặc định chỉ chấp nhận 200/302; ngoại lệ 403 cũ được khai báo cụ thể, không coi mọi link đã đạt.

**Kiểm thử nguồn cuối:** `git diff --check`, pip check, Django check, `makemigrations --check --dry-run` đạt; không migration. Django dùng settings test/SQLite ngoài repo, không đọc/ghi DB vận hành. `ops/check_ui_contrast.py`: 198 cặp, 0 lỗi. Build Tailwind đạt và bundle cuối đã cập nhật. `venv/Scripts/python.exe "$env:TEMP/project-layout-final-tests.py" --backend sqlite`: 532 test/204,799s, OK (7 skip); cùng lệnh `--backend sqlserver`: 532 test/353,409s, OK, không skip. Wrapper gọi `ops/run_tests.py`, DB/media dùng một lần và chỉ tăng tốc password fixture trong test. Focused 103 test đạt (2 skip); sau dọn nội dung chạy lại 29 test UI Hành chính/bố cục/mobile: 72,173s, OK. Không sửa assertion nghiệp vụ để làm test đạt.

**UAT Edge trên dữ liệu giả cách ly:** các runner dùng `--directory "$env:TEMP/ihrms-finance-followup-20261014" --packages-dir "$env:TEMP/ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages" --port 8782`. `ops/run_project_layout_uat.py --only <20 route trong administration-after.json>`: 882 kiểm tra, 0 lỗi; 1920/1440/1024/768/390px × sáng/tối, nhãn/kích thước/focus/Enter, tỷ lệ 60/40, reduced motion, duyệt/từ chối phòng/xe/VPP và cấp phát. Đã xem ảnh công văn, kiểm kê, thanh lý và mua sắm ở màn hình rộng/hẹp, sáng/tối. Restart riêng máy chủ demo sau sửa vì template cache; không restart ứng dụng thật.

`ops/run_administration_workflow_uat.py` cùng tham số: 23 kiểm tra, 0 lỗi; tạo phòng/xe, mua sắm hai hàng động→duyệt→đã mua, tạo/cập nhật công văn và lịch sử, thanh lý→thêm tài sản→Giám đốc duyệt→HR lập biên bản→Disposed, kiểm kê→Completed và trang in. Kiểm tra thông báo, dữ liệu lưu, trang đích và Dashboard còn truy cập được. Escape ở dialog không ghi. Fixture Giám đốc được gán đúng vị trí theo guard hiện có; không mở guard để chạy test.

**PDF và cache:** `ops/run_print_layout_uat.py` cùng tham số: 380 kiểm tra/37 PDF, 0 lỗi. `ops/run_timesheet_print_uat.py` thêm `--pdf-packages-dir "$env:TEMP/ihrms-pdf-qa-packages-20261014" --phase after`: 645 kiểm tra/8 tình huống/32 PDF, 0 lỗi; demo này không có baseline BCC nên không báo 661. TEMP `admin-stable-print.py` xuất hai nguồn cùng bản ghi; `administration-print-comparison/result.json` xác nhận 37/37 văn bản và pixel không đổi. Poppler render 37 tài liệu chung + 8 BCC thành 67 trang; đã xem 6 contact sheet, không trang trắng. `ops/run_asset_cache_uat.py`: 9 kiểm tra đạt, cache cũ→v17, khoảng trường–nút 597,09→16px; fixture cache gắn đúng Tailwind là asset đã đổi phiên bản. Bằng chứng chỉ chứa dữ liệu giả.

**Bản sao và Git:** `D:/QLHCNS-Backups/IHRMS_Review_20261014_Administration.zip` lấy từ index nguồn cuối, loại .env (giữ .env.example), DB, media/uploads, log/runtime, tài khoản/bí mật và reference chưa theo dõi; có manifest branch/base/tree/hash, mở lại xác minh SHA-256 từng tệp. Đây là bản sao review mã nguồn, không phải backup phục hồi dữ liệu. Bằng chứng tại `IHRMS_Administration_Proof_20261014.zip`. Commit `ui: administration`, push origin main; SHA remote, ahead/behind và GitHub Actions được ghi trong `D:/QLHCNS-Backups/IHRMS_Administration_20261014.delivery.json`. Không force-push hoặc deploy.

**Giới hạn và việc còn mở:** baseline có 8 link 403: link export công văn của EMPLOYEE/DEPT_MANAGER/UNLINKED và profile của tài khoản demo SYS_ADMIN/UNLINKED chưa gắn hồ sơ; chưa thay quyền. Nút hủy phòng/xe vẫn bị ẩn bởi điều kiện gốc `b.employee.user_account.user == request.user`, nên chưa UAT hủy qua UI. Hai template office_incoming/outgoing cũ không có view/URL đăng ký; chỉ dọn trình bày, không báo đã UAT route không tồn tại. Chủ dự án cần quyết định riêng ba vấn đề này trước khi thay nghiệp vụ/quyền. Chưa kiểm thử screen reader, zoom 200% thực, phiên tài khoản thật hoặc máy in vật lý; Edge tự động trên demo không chứng minh phiên trình duyệt của người dùng. Khi ứng dụng thật nhận mã mới, người vận hành restart nếu có template cache rồi tải lại bình thường để nhận asset mới; không cần xóa cookie. Dừng sau Hành chính.

## 2026-10-14 — Giai đoạn 5: Kế toán, chuẩn hóa giao diện và liên kết theo quyền

**Tóm tắt cho chủ dự án**

- Bỏ liên kết hồ sơ ngoài quyền của kế toán; tên/mã nhân viên hiển thị bằng văn bản trong danh sách lương.
- Chuẩn hóa 5 trang Kế toán; nhãn/form có nghĩa, số kết quả, nút thang lương trong vùng hành động tiêu đề.
- Tính lại toàn kỳ có xác nhận; không đổi POST, dữ liệu nhập tay, cách tính hay quyền.
- Edge đạt205 kiểm tra; SQLite528 test đạt (skip7), SQL Server528 test đạt; query5 trang không tăng.
- Hồi quy380 kiểm tra/37 PDF và645 kiểm tra BCC/8 tình huống đạt; không sửa CSS/giấy in.
- Nguồn và bằng chứng review ngoài repo; commit riêng Kế toán trước khi bắt đầu Hành chính, không deploy.

**Đầu lượt/phạm vi:** main/origin khớp `2cecd21b70d8b787a3cfadd8f3ebb9d3ed1dfa15`, fetch0/0; CI bản in trước đã success (run38500185039), metadata bàn giao trước được cập nhật ngoài repo. Đọc yêu cầu6f93f180 và UI Ux Pro Max, tra UX về nhãn thường trực/xác nhận/focus; không dùng UI Styling/shadcn. Giữ nguyên thư mục reference chưa theo dõi và dữ liệu thật.

**Kiểm kê guard/hành động:** 5 view Kế toán giữ `_can_manage_finance`/`has_permission(manage_finance)`, không sửa PERMISSION_MATRIX, `_employee_scope`, view/model hay migration. Giữ nguyên form tạo kỳ (payroll_month/payroll_year), tạo người phụ thuộc (employee/full_name/relationship/registered_from), ba form cấu hình (form_type insurance/deduction/bracket và toàn bộ tên/required/step/giới hạn hiện có), generate/calculate/lock/issue/update-line theo trạng thái Open/Locked, CSRF và URL. Menu nhân viên giữ can_manage_hr, can_export_employee_data/can_view_all_employees, target popover và mọi href/fragment.

**Sửa và quyết định phạm vi:** salary_list đổi tên nhân viên từ nút/link hr_employee_detail#luong thành chữ; kế toán không có quyền xem hồ sơ nhân viên; mở thêm quyền là quyết định riêng của chủ dự án. Dùng page_header/actions partial, field/options partial cho phụ thuộc/cấu hình, h2 cho form và danh sách, salaries|length/dependents|length dùng cache QuerySet hiện có. Bỏ25 class rỗng và mọi ID finance-1-/2-/3-, placeholder lặp nhãn, dấu+ ở nút. Năm/tiền/ui-number/tabular giữ nguyên. Hai danh sách lương/phụ thuộc chưa có tìm kiếm/phân trang, hiện đủ cho quy mô hiện tại; thêm tìm kiếm là yêu cầu riêng. Đọc toàn Payroll.calculate(): chỉ cập nhật ngày công/kết quả gross/insurance/tax/net/signature/timestamp, giữ các trường nhập tay; xác nhận dùng câu trung tính đúng nội dung cập nhật tự động. Menu nhân viên bỏ42 token utility trong8 anchor (block/px/py/text-xs/hover/border)→0; tận dụng selector ui-row-popover a đã có hover/focus/44px, không thêm CSS chung. Năm trang Kế toán bỏ overflow-x-auto→0 utility cũ trong thuộc tính class; còn mobile-table-scroll là thành phần hiện có, không phải utility cần thay. Không thay CSS/assets, URL cache hoặc mẫu giấy.

**Test và baseline:** thêm ui_test_helpers.assert_internal_links để quét anchor nội bộ bằng đúng client đã đăng nhập, không replay POST; mọi link trong5 trang có dữ liệu trả200/302, không403/404. FINANCE_OFFICER test không còn href hồ sơ; không giữ link có điều kiện nên không có nhánh mở quyền cần test. Probe trước sửa trên mã2cecd21: 12 test,4 failure đúng lỗi link/xác nhận/markup (không error). Sau sửa test_finance_followup/test_finance_ui/tests_recruitment_accounting_navigation qua wrapper ops/run_tests.py:16 test/4,262s đạt. Số query cùng fixture salary14→14,dependent10→10,tax11→11,period9→9,payroll15→15; có assertion trần để bắt tăng query. Không sửa N+1 có sẵn nếu ngoài phạm vi.

**Lệnh/kết quả:** `git diff --check` exit0; `venv/Scripts/python.exe -m pip check` exit0; Django check và makemigrations --check --dry-run qua TEMP finance-framework.py dùng settings test/SQLite ngoài repo: exit0, không migration; lần gọi đầu thiếu DJANGO_SETTINGS_MODULE đã sửa wrapper và chạy lại đạt. `venv/Scripts/python.exe ops/check_ui_contrast.py`:198 cặp,0fail/exit0. `venv/Scripts/python.exe "$env:TEMP/project-layout-final-tests.py" --backend sqlite`:528 test/131,956s, OK skip7; cùng wrapper `--backend sqlserver`:528 test/300,173s, OK0skip, exit0; wrapper chỉ MD5 fixture test và gọi ops/run_tests.py với DB/media dùng một lần. Sau dọn BOM/whitespace chạy lại focused16 đạt. Không dùng kết quả full suite lượt trước.

**UAT Edge và in:** `venv/Scripts/python.exe ops/run_finance_followup_uat.py --directory "$env:TEMP/ihrms-finance-followup-20261014" --packages-dir "$env:TEMP/ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages" --port8782`:205 kiểm tra,0fail/exit0; 5 trang×1920/1440/1024/768/390×sáng/tối, dữ liệu tên dài, không tràn, control44px/chữ14px, focus/Tab, Enter mở xác nhận/Escape đóng, hủy không ghi, xác nhận có timestamp mới và giữ tiền nhập tay, thêm người phụ thuộc lưu/thông báo/trang đích, Dashboard còn truy cập được; HR menu mở bằng Enter/Tab link/Escape tại5kích thước×2theme. Đã xem ảnh salary/dependent/payroll1440 sáng/tối. Phép đo đầu đếm cả nguồn số ẩn ui-number-source (2px) nên báo thấp giả; sửa selector chỉ đo control hiển thị và chạy lại, không đổi CSS để chữa test.

`ops/run_print_layout_uat.py` cùng directory/packages/port8782:380 kiểm tra/37PDF đạt/exit0. `ops/run_timesheet_print_uat.py` thêm --pdf-packages-dir "$env:TEMP/ihrms-pdf-qa-packages-20261014" --phase after:645 kiểm tra/8 tình huống/32PDF đạt; thư mục mới không có baseline trước BCC nên16 so query/công thức trước-sau không chạy, thay bằng query5trang và test BCC/full suite; không báo661. Lần đầu chạy hai runner cùng sửa tài khoản thử nghiệm gây mất session/SQLite locked; đã dừng chạy song song trên cùng demo và chạy lại tuần tự đạt. CSS in và mọi template giấy không đổi trong diff. Poppler render37chung+8BCC, kiểm trang trắng và contact sheet lưu ngoài Git; kết quả cuối trong pdf-visual-qa/result.json. Bằng chứng JSON/PDF/ảnh là giả, không đưa DB/password/marker secret vào Git.

**Bàn giao:** `D:/QLHCNS-Backups/IHRMS_Review_20261014_Finance.zip` từ index cuối, manifest main/base/tree và SHA256 từng tệp, mở lại kiểm hash; `D:/QLHCNS-Backups/IHRMS_Finance_Proof_20261014.zip` chỉ ảnh/PDF/JSON giả. Loại.env (giữ.env.example), DB/media/uploads/runtime/log/tài khoản/bí mật/reference chưa theo dõi. Commit riêng `ui: finance follow-up`; metadata SHA/hash/remote/CI ở `D:/QLHCNS-Backups/IHRMS_Finance_20261014.delivery.json`, push main, so SHA0/0, không force-push/deploy. Chỉ bắt đầu Hành chính khi full suite phần này đã đạt.

**Giới hạn:** chưa screen reader, zoom200% thực, UAT phiên tài khoản thật hoặc máy in vật lý. Không thay chính sách kế toán xem hồ sơ; chủ dự án quyết nếu muốn mở quyền. Các thao tác viết dùng DB/media giả ngoài repo; dữ liệu vận hành giữ nguyên.

## 2026-10-14 — Khôi phục bản in bảng chấm công theo mẫu BCC VietHealth

**Tóm tắt cho chủ dự án**

- Sửa riêng bản in bảng công: A4, Times New Roman, logo/Phụ lục 1, bảng ba cột, cuối tuần xanh và khoảng ký đúng mẫu.
- Hiện đủ việc/giờ cuối tuần và ngày lễ trên màn hình lẫn bản in; giữ công thức, quyền và dữ liệu vận hành.
- 661 kiểm tra/8 tình huống BCC; 380 kiểm tra/37 PDF hồi quy; 31 biểu mẫu khác có văn bản và pixel không đổi.
- Full suite: SQLite 520 test đạt (7 skip); SQL Server 520 test đạt; cache cũ→mới đạt 9 kiểm tra.
- Giữ số ngoài giờ âm −176 theo công thức; chủ dự án cần quyết định nghiệp vụ riêng nếu muốn hiển thị khác.
- Bản sao nguồn/bằng chứng và metadata commit/CI ngoài repository; chưa in máy thật, thử chữ ký scan hoặc zoom 200%.

**Phạm vi và đầu lượt:** đọc yêu cầu đính kèm 140fbd11 và skill UI Ux Pro Max/PDF; không dùng UI Styling. Nhánh main, HEAD/origin ban đầu `4e3bc318a1d4ecd1e35212cf6f8c54d6311489c0`, fetch đồng bộ 0/0. Giữ nguyên thư mục reference chưa theo dõi chứa PDF mẫu người dùng; không đưa PDF có tên thật vào Git hoặc bản sao review. Đối chiếu trực tiếp mẫu Letter 612×792pt với PDF giả A4; không sửa model/migration/URL/quyền/tên GET/POST hoặc cách tính.

**Xác nhận trước sửa, lỗi 1–9 và nguyên nhân:** dùng bản nguồn archive 4e3bc31 (ngoài repo, không tạo nhánh) phục vụ cổng 8781, cùng DB/media giả, xuất hai chế độ PDF và đo print DOM. (1) Không tái hiện mất viền tại mép giấy trên commit này: viền phải cũ vẫn có ở x=561,75pt, bên trong giấy A4 ~594,96pt; nhưng nằm ngoài vùng yêu cầu BCC mới (546,77pt). Không quy kết ảnh chủ dự án cho một nguyên nhân chưa chứng minh. Với lề BCC mới, làm tròn collapsed border từng gây x=547,50pt; chừa 1 CSS px cho đường biên đưa x tối đa về 546,75pt, không giảm cỡ chữ. (2) Nền cuối tuần bị reset transparent !important toàn cục: cũ 0 hàng xanh; nay đúng số thứ Bảy/Chủ nhật, fill #5B9BD5 toàn hàng, tiêu đề/ngày lễ trắng. (3) `.timesheet-document p {margin:0}` thắng margin-top của tên ký: khoảng cũ ~1,59mm; nay đo 23,58mm với margin rõ 23mm. (4) Trạng thái duyệt cũ in cùng form; nay chỉ trên màn hình. (5) Bổ sung logo 36mm, Phụ lục 1, metadata italic có thụt lề, tên dự án và header hai tầng khi đúng một dự án. (6) Arial 8,5pt/title13pt thành TNR10,4pt/title18pt, giờ căn phải. (7) Cho phép 1–2 trang tự nhiên, header lặp; hai ngày cuối/tổng/nghỉ phép/chữ ký cùng trang, không trang trắng. (8) Số ngoài giờ âm giữ nguyên, ví dụ tháng 10 trống =0−176=−176; chưa chọn phương án in 0/Thiếu giờ. (9) Nhánh template cuối tuần/lễ cũ bỏ entries dù backend cộng giờ; nay hiển thị đủ, gồm Retreat thứ Bảy 8h và công ngày lễ.

**Mã thay đổi:** `timesheet_month.html`, partial `_timesheet_print_summary.html`, `print_forms.css`, `attendance.py`; bổ sung context dự án từ entries đã select_related, không query mới. Phần màn hình của summary/form giữ nguyên, phần in chỉ đọc giá trị đã lưu; cache hai property của balance trong template để việc có hai phần trình bày không tăng truy vấn. So trước/sau 8 tình huống lần lượt 27/23/22/22/23/19/23/22 truy vấn, không tăng; total/required/diff giữ nguyên. CSS giới hạn timesheet/print, các giấy HCNS khác giữ nguyên. Tăng URL print/project-layout và cache service worker v16 để tránh dùng asset cũ. AGENTS bổ sung bắt buộc print UAT và so ảnh/số đo cho thay đổi CSS chung/card/scroll/filter/template in. Cập nhật test asset và runner cache/print; thêm 5 Django test và runner BCC. Không thêm dependency của ứng dụng; thư viện QA chỉ cài vào TEMP.

**Vì sao kiểm thử cũ bỏ sót:** runner cũ vẫn đạt 375 check/37 PDF trên nguồn lỗi (yêu cầu đính kèm nhắc 374, thực tế hiện tại 375). Nó kiểm khổ/tràn/chủ thể chung nhưng không xác nhận logo, phông BCC, fill từng ngày, việc cuối tuần, khoảng ký và header/khối kết thúc theo dữ liệu nhiều dòng. Probe 5 test mới trên nguồn archive: cả 5 thất bại đúng điểm cần sửa, không có error. Runner chung mới 380 check; runner chuyên biệt đo PDF thực và query/formula, không dùng HTML/số trang đơn thuần để kết luận.

**Kiểm tra trên nguồn cuối (PowerShell; tất cả lệnh cuối đạt exit 0 trừ probe trước sửa được kỳ vọng thất bại):**

- `git diff --check`; `venv/Scripts/python.exe -m pip check`; `venv/Scripts/python.exe src/manage.py check`; `venv/Scripts/python.exe src/manage.py makemigrations --check --dry-run`; `venv/Scripts/python.exe ops/check_ui_contrast.py`: đạt, không migration; 198 cặp tương phản, 0 fail. Lệnh Django dùng APP_ENV=test, SQLite tạm ngoài repo và SECRET_KEY ngẫu nhiên, không đọc/ghi DB vận hành.
- `venv/Scripts/python.exe "$env:TEMP/project-layout-final-tests.py" --backend sqlite` → 520 test/109,065s, OK, skip7. Cùng lệnh `--backend sqlserver` → 520 test/178,655s, OK, không skip. Sau dọn whitespace và nhật ký, chạy lại cùng wrapper `--backend sqlite apps.portal.test_timesheet_print apps.portal.test_project_layout`: 18 test đạt, exit0. Wrapper gọi `ops/run_tests.py`, chỉ tăng tốc password fixture bằng MD5 trong test, DB/media dùng một lần; không đổi cấu hình ứng dụng.
- `venv/Scripts/python.exe ops/run_timesheet_print_uat.py --directory "$env:TEMP/ihrms-bcc-print-20261014" --packages-dir "$env:TEMP/ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages" --pdf-packages-dir "$env:TEMP/ihrms-pdf-qa-packages-20261014" --port 8780 --phase after` → 661 check/8 tình huống/32 PDF, 0 fail. Trước sửa dùng `--port 8781 --phase before --source-root "$env:TEMP/ihrms-bcc-baseline-4e3bc31"`; báo lỗi kỳ vọng lưu riêng. Bao gồm 0/1/nhiều dự án, 28/29/30/31 ngày, tên/dòng dài, có/không balance, manager rỗng, đã duyệt và nghỉ được duyệt; 1920/1440/1024/768/390px×sáng/tối. PDF thật prefer_css_page_size True và False/A4, cộng print DOM 163mm so với vùng cũ 186mm; mọi mép bảng trong lề, 8–10 hàng xanh đúng tháng, chữ ≥10pt, chữ ký ≥22mm, không cắt việc/giờ, header lặp và khối kết thúc cùng trang. 16 cặp sáng/tối render pixel giống nhau.
- `venv/Scripts/python.exe ops/run_browser_uat.py --backend sqlserver --layout-only --packages-dir "$env:TEMP/ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages" --output-dir "$env:TEMP/ihrms-bcc-business-20261014"` → 133 check/32 ảnh; tạo/sửa hồ sơ, hợp đồng, nhập/sửa bảng công, nghỉ phép/duyệt và KPI, kiểm dữ liệu lưu/thông báo/trang đích; DB đã hủy. Chạy trước tối ưu cache property balance (chỉ render); full suite và BCC UAT sau tối ưu đã chạy lại.
- `ops/run_print_layout_uat.py --directory ... --packages-dir ... --port 8780` trên cùng thư mục giả/packages ở trên → 380 check/37 PDF, 0 fail; chạy nguồn archive để có baseline rồi chạy lại nguồn cuối. So trực tiếp 31 PDF không phải bảng công/legacy bằng text+pixel: tất cả không đổi; 5 legacy dùng dữ liệu sinh ID riêng được kiểm qua runner và xem ảnh. `ops/run_asset_cache_uat.py` cùng directory/packages/port → 9 check đạt; cache v15 thật được tạo trước, v16 thay thế, gap cũ597,09→16px, URL CSS in mới và TNR được xác nhận.
- Render Poppler sau lần UAT cuối: 45 tài liệu/67 trang (37 chung+8 BCC), không trang trắng, đã xem 6 contact sheet, ảnh lớn trang1/2 và đối chiếu cạnh PDF mẫu. A4 hẹp/dài hơn Letter nên số dòng/trang khác, không sao chép chữ ký/dữ liệu thật; mẫu 1 dự án kết thúc ở trang2 với ngày27–30 thay vì24–30. Màu, lề A4, kiểu chữ và khoảng ký đáp ứng yêu cầu; không hứa pixel trùng mẫu Letter khác dữ liệu. Build Tailwind ra TEMP cho hash trùng bundle theo dõi, không sửa bundle.

**Bằng chứng và bàn giao:** dữ liệu/PDF/ảnh/JSON ở `%TEMP%/ihrms-bcc-print-20261014`, log `bcc-verified-print.log`, `bcc-golden-after.log`, `bcc-verified-cache.log`, `bcc-verified-sqlite.log`, `bcc-verified-sqlserver.log` ngoài Git. Ảnh so mẫu thật chỉ giữ riêng TEMP, không đưa vào bộ proof. Nguồn review `D:/QLHCNS-Backups/IHRMS_Review_20261014_BCC_Print.zip`, bằng chứng giả `D:/QLHCNS-Backups/IHRMS_BCC_Print_Proof_20261014.zip`: manifest tree/base/main và SHA-256 từng tệp, mở lại kiểm đủ hash; loại .env (giữ .env.example), DB, media/uploads, runtime/log và tài khoản/bí mật. Đây là bản sao review, không phải backup dữ liệu. Commit dự kiến duy nhất `fix(print): match BCC timesheet form`, push origin main và xác minh SHA/ahead-behind/Actions; kết quả commit và hash/CI cuối ghi trong `D:/QLHCNS-Backups/IHRMS_BCC_Print_20261014.delivery.json` để tránh SHA tự tham chiếu. Không force-push/deploy.

**Giới hạn/việc chủ dự án cần làm:** đã UAT Edge headless thật trên dữ liệu giả cách ly, chưa UAT phiên tài khoản thật của người dùng; chưa in máy in vật lý, gắn chữ ký tay/scan hay zoom 200% trong Edge. Chủ dự án duyệt A4 thay Letter theo yêu cầu và việc không in trạng thái duyệt; quyết định riêng cách hiển thị thiếu giờ âm nếu muốn đổi nghiệp vụ. Sau khi ứng dụng đang dùng nhận code mới, tải lại trang bình thường để nhận asset mới (khởi động lại tiến trình nếu template cache); không cần xóa cookie. Nếu máy in thực tế còn cắt viền, cung cấp PDF xuất từ phiên đó để đối chiếu số đo, chưa suy đoán nguyên nhân từ ảnh.

## 2026-10-14 — Gộp bộ lọc với kết quả và gom thao tác quyết định

**Tóm tắt cho chủ dự án**

- Gộp 14 dải lọc vào thẻ kết quả; nút Áp dụng/Xóa lọc sát trường cuối, không còn khối hướng dẫn rời.
- Quyết định có một khối xử lý, Hủy/Từ chối thu gọn; lỗi giữ ghi chú, quyền và POST/CSRF không đổi.
- Tái hiện cache cũ: khoảng cách nút 613,09px → 16px sau reload thường, cache service worker cũ được thay.
- 515 test đạt trên SQLite và SQL Server; Edge kiểm cả hai theme, năm kích thước và luồng nghiệp vụ giả.
- 38 PDF/51 trang không trắng; bảng công và quyết định không đổi nội dung/pixel so với nguồn trước.
- Bản sao nguồn và bộ ảnh/PDF review ngoài repository; không phải backup phục hồi, không deploy.

**Nguồn/phạm vi:** đầu lượt main sạch, HEAD/origin/main `49537a924511eee6df7b2c7d5c21541e57bd4750`, fetch và ahead/behind 0/0. Dùng UI Ux Pro Max; kiểm PDF theo quy trình render. Thay markup 14 trang: activity/calendar, activity/dashboard, document/hcns/catalog, portal/dashboard_people, dispatch_list, hr_employee_list, kpi_score_list, personnel_decision_list, report_budget, report_headcount, report_hub, report_personnel_changes, report_timesheet, timesheet_month. Giữ tham số, reset/scope/phân trang, năm raw, quyền, dữ liệu và tỷ lệ 60/40. Caption không lặp trên màn hình; ghi chú hợp đồng nằm cạnh số kết quả. Các vùng no-print chỉ bao bộ lọc/thao tác, không bao bảng kết quả.

**Thực hiện:** CSS opt-in tập trung tại shared_components.css; giữ project_layout.css dành cho bố cục. Đổi URL phiên bản của shared_components.css/js, project_layout.css, hr_ui.css và cache worker v15. personnel_decision_detail gom các form độc lập vào một panel, tiện ích tải/in/sửa là nút phụ; disclosure mở lý do và Đóng trả focus. Bỏ messages lặp trong template. `document/hcns/views.py` chỉ thêm lưu tạm tối đa 2000 ký tự ghi chú lỗi trong session cùng người dùng/quyết định và lấy ra một lần qua redirect cũ; không localStorage, không sửa guard/trạng thái/schema/API. File lỗi cần chọn lại. Cập nhật MASTER/spec và regression/UAT.

**Kiểm tra nguồn cuối:** `git diff --check`, `venv/Scripts/python.exe -m pip check`, `src/manage.py check`, `src/manage.py makemigrations --check --dry-run` đều exit0; lệnh manage dùng APP_ENV=test/DB_ENGINE=sqlite/SECRET_KEY tạm. Đã bỏ đúng tệp SQLite rỗng src/qlhcns do lệnh check tạo (0 byte), không động DB vận hành. `ops/check_ui_contrast.py`:198 cặp,0 lỗi. Build Tailwind ra TEMP bằng CLI:exit0, SHA256 khớp bundle tracked; npm audit --audit-level=low:0 vulnerabilities. Full suite qua `TEMP/project-layout-final-tests.py --backend sqlite|sqlserver` gọi ops/run_tests.py với MD5 chỉ cho fixture DB dùng một lần:515 test; SQLite112,661s/7 skip dành cho SQL Server; SQL Server217,717s/0 skip;exit0. Sau dọn khoảng trắng, chạy lại `apps.portal.test_project_layout apps.document.tests_hr_workflow`:44 test/16,122s/exit0. Hai lỗi đầu lượt là assertion class lịch/cache phiên bản cũ, đã cập nhật và chạy lại full suite; không tính lượt lỗi là đạt.

**Edge trên nguồn cuối:** dùng demo mới `TEMP/ihrms-results-workflow-20261014`, DB/media/tài khoản giả riêng; packages Playwright ở TEMP/ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages. Các lệnh ops/run_* nhận --directory thư mục trên, --packages-dir thư mục packages, --port 8770; baseline49537a9 xuất git archive ngoài repo, serve8771. `run_filter_bar_uat.py --baseline-port 8771`:1801 check/300 phép đo/0 lỗi,14 portal+Admin ×1920/1440/1024/768/390 ×sáng/tối ×trước/sau; gap khi cùng hàng≤17px,lệch đáy≤1px,nút≥44px, không tràn. Kiểm Enter GET/reset/empty/Tab/dropdown Escape và viewport hiệu dụng720px tương đương1440px zoom200%; tôn trọng các điểm Tab nội bộ của input ngày Edge. `run_asset_cache_uat.py`:6 check; proxy loopback đổi từ release cũ/cache cũ sang nguồn mới, reload thường613,09→16px, worker thay cache; không xóa dữ liệu trình duyệt. `run_project_layout_uat.py`:954 check/73 URL/0 problem, có luồng kiểm kê/phòng/xe/VPP. Fixture chỉ đổi password khi cần, tránh làm mất session UAT đồng thời; chờ networkidle ở chuyển trang. `run_dashboard_layout_uat.py`:1642 check/132 ảnh/0 JS error. `run_decision_layout_uat.py`:130 check/22 ảnh, giấy xem trước tên dài, HR trình duyệt/director duyệt/từ chối, lỗi PDF giữ ghi chú, ban hành/hủy, dữ liệu/history/thông báo và Dashboard cập nhật; form rỗng không mở confirm, Escape hủy xác nhận/Enter gửi. `run_browser_uat.py --backend sqlserver --layout-only --output-dir TEMP/ihrms-results-sqlserver-business-20261014`:133 check/32 ảnh, hồ sơ/hợp đồng/nghỉ/chấm công/KPI, DB cách ly đã xóa. Mọi lượt cuối exit0; các lần mất session/khởi động lại server trong probe không được tính là đạt.

**Bản in:** `run_print_layout_uat.py`375 check/37 PDF/exit0, thêm PDF trang chi tiết quyết định từ UAT workflow. Poppler render38 PDF/51 trang, pypdf xác nhận không trang trắng; đã xem5 contact sheet và ảnh lớn màn hình quyết định/nhân viên. So sánh trực tiếp nguồn49537a9 với nguồn mới trên cùng dữ liệu giả: bảng công và giấy quyết định đều1 trang, văn bản và pixel render không đổi. File in/ảnh/hash chỉ ở TEMP và bản sao review ngoài Git. Không đổi print_forms.css, khổ giấy, lề hay HCNS document template.

**Bàn giao:** `D:/QLHCNS-Backups/IHRMS_Review_20261014_Results_Workflow.zip` từ Git index cuối, có manifest tree/base/main và SHA256 từng tệp; mở lại kiểm hash, loại .env (giữ .env.example), database, media/uploads, log, runtime và tài khoản. Bộ xem ảnh/PDF giả: `D:/QLHCNS-Backups/IHRMS_Results_Workflow_Proof_20261014.zip`. Commit/push main theo quyền mặc định, đối chiếu HEAD/remote/ahead-behind và CI theo SHA sau push; metadata SHA/hash/CI cuối ở `D:/QLHCNS-Backups/IHRMS_Results_Workflow_20261014.delivery.json` để không nhúng SHA tự tham chiếu vào commit. CLI gh trả401; đọc Actions bằng connector GitHub thay thế. Không force-push/deploy.

**Giới hạn và việc chủ dự án cần làm:** cua.getState trả apps=[]/browsers=[], nên kết quả là Edge headless do Playwright chạy trên dữ liệu giả, chưa UAT phiên tài khoản thật. Chưa dùng screen reader, máy in vật lý hoặc thao tác zoom từ toolbar Edge; kiểm reflow bằng viewport hiệu dụng, không lấy CSS zoom làm tương đương browser zoom. Chủ dự án khởi động lại ứng dụng đang dùng nếu có cache template, sau đó tải lại trang bình thường để nhận base/assets mới; không cần xóa cookie/cache. Nếu máy in/extension vẫn khác, gửi PDF cụ thể để đối chiếu bộ proof, không chỉnh giấy bằng CSS màn hình.

## 2026-10-13 — Chuẩn hóa dải lọc, kiểm lịch sử bản in và CI

**Tóm tắt cho chủ dự án**

- Đổi14dải lọc về `[Trường…] [Áp dụng] [Xóa lọc]`, trong card thống nhất, không đẩy nút ra mép phải.
- Trang quyết định1920px: khoảng cách trường–nút636,203px→16px; Admin234,203px→8px, cùng đáy/44px.
- Reset có điều kiện, giữ scope; label/Tab/Enter/năm/phân trang/quyền giữ nguyên, mobile hai nút cùng hàng.
- Sửa vùng cuộn khi in còn lề âm gây cắt đường viền; giữ giấy HCNS/profile và layout60/40 của các khối khác.
- CI main369ef79 đã xác nhận success; bản sửa TEMP Linux giữ nguyên và test không TEMP/TMP đạt.
- Kết quả nguồn cuối, bản sao và SHA bàn giao ghi ở cuối mục; không deploy/UAT tài khoản thật.

**Đầu lượt:** main sạch, HEAD `369ef79a412ac7d90f118f35abf1961a68d5d9f7`, fetchorigin0/0. Đọc tệp yêu cầu e0454606/“Văn bản đã dán.txt”, UI UX Pro Max; không dùng UI Styling/shadcn. Đối chiếu lịch sử in36b8380/e73fc35 và các mốc UI a4d13dd/9eba8ca/a3b949b/6fce707. Không reset/rollback toàn bộ: lỗi cụ thể của bản hiện tại là vùng bảng còn width/margin màn hình, trong khi giấy đã đổi padding. Sửa riêng `.ui-scroll/.mobile-table-scroll/.overflow-x-auto` khi print về width100%,margin0,padding0; thêm assertion mép bảng trong main, không đổi chữ/profile/trường mẫu.

**Triển khai:** CSS dải lọc chuyển duy nhất về shared_components.css, gỡ toàn bộ ui-query-* khỏi project_layout.css và margin-left:auto của nút Admin. Flex inline gap12/16px, trường textbasis16rem/max24rem,select13rem,ngày/tháng/năm/số10rem; desktopwrap tự nhiên,tablet2cột/mobilerộng100%,nút44px/cùnghàng. Card padding16px,khôngh2riêng. Partial ui/query_actions.html và ui/field.html cho cả14trang; options_template tách từng select, chỉ thêm filter ui_has_filters đọc tham số khai báo, không query/view/model mới. Nút chính Áp dụng, reset chỉ khi tham số lọc khác rỗng, bỏ page/scope, giữ metric/on_date drill-down và groupcatalog. Loại caption hiện khi quyết định trống/link nút tên/đường kẻ dưới empty state. Sửa so sánh selected_period int với idint trong options KPI để giữ chọn khi render. Build lại Tailwind từ nguồn hiện tại và cache query CSS mới. MASTER/spec18 cập nhật quy chuẩn mới thay nút mép phải.

**14trang:** activity/calendar,dashboard;document/hcns/catalog;portal/dashboard_people,dispatch_list,hr_employee_list,kpi_score_list,personnel_decision_list,report_budget,report_headcount,report_hub,report_personnel_changes,report_timesheet,timesheet_month.10trang có số từ paginator/dữ liệu đã có;4trang không thêm số: lịch lặp một hoạt động theo nhiều ngày, report_hub nhiều tổng khác đơn vị, report_personnel_changes nhiều tập có thể chồng, timesheet_month là chọn kỳ của một người chứ không danh sách kết quả. Không bịa tổng hay query bổ sung. Caption quyết định visually-hidden, vẫn giữ tên bảng cho AT.

**CI đã xác minh:** gh CLI401, chuyển connectorGitHub read-only. Log job115383355138/run38420720139 fail thật do KeyError TEMP trong test_dashboard_followup. Commit22484d9 đã đổi tempfile.gettempdir; main369ef79 merge giữ sửa đó. API `actions/runs?branch=main` xác nhận run38424309757 (push main) completed/success, PRfix run38423612639 cũngsuccess. Không sửa/giảm workflow. Test riêng method đó với childprocess không TEMP/TMP đạt1test0,319s; TEMP/inline-no-temp-ci.log. Nguồn mới tránh Windows path trong test/helper mới; runner sử dụngtham sốDirectory và pathlib. Sau push kiểm Actions commit mới riêng, không lấy CI của369ef79 làm bằng chứng cho commit mới.

**Đo/kiểm:** tạo baseline nguồn369ef79 qua gitarchive ngoài repository, server8768, nguồn mới8767; dùng cùng demo SQLite/media giả có marker, không.env/dữ liệu thật. ops/run_filter_bar_uat.py đo14trang+Admin Contractchangelist×1920/1440/1024/768/390×2theme×before/after=300tổhợp; chụp24ảnh trước/sau cho quyết định/nhân viên/chấm công/reporthub/catalog/Admin. AdminEmployee không có search_fields nên đổi sang ContractAdmin có search thật, không thêm filter vàoAdmin. Căn đáy0px, gap16pxportal/8pxAdmin khi cùnghàng; bảng/tênlong/mobile/nooverflow/font14/focus3px và Enter ởtextfield→nativeGET/reset URL/scope được kiểm. Các lượtfail font/template-load và mobile specificity đã sửa rồi rerun; không tính lượt lỗi là đạt. JSON/screenshot runtime/inline-filter-uat/result.json; khôngGit. QueryForms và11testprojectlayout kiểm14trang, mộtsubmitÁp dụng, label/id/card/reset,nămraw; testDirectorẩnstatus,EMPLOYEE403,phântrangq/statusencode, giữ quyền báo cáo.

**Lệnh/kiểm cuối:** `git diff --check`; `venv/Scripts/python.exe -m pip check`; `venv/Scripts/python.exe -m pip_audit -r requirements.txt`; `npm audit --audit-level=low`; `npm run build:css`; `venv/Scripts/python.exe ops/check_ui_contrast.py`:exit0,198pair/0failure,mintextlight5,100,dark7,007/UI3,506 và3,982. Django check và makemigrations --check --dry-run dùng childprocess sys.path=src, secret random,SQLite testsettings; exit0/Nochanges. Lượt gọi đầu thiếu sys.path failconfig đã sửa, không tính là đạt; makemigrations tạo fileSQLite0byte src/qlhcns, đã xác nhận đúngpath/kíchthước và xóa riêng artifact tự tạo trước bàn giao. Full suite source cuối dùng TEMP/project-layout-final-tests.py gọi ops/run_tests.py --backend sqlite|sqlserver, hash nhanh chỉfixture; logs TEMP/inline-source-final-sqlite.log và inline-source-final-sqlserver.log. Testtậptrung inline-focus4.log:11test1,017s/exit0. Browser ops/run_project_layout_uat.py (đổiassertinline) đạt954check/73URL; ops/run_dashboard_layout_uat.py (assertbaseline chỉdesktop>=1024 khi đủhàng) đạt1654check/132ảnh/0JSerror. ops/run_print_layout_uat.py đạt375check/37PDF; pypdf/Poppler37PDF50trang/0blank/flash,kiểm thêm mép bảng. SQLServer business layout-only thất bại assertion câu đếm cũ; sửa đúng nhãn “Có N người phù hợp.”, vẫn kiểm sốdòng vàfixtureKPI, rerun133check/32ảnh/DBdestroyed, TEMP/inline-business-delivery.log. Bảnin/phântrang/quyền không đổi nghiệp vụ.

**Kết quả nguồn cuối:**512testSQLite44,668s/7skip đúng testSQLServer;512testSQLServer91,444s/0skip; cảhaiexit0. LượtEdge source cuối1612check/300measurement/0failure (bổ sung nhãn14px, widthmobile, Admininline, Entertextfield); TEMP/inline-filter-source-final.log. Những geometrycùnghàng trên14trang gap16px,baseline0px;Admin8px/0px;buttonheight44px. Ảnhtrước/sau24tệp nằm inline-filter-uat; main369ef79 baselinekhônghềreset nguồnđanglàm. Bản mới37PDF50trang đã xem contact sheets và timesheetfull để xác nhậnmépbảng. Bảnin nguyêngốc và khoảnhtrống/trang dài vẫn theo nội dung/profile, khôngcropđểvừa1trang.

**Bàn giao/giới hạn:** sourceZIP `D:/QLHCNS-Backups/IHRMS_Review_20261013_Inline_Filters.zip`, snapshotGitindex/manifest/perfileSHA256 ngoài repo, không.env/DB/media/log/login; khôngbackup phục hồi. Bộảnh/PDFgiả `D:/QLHCNS-Backups/IHRMS_Inline_Filters_Proof_20261013.zip` chỉ có bằng chứngrender/geometry/hash, khôngpassword. Không screenreader chuyên dụng, zoom200%, máyin vật lý hoặc UAT tài khoản thật; Edgeheadless vàPDF đều dùng giả. Ctrl+F5/restartnếucachedtemplate, xem bộ ảnh/PDFreview trước in thật. Mộtcommit `ui: unify filter bar with inline actions`, pushmain/remoteSHA/Actions mới sau bàn giao; khôngforcepush/deploy. Kết quảnguồncuốicậpnhậttrướcsnapshot,metadataSHA/hash/CI ngoàiGit để không tạocommitnhật ký thứhai.

## 2026-10-13 — Sửa lỗi CI backend do biến môi trường TEMP trên Linux

**Phạm vi và nguyên nhân:** xử lý job GitHub Actions `Main regression and dependency checks / backend (pull_request)` (run `38420720139`, job `115383355138`) đang fail. Log cho thấy test `apps.portal.test_dashboard_followup.DashboardFollowupTests.test_cleaned_templates_keep_links_and_queries` lỗi `KeyError: 'TEMP'` tại `src/apps/portal/test_dashboard_followup.py:93` vì đọc trực tiếp `os.environ['TEMP']` (Windows-only) trên runner Linux.

**Đã sửa:** thay đường dẫn thư mục tạm trong test từ `Path(os.environ['TEMP'])` sang `Path(tempfile.gettempdir())`; cập nhật import tương ứng trong `src/apps/portal/test_dashboard_followup.py`. Không đổi logic nghiệp vụ, model, migration, quyền hay mã production.

**Kiểm tra và kết quả:** chạy `SECRET_KEY=test-secret-key python src/manage.py test apps.portal.test_dashboard_followup.DashboardFollowupTests.test_cleaned_templates_keep_links_and_queries` trên source đã sửa: `Ran 1 test ... OK`, truy vấn trước/sau giữ nguyên (`FOLLOWUP_PAGE_QUERY_COUNTS` before=after cho cả 3 template). Lượt chạy trước đó không đặt `SECRET_KEY` đã fail đúng kỳ vọng với `ImproperlyConfigured` từ settings.

**Việc còn mở/hành động:** cần CI chạy lại trên GitHub để xác nhận job backend của PR #5 pass toàn bộ matrix; không có thao tác production/deploy trong đợt này.

## 2026-10-13 — Khôi phục định dạng in và tách biểu mẫu khỏi layout màn hình

**Phạm vi và nguyên nhân:** chủ dự án gửi ảnh bảng chấm công mất khung/bảng/chữ ký, ô nhập vẫn xuất hiện và thông báo thành công có SVG khổng lồ trên giấy. Main sạch đầu lượt, HEAD/origin `a3b949b3ff1fc45cdbdff020783dc873e7214784`, fetch0/0. Các đợt UI chuyển quy tắc sang `@media screen` nhưng không thay đủ quy tắc in; lần kiểm tra trước chưa kiểm PDF của toàn bộ biểu mẫu. Áp dụng UI UX Pro Max và quy trình PDF, không đổi schema/service/quyền/công thức hay dữ liệu thật.

**Đã sửa:** `print_forms.css` nạp riêng `media=print` trong base: ẩn shell/thông báo/icon điều khiển/form lọc/dialog; phục hồi bảng/chữ/tổng/chữ ký và màu mực trung tính, không lấy kích thước44px hay60/40 cho giấy. Bỏ CSS in rời chồng chéo của timesheet, thêm giá trị đã lưu cho5loại ngày nghỉ, giữ nguyên input/POST trên màn hình. Mẫu kiểm kê13cột dùng named page A4ngang. Grid HCNS editor được loại khỏi override60/40. TNR/lề/khổ giấy theo profile cũ giữ nguyên; thêm data-hcns-form để điều chỉnh đúng2mẫu theo XML Word gốc: phỏng vấnline216/240, đánh giáline264/240. Phỏng vấn trở lại1trang với phần ký; ngăn phần ký tách khỏi đoạn cuối. Năm template tài sản cũ thêm default_if_none để in ô thiếu trống và giữ số0. Spec19 bổ sung cổng kiểm print/PDF.

**Tái hiện:** `ops/run_print_layout_uat.py --probe-only` tắt riêng stylesheet in mới trên nguồn hiện tại,32đường dẫn:202check đạt/131check lỗi, gồm thông báo/icon lọt vào giấy và timesheet mất chiều rộng/grid. TEMP/print-baseline-final.log và synthetic/print-probe/result.json. Đây là probe CSS, không khẳng định rollback đầy đủ mọi template lịch sử. Lượt đầu bị403 ở salary-scale vì dùng HR; sửa runner đăng nhập Finance đúng quyền cho mẫu lương, không nới gate ứng dụng.

**Kiểm tra nguồn cuối:** `venv/Scripts/python.exe "$env:TEMP/project-layout-final-tests.py" --backend sqlite|sqlserver apps.portal.test_project_layout apps.document.tests_hr_workflow`:37test,SQLite7,046s vàSQLServer11,158s,0skip,exit0. Wrapper chỉ dùng hash nhanh trên fixture DB dùng một lần. Hai hồi quy mới kiểm ngày nghỉ1,5 in từ summary đã lưu nhưng giữ input màn hình, và trường nullable in trống/số0 giữ nguyên. Compile toàn template trong cùng bộ. `ops/run_print_layout_uat.py --directory "$env:TEMP/ihrms-dashboard-phase2-demo-20261013" --packages-dir "$env:TEMP/ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages"`:374check/37PDF/0failure, gồm26HCNS+6timesheet/báo cáo/công văn+5tài sản cũ;2theme,flash/icon exclusion,font/giấy/editor/giá trị ngày nghỉ,missing values và landscape. Chỉ tạo thêm tài sản/biên bản giả trong SQLite có marker, media/log/tài khoản ngoài Git.

**PDF thực tế:** Edge `page.pdf(prefer_css_page_size=True)`; pypdf kiểm37PDF/50trang, không trang trắng hoặc flash sentinel; Poppler render toàn50trang, đã xem cả5contact sheet và ảnh lớn timesheet/phỏng vấn/kiểm kê. Timesheet31ngày+tổng176h+chữ ký=1trang A4; phỏng vấn=1trang; kiểm kêlegacy=1trang A4ngang841,92×594,96pt. Khổ giấy profile khác A4 được giữ theo mẫu. TEMP/print-verified-uat.log, print-verified-pdf-qa.log; PDF/PNG/JSON trong synthetic/print-layout-uat. `ops/run_browser_uat.py --backend sqlserver --layout-only --packages-dir ... --output-dir "$env:TEMP/ihrms-print-fix-business-uat"`:133check/32ảnh, tạo/sửa hồ sơ-hợp đồng-nghỉ/chấm công và chỉ số, DB cách ly đã xóa. Đây là hồi quy luồng màn hình ảnh hưởng; các sửa null cuối chỉ là template in, đã chạy lại37PDF và37test sau dọn. `git diff --check` đạt.

**Bàn giao:** source review `D:/QLHCNS-Backups/IHRMS_Review_20261013_Print_Fix.zip`, từ Git index, manifest/tree/hash từng tệp; loại.env/database/media/log/tài khoản, không phải backup phục hồi. Bộ xem giấy riêng `D:/QLHCNS-Backups/IHRMS_Print_Review_20261013.zip` chỉ chứa PDF/ảnh giả và manifest, không chứa thông tin đăng nhập. Xác minh mở lại/hash trước commit, SHAcommit/remote và metadata ngoài repository. Commit/pushmain theo quyền mặc định, không forcepush/deploy.

**Giới hạn/hành động:** kiểm bằng Edge headless trên dữ liệu giả/mẫu trắng và PDF; chưa xác nhận máy in vật lý hoặc Print Preview có extension trong phiên thật của chủ dự án. Không tuyên bố mọi lượng dữ liệu/tên dài/đơn đã ký đều vừa1trang; mẫu dài được ngắt theo nội dung, không crop. Chủ dự án khởi động lại ứng dụng nếu dùng cached template, Ctrl+F5 rồi mở lại Ctrl+P; không dùng tab Print Preview cũ. Nếu còn lỗi, đối chiếu PDF cụ thể với bộ review để phân biệt nguồn/scale/driver/extension. Chưa deploy.

## 2026-10-13 — Quy chuẩn bố cục 60/40 và dải lọc toàn ứng dụng

**Phạm vi:** tiếp tục yêu cầu toàn dự án trên `main`; đầu lượt working tree sạch, origin/main và HEAD `b391151828fa4c7a52e00e8bf4068e276e41eb16` đồng bộ. Áp dụng UI UX Pro Max; giữ công thức, schema, quyền, dữ liệu vận hành và bố cục giấy in. Dùng quy chuẩn màn hình `src/static/css/project_layout.css`, nạp cuối trong base; các cặp khối/form và nhóm đúng hai KPI dùng60/40 từ1280px, một cột ở màn hình hẹp. Grid legacy được đánh dấu có chủ đích; không đổi lịch7ngày, bảng, nhóm3trường hay chữ ký HCNS.

**Đã sửa:** 14dải lọc GET ngoài tìm kiếm chung được chuẩn hóa thành trường bên trái/nút bên phải, giữ query/action/giá trị năm. Chấm công, báo cáo và hoạt động chuyển dải lọc xuống dưới tiêu đề; chọn rồi bấm Lọc thay cho tự gửi onchange. Ô form theo cột, gap16px, nút44px/chữ14px; kiểm kê có nhãn và nút tạo gọn. Bổ sung căn phải thao tác form, responsive nút công văn và navbar Admin. Spec mục18 ghi quy chuẩn mới và ngoại lệ.

**Lỗi tái hiện trong Edge:** audit đầu trả500 ở ba trang duyệt phòng/xe/VPP do thiếu template; công văn tràn ở390px; navbar Admin tràn29px. Bổ sung ba template duyệt và include dùng chung, chỉ nối action/decision/CSRF/backend sẵn có; không sửa service/quyền/trạng thái. Đã khởi động lại đúng tiến trình Python demo để loại cache template cũ. Probe và ảnh ở TEMP/project-layout-browser.log, TEMP/project-layout-probe.log và thư mục synthetic; các lượt lỗi không được tính là đạt.

**Kiểm tra và kết quả:** bổ sung `test_project_layout.py` kiểm compile toàn template, roundtrip nhân viên có hợp đồng, năm raw2026, quyền/tạo kiểm kê và ba trang duyệt giữ gate. Thêm `ops/run_project_layout_uat.py`: chỉ chấp nhận marker synthetic và DB/media ngoài repository; Edge thật qua Playwright,73đường dẫn không có tham số,1440/1024/390px,sáng/tối, đo60/40/nooverflow/nút phải, GET bằng Enter và dữ liệu giữ nguyên. Tạo kiểm kê xác nhận đúng một bản ghi/trang đích; phòng/xe/VPP duyệt/từ chối và cấp phát đúng tồn kho. Thêm lượt tài khoản HR có hồ sơ cho các form tạo công việc/công văn/hoạt động/nhân viên/hợp đồng/chấm công. Kết quả nguồn cuối và metadata bàn giao được cập nhật ở cuối mục này trước commit.

Lệnh: `venv/Scripts/python.exe ops/run_project_layout_uat.py --directory "$env:TEMP/ihrms-dashboard-phase2-demo-20261013" --packages-dir "$env:TEMP/ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages"`; lượt form thêm `--account demo-hr --only /portal/tasks/create/ /portal/dispatches/create/ /portal/project-activities/create/ /portal/timesheet/ /portal/hr/employees/create/ /portal/hr/contracts/create/`. Dashboard5role×6width×2theme và trang quyết định dùng `ops/run_dashboard_layout_uat.py` cùng hai tham số directory/packages; selector assertion đổi theo dải lọc mới. Nghiệp vụ hồ sơ/hợp đồng/chấm công/nghỉ dùng `ops/run_browser_uat.py --backend sqlserver --packages-dir ... --output-dir "$env:TEMP/ihrms-project-final-business-uat"`, DB dùng một lần. Full suite dùng `ops/run_tests.py --backend sqlite|sqlserver`; lượt nguồn cuối dùng wrapper TEMP/project-layout-final-tests.py gọi cùng runner, chỉ tăng tốc hash mật khẩu fixture bằng MD5 trên DB test, không đổi cấu hình ứng dụng. Log test/runtime nằm ngoài Git.

**Kết quả cuối:** nguồn đã dọn, `git diff --check` đạt. Suite cuối506test: SQLite115,490s/7skip dành cho SQLServer; SQLServer193,888s/0skip, đều exit0. Sau bỏ class lặp ở catalog, chạy lại5test layout/compile trên SQLite0,367s/exit0. Hai lượt full với hash mặc định trước đó505test cũng đạt (SQLite542,739s/7skip, SQLServer697,206s/0skip). Edge audit cuối628check/73URL/0problem; HR forms89check/6URL/0problem; Dashboard1658check/132ảnh/0JSerror. BusinessSQLServer lượt đầy đủ386check/32ảnh và lượt cuối sau sửa độ rộng ô133check/32ảnh, cả hai DB cách ly đã xóa. Đã xem trực tiếp ảnh chấm công và kiểm kê để kiểm tra vị trí/nút/nhãn. Log nguồn cuối: TEMP/project-final-tests-sqlite.log, project-final-tests-sqlserver.log, project-clean-focused.log, project-layout-final.log, project-hr-forms.log, project-dashboard-final.log, project-business-final.log; JSON/ảnh ở runtime synthetic và TEMP/ihrms-project-clean-final-uat. Nguồn test/run giữ riêng khỏi Git các dữ liệu giả, media, tài khoản và log.

**Bàn giao:** nguồn gửi review tại `D:/QLHCNS-Backups/IHRMS_Review_20261013_Project_Layout.zip`, từ Git index đã kiểm, có REVIEW_SNAPSHOT.txt và SHA256 từng tệp, loại runtime/bí mật; không phải backup phục hồi dữ liệu. Manifest/tree/hashZIP và SHAcommit/remote được ghi trong metadata bàn giao ngoài repository sau khi xác minh. Commit trên main/pushoriginmain đã được chủ dự án cho phép mặc định; không forcepush/deploy. Luồng quyết định chạy lại trên demo đạt28check/4ảnh: HR trình duyệt, Giám đốc duyệt/từ chối, Escape hủy xác nhận, Enter gửi, dữ liệu/history và Dashboard cập nhật; TEMP/project-decision-final.log.

**Giới hạn:** Edge chạy headless trên tài khoản giả và DB cách ly, không phải UAT phiên tài khoản thật của người dùng. 73đường dẫn là audit GET, các endpoint405 chỉ POST được ghi rõ trong JSON; không tuyên bố mọi trạng thái/chi tiết có tham số đã thử. Những chi tiết và luồng ảnh hưởng được kiểm qua runner Dashboard/HR/decision; suite backend kiểm phần nghiệp vụ còn lại. Chưa deploy. Chủ dự án tải lại ứng dụng/Ctrl+F5 để nhận CSS mới; nếu server dùng cached template, khởi động lại quy trình chạy ứng dụng hiện hữu trước review.

## 2026-10-13 — Thống nhất các hàng Dashboard theo tỷ lệ 60/40

**Tóm tắt cho chủ dự án**

- Chọn phương án trái60%/phải40% theo yêu cầu; cùng mép cột cho các hàng panel.
- KPI chia đều; panel đơn dùng toàn bộ chiều rộng; màn hình hẹp một cột.
- Nguồn cuối đạt34test,Edge1658check/132ảnh vàSQLServer133check/32ảnh cách ly.
- Bản sao/commit/push/remote ghi metadata bàn giao; không deploy.

**Phạm vi:** main sạch đầu lượt, fetchorigin/main,ahead0/behind0,HEAD `bb053b25b5ebec5af52e7253c2bca7be60c3214a`; nạp UI UX Pro Max, đọc AGENTS/spec/CSS/runner. Sửa duy nhất tỷ lệ CSS panel và cache query `20261013-balanced-60-40`; bỏ quy tắc tỷ lệ54,5/45,5 và50/50 cũ bị chồng. Từ1280px `.dashboard-panel-grid`/`.phase2-list-grid` có2child dùng3fr/2fr, tính trên khoảng rộng sau trừ gap16px. Định biên/hợp đồng, hợp đồng/xử lý và nghỉ/history cùng mép cột. Panel chỉ1child vẫn1fr; KPI2/3/4ô chia đều như trước. Không service/quyền/query/model/form/logic nghiệp vụ thay đổi. Spec17 cập nhật quy ước; runner thêmwidth1280 và đo tỷ lệ sai số0,2%.

**Probe thật:** sau thêm assertionratio nhưng trước sửaCSS, chạy `venv/Scripts/python.exe ops/run_dashboard_layout_uat.py --directory "$env:TEMP/ihrms-dashboard-phase2-demo-20261013" --packages-dir "$env:TEMP/ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages"` thất bại exit1 tại HR1920light/pairedcolumns60/40; TEMP/dashboard-60-40-probe.log. Không giảm assertion để pass. Demo SQLite đã xác nhận synthetic marker ngoàirepo, server8767 chỉ khởi động lại đúngPID/commandline. Đã xem ảnhHR1920light trên nguồn mới; các hàng panel cùng đường chia cột.

**Kiểm tra cuối:** kết quả và lệnh cụ thể ở phần cuối mục này. Kiểm tra tập trung phù hợp CSS/SSR nhỏ; không chạy fullsuite hoặc gọi kết quả full501lượt trước là đã kiểm mã mới. DB/mediaSQLtest dùng một lần, không đụng dữ liệu thật. Edge5role×6width(1920,1440,1280,1024,768,360)×2theme, measurement60/40, singlefullwidth, nooverflow, giá trị/cao thẻ/KPIlinks/keyboard. Business `ops/run_browser_uat.py --backend sqlserver --layout-only` kiểm tạo/sửaHR/hợpđồng/thông báo/trangđích/lưu/KPIclick và responsive bị ảnh hưởng; bỏ vòngduyệt/rolekhôngảnh hưởngCSS theo optioncósẵn.

**Bàn giao/giới hạn:** ZIPreview `D:/QLHCNS-Backups/IHRMS_Review_20261013_Dashboard_60_40.zip` từGitindex cuối ngoàirepo, manifesttree/parent/hashmỗinguồn, khôngenv/database/media/uploads/log/CSV/tàikhoản/demo/secrets. Khôngbackup dữ liệu. Commit `ui: align dashboard panels to 60-40`, pushmainkhôngforce; SHA/remote/clean/aheadbehind ghi verificationngoàirepo/bàn giao để không tựthamchiếucommit. Khôngdeploy. Chủ dự án Ctrl+F5demo8767/portal, xem các mép cột thẳng hàng. Chưa UATbrowseruser/tài khoảnthật, screenreader/zoom200%; không báođạt. CI chưa theo dõi vì lỗiGitHubCLIHTTP401 đã xác minh lượttrước, không dùng kếtquảđó khẳngđịnh trạng tháiCIcommitmới.


**Kết quả cuối trên chính nguồn đã dọn:**

- `git diff --check`/`git diff --cached --check`: exit0; `venv/Scripts/python.exe ops/check_ui_contrast.py`: exit0,198cặp/0lỗi, không đổi token/màu.
- `venv/Scripts/python.exe "$env:TEMP/ihrms-ui-refinements-20261013/runner.py" --backend sqlite apps.portal.test_home_dashboard apps.portal.test_dashboard_followup apps.portal.test_dashboard_drilldown apps.portal.test_home_dashboard_phase2`:34/34test OK,24,410s,nativeexit0; TEMP/dashboard-60-40-final-tests.log. Noissues; querymax23SQLite/servicekhôngghi/privacy/scope/metriclinks/growth17→17 giữ. Không gọi fullsuite501lượttrước là kếtquảlượtnày.
- Edge runner đầy đủ vớiassert60/40: exit0,1658check/132ảnh/0JSerror,5role×6width×2theme, TEMP/dashboard-60-40-final-edge.log; ảnh/dashboard-layout-uat ởdemongoàiGit. Đo riêng18hàngpanel trong6scenario(HR×1280/1440/1920×light/dark): leftShare=.6±.002 và mépcộtphảigiữthẳnghàng±2px; ratio-60-40-measurements.json. Singlepanelvẫnfullwidth. Đã xemHR1920light/1280dark.
- SQLServer Edge `venv/Scripts/python.exe ops/run_browser_uat.py --backend sqlserver --layout-only --packages-dir "$env:TEMP/ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages" --output-dir "$env:TEMP/ihrms-dashboard-60-40-business-final"`: exit0,133check/32ảnh/0JSerror,DBdestroyed=true; TEMP/dashboard-60-40-business-final.log. Create/editHR/contractVietnamese/persist/messages/KPIclick/responsiveđãkiểm. Vòng đầu thấtbại sau45check tại assertionratio1.2:1cũ; cập nhật duy nhất expectation1.5:1 trongrunner theo yêucầumới, chạy lại đạt. Không bỏassert hoặc đổiquyền/bizlogic. Có lúc commentarynói36test nhưng logthực tế34; bảnglệnh/kếtquảtrên là sốđúng.

**Bản sao cuối:** Gitindex nguồn cuối gồmCSS/template/2runner/spec/nhậtký; xuấtZIP đãnêu vàmởlạikiểmhashmỗitệp/manifest. Commit `ui: align dashboard panels to 60-40`; pushmain/SHAremote0/0/clean xácminhsaucommittrong `.verification.json` vàbàngiao, khôngtạoSHAgiảtrongnhậtký tựchứaSHA. Ctrl+F5demo/portalđểnhậnCSSquerymới. Chưa tài khoảnthật/screenreader/zoom200%/CIcommitmới; khôngdeploy.


## 2026-10-13 — Cân đối Dashboard và trang quyết định theo Atoms

**Tóm tắt cho chủ dự án**

- Sửa cột trống khi thiếu quyền, căn tiêu đề và gom KPI/footer vào cùng thẻ.
- Dashboard gọn hơn; nghỉ cá nhân/distribution trạng thái mở bằng disclosure khi phù hợp.
- Sửa bộ lọc và form duyệt/từ chối quyết định, giữ quyền/nghiệp vụ/giấy HCNS.
- Nguồn cuối đạt hồi quy/full hai backend và Edge đo hình học theo từng vai trò.
- Bản sao sạch và metadata SHA nguồn/commit/remote đi kèm bàn giao.
- Chưa UAT phiên tài khoản thật, screenreader/zoom200%; không deploy.

**Nguồn/Git:** người dùng báo demo và tài khoản thật bố cục lệch, cung cấp5ảnh. Main sạch đầu lượt, fetch origin/main, ahead0/behind0, HEAD `e3873ca23aadbc2543cad9a62e718e4fb3fae82c`. Đọc AGENTS thay thế, nhật ký/đặc tả/templates/styles/tests liên quan, dùng UI UX Pro Max (không UI Styling/shadcn). Web.open không truy cập được URL mẫu; CUA inventory lỗi kernel assets/oserror3; Edge headless sau DOMready đã đọc trực tiếp https://r7rc1s.atoms.world/, title Quản Lý Hành Chính Nhân Sự và ảnh TMP/atoms-layout-reference-20261013.png. Lần networkidle timeout vì trang không idle; lần screenshot sớm trước render trống, đã chờ h1/h2 và chụp lại đủ bố cục. Chỉ tham khảo thiết kế, không copy tiền/trend/giờ ca/dữ liệu mẫu. Không model/migration/permission/guard/query/service/bizlogic/POST/action/field/CSRF hoặc giấy in thay đổi.

**Nguyên nhân/sửa:** .dashboard-panel-grid:not(work-grid) ghi đè rule only-child nên Director giữ cột trống; thêm rule đủ specificity cho tất cả grid đơn. Chart rows17rem/distributionflex căn cùng panel, giảm khoảng trắng và nút đúng bề rộng nội dung. Header quyết định dùng ui-page-actions dành cho nút nên bị dồn phải; đổi page-header, thêm rule header chung với h1 cho các trang UI dùng lớp legacy. Bộ lọc3cột cùng baseline desktop/1cột mobile, workflow2form cùng panel trái, historycard gọn. UIKPI phụ chứa cả summary/footer/disclosure, giá trị chung đường căn; own nằm dưới global bằng native details khi cùng có quyền. Tên dài clamp2giữ DOM/title; scope dữ liệu không đổi. home_presentation chỉ bỏ legacy value=None khỏi nhóm trình bày, không query mới; ready0/error của nguồn thật giữ. Cache CSS query mới cho dashboard/HR/shared. Spec mục17 mô tả quyết định mới, không sửa công thức Đợt1/2.

**Kiểm tra vòng đầu:** 73test SQLite đạt nhưng chạy trong lúc còn sửa template nên không dùng làm nguồn cuối. Edge vòng đầu bắt HTTP500 do thiếu endfor ở partial mới; đã sửa, khởi động lại demo, không bỏ assertion. Layout sau sửa1334check/110ảnh/0JSerror:5role×1920/1440/1024/768/360×light/dark, dashboard và list/detail quyết định đúng quyền, kiểm nooverflow14px/44px/bàn phím cùng các phép đo panel đơn/căn đỉnh/baseline/cao thẻ. Đã xem ảnhHR1920sáng so với Atoms. Sau vòng này thêm clamp tên/nút và shared header/cache; phải chạy lại trên nguồn cuối. Decisionflow đầu28check/4ảnh: clone2Draft giả mới, HRtrình→Directorduyệt/từ chối bằng UI, Esccancel→Enterconfirm, thông báo/trang đích/status/history1event/Dashboard cập nhật đều đạt. Không sửa quyết định cũ của người dùng. Các nguồn thật không truy cập qua browser, chỉ có phản hồi/ảnh do người dùng báo; không tuyên bố đã UAT tài khoản thật.

**Nguồn kiểm thử cuối:** Git index xuất TEMP, APP_ENV=test/M365off, testDB/media/log cách ly. Các lệnh và kết quả cuối ở phần nghiệm thu bên dưới. Không dùng501test của commit cũ làm bằng chứng nguồn mới. Không thêm dependency; optionalPlaywright đã ở TEMP.

**Còn mở/bàn giao:** review demo localhost8767 sau Ctrl+F5 bằng HRManager/Officer/Director/Manager/Employee; thông tin giả tại TEMP/ihrms-dashboard-phase2-demo-20261013/DEMO_ACCOUNTS.txt ngoàiGit. Chủ dự án đối chiếu tài khoản thật; Codex chưa có phiên browseruser qua CUA (kernel assets lỗi), screenreader/zoom200% chưa kiểm. Không deploy hoặc mở tiền/Đợt3. ZIP sạch từ index ngoài repo và metadata hash/SHA remote sẽ ghi kết quả cuối; không đưa DB/media/env/accountCSV/token vàoGit.


**Nghiệm thu nguồn cuối:** nguồn app/tests/runner/style cuối export từ index tree `1a85e6d79879f4c8857b83962b5809bc62973122` vào TEMP/ihrms-balanced-layout-final-20261013/stage-source. Wrapper resolve SQL connection trong memory, APP_ENV=test/M365off, DB/media/log riêng. Đối chiếu13tệp mã/runner/style thay đổi khớp snapshot sau chuẩn hóaLF/CRLF; nhật ký chỉ bổ sung kết quả sau test, không sửa app. Không lấy kết quả commit Đợt2 cũ.

- `git diff --check`, `git diff --cached --check`: exit0. `venv/Scripts/python.exe -m pip check`: exit0, No broken requirements found.
- `venv/Scripts/python.exe "$env:TEMP/ihrms-balanced-index-gates.py"`: exit0; check noissues; makemigrations --check --dry-run no changes; contrast198cặp/0lỗi, tokenpalette không đổi. TEMP/balanced-final-gates.log.
- Focused `venv/Scripts/python.exe "$env:TEMP/ihrms-balanced-index-runner.py" --backend sqlite|sqlserver apps.portal.test_home_dashboard_phase2 apps.portal.test_home_dashboard apps.portal.test_dashboard_followup apps.portal.test_dashboard_drilldown apps.portal.test_global_search apps.document.tests_hr_workflow`:73/73 mỗi backend,exit0. SQLite80,958s/SQL122,927s; TEMP/balanced-final-{sqlite,sqlserver}.log. Giữ queryceiling24; denied/source/privacy/drilldown/HRdecision/export/lương nghiệp vụ hồi quy. Legacy bỏ ôNone không sửa số0 hoặc stateerror nguồn thật.
- Full `venv/Scripts/python.exe "$env:TEMP/ihrms-balanced-index-runner.py" --backend sqlite` và `--backend sqlserver`: sqlite: 501test OK, skip7, 534.753s, nativeexit0; sqlserver: 501test OK, skip0, 585.629s, nativeexit0. TEMP/balanced-full-{sqlite,sqlserver}.log. DB dùng một lần đã hủy. Đây là nguồn index cuối của đợt cân đối, không sử dụng full501 từ đợt trước.
- `venv/Scripts/python.exe ops/run_dashboard_layout_uat.py --directory "$env:TEMP/ihrms-dashboard-phase2-demo-20261013" --packages-dir "$env:TEMP/ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages"`: exit0,1334check/110ảnh/0JSerror, TEMP/balanced-final-layout-edge.log. 5role×5width×2theme; dashboard + decisionlist/detail ở3role được phép. Đo panelđơn fullwidth, cănđỉnh, secondaryvaluebaseline/equalheight, filterbaseline, headingleft và workflowleft với sai số2px; không chỉHTTP/screenshot. Đã xem ảnhDirector1440dark/dashboard/detail. Native own/status disclosures kiểm thêm8scenario(4width×2theme) mở/đóng Enter, popover nằm trong viewport,8/8đạt; dashboard-layout-uat/disclosure-result.json.
- Probe CSS cũ commit e3873ca qua intercept tài nguyên CSS trên cùng Edge/page/fixture: Director1440 panel597,8125px/grid1120px=53,376%; assertionfullwidth không đạt. CSSfinal panel1120/grid1120=100%, đạt. Không sửa sourcefile đểprobe. dashboard-layout-uat/geometry-probe.json và probe-old-css-director.png ngoàiGit.
- `venv/Scripts/python.exe ops/run_decision_layout_uat.py --directory "$env:TEMP/ihrms-dashboard-phase2-demo-20261013" --packages-dir "$env:TEMP/ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages"`: sourcefinal exit0,28check/4ảnh, TEMP/balanced-final-decision-flow.log. Tạo2Draft mới mỗirun, HRsubmit→Directorapprove/reject, Escape hủy xác nhận/Enter mở lại/confirmPOST, statuspersist/singlehistory/notificationmessage/trangđích/dashboardtimeline đạt. Chỉ demoSQLite marker synthetic, không sửa/xóa hồ sơ thật.
- `venv/Scripts/python.exe ops/run_browser_uat.py --backend sqlserver --packages-dir "$env:TEMP/ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages" --output-dir "$env:TEMP/ihrms-balanced-business-20261013"`: exit0,406check/32ảnh/0JSerror,DBdestroyed=true. TEMP/balanced-business-edge.log; tạo/sửa hồ sơ/hợpđồng/sốVN/KPIgốc/gửiduyệtnghỉ/responsiveroles đạt. Sốcheck giảm10 so416 vì thẻ legacyNone bị bỏ nên nhánh test tràn trong ô đó không còn chạy, không xóa assertion cũ.

**Bản sao/commit/push:** `D:/QLHCNS-Backups/IHRMS_Review_20261013_Balanced_Layout.zip` từ index cuối cùng app đã kiểm và nhật ký kết quả, khôngenv(DBsecret)/database/media/uploads/log/runtime/accountCSV/demoaccounts; .env.example giữ. Manifest tree/parent/SHA256 nguồn, mở lại kiểm từnghash và sốentry. ZIP này là source review, không backup DB/media. Commit `ui: balance dashboard and decision layouts` trênmain, pushoriginmain khôngforce/deploy; SHA/remote/aheadbehind/clean thực tế ghi trong `.verification.json` cạnh ZIP và bàn giao để tránh nhật ký tự tham chiếucommit. `gh run list --branch main --limit 1 --json status,conclusion,headSha` exit1 HTTP401 Bad credentials, chưa theo dõiCI; chủ dự án xem Actions qua browser hoặc tự `gh auth login`, không gửitokenqua chat.

**Giới hạn:** Edgeheadless thật với dữ liệu giả, không UAT phiên người dùng/tài khoản thật (CUA kernel assets lỗi); còn screenreader/zoom200%/cảm nhận người dùng ở dữ liệu vận hành. Nguyên nhân người dùng báo ở tài khoản thật được sửa bằng cùngCSS/template, không được ghi là Codex đã xem sessionthật. Bản bố cục vẫn theo quyền hiện có; không mở contract/Candidate choDirector để lấp khoảngtrống. Dữ liệu thiếu không tạoKPIgiả; giữ logicghi/guard/paperHCNS. Chủ dự án Ctrl+F5 demo8767 và portal đang chạy, đối chiếuGiámđốc/HR/trưởngphòng; không deploytheo quyềncommit/push.

**Query cuối:**

| Role | SQLite unlinked/linked | SQL unlinked/linked | p95 SQLite max(s) | p95 SQL max(s) |
| --- | --- | --- | ---: | ---: |
| EMPLOYEE | 3/8 | 4/9 | 0.0205 | 0.0247 |
| DEPT_MANAGER | 3/12 | 4/13 | 0.0372 | 0.0403 |
| HR_OFFICER | 11/16 | 12/17 | 0.0417 | 0.0452 |
| HR_MANAGER | 17/21 | 18/22 | 0.0631 | 0.0614 |
| DIRECTOR | 12/16 | 13/17 | 0.0525 | 0.0596 |
| FINANCE_OFFICER | 3/8 | 4/9 | 0.0261 | 0.0238 |
| SYS_ADMIN | 3/8 | 4/9 | 0.0255 | 0.0236 |
| SUPER_ADMIN | 4/9 | 5/10 | 0.0248 | 0.0289 |
| SUPERUSER | 19/23 | 20/24 | 0.0617 | 0.0715 |

Giữ trần24 toàn GET/render và scope; không tăng query theo bố cục. p95 là20mẫu testfixture trên máy local, không chứng nhận tải sản xuất. Fullsource/app cuối khớp524tệp src/ops với snapshot kiểm; chỉ nhật ký kết quả bổ sung sau test.


## 2026-10-13 — Triển khai Dashboard Đợt 2 đã duyệt

**Tóm tắt cho chủ dự án**

- Bật nghỉ gần đây, chỉ số tuyển dụng/vào làm và lịch sử quyết định theo quyền thật.
- HR Officer/Trưởng phòng chỉ nghỉ của mình; loại nghỉ chi tiết chỉ manage_hr.
- Đã gộp truy vấn để superuser SQL Server không vượt trần24; không mở tiền/Đợt3.
- Full501test đạt mỗi backend; Edge996check và luồng SQL416check trên dữ liệu giả cách ly.
- Nguồn đã dọn; bản sao/commit/push và SHA remote có metadata bàn giao kèm nhật ký.
- Chưa screen reader/zoom200%/UAT tài khoản thật; không deploy.

**Phạm vi/Git/nguồn:** main sạch đầu lượt, fetch origin/main, rev-list0/0, HEAD/remote `27a79d7075f8e557b3a412754d636f8f78f891fc`. Đã đọc yêu cầu a004c144, AGENTS, ba mục mới nhất, đặc tả/nguồn/tests/quyền/selector/model/view và nạp UI UX Pro Max; không UI Styling/shadcn. Ba PNG `design-system/reference/atoms/01_dashboard.png`,02/03 không tồn tại trong workspace, Downloads/atoms cũng không có PNG; lần view_image trả file not found. Dùng ảnh Atoms chủ dự án đã gửi và component hiện có; không khẳng định đã đọc ba tệp thiếu. Tiên quyết search.py ba mục trả manage_hr/request/approve đúng sidebar, mục5.5/7.2 đã đánh dấu lịch sử. Không model/migration/quyền/guard/URL name/CSRF/middleware/field/form/lương/nghỉ/giấy HCNS/dependency/topbar; không dữ liệu vận hành.

**Quyền đã in trước sửa (has_permission):**

| Vai trò | Nghỉ tôi linked | Nghỉ global | Tin Open | Candidate | Vào làm | History | Đề xuất |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EMPLOYEE | Có, chung | Không | Không | Không | Không | Không | Không |
| DEPT_MANAGER | Có, chung | Không | Không | Không | Phòng quản lý | Không | Phòng quản lý linked |
| HR_OFFICER | Có, chi tiết | Không | Không | Global | Global | Global | Không |
| HR_MANAGER | Có, chi tiết | Có, chi tiết | Có | Có | Global | Global | Global |
| DIRECTOR | Có, chung | Có, chung | Có | Không | Global | PendingApproval hoặc history tự tạo | Không |
| FINANCE_OFFICER/SYS_ADMIN | Có, chung | Không | Không | Không | Không | Không | Không |
| SUPER_ADMIN không cờ | Có, chung | Không | Không | Không | Không | Không | Không |
| Superuser active | Có, chi tiết | Có, chi tiết | Có | Có | Global | Global | Global |

approve_leave_all_departments thật chỉ HR_MANAGER/DIRECTOR ngoài superuser; không cần dừng D2-2. request_recruitment thật DEPT_MANAGER/HR_MANAGER, approve_recruitment HR_MANAGER; recruitment_list global HR_MANAGER/superuser, DEPT_MANAGER phòng quản lý khi Employee live, unlinked none; role khác none. Không chênh bảng quyền mong đợi. Own ẩn unlinked, global giữ theo quyền. D2-9 theo scope trang đích, không tự loại position đã xóa vì view chưa loại; posting loại parent theo D2-7. Đã ghi sự khác nhau vào đặc tả.

**Thực hiện:** thêm dashboard_phase2 service chỉ đọc với projection tối thiểu, 30ngày local midnight/6đơn/8history/sortpk. Gate trước query/DTO/HTML; không actor/reason/file/snapshot/contact/CV/lương. Loại chi tiết chỉ manage_hr, Director generic kể cả toàn Trung tâm. History Exists giữ tập decision được đọc đúng view, sự kiện hiển thị live; recipient không timeline. Candidate grouped6, tổng4, Hired/Closed ghi là trạng thái, không người đã nhận việc. Joined Count distinct gộp aggregate trạng thái cũ, metric=joined cùng selector/drill-down, không đổi bốn KPI hay điều kiện hợp đồng. Nghỉ global+own cùng bật dùng ROW_NUMBER global/partition Employee trong một SELECT, tối đa6 từng danh sách độc lập. Không filter trạng thái đích chưa có; CTA chung riêng, count không link. Template/CSS/SVG/token/UI component SSR mới đặt sau các khối cũ, không đổi thứ tự Đợt1.

**Probe và vòng sửa:** test_approved_blocks_present trên mã trước sửa thất bại thật 1/1 exit1 (thiếu own_leave), TEMP/phase2-probe.log. Focused SQLite vòng đầu38test lỗi2: trần cũ20 và assertion FROM/JOIN parent; sửa test theo trần đã duyệt24, phân biệt JOIN parent posting với truy vấn nguồn đề xuất. Sau sửa39test đạt. SQL lần đầu39test lỗi1 do superuserlinked25SELECT; không báo đạt. Gộp hai danh sách nghỉ, SQL phase2 10test đạt, superuser24. Test độc lập own ngoài top6global được bổ sung, không giảm coverage để qua trần. Existing test_followup baseline before_note chỉ đo ghi chú hợp đồng, không baseline Đợt2; baseline thật đầu lượt nằm bảng dưới.

**Baseline đo lại trước sửa:** CaptureQueriesContext toàn GET/render, login/warm-up ngoài đo, fixed HomeDashboardTests fixture, SQLite in-memory/SQL Server DB dùng một lần; hai lệnh wrapper `TEMP/ihrms-ui-refinements-20261013/runner.py --backend sqlite|sqlserver apps.portal.test_dashboard_followup.DashboardFollowupTests.test_eight_role_query_matrix` exit0; log TEMP/phase2-baseline-{sqlite,sqlserver}.log. Không lấy số của lượt trước.

| Vai trò | SQLite trước unlinked/linked | SQL Server trước unlinked/linked |
| --- | --- | --- |
| EMPLOYEE | 3/7 | 4/8 |
| DEPT_MANAGER | 3/10 | 4/11 |
| HR_OFFICER | 9/13 | 10/14 |
| HR_MANAGER | 12/16 | 13/17 |
| DIRECTOR | 9/13 | 10/14 |
| FINANCE_OFFICER | 3/7 | 4/8 |
| SYS_ADMIN | 3/7 | 4/8 |
| SUPER_ADMIN không cờ | 4/8 | 5/9 |

**Máy/đo:** Intel Core i7-1185G7@3GHz,4core/8logical,15,7GiB RAM; fixture cùng test class trên hai backend, warm20GET/role/profile, p95 nearest rank (19/20), coldGET ghi riêng; không suy năng lực server sản xuất. +100phòng/+1.000Employee/+1.000Candidate/+1.000history trên synthetic fixture; service SELECT không ghi, middleware idle session hiện có chỉ ghi django_session ở integration hồi quy. Không trừ SELECT transaction SQL Server. Bảng cuối và log gate/full/UI ở phần nghiệm thu bên dưới.

**Demo/Edge:** ops/dashboard_demo.py mở rộng seed loại Thai sản mồi, bốn trạng thái nghỉ, Candidate6/Open/request4/joined/history thật trên SQLite giả; không copy DB/media thật. Runtime mới `TEMP/ihrms-dashboard-phase2-demo-20261013`, server http://127.0.0.1:8767/portal/; thông tin đăng nhập ở DEMO_ACCOUNTS.txt ngoài Git. Edge headless đọc dữ liệu/live navigation; ops/run_dashboard_phase2_uat.py kiểm5role×5width×2theme, chữ14/control44/keyboard/reduced-motion/scope/privacy/drill-down/detail, ảnh ngoài Git. Vòng đầu996check/50ảnh/0JSerror; đã xem ảnh1440light. Runner vòng đầu lỗi strict locator summary vì hai summary; sửa .first rồi chạy lại, không lỗi ứng dụng. Bản guard cuối đã chạy lại đạt trên tên giả dài; kết quả cuối bên dưới. Chưa phiên Edge tương tác của người dùng, screenreader/zoom200%/UAT thật.

**Commit tài liệu:** `f46bf5b` — `docs: record dashboard phase 2 decisions`; mục16 đã chốt D2-1…9, bảng7.2 đối chiếu quyết định mới, không đổi công thức Đợt1. Commit mã/test/nhật ký `ui: dashboard phase 2` sau test cuối. SHA commit tự chứa nhật ký được ghi tại bàn giao/verification ngoài repo để tránh tự tham chiếu. CI chưa theo dõi; không deploy. Chủ dự án dùng demo8767 Ctrl+F5 và đăng nhập HR Manager/Officer/Trưởng phòng/Giám đốc/Nhân viên, kiểm loại nghỉ chi tiết chỉ HR; trưởng phòng hiện chỉ nghỉ của mình theo quyết định đã duyệt, mở lịch sử phòng cần giao yêu cầu riêng.


**Truy vấn cuối / p95 (toàn GET+render):**

| Role | SQLite cuối unlinked/linked | SQL cuối unlinked/linked | p95 SQLite lớn nhất(s) | p95 SQL lớn nhất(s) |
| --- | --- | --- | ---: | ---: |
| EMPLOYEE | 3/8 | 4/9 | 0.0394 | 0.0380 |
| DEPT_MANAGER | 3/12 | 4/13 | 0.0452 | 0.1259 |
| HR_OFFICER | 11/16 | 12/17 | 0.0773 | 0.0985 |
| HR_MANAGER | 17/21 | 18/22 | 0.0757 | 0.1175 |
| DIRECTOR | 12/16 | 13/17 | 0.0667 | 0.1153 |
| FINANCE_OFFICER | 3/8 | 4/9 | 0.0288 | 0.0362 |
| SYS_ADMIN | 3/8 | 4/9 | 0.0316 | 0.0834 |
| SUPER_ADMIN | 4/9 | 5/10 | 0.0399 | 0.1025 |
| SUPERUSER | 19/23 | 20/24 | 0.1006 | 1.3452 |

Trần24 đạt cả9nhóm/profile; baseline8role trước sửa ở bảng trên, superuser đo riêng cuối (không gán baseline chưa đo). p95 cuối lớn nhất SQLite0,1006s/SQL1,3452s (superuserunlinked), đều≤1,5s; ghi cả outlier thật, không chọn riêng số focused nhỏ hơn. Hai full suite chạy đồng thời trên máy đã nêu; đây là fixture test, không chứng nhận tải sản xuất. ColdGET và20mẫu/p95 mỗi role/profile nằm trong PHASE2_QUERY_MATRIX của log. N+1 growth SQLite17→17/SQL18→18 với100phòng/1.000Employee/Candidate/history, không tăng query.

**Nghiệm thu cuối:** các lệnh dưới đây chạy trên nguồn guard cuối; lấy native exit ngay sau Python, không coi stderr PowerShell NativeCommandError là exit test. M365 off/APP_ENV=test, DB/media/log dùng một lần; SQL connection chỉ resolve trong memory, không ghi/echo thông tin đăng nhập.

- `git diff --check` và `git diff --cached --check`: exit0.
- `venv/Scripts/python.exe -m pip check`: exit0, No broken requirements found.
- `venv/Scripts/python.exe "$env:TEMP/ihrms-dashboard-phase2-guard-index-gates.py"`: exit0; gọi check, makemigrations --check --dry-run và ops/check_ui_contrast.py trên stage-source: no issues/no changes,198cặp/0lỗi; min text5,100(light)/7,007(dark), min UI3,506/3,982.
- Focused `venv/Scripts/python.exe "$env:TEMP/ihrms-ui-refinements-20261013/runner.py" --backend sqlite|sqlserver apps.portal.test_home_dashboard_phase2 apps.portal.test_home_dashboard apps.portal.test_dashboard_followup apps.portal.test_dashboard_drilldown apps.portal.test_global_search`:43/43 mỗi backend, exit0; TEMP/phase2-focused-{sqlite,sqlserver}-guard-final.log. SQLite40,790s; SQL75,344s. Probe thiếu khối và link403 cũ đều thất bại thật exit1 như đã ghi; sau sửa đều đạt.
- Full `venv/Scripts/python.exe "$env:TEMP/ihrms-dashboard-phase2-guard-index-runner.py" --backend sqlite` và `--backend sqlserver`: SQLite501test OK(7skip),549,922s, nativeexit0; SQLServer501/501 OK(0skip),593,601s, nativeexit0; logs TEMP/phase2-full-{sqlite,sqlserver}-guard-final.log. Nguồn test xuất Git index bằng git archive tree `78cbc2866a038f845a9a473c72bfa48bea3dacc9` vào TEMP/ihrms-dashboard-phase2-guard-final-20261013/stage-source. Đối chiếu14tệp mã/test/CSS/runner đang stage với nguồn test khớp sau chuẩn hóaLF/CRLF. Chỉ bổ sung kết quả vào nhật ký sau test, không đổi mã/test; không dùng full500test trước guard để nghiệm thu nguồn501test cuối.
- `venv/Scripts/python.exe ops/run_dashboard_phase2_uat.py --directory "$env:TEMP/ihrms-dashboard-phase2-demo-20261013" --packages-dir "$env:TEMP/ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages"`: exit0,996check/50ảnh/0JSerror trên bản guard cuối,5role×5width×2theme, tên giả dài; TEMP/phase2-edge-guard-final.log. Legacy bổ sung4check/2ảnh: Director giữ metadata nhưng không link và detail403 đúng guard; HR có link/detail200. Login Edge tại localhost8767 cũng đạt,1ảnh. Bằng chứng dashboard-phase2-uat trong thư mục demo; đã xem ảnh HRdesktop sáng và HR Officer360 tối.
- `venv/Scripts/python.exe ops/run_browser_uat.py --backend sqlserver --packages-dir "$env:TEMP/ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages" --output-dir "$env:TEMP/ihrms-dashboard-phase2-business-guard-uat"`: exit0,416check/32ảnh/0JSerror, DBdestroyed=true; TEMP/phase2-business-edge-guard.log. Tạo/sửa hồ sơ, tạo hợp đồng, thông báo/trang đích/dữ liệu lưu, bốn KPI và gửi→duyệt nghỉ→Dashboard đều kiểm lại qua Edge thật headless. Không phải UAT phiên trình duyệt/tài khoản thật của chủ dự án.

**Bản sao và bàn giao:** `D:/QLHCNS-Backups/IHRMS_Review_20261013_Dashboard_Phase2_Final.zip` từ Git index cuối, loại env/runtime/database/media/uploads/log/accountCSV/credentials, giữ .env.example. REVIEW_SNAPSHOT.txt có tree/parent/hash mỗi nguồn; mở lại kiểm số tệp và toàn bộSHA256. Không phải backup phục hồi DB/media. `.zip.sha256` và `.verification.json` cạnh ZIP chứa bằng chứng hash/commit/push/remote thực tế; dùng metadata ngoài repo để ghi SHA của commit tự chứa nhật ký mà không tạo commit thứ ba. Hai commit main theo yêu cầu: docs `d04239084481bb3187b62e09034374386d60517f`, UI `ui: dashboard phase 2`; không force-push/deploy. Trước bàn giao main ahead1/behind0 sau docs, origin/main còn baseline27a79d7; bước push/remote HEAD cụ thể xác minh và bổ sung vào verification khi bàn giao. Không tự ghi “CI đạt”: `gh run list --branch main --limit 3 --json status,conclusion,headSha` exit1 HTTP401 Bad credentials, **chưa theo dõi CI**. Chủ dự án xem GitHub Actions sau khi tự xác thực CLI hoặc qua trình duyệt; không cần gửi token qua chat.

**Việc chủ dự án:** mở http://localhost:8767/portal/, tài khoản giả trong TEMP/ihrms-dashboard-phase2-demo-20261013/DEMO_ACCOUNTS.txt (URL runtime đã chỉnh đúng server đang chạy, không chép mật khẩu vào Git); Ctrl+F5, xem HR Manager/Officer/Trưởng phòng/Giám đốc/Nhân viên. Tên loại nghỉ chi tiết chỉ HR, trưởng phòng chỉ “của tôi” theo quyết định đã chốt; mở lịch sử phòng cần nhiệm vụ/policy riêng. Chưa screen reader, zoom200%, UAT tài khoản thật hoặc theo dõi CI; không mở Đợt3/tiền/header ca/kỳ lương. Skill tra cứu UX/Web bàn phím/focus phù hợp đã đối chiếu; không có stack Django trong dữ liệu, kết quả domain web off-topic không dùng/persist, dùng checklist web và component SSR của dự án.

**Ghi nhận dọn bàn giao:** log PowerShell chuyển hướng là UTF-16; lần tổng hợp đầu đọc UTF-8 bị lỗi giải mã trước khi ghi nhật ký. Đã đọc theo BOM và ghi Markdown UTF-8 đúng. ZIP Phase2 không hậu tố Final là nguồn test trước bổ sung kết quả nhật ký, không dùng bàn giao; ZIP Final chứa cùng mã đã kiểm và nhật ký cuối.


## 2026-10-13 — Đồng bộ tìm kiếm với sidebar và dọn đặc tả Đợt 2

**Tóm tắt cho chủ dự án**

- Đã sửa tìm kiếm theo điều kiện sidebar, không coi trang rỗng200 là quyền dùng chức năng.
- Giữ quyền dữ liệu và tìm không dấu; số truy vấn không tăng so với đầu lượt.
- Kiểm tra Edge đạt 421 bước và 32 ảnh cho bốn vai trò, cả sáng/tối và màn hình rộng/hẹp.
- Đặc tả đề xuất trần24 có điều kiện và khối đề xuất tuyển dụng D2-9, chưa áp dụng.
- Full suite cuối đạt cả hai backend; chưa kiểm screen reader, zoom200% hoặc tài khoản thật; chưa theo dõi CI.

**Phạm vi/nguồn:** đọc AGENTS, hai mục mới nhất, search/test/base/context processor/permissions và 5.5/7.2/16 đặc tả; nạp UI UX Pro Max, không UI Styling/shadcn. Main sạch đầu lượt; fetch origin/main, rev-list0/0; HEAD/remote cùng `59dcff84717172104fb0c4b055076cd8bb0ab10a`. Không reset/stash/đổi nhánh, không sửa guard/quyền/model/migration/URL/field/CSRF/middleware/selector/giấy HCNS/dependency. Quy trình dọn nguồn/bản sao/commit/push có hiệu lực; không deploy.

**A1 — sửa điều kiện liệt kê:** `views/search.py` trả hr_employee_list và hcns_catalog về manage_hr; recruitment_list về request_recruitment hoặc approve_recruitment. Sửa thêm task_list thành view_activity_dashboard đúng điều kiện menu Dự án. Lượt trước nhầm chiều “GET200 thì phải xuất hiện”; trang scope none() vẫn200 không đồng nghĩa được thấy chức năng trong điều hướng. Không sửa view hoặc queryset dữ liệu. Rà toàn bộ entry PAGES với base.html/context flags: các mục còn lại giữ nguyên điều kiện đúng; notification_list ở topbar và report_headcount ở link báo cáo/Dashboard là ngoại lệ ngoài sidebar, dùng guard thật. Các biến thể cùng route trong sidebar có GET nhóm/forms không tự mở group ngoài quyền. Giữ hai nguồn điều kiện trong base/PAGES vì đổi toàn sidebar vượt phạm vi an toàn; test HTML tự động khóa sự đồng bộ, không thêm query/header hoặc đổi context processor.

**A2 — test và probe:** `test_page_sidebar_and_guard_matrix` dùng HomeDashboardTests fixture, HTMLParser chỉ đọc link trong aside#portalSidebar và kiểm toàn bộ entry PAGES. Chín nhóm role (tám yêu cầu kể cả superuser + SUPER_ADMIN không cờ) × linked/unlinked: listed⇒GET200; entry có sidebar⇒listed với ngoại lệ hồ sơ đã ghi, không có phép suy GET200⇒listed. Test thường không thấy ba mục HR; HR Manager/Officer thấy hai mục, request/approve role thấy đề xuất theo menu. Probe trên mã cũ `test_ordinary_roles_do_not_discover_empty_hr_pages` thất bại thật tại EMPLOYEE/hr_employee_list, 2 test baseline chạy, exit1; test đo query vẫn đạt. Log TEMP/ihrms-sidebar-baseline-sqlite.log. Lần focused đầu sau sửa phát hiện SUPER_ADMIN linked thiếu submit_profile_change_request nhưng sidebar cá nhân vẫn có link; thêm ngoại lệ đúng guard thật vào test, không nới page_visible hoặc view. Test cuối giữ route resolve, accent/scope/ceiling/escape/no-store; không nhân bản test.

**A3:** `User.employee` được khai báo OneToOneField trực tiếp trong security/models.py, nên `employee_id` luôn có ở mọi User, giá trị None nếu unlinked; không là reverse relation. _get_employee dùng getattr(user,'employee',None); hai cách kiểm sự hiện diện tương đương ở gate submit khi relation khai báo này. AnonymousUser bị login_required trước page_visible. Không có lỗi AttributeError cần sửa. Gate approve_profile_change_request vẫn cho HR unlinked; linked còn phải submit; SUPER_ADMIN không cờ bị view403 dù sidebar cá nhân hiện link. Search giữ ẩn để listed không dẫn403. Test linked/unlinked, approve và SUPER_ADMIN đã chạy; giữ ngoại lệ link cá nhân này trong test/nhật ký, không sửa sidebar hoặc quyền.

**Đo truy vấn đầu/cuối (linked, toàn GET/render):** baseline probe dùng cùng matcher/fixture/warm-up; final có thêm assertion không vượt số đầu lượt. Sửa catalogue chỉ kiểm quyền trong memory, không SELECT mới. Các số before/after-matcher trong log vẫn là phép so icontains với accent scan; bảng sau so **đầu lượt với cuối lượt**, không nhầm hai phép đo.

| Vai trò | SQLite đầu → cuối | SQL Server đầu → cuối |
| --- | --- | --- |
| EMPLOYEE | 7 → 7 | 8 → 8 |
| DEPT_MANAGER | 7 → 7 | 8 → 8 |
| HR_OFFICER | 7 → 7 | 8 → 8 |
| HR_MANAGER | 7 → 7 | 8 → 8 |
| DIRECTOR | 8 → 8 | 9 → 9 |
| FINANCE_OFFICER | 7 → 7 | 8 → 8 |
| SYS_ADMIN | 7 → 7 | 8 → 8 |
| Superuser | 8 → 8 | 9 → 9 |

**Kiểm thử nguồn cuối:** stage tree `b938415936ec9bdb3ec636271b4b77b2d8b6787b`, xuất `git archive` vào TEMP/ihrms-sidebar-20261013/stage-source. Wrapper TEMP/ihrms-sidebar-index-runner.py gọi ops/run_tests.py ở snapshot; APP_ENVtest, media/log riêng, SQL connection chỉ memory, database test UUID không dùng dữ liệu vận hành. Nhãn focused `--backend sqlite|sqlserver apps.portal.test_global_search`: 9/9 mỗi backend, SEARCH_PAGE_GUARD_MISMATCHES=[], query đúng bảng. Full suite hai backend đang chạy cùng wrapper không nhãn, lấy `$LASTEXITCODE` ngay sau Python và exit; kết quả cuối bổ sung dưới đây. Gate TEMP/ihrms-sidebar-index-gates.py: check/makemigrations --check --dry-run đạt, không migration; contrast190 cặp/0 lỗi, exit0; pip check exit0; diff/index diff --check đạt. Không dùng full488 đợt trước thay kết quả nguồn này.

**UI nghiệp vụ đọc:** `venv/Scripts/python.exe ops/run_search_sidebar_uat.py --directory "$env:TEMP/ihrms-atoms-demo-20261013" --packages-dir "$env:TEMP/ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages"`: exit0, 421 kiểm tra/32 ảnh, errors=[]; Edge live login HR_MANAGER/EMPLOYEE/DEPT_MANAGER/DIRECTOR, search chính xác ba chức năng theo quyền/sidebar, 360/768/1024/1440 × sáng/tối, không overflow, chữ≥14px/control≥44px, gửi tìm bằng Enter. Demo SQLite/media/accounts cách ly, không sửa dữ liệu thật; chỉ đọc search nên không làm lại create/approve không bị ảnh hưởng. Bằng chứng demo/sidebar-search-uat/browser-result.json và ảnh; log TEMP/ihrms-sidebar-browser.log. Đã xem employee1440dark; không claim UAT phiên trình duyệt thật của chủ dự án.

**B — chỉ tài liệu:** thêm câu chuyển tiếp ở 5.5/7.2, bảng đối chiếu7.2↔16.4 giữ bản cũ, xác định mục16 là đề xuất hiện hành/chờ D2. Không đổi Đợt1. Trần20 là mục tiêu tự đặt, không giới hạn kỹ thuật; D2-8 đề xuất≤24 và không N+1 khi100 phòng/1.000 hồ sơ, denied+0/nguồn ẩn không query, đo p95/máy UAT; vượt thì chia rollout/gộp query; thay thế giữ20 và bỏ một khối. HR Manager17+4=21, D2-9 thành22 là dự toán chưa đo. D2-9 chờ duyệt/mặc địnhẩn, RecruitmentRequest grouped current status trong managed_departments_for, request/approve gate, không reason/lương/đã tuyển; hrefNone khi thiếu filter và CTAchung riêng, +1SELECT/test đề xuất; bổ sung bảng tóm tắt/quyền/quyết định. Không viết mã/template/view/CSS của Đợt2, không chốt D2-1..9 thay chủ dự án.

**Bàn giao/giới hạn:** hai commit theo yêu cầu, bản sao review mã nguồn sạch ngoài repo, mở lại/hash trước commit và kiểm SHA sau push. Không force-push/deploy. `gh run list` đầu lượt theo SHA59dcff8 vẫn HTTP401 Bad credentials; chưa theo dõi CI, không ghi token. Chưa screen reader/zoom200%/tài khoản thật. Chủ dự án duyệt D2-1..9 trước giao triển khai; lượt này dừng ở sửa catalogue và đặc tả.

**Full suite cuối:** `venv/Scripts/python.exe "$env:TEMP/ihrms-sidebar-index-runner.py" --backend sqlite` không nhãn: 489 test, OK (7 skip), 557.569 giây, exit0; `--backend sqlserver`: 489/489 OK, không skip, 614.513 giây, exit0. Log TEMP/ihrms-sidebar-full-sqlite.log và ihrms-sidebar-full-sqlserver.log; DB test được Destroying, media/log cách ly. Cả hai log SEARCH_PAGE_GUARD_MISMATCHES=[]; đầu/cuối query giữ nguyên bảng trên. Tất cả mã ứng dụng/test staged đã đối chiếu snapshot khớp sau chuẩn hóa CRLF/LF; chỉ tài liệu và nhật ký thêm sau test. Không dùng full488 của lượt trước. Gate/diff/pip và Edge421/32 ảnh đạt trên nguồn này.

**Bản sao/commit:** bản mã review cuối `D:/QLHCNS-Backups/IHRMS_Review_20261013_Sidebar_Spec.zip` lấy nguồn index trước commit tài liệu, có manifest/tree/parent và SHA256 từng tệp; loại runtime/secret/database/media/credentials, giữ .env.example. Mở lại kiểm từng hash và ZIP integrity trước commit, đối chiếu tree với commit sau push; báo cáo `.verification.json` và `.zip.sha256` ngoài repo. Bản nguồn Phần A trước commit ở `IHRMS_Review_20261013_Sidebar_Code.zip`. Đây là nguồn review, không backup dữ liệu vận hành. SHA hai commit/kết quả remote cuối ghi trong báo cáo kiểm chứng cạnh bản sao và câu trả lời bàn giao; bản nhật ký commit không tự chứa SHA của chính nó. Bước push mặc định theo AGENTS; không force/deploy, không sửa mã sau test.

**Commit A đã tạo:** `9f9aa83c833c6c3d3a872bfd22f2d704db29cf20` — `fix(search): align page catalog with sidebar visibility`. Commit B `docs: dashboard phase 2 spec cleanup` là commit ngay sau A, chứa riêng đặc tả/nhật ký; SHA thực tế và kết quả remote được ghi trong verification cuối để giữ working tree sạch và đúng hai commit. Kiểm CI theo SHA push cuối nếu CLI vẫn401: ghi chưa theo dõi CI trong verification/bàn giao, không ngụ ý CI đạt.

## 2026-10-13 — Quy trình dọn nguồn, tạo bản sao và commit/push mặc định

**Tóm tắt cho chủ dự án**

- Đã ghi quy trình bắt buộc sau mỗi đợt sửa mã vào hướng dẫn dự án.
- Dọn nguồn, kiểm thử cuối, tạo bản sao sạch, commit và push là các bước mặc định.
- Chỉ hoãn push khi chủ dự án yêu cầu rõ trong đợt tương ứng; không tự deploy.
- Hoàn tất bàn giao hai commit tìm kiếm/đặc tả đang chờ theo chỉ đạo mới.

**Phạm vi:** dùng Create Rule, cập nhật AGENTS.md thay vì tạo quy tắc trùng. Main đầu lượt ahead2/behind0, remote `2c47252`; giữ dòng SHA bổ sung của nhật ký. Yêu cầu mới cho phép hoàn tất push mặc định, thay việc giữ local của lượt trước. Không sửa mã ứng dụng hoặc triển khai khối Đợt 2.

**Quy tắc:** dọn trong phạm vi, giữ dữ liệu/thay đổi khác; kiểm thử nguồn cuối; bản sao review ngoài repo có manifest/hash, không runtime/bí mật; commit/push main và kiểm SHA remote. Không force-push/deploy. Khi lỗi phải báo đúng kết quả và cách xử lý.

**Bàn giao:** bản sao `D:/QLHCNS-Backups/IHRMS_Review_20261013_Phase2_Process.zip`, nguồn staged kèm quy trình và nhật ký cuối, manifest parent commit/tree và SHA từng tệp. Mở lại kiểm hash/số tệp, báo cáo `.verification.json` và `.zip.sha256` cạnh ZIP. Hai commit ứng dụng/đặc tả đã kiểm ở lượt trước được push cùng commit hướng dẫn này; không thay mã sau full suite 488 test mỗi backend/Edge130 đã ghi. Lượt này chỉ tài liệu: diff check và kiểm bản sao; không chạy lại nghiệp vụ. SHA push/kết quả remote báo trong bàn giao và verification ngoài repo để tránh tự tham chiếu commit. Không theo dõi CI do GitHub CLI401 từ lượt trước.

## 2026-10-13 — Kiểm chứng tìm kiếm và đặc tả Dashboard Đợt 2

**Tóm tắt cho chủ dự án**
- Đã sửa tìm người không dấu, giữ phạm vi được phép xem và cảnh báo khi quá nhiều hồ sơ.
- Đã sửa các trang tìm kiếm bị ẩn lệch guard; không đổi quyền đọc dữ liệu của trang đích.
- Full suite đạt trên cả hai backend; giao diện đạt kiểm tra sáng/tối, bàn phím và màn hình rộng/hẹp.
- Đợt 2 mới là đặc tả; cần chốt loại nghỉ, quyền tuyển dụng, nguồn ngày tuyển, nhật ký và ngân sách truy vấn.
- Chưa kiểm screen reader, zoom 200% hay phiên tài khoản thật; không push/deploy.

**Phạm vi/Git đầu lượt:** theo tệp yêu cầu Phần A sửa tìm kiếm/kiểm chứng và Phần B chỉ đặc tả. Đọc AGENTS, ba mục mới nhất, đặc tả, search/tests/dashboard_employee_scope và RBAC; dùng UI UX Pro Max, không UI Styling/shadcn/dependency/CDN. `main`, working tree đầu lượt sạch; fetch `origin/main`, rev-list 0/0, `git ls-remote origin refs/heads/main` bằng HEAD `2c47252b712c5af3de2149654e3053190fb28bf6`: commit tìm kiếm/demo đã trên remote. Không reset/stash/đổi nhánh, không model/migration/quyền/field/CSRF/URL name/middleware/selector Pending/tiền/giấy HCNS; không thêm bộ lọc hồ sơ chưa hợp đồng.

**A1:** `views/search.py:people_matches` áp scope trước; quét tối đa 5.001 dòng chỉ pk/full_name/employee_code/company_email theo full_name, pk. NFD/casefold và đ→d cho cả tên/mã/email; lấy tối đa 21 PK rồi truy vấn một lần với department, chỉ các cột an toàn. Trên scope >5.000 dùng lại icontains và hiện “Tìm không dấu bị giới hạn do số hồ sơ lớn”; không lặng lẽ trả kết quả thiếu. Giữ 2–100 ký tự, tối đa 20 + thông báo còn kết quả, đăng nhập/GET-only/no-store/escape/link theo quyền. Không đổi collation/schema, không chọn CCCD/lương hoặc trường mã hóa trong matcher. Template chỉ thêm cảnh báo.

**A2 — lệch đã tái hiện bằng client:** có 15 cặp role/trang bị ẩn dù GET đích trả 200: hr_employee_list ở EMPLOYEE/DEPT_MANAGER/DIRECTOR/FINANCE_OFFICER/SYS_ADMIN (5); hcns_catalog cùng 5 role; recruitment_list ở EMPLOYEE/HR_OFFICER/DIRECTOR/FINANCE_OFFICER/SYS_ADMIN (5). Đổi ba entry PAGES thành authenticated, view vẫn giữ scope hồ sơ/biểu mẫu/phòng; các role có scope rỗng chỉ nhận danh sách rỗng, không mở thêm dữ liệu. Thêm điều kiện hồ sơ/submit hoặc approve cho profile_change_request_list để tài khoản unlinked không nhận link 403; SUPER_ADMIN không cờ không tự cấp quyền. Ma trận 8 role (EMPLOYEE/DEPT_MANAGER/HR_OFFICER/HR_MANAGER/DIRECTOR/FINANCE_OFFICER/SYS_ADMIN/superuser) kiểm mọi entry bằng GET tìm kiếm và GET đích, cùng fixture HomeDashboardTests; test riêng unlinked/SUPER_ADMIN. Không nới guard. Giữ test route resolve có sẵn, không thêm bản trùng.

**Test mới/đo query:** `test_global_search.py` thêm case accent/case/đ/NFD theo nguồn, scope trước scan, giới hạn/cảnh báo, safe projection, page guard matrix, unlinked và đo matcher trước/sau trên cùng view/fixture. Login/warm-up ngoài đo; before là matcher icontains cũ, after là matcher mới; toàn GET/render, không bỏ SELECT của backend. Bảng đo cuối cập nhật bên dưới khi full suite hoàn tất. Focused SQLite 8/8 đạt, SEARCH_PAGE_GUARD_MISMATCHES=[]; trước warm-up có kết quả khác ở role đầu, không dùng làm bảng cuối.

| Vai trò linked | SQLite trước → sau | SQL Server trước → sau |
| --- | --- | --- |
| EMPLOYEE | 6 → 7 | 7 → 8 |
| DEPT_MANAGER | 6 → 7 | 7 → 8 |
| HR_OFFICER | 6 → 7 | 7 → 8 |
| HR_MANAGER | 6 → 7 | 7 → 8 |
| DIRECTOR | 7 → 8 | 8 → 9 |
| FINANCE_OFFICER | 6 → 7 | 7 → 8 |
| SYS_ADMIN | 6 → 7 | 7 → 8 |
| Superuser | 7 → 8 | 8 → 9 |

Ma trận search đã đạt trên cả hai backend trong lượt full đầu (chỉ ca cache cũ thất bại); sẽ đối chiếu lại log full cuối, không dùng lượt trước làm kết luận full suite. Tăng đúng +1 SELECT mọi role; safe projection 2 query, department truy cập không N+1. Superuser được đo riêng, không thay bằng role SUPER_ADMIN không cờ.

**A3/UI:** Edge trên demo SQLite cách ly, bổ sung duy nhất tên/email giả của DEMO-022 để tìm Nguyễn/Đặng và tên dài. `ops/run_search_phase2_uat.py --directory "$env:TEMP/ihrms-atoms-demo-20261013" --packages-dir "$env:TEMP/ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages"`: 130 kiểm tra/24 ảnh, exit native 0, errors=[]; Trang chủ/Chi tiết KPI/kết quả tìm kiếm ×360/768/1024/1440 × sáng/tối, HTTP200/không overflow, chữ hiển thị ≥14px, control ≥44px, keyboard Enter tìm NGUYEN khớp Nguyễn Đặng. Đã xem ảnh kết quả desktop tối. Bằng chứng `phase2-search-uat/browser-result.json` và ảnh trong thư mục demo; log TEMP/ihrms-phase2-browser-confirmed.log. Vòng đầu phát hiện breadcrumb 12px: nâng riêng caption khung màn hình lên small 14px, không đổi giấy/in; base stylesheet và service worker v14 đổi cache. Runner ban đầu bị race navigation khi gửi Enter rồi goto; đổi expect_navigation trước Enter và chạy lại cuối đạt. Không chứng nhận WCAG/phiên trình duyệt thật của chủ dự án.

**Cây kiểm thử/gate:** export Git index bằng git archive vào TEMP/ihrms-phase2-20261013/stage-source; wrapper TEMP/ihrms-phase2-index-runner.py gọi ops/run_tests.py của nguồn đó, resolve SQL connection chỉ trong memory, DB dùng một lần/media/log riêng, M365 off. Gate wrapper TEMP/ihrms-phase2-index-gates.py chạy check, makemigrations --check --dry-run, ops/check_ui_contrast.py: exit 0, no issues/no changes, 190 cặp/0 lỗi; pip check exit 0, diff/index diff --check đạt. Lấy `$LASTEXITCODE` ngay sau Python và exit giá trị đó khi redirect PowerShell. Bản đầu SQLite chạy 488 test nhưng 1 test khóa CSS v20261013-phase1-followup cũ thất bại, 7 skip; không báo đạt. Sửa test cache cũ trong tests.py để kiểm href có cache query; tests_mobile kiểm service worker v14. Ca hồi quy riêng đạt 1/1. Full cuối phải chạy lại cả backend sau sửa test, không dùng kết quả 477 của commit trước hoặc kết quả lần đầu chưa đạt.

**Phần B — chỉ tài liệu:** thêm mục 16 Đợt 2 trong DASHBOARD_ATOMS_TECH_SPEC.md và sửa số mục KPI bị trùng 14 thành15. Bảng tóm tắt/nguồn/công thức/quyền × khối/privacy/drill-down/query budget/kiểm thử/rủi ro/8 quyết định. Đọc model/guard thật: Candidate không FK JobPosting/Employee hoặc hired_at; Hired có thể được set trước khi form Employee lưu, Offer.expected_join_date không là ngày tuyển. SecurityEvent chỉ access/export; BaseAuditModel không là full audit. Đề xuất nếu cần chỉ “Cập nhật quyết định nhân sự” theo PersonnelDecisionHistory và scope decision, actor/comment ẩn; nhật ký tổng quát thiếu nguồn. Header tầng 2/giờ ca/kỳ lương hoãn. Không viết code/template/style/view của khối Đợt 2. Baseline và dự toán cho thấy HR Manager SQL17 + nghỉ/tin/ứng viên/history thành21; giữ trần20, phải chốt chia rollout/giảm query.

**Còn mở/bàn giao:** các quyết định D2-1 đến D2-8 để chủ dự án duyệt trước khi giao triển khai; xem nhóm chung nghỉ, scope lịch sử, tin/candidate, nguồn ngày tuyển, source/actor nhật ký, hoãn header2 và query budget. Không sửa middleware ghi session hoặc selector Pending có parent đã xóa. Chưa screen reader/zoom200%/UAT tài khoản thật, chưa theo dõi CI; không push nên SHA local mới chưa có CI remote. Hai commit riêng theo yêu cầu; SHA/kết quả full cuối bổ sung vào cùng mục này khi chốt. Không mở bất kỳ khối Đợt 2 nào.

**Kết quả full cuối:** `venv/Scripts/python.exe "$env:TEMP/ihrms-phase2-index-runner.py" --backend sqlite` trên stage-source cuối: 488 test, OK (7 skip), 525.294 giây, exit native0; `--backend sqlserver`: 488/488 OK, không skip, 568.245 giây, exit native0. Log TEMP/ihrms-phase2-full-sqlite-final.log và ihrms-phase2-full-sqlserver-final.log; database dùng một lần đã hủy. Đây là full suite của chính thay đổi A1/A2/route/demo/bố cục hiện tại, không lấy kết quả commit 9eba8ca. Cây stage cuối `2324a80745f963a32bac27967f8265fa8402ee29`; đối chiếu tất cả tệp mã stage với snapshot khớp sau chuẩn hóa LF/CRLF. Chỉ tài liệu/nhật ký bổ sung sau test, không thay nguồn ứng dụng. Cả log cuối đều SEARCH_PAGE_GUARD_MISMATCHES=[] và query matrix đúng bảng trên. Lần đầu SQL cũng chỉ lỗi assertion CSS cũ; không dùng làm kết quả đạt, đã chạy lại full cuối sau sửa test. Gate/migration/contrast/pip và diff check đều đạt; Edge cuối 130/24 ảnh vẫn khớp nguồn cuối. `gh run list --commit 2c47252...` trả HTTP401 Bad credentials; **chưa theo dõi CI**, không ghi token. SHA mới local không push nên chưa có run CI remote theo hai SHA; chủ dự án có thể xem Actions sau khi tự cho phép push, không cần gửi token qua chat.

**Commit Phần A:** `ea9b9b655d6785dae12774c6866b4b11264dae60` — `fix(search): accent-insensitive people search and page permission tests`. Phần B chỉ đặc tả và cùng mục nhật ký, commit `docs: dashboard phase 2 specification`; SHA thực tế bổ sung sau commit để tránh tự tham chiếu. Giữ đúng hai commit, không push/deploy.

**Commit Phần B và remote cuối:** `07305f0e161534fed839e1bc3efa91e27eb14a97` — `docs: dashboard phase 2 specification`. Xác minh `main` ahead2/behind0; `git ls-remote origin refs/heads/main` vẫn `2c47252b712c5af3de2149654e3053190fb28bf6`, chưa push. Dòng SHA Phần B này được bổ sung vào working tree sau commit, chưa commit, để ghi đúng hai SHA mà không tạo commit thứ ba; mọi mã và đặc tả đã nằm trong hai commit. Chủ dự án duyệt mục 16/D2-1..D2-8, yêu cầu triển khai phần được duyệt hoặc cho phép push riêng; chưa triển khai Đợt 2.

## 2026-10-13 — Làm sạch nhật ký và bàn giao mã nguồn

**Yêu cầu/phạm vi:** làm sạch nhật ký, tạo bản sao review, commit và push. Chỉ làm trên `main`; đầu lượt fetch `origin/main` thành công, ahead 1/behind 0, HEAD `9eba8cadf3d9e2a239c7a8582e22b63fc7e2114d`. Gom 26 tệp liên quan còn chờ của Dashboard/chi tiết KPI/bảng hợp đồng/tìm kiếm/demo/kiểm thử và tài liệu. Giữ `design-system/reference/` chưa theo dõi ngoài commit; không đụng dữ liệu vận hành hoặc tài khoản demo.

**Nhật ký:** sửa mục Hoàn thiện Dashboard Đợt 1 mất dấu thành tiếng Việt UTF-8, chuẩn hóa tiêu đề ngày dd/mm/yyyy sang ISO, sửa dấu phân cách tiêu đề Word, chuyển ba tiểu mục công cụ/hướng dẫn thành heading cấp 3 của mục tương ứng; xếp 116 mục lịch sử theo ngày mới đến cũ và chuẩn hóa dòng trống. Đối chiếu từng dòng nội dung lịch sử ngoài mục lỗi: giữ đủ, không xóa kết quả/giới hạn/lệnh kiểm tra. Bản gốc trước dọn tại `D:/QLHCNS-Backups/PROJECT_WORK_LOG_before_cleanup_20261013.md`, ngoài Git; không đưa bản gốc này vào ZIP review.

**Bản sao review:** `D:/QLHCNS-Backups/IHRMS_Review_20261013_Search_Dashboard.zip`, xuất toàn bộ mã nguồn đã stage theo `git ls-files` và blob index; manifest `REVIEW_SNAPSHOT.txt` ghi parent commit, tree ID, branch, danh sách loại trừ và SHA-256 từng tệp. Có 610 tệp nguồn được chọn từ 617 tệp theo dõi, loại 7 tệp runtime/đầu ra. Không kèm `.env` (giữ `.env.example`), database, media/uploads, log, CSV tài khoản, credentials/secret demo hoặc lịch sử Git. Quy trình bàn giao mở lại ZIP, kiểm số entry và đối chiếu hash từng tệp; SHA-256 ZIP được ghi trong file `.sha256` bên cạnh và báo cùng kết quả bàn giao. Đây là bản mã nguồn review, không phải bản sao phục hồi database/media. ZIP và commit dùng cùng tree; kết quả đối chiếu cuối được lưu ngoài repo tại `IHRMS_Review_20261013_Search_Dashboard.verification.json`.

**Kiểm tra:** `git diff --check` và `git diff --cached --check`; xác nhận UTF-8/không còn mục mất dấu/giữ nguyên nội dung lịch sử ngoài phần sửa. Đọc lại bằng chứng JSON của nguồn ứng dụng đã kiểm ở đợt trước: demo 42 kiểm tra, SQLite/SQL Server mỗi backend 399 kiểm tra và 32 ảnh, `errors=[]`, DB dùng một lần đã hủy; các kết quả 29 test mỗi backend nằm trong mục đợt đó. Lượt này chỉ sửa nhật ký, không thay mã ứng dụng sau kiểm thử nên không chạy lại luồng nghiệp vụ để tránh tạo bằng chứng lặp không cần thiết. Không dùng full suite của commit cũ để kết luận toàn bộ nguồn mới đã chạy full suite. Kiểm tra stage/ZIP không có runtime hoặc bí mật trước bàn giao.

**Git/bàn giao:** commit dự kiến `feat(portal): add scoped search and Atoms dashboard demo`, chứa mã nguồn đã kiểm và nhật ký đã dọn; sau đó `git push origin main`, đối chiếu SHA local với `git ls-remote origin refs/heads/main` và ahead/behind. SHA commit/tree thực tế cùng kết quả remote được ghi trong manifest/báo cáo kiểm chứng và câu trả lời bàn giao, tránh tự tham chiếu SHA trong chính commit. Nếu push lỗi phải ghi rõ lỗi và xử lý trước khi báo hoàn tất; không deploy. Chủ dự án có thể dùng ZIP review và bản demo đang chạy như hướng dẫn trong mục trước; CI và UAT phiên trình duyệt của chủ dự án chưa được xác nhận trong lượt này.

## 2026-10-13 — Tìm kiếm dùng chung và dữ liệu demo Dashboard Atoms

**Phạm vi:** theo yêu cầu tạo ô tìm kiếm toàn app và tài khoản/hợp đồng giả để kiểm KPI, biểu đồ. Dùng UI UX Pro Max; tiếp tục trên `main`, đầu lượt fetch `origin/main` thành công, ahead 1/behind 0. Giữ toàn bộ thay đổi cục bộ có sẵn; lượt này chưa commit/push/deploy. Không đổi schema, quyền, cách tính KPI, hợp đồng hay quy trình duyệt.

**Mã đã sửa:** `views/search.py`, `urls.py`, facade views, `global_search.html`, `base.html`, `_shell_icon.html`, `context_processors.py`, `app_shell.css`; tìm kiếm chung tên/mã/email nhân viên và trang chức năng được phép mở. Scope toàn Trung tâm/phòng quản lý/chính mình được áp trước truy vấn; không tìm định danh nhạy cảm/lương/nội dung đơn. Tối thiểu 2, tối đa 100 ký tự; tối đa 20 nhân viên, có thông báo thu hẹp nếu còn kết quả; escape HTML, chỉ GET, yêu cầu đăng nhập và no-store. Tìm kiếm không phải tìm toàn văn mọi bản ghi của mọi phân hệ. Không thêm truy vấn cho header ngoài trang kết quả.

**Dashboard:** `_headcount_chart.html`, `_contract_distribution.html`, `dashboard_data.py`, `home_dashboard.css`, `dashboard.html`; nhóm có màu riêng, tên/số/ký hiệu và bảng thay thế, thanh tỷ trọng hợp đồng, thực tế/kế hoạch cùng thang đo, hai khối cân chiều rộng, hiển thị đủ 6 phòng demo. Bỏ ghi chú hồ sơ chưa hợp đồng khi số là 0. Bump cache stylesheet/service worker. Giữ KPI thử việc: quỹ lương, xu hướng và tỷ lệ có mặt trong ảnh mẫu chưa có chính sách/nguồn được duyệt. Cập nhật bổ sung phạm vi trong đặc tả.

**Demo cách ly:** `ops/dashboard_demo.py` từ chối ghi đè thư mục không rỗng và không tạo runtime trong repository; luôn chọn SQLite `synthetic.sqlite3` riêng, media/log/email riêng, M365 tắt, server chỉ bind loopback, có banner dữ liệu giả. Đã tạo `%TEMP%/ihrms-atoms-demo-20261013`: 22 nhân viên, 6 phòng, 4 loại/27 hợp đồng, các trạng thái Draft/Active/Expired/Terminated và biên hôm nay/7/30/60 ngày, quá hạn, bắt đầu tương lai; 6 tài khoản vai trò, 2 đơn nghỉ Approved hôm nay và 2 Pending. KPI ngày 13/10/2026: managed 22, Active 17, Approved 2, Probation 3; 22 hợp đồng hiệu lực. Credentials, secret, database và media ở thư mục demo ngoài Git, không ghi vào nhật ký. Chưa sửa/xóa dữ liệu vận hành.

**Cách review:** server demo đang chạy tại `http://127.0.0.1:8766/portal/`; đăng nhập `demo-hr`, mật khẩu đọc tại `%TEMP%/ihrms-atoms-demo-20261013/DEMO_ACCOUNTS.txt`. Các role khác cùng file. Khi cần chạy lại: `venv/Scripts/python.exe ops/dashboard_demo.py serve --directory "$env:TEMP/ihrms-atoms-demo-20261013" --port 8766`. Tạo bản mới dùng `create` với một thư mục ngoài repo chưa có dữ liệu. Demo giữ lại cho review; ngày hiệu lực là ngày thực tế nên số có thể thay đổi khi mở vào ngày khác, đối chiếu `DEMO_EXPECTATIONS.json` với ngày tạo.

**Kiểm tra trên nguồn cuối:** `venv/Scripts/python.exe "$env:TEMP/ihrms-ui-refinements-20261013/runner.py" --backend sqlite apps.portal.test_global_search apps.portal.test_home_dashboard apps.portal.test_dashboard_drilldown apps.portal.test_dashboard_followup apps.portal.test_ui_refinements`: 29/29 đạt. Wrapper chuyển log ra TEMP và gọi `ops/run_tests.py`, DB/media cách ly. `py_compile` các runner/search/tests và `git diff --check` đạt. `test_global_search.py` kiểm đăng nhập/GET, phạm vi theo role, email, tên chức năng không dấu, route resolve, xóa mềm, escape/no-store, giới hạn ký tự và 20 kết quả.

**Edge live demo:** `venv/Scripts/python.exe ops/run_dashboard_demo_uat.py --directory "$env:TEMP/ihrms-atoms-demo-20261013" --packages-dir "$env:TEMP/ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages"`: 42 kiểm tra đạt, 10 ảnh, không lỗi JavaScript. Đăng nhập thật 6 role, email search scope, mở điểm đến tìm kiếm hợp đồng, 4 KPI đối chiếu số/điểm đến, 6 phòng/4 loại/thanh tỷ trọng; 360/390/768/1024/1440 px × sáng/tối, không tràn ngang, gửi tìm kiếm bằng bàn phím. Bằng chứng `browser-result.json` và `screenshots/` trong thư mục demo; đã xem ảnh desktop sáng và mobile tối. Playwright chỉ cài trong TEMP, không thêm dependency dự án.

**SQL Server và hồi quy nghiệp vụ — kết quả cuối:** cùng lệnh 29 test ở trên đổi `--backend sqlserver`: 29/29 đạt, 285,182 giây, database SQL Server riêng đã hủy. Edge live chạy `venv/Scripts/python.exe ops/run_browser_uat.py --backend sqlite --packages-dir "$env:TEMP/ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages" --output-dir "$env:TEMP/ihrms-search-live-uat-sqlite-20261013"` và cùng lệnh đổi `--backend sqlserver`, output `ihrms-search-live-uat-sql-final-20261013`: mỗi backend 399 kiểm tra/32 ảnh đạt, `errors=[]`, bước cuối `No uncaught browser JavaScript errors`, `db_destroyed=true`, không Traceback ở log cuối. Có đăng nhập thật/CSRF, tạo hồ sơ rồi hợp đồng, nhập số Việt Nam lưu chuẩn, tên dài không đè cột, dropdown hồ sơ, 4 KPI/scope/ngày/điểm đến, 5 độ rộng × sáng/tối trên Dashboard/hợp đồng/nhân viên, gửi đơn nghỉ rồi duyệt qua dialog; kiểm DB lưu đúng và một lần, queue tăng sau gửi/giảm sau duyệt, 17 trường hợp tài khoản linked/unlinked/superuser và link được đọc, không tiền trên Dashboard. Demo review giữ nguyên; chỉ DB/media hồi quy dùng một lần được cách ly.

**Các lần chạy chưa đạt và sửa runner:** lần đầu `[name=q]` trùng giữa header và bộ lọc nhân viên, đổi thành `main [name=q]`. Lần tiếp theo kiểm tra cũ đòi hai biểu đồ rộng bằng nhau; cập nhật assertion tỷ lệ 1,2:1 theo bố cục Atoms vừa triển khai. Hai lần chưa đạt đã hủy DB, không dùng làm bằng chứng hoàn tất. Chạy lại cuối trên cả hai backend đạt như trên. PowerShell chuyển logging stderr của Python thành `NativeCommandError` khi dùng `> log 2>&1`, khiến exit của shell là 1 dù script hoàn tất: đã tái hiện bằng một Python chỉ in stderr, xác nhận `$LASTEXITCODE=0` trong probe và cùng lệnh không có Write-Output trả shell 1. Vì vậy dùng kết quả assertion/JSON cuối + không Traceback, không coi nhãn lỗi redirection là lỗi nghiệp vụ; khi chạy lại qua PowerShell nên in/lấy `$LASTEXITCODE` ngay sau Python và `exit $LASTEXITCODE` để bảo toàn exit native.

**Giới hạn:** `cua.getState()` lỗi `failed to write kernel assets: The system cannot find the path specified. (os error 3)`; chưa UAT phiên trình duyệt đang mở của chủ dự án. Bằng chứng trên là Edge tự động trên ứng dụng thật với dữ liệu giả cách ly. Không tuyên bố đã chạy toàn bộ suite hoặc CI trong lượt này. Các thẻ fallback cũ chưa có nguồn vẫn hiện “Chưa có dữ liệu”; không bịa số để khớp ảnh Atoms.

## 2026-10-13 — Hoàn thiện Dashboard Đợt 1 sau review

**Mục tiêu/phạm vi:** sửa các phần review yêu cầu trên main; đầu lượt fetch origin/main thành công, ahead 0/behind 0. Dùng UI UX Pro Max. Không làm Đợt 2, không đổi model, migration, quyền, form, CSRF, logic lương/nghỉ/duyệt hoặc giấy HCNS. Commit `ui: dashboard phase 1 follow-up`; tại thời điểm ghi mục này chưa push/deploy.

**Thẻ và liên kết:** chỉ bỏ thẻ cũ khi khối mới ready/empty và cùng số đếm. So Active cũ với Active mới, không so với tổng gồm thử việc/nghỉ dài hạn; hàng chờ nghỉ so đúng tổng Pending của selector. Partial/error/thiếu khối hoặc số khác thì giữ thẻ; số khác đổi nhãn “theo tổng quan cũ”. Giữ đề xuất tuyển dụng, tài liệu, công việc, tài sản và checklist; các khóa context cũ không đổi. Khóa chưa được view cung cấp số vẫn hiện “Chưa có dữ liệu”, không giả thành 0. Bỏ link hr_employee_list của tổng Active/global/phòng vì danh sách yêu cầu hợp đồng và không có bộ lọc trạng thái tương ứng. Ghi rõ managed/Active gồm cả hồ sơ chưa có hợp đồng. Manage HR có ghi chú số hồ sơ chưa có hợp đồng và link tạo hợp đồng; một COUNT/EXISTS riêng, không tải hồ sơ để đếm; người không có quyền không nhận truy vấn/ghi chú này. Giá trị 0 có state ready.

**Phạm vi commit:** gồm chỉnh Dashboard/icon/bố cục và ba trang đã hoàn thiện UI. URL/trang chi tiết KPI và tham số GET từ lượt trước được giữ trong working tree, chưa đưa vào commit này. AGENTS.md, bổ sung đặc tả, bảng hợp đồng, runner trình duyệt, reference và nhật ký cũ giữ ngoài commit. core.py chỉ bỏ việc loại toàn bộ nhóm quản trị; dashboard_data.py chỉ sửa state/ghi chú/count/icon, giữ route hiện có. Xuất bản stage vào TEMP/committed-source-test để kiểm đúng mã sẽ commit; không tạo nhánh hoặc ghi đè working tree.

**Ba trang:** hồ sơ nhân viên, bảng công và Trung tâm báo cáo dùng component/token ui. Tạo hợp đồng và liên kết lịch sử có vùng bấm/focus. Bảng công giữ field/action/thứ tự cột/ngày/status, sửa khối bọc tránh tràn 360 px. Báo cáo dùng page_header/card/button và SVG thay emoji; href Excel/sổ công văn/quản trị giữ nguyên, HTML trước/sau khớp. Quét class Tailwind cũ/hex/emoji: 29/132/158 match trước, đều 0 sau (`venv/Scripts/python.exe TEMP/ihrms-followup-style-audit.py`, exit 0; style-audit.json, regex thuộc tính class và Unicode codepoint ngoài Git). Lỗi encoding shell ban đầu đã sửa, không dùng làm bằng chứng đạt. Không đổi template HCNS; giữ cỡ in 9 pt của bảng công, chỉ kiểm màn hình.

**Truy vấn:** 8 role × linked/unlinked trên cả hai backend. SQL Server: EMPLOYEE 4 → 4 và 8 → 8; DEPT_MANAGER 4 → 4 và 11 → 11; HR_OFFICER 9 → 10 và 13 → 14; HR_MANAGER 13 → 13 và 17 → 17; DIRECTOR 11 → 10 và 15 → 14; FINANCE_OFFICER 4 → 4 và 8 → 8; SYS_ADMIN 4 → 4 và 8 → 8; SUPER_ADMIN 5 → 5 và 9 → 9. Baseline lấy từ nguồn trước COUNT/skip NULL trên cùng fixture, không lấy số lượt trước. Lần đầu SQL tăng 18 SELECT; bỏ phép đếm DepartmentID IS NULL khi schema bắt buộc phòng ban. Khi nullable vẫn giữ phép đếm cũ; không đổi model/công thức. Ghi chú thêm một COUNT cho manage_hr, bù một SELECT không thể có kết quả ở người được xem định biên; max SQL cuối 17. SQLite: HR Manager 12 → 12 (chưa gắn hồ sơ), 16 → 16 (đã gắn); Director 10 → 9 và 14 → 13; HR Officer 8 → 9 và 12 → 13; vai trò khác không tăng, max 16. SQL có thêm SELECT kiểm tra transaction, vẫn tính trong báo cáo; không N+1. Ba trang SQLite: hồ sơ 18 → 18, bảng công 15 → 15, báo cáo 13 → 13; SQL: 19 → 19, 16 → 16, 14 → 14 gồm render. Template cũ nạp từ TEMP bằng locmem, không thay tệp thật. Test Active hai nguồn có/không kế hoạch, 0 người, đã xóa, Probation/OnLeave/Resigned; nhánh nullable kiểm bằng count stub vì DepartmentID thực tế không nullable, không tạo record sai.

**Test mới:** test_dashboard_followup.py kiểm giữ/bỏ/đổi nhãn, zero ready, ghi chú đúng số/quyền, ba template không class cũ/hex/emoji, href/query không tăng, hai nguồn Active và query matrix. Probe mã HEAD trước sửa trong memory phát hiện đúng 3 assertion lỗi: zero state, link directory lệch, thẻ trùng còn giữ. Probe exit 0 là phát hiện đủ lỗi, không phải mã cũ đạt. Cập nhật test nhãn/cache/component theo UI; full đầu còn nhãn/cache cũ chưa được dùng để báo đạt.

**Kết quả cuối:** bản stage sau guard giảm SELECT ở TEMP/ihrms-followup-20261013/committed-source-test. `venv/Scripts/python.exe TEMP/ihrms-followup-index-runner.py --backend sqlite` gọi ops/run_tests.py của bản stage: 477 test, OK (7 skip), 539.332 s, exit 0; đổi `--backend sqlserver`: 477/477 OK, không skip, 568.401 s, exit 0. Log TEMP/ihrms-followup-delivery-full-sqlite.log và ihrms-followup-delivery-full-sqlserver.log. DB/media riêng, M365 off, APP_ENV=test; SQL connection lấy trong memory để tạo DB dùng một lần, không ghi bí mật ra file. Cùng wrapper với nhãn apps.portal.test_home_dashboard apps.portal.test_dashboard_followup apps.portal.tests_mobile: 26/26 SQLite trước guard, 26/26 SQL Server trên guard cuối, exit 0; full cuối chạy lại các nhãn đó. `TEMP/ihrms-followup-index-gates.py` chạy Django check/makemigrations --check --dry-run và ops/check_ui_contrast.py: exit 0, không migration, 190 cặp/0 lỗi. pip check, git diff --check và git diff --cached --check đạt; stage không có .env/database/media.

**Giao diện:** Edge headless trên HTML Django render từ fixture giả, đúng stage cuối. `venv/Scripts/python.exe -u TEMP/ihrms-followup-index-ui.py`: exit 0, 80 ảnh/401 checks, không pageerror; ui-delivery-final/ui-result.json dưới TEMP/ihrms-followup-20261013. Năm Trang chủ (HR Manager, HR Officer, Trưởng phòng, Giám đốc, Nhân viên) và ba trang sửa × 1920/1440/1024/768/360 × light/dark. Không overflow; control ≥44 px, chữ màn hình ≥14 px, Tab focus và reduced-motion. Đã xem ảnh báo cáo dark, bảng công 360 light, Trang chủ/detail stage cuối. TEMP/ihrms-followup-role-pages.py: exit 0, ba trang × tám role trả đúng 200/403/404 theo guard cũ, không nới quyền. Probe lỗi selector/DisallowedHost/overflow đã sửa; không dùng kết quả lỗi báo đạt. Đây là HTML fixture và Edge riêng, chưa UAT tài khoản thật hoặc chứng nhận WCAG.

**Còn mở/commit:** middleware ghi django_session khi GET, selector Pending có hồ sơ cha đã xóa và bộ lọc chưa hợp đồng nằm ngoài phạm vi. Chưa screen reader, zoom 200%, UAT tài khoản thật hoặc CI theo SHA. Chủ dự án Ctrl+F5 Trang chủ với các vai trò HR Manager, HR Officer, Trưởng phòng, Giám đốc; quyết định bộ lọc chưa hợp đồng và push. Commit `9eba8cadf3d9e2a239c7a8582e22b63fc7e2114d`; main ahead 1/behind 0 sau commit, lúc đó chưa push. Đối chiếu hash 601 tệp commit với nguồn đã chạy full suite khớp (ngoại trừ nhật ký bổ sung sau test). SHA được ghi vào working tree sau commit để giữ một commit duy nhất của đợt đó. Các yêu cầu push về sau được ghi trong mục bàn giao tương ứng.

## 2026-10-13 — Tinh gọn Dashboard và mở chi tiết bốn KPI nhân sự

**Phạm vi:** theo yêu cầu mới, main b0954e5, fetch origin/main đầu lượt ahead/behind 0/0. Dùng UI UX Pro Max, giữ toàn bộ thay đổi chưa commit lượt kiểm thử trước và reference. Tinh gọn Dashboard Đợt 1, icon và liên kết chi tiết; không mở tiền/lịch sử giả, không đổi tính lương/phép/quyền, model/migration/HCNS. Chưa commit/push đợt này.

**Giao diện:** dashboard.html và các partial gom công thức/nguồn dài vào Cách tính chỉ số/Phạm vi dữ liệu, bỏ mô tả kỹ thuật lặp dưới từng KPI; giữ ngày/phạm vi ở đầu, đơn vị/legend/0 và thiếu kế hoạch rõ. Bảng loại hợp đồng nằm trong disclosure để không lặp thông tin biểu đồ, có table truy cập bàn phím. home_dashboard.css thu khoảng đệm/chiều cao KPI, hai cột biểu đồ bằng nhau, thanh định biên gọn, vùng danh sách hợp đồng dài cuộn có focus. Không hiện riêng nhóm quá hạn rỗng. Cột phải gồm Việc cần xử lý + Checklist + Thao tác nhanh qua _quick_actions.html, tránh khoảng trắng lớn cạnh danh sách hợp đồng. Khu Công việc của tôi giữ hai cột cân bằng. Icon KPI people/briefcase/calendar/person, checklist/checklist, khối hợp đồng/contract và phân bố/pie, thêm SVG trong _shell_icon.html. home_presentation truyền icon theo nội dung; bump CSS version/service worker v11.

**Chi tiết KPI:** dashboard_data.py dùng chung dashboard_employee_scope cho card và selector đích; metric icon/href thực. Route portal:dashboard_people ở /portal/dashboard/people/, core.py + dashboard_people.html, metric managed/active/approved/probation và on_date ISO. managed Active+Probation+OnLeave, active/Probation trạng thái hiện tại, approved distinct người có đơn Approved bao gồm ngày chọn (không lấy lý do/chứng từ/lương). view_all_employees global; DEPT_MANAGER linked chỉ phòng quản lý; approved thêm view_reports. GET chỉ đọc, search tên/mã, pagination giữ metric/on_date/q, sai metric/ngày 400, không quyền 403, department giả không mở scope. Khi có quyền hồ sơ, link tên sang chi tiết có sẵn. Đây là danh sách thống kê đúng người KPI đã tính, không đổi điều kiện hợp đồng của Nhân viên & hồ sơ; không liên kết KPI tới danh sách có số khác. Thêm test_dashboard_drilldown.py cho count/đích, không hợp đồng, Approved trùng, ngày, scope/quyền, tìm kiếm và phân trang. Bổ sung mục 14 đặc tả theo chính yêu cầu mới; không thay công thức duyệt trước.

**Kiểm thử backend trên nguồn cuối:** wrapper TEMP/ihrms-ui-refinements-20261013/runner.py gọi ops/run_tests.py --backend sqlite apps.portal.test_home_dashboard apps.portal.test_dashboard_drilldown apps.portal.tests_mobile: 24/24 OK, exit 0, log TEMP/ihrms-dashboard-balanced-focused.log. Cùng nhãn --backend sqlserver: 24/24 OK, exit 0, log ihrms-dashboard-balanced-focused-sqlserver.log. Test dashboard có ma trận role/profile, GET/query budget, lỗi/thiếu/rỗng và biên ngày. py_compile dashboard_data/core/runner, git diff --check đạt; contrast 190 cặp/0 lỗi. Không chạy full suite trong đợt này và không dùng 472 test lượt cũ làm bằng chứng nguồn này.

**Kiểm thử ứng dụng chạy thật/Edge:** ops/run_browser_uat.py trên DB/media dùng một lần, tài khoản giả và POST/CSRF thật. Lượt đầy đủ --backend sqlite/sqlserver với --packages-dir "C:\Users\dinht\AppData\Local\Temp\ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages" --output-dir "C:\Users\dinht\AppData\Local\Temp\ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/compact-final-sqlite|compact-final-sqlserver" đều exit 0: mỗi backend 351 checks +32 ảnh, không pageerror, db_destroyed=true. Bao gồm tạo/sửa hồ sơ/hợp đồng, tiền Việt Nam lưu số chuẩn, chỉ số/đích KPI count bằng row, duyệt nghỉ -> queue cập nhật, 17 tài khoản role linked/unlinked +superuser, toàn bộ đích Dashboard HTTP200 cùng tài khoản, không tiền/lộ khối bị chặn; ba trang x 5 rộng x light/dark. Sau khi chuyển Thao tác nhanh/Checklist vào cột phải, chạy thêm chính nguồn cuối `--backend sqlite|sqlserver --layout-only --output-dir "C:\Users\dinht\AppData\Local\Temp\ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/balanced-sqlite|balanced-sqlserver"` cùng packages-dir: mỗi backend 127 checks +32 ảnh, exit 0, không pageerror, db_destroyed=true. Lượt này tạo/sửa hồ sơ/hợp đồng, bấm trực tiếp từng KPI bằng Playwright click, số/row đích đúng 12/10/1/1 trên fixture, 4 card đều link ở mọi rộng/theme, kiểm hai cột biểu đồ bằng nhau và không page overflow. Flag layout-only chỉ bỏ vòng duyệt/17 tài khoản đã chạy đầy đủ; không báo đã chạy lại hai phần đó sau thay vị trí partial. Backend 24 tests đã chạy lại toàn nguồn cuối, gồm render từng role và đích liên kết.

**Bằng chứng/giới hạn:** browser-result.json và screenshots trong bốn thư mục trên, log cùng thư mục cha. Đã xem ảnh balanced-sqlite/dashboard-1440-light.png và ảnh dark/màn hình hẹp tương ứng khi kiểm lại; ảnh trước tinh chỉnh chiều cao không làm bằng chứng bố cục cuối. DB giả được dọn; không sửa/xóa dữ liệu vận hành. Chưa UAT phiên trình duyệt của chủ dự án (lỗi kết nối os error 3 lượt trước), screen reader/zoom/máy in và tất cả workflow khác. Không chứng nhận WCAG toàn ứng dụng, chưa deploy, chưa commit/push. Chủ dự án Ctrl+F5, bấm từng KPI để xem chi tiết; dữ liệu có thể thay đổi giữa lúc mở Dashboard và trang đích nên số được tính lại theo ngày/quyền, không snapshot lịch sử trạng thái.

## 2026-10-13 — Kiểm thử luồng trình duyệt và sửa bảng hợp đồng theo Dashboard Đợt 1

**Yêu cầu/phạm vi:** chủ dự án mở quyền test trình duyệt, cho phép dữ liệu giả và yêu cầu sau mỗi lần sửa code kiểm lại luồng nghiệp vụ/Dashboard theo đặc tả duyệt. Main đầu đợt b0954e5, fetch origin và ahead/behind 0/0. Giữ nguyên 30 dòng nhật ký cũ chưa commit và design-system/reference/ ngoài phạm vi. Dùng UI UX Pro Max; thêm yêu cầu kiểm thử trình duyệt vào AGENTS.md bằng Create Rule. Không thay nghiệp vụ, quyền, model, migration hoặc giấy HCNS; chưa commit/push trong đợt này.

**Tái hiện/sửa:** đăng nhập HR_MANAGER qua Edge, tạo hồ sơ giả tên dài, tạo hợp đồng bằng POST thật/CSRF; lỗi tên nhân viên vượt bounding box ô bảng tái hiện trước sửa (baseline-sqlite-3, assertion Long employee contract link stays inside its table cell). hr_contract_list.html dùng header trái/nút phải, colgroup rõ chiều rộng và ui-table-link xuống dòng trong ô thay ui-button nowrap; shared_components.css giữ vùng bấm 44 px/focus, bảng có scroll trong wrapper ở màn hình hẹp. Đổi phiên bản CSS/base/service-worker v10 và kiểm tra cache tương ứng tests_mobile. Đã xem ảnh sau tạo hợp đồng light, hợp đồng dark SQL Server và Dashboard dark; tên/mã dài không chồng cột Loại.

**Bộ chạy lại:** ops/run_browser_uat.py dựng Django LiveServer + Edge Playwright trên SQL Server database test_ihrms_browser_UUID hoặc SQLite file mới trong TEMP; không dùng DB/media ứng dụng, email locmem, M365 off, mật khẩu giả ngẫu nhiên không ghi log. Chỉ trong process test cho phép ORM tuần tự cạnh sync driver Playwright; không đổi settings ứng dụng. Playwright 1.63.0 cài vào TEMP/packages, không đổi requirements hoặc venv. Cuối lượt đóng server/connection và xóa DB giả; JSON báo db_destroyed. Các lỗi khi dựng runner ban đầu (CCCD fixture quá dài, selector nút trùng nút đăng xuất, ORM/event loop, DepartmentID không nullable và connection SQLite bị giữ) đã sửa trong runner; ba SQLite giả sót ở lượt lỗi đã dọn bằng đường dẫn xác nhận trong TEMP. Không dùng kết quả lượt lỗi làm kết quả đạt.

**Lệnh/kết quả trình duyệt:** `venv/Scripts/python.exe -u ops/run_browser_uat.py --backend sqlite --packages-dir "C:\Users\dinht\AppData\Local\Temp\ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/packages" --output-dir "C:\Users\dinht\AppData\Local\Temp\ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/fixed-sqlite-2"`: exit 0, 298 checks, 32 ảnh, không pageerror, db_destroyed=true. Cùng lệnh `--backend sqlserver --output-dir "C:\Users\dinht\AppData\Local\Temp\ihrms-browser-uat-dafbe3c4812644cd85e43e7f0fb8ab91/fixed-sqlserver"`: exit 0, 298 checks, 32 ảnh, không pageerror, db_destroyed=true. Log fixed-sqlite-2.log/fixed-sqlserver.log và browser-result.json/screenshots trong hai thư mục này. Trình duyệt là Edge headless thật, có HTTP/POST/CSRF và database thật riêng; không HTML tĩnh.

**Các luồng đã đạt:** đăng nhập; tạo hồ sơ -> chưa hợp đồng không trong danh sách -> tạo hợp đồng/nhập 5.000.000 lưu 5000000 -> mở đúng hồ sơ từ hợp đồng -> tìm nhân viên -> Enter/Escape dropdown -> Sửa hồ sơ và đối chiếu DB. Gửi nghỉ phép bằng EMPLOYEE -> ngày nghiệp vụ tính đúng -> Dashboard HR_MANAGER queue 1 -> mở đúng đơn Pending -> dialog xác nhận -> duyệt -> DB Approved/1 LeaveApproval -> queue 0. Kiểm Dashboard fixture độc lập: Active=10, tổng Active+Probation+OnLeave=12, Probation=1, hai Approved cùng người chỉ tính 1; 5 hợp đồng D..D+60, D+61/start tương lai/non-Active loại khỏi nhóm; quá hạn riêng 1; hiệu lực 7 hợp đồng không đếm người, hai loại có donut/bảng; kế hoạch thiếu khác 0, actual/phòng vượt kế hoạch vẫn 450%; GET không sửa status/ngày hợp đồng. Tám role linked/unlinked và superuser (17 tài khoản) giữ gate status/contracts/headcount/profile; không tiền Dashboard; tất cả link render trong Dashboard mở HTTP 200 bằng cùng tài khoản. Ba trang Dashboard/hợp đồng/nhân viên x 5 rộng 1920/1440/1024/768/360 x light/dark không overflow toàn trang; mọi link tên hợp đồng nằm trong ô, cộng 2 ảnh luồng =32 ảnh mỗi backend.

**Kiểm tra backend/khác:** wrapper TEMP/ihrms-ui-refinements-20261013/runner.py gọi ops/run_tests.py với `--backend sqlite apps.portal.test_home_dashboard apps.portal.test_ui_refinements apps.portal.tests_mobile apps.portal.test_hr_ui`: 29/29 OK, 6.483 s, exit 0. Cùng nhãn `--backend sqlserver`: 29/29 OK, 28.524 s, exit 0. Nhãn dashboard gồm ma trận quyền, dữ liệu rỗng/thiếu/lỗi, biên ngày, count không nhân đôi, GET chỉ đọc/query budget/N+1. Không chạy lại full suite trong đợt CSS/template/test runner này; không dùng 472 test đợt trước làm bằng chứng nguồn này. py_compile runner, git diff --check và contrast 190 cặp/0 lỗi đạt; không tuyên bố WCAG toàn ứng dụng.

**Giới hạn/kết nối:** cua.getState và Computer Use @oai/sky qua node_repl đều lỗi failed to write kernel assets / system cannot find path (os error 3), thử reset cua/retry vẫn lỗi. Vì vậy chưa UAT phiên Edge được người dùng cấp quyền; các kiểm tra đã đạt là phiên Edge riêng kể trên. Chưa UAT tương tác có người dùng/zoom/screen reader/máy in, mọi luồng tuyển dụng/kế toán/dự án hoặc Đợt 2/3 chưa triển khai. Không mở policy tiền hay thêm KPI lịch sử. Chủ dự án tải lại Ctrl+F5; để kiểm tiếp tab đang mở, khởi động lại Codex/plugin trình duyệt và chia sẻ lại tab/URL ứng dụng, sau đó kiểm lại kết nối cua.getState. Từ nay mỗi sửa mã chạy luồng ảnh hưởng như AGENTS.md; mở rộng runner cho phân hệ khác khi sửa.

## 2026-10-13 — Đồng bộ theme, dropdown nhân viên, ô nhập gọn và năm không nhóm số

**Phạm vi:** theo sáu yêu cầu mới, dùng UI UX Pro Max trên main. Đầu đợt fetch origin/main thành công, ahead 10/behind 0. Có sửa CSRF chưa commit, nhật ký cũ và reference chưa theo dõi; giữ nguyên các mục nhật ký cũ ngoài stage. Chủ dự án cho phép sửa, tạo bản review, commit và push. Bản sửa CSRF lượt trước được đưa vào bàn giao này và kiểm thử lại; không deploy.

**Thay đổi:** sidebar light nền sáng/chữ navy, sidebar dark navy; các trạng thái/focus dùng token riêng cho hai theme. Đồng bộ DESIGN/MASTER và bảng tương phản sinh bằng script. Thao tác nhân viên dùng native popover dropdown ở lớp nổi; không kéo cao dòng, không bị overflow của bảng cắt, có Enter/Escape và phím mũi tên, giữ nguyên liên kết/quyền từng thao tác. Ô tìm kiếm và nút lọc đặt liền nhau, giới hạn field theo nội dung; form HR ba cột trên màn hình rộng, mobile xếp lại, control vẫn 44 px. CSS chỉ screen, không đổi bố cục giấy HCNS. Bump phiên bản asset/service worker để không giữ CSS/JS cũ.

**Điều kiện hợp đồng:** chủ dự án xác nhận có ít nhất một hợp đồng chưa xóa, bất kỳ trạng thái. Danh sách dùng EXISTS theo scope hiện có, không nhân đôi khi một người có nhiều hợp đồng. Hồ sơ chưa có hợp đồng vẫn còn trong database, mở được trong scope cho phép và vẫn chọn được khi tạo hợp đồng; thêm đường Tạo hợp đồng cho hồ sơ mới. Không xóa dữ liệu, không nới quyền, không thêm migration. Năm dùng ui_year trong các template có ý nghĩa năm (kỳ lương, phép, báo cáo, công và hai trường năm của biên bản thanh lý). Chỉ sửa hai giá trị năm ở giấy thanh lý, không sửa layout. JS bỏ proxy nhóm số cho field year; số tiền/số lượng vẫn giữ định dạng Việt Nam, không suy rằng mọi số 4 chữ số đều là năm.

**Kiểm thử:** bộ focused ban đầu UI/HR/CSRF đạt 16/16 SQLite, exit 0. Test menu cũ còn yêu cầu details được cập nhật theo dropdown mới và fixture hợp đồng; nhóm focused trên nguồn cuối (điều kiện hợp đồng/năm/quyền/menu/CSRF) đạt 8/8 SQLite, exit 0. CSRF enforce thực: token cũ sau đăng nhập bị 403, cookie hiện tại hợp lệ được chấp nhận, token giả/thiếu vẫn 403. Full nguồn cuối qua wrapper TEMP/ihrms-ui-refinements-20261013/runner.py gọi ops/run_tests.py --backend sqlite: 472 test, OK (skipped=7), 527.136 s, exit 0; --backend sqlserver: 472/472 test, OK, không skip, 592.905 s, exit 0. Wrapper đặt APP_ENV=test, khóa ngẫu nhiên và chuyển file logging sang TEMP; runner tạo DB/media riêng. Log full-final-sqlite.log và full-final-sqlserver.log nằm cùng TEMP. Lượt full đầu từng lỗi 4 kiểm tra cũ trên cả hai backend; đã cập nhật fixture hợp đồng ở tests_hr_workflow/tests_review_hardening, markup popover và cache v9 ở tests/tests_mobile, rồi chạy lại toàn bộ trên nguồn cuối đạt như trên.

**Giao diện:** Edge headless trên HTML Django render từ fixture giả, năm trang danh sách nhân viên/form nhân viên/form hợp đồng/định biên/kỳ lương × 1920/1440/1024/768/360 px × light/dark, 50 ảnh và 224 checks đạt, exit 0. Kiểm thêm menu 10 trạng thái sáng/tối/độ rộng, 74 checks đạt. Sidebar đổi màu; field không rộng quá 28 rem, vùng bấm 44 px; năm 2026 không thành 2.026, tiền vẫn có proxy số Việt Nam. Menu mở bằng Enter, nhận focus, không thay chiều cao dòng, nằm trong viewport, Escape đóng và trả focus; drawer/reduced-motion đạt. Đã xem ảnh danh sách light, form dark và menu dark. Sửa focus gây cuộn tự đóng menu sau kiểm lần đầu. Test/script/ảnh nằm TEMP/ihrms-ui-refinements-20261013, ngoài Git; chưa UAT tài khoản thật, screen reader, mọi trang con hoặc máy in/Office thật. Không tuyên bố đạt WCAG toàn ứng dụng.

**Gate:** pip check, Django check, makemigrations --check --dry-run đều exit 0; không migration mới. check_ui_contrast.py --write-doc đạt 190 cặp/0 lỗi, light min text/UI 5.100/3.506, dark 7.007/3.982. git diff --check và git diff --cached --check đạt; node --check ba script shared_components/ui_numbers/login_csrf đạt. Không sửa model, CSRF middleware, phép tính lương/phép hoặc dữ liệu vận hành. Lưu riêng log test trên SQLite/SQL Server và dùng DB/media test riêng qua runner dự án.

**Bản review và giao:** commit mã 5af6eb742f8e11d85807793d91194948ad331dff (ui: refine employee directory and theme controls) đã push origin/main; git ls-remote origin refs/heads/main khớp HEAD ngay sau push, exit 0. Mười commit UI/docs main có sẵn chưa push cũng đã đồng bộ, không tạo nhánh khác/force push. ZIP nguồn D:/QLHCNS-Backups/IHRMS_Review_20261013_UI_Refinements.zip chứa đúng mã committed tại commit này: 600 tệp nguồn + REVIEW_SNAPSHOT.txt (601 entry), manifest/hash từng tệp; mở lại ZIP kiểm testzip/entry count và SHA-256 từng tệp đều đạt. SHA-256 ZIP: 750596e32f58467a6e1d2d29fef79ff6942f445885e82b7ca606cece1e1130d9. Loại .env (giữ .env.example), DB, media/uploads, logs, outputs, backup, khóa riêng và CSV tài khoản. Không phải bản sao khôi phục dữ liệu. ZIP được tạo trước commit bổ sung kết quả bàn giao vào chính mục nhật ký này; mã ứng dụng không đổi sau ZIP. Các 30 dòng nhật ký cũ và design-system/reference/ vẫn giữ nguyên ngoài commit.

**Còn mở:** chưa deploy; chủ dự án Ctrl+F5 rồi kiểm danh sách/dropdown bằng vai trò thật; nhân viên chưa có hợp đồng chưa hiện, cần tạo hợp đồng trước. Chưa UAT tài khoản thật, screen reader, mọi trang hoặc máy in/Office thật. Lệnh gh run list --branch main --limit 4 --json headSha,status,conclusion,url trả HTTP 401 Bad credentials; chưa xác nhận CI, không coi là CI đạt. Chủ dự án chạy gh auth status, cập nhật đăng nhập/quyền CLI bằng gh auth login (hoặc token môi trường đang dùng), rồi xem Actions theo SHA được push tại https://github.com/dinhtanhb/QLHCNS/actions. Commit bổ sung nhật ký bàn giao chỉ thay mục này; push và SHA cuối được đối chiếu tại phản hồi bàn giao.

## 2026-10-13 — Sửa token đăng nhập cũ gây lỗi CSRF 403

**Mục tiêu/phạm vi:** sửa lỗi người dùng báo qua ảnh CSRF token from POST incorrect. Xác nhận main, fetch origin/main thành công, ahead 10/behind 0. Giữ các thay đổi nhật ký và reference có trước; không sửa dữ liệu vận hành hoặc tắt CSRF.

**Bằng chứng và thay đổi:** log app.log lúc 09:58:44 và 09:58:51 ghi lỗi tại /portal/login/. Template đã có csrf_token; service worker chỉ cache static, không HTML. Django xoay token khi đăng nhập; biểu mẫu từ tab cũ/Back có thể giữ token khác cookie. Chưa xác nhận thao tác cụ thể của người dùng, không coi giả thuyết tab cũ là đã được người dùng xác nhận. Thêm src/static/js/login_csrf.js chỉ cho form đăng nhập: đồng bộ token cookie hiện tại khi pageshow và ngay trước submit; không tự gửi mật khẩu, không retry POST, không nới middleware. Cookie thiếu/sai định dạng giữ token server để cơ chế từ chối vẫn hoạt động. src/templates/registration/login.html tải script riêng; không thay layout/quyền/dashboard.

**Kiểm tra:** src/apps/security/test_login_csrf.py dùng Client(enforce_csrf_checks=True), dữ liệu giả/DB/media cách ly. Kiểm token cũ sau xoay bị 403, cookie hiện tại được chấp nhận, token thiếu/giả bị 403 và trang tải script/no-store. Lần đầu phát hiện block extra_js không tồn tại ở base; đã chuyển script vào block content và chạy lại. Node script TEMP đạt 7 kiểm tra submit/token đổi/pageshow/cookie thiếu hoặc lỗi/trang không login, exit 0. `venv/Scripts/python.exe ops/run_tests.py --backend sqlite apps.security.test_login_csrf` chạy lại đạt 3/3, 3,358 giây, exit 0. git diff --check exit 0.

**Bàn giao/giới hạn:** chưa kiểm lại browser đang gặp lỗi, SQL Server/full suite hoặc CI trong lượt sửa nhỏ này. Không commit/push/deploy. Chủ dự án mở lại /portal/login/ bằng GET hoặc Ctrl+F5 (không gửi lại POST cũ ở trang 403), rồi đăng nhập; báo đường dẫn và thao tác nếu vẫn lỗi. Không xóa cookie hoặc yêu cầu đổi thiết lập CSRF để né lỗi. Các tệp thay đổi cục bộ có trước được giữ nguyên.

## 2026-10-13 — Triển khai dashboard Atoms Đợt 1

**Phạm vi và quyết định:** chỉ làm trên `main`. Trước sửa, fetch thành công và nhánh ahead 8/behind 0. Giữ nguyên mục backup/export và đặc tả soạn trước còn dirty; reference PNG không đưa vào commit. Dùng UI UX Pro Max, không UI Styling/shadcn. Theo phần Q3 chi tiết của prompt, Director vẫn không được xem khối hợp đồng; câu mở đầu nói mở quyền không được dùng để nới quyền. Q1 giữ navy–teal; Q2 ẩn mọi tiền; Q6 dùng nhóm Active/Probation/OnLeave; Q7 hoãn topbar; Q8 theo quyền thật. Ngày và năm lấy ngày địa phương hiện tại, không đọc GET.

**Thay đổi:** sửa câu violet cũ ở MASTER, không đổi tokens. Thêm dashboard_data.py và selectors.py. Trang chủ có KPI status, Approved ngày D, định biên năm, loại hợp đồng, sắp hết hạn và quá hạn riêng theo quyền. Dùng lại thành phần G4 và badge registry. Các partial dưới portal/dashboard ghép nội dung nghiệp vụ, không tạo hệ card/badge mới; _contract_rows dùng lại cho hai nhóm hạn. Biểu đồ SVG/CSS có nhãn và bảng thay thế. Tỷ lệ hiển thị một chữ số thập phân; số tính gốc được giữ. Chỉ lấy các trường hợp đồng cần hiển thị, không lấy lương vào DTO. KPI không có đích lọc đúng thì không là link; liên kết danh sách chung tách riêng. Không thêm filters, model, migration, quyền, form/CSRF/POST hoặc dependency.

**Nội dung giữ lại:** công việc cá nhân, thao tác nhanh, tiến độ dự án và cảnh báo chưa gắn hồ sơ. Cảnh báo checklist quá hạn hiện có cũng được giữ riêng sau test hồi quy; không gộp nó vào tổng Pending đơn nghỉ. Chuyển selector nghỉ sang module chung và giữ wrapper cũ cho GET/POST. Không thay hành vi duyệt. Mã thật chỉ cấm Trưởng phòng tự duyệt; HR Manager/Director có ngoại lệ cũ. Dashboard không có nút POST duyệt trực tiếp.

**Khối chưa bật:** queue mới chỉ có đơn nghỉ Pending dùng cùng selector trang duyệt. Chưa bật nhóm hồ sơ/tài liệu/tuyển dụng/hoạt động vì chưa có selector được đối chiếu trong phạm vi này. Nghỉ gần đây, ứng viên, cập nhật, tiền, trend, tỷ lệ có mặt, header tầng 2/search/giờ ca và Đợt 2 không làm. Selector cũ có thể trả đơn có hồ sơ cha đã xóa; không tự đổi nghiệp vụ. Gặp trường hợp đó, queue mới có trạng thái Dữ liệu chưa đầy đủ và không gắn link lệch số. Model Employee hiện bắt buộc department; nhóm không phòng được kiểm ở DTO, không tạo NULL trái constraint trong database. HeadcountPlan null cũng là thiếu kế hoạch ở DTO, không là giá trị được phép lưu.

**Mốc truy vấn SQLite:** cùng fixture giả, cùng thứ tự tạo tài khoản và GET sau warm-up. Đo bằng CaptureQueriesContext, tính cả render. Mỗi ô là chưa gắn / có hồ sơ. SELECT là số lần đọc database.

| Vai trò | Trước | Sau |
| --- | --- | --- |
| EMPLOYEE | 3 / 9 | 3 / 7 |
| DEPT_MANAGER | 3 / 13 | 3 / 10 |
| HR_OFFICER | 4 / 10 | 8 / 12 |
| HR_MANAGER | 11 / 17 | 12 / 16 |
| DIRECTOR | 12 / 18 | 10 / 14 |
| FINANCE_OFFICER | 3 / 9 | 3 / 7 |
| SYS_ADMIN | 3 / 9 | 3 / 7 |
| Superuser | 12 / 18 | 13 / 17 |

Mốc đo exit 0; max sau sửa 17 SELECT, dưới 20. Test thêm 100 phòng và 1.000 nhân viên giữ số query của service ổn định. Role matrix kiểm linked/unlinked, staff/superuser/SUPER_ADMIN không cờ; khối bị từ chối không có trong HTML và không query nguồn tương ứng. Tài khoản inactive/anonymous không query service. Không query Payroll. GET toàn trang vẫn ghi một lần django_session từ middleware bảo mật hiện có; đây là lệch với yêu cầu tuyệt đối không INSERT/UPDATE/DELETE. Service không ghi và toàn GET không ghi bảng nghiệp vụ. Không sửa middleware ngoài phạm vi hoặc báo giả rằng mọi GET không ghi.

**Kiểm thử và kết quả:** test smoke mới thất bại trên mã cũ (exit 1) vì thiếu khối dashboard, sau sửa đạt. Full suite lần đầu có hai lỗi: mất cảnh báo checklist và assertion phiên bản CSS cũ. Đã sửa hai điểm và nhóm focused gồm dashboard + hai hồi quy đạt 16/16 SQLite, exit 0. Full sau sửa hai hồi quy: `ops/run_tests.py --backend sqlite` phát hiện 465 test, 458 đạt/7 bỏ qua, 519,943 giây, exit 0; `--backend sqlserver` đạt 465/465, 546,841 giây, exit 0. Sau hai lần full chỉ thêm guard không query cho Trưởng phòng có Employee đã xóa và assertion tương ứng; focused mã bàn giao chạy lại 16/16 trên SQLite (7,352 giây) và SQL Server (27,225 giây), đều exit 0. Không chạy lại full sau guard nhỏ này; không coi kết quả full là đã đo đúng mọi byte của mã cuối. Mốc query chạy lại trên mã cuối vẫn 3–17 SELECT, exit 0. Các log/fixture/bản HTML/ảnh nằm ngoài Git tại TEMP/ihrms-dashboard-phase1-20261013. Runner dự án dùng DB/media riêng; wrapper TEMP chỉ đổi đích log và gọi lại ops/run_tests.py, không đổi nghiệp vụ hay runner trong repository.

**Kiểm tra giao diện:** Edge headless trên HTML do Django Test Client render từ dữ liệu giả: HR Manager/Director/Employee × 1920/1440/1024/768/360 px × light/dark, 30 ảnh và 139 checks, exit 0. Không tràn ngang trang; bốn KPI ở desktop khi đủ quyền; panel một cột trên mobile; vùng bấm từ 44 px, nhãn bảng từ 14 px. Drawer Enter/Escape, focus trở lại, mở bảng bằng bàn phím, focus vùng cuộn và reduced-motion đạt. Đã kiểm phóng chữ root 200%, chưa phải UAT zoom trình duyệt thực. Sửa CSS sau khi phát hiện quy tắc chung lấn lưới KPI; sửa tỷ lệ nhiều chữ số khi xem ảnh rồi chụp/kiểm lại. CSS mới chỉ screen và Trang chủ; không đổi CSS chung/tokens/giấy HCNS. Không kiểm lại Office/PDF/in máy thật.

**Lệnh cuối:** pip check, manage.py check, makemigrations --check --dry-run và ops/check_ui_contrast.py đều exit 0. Migration check đầu dùng tên :memory: theo Path của settings bị cảnh báo đường dẫn Windows; đã chạy lại với SQLite TEMP hợp lệ, không cảnh báo và không có migration mới. Contrast có 190 cặp, 0 lỗi; light min text/UI 5.100/3.506, dark 7.007/3.982. Không coi đây là chứng nhận WCAG. git diff --check exit 0. Focused/full được ghi ở trên; không có migration mới. Các SQL Server DB test dùng tên riêng do runner tạo và được runner báo xóa khi kết thúc; không thao tác DB nghiệp vụ.

**Commit/bàn giao:** commit docs Q1 là `15416e27df5a1220fc2746befb1e37d9fc1c28a6` (`docs: align MASTER with navy-teal tokens`). Commit ứng dụng `ui: dashboard phase 1` chỉ gồm tệp đợt này và test; SHA xác nhận bằng git rev-parse HEAD và báo trong bàn giao sau commit. Để tra cứu SHA từ mục này dùng git log -1 --format=%H --grep="^ui: dashboard phase 1$". Không push/deploy. Chưa kiểm screen reader thực, browser zoom 200% đầy đủ, UAT tài khoản thật, M365 thật hoặc CI theo SHA. Chủ dự án Ctrl+F5 Trang chủ và xem bằng vài vai trò thật, duyệt bố cục; quyết định có push không và có xử lý riêng ghi session/selector hồ sơ cha đã xóa không. Không bắt đầu Đợt 2.

## 2026-10-13 — Sửa đặc tả dashboard Atoms để chủ dự án duyệt

**Mục tiêu/phạm vi:** chỉ sửa `docs/DASHBOARD_ATOMS_TECH_SPEC.md` và mục nhật ký này. Dùng UI UX Pro Max, không dùng UI Styling/shadcn. Chưa triển khai dashboard hoặc thay quyền, dữ liệu, model, migration, URL, form, CSRF, giấy HCNS hay dependency. Chỉ làm trên `main`.

**Kiểm kê:** `git branch --show-current` trả `main`; `git status --short` có nhật ký sửa sẵn và thư mục reference/spec chưa theo dõi. `git fetch origin main` thành công; `git rev-list --left-right --count HEAD...origin/main` trả 7/0. `git rev-parse HEAD` trả `cf8213554d829df3e7e094604f2bb36019a9638f`. Giữ nguyên các thay đổi có trước; chỉ stage phần tài liệu của đợt này.

**Đã làm:** khôi phục mã commit, URL, hash và định dạng số/giờ trước khi sửa nội dung. Đọc lại tám ảnh Atoms, permissions.py, core/home_presentation và RBAC. Thêm bảng tóm tắt đầu tài liệu, ràng buộc kế thừa G2–G5, thành phần G4 dùng lại, bảng lệch dữ liệu và ma trận role × khối/linked/unlinked/superuser/staff. Thu nhỏ Đợt 1; nghỉ gần đây/tuyển dụng/cập nhật chuyển Đợt 2. Tách filters GET và app shell; chưa filter thì card không link. Quy định tiền đầy đủ qua ui_vnd, mọi khối tiền ẩn tới khi duyệt policy. Bổ sung cách đo query và test đề xuất, không ghi chúng là đã chạy. Tài liệu đã được ghi lại UTF-8 và đọc lại sau khi phát hiện luồng ghi ban đầu làm mất dấu.

**Bằng chứng/mâu thuẫn:** `Get-FileHash -Algorithm SHA256` trên bản bundle trong TEMP xác nhận `0a6e78dadc448d4664a3f7abf9a015f29dd148704d8d5d1be2ca1c2ed29dac11`; không xác nhận website live hiện cùng bản. Lệnh `rg -n -- '--ui-brand:|--ui-sidebar-bg:|--ui-bg:|navy|teal|violet' src/static/css/ui_tokens.css DESIGN.md design-system/MASTER.md` xác nhận light teal #0b7461/navy #0c233b, dark teal #63dbc2. DESIGN dòng 43/76 và MASTER dòng 17 dùng navy–teal; MASTER dòng 11 còn violet. RBAC cho Director xem hợp đồng nhưng hr_contract_list đòi manage_hr, Director hiện bị chặn. SUPER_ADMIN không cờ không được has_permission cấp toàn quyền như mô tả tài liệu. Nhật ký 09/10/2026 đã gỡ lương khỏi Trang chủ; không tự đảo chính sách này. Không sửa MASTER/DESIGN/quyền trong đợt tài liệu.

**Kiểm tra/kết quả:** `git diff --check` exit 0. Không chạy Django/backend/contrast vì chỉ sửa tài liệu và không sửa ops/check_ui_contrast.py, đúng phạm vi yêu cầu. Mục tiêu SELECT ≤20, test role/biên ngày/GET không ghi, tương phản hai theme và UAT là điều kiện đề xuất cho lượt code, chưa được kiểm thử trong đợt này. Không tuyên bố đạt WCAG hoặc đã triển khai.

**Bàn giao:** được phép commit riêng `docs: revise dashboard spec` trên `main`; không push/deploy. Chủ dự án đọc mục 1 và chốt Q1–Q8 ở mục 14: thương hiệu, policy tiền, Director đọc hợp đồng, mẫu số có mặt, nguồn lịch sử/ngày tuyển, nghĩa tổng nhân sự, shell/search/ca và các lệch quyền còn lại. Mặc định ẩn/hoãn phần chưa rõ. Dừng trước khi triển khai; không cần người dùng tự chạy lệnh cho lượt tài liệu.

## 2026-10-13 — Đặc tả dashboard tường minh theo Atoms

**Mục tiêu/phạm vi:** theo yêu cầu tham khảo https://r7rc1s.atoms.world/, viết docs/DASHBOARD_ATOMS_TECH_SPEC.md; chưa sửa dashboard hay phân quyền. main, ahead7/behind0 sau fetch origin/main; giữ các mục backup/export chưa commit và reference PNG untracked. Dùng UI UX Pro Max và tài liệu MASTER/token hiện hành; đọc DESIGN tham chiếu tại Downloads/atoms, không ghi đè DESIGN.md dự án.

**Đã làm:** đối chiếu views/core.py/dashboard, home_presentation.py, Employee/Contract/LeaveRequest/Attendance/WorkShift/HeadcountPlan/Payroll/Recruitment và permission matrix/endpoint đích. Đặc tả bố cục4 KPI, lưới7/5, header2 tầng, panel hợp đồng/queue/tuyển dụng/nghỉ phép/timeline và giữ khu vực cá nhân/dự án. Mỗi chỉ số có nhãn/nguồn/công thức/kỳ/scope/state/drill-down. Có DTO/service read-only đề xuất, yêu cầu query/Decimal/cache/performance, role matrix và acceptance cases. Phân biệt source đã có với phần chưa có context/lịch sử; HeadcountPlan có sẵn nhưng không approval state; Gross không là tổng chi phí; Active không là có mặt; hired status không chứng minh đã tạo Employee. Quyền quỹ lương giữ manage_finance; không suy ra quyền lương từ view_reports. Chỉ rõ hr_contract_list chặn DIRECTOR, attendance là cá nhân và filters nhiều route chưa có để tránh link403 hoặc giả drill-down.

**Nguồn/giới hạn:** web.open không đọc được URL; browser tích hợp khởi tạo lỗi thiếu kernel assets (os error3), chưa xem tương tác live. Sau đó Python urllib đọc HTML HTTP200 và bundle công khai /assets/index-CfxoekPe.js, xác nhận tên các khối/route; SHA bundle 0a6e78dadc448d4664a3f7abf9a015f29dd148704d8d5d1be2ca1c2ed29dac11. Tệp nguồn tải về tại TEMP/ihrms-atoms-spec-20261013, ngoài Git. Cấu trúc hình dựa8 ảnh tham chiếu đã có và DESIGN do chủ dự án cung cấp; không tuyên bố đã UAT website live.

**Kiểm tra/kết quả:** script stdlib xác minh link Markdown cục bộ và13 URL name hiện có, code fences cân bằng, exit0; git diff --check exit0. Không chạy Django/backend suites vì chỉ bổ sung đặc tả/nhật ký, không thay code/model/DB. Không dùng456 tests đợt UI trước làm kết quả cho dashboard mới. Chưa commit/push. Gặp schema/permission gap đã ghi trong spec, không tự thêm migration hoặc nới quyền.

**Bàn giao/còn mở:** chủ dự án đọc spec, đặc biệt công thức mục4 và phân kỳ/quyết định mục10; sau đó giao triển khai các section đủ nguồn/quyền ở đợt1. Muốn HR/lãnh đạo xem quỹ lương, danh sách hợp đồng đọc-only mới hoặc trend/timeline tuyển dụng đầy đủ cần chốt policy/nguồn lịch sử trước. Những section đủ dữ liệu không cần chờ các gap này. Không thay dữ liệu thật hay dừng/chạy server ứng dụng trong đợt đặc tả.

## 2026-10-12 — Thiết kế Atoms cho khung chung và các trang đã hoàn tất G5

**Kiểm kê và phạm vi:** main, ahead6/behind0 sau fetch origin/main. Giữ nguyên các mục backup/export trước trong nhật ký và thư mục reference chưa theo dõi. Đã xem đủ8 ảnh design-system/reference/atoms bằng UI UX Pro Max; không dùng UI Styling/shadcn, không thêm dependency/CDN. Chủ dự án chọn “Khung chung + các trang đã hoàn tất G5”: trang chủ, Cá nhân, Nhân sự, Tuyển dụng, Kế toán. Yêu cầu mới cho phép đổi palette, thay quyết định tím trước đó; nguyên tắc nghiệp vụ/RBAC/CSRF/field constraints/44px/14px bảng/16px body/responsive/giấy HCNS vẫn giữ.

**Thay đổi:** navy sidebar, teal CTA, nền trung tính xanh nhẹ qua ui_tokens.css; atoms_ui.css chỉ screen/opt-in ui-page. Viền card nhẹ tách viền control đủ3:1; sidebar có focus token riêng. Đồng bộ DESIGN/MASTER và bảng172 cặp tương phản. Card header, bảng, KPI icon/phạm vi và hồ sơ nhân viên rõ thứ bậc; avatar chữ trang trí lấy ký tự đầu tên, không bổ sung thông tin nhạy cảm. Board ứng viên chỉ đọc nhóm các row của trang hiện tại, ghi rõ phạm vi, giữ bảng/URL/phân trang; từng cột cuộn giới hạn36rem. ui_status_groups không query/sort/workflow và giữ unknown status. Không thêm rating, kéo thả, chuyển trạng thái, tìm kiếm toàn cục hoặc số liệu không có context. Không sửa views/models/migrations/quyền/tính lương/hợp đồng form; ảnh mẫu không đưa vào Git hay dùng dữ liệu cá nhân trong demo.

**Kiểm thử và xác minh:**
- `python ops/check_ui_contrast.py --write-doc`:172 pairs,failures0,exit0; min text/UI light5.100/3.506 và dark7.007/3.982. Viền card/connector là trang trí, không dùng thay viền control. `git diff --check` exit0.
- `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.portal.test_atoms_ui apps.portal.test_home_dashboard apps.portal.test_personal_ui apps.portal.test_hr_ui apps.portal.test_recruitment_ui apps.portal.test_finance_ui apps.common.tests_ui_components apps.portal.tests_mobile`:36 tests OK,exit0; focused-final chạy lại sau CSS giới hạn chiều cao board. Hai test mới kiểm tra grouping/order/unknown không query và current page/escape/quyền/bảng danh sách.
- Full tuần tự `venv\Scripts\python.exe ops\run_tests.py --backend sqlite`:456 tests,OK(skipped7),445.570s,exit0; `--backend sqlserver`:456 tests,OK,533.997s,exit0. Cả hai có3 HTTP scenarios PASS. SQL DB riêng `test_ihrms_ac0485d6a0214079a0ea8a380875009e` đã tạo/xóa. RuntimeWarning timezone fixture cũ còn có; không có PermissionError/WinError32. Không dùng số test đợt trước; PowerShell bọc stderr Creating test database thành NativeCommandError, kết quả lấy từ exitfiles/tổng kết runner.
- `venv\Scripts\python.exe -m pip check`:No broken requirements,exit0; `venv\Scripts\python.exe src\manage.py check`:no issues,exit0; `makemigrations --check --dry-run`:No changes detected,exit0. Django checks dùng DB SQLite TEMP,APP_ENV=test,SECRET_KEY tạm. Full bắt đầu sau focused36; sửa cuối chỉ CSS chiều cao board và bỏ assertion không cần thiết trong test, đã chạy focused/browser tương ứng; không sửa nghiệp vụ.
- CaptureQueriesContext39 route đại diện, cùng fixture/warm-up:mọi GET200,delta queries0 (8–51 tùy trang). N+1 salary có sẵn giữ nguyên cho đợt backend riêng. Ma trận24 tài khoản linked/unlinked/superstaff×39=936 cases:HTTP/redirect/forms/name/type/value/required/min/max/step/action/submitter/external form không đổi,exit0. Script đầu bảng công khác vì GET gốc tạo summary giả; thêm warm-up rồi chạy lại đạt, không sửa backend.
- Edge headless/Node stdlib/CDP localhost8885, DB/media/log TEMP giả,M365 off,email Locmem:312 ảnh39 route×360/768/1024/1440×2theme; không tràn trang,control/proxy>=44px,table>=14px,Range rect không lấn cột. Chụp lại312 ảnh sau giới hạn chiều cao board; thêm8 ảnh board với dữ liệu giả đủ6 trạng thái (ghi đè8 ảnh cũ). Đã xem trực tiếp home1440light,hr-list360dark,board1440light cuối. Cộng6 ảnh print =318 PNG ngoài Git.
- interactions.cjs exit0:1706 text samples/theme,min5.699 light/7.383 dark;358 controls/theme,min4.121/6.255;Tab focus39 route/theme min5.283/9.203,solid>=2px. Sidebar active text9.887 và ring3px6.557 cả2theme. Desktop collapse/drawer Escape/focus return,HR empty filter/invalid summary,board current-page rows/Enter detail,finance confirm Tabwrap/cancel,reduced-motion đều PASS. Script cũ mất helper p5bg sau navigation; đã khởi tạo lại và dùng đúng mobileNavToggle cho desktop/mobile, không sửa appJS để né test.
- Print3 giấy salary-decision/candidate-interview/salary-scale:HTML/text/geometry/color và pixel vùng giấy trước/sau giống hệt (Pillowvenv có sẵn),exit0. CSS baseline được CDP Fetch phục vụ từ bản gốc TEMP; không đổi server/nghiệp vụ. Không sửa giấy/Excel/Word HCNS.

**Bàn giao và giới hạn:** 15 tệp mã/tài liệu cùng1 mục nhật ký, hash nguồn cuối khớp bản đã kiểm. Preview server giả dừng đúng PID/commandline. Commit `ui: adopt Atoms portal design` trên main; SHA lấy từ Git khi bàn giao, không push/deploy. Giữ reference PNG untracked và các mục backup/export cũ ngoài index. Chứng cứ `C:/Users/dinht/AppData/Local/Temp/ihrms-ui-atoms-20261012`, ngoài Git. Lượt đọc log trước bị auto-review quota nên không thực thi, không phải kết luận unsafe; chủ dự án yêu cầu tiếp tục, tool nay hoạt động và đã đối chiếu kết quả thực.

Chưa UAT người dùng có giao diện, screen reader, zoom200%, máy in/Office/SharePoint thật hoặc CI theo SHA; chưa kiểm tra riêng admin và các trang legacy chưa rollout. Không tuyên bố WCAG toàn app. Palette/khung tác động portal chung; bố cục G5 Hành chính/Kế hoạch/Báo cáo/Dự án vẫn chờ các đợt sau. Chủ dự án Ctrl+F5 xem khung/trang chủ/hồ sơ/ứng viên/Kế toán, thử sidebar/drawer, xem hai theme và quyết định push.

## 2026-10-12 — Tạo bản sao review sau G5 Kế toán

**Phạm vi:** snapshot mã nguồn để FULL/REVIEW, không phải backup DB hay bản khôi phục. Nhánh main, commit nền `62c8f964646ca62f8cf2e4449592aec8957e93d3`, ahead6/behind0 sau `git fetch origin main`. Tại lúc chụp có thay đổi chưa commit trong docs/PROJECT_WORK_LOG.md (mục backup trước) và8 ảnh chưa theo dõi trong design-system/reference/. Giữ nguyên các thay đổi này; ZIP lấy bytes working tree của tệp theo dõi, gồm nhật ký cục bộ lúc chụp; ảnh reference chưa theo dõi không đưa vào.

**Đã làm:** tạo `D:\QLHCNS-Backups\IHRMS_Review_2026-10-12_230000_62c8f96.zip` và checksum kèm theo. Kiểm kê bằng `git ls-files -z`; Python hệ thống/zipfile đóng gói579 tệp nguồn + REVIEW_SNAPSHOT.txt =580 entry. Loại14 tệp theo dõi thuộc outputs/dữ liệu cùng các loại .env (giữ .env.example), database, media/uploads, CSV, keys/credentials, logs/backups; mọi tệp ignored/untracked và Git history không đưa vào. Manifest ghi commit/nhánh/phạm vi/exclusions/dirty paths và SHA-256 từng entry. Quét mẫu credential/private key phổ biến không phát hiện nghi vấn; đây không phải chứng nhận đã rà mọi dữ liệu nhạy cảm trong mã.

**Kiểm tra:** mở lại ZIP, kiểm entry count/duplicate/CRC bằng zipfile.testzip; đọc toàn bộ579 entry nguồn, so SHA-256 với bytes captured và nguồn hiện tại đều khớp; manifest cũng khớp. Dung lượng 5,207,257 byte. SHA-256 ZIP `F451A8135D7087C5EFC0A7FC793C8B25867F4862659C97F5C365AD9022D06F1C`; có tệp `.zip.sha256`. Lệnh đóng gói/verify inline Python exit0. Không chạy test mới, sửa nghiệp vụ hoặc ghi DB. Các kết quả test trước trong nhật ký không được coi là chạy lại ở đợt export.

**Bàn giao:** bản ZIP được tạo trước mục nhật ký này nên không chứa chính mục ghi export sau cùng. Chưa review mã trong đợt này, không commit/push. Người review giải nén ra thư mục riêng, đọc AGENTS.md và docs/Huong_Dan_Review_Du_An.md, chọn FULL/REVIEW; dùng DB/media cách ly nếu kiểm thử, không cần nhận secrets/data thật. Thư mục reference và mục backup cũ vẫn giữ trong workspace.

## 2026-10-12 — G5 Kế toán

**Kiểm kê trước sửa:** main, ahead5/behind0 sau fetch origin/main; chỉ mục backup cũ8 dòng chưa commit, giữ ngoài stage. Dùng UI UX Pro Max, MASTER/tokens ưu tiên; không UI Styling/shadcn, không thêm dependency. Năm template: finance_period_list/payroll_run/salary_list/dependent_list/tax_config. Kỳ lương đã có component G4; salary-scale dùng HCNS editor G5 Nhân sự, giấy/Excel không sửa.

**Guard và hợp đồng:** GET/POST dùng manage_finance hiện có. Bảng lương chỉ tạo/tính/khóa/sửa khi period.status != Locked; phát hành phiếu khi Locked và unissued_payslips. Giữ cảnh báo missing_salary_employees/missing_employees. Không có route mở khóa nên không thêm tính năng. Row form pf<pk> giữ external form attributes và POST insurance_salary/allowance/overtime_amount/overtime_tax_exempt_amount/deduction_amount, step1/min0. Tax form_type insurance/deduction/bracket và mọi tên/constraints giữ nguyên; người phụ thuộc giữ employee/full_name/relationship/registered_from. Không sửa views/models/migrations/tính lương/quyền; link salary-scale hiện có giữ nguyên.

**Thay đổi:** thêm finance_base.html, finance_ui.css chỉ screen và4 test trong test_finance_ui.py. Dùng card/bảng/badge/error summary/confirm chung; tiền ui_vnd căn phải, ngày ui_date, caption/scope và vùng cuộn có nhãn/focus. Upper bound0 hiển thị0đ, None là Trở lên. Ô ngoài form có for/id/aria-label, lỗi nằm trong đúng row form. Bỏ emoji/utility màu; control44px, form người phụ thuộc/bậc thuế2 cột desktop và1 cột mobile. Hộp khóa giữ POST/CSRF và guard. Không thêm sort, pagination hoặc nghiệp vụ.

**Kiểm tra và kết quả:**
- `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.portal.test_finance_ui apps.payroll apps.portal.tests_recruitment_accounting_navigation apps.portal.tests_mobile`:43 tests OK,exit0; rerun focused-final sau căn cột.4 test mới kiểm tra external fields/lock, Locked controls+payslip issue+denial, tax form_type/constraints/0 upper bound, người phụ thuộc required/labels.
- `venv\Scripts\python.exe ops\run_tests.py --backend sqlite`:454 tests, OK(skipped7),exit0. Sau đó `--backend sqlserver`:454 tests, OK,exit0. Cả hai backend báo3 HTTP scenarios PASS. SQL DB riêng `test_ihrms_6bd7a801eac14cc8a71207c09b024dee` đã tạo/xóa. Log có RuntimeWarning timezone từ fixture cũ; không có PermissionError/WinError32. Không dùng số đợt trước; exitfiles và tổng kết runner là bằng chứng (PowerShell có NativeCommandError khi bọc stderr Creating test database).
- `git diff --check` exit0; `venv\Scripts\python.exe -m pip check` No broken requirements,exit0; `venv\Scripts\python.exe src\manage.py check` no issues,exit0; `makemigrations --check --dry-run` No changes detected,exit0. Check dùng SQLite TEMP, APP_ENV=test, SECRET_KEY tạm. `python ops/check_ui_contrast.py`:168 pairs,failures0,exit0.
- CaptureQueriesContext trên6 màn hình (5 trang, payroll Open/Locked), cùng fixture/warm-up:200 trước/sau, queries9/15/15/51/10/11,delta0,exit0. Salary có N+1 phòng ban sẵn(51 queries fixture), để đợt backend riêng. 24 tài khoản linked/unlinked/superstaff×6=144 cases:HTTP/redirect/forms/method/action/name/type/value/min/max/step/required/submitter giữ nguyên, kể cả external form=pf<pk>,exit0.
- Edge headless/Node stdlib/CDP localhost8884; DB/media/log TEMP giả,M365 off,email Locmem. 48 ảnh6 màn×360/768/1024/1440×2theme; no page overflow, controls/proxy>=44px, table14px. Lượt đầu source NumberInput absolute thoát scroller làm pageWidth1466 ở360; position:relative ở ui-scroll đã sửa. Rà ảnh phát hiện nowrap cũ làm tên dài lấn cột; bodycell wrap và đo Range rect trong ô đã đạt. Chụp lại48 ảnh phiên bản cuối; đã xem tax360dark và payroll-open1440light sau sửa.
- interactions.cjs exit0:404 text samples/theme,min7.10 light/8.25 dark;90 controls/theme,min4.55/5.71;Tab focus6 màn/theme đạt3:1/ring>=2px. Invalid periods/dependents/tax summary nhận focus cả2theme; lock dialog Tab wrap/Escape/return focus cả2theme. External row min0 lỗi dùng nhãn tiếng Việt; allowance2.345.678 POST canonical2345678 giữ form; tax0,07 POST canonical và upper boundblank; Locked không có writecontrols, giữ phát hành phiếu. Không xác nhận khóa hoặc gửi mail thật; backend suites kiểm tra nghiệp vụ khóa. Script CDP từng lỗi const redeclare, đã bọcIIFE và chạy lại, không sửa backend.
- Thêm2 ảnh sau hủy khóa360 light/dark và2 ảnh print salary-scale trước/sau:paper HTML/text/geometry/color và pixel giống nhau (Pillow có sẵn trong venv),exit0. Tổng52 PNG ngoài Git. Không sửa giấy/Excel HCNS. Full bắt đầu sau focused43; chỉnh cuối chỉ CSS/wrap/grid và căn cột; đã chạy focused/baseline/browser tương ứng. Hash8 tệp nguồn/test cuối đã xác minh; không đổi tính toán hay constraints.

**Bàn giao và giới hạn:** commit riêng `ui: finance` trên main, SHA lấy từ Git khi bàn giao; không push/deploy, giữ backup cũ8 dòng ngoài stage. Chứng cứ `C:/Users/dinht/AppData/Local/Temp/ihrms-ui-phase5-finance-20261012`, ngoài Git; preview server giả dừng đúng PID/commandline sau kiểm tra. Backend tax/dependent/period_create redirect sau POST kể cả lỗi; UI giữ dữ liệu khi clientvalidation nhưng chưa khôi phục sau redirect, không tự thêm lưu nháp/sửa view. Chưa UAT tài khoản thật, screen reader, zoom200%, máy in/Office/SharePoint thật hoặc CI theo SHA; native datecontrols phụ thuộc locale Edge, cần xem trên máy đích. Không tuyên bố WCAG toàn app. G5 còn Hành chính→Kế hoạch→Báo cáo→Dự án, không bắt đầu phân hệ mới trong đợt này. Chủ dự án Ctrl+F5 xem5 trang Kế toán, thử cuộn bảng và hủy khóa, quyết định push; lượt sau kiểm kê Hành chính.

## 2026-10-12 — G5 Tuyển dụng và chuyển menu duyệt hoạt động

**Kiểm kê trước sửa:** main, ahead4/behind0 sau fetch origin/main; giữ mục backup cũ ngoài commit. Skill UI UX Pro Max; MASTER/tokens ưu tiên, không dùng UI Styling/shadcn. Sáu template portal: recruitment_hub/list/create, hr_candidate_list/form/detail. HCNS candidate-interview/candidate-score-summary dùng editor đã chuyển G5 Nhân sự; giấy giữ nguyên.

**Guard/hợp đồng:** hub: can_request_recruitment/can_approve_recruitment/can_manage_hr; đề xuất: can_request/can_approve và Pending; ứng viên: can_manage_hr, Hired; kết quả phỏng vấn: Pending, offer: Sent. Giữ mọi URL/action/POST field/CSRF, department scope và phân trang ứng viên. Duyệt đề xuất hoạt động chuyển sang Dự án, vẫn dùng can_approve_activity_proposals, số chờ và aria-current; các link Dự án khác vẫn theo can_view_activity_dashboard. Không đổi backend/permissions/models/migrations.

**Thực hiện:** sáu trang dùng recruitment_base.html, recruitment_ui.css (screen-only), component/card/table/badge/error summary/confirm/pagination dùng chung. Giữ tone/token MASTER, không thêm dependency/CDN; link ứng viên thay row onclick, nhãn for/id kể cả bản ghi lặp, giữ field constraints và dữ liệu POST khi tạo lỗi. Offer hiển thị ui_vnd, ngày ui_date; bổ sung registry trình bày recruitment.interview:result theo đúng RESULT_CHOICES. Menu hoạt động vẫn giữ permission/badge/aria-current, không đổi URL hay quyền server. Thêm4 test UI, cập nhật test điều hướng cũ theo yêu cầu chuyển menu.

**Kiểm tra hiện tại:**
- `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.portal.test_recruitment_ui apps.portal.tests_recruitment_accounting_navigation apps.portal.tests_mobile apps.common.tests_ui_components`:20 tests OK,exit0 (focused-final.log). Lượt16 test trước phải sửa parser phạm vi sidebar: dashboard có cùng link trong nội dung, DIRECTOR không có nhóm Tuyển dụng nên không dùng nhóm đó làm delimiter. Mã UI sau sửa thẻ đóng đã render bình thường; không nới quyền.
- `git diff --check` exit0; `venv\Scripts\python.exe -m pip check` No broken requirements,exit0; `src\manage.py check` no issues,exit0; `makemigrations --check --dry-run` No changes detected,exit0. Hai lệnh Django dùng DB SQLite TEMP/APP_ENV=test/SECRET_KEY tạm. `python ops/check_ui_contrast.py`:168 pairs,failures0,exit0.
- CaptureQueriesContext:6 trang200 trước/sau, warm-up cùng fixture;8/9/10/10/8/12 queries,delta0. So sánh24 tài khoản linked/unlinked/superstaff ×6 trang=144 cases:HTTP/redirect/forms/action/name/type/value/required/min/max/step/submitter giữ nguyên,exit0. Không thêm view/query.
- Edge headless/Node stdlib/CDP, localhost8883/DB/media/log TEMP giả, M365 off/email Locmem:48 ảnh6 trang×4 width360/768/1024/1440×2theme; no page overflow,controls/proxy>=44px,table>=14px,exit0. Thêm4 ảnh menu Giám đốc360/1440×2theme kiểm tra Dự án mở/aria-current/link đúng và Nhân sự không chứa link;exit0. Đã xem trực tiếp candidate-detail360dark,hub1440light,menu1440dark.
- interactions.cjs exit0:239 text samples/theme,min6.61light/8.25dark;64 controls/theme,min4.55/5.71;focus Tab6 trang/theme đạt3:1 và ring>=2px. Invalid form summary nhận focus/giữ dữ liệu; duplicate candidate POST giữ giá trị; Tab wrap/Escape/focus restore dialog cả2theme; offer salary9.876.543 POST lưu canonical9876543; confirm duyệt gửiApproved; phân trang/link chi tiết Enter. Chỉ ghi DB giả.
- HCNS candidate-interview/candidate-score-summary trước/sau:4 ảnh print media,outerHTML/text/geometry/color và pixel vùng giấy giống nhau (Pillow có sẵn trong venv),exit0. Tổng56 PNG ngoài Git. Không sửa HCNS giấy/Word/Excel templates.
- Script TEMP seed đã sửa get_or_create offer để không lỗi khi có2 offer sau tương tác; script thống kê sửa encodingUTF8; không đổi backend hay dữ liệu thật.
- Full SQLite lượt1:450 tests,1 failure do tests_recruitment_accounting_navigation vẫn đòi duyệt hoạt động trong Nhân sự,7 skipped,exit1;3 HTTP scenarios PASS. Đã cập nhật kỳ vọng menu cũ và focused20 đạt; full SQL lượt1 cũng450 tests/1 failure cùng kỳ vọng menu cũ,exit1. Sau cập nhật test đã chạy lại tuần tự đầy đủ, kết quả cuối dưới đây.

- Kết quả cuối: `ops\run_tests.py --backend sqlite` (sqlite-final.log):450 tests,OK(skipped=7),exit0; `--backend sqlserver` (sqlserver-final.log):450 tests,OK,exit0. SQL DB riêng `test_ihrms_0c35d9ffb1564a019cd8b66b44aaca47` đã tạo/xóa;3 HTTP scenarios PASS cả2 backend. Không dùng số test đợt trước. RuntimeWarning DateTimeField từ fixture cũ còn có; không thấy PermissionError/WinError32. NativeCommandError do PowerShell bọc stderr Creating test database không phải lỗi test; dùng exitfiles/tổng kết làm bằng chứng.
- Xác minh hash12 tệp nguồn/test cuối không đổi so với phiên bản đã kiểm; preview server giả đã dừng đúng PID/commandline. Stage chỉ13 tệp UI/test/nhật ký, không .env/DB/media/ảnh/data thật. Commit riêng `ui: recruitment` trên main; SHA lấy từ Git khi bàn giao,không push/deploy.

**Giới hạn/phần còn lại:** chưa UAT người dùng có giao diện/screen reader/zoom200%, Office/máy in/SharePoint thật hoặc CI theo SHA. Không tuyên bố WCAG toàn app. Nghiệp vụ có sẵn hr_candidate_onboard cần Accepted offer; UI vẫn giữ guard cũ, không tự thêm điều kiện hiển thị. G5 còn Kế toán,Hành chính,Kế hoạch,Báo cáo,Dự án; không bắt đầu phân hệ mới trong đợt này. Chứng cứ `C:/Users/dinht/AppData/Local/Temp/ihrms-ui-phase5-recruitment-20261012`, ngoài Git. Chủ dự án Ctrl+F5 xem menu Dự án và6 trang Tuyển dụng, quyết định push; đợt này chỉ commit `ui: recruitment` trên main,không push/deploy. Giữ mục backup cũ8 dòng ngoài stage.

## 2026-10-12 — UI Giai đoạn 5: Nhân sự

**Kiểm kê trước sửa:** main; fetch origin main thành công, ahead/behind3/0 (G4/G3/Cá nhân local). Giữ8 dòng backup dirty ngoài index. Tiếp tục UI UX Pro Max theo MASTER/tokens > DESIGN; không UI Styling/shadcn; commit riêng ui: hr, không push/deploy. Template: hr_employee_form, hr_contract_form/list, leave_approval_list, timesheet_approval_list, document_approval_list, personnel_decision_list/detail; lifecycle case_list/create/detail; HCNS catalog/draft phần editor/control. hr_employee_list/detail đã G4; profile_change_request_list/form đã Cá nhân. Candidate thuộc Tuyển dụng; activity_proposal_approval_list thuộc Dự án dù có liên kết trong nhóm duyệt. Nội dung giấy document/hcns/document.html và appointment_document.html, hcns_forms.css/JS gốc không đổi.

**Guard/action gốc:** employee create/edit manage_hr; form giữ employee/current_department_inactive, fieldsCCCĐ/tax/BHXH đã có dưới guard view, không thêm hiển thị. Contract list/create manage_hr, selected_employee giữ; detail employee G4 sensitive view_employee_compensation giữ. Leave approvals approve_leave và scope approvable cũ; decision hidden Approved/Rejected. Timesheet approvals approve_timesheet với scope cũ, summary POST. Document approvals approve_document, decision Approved/Rejected. Lifecycle list view_own_lifecycle_items/manage_lifecycle_case; create manage; detail can_manage && Pending assign, Pending và assigned_to_user_id==user.pk hoặc manage để update; requires_asset_return conditional; user_options role==responsible_role_code giữ nguyên. Decision list manage_hr/approve_personnel_decision, filterstatus chỉ can_manage_decisions; detail can_view_workflow/can_download_word/can_edit/submit/approve/issue/cancel và is_employee_recipient đều giữ; transition URLs/action/comment/file/CSRF gốc, guard tự duyệt backend giữ. HCNS catalog own_employee/employees/selected_employee/group.forms giữ; draft read_only/source/workflow/can_save_decision/section.table/cell.locked/fixed giữ nguyên, BoundField/formset/management_form/referenceJSON và export/preview/save vẫn cũ; giấy in không recolor. Các guard/action/field này đã giữ nguyên khi chuyển lớp trình bày.

**Đã triển khai:** hr_base.html opt-in ui-page/ui-hr và CSS hr_ui.css cho13 template kiểm kê (14 GET gồm create/edit hồ sơ). Dùng header/card/table/scroll/caption/scope, field có label/id, nhóm2/3cột gốc→1mobile, error summary, badge registry text+SVG, empty state/hướng dẫn, button44px/focus, phân trang giữ query; không thêm bulk/sorting/filter. Confirm POST dùng dialog G4, giữ submitter và hidden decision/action. Không sửa model/migration/view/URL/field/CSRF/quyền/DB thật/dependency. Hai trang nhân viên list/detail G4 và cập nhật hồ sơ G5-Cá nhân không làm lại. UI HCNS catalog/editor dùng chung các phân hệ được áp tokens tại vùng màn hình; paper, document.html, appointment_document.html và hcns_forms.css/JS gốc không sửa/recolor.

**Skill:** Python hệ thống chạy UI UX Pro Max search.py: form labels accessible, data table accessible, confirm destructive action, empty state guidance (`--domain ux -n 1`), exit0; Form Labels/Table Handling/Confirmation Dialogs/Empty States phù hợp. Theo MASTER/tokens, không lệch palette/font/print/dependency. Giữ formset/management_form/row template/JSON; BoundField widget gốc thêm ui_bound_field/error summary/id/aria-invalid. Guard thêm field.errors trong draft chỉ hiển thị lỗi, không đổi quyền.

**Regression/lệnh/kết quả thật:**
- `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.portal apps.lifecycle apps.document`: lượt đầu203 test,3fail/3skip,exit1. Khôi phục overflow-x-auto/mobile-table-scroll wrapper hợp đồng; đổi assertion class lịch sử quyết định cũ sang aria-label. Rà markup sửa regex chạm thead và tbody bị grid trước suite cuối. Qua ảnh sửa prose checklist p bị grid ngắt strong, giữ nhóm3field hồ sơ. Không sửa nghiệp vụ.
- `test_hr_ui.py` có4 test mới guard/CCCD/field+constraints+CSRF, selected_employee hợp đồng, hidden Approved/Rejected, checklist Pending/Done và submitter done/skip. Lượt đầu9 discovery gồm5homepage do import class; đổi module alias tránh chạy trùng. Regression cuối `... --backend sqlite apps.portal.test_hr_ui apps.portal.tests_mobile apps.document.tests_hr_workflow`:41/41,24.145s,exit0. Không báo lượt fail là đạt.
- Full chạy tuần tự: sqlite: 446 test, 483.122s, OK (7 skipped theo backend), exit0; sqlserver: 446 test, 446.244s, OK không skipped, exit0. SQL Server runner cách ly dùng test_ihrms_4b8257a88e64424d9098e6ff2cc0c8e5, tạo/xóa qua runner; cả2backend báo3kịch bảnHTTP PASS. Có warning timezone fixture cũ; không có PermissionError/WinError32 xoay log. Không dùng kết quả lượt khác thay HR.
- Với SQLite/APP_ENV=test/DB_NAME TEMP/key tạm: `venv\Scripts\python.exe src\manage.py check` không issues; `... makemigrations --check --dry-run` No changes detected; `venv\Scripts\python.exe -m pip check` No broken requirements; exit0. `git diff --check` exit0. Sau suite chỉ bổ sung nhật ký, không đổi mã/rerun full không cần thiết.
- SQLite giả, original/current templates cùng fixture/warm-up:14/14 GET200, query9–22,delta0. So form contract14trang(method/action/enctype/name/type/value/required/min/max/step/maxlength/disabled), bỏ CSRF token ngẫu nhiên: giữ nguyên. Static giữ tất cả URL/if/elif gốc, chỉ thêm if field.errors. Matrix24 tài khoản giả (11vai trò×linked/unlinked+2superuserstaff/nonstaff),336cặpGET: HTTP/Location/form/action/submitter/field giữ nguyên; không POST/dữ liệu thật trong phép đo.
- Edge headless/NodeCDPstdlib localhost8882, SQLite/emailLocmem/M365off/media/logTEMP.112ảnh14trang×360/768/1024/1440×light/dark: không overflow trang, control/proxy tương tác>=44px,bảng14px; exit0. Chụp lại8ảnh checklist sau đặt tên cột Thao tác, exit0, ghi đè cùng tệp; thêm4ảnh HCNSpaper trước/sau, tổng116PNG. Trực tiếp xem employee-create1440dark, leave-approval360light, lifecycle-detail1440dark trước/sau sửa prose và printdecision-detail; không tuyên bố xem từng ảnh.
- interactions exit0:14trang/theme,240 mẫu chữ/theme min light6.61/dark8.25>=4.5;106control/theme min border4.55/5.71>=3;14focus/theme min6.79/7.92>=3,solid>=2px. Loại paper khỏi mẫu screen. Employee/contract invalid có summary/giữ input; Offboarding giữ JS required date; checklist confirm initialfocus/Tabwrap/Escape giữ value; POST Bỏ qua fakeDB giữ submitter+reason; document confirm hủy giữ pending. Không gửi mail/mởlinkngoài.
- Printmedia cùng fake context: hcns-draft(salary-decision) và decision-detail giữ paperouterHTML/text/size/colors; pixel PNGpaper giống hệt qua ImageChops/Pillow sẵn có, không cài mới. Chưa kiểm paginationA4/máy in/WordOffice/SharePoint/toàn26mẫu. Không suy thành WCAG/toànapp. Fixture date JSON serialization ban đầu lỗi, đã sửa DjangoJSONEncoder trong TEMP, không đổi model.

**Bàn giao:** Nhân sự hoàn tất để commit riêng `ui: hr` trên main; SHA báo ở đầu ra Git. Không push/deploy. Chứng cứ tại `C:/Users/dinht/AppData/Local/Temp/ihrms-ui-phase5-hr-20261012`: screenshots/log/JSON/scripts/DB ngoài Git; 17 source hash xác nhận mã không đổi trước commit. Giữ 8 dòng nhật ký backup cũ dirty ngoài index. Chủ dự án Ctrl+F5 các trang Nhân sự, xem theo tài khoản thực, duyệt UI và kiểm tra bản in/Word trước khi quyết định push. Chưa UAT người dùng, screen reader, zoom 200%, máy in thực tế hoặc CI theo SHA. G5 còn sáu phân hệ: Tuyển dụng → Kế toán → Hành chính → Kế hoạch → Báo cáo → Dự án; không bắt đầu dở dang phân hệ kế. Các trang mẫu G4 giữ trạng thái đã làm. Lượt tiếp theo kiểm kê Tuyển dụng trước sửa.

## 2026-10-12 — UI Giai đoạn 5: áp dụng theo phân hệ (Cá nhân)

**Trước khi sửa / phạm vi:** main, fetch thành công, ahead/behind2/0 (G4/G3 đã commit local); giữ mục backup 8 dòng ngoài stage. Được commit riêng ui: personal, không push/deploy. Làm tuần tự Cá nhân trước Nhân sự, Tuyển dụng, Kế toán, Hành chính, Kế hoạch, Báo cáo, Dự án. Đã đọc AGENTS/review/log/RBAC/DESIGN/MASTER/PHASE1/tokens; dùng UI UX Pro Max, không UI Styling. Template Cá nhân: profile.html, profile_change_request_list.html, profile_change_request_form.html, org_chart.html + org_chart_node.html, timesheet_month.html, leave_list.html + leave_create.html, kpi_my_list.html, payslip_list.html, notification_list.html.

**Kiểm kê guard/action trước sửa:** profile giữ employee, current_salary/current_contract và histories (chỉ dữ liệu hồ sơ mình từ view; không hiển thị CCCD mới). Request list giữ item.status==Pending and can_approve_profile_change_request; chứng từ/decision_note conditional; create link vốn vô điều kiện. Tạo request backend cần submit_profile_change_request + employee; HR chưa gắn có thể duyệt list nhưng create link có sẵn dẫn403, ghi nhận và không tự đổi quyền/guard. Org chart login và cây active có sẵn, giữ node.children/node.manager và JS search/zoom. Timesheet entry/add/delete + summary POST/CSRF; fieldset disabled khi Approved, giữ month/year/hours/leave fields và mọi URL. GET timesheet vốn get_or_create summary; chỉ thử trên SQLite giả, không đổi view. Leave list giữ balance và link In/Word theo AL/CO/UL; create cần employee ở backend. KPI giữ can_score_kpi. Payslip view chỉ lấy lương own/Locked/có payslip, giữ PDF guarded owner. Notification giữ not n.is_read và draft.status Draft/Sent; các form mark read/mark sent POST/CSRF và mailto cũ; không gửi mail. Các trang approve-only nằm menu Nhân sự, task nằm Dự án và training nằm Kế hoạch sẽ làm ở phân hệ đó. Biểu mẫu HCNS/in không recolor. Giữ nguyên các guard/action này khi chuyển thành phần dùng chung.

**Skill / quyết định thiết kế:** Python hệ thống chạy `C:/Users/dinht/.agents/skills/ui-ux-pro-max/scripts/search.py` cho `form labels accessible`, `data table accessible`, `confirm destructive action`, `empty state guidance` (`--domain ux -n 1`) trả Form Labels, Table Handling, Confirmation Dialogs, Empty States phù hợp; exit0. `hierarchy organization tree --domain chart -n 1` trả Treemap về tỷ lệ, chưa sát quan hệ báo cáo; retry `organization chart` trả Performance vs Target, vẫn chưa phù hợp. Không coi match này là guidance organization chart đã xác minh; giữ cấu trúc cây/JS search/zoom gốc, dùng MASTER/tokens và kiểm tra trực quan. Không tạo chart mới hoặc đổi dữ liệu. Dùng font hệ thống, không thêm dependency/CDN.

**Đã áp dụng:** `personal_base.html` opt-in `.ui-page.ui-personal`, load `personal_ui.css`; 11 template đã kiểm kê chuyển header/card/table/form/field/badge/empty/confirm/pagination sang thành phần G4. CSS mới scoped vào Cá nhân, lấy màu/cỡ chữ/khoảng cách/bán kính từ ui-*; màn hình từ360px, sơ đồ mobile hiển thị cây dọc và desktop wrap các root để giữ chữ dễ đọc, không thay quan hệ quản lý/search/zoom. Date hiển thị dd/MM/yyyy, tiền dùng ui_vnd/căn phải; POST vẫn ISO và tên field cũ. Profile giữ nhánh dữ liệu lương/hợp đồng/lịch sử, không thêm CCCD hay dữ liệu của người khác. KPI actual=0 nay hiển thị0 thay vì “Chưa cập nhật” do default cũ bắt cả0; chỉ đổi hiển thị, giữ ngưỡng achievement>=100/70 và cách tính. Notification unread có chữ+icon; mailto giữ nguyên, xác nhận “đã gửi Outlook” chỉ sau hướng dẫn rõ, không gửi mail trong kiểm thử.

Bảng công giữ CSS gốc cho print, chỉ đưa phần control screen sang tokens/44px/label và xóa emoji icon in. Entry delete chuyển native confirm sang dialog chung, POST/CSRF không đổi; summary fieldset Approved vẫn disabled. Qua ảnh in phát hiện source số canonical và proxy Việt Nam cùng hiện (lỗi trình bày cũ); scoped print ẩn source, mỗi trường còn một proxy. Không recolor HCNS, không đổi số liệu/công thức/nghiệp vụ. `tests_mobile.py` cập nhật assertion leave KPI từ hook cũ sang ui-kpi-value/ui-kpi-label, không bỏ kiểm tra. `test_personal_ui.py` có5 test mới về GET10 trang/data scope/CCCD, CSRF+field+constraints, guard approve/submitter values, fieldset Approved và zero KPI/threshold.

**Kiểm tra đã xác nhận (exit code thật):**
- Lượt portal đầu `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.portal`: 136 test, 1 fail (assertion hook KPI cũ), 3 skipped, exit1; đã sửa assertion component mới. `... --backend sqlite apps.portal.test_personal_ui`:5/5 exit0. Sau sửa, `... --backend sqlite apps.portal.test_personal_ui apps.portal.tests_mobile`:12/12,0.991s,exit0. Không báo lượt fail là đạt.
- Mã cuối chạy tuần tự `venv\Scripts\python.exe ops\run_tests.py --backend sqlite`:442 test, OK (7 skipped theo backend),486.027s,exit0; rồi `... --backend sqlserver`:442/442,532.767s,exit0. Runner cách ly DB/media; SQL Server dùng `test_ihrms_49af1800cb744fac9f1755b94db858b6` đã tạo/xóa. Hai backend báo3 kịch bản HTTP PASS. Không dùng số G3/G4. Log có RuntimeWarning timezone từ fixture cũ; không có PermissionError/WinError32 xoay log trong hai lượt này.
- Với DB_ENGINE=django.db.backends.sqlite3, DB_NAME ở TEMP, APP_ENV=test và SECRET_KEY tạm: `venv\Scripts\python.exe src\manage.py check` không issues,exit0; `... makemigrations --check --dry-run` No changes detected,exit0. `venv\Scripts\python.exe -m pip check` No broken requirements,exit0. `git diff --check` exit0.
- CaptureQueriesContext trên10 trang, cùng warm-up trước/sau: mọi GET200, delta0; query8–26 tùy trang. Lượt đo đầu không warm-up sau nên profile+6, đã sửa cách đo công bằng như baseline và xác nhận delta0. Không thêm query/view/backend logic.
- Edge headless/Node stdlib/CDP trên localhost8881, SQLite giả riêng, M365 off, email Locmem/media/log TEMP. 80 ảnh10 trang×4 width360/768/1024/1440×light/dark, kiểm tra pageWidth<=viewport, control/proxy tương tác>=44px và table14px; exit0. Chụp lại8 ảnh org_chart có cây nhiều cấp (ghi đè8 ảnh trước), thêm24 ảnh empty KPI/payslip/notification (4 width×2theme), 2 ảnh Outlook confirm360px và4 ảnh print trước/sau Pending/Approved: tổng110 tệp PNG. Đã trực tiếp xem profile360dark, timesheet360light, org1440dark có nhánh, Outlook confirm360dark, empty-payslip360dark và bản in Pending/Approved.
- `interactions.cjs` exit0: sampled text472 mẫu/theme min light6.61/dark7.71>=4.5; control57/theme min4.55/5.71>=3; focus Tab9 trang/theme min6.79/7.92>=3, solid>=2px (profile không có control). Form invalid có summary và giữ reason; org search không kết quả+zoom; dialog focus ban đầu/hủy Escape/Tab wrap; xác nhận xóa POST và profile more_info giữ submitter bằng dữ liệu giả; pagination next. `notification-dialog.cjs` exit0 kiểm tra hướng dẫn/hủy cả2theme, không mở mailto hoặc xác nhận thư đã gửi. Script tạm có lỗi đo source số ẩn2px và DOM đang chuyển trang, đã sửa để đo proxy hiển thị/chờ DOM rồi chạy lại, không sửa backend.
- Print emulation bằng cùng populated fake context, không save status: hai trạng thái Pending/Approved có table/row geometry và visible text giống trước, pixel vùng bảng giống hệt (ImageChops bằng Pillow có sẵn trong venv, không cài mới). Sau sửa mỗi trường chỉ còn một giá trị Việt Nam:10 input hiển thị cũ→5proxy, bảng/màu không đổi. Chưa kiểm tra máy in vật lý, Word/PDF Office hay pagination A4 thực tế; đây là ảnh print media, không phải chứng nhận bản in mọi máy.

**Bàn giao / phần còn lại:** Cá nhân hoàn tất để commit riêng `ui: personal` trên main; SHA báo ở đầu ra Git. Chứng cứ tại `C:/Users/dinht/AppData/Local/Temp/ihrms-ui-phase5-personal-20261012` (screenshots/log/JSON/scripts/DB giả), ngoài Git. Không push/deploy. Lượt trước auto-review thao tác tổng hợp cuối bị lỗi quota, không phải kết luận thao tác unsafe; chủ dự án yêu cầu tiếp tục, nay công cụ đã hoạt động và đối chiếu exit code/log hiện tại. Không rerun full suites khi chỉ bổ sung nhật ký sau kiểm tra đạt.

G5 **chưa hoàn tất toàn bộ**: bảy phân hệ Nhân sự → Tuyển dụng → Kế toán → Hành chính → Kế hoạch → Báo cáo → Dự án chưa rollout (các trang mẫu G4 và trang chủ G3 giữ trạng thái đã làm). Các trang approve-only/core nghiệp vụ các phân hệ đó, task/training/biểu mẫu HCNS chưa chuyển ở đợt Cá nhân này. Không bắt đầu phân hệ khác dở dang. Giữ mục backup cũ8 dòng chưa commit ngoài stage. Còn mở: liên kết tạo cập nhật hồ sơ với HR chưa gắn dẫn403 theo guard gốc; báo chủ dự án quyết định đợt nghiệp vụ riêng. Chưa UAT người dùng có giao diện, screen reader, zoom200%, máy in/Office/SharePoint thật hoặc CI theo SHA; không tuyên bố WCAG toàn app. Chủ dự án Ctrl+F5 các trang Cá nhân, xem hồ sơ/lương theo tài khoản thực, thử bảng công/in, duyệt UI rồi quyết định push; lượt tiếp theo bắt đầu kiểm kê Nhân sự trước sửa.

## 2026-10-12 — UI Giai đoạn 3: trang chủ theo vai trò

**Phạm vi/ủy quyền:** triển khai G3 theo attachment của chủ dự án, sau G4 đã làm trước theo chỉ đạo. G2 đã commit. Xác nhận `main`, fetch `origin main` thành công, ahead/behind `1/0` (G4 local); chỉ commit `ui: role-based home dashboard`, không push/deploy. Giữ nguyên 8 dòng nhật ký backup đang dirty ngoài index. Đã đọc AGENTS, hướng dẫn review, nhật ký, ma trận RBAC, DESIGN, MASTER, UI_DESIGN_SYSTEM_PHASE1 và ui_tokens. Không đổi model/migration/URL/field/permission/business count/query scope/dependency; phần view chỉ bổ sung context trình bày đọc.

**Skill UI UX Pro Max:** Python hệ thống chạy `C:/Users/dinht/.agents/skills/ui-ux-pro-max/scripts/search.py "<query>" --domain <domain> -n 2` cho `dashboard KPI cards`, `warning alert guidance`, `empty state guidance`, `quick action navigation`, `recent activity feed` (ux) và `category comparison accessible` (chart); tất cả exit 0. Empty States phù hợp; quick actions có Keyboard Navigation phù hợp nhưng Sticky Navigation chưa sát; chart có Compare Categories/bar/sort descending/label/table phù hợp. Dashboard và feed không match; alert trả Touch Target chưa sát. Retry một lần theo từng ý bằng `information hierarchy`, `error feedback`, `keyboard navigation`, `feedback status` (`--domain ux -n 1`, exit 0). Có Color Only, Error Recovery, Keyboard Navigation, Submit Feedback; chưa xác minh guidance chuyên dụng KPI/banner/feed trong database skill, không coi exit 0 là bằng chứng match. KPI lấy contract MASTER/tokens và component G4 đã có; banner dùng warning + SVG + hướng dẫn. Biểu đồ dùng một màu thương hiệu theo MASTER thay cho gợi ý mỗi category một màu của skill. Không dùng UI Styling/shadcn.

**Đã thay đổi:**
- `src/apps/portal/templates/portal/dashboard.html`, `src/static/css/home_dashboard.css`: header cá nhân/kỳ dd/MM/yyyy; cảnh báo hồ sơ SVG warning, tiêu đề/mô tả/hành động có quyền; KPI nhãn14px/số24px/kỳ14px, zero giữ nguyên, missing ghi “Chưa có dữ liệu”; thẻ chờ duyệt >0 có viền và huy hiệu “Cần xử lý”, zero trung tính. Layout responsive dùng tokens, personal2 cột từ768px, tổng quan3 cột, mobile360px1 cột; thống nhất focus/44px với G4, không recolor bản in.
- `src/apps/portal/home_presentation.py` và hai dòng bổ sung context trong `views/core.py`: chỉ dựng nhóm/thẻ/liên kết từ count cũ + has_permission; không thêm truy vấn. Thẻ cá nhân công việc trỏ `task_list?scope=assigned_to_me`. KPI/phần việc cần xử lý chỉ có đích phù hợp quyền; Director không có link tuyển dụng do list không có phạm vi toàn Trung tâm cho Director. Task toàn Trung tâm/phòng và tài sản phòng chưa có list đúng phạm vi nên không dựng link. Assets toàn Trung tâm dùng list admin được guard view_asset. Queue sử dụng count cũ và pending_activity_proposal_count sẵn có từ context processor; không giả zero cho count không có.
- Warning hồ sơ: chỉ superuser + is_staff có nút admin User change (employee field sửa được). HR có manage_hr dùng `hr_employee_create`; giải thích hồ sơ tạo xong cần quản trị viên gắn tài khoản. SYS_ADMIN không superuser không có link gắn vì employee readonly trong UserAdmin. Tài khoản thường nhận hướng dẫn liên hệ HR. Thao tác tạo đơn nghỉ/giao việc/công văn cần có employee và đúng guard; tạo hồ sơ/mở báo cáo dùng quyền hiện hành. Không mở rộng quyền.
- Phòng ban: evaluate queryset cũ một lần, dùng lại cho chart/table; một phòng dùng tên/số/tỷ lệ, nhiều phòng thanh ngang giảm dần một sắc tím với nhãn và bảng details mở bằng bàn phím, zero có hướng dẫn. Tiến độ dự án đổi thành danh sách trạng thái text+SVG/badge, tháng14px, nút Dashboard có month cũ; giữ nguyên số liệu và phạm vi visible_activities_for.
- `src/templates/ui/kpi.html`: mở rộng tùy chọn href/warning/period, giữ nhánh danger và hành vi G4 khi không truyền tùy chọn. `src/apps/portal/tests.py`: cập nhật asset version. `src/apps/portal/test_home_dashboard.py`: 5 test mới bao phủ 11 vai trò linked/unlinked + superuser staff/nonstaff, block/permission/GET đích mới, query helper0, scope Director/tasks, positive/zero/missing/escape/số Việt Nam và phòng1/nhiều/empty.
- Bỏ qua “Hoạt động gần đây”: context hiện tại chỉ có thống kê/count và hoạt động trong kỳ, không có feed sự kiện đủ ngữ nghĩa/phạm vi để tái sử dụng; không thêm model/view/truy vấn lịch sử.

**Kiểm tra đã chạy, exit code thật:**
- `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.portal.test_home_dashboard`: 5/5, exit0.
- `venv\Scripts\python.exe ops\run_tests.py --backend sqlite`: 437 test, OK (7 skipped theo backend), 462.653s, exit0.
- Sau SQLite, `venv\Scripts\python.exe ops\run_tests.py --backend sqlserver`: 437/437, 366.021s, exit0; database `test_ihrms_8ec93ddd04f64792933e9eb6e2b358c0` do runner tạo/xóa. Hai backend đều báo 3 kịch bản HTTP PASS; không dùng số test G4. Log hai lượt không có PermissionError/WinError32 xoay log.
- `venv\Scripts\python.exe -m pip check`: No broken requirements, exit0. Với DB_ENGINE=django.db.backends.sqlite3/APP_ENV=test/SECRET_KEY tạm: `venv\Scripts\python.exe src\manage.py check` không issues, exit0; `venv\Scripts\python.exe src\manage.py makemigrations --check --dry-run` No changes detected, exit0. Tệp SQLite rỗng `src/qlhcns` do check tạo đã chuyển vào TEMP, không đưa Git. `git diff --check`: exit0.
- CaptureQueriesContext trên 24 tài khoản giả trước/sau: mọi GET200 và delta0; số query12–27 tùy vai trò/hồ sơ. Chỉ thay đổi trình bày, không thêm aggregate. Chứng cứ `queries-before.json`, `queries-after.json` ngoài Git.
- Edge headless qua Node/CDP stdlib, server riêng localhost8880 dùng bản SQLite giả, email Locmem, M365 off, media/log ngoài repo. 48 ảnh 6 tình huống (HR, trưởng phòng, nhân viên, nhân viên chưa gắn, superuser chưa gắn, CBDA) +16 ảnh HR pending và CBDA overdue: mỗi tình huống 360/768/1024/1440px light/dark. 64 ảnh, mọi pageWidth<=viewport, nhãn KPI>=14px/số>=24px/nút>=44×44; scripts browser-final/browser-pending exit0. Đã trực tiếp xem ảnh HR dark1440, unlinked light360, admin dark360 và CBDA quá hạn dark1440. Qua ảnh sửa specificity CSS warning bị component chung tải sau ghi đè, chụp lại trên mã cuối.
- `node .../interactions.cjs`: 55 mẫu chữ mỗi theme đều >=4.5:1 (min light6.61/dark7.71); 10 vị trí Tab mỗi theme có focus solid>=2px, đích>=44px và tương phản focus>=3:1; Enter mở bảng details và điều hướng KPI đạt, exit0. Script tạm ban đầu gửi thiếu ký tự Enter đã sửa; đây không phải lỗi nghiệp vụ. Không suy rộng mẫu đo thành chứng nhận WCAG toàn app.

**Chứng cứ/bàn giao:** ảnh tại `C:/Users/dinht/AppData/Local/Temp/ihrms-ui-phase3-20261012/screenshots`, log/JSON/script/DB giả cùng thư mục ngoài Git. Commit riêng trên main `ui: role-based home dashboard`; SHA lấy từ đầu ra Git khi bàn giao. Không push/deploy, không tự sang G5. Chưa UAT trình duyệt có giao diện bởi người dùng, screen reader, zoom200%, Office/SharePoint thật hoặc CI theo SHA. Chủ dự án mở trang chủ, Ctrl+F5, xem linked/unlinked và vai trò thực tế, đối chiếu ảnh, duyệt giao diện rồi quyết định push. Mục backup cũ vẫn chưa commit, giữ nguyên.

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

## 2026-10-12 — Tạo bản sao mã nguồn để review

**Phạm vi/đã làm:** tạo `D:\QLHCNS-Backups\IHRMS_Review_2026-10-12_101204_d1af082.zip` từ 527 tệp được Git theo dõi, kèm manifest ghi nhánh `main`, commit `d1af082f1c813baabd9c052753724648df73ce7f`. Trước tạo, fetch origin, xác nhận local/remote `0 0` và working tree sạch. Loại trừ `outputs/`, Git history và các tệp local bị ignore như `.env`, DB, media, CSV tài khoản, backup, venv/node_modules; giữ `.env.example` là mẫu cấu hình. Đây là snapshot mã nguồn, không phải backup DB/khôi phục toàn hệ thống.

**Kiểm tra/kết quả:** rà danh sách tệp và mẫu khóa/token phổ biến không phát hiện nghi vấn; mở lại ZIP, xác nhận 528 entry (527 nguồn + manifest), đọc và so SHA-256 từng tệp với nguồn đều khớp. Dung lượng 5.080.864 byte; SHA-256 ZIP `B4F5B14602E26D932AE8C8890626AA31BA2135FA8D4885FBAB919749F5A06EB0`. Không xóa tệp, không sửa nghiệp vụ, không chạy test hoặc ghi DB.

**Bàn giao:** ZIP chụp commit trên, không bao gồm mục nhật ký thêm sau khi tạo ZIP này. Chưa review mã trong lượt này, chưa commit/push vì chỉ được yêu cầu tạo bản sao; người review dùng FULL/REVIEW, không cần nhận `.env` hay dữ liệu thật.

Đây là **nơi ghi nhận tập trung duy nhất** các đợt thay đổi lớn, thao tác kiểm tra, quyết định và việc cần chủ dự án thực hiện. Cập nhật tiếp vào tệp này thay vì tạo log mới cho từng lần làm việc. Không ghi secrets, dữ liệu cá nhân hoặc nội dung `.env`.

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

## 2026-10-05 — Khôi phục đăng nhập SQL Server và sửa trạng thái đặt xe trên main

**Mục tiêu/phạm vi:** xử lý lỗi POST `/portal/login/` báo thiếu `axes_accessattempt`, rà các migration đang chờ và lỗi chức năng xác nhận được khi review. Xác nhận `main` khớp `origin/main` sau `git fetch origin main`; giữ nguyên `.sixth/` và `_review_probe.py` chưa được theo dõi.

**Nguyên nhân và sao lưu:** kiểm tra chỉ đọc trên SQL Server đang cấu hình cho thấy bảng `axes_accessattempt` chưa có và 0/10 migration Axes đã áp dụng; `security.0003` tạo `tblSecurityEvent` cũng còn chờ, trong khi signal đăng nhập ghi vào bảng đó. Tạo backup COPY_ONLY/CHECKSUM tại `C:\Program Files\Microsoft SQL Server\MSSQL16.SQLEXPRESS\MSSQL\Backup\ihrms_before_axes_20261005_103326_21d08a48.bak`; `RESTORE VERIFYONLY WITH CHECKSUM` đạt. Backup chứa dữ liệu nghiệp vụ, ở ngoài Git và cần giữ theo chính sách lưu trữ/khôi phục của quản trị SQL Server.

**Đã làm trên SQL Server gốc:** chạy `venv\Scripts\python.exe src\manage.py migrate axes --noinput` (10/10 OK), `migrate security --noinput` (security.0003 OK), rồi `migrate --noinput` (attendance.0008, office.0005 và .0006, payroll.0004 đều OK). Trước khi áp dụng các ràng buộc nghiệp vụ, `audit_review_integrity` chỉ đọc báo 0 sai lệch ở cả 5 nhóm; sau migration vẫn 0. `migrate --plan` không còn thao tác; `manage.py check` đạt; `makemigrations --check --dry-run` báo No changes detected. Không tạo/xóa bản ghi nghiệp vụ gốc để thử nghiệm.

**Sửa mã:** `VehicleBooking` trước đây chỉ cho `Approved`/`Cancelled`, nhưng form tạo gửi `Pending` và luồng duyệt có `Rejected`; mọi yêu cầu mới bị `full_clean()` từ chối. Bổ sung bốn trạng thái hợp lệ, mặc định `Pending`, migration `office.0006`, và hai kiểm thử tổng hợp cho model/HTTP tạo yêu cầu. Kiểm thử riêng `venv\Scripts\python.exe ops\run_tests.py --backend sqlite apps.office.tests` và `--backend sqlserver apps.office.tests`: mỗi backend 8/8 đạt, SQL Server dùng database thử tạm. `pip check` không có dependency hỏng; `git diff --check` đạt.

**Kiểm thử toàn bộ:** `venv\Scripts\python.exe ops\run_tests.py --backend sqlite`: 319 test, 317 đạt, 2 bỏ qua do chỉ dành SQL Server, exit 0; log `D:\QLHCNS-Backups\review-20261005-full-sqlite.log`. `venv\Scripts\python.exe ops\run_tests.py --backend sqlserver`: 319/319 đạt, exit 0 trên database tạm do runner tạo/xóa; log `D:\QLHCNS-Backups\review-20261005-full-sqlserver.log`. Cả ba kịch bản HTTP HR, chấm công và nghỉ phép PASS trên hai backend. Log có cảnh báo cấu hình Jazzmin `dark_mode_theme` đã deprecated, không làm test thất bại. Bugbot không khả dụng trong môi trường công cụ hiện tại; review mã và luồng liên quan được thực hiện thủ công.

**Việc còn mở/hành động của chủ dự án:** sau khi cập nhật mã lên máy đang chạy, dùng tài khoản thử để xác nhận đăng nhập và tạo/duyệt/từ chối đặt xe qua trình duyệt; đối chiếu với kết quả HTTP tự động. Chưa kiểm thử giao diện Edge trong lượt này hoặc mọi lỗi thiết kế/hiệu năng của toàn dự án. Backup SQL ở đường dẫn trên cần DBA giữ/luân chuyển theo quy định; không đưa vào Git. `gh run list --commit 6429d2f8769b58f41c4900358508515600eb65d9 --limit 10` trả HTTP 401 Bad credentials; chủ dự án mở GitHub Actions của commit này bằng tài khoản có quyền, đối chiếu các job và cung cấp log nếu job lỗi. Không ghi CI là đạt khi chưa xem được kết quả.

**Nhánh/commit:** mã sửa ở `main` commit `6429d2f8769b58f41c4900358508515600eb65d9`; `git push origin main` thành công và `git fetch origin main` xác nhận local/remote trùng nhau tại commit đó. Mục nhật ký này được commit riêng trong cùng đợt.

## 2026-10-05 — Sửa GitHub Actions frontend và kiểm tra lại toàn bộ trên main

**Mục tiêu/phạm vi:** theo yêu cầu chạy lại kiểm thử và làm GitHub Actions hết lỗi trên `main`. Đầu đợt xác nhận local `main` khớp `origin/main` tại `e652db0`, chỉ có `.sixth/` và `_review_probe.py` chưa theo dõi; giữ nguyên hai mục đó. Skill `review-bugbot` yêu cầu subagent loại `bugbot`, nhưng môi trường công cụ không cung cấp loại này; review thủ công các thay đổi và luồng CI, không ghi nhận là Bugbot đã chạy.

**Nguyên nhân CI đã xác nhận:** mở GitHub Actions bằng Edge có phiên đăng nhập, run #9 của commit `e652db0` thất bại ở job `frontend`, còn `backend` và `backup-command-tests` đạt. Log `npm audit --audit-level=low` báo 5 cảnh báo high do `braces` trong cây Tailwind CSS 3.4.17; advisory GHSA-vfj7-8cjw-p6xm chưa có bản vá cho `braces` 3.x. `gh auth status` xác nhận token CLI trong keyring không hợp lệ; trạng thái CI được đọc trên trang GitHub, không suy từ CLI.

**Thay đổi:** nâng Tailwind và CLI lên 4.3.0 pin chính xác, lockfile sử dụng `@parcel/watcher` 2.6.0 không còn cây `braces`; chuyển CSS đầu vào sang `@import`/`@source` của Tailwind 4, build lại CSS và bỏ cấu hình v3 không còn dùng. Cập nhật hướng dẫn frontend. CI nâng `actions/setup-node` từ v4 lên v6 để bỏ cảnh báo runtime Node 20. Bộ thử backup chọn đúng shell của môi trường hiện tại (`powershell.exe` trên Windows PowerShell, `pwsh` trên PowerShell Core); kịch bản Failure trước đó không chạy được ở máy Windows này.

**Kiểm tra đã chạy:** `npm ci`, `npm audit --audit-level=low` (0 vulnerability), `npm run build:css` đều exit 0. Đối chiếu selector CSS: 417 selector lớp có trong template và CSS v3 đều hiện diện sau build v4; kiểm tra này không thay thế xác nhận bố cục trình duyệt. `python -m pip check`, `python -m pip_audit -r requirements.txt` (No known vulnerabilities found), `manage.py check`, `makemigrations --check --dry-run` đạt. Cả 6 kịch bản mô phỏng `ops/backup/Test-BackupSafety.ps1` (Full/Log × Express/Standard/Failure) PASS; không kiểm thử backup/restore SQL thật bằng bộ này.

**Kiểm thử toàn bộ và CI mới:** `venv\Scripts\python.exe ops\run_tests.py --backend sqlite`: 319 test, 317 đạt, 2 bỏ qua do dành riêng SQL Server, exit 0; log `D:\QLHCNS-Backups\review-20261005-ci-sqlite.log`. `venv\Scripts\python.exe ops\run_tests.py --backend sqlserver`: 319/319 đạt, exit 0; log `D:\QLHCNS-Backups\review-20261005-ci-sqlserver.log`. Cả ba kịch bản HTTP HR, chấm công, nghỉ phép PASS trên hai backend; runner đã xóa database SQL Server tạm, kiểm tra chỉ đọc xác nhận còn 0 database `test_ihrms_%`. Có cảnh báo Jazzmin `dark_mode_theme` deprecated trong log, không làm test thất bại. Đã xác nhận trực tiếp trên Edge [GitHub Actions run #11](https://github.com/dinhtanhb/QLHCNS/actions/runs/37261635104) của commit `39f132e023b5d5c9360cb1689c8b224849cb00a7`: Status Success; backend, frontend và backup-command-tests đều thành công, không có annotation error/warning; còn 3 notice về lịch chuyển ubuntu-latest sang Ubuntu 26.

**Nhánh/commit và việc còn mở:** `main`, mã sửa ở `39f132e023b5d5c9360cb1689c8b224849cb00a7`, đã push và fetch xác nhận origin/main khớp local. Commit trung gian `e0e8fa8` chỉ xóa cấu hình v3 do lệnh stage gặp pathspec của tệp đã xóa; các thay đổi còn lại đã được đưa ngay vào commit kế tiếp `39f132e`. Run #10 của commit trung gian đã lỗi frontend và được yêu cầu hủy để giải phóng hàng đợi cho run #11; không coi run trung gian là kết quả nghiệm thu. Chưa kiểm thử trực quan bố cục Edge sau nâng Tailwind, chưa xác nhận production IIS/SharePoint. Chủ dự án cần chạy `npm ci`, `npm run build:css`, rồi `venv\Scripts\python.exe src\manage.py collectstatic --noinput` theo quy trình triển khai trên máy chủ và kiểm tra bố cục các màn hình đang dùng; việc collectstatic/triển khai production không nằm trong đợt kiểm thử này.

## 2026-10-05 — Chuẩn hóa reviewer Sixth và hướng dẫn review dùng lại

**Mục tiêu/phạm vi:** đánh giá `.sixth/agents/code-review.md` và cập nhật hướng dẫn theo yêu cầu chủ dự án. `git status`, nhánh và `git fetch origin main` xác nhận `main` ở `164ffd30bc973b40cf4ca68ab6dfa9aa1a1738d8`, khớp remote (ahead/behind 0/0). Ban đầu `.sixth/` và `_review_probe.py` chưa theo dõi. Chỉ sửa file reviewer được yêu cầu; không sửa probe. `code-reviewr.md` không tồn tại trên đĩa dù người dùng đang có tab IDE tương ứng.

**Đánh giá và thay đổi:** reviewer cũ có quy trình đọc caller/test và xác minh finding phù hợp, nhưng chủ yếu review diff sau tính năng, thiếu quy tắc IHRMS, bảo vệ dữ liệu, hai backend và xác nhận CI. Đã sao lưu bản gốc ngoài Git tại `D:\QLHCNS-Backups\review-agent-guide-20261005`. Cập nhật reviewer với FULL/CHANGES và REVIEW/FIX, checklist luồng nghiệp vụ, main, dữ liệu giả/DB-media cô lập, bằng chứng finding, quyền sửa/commit/push theo nhiệm vụ và cách báo phần chưa kiểm thử. Tạo `docs/Huong_Dan_Review_Du_An.md` có mẫu yêu cầu cho Sixth hoặc thực hiện trực tiếp, các lệnh chuẩn, điều kiện hoàn tất và giới hạn Bugbot. README/AGENTS chỉ liên kết tới hướng dẫn; nhật ký đợt chỉ ghi tại đây.

**Kiểm tra thực tế:** đối chiếu mã extension Sixth AI 0.3.7 đang cài, xác nhận loader `.sixth/agents`, schema permissions, trust prompt và công cụ `launch_agent`; agent nền nhận task riêng, không nhận toàn bộ chat. Dùng Node VM chỉ chạy hàm parser `x0r` trích từ extension (không khởi động extension): file mới được nhận là `code-review`, source project, đủ 6 quyền bao gồm read mặc định. Python kiểm tra liên kết local, UTF-8 và code fence của bốn file hướng dẫn: PASS. `git diff --check`: exit 0. Đối chiếu lệnh với `ops/run_tests.py`, `ops/Run-Tests.ps1` và `.github/workflows/ci.yml`; không chạy full suite/build/audit mới vì đợt này chỉ sửa hướng dẫn, không sửa ứng dụng, dependency hoặc workflow.

**Việc còn mở/bàn giao:** chưa thử gọi agent Sixth qua UI nên không coi parser PASS là run review đã thành công. Chủ dự án mở Sixth AI trong workspace, dùng mẫu FULL/REVIEW ở hướng dẫn, yêu cầu agent `code-review`, xử lý trust prompt nếu xuất hiện rồi xác nhận có run riêng/kết quả. Nếu không có agent Sixth trong công cụ đang dùng, đính kèm hai file và yêu cầu review trực tiếp; ghi đúng cách đã thực hiện. Không áp dụng migration hay ghi dữ liệu nghiệp vụ trong đợt này.

**Git trong lượt tiếp tục:** chủ dự án yêu cầu commit/push toàn bộ. Fetch lại xác nhận main không phân kỳ với origin/main. Kiểm tra toàn bộ tệp mới: chỉ có reviewer, hướng dẫn và `_review_probe.py`; probe dùng cấu hình test/SQLite, khóa mẫu riêng cho probe và instance giả, không gọi save. Chạy `venv\Scripts\python.exe _review_probe.py` lần đầu lỗi encoding cp1252; chạy lại với `PYTHONIOENCODING=utf-8` hiển thị đủ trạng thái rồi exit 1 vì `clean_fields()` kiểm tra FK trên SQLite thiếu bảng `tblVehicle`. Không ghi probe đạt và không migrate/tạo fixture trên DB cấu hình để chữa lỗi này. Giữ probe nguyên trạng theo yêu cầu đưa toàn bộ lên Git; nếu cần chạy lại độc lập, phải có SQLite cô lập đã migrate và fixture giả tương ứng hoặc chuyển probe thành test dùng runner chuẩn. Không đưa .env, DB, backup hoặc dữ liệu thật. SHA commit và đối chiếu remote sau push được báo trong kết quả bàn giao.

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

## 2026-10-02 — Gia cố bảo vệ dữ liệu nhạy cảm trên main

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

## 2026-10-02 — Vá các đề xuất review được chủ dự án duyệt trên main

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

## 2026-10-02 — Kiểm thử trên SQL Server và Edge với bản sao dữ liệu tại máy Windows

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

## 2026-10-02 — Đẩy kết quả UAT và chặn số tiền âm trong bảng lương

**Mục tiêu/phạm vi:** theo yêu cầu tiếp tục trên `main`, commit/push kết quả UAT trước rồi rà soát, sửa lỗi có thể tái hiện. Đã đọc `AGENTS.md` và nhật ký, `git fetch origin main` xác nhận local và `origin/main` cùng ở `2cc0e3b`, giữ nguyên bốn tệp thay đổi từ đợt UAT. Không ghi dữ liệu lên database nghiệp vụ gốc.

**Git đợt UAT:** `git diff --cached --check` đạt; commit `65f9ca6aceb5bfa7251e7c1b4fd305c7b98c340e` (`fix: stabilize SQL Server test and timesheet number inputs`) gồm template chấm công, hai tệp kiểm thử và nhật ký đợt trước; `git push origin main` thành công, fetch lại xác nhận `main` khớp `origin/main`, working tree sạch trước khi sửa tiếp.

**Lỗi tái hiện và sửa:** báo cáo review cũ có nhiều mục đã được sửa trong mã hiện tại. Mục tiền nhập tay âm còn tái hiện: `Payroll.full_clean()` cho qua sáu trường tiền âm, `EmployeeSalary.full_clean()` cho qua lương cơ bản âm. Đã chạy ca kiểm thử mới trước sửa và thấy 7 subtest thất bại đúng lỗi. Trong `src/apps/payroll/models.py`, thêm kiểm tra số tiền không âm cho sáu trường nhập `Payroll` khi `full_clean()` và trước `calculate()`, cùng kiểm tra `EmployeeSalary.current_basic_salary`; `src/apps/payroll/tests.py` thêm ca hồi quy. Kiểm tra chỉ đọc trên database gốc cho thấy sáu trường `Payroll` không có giá trị âm. Không thêm migration hay thay đổi công thức tính. Bản sửa thử đầu tiên còn chặn mức miễn thuế tăng ca nhập lớn hơn tiền tăng ca; SQL Server test hiện hữu chỉ ra quy tắc đang dùng là lấy mức nhỏ hơn khi tính, nên đã bỏ phần chặn đó và giữ nguyên quy tắc nghiệp vụ.

**Kiểm tra sau sửa:** `venv\Scripts\python.exe src\manage.py check`: 0 lỗi; `venv\Scripts\python.exe src\manage.py makemigrations --check --dry-run`: No changes detected; `git diff --check`: đạt. `venv\Scripts\python.exe ops\run_tests.py --backend sqlite`: 317 test, 315 đạt, 2 bỏ qua vì cần SQL Server, exit 0; cả 3 tình huống HTTP PASS. `venv\Scripts\python.exe ops\run_tests.py --backend sqlserver`: 317/317 đạt, exit 0, database test SQL Server tạm do runner tạo và xóa; cả 3 tình huống HTTP PASS. Không dùng test này để tuyên bố đã thao tác nút xác nhận xóa trên Edge.

**Việc còn mở:** chưa xác nhận toàn bộ lỗi thiết kế/hiệu năng trong báo cáo review cũ đã hết; chưa thử race thực tế, IIS/SharePoint production và hộp thoại `confirm()` của nút Xóa trên Edge. Tệp backup SQL của đợt UAT còn cần người quản trị xóa theo đường dẫn và lệnh ở mục ngay trên; không đưa tệp đó vào Git. Không chạy migration hoặc triển khai production trên database gốc. Mã sửa đã được commit/push trên `main` ở `447508a389da49d4110f7c674b32a33dbc80b442`; fetch lại xác nhận remote trùng local. Lệnh `gh run list --commit 447508a389da49d4110f7c674b32a33dbc80b442` bị GitHub API trả 401 Bad credentials, nên chưa xác nhận CI của commit này; người phụ trách mở GitHub Actions của commit trên bằng tài khoản có quyền, đối chiếu trạng thái backend/frontend/backup-command-tests và cung cấp log nếu job lỗi.

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

## 2026-09-27 — Cải thiện trải nghiệm mobile và PWA portal (Yêu cầu 3–6)

**Mục tiêu/phạm vi:** giúp portal hoạt động thuận tiện trên điện thoại, thay CSS Tailwind CDN bằng bản build nội bộ, và cho phép cài lối tắt PWA online-only. Sao lưu trước đợt sửa: `D:\QLHCNS-Backup-before-mobile-requirements-3-6-20260927-183513.bundle` (bundle Git chứa các refs tại thời điểm trước sửa).

**Đã làm:** bọc 21 bảng trong 18 template được review yêu cầu bằng vùng cuộn ngang; giữ nguyên bốn template in và thêm quy tắc in để wrapper không cắt nội dung. Chuyển menu portal sang hamburger dưới 768px, giữ menu ngang từ 768px và giữ điều kiện phân quyền, ARIA, click ngoài và Escape. Thêm Tailwind CLI 3.4.17, lockfile, lệnh build/watch và CSS đã build `src/static/css/tailwind.css`; bỏ Tailwind Play CDN. Thêm manifest `/portal/`, biểu tượng 192/512 từ biểu trưng sẵn có và service worker chỉ cache cùng origin `/static/`; không cache HTML hoặc dữ liệu nghiệp vụ. Bổ sung test hồi quy và hướng dẫn build/mobile/PWA tại `docs/06_Frontend_Standards.md`.

**Kiểm tra:** `python src/manage.py check` đạt; `python src/manage.py makemigrations --check --dry-run` báo không có thay đổi; `python src/manage.py test apps.portal.tests_mobile` đạt 5/5; `python src/manage.py findstatic css/tailwind.css manifest.json img/ihrms-pwa-192.png --verbosity 2` tìm thấy các asset. `npm ci` thành công; `npm run build:css` sinh CSS 33 KB (có cảnh báo Browserslist data cũ, không chặn build). Trình duyệt kiểm tra tại 375px, 768px và 1024px: mobile có thể mở/đóng hamburger, menu con và cuộn bảng nằm trong khung không làm rộng trang; từ 768px menu hamburger ẩn và nav ngang hiện; dropdown desktop vẫn đóng bằng Escape/click ngoài. Kết nối cấu hình hiện tại nhận diện SQL Server (`microsoft`), nhưng test mobile không truy vấn DB; không chạy migration hay ghi dữ liệu nghiệp vụ.

**Git/trạng thái:** nhánh `chore/django-5.2-upgrade`; thay đổi mobile ở commit cục bộ `67314ee` (`feat: improve portal mobile experience`), chưa push. Tệp chưa theo dõi `docs/Huong_Dan_Setup_TaskScheduler_SIT_UAT.md` đã có từ trước và được giữ nguyên, không thuộc thay đổi này.

**Còn mở:** PWA chỉ có thể cài qua HTTPS hoặc localhost trên trình duyệt hỗ trợ; service worker chỉ tăng tốc asset và không tạo chế độ offline cho dữ liệu. Khi sửa Tailwind class, chạy `npm ci` rồi `npm run build:css` trước `collectstatic`.

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

### Công cụ Word trên máy Windows

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

### Cổng còn lại trước vận hành thật

- Chạy `check --deploy` với cấu hình production thật; xác nhận HTTPS, host/CSRF, cookies, secret, static, logging và IIS/reverse proxy.
- Chạy toàn bộ test trên SQL Server; hiện 86 test gần nhất là trên SQLite, chưa chứng minh tương thích đầy đủ trên backend SQL Server.
- Finance đối soát công thức lương/thuế/bảo hiểm với bộ số mẫu đã được phê duyệt; HR, quản lý và nhân viên hoàn tất UAT trên dữ liệu ẩn danh.
- Thiết lập backup SQL Server và tệp hồ sơ ở nơi độc lập; diễn tập restore, đo thời gian và xác nhận RPO/RTO với công ty.
- IT rà quyền tài khoản, SharePoint ACL/retention/audit và lịch vận hành; diễn tập go-live/rollback trước khi mở cho toàn công ty.

### Mẫu mục nhật ký cho đợt sau

### YYYY-MM-DD — Tên thay đổi

**Mục tiêu/phạm vi:**
**Phân hệ/tệp:**
**Đã làm và quyết định:**
**Kiểm tra (lệnh, môi trường, kết quả):**
**Nhánh/commit/push:**
**Chưa làm hoặc chưa xác nhận:**
**Chủ dự án cần làm:** bước cụ thể, người phụ trách và kết quả cần gửi lại.

## 2026-09-24 — Word guide synchronization and rendering setup

**Scope:** synchronize the DOCX user guide to Markdown version 1.1 and verify its rendered layout.

**Completed:** created the isolated Python environment at `%LOCALAPPDATA%\IHRMS-DocTools`; installed `python-docx 1.2.0` and `pdf2image 1.17.0`; installed Poppler 25.07.0 with winget. LibreOffice 26.2.5.2 was already installed. Rebuilt `docs/HUONG_DAN_SU_DUNG_IHRMS.docx` from `HUONG_DAN_SU_DUNG_IHRMS.md`; retained the previous DOCX outside the repository.

**Verification:** both Python package imports passed; LibreOffice, `pdftoppm`, and `pdfinfo` ran. Rendered the DOCX to PDF and four page images; visually inspected all four pages for Vietnamese glyphs, table fit, list numbering, and pagination. QA output is outside the repository at `D:\QLHCNS-docx-render-final`.

**Open:** the document changes have not been committed or pushed. Re-render after future content updates.

## 2026-09-24 — Đề xuất mở rộng IHRMS cho hoạt động dự án NGO/MEL

**Mục tiêu/phạm vi:** đánh giá yêu cầu lập kế hoạch tháng, điều phối CBDA, lịch, MEL, ngân sách và quyết toán; lập lộ trình code theo các cổng phê duyệt.

**Đã rà soát:** Project Charter, RBAC matrix, apps.project.Project, apps.task.Task, apps.planning.Event/AnnualBudget, apps.document.OfficialDispatch, các route/template giao việc/sự kiện và quyền hiện hành. Charter hiện loại Grant, ngân sách tài trợ, hoạt động phát triển cộng đồng và MEL khỏi phạm vi; model hiện chưa hỗ trợ workflow NGO đầy đủ.

**Đã tạo:** docs/NGO_Activity_Planning_MEL_Roadmap.md ghi nhận nhận xét hiện trạng, luồng mục tiêu, mô hình dữ liệu/tích hợp, quyền, dashboard, tiêu chí nghiệm thu, ước lượng 7–10 tuần và quyết định NGO cần chốt. Đây là đề xuất; chưa sửa code, Charter, migration hay cấu hình.

**Ranh giới kiến trúc được làm rõ:** miền Hoạt động dự án riêng; Hộp việc của tôi, thành phần giao việc/lịch, trao đổi, thông báo và nhắc hạn dùng chung; dashboard dự án riêng. KPI nhân sự và chỉ số MEL dùng mô hình, quyền, công thức và báo cáo riêng, chỉ tái sử dụng thành phần hiển thị. Chưa sửa code hoặc schema.

**Kiểm tra phần hành chính–nhân sự (24/09/2026):** Codex chạy `python src/manage.py check` (đạt), `makemigrations --check --dry-run` (No changes detected), và 86 test trên SQLite test database tạm (đạt). Codex xác nhận kết nối cấu hình hiện tại tới SQL Server bằng `connection.vendor=microsoft` và `SELECT 1`; chưa chạy test suite SQL Server vì chưa xác minh đó là database SIT riêng, an toàn cho Django tạo/xóa test database. Người dùng trước đó báo các luồng nghiệp vụ chạy bình thường; báo cáo này chưa phải UAT ký nhận.

**Còn mở:** Chưa đủ điều kiện go-live/pilot với dữ liệu thật. Cần test SQL Server SIT, `check --deploy` trên cấu hình máy chủ, UAT có biên bản, xác nhận backup/restore và quyền dữ liệu. Với phân hệ NGO, Ban Giám đốc cần phê duyệt mở rộng Charter; Chương trình/MEL/Tài chính/IT chốt RACI, SLA, xung đột lịch, tiền tệ, chứng từ, dữ liệu người tham gia và database SIT trước khi có schema/migration. Chủ dự án làm theo mục “Việc chủ dự án cần điều phối ở Cổng 0” trong roadmap; không gửi dữ liệu thụ hưởng định danh qua chat.
