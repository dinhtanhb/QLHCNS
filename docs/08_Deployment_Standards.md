# DEPLOYMENT & OPERATION STANDARDS

## Project

Internal Administration & Human Resource Management System (IHRMS)

## Version

1.0

## Status

Reference baseline - validate environment-specific values before use.

This document is a target standard; it does not prove that a server is configured or that the application is approved for deployment. Review the [server trial readiness guide](Server_Trial_Readiness_2026-09-27.md) before setting up SIT.

---

# 1. PURPOSE

Tài liệu này quy định:

- Kiến trúc triển khai
- Môi trường vận hành
- Chuẩn cấu hình máy chủ
- Chuẩn Backup
- Chuẩn Restore
- Chuẩn Monitoring
- Chuẩn Logging
- Chuẩn Go-Live
- Chuẩn vận hành sau triển khai

Áp dụng cho toàn bộ hệ thống IHRMS.

---

# 2. DEPLOYMENT MODEL

## Deployment Type

```text
On-Premise
```

---

## Infrastructure Type

```text
Physical Server
```

---

## Application Type

```text
Web Application
```

---

## Network Type

```text
Internal Corporate Network
```

---

# 3. ENVIRONMENT ARCHITECTURE

## Environment Structure

```text
Development

↓

Testing (SIT)

↓

UAT

↓

Production
```

---

# 4. DEVELOPMENT ENVIRONMENT

## Purpose

Dùng cho lập trình.

---

## Installed Components

```text
Python 3.12

Django 5

SQL Server Development

VS Code

Git
```

---

# 5. SIT ENVIRONMENT

## Purpose

Kiểm thử tích hợp.

---

## Requirements

```text
Clone cấu hình Production

Database riêng

Storage riêng
```

---

# 6. UAT ENVIRONMENT

## Purpose

Người dùng kiểm thử nghiệp vụ.

---

## Requirements

```text
Dữ liệu mẫu

Workflow đầy đủ

Microsoft 365 Test Account
```

---

# 7. PRODUCTION ENVIRONMENT

## Purpose

Vận hành chính thức.

---

## Components

```text
Windows Server

IIS

Python Runtime

Django Application

SQL Server

Microsoft 365 Integration

SharePoint

OneDrive
```

---

# 8. SERVER STANDARD

## Minimum Server Specification

### CPU

```text
8 Core
```

---

### Memory

```text
32 GB RAM
```

---

### Storage

```text
1 TB SSD
```

---

### Network

```text
1 Gbps
```

---

# 9. STORAGE ALLOCATION

## Operating System

```text
200 GB
```

---

## Application

```text
100 GB
```

---

## Logs

```text
100 GB
```

---

## Database

```text
500 GB
```

---

## Reserved

```text
100 GB
```

---

# 10. WINDOWS SERVER STANDARD

## Supported Version

```text
Windows Server 2022
```

---

## Required Features

```text
IIS

.NET Hosting Bundle

URL Rewrite

Application Request Routing
```

---

# 11. IIS STANDARD

## Website

```text
IHRMS
```

---

## Application Pool

```text
Dedicated Pool
```

---

## Pipeline Mode

```text
Integrated
```

---

## Identity

```text
Dedicated Service Account
```

---

# 12. DATABASE DEPLOYMENT

## Database Engine

```text
Microsoft SQL Server
```

---

## Database Name

```text
IHRMS
```

---

## Environment Database

```text
IHRMS_DEV

IHRMS_TEST

IHRMS_UAT

IHRMS_PROD
```

---

# 13. APPLICATION CONFIGURATION

## Configuration Files

```text
development.env

test.env

uat.env

production.env
```

---

## Sensitive Information

Không commit:

```text
Password

Connection String

Client Secret

JWT Secret
```

---

# 14. SOURCE CODE VERSIONING

## Tool

```text
Git
```

---

## Branch Strategy

```text
main

uat

develop

feature/*
```

---

# 15. RELEASE PROCESS

```text
Development

↓

Code Review

↓

Unit Test

↓

SIT

↓

UAT

↓

Production
```

---

# 16. DATABASE RELEASE PROCESS

```text
Migration Script

↓

Review

↓

Backup

↓

Execute

↓

Verify
```

---

# 17. DEPLOYMENT CHECKLIST

## Pre Deployment

✅ Source Code Approved

✅ Unit Test Passed

✅ Integration Test Passed

✅ UAT Approved

✅ Migration Script Approved

✅ Backup Completed

---

## Deployment

✅ Application Deployed

✅ Configuration Applied

✅ Database Updated

✅ Permissions Assigned

---

## Post Deployment

✅ Login Tested

✅ Dashboard Tested

✅ Workflow Tested

✅ Microsoft 365 Tested

---

# 18. BACKUP STANDARD

## Database Backup

### Full Backup

```text
Daily
```

---

### Time

```text
22:00
```

---

## Transaction Log Backup

```text
Every 1 Hour
```

---

# 19. BACKUP RETENTION

## Daily Backup

```text
30 Days
```

---

## Weekly Backup

```text
12 Weeks
```

---

## Monthly Backup

```text
12 Months
```

---

# 20. FILE BACKUP

## SharePoint

Microsoft 365 Retention Policy.

---

## OneDrive

Microsoft 365 Retention Policy.

---

## Application Logs

Daily Backup.

---

# 21. RESTORE STANDARD

## Database Restore

Thực hiện:

```text
Quarterly
```

---

## Restore Verification

Bắt buộc.

---

## Restore Report

Bắt buộc.

---

# 22. RPO

## Recovery Point Objective

```text
24 Hours
```

---

# 23. RTO

## Recovery Time Objective

```text
8 Hours
```

---

# 24. MONITORING STANDARD

## Monitor Areas

```text
CPU

Memory

Disk

Network

Application

Database
```

---

# 25. APPLICATION MONITORING

## Monitor Services

```text
Authentication

Payroll

Task

Workflow

Microsoft 365
```

---

# 26. DATABASE MONITORING

## Monitor

```text
Database Size

Deadlock

Slow Query

Failed Login

Backup Status
```

---

# 27. LOGGING STANDARD

## Log Levels

```text
Info

Warning

Error

Critical
```

---

## Log Folder

```text
/Logs
```

---

## Retention

```text
90 Days
```

---

# 28. AUDIT MONITORING

Theo dõi:

```text
Payroll Access

Permission Changes

User Creation

Role Changes

Export Activities
```

---

# 29. ALERT STANDARD

## Critical Alerts

```text
Application Stop

Database Offline

Authentication Failure

Backup Failure
```

---

## Notification Channel

```text
Outlook

Microsoft Teams
```

---

# 30. DISASTER RECOVERY

## Disaster Types

```text
Server Failure

Database Corruption

Storage Failure

Network Failure

Security Incident
```

---

## Recovery Procedure

```text
Incident

↓

Assessment

↓

Containment

↓

Restore

↓

Validation

↓

Business Resume
```

---

# 31. SECURITY OPERATION

## User Provisioning

HR Request

↓

IT Approval

↓

Account Creation

↓

Role Assignment

---

## User Deactivation

Employee Leave

↓

Disable Account

↓

Revoke Access

↓

Archive Data

---

# 32. CERTIFICATE MANAGEMENT

## SSL

Mandatory.

---

## Renewal

Annual.

---

# 33. MICROSOFT 365 OPERATION

## Services

```text
Entra ID

Outlook

Teams

SharePoint

OneDrive
```

---

## Health Check

Daily.

---

# 34. MAINTENANCE PLAN

## Daily

Check:

```text
Application Status

Database Status

Backup Status
```

---

## Weekly

Check:

```text
Logs

Disk Space

Failed Jobs
```

---

## Monthly

Check:

```text
Performance

Security

User Accounts

Permissions
```

---

# 35. PATCH MANAGEMENT

## Windows Updates

Monthly.

---

## Python Packages

Quarterly Review.

---

## Django Security Update

Immediate.

---

# 36. USER SUPPORT PROCESS

```text
User Issue

↓

IT Support

↓

Investigation

↓

Resolution

↓

Closure
```

---

# 37. INCIDENT MANAGEMENT

## Priority 1

System Down

Target:

```text
4 Hours
```

---

## Priority 2

Major Function Failure

Target:

```text
8 Hours
```

---

## Priority 3

Minor Function Failure

Target:

```text
2 Business Days
```

---

## Priority 4

Enhancement Request

Target:

```text
Planned Release
```

---

# 38. GO-LIVE ACCEPTANCE CRITERIA

## Infrastructure

✅ IIS Running

✅ SQL Server Running

✅ SSL Active

✅ Backup Active

---

## Security

✅ JWT Active

✅ Entra ID Active

✅ RBAC Active

✅ Audit Active

---

## Business

✅ All Critical Workflows Passed

✅ Payroll Passed

✅ Leave Passed

✅ Recruitment Passed

✅ Task Passed

✅ Procurement Passed

---

## Microsoft 365

✅ Outlook Passed

✅ Teams Passed

✅ SharePoint Passed

✅ OneDrive Passed

---

# 39. POST GO-LIVE SUPPORT

## Hyper Care

Duration:

```text
30 Days
```

---

## Activities

```text
Issue Monitoring

User Support

Performance Monitoring

Bug Fixing
```

---

# 40. OPERATION SUCCESS CRITERIA

Hệ thống được xem là vận hành ổn định khi:

✅ Uptime >= 99.5%

✅ Backup chạy thành công

✅ Restore kiểm chứng thành công

✅ Không có lỗi Critical

✅ Dashboard hoạt động

✅ Workflow hoạt động

✅ Microsoft 365 hoạt động

✅ Người dùng sử dụng ổn định

---

# 41. DEPLOYMENT APPROVAL

Status:

Approved

Ready For:

- Source Code Generation
- Environment Setup
- SIT
- UAT
- Production Deployment