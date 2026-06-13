# DESIGN.md

Design system & visual guidelines for **Association Rules Studio** (`index.html`).
All styles live in the single `<style>` block; there is no external stylesheet.

## Theme: "Deep Space"

A dark, cosmic UI: deep indigo-black background, soft nebula glows, a subtle CSS
starfield, and frosted-glass panels that appear to float above space. Accents are a cool
violet/indigo + cyan palette with warm star-gold highlights. Buttons and focus states use
soft colored **glows** instead of heavy drop shadows.

## Design tokens (`:root`)

The UI is **token-driven**. Change these custom properties to retheme; most of the app
follows automatically. Keep the token names stable.

| Token | Value | Role |
|---|---|---|
| `--ink` | `#eaeefb` | Primary text (near-white) |
| `--muted` | `#97a1c2` | Secondary / muted text |
| `--paper` | `#0e1424` | Dark base surface |
| `--paper-strong` | `#141c30` | Slightly raised surface (e.g. table header) |
| `--line` | `rgba(255,255,255,0.10)` | Hairline borders |
| `--line-strong` | `rgba(255,255,255,0.20)` | Stronger borders / input outlines |
| `--pine` | `#8b7bff` | **Primary accent** (violet/indigo) |
| `--moss` | `#22d3ee` | Secondary accent (cyan) |
| `--saffron` | `#f4c869` | Highlight / "warm" buttons (star-gold) |
| `--clay` | `#ff6bb3` | Tertiary accent (magenta) |
| `--blue` | `#6ea8ff` | Extra accent (sky blue) |
| `--graph-bg` | `#060912` | Graph / graph-only background |
| `--graph-panel` | `rgba(15,21,38,0.88)` | Floating panels inside the graph |
| `--shadow` | `0 24px 70px rgba(2,4,12,0.55)` | Standard elevation |
| `--glow` | `0 0 26px rgba(139,123,255,0.42)` | Accent glow |
| `--bg` | `#060912` | App base background color |
| `--surface` | `rgba(255,255,255,0.045)` | Glass panel fill |
| `--surface-strong` | `rgba(255,255,255,0.08)` | Stronger glass fill (chips, buttons) |
| `--radius-lg` / `--radius-md` / `--radius-sm` | `28px` / `18px` / `12px` | Corner radii |

`color-scheme: dark` is set on `:root` so native controls (number spinners, scrollbars)
render dark.

## Light theme & the theme toggle

A topbar switch (`#themeToggleBtn`, a sliding moon↔sun toggle in `.topbar-actions`) flips
between the default **dark** "Deep Space" theme and a **light** theme. The choice persists
in `localStorage` under `THEME_STORAGE_KEY` (`association-rule-theme`) and defaults to dark.

- Light mode is activated by `data-theme="light"` on the **root `<html>` element**
  (`applyTheme` / `toggleTheme` / `initTheme`). It is implemented as
  `:root[data-theme="light"]`, which **redefines the design tokens** to a bright palette
  (`--ink:#1b2438`, `--bg:#e9eef9`, white `--surface`, dark-on-light `--line`, deeper
  accents `--pine:#6d5cf0` / `--moss:#0891b2`) and sets `color-scheme: light`.
- Because most of the UI is token-driven, the token swap covers the bulk of it. A handful
  of **hardcoded dark backgrounds** get explicit light overrides: the `html` nebula
  gradient, the `body::before` starfield (hidden in light), `.topbar`, `.tabs` / `.tab`,
  `thead th`, table zebra/hover, `.log` console, `.graph-card` (+ card-head, pill,
  controls, detail panel), and the graph buttons.
- **Graph/chart text is theme-aware in JS** via `chartInk()` (see below); `toggleTheme`
  re-runs `renderCharts()` so labels/axes/halos flip with the theme.


## Color usage

- **Primary action** (`Run analysis`, `Show graph`): `.btn-primary` — violet→indigo
  gradient (`--pine` → `#4c2fd6`) with a glow.
- **Warm action** (`Export all`, `Fit graph`): `.btn-warm` — gold gradient on dark text.
- **Secondary action**: `.btn-secondary` — glass fill with a hairline border.
- **Focus rings**: violet — `box-shadow: 0 0 0 4px rgba(139,123,255,0.20)`.
- **Table hover**: `rgba(139,123,255,0.16)`; zebra rows: `rgba(255,255,255,0.03)`.
- **Selection**: violet (`::selection`); placeholders: muted violet-grey.

### Colors injected from JavaScript (D3) — NOT tokenized
These must be edited in the `<script>` when retheming. Theme-dependent text/stroke/halo
colors for the chart and graph come from the **`chartInk()`** helper (returns a dark- or
light-mode palette based on `data-theme`); the vibrant accent hues below are shared by both
themes:
- **Top-20 bar gradient** (`#barGradient`): `#8b7bff` → `#22d3ee`.
- **Bar value labels / axes**: theme-aware via `chartInk()` (`barValue` / `axisText` /
  `yAxisText` / `axisLine`).
- **Graph edge color**: sequential `piecewise(interpolateRgb.gamma(2.2), ["#22d3ee",
  "#8b7bff", "#ff6bb3"])` — cyan → violet → magenta by confidence.
- **Single-item node**: `#8b7bff`; **compound-node palette**:
  `["#8b7bff", "#22d3ee", "#ff6bb3", "#f4c869", "#6ea8ff", "#42e8c0"]`.
- Edge/label strokes use halos from `chartInk()`: dark halos `rgba(6,9,18,0.78–0.86)` in
  dark mode, light halos `rgba(255,255,255,0.9–0.92)` with dark text in light mode.

> Before using a new D3 function, confirm it exists in the vendored build:
> `grep -o "piecewise" d3.v7.min.js`.

## Background & starfield

- `html` background: three layered `radial-gradient` nebula glows (violet, cyan, magenta)
  over a dark `linear-gradient`, with `background-attachment: fixed`.
- `body::before`: a fixed, `z-index:-1`, `pointer-events:none` layer of tiled
  `radial-gradient` dots forming the **starfield** (`background-size: 460px 460px;
  background-repeat: repeat`). It twinkles via the `twinkle` keyframes (opacity
  oscillation).
- **Motion is gated**: `@media (prefers-reduced-motion: reduce)` disables the twinkle.

## Layout

- **`.app-shell`** — top-level CSS grid: `minmax(320px,420px) 1fr` (sidebar | workspace),
  collapsing to `72px 1fr` when `body.sidebar-collapsed`, and to a single column below
  `1180px`.
- **`.sidebar`** — sticky, scrollable controls (input, thresholds, text filters, presets,
  run/export). Collapsible via `#sidebarToggleBtn`; also **auto-collapses 3 s after a
  successful analysis**.
- **`.workspace`** — grid with rows `auto auto minmax(0, 1fr)`:
  topbar, tabs, then the **expanding panel**.
  ⚠️ The `minmax(0,1fr)` must stay on the **panel** row (3rd), not the tabs — otherwise an
  empty panel gets pushed to the bottom of the page before any analysis runs.
- **`.topbar`** — flex row holding the title block (`Results` + dataset name), compact
  **stat chips** (`.stat-chip`: Transactions / Items / Rules / Visible) right of the title,
  and `.topbar-actions` (theme toggle + status pill + Help button) pushed to the far right
  via `margin-left:auto`. There is no longer a separate full-width `.stats` row — the chips
  keep the metrics inline to save vertical space.
- **Tabs / panels** — Console, Table (default), Graph & Top 20. Only the `.panel.active`
  is shown.
- **`.chart-grid`** — two columns (Top-20 chart | graph card), single column below
  `1180px`.

## Components

- **Glass panels** (`.sidebar`, `.workspace`, `.section`, `.card`): `--surface`
  fill, hairline border, `backdrop-filter: blur(...)`, `--shadow`.
- **Pills / chips** (`.pill`, `.metric-chip`, `.stat-chip`): rounded, `--surface-strong`,
  muted text.
- **Version pill** (`.version-pill`, `#appVersion`): violet-tinted pill in the brand area
  showing the current `APP_VERSION` (e.g. `v1.0`); populated by `applyAppVersion()`.
- **Status pill** (`#runtimeStatus`): neutral while busy; gets `.pill.is-ready` (green
  text/border/tint) when idle and showing "ready". Toggled in `setBusy`.
- **Inputs**: dark translucent fill (`rgba(255,255,255,0.06)`), light text, violet focus
  glow. Graph-control inputs sit on the dark graph card and use a translucent fill — never
  a light background (would be invisible with light text).
- **Table**: dark sticky header (`#141c30`), subtle zebra striping, violet hover, tabular
  numerals on numeric columns (`.number`).
- **Graph card** (`.graph-card`): own deep-space gradient + nebula glows; floating
  controls, detail panel, and tooltip use dark glass (`rgba(10,15,32,0.9x)`). Action bar
  (`.btn-graph`) includes Fullscreen, New tab, and **Export PNG** (renders the current
  viewport to a PNG on a `#060912` canvas background).
- **Log / Console** (`.log`): near-black mono console (`#0a0f1e`).
- **Toast / Tooltip / Help modal**: dark glass surfaces consistent with the theme.
- **Help modal** (`.help-modal`): a searchable, two-pane dialog (topic nav + content). The
  content is comprehensive and mirrors `README.md`. Rich help elements are themed in the
  help CSS block: `.help-table` (violet header, hairline borders, zebra body rows),
  `.help-license` (near-black `#0a0f1e` mono block with `white-space: pre-wrap` for verbatim
  license texts), plus styled `<ul>/<ol>`, inline `<code>`, and accent-cyan links. Topic
  titles render via `textContent` (use a plain `&`), bodies via `innerHTML`.

## Typography

- **Display / headings**: `"Space Grotesk"` (Google Fonts), tight letter-spacing.
- **Body / UI**: `"Source Sans 3"`.
- **Monospace** (log, ID textareas): `ui-monospace, SFMono-Regular, Menlo, Consolas`.
- Fonts are loaded via `@import` from Google Fonts; everything else is local/offline.

## Scrollbars & misc

- Custom thin violet scrollbars via `scrollbar-color` (Firefox) and `::-webkit-scrollbar`.
- `.spinner` (run button) uses the `spin` keyframes.

## Responsive breakpoints

- **≤ 1180px**: app shell and chart grid collapse to one column; sidebar becomes static.
- **≤ 720px**: topbar/toolbar/help/stats/field rows/button grids/graph controls stack to a
  single column; graph height reduced.

## Retheming checklist

1. Update `:root` tokens (covers most of the UI automatically).
2. Replace any **hardcoded** light literals in CSS (e.g. high-alpha
   `rgba(255,255,255,X)` panel fills, hex text colors) that bypass tokens.
3. Update **JS/D3-injected colors** (chart gradient, axis/label fills, edge interpolator,
   node palette) — listed above.
4. Re-check contrast: no light-on-light (e.g. graph inputs) or dark-on-dark text.
5. Confirm any new D3 color/scale API exists in `d3.v7.min.js`.
6. Respect `prefers-reduced-motion` for any new animation.
