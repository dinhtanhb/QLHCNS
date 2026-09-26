# Theo dõi hoạt động dự án NGO trong IHRMS

**Cập nhật:** 25/09/2026
**Phạm vi hiện tại:** giao việc, theo dõi tiến độ/lịch, Task báo cáo, tệp báo cáo SharePoint, hồ sơ đề xuất hoạt động + dự trù dạng PDF, trình Giám đốc duyệt/yêu cầu chỉnh sửa, hàng chờ duyệt và thông báo trong IHRMS.
**Ngoài phạm vi hiện tại:** theo dõi ngân sách thực chi, quản lý chứng từ tài chính, xác minh tính hợp lệ hoặc quyết toán. Dự trù PDF chỉ là tài liệu xin duyệt; chưa phải module tài chính.

## Mục tiêu nghiệp vụ

Khi một công văn đi đã phát hành được liên kết với Hoạt động dự án, IHRMS tự tạo một Task báo cáo cho CBDA phụ trách chính. Task có người giao, người nhận, hoạt động/dự án liên quan, hạn, trạng thái và liên kết tệp báo cáo. CBDA cập nhật Task và tải báo cáo lên thư viện SharePoint; không thể đánh dấu hoàn thành nếu chưa có báo cáo. Quản lý dự án và điều phối viên xem bảng tiến độ theo tháng để hỗ trợ và nhắc người phụ trách.

## Quy tắc đã triển khai

- Công văn đi đã phát hành là điều kiện để giao Task. Ngày bắt đầu Task lấy từ ngày bắt đầu hoạt động; hạn báo cáo là 10 ngày làm việc sau ngày kết thúc hoạt động. Khi lịch hoạt động thay đổi, Task được đồng bộ ngày và người liên quan nhận thông báo; Task đã hoàn thành trước ngày kết thúc mới sẽ được mở lại và bỏ liên kết báo cáo cũ (tệp vẫn lưu trên SharePoint). Không thể hoàn thành Task trước khi hoạt động kết thúc. Lịch làm việc hiện theo thứ Hai–thứ Sáu, trừ ngày lễ đang hoạt động trong danh mục Ngày lễ; chưa hỗ trợ ngày làm việc thứ Bảy.
- Công văn đi hiện hữu được dùng làm dấu mốc phát hành. Khi lưu/liên kết công văn với hoạt động, hệ thống tạo một Task duy nhất; cập nhật hoạt động lần nữa không nhân bản Task.
- Task giao cho CBDA chính; điều phối viên (hoặc người ký công văn nếu thiếu điều phối viên) là người giao. CBDA chỉ xem hoạt động được giao/điều phối cho mình; Ban Giám đốc, quản lý dự án và điều phối viên xem toàn bộ.
- Tệp báo cáo thuộc cấu hình SharePoint `activity_reports` (thư mục mặc định `BaoCaoHoatDong`). Nếu M365 bị tắt, cấu hình hiện tại dùng storage cục bộ theo thiết lập của ứng dụng.
- Thông báo nhắc trong IHRMS được tạo trước hạn 3 ngày làm việc, 1 ngày làm việc, đúng ngày hạn và vào mỗi ngày làm việc quá hạn. Chạy lặp trong cùng ngày không gửi trùng. Đây là cấu hình mặc định của đợt đầu.
- Hoạt động có khoảng ngày trùng với hoạt động khác của cùng CBDA chính hiển thị cảnh báo trên form; vẫn cho lưu để điều phối viên xử lý.

## Vai trò

- **Giám đốc/Quản lý dự án:** xem dashboard toàn đơn vị, theo dõi trễ hạn và thiếu báo cáo; hỗ trợ hoặc điều phối lại.
- **Điều phối viên:** gắn công văn đã phát hành, CBDA phụ trách và hoạt động; theo dõi Task và thông báo.
- **CBDA:** xem việc của mình, cập nhật trạng thái, tải báo cáo và hoàn thành Task.
- **Quản trị hệ thống:** gán vai trò `PROJECT_MANAGER`, `PROJECT_COORDINATOR`, `CBDA` cho tài khoản phù hợp và cấu hình thư viện SharePoint.

## Cách sử dụng

1. Người có vai trò Quản lý dự án/Điều phối viên mở **Hoạt động dự án → Tạo hoạt động**, chọn dự án, CBDA chính, điều phối viên, khoảng ngày, mục đích/kết quả và thông tin cần thiết.
2. Chọn công văn đi đã phát hành trong sổ Công văn của IHRMS, hoặc bổ sung công văn khi cập nhật hoạt động sau. Liên kết công văn tạo Task báo cáo; kiểm tra Task xuất hiện trong danh sách giao việc, đúng người và đúng hạn.
3. CBDA vào Giao việc của tôi, cập nhật tiến độ. Sau khi triển khai, tải báo cáo lên Task; mở tệp kiểm tra được rồi mới chuyển trạng thái Hoàn thành.
4. Quản lý/điều phối viên mở mục **Hoạt động dự án**, chọn tháng để xem tổng số hoạt động, Task hoàn tất, quá hạn, thiếu báo cáo và hoạt động chưa có Task.

### Luồng hồ sơ xin duyệt đề xuất/dự trù đã triển khai

1. CBDA hoàn thiện Excel theo mẫu công ty ở máy cá nhân, xuất **Đề xuất hoạt động (PDF)** và **Dự trù kinh phí (PDF)**, rồi tải đúng hai PDF trong **Đề xuất & dự trù**. IHRMS không yêu cầu tải Excel.
2. Điều phối viên kiểm tra hồ sơ, chọn tài khoản Giám đốc rồi mở thư nháp bằng Outlook. Người gửi tự kiểm tra From/To, thêm CC, tải và đính kèm hai PDF, gửi thư; sau đó xác nhận gửi trong IHRMS. Hệ thống không gửi SMTP tự động và không xác minh email đã đến.
3. Giám đốc mở **Duyệt & Xử lý → Duyệt đề xuất hoạt động** hoặc link email. Hàng chờ chỉ hiện hồ sơ `Submitted` được giao đúng tài khoản. Giám đốc xem PDF, phê duyệt hoặc yêu cầu chỉnh sửa kèm ý kiến.
4. Khi yêu cầu chỉnh sửa, thông báo IHRMS gửi tới người gửi, người tạo hồ sơ, CBDA và ĐPV (loại trùng); trạng thái/ý kiến hiển thị trong dashboard dưới hoạt động. Người nhận mở từ chuông hoặc trang Thông báo. Quyết định trước khi triển khai thông báo không được gửi ngược.
5. Dashboard **Hoạt động dự án** và lịch là menu độc lập cuối thanh điều hướng; hàng chờ duyệt vẫn nằm trong **Duyệt & Xử lý**. Danh sách hoạt động lọc theo tháng, nên phải chọn tháng có ngày hoạt động.

## Nhắc việc tự động trên Windows

Mã nguồn có lệnh `python src/manage.py send_activity_report_reminders`. Để lệnh chạy hằng ngày, IT cần đăng ký Windows Task Scheduler trên máy ứng dụng. Script `ops/scheduler/Run-ActivityReportReminders.ps1` dùng Python của `venv` trong thư mục dự án hoặc biến môi trường `IHRMS_PYTHON`, và ghi log dưới `Logs`.

Đề xuất cấu hình Scheduled Task: chạy mỗi ngày lúc 08:00; Action `powershell.exe -NoProfile -ExecutionPolicy Bypass -File "<đường-dẫn-dự-án>\ops\scheduler\Run-ActivityReportReminders.ps1"`; chạy bằng tài khoản dịch vụ có quyền đọc mã dự án, môi trường `.env` và kết nối SharePoint/SQL Server cần thiết. Sau khi tạo task, chạy thử thủ công một lần và xác nhận log cùng thông báo trong IHRMS. Script tự bỏ qua cuối tuần/ngày nghỉ.

## Trạng thái triển khai

- Đã có dashboard/lịch hoạt động riêng ở menu cuối; các trang tạo/chỉnh sửa hoạt động, bộ lọc và hiển thị trạng thái Task/báo cáo/proposal được triển khai. CBDA xem hoạt động được giao hoặc điều phối cho mình; vai trò Quản lý dự án/Điều phối viên có thể tạo/sửa theo quyền.
- Đã có hồ sơ đề xuất theo phiên bản, lưu hai PDF trong storage đã cấu hình; Điều phối viên soạn email Outlook thủ công; Giám đốc có hàng chờ duyệt đích danh; quyết định yêu cầu sửa/phê duyệt lưu lịch sử. Yêu cầu chỉnh sửa thông báo người gửi, người tạo, CBDA phụ trách và ĐPV; dashboard hiển thị trạng thái và nhận xét.
- Django migrations đã tạo bảng `tblActivity`, liên kết `tblTask.ActivityID` và cột tệp `tblTask.report_file` trong SQL Server database `qlhcns`. Liên kết công văn dùng `document.OfficialDispatch`.
- 14 kiểm thử mới cùng toàn bộ bộ kiểm thử được chọn (100 test) đạt trên SQLite test database tạm. `manage.py check`, `makemigrations --check --dry-run` và kiểm tra migration SQL Server đều đạt.
- Đã thử upload, đọc lại và xóa tệp giả qua cấu hình storage của `activity_reports`; SharePoint trả đúng thư mục `BaoCaoHoatDong`. Người dùng cần kiểm tra quy trình trên giao diện IHRMS với dữ liệu UAT.
- Còn mở: UAT phân vai CBDA/ĐPV/Giám đốc trên giao diện, kiểm thử một vòng upload hai PDF → gửi Outlook thật đến hộp thư nội bộ → yêu cầu chỉnh sửa → nhận thông báo ở cả tài khoản CBDA/ĐPV → gửi phiên bản sửa → phê duyệt; xác nhận đúng thư viện SharePoint cho hồ sơ proposal và report; đăng ký Task Scheduler khi ưu tiên vận hành; chốt lịch làm thứ Bảy nếu cần. Không tạo thông báo hồi tố cho quyết định cũ.
- Ghi lại kết quả và mọi thao tác tiếp theo tại [`PROJECT_WORK_LOG.md`](PROJECT_WORK_LOG.md).
