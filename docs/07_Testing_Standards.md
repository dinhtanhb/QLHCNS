# TESTING STANDARDS DOCUMENT

## Project

Internal Administration & Human Resource Management System (IHRMS)

## Version

1.0

## Status

Approved

---

# 1. PURPOSE

Tài liệu này quy định:

- Chiến lược kiểm thử
- Quy trình kiểm thử
- Chuẩn Test Case
- Chuẩn UAT
- Chuẩn nghiệm thu
- Checklist Go Live

Áp dụng cho toàn bộ hệ thống IHRMS.

---

# 2. TESTING OBJECTIVES

Đảm bảo:

- Đúng nghiệp vụ
- Đúng dữ liệu
- Đúng phân quyền
- Đúng workflow
- Đúng báo cáo
- Đúng tích hợp Microsoft 365
- Hiệu năng đạt yêu cầu
- Bảo mật đạt yêu cầu

---

# 3. TESTING SCOPE

## Module

### Organization

### HRM

### Recruitment

### Attendance

### Leave

### Payroll

### Contract

### Document

### Task

### KPI

### Asset

### Procurement

### Dashboard

### Microsoft 365

---

# 4. TEST ENVIRONMENT

## Development

Developer kiểm thử chức năng.

---

## SIT

System Integration Test.

---

## UAT

User Acceptance Test.

---

## Production

Kiểm thử sau Go Live.

---

# 5. TESTING TYPES

## Unit Test

Kiểm thử từng hàm.

---

## Integration Test

Kiểm thử luồng liên module.

---

## System Test

Kiểm thử toàn hệ thống.

---

## Security Test

Kiểm thử bảo mật.

---

## UAT

Kiểm thử nghiệp vụ người dùng.

---

## Performance Test

Kiểm thử tải.

---

## Regression Test

Kiểm thử hồi quy.

---

# 6. TEST CASE STANDARD

Mỗi Test Case phải có:

```text
Test Case ID

Module

Scenario

Precondition

Test Steps

Expected Result

Actual Result

Status

Tester

Test Date
```

---

# 7. TEST STATUS

## PASS

Kết quả đúng.

---

## FAIL

Kết quả sai.

---

## BLOCKED

Không kiểm thử được.

---

## NOT RUN

Chưa kiểm thử.

---

# 8. ORGANIZATION TEST CASES

## ORG-001

Tạo phòng ban.

Expected:

Phòng ban được tạo thành công.

---

## ORG-002

Cập nhật phòng ban.

Expected:

Thông tin được cập nhật.

---

## ORG-003

Ngừng sử dụng phòng ban.

Expected:

Không hiển thị trong danh sách hoạt động.

---

## ORG-004

Kiểm tra sơ đồ tổ chức.

Expected:

Đúng cấu trúc báo cáo.

---

# 9. HUMAN RESOURCE TEST CASES

## HR-001

Tạo nhân viên mới.

Expected:

Sinh mã nhân viên.

---

## HR-002

Cập nhật hồ sơ.

Expected:

Lưu thay đổi thành công.

---

## HR-003

Upload hồ sơ đính kèm.

Expected:

File lưu SharePoint thành công.

---

## HR-004

Tạo quá trình điều chuyển.

Expected:

Lưu lịch sử điều chuyển.

---

## HR-005

Nghỉ việc nhân viên.

Expected:

Chuyển trạng thái Inactive.

---

## HR-006

Kiểm tra lịch sử nhân sự.

Expected:

Hiển thị đầy đủ.

---

# 10. RECRUITMENT TEST CASES

## REC-001

Tạo yêu cầu tuyển dụng.

---

## REC-002

Phê duyệt tuyển dụng.

---

## REC-003

Tạo vị trí tuyển dụng.

---

## REC-004

Nhập hồ sơ ứng viên.

---

## REC-005

Lên lịch phỏng vấn.

---

## REC-006

Tạo Offer.

---

## REC-007

Tiếp nhận nhân viên.

---

# 11. ATTENDANCE TEST CASES

## ATT-001

Check In.

---

## ATT-002

Check Out.

---

## ATT-003

Ghi nhận OT.

---

## ATT-004

Điều chỉnh công.

---

## ATT-005

Khóa công tháng.

---

## ATT-006

Tính tổng công.

---

# 12. LEAVE TEST CASES

## LEA-001

Tạo đơn nghỉ phép.

---

## LEA-002

Phê duyệt nghỉ phép.

---

## LEA-003

Từ chối nghỉ phép.

---

## LEA-004

Trừ ngày phép.

---

## LEA-005

Kiểm tra số phép còn lại.

---

# 13. PAYROLL TEST CASES

## PAY-001

Sinh bảng lương tháng.

Expected:

Tính đúng lương.

---

## PAY-002

Tính phụ cấp.

---

## PAY-003

Tính OT.

---

## PAY-004

Tính BHXH.

---

## PAY-005

Tính BHYT.

---

## PAY-006

Tính BHTN.

---

## PAY-007

Tính Thuế TNCN.

---

## PAY-008

Tính lương thực nhận.

---

## PAY-009

Khóa bảng lương.

---

## PAY-010

Xuất phiếu lương.

---

# 14. CONTRACT TEST CASES

## CON-001

Tạo hợp đồng.

---

## CON-002

Tạo phụ lục.

---

## CON-003

Gia hạn hợp đồng.

---

## CON-004

Cảnh báo hết hạn.

---

## CON-005

Upload hợp đồng.

---

# 15. DOCUMENT TEST CASES

## DOC-001

Tạo tài liệu.

---

## DOC-002

Upload tài liệu.

---

## DOC-003

Phiên bản mới.

---

## DOC-004

Phê duyệt tài liệu.

---

## DOC-005

Tra cứu tài liệu.

---

# 16. TASK TEST CASES

## TASK-001

Tạo công việc.

---

## TASK-002

Giao việc.

---

## TASK-003

Cập nhật tiến độ.

---

## TASK-004

Đính kèm file.

---

## TASK-005

Checklist.

---

## TASK-006

Comment.

---

## TASK-007

Task quá hạn.

Expected:

Hiển thị trạng thái quá hạn.

---

# 17. KPI TEST CASES

## KPI-001

Tạo KPI.

---

## KPI-002

Nhập Actual.

---

## KPI-003

Tính Achievement.

---

## KPI-004

Tính điểm KPI.

---

## KPI-005

Xếp hạng KPI.

---

# 18. ASSET TEST CASES

## AST-001

Tiếp nhận tài sản.

---

## AST-002

Cấp phát tài sản.

---

## AST-003

Thu hồi tài sản.

---

## AST-004

Bảo trì tài sản.

---

## AST-005

Thanh lý tài sản.

---

# 19. PROCUREMENT TEST CASES

## PRO-001

Tạo đề nghị mua sắm.

---

## PRO-002

Phê duyệt mua sắm.

---

## PRO-003

Bàn giao tài sản.

---

## PRO-004

Đóng đề nghị.

---

# 20. DASHBOARD TEST CASES

## DASH-001

Director Dashboard.

---

## DASH-002

HR Dashboard.

---

## DASH-003

Manager Dashboard.

---

## DASH-004

Bộ lọc Dashboard.

---

## DASH-005

Biểu đồ Dashboard.

---

# 21. MICROSOFT 365 TEST CASES

## M365-001

Đăng nhập SSO.

---

## M365-002

Gửi Email Outlook.

---

## M365-003

Teams Notification.

---

## M365-004

Upload SharePoint.

---

## M365-005

Upload OneDrive.

---

# 22. PERMISSION TEST CASES

## SEC-001

Employee không xem lương người khác.

---

## SEC-002

Manager chỉ xem phòng mình.

---

## SEC-003

HR xem dữ liệu nhân sự toàn công ty.

---

## SEC-004

Director xem Dashboard tổng hợp.

---

## SEC-005

Role không có quyền không được truy cập API.

---

# 23. AUDIT TEST CASES

## AUD-001

Create Log.

---

## AUD-002

Update Log.

---

## AUD-003

Delete Log.

---

## AUD-004

Approve Log.

---

## AUD-005

Export Log.

---

# 24. PERFORMANCE TEST CASES

## PERF-001

Employee List.

Expected:

< 3 giây.

---

## PERF-002

Dashboard.

Expected:

< 5 giây.

---

## PERF-003

Search Employee.

Expected:

< 3 giây.

---

# 25. SECURITY TEST CASES

## SEC-101

JWT Validation.

---

## SEC-102

Expired Token.

---

## SEC-103

Refresh Token.

---

## SEC-104

Permission Validation.

---

## SEC-105

HTTPS Only.

---

## SEC-106

SQL Injection Protection.

---

## SEC-107

XSS Protection.

---

# 26. UAT STRATEGY

## Participants

### Director

### HR Manager

### HR Officer

### Finance Officer

### Department Manager

### Employee

### IT

---

# 27. UAT ACCEPTANCE CRITERIA

Pass Rate:

```text
≥ 95%
```

---

Critical Defect:

```text
0
```

---

High Defect:

```text
0
```

---

# 28. DEFECT SEVERITY

## Critical

Hệ thống ngừng hoạt động.

---

## High

Nghiệp vụ chính không hoạt động.

---

## Medium

Có giải pháp thay thế.

---

## Low

Lỗi giao diện.

---

# 29. GO LIVE CHECKLIST

## System

✅ Application chạy ổn định.

✅ Database hoạt động.

✅ IIS hoạt động.

---

## Security

✅ JWT hoạt động.

✅ SSO hoạt động.

✅ RBAC hoạt động.

---

## Modules

✅ Hệ thống nhân sự.

✅ Chấm công.

✅ Nghỉ phép.

✅ Tiền lương.

✅ Hợp đồng.

✅ Công việc.

✅ KPI.

✅ Tài sản.

✅ Mua sắm.

✅ Dashboard.

---

## Microsoft 365

✅ Outlook.

✅ Teams.

✅ SharePoint.

✅ OneDrive.

---

# 30. POST GO LIVE CHECKLIST

Tuần 1:

✅ Theo dõi lỗi.

✅ Kiểm tra dữ liệu.

✅ Kiểm tra hiệu năng.

---

Tuần 2:

✅ Kiểm tra Backup.

✅ Kiểm tra Audit.

✅ Kiểm tra báo cáo.

---

Tháng 1:

✅ Đánh giá người dùng.

✅ Nghiệm thu chính thức.

---

# 31. DEFINITION OF TEST SUCCESS

Một module được xem là đạt khi:

✅ 100% Test Case thực hiện.

✅ ≥95% PASS.

✅ Không còn lỗi Critical.

✅ Không còn lỗi High.

✅ Workflow hoạt động.

✅ Permission đúng.

✅ Audit Log đúng.

✅ Báo cáo đúng.

---

# 32. TESTING APPROVAL

Status:

Approved

Ready For:

- Development
- SIT
- UAT
- Go Live

---

# 33. AUTOMATED DATABASE REGRESSION

- Mỗi push/PR vào `main` chạy toàn bộ regression trên SQLite qua `.github/workflows/ci.yml`.
- `.github/workflows/sqlserver-regression.yml` chạy toàn bộ regression trên SQL Server vào 00:30 thứ Hai (giờ Việt Nam) và cho phép chạy thủ công bằng `workflow_dispatch`.
- Các test đồng thời dựa vào `select_for_update` chỉ được coi là đã xác nhận khi job SQL Server đạt; kết quả skip trên SQLite không thay thế kiểm tra này.
- Mỗi lượt dùng database `test_ihrms_<UUID>` và media tạm; không trỏ runner vào database nghiệp vụ.
- Trước phát hành cần đối chiếu đúng SHA và trạng thái từng job. Test tự động không thay restore drill, UAT hoặc kiểm tra tích hợp Microsoft 365 trên môi trường đích.
