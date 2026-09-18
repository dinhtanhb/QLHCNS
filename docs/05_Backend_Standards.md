# 05_Backend_Standards.md

# BACKEND DEVELOPMENT STANDARDS

## Project

Internal Administration & Human Resource Management System (IHRMS)

## Version

1.0

## Status

Approved

---

# 1. PURPOSE

Tài liệu này quy định:

- Kiến trúc Backend
- Chuẩn lập trình Django
- Chuẩn đặt tên
- Chuẩn viết API
- Chuẩn Repository
- Chuẩn Service
- Chuẩn Validation
- Chuẩn Audit
- Chuẩn Error Handling
- Chuẩn Testing

Tất cả source code phải tuân thủ tài liệu này.

---

# 2. TECHNOLOGY STANDARD

## Backend

```text
Python 3.12
```

---

## Framework

```text
Django 5
```

---

## API

```text
Django REST Framework
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

# 3. APPLICATION ARCHITECTURE

## Architectural Style

```text
Modular Monolith
```

---

## Layers

```text
Presentation Layer

↓

API Layer

↓

Service Layer

↓

Repository Layer

↓

Database Layer
```

---

# 4. DJANGO PROJECT STRUCTURE

```text
ihrms/

├── config/
│
├── apps/
│
│   ├── organization/
│   ├── hrm/
│   ├── recruitment/
│   ├── attendance/
│   ├── leave/
│   ├── payroll/
│   ├── contracts/
│   ├── documents/
│   ├── tasks/
│   ├── kpi/
│   ├── assets/
│   ├── procurement/
│   ├── dashboard/
│   ├── notifications/
│   ├── audit/
│   ├── security/
│   ├── m365/
│   └── common/
│
├── media/
│
├── static/
│
├── templates/
│
└── logs/
```

---

# 5. MODULE STRUCTURE

Mỗi module phải có cấu trúc:

```text
module/

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

# 6. NAMING CONVENTION

## Class

```python
Employee
Department
RecruitmentRequest
```

---

## Serializer

```python
EmployeeSerializer
EmployeeCreateSerializer
EmployeeUpdateSerializer
```

---

## Repository

```python
EmployeeRepository
DepartmentRepository
```

---

## Service

```python
EmployeeService
PayrollService
TaskService
```

---

## API View

```python
EmployeeViewSet
DepartmentViewSet
```

---

## Permission

```python
EmployeePermission
PayrollPermission
```

---

# 7. MODEL DEVELOPMENT STANDARD

## General Rules

Một model tương ứng một bảng.

---

Model phải sử dụng:

```python
UUID hoặc Identity Key
```

theo thiết kế Database.

---

## Audit Fields

Tất cả model nghiệp vụ đều phải có:

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

## Soft Delete

Không được xóa dữ liệu vật lý.

Bắt buộc:

```python
is_deleted = True
```

---

# 8. BASE MODEL STANDARD

Tạo Common Base Model dùng chung.

Nội dung:

```text
Audit Fields

Soft Delete

Common Methods
```

Mọi model nghiệp vụ kế thừa từ BaseModel.

---

# 9. REPOSITORY STANDARD

## Mục tiêu

Toàn bộ thao tác dữ liệu phải đi qua Repository.

---

Không được:

```python
Employee.objects.filter(...)
```

trong Service Layer.

---

Bắt buộc:

```python
EmployeeRepository
```

---

## Repository Responsibilities

### Create

Tạo dữ liệu.

---

### Read

Đọc dữ liệu.

---

### Update

Cập nhật dữ liệu.

---

### Soft Delete

Xóa mềm.

---

### Search

Tìm kiếm.

---

### Filter

Lọc dữ liệu.

---

# 10. SERVICE LAYER STANDARD

## Mục tiêu

Business Logic chỉ được viết tại Service Layer.

---

Không được viết:

```python
Business Logic
```

trong:

```python
View

Serializer

Repository
```

---

## Ví dụ

Payroll Calculation

↓

PayrollService

---

Leave Validation

↓

LeaveService

---

Recruitment Workflow

↓

RecruitmentService

---

# 11. VALIDATION STANDARD

## Validation Levels

### API Validation

Kiểm tra dữ liệu đầu vào.

---

### Business Validation

Kiểm tra nghiệp vụ.

---

### Database Validation

Kiểm tra ràng buộc.

---

## Ví dụ

EmployeeCode phải duy nhất.

---

NationalID không được trùng.

---

Contract Date phải hợp lệ.

---

# 12. API DESIGN STANDARD

## RESTFUL API

Bắt buộc.

---

## URL Convention

```text
/api/v1/
```

---

Ví dụ:

```text
/api/v1/employees/

/api/v1/departments/

/api/v1/tasks/
```

---

# 13. HTTP METHOD STANDARD

## GET

Đọc dữ liệu.

---

## POST

Tạo dữ liệu.

---

## PUT

Cập nhật toàn bộ.

---

## PATCH

Cập nhật một phần.

---

## DELETE

Soft Delete.

---

# 14. API RESPONSE STANDARD

## Success

```json
{
    "success": true,
    "message": "Success",
    "data": {}
}
```

---

## Error

```json
{
    "success": false,
    "message": "Validation Error",
    "errors": []
}
```

---

# 15. PAGINATION STANDARD

Bắt buộc cho toàn bộ danh sách.

---

Default

```text
20 records
```

---

Maximum

```text
100 records
```

---

# 16. FILTERING STANDARD

Bắt buộc hỗ trợ:

```text
Keyword

Date Range

Status

Department

Employee
```

nếu phù hợp module.

---

# 17. SORTING STANDARD

Cho phép:

```text
CreatedDate

ModifiedDate

Code

Name
```

---

# 18. SEARCH STANDARD

Search không phân biệt:

```text
Hoa thường

Dấu tiếng Việt
```

---

Hỗ trợ:

```text
Contains Search
```

---

# 19. FILE MANAGEMENT STANDARD

## File Metadata

Lưu SQL Server.

---

## File Content

Lưu:

```text
SharePoint

OneDrive
```

---

Không lưu Binary vào SQL Server.

---

# 20. AUDIT LOG STANDARD

Bắt buộc cho:

```text
Create

Update

Delete

Approve

Reject

Export
```

---

Thông tin lưu:

```text
User

Role

Action

Old Value

New Value

Date Time

IP Address
```

---

# 21. WORKFLOW STANDARD

Các module bắt buộc workflow:

```text
Leave

Recruitment

Contract

Procurement

Document

Payroll Approval
```

---

Workflow phải lưu:

```text
Current Step

Approver

Decision

Date
```

---

# 22. PERMISSION STANDARD

Mọi API phải kiểm tra:

```text
Authentication

Authorization
```

---

Không được:

```text
Bypass Permission
```

---

# 23. PAYROLL STANDARD

Không cho phép:

```text
Tính lương trong View
```

---

Bắt buộc:

```text
Payroll Engine

Payroll Service
```

---

Các bước:

```text
Attendance

↓

Leave

↓

Allowance

↓

Deduction

↓

Tax

↓

Net Salary
```

---

# 24. TASK STANDARD

Task phải hỗ trợ:

```text
Status

Priority

Deadline

Comment

Checklist

Attachment
```

---

Task Overdue phải tự động xác định.

---

# 25. DOCUMENT STANDARD

Mọi tài liệu phải có:

```text
Document Code

Version

Document Category

Status
```

---

Lưu lịch sử phiên bản.

---

# 26. ERROR HANDLING STANDARD

## Không hiển thị

```text
Stack Trace
```

cho người dùng.

---

## Ghi Log

Bắt buộc.

---

## Trả thông báo thân thiện.

---

# 27. LOGGING STANDARD

## Application Log

```text
Info

Warning

Error

Critical
```

---

## Log Storage

```text
logs/
```

---

# 28. EXCEPTION STANDARD

Tạo Common Exception Classes.

```python
ValidationException

NotFoundException

BusinessException

PermissionException
```

---

# 29. TRANSACTION STANDARD

Các nghiệp vụ:

```text
Payroll

Recruitment

Contract

Procurement
```

phải sử dụng:

```python
Database Transaction
```

---

# 30. PERFORMANCE STANDARD

Danh sách:

```text
< 3 giây
```

---

Dashboard:

```text
< 5 giây
```

---

# 31. CACHING RULE

Không triển khai Cache Layer ở phiên bản đầu.

Thiết kế code phải sẵn sàng mở rộng sau này.

---

# 32. UNIT TEST STANDARD

Mỗi:

```text
Repository

Service
```

phải có Unit Test.

---

Coverage tối thiểu:

```text
80%
```

---

# 33. INTEGRATION TEST STANDARD

Bắt buộc cho:

```text
Payroll

Leave

Recruitment

Procurement

Task
```

---

# 34. API DOCUMENTATION

Sử dụng:

```text
Swagger/OpenAPI
```

---

Bắt buộc sinh:

```text
Request

Response

Schema

Authentication
```

---

# 35. CODE QUALITY STANDARD

Tuân thủ:

```text
PEP8
```

---

Không được:

```text
Hard Code

Duplicate Logic

Magic Number
```

---

# 36. SECURITY CODING STANDARD

Không lưu:

```text
Plain Password
```

---

Không log:

```text
Password

Token

Bank Account

National ID
```

---

Không trả về:

```text
Internal Error Detail
```

cho Frontend.

---

# 37. DEVELOPMENT CHECKLIST

Trước khi Merge:

✅ Unit Test Pass

✅ Integration Test Pass

✅ Migration Generated

✅ API Documentation Updated

✅ Permission Checked

✅ Audit Log Checked

✅ Code Review Completed

---

# 38. DEFINITION OF DONE

Một chức năng được xem là hoàn thành khi:

✅ Code hoàn chỉnh

✅ Migration thành công

✅ API hoạt động

✅ Permission đúng

✅ Audit Log hoạt động

✅ Unit Test đạt

✅ Integration Test đạt

✅ Không còn lỗi Critical

✅ Tài liệu được cập nhật

---

# 39. BACKEND APPROVAL

Status:

Approved

Ready For:

- Frontend Standards
- Development
- Code Generation
- Testing

# 05A_Backend_Standards_Addendum_DbTable_Mapping.md

# PHỤ LỤC: QUY TẮC MAPPING DJANGO MODEL ↔ TÊN BẢNG SQL SERVER

## Project

Internal Administration & Human Resource Management System (IHRMS)

## Bổ sung cho

05_Backend_Standards.md, 14_Code_Generation_Guide.md, 16_Django_Module_Blueprint.md

## Version

1.0

## Status

Draft — cần áp dụng bắt buộc trước khi viết Django Model đầu tiên

## Lý do bổ sung

`03_Database_Design.md` đặt tên bảng theo chuẩn `tblPascalCase` (vd. `tblEmployee`, `tblDepartment`), trong khi Django mặc định tự sinh tên bảng theo `<app_label>_<model_name_lowercase>` (vd. `hrm_employee`). Nếu không khai báo tường minh, tên bảng thực tế trên SQL Server sẽ **không khớp** với thiết kế đã duyệt — gây khó khăn khi đối chiếu, viết SQL báo cáo trực tiếp, hoặc migrate dữ liệu cũ. Ba tài liệu Backend Standards, Code Generation Guide và Django Module Blueprint hiện chưa có quy tắc nào xử lý việc này.

---

# 1. QUY TẮC BẮT BUỘC

## RULE-BE-DB-001 — Mọi Model phải khai báo `db_table` khớp tên bảng đã duyệt

```python
class Employee(BaseAuditModel):
    class Meta:
        db_table = "tblEmployee"
        verbose_name = "Nhân viên"
        verbose_name_plural = "Nhân viên"
```

- Tên trong `db_table` PHẢI lấy nguyên văn từ cột heading (`## tblXxx`) của `03_Database_Design.md` — không tự ý đổi case, không thêm prefix app.
- Reviewer (Code Review theo `07_Testing_Standards.md`) phải đối chiếu `db_table` với Database Design trước khi duyệt PR.
- Không dùng `managed = False` — Django vẫn quản lý migration bình thường, chỉ đổi tên bảng vật lý.

## RULE-BE-DB-002 — Tên trường Model giữ `snake_case` chuẩn Python, không copy PascalCase từ DB

Theo `05_Backend_Standards.md` mục 6, tên class Python dùng PascalCase (`Employee`), nhưng **tên field trong Model vẫn phải là `snake_case`** theo PEP8 — DB Design dùng PascalCase (`EmployeeCode`) là chuẩn đặt tên cột SQL, không phải chuẩn đặt tên attribute Python. Dùng `db_column` để map:

```python
class Employee(BaseAuditModel):
    employee_code = models.CharField(max_length=50, unique=True, db_column="EmployeeCode")
    full_name = models.CharField(max_length=200, db_column="FullName")
    date_of_birth = models.DateField(db_column="DateOfBirth")

    class Meta:
        db_table = "tblEmployee"
```

**Bảng đối chiếu nhanh:**

| Database Design (03) | Django Model attribute | db_column |
|---|---|---|
| `EmployeeID` (PK) | `id` (Django auto) hoặc `employee_id` nếu cần custom PK | — (Django tự quản nếu dùng `id` mặc định) |
| `EmployeeCode` | `employee_code` | `EmployeeCode` |
| `DepartmentID` (FK) | `department` (ForeignKey) | `DepartmentID` |
| `IsActive` | `is_active` | `IsActive` |
| `CreatedDate` | `created_date` | `CreatedDate` |

## RULE-BE-DB-003 — Khóa chính: dùng `BaseAuditModel` dùng chung

Theo ADR-DB-001 (`03A_Database_Design_Addendum_Physical_Schema.md`), toàn hệ thống dùng `BIGINT IDENTITY` làm PK. Tạo 1 abstract base model trong `apps/common/models.py` để mọi app kế thừa, tránh lặp code và đảm bảo nhất quán:

```python
# apps/common/models.py
from django.db import models


class BaseAuditModel(models.Model):
    """
    Base model bắt buộc cho MỌI model nghiệp vụ trong hệ thống IHRMS.
    Áp dụng theo:
      - 00_Project_Charter.md mục 12 (Audit Log, Soft Delete bắt buộc)
      - 03_Database_Design.md mục 2, 3 (DB-004, DB-005, Common Audit Fields)
    """
    created_by = models.ForeignKey(
        "security.User", null=True, blank=True,
        on_delete=models.PROTECT, related_name="+",
        db_column="CreatedBy",
    )
    created_date = models.DateTimeField(auto_now_add=True, db_column="CreatedDate")
    modified_by = models.ForeignKey(
        "security.User", null=True, blank=True,
        on_delete=models.PROTECT, related_name="+",
        db_column="ModifiedBy",
    )
    modified_date = models.DateTimeField(auto_now=True, null=True, db_column="ModifiedDate")
    deleted_by = models.ForeignKey(
        "security.User", null=True, blank=True,
        on_delete=models.PROTECT, related_name="+",
        db_column="DeletedBy",
    )
    deleted_date = models.DateTimeField(null=True, blank=True, db_column="DeletedDate")
    is_deleted = models.BooleanField(default=False, db_column="IsDeleted")

    class Meta:
        abstract = True
```

**Không dùng `on_delete=models.CASCADE`** cho các FK tham chiếu tới `User`/`Employee` trong `BaseAuditModel` và các quan hệ nghiệp vụ chính (Employee → Department, Contract → Employee...) — vì hệ thống dùng Soft Delete (DB-005), xóa cứng bản ghi cha sẽ làm mất dữ liệu lịch sử/audit trái với nguyên tắc 3 và 4 của `00_Project_Charter.md` ("mọi giao dịch phải lưu lịch sử", "mọi nghiệp vụ phải hỗ trợ kiểm toán"). Dùng `models.PROTECT` hoặc `models.SET_NULL` tuỳ nghiệp vụ, không dùng `CASCADE` cho quan hệ tới bảng master/audit.

## RULE-BE-DB-004 — Soft Delete: không override `.delete()` mặc định của QuerySet mà không kiểm soát

```python
class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        # Chặn hard-delete hàng loạt qua QuerySet.delete() mặc định của Django,
        # buộc đi qua EmployeeService.soft_delete() để ghi Audit Log đúng quy trình.
        raise NotImplementedError(
            "Không được gọi .delete() trực tiếp trên QuerySet. "
            "Dùng Service Layer tương ứng để đảm bảo Soft Delete + Audit Log."
        )
```

Repository/Service layer (theo `02_Solution_Architecture.md` mục 9) chịu trách nhiệm set `is_deleted = True`, `deleted_by`, `deleted_date` và ghi `tblAuditLog` trong cùng transaction (`Unit of Work`).

---

# 2. VÍ DỤ ĐẦY ĐỦ — MODEL `Employee`

```python
# apps/hrm/models/employee.py
from django.db import models
from apps.common.models import BaseAuditModel


class Employee(BaseAuditModel):
    GENDER_CHOICES = [("Male", "Nam"), ("Female", "Nữ"), ("Other", "Khác")]
    EMPLOYMENT_STATUS_CHOICES = [
        ("Active", "Đang làm việc"),
        ("Probation", "Thử việc"),
        ("OnLeave", "Đang nghỉ dài hạn"),
        ("Resigned", "Đã nghỉ việc"),
    ]

    employee_code = models.CharField(max_length=50, unique=True, db_column="EmployeeCode")
    first_name = models.CharField(max_length=100, db_column="FirstName")
    last_name = models.CharField(max_length=100, db_column="LastName")
    full_name = models.CharField(max_length=200, db_column="FullName")
    date_of_birth = models.DateField(db_column="DateOfBirth")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, db_column="Gender")

    # Dữ liệu nhạy cảm — xem 03A_Database_Design_Addendum mục 5, cần field-level encryption
    national_id = models.CharField(max_length=20, unique=True, db_column="NationalID")
    tax_code = models.CharField(max_length=20, null=True, blank=True, db_column="TaxCode")
    social_insurance_no = models.CharField(max_length=20, null=True, blank=True, db_column="SocialInsuranceNo")

    personal_email = models.EmailField(max_length=100, null=True, blank=True, db_column="PersonalEmail")
    company_email = models.EmailField(max_length=100, unique=True, db_column="CompanyEmail")
    mobile_phone = models.CharField(max_length=20, db_column="MobilePhone")
    address = models.CharField(max_length=500, null=True, blank=True, db_column="Address")

    join_date = models.DateField(db_column="JoinDate")
    leave_date = models.DateField(null=True, blank=True, db_column="LeaveDate")

    department = models.ForeignKey(
        "organization.Department", on_delete=models.PROTECT,
        db_column="DepartmentID", related_name="employees",
    )
    position = models.ForeignKey(
        "organization.Position", on_delete=models.PROTECT,
        db_column="PositionID", related_name="employees",
    )
    job_title = models.ForeignKey(
        "organization.JobTitle", null=True, blank=True, on_delete=models.SET_NULL,
        db_column="JobTitleID", related_name="employees",
    )
    manager = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL,
        db_column="ManagerID", related_name="subordinates",
    )
    employment_status = models.CharField(
        max_length=30, choices=EMPLOYMENT_STATUS_CHOICES,
        default="Active", db_column="EmploymentStatus",
    )
    photo_url = models.CharField(max_length=500, null=True, blank=True, db_column="PhotoUrl")

    class Meta:
        db_table = "tblEmployee"
        verbose_name = "Nhân viên"
        verbose_name_plural = "Nhân viên"
        indexes = [
            models.Index(fields=["company_email"], name="IX_Employee_CompanyEmail"),
        ]

    def __str__(self):
        return f"{self.employee_code} - {self.full_name}"
```

---

# 3. CẬP NHẬT `14_Code_Generation_Guide.md`

Đề xuất bổ sung vào checklist sinh code tự động (nếu dùng AI/script để generate model hàng loạt từ `03_Database_Design.md`):

- [ ] Mỗi model PHẢI có `Meta.db_table` trỏ đúng tên bảng gốc.
- [ ] Mỗi field PHẢI có `db_column` trỏ đúng tên cột gốc (trừ PK dùng `id` mặc định).
- [ ] Mỗi model kế thừa `BaseAuditModel`, không tự khai lại 7 field audit.
- [ ] Không dùng `on_delete=CASCADE` cho FK tới Employee/User/Department (bảng master/lịch sử).
- [ ] Có test kiểm tra `Model._meta.db_table` khớp danh sách bảng trong `03_Database_Design.md` (có thể viết 1 script đối chiếu tự động chạy trong CI, theo `07_Testing_Standards.md`).

---

# 4. TRẠNG THÁI PHÊ DUYỆT

Cần Tech Lead / IT xác nhận trước khi coder bắt đầu viết Model cho Sprint đầu tiên, vì đây là quy tắc nền tảng áp dụng cho toàn bộ 72 bảng.
