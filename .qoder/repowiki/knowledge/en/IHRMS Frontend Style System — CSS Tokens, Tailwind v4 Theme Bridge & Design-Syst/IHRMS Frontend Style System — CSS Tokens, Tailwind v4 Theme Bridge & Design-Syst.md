---
kind: frontend_style
name: IHRMS Frontend Style System — CSS Tokens, Tailwind v4 Theme Bridge & Design-System Governance
category: frontend_style
scope:
    - '**'
source_files:
    - src/frontend/tailwind.input.css
    - package.json
    - src/static/css/ui_tokens.css
    - src/static/css/design_tokens.css
    - src/static/css/theme.css
    - design-system/MASTER.md
    - docs/UI_DESIGN_SYSTEM.md
    - docs/UI_DESIGN_SYSTEM_PHASE1.md
    - docs/UI_BUTTON_KINDS.json
    - docs/UI_FORM_REGISTRY.json
    - ops/check_ui_contrast.py
---

## What system/approach is used

IHRMS uses a **CSS custom-property token layer** (`--ui-*`) as the single source of truth for colors, typography, spacing, radii, motion, chart series, sidebar tokens, and layout dimensions. The runtime theme (light/dark) is driven by `html[data-theme]` plus `prefers-color-scheme`, with a JS-driven toggle.

Tailwind v4 (`@tailwindcss/cli` 4.3.0) is present but used only as a **theme bridge**: `src/frontend/tailwind.input.css` imports Tailwind with `source(none)` and maps Tailwind's built-in semantic names (`gray-*`, `slate-*`, `blue-*`, `indigo-*`, `font-sans`, `shadow-sm`) onto the `--ui-*` tokens via `@theme`. This lets existing templates keep using Tailwind utility classes while all visual values flow through the design-token layer.

The build pipeline is minimal: `npm run build:css` runs `tailwindcss --input src/frontend/tailwind.input.css --output src/static/css/tailwind.css --minify`; there is no PostCSS, Sass, or CSS-in-JS stack.

## Key files and packages

- `package.json` — declares `tailwindcss` 4.3.0 and `@tailwindcss/cli` 4.3.0; scripts `build:css` / `watch:css` point at `src/frontend/tailwind.input.css` → `src/static/css/tailwind.css`.
- `src/frontend/tailwind.input.css` — Tailwind entry; `@import "tailwindcss" source(none); @source "../";` + `@theme` mapping from Tailwind primitives to `--ui-*`.
- `src/static/css/ui_tokens.css` — canonical token definitions under `@layer tokens`; light theme on `:root, html[data-theme="light"]`, dark theme on `html[data-theme="dark"]`, plus `prefers-reduced-motion` and `prefers-color-scheme: dark` overrides.
- `src/static/css/design_tokens.css` — legacy `--ihrms-*` aliases that re-export `--ui-*` so older CSS keeps working; also contains a frozen HCNS purple palette scoped to `.hcns-paper` and `@media print`.
- `src/static/css/theme.css` — screen/print adapters that map Bootstrap/Select2/Django Admin selectors (`.btn-primary`, `.table`, `.card`, `.navbar-primary`, etc.) to `--ui-*` tokens inside `@layer base`.
- `src/static/css/` — ~25 per-page/per-module CSS files (`administration_ui.css`, `hr_ui.css`, `personal_ui.css`, `planning_ui.css`, `report_dashboard.css`, `home_dashboard.css`, `shared_components.css`, `atoms_ui.css`, `print_forms.css`, …) that compose tokens into page styles.
- `design-system/MASTER.md` — project-authority document governing the design system; defines scope, token precedence, component contracts, breakpoints, accessibility gates, and phase-gated rollout rules.
- `docs/UI_DESIGN_SYSTEM.md`, `docs/UI_DESIGN_SYSTEM_PHASE1.md`, `docs/UI_BUTTON_KINDS.json`, `docs/UI_FORM_REGISTRY.json` — supplementary spec artifacts referenced by MASTER.md.
- `ops/check_ui_contrast.py` — automated contrast checker invoked by the design-system gate.

## Architecture and conventions

### Token hierarchy

`ui_tokens.css` declares the full `--ui-*` vocabulary:

- Typography: `--ui-font-family`, `--ui-font-size-*`, `--ui-line-height-*`, `--ui-font-weight-*`, `--ui-text-h1/h2/label/kpi/stat/work`, tabular numerics.
- Spacing: `--ui-space-1..32` (4–128px).
- Radius: exactly three roles — `--ui-radius-control` (8px), `--ui-radius-card` (8px), `--ui-radius-pill`.
- Layout: `--ui-sidebar-width` (16rem), `--ui-content-max-width` (90rem), `--ui-dialog-width`, `--ui-table-col-*`, `--ui-layer-*` z-index scale.
- Motion: `--ui-motion-feedback` (120ms), `--ui-motion-panel` (180ms), reduced-motion sets both to 0.
- Color families: brand (teal), success/warning/danger/info, sidebar, chart series, disabled, hover/selected/focus.

Theme variants live on `:root` (defaults), `html[data-theme="light"]`, `html[data-theme="dark"]`, and `@media (prefers-color-scheme: dark)` for OS preference when no explicit theme is set.

### Tailwind bridge

`tailwind.input.css` maps Tailwind's semantic color scales onto `--ui-*`:

- `gray-*` / `slate-*` → `--ui-bg`, `--ui-surface-raised`, `--ui-divider`, `--ui-border`, `--ui-text-muted`, `--ui-text`.
- `blue-*` / `indigo-*` → `--ui-brand`, `--ui-brand-hover`, `--ui-brand-active`.
- `font-sans` → `--ui-font-family`.
- `shadow-sm` → `--ui-shadow-card`.

This means components can still write `bg-gray-50 text-gray-700` or `text-blue-500` and receive the IHRMS brand/token values rather than Tailwind defaults.

### Legacy adapter layer

`design_tokens.css` provides one-way aliases `--ihrms-*` → `--ui-*` so pre-refactor CSS continues to work. It also ships a frozen HCNS purple palette under `.hcns-paper` and `@media print` so paper forms are isolated from the interactive theme.

### Cascade layers

`ui_tokens.css` opens the cascade with `@layer legacy, reset, tokens, base, components, layouts, pages;`. This enforces a strict ordering: legacy overrides first, then reset, then tokens, then base, then components, then layouts, then pages. New CSS must be placed in the correct layer.

### Print isolation

Print output is deliberately decoupled from screen themes. `design_tokens.css` contains a frozen HCNS palette for `@media print`, and `theme.css` forces `color-scheme: light !important` on `html` in print and hides `.ihrms-theme-toggle`.

### Responsive strategy

Breakpoints are defined in CSS media queries at 360/768/1024/1440px (per MASTER.md). There is no Tailwind config file — Tailwind v4 is used without a config, relying on the `@theme` block and CSS `@media` rules. Sidebar switches from fixed (≥1024px) to drawer (<1024px); content max-width is `--ui-content-max-width` (90rem ≈ 1440px).

### Theming contract

- Base loads theme JS before CSS.
- JS toggles `html[data-theme]`; if unset, `prefers-color-scheme` applies.
- All UI code consumes `--ui-*` directly; `--ihrms-*` is deprecated alias-only.
- Brand is teal: light `#0b7461`, dark `#63dbc2`; sidebar background differs between themes.
- No gradients, glow, Neumorphism, or external font CDNs.

### Component contracts

MASTER.md prescribes button kinds (primary/secondary/tertiary/danger), form grid modes (`.ui-form-grid--inline|grouped|--long`), badge/alert sizing, table row minimum height (44px), control radius (8px), focus ring (3px), and filter-bar layout (`[Tìm kiếm] [Lọc phụ…] [Áp dụng] [Xóa lọc]`). These are documented contracts, not lint-enforced rules.

## Conventions and constraints

- **Token ownership**: `src/static/css/ui_tokens.css` is the authoritative source for `--ui-*` values; `design-system/MASTER.md` states it explicitly.
- **No Tailwind config**: Tailwind v4 is configured exclusively through `@theme` in `tailwind.input.css`; there is no `tailwind.config.js`.
- **Legacy compatibility**: `design_tokens.css` provides one-way `--ihrms-*` → `--ui-*` aliases; new code should use `--ui-*` directly.
- **HCNS print isolation**: The HCNS purple palette is frozen under `.hcns-paper` and `@media print` and must not be recolorized (per MASTER.md).
- **Cascade order**: Files must respect `@layer legacy, reset, tokens, base, components, layouts, pages;` declared in `ui_tokens.css`.
- **Typography rule**: Font sizes use px/rem only, never em; minimum 14px for all UI text (documented in `ui_tokens.css`).
- **Radius roles**: Exactly three radius tokens exist — control, card, pill — and no additional radii are introduced.
- **Motion tokens**: `--ui-motion-feedback` and `--ui-motion-panel` default to 120ms/180ms and are forced to 0ms under `prefers-reduced-motion: reduce`.
- **Responsive breakpoints**: 360/768/1024/1440px are the prescribed breakpoints; CSS variables must not be used as breakpoint conditions (per MASTER.md).
- **Contrast gating**: MASTER.md requires measured contrast ratios (text ≥4.5:1, controls/focus ≥3:1) for both themes, enforced via `ops/check_ui_contrast.py`.
- **Build command**: `npm run build:css` is the only CSS build script; it compiles `src/frontend/tailwind.input.css` to `src/static/css/tailwind.css` with minification.
- **Design-system authority**: `design-system/MASTER.md` is designated the highest-precedence source of truth for design decisions, above `DESIGN.md` and skill defaults.