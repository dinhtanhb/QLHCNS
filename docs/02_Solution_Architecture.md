# 02_Solution_Architecture.md

# SOLUTION ARCHITECTURE DOCUMENT

## Phạm vi áp dụng hiện tại

Đối chiếu mã ngày 28/10/2026: ứng dụng là Django modular monolith trong `src/`, portal dùng Django Templates và CSS token/component; Admin dùng Jazzmin khi có cài đặt. Đăng nhập hiện hành dùng session Django và Axes, không dùng JWT/Entra SSO. SharePoint dùng Microsoft Graph khi được cấu hình; Outlook mở bản nháp do người dùng tự gửi. OneDrive, Teams và SSO chưa được triển khai. Máy chủ SIT mục tiêu dùng Waitress sau reverse proxy HTTPS; chưa có xác nhận vận hành trên máy chủ đích. Những sơ đồ/công nghệ tích hợp phía dưới là thiết kế ban đầu, không chứng minh thành phần đã có trong mã. Xem [baseline hiện hành](99_Architecture_Baseline.md), [runbook SIT](Server_Trial_Readiness_2026-09-27.md) và [nhật ký](PROJECT_WORK_LOG.md) trước khi triển khai.

## Project

Internal Administration & Human Resource Management System (IHRMS)

## Version

1.0

## Status

Approved

---

# 1. ARCHITECTURE OVERVIEW

## Mục tiêu kiến trúc

Thiết kế hệ thống quản lý hành chính và nhân sự nội bộ:

- Dễ bảo trì
- Dễ mở rộng
- Bảo mật
- Ổn định
- Hiệu năng tốt
- Phù hợp quy mô 30-200 nhân sự
- Triển khai trên máy chủ vật lý công ty

---

# 2. ARCHITECTURE PRINCIPLES

## AP-01

Single Source Of Truth

Mỗi dữ liệu chỉ tồn tại một nguồn dữ liệu chính thức.

---

## AP-02

Modular Monolith

Hệ thống được chia module nghiệp vụ rõ ràng.

Tất cả chạy trong một ứng dụng Django duy nhất.

---

## AP-03

Separation Of Concerns

Tách biệt:

- Presentation
- API
- Service
- Repository
- Database

---

## AP-04

Security First

Bảo mật được tích hợp từ đầu.

---

## AP-05

Auditability

Mọi giao dịch nghiệp vụ phải truy vết được.

---

## AP-06

Microsoft 365 Centric

Microsoft 365 đóng vai trò nền tảng tích hợp chính.

---

# 3. SYSTEM ARCHITECTURE

## Logical Architecture

```text
┌────────────────────────────┐
│        End Users           │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│       Web Browser          │
└────────────┬───────────────┘
             │ HTTPS
             ▼
┌────────────────────────────┐
│            IIS             │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│        Django App          │
│      (Modular Monolith)    │
└────────────┬───────────────┘
             │
   ┌─────────┴─────────┐
   ▼                   ▼
SQL Server       Microsoft 365
                    │
     ┌──────────────┼──────────────┐
     ▼              ▼              ▼
 SharePoint      OneDrive      Teams
```

---

# 4. PHYSICAL ARCHITECTURE

## Environment

### Production

```text
Physical Server

Windows Server

IIS

Django Application

SQL Server

Microsoft 365 Integration
```

---

## Development

```text
Developer PC

VS Code

Python

SQL Server Development Database
```

---

## Testing

```text
Separate Testing Environment

Clone cấu hình Production
```

---

# 5. TECHNOLOGY STACK

## Backend

```text
Python 3.12

Django 5

Django REST Framework
```

---

## Frontend

```text
HTML5

Bootstrap 5

AdminLTE

JavaScript

AJAX

jQuery
```

---

## Database

```text
Microsoft SQL Server
```

---

## Authentication

```text
JWT

Refresh Token

Microsoft Entra ID
```

---

## Storage

```text
SharePoint

OneDrive
```

---

## Server

```text
Windows Server

IIS
```

---

# 6. APPLICATION ARCHITECTURE

## Layer Design

```text
Presentation Layer

↓

API Layer

↓

Application Service Layer

↓

Repository Layer

↓

Data Access Layer

↓

SQL Server
```

---

# 7. MODULE ARCHITECTURE

## Core Modules

### Organization

Quản lý cơ cấu tổ chức.

---

### Human Resource

Quản lý hồ sơ nhân sự.

---

### Recruitment

Quản lý tuyển dụng.

---

### Attendance

Quản lý công.

---

### Leave

Quản lý nghỉ phép.

---

### Payroll

Quản lý tiền lương.

---

### Contract

Quản lý hợp đồng.

---

### Document

Quản lý tài liệu.

---

### Task

Quản lý công việc.

---

### KPI

Quản lý KPI.

---

### Asset

Quản lý tài sản.

---

### Procurement

Quản lý mua sắm.

---

### Dashboard

Dashboard điều hành.

---

### Microsoft365

Tích hợp M365.

---

# 8. DJANGO APPLICATION STRUCTURE

```text
apps/

├── organization
├── hrm
├── recruitment
├── attendance
├── leave
├── payroll
├── contracts
├── documents
├── tasks
├── kpi
├── assets
├── procurement
├── dashboard
├── m365
├── audit
├── notifications
├── security
└── common
```

---

# 9. INTERNAL DESIGN PATTERN

## Repository Pattern

Tách logic truy xuất dữ liệu.

Ví dụ:

```text
EmployeeRepository

ContractRepository

TaskRepository
```

---

## Service Layer

Tập trung toàn bộ business logic.

Ví dụ:

```text
EmployeeService

PayrollService

TaskService
```

---

## Unit Of Work

Quản lý transaction.

---

## DTO Pattern

Chuyển dữ liệu giữa các tầng.

---

# 10. DATA FLOW ARCHITECTURE

## Employee Creation

```text
UI

↓

API

↓

Employee Service

↓

Employee Repository

↓

SQL Server

↓

Audit Log
```

---

## Leave Approval

```text
Employee

↓

Manager

↓

HR

↓

Database Update

↓

Teams Notification

↓

Audit Log
```

---

## Payroll Calculation

```text
Attendance

+

Leave

+

Allowance

+

Deduction

↓

Payroll Engine

↓

Payroll Result

↓

Payslip
```

---

# 11. SECURITY ARCHITECTURE

## Authentication Flow

```text
User

↓

Login

↓

Entra ID

↓

JWT Token

↓

Application Access
```

---

## Authorization Flow

```text
User

↓

Role

↓

Permission

↓

Feature Access
```

---

## Security Components

```text
JWT

Refresh Token

RBAC

Audit Log

Soft Delete

Session Log
```

---

# 12. FILE MANAGEMENT ARCHITECTURE

## Metadata

Lưu trong:

```text
SQL Server
```

---

## File Content

Lưu trong:

```text
SharePoint

OneDrive
```

---

## Document Flow

```text
Upload

↓

SharePoint

↓

Metadata

↓

SQL Server
```

---

# 13. MICROSOFT 365 INTEGRATION

## Outlook

Chức năng:

- Email Notification
- Workflow Notification
- Reminder

---

## Teams

Chức năng:

- Task Notification
- Approval Notification
- Alert Notification

---

## SharePoint

Chức năng:

- Document Storage
- Version Control
- Search

---

## OneDrive

Chức năng:

- Attachment Storage

---

## Entra ID

Chức năng:

- Single Sign On
- User Authentication

---

# 14. NOTIFICATION ARCHITECTURE

## Event Sources

```text
Leave Request

Recruitment

Contract Expiry

Task Deadline

KPI Review

Procurement Approval
```

---

## Notification Channels

```text
Teams

Outlook

In-App Notification
```

---

# 15. AUDIT ARCHITECTURE

## Audit Scope

Bắt buộc cho:

```text
Employee

Recruitment

Attendance

Payroll

Contract

Document

Task

KPI

Asset

Procurement
```

---

## Audit Events

```text
Create

Update

Delete

Approve

Reject

Login

Logout
```

---

# 16. PERFORMANCE REQUIREMENTS

## Page Response

```text
< 3 Seconds
```

---

## Dashboard

```text
< 5 Seconds
```

---

## Concurrent Users

```text
50 users
```

---

## Future Capacity

```text
200 users
```

---

# 17. AVAILABILITY REQUIREMENTS

## Availability

```text
99.5%
```

---

## Working Hours

```text
24/7 Access

Business Hours Priority
```

---

# 18. BACKUP ARCHITECTURE

## Database Backup

```text
Daily Full Backup
```

---

## File Backup

```text
Microsoft 365 Retention

SharePoint Backup Policy
```

---

## Retention

```text
30 Days Daily Backup

12 Months Monthly Backup
```

---

# 19. DISASTER RECOVERY

## RPO

```text
24 Hours
```

---

## RTO

```text
8 Hours
```

---

# 20. DEPLOYMENT ARCHITECTURE

```text
Production

Windows Server

│

├─ IIS

├─ Django Application

├─ SQL Server

├─ Microsoft 365 Connector

└─ File Storage
```

---

# 21. OPERATION ARCHITECTURE

## System Administrator

- User Management
- Permission Management
- Configuration

---

## HR Administrator

- Employee Data
- Payroll
- Recruitment

---

## Department Manager

- Task
- KPI
- Team Monitoring

---

## Employee

- Self Service

---

# 22. ARCHITECTURE DECISIONS

## ADR-001

Architecture Style:

Modular Monolith

---

## ADR-002

Database:

Microsoft SQL Server

---

## ADR-003

Authentication:

JWT + Entra ID

---

## ADR-004

Storage:

SharePoint + OneDrive

---

## ADR-005

Deployment:

Windows Server + IIS

---

## ADR-006

Frontend:

Bootstrap 5 + AdminLTE

---

## ADR-007

Backend:

Django 5 + DRF

---

# 23. ARCHITECTURE APPROVAL

Status:

Approved

Ready for:

- Database Design
- Security Design
- Backend Design
- UI Design
- Development
