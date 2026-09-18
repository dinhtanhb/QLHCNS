# PROJECT CHARTER

## 1. THÔNG TIN DỰ ÁN

### Tên dự án

Hệ thống Quản lý Hành chính - Nhân sự Nội bộ (Internal Administration & Human Resource Management System)

### Tên viết tắt

IHRMS

### Phiên bản

v1.0

### Trạng thái

Approved

### Ngày khởi tạo

17/09/2026

### Đơn vị sử dụng

Toàn bộ công ty

### Loại dự án

Phần mềm quản lý nội bộ doanh nghiệp

### Mô hình triển khai

On-Premise

### Hạ tầng triển khai

Máy chủ vật lý nội bộ công ty

---

# 2. TẦM NHÌN DỰ ÁN

Xây dựng một hệ thống quản trị nội bộ tập trung, thống nhất toàn bộ hoạt động hành chính, nhân sự, tuyển dụng, chấm công, tính lương, quản lý công việc, KPI, tài sản và tài liệu doanh nghiệp trên một nền tảng duy nhất.

Hệ thống đóng vai trò là nguồn dữ liệu trung tâm phục vụ công tác quản trị nhân sự, vận hành nội bộ và ra quyết định của Ban Giám đốc.

---

# 3. SỨ MỆNH DỰ ÁN

Thay thế các quy trình thủ công đang vận hành bằng:

- Excel
- Email
- File lưu trữ phân tán
- Trao đổi qua nhiều kênh

thành một hệ thống tập trung có khả năng:

- Chuẩn hóa quy trình
- Kiểm soát dữ liệu
- Giảm sai sót
- Tăng tính minh bạch
- Tăng khả năng theo dõi
- Hỗ trợ ra quyết định

---

# 4. MỤC TIÊU CHIẾN LƯỢC

## Mục tiêu quản trị

- Chuẩn hóa dữ liệu nhân sự.
- Chuẩn hóa dữ liệu tổ chức.
- Chuẩn hóa hồ sơ nhân viên.
- Chuẩn hóa quy trình nội bộ.

## Mục tiêu vận hành

- Số hóa quy trình nghỉ phép.
- Số hóa quy trình tuyển dụng.
- Số hóa quy trình chấm công.
- Số hóa quy trình tính lương.
- Số hóa quy trình giao việc.
- Số hóa quy trình mua sắm.

## Mục tiêu quản lý

- Theo dõi KPI.
- Theo dõi tiến độ công việc.
- Theo dõi deadline.
- Theo dõi hợp đồng.
- Theo dõi tài sản.

## Mục tiêu dữ liệu

- Một nguồn dữ liệu duy nhất.
- Hạn chế dữ liệu trùng lặp.
- Lưu vết toàn bộ thay đổi.
- Đảm bảo khả năng kiểm toán.

---

# 5. PHẠM VI DỰ ÁN

## Nằm trong phạm vi

### Module 01

Organization Management

### Module 02

Human Resource Management

### Module 03

Recruitment Management

### Module 04

Attendance Management

### Module 05

Leave Management

### Module 06

Payroll Management

### Module 07

Contract Management

### Module 08

Document Management

### Module 09

Task Management

### Module 10

KPI Management

### Module 11

Asset Management

### Module 12

Procurement Management

### Module 13

Dashboard & Reporting

### Module 14

Microsoft 365 Integration

---

# 6. NGOÀI PHẠM VI

Hệ thống không bao gồm:

- Quản lý nhà tài trợ.
- Quản lý Grant.
- Quản lý ngân sách tài trợ.
- Quản lý hoạt động dự án phát triển cộng đồng.
- Quản lý MEL nghiệp vụ dự án.
- Quản lý M&E.
- Quản lý tài chính kế toán chuyên sâu.
- Quản lý CRM.
- Quản lý khách hàng.
- Quản lý bán hàng.

---

# 7. CƠ CẤU TỔ CHỨC ÁP DỤNG

## Ban Giám Đốc

Quản lý điều hành.

## Hành Chính Nhân Sự

Quản lý nhân sự và hành chính.

## Kế Toán

Quản lý nghiệp vụ lương và thanh toán.

## Chương Trình

Quản lý hoạt động chuyên môn.

## MEL

Theo dõi và đánh giá nội bộ.

## IT

Quản trị hệ thống.

## Văn Phòng Dự Án

Thực hiện vận hành dự án.

## Văn Phòng Trung Tâm

Điều phối hoạt động toàn tổ chức.

---

# 8. ĐỐI TƯỢNG NGƯỜI DÙNG

## Director

Ban Giám đốc.

## HR Manager

Quản lý nhân sự.

## HR Officer

Chuyên viên nhân sự.

## Finance Officer

Kế toán.

## Department Manager

Trưởng phòng.

## Employee

Nhân viên.

## IT Administrator

Quản trị hệ thống.

## System Administrator

Quản trị toàn hệ thống.

---

# 9. MỤC TIÊU KPI DỰ ÁN

## Nhân sự

100% hồ sơ nhân viên được quản lý tập trung.

## Nghỉ phép

100% phiếu nghỉ phép thực hiện trên hệ thống.

## Chấm công

100% dữ liệu công được ghi nhận điện tử.

## Tính lương

100% bảng lương được tạo từ hệ thống.

## Tuyển dụng

100% hồ sơ ứng viên được lưu trữ tập trung.

## Công việc

100% công việc có deadline được theo dõi trên hệ thống.

## Tài liệu

100% tài liệu chính thức lưu trên SharePoint.

---

# 10. KIẾN TRÚC HỆ THỐNG CHÍNH THỨC

## Backend

Python 3.12

Django 5

Django REST Framework

## Frontend

Bootstrap 5

AdminLTE 3

HTML5

CSS3

JavaScript

AJAX

jQuery

## Database

Microsoft SQL Server

## Authentication

JWT

Microsoft Entra ID

Single Sign-On

## Authorization

RBAC

## File Storage

SharePoint

OneDrive

## Messaging

Microsoft Outlook

Microsoft Teams

## Web Server

IIS

## Operating System

Windows Server

## Deployment

On-Premise

## Architecture Type

Modular Monolith

---

# 11. KIẾN TRÚC DỮ LIỆU

## Master Data

- Employee
- Department
- Position
- Job Title
- Leave Type
- Contract Type
- Asset Type
- KPI Type
- Task Status
- Document Category

## Transaction Data

- Attendance
- Leave Request
- Payroll
- Recruitment
- Interview
- Contract
- Task
- KPI Result
- Asset Allocation
- Procurement Request

## Reference Data

- Province
- District
- Bank
- Degree
- Certificate
- Organization Unit

---

# 12. YÊU CẦU BẢO MẬT

## Cấp độ bảo mật

Enterprise Internal

## Xác thực

JWT

Refresh Token

SSO

## Phân quyền

Role Based Access Control

## Nhật ký hệ thống

Bắt buộc.

## Audit Log

Bắt buộc.

## Soft Delete

Bắt buộc.

## Mã hóa

Thông tin nhạy cảm phải được mã hóa.

---

# 13. NGUYÊN TẮC THIẾT KẾ

## Nguyên tắc 1

Dữ liệu nhập một lần sử dụng nhiều lần.

## Nguyên tắc 2

Không lưu dữ liệu trùng lặp.

## Nguyên tắc 3

Mọi giao dịch phải lưu lịch sử thay đổi.

## Nguyên tắc 4

Mọi nghiệp vụ phải hỗ trợ kiểm toán.

## Nguyên tắc 5

Mọi workflow phải có khả năng phê duyệt.

## Nguyên tắc 6

Tất cả tài liệu phải hỗ trợ phân quyền.

## Nguyên tắc 7

Toàn bộ hệ thống hỗ trợ mở rộng đến tối thiểu 200 người dùng.

---

# 14. TIÊU CHUẨN ĐẶT TÊN

## Database

Tiếng Anh.

## API

Tiếng Anh.

## Source Code

Tiếng Anh.

## Business Display

Tiếng Việt.

## Reports

Tiếng Việt.

## Forms

Tiếng Việt.

---

# 15. TIÊU CHUẨN KIỂM THỬ

## Unit Test

Bắt buộc.

## Integration Test

Bắt buộc.

## User Acceptance Test

Bắt buộc.

## Security Test

Bắt buộc.

## Performance Test

Bắt buộc.

---

# 16. TIÊU CHUẨN TRIỂN KHAI

## Môi trường

Development

Testing

Production

## Version Control

Git

## Backup

Hàng ngày.

## Restore

Theo quy trình chuẩn.

## Monitoring

Bắt buộc.

## Logging

Bắt buộc.

---

# 17. TIÊU CHUẨN THÀNH CÔNG DỰ ÁN

Dự án được xem là hoàn thành khi đáp ứng đồng thời các tiêu chí sau.

## 17.1 Tiêu chuẩn Nghiệp vụ

### Tổ chức

- Quản lý được cơ cấu tổ chức.
- Quản lý được phòng ban.
- Quản lý được chức danh.
- Quản lý được quản lý trực tiếp.
- Hiển thị đúng sơ đồ tổ chức.

### Nhân sự

- Quản lý đầy đủ hồ sơ nhân viên.
- Quản lý lịch sử công tác.
- Quản lý quá trình bổ nhiệm.
- Quản lý quá trình điều chuyển.
- Quản lý quá trình tăng lương.
- Quản lý hồ sơ đính kèm.

### Tuyển dụng

- Quản lý nhu cầu tuyển dụng.
- Quản lý ứng viên.
- Quản lý phỏng vấn.
- Quản lý Offer.
- Quản lý tiếp nhận nhân viên.

### Chấm công

- Ghi nhận công hàng ngày.
- Quản lý tăng ca.
- Quản lý công tác.
- Quản lý làm bù.
- Quản lý điều chỉnh công.

### Nghỉ phép

- Tạo đơn nghỉ phép.
- Phê duyệt nhiều cấp.
- Theo dõi số phép còn lại.
- Tổng hợp báo cáo nghỉ phép.

### Tiền lương

- Tính lương chính xác.
- Hỗ trợ phụ cấp.
- Hỗ trợ khấu trừ.
- Hỗ trợ thuế TNCN.
- Hỗ trợ BHXH/BHYT/BHTN.
- Xuất bảng lương.
- Xuất phiếu lương.

### Hợp đồng

- Quản lý hợp đồng lao động.
- Quản lý phụ lục.
- Quản lý gia hạn.
- Cảnh báo hợp đồng sắp hết hạn.

### Văn bản

- Quản lý văn bản đến.
- Quản lý văn bản đi.
- Quản lý quyết định.
- Quản lý quy trình.
- Quản lý biểu mẫu.
- Quản lý phiên bản tài liệu.

### Công việc

- Tạo công việc.
- Phân công công việc.
- Theo dõi tiến độ.
- Theo dõi deadline.
- Quản lý checklist.
- Quản lý bình luận.
- Quản lý file đính kèm.

### KPI

- Thiết lập KPI.
- Theo dõi KPI.
- Đánh giá KPI.
- Chấm điểm KPI.
- Báo cáo KPI.

### Tài sản

- Quản lý tài sản.
- Cấp phát tài sản.
- Thu hồi tài sản.
- Bảo trì tài sản.
- Thanh lý tài sản.

### Mua sắm

- Tạo đề nghị mua sắm.
- Phê duyệt đề nghị.
- Theo dõi thực hiện.
- Bàn giao tài sản.

---

## 17.2 Tiêu chuẩn Kỹ thuật

### Ứng dụng

- Không có lỗi nghiêm trọng (Critical).
- Không có lỗi mức cao (High) trước Go-Live.
- Toàn bộ chức năng hoạt động ổn định.

### Cơ sở dữ liệu

- Toàn bộ migration thực hiện thành công.
- Không có lỗi khóa ngoại.
- Không có lỗi dữ liệu trùng ngoài quy định.

### API

- Tất cả API hoạt động chính xác.
- API trả đúng dữ liệu.
- Phân quyền API chính xác.

### Bảo mật

- JWT hoạt động ổn định.
- SSO Microsoft 365 hoạt động ổn định.
- RBAC hoạt động đúng.
- Audit Log ghi nhận đầy đủ.

---

## 17.3 Tiêu chuẩn Hiệu năng

### Thời gian phản hồi

Danh sách dữ liệu:

< 3 giây

Màn hình Dashboard:

< 5 giây

Tra cứu thông tin:

< 3 giây

### Đồng thời

Hệ thống hỗ trợ tối thiểu:

- 50 người dùng đồng thời.

Khả năng mở rộng:

- 200 người dùng.

---

## 17.4 Tiêu chuẩn Tích hợp

### Microsoft Outlook

- Gửi email thành công.
- Gửi thông báo workflow thành công.

### Microsoft Teams

- Gửi thông báo công việc.
- Gửi thông báo phê duyệt.
- Gửi thông báo quá hạn.

### SharePoint

- Lưu tài liệu thành công.
- Tìm kiếm tài liệu thành công.

### OneDrive

- Lưu file đính kèm thành công.
- Truy xuất file đính kèm thành công.

### Entra ID

- Đăng nhập một lần (SSO).
- Đồng bộ tài khoản người dùng.

---

## 17.5 Tiêu chuẩn Kiểm thử

### Unit Test

Coverage tối thiểu:

80%

### Integration Test

100% luồng nghiệp vụ chính được kiểm thử.

### UAT

Tối thiểu:

95% Test Case đạt kết quả Pass.

---

## 17.6 Tiêu chuẩn Golive

Hệ thống được phép Golive khi:

- Ban Giám Đốc nghiệm thu.
- Hành Chính Nhân Sự nghiệm thu.
- Kế toán nghiệm thu.
- IT nghiệm thu.
- Tất cả lỗi Critical và High đã được xử lý.
- Dữ liệu ban đầu đã được nhập đầy đủ.
- Backup và Restore được kiểm chứng thành công.
- Tài liệu hướng dẫn sử dụng được bàn giao.

---

## 17.7 Tiêu chuẩn Thành công Cuối cùng

Sau 03 tháng vận hành:

- 100% nhân viên sử dụng hệ thống.
- 100% nghỉ phép thực hiện trên hệ thống.
- 100% chấm công thực hiện trên hệ thống.
- 100% phiếu lương phát hành từ hệ thống.
- 100% công việc có deadline được theo dõi trên hệ thống.
- 100% hồ sơ nhân sự được quản lý tập trung.
- 100% tài liệu nội bộ được lưu trữ trên SharePoint/OneDrive.

Dự án được xác nhận hoàn thành và chuyển sang giai đoạn vận hành chính thức.