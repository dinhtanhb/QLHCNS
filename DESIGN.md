---
name: "QLHCNS Design System"
description: "Framework-agnostic design rules for web and mobile app implementation."

# ─── Colors ───────────────────────────────────────────────
colors:
  # Brand
  primary:       "#8b5cf6"
  primaryStrong: "#4c1d95"
  primarySoft:   "#ddd6fe"
  accent:        "#8b5cf6"

  # Surfaces
  surface:       "#f5f3ff"
  surfaceMuted:  "#ddd6fe"

  # Text & Border
  text:          "#2e1065"
  border:        "#5b21b6"

  # Feedback
  success:       "#16A34A"
  warning:       "#D97706"
  danger:        "#DC2626"

# ─── Typography ───────────────────────────────────────────
typography:
  family:        "system-ui, -apple-system, Segoe UI, sans-serif"
  displayFamily: "system-ui, -apple-system, Segoe UI, sans-serif"
  monoFamily:    "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace"
  source:        "system font stack"
  weights:       "300, 400, 500, 600"
  defaultWeight: 600
  tone:          "sans"

# Spacing
spacing:
  xs:      4px
  sm:      8px
  md:      12px
  lg:      16px
  xl:      24px
  xxl:     32px
  section: 48px

# Radius
radius:
  sm: 4px
  md: 8px
  lg: 12px

# Motion
motion:
  fast:   120ms
  normal: 180ms
  slow:   260ms
---

# Design System Rules

## Purpose
QLHCNS Design System defines portable, framework-agnostic design rules for web and mobile product interfaces. Use it as the source of truth before changing layouts, components, color, typography, motion, or interaction states.

This file is a portable design skill. Any AI or engineer should be able to read it and improve a web or mobile interface without needing React, Vue, Svelte, Tailwind, native mobile, or any other specific technology.

## Operating Modes

### New Project Mode
- Use these rules to create a coherent first implementation when no existing UI exists.
- Build the information architecture, component system, and responsive behavior from the tokens and rules below.

### Existing Project Refactor Mode
- Treat the existing product as the source of truth for content, routes, behavior, data, and information architecture.
- Improve the visual system by patching styles, tokens, spacing, typography, hierarchy, responsive behavior, and component states.
- Do not regenerate whole pages from scratch when a targeted patch can preserve the current experience.
- Do not replace real content with placeholder, demo, lorem ipsum, or simplified content.
- If a section looks inconsistent with this design system, restyle it first. Do not remove it.
- If removing content, routes, features, media, or data logic seems necessary, stop and ask for approval.

## Preservation Rules For Existing Products
- Preserve all existing headings, paragraphs, labels, buttons, links, images, icons, forms, navigation items, sections, routes, and data-fetching logic unless the user explicitly requests removal.
- Preserve semantic meaning and section order unless the user asks for an information-architecture change.
- Preserve working interactions: forms, menus, language toggles, theme toggles, dialogs, tabs, carousels, and scroll behavior.
- Preserve real brand/product names and domain-specific copy. Design changes must not make the page generic.
- Keep every original section represented after the refactor. A redesigned section is acceptable; a missing section is not.
- Never leave the first viewport empty unless the existing product intentionally has an empty state.

## Safe Refactor Workflow
1. Read the existing UI code before editing. Identify sections, routes, state, data dependencies, and user actions.
2. Inventory current colors, typography, spacing, radius, shadows, and component states.
3. Map old visual values to the tokens in this file one-to-one where possible.
4. Patch section by section. Avoid full-file rewrites when the current structure works.
5. After each section, verify the original content is still present, visible, and reachable.
6. After changing colors, check every affected text/background pair for contrast.
7. Verify desktop and mobile before finishing.

## Visual Direction
- Color direction: Violet - Creative premium UI.
- Typography direction: System Sans - Clean product UI.
- Style direction: Neumorphism - Soft extruded surfaces with tactile shadows, inset states, and calm monochrome depth
- References: Soft UI controls, enterprise no-code hero surfaces, soft split authentication panels, dark embossed portfolio heroes, tactile settings panels.
- Visual style: Violet color direction, System Sans typography, Neumorphism style.

## Style System: Neumorphism
Use Neumorphism to create interfaces that feel carved from one material: raised buttons, inset form fields, embossed icon discs, soft navigation capsules, and abstract relief shapes share the same base surface. The style works best for enterprise landing pages, auth flows, dashboards, settings, wellness apps, tactile portfolios, and focused product tools. It can be light and industrial, clean and friendly, or dark and embossed, but it must never trade readability, contrast, or state clarity for soft shadows.

### Layout Rules
- start from one dominant material color: pale gray, cool off-white, muted blue-gray, charcoal, or dark graphite; depth comes from shadows on that base.
- use simple compositions with large calm surfaces, generous margins, and few strong color accents; crowded layouts make neumorphic depth muddy.
- use raised surfaces for navigation capsules, CTA buttons, icon discs, cards, split panels, abstract relief shapes, and selected controls.
- use inset surfaces for input wells, active nav items, search fields, toggle tracks, pressed controls, progress channels, and recessed decoration.
- enterprise landing pages can combine a soft raised nav, large typographic hero, orange or blue CTA, and embossed diagram or icon orbit on the side.
- auth flows can use a split soft panel: one raised side for welcome/sign-in and one flatter side with inset fields and a strong primary button.
- dark neumorphism should feel embossed and architectural: charcoal background, subtle raised geometry, deep shadows, and one warm or saturated accent.
- keep dense reading sections, tables, long forms, and documentation flatter or lightly bordered; do not force every container into raised material.
- collapse to cleaner solid or bordered surfaces on very small screens when shadows reduce clarity or waste space.

### Component Patterns
- buttons need visible labels, hover, active, pressed, focus-visible, disabled, loading, success, and error states beyond shadow alone.
- primary CTAs should use color fill or a strong accent glow in addition to raised depth; orange, blue, or warm gold accents work well against neutral material.
- secondary buttons can be pill-shaped raised or inset capsules, but the label must remain darker and sharper than the surface.
- cards should feel like raised plates with clear internal spacing, readable headings, and one purpose such as status, metric, setting group, media control, or summary.
- icon discs and orbital feature markers should use soft raised circles with crisp black or high-contrast icons; avoid fuzzy low-contrast symbols.
- form fields should be inset wells with visible placeholder or label text, clear focus ring, and error state that cuts through the soft material.
- toggles, segmented controls, sliders, steppers, and switches are strong fits because raised and pressed states map naturally to touch interaction.
- use paired light and dark shadows tuned to the actual surface color; pale UIs need delicate gray shadows, dark UIs need restrained black shadows plus subtle highlights.
- abstract relief shapes can decorate hero sections, but they must stay behind content and share the same material logic as the UI.
- dialogs and menus should be more explicit than decorative surfaces, with clear borders, elevation, and dismissal controls.

### Existing Project Refactor Rules
- inventory the existing interface first: controls, cards, forms, navigation, repeated items, metrics, dialogs, and user actions.
- preserve every existing section and add soft depth only to meaningful containers, controls, or selected states.
- do not replace real content with decorative raised blocks or empty soft panels.
- patch shadows, radius, backgrounds, borders, and states section by section instead of rebuilding whole pages.
- when restyling a landing page, keep the hero content, CTA path, and product/diagram visual intact; apply neumorphic depth to nav, CTAs, icon clusters, and supporting shapes.
- when restyling auth or form flows, prioritize field clarity and form completion over soft shadow aesthetics.
- when a current layout is already dense, improve grouping and spacing before adding neumorphic depth.
- if old colors make shadows invisible or text low-contrast, prioritize semantic foreground and accessible contrast over the effect.
- when applying to a dark UI, reduce shadow spread and use subtle borders or inner highlights so depth does not become smudgy.
- when applying to a light UI, avoid low-contrast gray-on-gray text and make primary actions stronger than the soft material.
- if decorative relief shapes compete with content, lower their contrast, move them behind the text, or remove them.

### Spacing Rules
- use 10px to 14px padding for compact controls, 16px to 24px for form fields and cards, and 32px to 56px for large hero panels.
- keep enough outer spacing for shadows to render without clipping, especially inside scroll containers, sidebars, split panels, and hero cards.
- use consistent gutters and alignment over many nested panels; neumorphism looks best when the grid is quiet and precise.
- use compact but comfortable spacing for toolbars, settings rows, and forms so the soft style does not make the UI feel oversized.
- keep radius consistent: small controls 8px to 12px, cards 16px to 24px, large hero/nav capsules 28px or fully pill-shaped.
- avoid nested raised cards; use inset separators, row grouping, flat inner areas, or a split-panel layout instead.
- give repeated controls stable dimensions so pressed, selected, loading, or hover states do not shift layout.

### Visual Hierarchy Rules
- make primary actions obvious with color, weight, placement, and label clarity instead of shadow intensity alone.
- use raised, flat, inset, and embossed depth levels to separate primary, secondary, selected, passive, and decorative surfaces.
- large hero typography should be crisp and high contrast; soft material can surround it but must not soften the message.
- keep focus-visible rings stronger and sharper than decorative shadows.
- avoid low-contrast text on softly tinted backgrounds; neumorphism often fails when contrast is treated as optional.
- let typography, alignment, and content order carry hierarchy before soft elevation.
- use accent color sparingly for primary CTAs, active controls, progress, selected states, and important icons.
- in dark neumorphism, use one warm or bright accent as the focal point while most relief shapes stay nearly monochrome.
- do not let shadow softness blur the difference between enabled, disabled, selected, and pressed states.

### Style Anti-patterns
- use low-contrast raised surfaces that hide boundaries, labels, or state.
- apply inset shadows to every input, card, and button indiscriminately.
- clip shadows with tight containers or overflow settings.
- depend on shadow alone to communicate clickability, selection, errors, disabled state, or destructive actions.
- use neumorphism for content-heavy articles, dense data tables, or documentation when simple readable surfaces would work better.
- make everything pale gray, low opacity, and softly blurred until the product loses hierarchy.
- nest multiple raised panels until the interface feels swollen or slow.
- use decorative embossed shapes as a substitute for product content, diagrams, CTAs, or form clarity.

### Style Checklist
- text remains readable on every soft surface.
- primary actions are still easy to identify without relying on shadow.
- pressed, selected, disabled, loading, focus-visible, success, and error states remain distinct.
- existing sections, CTAs, forms, navigation, data, and media remain present.
- the chosen mode is clear: light soft enterprise, split auth, tactile dashboard, or dark embossed hero.
- focus-visible and error states are stronger than decorative elevation.
- shadows are not clipped and do not blur dense content hierarchy.
- the result feels tactile and calm, not washed out or randomly embossed.

## Design Tokens
Use semantic tokens first. Raw values from frontmatter are source values, not permission to scatter hex codes or one-off sizes through implementation.

### Color
- Primary action color: #8b5cf6.
- Strong primary: #4c1d95. Use for high-emphasis text, selected state, or strong borders.
- Soft primary: #ddd6fe. Use for subtle surfaces, selected backgrounds, or calm highlights.
- Surface: #f5f3ff.
- Muted surface: #ddd6fe.
- Text: #2e1065.
- Border: #5b21b6.
- Success, warning, and danger are semantic states. Pair them with labels, icons, or position; never rely on color alone.
- When moving from a dark theme to a light or warm theme, update inherited light text classes such as white, muted-white, or low-opacity foregrounds.
- Do not apply one warm/cream/brown palette across the entire page without contrast, hierarchy, and content anchors.

### Text Selection
- Use this style-specific `::selection` treatment for Neumorphism. It should follow the selected color tokens and stay readable.
```css
/* Neumorphism selection: pressed soft surface. */
::selection {
  background-color: #ddd6fe;
  color: #4c1d95;
  text-shadow: 1px 1px 0 #f5f3ff;
}
```
- If the selected color changes, keep the same style behavior but re-check text/background contrast.

### Contrast And Visibility Gate
- Every visible text node must remain readable after color changes.
- Check hero text, navigation, buttons, card titles, form labels, helper text, icons, borders, and disabled states against their actual backgrounds.
- If legacy classes or CSS keep text white on a light surface, replace them with semantic foreground tokens.
- If content appears missing after a restyle, inspect contrast and visibility before deleting or rebuilding the section.
- Do not finish with invisible text, hidden CTAs, empty hero areas, or decorative backgrounds replacing product content.

### Typography
- Primary family: system-ui, -apple-system, Segoe UI, sans-serif.
- Display family: system-ui, -apple-system, Segoe UI, sans-serif.
- Monospace family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace.
- Allowed weights: 300, 400, 500, 600.
- Default UI weight: 600.
- Keep heading levels semantic. Visual size must follow layout importance, not HTML heading number.
- Keep letter spacing at 0 by default. Use uppercase labels sparingly and only for short metadata.

### Spacing And Radius
- Spacing scale: 4/8/12/16/24/32/48.
- Prefer spacing and grouping over extra borders.
- Use 4px radius for compact controls, 8px for standard cards/inputs, and 12px only for larger feature surfaces.
- Do not invent new spacing values unless the layout cannot be solved with the scale.

## Layout Rules
- Start mobile-first. The smallest useful viewport defines the base layout.
- Use content-driven breakpoints. Do not scale type directly with viewport width.
- Keep navigation, primary actions, and form completion paths easy to reach on touch devices.
- Prefer a clear grid, predictable alignment, and stable dimensions for controls, cards, tabs, and repeated items.
- Empty, loading, and error states must preserve layout stability and explain the next action.

## Component Rules
- Every interactive component must define default, hover, active, focus-visible, disabled, loading, success, and error behavior when those states apply.
- Buttons must communicate hierarchy through role: primary, secondary, tertiary, destructive, or icon-only.
- Forms must keep labels visible, helper text close to the field, and errors specific enough to fix.
- Cards must represent repeated items or contained tools. Do not nest cards inside other cards.
- Modals and popovers must include focus management, escape behavior, and clear dismissal affordances.

## Interaction And Motion
- Motion must clarify state change, not decorate the screen.
- Transitions should usually stay between 120ms and 260ms.
- Provide reduced-motion behavior for animations, parallax, shimmer, and auto-moving content.
- Pointer hover cannot be the only way to reveal important controls because touch devices do not have hover.

## Accessibility Requirements
WCAG 2.2 AA, keyboard-first interactions, visible focus states, semantic HTML before ARIA, reduced-motion support, accessible target sizes.

- Text and meaningful non-text UI must meet WCAG 2.2 AA contrast.
- Keyboard users must be able to reach, understand, and operate every interactive control.
- Focus indicators must be visible, high-contrast, and not hidden by overflow or animation.
- Semantic HTML or native platform semantics come before ARIA patches.
- Touch targets should be at least 24px by WCAG 2.2 AA and should reach 44px when layout allows.

## Content Tone
Clear, concise, implementation-focused, low-jargon, and helpful without being decorative.

- Use direct labels for actions.
- Avoid vague UI copy like "Submit" when the action can be named.
- Keep empty states useful: state what happened, why it matters, and what the user can do next.

## Rules: Do
- use semantic tokens before raw values in components.
- preserve existing content, copy, media, routes, and behavior when applying this system to an existing project.
- preserve hierarchy with spacing, contrast, typography, and component state.
- define default, hover, active, focus-visible, disabled, loading, success, and error states.
- design mobile-first, then enhance for tablet and desktop density.
- keep implementation guidance portable across React, Vue, Svelte, plain HTML/CSS, and mobile UI stacks.
- use soft tactile surfaces where they clarify grouping, repeated actions, selected state, or premium calm.
- choose a clear mode: light enterprise soft UI, split auth panel, compact tactile dashboard, or dark embossed hero.
- preserve accessible contrast and visible focus states above the depth effect.
- pair shadows with semantic component states such as raised default, pressed active, inset selected, disabled flat, and error outlined.
- keep the visual system calm, spacious, and readable.
- tune shadows to the palette instead of copying generic black and white shadow recipes.
- use neumorphism for controls, forms, dashboards, landing pages, and portfolios that benefit from a physical, touch-friendly feel.
- use abstract embossed shapes only when they reinforce the brand atmosphere and remain behind the real content.

## Rules: Don't
- use low-contrast text, hidden focus indicators, or color-only state communication.
- delete or replace existing product content unless the user explicitly asks for content removal.
- introduce one-off spacing, typography, or radius values outside the token system.
- mix unrelated visual metaphors in the same screen.
- depend on framework-specific component names in design rules.
- add decorative motion without reduced-motion fallbacks.
- use low-contrast raised surfaces that hide boundaries, labels, or state.
- apply inset shadows to every input, card, and button indiscriminately.
- clip shadows with tight containers or overflow settings.
- depend on shadow alone to communicate clickability, selection, errors, disabled state, or destructive actions.
- use neumorphism for content-heavy articles, dense data tables, or documentation when simple readable surfaces would work better.
- make everything pale gray, low opacity, and softly blurred until the product loses hierarchy.
- nest multiple raised panels until the interface feels swollen or slow.
- use decorative embossed shapes as a substitute for product content, diagrams, CTAs, or form clarity.

## AI Implementation Checklist
- Read this file before changing UI, layout, component styling, or interaction behavior.
- Identify the target surface: mobile app, mobile web, desktop web, dashboard, landing page, form flow, or content-heavy view.
- Map the design tokens to the project technology without changing the design intent.
- Reuse existing project components when they can satisfy these rules.
- If the current UI conflicts with this file, explain the conflict and choose the more accessible, consistent option.
- Confirm all original navigation items, hero content, CTAs, media, sections, and forms still exist unless removal was requested.
- Confirm no text became invisible from background, opacity, blend-mode, or inherited color changes.
- Confirm the first viewport contains meaningful product content, not just a background treatment.
- Verify keyboard navigation, focus-visible styling, responsive behavior, text overflow, loading state, and error state before finishing.
