# Hướng dẫn setup/cấu hình: Task Scheduler, máy chủ SIT, UAT — IHRMS

Đối tượng đọc: **Quản trị IT phụ trách máy chủ Windows** (không phải Codex — đây là việc trên hạ tầng thật, không phải sửa code). Tài liệu này diễn giải chi tiết hơn 3 việc đã nêu trong `docs/Server_Trial_Readiness_2026-09-27.md` và `ops/scheduler/IT_Huong_Dan_Dang_Ky_Task_Scheduler.md` — hai tài liệu đó đã có sẵn trong repo và khá đầy đủ, tài liệu này gom lại theo đúng thứ tự làm thực tế và giải thích thêm phần IIS mà repo chưa viết cụ thể.

**Không đụng vào phần "mẫu báo cáo Kế toán"** — theo yêu cầu, tạm bỏ qua, chờ Kế toán xác nhận mẫu BHXH/PIT/chi phí phòng ban trước.

---

# Phần 1 — Windows Task Scheduler (nhắc việc tự động)

## 1.1. Việc này là gì, vì sao cần

IHRMS có 2 lệnh Django tạo thông báo nhắc hạn **bên trong ứng dụng** (không gửi email):

| Lệnh Django | Mục đích | Script PowerShell tương ứng |
|---|---|---|
| `send_activity_report_reminders` | Nhắc hạn báo cáo hoạt động dự án (NGO) | `ops/scheduler/Run-ActivityReportReminders.ps1` |
| `send_lifecycle_reminders` | Nhắc đầu việc onboarding/offboarding quá hạn | `ops/scheduler/Run-LifecycleReminders.ps1` |

Nếu không đăng ký Task Scheduler, 2 lệnh này **không tự chạy** — nghĩa là chuông thông báo trong app sẽ không bao giờ tự nhắc, dù logic nhắc hạn đã viết đúng. Đây thuần túy là việc "bật công tắc" trên máy chủ, không phải lỗi code.

## 1.2. Điều kiện tiên quyết

- Ứng dụng IHRMS đã được cài trên máy chủ (venv đã tạo, `requirements.txt` đã cài, `.env` đã cấu hình đúng — xem Phần 2 nếu chưa làm bước này).
- Bạn có quyền Administrator trên máy chủ đó.
- Thư mục gốc dự án trên máy chủ (ví dụ `D:\QLHCNS`) đã đúng, `venv\Scripts\python.exe` tồn tại trong đó.

## 1.3. Các bước thực hiện

### Bước 1 — (Chỉ cần nếu venv nằm khác đường dẫn mặc định) Khai báo biến môi trường `IHRMS_PYTHON`

Script tự tìm Python theo thứ tự: biến môi trường `IHRMS_PYTHON` → nếu không có thì dùng `<gốc dự án>\venv\Scripts\python.exe`. Nếu venv của bạn đúng ngay dưới gốc dự án thì **bỏ qua bước này**. Nếu khác, mở PowerShell Administrator:

```powershell
[Environment]::SetEnvironmentVariable("IHRMS_PYTHON", "D:\QLHCNS\venv\Scripts\python.exe", "Machine")
```

Dùng `"Machine"` (biến hệ thống) chứ không phải `"User"`, vì Task Scheduler thường chạy dưới tài khoản `SYSTEM`, tài khoản này không đọc được biến môi trường cấp User của bạn.

### Bước 2 — Chạy thử tay trước (bắt buộc, đừng bỏ qua)

Mở PowerShell **Administrator** tại gốc dự án:

```powershell
cd D:\QLHCNS
powershell -ExecutionPolicy Bypass -File .\ops\scheduler\Run-ActivityReportReminders.ps1
powershell -ExecutionPolicy Bypass -File .\ops\scheduler\Run-LifecycleReminders.ps1
```

Kiểm tra 2 điều:
1. Không có dòng lỗi màu đỏ trên console.
2. Có file log mới xuất hiện: `Logs\activity-reminders-YYYYMMDD.log` và `Logs\lifecycle-reminders-YYYYMMDD.log`, bên trong có dòng kiểu "Đã tạo N thông báo..." (N = 0 cũng là bình thường nếu hôm đó không có gì đến hạn).

Chỉ sang Bước 3 khi cả 2 lệnh chạy tay **không lỗi**.

### Bước 3 — Đăng ký lịch tự động

Cách nhanh nhất là dùng lệnh `schtasks` (PowerShell Administrator), sửa `D:\QLHCNS` thành đường dẫn thật trên máy chủ:

```powershell
schtasks /Create /TN "IHRMS - Activity Report Reminders" `
  /TR "powershell.exe -ExecutionPolicy Bypass -File `"D:\QLHCNS\ops\scheduler\Run-ActivityReportReminders.ps1`"" `
  /SC DAILY /ST 07:30 /RU "SYSTEM" /RL HIGHEST /F

schtasks /Create /TN "IHRMS - Lifecycle Checklist Reminders" `
  /TR "powershell.exe -ExecutionPolicy Bypass -File `"D:\QLHCNS\ops\scheduler\Run-LifecycleReminders.ps1`"" `
  /SC DAILY /ST 07:35 /RU "SYSTEM" /RL HIGHEST /F
```

Nếu muốn thao tác bằng giao diện thay vì gõ lệnh: mở **Task Scheduler** (gõ `taskschd.msc`) → **Create Task...** (không dùng "Create Basic Task" vì cần tùy chỉnh) → điền tương tự:
- Tab **General**: đặt tên, tick **"Run whether user is logged on or not"** và **"Run with highest privileges"**.
- Tab **Triggers** → New → **Daily**, giờ bắt đầu 07:30 (hoặc 07:35 cho task thứ 2).
- Tab **Actions** → New → Program: `powershell.exe`, Add arguments: `-ExecutionPolicy Bypass -File "D:\QLHCNS\ops\scheduler\Run-ActivityReportReminders.ps1"`.

Giải thích các tham số dùng lệnh `schtasks`:
- `/SC DAILY /ST 07:30` — chạy hằng ngày 7:30 sáng, trước giờ làm để nhân viên vào là thấy thông báo mới. Lệch nhau 5 phút giữa 2 task để tránh 2 tiến trình cùng ghi log 1 lúc.
- `/RU "SYSTEM"` — chạy dưới tài khoản hệ thống, không phụ thuộc ai đang đăng nhập máy. Nếu chính sách bảo mật công ty yêu cầu dùng tài khoản dịch vụ riêng, đổi `SYSTEM` thành tên tài khoản đó và thêm `/RP <mật khẩu>` (Windows sẽ hỏi lại mật khẩu nếu dùng GUI).
- `/RL HIGHEST` — chạy quyền cao nhất tài khoản đó có (không phải Administrator tuyệt đối).
- `/F` — ghi đè nếu task cùng tên đã tồn tại, an toàn khi chạy lại để cập nhật.

### Bước 4 — Lưu ý quan trọng: 2 lệnh KHÔNG đối xứng nhau

- `send_activity_report_reminders` tự bỏ qua thứ Bảy/Chủ nhật.
- `send_lifecycle_reminders` **không** kiểm tra ngày trong tuần — sẽ chạy và gửi nhắc cả cuối tuần nếu Task Scheduler kích hoạt đúng ngày đó.

Đây **có thể là chủ ý** (ví dụ hạn thu hồi tài sản/khóa tài khoản khi nghỉ việc không nên bị lùi chỉ vì rơi vào cuối tuần), không phải lỗi hiển nhiên cần sửa ngay. **Việc của bạn ở bước này**: hỏi lại HR/Ban giám đốc xem có muốn 2 lệnh nhất quán không, rồi mới quyết định — nếu muốn sửa thì đó là việc chuyển lại cho Codex (thêm điều kiện bỏ qua cuối tuần vào `send_lifecycle_reminders`), không phải việc tự chỉnh giờ chạy Task Scheduler để né vấn đề.

### Bước 5 — Kiểm tra sau khi đăng ký (làm vào ngày hôm sau)

1. Task Scheduler → chọn từng task → tab **History** (nếu không thấy, bấm "Enable All Tasks History" ở panel bên phải) → tìm sự kiện "Task completed" mã `0x0`. Nếu thấy "Task failed" nghĩa là có lỗi, xem Bước 6.
2. Mở `Logs\activity-reminders-*.log` và `Logs\lifecycle-reminders-*.log`, xác nhận có dòng log mới của đúng ngày hôm đó.
3. Trong IHRMS, đăng nhập bằng 1 tài khoản test có sẵn 1 task/timesheet cố tình để trễ hạn, xác nhận chuông thông báo có thông báo mới đúng nội dung.

### Bước 6 — Xử lý khi task báo lỗi

1. Mở đúng file log của ngày báo lỗi trong `Logs\` — script đã ghi toàn bộ output/traceback vào đó.
2. Lỗi thường gặp nhất: sai đường dẫn `IHRMS_PYTHON`, hoặc venv chưa cài đủ `requirements.txt` (script gọi thẳng `python.exe` trong venv, không cần activate, nhưng venv đó phải được tạo và cài đặt đầy đủ trước).
3. Nếu lỗi là `django.db.utils.OperationalError` (không kết nối được SQL Server) — không phải lỗi của 2 script này, kiểm tra dịch vụ SQL Server trên máy chủ có đang chạy không, và tài khoản chạy Task Scheduler có quyền kết nối DB không.

## 1.4. Lưu ý: đây chưa phải gửi email thật

2 lệnh trên **chỉ tạo thông báo trong ứng dụng IHRMS**, chưa gửi email/Outlook tự động qua SMTP/Graph — việc đó nằm ngoài phạm vi 2 script này (xem "Hạng mục 1" trong `docs/HRMS_Next_Features_TechSpec_2026-09-26.md` nếu cần làm sau).

## 1.5. Đừng quên: Task Scheduler backup SQL Server là việc riêng

`ops/backup/README.md` đã có hướng dẫn đăng ký 2 Task Scheduler khác cho **Full Backup (22:00 hằng ngày)** và **Transaction Log Backup (mỗi giờ)** — không gộp chung với 2 task nhắc việc ở trên. Tóm tắt nhanh nếu chưa làm:

```powershell
schtasks /Create /TN "QLHCNS - Full Backup" `
  /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"D:\QLHCNS\ops\backup\Backup-FullDatabase.ps1`"" `
  /SC DAILY /ST 22:00 /RL HIGHEST /F

schtasks /Create /TN "QLHCNS - Transaction Log Backup" `
  /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"D:\QLHCNS\ops\backup\Backup-TransactionLog.ps1`"" `
  /SC DAILY /ST 00:05 /RI 60 /DU 9999:59 /RL HIGHEST /F
```

(`/RI 60` = lặp lại mỗi 60 phút, `/DU 9999:59` ≈ lặp vô thời hạn — nếu dùng GUI thì tick "Repeat task every 1 hour, for a duration of Indefinitely".) Trước khi bật, phải chạy `Setup-RecoveryModel.sql` **một lần** trong SSMS để chuyển DB sang chế độ FULL recovery — nếu bỏ qua bước này, backup transaction log sẽ lỗi. Chi tiết đầy đủ + diễn tập restore hàng quý (bắt buộc): đọc `ops/backup/README.md`.

---

# Phần 2 — Dựng máy chủ SIT (Windows Server + SQL Server + HTTPS)

## 2.1. Việc này là gì, vì sao cần

SIT (System Integration Test) là môi trường **giống production nhưng dùng dữ liệu giả**, để kiểm tra ứng dụng chạy đúng trên hạ tầng thật (không phải máy dev) trước khi đưa vào dùng chính thức. Hiện tại ứng dụng mới chạy tốt trên máy dev (SQL Server test tạm do Django tự tạo/xóa) — **chưa có bằng chứng nào chạy được trên máy chủ Windows Server thật với TLS thật**.

## 2.2. Trước khi bắt đầu — IT cần chuẩn bị sẵn 6 thứ

| # | Cần gì | Ghi chú |
|---|---|---|
| 1 | Windows Server SIT riêng | Python 3.12, ODBC Driver 17 for SQL Server đã cài; quyền chạy ứng dụng và ghi log |
| 2 | Database SQL Server SIT riêng | Tài khoản dịch vụ quyền tối thiểu (không dùng tài khoản `sa`), kết nối mạng được từ máy ứng dụng. **Không dùng DB production** |
| 3 | Hostname nội bộ + chứng chỉ TLS | Ví dụ `ihrms-sit.congty.local`; reverse proxy (IIS/ARR) do IT quản lý đứng trước, Waitress (WSGI server của Django) chỉ lắng nghe loopback `127.0.0.1` |
| 4 | Thư viện/folder SharePoint cho SIT | Có ACL phù hợp, Graph credentials (Tenant ID/Client ID/Client Secret) đã được duyệt cho môi trường test |
| 5 | Tài khoản thử theo vai trò | Dữ liệu giả/ẩn danh — xem danh sách tài khoản UAT ở Phần 3 |
| 6 | Kho backup độc lập + người phụ trách restore | Cấp quyền ghi `Logs/` và `src/staticfiles/` cho service account chạy ứng dụng |

## 2.3. Các bước dựng SIT

### Bước 1 — Lấy code và cài dependency

Clone nhánh đã được duyệt vào thư mục riêng trên máy chủ, ví dụ `D:\IHRMS-SIT`. **Không chép** `.env`, `venv/`, `Backups/`, SQLite DB hay dữ liệu người dùng từ máy dev sang — tạo mới sạch trên máy chủ.

```powershell
py -3.12 -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m pip check
```

### Bước 2 — Tạo và điền `.env`

```powershell
Copy-Item .env.example .env
.\venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Sinh `SECRET_KEY` mới ngay trên SIT** (không tái dùng key của máy dev), lưu vào kho secrets nội bộ, rồi điền vào `.env`. Nội dung `.env` cần sửa (thay giá trị mẫu bằng thông tin SIT thật):

```
DEBUG=False
ALLOWED_HOSTS=ihrms-sit.ten-mien-noi-bo
CSRF_TRUSTED_ORIGINS=https://ihrms-sit.ten-mien-noi-bo
DB_ENGINE=mssql
DB_NAME=<database SIT riêng>
DB_HOST=<SQL Server SIT>
DB_TRUSTED_CONNECTION=yes
ENABLE_HTTPS_ENFORCEMENT=True
SECURE_HSTS_SECONDS=0
M365_STORAGE_ENABLED=True
```

Vài điểm cần hiểu đúng, không suy diễn:
- Nếu dùng **SQL Authentication** (không phải Windows Integrated), đặt `DB_TRUSTED_CONNECTION=no` và điền thêm `DB_USER`/`DB_PASSWORD` từ kho secrets.
- Nếu dùng **Windows Integrated Authentication** (`DB_TRUSTED_CONNECTION=yes`), ứng dụng **phải chạy bằng chính service account đã được cấp quyền SQL** — tài khoản cá nhân bạn đang đăng nhập chạy được không có nghĩa service account (ví dụ chạy Waitress dưới NETWORK SERVICE hay 1 service account riêng) cũng chạy được, phải cấp quyền SQL riêng cho đúng tài khoản sẽ chạy ứng dụng.
- `SECURE_HSTS_SECONDS=0` — cố ý để 0 ở SIT, chỉ bật khi IT xác nhận **mọi** domain/subdomain liên quan đều dùng HTTPS (HSTS ghim chính sách HTTPS vào trình duyệt người dùng trong thời gian dài, bật sai sẽ khó gỡ).
- Điền Graph tenant/client/site/folder cho SharePoint **đã được duyệt riêng cho SIT** — không trỏ vào SharePoint production khi test.

### Bước 3 — Kiểm tra cấu hình trước khi migrate

```powershell
.\venv\Scripts\python.exe src\manage.py check
.\venv\Scripts\python.exe src\manage.py check --deploy
.\venv\Scripts\python.exe src\manage.py showmigrations
.\venv\Scripts\python.exe src\manage.py makemigrations --check --dry-run
.\venv\Scripts\python.exe src\manage.py migrate --plan
```

- `check --deploy` mà báo lỗi về HTTPS redirect, secure cookies, `ALLOWED_HOSTS`, hoặc `SECRET_KEY` → **dừng lại, sửa `.env` trước**, đừng migrate khi còn cảnh báo này.
- Cảnh báo về HSTS có thể chấp nhận để 0 riêng cho SIT nội bộ — nhưng **tuyệt đối không coi đây là đạt chuẩn production**.
- DBA phải xác nhận đây đúng là DB SIT (không phải production) và đã backup trước, rồi mới chạy:

```powershell
.\venv\Scripts\python.exe src\manage.py migrate
```

### Bước 4 — Thu thập static files

```powershell
.\venv\Scripts\python.exe src\manage.py collectstatic --noinput
```

Sẽ copy khoảng 219 file vào `src\staticfiles\`. Lưu ý: có 2 file JavaScript trùng tên giữa Jazzmin và Django admin gốc — `findstatic` sẽ ưu tiên bản Jazzmin, không phải lỗi cần sửa, nhưng nên **mở thử trang `/admin/` trên trình duyệt SIT sau khi map static** để chắc chắn không có JS bị vỡ do trùng.

### Bước 5 — Chạy WSGI thử bằng Waitress

Waitress là WSGI server cho Windows (thay `runserver` — `runserver` chỉ dùng để phát triển, không dùng làm web server thật). Mở PowerShell riêng:

```powershell
Set-Location .\src
..\venv\Scripts\waitress-serve.exe --listen=127.0.0.1:8001 config.wsgi:application
```

Ở cửa sổ PowerShell khác, kiểm tra Waitress đã lên:

```powershell
Invoke-WebRequest http://127.0.0.1:8001/portal/ -MaximumRedirection 5
```

Cần thấy HTTP 200. **Waitress chỉ lắng nghe `127.0.0.1` (loopback) — không mở trực tiếp ra Internet/LAN rộng.**

### Bước 6 — Cấu hình IIS làm reverse proxy trước Waitress (phần repo chưa viết cụ thể)

Đây là phần máy chủ Windows thường dùng nhất cho việc này. Cần 2 module IIS chưa cài sẵn mặc định:

1. **URL Rewrite** — tải và cài từ trang chính thức Microsoft (`iis.net/downloads/microsoft/url-rewrite`).
2. **Application Request Routing (ARR)** — cùng trang trên, mục ARR.

Sau khi cài, mở **IIS Manager**:

1. Tạo 1 **Site** mới (hoặc dùng site có sẵn) trỏ `Binding` vào HTTPS, cổng 443, chọn chứng chỉ TLS đã có cho `ihrms-sit.ten-mien-noi-bo`. Binding path (Physical path) trỏ vào 1 thư mục rỗng bất kỳ (không cần chứa code Django — IIS ở đây chỉ đóng vai trò cổng vào, không tự chạy Python).
2. Vào site đó → **URL Rewrite** → **Add Rule(s)** → **Reverse Proxy** (nếu không thấy tùy chọn này, kiểm tra lại đã bật "proxy" trong **ARR → Server Proxy Settings** ở cấp Server (không phải cấp Site) — tick "Enable proxy").
3. Nhập địa chỉ đích: `127.0.0.1:8001` (đúng cổng Waitress đang lắng nghe ở Bước 5).
4. Sau khi rule được tạo, mở **web.config** của site (IIS tự sinh) và thêm header `X-Forwarded-Proto` để Django biết request gốc là HTTPS — đây là bước bắt buộc, thiếu bước này Django sẽ hiểu nhầm là HTTP và redirect lặp vô hạn (đúng như cảnh báo trong `settings.py`):

```xml
<system.webServer>
  <rewrite>
    <rules>
      <rule name="ReverseProxyToWaitress" stopProcessing="true">
        <match url="(.*)" />
        <action type="Rewrite" url="http://127.0.0.1:8001/{R:1}" />
        <serverVariables>
          <set name="HTTP_X_FORWARDED_PROTO" value="https" />
        </serverVariables>
      </rule>
    </rules>
    <allowedServerVariables>
      <add name="HTTP_X_FORWARDED_PROTO" />
    </allowedServerVariables>
  </rewrite>
</system.webServer>
```

5. Cấu hình IIS phục vụ **`/static/`** trực tiếp từ `src\staticfiles\` thay vì đi qua Waitress (nhanh hơn) — thêm 1 rule loại trừ trong URL Rewrite: nếu `{URL}` bắt đầu bằng `static/` thì **không rewrite** (để IIS tự phục vụ file tĩnh từ physical path đã trỏ đúng thư mục `staticfiles`), chỉ rewrite phần còn lại sang Waitress.
6. **Chặn truy cập thẳng vào cổng 8001** từ bên ngoài máy chủ (firewall Windows chỉ cho phép `127.0.0.1` gọi cổng này) — nếu không chặn, ai cũng gọi thẳng Waitress qua HTTP, bỏ qua toàn bộ TLS/IIS phía trước, vô hiệu hóa mọi cấu hình HTTPS vừa làm.

Sau khi xong, mở `https://ihrms-sit.ten-mien-noi-bo/portal/` từ trình duyệt máy khác trong mạng nội bộ, kiểm tra: đăng nhập được, CSS/hình ảnh tải đúng (xác nhận static file mapping đúng), cookie phiên đăng nhập hoạt động bình thường (không bị redirect lặp).

> Nếu công ty đã có sẵn giải pháp reverse proxy khác (Nginx trên Windows, hoặc F5/HAProxy do team hạ tầng quản lý), thay IIS+ARR ở bước này bằng công cụ đó — nguyên tắc giống nhau: chỉ chấp header `X-Forwarded-Proto` khi chắc chắn client không thể đi thẳng vào Waitress, và luôn kết thúc TLS ở lớp proxy.

### Bước 7 — Chạy test hồi quy trên chính SQL Server SIT

Chỉ chạy trên SIT — được phép tự tạo/xóa database test, **không chạy nhắm vào DB production hay DB dùng chung**:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\Run-Tests.ps1
```

Script tự chạy Django từ `src`, phát hiện toàn bộ test modules gồm `apps.portal.tests_mobile` (5 test mobile/PWA), in số test và kết thúc với mã lỗi nếu không phát hiện test hoặc có test lỗi. Không chạy `python src\manage.py test` từ thư mục gốc — cách đó có thể báo 0 test. Django sẽ tạo rồi xóa test database; chỉ dùng cấu hình SQL Server SIT riêng.

Lưu số test đạt/không đạt, backend dùng, log của lần chạy trên chính máy chủ này vào `docs/PROJECT_WORK_LOG.md` — **không dựa vào kết quả từng chạy trên máy dev**, môi trường khác nhau phải tự kiểm chứng lại.

### Bước 8 — Smoke test bằng dữ liệu nhân tạo

Việc này trùng với Phần 3 (UAT) bên dưới — dùng luôn kịch bản UAT để vừa smoke test vừa làm luôn UAT chính thức, đỡ làm 2 lần.

## 2.4. Backup, phục hồi và quay lui khi dựng SIT

- Trước khi migrate, DBA sao lưu SQL Server SIT ra vị trí độc lập trước, xác nhận xong mới migrate.
- Nếu dùng lưu file cục bộ (chưa bật `M365_STORAGE_ENABLED`), backup `src/media/` cùng lúc với DB.
- Sao lưu `.env` riêng theo quy trình mã hóa của IT — **không đưa vào Git, không gửi qua chat/email, không để trong thư mục backup công khai**.
- Trước khi coi SIT là "đạt", phải thử restore 1 lần sang DB SIT khác và kiểm tra đăng nhập/dữ liệu mẫu đúng — chưa restore thử thì chưa được coi là go-live sẵn sàng (xem thêm checklist diễn tập restore chi tiết ở `ops/backup/README.md`, mục 3).
- Khi cần quay lui: dừng ứng dụng + IIS site, giữ nguyên log, khôi phục DB và file từ bản backup đã từng thử restore thành công. Không tự sửa tay bảng production hay xóa migration để "sửa nhanh".

---

# Phần 3 — Chạy UAT (User Acceptance Test)

## 3.1. UAT là gì trong ngữ cảnh này

UAT là bước **người dùng nghiệp vụ thật (HR, Kế toán, Giám đốc...) tự tay thao tác trên môi trường SIT** để xác nhận phần mềm đúng như họ cần, trước khi ký giấy đồng ý đưa vào dùng chính thức. Đây không phải việc IT tự kiểm tra kỹ thuật (đó là Phần 2), mà là việc có chữ ký nghiệm thu.

**Quan trọng cần biết trước:** file `docs/UAT_Kich_Ban_Nghiem_Thu_4_Hang_Muc.md` đã có sẵn trong repo, nhưng **chỉ có 12 kịch bản cho 4 hạng mục mới thêm gần đây** (Thông báo/Outbox email, Sơ đồ tổ chức, Tự cập nhật hồ sơ, Checklist Onboarding/Offboarding) — **không bao gồm** các phân hệ lõi đã có từ trước (nghỉ phép, chấm công, lương, tài sản, công văn...). Nếu đây là lần đầu đưa IHRMS vào dùng chính thức (không phải chỉ nghiệm thu riêng 4 tính năng mới), cần bổ sung thêm kịch bản cho các phân hệ lõi — xem gợi ý ở Mục 3.4.

## 3.2. Chuẩn bị trước khi test (người thực hiện: IT)

Tạo các tài khoản test trên môi trường SIT, đặt tiền tố `uat_` để dễ dọn sau khi xong:

| Username gợi ý | Vai trò (Role) | Vai trò trong kịch bản |
|---|---|---|
| `uat_nhanvien` | EMPLOYEE | Nhân viên thường |
| `uat_truongphong` | DEPT_MANAGER | Quản lý trực tiếp của `uat_nhanvien` (cùng phòng ban) |
| `uat_truongphong_b` | DEPT_MANAGER | Quản lý **phòng ban khác** (test không được duyệt chéo) |
| `uat_hr` | HR_OFFICER | Nhân sự tác nghiệp |
| `uat_hrm` | HR_MANAGER | Nhân sự quản lý |
| `uat_ketoan` | FINANCE_OFFICER | Kế toán |
| `uat_giamdoc` | DIRECTOR | Giám đốc |

Đảm bảo `uat_nhanvien` và `uat_truongphong` **cùng 1 phòng ban**, và `uat_truongphong` được đặt làm `manager` của phòng ban đó (vào Django Admin → Organization → Department → chọn đúng phòng → điền trường Manager). Thiếu bước này, nhiều kịch bản về duyệt/phân quyền sẽ không test đúng được.

Toàn bộ test **chỉ dùng dữ liệu giả**, môi trường SIT/UAT với SQL Server thật (không phải SQLite) — không dùng dữ liệu nhân viên/lương thật.

## 3.3. Chạy đúng theo kịch bản có sẵn

Mở `docs/UAT_Kich_Ban_Nghiem_Thu_4_Hang_Muc.md`, có 3 nhóm (A, B, C) với tổng 12 kịch bản, mỗi kịch bản là 1 bảng các bước có sẵn checkbox "Đạt/Không đạt". Cách chạy hiệu quả:

1. **Phân công người test đúng vai trò** — ví dụ kịch bản A2 ("Không tự duyệt đơn của chính mình") cần chính người đóng vai `uat_truongphong` thao tác, không phải IT tự đóng cả 2 vai để tiết kiệm thời gian (một số kịch bản như B3 cố tình mô phỏng 2 người thao tác gần như đồng thời — mục đích là kiểm tra hệ thống, phải làm đúng vai).
2. Với mỗi bước, **tick Đạt/Không đạt ngay khi làm xong**, đừng dồn lại nhớ sau.
3. Kịch bản B3 (chặn race condition khi 2 người cùng sửa 1 hồ sơ) cần người rành thao tác Django Admin hỗ trợ — đọc kỹ mô tả bước trong bảng trước khi làm, đây là kịch bản kỹ thuật hơn các kịch bản khác.
4. Kịch bản nhóm C (Checklist Onboarding/Offboarding) **yêu cầu đã có sẵn ít nhất 1 mẫu Onboarding và 1 mẫu Offboarding** cấu hình trong Django Admin trước — xem `docs/HR_Huong_Dan_Checklist_Onboarding_Offboarding.md` nếu HR chưa tạo mẫu.

## 3.4. Nếu đây là UAT trước khi đưa toàn bộ hệ thống vào dùng (không chỉ 4 tính năng mới)

Kịch bản có sẵn không đủ — nên bổ sung tối thiểu các luồng lõi sau trước khi ký nghiệm thu toàn hệ thống (có thể viết theo đúng format bảng như file mẫu, hoặc yêu cầu Codex soạn thêm bảng kịch bản theo mẫu có sẵn — đây là việc hợp lý để giao lại cho Codex vì chỉ là viết thêm tài liệu theo khuôn có sẵn, không phải quyết định nghiệp vụ):

- **Nghỉ phép**: tạo đơn → duyệt → số dư phép trừ đúng; thử vượt quá số ngày còn lại bị chặn.
- **Chấm công/Bảng công**: nhập timesheet → duyệt → tính đúng giờ chuẩn/giờ thực tế; bản in đúng định dạng A4.
- **Lương**: tạo kỳ lương với dữ liệu giả → tính lương → khóa kỳ → xác nhận FINANCE_OFFICER không sửa/xóa được dòng lương kỳ đã khóa (đúng phần đã sửa C2 trong đợt review vừa qua — nên đưa vào UAT để nghiệm thu chính lỗi đã sửa, không chỉ tin vào code review).
- **Tài sản**: cấp phát → thu hồi → đề nghị thanh lý → chỉ Giám đốc/superuser duyệt được thanh lý (đúng phần đã sửa C3).
- **Công văn/Tài liệu**: tạo công văn đi/đến → duyệt → không xem được công văn phòng ban khác qua sửa URL (đúng phần chống IDOR đã có).
- **Hoạt động dự án**: tạo hoạt động → Task báo cáo tự sinh đúng hạn → tải báo cáo lên SharePoint SIT (thư mục thử nghiệm) → hoàn thành Task.

Sau khi test xong, dùng đúng mẫu "Biên bản nghiệm thu" ở cuối file `docs/UAT_Kich_Ban_Nghiem_Thu_4_Hang_Muc.md` (điền số kịch bản đã chạy thực tế, không phải chỉ 12 kịch bản gốc), ghi rõ lỗi phát sinh (nếu có) kèm mức độ, và xin đủ 4 chữ ký: HR_MANAGER, FINANCE_OFFICER (nếu có kịch bản liên quan lương), DIRECTOR/người phê duyệt, và IT (xác nhận hạ tầng).

## 3.5. Sau UAT

- Nếu có lỗi phát sinh trong lúc test → ghi lại đầy đủ (bước tái hiện, kết quả mong đợi vs thực tế) → chuyển cho Codex sửa, **không tự sửa tay trên SIT rồi quên cập nhật lại code**.
- Nếu "Đạt có điều kiện" → liệt kê rõ điều kiện cần khắc phục trước go-live, không chỉ ghi chung chung "còn vài lỗi nhỏ".
- Dù UAT đạt, tài liệu `Server_Trial_Readiness_2026-09-27.md` vẫn nhắc: đây **chưa phải phê duyệt go-live production** — go-live cần thêm quyết định chính thức của người có thẩm quyền, ngoài phạm vi kỹ thuật.

---

# Tóm tắt thứ tự làm

1. **Phần 2** (dựng SIT) làm trước — không có SIT thì không có gì để chạy Task Scheduler hay UAT lên.
2. **Phần 1** (Task Scheduler) làm ngay sau khi SIT chạy ổn, không cần chờ UAT xong — đây là cấu hình hạ tầng độc lập.
3. **Phần 3** (UAT) làm sau cùng, trên chính máy chủ SIT đã dựng — nếu muốn, có thể gộp Bước 8 ở Phần 2 (smoke test) làm luôn thành buổi UAT chính thức để đỡ mất công lặp lại.
