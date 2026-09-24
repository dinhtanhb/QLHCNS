# Đánh giá mức sẵn sàng IHRMS — 23/09/2026

## Kết luận điều hành

**Chưa đủ điều kiện chuyển sang SQL Server và chưa nên đưa vào vận hành production.** Quy mô 30–50 nhân sự không phải trở ngại về năng lực của Django hay SQL Server; kiến trúc modular monolith hiện tại là hợp lý cho quy mô đó. Các chặn hiện tại nằm ở khả năng tái tạo bản phát hành, phiên bản framework hết hỗ trợ, cấu hình production và việc chưa kiểm thử/migrate dữ liệu trên SQL Server.

Đánh giá này dựa trên mã hiện có trong `src/`, tài liệu dự án, Django system checks và test suite. Đây là đánh giá readiness kỹ thuật, không phải chứng nhận công thức lương/thuế hay phê duyệt quy trình nghiệp vụ.

## Bằng chứng đã kiểm tra

- `python manage.py test`: **81 test đạt** trên SQLite.
- `python manage.py check`: không có lỗi.
- `python manage.py check --deploy`: có 5 cảnh báo: HSTS chưa bật, HTTPS redirect chưa bật, `SECRET_KEY` bị đánh giá yếu, session cookie chưa secure, CSRF cookie chưa secure.
- `python manage.py makemigrations --check --dry-run`: không phát hiện migration còn thiếu.
- Cấu hình runtime đang chạy `DEBUG=False`, SQLite; `STATIC_ROOT` chưa cấu hình.
- Không tìm thấy raw SQL hoặc dấu hiệu truy vấn đặc thù SQLite trong lần quét ứng dụng; tuy nhiên các test hiện tại chỉ chạy SQLite, chưa chứng minh tính tương thích ở backend khác.
- Một số nghiệp vụ đã có ràng buộc và test bổ sung: kỳ lương khóa/phát hành phiếu PDF, điều chuyển/bổ nhiệm theo ngày hiệu lực, cấp phát tài sản, hoàn tất kiểm kê, phép qua tháng/năm và xóa mềm.

## Chặn phát hành — cần xử lý trước production

### P0 — Git không thể tái tạo source tree

`HEAD` lưu `src` dưới dạng gitlink (`160000`) nhưng repository không có `.gitmodules`; `git submodule status` trả về `fatal: no submodule mapping found in .gitmodules for path 'src'`. Thư mục `src` tại máy hiện tại không có metadata `.git` riêng. Vì vậy clone sạch không thể tái tạo mã ứng dụng và các thay đổi trong `src` không xuất hiện như thay đổi file thông thường ở repository cha.

**Cần làm:** chọn một cấu trúc có thể clone sạch: đưa source vào repository thường, hoặc khôi phục submodule với URL/commit được quản lý và CI xác minh được. Sau đó kiểm tra clone mới trên máy khác trước khi tạo gói phát hành.

### P0 — Django 5.0.14 đã hết hỗ trợ

`requirements.txt` ghim Django 5.0.14. Django 5.0 hết extended support ngày 02/04/2025 và không còn nhận security/data-loss fixes. Nâng lên một nhánh Django còn hỗ trợ, rồi nâng từng phụ thuộc và chạy toàn bộ test. Tại ngày đánh giá, trang tải Django liệt kê 5.2 LTS là nhánh hỗ trợ đến 04/2028; chọn phiên bản patch hiện hành cùng backend/plug-in tương thích thay vì giữ nguyên 5.0.14. [Django — supported versions](https://www.djangoproject.com/download/)

### P0 — Chưa có bằng chứng SQL Server end-to-end

`settings.py` có nhánh `ENGINE="mssql"`, nhưng `mssql-django` và `pyodbc` vẫn bị comment trong `requirements.txt`. Driver ODBC bị cố định thành Driver 17. Thư viện có trong virtualenv của máy đánh giá không thay thế được dependency khai báo và cài đặt trên production. Chưa chạy migrate, test, payroll, khóa/phát hành phiếu lương và kiểm thử đồng thời trên một SQL Server thực.

Backend chính thức `mssql-django` hỗ trợ Django và SQL Server theo ma trận phiên bản riêng; các giới hạn ORM/DB cần đối chiếu với đúng phiên bản đã chọn. [Microsoft mssql-django](https://github.com/microsoft/mssql-django), [Microsoft Learn: support/lifecycle](https://learn.microsoft.com/en-us/sql/connect/python/mssql-django/support-lifecycle?view=sql-server-ver17)

**Cần làm:** pin backend/driver tương thích; tạo database SIT rỗng; chạy migrations từ đầu; chạy toàn bộ test trên SQL Server; bổ sung bài test transaction/row-lock/concurrency; kiểm thử IIS/WSGI, static, upload, PDF và backup/restore.

### P0 — Chưa đạt baseline bảo mật web production

`check --deploy` nêu các cảnh báo HTTPS/HSTS/session/CSRF cookie và chất lượng secret. `DEBUG=False` là đúng trong runtime kiểm tra, nhưng cấu hình production chưa được tách và kiểm chứng. `ALLOWED_HOSTS` được đọc trực tiếp từ biến môi trường; không có `STATIC_ROOT`; chưa có cấu hình logging/monitoring/HTTPS proxy được kiểm nghiệm.

**Cần làm:** tách cấu hình theo môi trường; tạo secret ngẫu nhiên mạnh mới cho production; khóa HTTPS và cookie secure sau khi cấu hình IIS/proxy đúng; khai báo host/CSRF trusted origins; chạy `check --deploy` không còn cảnh báo chưa được giải trình; thiết lập collectstatic, log, quyền service account và upload directory. Tham khảo [Django deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/).

## Việc cần xác nhận trước khi vận hành thật

### P1 — Lương và dữ liệu nhân sự

- Kế toán/đơn vị tư vấn xác nhận effective date, thuế, BHXH/BHYT/BHTN, giảm trừ, phụ cấp và quy tắc làm tròn theo chính sách công ty và quy định hiện hành.
- So sánh độc lập bảng tính mẫu với kết quả hệ thống cho người mới/nghỉ giữa kỳ, người phụ thuộc, nghỉ không lương, tăng ca, mức đóng bảo hiểm có trần và từng nhóm thuế.
- Thử quy trình tạo kỳ → sinh dòng nhân viên → tính lại → đối soát → khóa → phát hành PDF → kiểm tra tài khoản nhân viên chỉ tải phiếu của chính mình.
- Thiết lập người nhập và người duyệt tách biệt; giới hạn Finance/Admin; xác nhận khả năng mở khóa kỳ có kiểm soát nếu doanh nghiệp cần quy trình điều chỉnh.

### P1 — Backup, restore và files

Tài liệu deployment hiện mô tả lịch backup/RPO/RTO nhưng trong code/repo chưa có bằng chứng job backup, cảnh báo thất bại, log tập trung hay biên bản restore. Cần backup database SQL Server và `media/` tới vị trí độc lập; mã hóa và giới hạn quyền; giữ lịch sử theo chính sách; diễn tập restore trên môi trường riêng; đo thời gian khôi phục thực tế. Không dùng thao tác copy thô `db.sqlite3` khi SQLite đang được ghi.

### P1 — Kiểm thử nghiệp vụ và quyền

81 test là nền tảng hữu ích nhưng không thay thế UAT. Bổ sung kiểm tra role/IDOR cho hồ sơ, nghỉ phép, chấm công, báo cáo và phiếu lương; kịch bản cạnh tranh hai người duyệt/cấp cùng tài sản; kiểm thử upload dung lượng/đuôi file; regression payroll; smoke test trình duyệt ở các vai trò. Xác nhận các tích hợp được nêu trong tài liệu kiến trúc (Entra/Microsoft 365, email/Teams) có thực sự được triển khai trước khi đưa vào phạm vi cam kết.

## Lộ trình đề xuất theo thứ tự

1. **Khôi phục source control** để clone sạch và tạo artifact được.
2. **Nâng Django và dependencies** lên các phiên bản còn hỗ trợ; giữ lock file đầy đủ.
3. **Tách settings dev/SIT/UAT/prod** và hoàn tất hardening HTTPS, cookies, secrets, static, logging.
4. **Tạo SQL Server SIT**; chạy schema migration từ đầu và xử lý sai khác; không trỏ production vào SQLite hiện tại.
5. **Chuyển dữ liệu thử nghiệm trên bản sao**: mapping, import, đối chiếu số lượng và tổng kiểm soát, kiểm thử rollback; giữ SQLite gốc chỉ-đọc cho đến khi ký xác nhận.
6. **UAT với dữ liệu ẩn danh**: nhân viên, trưởng bộ phận, HR, Finance và Director kiểm tra luồng end-to-end; Finance ký biên bản kiểm thử lương.
7. **Diễn tập go-live**: backup/restore, downtime và cutover, tạo user, hướng dẫn hỗ trợ, kiểm tra quyền, monitoring, rollback.
8. Chỉ go-live khi source clone sạch, test SQLite + SQL Server đạt, không còn cảnh báo deploy chưa chấp nhận, backup restore đạt RPO/RTO được công ty duyệt và chủ nghiệp vụ ký UAT.

## Phù hợp quy mô 30–50 người

Có thể giữ một ứng dụng Django monolith trên một máy chủ ứng dụng nội bộ và SQL Server được sao lưu độc lập; không cần microservices hay hạ tầng lớn nếu tải thực tế thấp. Cần tối thiểu môi trường SIT riêng, HTTPS nội bộ, service account ít quyền, database credentials tách khỏi Git, backup ra thiết bị/vị trí thứ hai và một người chịu trách nhiệm vận hành. Tài liệu hiện ghi thông số server 8 CPU/32 GB/1 TB nhưng chưa có benchmark chứng minh cần mức đó; nên sizing theo Windows/IIS/SQL Server licensing, backup retention và dung lượng file thực tế, không mặc định cần cấu hình này cho 50 người.

## Tham chiếu

- Runtime: `src/config/settings.py`
- Dependencies: `requirements.txt`, `.env.example`
- Quy trình và deployment baseline: `docs/08_Deployment_Standards.md`
- Mã nguồn: `src/apps/` (hiện trạng gitlink cần sửa trước release)
- Test suite: `src/apps/*/tests.py`
