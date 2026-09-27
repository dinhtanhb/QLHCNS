# Hướng dẫn đưa IHRMS lên máy chủ chạy thử (SIT)

Cập nhật: 27/09/2026
Phạm vi: dựng môi trường SIT nội bộ trên Windows Server, SQL Server riêng và reverse proxy HTTPS. Đây chưa phải hướng dẫn production/go-live.

## Kết luận hiện tại

Mã nguồn đạt 177 test trên SQL Server test database tạm; manage.py check, makemigrations --check --dry-run và pip check đạt. Đã bổ sung STATIC_ROOT để đóng gói CSS/JS. Chưa có kết quả trên máy chủ đích, hostname/chứng chỉ, tài khoản SQL SIT, restore drill hay UAT. Có thể bắt đầu dựng SIT sau khi IT chuẩn bị các thông tin dưới đây. Không dùng DB production hoặc dữ liệu nhân sự/lương thật.

## Kiểm tra đã thực hiện ở máy phát triển

- Django 5.2.17, Python 3.12.14; backend hiện tại là SQL Server.
- 177 test đạt trên test database do Django tạo và xóa.
- manage.py check sạch; makemigrations --check --dry-run không có migration thiếu; pip check không có dependency hỏng.
- check --deploy trên cấu hình máy hiện tại có 5 cảnh báo: HTTPS redirect, HSTS, cookie secure và độ mạnh SECRET_KEY. Sinh key riêng và chạy lại trên cấu hình SIT.
- Requests cảnh báo do chardet 7.6.0 không được Requests 2.32.3 chấp nhận; đã ghim chardet 5.2.0.
- Trước chỉnh sửa đã tạo bản sao đầy đủ tại D:\QLHCNS-FullBackup-before-server-trial-20260927: 11.057 tệp, 120.039.816 byte; Robocopy báo 0 lỗi, 0 sai khác.

## Việc cần IT chuẩn bị

1. Windows Server SIT riêng, Python 3.12, ODBC Driver 17, quyền chạy ứng dụng và ghi log.
2. Database SQL Server SIT riêng, tài khoản dịch vụ quyền tối thiểu và kết nối mạng từ máy ứng dụng. Không dùng DB production.
3. Hostname nội bộ và chứng chỉ TLS; reverse proxy/IIS/ARR do IT quản lý. Waitress chỉ lắng nghe loopback.
4. Thư viện/folder SharePoint cho SIT có ACL phù hợp và Graph credentials được duyệt. Chỉ dùng tệp giả khi thử.
5. Tài khoản thử theo vai trò và dữ liệu giả/ẩn danh.
6. Kho backup độc lập, người phụ trách restore. Cấp quyền ghi Logs/ và src/staticfiles/ cho service account.

## 1. Lấy code và cài dependency

Clone nhánh đã được chủ dự án duyệt vào thư mục riêng, ví dụ D:/IHRMS-SIT. Không chép .env, venv/, Backups/, SQLite DB hay dữ liệu người dùng từ máy phát triển.

    py -3.12 -m venv venv
    .\venv\Scripts\python.exe -m pip install --upgrade pip
    .\venv\Scripts\python.exe -m pip install -r requirements.txt
    .\venv\Scripts\python.exe -m pip check

Tạo .env ở thư mục gốc, cùng cấp requirements.txt:

    Copy-Item .env.example .env
    .\venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

Sinh secret mới ngay trên SIT, đưa vào kho secrets rồi cấu hình .env. Không ghi giá trị bí mật vào log/email. Ví dụ bên dưới là tên biến cần thay bằng thông tin SIT:

    DEBUG=False
    ALLOWED_HOSTS=ihrms-sit.ten-mien-noi-bo
    CSRF_TRUSTED_ORIGINS=https://ihrms-sit.ten-mien-noi-bo
    DB_ENGINE=mssql
    DB_NAME=<database SIT rieng>
    DB_HOST=<SQL Server SIT>
    DB_TRUSTED_CONNECTION=yes
    ENABLE_HTTPS_ENFORCEMENT=True
    SECURE_HSTS_SECONDS=0
    M365_STORAGE_ENABLED=True

Nếu dùng SQL authentication, IT đặt DB_TRUSTED_CONNECTION=no và điền DB_USER/DB_PASSWORD bằng kho secrets. Nếu dùng Windows Integrated Authentication, ứng dụng phải chạy bằng service account đã cấp quyền SQL. Không suy diễn rằng tài khoản cá nhân chạy được thì service account cũng chạy được. Điền Graph tenant/client/site/folder được duyệt; không dùng SharePoint production cho file test nếu chưa có ACL và thư mục thử nghiệm riêng.

## 2. Kiểm tra config và database trước migration

Chạy ở thư mục gốc repo:

    .\venv\Scripts\python.exe src\manage.py check
    .\venv\Scripts\python.exe src\manage.py check --deploy
    .\venv\Scripts\python.exe src\manage.py showmigrations
    .\venv\Scripts\python.exe src\manage.py makemigrations --check --dry-run
    .\venv\Scripts\python.exe src\manage.py migrate --plan

DBA xác nhận đây là DB SIT và đã backup trước migrate. Chỉ khi đã duyệt kế hoạch mới chạy:

    .\venv\Scripts\python.exe src\manage.py migrate

Nếu check --deploy báo HTTPS redirect, secure cookies, ALLOWED_HOSTS hoặc SECRET_KEY, hãy dừng và sửa cấu hình. HSTS có thể để 0 trong SIT để tránh ghim trình duyệt dài hạn; nếu còn cảnh báo HSTS thì ghi nhận là chấp nhận riêng cho SIT nội bộ, tuyệt đối không coi là đạt production.

## 3. Thu thập static và chạy WSGI thử

    .\venv\Scripts\python.exe src\manage.py collectstatic --noinput

Note: collectstatic copied 219 files locally and reported two duplicate admin JavaScript paths packaged by Jazzmin and Django. findstatic resolves the Jazzmin copies first; verify the admin page in the SIT browser after static mapping.

IIS/reverse proxy phục vụ /static/ từ src/staticfiles/. Chạy Waitress ở cửa sổ PowerShell riêng, tại thư mục gốc:

    Set-Location .\src
    ..\venv\Scripts\waitress-serve.exe --listen=127.0.0.1:8001 config.wsgi:application

Ở cửa sổ khác:

    Invoke-WebRequest http://127.0.0.1:8001/portal/ -MaximumRedirection 5

Sau đó mở URL HTTPS SIT qua reverse proxy để kiểm tra đăng nhập, CSS, static files và cookie. Proxy kết thúc TLS, kiểm tra Host, xóa/ghi đè X-Forwarded-Proto=https và chặn truy cập trực tiếp tới cổng 8001. Chỉ tin header proxy khi client không thể đi thẳng vào Waitress. Không mở Waitress trực tiếp ra Internet/LAN rộng.

Waitress hỗ trợ CPython trên Windows. Django yêu cầu WSGI/ASGI server thay runserver khi triển khai. Tham khảo [Django deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/), [Django static files](https://docs.djangoproject.com/en/5.2/howto/static-files/deployment/) và [Waitress](https://docs.pylonsproject.org/projects/waitress/en/stable/).

## 4. Test hồi quy SQL Server SIT

Chỉ chạy trên SIT được phép tạo/xóa database test. Django test runner sẽ tạo rồi xóa test database; không chạy với production hay database dùng chung:

    .\venv\Scripts\python.exe src\manage.py test apps.task.tests apps.m365.tests apps.contract.tests apps.security.tests apps.common.tests apps.lifecycle.tests apps.reporting.tests apps.attendance.tests apps.leave.tests apps.portal.tests apps.payroll.tests apps.recruitment.tests apps.asset.tests apps.activity.tests apps.organization.tests apps.kpi.tests apps.document.tests apps.hrm.tests apps.office.tests apps.project.tests apps.planning.tests apps.notification.tests apps.procurement.tests

Kết quả ngày 27/09 là 177 test đạt trên SQL Server test database tạm. Lưu số test/backend/log của lần chạy trên máy chủ; xử lý mọi lỗi thay vì dựa vào kết quả trước đây.

## 5. Smoke test bằng dữ liệu nhân tạo

Dùng [kịch bản UAT](UAT_Kich_Ban_Nghiem_Thu_4_Hang_Muc.md), tạo tài khoản theo vai trò và thử:

- Đăng nhập/đăng xuất, menu và quyền xem/sửa ở máy chủ.
- Hồ sơ, yêu cầu cập nhật, checklist HCNS, sơ đồ tổ chức.
- Nghỉ phép, bảng công, công văn, tài sản.
- Hoạt động dự án: giao Task, cập nhật, tải báo cáo giả lên SharePoint, hoàn thành; kiểm tra lịch/dashboard.
- Link xin duyệt mở cửa sổ soạn Outlook trên máy nhân viên; người gửi kiểm tra rồi tự gửi.
- SharePoint upload/download/delete file giả trong folder SIT; xác nhận đúng thư viện, ACL và xóa file thử.
- Lương chỉ với dữ liệu giả/ẩn danh; không phát lương thật từ SIT.

## Backup, phục hồi và quay lui

- Trước migration, DBA sao lưu SQL Server SIT ra vị trí độc lập. Sau đó xác nhận migration history và smoke test.
- Nếu dùng local storage, sao lưu src/media/ cùng DB. Nếu dùng SharePoint, xác nhận retention/ACL và quy trình phục hồi M365.
- Sao lưu .env riêng theo quy trình mã hóa của IT; không đưa vào Git, chat/email hoặc thư mục backup công khai.
- Trước nghiệm thu, restore thử sang DB SIT khác và kiểm tra đăng nhập/dữ liệu mẫu. Chưa chứng minh restore thì chưa đạt go-live.
- Khi quay lui, dừng ứng dụng/proxy, giữ log, khôi phục DB và files từ backup đã thử. Không xóa migration hoặc sửa bảng production thủ công.

## Còn thiếu trước production

Chưa xác nhận website trên máy chủ SIT, TLS/domain, restore drill, quyền service account, ACL SharePoint server, UAT có chữ ký. Windows Task Scheduler cho nhắc hạn chưa đăng ký theo thứ tự ưu tiên đã thống nhất. Tài liệu này không phải phê duyệt go-live.
