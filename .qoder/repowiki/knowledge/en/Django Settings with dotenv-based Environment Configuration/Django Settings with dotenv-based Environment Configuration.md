---
kind: configuration_system
name: Django Settings with dotenv-based Environment Configuration
category: configuration_system
scope:
    - '**'
source_files:
    - src/config/settings.py
    - src/config/env.py
    - .env.example
---

## Approach

IHRMS uses the standard Django settings pattern (`src/config/settings.py`) layered on top of `python-dotenv` for loading `.env` files. There is no third-party configuration library (e.g. dynaconf, django-environ, pydantic-settings); all runtime configuration is resolved from environment variables via `os.getenv`, with a small in-repo helper for boolean flags.

## Key Files

- `src/config/settings.py` — single source of truth for all Django settings: security, database, M365/SharePoint integration, Jazzmin admin UI, logging, middleware, installed apps, and storage backends.
- `src/config/env.py` — tiny dependency-free helper defining `env_flag(name, default="False")`, which treats only `true`, `1`, `t` as truthy; everything else (empty, unknown, false) evaluates to `False`. The function accepts an optional `environ` mapping so it can be unit-tested without reloading Django settings.
- `.env.example` — template copied into a local `.env` at the repo root (`ROOT_DIR / ".env"`); documents every required/optional variable with Vietnamese comments.
- `src/config/__init__.py`, `asgi.py`, `wsgi.py`, `urls.py` — standard Django entry points that import `settings`; they do not add configuration logic.

## Architecture & Conventions

### Loading order

1. `settings.py` imports `dotenv.load_dotenv(ROOT_DIR / ".env")` at module load time (line 26), where `ROOT_DIR = BASE_DIR.parent` resolves to the repository root.
2. `SECRET_KEY` is read via `os.getenv("SECRET_KEY")` and raises `django.core.exceptions.ImproperlyConfigured` if missing — this is the hard gate that prevents startup without a secret.
3. Boolean flags go through `env_flag` (e.g. `DEBUG`, `ENABLE_HTTPS_ENFORCEMENT`, `M365_STORAGE_ENABLED`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`).
4. String/list settings use `os.getenv(key, default)` directly (e.g. `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DB_ENGINE`, `SESSION_IDLE_TIMEOUT`).

### Environment-aware behavior

- `APP_ENV` defaults to `development` and is lower-cased. When set to `uat` or `production`, `settings.py` enforces three invariants at import time:
  - `DEBUG=False`
  - `ENABLE_HTTPS_ENFORCEMENT=True`
  - `SECRET_KEY` is at least 50 characters, has ≥ 5 distinct characters, and does not start with `django-insecure-`
  - `ALLOWED_HOSTS` is non-empty and does not contain `*`
  Any violation raises `ImproperlyConfigured` with a Vietnamese error message naming the environment.

- HTTPS enforcement is gated by `ENABLE_HTTPS_ENFORCEMENT`: when true, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, and `SECURE_PROXY_SSL_HEADER` are enabled; HSTS values come from `SECURE_HSTS_SECONDS`, `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`.

### Database layering

- `DB_ENGINE` selects between SQLite (default, `django.db.backends.sqlite3`) and SQL Server (`mssql`).
- SQLite mode uses `BASE_DIR / DB_NAME` (default `db.sqlite3`).
- SQL Server mode reads `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_DRIVER`, `DB_TRUSTED_CONNECTION`, and optionally `DB_EXTRA_PARAMS`. In production, if `DB_EXTRA_PARAMS` is unset it defaults to `Encrypt=yes;TrustServerCertificate=no`.

### Feature toggles

Feature switches are exposed as env vars parsed through `env_flag`:
- `DEBUG`
- `ENABLE_HTTPS_ENFORCEMENT`
- `M365_STORAGE_ENABLED` (enables SharePoint/OneDrive storage instead of local `MEDIA_ROOT`)
- `SECURE_HSTS_INCLUDE_SUBDOMAINS`, `SECURE_HSTS_PRELOAD`

### Secrets

Secrets are expected exclusively in environment variables loaded from `.env`:
- `SECRET_KEY` (required, validated at import)
- `DB_USER`, `DB_PASSWORD` (SQL Server)
- `M365_TENANT_ID`, `M365_CLIENT_ID`, `M365_CLIENT_SECRET`
- `AXES_IP_FAILURE_LIMIT`

The `.env.example` file explicitly instructs developers to generate a new key via `get_random_secret_key()` and warns never to commit the real `.env` to Git.

### Logging configuration

Logging is configured entirely inside `settings.py` using Python's built-in `logging` dict config. It writes to `ROOT_DIR / "Logs"` with two rotating handlers (`app.log`, `error.log`, 5 MB each, 30 backups). A custom filter `apps.security.logging.SafeExceptionFilter` is wired in to redact sensitive data.

### External integrations as config

Microsoft 365 / SharePoint integration is fully driven by env vars: `M365_*` keys populate `M365_FOLDER_MAP` and `M365_UPLOAD_PREFIX_MAP`, with legacy `M365_LIBRARY_*` names supported as fallbacks. This lets deployment toggle document storage targets without code changes.

## Conventions & Rules

- **All runtime configuration lives in environment variables** — there are no per-environment Django setting files (no `settings_dev.py`, `settings_prod.py`). Overrides happen by changing `.env` or process environment.
- **Boolean flags must be written as `true`, `1`, or `t`** (lowercase) to be recognized as truthy; any other value is falsy. This is enforced by `env_flag` in `src/config/env.py`.
- **Production/UAT require explicit hardening**: `APP_ENV=uat|production` triggers validation that `DEBUG=False`, `ENABLE_HTTPS_ENFORCEMENT=True`, `SECRET_KEY` is strong, and `ALLOWED_HOSTS` is specific and non-wildcard. Violations raise `ImproperlyConfigured` at import time.
- **HTTPS enforcement is opt-in via `ENABLE_HTTPS_ENFORCEMENT`**: dev runs stay HTTP-compatible; production sets it to `True` behind IIS/reverse proxy with SSL.
- **Database backend selection is via `DB_ENGINE`**: SQLite is the development default; SQL Server is used for SIT/server deployments.
- **`.env` is placed at the repository root**, outside `src/`, and is excluded from version control (documented in `.env.example` header).
- **Jazzmin admin UI configuration** (`JAZZMIN_SETTINGS`, `JAZZMIN_UI_TWEAKS`) is embedded inline in `settings.py` rather than split out — it is considered application presentation, not runtime configuration.
- **No feature-flag service or remote config store** is used; all toggles are local environment variables.