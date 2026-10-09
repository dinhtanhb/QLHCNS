# UI/UX SPECIFICATION DOCUMENT

> Đây là đặc tả màn hình gốc. Bố cục, màu, font và hành vi menu đang triển khai được chốt tại [UI_DESIGN_SYSTEM.md](UI_DESIGN_SYSTEM.md); quyền thao tác theo [10_RBAC_Permission_Matrix.md](10_RBAC_Permission_Matrix.md). Dashboard Báo cáo hiện có lọc kỳ, nhóm chỉ số theo phân hệ và xuất Excel/Word/PowerPoint; mục REP-001 dưới đây là yêu cầu ban đầu, không phải danh sách chức năng đã triển khai.

## Project

Internal Administration & Human Resource Management System (IHRMS)

## Version

1.0

## Status

Approved

---

# 1. DOCUMENT PURPOSE

Tài liệu này quy định chi tiết:

- Danh sách màn hình
- Luồng sử dụng
- Bố cục màn hình
- Thành phần giao diện
- Điều hướng
- Trường dữ liệu
- Hành động người dùng
- Dashboard
- Responsive Design

Là tài liệu chuẩn để:

- Thiết kế giao diện
- Lập trình Frontend
- Kiểm thử UAT
- Nghiệm thu người dùng

---

# 2. APPLICATION NAVIGATION

## Main Menu

```text
Dashboard

Organization

Human Resources

Recruitment

Attendance

Leave

Payroll

Contracts

Documents

Tasks

KPI

Assets

Procurement

Reports

Administration
```

---

# 3. DASHBOARD SCREENS

# DASH-001

## Director Dashboard

### Mục đích

Theo dõi tình hình toàn công ty.

---

### Người dùng

Director

---

### KPI Cards

```text
Total Employees

New Employees

Employees Leaving

Open Recruitment

Pending Leave Requests

Pending Procurement

Overdue Tasks

Contracts Expiring

Monthly Payroll

Company KPI Score
```

---

### Charts

```text
Headcount Trend

Recruitment Trend

Task Status

Department KPI

Leave Analysis

Payroll Trend
```

---

### Filters

```text
Year

Month

Department
```

---

### Actions

```text
View Detail

Export Excel

Export PDF
```

---

# DASH-002

## HR Dashboard

### KPI

```text
Headcount

Recruitment

Attendance

Leave

Contracts
```

---

### Reports

```text
Employee Movement

Leave Summary

Attendance Summary

Contract Expiration
```

---

# DASH-003

## Manager Dashboard

### KPI

```text
Team Size

Team Attendance

Overdue Tasks

Team KPI

Pending Approvals
```

---

# 4. ORGANIZATION MODULE

# ORG-001

## Department List

### Purpose

Quản lý danh sách phòng ban.

---

### Permissions

```text
Admin

HR Manager

Director
```

---

### Search Filters

```text
Department Code

Department Name

Manager

Status
```

---

### Grid Columns

```text
Department Code

Department Name

Manager

Employee Count

Status

Actions
```

---

### Actions

```text
Create

Edit

View

Disable
```

---

# ORG-002

## Department Detail

### Sections

#### General Information

```text
Department Code

Department Name

Parent Department

Manager

Description
```

---

#### Employees

Danh sách nhân viên thuộc phòng.

---

# ORG-003

## Organization Chart

### Purpose

Hiển thị sơ đồ tổ chức.

---

### View

```text
Tree Structure
```

---

### Actions

```text
Expand

Collapse

Print
```

---

# 5. HUMAN RESOURCE MODULE

# HR-001

## Employee List

### Purpose

Tra cứu nhân viên.

---

### Search Filters

```text
Employee Code

Full Name

Department

Position

Status

Join Date
```

---

### Grid Columns

```text
Employee Code

Full Name

Department

Position

Join Date

Employment Status

Actions
```

---

### Actions

```text
Create

Import

Export

View

Edit
```

---

# HR-002

## Employee Create

### Sections

#### Personal Information

```text
Employee Code

First Name

Last Name

Date Of Birth

Gender

National ID

Tax Code
```

---

#### Contact Information

```text
Phone

Personal Email

Company Email

Address
```

---

#### Employment Information

```text
Join Date

Department

Position

Job Title

Manager
```

---

#### Banking Information

```text
Bank Name

Account Number

Account Holder
```

---

#### Attachments

```text
CV

National ID

Certificates

Other Documents
```

---

# HR-003

## Employee Profile

### Tabs

```text
Summary

Personal Information

Employment History

Salary History

Training

Certificates

Documents

Audit Log
```

---

# HR-004

## Employee Transfer

### Fields

```text
Employee

Current Department

New Department

Effective Date

Reason
```

---

# HR-005

## Employee Termination

### Fields

```text
Employee

Termination Date

Termination Type

Reason
```

---

# 6. RECRUITMENT MODULE

# REC-001

## Recruitment Request List

### Grid

```text
Request No

Department

Position

Quantity

Expected Date

Status
```

---

# REC-002

## Recruitment Request Detail

### Sections

```text
Request Information

Approval History

Vacancy Information
```

---

# REC-003

## Candidate List

### Search

```text
Name

Phone

Email

Recruitment Source

Status
```

---

### Grid

```text
Candidate Code

Name

Position

Interview Status

Result
```

---

# REC-004

## Candidate Profile

### Tabs

```text
Personal Information

CV

Interviews

Assessment

Offer
```

---

# REC-005

## Interview Form

### Fields

```text
Candidate

Interview Date

Interview Type

Interviewer

Comments

Result
```

---

# 7. ATTENDANCE MODULE

# ATT-001

## Attendance List

### Filters

```text
Employee

Department

Date Range

Status
```

---

### Grid

```text
Employee

Date

Check In

Check Out

Hours

Status
```

---

# ATT-002

## Attendance Adjustment

### Fields

```text
Employee

Attendance Date

Requested Time

Reason

Attachment
```

---

# ATT-003

## Overtime Request

### Fields

```text
Employee

From Time

To Time

Reason
```

---

# 8. LEAVE MODULE

# LEA-001

## Leave Request List

### Grid

```text
Request No

Employee

Leave Type

Days

Status
```

---

# LEA-002

## Leave Request Form

### Fields

```text
Leave Type

From Date

To Date

Total Days

Reason

Attachment
```

---

### Workflow Section

```text
Current Approver

Approval History
```

---

# LEA-003

## Leave Approval Screen

### Actions

```text
Approve

Reject

Request Clarification
```

---

# 9. PAYROLL MODULE

# PAY-001

## Payroll Period List

### Columns

```text
Month

Year

Status

Created Date
```

---

# PAY-002

## Payroll Detail

### Employee Salary Components

```text
Basic Salary

Allowances

Overtime

Gross Income

Tax

Insurance

Deductions

Net Income
```

---

# PAY-003

## Payslip

### Sections

```text
Employee Information

Earnings

Deductions

Net Salary
```

---

# 10. CONTRACT MODULE

# CON-001

## Contract List

### Columns

```text
Contract No

Employee

Contract Type

Start Date

End Date

Status
```

---

# CON-002

## Contract Detail

### Sections

```text
Contract Information

Appendix

Document

History
```

---

# 11. DOCUMENT MODULE

# DOC-001

## Document List

### Filters

```text
Document No

Category

Version

Status
```

---

### Columns

```text
Document No

Document Name

Category

Version

Status
```

---

# DOC-002

## Document Detail

### Tabs

```text
Information

Versions

Approval

Audit Log
```

---

# DOC-003

## Upload Document

### Fields

```text
Document Number

Document Name

Category

Version

Effective Date

File
```

---

# 12. TASK MODULE

# TASK-001

## Task List

### Filters

```text
Task Code

Task Name

Department

Status

Priority

Assigned To
```

---

### Grid

```text
Task Code

Task Name

Assigned To

Priority

Due Date

Status
```

---

# TASK-002

## Task Detail

### Sections

```text
General Information

Checklist

Comments

Attachments

History
```

---

# TASK-003

## Kanban Board

### Columns

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

# TASK-004

## Gantt View

### Timeline

```text
Task Start Date

Task End Date

Progress
```

---

# TASK-005

## Calendar View

### Display

```text
Daily

Weekly

Monthly
```

---

# 13. KPI MODULE

# KPI-001

## KPI Template List

### Columns

```text
KPI Code

KPI Name

Weight

Target
```

---

# KPI-002

## KPI Evaluation

### Fields

```text
Target

Actual

Achievement

Score

Comment
```

---

# KPI-003

## KPI Dashboard

### Components

```text
KPI Cards

Achievement Chart

Ranking
```

---

# 14. ASSET MODULE

# AST-001

## Asset List

### Columns

```text
Asset Code

Asset Name

Type

Purchase Date

Status
```

---

# AST-002

## Asset Allocation

### Fields

```text
Asset

Employee

Assigned Date

Return Date
```

---

# AST-003

## Asset Maintenance

### Fields

```text
Asset

Maintenance Date

Supplier

Cost

Description
```

---

# 15. PROCUREMENT MODULE

# PRO-001

## Procurement Request List

### Columns

```text
Request No

Department

Request Date

Status
```

---

# PRO-002

## Procurement Request Form

### Fields

```text
Item

Quantity

Estimated Cost

Justification
```

---

# PRO-003

## Approval Screen

### Components

```text
Request Information

Approval Workflow

Comments
```

---

# 16. REPORTS MODULE

# REP-001

## Report Center

### Categories

```text
HR Reports

Payroll Reports

Recruitment Reports

Task Reports

KPI Reports

Asset Reports

Procurement Reports
```

---

### Actions

```text
Preview

Export Excel

Export PDF
```

---

# 17. ADMINISTRATION MODULE

# ADM-001

## User Management

### Grid

```text
Username

Employee

Role

Status
```

---

# ADM-002

## Role Management

### Sections

```text
Role Information

Permissions
```

---

# ADM-003

## Audit Log

### Filters

```text
User

Action

Module

Date Range
```

---

### Columns

```text
Timestamp

User

Action

Record

IP Address
```

---

# 18. MOBILE UX REQUIREMENTS

Mobile phải hỗ trợ:

```text
Dashboard

Task

Leave

Attendance

Profile

Notifications
```

---

# 19. NOTIFICATION CENTER

## Categories

```text
Tasks

Leave

Recruitment

Contracts

Assets

Procurement

System
```

---

## Actions

```text
Open

Mark As Read

Delete
```

---

# 20. UI COMPLETION CRITERIA

Một màn hình được xem là hoàn thành khi:

✅ Đúng nghiệp vụ

✅ Responsive

✅ Validation đầy đủ

✅ Permission hoạt động

✅ Workflow hiển thị đúng

✅ Audit Log hiển thị đúng

✅ Search hoạt động

✅ Filter hoạt động

✅ Export hoạt động

✅ Không còn lỗi
