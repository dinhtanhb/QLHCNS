# 03_Database_Design.md

# DATABASE DESIGN DOCUMENT

## Project

Internal Administration & Human Resource Management System (IHRMS)

## Version

1.2

## Status

FINAL APPROVED

---

# 1. DATABASE OBJECTIVES

Hệ thống cơ sở dữ liệu phục vụ:

- Tổ chức
- Nhân sự
- Tuyển dụng
- Chấm công
- Nghỉ phép
- Tiền lương
- Hợp đồng
- Tài liệu
- Công việc
- KPI
- Tài sản
- Mua sắm
- Dashboard
- Microsoft 365

Quy mô thiết kế:

```text
30 nhân sự hiện tại

Mở rộng đến 200 nhân sự
```

---

# 2. DATABASE PRINCIPLES

## DB-001

Chuẩn hóa dữ liệu.

---

## DB-002

Một nguồn dữ liệu duy nhất.

---

## DB-003

Sử dụng Foreign Key cho toàn bộ quan hệ.

---

## DB-004

Toàn bộ dữ liệu nghiệp vụ hỗ trợ Audit.

---

## DB-005

Toàn bộ dữ liệu nghiệp vụ hỗ trợ Soft Delete.

---

## DB-006

Không lưu file vật lý trong SQL Server.

---

## DB-007

File lưu tại:

```text
SharePoint
OneDrive
```

---

## DB-008

Metadata lưu tại SQL Server.

---

# 3. COMMON AUDIT FIELDS

Tất cả bảng nghiệp vụ phải có:

```sql
CreatedBy
CreatedDate

ModifiedBy
ModifiedDate

DeletedBy
DeletedDate

IsDeleted
```

---

# 4. ORGANIZATION MODULE

## tblOrganization

```sql
OrganizationID PK

OrganizationCode

OrganizationName

Description

IsActive
```

---

## tblDepartment

```sql
DepartmentID PK

DepartmentCode

DepartmentName

OrganizationID FK

ManagerEmployeeID FK

Description

IsActive
```

---

## tblPosition

```sql
PositionID PK

PositionCode

PositionName

Description

IsActive
```

---

## tblJobTitle

```sql
JobTitleID PK

JobTitleCode

JobTitleName

Description

IsActive
```

---

# 5. HUMAN RESOURCE MODULE

## tblEmployee

```sql
EmployeeID PK

EmployeeCode

FirstName

LastName

FullName

DateOfBirth

Gender

NationalID

TaxCode

SocialInsuranceNo

PersonalEmail

CompanyEmail

MobilePhone

Address

JoinDate

LeaveDate

DepartmentID FK

PositionID FK

JobTitleID FK

ManagerID FK

EmploymentStatus

PhotoUrl
```

---

## tblEmployeeBankAccount

```sql
BankAccountID PK

EmployeeID FK

BankName

AccountName

AccountNumber

Branch
```

---

## tblEmployeeEmergencyContact

```sql
EmergencyContactID PK

EmployeeID FK

FullName

Relationship

PhoneNumber

Address
```

---

## tblEmployeeEducation

```sql
EducationID PK

EmployeeID FK

Degree

Major

School

GraduationYear
```

---

## tblEmployeeCertificate

```sql
CertificateID PK

EmployeeID FK

CertificateName

IssuedBy

IssueDate

ExpiryDate
```

---

## tblEmployeeAttachment

```sql
AttachmentID PK

EmployeeID FK

DocumentName

DocumentType

DocumentUrl

FileSize
```

---

## tblEmployeeHistory

```sql
HistoryID PK

EmployeeID FK

HistoryType

EffectiveDate

Description
```

---

## tblEmployeeTransfer

```sql
TransferID PK

EmployeeID FK

FromDepartmentID FK

ToDepartmentID FK

EffectiveDate

Reason
```

---

## tblEmployeePromotion

```sql
PromotionID PK

EmployeeID FK

OldPositionID FK

NewPositionID FK

EffectiveDate

Reason
```

---

## tblEmployeeSalaryHistory

```sql
SalaryHistoryID PK

EmployeeID FK

OldSalary

NewSalary

EffectiveDate

Reason
```

---

## tblEmployeeReward

```sql
RewardID PK

EmployeeID FK

RewardType

RewardDate

Amount

Description
```

---

## tblEmployeeDiscipline

```sql
DisciplineID PK

EmployeeID FK

DisciplineType

DisciplineDate

Description
```

---

# 6. RECRUITMENT MODULE

## tblRecruitmentRequest

```sql
RecruitmentRequestID PK

RequestCode

DepartmentID FK

PositionID FK

RequiredQuantity

RequestReason

RequiredDate

Status
```

---

## tblJobPosting

```sql
JobPostingID PK

RecruitmentRequestID FK

PostingTitle

OpenDate

CloseDate

Status
```

---

## tblCandidate

```sql
CandidateID PK

CandidateCode

FullName

PhoneNumber

Email

CurrentAddress

Source

CVFileUrl

Status
```

---

## tblInterview

```sql
InterviewID PK

CandidateID FK

InterviewDate

InterviewType

InterviewerID FK

Result

Comments
```

---

## tblOffer

```sql
OfferID PK

CandidateID FK

OfferDate

ExpectedJoinDate

SalaryOffer

Status
```

---

# 7. CALENDAR MODULE

## tblHoliday

```sql
HolidayID PK

HolidayCode

HolidayName

HolidayDate

Description

IsActive
```

---

## tblWorkingCalendar

```sql
WorkingCalendarID PK

CalendarYear

WorkingDaysPerMonth

WorkingHoursPerDay

IsDefault
```

---

# 8. ATTENDANCE MODULE

## tblWorkShift

```sql
WorkShiftID PK

ShiftCode

ShiftName

StartTime

EndTime
```

---

## tblAttendance

```sql
AttendanceID PK

EmployeeID FK

AttendanceDate

CheckInTime

CheckOutTime

WorkingHours

Status
```

---

## tblOvertime

```sql
OvertimeID PK

EmployeeID FK

WorkDate

StartTime

EndTime

TotalHours

Status
```

---

## tblAttendanceAdjustment

```sql
AdjustmentID PK

EmployeeID FK

AttendanceDate

Reason

ApprovedBy

Status
```

---

# 9. LEAVE MODULE

## tblLeaveType

```sql
LeaveTypeID PK

LeaveTypeCode

LeaveTypeName

IsPaid
```

---

## tblLeaveRequest

```sql
LeaveRequestID PK

EmployeeID FK

LeaveTypeID FK

FromDate

ToDate

TotalDays

Reason

Status
```

---

## tblLeaveApproval

```sql
ApprovalID PK

LeaveRequestID FK

ApproverID FK

ApprovalLevel

Decision

DecisionDate
```

---

# 10. SALARY STRUCTURE

## tblSalaryGrade

```sql
SalaryGradeID PK

GradeCode

GradeName

Description
```

---

## tblSalaryStructure

```sql
SalaryStructureID PK

SalaryGradeID FK

BasicSalary

PositionAllowance

ResponsibilityAllowance

PhoneAllowance

TransportationAllowance

MealAllowance

EffectiveDate
```

---

## tblEmployeeSalary

```sql
EmployeeSalaryID PK

EmployeeID FK

SalaryGradeID FK

CurrentBasicSalary

EffectiveDate

EndDate

Status
```

---

# 11. PAYROLL MODULE

## tblPayrollPeriod

```sql
PayrollPeriodID PK

PayrollMonth

PayrollYear

StartDate

EndDate

Status
```

---

## tblPayroll

```sql
PayrollID PK

PayrollPeriodID FK

EmployeeID FK

BasicSalary

Allowance

OvertimeAmount

GrossIncome

InsuranceAmount

TaxAmount

DeductionAmount

NetIncome
```

---

## tblPayrollAllowance

```sql
AllowanceID PK

PayrollID FK

AllowanceType

Amount
```

---

## tblPayrollDeduction

```sql
DeductionID PK

PayrollID FK

DeductionType

Amount
```

---

## tblPayslip

```sql
PayslipID PK

PayrollID FK

GeneratedDate

FileUrl
```

---

# 12. CONTRACT MODULE

## tblContractType

```sql
ContractTypeID PK

ContractTypeCode

ContractTypeName
```

---

## tblContract

```sql
ContractID PK

EmployeeID FK

ContractTypeID FK

ContractNo

StartDate

EndDate

BasicSalary

Status
```

---

## tblContractAppendix

```sql
AppendixID PK

ContractID FK

AppendixNo

EffectiveDate

Description
```

---

# 13. DOCUMENT MODULE

## tblDocumentCategory

```sql
CategoryID PK

CategoryCode

CategoryName
```

---

## tblDocument

```sql
DocumentID PK

DocumentNo

DocumentName

CategoryID FK

VersionNo

EffectiveDate

DocumentUrl

Status
```

---

## tblDocumentApproval

```sql
ApprovalID PK

DocumentID FK

ApproverID FK

ApprovalDate

Decision
```

---

# 14. TASK MODULE

## tblTaskStatus

```sql
TaskStatusID PK

StatusCode

StatusName
```

---

## tblTask

```sql
TaskID PK

TaskCode

TaskName

Description

ParentTaskID

CreatedByEmployeeID FK

AssignedToEmployeeID FK

DepartmentID FK

Priority

StartDate

DueDate

TaskStatusID FK
```

---

## tblTaskChecklist

```sql
ChecklistID PK

TaskID FK

ChecklistItem

IsCompleted
```

---

## tblTaskComment

```sql
CommentID PK

TaskID FK

EmployeeID FK

CommentText

CommentDate
```

---

## tblTaskAttachment

```sql
AttachmentID PK

TaskID FK

DocumentUrl

FileName
```

---

# 15. KPI MODULE

## tblKPIPeriod

```sql
KPIPeriodID PK

Year

Quarter

Month
```

---

## tblKPITemplate

```sql
KPITemplateID PK

KPIName

Description

Weight

TargetValue
```

---

## tblCompanyKPI

```sql
CompanyKPIID PK

KPITemplateID FK

KPIPeriodID FK

Target

Actual

Achievement

Score
```

---

## tblDepartmentKPI

```sql
DepartmentKPIID PK

DepartmentID FK

KPITemplateID FK

KPIPeriodID FK

Target

Actual

Achievement
```

---

## tblEmployeeKPI

```sql
EmployeeKPIID PK

EmployeeID FK

KPITemplateID FK

KPIPeriodID FK

Target

Actual

Achievement

Score
```

---

# 16. ASSET MODULE

## tblAssetType

```sql
AssetTypeID PK

AssetTypeCode

AssetTypeName
```

---

## tblAsset

```sql
AssetID PK

AssetCode

AssetName

AssetTypeID FK

PurchaseDate

PurchaseValue

Status
```

---

## tblAssetAllocation

```sql
AllocationID PK

AssetID FK

EmployeeID FK

AssignedDate

ReturnDate
```

---

## tblAssetMaintenance

```sql
MaintenanceID PK

AssetID FK

MaintenanceDate

Description

Cost
```

---

# 17. PROCUREMENT MODULE

## tblProcurementRequest

```sql
ProcurementRequestID PK

RequestNo

RequestedBy FK

DepartmentID FK

RequestDate

Reason

Status
```

---

## tblProcurementItem

```sql
ItemID PK

ProcurementRequestID FK

ItemName

Quantity

EstimatedCost
```

---

## tblProcurementApproval

```sql
ApprovalID PK

ProcurementRequestID FK

ApproverID FK

ApprovalLevel

Decision

DecisionDate
```

---

# 18. NOTIFICATION MODULE

## tblNotification

```sql
NotificationID PK

EmployeeID FK

NotificationType

Title

Message

IsRead

CreatedDate
```

---

# 19. SECURITY MODULE

## tblRole

```sql
RoleID PK

RoleCode

RoleName
```

---

## tblPermission

```sql
PermissionID PK

PermissionCode

PermissionName
```

---

## tblRolePermission

```sql
RolePermissionID PK

RoleID FK

PermissionID FK
```

---

## tblUser

```sql
UserID PK

EmployeeID FK

Username

Email

RoleID FK

IsActive
```

---

## tblDelegation

```sql
DelegationID PK

DelegatorEmployeeID FK

DelegateEmployeeID FK

DelegationFrom

DelegationTo

Reason

Status
```

---

# 20. AUDIT MODULE

## tblAuditLog

```sql
AuditLogID PK

TableName

RecordID

ActionType

OldValue

NewValue

ChangedBy

ChangedDate
```

---

## tblUserLoginLog

```sql
LoginLogID PK

UserID FK

LoginTime

LogoutTime

IPAddress
```

---

# 21. WORKFLOW MODULE

## tblWorkflowDefinition

```sql
WorkflowID PK

WorkflowCode

WorkflowName
```

---

## tblWorkflowStep

```sql
WorkflowStepID PK

WorkflowID FK

StepNo

RoleID FK

StepName
```

---

## tblWorkflowTransaction

```sql
WorkflowTransactionID PK

WorkflowID FK

ReferenceID

CurrentStep

Status
```

---

# 22. RELATIONSHIP SUMMARY

```text
Organization
└── Department

Department
└── Employee

Position
└── Employee

JobTitle
└── Employee

Employee
├── Attendance
├── Leave
├── Payroll
├── Contract
├── EmployeeSalary
├── KPI
└── Asset Allocation

RecruitmentRequest
└── JobPosting

Candidate
└── Interview

Contract
└── ContractAppendix

Task
├── TaskChecklist
├── TaskComment
└── TaskAttachment

Asset
├── AssetAllocation
└── AssetMaintenance
```

---

# 23. INDEX STRATEGY

Tạo Index cho:

```sql
EmployeeCode

NationalID

DepartmentCode

ContractNo

DocumentNo

TaskCode

AssetCode

RequestNo

AttendanceDate

KPIPeriodID

PayrollMonth

PayrollYear

Status
```

---

# 24. DATA RETENTION

## Employee

```text
Permanent
```

---

## Payroll

```text
10 Years
```

---

## Contract

```text
10 Years
```

---

## Audit Log

```text
5 Years
```

---

## Documents

```text
5 Years Minimum
```

---

# 25. DATABASE APPROVAL

Status:

FINAL APPROVED

Version:

1.1

Architecture:

LOCKED

Ready For:

✅ Security Design

✅ Django Models

✅ API Development

✅ UI Development

✅ Testing

✅ Source Code Generation

# 03A_Database_Design_Addendum_Physical_Schema.md

# PHỤ LỤC: ĐẶC TẢ VẬT LÝ CƠ SỞ DỮ LIỆU (PHYSICAL SCHEMA ADDENDUM)

## Project

Internal Administration & Human Resource Management System (IHRMS)

## Bổ sung cho

03_Database_Design.md (v1.1)

## Version

1.0

## Status

Draft — chờ HR Manager / Kế toán / IT xác nhận trước khi khóa (LOCKED)

## Lý do bổ sung

`03_Database_Design.md` mới dừng ở mức liệt kê tên bảng, tên field và đánh dấu PK/FK (mức Logical/Conceptual Model). Tài liệu chưa có kiểu dữ liệu, độ dài, nullable, default, index, unique constraint — là những thông tin bắt buộc để:

- Viết đúng Django Model (`models.py`)
- Sinh migration chính xác ngay từ đầu, tránh sửa lại nhiều lần
- Validate dữ liệu tại tầng API/Serializer đúng với tầng DB
- Import dữ liệu Excel ban đầu không bị lỗi kiểu dữ liệu

Tài liệu này **không thay đổi** cấu trúc bảng/field đã duyệt ở `03_Database_Design.md`, chỉ bổ sung thuộc tính vật lý cho từng field.

Sau khi các bên xác nhận, nội dung file này sẽ được gộp thẳng vào `03_Database_Design.md` và nâng version lên 1.2 — LOCKED.

---

# 1. QUYẾT ĐỊNH KIẾN TRÚC BỔ SUNG — CHIẾN LƯỢC KHÓA CHÍNH (PK STRATEGY)

`05_Backend_Standards.md` mục 7 hiện ghi "Model phải sử dụng UUID hoặc Identity Key" — để ngỏ hai lựa chọn sẽ dẫn đến mỗi module implement một kiểu khác nhau. Đề xuất chốt một chuẩn duy nhất:

## ADR-DB-001 — Primary Key Standard

**Quyết định:** Toàn bộ PK nghiệp vụ sử dụng `BIGINT IDENTITY(1,1)`.

**Lý do:**
- Hệ thống triển khai On-Premise, SQL Server, quy mô 30-200 người dùng, không cần đồng bộ dữ liệu đa hệ thống phân tán → không có lý do kỹ thuật bắt buộc dùng UUID.
- `BIGINT IDENTITY` cho hiệu năng clustered index và JOIN tốt hơn `UNIQUEIDENTIFIER` (UUID) trên SQL Server, đặc biệt với các bảng giao dịch lớn theo thời gian (Attendance, AuditLog, WorkflowTransaction).
- Đơn giản hóa việc đọc log, debug, và thao tác dữ liệu thủ công khi cần (khắc phục sự cố, đối chiếu số liệu kế toán).

**Ngoại lệ được phép:**
- `tblUser.ExternalObjectId` (Entra ID Object ID) — kiểu `UNIQUEIDENTIFIER`, dùng để map với tài khoản Microsoft 365, KHÔNG dùng làm PK.
- Các bảng có nhu cầu chia sẻ ID ra bên ngoài hệ thống (ví dụ file token công khai) có thể có thêm cột `PublicGuid UNIQUEIDENTIFIER DEFAULT NEWID()` song song với PK, không thay thế PK.

**Django mapping:**
```python
id = models.BigAutoField(primary_key=True)
```
(Django tự sinh cột PK tên `id` nếu không khai báo khác — xem quy tắc đặt tên PK ở mục 2 bên dưới để quyết định giữ `id` hay đặt tên riêng như `EmployeeID`.)

---

# 2. QUY ƯỚC KIỂU DỮ LIỆU CHUẨN (DATA TYPE STANDARD)

| Loại field (theo hậu tố tên) | Kiểu SQL Server | Ghi chú |
|---|---|---|
| `...ID` (PK) | `BIGINT IDENTITY(1,1)` | Xem ADR-DB-001 |
| `...ID` (FK) | `BIGINT` | Cùng kiểu với PK được tham chiếu; `NULL` cho phép nếu quan hệ optional |
| `...Code` | `NVARCHAR(50)` | UNIQUE trong phạm vi bảng, dùng cho tra cứu nghiệp vụ |
| `...Name`, `FullName`, `FirstName`, `LastName` | `NVARCHAR(200)` | Hỗ trợ tiếng Việt có dấu |
| `Description`, `Reason`, `Comments`, `CommentText` | `NVARCHAR(1000)` | Có thể để `NVARCHAR(MAX)` nếu nghiệp vụ cần văn bản dài (vd. `CommentText`, `Description` của Document) |
| `...Email` | `NVARCHAR(100)` | Có CHECK constraint định dạng email ở tầng ứng dụng, không ở DB |
| `...Phone`, `MobilePhone`, `PhoneNumber` | `NVARCHAR(20)` | Lưu dạng chuỗi, không dùng số nguyên (tránh mất số 0 đầu) |
| `Address`, `CurrentAddress` | `NVARCHAR(500)` | |
| `NationalID` (CCCD) | `NVARCHAR(20)` | **Xem mục 5 — dữ liệu nhạy cảm, cần mã hóa** |
| `TaxCode` (MST cá nhân) | `NVARCHAR(20)` | |
| `SocialInsuranceNo` (Số BHXH) | `NVARCHAR(20)` | **Dữ liệu nhạy cảm** |
| `AccountNumber` | `NVARCHAR(30)` | **Dữ liệu nhạy cảm** |
| `...Date`, `...Day` (chỉ ngày) | `DATE` | VD: `DateOfBirth`, `JoinDate`, `EffectiveDate`, `FromDate`, `ToDate`, `AttendanceDate` |
| `...Time` (giờ trong ngày) | `TIME(0)` | VD: `StartTime`, `EndTime`, `CheckInTime`, `CheckOutTime` |
| `...DateTime`, `CreatedDate`, `ModifiedDate`, `DeletedDate`, `LoginTime`, `LogoutTime`, `CommentDate`, `ChangedDate` | `DATETIME2(0)` | Ghi nhận cả ngày lẫn giờ, mốc thời gian hệ thống |
| Số tiền: `...Salary`, `...Amount`, `...Cost`, `...Value`, `GrossIncome`, `NetIncome` | `DECIMAL(18,2)` | Đơn vị VNĐ, không dùng FLOAT/REAL |
| Số lượng: `Quantity`, `RequiredQuantity`, `TotalDays`, `TotalHours`, `WorkingHours`, `WorkingDaysPerMonth` | `DECIMAL(9,2)` | Cho phép số thập phân (nửa ngày phép, giờ lẻ) |
| Tỷ lệ/điểm: `Weight`, `Achievement`, `Score` | `DECIMAL(9,2)` | |
| `IsActive`, `IsDeleted`, `IsPaid`, `IsDefault`, `IsCompleted`, `IsRead` | `BIT` | Default tương ứng, xem mục 3 |
| `Status` (dùng chuỗi trạng thái cố định) | `NVARCHAR(30)` | Danh sách giá trị cố định — khuyến nghị chuyển sang bảng danh mục hoặc `CHECK CONSTRAINT`, xem mục 6 |
| `...Url`, `PhotoUrl`, `CVFileUrl`, `FileUrl`, `DocumentUrl` | `NVARCHAR(500)` | Lưu đường dẫn SharePoint/OneDrive, KHÔNG lưu file (đúng DB-006/DB-007) |
| `FileSize` | `BIGINT` | Đơn vị byte |
| `IPAddress` | `NVARCHAR(45)` | Hỗ trợ cả IPv4 và IPv6 |
| `OldValue`, `NewValue` (AuditLog) | `NVARCHAR(MAX)` | Lưu JSON snapshot |
| `Year`, `Quarter`, `Month`, `PayrollMonth`, `PayrollYear`, `CalendarYear`, `StepNo`, `ApprovalLevel`, `CurrentStep` | `SMALLINT` | |
| `Gender` | `NVARCHAR(10)` | Giá trị: `Male` / `Female` / `Other` |

---

# 3. TRƯỜNG AUDIT CHUẨN (bổ sung kiểu dữ liệu cho mục 3 của 03_Database_Design.md)

```sql
CreatedBy       BIGINT          NOT NULL        -- FK -> tblUser.UserID
CreatedDate     DATETIME2(0)    NOT NULL DEFAULT SYSUTCDATETIME()
ModifiedBy      BIGINT          NULL            -- FK -> tblUser.UserID
ModifiedDate    DATETIME2(0)    NULL
DeletedBy       BIGINT          NULL            -- FK -> tblUser.UserID
DeletedDate     DATETIME2(0)    NULL
IsDeleted       BIT             NOT NULL DEFAULT 0
```

**Quy tắc thời gian:** toàn bộ `DATETIME2` lưu theo UTC (`SYSUTCDATETIME()`), quy đổi sang giờ Việt Nam (UTC+7) ở tầng hiển thị/Frontend — tránh sai lệch khi server đổi giờ hoặc mở rộng multi-region sau này.

---

# 4. ĐẶC TẢ CHI TIẾT THEO BẢNG (72 BẢNG)

> Quy ước đọc: field không ghi chú NULL/NOT NULL mặc định là `NOT NULL`. Mọi bảng nghiệp vụ tự động có đủ 7 trường Audit ở mục 3 (không lặp lại bên dưới để đỡ dài). Bảng danh mục thuần (LeaveType, ContractType, TaskStatus, AssetType, DocumentCategory, Role, Permission...) tối thiểu cần `CreatedDate`, `IsDeleted`.

## 4.1 MODULE ORGANIZATION

### tblOrganization
| Field | Type | Null | Ghi chú |
|---|---|---|---|
| OrganizationID | BIGINT IDENTITY | PK | |
| OrganizationCode | NVARCHAR(50) | NOT NULL | UNIQUE |
| OrganizationName | NVARCHAR(200) | NOT NULL | |
| Description | NVARCHAR(1000) | NULL | |
| IsActive | BIT | NOT NULL DEFAULT 1 | |

### tblDepartment
| Field | Type | Null | Ghi chú |
|---|---|---|---|
| DepartmentID | BIGINT IDENTITY | PK | |
| DepartmentCode | NVARCHAR(50) | NOT NULL | UNIQUE |
| DepartmentName | NVARCHAR(200) | NOT NULL | |
| OrganizationID | BIGINT | NOT NULL | FK → tblOrganization |
| ManagerEmployeeID | BIGINT | NULL | FK → tblEmployee (phòng mới lập có thể chưa có trưởng phòng) |
| Description | NVARCHAR(1000) | NULL | |
| IsActive | BIT | NOT NULL DEFAULT 1 | |

### tblPosition / tblJobTitle
| Field | Type | Null | Ghi chú |
|---|---|---|---|
| PositionID / JobTitleID | BIGINT IDENTITY | PK | |
| PositionCode / JobTitleCode | NVARCHAR(50) | NOT NULL | UNIQUE |
| PositionName / JobTitleName | NVARCHAR(200) | NOT NULL | |
| Description | NVARCHAR(1000) | NULL | |
| IsActive | BIT | NOT NULL DEFAULT 1 | |

## 4.2 MODULE HUMAN RESOURCE

### tblEmployee
| Field | Type | Null | Ghi chú |
|---|---|---|---|
| EmployeeID | BIGINT IDENTITY | PK | |
| EmployeeCode | NVARCHAR(50) | NOT NULL | UNIQUE — theo BR-001 (mỗi NV chỉ 1 mã) |
| FirstName | NVARCHAR(100) | NOT NULL | |
| LastName | NVARCHAR(100) | NOT NULL | |
| FullName | NVARCHAR(200) | NOT NULL | Computed hoặc lưu song song để tối ưu tìm kiếm/báo cáo |
| DateOfBirth | DATE | NOT NULL | |
| Gender | NVARCHAR(10) | NOT NULL | |
| NationalID | NVARCHAR(20) | NOT NULL | UNIQUE, **mã hóa** — xem mục 5 |
| TaxCode | NVARCHAR(20) | NULL | |
| SocialInsuranceNo | NVARCHAR(20) | NULL | **Mã hóa** |
| PersonalEmail | NVARCHAR(100) | NULL | |
| CompanyEmail | NVARCHAR(100) | NOT NULL | UNIQUE |
| MobilePhone | NVARCHAR(20) | NOT NULL | |
| Address | NVARCHAR(500) | NULL | |
| JoinDate | DATE | NOT NULL | |
| LeaveDate | DATE | NULL | |
| DepartmentID | BIGINT | NOT NULL | FK — theo BR-002 (1 NV thuộc 1 phòng tại 1 thời điểm) |
| PositionID | BIGINT | NOT NULL | FK |
| JobTitleID | BIGINT | NULL | FK |
| ManagerID | BIGINT | NULL | FK → tblEmployee (self-reference) |
| EmploymentStatus | NVARCHAR(30) | NOT NULL DEFAULT 'Active' | Xem danh mục trạng thái mục 6 |
| PhotoUrl | NVARCHAR(500) | NULL | |

*(Các bảng con: tblEmployeeBankAccount, tblEmployeeEmergencyContact, tblEmployeeEducation, tblEmployeeCertificate, tblEmployeeAttachment, tblEmployeeHistory, tblEmployeeTransfer, tblEmployeePromotion, tblEmployeeSalaryHistory, tblEmployeeReward, tblEmployeeDiscipline: áp dụng quy ước chung mục 2 — `...ID` PK là BIGINT IDENTITY, `EmployeeID`/`...ID` FK là BIGINT NOT NULL, `...Date`/`EffectiveDate` là DATE, `Amount`/`OldSalary`/`NewSalary` là DECIMAL(18,2), `Description`/`Reason` là NVARCHAR(1000), `DocumentUrl`/`CVFileUrl` là NVARCHAR(500), `FileSize` là BIGINT.)*

**Riêng lưu ý:**
- `tblEmployeeAttachment.DocumentType` → `NVARCHAR(50)`, nên ràng buộc danh sách giá trị ở tầng ứng dụng (CCCD, Bằng cấp, Hợp đồng, Khác...).
- `tblEmployeeCertificate.ExpiryDate` → `DATE NULL` (không phải chứng chỉ nào cũng có hạn).

## 4.3 MODULE RECRUITMENT

### tblRecruitmentRequest
| Field | Type | Null |
|---|---|---|
| RecruitmentRequestID | BIGINT IDENTITY | PK |
| RequestCode | NVARCHAR(50) | NOT NULL, UNIQUE |
| DepartmentID | BIGINT | NOT NULL, FK |
| PositionID | BIGINT | NOT NULL, FK |
| RequiredQuantity | SMALLINT | NOT NULL |
| RequestReason | NVARCHAR(1000) | NULL |
| RequiredDate | DATE | NOT NULL |
| Status | NVARCHAR(30) | NOT NULL DEFAULT 'Draft' |

### tblJobPosting
`JobPostingID` PK · `RecruitmentRequestID` FK NOT NULL · `PostingTitle NVARCHAR(300)` · `OpenDate DATE` · `CloseDate DATE NULL` · `Status NVARCHAR(30)`.

### tblCandidate
`CandidateID` PK · `CandidateCode NVARCHAR(50) UNIQUE` · `FullName NVARCHAR(200)` · `PhoneNumber NVARCHAR(20)` · `Email NVARCHAR(100)` · `CurrentAddress NVARCHAR(500) NULL` · `Source NVARCHAR(100) NULL` · `CVFileUrl NVARCHAR(500) NULL` · `Status NVARCHAR(30)`.

### tblInterview
`InterviewID` PK · `CandidateID` FK NOT NULL · `InterviewDate DATETIME2(0)` · `InterviewType NVARCHAR(50)` · `InterviewerID BIGINT NOT NULL FK → tblEmployee` · `Result NVARCHAR(30) NULL` · `Comments NVARCHAR(1000) NULL`.

### tblOffer
`OfferID` PK · `CandidateID` FK NOT NULL · `OfferDate DATE` · `ExpectedJoinDate DATE` · `SalaryOffer DECIMAL(18,2)` · `Status NVARCHAR(30)`.

## 4.4 MODULE CALENDAR / ATTENDANCE

### tblHoliday
`HolidayID` PK · `HolidayCode NVARCHAR(50) UNIQUE` · `HolidayName NVARCHAR(200)` · `HolidayDate DATE UNIQUE` · `Description NVARCHAR(500) NULL` · `IsActive BIT DEFAULT 1`.

### tblWorkingCalendar
`WorkingCalendarID` PK · `CalendarYear SMALLINT` · `WorkingDaysPerMonth DECIMAL(4,1)` · `WorkingHoursPerDay DECIMAL(4,1)` · `IsDefault BIT DEFAULT 0`.

### tblWorkShift
`WorkShiftID` PK · `ShiftCode NVARCHAR(50) UNIQUE` · `ShiftName NVARCHAR(100)` · `StartTime TIME(0)` · `EndTime TIME(0)`.

### tblAttendance
`AttendanceID` PK · `EmployeeID` FK NOT NULL · `AttendanceDate DATE NOT NULL` · `CheckInTime TIME(0) NULL` · `CheckOutTime TIME(0) NULL` · `WorkingHours DECIMAL(4,2) NULL` · `Status NVARCHAR(30)`.
**Constraint:** `UNIQUE (EmployeeID, AttendanceDate)` — mỗi nhân viên chỉ một bản ghi công/ngày.

### tblOvertime
`OvertimeID` PK · `EmployeeID` FK NOT NULL · `WorkDate DATE` · `StartTime TIME(0)` · `EndTime TIME(0)` · `TotalHours DECIMAL(4,2)` · `Status NVARCHAR(30)`.

### tblAttendanceAdjustment
`AdjustmentID` PK · `EmployeeID` FK NOT NULL · `AttendanceDate DATE` · `Reason NVARCHAR(500)` · `ApprovedBy BIGINT NULL FK → tblEmployee` · `Status NVARCHAR(30)`.

## 4.5 MODULE LEAVE

### tblLeaveType
`LeaveTypeID` PK · `LeaveTypeCode NVARCHAR(50) UNIQUE` · `LeaveTypeName NVARCHAR(100)` · `IsPaid BIT DEFAULT 1`.

### tblLeaveRequest
`LeaveRequestID` PK · `EmployeeID` FK NOT NULL · `LeaveTypeID` FK NOT NULL · `FromDate DATE` · `ToDate DATE` · `TotalDays DECIMAL(4,1)` (hỗ trợ nghỉ nửa ngày) · `Reason NVARCHAR(500) NULL` · `Status NVARCHAR(30)`.
**Constraint:** `CHECK (ToDate >= FromDate)`.

### tblLeaveApproval
`ApprovalID` PK · `LeaveRequestID` FK NOT NULL · `ApproverID BIGINT NOT NULL FK → tblEmployee` · `ApprovalLevel SMALLINT` · `Decision NVARCHAR(20) NULL` · `DecisionDate DATETIME2(0) NULL`.

## 4.6 SALARY STRUCTURE

### tblSalaryGrade
`SalaryGradeID` PK · `GradeCode NVARCHAR(50) UNIQUE` · `GradeName NVARCHAR(100)` · `Description NVARCHAR(500) NULL`.

### tblSalaryStructure
`SalaryStructureID` PK · `SalaryGradeID` FK NOT NULL · `BasicSalary DECIMAL(18,2)` · `PositionAllowance`, `ResponsibilityAllowance`, `PhoneAllowance`, `TransportationAllowance`, `MealAllowance` đều `DECIMAL(18,2) DEFAULT 0` · `EffectiveDate DATE`.

### tblEmployeeSalary
`EmployeeSalaryID` PK · `EmployeeID` FK NOT NULL · `SalaryGradeID` FK NOT NULL · `CurrentBasicSalary DECIMAL(18,2)` · `EffectiveDate DATE` · `EndDate DATE NULL` · `Status NVARCHAR(30)`.

## 4.7 MODULE PAYROLL

### tblPayrollPeriod
`PayrollPeriodID` PK · `PayrollMonth SMALLINT (1-12)` · `PayrollYear SMALLINT` · `StartDate DATE` · `EndDate DATE` · `Status NVARCHAR(30)`.
**Constraint:** `UNIQUE (PayrollMonth, PayrollYear)`.

### tblPayroll
`PayrollID` PK · `PayrollPeriodID` FK NOT NULL · `EmployeeID` FK NOT NULL · `BasicSalary`, `Allowance`, `OvertimeAmount`, `GrossIncome`, `InsuranceAmount`, `TaxAmount`, `DeductionAmount`, `NetIncome` đều `DECIMAL(18,2)`.
**Constraint:** `UNIQUE (PayrollPeriodID, EmployeeID)` — theo BR-005, khi `PayrollPeriod.Status = 'Locked'` thì record `tblPayroll` liên quan không được UPDATE trực tiếp (kiểm soát ở tầng Service, không phải DB constraint).

### tblPayrollAllowance / tblPayrollDeduction
`AllowanceID`/`DeductionID` PK · `PayrollID` FK NOT NULL · `AllowanceType`/`DeductionType NVARCHAR(50)` · `Amount DECIMAL(18,2)`.

### tblPayslip
`PayslipID` PK · `PayrollID` FK NOT NULL UNIQUE · `GeneratedDate DATETIME2(0)` · `FileUrl NVARCHAR(500)`.

## 4.8 MODULE CONTRACT

### tblContractType
`ContractTypeID` PK · `ContractTypeCode NVARCHAR(50) UNIQUE` · `ContractTypeName NVARCHAR(100)`.

### tblContract
`ContractID` PK · `EmployeeID` FK NOT NULL · `ContractTypeID` FK NOT NULL · `ContractNo NVARCHAR(50) UNIQUE` · `StartDate DATE` · `EndDate DATE NULL` (hợp đồng không xác định thời hạn → NULL) · `BasicSalary DECIMAL(18,2)` · `Status NVARCHAR(30)`.

### tblContractAppendix
`AppendixID` PK · `ContractID` FK NOT NULL · `AppendixNo NVARCHAR(50)` · `EffectiveDate DATE` · `Description NVARCHAR(1000) NULL`.

## 4.9 MODULE DOCUMENT

### tblDocumentCategory
`CategoryID` PK · `CategoryCode NVARCHAR(50) UNIQUE` · `CategoryName NVARCHAR(100)`.

### tblDocument
`DocumentID` PK · `DocumentNo NVARCHAR(50) UNIQUE` · `DocumentName NVARCHAR(300)` · `CategoryID` FK NOT NULL · `VersionNo NVARCHAR(20) DEFAULT '1.0'` (theo BR-007, tài liệu phát hành phải có phiên bản) · `EffectiveDate DATE NULL` · `DocumentUrl NVARCHAR(500)` · `Status NVARCHAR(30)`.

### tblDocumentApproval
`ApprovalID` PK · `DocumentID` FK NOT NULL · `ApproverID BIGINT NOT NULL FK → tblEmployee` · `ApprovalDate DATETIME2(0) NULL` · `Decision NVARCHAR(20) NULL`.

## 4.10 MODULE TASK

### tblTaskStatus
`TaskStatusID` PK · `StatusCode NVARCHAR(30) UNIQUE` · `StatusName NVARCHAR(100)`.

### tblTask
`TaskID` PK · `TaskCode NVARCHAR(50) UNIQUE` · `TaskName NVARCHAR(300)` · `Description NVARCHAR(MAX) NULL` · `ParentTaskID BIGINT NULL FK → tblTask` (self-reference, hỗ trợ sub-task) · `CreatedByEmployeeID` FK NOT NULL · `AssignedToEmployeeID BIGINT NULL FK` (nullable vì FR-TASK-003 cho phép giao nhiều người — xem lưu ý bên dưới) · `DepartmentID BIGINT NULL FK` · `Priority NVARCHAR(20)` · `StartDate DATE NULL` · `DueDate DATE NULL` · `TaskStatusID` FK NOT NULL.

**⚠️ Lưu ý thiết kế cần xác nhận:** `01_BRD_MASTER.md` (FR-TASK-003) yêu cầu "Giao nhiều người" cho một công việc, nhưng `tblTask` chỉ có một cột `AssignedToEmployeeID` (quan hệ 1-N). Đề xuất bổ sung bảng `tblTaskAssignee (TaskAssigneeID PK, TaskID FK, EmployeeID FK, AssignedDate DATETIME2)` dạng N-N để đúng với yêu cầu nghiệp vụ, và giữ `AssignedToEmployeeID` làm "người chịu trách nhiệm chính" (owner) theo BR-008.

### tblTaskChecklist / tblTaskComment / tblTaskAttachment
`...ID` PK · `TaskID` FK NOT NULL · Checklist: `ChecklistItem NVARCHAR(500)`, `IsCompleted BIT DEFAULT 0` · Comment: `EmployeeID` FK NOT NULL, `CommentText NVARCHAR(MAX)`, `CommentDate DATETIME2(0)` · Attachment: `DocumentUrl NVARCHAR(500)`, `FileName NVARCHAR(300)`.

## 4.11 MODULE KPI

### tblKPIPeriod
`KPIPeriodID` PK · `Year SMALLINT` · `Quarter SMALLINT NULL` · `Month SMALLINT NULL`.

### tblKPITemplate
`KPITemplateID` PK · `KPIName NVARCHAR(300)` · `Description NVARCHAR(1000) NULL` · `Weight DECIMAL(5,2)` (tỷ trọng %, theo BR-009 mọi KPI phải có Target và Period) · `TargetValue DECIMAL(18,2) NULL`.

### tblCompanyKPI / tblDepartmentKPI / tblEmployeeKPI
`...KPIID` PK · `KPITemplateID` FK NOT NULL · `KPIPeriodID` FK NOT NULL · (Department/Employee thêm `DepartmentID`/`EmployeeID` FK NOT NULL) · `Target DECIMAL(18,2)` · `Actual DECIMAL(18,2) NULL` · `Achievement DECIMAL(5,2) NULL` (%) · `Score DECIMAL(5,2) NULL` (chỉ CompanyKPI/EmployeeKPI có Score theo thiết kế gốc).

## 4.12 MODULE ASSET

### tblAssetType
`AssetTypeID` PK · `AssetTypeCode NVARCHAR(50) UNIQUE` · `AssetTypeName NVARCHAR(100)`.

### tblAsset
`AssetID` PK · `AssetCode NVARCHAR(50) UNIQUE` · `AssetName NVARCHAR(200)` · `AssetTypeID` FK NOT NULL · `PurchaseDate DATE NULL` · `PurchaseValue DECIMAL(18,2) NULL` · `Status NVARCHAR(30)`.

### tblAssetAllocation
`AllocationID` PK · `AssetID` FK NOT NULL · `EmployeeID` FK NOT NULL · `AssignedDate DATE` · `ReturnDate DATE NULL`.

### tblAssetMaintenance
`MaintenanceID` PK · `AssetID` FK NOT NULL · `MaintenanceDate DATE` · `Description NVARCHAR(500) NULL` · `Cost DECIMAL(18,2) NULL`.

## 4.13 MODULE PROCUREMENT

### tblProcurementRequest
`ProcurementRequestID` PK · `RequestNo NVARCHAR(50) UNIQUE` · `RequestedBy BIGINT NOT NULL FK → tblEmployee` · `DepartmentID` FK NOT NULL · `RequestDate DATE` · `Reason NVARCHAR(1000) NULL` · `Status NVARCHAR(30)`.

### tblProcurementItem
`ItemID` PK · `ProcurementRequestID` FK NOT NULL · `ItemName NVARCHAR(300)` · `Quantity SMALLINT` · `EstimatedCost DECIMAL(18,2) NULL`.

### tblProcurementApproval
`ApprovalID` PK · `ProcurementRequestID` FK NOT NULL · `ApproverID BIGINT NOT NULL FK` · `ApprovalLevel SMALLINT` · `Decision NVARCHAR(20) NULL` · `DecisionDate DATETIME2(0) NULL`.

## 4.14 MODULE NOTIFICATION

### tblNotification
`NotificationID` PK · `EmployeeID` FK NOT NULL · `NotificationType NVARCHAR(50)` · `Title NVARCHAR(300)` · `Message NVARCHAR(1000)` · `IsRead BIT DEFAULT 0` · `CreatedDate DATETIME2(0) DEFAULT SYSUTCDATETIME()`.

## 4.15 MODULE SECURITY

### tblRole / tblPermission
`RoleID`/`PermissionID` PK · `RoleCode`/`PermissionCode NVARCHAR(50) UNIQUE` · `RoleName`/`PermissionName NVARCHAR(200)`.

### tblRolePermission
`RolePermissionID` PK · `RoleID` FK NOT NULL · `PermissionID` FK NOT NULL. **Constraint:** `UNIQUE (RoleID, PermissionID)`.

### tblUser
`UserID` PK · `EmployeeID BIGINT NULL FK` (nullable — cho phép tài khoản hệ thống không gắn nhân sự, vd. Super Admin) · `Username NVARCHAR(100) UNIQUE` · `Email NVARCHAR(100) UNIQUE` · `RoleID` FK NOT NULL · `IsActive BIT DEFAULT 1`.
**Bổ sung cần có (SSO):** `ExternalObjectId UNIQUEIDENTIFIER NULL UNIQUE` — lưu Entra ID Object ID để map SSO, theo `04_Security_Design.md` (Entra ID) và `14_Code_Generation_Guide.md`. Hệ thống này KHÔNG lưu mật khẩu (`PasswordHash`) vì xác thực hoàn toàn qua Entra ID/SSO — cần xác nhận với IT nếu vẫn cần tài khoản local dự phòng.

### tblDelegation
`DelegationID` PK · `DelegatorEmployeeID`, `DelegateEmployeeID` FK NOT NULL (đều → tblEmployee) · `DelegationFrom DATE` · `DelegationTo DATE` · `Reason NVARCHAR(500) NULL` · `Status NVARCHAR(30)`.

## 4.16 MODULE AUDIT

### tblAuditLog
`AuditLogID` PK · `TableName NVARCHAR(100)` · `RecordID BIGINT` · `ActionType NVARCHAR(20)` (Create/Update/Delete/Approve/Reject/Login/Logout) · `OldValue NVARCHAR(MAX) NULL` · `NewValue NVARCHAR(MAX) NULL` · `ChangedBy BIGINT NOT NULL FK → tblUser` · `ChangedDate DATETIME2(0) DEFAULT SYSUTCDATETIME()`.
**Lưu ý:** bảng này sẽ tăng trưởng nhanh nhất hệ thống — cần partition theo tháng/năm hoặc archive định kỳ theo chính sách lưu trữ 5 năm (mục 24 của `03_Database_Design.md`).

### tblUserLoginLog
`LoginLogID` PK · `UserID` FK NOT NULL · `LoginTime DATETIME2(0)` · `LogoutTime DATETIME2(0) NULL` · `IPAddress NVARCHAR(45)`.

## 4.17 MODULE WORKFLOW

### tblWorkflowDefinition
`WorkflowID` PK · `WorkflowCode NVARCHAR(50) UNIQUE` · `WorkflowName NVARCHAR(200)`.

### tblWorkflowStep
`WorkflowStepID` PK · `WorkflowID` FK NOT NULL · `StepNo SMALLINT` · `RoleID` FK NOT NULL · `StepName NVARCHAR(200)`.

### tblWorkflowTransaction
`WorkflowTransactionID` PK · `WorkflowID` FK NOT NULL · `ReferenceID BIGINT` (ID của bản ghi nghiệp vụ đang chạy workflow, vd. LeaveRequestID) · `CurrentStep SMALLINT` · `Status NVARCHAR(30)`.

---

# 5. DỮ LIỆU NHẠY CẢM CẦN MÃ HÓA (bổ sung chi tiết cho 04_Security_Design.md)

Theo yêu cầu bảo mật ở `00_Project_Charter.md` mục 12 ("Thông tin nhạy cảm phải được mã hóa") nhưng chưa có danh sách field cụ thể. Đề xuất áp dụng **mã hóa tầng ứng dụng (Application-level encryption / Always Encrypted của SQL Server)** cho các field sau:

| Bảng | Field | Loại dữ liệu |
|---|---|---|
| tblEmployee | NationalID | CCCD/CMND |
| tblEmployee | SocialInsuranceNo | Số sổ BHXH |
| tblEmployee | TaxCode | MST cá nhân |
| tblEmployeeBankAccount | AccountNumber | Số tài khoản ngân hàng |
| tblPayroll | (toàn bộ số tiền) | Không mã hóa field, nhưng giới hạn quyền xem theo RBAC (R03/R05 mới xem full, xem `10_RBAC_Permission_Matrix.md`) |

Các field này **không được ghi log dạng plaintext** vào `tblAuditLog.OldValue/NewValue` — cần mask (vd. `***-***-1234`) trước khi lưu Audit Log.

---

# 6. BẢNG STATUS — KHUYẾN NGHỊ CHUYỂN THÀNH DANH MỤC ĐỘNG

Nhiều bảng dùng `Status NVARCHAR(30)` tự do (Employee, Attendance, Task, Contract, Payroll, Procurement...). Rủi ro: mỗi module tự định nghĩa chuỗi trạng thái khác nhau, dễ gõ sai, khó kiểm soát khi thêm trạng thái mới.

**Khuyến nghị:** với các Status có luồng chuyển trạng thái rõ ràng (Task, Leave, Contract, Recruitment, Procurement, Document), dùng chung `tblWorkflowDefinition`/`tblWorkflowStep` đã có sẵn trong thiết kế thay vì text tự do; với Status không qua workflow phê duyệt (`EmploymentStatus`, `AssetStatus`...), enforce bằng `CHECK CONSTRAINT` liệt kê giá trị hợp lệ, được liệt kê tường minh ở `13_Master_Data_Dictionary.md`.

---

# 7. CHỈ MỤC (INDEX) BỔ SUNG NGOÀI MỤC 23 CỦA 03_Database_Design.md

Ngoài các cột đã liệt kê ở "23. INDEX STRATEGY", bổ sung:

```sql
CREATE UNIQUE INDEX UX_Employee_NationalID ON tblEmployee(NationalID) WHERE IsDeleted = 0;
CREATE UNIQUE INDEX UX_Employee_CompanyEmail ON tblEmployee(CompanyEmail) WHERE IsDeleted = 0;
CREATE INDEX IX_Attendance_EmployeeID_Date ON tblAttendance(EmployeeID, AttendanceDate);
CREATE INDEX IX_AuditLog_TableName_RecordID ON tblAuditLog(TableName, RecordID);
CREATE INDEX IX_Payroll_PeriodID_EmployeeID ON tblPayroll(PayrollPeriodID, EmployeeID);
CREATE INDEX IX_Task_AssignedTo_Status ON tblTask(AssignedToEmployeeID, TaskStatusID);
CREATE INDEX IX_LeaveRequest_EmployeeID_Status ON tblLeaveRequest(EmployeeID, Status);
```

(Dùng filtered index `WHERE IsDeleted = 0` vì hệ thống áp dụng Soft Delete toàn bộ — tránh unique constraint bị vi phạm bởi bản ghi đã xóa mềm.)

---

# 8. TRẠNG THÁI PHÊ DUYỆT

Sau khi HR Manager, Kế toán và IT xác nhận nội dung phụ lục này, đề xuất gộp vào `03_Database_Design.md`, nâng version → 1.2, và đánh dấu `LOCKED` để chuyển sang giai đoạn viết Django Model.

# 06A_Payroll_Statutory_Rate_Master_Data.md

# PHỤ LỤC: MASTER DATA TỶ LỆ BẢO HIỂM & THUẾ TNCN (STATUTORY RATE CONFIGURATION)

## Project

Internal Administration & Human Resource Management System (IHRMS)

## Bổ sung cho

01_BRD_MASTER.md (FR-PAY-007 → FR-PAY-011), 03_Database_Design.md (Module Payroll), 13_Master_Data_Dictionary.md

## Version

1.0

## Status

Draft — cần Kế toán xác nhận công thức và tỷ lệ trước khi khóa Payroll Engine

## Lý do bổ sung

`01_BRD_MASTER.md` mục 5 (FR-PAY-007 đến FR-PAY-010) chỉ liệt kê **tên** các khoản khấu trừ (BHXH, BHYT, BHTN, Thuế TNCN) mà chưa có tỷ lệ/công thức cụ thể; `03_Database_Design.md` (`tblPayroll`) cũng chỉ có cột `InsuranceAmount`, `TaxAmount` dạng số tiền đã tính sẵn, không có nơi lưu **tỷ lệ áp dụng tại thời điểm tính lương**.

**Rủi ro nếu không xử lý:** tỷ lệ BHXH/BHYT/BHTN và biểu thuế TNCN thay đổi theo quy định Nhà nước theo từng giai đoạn (gần nhất: biểu thuế TNCN và mức giảm trừ gia cảnh đổi từ 01/01/2026 theo Luật Thuế TNCN 2025 và Nghị quyết 110/2025/UBTVQH15). Nếu hardcode tỷ lệ trong code (`PayrollService`), mỗi lần Nhà nước điều chỉnh sẽ phải sửa code + deploy lại, đồng thời **payroll của các kỳ cũ đã đóng (Locked) tính lại sẽ sai** nếu vô tình dùng tỷ lệ mới. Giải pháp là đưa toàn bộ tỷ lệ/mức về **master data có hiệu lực theo thời gian**.

---

# 1. THIẾT KẾ BẢNG MASTER DATA MỚI (bổ sung vào 03_Database_Design.md — Module Payroll)

## tblInsuranceRateConfig

Lưu tỷ lệ trích BHXH/BHYT/BHTN theo từng giai đoạn hiệu lực.

| Field | Type | Ghi chú |
|---|---|---|
| InsuranceRateConfigID | BIGINT IDENTITY | PK |
| EffectiveFrom | DATE | NOT NULL |
| EffectiveTo | DATE | NULL (NULL = đang áp dụng) |
| EmployeeSocialInsuranceRate | DECIMAL(5,2) | % NLĐ đóng BHXH (hưu trí-tử tuất) |
| EmployeeHealthInsuranceRate | DECIMAL(5,2) | % NLĐ đóng BHYT |
| EmployeeUnemploymentInsuranceRate | DECIMAL(5,2) | % NLĐ đóng BHTN |
| EmployerSocialInsuranceRate | DECIMAL(5,2) | % DN đóng BHXH (hưu trí + ốm đau-thai sản + TNLĐ-BNN) |
| EmployerHealthInsuranceRate | DECIMAL(5,2) | % DN đóng BHYT |
| EmployerUnemploymentInsuranceRate | DECIMAL(5,2) | % DN đóng BHTN |
| MaxSalaryBaseForSocialInsurance | DECIMAL(18,2) | Trần lương đóng BHXH/BHYT (20 lần lương cơ sở) |
| MaxSalaryBaseForUnemploymentInsurance | DECIMAL(18,2) | Trần lương đóng BHTN (20 lần lương tối thiểu vùng) |
| LegalReference | NVARCHAR(300) | Số hiệu văn bản pháp lý căn cứ |
| Note | NVARCHAR(500) | NULL |

**Dữ liệu khởi tạo tham khảo (áp dụng từ 01/01/2026, theo Luật BHXH 2024, Luật Việc làm 2025, Nghị định 188/2025/NĐ-CP, Nghị định 158/2025/NĐ-CP)** — *cần Kế toán xác nhận lại trước khi nhập chính thức, vì đây là dữ liệu tổng hợp từ nguồn tham khảo công khai, không thay thế văn bản pháp luật gốc:*

| Thành phần | NLĐ đóng | DN đóng |
|---|---|---|
| BHXH (hưu trí, tử tuất, ốm đau-thai sản, TNLĐ-BNN) | 8,0% | 14,0% (hưu trí) + 3,0% (ốm đau-thai sản) + 0,5% (TNLĐ-BNN) |
| BHYT | 1,5% | 3,0% |
| BHTN | 1,0% | 1,0% |
| **Tổng** | **10,5%** | **21,5%** |

*(Doanh nghiệp đủ điều kiện an toàn lao động có thể được áp dụng mức TNLĐ-BNN 0,3% thay vì 0,5% — cần Kế toán xác nhận công ty có thuộc diện này không.)*

## tblPersonalIncomeTaxBracket

Lưu biểu thuế TNCN lũy tiến từng phần, theo giai đoạn hiệu lực.

| Field | Type | Ghi chú |
|---|---|---|
| TaxBracketID | BIGINT IDENTITY | PK |
| EffectiveFrom | DATE | NOT NULL |
| EffectiveTo | DATE | NULL |
| BracketNo | SMALLINT | Thứ tự bậc thuế (1, 2, 3...) |
| IncomeFromMonthly | DECIMAL(18,2) | Cận dưới thu nhập tính thuế/tháng |
| IncomeToMonthly | DECIMAL(18,2) | NULL = không giới hạn (bậc cao nhất) |
| TaxRate | DECIMAL(5,2) | % thuế suất của bậc |

**Dữ liệu khởi tạo tham khảo (áp dụng từ 01/01/2026, theo Luật Thuế TNCN số 109/2025/QH15 — 5 bậc thay vì 7 bậc như trước 2026):**

| Bậc | Thu nhập tính thuế/tháng (triệu VNĐ) | Thuế suất |
|---|---|---|
| 1 | Đến 10 | 5% |
| 2 | Trên 10 đến 30 | 10% |
| 3 | Trên 30 đến 60 | 20% |
| 4 | Trên 60 đến 100 | 30% |
| 5 | Trên 100 | 35% |

## tblTaxDeductionConfig

Lưu mức giảm trừ gia cảnh và các khoản giảm trừ khác, theo giai đoạn hiệu lực.

| Field | Type | Ghi chú |
|---|---|---|
| TaxDeductionConfigID | BIGINT IDENTITY | PK |
| EffectiveFrom | DATE | NOT NULL |
| EffectiveTo | DATE | NULL |
| SelfDeductionMonthly | DECIMAL(18,2) | Giảm trừ bản thân người nộp thuế/tháng |
| DependentDeductionMonthly | DECIMAL(18,2) | Giảm trừ mỗi người phụ thuộc/tháng |
| MaxEducationDeductionYearly | DECIMAL(18,2) | NULL nếu không áp dụng |
| MaxMedicalDeductionYearly | DECIMAL(18,2) | NULL nếu không áp dụng |
| LegalReference | NVARCHAR(300) | |

**Dữ liệu khởi tạo tham khảo (áp dụng từ 01/01/2026, theo Nghị quyết 110/2025/UBTVQH15 và Nghị định 253/2026/NĐ-CP):**

| Khoản | Mức |
|---|---|
| Giảm trừ bản thân | 15.500.000 đ/tháng |
| Giảm trừ mỗi người phụ thuộc | 6.200.000 đ/tháng |
| Giảm trừ chi phí giáo dục-đào tạo (tối đa) | 24.000.000 đ/năm |
| Giảm trừ chi phí y tế (tối đa) | 23.000.000 đ/năm |

## tblEmployeeDependent

Chưa có trong `03_Database_Design.md` nhưng cần thiết để tính đúng số người phụ thuộc khi trừ thuế — đề xuất bổ sung:

| Field | Type | Ghi chú |
|---|---|---|
| DependentID | BIGINT IDENTITY | PK |
| EmployeeID | BIGINT | FK NOT NULL → tblEmployee |
| FullName | NVARCHAR(200) | |
| DateOfBirth | DATE | |
| Relationship | NVARCHAR(50) | Con, Cha, Mẹ... |
| TaxCode | NVARCHAR(20) | NULL |
| RegisteredFrom | DATE | Ngày đăng ký giảm trừ |
| RegisteredTo | DATE | NULL |
| IsActive | BIT | DEFAULT 1 |

---

# 2. CÔNG THỨC TÍNH — BỔ SUNG CHO PAYROLL ENGINE (02_Solution_Architecture.md mục 10)

```text
Lương đóng bảo hiểm = MIN(Lương cơ bản + Phụ cấp tính BH, MaxSalaryBaseForSocialInsurance)

BHXH/BHYT/BHTN (NLĐ trừ vào lương)
  = Lương đóng bảo hiểm × (EmployeeSocialInsuranceRate + EmployeeHealthInsuranceRate + EmployeeUnemploymentInsuranceRate)
  (tra tblInsuranceRateConfig theo PayrollPeriod.StartDate)

Thu nhập chịu thuế = Tổng thu nhập chịu thuế TNCN - Bảo hiểm bắt buộc (NLĐ đóng) - Các khoản miễn thuế khác

Thu nhập tính thuế = Thu nhập chịu thuế
                      - SelfDeductionMonthly
                      - (Số người phụ thuộc hợp lệ × DependentDeductionMonthly)
                      - Các khoản giảm trừ giáo dục/y tế (nếu có, không vượt mức trần)

Thuế TNCN = Tính lũy tiến từng phần theo tblPersonalIncomeTaxBracket
            (tra theo PayrollPeriod.StartDate, KHÔNG dùng bracket hiện tại của ngày chạy batch lương)
```

**Nguyên tắc bắt buộc:** mọi truy vấn tỷ lệ/bậc thuế/mức giảm trừ trong `PayrollService` PHẢI lọc theo `EffectiveFrom <= PayrollPeriod.StartDate AND (EffectiveTo IS NULL OR EffectiveTo >= PayrollPeriod.StartDate)` — không lấy bản ghi "đang hiệu lực tại thời điểm chạy job" để đảm bảo tính lương truy hồi (retro-payroll) hoặc chạy lại kỳ cũ vẫn cho kết quả đúng lịch sử.

---

# 3. TÁC ĐỘNG ĐẾN CÁC TÀI LIỆU KHÁC

- **`13_Master_Data_Dictionary.md`**: bổ sung 4 danh mục mới (`tblInsuranceRateConfig`, `tblPersonalIncomeTaxBracket`, `tblTaxDeductionConfig`, `tblEmployeeDependent`) vào phần "Master Data Ownership" — Data Owner đề xuất: **Finance Officer** (Kế toán), người duy nhất được sửa các bảng này (khớp với `10_RBAC_Permission_Matrix.md` R05).
- **`10_RBAC_Permission_Matrix.md`**: chỉ **R05 - Finance Officer** và **R01 - Super Admin** được Create/Update 4 bảng cấu hình trên; các role khác chỉ Read (nếu cần hiển thị bảng lương chi tiết).
- **`11_Workflow_Definition.md`**: đề xuất thêm workflow phê duyệt khi thay đổi tỷ lệ/bậc thuế (2 cấp: Finance Officer đề xuất → Director/HR Manager xác nhận) trước khi bản ghi mới có hiệu lực, vì đây là thay đổi ảnh hưởng đến toàn bộ nhân sự.

---

# 4. LƯU Ý QUAN TRỌNG

Các số liệu tỷ lệ/mức tiền trong tài liệu này được tổng hợp từ các nguồn tham khảo công khai tại thời điểm soạn thảo (09/2026) để minh họa cách thiết kế bảng cấu hình, **không phải tư vấn pháp lý hay tư vấn thuế chính thức**. Trước khi đưa vào seed data Production, đội dự án bắt buộc phải:

1. Đối chiếu lại với Kế toán/đơn vị tư vấn thuế của công ty.
2. Xác nhận công ty có thuộc diện áp dụng mức TNLĐ-BNN ưu đãi (0,3%) hay không.
3. Xác nhận số người phụ thuộc thực tế đã đăng ký giảm trừ gia cảnh của từng nhân viên (dữ liệu này không tự sinh được, phải nhập thủ công lần đầu từ hồ sơ thuế hiện có).

---

# 5. TRẠNG THÁI PHÊ DUYỆT

Cần Finance Officer xác nhận toàn bộ số liệu ở mục 1 trước khi Payroll Engine được coi là "Ready for Development".
