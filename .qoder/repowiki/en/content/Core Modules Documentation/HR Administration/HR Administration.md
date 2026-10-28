# HR Administration

<cite>
**Referenced Files in This Document**
- [README.md](file://README.md)
- [01_BRD_MASTER.md](file://docs/01_BRD_MASTER.md)
- [02_Solution_Architecture.md](file://docs/02_Solution_Architecture.md)
- [03_Database_Design.md](file://docs/03_Database_Design.md)
- [11_Workflow_Definition.md](file://docs/11_Workflow_Definition.md)
- [HUONG_DAN_SU_DUNG_IHRMS.md](file://docs/HUONG_DAN_SU_DUNG_IHRMS.md)
- [models.py](file://src/apps/hrm/models.py)
- [models.py](file://src/apps/contract/models.py)
- [models.py](file://src/apps/document/models.py)
- [models.py](file://src/apps/lifecycle/models.py)
- [views.py](file://src/apps/document/hcns/views.py)
- [personnel_decision_detail.html](file://src/apps/portal/templates/portal/personnel_decision_detail.html)
- [profile_change_request_list.html](file://src/apps/portal/templates/portal/profile_change_request_list.html)
- [layouts.py](file://src/apps/document/hcns/layouts.py)
- [services.py](file://src/apps/lifecycle/services.py)
- [send_lifecycle_reminders.py](file://src/apps/lifecycle/management/commands/send_lifecycle_reminders.py)
- [common.py](file://src/apps/portal/views/common.py)
- [hr.py](file://src/apps/portal/views/hr.py)
- [hr_contract_list.html](file://src/apps/portal/templates/portal/hr_contract_list.html)
- [hr_contract_form.html](file://src/apps/portal/templates/portal/hr_contract_form.html)
- [hr_employee_list.html](file://src/apps/portal/templates/portal/hr_employee_list.html)
- [status_tabs.html](file://src/templates/ui/status_tabs.html)
- [shared_components.css](file://src/static/css/shared_components.css)
- [hr_ui.css](file://src/static/css/hr_ui.css)
</cite>

## Update Summary
**Changes Made**
- Updated Employee List View section to reflect enhanced contract type information using Subqueries
- Added Status Tabs Implementation section documenting the new shared status tabs component
- Updated Contract Management Forms section to document two-column layout with contextual rail
- Enhanced Performance Considerations section with Subquery optimization details
- Added new UI components and CSS architecture documentation for status tabs and form layouts

## Table of Contents
1. [Introduction](#introduction)
2. [Project Structure](#project-structure)
3. [Core Components](#core-components)
4. [Architecture Overview](#architecture-overview)
5. [Detailed Component Analysis](#detailed-component-analysis)
6. [Status Tabs Implementation](#status-tabs-implementation)
7. [Enhanced Employee List View](#enhanced-employee-list-view)
8. [Improved Contract Management Forms](#improved-contract-management-forms)
9. [Performance Optimizations](#performance-optimizations)
10. [Dependency Analysis](#dependency-analysis)
11. [Performance Considerations](#performance-considerations)
12. [Troubleshooting Guide](#troubleshooting-guide)
13. [Conclusion](#conclusion)

## Introduction
This document explains the HR administration capabilities implemented in IHRMS, focusing on employee lifecycle management, contract administration, decision workflows, and official document generation. It maps business requirements to Django models, workflow definitions, portal interfaces, and automation helpers used for onboarding and offboarding.

IHRMS is a modular monolith built with Django 5.2, targeting internal administration, human resources, recruitment, attendance, payroll, contracts, documents, tasks, KPIs, assets, procurement, dashboards, and Microsoft 365 integration. The system aims to replace manual Excel, email, Word, paper forms, and fragmented file sharing with a single authoritative platform.

Recent enhancements include an improved employee list view with contract type information, enhanced contract management forms with two-column layout, status tabs implementation, and performance optimizations using Subqueries.

**Section sources**
- [README.md:1-90](file://README.md#L1-L90)
- [01_BRD_MASTER.md:1-148](file://docs/01_BRD_MASTER.md#L1-L148)

## Project Structure
The HR-related functionality spans several Django applications:

| Area | Application | Responsibility |
|---|---|---|
| Employee data and personnel changes | `apps/hrm` | Employee profile, change requests, transfers, promotions, rewards, discipline |
| Contracts | `apps/contract` | Contract types, contracts, appendices |
| Documents and decisions | `apps/document` | General documents, approvals, personnel decisions, dispatch books, official dispatches |
| Lifecycle checklists | `apps/lifecycle` | Onboarding/offboarding templates, cases, checklist items, reminders |
| Portal UI | `apps/portal` | Decision detail page, profile change request list, navigation and actions |
| Layouts and rendering | `apps/document/hcns` | Decision layouts, Word export, template selection |

```mermaid
graph TB
User["User / HR Officer"] --> Portal["Portal UI"]
Portal --> Hrm["HRM Models"]
Portal --> Contract["Contract Models"]
Portal --> Document["Document Models"]
Portal --> Lifecycle["Lifecycle Models"]
Document --> HcnsLayouts["HCNS Layouts"]
Lifecycle --> Notification["Notification Service"]
```

**Diagram sources**
- [models.py:11-124](file://src/apps/hrm/models.py#L11-L124)
- [models.py:19-76](file://src/apps/contract/models.py#L19-L76)
- [models.py:100-163](file://src/apps/document/models.py#L100-L163)
- [models.py:6-94](file://src/apps/lifecycle/models.py#L6-L94)
- [layouts.py:17-35](file://src/apps/document/hcns/layouts.py#L17-L35)

**Section sources**
- [02_Solution_Architecture.md:277-388](file://docs/02_Solution_Architecture.md#L277-L388)
- [01_BRD_MASTER.md:128-148](file://docs/01_BRD_MASTER.md#L128-L148)

## Core Components
This section summarizes the main HR administration entities and their responsibilities.

### Employee Model
The employee model stores personal identity, contact information, organizational assignment, employment status, and photo reference. It also exposes related history through foreign keys such as transfers, promotions, rewards, disciplines, contracts, and personnel decisions.

| Field group | Fields | Purpose |
|---|---|---|
| Identity | Employee code, first name, last name, full name, date of birth, gender | Unique identification and basic demographics |
| Legal identifiers | National ID, tax code, social insurance number | Compliance and payroll/benefits linkage |
| Contact | Personal email, company email, mobile phone, address | Communication and correspondence |
| Employment dates | Join date, leave date | Lifecycle boundaries |
| Organization | Department, position, job title, direct manager | Reporting structure and role context |
| Status and media | Employment status, photo URL | Current state and profile image reference |

The database design also defines common audit fields across business tables, including created/modified/deleted metadata and soft delete flags.

**Section sources**
- [models.py:11-71](file://src/apps/hrm/models.py#L11-L71)
- [03_Database_Design.md:103-118](file://docs/03_Database_Design.md#L103-L118)
- [03_Database_Design.md:194-240](file://docs/03_Database_Design.md#L194-L240)

### Profile Change Requests
Employees can request updates to a controlled whitelist of personal fields. Each request captures the target field, current value, proposed value, reason, optional attachment, approval status, decision metadata, and a submitted snapshot to prevent race conditions when HR modifies the same field while a request is pending.

| Aspect | Behavior |
|---|---|
| Allowed fields | Personal email, mobile phone, address |
| States | Pending, Approved, Rejected, NeedsMoreInfo |
| Validation | Rejects fields outside the allowed whitelist |
| Security | Attachment uses validated upload path; sensitive fields are not exposed broadly |
| UI | Employees create requests; HR reviews and decides |

**Section sources**
- [models.py:74-124](file://src/apps/hrm/models.py#L74-L124)
- [profile_change_request_list.html:1-10](file://src/apps/portal/templates/portal/profile_change_request_list.html#L1-L10)
- [HUONG_DAN_SU_DUNG_IHRMS.md:34-42](file://docs/HUONG_DAN_SU_DUNG_IHRMS.md#L34-L42)
- [HUONG_DAN_SU_DUNG_IHRMS.md:113-114](file://docs/HUONG_DAN_SU_DUNG_IHRMS.md#L113-L114)

### Employee History and Personnel Actions
The HR module tracks personnel movements and events:

| Entity | Meaning |
|---|---|
| Transfer | Movement between departments with effective date and reason |
| Promotion | Position change with old and new positions, effective date, and reason |
| Reward | Recognition event with type, date, amount, and description |
| Discipline | Disciplinary action with type, date, and description |

Both transfer and promotion trigger due-change processing so that organizational assignments reflect approved effective dates.

**Section sources**
- [models.py:125-186](file://src/apps/hrm/models.py#L125-L186)
- [03_Database_Design.md:334-434](file://docs/03_Database_Design.md#L334-L434)

## Architecture Overview
The HR administration flow integrates user interface, Django models, workflow rules, and document generation.

```mermaid
sequenceDiagram
participant Employee as "Employee"
participant Portal as "Portal UI"
participant Hrm as "HRM Models"
participant Document as "Document Models"
participant Layouts as "HCNS Layouts"
participant Storage as "File Storage"
Employee->>Portal : Create profile change request
Portal->>Hrm : Validate and save request
Note over Hrm : Snapshot stored to protect against concurrent changes
Employee->>Portal : View request list
Portal-->>Employee : Show status, values, attachments
HR->>Portal : Approve or reject request
Portal->>Hrm : Update status and decision metadata
```

**Diagram sources**
- [models.py:74-124](file://src/apps/hrm/models.py#L74-L124)
- [profile_change_request_list.html:1-10](file://src/apps/portal/templates/portal/profile_change_request_list.html#L1-L10)

```mermaid
sequenceDiagram
participant HR as "HR Officer"
participant Portal as "Decision Detail UI"
participant Document as "PersonnelDecision"
participant Layouts as "HCNS Layouts"
participant Storage as "Signed PDF Storage"
HR->>Portal : Save draft decision
Portal->>Document : Persist draft with content snapshot
HR->>Portal : Submit for approval
Portal->>Document : Set PendingApproval
HR->>Portal : Approve or reject
Portal->>Document : Update status and history
HR->>Portal : Issue decision with signed PDF
Portal->>Storage : Upload signed PDF
Portal->>Layouts : Render Word/PDF layout
```

**Diagram sources**
- [views.py:157-188](file://src/apps/document/hcns/views.py#L157-L188)
- [views.py:430-476](file://src/apps/document/hcns/views.py#L430-L476)
- [personnel_decision_detail.html:1-14](file://src/apps/portal/templates/portal/personnel_decision_detail.html#L1-L14)
- [layouts.py:17-35](file://src/apps/document/hcns/layouts.py#L17-L35)

**Section sources**
- [02_Solution_Architecture.md:438-524](file://docs/02_Solution_Architecture.md#L438-L524)
- [02_Solution_Architecture.md:592-633](file://docs/02_Solution_Architecture.md#L592-L633)

## Detailed Component Analysis

### Employee Lifecycle Management
The lifecycle module provides structured checklists for onboarding and offboarding. A checklist template defines steps, responsible roles, due offsets, and whether asset return is required. An employee lifecycle case represents one onboarding or offboarding instance, and each checklist item tracks assignment, due date, completion, skip reasons, reminders, and optional asset allocation linkage.

```mermaid
classDiagram
class ChecklistTemplate {
+string template_code
+string template_name
+enum template_type
+bool is_active
}
class ChecklistTemplateItem {
+int sequence
+string item_name
+string responsible_role_code
+int due_offset_days
+bool requires_asset_return
}
class EmployeeLifecycleCase {
+enum case_type
+date effective_date
+enum status
+string triggering_event_ref
}
class LifecycleChecklistItem {
+string item_name
+string responsible_role_code
+bool requires_asset_return
+date due_date
+enum status
+date completed_at
+string skip_reason
+date last_reminded_on
}
ChecklistTemplateItem --> ChecklistTemplate : "belongs to"
LifecycleChecklistItem --> EmployeeLifecycleCase : "belongs to"
LifecycleChecklistItem --> ChecklistTemplateItem : "cloned from"
```

**Diagram sources**
- [models.py:6-94](file://src/apps/lifecycle/models.py#L6-L94)

Onboarding and offboarding cases are opened by service functions that validate the template, create or reuse a case, and clone template items into checklist items. Reminders are generated by a management command that calls the reminder service.

```mermaid
flowchart TD
Start(["Open lifecycle case"]) --> Validate["Validate template and case type"]
Validate --> Exists{"Case already exists?"}
Exists --> |Yes| ReturnExisting["Return existing case"]
Exists --> |No| CreateCase["Create EmployeeLifecycleCase"]
CreateCase --> CloneItems["Clone template items"]
CloneItems --> AssignDue["Compute due dates"]
AssignDue --> End(["Case ready"])
```

**Diagram sources**
- [services.py:10-33](file://src/apps/lifecycle/services.py#L10-L33)

**Section sources**
- [models.py:6-94](file://src/apps/lifecycle/models.py#L6-L94)
- [services.py:10-33](file://src/apps/lifecycle/services.py#L10-L33)
- [send_lifecycle_reminders.py:1-11](file://src/apps/lifecycle/management/commands/send_lifecycle_reminders.py#L1-L11)
- [HUONG_DAN_SU_DUNG_IHRMS.md:165-173](file://docs/HUONG_DAN_SU_DUNG_IHRMS.md#L165-L173)

### Contract Administration
Contracts are modeled with a contract type, unique contract number, start and optional end date, basic salary, and status. Appendices allow amendments linked to a base contract.

| Concept | Implementation |
|---|---|
| Contract types | Code and name lookup table |
| Contract states | Draft, Active, Expired, Terminated |
| Date validation | End date must be after start date when present |
| Appendices | Amendment number, effective date, description |

```mermaid
classDiagram
class ContractType {
+string contract_type_code
+string contract_type_name
}
class Contract {
+string contract_no
+date start_date
+date end_date
+decimal basic_salary
+enum status
}
class ContractAppendix {
+string appendix_no
+date effective_date
+string description
}
Contract --> ContractType : "has type"
ContractAppendix --> Contract : "amends"
```

**Diagram sources**
- [models.py:6-16](file://src/apps/contract/models.py#L6-L16)
- [models.py:19-56](file://src/apps/contract/models.py#L19-L56)
- [models.py:59-76](file://src/apps/contract/models.py#L59-L76)

Example usage patterns:
- Creating a contract: select an employee, choose contract type, assign a unique contract number, set start date, optionally set end date, enter basic salary, and save as draft before moving to active status.
- Managing appendices: link an amendment to an existing contract, set effective date, and describe the change.
- Monitoring validity: use contract status and dates to track expiring or terminated agreements.

**Section sources**
- [models.py:19-76](file://src/apps/contract/models.py#L19-L76)
- [01_BRD_MASTER.md:476-508](file://docs/01_BRD_MASTER.md#L476-L508)
- [11_Workflow_Definition.md:640-728](file://docs/11_Workflow_Definition.md#L640-L728)

### Decision Workflow System
Personnel decisions cover appointments, salary adjustments, terminations, maternity benefits, and asset disposal. The system separates the business record from the generated official document and maintains a strict workflow.

Key behaviors:
- Draft creation preserves a content snapshot tied to a template slug.
- Submission requires a decision number and decision date.
- Approval and rejection require appropriate permissions and valid state transitions.
- Issuance requires a signed PDF and moves the decision to issued status.
- History records every state transition, actor, previous state, next state, and comment.
- Decisions do not automatically update the employee profile; they are snapshots for official documentation.

```mermaid
stateDiagram-v2
[*] --> Draft
Draft --> PendingApproval : "Submit"
PendingApproval --> Approved : "Approve"
PendingApproval --> Rejected : "Reject"
Rejected --> Draft : "Revise and resubmit"
Approved --> Issued : "Issue with signed PDF"
Draft --> Cancelled : "Cancel draft"
Rejected --> Cancelled : "Cancel rejected draft"
Issued --> [*]
```

**Diagram sources**
- [models.py:100-163](file://src/apps/document/models.py#L100-L163)
- [views.py:454-476](file://src/apps/document/hcns/views.py#L454-L476)
- [11_Workflow_Definition.md:770-787](file://docs/11_Workflow_Definition.md#L770-L787)

#### Decision Creation Flow
```mermaid
sequenceDiagram
participant HR as "HR Officer"
participant Portal as "Decision Form"
participant Views as "Decision Views"
participant DB as "PersonnelDecision"
HR->>Portal : Enter decision details
Portal->>Views : Save draft
Views->>DB : Validate, set Draft, save snapshot
HR->>Portal : Submit for approval
Portal->>Views : Transition to PendingApproval
Views->>DB : Record Submitted event
```

**Diagram sources**
- [views.py:157-188](file://src/apps/document/hcns/views.py#L157-L188)

#### Decision Approval and Issuance Flow
```mermaid
sequenceDiagram
participant HR as "HR Officer"
participant Portal as "Decision Detail"
participant Views as "Transition Handler"
participant DB as "Decision + History"
participant Storage as "PDF Storage"
HR->>Portal : Approve or reject
Portal->>Views : Send action
Views->>DB : Update status and write history
HR->>Portal : Upload signed PDF and issue
Portal->>Views : Validate and issue
Views->>Storage : Store signed PDF
Views->>DB : Mark Issued
```

**Diagram sources**
- [views.py:430-476](file://src/apps/document/hcns/views.py#L430-L476)
- [personnel_decision_detail.html:25-50](file://src/apps/portal/templates/portal/personnel_decision_detail.html#L25-L50)

**Section sources**
- [models.py:100-163](file://src/apps/document/models.py#L100-L163)
- [views.py:157-188](file://src/apps/document/hcns/views.py#L157-L188)
- [views.py:430-476](file://src/apps/document/hcns/views.py#L430-L476)
- [personnel_decision_detail.html:1-14](file://src/apps/portal/templates/portal/personnel_decision_detail.html#L1-L14)
- [11_Workflow_Definition.md:770-787](file://docs/11_Workflow_Definition.md#L770-L787)

### Document Generation Integration
Official decisions are rendered using HCNS layouts. The layout layer selects subject lines, bases, articles, recipients, and signer based on the template slug and provided values. The decision detail UI supports downloading Word output and printing or saving PDFs when a layout is available.

```mermaid
flowchart TD
Values["Decision values<br/>employee, decision_no, date, articles"] --> Layout["Layout resolver"]
Layout --> TemplateSlug{"Template slug"}
TemplateSlug --> Appointment["Appointment decision layout"]
TemplateSlug --> Generic["Generic decision layout"]
Generic --> Subject["Interpolate subject and articles"]
Appointment --> Output["Rendered context"]
Subject --> Output
Output --> Export["Word download / Print to PDF"]
```

**Diagram sources**
- [layouts.py:17-35](file://src/apps/document/hcns/layouts.py#L17-L35)
- [personnel_decision_detail.html:1-14](file://src/apps/portal/templates/portal/personnel_decision_detail.html#L1-L14)
- [views.py:430-442](file://src/apps/document/hcns/views.py#L430-L442)

**Section sources**
- [layouts.py:17-35](file://src/apps/document/hcns/layouts.py#L17-L35)
- [personnel_decision_detail.html:1-14](file://src/apps/portal/templates/portal/personnel_decision_detail.html#L1-L14)
- [views.py:430-442](file://src/apps/document/hcns/views.py#L430-L442)

### Onboarding and Offboarding Workflows
Onboarding begins when an offer is accepted and continues through employee profile creation, account setup, department assignment, asset assignment, training, and completion. Offboarding covers resignation approval, HR validation, asset return, account disablement, final settlement, and completion.

```mermaid
flowchart TD
Offer["Offer accepted"] --> Onboard["Create employee profile"]
Onboard --> Account["Create user account"]
Account --> Department["Assign department"]
Department --> Assets["Assign assets"]
Assets --> Training["Training"]
Training --> Done["Completed"]
Resignation["Resignation"] --> ManagerApproval["Manager approval"]
ManagerApproval --> HrValidation["HR validation"]
HrValidation --> AssetReturn["Asset return"]
AssetReturn --> AccountDisable["Account disable"]
AccountDisable --> Settlement["Final settlement"]
Settlement --> OffDone["Completed"]
```

**Diagram sources**
- [11_Workflow_Definition.md:450-494](file://docs/11_Workflow_Definition.md#L450-494)
- [11_Workflow_Definition.md:538-583](file://docs/11_Workflow_Definition.md#L538-L583)

Operational guidance:
- HR opens an onboarding or offboarding checklist for the correct employee and active template.
- Checklist items are assigned to responsible roles and marked complete or skipped with reasons.
- Items requiring asset return should link to existing asset allocation records rather than creating history manually.
- Reminder commands generate notifications for overdue checklist items; automatic scheduling depends on IT configuration.

**Section sources**
- [11_Workflow_Definition.md:450-583](file://docs/11_Workflow_Definition.md#L450-L583)
- [HUONG_DAN_SU_DUNG_IHRMS.md:165-173](file://docs/HUONG_DAN_SU_DUNG_IHRMS.md#L165-L173)
- [services.py:10-33](file://src/apps/lifecycle/services.py#L10-L33)
- [send_lifecycle_reminders.py:1-11](file://src/apps/lifecycle/management/commands/send_lifecycle_reminders.py#L1-L11)

## Status Tabs Implementation

The status tabs system provides a unified filtering mechanism across HR list views, replacing traditional dropdown filters with interactive tabs showing real-time counts for each status.

### Shared Status Tabs Component
The `_status_tabs()` function in `views/common.py` generates tab data with accurate counts by performing a single GROUP BY query before applying status filters. This ensures tab counts represent the total distribution across all records, not just filtered results.

```mermaid
flowchart TD
Request["HTTP Request"] --> Queryset["Base Queryset (unfiltered)"]
Queryset --> CountQuery["Single GROUP BY COUNT query"]
CountQuery --> TabData["Tab data with counts"]
TabData --> Template["status_tabs.html template"]
Template --> HTML["Interactive tab links"]
```

**Diagram sources**
- [common.py:29-62](file://src/apps/portal/views/common.py#L29-L62)
- [status_tabs.html:1-9](file://src/templates/ui/status_tabs.html#L1-L9)

### Implementation Details
- **Single Query Optimization**: Uses `annotate(total=models.Count("pk"))` with `values(param)` for efficient counting
- **URL Parameter Handling**: Preserves other filter parameters (q, type) while removing pagination (`page`)
- **Active State Management**: Marks current tab with `aria-current="page"` for accessibility
- **Responsive Design**: Horizontal scrolling with sticky positioning under the header bar

### Applied Pages
Status tabs are implemented across three key HR pages:
- **Personnel Decisions**: 7 tabs covering all decision states
- **Official Dispatches**: 6 tabs generated from model choices
- **Contracts**: 5 tabs for contract status filtering

**Section sources**
- [common.py:29-62](file://src/apps/portal/views/common.py#L29-L62)
- [status_tabs.html:1-9](file://src/templates/ui/status_tabs.html#L1-L9)
- [shared_components.css:155-177](file://src/static/css/shared_components.css#L155-L177)

## Enhanced Employee List View

The employee list view now displays contract type information using optimized Subqueries to avoid N+1 query problems.

### Subquery Implementation
The `hr_employee_list()` view uses Django's `Subquery` and `Exists` to efficiently retrieve the latest contract type for each employee:

```python
latest_contract = Contract.objects.filter(employee_id=OuterRef("pk")).order_by("-start_date", "-pk")
employees = (
    _employee_scope(request)
    .filter(Exists(contracts))
    .select_related("department", "position")
    .annotate(current_contract_type=Subquery(latest_contract.values("contract_type__contract_type_name")[:1]))
    .order_by("full_name")
)
```

### Key Features
- **Performance**: Single query for all employees instead of N+1 queries per row
- **Latest Contract Logic**: Orders by `-start_date, -pk` to get most recent contract
- **Filtering**: Only shows employees who have contracts using `Exists()`
- **Display**: Shows contract type column with fallback "—" for missing data

### Template Updates
The employee list template includes:
- New "Loại hợp đồng" (Contract Type) column
- New "Ngày vào" (Join Date) column with numeric formatting
- Updated column group widths for proper layout

**Section sources**
- [hr.py:57-78](file://src/apps/portal/views/hr.py#L57-L78)
- [hr_employee_list.html:17-25](file://src/apps/portal/templates/portal/hr_employee_list.html#L17-L25)
- [shared_components.css:113-114](file://src/static/css/shared_components.css#L113-L114)

## Improved Contract Management Forms

Contract management forms now feature a two-column layout with contextual information rail to improve data entry accuracy and efficiency.

### Two-Column Layout Architecture
The form uses CSS Grid with responsive behavior:
- **Desktop (≥1280px)**: Main form area + 20rem fixed-width contextual rail
- **Mobile (<1280px)**: Single column layout with rail below form
- **Sticky Rail**: Contextual information stays visible during scrolling

### Contextual Information Rail
When creating contracts from an employee profile, the right rail displays:
- Selected employee summary (name, code, department, position, join date)
- Current contract information (number, type, dates, status)
- Business rules and guidelines
- Quick navigation links

### Form Structure
```mermaid
flowchart TD
FormContainer["ui-form-layout container"] --> MainForm["ui-form-main (left)"]
FormContainer --> ContextRail["ui-form-rail (right)"]
MainForm --> ContractFields["Contract input fields"]
ContextRail --> EmployeeInfo["Selected employee info"]
ContextRail --> CurrentContract["Current contract details"]
ContextRail --> Rules["Business rules"]
```

**Diagram sources**
- [hr_contract_form.html:6-70](file://src/apps/portal/templates/portal/hr_contract_form.html#L6-L70)
- [shared_components.css:179-201](file://src/static/css/shared_components.css#L179-L201)

### View Enhancements
The `hr_contract_create()` view adds contextual data when an employee is selected:
- Loads employee with department and position relationships
- Retrieves current contract with contract type
- Passes both to template for rail display

**Section sources**
- [hr_contract_form.html:6-70](file://src/apps/portal/templates/portal/hr_contract_form.html#L6-L70)
- [hr.py:299-350](file://src/apps/portal/views/hr.py#L299-L350)
- [shared_components.css:179-201](file://src/static/css/shared_components.css#L179-L201)

## Performance Optimizations

Recent changes focus on database query optimization and efficient data retrieval patterns.

### Subquery Pattern for Employee List
The employee list uses Subqueries to avoid N+1 query problems:
- **Before**: Separate query for each employee's latest contract
- **After**: Single annotated query with Subquery for all employees
- **Result**: O(1) additional queries regardless of employee count

### Status Tabs Query Optimization
Status tabs use efficient aggregation:
- **Single GROUP BY query** for all status counts
- **Pre-filtering** before status application to maintain accurate counts
- **Memory-efficient** tab data structure

### Database Query Budget
The system maintains strict query budgets:
- Dashboard pages: ≤25 SELECT queries
- Employee lists: Single query for contract type annotation
- Status tabs: One aggregate query per list view

### Caching Strategies
- **select_related()** for foreign key relationships
- **prefetch_related()** for reverse relations where needed
- **Annotated queries** to minimize round trips

**Section sources**
- [hr.py:57-78](file://src/apps/portal/views/hr.py#L57-L78)
- [common.py:29-62](file://src/apps/portal/views/common.py#L29-L62)

## Dependency Analysis
The HR administration components have clear dependencies:

- `hrm.models` depends on organization models for department, position, and job title.
- `document.models` depends on storage services and upload validators for official documents and decisions.
- `lifecycle.models` depends on notification services for reminders and may link to asset allocation records.
- Portal templates depend on view-provided permissions and URLs for decision workflows and profile change requests.
- HCNS layouts depend on template slugs and interpolated values to render official documents.
- Status tabs depend on the shared `_status_tabs()` utility function.
- Two-column forms depend on CSS Grid layout classes and responsive breakpoints.

```mermaid
graph LR
HrmModels["HRM Models"] --> OrgModels["Organization Models"]
DocumentModels["Document Models"] --> Storage["M365 Storage"]
DocumentModels --> UploadValidators["Upload Validators"]
LifecycleModels["Lifecycle Models"] --> NotificationService["Notification Service"]
PortalTemplates["Portal Templates"] --> DecisionViews["Decision Views"]
DecisionViews --> DocumentModels
HcnsLayouts["HCNS Layouts"] --> DecisionValues["Decision Values"]
StatusTabs["Status Tabs"] --> CommonUtils["Common Utilities"]
TwoColumnForms["Two-Column Forms"] --> CssGrid["CSS Grid Layout"]
```

**Diagram sources**
- [models.py:43-63](file://src/apps/hrm/models.py#L43-L63)
- [models.py:100-124](file://src/apps/document/models.py#L100-L124)
- [models.py:6-94](file://src/apps/lifecycle/models.py#L6-L94)
- [layouts.py:17-35](file://src/apps/document/hcns/layouts.py#L17-L35)
- [common.py:29-62](file://src/apps/portal/views/common.py#L29-L62)
- [shared_components.css:179-201](file://src/static/css/shared_components.css#L179-L201)

**Section sources**
- [models.py:11-124](file://src/apps/hrm/models.py#L11-L124)
- [models.py:100-163](file://src/apps/document/models.py#L100-L163)
- [models.py:6-94](file://src/apps/lifecycle/models.py#L6-L94)
- [layouts.py:17-35](file://src/apps/document/hcns/layouts.py#L17-L35)

## Performance Considerations
- Keep decision drafts small and avoid large inline content; store supporting files in SharePoint or OneDrive and reference them via URLs.
- Use pagination and filtering for employee lists, contract histories, and decision histories.
- Avoid heavy template rendering on every page load; cache layout configuration where safe.
- Schedule lifecycle reminders through Windows Task Scheduler only after confirming runtime stability.
- Monitor storage capacity for SharePoint-backed uploads and ensure backup procedures cover both SQL Server and file storage.
- **New**: Leverage Subqueries for complex joins instead of Python-level loops to prevent N+1 query problems.
- **New**: Use status tabs with pre-aggregated counts to minimize database queries per page load.
- **New**: Implement two-column layouts with CSS Grid for better responsive behavior without JavaScript overhead.

[No sources needed since this section provides general guidance]

## Troubleshooting Guide
Common issues and resolutions:

| Issue | Likely cause | Resolution |
|---|---|---|
| Profile change request rejected during approval | Field value changed after submission snapshot | HR cannot apply stale request; employee creates a new request with updated values |
| Decision cannot be submitted | Missing decision number or decision date | Fill required fields before submitting |
| Decision cannot be approved | Wrong permission or invalid state | Ensure user has approval permission and decision is PendingApproval |
| Decision cannot be issued | No signed PDF or wrong state | Upload a valid signed PDF and ensure decision is Approved |
| Word download fails | Missing filename stem or unavailable layout | Check template slug and rendered context |
| Lifecycle reminder not received | Scheduler not configured | Run reminder command manually and configure Windows Task Scheduler |
| File upload or open error | SharePoint permissions or storage misconfiguration | Report IT with IHRMS record, time, and error; do not delete files directly in SharePoint |
| Employee list shows slow performance | N+1 query problem with contract types | Verify Subquery implementation is working correctly |
| Status tabs show incorrect counts | Query filtering applied before counting | Check that `_status_tabs()` receives unfiltered queryset |
| Two-column form breaks on mobile | CSS Grid breakpoint issues | Verify responsive CSS classes are properly applied |

**Section sources**
- [views.py:454-476](file://src/apps/document/hcns/views.py#L454-L476)
- [HUONG_DAN_SU_DUNG_IHRMS.md:66-75](file://docs/HUONG_DAN_SU_DUNG_IHRMS.md#L66-L75)
- [HUONG_DAN_SU_DUNG_IHRMS.md:216-228](file://docs/HUONG_DAN_SU_DUNG_IHRMS.md#L216-L228)
- [send_lifecycle_reminders.py:1-11](file://src/apps/lifecycle/management/commands/send_lifecycle_reminders.py#L1-L11)

## Conclusion
IHRMS implements HR administration through well-defined models, controlled workflows, and integrated document generation. Employee profiles support personal data and change requests with approval safeguards. Contracts capture types, terms, and appendices. Personnel decisions provide auditable workflows, snapshots, and official document rendering. Lifecycle checklists standardize onboarding and offboarding, while reminders and notifications keep processes visible.

Recent enhancements significantly improve the user experience and system performance:
- **Enhanced employee list view** with contract type information using efficient Subqueries
- **Status tabs implementation** providing intuitive filtering with accurate counts
- **Two-column contract forms** with contextual information rails for better data entry
- **Performance optimizations** reducing database queries and improving response times

For reliable operations, HR should follow the documented workflows, IT should maintain storage and scheduler configuration, and users should treat decisions and attachments as official records requiring proper access control. The new UI patterns and performance improvements ensure the system scales effectively while maintaining usability.

[No sources needed since this section summarizes without analyzing specific files]
