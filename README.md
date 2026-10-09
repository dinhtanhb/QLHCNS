# IHRMS — Quản lý Hành chính & Nhân sự

Nhật ký thay đổi và kết quả kiểm tra được ghi tại [docs/PROJECT_WORK_LOG.md](docs/PROJECT_WORK_LOG.md); quy tắc làm việc tại [AGENTS.md](AGENTS.md).

IHRMS là ứng dụng nội bộ Django 5.2, gồm Cổng nhân viên (/portal/), trang quản trị (/admin/) và các phân hệ nghiệp vụ. Mã nguồn Django nằm trong thư mục src/ (chữ thường).

## Nhánh mã nguồn

Chỉ dùng `main` để phát triển, kiểm thử và chạy ứng dụng. Quy tắc chi tiết tại [AGENTS.md](AGENTS.md); kết quả hợp nhất tại [nhật ký dự án](docs/PROJECT_WORK_LOG.md). Khi bản sao cục bộ không có thay đổi chưa commit, cập nhật trong thư mục gốc dự án:

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
```

Nếu còn thay đổi cục bộ hoặc Git báo không thể fast-forward, giữ nguyên chúng và đối chiếu trước khi tiếp tục.

## Trạng thái chuẩn bị máy chủ SIT

Rà soát ngày 27/09/2026: cấu hình máy phát triển kết nối SQL Server; 177 test đạt trên SQL Server test database tạm; check, kiểm tra migration và pip check đạt. Đây chưa phải bằng chứng máy chủ SIT đã cấu hình xong.

Hướng dẫn dựng SIT, danh sách việc IT cần chuẩn bị và checklist kiểm thử: [docs/Server_Trial_Readiness_2026-09-27.md](docs/Server_Trial_Readiness_2026-09-27.md). Không trỏ SIT vào database production, không chép secrets từ .env của máy khác và không đưa .env, backup SQL, dữ liệu nhân sự/lương hay tệp tải lên vào Git.

## Tài liệu dự án

- [Cẩm nang sử dụng](docs/HUONG_DAN_SU_DUNG_IHRMS.md), [giáo án tập huấn](docs/TAP_HUAN_IHRMS.md), [kịch bản UAT](docs/UAT_Kich_Ban_Nghiem_Thu_4_Hang_Muc.md)
- [Lộ trình Hoạt động dự án NGO](docs/NGO_Activity_Planning_MEL_Roadmap.md)
- [Đánh giá sẵn sàng lịch sử](docs/Production_Readiness_Review_2026-09-23.md) là snapshot ngày 24/09; xem runbook SIT để biết trạng thái mới hơn
- [Tiêu chuẩn triển khai](docs/08_Deployment_Standards.md); hướng dẫn Codex ở .agents/skills/
- [Hướng dẫn review tổng thể hoặc thay đổi, mẫu yêu cầu và lệnh kiểm tra](docs/Huong_Dan_Review_Du_An.md); reviewer Sixth tại [.sixth/agents/code-review.md](.sixth/agents/code-review.md)
- [Hệ thống giao diện hiện hành](docs/UI_DESIGN_SYSTEM.md), [tiêu chuẩn frontend](docs/06_Frontend_Standards.md) và [đặc tả màn hình](docs/09_UI_UX_Specification.md)

Hoạt động dự án có dashboard, lịch, Task báo cáo, đề xuất PDF và hàng chờ duyệt. Người dùng soạn/gửi thư xin duyệt bằng Outlook trên máy họ. Ứng dụng chưa tự gửi thư qua máy chủ, chưa có sổ ngân sách/chứng từ/quyết toán và chưa triển khai SSO, Teams hay Office tự động. SharePoint cần cấu hình và kiểm tra quyền riêng cho SIT.

## Thành phần

| Thành phần | Yêu cầu/trạng thái |
|---|---|
| Python | 3.12 |
| Django | 5.2.17 |
| Cơ sở dữ liệu | SQL Server; database riêng cho SIT |
| Máy chủ mục tiêu | Windows Server; các nền tảng khác chưa được xác nhận |
| WSGI cho Windows SIT | Waitress đặt sau reverse proxy có TLS |
| SQL driver | ODBC Driver 17 theo cấu hình hiện tại |
| Tệp đính kèm | SharePoint khi bật; thư mục src/media/ nếu lưu cục bộ |

## Cài đặt phát triển trên Windows

Trong PowerShell tại thư mục gốc dự án:

    py -3.12 -m venv venv
    .\venv\Scripts\Activate.ps1
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    Copy-Item .env.example .env

Sửa .env với database phát triển, sinh SECRET_KEY mới bằng lệnh dưới đây và không dùng giá trị mẫu:

    python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

Đặt DEBUG=True chỉ trong môi trường phát triển dùng runserver. Dùng DEBUG=False trên SIT/UAT.

    python src\manage.py check
    python src\manage.py migrate
    python src\manage.py createsuperuser
    python src\manage.py runserver

Mở http://127.0.0.1:8001/portal/. Lệnh `runserver` của QLHCNS mặc định dùng cổng 8001 để tránh trùng các dự án khác. Có thể chọn cổng khác bằng `python src\manage.py runserver 8002`. runserver chỉ dành cho phát triển cục bộ, không dùng làm web server máy chủ. Chỉ chạy migrate sau khi xác nhận database đích là database phát triển/SIT riêng và đã sao lưu.

## Kiểm thử, sao lưu, phân quyền

Từ thư mục gốc dự án, dùng một lệnh chuẩn:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\Run-Tests.ps1
```

Script tự chuyển vào `src`, dùng `venv\Scripts\python.exe` nếu có, chạy toàn bộ test đã phát hiện (bao gồm `apps.portal.tests_mobile`) và báo lỗi nếu số test bằng 0. Chạy trực tiếp `python src\manage.py test` từ thư mục gốc có thể phát hiện 0 test; nếu gọi Django trực tiếp, phải đứng trong `D:\QLHCNS\src`. Django test runner tạo rồi xóa test database, vì vậy chỉ chạy khi cấu hình trỏ tới database test cô lập (SQLite local hoặc SQL Server test/SIT), không phải database nghiệp vụ dùng chung.

Ma trận vai trò nằm tại src/apps/security/permissions.py và được kiểm tra ở máy chủ. Các vai trò gồm SUPER_ADMIN, SYS_ADMIN, DIRECTOR, HR_MANAGER, HR_OFFICER, DEPT_MANAGER, FINANCE_OFFICER, PROJECT_MANAGER, PROJECT_COORDINATOR, CBDA, EMPLOYEE.

DBA sao lưu SQL Server và thử restore vào môi trường riêng. Nếu có lưu tệp cục bộ, sao lưu src/media/ cùng database. Tệp SharePoint theo chính sách retention/backup Microsoft 365. Cất .env trong kho secrets được kiểm soát riêng.

Trước go-live, xem [Django deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/) và checklist của công ty.
