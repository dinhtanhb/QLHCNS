# 04_Security_Design.md

# SECURITY DESIGN DOCUMENT

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