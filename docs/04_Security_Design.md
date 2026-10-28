# 04_Security_Design.md

# SECURITY DESIGN DOCUMENT

## Phạm vi áp dụng hiện tại

Mobile bổ sung API JSON opt-in `/api/mobile/v1/`, dùng session Django riêng qua bearer, Axes và quyền/dữ liệu hiện hành; không phải JWT. Phạm vi, thời hạn, lưu phiên native và push tùy chọn được mô tả tại [API mobile](mobile/API.md). Web vẫn dùng cookie/CSRF như trước.

Đối chiếu mã ngày 28/10/2026: đăng nhập dùng session Django, backend Axes và `ModelBackend`; quyền nghiệp vụ được kiểm phía máy chủ trong `apps/security/permissions.py` và bộ lọc dữ liệu trong `apps/security/data_access.py`. JWT, refresh token, Entra SSO và thông báo Teams bên dưới là thiết kế dự kiến, chưa phải chức năng đang hoạt động. Áp dụng [ma trận quyền hiện hành](10_RBAC_Permission_Matrix.md), [hướng dẫn review](Huong_Dan_Review_Du_An.md) và quy tắc tài khoản QA trong [AGENTS.md](../AGENTS.md). Không dùng quyền kiểm thử để mượn danh tính hoặc phiên người dùng thật. Các biện pháp cấu hình máy chủ phải được kiểm trên đúng đích theo [checklist go-live](Checklist_Go_Live_IHRMS.md); tài liệu thiết kế không thay cho bằng chứng kiểm thử.

## Project

Internal Administration & Human Resource Management System (IHRMS)

## Version

1.0

## Status

Approved

---

# 1. SECURITY OBJECTIVES

## Mục tiêu

Thiết kế hệ thống bảo mật đáp ứng:

- Bảo mật dữ liệu nhân sự
- Bảo mật dữ liệu lương
- Bảo mật dữ liệu hợp đồng
- Bảo mật dữ liệu cá nhân
- Kiểm toán toàn bộ hoạt động
- Quản lý truy cập theo vai trò
- Tích hợp Microsoft Entra ID
- Tuân thủ nguyên tắc tối thiểu quyền hạn

---

# 2. SECURITY PRINCIPLES

## SEC-001

Least Privilege

Người dùng chỉ được cấp đủ quyền cần thiết.

---

## SEC-002

Need To Know

Người dùng chỉ được xem dữ liệu liên quan.

---

## SEC-003

Separation Of Duties

Không cho phép một người thực hiện toàn bộ quy trình nhạy cảm.

---

## SEC-004

Accountability

Mọi thao tác phải truy vết được.

---

## SEC-005

Defense In Depth

Bảo vệ nhiều lớp.

---

## SEC-006

Zero Trust Internal Access

Mọi truy cập đều phải xác thực và phân quyền.

---

# 3. SECURITY ARCHITECTURE

```text
User

↓

Authentication

↓

Authorization

↓

Application Security

↓

Business Rules

↓

Database Security

↓

Audit Logging

↓

Monitoring
```

---

# 4. AUTHENTICATION DESIGN

## Authentication Types

### Local Authentication

```text
Username
Password
JWT
Refresh Token
```

---

### Microsoft Authentication

```text
Microsoft Entra ID

Single Sign On
```

---

# 5. LOGIN FLOW

```text
User

↓

Enter Credential

↓

Authentication Service

↓

Validate User

↓

Generate Access Token

↓

Generate Refresh Token

↓

Create Login Log

↓

Access Granted
```

---

# 6. TOKEN DESIGN

## Access Token

```text
JWT
```

Validity:

```text
8 Hours
```

---

## Refresh Token

Validity:

```text
30 Days
```

---

## Required Claims

```text
UserID

EmployeeID

Username

Role

DepartmentID

Permission List
```

---

# 7. PASSWORD POLICY

## Requirement

Minimum Length

```text
8 Characters
```

---

Must Contain

```text
Uppercase

Lowercase

Number

Special Character
```

---

Password Expiry

```text
90 Days
```

---

History

```text
Last 5 Passwords
```

Cannot Reuse.

---

Account Lock

```text
5 Failed Attempts
```

---

Lock Duration

```text
30 Minutes
```

---

# 8. SINGLE SIGN ON

## Identity Provider

```text
Microsoft Entra ID
```

---

## User Provisioning

First Login

↓

Create Local User Profile

↓

Assign Default Role

↓

Grant Access

---

# 9. AUTHORIZATION MODEL

## Model

RBAC

Role Based Access Control

---

# 10. SYSTEM ROLES

## Role 01

Super Admin

---

## Role 02

System Admin

---

## Role 03

HR Manager

---

## Role 04

HR Officer

---

## Role 05

Finance Officer

---

## Role 06

Department Manager

---

## Role 07

Employee

---

## Role 08

Director

---

# 11. DATA ACCESS RULES

## Employee

Can view:

```text
Own Profile
```

Only.

---

## Department Manager

Can view:

```text
Own Department
```

Only.

---

## HR

Can view:

```text
Employee Data
```

Across Organization.

---

## Director

Can view:

```text
Organization-Wide Data
```

---

# 12. SENSITIVE DATA CLASSIFICATION

## Public

No restriction.

Example:

```text
Department
Organization Structure
```

---

## Internal

Organization Access Only.

Example:

```text
Policies
Guidelines
```

---

## Confidential

Restricted Access.

Example:

```text
Performance Evaluation

Recruitment Evaluation
```

---

## Highly Confidential

Strict Access Control.

Example:

```text
Salary

Tax

Bank Information

Social Insurance

National ID
```

---

# 13. PAYROLL SECURITY

Payroll được xem là dữ liệu cấp cao nhất.

Chỉ các role sau được truy cập:

```text
Director

HR Manager

Finance Officer
```

---

Employee chỉ xem:

```text
Payslip của chính mình
```

---

Không cho phép:

```text
Department Manager
```

xem bảng lương người khác.

---

# 14. CONTRACT SECURITY

## Employee

Chỉ xem hợp đồng của chính mình.

---

## HR

Quản lý hợp đồng.

---

## Director

Xem toàn bộ hợp đồng.

---

# 15. DOCUMENT SECURITY

## Security Levels

Level 1

Public Internal

---

Level 2

Department

---

Level 3

Management

---

Level 4

Confidential

---

# 16. FILE ACCESS SECURITY

## Storage

```text
SharePoint

OneDrive
```

---

Application chỉ lưu:

```text
Metadata
```

---

Không lưu file vật lý trong SQL Server.

---

# 17. AUDIT LOG DESIGN

## Audit Scope

Bắt buộc với:

```text
Employee

Attendance

Leave

Payroll

Contract

Document

Task

KPI

Asset

Procurement
```

---

## Logged Events

```text
Create

Update

Delete

Approve

Reject

Cancel

Login

Logout

Export
```

---

# 18. AUDIT DATA STRUCTURE

## Audit Fields

```sql
AuditLogID

TableName

RecordID

ActionType

OldValue

NewValue

ChangedBy

ChangedDate

IPAddress
```

---

# 19. SESSION SECURITY

## Session Policy

Only One Active Session Per User.

---

New Login

↓

Old Session Invalidated

---

# 20. API SECURITY

## Authentication

```text
JWT Required
```

---

## Authorization

```text
Permission Validation Required
```

---

## Transport

```text
HTTPS Only
```

---

# 21. INPUT VALIDATION

## Rules

Validate:

```text
Required Fields

Data Type

Length

Range

Format
```

---

Protect Against:

```text
SQL Injection

Cross Site Scripting

Cross Site Request Forgery
```

---

# 22. DATABASE SECURITY

## Database Access

Application Only.

---

No Direct User Access.

---

## Service Account

Dedicated Service Account.

---

## Database Encryption

Encryption For:

```text
National ID

Tax Code

Bank Account

Insurance Number
```

---

# 23. BACKUP SECURITY

## Database Backup

Daily

---

## Retention

30 Days

---

## Monthly Backup

12 Months

---

# 24. RESTORE SECURITY

## Restore Authorization

Only:

```text
System Admin
```

---

## Restore Logging

Mandatory.

---

# 25. EXPORT SECURITY

## Export Formats

```text
Excel

PDF
```

---

## Export Logging

Mandatory.

---

Log:

```text
User

Date

Module

File Name
```

---

# 26. NOTIFICATION SECURITY

## Teams Notification

Cannot contain:

```text
Salary

Bank Account

National ID

Tax Data
```

---

## Email Notification

Sensitive Information Masked.

---

# 27. DATA RETENTION POLICY

## Employee

Permanent Retention.

---

## Payroll

10 Years.

---

## Contract

10 Years.

---

## Audit Logs

5 Years.

---

## Documents

5 Years Minimum.

---

# 28. ACCOUNT DEACTIVATION

Trigger:

```text
Employee Leave
```

---

Actions:

```text
Disable User

Revoke Tokens

Block Login
```

---

# 29. INCIDENT RESPONSE

## Incident Types

Unauthorized Access

Data Leakage

Malware

Account Compromise

Data Corruption

---

## Required Actions

Detect

↓

Contain

↓

Investigate

↓

Recover

↓

Report

---

# 30. SECURITY MONITORING

## Monitor Events

Failed Login

Permission Denied

Export Activity

Payroll Access

Mass Data Update

Role Change

---

# 31. COMPLIANCE REQUIREMENTS

System phải hỗ trợ:

```text
Audit

Investigation

Internal Control

Personnel Data Protection
```

---

# 32. SECURITY TESTING

## Mandatory Test Types

Authentication Test

Authorization Test

Session Test

Audit Log Test

Permission Test

API Security Test

Input Validation Test

Backup Restore Test

---

# 33. SECURITY GO-LIVE CHECKLIST

Before Production:

✅ HTTPS Enabled

✅ JWT Enabled

✅ Entra ID Configured

✅ Audit Log Enabled

✅ Backup Scheduled

✅ Restore Tested

✅ Permissions Verified

✅ Export Logging Verified

✅ Password Policy Active

✅ Sensitive Data Protected

---

# 34. SECURITY APPROVAL

Status:

Approved

Ready For:

- Backend Design
- API Design
- UI Design
- Development
- Testing


## Trạng thái bảo vệ dữ liệu trong mã nguồn (02/10/2026)

Các mục thiết kế ở trên là yêu cầu mục tiêu; không được coi toàn bộ đã triển khai.
Bản mã hiện tại có:

- URL tệp qua `/private-files/`, kiểm tra đăng nhập, vai trò và chủ/phạm vi bản ghi trước khi đọc đĩa hoặc Graph; bản ghi đã xóa bị từ chối. Tệp trả dạng download, sandbox và no-store. Không trả URL trực tiếp SharePoint.
- Django không phục vụ `/media/`, kể cả DEBUG. IIS/reverse proxy phải bỏ virtual directory/alias phục vụ media và đặt tệp ngoài web root; quyền đĩa chỉ cấp service account. Bảo vệ trong Django không chặn được alias độc lập ở IIS.
- SYS_ADMIN không sửa vai trò, liên kết nhân viên, superuser/staff, group hoặc permission; không đổi mật khẩu tài khoản đặc quyền. Chỉ superuser thực sự được quản lý phân quyền. CCCD/MST/BHXH không xuất hiện trong Admin Employee cho SYS_ADMIN/DEPT_MANAGER.
- Thao tác Admin xóa/khôi phục kiểm tra quyền từng bản ghi trong transaction, bao gồm kỳ lương Locked. Action tạo Task hoạt động yêu cầu quyền sửa.
- Xuất nhân sự/hợp đồng yêu cầu quyền riêng; công văn xuất theo cùng phạm vi xem và độ mật. Chuỗi trong Excel được ghi dạng text.
- Đăng nhập Portal/Admin dùng django-axes, 5 lần sai theo username khóa 30 phút; IP có ngưỡng riêng mặc định 50 (`AXES_IP_FAILURE_LIMIT`), tránh 5 lần sai của một tài khoản làm khóa cả văn phòng. Ngưỡng IP vẫn chặn dò nhiều tài khoản; chỉ tin header IP từ proxy đã cấu hình tin cậy, không nhận header tùy ý. Đăng nhập đúng chỉ xóa bộ đếm của username đó, giữ các tài khoản khác trên cùng IP; không kéo dài thời gian khóa khi thử trong lúc khóa.
- Phiên không thao tác hết hạn sau SESSION_IDLE_TIMEOUT (mặc định 1800 giây); nội dung đã đăng nhập no-store; cookie HttpOnly/SameSite; APP_ENV=production từ chối DEBUG, thiếu HTTPS, key yếu hoặc wildcard host. Kết nối SQL Server ở production ép Encrypt=yes;TrustServerCertificate=no; cần chứng chỉ server hợp lệ.
- SecurityEvent lưu metadata login/logout, tải tệp và xuất dữ liệu, không lưu giá trị nhạy cảm/tên tệp/credentials. Admin chỉ đọc nhật ký. Đây chưa phải audit bất biến: DBA vẫn có quyền database.
- Lỗi nghiệp vụ ghi loại exception và ID; handler logging trong DEBUG=False bỏ payload/traceback exception để tránh ghi SQL/Graph chứa bí mật.
- Dependency đã nâng và quét lỗ hổng đã biết; phải quét lại theo mỗi bản phát hành.

**Chưa được xác nhận/triển khai đầy đủ:** mã hóa cấp trường CCCD/MST/BHXH/lương (các trường vẫn plaintext trong database), SQL Server TLS/TDE và backup encryption, quản lý/luân chuyển khóa, MFA/SSO Entra, chính sách một phiên hoạt động, audit bất biến và pentest trên máy chủ thực. Không tự đổi kiểu trường dữ liệu đang chạy để tránh mất uniqueness/truy vấn hoặc khóa dữ liệu khi chưa có thiết kế khóa và migration khôi phục.

Trước production: DBA xác nhận TLS và mã hóa database/backup, kiểm thử khôi phục có khóa; IT bật HTTPS/MFA, rà ACL SharePoint và service account tối thiểu, loại bỏ raw media alias. IIS phải thay thế header X-Forwarded-Proto từ client và chặn truy cập trực tiếp backend HTTP.
Chi tiết kiểm chứng và các bước triển khai nằm tại [PROJECT_WORK_LOG.md](PROJECT_WORK_LOG.md).
