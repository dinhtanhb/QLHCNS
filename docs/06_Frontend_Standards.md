# FRONTEND DEVELOPMENT STANDARDS

## Project

Internal Administration & Human Resource Management System (IHRMS)

## Version

1.0

## Status

Approved

---

# 1. PURPOSE

Tài liệu này quy định:

- Chuẩn giao diện
- Chuẩn UX
- Chuẩn UI
- Chuẩn màn hình
- Chuẩn Dashboard
- Chuẩn Form
- Chuẩn Data Grid
- Chuẩn Responsive
- Chuẩn Notification
- Chuẩn Workflow UI

Toàn bộ giao diện hệ thống phải tuân thủ tài liệu này.

---

# 2. FRONTEND TECHNOLOGY

## Framework

```text
Bootstrap 5
```

---

## Admin Template

```text
AdminLTE 3
```

---

## Language

```text
HTML5

CSS3

JavaScript ES6

jQuery

AJAX
```

---

# 3. UI DESIGN PRINCIPLES

## UI-001

Simple

Giao diện đơn giản.

---

## UI-002

Consistent

Toàn bộ hệ thống thống nhất.

---

## UI-003

Business First

Ưu tiên nghiệp vụ.

---

## UI-004

Responsive

Hoạt động tốt trên:

- Desktop
- Tablet
- Mobile

---

## UI-005

Data Focused

Ưu tiên khả năng nhập liệu và tra cứu.

---

# 4. APPLICATION LAYOUT

## Layout Structure

```text
------------------------------------------------
Top Navigation Bar
------------------------------------------------

Sidebar

+

Content Area

+

Right Notification Panel (Optional)

------------------------------------------------

Footer
------------------------------------------------
```

---

# 5. HEADER STANDARD

Header phải hiển thị:

```text
Logo

System Name

Notification

Task Reminder

User Profile

Logout
```

---

# 6. SIDEBAR STANDARD

Menu dạng cây.

Ví dụ:

```text
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

Dashboards

Reports

Administration
```

---

# 7. PAGE LAYOUT STANDARD

Mỗi màn hình phải có:

```text
Page Title

Breadcrumb

Toolbar

Search Area

Data Area

Action Buttons
```

---

## Example

```text
Human Resource

Home > HR > Employee

[Create]

[Import]

[Export]

Search

Grid
```

---

# 8. COLOR STANDARD

## Primary

```text
#0F4C81
```

Corporate Blue

---

## Success

```text
#28A745
```

---

## Warning

```text
#FFC107
```

---

## Danger

```text
#DC3545
```

---

## Info

```text
#17A2B8
```

---

## Background

```text
#F4F6F9
```

---

## White

```text
#FFFFFF
```

---

# 9. TYPOGRAPHY STANDARD

## Font Family

```text
Segoe UI
```

---

Fallback

```text
Arial

Sans-serif
```

---

## Font Size

### Title

```text
24px
```

---

### Page Header

```text
20px
```

---

### Section Header

```text
18px
```

---

### Body

```text
14px
```

---

### Small Text

```text
12px
```

---

# 10. ICON STANDARD

Use:

```text
Font Awesome
```

---

Examples

```text
fa-user

fa-users

fa-file

fa-tasks

fa-chart-bar

fa-briefcase
```

---

# 11. BUTTON STANDARD

## Primary Button

```text
Blue
```

Actions:

```text
Save

Create

Submit
```

---

## Success Button

```text
Green
```

Actions:

```text
Approve
```

---

## Warning Button

```text
Yellow
```

Actions:

```text
Edit
```

---

## Danger Button

```text
Red
```

Actions:

```text
Delete

Reject
```

---

## Secondary Button

```text
Gray
```

Actions:

```text
Cancel

Back
```

---

# 12. FORM STANDARD

## Form Layout

Desktop:

```text
2 Columns
```

---

Mobile:

```text
1 Column
```

---

# 13. FORM FIELD STANDARD

Required field:

```text
*
```

Màu đỏ.

---

Example:

```text
Employee Code *
```

---

# 14. INPUT CONTROL STANDARD

## Textbox

Short text.

---

## Text Area

Long description.

---

## Dropdown

Reference data.

---

## Date Picker

Date.

---

## Time Picker

Time.

---

## Number

Numeric value.

---

## Currency

Money.

---

## Checkbox

Boolean.

---

## Radio Button

Single choice.

---

# 15. FORM ACTION AREA

Standard order:

```text
Save

Save & New

Reset

Cancel
```

---

# 16. VALIDATION MESSAGE STANDARD

## Success

```text
Dữ liệu đã được lưu thành công.
```

---

## Warning

```text
Vui lòng kiểm tra lại dữ liệu.
```

---

## Error

```text
Có lỗi xảy ra. Vui lòng thử lại.
```

---

# 17. LIST SCREEN STANDARD

Tất cả danh sách phải có:

```text
Search

Filter

Sort

Pagination

Export
```

---

# 18. DATA GRID STANDARD

Columns:

```text
Code

Name

Status

Created Date

Modified Date

Action
```

---

# 19. PAGINATION STANDARD

Default:

```text
20 records
```

---

Options:

```text
20

50

100
```

---

# 20. SEARCH PANEL STANDARD

Cho phép:

```text
Keyword

Date Range

Status

Department

Employee
```

Theo từng module.

---

# 21. ACTION COLUMN STANDARD

Icons:

```text
View

Edit

Delete

Approve

History
```

---

# 22. DETAIL SCREEN STANDARD

Sections:

```text
General Information

Reference Information

Attachments

History

Audit Log
```

---

# 23. ATTACHMENT STANDARD

Hiển thị:

```text
File Name

File Size

Created Date

Download
```

---

# 24. DASHBOARD STANDARD

## Layout

```text
Filter Area

KPI Area

Charts Area

Detail Area
```

---

# 25. KPI CARD STANDARD

Hiển thị:

```text
Current Value

Previous Value

Trend

Color Indicator
```

---

# 26. KPI COLOR STANDARD

## Success

```text
Green

>=100%
```

---

## Warning

```text
Yellow

80% - 99%
```

---

## Danger

```text
Red

<80%
```

---

# 27. CHART STANDARD

Approved Charts:

```text
Line Chart

Column Chart

Bar Chart

Donut Chart

Pie Chart

Area Chart
```

---

# 28. DASHBOARD FILTER

Cho phép:

```text
Year

Month

Department

Employee
```

---

# 29. TASK BOARD STANDARD

## View 1

Kanban

---

Columns:

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

## View 2

Calendar

---

## View 3

Gantt

---

# 30. PRIORITY COLOR STANDARD

## Low

Gray

---

## Medium

Blue

---

## High

Orange

---

## Critical

Red

---

# 31. TASK STATUS COLOR STANDARD

## Backlog

Gray

---

## To Do

Blue

---

## In Progress

Orange

---

## Review

Purple

---

## Approved

Green

---

## Done

Dark Green

---

## Cancelled

Red

---

# 32. WORKFLOW UI STANDARD

Approval Flow hiển thị:

```text
Current Step

Current Approver

Approval History

Next Approver
```

---

# 33. NOTIFICATION STANDARD

Notifications:

```text
Task

Leave

Recruitment

Contract

Procurement

Document
```

---

# 34. IN-APP NOTIFICATION

Dropdown notification.

Hiển thị:

```text
Title

Date Time

Status
```

---

# 35. EMAIL DESIGN STANDARD

Template chuẩn:

```text
Header

Content

Action Link

Footer
```

---

# 36. MOBILE RESPONSIVE STANDARD

Breakpoint:

## Desktop

```text
>=1200px
```

---

## Tablet

```text
768px - 1199px
```

---

## Mobile

```text
<768px
```

---

# 37. ACCESSIBILITY STANDARD

Support:

```text
Keyboard Navigation

Screen Reader Friendly

Color Contrast
```

---

# 38. PAGE LOADING STANDARD

Loading Indicator bắt buộc.

Ví dụ:

```text
Spinner

Progress Bar
```

---

# 39. EMPTY STATE STANDARD

Khi không có dữ liệu:

```text
Không có dữ liệu.
```

---

Hiển thị:

```text
Create New Button
```

nếu phù hợp.

---

# 40. ERROR PAGE STANDARD

## 403

```text
Không có quyền truy cập.
```

---

## 404

```text
Không tìm thấy dữ liệu.
```

---

## 500

```text
Có lỗi hệ thống.
```

---

# 41. EXPORT STANDARD

Formats:

```text
Excel

PDF
```

---

# 42. IMPORT STANDARD

Import:

```text
Excel Template
```

---

Validation:

```text
Row Level Validation
```

---

# 43. AUDIT VIEW STANDARD

Hiển thị:

```text
Date

User

Action

Old Value

New Value
```

---

# 44. UI TEST CHECKLIST

Trước khi nghiệm thu:

✅ Responsive

✅ Search

✅ Filter

✅ Pagination

✅ Export

✅ Validation

✅ Permission

✅ Notification

✅ Workflow

✅ Audit View

---

# 45. DEFINITION OF DONE

Một màn hình được xem là hoàn thành khi:

✅ UI hoàn chỉnh

✅ Responsive

✅ Validation hoạt động

✅ Permission hoạt động

✅ Workflow hiển thị đúng

✅ Audit hiển thị đúng

✅ Export hoạt động

✅ UAT Pass

---

# 46. FRONTEND APPROVAL

Status:

Approved

Ready For:

- UI Development
- Dashboard Development
- UAT
- Go Live