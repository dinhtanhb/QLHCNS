---
kind: build_system
name: IHRMS Monorepo Build & CI Pipeline (Django + Tailwind + GitHub Actions)
category: build_system
scope:
    - '**'
source_files:
    - .github/workflows/ci.yml
    - .github/workflows/sqlserver-regression.yml
    - requirements.txt
    - package.json
    - ops/run_tests.py
    - ops/backup/Test-BackupSafety.ps1
---

## Build System Overview

The IHRMS monorepo uses a minimal, script-driven build system centered on three layers:

1. **Python/Django backend** — pinned in `requirements.txt`, installed via `pip install -r requirements.txt`, run through Django's `src/manage.py`.
2. **Frontend CSS** — built with Tailwind CLI v4 (`@tailwindcss/cli` 4.3.0) via npm scripts defined in the root `package.json`.
3. **CI/CD** — two GitHub Actions workflows under `.github/workflows/` covering push/PR regression and a scheduled SQL Server integration test.

There is no Makefile, Dockerfile, or container image definition in the repository; deployment artifacts are produced by running the application directly against SQLite (CI) or SQL Server (scheduled regression).

## Key Files

- `requirements.txt` — single source of truth for Python dependencies (Django 5.2.17, mssql-django, reportlab, openpyxl, python-docx, python-pptx, django-jazzmin, django-axes, cryptography, etc.).
- `package.json` — defines only the Tailwind CSS build: `npm run build:css` compiles `src/frontend/tailwind.input.css` to `src/static/css/tailwind.css` (minified); `watch:css` runs in watch mode.
- `.github/workflows/ci.yml` — main regression pipeline (runs on push/PR to `main` and `workflow_dispatch`).
- `.github/workflows/sqlserver-regression.yml` — weekly cron job (`cron: "30 17 * * 0"`, i.e. Monday 00:30 Asia/Ho_Chi_Minh) that spins up a SQL Server 2022 service container and runs the same test suite against it.
- `ops/run_tests.py` — the single entry point invoked by both workflows to execute the full regression suite (`--backend sqlite` vs `--backend sqlserver`).
- `ops/backup/Test-BackupSafety.ps1` — PowerShell tests for backup/restore scripts, exercised in CI.

## Architecture & Conventions

### Dependency pinning
All runtime dependencies are pinned to exact versions in `requirements.txt` (e.g. `Django==5.2.17`, `mssql-django==1.8.0`, `reportlab==4.2.5`). The CI installs them with `python -m pip install -r requirements.txt` and then runs `python -m pip check` to enforce consistency before any test execution.

### Two-tier database testing
- **SQLite path** (`ci.yml`): sets `DB_ENGINE=django.db.backends.sqlite3` and runs the full regression suite quickly on every PR/push.
- **SQL Server path** (`sqlserver-regression.yml`): provisions an official `mcr.microsoft.com/mssql/server:2022-latest` container, installs ODBC Driver 18 (`msodbcsql18` + `unixodbc-dev`), and runs the same suite with `DB_ENGINE=mssql`, `DB_USER=sa`, `DB_PASSWORD=IHRMS_ci_only_2026!Strong`, `DB_HOST=127.0.0.1`, `DB_PORT=1433`, `DB_DRIVER=ODBC Driver 18 for SQL Server`, `DB_EXTRA_PARAMS=Encrypt=yes;TrustServerCertificate=yes`.

Both paths use disposable databases/media created at runtime; no persistent state is carried between jobs.

### Settings isolation
The CI overrides settings via environment variables rather than separate settings modules:
- `DJANGO_SETTINGS_MODULE=config.settings`
- `DEBUG=False`
- `M365_STORAGE_ENABLED=False`
- `ENABLE_HTTPS_ENFORCEMENT=False`
- A random `SECRET_KEY` is generated per-job via `python -c 'import secrets; print(secrets.token_urlsafe(64))'`.

### Frontend build
Only CSS is built in CI (`npm run build:css`). There is no bundler, transpiler, or test harness for JavaScript in the repo; the frontend is Tailwind-generated CSS served as static files by Django.

### Security scanning
- Python: `pip-audit==2.9.0` runs against `requirements.txt` (`python -m pip_audit -r requirements.txt`).
- Node: `npm audit --audit-level=low` runs after `npm ci`.

### Test orchestration
All Django/UAT/browser tests are launched from `ops/run_tests.py`, which accepts a `--backend` flag selecting the target database. This centralizes the test invocation so CI workflows stay thin.

### Backup script validation
The `ops/backup/` PowerShell scripts (`Backup-FullDatabase.ps1`, `Backup-TransactionLog.ps1`) are unit-tested by `Test-BackupSafety.ps1`, which exercises combinations of `-Kind Full|Log` × `-Scenario Express|Standard|Failure` using mocked `sqlcmd` only.

## Conventions & Constraints

- **Pinned dependencies**: Every Python package in `requirements.txt` uses `==` version pins; this is enforced by CI via `pip check` and `pip-audit`.
- **Single test entry point**: CI never calls Django management commands directly for tests — it always goes through `python ops/run_tests.py --backend <sqlite|sqlserver>`.
- **Settings via env vars**: No `.env` file is committed; CI injects `SECRET_KEY`, `DB_*`, `APP_ENV=test`, `DEBUG=False`, `M365_STORAGE_ENABLED=False`, `ENABLE_HTTPS_ENFORCEMENT=False`.
- **Branch gating**: The main workflow triggers only on `push`/`pull_request` against `main`; there is no branch protection rule visible in the repo itself (enforced by GitHub UI, not code).
- **Concurrency control**: `concurrency.group: ci-${{ github.ref }}` with `cancel-in-progress: true` ensures duplicate runs on the same ref do not queue.
- **Node version**: CI pins Node.js 22 via `actions/setup-node@v6` with `cache: npm`.
- **Python version**: CI pins CPython 3.12 via `actions/setup-python@v6` with `cache: pip`.
- **No container images**: There is no `Dockerfile` or `docker-compose.yml` in the repository; deployment is expected to be done outside this repo (referenced by docs such as `docs/08_Deployment_Standards.md`).
- **Tailwind output location**: The build script writes compiled CSS to `src/static/css/tailwind.css`, which Django serves as a static asset.