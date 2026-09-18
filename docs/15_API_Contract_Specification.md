# API CONTRACT SPECIFICATION

## Project

Internal Administration & Human Resource Management System (IHRMS)

## Version

1.0

## Status

Approved

---

# 1. PURPOSE

Tài liệu này định nghĩa:

- API Endpoint
- Request Format
- Response Format
- Authentication
- Authorization
- Pagination
- Filtering
- Sorting
- Error Codes

Là tài liệu chuẩn cho:

- Backend Development
- Frontend Development
- Integration Testing
- Swagger/OpenAPI

---

# 2. API STANDARDS

## Base URL

```text
/api/v1
```

---

## Content Type

```text
application/json
```

---

## Authentication

```text
Bearer JWT Token
```

---

## Response Encoding

```text
UTF-8
```

---

# 3. STANDARD SUCCESS RESPONSE

```json
{
  "success": true,
  "message": "Success",
  "data": {},
  "errors": [],
  "timestamp": "2026-09-17T10:00:00"
}
```

---

# 4. STANDARD PAGINATION RESPONSE

```json
{
  "success": true,
  "message": "Success",
  "data": {
    "items": [],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_records": 100,
      "total_pages": 5
    }
  }
}
```

---

# 5. STANDARD ERROR RESPONSE

```json
{
  "success": false,
  "message": "Validation Error",
  "errors": [
    {
      "field": "employee_code",
      "message": "Employee Code already exists"
    }
  ]
}
```

---

# 6. HTTP STATUS CODES

## Success

```text
200 OK

201 Created

204 No Content
```

---

## Error

```text
400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

409 Conflict

422 Validation Error

500 Internal Server Error
```

---

# 7. PAGINATION STANDARD

## Query Parameters

```text
?page=1

?page_size=20
```

---

## Default

```text
20
```

---

## Maximum

```text
100
```

---

# 8. FILTERING STANDARD

## Query Parameters

```text
keyword

status

department_id

employee_id

from_date

to_date
```

---

## Example

```http
GET /api/v1/employees?keyword=tan&status=active
```

---

# 9. SORTING STANDARD

## Query Format

```text
sort_by

sort_order
```

---

## Example

```http
GET /api/v1/employees?sort_by=employee_code&sort_order=asc
```

---

# 10. AUTHENTICATION APIs

## AUTH-001

### Login

```http
POST /api/v1/auth/login
```

Request

```json
{
  "username": "admin",
  "password": "Password@123"
}
```

Response

```json
{
  "access_token": "",
  "refresh_token": ""
}
```

---

## AUTH-002

### Refresh Token

```http
POST /api/v1/auth/refresh
```

---

## AUTH-003

### Logout

```http
POST /api/v1/auth/logout
```

---

## AUTH-004

### Current User

```http
GET /api/v1/auth/me
```

---

# 11. ORGANIZATION APIs

## ORG-001

### Department List

```http
GET /api/v1/departments
```

---

## ORG-002

### Department Detail

```http
GET /api/v1/departments/{id}
```

---

## ORG-003

### Create Department

```http
POST /api/v1/departments
```

Request

```json
{
  "department_code": "HR",
  "department_name": "Human Resources",
  "manager_employee_id": 1001
}
```

---

## ORG-004

### Update Department

```http
PUT /api/v1/departments/{id}
```

---

## ORG-005

### Delete Department

```http
DELETE /api/v1/departments/{id}
```

---

# 12. EMPLOYEE APIs

## EMP-001

### Employee List

```http
GET /api/v1/employees
```

---

## EMP-002

### Employee Detail

```http
GET /api/v1/employees/{id}
```

---

## EMP-003

### Create Employee

```http
POST /api/v1/employees
```

Request

```json
{
  "employee_code": "EMP0001",
  "first_name": "Tan",
  "last_name": "Vu",
  "department_id": 1,
  "position_id": 2,
  "join_date": "2026-01-01"
}
```

---

## EMP-004

### Update Employee

```http
PUT /api/v1/employees/{id}
```

---

## EMP-005

### Terminate Employee

```http
POST /api/v1/employees/{id}/terminate
```

---

## EMP-006

### Employee Transfer

```http
POST /api/v1/employees/{id}/transfer
```

---

# 13. RECRUITMENT APIs

## REC-001

### Recruitment Request List

```http
GET /api/v1/recruitment-requests
```

---

## REC-002

### Create Recruitment Request

```http
POST /api/v1/recruitment-requests
```

---

## REC-003

### Recruitment Approval

```http
POST /api/v1/recruitment-requests/{id}/approve
```

---

## REC-004

### Candidate List

```http
GET /api/v1/candidates
```

---

## REC-005

### Create Candidate

```http
POST /api/v1/candidates
```

---

## REC-006

### Schedule Interview

```http
POST /api/v1/interviews
```

---

## REC-007

### Create Offer

```http
POST /api/v1/offers
```

---

# 14. ATTENDANCE APIs

## ATT-001

### Attendance List

```http
GET /api/v1/attendance
```

---

## ATT-002

### Check In

```http
POST /api/v1/attendance/check-in
```

---

## ATT-003

### Check Out

```http
POST /api/v1/attendance/check-out
```

---

## ATT-004

### Attendance Adjustment

```http
POST /api/v1/attendance-adjustments
```

---

## ATT-005

### Approve Attendance Adjustment

```http
POST /api/v1/attendance-adjustments/{id}/approve
```

---

# 15. LEAVE APIs

## LEA-001

### Leave Request List

```http
GET /api/v1/leave-requests
```

---

## LEA-002

### Create Leave Request

```http
POST /api/v1/leave-requests
```

---

## LEA-003

### Approve Leave Request

```http
POST /api/v1/leave-requests/{id}/approve
```

---

## LEA-004

### Reject Leave Request

```http
POST /api/v1/leave-requests/{id}/reject
```

---

# 16. PAYROLL APIs

## PAY-001

### Payroll Period List

```http
GET /api/v1/payroll-periods
```

---

## PAY-002

### Generate Payroll

```http
POST /api/v1/payroll/generate
```

---

## PAY-003

### Payroll Details

```http
GET /api/v1/payroll
```

---

## PAY-004

### Payroll Approval

```http
POST /api/v1/payroll/{id}/approve
```

---

## PAY-005

### Payroll Lock

```http
POST /api/v1/payroll/{id}/lock
```

---

## PAY-006

### Payslip

```http
GET /api/v1/payslips/{id}
```

---

# 17. CONTRACT APIs

## CON-001

### Contract List

```http
GET /api/v1/contracts
```

---

## CON-002

### Create Contract

```http
POST /api/v1/contracts
```

---

## CON-003

### Contract Renew

```http
POST /api/v1/contracts/{id}/renew
```

---

## CON-004

### Contract Approval

```http
POST /api/v1/contracts/{id}/approve
```

---

# 18. DOCUMENT APIs

## DOC-001

### Document List

```http
GET /api/v1/documents
```

---

## DOC-002

### Upload Document

```http
POST /api/v1/documents/upload
```

---

## DOC-003

### Document Approval

```http
POST /api/v1/documents/{id}/approve
```

---

## DOC-004

### Document Download

```http
GET /api/v1/documents/{id}/download
```

---

# 19. TASK APIs

## TASK-001

### Task List

```http
GET /api/v1/tasks
```

---

## TASK-002

### Create Task

```http
POST /api/v1/tasks
```

---

## TASK-003

### Assign Task

```http
POST /api/v1/tasks/{id}/assign
```

---

## TASK-004

### Update Progress

```http
POST /api/v1/tasks/{id}/progress
```

---

## TASK-005

### Task Approval

```http
POST /api/v1/tasks/{id}/approve
```

---

## TASK-006

### Task Comment

```http
POST /api/v1/tasks/{id}/comments
```

---

# 20. KPI APIs

## KPI-001

### KPI Template List

```http
GET /api/v1/kpi/templates
```

---

## KPI-002

### KPI Assignment

```http
POST /api/v1/kpi/assign
```

---

## KPI-003

### KPI Evaluation

```http
POST /api/v1/kpi/evaluate
```

---

## KPI-004

### KPI Dashboard

```http
GET /api/v1/kpi/dashboard
```

---

# 21. ASSET APIs

## AST-001

### Asset List

```http
GET /api/v1/assets
```

---

## AST-002

### Create Asset

```http
POST /api/v1/assets
```

---

## AST-003

### Asset Allocation

```http
POST /api/v1/assets/allocate
```

---

## AST-004

### Asset Return

```http
POST /api/v1/assets/return
```

---

## AST-005

### Asset Maintenance

```http
POST /api/v1/assets/maintenance
```

---

# 22. PROCUREMENT APIs

## PRO-001

### Procurement Request List

```http
GET /api/v1/procurement-requests
```

---

## PRO-002

### Create Procurement Request

```http
POST /api/v1/procurement-requests
```

---

## PRO-003

### Budget Approval

```http
POST /api/v1/procurement-requests/{id}/budget-approve
```

---

## PRO-004

### Final Approval

```http
POST /api/v1/procurement-requests/{id}/final-approve
```

---

## PRO-005

### Close Procurement

```http
POST /api/v1/procurement-requests/{id}/close
```

---

# 23. DASHBOARD APIs

## DASH-001

### Director Dashboard

```http
GET /api/v1/dashboard/director
```

---

## DASH-002

### HR Dashboard

```http
GET /api/v1/dashboard/hr
```

---

## DASH-003

### Manager Dashboard

```http
GET /api/v1/dashboard/manager
```

---

## DASH-004

### Employee Dashboard

```http
GET /api/v1/dashboard/employee
```

---

# 24. REPORT APIs

## REP-001

### HR Reports

```http
GET /api/v1/reports/hr
```

---

## REP-002

### Recruitment Reports

```http
GET /api/v1/reports/recruitment
```

---

## REP-003

### Payroll Reports

```http
GET /api/v1/reports/payroll
```

---

## REP-004

### KPI Reports

```http
GET /api/v1/reports/kpi
```

---

# 25. ADMINISTRATION APIs

## ADM-001

### Users

```http
GET /api/v1/users
```

---

## ADM-002

### Roles

```http
GET /api/v1/roles
```

---

## ADM-003

### Permissions

```http
GET /api/v1/permissions
```

---

## ADM-004

### Audit Logs

```http
GET /api/v1/audit-logs
```

---

# 26. MICROSOFT 365 APIs

## M365-001

### Sync Users

```http
POST /api/v1/m365/sync-users
```

---

## M365-002

### Send Teams Notification

```http
POST /api/v1/m365/teams/send
```

---

## M365-003

### Send Email

```http
POST /api/v1/m365/outlook/send
```

---

## M365-004

### Upload SharePoint

```http
POST /api/v1/m365/sharepoint/upload
```

---

## M365-005

### Upload OneDrive

```http
POST /api/v1/m365/onedrive/upload
```

---

# 27. API VERSIONING

Version hiện tại:

```text
v1
```

---

Future:

```text
v2

v3
```

---

# 28. API SECURITY RULES

Bắt buộc:

✅ JWT

✅ Permission Validation

✅ Audit Log

✅ HTTPS

✅ Data Scope Validation

---

# 29. API APPROVAL

Status:

Approved

Ready For:

- Django REST Framework Development
- Swagger Generation
- Frontend Integration
- SIT
- UAT