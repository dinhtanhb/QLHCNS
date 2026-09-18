BUSINESS REQUIREMENT DOCUMENT (MASTER VERSION)

Project: Internal Administration & Human Resource Management System (IHRMS)
 Version: 1.0
 Status: Approved for Architecture Design
 Scope: Internal Administration, Human Resource, Recruitment, Attendance, Payroll, Task, KPI, Asset, Procurement, Document Management, Microsoft 365 Integration

1. EXECUTIVE SUMMARY

IHRMS là hệ thống quản trị nội bộ tập trung phục vụ toàn bộ hoạt động hành chính, nhân sự và vận hành của công ty.

Mục tiêu là thay thế các quy trình thủ công đang được thực hiện bằng:

Excel
Email
Word
File chia sẻ rời rạc
Teams chat
Các biểu mẫu giấy

thành một nền tảng quản lý tập trung duy nhất.

Hệ thống trở thành nguồn dữ liệu chính thức của doanh nghiệp đối với:

Nhân sự
Tuyển dụng
Chấm công
Tính lương
Công việc
KPI
Hợp đồng
Văn bản
Tài sản
Mua sắm
2. BUSINESS OBJECTIVES
BO-01

Chuẩn hóa toàn bộ dữ liệu nhân sự.

BO-02

Số hóa toàn bộ quy trình hành chính.

BO-03

Tự động hóa các phê duyệt nội bộ.

BO-04

Tăng khả năng theo dõi KPI và tiến độ công việc.

BO-05

Giảm phụ thuộc vào Excel.

BO-06

Tăng khả năng kiểm toán dữ liệu.

BO-07

Tạo Dashboard điều hành cho Ban Giám đốc.

BO-08

Tích hợp Microsoft 365 để tạo môi trường làm việc thống nhất.

3. STAKEHOLDERS
Nhóm Điều hành
Director

Mục tiêu:

Theo dõi tổ chức
Theo dõi nhân sự
Theo dõi KPI
Theo dõi hiệu quả vận hành
Nhóm Nhân sự
HR Manager

Mục tiêu:

Quản lý toàn bộ nhân sự
Tuyển dụng
Hợp đồng
Chính sách nhân sự
HR Officer

Mục tiêu:

Thực thi quy trình
Cập nhật dữ liệu
Theo dõi hồ sơ
Nhóm Quản lý
Department Manager

Mục tiêu:

Quản lý nhân viên thuộc phòng
Phân công công việc
Đánh giá KPI
Nhóm Nhân viên
Employee

Mục tiêu:

Cập nhật thông tin cá nhân
Xin nghỉ phép
Xem công
Xem lương
Theo dõi công việc
Nhóm Hỗ trợ
IT Administrator

Mục tiêu:

Quản trị hạ tầng
Bảo mật
Vận hành hệ thống
Nhóm Tài chính
Finance Officer

Mục tiêu:

Quản lý bảng lương
Thanh toán
Mua sắm
4. BUSINESS FUNCTION MAP
Nhóm Quản trị tổ chức
Organization Management
Nhóm Nhân sự
Employee Management
Recruitment
Attendance
Leave
Payroll
Contract
Nhóm Vận hành
Task Management
KPI Management
Asset Management
Procurement
Nhóm Hành chính
Document Management
Nhóm Điều hành
Dashboard & Reporting
Nhóm Tích hợp
Microsoft 365 Integration
5. FUNCTIONAL REQUIREMENTS
MODULE 01 – ORGANIZATION MANAGEMENT
Mục tiêu

Quản lý cơ cấu tổ chức của công ty.

Chức năng
FR-ORG-001

Quản lý công ty.

FR-ORG-002

Quản lý đơn vị trực thuộc.

FR-ORG-003

Quản lý phòng ban.

FR-ORG-004

Quản lý tổ nhóm.

FR-ORG-005

Quản lý chức danh.

FR-ORG-006

Quản lý chức vụ.

FR-ORG-007

Quản lý sơ đồ tổ chức.

FR-ORG-008

Quản lý quan hệ báo cáo.

FR-ORG-009

Quản lý quản lý trực tiếp.

FR-ORG-010

Tra cứu cơ cấu tổ chức.

MODULE 02 – HUMAN RESOURCE MANAGEMENT
Hồ sơ cá nhân
FR-HR-001

Tạo hồ sơ nhân viên.

FR-HR-002

Cập nhật hồ sơ nhân viên.

FR-HR-003

Quản lý CCCD.

FR-HR-004

Quản lý MST cá nhân.

FR-HR-005

Quản lý BHXH.

FR-HR-006

Quản lý thông tin ngân hàng.

FR-HR-007

Quản lý địa chỉ liên hệ.

FR-HR-008

Quản lý liên hệ khẩn cấp.

Học vấn
FR-HR-009

Quản lý trình độ học vấn.

FR-HR-010

Quản lý bằng cấp.

FR-HR-011

Quản lý chứng chỉ.

FR-HR-012

Quản lý đào tạo.

Biến động nhân sự
FR-HR-013

Bổ nhiệm.

FR-HR-014

Miễn nhiệm.

FR-HR-015

Điều chuyển.

FR-HR-016

Tăng lương.

FR-HR-017

Khen thưởng.

FR-HR-018

Kỷ luật.

FR-HR-019

Nghỉ việc.

FR-HR-020

Theo dõi lịch sử nhân sự.

MODULE 03 – RECRUITMENT
Quy trình tuyển dụng
FR-REC-001

Tạo yêu cầu tuyển dụng.

FR-REC-002

Phê duyệt tuyển dụng.

FR-REC-003

Quản lý vị trí tuyển dụng.

FR-REC-004

Quản lý đợt tuyển dụng.

FR-REC-005

Quản lý ứng viên.

FR-REC-006

Lưu CV ứng viên.

FR-REC-007

Đặt lịch phỏng vấn.

FR-REC-008

Đánh giá ứng viên.

FR-REC-009

Tạo Offer.

FR-REC-010

Onboarding.

MODULE 04 – ATTENDANCE MANAGEMENT
FR-ATT-001

Check In.

FR-ATT-002

Check Out.

FR-ATT-003

Quản lý ca làm việc.

FR-ATT-004

Quản lý lịch làm việc.

FR-ATT-005

Tăng ca.

FR-ATT-006

Làm bù.

FR-ATT-007

Công tác.

FR-ATT-008

Điều chỉnh công.

FR-ATT-009

Khóa dữ liệu công.

FR-ATT-010

Tổng hợp công tháng.

MODULE 05 – LEAVE MANAGEMENT
FR-LEA-001

Nghỉ phép năm.

FR-LEA-002

Nghỉ bệnh.

FR-LEA-003

Nghỉ không lương.

FR-LEA-004

Nghỉ việc riêng.

FR-LEA-005

Nghỉ thai sản.

FR-LEA-006

Tạo đơn nghỉ phép.

FR-LEA-007

Phê duyệt nghỉ phép.

FR-LEA-008

Tự động trừ phép.

FR-LEA-009

Theo dõi số phép còn lại.

FR-LEA-010

Báo cáo nghỉ phép.

MODULE 06 – PAYROLL
Thành phần thu nhập
FR-PAY-001

Lương cơ bản.

FR-PAY-002

Phụ cấp.

FR-PAY-003

Trách nhiệm.

FR-PAY-004

Điện thoại.

FR-PAY-005

Xăng xe.

FR-PAY-006

Công tác.

Khấu trừ
FR-PAY-007

BHXH.

FR-PAY-008

BHYT.

FR-PAY-009

BHTN.

FR-PAY-010

Thuế TNCN.

FR-PAY-011

Khấu trừ khác.

Tính lương
FR-PAY-012

Tính lương theo công.

FR-PAY-013

Tính OT.

FR-PAY-014

Tính nghỉ không lương.

FR-PAY-015

Khóa bảng lương.

FR-PAY-016

Phát hành phiếu lương.

FR-PAY-017

Xuất bảng lương.

MODULE 07 – CONTRACT MANAGEMENT
FR-CON-001

Hợp đồng thử việc.

FR-CON-002

Hợp đồng xác định thời hạn.

FR-CON-003

Hợp đồng không xác định thời hạn.

FR-CON-004

Quản lý phụ lục.

FR-CON-005

Gia hạn hợp đồng.

FR-CON-006

Theo dõi hiệu lực.

FR-CON-007

Cảnh báo hết hạn.

FR-CON-008

Lưu file hợp đồng.

MODULE 08 – DOCUMENT MANAGEMENT
FR-DOC-001

Quản lý văn bản đến.

FR-DOC-002

Quản lý văn bản đi.

FR-DOC-003

Quản lý quyết định.

FR-DOC-004

Quản lý thông báo.

FR-DOC-005

Quản lý quy trình.

FR-DOC-006

Quản lý biểu mẫu.

FR-DOC-007

Quản lý hướng dẫn.

FR-DOC-008

Quản lý tài liệu ISO.

FR-DOC-009

Version Control.

FR-DOC-010

Document Approval.

MODULE 09 – TASK MANAGEMENT
FR-TASK-001

Tạo công việc.

FR-TASK-002

Giao việc.

FR-TASK-003

Giao nhiều người.

FR-TASK-004

Checklist.

FR-TASK-005

Comment.

FR-TASK-006

Attachment.

FR-TASK-007

Deadline.

FR-TASK-008

Priority.

FR-TASK-009

Kanban.

FR-TASK-010

Calendar.

FR-TASK-011

Gantt.

FR-TASK-012

Theo dõi quá hạn.

MODULE 10 – KPI MANAGEMENT
FR-KPI-001

KPI công ty.

FR-KPI-002

KPI phòng ban.

FR-KPI-003

KPI cá nhân.

FR-KPI-004

Target.

FR-KPI-005

Actual.

FR-KPI-006

Achievement.

FR-KPI-007

Scoring.

FR-KPI-008

Ranking.

FR-KPI-009

Đánh giá KPI.

FR-KPI-010

Báo cáo KPI.

MODULE 11 – ASSET MANAGEMENT
FR-AST-001

Danh mục tài sản.

FR-AST-002

Tiếp nhận tài sản.

FR-AST-003

Cấp phát tài sản.

FR-AST-004

Thu hồi tài sản.

FR-AST-005

Bảo trì tài sản.

FR-AST-006

Thanh lý tài sản.

FR-AST-007

Kiểm kê tài sản.

MODULE 12 – PROCUREMENT
FR-PRO-001

Tạo đề nghị mua sắm.

FR-PRO-002

Phê duyệt mua sắm.

FR-PRO-003

Theo dõi báo giá.

FR-PRO-004

Theo dõi mua hàng.

FR-PRO-005

Bàn giao tài sản.

FR-PRO-006

Đóng yêu cầu.

MODULE 13 – DASHBOARD & REPORTING
Director Dashboard
Headcount
Turnover
Recruitment
Payroll
KPI
Tasks
HR Dashboard
Recruitment
Leave
Attendance
Contract
Manager Dashboard
Team KPI
Team Task
Team Attendance
MODULE 14 – MICROSOFT 365 INTEGRATION
FR-M365-001

SSO bằng Entra ID.

FR-M365-002

Gửi email Outlook.

FR-M365-003

Thông báo Teams.

FR-M365-004

Đồng bộ SharePoint.

FR-M365-005

Lưu file lên OneDrive.

FR-M365-006

Reminder tự động.

6. WORKFLOWS
Leave Workflow

Employee
 ↓
 Department Manager
 ↓
 HR
 ↓
 Approved / Rejected

Recruitment Workflow

Recruitment Request
 ↓
 Approval
 ↓
 Posting
 ↓
 Application
 ↓
 Interview
 ↓
 Offer
 ↓
 Onboarding

Procurement Workflow

Employee
 ↓
 Department Manager
 ↓
 Finance
 ↓
 Director
 ↓
 Purchasing
 ↓
 Delivery
 ↓
 Close

Task Workflow

Backlog
 ↓
 To Do
 ↓
 In Progress
 ↓
 Review
 ↓
 Approved
 ↓
 Done

7. BUSINESS RULES
BR-001

Một nhân viên chỉ có một mã nhân viên duy nhất.

BR-002

Một nhân viên chỉ thuộc một phòng ban tại một thời điểm.

BR-003

Mọi thay đổi nhân sự phải lưu lịch sử.

BR-004

Đơn nghỉ phép phải được phê duyệt trước ngày nghỉ.

BR-005

Bảng lương sau khi khóa không được chỉnh sửa trực tiếp.

BR-006

Hợp đồng hết hạn phải cảnh báo trước tối thiểu 30 ngày.

BR-007

Tài liệu phát hành phải có phiên bản.

BR-008

Mọi công việc phải có người chịu trách nhiệm.

BR-009

Mọi KPI phải có Target và Period.

BR-010

Mọi giao dịch quan trọng phải lưu Audit Log.

8. REPORTING REQUIREMENTS
HR Reports
Employee Headcount
Employee Movement
Leave Summary
Attendance Summary
Contract Expiration
Payroll Reports
Monthly Payroll
Payroll Detail
Tax Summary
Recruitment Reports
Recruitment Pipeline
Interview Result
Time To Hire
Task Reports
Task Progress
Overdue Tasks
Team Workload
KPI Reports
Company KPI
Department KPI
Employee KPI
Asset Reports
Asset Allocation
Asset Maintenance
Asset Inventory
9. DATA GOVERNANCE REQUIREMENTS
Audit Log bắt buộc.
Soft Delete bắt buộc.
Approval History bắt buộc.
Version Control bắt buộc.
Backup hàng ngày.
Restore có kiểm thử.
Phân loại dữ liệu nhạy cảm.
Nhật ký đăng nhập.
Nhật ký thay đổi dữ liệu.
Chính sách lưu trữ tài liệu tối thiểu 05 năm.
10. SUCCESS CRITERIA

Hệ thống được chấp nhận khi:

100% module trong phạm vi hoạt động.
100% workflow chính hoạt động.
Tích hợp Microsoft 365 hoạt động ổn định.
UAT đạt tối thiểu 95%.
Không còn lỗi Critical hoặc High.
Dữ liệu nhân sự được quản lý tập trung.
Hệ thống vận hành ổn định trên máy chủ công ty.