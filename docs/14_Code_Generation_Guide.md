# CODE GENERATION GUIDE

> Phạm vi áp dụng (28/10/2026): đây là hướng dẫn sinh mã ban đầu. Không dùng các yêu cầu DRF/JWT/Entra ID bên dưới để tự thêm công nghệ hoặc dựng lại skeleton hiện có. Mã hiện hành dùng Django ORM, template, session auth và RBAC phía máy chủ. Đọc [baseline hiện hành](99_Architecture_Baseline.md), [tiêu chuẩn backend](05_Backend_Standards.md) và [AGENTS.md](../AGENTS.md); chỉ sinh mã trong phạm vi chủ dự án giao.

## Project

Internal Administration & Human Resource Management System (IHRMS)

## Version

1.0

## Status

Approved

## Purpose

Tài liệu này là tài liệu hướng dẫn duy nhất để AI Developer, Qwen hoặc Developer triển khai source code.

Mọi source code sinh ra phải tuân thủ:

- 00_Project_Charter.md
- 01_BRD_MASTER.md
- 02_Solution_Architecture.md
- 03_Database_Design.md
- 04_Security_Design.md
- 05_Backend_Standards.md
- 06_Frontend_Standards.md
- 07_Testing_Standards.md
- 08_Deployment_Standards.md
- 09_UI_UX_Specification.md
- 10_RBAC_Permission_Matrix.md
- 11_Workflow_Definition.md
- 12_Report_Data_Dictionary.md
- 13_Master_Data_Dictionary.md

---

# 1. GENERAL RULES

## CG-001

Không được thay đổi:

```text
Technology Stack
```

Đã khóa:

```text
Python 3.12
Django 5
DRF
SQL Server
Bootstrap 5
AdminLTE
JWT
Microsoft Entra ID
IIS
Windows Server
```

---

## CG-002

Không được đổi Database.

Chỉ sử dụng:

```text
Microsoft SQL Server
```

---

## CG-003

Không được đổi kiến trúc.

Chỉ sử dụng:

```text
Modular Monolith
```

---

## CG-004

Không được bổ sung:

```text
React
Vue
Angular
NextJS
FastAPI
Flask
PostgreSQL
MongoDB
```

---

# 2. PROJECT STRUCTURE

Source code phải tạo đúng cấu trúc:

```text
ihrms/

config/

apps/

media/

static/

templates/

logs/
```

---

# 3. DJANGO APP STRUCTURE

Mỗi app phải có:

```text
models/

repositories/

services/

serializers/

validators/

permissions/

api/

tests/
```

---

Ví dụ:

```text
apps/hrm/

models/
repositories/
services/
serializers/
validators/
permissions/
api/
tests/
```

---

# 4. MODULE GENERATION ORDER

Sinh code đúng thứ tự.

## Phase 1

```text
Common

Audit

Security

Authentication
```

---

## Phase 2

```text
Organization

HRM
```

---

## Phase 3

```text
Recruitment

Attendance

Leave
```

---

## Phase 4

```text
Payroll

Contract
```

---

## Phase 5

```text
Document

Task

KPI
```

---

## Phase 6

```text
Asset

Procurement
```

---

## Phase 7

```text
Dashboard

M365 Integration
```

---

# 5. MODEL GENERATION RULES

## CG-MDL-001

Mọi model phải kế thừa:

```python
BaseModel
```

---

## CG-MDL-002

BaseModel bắt buộc chứa:

```python
created_by
created_date

modified_by
modified_date

deleted_by
deleted_date

is_deleted
```

---

## CG-MDL-003

Không dùng hard delete.

Bắt buộc Soft Delete.

---

## CG-MDL-004

Tên model phải lấy từ:

```text
03_Database_Design.md
```

---

Ví dụ:

```python
Employee

Department

Contract

Task

Asset
```

---

# 6. REPOSITORY RULES

## CG-REP-001

Toàn bộ truy xuất dữ liệu phải đi qua Repository.

---

Không được:

```python
Employee.objects.filter(...)
```

trong:

```python
Service
View
Serializer
```

---

## CG-REP-002

Tạo Repository cho từng Aggregate.

Ví dụ:

```python
EmployeeRepository

ContractRepository

TaskRepository
```

---

## CG-REP-003

Repository chịu trách nhiệm:

```text
Create

Get

Update

Soft Delete

Search

Filter
```

---

# 7. SERVICE RULES

## CG-SRV-001

Business Logic chỉ nằm trong Service Layer.

---

Không đặt Business Logic trong:

```text
View

ViewSet

Serializer
```

---

## CG-SRV-002

Workflow xử lý trong Service.

Ví dụ:

```python
LeaveApprovalService

PayrollCalculationService

RecruitmentWorkflowService
```

---

# 8. SERIALIZER RULES

## CG-SER-001

Tách riêng:

```python
CreateSerializer

UpdateSerializer

DetailSerializer

ListSerializer
```

---

## CG-SER-002

Validation cơ bản:

```python
Serializer
```

Validation nghiệp vụ:

```python
Service
```

---

# 9. API RULES

## CG-API-001

Sử dụng:

```python
DRF ViewSet
```

---

## CG-API-002

Base URL

```text
/api/v1/
```

---

Ví dụ:

```text
/api/v1/employees

/api/v1/departments

/api/v1/tasks
```

---

## CG-API-003

Response Format

Success:

```json
{
  "success": true,
  "message": "Success",
  "data": {}
}
```

---

Error:

```json
{
  "success": false,
  "message": "Error",
  "errors": []
}
```

---

# 10. AUTHENTICATION RULES

## CG-AUTH-001

JWT bắt buộc.

---

## CG-AUTH-002

Refresh Token bắt buộc.

---

## CG-AUTH-003

Microsoft Entra ID Integration bắt buộc.

---

# 11. AUTHORIZATION RULES

## CG-AUTHZ-001

RBAC phải tuân thủ:

```text
10_RBAC_Permission_Matrix.md
```

---

## CG-AUTHZ-002

Mỗi ViewSet phải có:

```python
Permission Class
```

---

## CG-AUTHZ-003

Phải kiểm tra:

```text
Role

Permission

Data Scope
```

---

# 12. WORKFLOW RULES

## CG-WF-001

Workflow phải tuân thủ:

```text
11_Workflow_Definition.md
```

---

Không được sáng tạo thêm bước.

---

## CG-WF-002

Mỗi Workflow phải lưu:

```text
Current Step

Decision

Comment

Decision By

Decision Date
```

---

# 13. AUDIT LOG RULES

## CG-AUD-001

Audit Log bắt buộc cho:

```text
Employee

Leave

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

## CG-AUD-002

Audit Events:

```text
Create

Update

Delete

Approve

Reject

Export
```

---

# 14. FILE STORAGE RULES

## CG-FILE-001

Không lưu file trong SQL Server.

---

## CG-FILE-002

File lưu:

```text
SharePoint

OneDrive
```

---

## CG-FILE-003

SQL Server chỉ lưu:

```text
Metadata
```

---

# 15. TASK MANAGEMENT RULES

Task phải hỗ trợ:

```text
Checklist

Comment

Attachment

Priority

Deadline

Status
```

---

Status phải dùng:

```text
Backlog

To Do

In Progress

Review

Approved

Done

Cancelled
```

---

# 16. KPI RULES

KPI Engine phải sử dụng:

```text
Target

Actual

Achievement

Score
```

---

Formula lấy từ:

```text
12_Report_Data_Dictionary.md
```

---

# 17. PAYROLL RULES

## Payroll Engine

Thứ tự tính:

```text
Base Salary

+

Allowance

+

Overtime

=

Gross Income

-

Insurance

-

Tax

-

Deductions

=

Net Income
```

---

Không được thay đổi công thức.

---

# 18. DASHBOARD RULES

## Dashboard Data Source

Lấy từ:

```text
12_Report_Data_Dictionary.md
```

---

Không hardcode KPI.

---

## Dashboard Types

```text
Director

HR

Manager

Employee
```

---

# 19. UI GENERATION RULES

Bắt buộc theo:

```text
09_UI_UX_Specification.md
```

---

Mỗi Module phải sinh:

```text
List

Create

Edit

Detail
```

---

# 20. VALIDATION RULES

Thực hiện theo:

```text
13_Master_Data_Dictionary.md
```

---

Ví dụ:

```text
EmployeeCode Unique

NationalID Unique

DepartmentCode Unique
```

---

# 21. TEST GENERATION RULES

Mọi module phải tạo:

```text
Unit Test

Integration Test
```

---

Coverage:

```text
>=80%
```

---

# 22. CODE QUALITY RULES

## Standard

```text
PEP8
```

---

## Không được

```text
Duplicate Logic

Magic Number

Hard Code

Unused Variable

Unused Import
```

---

# 23. LOGGING RULES

Bắt buộc logging:

```text
Info

Warning

Error

Critical
```

---

Không log:

```text
Password

JWT

National ID

Bank Account
```

---

# 24. EXCEPTION RULES

Bắt buộc tạo:

```python
ValidationException

BusinessException

PermissionException

NotFoundException
```

---

# 25. SWAGGER RULES

Toàn bộ API phải:

```text
Swagger/OpenAPI Ready
```

---

Phải có:

```text
Request

Response

Permission

Examples
```

---

# 26. MODULE COMPLETION CHECKLIST

Một module chỉ được xem là hoàn thành khi:

✅ Models

✅ Repository

✅ Services

✅ Serializers

✅ Permissions

✅ APIs

✅ Unit Test

✅ Integration Test

✅ Swagger

✅ Audit Log

✅ Workflow

✅ UI

✅ UAT Pass

---

# 27. AI GENERATION INSTRUCTION

Khi AI sinh code:

Luôn đọc trước:

```text
03_Database_Design.md

04_Security_Design.md

05_Backend_Standards.md

09_UI_UX_Specification.md

10_RBAC_Permission_Matrix.md

11_Workflow_Definition.md

13_Master_Data_Dictionary.md
```

---

Sau đó mới sinh:

```text
Models

Repositories

Services

Permissions

APIs

Tests
```

---

# 28. CODE GENERATION APPROVAL

Status:

Approved

Ready For:

- Django Model Generation
- API Generation
- UI Generation
- Test Generation
- Production Development
