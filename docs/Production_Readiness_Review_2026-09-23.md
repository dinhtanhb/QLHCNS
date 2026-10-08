# Đánh giá mức sẵn sàng triển khai IHRMS

**Cập nhật:** 24/09/2026

**Phạm vi:** mã nguồn trên nhánh `chore/django-5.2-upgrade`, cấu hình và kết quả kiểm tra được cung cấp đến thời điểm cập nhật.

**Kết luận:** IHRMS đã tiến thêm đáng kể: mã nguồn có thể clone sạch, dependency đã nâng lên Django 5.2, kết nối SQL Server tại môi trường kiểm tra hoạt động, và lưu tệp SharePoint đã được smoke test thực tế. Tuy vậy, chưa đủ bằng chứng để mở vận hành chính thức cho nhân viên. Cần hoàn tất hardening trên đúng Windows Server/IIS và tên miền công ty, backup/restore, kiểm thử nghiệp vụ/UAT và diễn tập go-live.

## Những gì đã xác nhận

- GitHub có source tree thông thường, clone sạch được. Commit tích hợp SharePoint và tài liệu hiện tại là `475c3e7` trên nhánh `chore/django-5.2-upgrade`.
- `requirements.txt` ghim Django `5.2.17`; các migration hiện có được phát sinh và `makemigrations --check --dry-run` trả về `No changes detected` trong lần kiểm tra gần nhất.
- Trên máy kiểm thử, Django kết nối được SQL Server (`connection.vendor=microsoft`). Chủ dự án đã báo đã chuyển cấu hình và áp dụng migration SQL Server. Tuy nhiên, toàn bộ 81 bài kiểm thử đã cung cấp trước đó chạy trên SQLite; chưa có kết quả chạy đủ test suite trên SQL Server.
- `manage.py check` không có lỗi. Lần chạy gần nhất có 86/86 bài đạt trên SQLite: asset/common/hrm/leave/payroll/security và m365.
- Cần gọi rõ các module test, ví dụ `python src/manage.py test apps.asset.tests apps.common.tests apps.hrm.tests apps.leave.tests apps.payroll.tests apps.security.tests apps.m365.tests apps.portal.tests_mobile`. Lệnh `python src/manage.py test` không kèm module từ thư mục gốc hiện phát hiện 0 bài trong cấu trúc này; xem cập nhật 28/09 bên dưới để chạy bộ test hiện hành.
- Microsoft Graph/SharePoint đã được kiểm tra thật qua thao tác tải lên, xem/đọc lại và xóa tệp thử. Người dùng xác nhận các luồng lưu tệp cần thiết vào thư viện/folder SharePoint tương ứng hoạt động. Đây là kiểm tra lưu trữ, không chứng minh email, Teams, OneDrive đồng bộ hay SSO đã được triển khai.
- Các FileField cần lưu hồ sơ dùng adapter storage ổn định qua migration; khi SharePoint bị tắt, hệ thống dùng media storage cục bộ. Migrations của document, leave, m365, office và recruitment đã được tạo.

## Còn thiếu trước khi go-live

> **Cập nhật 28/09/2026 — test discovery:** Review lịch sử ở trên phản ánh trạng thái tại ngày 24/09. Lệnh chuẩn hiện hành là `powershell -NoProfile -ExecutionPolicy Bypass -File .\ops\Run-Tests.ps1` từ thư mục gốc; script tự chạy trong `src`, bao gồm `apps.portal.tests_mobile`, in số test và báo lỗi nếu không phát hiện test. Kết quả SIT phải được ghi riêng cho từng lần chạy.

### 1. Cấu hình Windows Server và HTTPS

Chạy `manage.py check --deploy` bằng đúng cấu hình triển khai. Kết quả trước đây có cảnh báo về HTTPS redirect, HSTS, `SECRET_KEY`, cookie session/CSRF và `DEBUG`; chưa có bằng chứng các cảnh báo đã được xử lý trên máy chủ production. Cấu hình IIS/reverse proxy, HTTPS, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, secure cookies, static files, service account và logging cần được kiểm tra tại máy chủ đích. Không bật HSTS trước khi xác nhận toàn bộ hostname/subdomain luôn hoạt động qua HTTPS.

### 2. SQL Server

Kết nối và migration đã được báo thành công tại môi trường kiểm tra, nhưng cần xác nhận server production dùng database riêng cho IHRMS, đúng tài khoản dịch vụ và quyền tối thiểu. Chạy test suite trên SQL Server (không chỉ SQLite), thử các transaction/khóa đồng thời, và diễn tập cài đặt mới từ clone sạch. Không dùng chung database nghiệp vụ của ứng dụng khác.

### 3. Dữ liệu lương và UAT

Finance cần đối chiếu độc lập kết quả với bảng tính được công ty phê duyệt, gồm nhân viên vào/nghỉ giữa kỳ, tăng ca, nghỉ không lương, người phụ thuộc, thuế, bảo hiểm, làm tròn và các khoản phụ cấp. HR, quản lý, nhân viên, Finance và IT cần ký UAT cho các luồng được giao. Dữ liệu test hiện tại không thay thế dữ liệu chuẩn đã xác minh.

### 4. Backup và khôi phục

Do dữ liệu hiện tại chỉ là dữ liệu thử, trước đây chưa cần backup. Trước production phải lập lịch backup SQL Server và tệp hồ sơ, lưu bản sao ở vị trí độc lập, giới hạn quyền truy cập và theo dõi lỗi job. Thực hiện restore thử vào môi trường riêng, ghi thời gian khôi phục thực tế và được công ty duyệt RPO/RTO.

### 5. Phạm vi Microsoft 365 và quản trị tệp

SharePoint document storage đã qua smoke test. IT vẫn cần xác nhận quyền Graph/Entra ở mức tối thiểu, danh sách người được phép xem thư viện, retention, audit và quy trình khi SharePoint gián đoạn. Không đưa file nhạy cảm lên thư viện dùng chung nếu ACL chưa được kiểm tra. Mail, Teams automation, Office co-authoring, OneDrive cá nhân và SSO chỉ được tính là sẵn sàng khi có cấu hình và UAT riêng.

## Lộ trình còn lại

1. Chốt chủ quy trình, ma trận quyền, người phê duyệt thay thế và chính sách lương/lưu trữ.
2. Chuẩn bị Windows Server/IIS và SQL Server production hoặc SIT riêng; cấu hình secrets ngoài Git, HTTPS, host, static, log và tài khoản dịch vụ.
3. Chạy `check --deploy`, migrations và toàn bộ test trên SQL Server; lưu log kết quả, không đưa secrets vào log.
4. Đào tạo HR, Finance, quản lý và nhân viên trên môi trường demo; hoàn tất UAT trên dữ liệu ẩn danh.
5. Thiết lập backup, restore thử, giám sát và phương án quay lui; diễn tập cutover.
6. Chỉ go-live khi chủ nghiệp vụ, IT và người phê duyệt của công ty ký checklist phát hành.

## Phù hợp quy mô 30–50 nhân viên

Django modular monolith cùng một database SQL Server riêng phù hợp với quy mô này; chưa cần microservices. Nên có tối thiểu một môi trường SIT/UAT tách khỏi production, một đầu mối IT vận hành, một đầu mối HR và Finance, tài khoản cá nhân theo vai trò, backup ngoài máy chủ và kênh hỗ trợ nội bộ. Cấu hình phần cứng phải dựa trên Windows/IIS/SQL Server licensing, dung lượng tài liệu và chính sách backup thực tế.

## Tài liệu liên quan

- [Cẩm nang sử dụng IHRMS](HUONG_DAN_SU_DUNG_IHRMS.md)
- [Giáo án và bài thực hành tập huấn](TAP_HUAN_IHRMS.md)
- [Kế hoạch triển khai](ihrms-rollout-plan.canvas.tsx)
- [Kiến trúc giải pháp](02_Solution_Architecture.md)
- [Tiêu chuẩn triển khai](08_Deployment_Standards.md)

> Báo cáo gốc ngày 23/09/2026 được lưu trong [Review_23092026_recovered.md](archive/reviews/Review_23092026_recovered.md); đây là bản snapshot lịch sử, không phải đánh giá hiện hành.
