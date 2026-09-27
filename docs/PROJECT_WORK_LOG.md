# Nhật ký công việc IHRMS

Đây là **nơi ghi nhận tập trung duy nhất** các đợt thay đổi lớn, thao tác kiểm tra, quyết định và việc cần chủ dự án thực hiện. Cập nhật tiếp vào tệp này thay vì tạo log mới cho từng lần làm việc. Không ghi secrets, dữ liệu cá nhân hoặc nội dung `.env`.

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
