---
name: ihrms-operations
description: Prepare and operate IHRMS environments, troubleshoot user and payroll workflows, plan SQLite-to-SQL-Server cutover, and verify backup, restore, security, and release readiness. Use for IHRMS deployment, go-live, production support, database migration, or operations requests.
---

# IHRMS operations and release

## Operational constraints

- This project handles identifiable HR data and confidential payroll. Use least privilege, separate accounts, TLS, and approved company retention rules.
- SQLite is the current test/development database. A setting change to `DB_ENGINE=mssql` is not a data migration. Preserve the original SQLite database and take a verified backup before any cutover.
- Do not run destructive management commands or schema/data changes against production. Use a disposable database for rehearsal; require an approved release window and rollback plan for production work.
- The application currently has a source-control gitlink problem and the pinned Django 5.0.14 is unsupported. Consult [Production Readiness Review](../../../docs/Production_Readiness_Review_2026-09-23.md) before representing the system as production-ready.
- Follow the rewritten end-user procedures in [IHRMS User Guide](../../../HUONG_DAN_SU_DUNG_IHRMS.md). Never request or expose passwords, secret keys, full identity numbers, or payroll documents in support messages.

## Environment setup and support

1. Keep development, SIT, UAT, and production configuration/database/files separate.
2. Use environment variables or a protected secret store for credentials. Never commit `.env`; rotate any secret suspected to have been exposed.
3. Production must use a maintained Django patch, compatible pinned packages, a supported SQL Server backend/ODBC driver, HTTPS, secure cookies, an explicit host/CSRF allowlist, production WSGI hosting, collected static assets, controlled media storage, and useful logs.
4. Never use `manage.py runserver` as the production server.
5. Create individual accounts; link each account to the correct employee record; assign only necessary roles. Disable access promptly on departure and review role changes.

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
