This is a documentation-only leaf with no executable code. It is organized into four layers:
- Top-level numbered Markdown files (00–16) form the canonical design baseline: project charter, BRD, solution architecture, database/security/backend/frontend/testing/deployment standards, UI/UX spec, RBAC matrix, workflow definition, data dictionaries, code-generation guide, API contract, and Django module blueprint; `99_Architecture_Baseline.md` is declared the highest-priority document that resolves conflicts.
- Unnumbered Markdown/DOCX/XLSX files at the root capture working artifacts such as code review reports, UAT scripts, migration plans, user guides (`HUONG_DAN_SU_DUNG_IHRMS.*`, `Huong_Dan_Bieu_Mau_HCNS.md`), and UI component JSON schemas (`UI_BUTTON_KINDS.json`, `UI_FORM_REGISTRY.json`).
- `templates/hcns/` holds Vietnamese HR template documents grouped by business area (personnel, contracts, attendance, payroll, recruitment, admin/assets).
- `screenshots/stage1_samples/` stores responsive dark/light screenshot pairs for login, dashboard, asset form, HR employee list/form, and headcount report across three breakpoints (390px, 1440x900, 1756px).
- `superpowers/plans` and `superpowers/specs` contain forward-looking assistant/chatbot planning and design docs.
- `archive/prompts` and `archive/reviews` keep historical prompt templates and recovered reviews out of the active set.
Dependency direction is one-way: these documents describe the codebase in `QLHCNS/`; nothing in this module imports or references source code.
