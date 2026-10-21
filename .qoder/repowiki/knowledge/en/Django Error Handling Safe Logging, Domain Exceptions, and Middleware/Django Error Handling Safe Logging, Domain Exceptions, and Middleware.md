---
kind: error_handling
name: 'Django Error Handling: Safe Logging, Domain Exceptions, and Middleware'
category: error_handling
scope:
    - '**'
source_files:
    - src/config/settings.py
    - src/apps/security/logging.py
    - src/apps/m365/graph_client.py
    - src/apps/common/middleware.py
    - src/apps/activity/views.py
    - src/apps/assistant/views.py
    - src/apps/document/hcns/prefill.py
    - src/apps/activity/models.py
    - src/apps/activity/services.py
---

## Approach

The IHRMS backend uses standard Django error-handling conventions with a small set of custom additions:

- **HTTP-layer errors**: `django.http.Http404` for missing resources and `django.core.exceptions.PermissionDenied` for authorization failures are raised directly from views and business logic.
- **Domain-level exceptions**: Custom `Exception` subclasses encapsulate application-specific failure modes (e.g. Microsoft Graph integration errors).
- **Validation errors**: Django model validation raises `ValidationError` (field-dict payloads) inside model `clean()` methods; service functions raise plain `ValueError` for invalid arguments.
- **Logging**: Python `logging` module with a project-wide `apps` logger namespace, rotating file handlers (`app.log`, `error.log`), and a security filter that strips exception payloads in production.
- **Middleware**: A single domain middleware (`ApplyDueEmployeeChangesMiddleware`) wraps background work in a try/except around `DatabaseError` so transient DB failures do not break unrelated portal pages.
- **No global exception handler** is registered in `settings.py`; unhandled exceptions fall through to Django's default exception view.

## Key Files

- `src/config/settings.py` — logging configuration, including the `safe_exception` filter and per-handler rotation.
- `src/apps/security/logging.py` — `SafeExceptionFilter` implementation.
- `src/apps/m365/graph_client.py` — `GraphAPIError` and its subclass `GraphNotConfigured`.
- `src/apps/common/middleware.py` — `ApplyDueEmployeeChangesMiddleware`.
- `src/apps/activity/views.py` — canonical use of `PermissionDenied` across many views.
- `src/apps/assistant/views.py` — canonical use of `Http404` for missing assistant resources.
- `src/apps/document/hcns/prefill.py` — mixed `PermissionDenied` / `Http404` usage in form prefill logic.

## Architecture and Conventions

### Custom Exception Hierarchy

Only one domain exception hierarchy exists, under `apps.m365.graph_client`:

```python
class GraphAPIError(Exception):
    def __init__(self, message, *, status_code=None, retry_after=None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after

class GraphNotConfigured(GraphAPIError): ...
```

Callers catch `GraphAPIError` by type (e.g. `assistant/m365_search.py` catches it around Graph calls) and may re-raise with an HTTP status code (e.g. `status_code=502`, `status_code=503`). The `GraphClient._request` method translates `requests.RequestException` and any HTTP response with `status_code >= 400` into `GraphAPIError`, centralizing external API error normalization.

### Security Filter on Logs

`SafeExceptionFilter` (in `apps/security/logging.py`) is applied to every log handler via the `safe_exception` filter name in `settings.LOGGING`. In non-debug mode (`not settings.DEBUG`) it rewrites the log record:

- Replaces the original message with `"Unhandled error: type=%s (exception payload omitted)"`.
- Strips `record.exc_info` and `record.exc_text`.

This prevents SQL connection strings, Graph tokens, or other secrets embedded in exception tracebacks from being persisted to `error.log` or `app.log`. Tests in `apps/security/tests_data_protection.py` assert this behavior.

### Logging Layout

All application code uses the standard pattern:

```python
import logging
logger = logging.getLogger(__name__)
```

The `apps` logger namespace is configured to write to console, `app.log`, and `error.log` at INFO level. The root logger is also INFO. There is no structured JSON formatter — logs are human-readable with the verbose format `[asctime] levelname name - message`.

### Middleware Error Isolation

`ApplyDueEmployeeChangesMiddleware` runs scheduled HR changes once per process per local day. Its inner call to `apply_due_employee_changes(today)` is wrapped in `try/except DatabaseError: pass`, explicitly documented as "A transient DB problem should not take down unrelated portal pages." This is the only place in the codebase where a broad exception class is swallowed without logging.

### HTTP Error Signals

- `PermissionDenied` is raised throughout `apps/activity/views.py` and `apps/document/hcns/prefill.py` to enforce RBAC at the view layer.
- `Http404` is raised in `apps/assistant/views.py` and `apps/document/hcns/prefill.py` when requested objects are absent.
- No custom `handler404` / `handler500` templates or middleware are registered in `config/urls.py` or `settings.py`; Django's defaults apply.

### Validation Errors

Model validation uses Django's built-in `ValidationError` with field-name-to-message dicts (e.g. `activity/models.py` raises it from `clean()`). Service-layer argument validation raises plain `ValueError` (e.g. `activity/services.py` raises `ValueError("number_of_days must be non-negative")`). These are not translated into HTTP responses by a central handler — callers in `activity/views.py` catch `ValueError` explicitly to render user-facing messages.

## Conventions and Constraints

1. **External API errors are normalized to `GraphAPIError`**. All network and HTTP failures inside `graph_client.py` are converted to `GraphAPIError(status_code=...)`, so callers can inspect `status_code` and `retry_after` rather than parsing raw `requests` exceptions.

2. **Exception payloads are never logged in production**. The `SafeExceptionFilter` attached to all handlers enforces this; tests in `tests_data_protection.py` verify that `exc_info` is cleared and the message is rewritten.

3. **Authorization failures use `PermissionDenied`**, not ad-hoc HTTP responses. Views in `apps/activity` consistently raise it instead of returning `HttpResponseForbidden`.

4. **Missing-resource cases use `Http404`**, not generic exceptions. Assistant and document prefill views raise it with Vietnamese messages describing why the resource was not found.

5. **Background/scheduled work is isolated from request processing**. The middleware swallows `DatabaseError` silently so that a failed daily job does not degrade normal page rendering.

6. **Business-rule violations in services raise `ValueError`** with descriptive Vietnamese messages; model-level constraints raise `ValidationError` with field-keyed dicts. There is no shared base exception class for these — they remain language-native types.

7. **No repository-wide sentinel error module** exists. Custom exceptions are colocated with the subsystem that owns them (only `m365` has a dedicated hierarchy).

8. **No `panic`/`recover` equivalent** is used — Python has no such construct, and no `try/finally` blocks are used as a recovery mechanism beyond the middleware's transient-error suppression.