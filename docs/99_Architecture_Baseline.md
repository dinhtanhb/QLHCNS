# ARCHITECTURE BASELINE

## Project

Internal Administration & Human Resource Management System (IHRMS)

## Version

1.0

## Status

BASELINE APPROVED

## Authority Level

HIGHEST PRIORITY DOCUMENT

---

# 1. PURPOSE

Đây là tài liệu gốc cuối cùng của dự án.

Tài liệu này được sử dụng để:

- Khóa phạm vi dự án
- Khóa kiến trúc
- Khóa nghiệp vụ
- Khóa công nghệ
- Khóa cơ sở dữ liệu
- Khóa workflow
- Khóa API
- Khóa giao diện
- Khóa tiêu chuẩn lập trình

Nếu có mâu thuẫn giữa các tài liệu:

```text
99_Architecture_Baseline.md
```

được ưu tiên cao nhất.

---

# 2. PROJECT BASELINE

## Project Name

Internal Administration & Human Resource Management System

---

## Project Code

IHRMS

---

## Project Type

Internal Enterprise Application

---

## Deployment Type

On-Premise

---

## Organization Type

Internal Administrative and Human Resource Management

---

# 3. SCOPE BASELINE

## IN SCOPE

### Module 01

Organization Management

---

### Module 02

Human Resource Management

---

### Module 03

Recruitment Management

---

### Module 04

Attendance Management

---

### Module 05

Leave Management

---

### Module 06

Payroll Management

---

### Module 07

Contract Management

---

### Module 08

Document Management

---

### Module 09

Task Management

---

### Module 10

KPI Management

---

### Module 11

Asset Management

---

### Module 12

Procurement Management

---

### Module 13

Dashboard & Reporting

---

### Module 14

Microsoft 365 Integration

---

# 4. OUT OF SCOPE

Không thuộc hệ thống:

```text
Donor Management

Grant Management

Community Project Management

Field Activity Management

MEL Operations

M&E Operations

CRM

Sales

Accounting ERP
```

---

# 5. TECHNOLOGY BASELINE

## Backend

```text
Python 3.12

Django 5

Django REST Framework
```

---

## Frontend

```text
Bootstrap 5

AdminLTE 3

HTML5

CSS3

JavaScript

jQuery

AJAX
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

## Authorization

```text
RBAC
```

---

## Storage

```text
SharePoint

OneDrive
```

---

## Web Server

```text
IIS
```

---

## Operating System

```text
Windows Server
```

---

# 6. PROHIBITED TECHNOLOGIES

Không được sử dụng:

```text
FastAPI

Flask

Laravel

Spring Boot

NodeJS

ExpressJS

React

Vue

Angular

NextJS

PostgreSQL

MongoDB

Firebase
```

---

# 7. ARCHITECTURE BASELINE

## Architecture Style

```text
Modular Monolith
```

---

## Application Layers

```text
Presentation Layer

↓

API Layer

↓

Service Layer

↓

Repository Layer

↓

Data Access Layer

↓

Database
```

---

# 8. SOURCE CODE BASELINE

## Project Structure

```text
config

apps

static

templates

media

logs
```

---

## Django App Standard

Every App Must Have

```text
models

repositories

services

serializers

validators

permissions

api

tests
```

---

# 9. DATABASE BASELINE

Database Design Source:

```text
03_Database_Design.md
```

---

## Database Engine

```text
SQL Server
```

---

## Naming Convention

```text
tblEmployee

tblDepartment

tblContract

tblTask
```

---

## Audit Fields

Mandatory

```text
CreatedBy

CreatedDate

ModifiedBy

ModifiedDate

DeletedBy

DeletedDate

IsDeleted
```

---

## Soft Delete

Mandatory

---

## Foreign Key

Mandatory

---

# 10. MASTER DATA BASELINE

Master Data Source

```text
13_Master_Data_Dictionary.md
```

---

## Single Source Of Truth

Master Data chỉ được định nghĩa tại:

```text
13_Master_Data_Dictionary.md
```

---

# 11. SECURITY BASELINE

Security Design Source

```text
04_Security_Design.md
```

---

## Mandatory

```text
JWT

RBAC

Audit Log

HTTPS

Password Policy

Permission Validation

Data Scope Validation
```

---

## Sensitive Data

```text
National ID

Bank Account

Tax Information

Insurance Information

Payroll
```

---

## Mandatory Audit

```text
Employee

Payroll

Contract

Document

Task

KPI

Asset

Procurement
```

---

# 12. RBAC BASELINE

RBAC Source

```text
10_RBAC_Permission_Matrix.md
```

---

Access Control must follow:

```text
Role

Permission

Data Scope
```

---

No Permission Bypass Allowed

---

# 13. WORKFLOW BASELINE

Workflow Source

```text
11_Workflow_Definition.md
```

---

## Mandatory Workflow

```text
Leave

Attendance Adjustment

Recruitment

Onboarding

Offboarding

Payroll

Contract

Document

Task

KPI

Asset

Procurement
```

---

No Custom Workflow Allowed

Without Business Approval

---

# 14. REPORT BASELINE

Report Source

```text
12_Report_Data_Dictionary.md
```

---

## KPI Formula

Không được thay đổi.

---

## Dashboard Formula

Không được hardcode.

---

## Data Source

Phải đúng theo tài liệu.

---

# 15. UI BASELINE

UI Source

```text
06_Frontend_Standards.md

09_UI_UX_Specification.md
```

---

## Theme

```text
Corporate

Administrative

Professional
```

---

## Responsive

```text
Desktop

Tablet

Mobile
```

---

## Standard Screens

```text
List

Create

Edit

Detail
```

---

# 16. API BASELINE

API Source

```text
15_API_Contract_Specification.md
```

---

Base Route

```text
/api/v1
```

---

Response Standard

```json
{
  "success": true,
  "message": "",
  "data": {}
}
```

---

Swagger Required

---

# 17. CODE GENERATION BASELINE

Source

```text
14_Code_Generation_Guide.md
```

---

## Mandatory

```text
Repository Pattern

Service Layer

DTO Pattern

Audit

Validation

Unit Test
```

---

## Forbidden

```text
Business Logic in View

Business Logic in Serializer

Direct ORM Access in Service
```

---

# 18. PAYROLL BASELINE

Payroll Formula

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

Deduction

=

Net Income
```

---

Must Follow

```text
03_Database_Design.md

11_Workflow_Definition.md

12_Report_Data_Dictionary.md
```

---

# 19. DOCUMENT MANAGEMENT BASELINE

Storage

```text
SharePoint

OneDrive
```

---

Database

```text
Metadata Only
```

---

Version Control Mandatory

---

Approval Workflow Mandatory

---

# 20. MICROSOFT 365 BASELINE

Mandatory Integration

```text
Entra ID

Outlook

Teams

SharePoint

OneDrive
```

---

No Alternative Integration

Without Approval

---

# 21. TESTING BASELINE

Source

```text
07_Testing_Standards.md
```

---

Minimum

```text
Unit Test

Integration Test

UAT
```

---

Coverage

```text
>= 80%
```

---

UAT Pass Rate

```text
>= 95%
```

---

# 22. DEPLOYMENT BASELINE

Source

```text
08_Deployment_Standards.md
```

---

Environment

```text
Development

SIT

UAT

Production
```

---

Production Platform

```text
Windows Server

IIS

SQL Server
```

---

# 23. SUCCESS BASELINE

Go Live Allowed Only If

✅ All Modules Completed

✅ Security Passed

✅ UAT Passed

✅ Audit Working

✅ Backup Working

✅ Restore Tested

✅ Microsoft 365 Working

✅ No Critical Defect

✅ No High Defect

---

# 24. CHANGE CONTROL

## Change Request Required

Các thay đổi sau bắt buộc phải có Change Request:

```text
Database

Workflow

RBAC

Payroll Formula

API Contract

Security

Technology Stack

Architecture
```

---

# 25. BASELINE LOCK

Từ thời điểm tài liệu này được phê duyệt:

Architecture

Business Scope

Technology Stack

Database Design

Workflow Design

RBAC

Report Formula

API Contract

Deployment Model

được xem là:

```text
LOCKED
```

và không được thay đổi nếu không có yêu cầu thay đổi chính thức.

---

# 26. BASELINE APPROVAL

Status:

FINAL APPROVED

Architecture State:

LOCKED

Ready For:

✅ Source Code Generation

✅ Backend Development

✅ Frontend Development

✅ Database Development

✅ Testing

✅ Deployment

✅ Production Release