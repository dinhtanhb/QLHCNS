# QLHCNS — IHRMS

Hệ thống **Quản lý Hành chính & Nhân sự** nội bộ, xây dựng trên Django 5.0.
Gồm hai phần: **Cổng thông tin nhân viên** (`/portal/`) và **Trang quản trị** (`/admin/`).

---

## 1. Yêu cầu máy cài đặt

| Thành phần | Phiên bản |
|---|---|
| Python | 3.12 trở lên |
| Hệ quản trị CSDL | SQLite (mặc định, không cần cài gì) hoặc SQL Server 2016+ |
| Hệ điều hành | Windows 10/11 (đã chạy thực tế), Linux đều được |

## 2. Cấu trúc thư mục

```
D:\QLHCNS\
├── .env                  <- Cấu hình bí mật (KHÔNG đưa lên Git)
├── .gitignore
├── requirements.txt
├── README.md
├── venv\                 <- Môi trường ảo Python
└── SRC\
    ├── manage.py
    ├── db.sqlite3        <- CSDL (KHÔNG đưa lên Git)
    ├── config\           <- settings.py, urls.py
    ├── apps\             <- 20 phân hệ nghiệp vụ
    ├── templates\        <- Giao diện dùng chung (base.html)
    ├── static\
    └── media\            <- File người dùng tải lên (KHÔNG đưa lên Git)
```

## 3. Cài đặt lần đầu

Mở **Command Prompt** và chạy lần lượt:

```bat
cd /d D:\QLHCNS
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Tạo file cấu hình: copy `.env.example` thành `.env` (đặt tại `D:\QLHCNS\.env`), mở bằng Notepad và điền `SECRET_KEY`.
Tạo chuỗi bí mật mới:

```bat
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Khởi tạo cơ sở dữ liệu và tài khoản quản trị:

```bat
cd /d D:\QLHCNS\SRC
python manage.py migrate
python manage.py createsuperuser
```

## 4. Chạy hằng ngày

```bat
cd /d D:\QLHCNS\SRC
..\venv\Scripts\activate
python manage.py runserver
```

Mở trình duyệt:
- Cổng nhân viên: http://127.0.0.1:8000/portal/
- Trang quản trị: http://127.0.0.1:8000/admin/
- Trung tâm báo cáo: http://127.0.0.1:8000/reports/

Dừng server: nhấn `Ctrl + C`.

## 5. Sau mỗi lần cập nhật mã nguồn

```bat
cd /d D:\QLHCNS\SRC
..\venv\Scripts\activate
pip install -r ..\requirements.txt
python manage.py migrate
python manage.py runserver
```

## 6. Sao lưu

Chỉ cần sao chép 3 thứ:
1. `D:\QLHCNS\SRC\db.sqlite3` — toàn bộ dữ liệu
2. `D:\QLHCNS\SRC\media\` — file đính kèm
3. `D:\QLHCNS\.env` — cấu hình

## 7. Các phân hệ (`SRC\apps\`)

| Thư mục | Chức năng |
|---|---|
| `common` | Tiện ích dùng chung, chuẩn hóa tên file tải lên |
| `security` | Tài khoản, vai trò, **ma trận phân quyền** (`permissions.py`) |
| `organization` | Cơ cấu tổ chức, phòng ban, chức danh |
| `hrm` | Hồ sơ nhân viên |
| `attendance` | Chấm công, lịch làm việc, ngày lễ |
| `leave` | Nghỉ phép, quỹ phép, nghỉ bù |
| `contract` | Hợp đồng lao động |
| `payroll` | Bảng lương, bảo hiểm, thuế TNCN |
| `portal` | Cổng thông tin nhân viên (giao diện chính) |
| `task` | Giao việc, theo dõi công việc |
| `kpi` | Chấm điểm KPI |
| `document` | Tài liệu nội bộ, quy trình ban hành |
| `office` | Công văn đến / công văn đi |
| `asset` | Tài sản, kiểm kê, thanh lý |
| `recruitment` | Tuyển dụng, hồ sơ ứng viên |
| `procurement` | Mua sắm, văn phòng phẩm |
| `project` | Dự án, chấm công theo dự án |
| `planning` | Kế hoạch, lịch, sự kiện |
| `notification` | Thông báo trong hệ thống |
| `reporting` | Trung tâm báo cáo, xuất Excel |

## 8. Phân quyền

Toàn bộ quyền được khai báo **duy nhất** tại `SRC\apps\security\permissions.py`, trong bảng `PERMISSION_MATRIX`.
Muốn thay đổi ai được làm gì, chỉ sửa bảng đó — cả menu lẫn trang thực tế sẽ tự áp dụng theo.

Các vai trò: `SUPER_ADMIN`, `SYS_ADMIN`, `DIRECTOR`, `HR_MANAGER`, `HR_OFFICER`, `DEPT_MANAGER`, `FINANCE_OFFICER`, `EMPLOYEE`.

> Lưu ý: cờ **Staff status** trong `/admin/` chỉ dùng để cho phép vào trang quản trị Django.
> Tài khoản nhân viên thường **không** được tick ô này.

## 9. Xử lý sự cố thường gặp

| Hiện tượng | Cách xử lý |
|---|---|
| `ModuleNotFoundError` | Chưa kích hoạt venv → chạy `..\venv\Scripts\activate` |
| `no such table` | Chưa chạy `python manage.py migrate` |
| Giao diện sai/cũ | Nhấn `Ctrl + F5` trên trình duyệt để xóa cache |
| `Conflicting migrations` | File migration bị đặt nhầm app → xóa file đặt sai chỗ |
| `SECRET_KEY` cảnh báo | Thiếu file `.env` tại `D:\QLHCNS\.env` |
