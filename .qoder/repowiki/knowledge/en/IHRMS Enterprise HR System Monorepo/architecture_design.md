The repository is organized as a flat monorepo where each child directory owns one concern and the root only holds shared configuration and cross-cutting contracts:
- `django_backend/` is the runtime application (Django 5.2 + SQL Server via `mssql-django`, MSAL for Microsoft 365).
- Root `package.json` drives Tailwind CSS compilation into `django_backend/src/static/css/tailwind.css`, making the frontend build a sibling of the Django app rather than a separate service.
- `ops_tooling/` scripts (`run_browser_uat.py`, `run_layout_alignment_audit.py`, `run_print_layout_uat.py`, `check_migration_state.py`) exercise the same Django app under test against isolated QA DB/media fixtures.
- `agent_skills/` and `AGENTS.md` define the end-to-end engineering workflow that all contributors (human or agent) follow on the single `main` branch; `docs/PROJECT_WORK_LOG.md` is the single source of truth for change logs across every child.
- `github_actions/` runs the same regression suites invoked by the ops scripts in CI.
- `build_artifacts/` holds stale Graphify AST/semantic caches plus generated dashboard HTML — not part of the build pipeline.
- `documentation/` contains the spec, templates, screenshots, and review guidelines referenced by both the agent skills and the AGENTS.md workflow.
The root `requirements.txt` pins the Python stack used by both `django_backend/` and `ops_tooling/`; `skills-lock.json` pins agent skill versions consumed by `agent_skills/`.