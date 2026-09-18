# REPORT & KPI DATA DICTIONARY

## Project

Internal Administration & Human Resource Management System (IHRMS)

## Version

1.0

## Status

Approved

---

# 1. PURPOSE

Tài liệu này định nghĩa:

- Toàn bộ Dashboard
- Toàn bộ KPI
- Toàn bộ Report
- Công thức tính toán
- Nguồn dữ liệu
- Bộ lọc
- Quy tắc tính toán

Là nguồn tham chiếu duy nhất cho:

- Dashboard Development
- BI Layer
- Reporting Module
- KPI Engine
- Testing
- UAT

---

# 2. REPORTING PRINCIPLES

## RP-001

Mỗi KPI phải có công thức rõ ràng.

---

## RP-002

Mỗi KPI phải có nguồn dữ liệu xác định.

---

## RP-003

Mỗi Dashboard phải truy xuất từ dữ liệu thực tế.

---

## RP-004

Không tính KPI bằng dữ liệu nhập tay.

---

## RP-005

Tất cả KPI phải truy vết được nguồn dữ liệu.

---

# 3. DASHBOARD CATALOG

## DASHBOARD 01

Director Dashboard

---

## DASHBOARD 02

HR Dashboard

---

## DASHBOARD 03

Department Manager Dashboard

---

## DASHBOARD 04

Employee Dashboard

---

# 4. DIRECTOR DASHBOARD

## KPI-001

### KPI Name

Total Employees

### Business Purpose

Theo dõi quy mô nhân sự.

### Formula

```text
COUNT(Employee Active)
```

### Data Source

```text
tblEmployee
```

### Filter

```text
Department

Year
```

### Refresh

Real Time

---

## KPI-002

### KPI Name

New Employees

### Formula

```text
Employees Joined In Period
```

### Data Source

```text
tblEmployee
```

### Filter

```text
Month

Year
```

---

## KPI-003

### KPI Name

Employees Leaving

### Formula

```text
Employees Leave In Period
```

### Data Source

```text
tblEmployee
```

---

## KPI-004

### KPI Name

Employee Turnover Rate

### Formula

```text
(Employee Leaving / Average Headcount)
× 100
```

### Unit

%

---

## KPI-005

### KPI Name

Open Recruitment Requests

### Formula

```text
Recruitment Request
WHERE Status <> Completed
```

### Data Source

```text
tblRecruitmentRequest
```

---

## KPI-006

### KPI Name

Open Positions

### Formula

```text
Total Open Vacancy
```

### Data Source

```text
tblJobPosting
```

---

## KPI-007

### KPI Name

Pending Leave Requests

### Formula

```text
Leave Status = Pending
```

### Data Source

```text
tblLeaveRequest
```

---

## KPI-008

### KPI Name

Pending Procurement Requests

### Formula

```text
Request Status = Pending
```

### Data Source

```text
tblProcurementRequest
```

---

## KPI-009

### KPI Name

Overdue Tasks

### Formula

```text
DueDate < Today

AND

Status <> Done
```

### Data Source

```text
tblTask
```

---

## KPI-010

### KPI Name

Contracts Expiring

### Formula

```text
Contract End Date

<= 90 Days
```

### Data Source

```text
tblContract
```

---

## KPI-011

### KPI Name

Monthly Payroll Cost

### Formula

```text
SUM(NetIncome)
```

### Data Source

```text
tblPayroll
```

---

## KPI-012

### KPI Name

Company KPI Achievement

### Formula

```text
SUM(Actual)
/
SUM(Target)

×100
```

### Unit

%

---

# 5. HR DASHBOARD

## KPI-013

Headcount By Department

### Formula

```text
Count Employee By Department
```

---

## KPI-014

New Hire

### Formula

```text
Employee Joined This Month
```

---

## KPI-015

Resignation

### Formula

```text
Employee Left This Month
```

---

## KPI-016

Contract Expiring 90 Days

### Formula

```text
EndDate <= Today + 90
```

---

## KPI-017

Leave Requests

### Formula

```text
Count Leave Requests
```

---

## KPI-018

Attendance Compliance

### Formula

```text
Attendance Days /
Working Days
```

---

# 6. MANAGER DASHBOARD

## KPI-019

Department Headcount

---

## KPI-020

Department Attendance Rate

### Formula

```text
Present / Working Days
```

---

## KPI-021

Team KPI Achievement

### Formula

```text
Department KPI Achievement
```

---

## KPI-022

Pending Task

### Formula

```text
Status <> Done
```

---

## KPI-023

Overdue Task

### Formula

```text
Task DueDate Passed
```

---

# 7. EMPLOYEE DASHBOARD

## KPI-024

Assigned Tasks

### Formula

```text
Tasks Assigned To Me
```

---

## KPI-025

Completed Tasks

### Formula

```text
Task Status = Done
```

---

## KPI-026

Remaining Leave Days

### Formula

```text
Annual Entitlement

-

Leave Used
```

---

## KPI-027

Current KPI Score

### Formula

```text
Achievement %
```

---

# 8. HR REPORTS

# REP-HR-001

## Report

Employee Master List

### Purpose

Quản lý hồ sơ nhân viên.

### Source

```text
tblEmployee
```

### Filters

```text
Department

Status

Join Date
```

### Output

Excel / PDF

---

# REP-HR-002

## Employee Movement Report

### Source

```text
tblEmployeeHistory
```

### Metrics

```text
Promotion

Transfer

Salary Increase

Termination
```

---

# REP-HR-003

## Employee Age Analysis

### Formula

```text
DateOfBirth
```

### Group

```text
<25

25-35

36-45

46+
```

---

# REP-HR-004

## Employee Tenure

### Formula

```text
Today - JoinDate
```

---

# REP-HR-005

## Gender Distribution

### Source

```text
tblEmployee
```

---

# 9. RECRUITMENT REPORTS

# REP-REC-001

Recruitment Pipeline

---

### Metrics

```text
Applied

Screening

Interview

Offer

Hired
```

---

# REP-REC-002

Time To Hire

### Formula

```text
Hiring Date

-

Recruitment Request Date
```

---

# REP-REC-003

Offer Acceptance Rate

### Formula

```text
Accepted Offers

/

Total Offers

×100
```

---

# REP-REC-004

Recruitment Source Analysis

### Metrics

```text
Facebook

Website

Referral

Recruitment Agency

Other
```

---

# 10. ATTENDANCE REPORTS

# REP-ATT-001

Attendance Summary

### Source

```text
tblAttendance
```

---

# REP-ATT-002

Overtime Summary

### Source

```text
tblOvertime
```

---

### Formula

```text
SUM(OvertimeHours)
```

---

# REP-ATT-003

Late Arrival Report

### Formula

```text
CheckIn

>

Shift Start Time
```

---

# 11. LEAVE REPORTS

# REP-LEA-001

Leave Summary

---

# REP-LEA-002

Leave Balance

### Formula

```text
Annual Entitlement

-

Leave Used
```

---

# REP-LEA-003

Leave Trend

### Purpose

Xu hướng nghỉ phép.

---

# 12. PAYROLL REPORTS

# REP-PAY-001

Monthly Payroll

### Source

```text
tblPayroll
```

---

# REP-PAY-002

Payroll Detail

---

### Fields

```text
Basic

Allowance

OT

Insurance

Tax

Net Salary
```

---

# REP-PAY-003

Insurance Summary

### Fields

```text
BHXH

BHYT

BHTN
```

---

# REP-PAY-004

Tax Summary

### Fields

```text
Taxable Income

Tax Amount
```

---

# 13. CONTRACT REPORTS

# REP-CON-001

Active Contracts

---

# REP-CON-002

Contract Expiration

### Period

```text
30 Days

60 Days

90 Days
```

---

# REP-CON-003

Contract Renewal

---

# 14. DOCUMENT REPORTS

# REP-DOC-001

Document Inventory

---

# REP-DOC-002

Document Approval Status

---

# REP-DOC-003

Document Revision History

---

# 15. TASK REPORTS

# REP-TASK-001

Task Progress Report

### Formula

```text
Done Tasks

/

Total Tasks

×100
```

---

# REP-TASK-002

Overdue Task Report

---

# REP-TASK-003

Workload Analysis

### Formula

```text
Task Count Per Employee
```

---

# REP-TASK-004

Task Completion Rate

### Formula

```text
Completed

/

Assigned

×100
```

---

# 16. KPI REPORTS

# REP-KPI-001

Company KPI

---

# REP-KPI-002

Department KPI

---

# REP-KPI-003

Employee KPI

---

# REP-KPI-004

Top KPI Achievement

### Ranking

Descending

---

# REP-KPI-005

Lowest KPI Achievement

### Ranking

Ascending

---

# 17. ASSET REPORTS

# REP-AST-001

Asset Inventory

---

# REP-AST-002

Asset Allocation

---

# REP-AST-003

Asset Maintenance

---

# REP-AST-004

Asset Depreciation

### Formula

```text
Purchase Value

-

Accumulated Depreciation
```

---

# 18. PROCUREMENT REPORTS

# REP-PRO-001

Procurement Requests

---

# REP-PRO-002

Procurement Status

---

# REP-PRO-003

Budget Usage

### Formula

```text
Approved Amount

/

Budget Amount
```

---

# 19. REPORT FILTER STANDARDS

## Global Filters

```text
Year

Month

Department

Employee

Status
```

---

## Optional Filters

```text
Position

Manager

Contract Type

Asset Type
```

---

# 20. EXPORT STANDARDS

## Excel

Mandatory

---

## PDF

Mandatory

---

## Naming Format

```text
ReportName_YYYYMMDD.xlsx
```

---

# 21. DATA REFRESH RULES

## Dashboard

```text
Real Time
```

---

## Reports

```text
On Demand
```

---

# 22. KPI COLOR DEFINITIONS

## Green

```text
>= 100%
```

---

## Yellow

```text
80% - 99%
```

---

## Red

```text
< 80%
```

---

# 23. REPORT SECURITY

Employee chỉ xem:

```text
Own Reports
```

---

Manager:

```text
Department Reports
```

---

Director:

```text
Organization Reports
```

---

# 24. REPORT APPROVAL

Status:

Approved

Ready For:

- Dashboard Development
- Reporting Development
- KPI Engine Development
- UAT