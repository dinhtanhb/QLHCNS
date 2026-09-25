# Theo dõi hoạt động dự án NGO trong IHRMS

**Cập nhật:** 25/09/2026
**Phạm vi đợt đầu:** giao việc, theo dõi tiến độ, nhắc hạn và lưu báo cáo hoạt động trên SharePoint.
**Ngoài phạm vi:** lập/duyệt ngân sách, thu thập chứng từ tài chính, rà soát hoặc quyết toán.

## Mục tiêu nghiệp vụ

Khi một công văn đi đã phát hành được liên kết với Hoạt động dự án, IHRMS tự tạo một Task báo cáo cho CBDA phụ trách chính. Task có người giao, người nhận, hoạt động/dự án liên quan, hạn, trạng thái và liên kết tệp báo cáo. CBDA cập nhật Task và tải báo cáo lên thư viện SharePoint; không thể đánh dấu hoàn thành nếu chưa có báo cáo. Quản lý dự án và điều phối viên xem bảng tiến độ theo tháng để hỗ trợ và nhắc người phụ trách.

## Quy tắc đã triển khai

- Hạn mặc định là 10 ngày làm việc tính sau ngày trên công văn; ngày công văn là ngày 0. Lịch hiện theo quy ước IHRMS: thứ Hai–thứ Sáu, loại trừ các ngày lễ đang hoạt động trong danh mục Ngày lễ. Làm việc thứ Bảy chưa được hỗ trợ như một ngoại lệ lịch.
- Công văn đi hiện hữu được dùng làm dấu mốc phát hành. Khi lưu/liên kết công văn với hoạt động, hệ thống tạo một Task duy nhất; cập nhật hoạt động lần nữa không nhân bản Task.
- Task giao cho CBDA chính; điều phối viên (hoặc người ký công văn nếu thiếu điều phối viên) là người giao. CBDA chỉ xem hoạt động được giao/điều phối cho mình; Ban Giám đốc, quản lý dự án và điều phối viên xem toàn bộ.
- Tệp báo cáo thuộc cấu hình SharePoint `activity_reports` (thư mục mặc định `BaoCaoHoatDong`). Nếu M365 bị tắt, cấu hình hiện tại dùng storage cục bộ theo thiết lập của ứng dụng.
- Thông báo nhắc trong IHRMS được tạo trước hạn 3 ngày làm việc, 1 ngày làm việc, đúng ngày hạn và vào mỗi ngày làm việc quá hạn. Chạy lặp trong cùng ngày không gửi trùng. Đây là cấu hình mặc định của đợt đầu.
- Hoạt động có khoảng ngày trùng với hoạt động khác của cùng CBDA chính bị kiểm tra/cảnh báo. Cần UAT hành vi nhập form trước khi dùng rộng rãi.
- Cảnh báo trùng lịch trong trang quản trị không chặn lưu; điều phối viên xem xét và sắp xếp lại hoặc xác nhận phương án.

## Vai trò

- **Giám đốc/Quản lý dự án:** xem dashboard toàn đơn vị, theo dõi trễ hạn và thiếu báo cáo; hỗ trợ hoặc điều phối lại.
- **Điều phối viên:** gắn công văn đã phát hành, CBDA phụ trách và hoạt động; theo dõi Task và thông báo.
- **CBDA:** xem việc của mình, cập nhật trạng thái, tải báo cáo và hoàn thành Task.
- **Quản trị hệ thống:** gán vai trò `PROJECT_MANAGER`, `PROJECT_COORDINATOR`, `CBDA` cho tài khoản phù hợp và cấu hình thư viện SharePoint.

## Cách sử dụng

1. Tạo Hoạt động dự án, chọn dự án, CBDA chính, điều phối viên, khoảng ngày, mục đích/kết quả và thông tin cần thiết.
2. Sau khi công văn đi đã được phát hành trong phân hệ Công văn đi, liên kết công văn đó với Hoạt động. Kiểm tra Task báo cáo đã xuất hiện trong danh sách giao việc, đúng người và đúng hạn.
3. CBDA vào Giao việc của tôi, cập nhật tiến độ. Sau khi triển khai, tải báo cáo lên Task; mở tệp kiểm tra được rồi mới chuyển trạng thái Hoàn thành.
4. Quản lý/điều phối viên mở mục **Hoạt động dự án**, chọn tháng để xem tổng số hoạt động, Task hoàn tất, quá hạn, thiếu báo cáo và hoạt động chưa có Task.

## Nhắc việc tự động trên Windows

Mã nguồn có lệnh `python src/manage.py send_activity_report_reminders`. Để lệnh chạy hằng ngày, IT cần đăng ký Windows Task Scheduler trên máy ứng dụng. Script `ops/scheduler/Run-ActivityReportReminders.ps1` dùng Python của `venv` trong thư mục dự án hoặc biến môi trường `IHRMS_PYTHON`, và ghi log dưới `Logs`.

Đề xuất cấu hình Scheduled Task: chạy mỗi ngày lúc 08:00; Action `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "<đường-dẫn-dự-án>\ops\scheduler\Run-ActivityReportReminders.ps1"`; chạy bằng tài khoản dịch vụ có quyền đọc mã dự án, môi trường `.env` và kết nối SharePoint/SQL Server cần thiết. Sau khi tạo task, chạy thử thủ công một lần và xác nhận log cùng thông báo trong IHRMS. Script tự bỏ qua cuối tuần/ngày nghỉ.

## Đã kiểm tra và còn mở

- 8 kiểm thử mới bao phủ hạn ngày làm việc/ngày lễ, sinh Task lặp an toàn, phân quyền CBDA, yêu cầu tải báo cáo, nhắc lặp trong ngày và dashboard.
- Kiểm thử chạy trên SQLite test database tạm; không chạy migration lên SQL Server hiện hữu. Cần chạy UAT riêng trên SQL Server SIT sau khi IT xác nhận database thử nghiệm.
- Trước khi vận hành: tạo lịch Windows Task Scheduler, xác nhận role người dùng, thực hiện thử với một công văn giả và một tệp báo cáo giả trên đúng thư viện SharePoint, kiểm tra quyền truy cập/dashboard, thống nhất ngày thứ Bảy nếu đơn vị làm việc thứ Bảy.
- Ghi lại kết quả và mọi thao tác tiếp theo tại [`PROJECT_WORK_LOG.md`](PROJECT_WORK_LOG.md).
