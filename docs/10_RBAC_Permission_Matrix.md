# ROLE BASED ACCESS CONTROL (RBAC)
# PERMISSION MATRIX DOCUMENT

## Project

Internal Administration & Human Resource Management System (IHRMS)

## Version

1.0

## Status

Approved

---

# 1. PURPOSE

Tài liệu này quy định:

- Vai trò người dùng
- Quyền truy cập
- Giới hạn dữ liệu
- Phân quyền chức năng
- Phân quyền báo cáo
- Phân quyền workflow
- Phân quyền API

Là cơ sở triển khai:

- Django Permission
- JWT Claims
- Middleware Authorization
- Menu Visibility
- API Security

---

# 2. ROLE DEFINITIONS

## R01 - Super Admin

Phạm vi:

Toàn bộ hệ thống.

Quyền:

- Cấu hình hệ thống
- Quản trị người dùng
- Quản trị vai trò
- Quản trị phân quyền
- Truy cập toàn bộ dữ liệu

---

## R02 - System Admin

Phạm vi:

Hạ tầng và kỹ thuật.

Quyền:

- Quản lý tài khoản
- Quản lý phân quyền
- Xem Audit Log
- Xem cấu hình hệ thống

Không được:

- Sửa dữ liệu lương
- Duyệt lương

---

## R03 - HR Manager

Phạm vi:

Toàn bộ dữ liệu nhân sự.

Quyền:

- Quản lý nhân sự
- Tuyển dụng
- Nghỉ phép
- Chấm công
- Hợp đồng
- KPI nhân sự

---

## R04 - HR Officer

Phạm vi:

Dữ liệu nhân sự.

Quyền:

- Tạo
- Cập nhật
- Theo dõi

Không được:

- Duyệt cuối cùng
- Xóa dữ liệu quan trọng

---

## R05 - Finance Officer

Phạm vi:

Lương và mua sắm.

Quyền:

- Xem bảng lương
- Tính lương
- Kiểm tra thanh toán
- Mua sắm

---

## R06 - Department Manager

Phạm vi:

Phòng ban phụ trách.

Quyền:

- Quản lý nhân viên thuộc phòng
- Duyệt nghỉ phép
- Duyệt công
- Quản lý công việc
- Đánh giá KPI

---

## R07 - Employee

Phạm vi:

Dữ liệu cá nhân.

Quyền:

- Xem thông tin cá nhân
- Xin nghỉ phép
- Xem công
- Xem phiếu lương
- Cập nhật hồ sơ cá nhân

---

## R08 - Director

Phạm vi:

Toàn công ty.

Quyền:

- Xem Dashboard
- Phê duyệt cuối cùng
- Xem KPI
- Xem hợp đồng
- Xem báo cáo điều hành

---

# 3. ACTION DEFINITIONS

## C

Create

---

## R

Read

---

## U

Update

---

## D

Delete (Soft Delete)

---

## A

Approve

---

## RJ

Reject

---

## EX

Export

---

## IM

Import

---

## AS

Assign

---

## CL

Close

---

# 4. ORGANIZATION MODULE

| Action | Super Admin | Sys Admin | HR Manager | HR Officer | Finance | Manager | Employee | Director |
|----------|------------|------------|------------|------------|------------|------------|------------|------------|
| Create | Y | N | Y | N | N | N | N | N |
| Read | Y | Y | Y | Y | N | Y | N | Y |
| Update | Y | N | Y | N | N | N | N | N |
| Delete | Y | N | N | N | N | N | N | N |
| Export | Y | Y | Y | Y | N | N | N | Y |

---

# 5. HUMAN RESOURCE MODULE

## Employee List

| Action | Super Admin | Sys Admin | HR Manager | HR Officer | Finance | Manager | Employee | Director |
|----------|------------|------------|------------|------------|------------|------------|------------|------------|
| Create | Y | N | Y | Y | N | N | N | N |
| Read All | Y | N | Y | Y | N | N | N | Y |
| Read Own | Y | Y | Y | Y | Y | Y | Y | Y |
| Update | Y | N | Y | Y | N | N | Own | N |
| Delete | Y | N | N | N | N | N | N | N |
| Export | Y | N | Y | Y | N | N | N | Y |

---

## Employee Attachment

| Action | Super Admin | HR Manager | HR Officer | Employee |
|----------|------------|------------|------------|------------|
| Upload | Y | Y | Y | Own |
| Download | Y | Y | Y | Own |
| Delete | Y | Y | N | N |

---

# 6. RECRUITMENT MODULE

| Action | Super Admin | HR Manager | HR Officer | Manager | Director |
|----------|------------|------------|------------|------------|------------|
| Create Request | Y | Y | Y | Y | N |
| Approve Request | Y | N | N | Y | Y |
| Create Vacancy | Y | Y | Y | N | N |
| Candidate Management | Y | Y | Y | N | N |
| Interview Result | Y | Y | Y | Y | Y |
| Offer Approval | Y | Y | N | N | Y |
| Export | Y | Y | Y | N | Y |

---

# 7. ATTENDANCE MODULE

| Action | Super Admin | HR Manager | HR Officer | Manager | Employee | Director |
|----------|------------|------------|------------|------------|------------|------------|
| Read All | Y | Y | Y | Department | Own | Y |
| Create Adjustment | Y | Y | Y | N | Request | N |
| Approve Adjustment | Y | Y | N | Y | N | N |
| Lock Attendance | Y | Y | N | N | N | N |
| Export | Y | Y | Y | N | N | Y |

---

# 8. LEAVE MODULE

| Action | Super Admin | HR Manager | HR Officer | Manager | Employee | Director |
|----------|------------|------------|------------|------------|------------|------------|
| Create Request | Y | Y | Y | Y | Y | N |
| Read | Y | Y | Y | Department | Own | Y |
| Approve | Y | Y | N | Y | N | N |
| Reject | Y | Y | N | Y | N | N |
| Cancel Request | Y | Y | Y | N | Own | N |
| Export | Y | Y | Y | N | N | Y |

---

# 9. PAYROLL MODULE

| Action | Super Admin | HR Manager | Finance | Employee | Director |
|----------|------------|------------|------------|------------|------------|
| Read Payroll | Y | Y | Y | Own | Y |
| Create Payroll | Y | Y | Y | N | N |
| Recalculate Payroll | Y | Y | Y | N | N |
| Approve Payroll | Y | N | N | N | Y |
| Lock Payroll | Y | Y | Y | N | N |
| Export Payroll | Y | Y | Y | N | Y |

---

# 10. CONTRACT MODULE

| Action | Super Admin | HR Manager | HR Officer | Employee | Director |
|----------|------------|------------|------------|------------|------------|
| Create Contract | Y | Y | Y | N | N |
| Read Contract | Y | Y | Y | Own | Y |
| Update Contract | Y | Y | Y | N | N |
| Approve Contract | Y | N | N | N | Y |
| Renew Contract | Y | Y | Y | N | N |
| Export | Y | Y | N | N | Y |

---

# 11. DOCUMENT MODULE

| Action | Super Admin | HR Manager | HR Officer | Manager | Employee | Director |
|----------|------------|------------|------------|------------|------------|------------|
| Create | Y | Y | Y | Y | N | N |
| Read | Y | Y | Y | Y | By Permission | Y |
| Update | Y | Y | Y | N | N | N |
| Approve | Y | Y | N | N | N | N |
| Publish | Y | Y | N | N | N | N |
| Export | Y | Y | Y | Y | N | Y |

---

# 12. TASK MODULE

| Action | Super Admin | Manager | Employee | Director |
|----------|------------|------------|------------|------------|
| Create | Y | Y | Y | Y |
| Assign | Y | Y | N | Y |
| Update Progress | Y | Y | Own | N |
| Complete | Y | Y | Own | N |
| Approve | Y | Y | N | Y |
| View All | Y | Department | Own | All |
| Export | Y | Y | N | Y |

---

# 13. KPI MODULE

| Action | Super Admin | HR Manager | Manager | Employee | Director |
|----------|------------|------------|------------|------------|------------|
| Create KPI | Y | Y | Y | N | N |
| Assign KPI | Y | Y | Y | N | N |
| Update Actual | Y | Y | Y | Own | N |
| Evaluate KPI | Y | Y | Y | N | N |
| View KPI | Y | Y | Department | Own | All |
| Export KPI | Y | Y | N | N | Y |

---

# 14. ASSET MODULE

| Action | Super/System Admin | HR Manager/Officer | Finance Officer | Project Coordinator | Director | Other staff/CBDA |
|----------|--------------------|--------------------|-----------------|---------------------|----------|------------------|
| View asset, inventory and disposal records | Y | Y | Y | Y | Y | N |
| Manage assets and inventory | Y | Y | N | N | N | N |
| Create/prepare disposal records | Y | Y | N | N | N | N |
| Approve disposal request | Y | N | N | N | Y* | N |

`view_asset` controls the portal menus, personal asset list, read-only asset pages and Django Admin visibility. `manage_asset` is limited to HR and system administrators. Director approval continues to use the existing director-employee check. Ordinary employees, department managers, project managers and CBDA do not get asset navigation or direct page access.

---

# 15. PROCUREMENT MODULE

| Action | Super Admin | Finance | Manager | Employee | Director |
|----------|------------|------------|------------|------------|------------|
| Create Request | Y | N | Y | Y | N |
| Read Request | Y | Y | Department | Own | Y |
| Approve Budget | Y | Y | N | N | N |
| Approve Final | Y | N | N | N | Y |
| Close Request | Y | Y | N | N | N |
| Export | Y | Y | N | N | Y |

---

# 16. DASHBOARD MODULE

| Dashboard | Super Admin | HR Manager | HR Officer | Finance | Manager | Employee | Director |
|------------|------------|------------|------------|------------|------------|------------|------------|
| Director Dashboard | Y | N | N | N | N | N | Y |
| HR Dashboard | Y | Y | Y | N | N | N | Y |
| Manager Dashboard | Y | N | N | N | Y | N | Y |
| Personal Dashboard | Y | Y | Y | Y | Y | Y | Y |

---

# 17. ADMINISTRATION MODULE

| Action | Super Admin | Sys Admin | Director |
|----------|------------|------------|------------|
| User Management | Y | Y | N |
| Role Management | Y | N | N |
| Permission Management | Y | N | N |
| System Config | Y | Y | N |
| Audit Log | Y | Y | Y |
| Login Log | Y | Y | N |

---

# 18. MICROSOFT 365 MODULE

| Action | Super Admin | Sys Admin | HR Manager | User |
|----------|------------|------------|------------|------------|
| Connect M365 | Y | Y | N | N |
| Sync Users | Y | Y | N | N |
| Send Email | Y | Y | Y | Own |
| Teams Notify | Y | Y | Y | N |
| SharePoint Access | By Permission | By Permission | By Permission | By Permission |

---

# 19. DATA ACCESS MATRIX

## Employee

```text
Chỉ xem dữ liệu cá nhân
```

---

## Department Manager

```text
Chỉ xem nhân viên phòng mình
```

---

## HR Officer

```text
Xem toàn bộ dữ liệu nhân sự
```

Không xem:

```text
Audit hệ thống
Role
Permission
```

---

## HR Manager

```text
Toàn bộ dữ liệu HR
```

---

## Finance

```text
Payroll
Procurement
```

---

## Director

```text
Toàn công ty
```

---

# 20. MENU VISIBILITY MATRIX

## Employee

```text
Dashboard

My Profile

Attendance

Leave

Tasks

KPI

Documents

Payslip
```

---

## Manager

```text
Employee Menu

+

Team

Approvals

Department KPI
```

---

## HR

```text
Human Resources

Recruitment

Attendance

Leave

Contracts
```

---

## Finance

```text
Payroll

Procurement

Reports
```

---

## Director

```text
Executive Dashboard

Executive Reports

Approvals
```

---

# 21. API AUTHORIZATION RULES

Mọi API phải:

✅ Authenticate

✅ Authorize

✅ Validate Role

✅ Validate Data Scope

✅ Log Activity

---

# 22. PERMISSION APPROVAL

Status:

Approved

Ready For:

- Django Permission Implementation
- JWT Claims Design
- Menu Security
- API Authorization
- UAT

# 10A_Role_Naming_Mapping_Addendum.md

# PHỤ LỤC: ÁNH XẠ TÊN VAI TRÒ (ROLE NAMING MAPPING)

## Project

Internal Administration & Human Resource Management System (IHRMS)

## Bổ sung cho

00_Project_Charter.md (mục 8), 01_BRD_MASTER.md (mục 3), 10_RBAC_Permission_Matrix.md (mục 2)

## Version

1.0

## Status

Draft — cần xác nhận để tránh nhầm lẫn khi cấu hình `tblRole`

## Lý do bổ sung

`00_Project_Charter.md` mục 8 định nghĩa 8 nhóm người dùng gồm **"IT Administrator"** và **"System Administrator"**. Khi sang đến `10_RBAC_Permission_Matrix.md` mục 2, 8 vai trò cụ thể hóa thành **"Super Admin" (R01)** và **"System Admin" (R02)** — không có ghi chú nào xác nhận đây là cùng một vai trò được đổi tên, hay là 2 vai trò bổ sung mới nằm ngoài Charter. Nếu không làm rõ trước khi tạo dữ liệu danh mục `tblRole`, đội phát triển và người dùng cuối có thể hiểu nhầm thành 10 vai trò thay vì 8.

---

# 1. BẢNG ĐỐI CHIẾU

| # | Charter (00) / BRD (01) | RBAC Matrix (10) — Mã vai trò | Đối chiếu |
|---|---|---|---|
| 1 | Director | R08 - Director | Khớp tên |
| 2 | HR Manager | R03 - HR Manager | Khớp tên |
| 3 | HR Officer | R04 - HR Officer | Khớp tên |
| 4 | Finance Officer | R05 - Finance Officer | Khớp tên |
| 5 | Department Manager | R06 - Department Manager | Khớp tên |
| 6 | Employee | R07 - Employee | Khớp tên |
| 7 | **IT Administrator** | **R02 - System Admin** | ⚠️ Tên khác nhau — cần xác nhận là 1 vai trò |
| 8 | **System Administrator** | **R01 - Super Admin** | ⚠️ Tên khác nhau — cần xác nhận là 1 vai trò |

**Diễn giải đề xuất** (dựa trên mô tả quyền hạn ở `10_RBAC_Permission_Matrix.md`):

- Charter "**System Administrator**" (vai trò cao nhất, quản trị toàn hệ thống) = RBAC "**R01 - Super Admin**" (Phạm vi: Toàn bộ hệ thống; Quyền: Cấu hình hệ thống, Quản trị người dùng/vai trò/phân quyền, Truy cập toàn bộ dữ liệu).
- Charter "**IT Administrator**" (quản trị hạ tầng kỹ thuật) = RBAC "**R02 - System Admin**" (Phạm vi: Hạ tầng và kỹ thuật; Quyền: Quản lý tài khoản, phân quyền, xem Audit Log; **Không được** sửa/duyệt lương).

Cách ánh xạ này hợp lý vì tên "System Admin" (R02) trong RBAC trùng khớp về ngữ nghĩa với "IT Administrator" (hạ tầng/kỹ thuật) hơn là với "System Administrator" (quản trị toàn hệ thống) của Charter — tránh để 2 role tên gần giống nhau ("System Administrator" và "System Admin") dễ gây nhầm khi thao tác trên UI phân quyền.

---

# 2. KHUYẾN NGHỊ CHUẨN HÓA TÊN GỌI DUY NHẤT

Để tránh việc 1 vai trò có 2 tên gọi khác nhau tồn tại song song trong các tài liệu, đề xuất **chốt danh sách tên hiển thị (display name) chính thức** dùng xuyên suốt từ Charter → BRD → RBAC → UI → `tblRole.RoleName`:

| RoleCode (tblRole) | Display Name (Tiếng Việt) | Display Name (English) | Thay thế tên cũ |
|---|---|---|---|
| SUPER_ADMIN | Quản trị viên hệ thống | Super Admin | ~~System Administrator~~ (Charter) |
| SYS_ADMIN | Quản trị viên kỹ thuật | System Admin | ~~IT Administrator~~ (Charter) |
| HR_MANAGER | Trưởng phòng Nhân sự | HR Manager | — |
| HR_OFFICER | Chuyên viên Nhân sự | HR Officer | — |
| FINANCE_OFFICER | Kế toán | Finance Officer | — |
| DEPT_MANAGER | Trưởng phòng ban | Department Manager | — |
| EMPLOYEE | Nhân viên | Employee | — |
| DIRECTOR | Ban Giám đốc | Director | — |

**Hành động cần thực hiện:**
1. Cập nhật `00_Project_Charter.md` mục 8: đổi "System Administrator" → "Super Admin", "IT Administrator" → "System Admin" (hoặc giữ nguyên Charter và ghi chú tương đương ngay tại RBAC — tùy bên nào được coi là văn bản gốc để sửa).
2. Dùng đúng 8 `RoleCode` ở bảng trên khi seed dữ liệu `tblRole` ban đầu (`INITIAL DATA / SEED SCRIPT`), không tự thêm role thứ 9 nếu không phát sinh yêu cầu nghiệp vụ mới.
3. `09_UI_UX_Specification.md` (nếu có màn hình quản lý người dùng) dùng đúng Display Name tiếng Việt ở bảng trên.

---

# 3. LƯU Ý LIÊN QUAN — PHÂN BIỆT "ROLE" VÀ "PHÒNG BAN HÀNH CHÍNH NHÂN SỰ"

`00_Project_Charter.md` mục 7 ("CƠ CẤU TỔ CHỨC ÁP DỤNG") liệt kê các đơn vị tổ chức: Ban Giám Đốc, Hành Chính Nhân Sự, Kế Toán, Chương Trình, MEL, IT, Văn Phòng Dự Án, Văn Phòng Trung Tâm — đây là **danh mục phòng ban** (`tblDepartment`), khác với **danh sách vai trò hệ thống** (`tblRole`) ở mục 8. Hai khái niệm không nên bị đánh đồng: một nhân viên phòng "Hành Chính Nhân Sự" có thể được gán role `HR_OFFICER` hoặc `HR_MANAGER` tùy vị trí, không tự động suy ra role từ tên phòng ban. Cần ghi rõ điều này trong tài liệu đào tạo/hướng dẫn nhập liệu ban đầu để tránh nhân viên IT hiểu nhầm "phòng ban IT" đương nhiên có role "System Admin".

---

# 4. TRẠNG THÁI PHÊ DUYỆT

Cần HR Manager và IT Administrator (theo tên gọi hiện tại của Charter) xác nhận bảng ánh xạ ở mục 1 trước khi seed dữ liệu `tblRole` vào môi trường Production.
