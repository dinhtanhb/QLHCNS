# DJANGO MODULE BLUEPRINT

## Project

Internal Administration & Human Resource Management System (IHRMS)

## Version

1.0

## Status

Approved

---

# 1. PURPOSE

Tài liệu này định nghĩa cấu trúc chi tiết cho từng Django App.

Là tài liệu chuẩn để:

- Sinh source code
- Review source code
- Kiểm thử source code
- Đảm bảo tính nhất quán toàn hệ thống

Mọi module phải tuân thủ:

- 03_Database_Design.md
- 04_Security_Design.md
- 05_Backend_Standards.md
- 10_RBAC_Permission_Matrix.md
- 11_Workflow_Definition.md
- 14_Code_Generation_Guide.md

---

# 2. STANDARD APP STRUCTURE

Mọi Django App phải sử dụng cấu trúc:

```text
app_name/

├── models/
│
├── repositories/
│
├── services/
│
├── serializers/
│
├── validators/
│
├── permissions/
│
├── api/
│
├── tests/
│
├── urls.py
│
└── apps.py
```

---

# 3. COMMON MODULE

## App Name

```text
common
```

---

## Purpose

Dùng chung toàn hệ thống.

---

## Components

### Models

```text
BaseModel
```

---

### Services

```text
FileStorageService

DateTimeService
```

---

### Validators

```text
CommonValidator
```

---

### Utilities

```text
ResponseBuilder

PaginationHelper

ExportHelper
```

---

# 4. AUDIT MODULE

## App Name

```text
audit
```

---

## Models

```text
AuditLog

UserLoginLog
```

---

## Repositories

```text
AuditLogRepository
```

---

## Services

```text
AuditService
```

---

## APIs

```text
AuditLogViewSet
```

---

# 5. SECURITY MODULE

## App Name

```text
security
```

---

## Models

```text
User

Role

Permission

RolePermission
```

---

## Services

```text
AuthenticationService

AuthorizationService
```

---

## APIs

```text
AuthViewSet

PermissionViewSet
```

---

# 6. ORGANIZATION MODULE

## App Name

```text
organization
```

---

## Models

```text
Organization

Department

Position

JobTitle
```

---

## Repositories

```text
OrganizationRepository

DepartmentRepository

PositionRepository

JobTitleRepository
```

---

## Services

```text
OrganizationService

DepartmentService

PositionService

JobTitleService
```

---

## APIs

```text
OrganizationViewSet

DepartmentViewSet

PositionViewSet

JobTitleViewSet
```

---

# 7. HUMAN RESOURCE MODULE

## App Name

```text
hrm
```

---

## Models

```text
Employee

EmployeeBankAccount

EmployeeEmergencyContact

EmployeeEducation

EmployeeCertificate

EmployeeAttachment

EmployeeHistory
```

---

## Repositories

```text
EmployeeRepository

EmployeeHistoryRepository
```

---

## Services

```text
EmployeeService

EmployeeTransferService

EmployeeTerminationService

EmployeeHistoryService
```

---

## Validators

```text
EmployeeValidator

NationalIDValidator
```

---

## APIs

```text
EmployeeViewSet

EmployeeTransferViewSet

EmployeeTerminationViewSet
```

---

# 8. RECRUITMENT MODULE

## App Name

```text
recruitment
```

---

## Models

```text
RecruitmentRequest

JobPosting

Candidate

Interview

Offer
```

---

## Repositories

```text
RecruitmentRequestRepository

CandidateRepository

InterviewRepository

OfferRepository
```

---

## Services

```text
RecruitmentRequestService

RecruitmentWorkflowService

CandidateService

InterviewService

OfferService

OnboardingService
```

---

## APIs

```text
RecruitmentRequestViewSet

CandidateViewSet

InterviewViewSet

OfferViewSet
```

---

# 9. ATTENDANCE MODULE

## App Name

```text
attendance
```

---

## Models

```text
WorkShift

Attendance

Overtime

AttendanceAdjustment
```

---

## Repositories

```text
AttendanceRepository

OvertimeRepository

AttendanceAdjustmentRepository
```

---

## Services

```text
AttendanceService

CheckInService

CheckOutService

OvertimeService

AttendanceAdjustmentService
```

---

## APIs

```text
AttendanceViewSet

AttendanceAdjustmentViewSet

OvertimeViewSet
```

---

# 10. LEAVE MODULE

## App Name

```text
leave
```

---

## Models

```text
LeaveType

LeaveRequest

LeaveApproval
```

---

## Repositories

```text
LeaveRequestRepository

LeaveApprovalRepository
```

---

## Services

```text
LeaveRequestService

LeaveApprovalService

LeaveBalanceService
```

---

## APIs

```text
LeaveRequestViewSet

LeaveApprovalViewSet
```

---

# 11. PAYROLL MODULE

## App Name

```text
payroll
```

---

## Models

```text
PayrollPeriod

Payroll

PayrollAllowance

PayrollDeduction

Payslip
```

---

## Repositories

```text
PayrollRepository

PayrollPeriodRepository

PayslipRepository
```

---

## Services

```text
PayrollEngine

PayrollCalculationService

PayrollApprovalService

PayslipService
```

---

## APIs

```text
PayrollViewSet

PayrollPeriodViewSet

PayslipViewSet
```

---

# 12. CONTRACT MODULE

## App Name

```text
contracts
```

---

## Models

```text
ContractType

Contract

ContractAppendix
```

---

## Repositories

```text
ContractRepository

ContractAppendixRepository
```

---

## Services

```text
ContractService

ContractApprovalService

ContractRenewalService

ContractReminderService
```

---

## APIs

```text
ContractViewSet

ContractRenewalViewSet
```

---

# 13. DOCUMENT MODULE

## App Name

```text
documents
```

---

## Models

```text
DocumentCategory

Document

DocumentApproval
```

---

## Repositories

```text
DocumentRepository

DocumentApprovalRepository
```

---

## Services

```text
DocumentService

DocumentApprovalService

DocumentVersionService

DocumentStorageService
```

---

## APIs

```text
DocumentViewSet

DocumentApprovalViewSet
```

---

# 14. TASK MODULE

## App Name

```text
tasks
```

---

## Models

```text
Task

TaskChecklist

TaskComment

TaskAttachment

TaskStatus
```

---

## Repositories

```text
TaskRepository

TaskCommentRepository

TaskChecklistRepository
```

---

## Services

```text
TaskService

TaskAssignmentService

TaskWorkflowService

TaskReminderService

TaskOverdueService
```

---

## APIs

```text
TaskViewSet

TaskCommentViewSet

TaskChecklistViewSet
```

---

# 15. KPI MODULE

## App Name

```text
kpi
```

---

## Models

```text
KPIPeriod

KPITemplate

DepartmentKPI

EmployeeKPI
```

---

## Repositories

```text
KPITemplateRepository

EmployeeKPIRepository

DepartmentKPIRepository
```

---

## Services

```text
KPIAssignmentService

KPICalculationService

KPIEvaluationService

KPIRankingService
```

---

## APIs

```text
KPITemplateViewSet

EmployeeKPIViewSet

DepartmentKPIViewSet
```

---

# 16. ASSET MODULE

## App Name

```text
assets
```

---

## Models

```text
AssetType

Asset

AssetAllocation

AssetMaintenance
```

---

## Repositories

```text
AssetRepository

AssetAllocationRepository

AssetMaintenanceRepository
```

---

## Services

```text
AssetService

AssetAllocationService

AssetReturnService

AssetMaintenanceService

AssetInventoryService
```

---

## APIs

```text
AssetViewSet

AssetAllocationViewSet

AssetMaintenanceViewSet
```

---

# 17. PROCUREMENT MODULE

## App Name

```text
procurement
```

---

## Models

```text
ProcurementRequest

ProcurementItem

ProcurementApproval
```

---

## Repositories

```text
ProcurementRequestRepository

ProcurementApprovalRepository
```

---

## Services

```text
ProcurementService

BudgetApprovalService

ProcurementWorkflowService

ProcurementClosingService
```

---

## APIs

```text
ProcurementRequestViewSet

ProcurementApprovalViewSet
```

---

# 18. DASHBOARD MODULE

## App Name

```text
dashboard
```

---

## Services

```text
DirectorDashboardService

HRDashboardService

ManagerDashboardService

EmployeeDashboardService
```

---

## APIs

```text
DirectorDashboardView

HRDashboardView

ManagerDashboardView

EmployeeDashboardView
```

---

# 19. REPORT MODULE

## App Name

```text
reports
```

---

## Services

```text
HRReportService

RecruitmentReportService

AttendanceReportService

PayrollReportService

TaskReportService

KPIReportService

AssetReportService

ProcurementReportService
```

---

## APIs

```text
ReportViewSet
```

---

# 20. NOTIFICATION MODULE

## App Name

```text
notifications
```

---

## Models

```text
Notification
```

---

## Services

```text
NotificationService

EmailNotificationService

TeamsNotificationService

InAppNotificationService
```

---

## APIs

```text
NotificationViewSet
```

---

# 21. MICROSOFT 365 MODULE

## App Name

```text
m365
```

---

## Services

```text
EntraIDService

OutlookService

TeamsService

SharePointService

OneDriveService

M365SyncService
```

---

## APIs

```text
SharePointViewSet

TeamsViewSet

OutlookViewSet
```

---

# 22. MODEL GENERATION SEQUENCE

## Step 1

```text
Common
```

---

## Step 2

```text
Security

Audit
```

---

## Step 3

```text
Organization
```

---

## Step 4

```text
HRM
```

---

## Step 5

```text
Recruitment
```

---

## Step 6

```text
Attendance

Leave
```

---

## Step 7

```text
Payroll
```

---

## Step 8

```text
Contracts
```

---

## Step 9

```text
Documents
```

---

## Step 10

```text
Tasks
```

---

## Step 11

```text
KPI
```

---

## Step 12

```text
Assets
```

---

## Step 13

```text
Procurement
```

---

## Step 14

```text
Dashboard
```

---

## Step 15

```text
Microsoft 365
```

---

# 23. CODE GENERATION CHECKLIST

Mỗi App phải sinh đủ:

✅ Models

✅ Repository

✅ Services

✅ Serializers

✅ Validators

✅ Permissions

✅ APIs

✅ URLs

✅ Unit Tests

✅ Integration Tests

✅ Swagger

✅ Audit Integration

---

# 24. BLUEPRINT APPROVAL

Status:

Approved

Ready For:

- Django Development
- AI Code Generation
- Module Implementation
- Testing