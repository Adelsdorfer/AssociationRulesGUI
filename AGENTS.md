# AGENTS.md

Guidance for coding agents and contributors working in this repository.

## Project summary

Association Rules Studio is a single-file browser application for association-rule mining
on Excel data. The HTML app is a port of the Python GUI in `AssociationRulesGUI.py` and
implements Apriori and rule generation directly in JavaScript.

Core constraints:

- no build system
- no package manager
- no server requirement
- no framework
- no `mlxtend`
- no edits to vendored third-party libraries

Everything user-facing happens from `index.html`.

## Repository layout

| Path | Purpose |
| --- | --- |
| `index.html` | Entire web app: HTML, CSS, JS |
| `AssociationRulesGUI.py` | Primary Python reference implementation |
| `Reference/AssociationRulesGUI.py` | Historical/reference copy of the Python GUI |
| `Arbeitsdatei-Quelle.xlsx` | Sample workbook for manual testing |
| `association-rule-filter-presets.json` | Example exported preset JSON |
| `d3.v7.min.js` | Vendored D3.js |
| `xlsx.full.min.js` | Vendored SheetJS |
| `README.md` | User-facing project documentation |
| `DESCRIPTION.md` | Short-form project description |
| `DESIGN.md` | Design-system and layout documentation |
| `AGENTS.md` | This file |

## Runtime model

Open `index.html` directly in a browser or serve the folder with any static server.

Normal manual verification uses:

1. `Arbeitsdatei-Quelle.xlsx`
2. `Run analysis`
3. the `Console`, `Table`, and `Graph & Top 20` tabs

There is no automated test suite in this folder.

## Input contract

The first worksheet is read with `XLSX.utils.sheet_to_json(..., { header: 1, defval: null, raw: true })`.

Column mapping is positional:

1. transaction ID
2. item / material
3. order number
4. consumption (optional)
5. price (optional)

At least 3 columns and 2 rows are required.

## Main pipeline

Everything lives in the single `<script>` block in `index.html`.

1. `handleFile`
   - reads the workbook into `state.workbookRows`
   - stores headers and source filename

2. `preprocessRows`
   - applies include/exclude filters
   - optionally removes consumption-zero rows
   - derives unit prices
   - groups rows into transactions

3. `apriori`
   - mines frequent itemsets
   - uses classic join-and-prune candidate generation
   - respects `maxItemsetSize`

4. `buildRules`
   - enumerates antecedent/consequent splits
   - computes metrics
   - computes cost fields
   - collects matching transaction IDs
   - generates deterministic 8-digit `unique_ID` values

5. `runAnalysis`
   - validates thresholds
   - validates include-term rules
   - logs progress
   - sorts results
   - updates shared state

## UI structure

The app is split into:

- a left sidebar with input, thresholds, text filters, presets, and run/export actions
- a right workspace with topbar, tabs, and one active panel

Workspace tabs:

- `Console`
- `Table`
- `Graph & Top 20`

The topbar also contains:

- compact stats chips
- graph auto-resize toggle
- theme toggle
- runtime status pill
- Help button

## Rendering responsibilities

### `renderTable`

- renders visible rules with sortable headers
- respects `quickSearch`
- respects metric visibility chips
- updates visible counts

### `renderTopChart`

- renders the Top-20 weighted consequent cost chart
- uses D3 scales and SVG
- animates bar widths on normal chart renders
- stores target widths in `data-final-width` for replay

### `showCombinationInGraph`

- sets the graph search field to the clicked combination ID
- forces graph min-confidence to `0`
- switches to the graph tab when needed
- re-renders the graph
- replays Top-20 bar animation

### `renderGraph`

- tears down any previous graph state before re-rendering
- builds nodes and links from current visible rules
- configures zoom, drag, force simulation, tooltips, focus mode, and detail panel
- supports fullscreen and graph-only modes

### `renderCharts`

- renders Top 20 and graph together
- includes Safari-sensitive sequencing so the graph does not repaint at the worst possible
  moment relative to the bar animation

## Graph behavior details

Important current behavior:

- Clicking a node focuses it and hides unrelated nodes/edges.
- Clicking a node or edge opens a fixed detail panel with copyable transaction IDs.
- Hovering shows a lighter-weight transient tooltip.
- The `Confidence %` checkbox toggles edge labels.
- `New tab` opens a graph-only mode using a transient `localStorage` payload.
- `Export PNG` exports the current viewport, not an abstract fresh graph.

Compound itemsets are rendered as touching multiple circles rather than one circle.

## Safari / WebKit constraints

Safari required explicit rendering workarounds. Preserve these unless you have verified a
better fix:

- In normal split view, graph overlays should not use live `backdrop-filter`.
- Tooltip behavior in Safari is intentionally simplified.
- The graph `ResizeObserver` is only allowed in fullscreen or graph-only mode.
- Do not promote `#ruleGraph` itself to a composited layer; that caused zoom-snap effects.
- Avoid turning split-view layout or graph sizing into a feedback loop. Safari is much less
  forgiving here than Chrome.

If you touch graph sizing, tooltip positioning, transitions, or `ResizeObserver` logic,
test Safari explicitly.

## Central state

Shared mutable state lives in `state`.

Relevant keys:

- `workbookRows`
- `headers`
- `sourceName`
- `allRules`
- `filteredRules`
- `visibleRules`
- `sortColumn`
- `sortAsc`
- `stats`
- `graphZoom`
- `graphSimulation`
- `graphResizeObserver`
- `graphAutoResize`
- `isSafari`
- `savedFilterPresets`
- `activeFilterPreset`

There is no framework and no reactive data layer. Functions mutate `state` directly and
call explicit `render*()` functions.

## Persistence

The app uses `localStorage` for:

- `association-rule-filter-presets-v1`
- `association-rule-sidebar-collapsed`
- `association-rule-theme`
- `association-rule-graph-autoresize`
- transient `association-graph-<timestamp>-<rand>` keys

Presets are not automatically written to a project JSON file during normal use. The JSON
file in the repository is an example exported artifact.

## Documentation sync rules

When behavior changes, keep these aligned:

- `README.md`
- `DESCRIPTION.md`
- `DESIGN.md`
- this `AGENTS.md`
- the in-app `helpTopics` content inside `index.html`

Common drift points:

- default thresholds
- visible default metric columns
- graph controls
- storage model for presets
- Safari-specific behavior
- repository file layout

## Coding rules for this repository

- Edit `index.html` unless the task is specifically about documentation.
- Do not edit `d3.v7.min.js` or `xlsx.full.min.js`.
- Keep the app runnable from `file://`.
- Prefer small, explicit state changes and direct render calls.
- Match existing style: 2-space indentation, double-quoted strings, `const`/`let`,
  `camelCase`.
- Keep user-facing UI text and logs in English.

## Known functional caveats

- `unique_ID` can collide because it is derived from order-number combinations.
- Apriori runtime grows quickly on large or dense datasets.
- Graph export can fail if cross-origin image content is introduced into the SVG.
- Only the first worksheet is processed.
- Graph problems often surface in the `Console` tab rather than as hard crashes because
  `renderCharts()` is guarded by `try/catch`.
