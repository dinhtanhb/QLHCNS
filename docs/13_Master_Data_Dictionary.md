# MASTER DATA DICTIONARY

## Project

Internal Administration & Human Resource Management System (IHRMS)

## Version

1.0

## Status

Approved

---

# 1. PURPOSE

Tài liệu này định nghĩa:

- Toàn bộ Master Data

- Ý nghĩa dữ liệu

- Kiểu dữ liệu

- Quy tắc nghiệp vụ

- Validation Rules

- Danh mục dùng chung

Là tài liệu tham chiếu cho:

- SQL Server Database

- Django Models

- API Validation

- Import Excel

- Data Migration

- Report Development

- Dashboard Development

---

# 2. DATA TYPE STANDARD

## String

```text

nvarchar

```

---

## Integer

```text

int

```

---

## Decimal

```text

decimal(18,2)

```

---

## Date

```text

date

```

---

## Date Time

```text

datetime

```

---

## Boolean

```text

bit

```

---

# 3. ORGANIZATION MASTER DATA

# MD-ORG-001

## tblOrganization

### OrganizationCode

Type:

```text

nvarchar(20)

```

Required:

```text

Yes

```

Unique:

```text

Yes

```

Example:

```text

ORG001

```

---

### OrganizationName

Type:

```text

nvarchar(200)

```

Required:

```text

Yes

```

---

### IsActive

Type:

```text

bit

```

Default:

```text

True

```

---

# MD-ORG-002

## tblDepartment

### DepartmentCode

Type:

```text

nvarchar(20)

```

Required:

```text

Yes

```

Unique:

```text

Yes

```

Example:

```text

HR

FIN

IT

PRG

MEL

```

---

### DepartmentName

Type:

```text

nvarchar(200)

```

Required:

```text

Yes

```

---

### ManagerEmployeeID

Reference:

```text

tblEmployee

```

---

# MD-ORG-003

## tblPosition

### PositionCode

Example:

```text

POS001

```

---

### PositionName

Example:

```text

Manager

Officer

Coordinator

Assistant

```

---

# MD-ORG-004

## tblJobTitle

### JobTitleCode

Example:

```text

JT001

```

---

### JobTitleName

Example:

```text

HR Manager

Finance Officer

M&E Specialist

Project Coordinator

```

---

# 4. EMPLOYEE MASTER DATA

# MD-HR-001

## Employee

### EmployeeCode

Type:

```text

nvarchar(20)

```

Required:

```text

Yes

```

Unique:

```text

Yes

```

Example:

```text

EMP0001

```

---

### FirstName

Type:

```text

nvarchar(100)

```

Required:

```text

Yes

```

---

### LastName

Type:

```text

nvarchar(100)

```

Required:

```text

Yes

```

---

### FullName

Generated:

```text

LastName + FirstName

```

---

### DateOfBirth

Type:

```text

date

```

Validation:

```text

Must be less than current date

```

---

### Gender

Values:

```text

Male

Female

Other

```

---

### NationalID

Type:

```text

nvarchar(20)

```

Required:

```text

Yes

```

Unique:

```text

Yes

```

---

### TaxCode

Type:

```text

nvarchar(20)

```

---

### SocialInsuranceNo

Type:

```text

nvarchar(30)

```

---

### PersonalEmail

Validation:

```text

Email Format

```

---

### CompanyEmail

Validation:

```text

Email Format

```

---

### MobilePhone

Validation:

```text

Vietnam Phone Number

```

---

### JoinDate

Required:

```text

Yes

```

---

### LeaveDate

Required:

```text

No

```

---

### EmploymentStatus

Values:

```text

Probation

Active

Inactive

Terminated

```

---

# MD-HR-002

## Employee Bank

### BankName

Reference:

```text

Bank Master

```

---

### AccountNumber

Required:

```text

Yes

```

---

### AccountHolder

Required:

```text

Yes

```

---

# MD-HR-003

## Education

### Degree

Values:

```text

High School

College

Bachelor

Master

Doctorate

```

---

### Major

Free Text

---

### GraduationYear

Validation:

```text

4 digits

```

---

# MD-HR-004

## Certificate

### CertificateName

Required:

```text

Yes

```

---

### ExpiryDate

Optional

---

# 5. RECRUITMENT MASTER DATA

# MD-REC-001

## Recruitment Source

Values:

```text

Website

Facebook

LinkedIn

Referral

Recruitment Agency

Job Fair

Other

```

---

# MD-REC-002

## Candidate Status

Values:

```text

Applied

Screening

Interview

Offer

Hired

Rejected

```

---

# MD-REC-003

## Interview Result

Values:

```text

Pass

Reserve

Fail

```

---

# 6. ATTENDANCE MASTER DATA

# MD-ATT-001

## Work Shift

### ShiftCode

Example:

```text

SHIFT01

```

---

### ShiftName

Examples:

```text

Office Hour

Flexible

Part Time

```

---

### StartTime

Example:

```text

08:00

```

---

### EndTime

Example:

```text

17:00

```

---

# MD-ATT-002

## Attendance Status

Values:

```text

Present

Absent

Late

Leave

Business Trip

Remote Work

```

---

# 7. LEAVE MASTER DATA

# MD-LEA-001

## Leave Type

### LeaveTypeCode

Example:

```text

AL

SL

UL

ML

```

---

### LeaveTypeName

Values:

```text

Annual Leave

Sick Leave

Unpaid Leave

Maternity Leave

```

---

### IsPaid

Values:

```text

True

False

```

---

# 8. PAYROLL MASTER DATA

# MD-PAY-001

## Allowance Type

Values:

```text

Position Allowance

Responsibility Allowance

Phone Allowance

Transportation Allowance

Meal Allowance

Other

```

---

# MD-PAY-002

## Deduction Type

Values:

```text

Insurance

Personal Tax

Penalty

Advance

Other

```

---

# MD-PAY-003

## Payroll Status

Values:

```text

Draft

Calculated

Approved

Locked

```

---

# 9. CONTRACT MASTER DATA

# MD-CON-001

## Contract Type

Values:

```text

Probation

Fixed Term

Indefinite Term

```

---

# MD-CON-002

## Contract Status

Values:

```text

Draft

Active

Expired

Terminated

```

---

# 10. DOCUMENT MASTER DATA

# MD-DOC-001

## Document Category

Values:

```text

Incoming Document

Outgoing Document

Decision

Policy

Procedure

Template

ISO Document

Announcement

```

---

# MD-DOC-002

## Document Status

Values:

```text

Draft

Review

Approved

Published

Archived

```

---

# MD-DOC-003

## Document Security Level

Values:

```text

Public

Internal

Restricted

Confidential

```

---

# 11. TASK MASTER DATA

# MD-TASK-001

## Task Priority

Values:

```text

Low

Medium

High

Critical

```

---

# MD-TASK-002

## Task Status

Values:

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

# MD-TASK-003

## Task Type

Values:

```text

Personal

Department

Cross Department

Management

```

---

# 12. KPI MASTER DATA

# MD-KPI-001

## KPI Category

Values:

```text

Company KPI

Department KPI

Employee KPI

```

---

# MD-KPI-002

## KPI Period

Values:

```text

Monthly

Quarterly

Yearly

```

---

# MD-KPI-003

## KPI Status

Values:

```text

Draft

Active

Closed

```

---

# 13. ASSET MASTER DATA

# MD-AST-001

## Asset Type

Values:

```text

Laptop

Desktop

Monitor

Printer

Phone

SIM Card

Furniture

Office Equipment

```

---

# MD-AST-002

## Asset Status

Values:

```text

Available

Allocated

Maintenance

Disposed

```

---

# MD-AST-003

## Asset Condition

Values:

```text

New

Good

Fair

Damaged

```

---

# 14. PROCUREMENT MASTER DATA

# MD-PRO-001

## Procurement Category

Values:

```text

IT Equipment

Office Equipment

Furniture

Software

Service

Training

Other

```

---

# MD-PRO-002

## Procurement Status

Values:

```text

Draft

Pending Approval

Approved

Purchased

Delivered

Completed

Rejected

```

---

# 15. USER & SECURITY MASTER DATA

# MD-SEC-001

## User Status

Values:

```text

Active

Inactive

Locked

```

---

# MD-SEC-002

## Role

Values:

```text

Super Admin

System Admin

HR Manager

HR Officer

Finance Officer

Department Manager

Employee

Director

```

---

# MD-SEC-003

## Login Status

Values:

```text

Success

Failed

Locked

```

---

# 16. NOTIFICATION MASTER DATA

# MD-NOT-001

## Notification Type

Values:

```text

Task

Leave

Recruitment

Payroll

Contract

Asset

Procurement

System

```

---

# MD-NOT-002

## Notification Status

Values:

```text

Unread

Read

```

---

# 17. WORKFLOW MASTER DATA

# MD-WF-001

## Workflow Status

Values:

```text

Draft

Pending

Approved

Rejected

Cancelled

Completed

```

---

# MD-WF-002

## Workflow Decision

Values:

```text

Approve

Reject

Return

Cancel

```

---

# MD-WF-003

## Workflow Step Status

Values:

```text

Waiting

Current

Completed

Skipped

```

---

# 18. FILE MASTER DATA

# MD-FILE-001

## File Type

Values:

```text

PDF

DOCX

XLSX

PPTX

JPG

PNG

ZIP

```

---

# MD-FILE-002

## Storage Location

Values:

```text

SharePoint

OneDrive

```

---

# 19. SYSTEM MASTER DATA

# MD-SYS-001

## Record Status

Values:

```text

Active

Inactive

```

---

# MD-SYS-002

## Audit Action

Values:

```text

Create

Update

Delete

Approve

Reject

Export

Login

Logout

```

---

# 20. DATA VALIDATION RULES

## Unique Fields

```text

EmployeeCode

NationalID

DepartmentCode

ContractNo

DocumentNo

AssetCode

Username

```

---

## Mandatory Audit Fields

```text

CreatedBy

CreatedDate

ModifiedBy

ModifiedDate

IsDeleted

```

---

## Soft Delete Rule

```text

Không xóa vật lý dữ liệu nghiệp vụ

```

---

# 21. MASTER DATA OWNERSHIP

| Data Group | Data Owner |

|------------|------------|

| Organization | HR Manager |

| Employee | HR Manager |

| Recruitment | HR Manager |

| Attendance | HR Officer |

| Leave | HR Officer |

| Payroll | Finance Officer |

| Contract | HR Manager |

| Document | HR Manager |

| Asset | HR Manager |

| Procurement | Finance Officer |

| Security | System Admin |

---

# 22. MASTER DATA APPROVAL

Status:

Approved

Ready For:

- Django Model Design

- API Validation

- Database Constraints

- Import Template Design

- Reporting Development

