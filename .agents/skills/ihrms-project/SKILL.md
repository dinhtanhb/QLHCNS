---
name: ihrms-project
description: Develop, debug, and review the IHRMS Django codebase, including HR, attendance, leave, payroll, assets, permissions, and PDF payslips. Use when working in the QLHCNS/IHRMS repository or when the user asks to inspect or change an IHRMS feature.
---

# IHRMS project development

## Project context

- Repository root: `D:/QLHCNS`; Django project currently runs from `src/`.
- `src/` is tracked in the main repository. Confirm the current branch/worktree and retain unrelated user changes before committing.
- The user's local environment has been configured for SQL Server; other clones/test runs may use SQLite. Never assume the active backend: inspect it safely with `manage.py shell -c "from django.db import connection; print(connection.vendor)"`. Do not run schema changes against a live database without explicit authorization.
- The application uses SharePoint through Microsoft Graph for configured file storage. Company email is composed in Outlook through a `mailto:` draft; the user attaches PDFs and sends manually. Do not reintroduce server-side SMTP assumptions without an explicit requirement.
- NGO project activity workflow is a distinct menu/module: activity dashboard/calendar, proposal/budget PDF package, assigned-director approval inbox, in-app notifications, and report Task. Financial commitment tracking, receipts, and settlement remain outside current scope.
- The application serves 30–50 internal employees. Prefer the existing Django modular monolith; do not add infrastructure for scale without evidence.
- Read `docs/00_Project_Charter.md`, `docs/04_Security_Design.md`, `docs/10_RBAC_Permission_Matrix.md`, and relevant module standards before changing sensitive flows.

## Work safely

1. Inspect repository status, applicable docs, model/view/template flow, and existing tests before editing. Keep unrelated user changes intact.
2. Preserve `db.sqlite3`, `.env`, uploaded `media/`, payroll and personnel records. Never print secrets or personal/payroll data into tool output.
3. Treat authorization as server-side. A hidden menu/button is not access control. Preserve employee ownership and department scope, and add tests for direct URL/POST access when modifying permissions.
4. Keep money as `Decimal`; do not change payroll, tax, insurance, leave quota, or rounding formulas without a test with known expected values and Finance approval for legal/business policy.
5. Keep effective-dated HR/payroll records historical. A future effective event must not be applied early.
6. Use `BaseAuditModel` patterns for new business records. Normal delete is soft-delete; use `all_objects` only for recovery/audit cases. Do not use hard deletion to clean test or production data.
7. Prefer portable Django ORM and migrations. Avoid SQLite-specific SQL/functions. Use transactions and database constraints for integrity; test lock/race behavior on SQL Server because SQLite does not implement equivalent row locking.
8. Avoid external calls, notifications, or exports with real employee data during tests.

## Validation

Run commands from `D:/QLHCNS` using the project virtualenv:

```powershell
& 'D:/QLHCNS/venv/Scripts/python.exe' src/manage.py check
& 'D:/QLHCNS/venv/Scripts/python.exe' src/manage.py makemigrations --check --dry-run
& 'D:/QLHCNS/venv/Scripts/python.exe' src/manage.py test
```

Use Django's test runner so writes go to an isolated test database. Never run `migrate`, `flush`, `loaddata`, or bulk updates against production as routine verification. If the change affects SQL Server behavior, also run the relevant suite against a disposable SQL Server SIT database and state clearly if that environment is unavailable.

For security/deployment settings, run `manage.py check --deploy` with production-like settings. Explain any remaining warning; do not silence checks just to make them pass.

## Completion report

State the changed behavior, relevant files, tests/checks run, whether SQL Server was exercised, and any remaining release blocker. Distinguish tested code from business/legal decisions awaiting HR/Finance sign-off.
