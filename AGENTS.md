# AGENTS.md

Guidance for AI coding agents (and humans) working in this repository.

## Project overview

**Association Rules Studio** is a single-file, fully client-side web application for
**market-basket / association-rule mining** on Excel data. It is a browser port of the
Python tool `AssociationRulesGUI.py` that lives in the same folder — there is **no server,
no build step, and no `mlxtend` dependency**. The Apriori algorithm, frequent-itemset
generation, and rule generation are all implemented from scratch in plain JavaScript.

Everything (HTML markup, CSS, and JavaScript) lives in **`index.html`**. The two `.js`
files are vendored third-party libraries loaded via `<script>` tags.

## Repository layout

| Path | Purpose |
|---|---|
| `index.html` | The entire application: HTML + CSS (`<style>`) + JS (`<script>`). **This is the only file you edit.** |
| `xlsx.full.min.js` | Vendored [SheetJS](https://sheetjs.com/) — reads `.xlsx`/`.xls` input and writes `.xlsx` exports. Do not edit. |
| `d3.v7.min.js` | Vendored [D3.js v7](https://d3js.org/) — table rendering, charts, force-directed graph, scales, color interpolation. Do not edit. |
| `Arbeitsdatei-Quelle.xlsx` | Sample/working input workbook for manual testing. |
| `AssociationRulesGUI.py` | The original Python reference implementation. Source of truth for algorithm behavior. |
| `WebVersion.7z` | Archived snapshot of the web version. Ignore unless explicitly asked. |
| `DESIGN.md` | Visual/design-system documentation (theme tokens, layout, conventions). |
| `AGENTS.md` | This file. |

## How to run

There is no build and no package manager. To run, open `index.html` directly in a
browser (`file://`) — all libraries are local, so it works fully offline. For testing,
load `Arbeitsdatei-Quelle.xlsx` via the **Input** file picker, then click **Run analysis**.

There are **no automated tests, no linter config, and no CI**. Verification is manual:
open the page, run an analysis, and confirm the table, Top-20 chart, and graph render.

## Input data contract

The first worksheet is read with `XLSX.utils.sheet_to_json(..., { header: 1 })`.
Columns are interpreted **positionally** (the header names are informational only):

1. Column 1 → transaction ID
2. Column 2 → item / material
3. Column 3 → order number (used to build `Mat_combination` and `unique_ID`)
4. Column 4 → consumption *(optional)*
5. Column 5 → price *(optional; converted to unit price via `price / consumption`)*

At least 3 columns and 2 rows (1 header + 1 data) are required.

## Architecture & data flow

All logic is inside the single `<script>` block in `index.html`. The pipeline:

1. **`handleFile`** — reads the workbook with SheetJS into `state.workbookRows`.
2. **`preprocessRows`** — applies include/exclude term filters and the consumption
   filter, derives unit prices, and groups rows into transactions per ID.
3. **`apriori`** — classic Apriori: count single items ≥ `minSupport`, then iteratively
   build size-`k` candidates via **`createCandidates`** (join + prune) up to
   `maxItemsetSize`.
4. **`buildRules`** — splits each frequent itemset into antecedent/consequent subsets,
   computes metrics, and assigns a deterministic 8-digit `unique_ID`
   (`createUnique8DigitId`, SHA-256 based).
5. **`runAnalysis`** — orchestrates the above, validates inputs (thresholds plus a rule
   that the **include-items** field must contain either 0 or ≥ 2 comma-separated terms),
   logs progress, sorts by confidence/lift, stores results on the central `state` object,
   and schedules the sidebar to auto-collapse 3 s after a successful run.

### Presentation layer
- **`renderTable`** — sortable, searchable D3 table; columns chosen via `renderMetricChooser`.
- **`renderCharts`** → **`renderTopChart`** (Top-20 cost bar chart) + **`renderGraph`**
  (force-directed rule network; nodes = items, directed edges = rules).
- **`exportRows`** — writes results back to `.xlsx` with SheetJS.
- **`exportGraphPng`** — exports the **current graph viewport** (clones `#ruleGraph` with
  its live zoom/pan `viewBox`) to a high-res PNG via canvas. Filename comes from
  **`graphPngFilename`**: if the **Graph search** field contains a number, its first digit
  run is used as a `<number>_` prefix (e.g. `12345678_rule-graph.png`), else
  `rule-graph.png`.
- **`setBusy`** — toggles the run button spinner and the runtime status pill; the pill
  gets the `is-ready` class (green) only when idle and showing "ready".
- Filter presets, help modal, sidebar collapse, and graph-only mode round out the UI.

### Central state
A single `state` object holds `workbookRows`, `headers`, `allRules`, `filteredRules`,
`visibleRules`, sort settings, `stats`, and saved filter presets. There is no framework
and no reactive system — functions read from and mutate `state` directly, then call the
relevant `render*` function.

## Metrics (must match the Python reference)

| Metric | Formula |
|---|---|
| Confidence | `supportAC / supportA` |
| Lift | `confidence / supportC` |
| Leverage | `supportAC − supportA·supportC` |
| Conviction | `(1 − supportC) / (1 − confidence)` (∞ when confidence = 1) |
| Zhang's metric | `zhangsMetric(supportA, supportC, supportAC)` |

If you change any metric, keep it consistent with `AssociationRulesGUI.py`.

## Versioning & licensing

- The app version is the JS constant **`APP_VERSION`** (top of the `<script>` block,
  currently `"1.0"`). `applyAppVersion()` (run on init) surfaces it in the brand version
  pill (`#appVersion`), the sidebar copyright line (`#sidebarCopyright`), and
  `document.title`. The "Open-source software" help topic also reads `APP_VERSION`. Bump
  this single constant to release a new version.
- The project is licensed under **GPL-3.0** (`LICENSE.txt`). `LICENSE.txt` also reproduces
  the full third-party license texts: SheetJS (Apache-2.0), D3.js (ISC), and the UI fonts
  (SIL OFL 1.1). When adding/removing a bundled component, update `LICENSE.txt`, the OSS
  help topic, and the README third-party table together.

## Persistence (localStorage keys)

- `association-rule-filter-presets-v1` — saved filter presets (`FILTER_PRESET_STORAGE_KEY`).
- `association-rule-sidebar-collapsed` — sidebar collapsed state (`SIDEBAR_COLLAPSED_STORAGE_KEY`).
- `association-graph-<timestamp>-<rand>` — transient payload for the "open graph in new tab" feature.
- Preset JSON export/import uses `FILTER_PRESET_EXPORT_VERSION` (currently `1`); bump it on a breaking schema change.

## Conventions & house rules

- **Edit only `index.html`.** Never modify the vendored `*.min.js` libraries.
- **No new dependencies, no build tooling, no server.** The app must keep working from a
  bare `file://` open, fully offline.
- **Keep it one file.** Do not split HTML/CSS/JS into separate files unless explicitly
  requested.
- **CSS:** the design is token-driven via `:root` custom properties (`--ink`, `--surface`,
  `--pine`, etc.). Prefer changing/using tokens over hardcoding colors. See `DESIGN.md`.
- **Colors injected from JS** (D3 `.attr("fill"/"stroke")`, chart gradients, node palette,
  `scaleSequential` interpolators) are **not** covered by CSS tokens — update them in the
  script when changing the theme.
- **Verify D3 APIs exist in the bundled build** before using them, e.g.
  `grep -o piecewise d3.v7.min.js`. The vendored file is a specific v7 build.
- **2-space indentation**, double-quoted strings, `const`/`let`, `camelCase` for JS;
  existing UI copy and log messages are in **English**.
- **User-facing errors** are surfaced via `throw new Error(...)` inside `runAnalysis`
  (caught → `toast` + `log`), or directly via `toast(...)`/`log(...)`.
- Don't add comments, docstrings, or refactors to code you didn't change.

## Known quirks / gotchas

- `unique_ID` is derived from `Mat_combination` (the order numbers). Two different
  item-combinations that share the same set of order numbers can therefore collide.
- Apriori candidate counting is `O(candidates × transactions)` per level — fine for
  spare-parts datasets, but can be slow on very large/dense data. `maxItemsetSize` (default
  4) bounds this in the browser.
- `renderCharts` is wrapped in `try/catch`; a runtime error in the graph fails silently to
  a toast/log instead of crashing — check the Console panel when a chart looks wrong.
- The expanding workspace grid row must stay on the **panel** row. The topbar now holds
  the title plus compact stat chips (Transactions/Items/Rules/Visible) and the status pill
  + Help button, so `.workspace` uses `grid-template-rows: auto auto minmax(0, 1fr)`
  (topbar, tabs, panel) — the old separate `.stats` row was removed.
- PNG export relies on serializing the live SVG; if you add external `<image>` or
  cross-origin assets into the graph, the canvas may taint and `toBlob` will fail.
