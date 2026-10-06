# WORKFLOW DEFINITION DOCUMENT

## Project

Internal Administration & Human Resource Management System (IHRMS)

## Version

1.0

## Status

Approved

---

# 1. PURPOSE

Tài liệu này định nghĩa toàn bộ quy trình xử lý nghiệp vụ (Workflow) trong hệ thống.

Mục tiêu:

- Chuẩn hóa quy trình
- Chuẩn hóa phê duyệt
- Chuẩn hóa phân quyền
- Chuẩn hóa thông báo
- Chuẩn hóa Audit Log

Làm cơ sở cho:

- Workflow Engine
- Approval Engine
- Notification Engine
- RBAC
- API
- Dashboard

---

# 2. WORKFLOW DEFINITIONS

## Workflow Status Standard

### Draft

Người dùng đang tạo.

---

### Pending Approval

Đang chờ phê duyệt.

---

### Approved

Được phê duyệt.

---

### Rejected

Bị từ chối.

---

### Cancelled

Đã hủy.

---

### Completed

Đã hoàn thành.

---

# 3. LEAVE REQUEST WORKFLOW

## WF-LEA-001

### Workflow Name

Leave Approval Workflow

---

### Trigger

Nhân viên tạo đơn nghỉ phép.

---

### Actors

```text
Employee

Department Manager

HR Officer
```

---

### Flow

```text
Draft

↓

Submit

↓

Department Manager Approval

↓

HR Confirmation

↓

Completed
```

---

### Reject Flow

```text
Department Manager Reject
OR
HR Reject

↓

Rejected
```

---

### Notifications

Employee

Department Manager

HR Officer

---

### Audit Log

Submit

Approve

Reject

Cancel

---

### SLA

Manager:

2 Working Days

HR:

1 Working Day

---

# 4. ATTENDANCE ADJUSTMENT WORKFLOW

## WF-ATT-001

### Workflow Name

Attendance Adjustment

---

### Trigger

Nhân viên yêu cầu điều chỉnh công.

---

### Actors

```text
Employee

Department Manager

HR Officer
```

---

### Flow

```text
Draft

↓

Submit

↓

Manager Approval

↓

HR Validation

↓

Completed
```

---

### Result

Attendance Record Updated

---

### SLA

Manager:

2 Days

HR:

1 Day

---

# 5. OVERTIME APPROVAL WORKFLOW

## WF-ATT-002

### Trigger

Yêu cầu OT.

---

### Flow

```text
Employee

↓

Manager Approval

↓

HR Review

↓

Approved

↓

Payroll Processing
```

---

### Output

Approved Overtime Hours

---

# 6. RECRUITMENT REQUEST WORKFLOW

## WF-REC-001

### Trigger

Department yêu cầu tuyển dụng.

---

### Actors

```text
Department Manager

HR Manager

Director
```

---

### Flow

```text
Draft

↓

Department Submission

↓

HR Review

↓

Director Approval

↓

Approved
```

---

### Output

Open Recruitment Request

---

### SLA

HR:

3 Days

Director:

3 Days

---

# 7. RECRUITMENT EXECUTION WORKFLOW

## WF-REC-002

### Flow

```text
Recruitment Request

↓

Open Position

↓

Receive Candidate

↓

CV Screening

↓

Interview

↓

Assessment

↓

Offer

↓

Accept Offer

↓

Onboarding
```

---

### Possible Exit

```text
Rejected

Candidate Withdrawn

Offer Rejected
```

---

# 8. INTERVIEW WORKFLOW

## WF-REC-003

### Flow

```text
Candidate

↓

Schedule Interview

↓

Interview

↓

Evaluation

↓

Decision
```

---

### Decision

```text
Pass

Reserve

Fail
```

---

# 9. EMPLOYEE ONBOARDING WORKFLOW

## WF-HR-001

### Trigger

Ứng viên nhận việc.

---

### Flow

```text
Offer Accepted

↓

Create Employee Profile

↓

Create User Account

↓

Assign Department

↓

Assign Assets

↓

Training

↓

Completed
```

---

### Output

Active Employee

---

# 10. EMPLOYEE TRANSFER WORKFLOW

## WF-HR-002

### Trigger

Điều chuyển nhân viên.

---

### Flow

```text
Proposal

↓

Department Approval

↓

HR Approval

↓

Update Employee Profile

↓

Completed
```

---

### Audit

Mandatory

---

# 11. EMPLOYEE TERMINATION WORKFLOW

## WF-HR-003

### Trigger

Nghỉ việc.

---

### Flow

```text
Resignation

↓

Manager Approval

↓

HR Validation

↓

Asset Return

↓

Account Disable

↓

Final Settlement

↓

Completed
```

---

### Output

Inactive Employee

---

# 12. PAYROLL WORKFLOW

## WF-PAY-001

### Trigger

Đến kỳ lương.

---

### Flow

```text
Attendance Lock

↓

Leave Lock

↓

Payroll Calculation

↓

Payroll Review

↓

Director Approval

↓

Payroll Lock

↓

Payslip Release
```

---

### Output

Monthly Payroll

---

### SLA

5 Working Days

---

# 13. CONTRACT CREATION WORKFLOW

## WF-CON-001

### Trigger

Tạo hợp đồng mới.

---

### Flow

```text
Draft Contract

↓

HR Review

↓

Director Approval

↓

Employee Review

↓

Signed

↓

Effective
```

---

### Output

Active Contract

---

# 14. CONTRACT RENEWAL WORKFLOW

## WF-CON-002

### Trigger

Hợp đồng sắp hết hạn.

---

### Reminder

```text
90 Days

60 Days

30 Days
```

---

### Flow

```text
Expiration Alert

↓

HR Review

↓

Director Approval

↓

Renewal

↓

Completed
```

---

# 15. DOCUMENT APPROVAL WORKFLOW

## WF-DOC-001

### Trigger

Tài liệu mới.

---

### Flow

```text
Create Draft

↓

Reviewer

↓

Approver

↓

Publish

↓

Released
```

---

### Version Control

Mandatory

---

## WF-HR-DEC-001 — Quyết định nhân sự

### Flow

```text
Save Draft
↓
Submit for Approval
↓
Approve / Reject
↓
Upload signed PDF and Issue
```

HR Officer/HR Manager tạo, sửa và trình bản nháp. HR Manager/Director duyệt; người trình không được tự duyệt. Từ chối phải có lý do; HR sửa và lưu lại để tạo lượt trình duyệt mới. Chỉ trạng thái Approved được ban hành và phải kèm PDF đã ký hợp lệ. Mỗi lần lưu/chuyển trạng thái ghi người thao tác, thời gian, trạng thái trước/sau và ghi chú vào lịch sử.

Nội dung quyết định được lưu thành snapshot, tách biệt bản ghi nghiệp vụ nguồn như mức lương hoặc điều chuyển. Sửa, duyệt hay ban hành quyết định không tự áp dụng thay đổi lên hồ sơ nhân viên. Quyền xem/tải bản nháp, PDF ký và lịch sử giới hạn cho HR hoặc người duyệt có tham gia workflow; không đưa quyết định vào thư viện tài liệu công khai.

---

# 16. DOCUMENT REVISION WORKFLOW

## WF-DOC-002

### Flow

```text
Existing Version

↓

Revise

↓

Review

↓

Approve

↓

New Version Published
```

---

# 17. TASK CREATION WORKFLOW

## WF-TASK-001

### Flow

```text
Create Task

↓

Assign

↓

In Progress

↓

Review

↓

Approved

↓

Done
```

---

### Optional

```text
Cancel
```

---

# 18. TASK OVERDUE WORKFLOW

## WF-TASK-002

### Trigger

Deadline Passed

---

### Flow

```text
Task Overdue

↓

Notification

↓

Reminder

↓

Escalation

↓

Manager Review
```

---

### Notifications

Teams

Email

In-App

---

# 19. KPI ASSIGNMENT WORKFLOW

## WF-KPI-001

### Flow

```text
Create KPI

↓

Assign KPI

↓

Accept KPI

↓

Start Measurement
```

---

# 20. KPI EVALUATION WORKFLOW

## WF-KPI-002

### Flow

```text
Target

↓

Actual Update

↓

Calculation

↓

Manager Review

↓

Final Evaluation

↓

Completed
```

---

# 21. ASSET PROCUREMENT WORKFLOW

## WF-PRO-001

### Trigger

Yêu cầu mua sắm.

---

### Actors

```text
Employee

Department Manager

Finance

Director
```

---

### Flow

```text
Request

↓

Department Approval

↓

Budget Review

↓

Director Approval

↓

Purchase

↓

Receive

↓

Completed
```

---

### Reject Flow

```text
Any Approval Level

↓

Rejected
```

---

# 22. ASSET ALLOCATION WORKFLOW

## WF-AST-001

### Trigger

Cấp phát tài sản.

---

### Flow

```text
Asset Available

↓

Assign Employee

↓

Accept Asset

↓

Allocation Completed
```

---

### Output

Asset Allocation Record

---

# 23. ASSET RETURN WORKFLOW

## WF-AST-002

### Trigger

Nghỉ việc hoặc thu hồi.

---

### Flow

```text
Return Request

↓

Asset Inspection

↓

Condition Assessment

↓

Inventory Update

↓

Completed
```

---

# 24. USER ACCOUNT CREATION WORKFLOW

## WF-SEC-001

### Trigger

Nhân viên mới.

---

### Flow

```text
Employee Created

↓

Create Account

↓

Assign Role

↓

Enable Access

↓

Send Credentials
```

---

# 25. USER DEACTIVATION WORKFLOW

## WF-SEC-002

### Trigger

Nhân viên nghỉ việc.

---

### Flow

```text
Termination

↓

Disable User

↓

Revoke Access

↓

Archive Profile

↓

Completed
```

---

# 26. MICROSOFT 365 DOCUMENT WORKFLOW

## WF-M365-001

### Flow

```text
Upload Document

↓

SharePoint

↓

Metadata Registration

↓

Permission Assignment

↓

Available
```

---

# 27. MICROSOFT 365 NOTIFICATION WORKFLOW

## WF-M365-002

### Trigger Sources

```text
Leave

Task

Recruitment

Contract

Procurement
```

---

### Flow

```text
Business Event

↓

Notification Engine

↓

Teams

↓

Outlook

↓

In-App Notification
```

---

# 28. WORKFLOW SLA MATRIX

| Workflow | Level 1 | Level 2 | Level 3 |
|----------|----------|----------|----------|
| Leave | 2 Days | 1 Day | - |
| Attendance Adjustment | 2 Days | 1 Day | - |
| Recruitment Request | 3 Days | 3 Days | - |
| Payroll | 5 Days | - | - |
| Contract | 3 Days | 3 Days | - |
| Procurement | 2 Days | 3 Days | 3 Days |

---

# 29. ESCALATION RULES

## Rule 01

Quá SLA 01 ngày

↓

Gửi Reminder

---

## Rule 02

Quá SLA 03 ngày

↓

Thông báo cấp trên

---

## Rule 03

Quá SLA 05 ngày

↓

Escalate tới Director

---

# 30. NOTIFICATION RULES

## Mandatory Notifications

```text
Leave Request

Leave Approval

Recruitment Approval

Offer Accepted

Contract Expiring

Task Overdue

Procurement Approval

Payroll Release
```

---

# 31. AUDIT REQUIREMENTS

Bắt buộc lưu:

```text
Workflow Name

Current Stage

Decision

Decision By

Decision Date

Comments
```

---

# 32. WORKFLOW APPROVAL

Status:

Approved

Ready For:

- Workflow Engine
- Database Workflow Tables
- API Development
- UI Development
- Testing