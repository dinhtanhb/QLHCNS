---
kind: logging_system
name: Django Logging with Rotating File Handlers and SafeExceptionFilter
category: logging_system
scope:
    - '**'
source_files:
    - src/config/settings.py
    - src/apps/security/logging.py
    - src/apps/portal/dashboard_data.py
    - src/apps/portal/views/common.py
    - src/apps/portal/views/finance.py
---

## What system/approach is used

The IHRMS backend uses Python's standard-library `logging` module configured via Django's `LOGGING` dict in `src/config/settings.py`. There is no third-party logger framework (no structlog, loguru, sentry-sdk integration for application logs). Log output goes to three sinks: console (`StreamHandler`), an application file (`RotatingFileHandler` → `Logs/app.log`), and an error-only file (`RotatingFileHandler` → `Logs/error.log`).

## Key files and packages

- `src/config/settings.py` — central `LOGGING` configuration block (lines 478–546).
- `src/apps/security/logging.py` — defines `SafeExceptionFilter`, the only custom filter.
- `src/apps/portal/dashboard_data.py`, `src/apps/portal/views/common.py`, `src/apps/portal/views/finance.py` — example call sites using `logger = logging.getLogger(__name__)`.
- `Backups/ApplicationLogs/` — sample rotated log files (`app.log`, `error.log`, `lifecycle-reminders-*.log`) produced by this configuration.

## Architecture and conventions

1. **Logger instantiation**: Modules create a module-scoped logger via `import logging; logger = logging.getLogger(__name__)` (observed in `apps/portal/*`). The settings comment under the `apps` logger namespace documents this pattern explicitly.
2. **Log levels**: Root logger and `django` logger default to `INFO`; `django.request` defaults to `ERROR`. Business code uses `logger.warning`, `logger.error`, `logger.exception` as seen in portal views.
3. **Structured fields**: No structured JSON payload is emitted. Messages are plain strings with positional `%s` placeholders (e.g. `Business request failed: view=%s actor_id=%s error_type=%s`, `Lỗi tính lương nhân viên %s (kỳ %s)`). Contextual fields are embedded as key=value fragments inside the message string rather than as separate structured attributes.
4. **File rotation**: Both `app_file` and `error_file` handlers use `RotatingFileHandler` with `maxBytes=5*1024*1024` (5 MB) and `backupCount=30`, keeping roughly 30 days of logs per the deployment standards comment referencing `docs/08_Deployment_Standards.md` section 27.
5. **Encoding**: All file handlers force `encoding="utf-8"`.
6. **Exception safety**: `SafeExceptionFilter` (in `apps.security.logging`) intercepts every record. When `settings.DEBUG` is false and a record carries `exc_info`, it rewrites `record.msg` to `"Unhandled error: type=%s (exception payload omitted)"`, clears `record.exc_info` and `record.exc_text`, so stack traces and exception payloads never reach disk in production. This is documented in the module docstring: "Avoid persisting exception payloads that may contain SQL/Graph secrets."
7. **Logger namespaces**:
   - `root` → `console`, `app_file` at `INFO`.
   - `django` → `console`, `app_file`, `error_file` at `INFO`, `propagate=False`.
   - `django.request` → `console`, `error_file` at `ERROR`, `propagate=False`.
   - `apps` → `console`, `app_file`, `error_file` at `INFO`, `propagate=False`.

## Conventions and constraints

- **Convention**: Application modules should obtain a logger through `logging.getLogger(__name__)` under the `apps.*` namespace so messages route to all three sinks (console + app.log + error.log). This is stated in the settings comment and enforced by the `apps` logger config having `propagate=False`.
- **Constraint**: Exception payloads are stripped from persisted logs outside `DEBUG`. `SafeExceptionFilter` unconditionally replaces `exc_info`/`exc_text` when not debugging, so stack traces do not appear in `app.log` or `error.log` in production.
- **Constraint**: Log files live under the repo-root `Logs/` directory, created at startup via `LOG_DIR.mkdir(parents=True, exist_ok=True)`.
- **Constraint**: Rotation policy is fixed at 5 MB per file, 30 backups — no environment-variable override exists in the current settings.
- **Constraint**: Only one formatter named `verbose` is defined, producing `[asctime] LEVEL name - message`; no JSON formatter is configured.
- **Constraint**: No external sinks (syslog, HTTP, Elasticsearch, Sentry) are wired into the `LOGGING` dict — routing is file+console only.