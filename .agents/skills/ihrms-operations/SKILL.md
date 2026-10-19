---
name: ihrms-operations
description: "Vận hành IHRMS: triển khai, hỗ trợ sự cố, chuyển SQLite sang SQL Server, sao lưu, phục hồi và kiểm tra điều kiện phát hành."
---

# IHRMS operations and release

## Operational constraints

- This project handles identifiable HR data and confidential payroll. Use least privilege, separate accounts, TLS, and approved company retention rules.
- The developer has tested/configured IHRMS against SQL Server 2022 Express; production is intended for a company Windows Server/SQL Server environment. Verify backend and target database before every operation. A setting change is not a data migration.
- Do not run destructive management commands or schema/data changes against production. Use a disposable database for rehearsal; require an approved release window and rollback plan for production work.
- `src/` is tracked in the main repository and Django dependencies have been upgraded to 5.2.x; consult the current [Production Readiness Review](../../../docs/Production_Readiness_Review_2026-09-23.md) and project work log before stating deployment readiness. Do not repeat the old gitlink/Django 5.0.14 issue as current state without rechecking.
- Follow the rewritten end-user procedures in [IHRMS User Guide](../../../docs/HUONG_DAN_SU_DUNG_IHRMS.md). Never request or expose passwords, secret keys, full identity numbers, or payroll documents in support messages.

## Environment setup and support

1. Keep development, SIT, UAT, and production configuration/database/files separate.
2. Use environment variables or a protected secret store for credentials. Never commit `.env`; rotate any secret suspected to have been exposed.
3. Production must use a maintained Django patch, compatible pinned packages, a supported SQL Server backend/ODBC driver, HTTPS, secure cookies, an explicit host/CSRF allowlist, production WSGI hosting, collected static assets, controlled media storage, and useful logs.
4. Never use `manage.py runserver` as the production server.
5. Create individual accounts; link each account to the correct employee record; assign only necessary roles. Disable access promptly on departure and review role changes.

## NGO project activity operations

- Activity management is separated in the final **Hoạt động dự án** navigation menu. Approval remains under **Duyệt & Xử lý**.
- The assigned Director opens **Duyệt đề xuất hoạt động** to review only proposals assigned to that account; email links are optional entry points.
- Proposal workflow stores the two PDFs (activity proposal and budget estimate) in the configured SharePoint library. Excel source files are not uploaded by the current user flow.
- Outlook email is user-sent: IHRMS opens a `mailto:` draft; the user checks From/To/CC, manually attaches the two downloaded PDFs, sends, then confirms submission in IHRMS. `mailto:` does not attach files or verify delivery.
- Change requests notify the submitter, proposal creator, assigned CBDA and activity coordinator in the IHRMS notification center, deduplicated by employee. The activity dashboard also shows latest proposal status/comment. These notifications are not backfilled for decisions made before this behavior was deployed.
- Current project module tracks activities, tasks, due dates, reports and approval documents. It does not implement budget ledger, receipt validation, or settlement. Windows Task Scheduler reminders remain an operations setup step; verify task registration and logs before telling users reminders are automatic.

## SQLite-to-SQL-Server release workflow

Do not skip a stage:

1. Repair source tracking so a clean clone and immutable release artifact can be produced.
2. Upgrade Django and dependencies to supported, compatible versions and pass the full regression suite.
3. Provision an empty SQL Server SIT database and service credential with least privilege. Pin and document the exact backend and ODBC version/TLS settings.
4. Apply Django migrations to the empty database; inspect schema, indexes, constraints, identity columns, date/time, Decimal, and Unicode behavior.
5. Build a repeatable ETL/import plan for existing SQLite data. Map IDs and foreign keys; preserve audit/history. Do not point the SQL Server app at the SQLite file or assume migrations copy data.
6. Rehearse import from a protected database copy. Compare table counts, key relationships, leave totals, payroll totals, and representative PDFs/reports. Record exceptions and approvals.
7. Run all tests and role-based UAT on SQL Server, including payroll close/PDF access, simultaneous approvals/asset allocations, uploads, and restore. SQLite success alone is insufficient.
8. Rehearse full backup, restore, cutover downtime, post-cutover verification, and rollback. Get HR, Finance, IT, and system owner sign-off.
9. Migrate production only in the approved window. Preserve the original SQLite backup read-only until reconciliation and business acceptance are complete.

## Backup and incident response

- Back up database and uploaded files together to an independent protected target; monitor job success and retention.
- Perform periodic restore drills in a separate environment. Record measured recovery point and time; compare with company-approved RPO/RTO.
- For payroll exposure or wrong-recipient payslip: notify Finance and IT immediately, restrict further access, preserve logs, and follow the incident process. Do not delete evidence or silently edit a locked payroll period.
- For a suspected account compromise: disable the account, rotate credentials/sessions as appropriate, preserve audit logs, and review recent access.

## Release gate

Mark a release ready only when the source can be cloned reproducibly; supported dependencies are pinned; `check --deploy` findings are resolved or formally accepted; tests pass on the production database backend; role-based UAT is signed; payroll figures are approved by Finance; backups and restore are proven; monitoring/support owners and rollback are assigned. For a 30–50 person company, a single well-managed Django application server and a separately backed-up SQL Server are generally sufficient; choose hardware from measured load and storage needs.
