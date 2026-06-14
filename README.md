# Association Rules Studio

Association Rules Studio is a single-file, fully client-side web application for
market-basket / association-rule mining on Excel data. Load a workbook, mine frequent
itemsets with Apriori, generate association rules with a full metric suite, and explore
the results through a table, a Top-20 cost chart, and an interactive D3 rule network.

This HTML version is a browser port of the Python GUI in
`AssociationRulesGUI.py`. There is no server, no build step, no package manager, and no
`mlxtend` dependency. Apriori, frequent-itemset generation, and rule generation are
implemented directly in plain JavaScript inside `index.html`.

## Highlights

- Zero install and offline-first. Open `index.html` directly or serve the folder with any
  static server.
- Excel input and Excel output via vendored SheetJS.
- Apriori from scratch with configurable support, confidence, and maximum itemset size.
- Sortable/searchable rules table with configurable metric visibility.
- Separate Console, Table, and Graph & Top 20 tabs.
- Top-20 weighted consequent cost chart with click-through into the graph.
- Force-directed rule graph with zoom, pan, drag, focus mode, fullscreen, new-tab mode,
  confidence labels, PNG export, and copyable transaction IDs.
- Searchable in-app Help modal.
- Filter presets stored in the browser, plus JSON export/import for sharing.
- Dark/light theme toggle and collapsible sidebar.

## Quick start

1. Open `index.html` in a modern browser.
2. Load an Excel workbook with the `Input file` picker.
3. Set thresholds such as `Min support` and `Min confidence`.
4. Click `Run analysis`.
5. Review the `Console` tab, inspect the `Table`, then switch to `Graph & Top 20`.
6. Export rules as `.xlsx`, export the graph as `.png`, or export filter presets as JSON.

The included sample workbook is `Arbeitsdatei-Quelle.xlsx`.

## Repository contents

```text
.
├── index.html
├── AssociationRulesGUI.py
├── Reference/
│   └── AssociationRulesGUI.py
├── Arbeitsdatei-Quelle.xlsx
├── association-rule-filter-presets.json
├── d3.v7.min.js
├── xlsx.full.min.js
├── README.md
├── DESIGN.md
├── DESCRIPTION.md
└── AGENTS.md
```

Notes:

- `index.html` contains the full app: markup, styles, and JavaScript.
- `AssociationRulesGUI.py` in the repository root is the main Python reference file the
  web version was derived from.
- `Reference/AssociationRulesGUI.py` is a duplicate reference copy kept with the
  historical material.
- `association-rule-filter-presets.json` is an example exported preset file, not the live
  browser storage.

## Input data format

The first worksheet is read with:

```js
XLSX.utils.sheet_to_json(sheet, { header: 1, defval: null, raw: true })
```

Columns are interpreted positionally:

| Column | Meaning | Required |
| --- | --- | --- |
| 1 | Transaction ID | Yes |
| 2 | Item / material | Yes |
| 3 | Order number | Yes |
| 4 | Consumption | Optional |
| 5 | Price | Optional |

Behavior:

- Rows with the same transaction ID are grouped into one basket.
- Empty rows are ignored.
- Items are trimmed and de-duplicated within a transaction.
- If both consumption and price are present and consumption is greater than zero, the app
  derives a unit price as `price / consumption`.
- If `Include consumption = 0` is disabled, rows with consumption `<= 0` are removed before
  mining.

## Default settings

| Control | Default |
| --- | --- |
| `Min support` | `0.003` |
| `Min confidence` | `0.10` |
| `Max. itemset size` | `4` |
| `Table limit` | `5000` |
| `Include consumption = 0` | enabled |
| `Output file name` | `SPC_Rules.xlsx` |

Default visible metric columns in the table:

- `Support`
- `Lift`
- `Combination Count`
- `Different Items`

Always-visible columns:

- `Antecedents`
- `Consequents`
- `Confidence`

## Workflow

### Load a workbook

Use the `Input file` picker in the sidebar. The selected filename appears in the input
status pill and in the workspace title area once analysis results exist.

### Set thresholds and text filters

The analysis section controls support, confidence, maximum itemset size, table row limit,
and whether consumption-zero rows are kept.

The text-filter section applies include/exclude term filters before mining. Terms are
comma-separated and case-insensitive.

Important validation rule:

- The `Only items containing terms` field must contain either zero terms or at least two
  terms. A single include term aborts the run with an error message.

### Run the analysis

Click `Run analysis`. The button shows a spinner, the status pill changes away from
`ready`, and progress is written to the `Console` tab. On success:

- the rules table is populated,
- the Top-20 chart and graph render,
- a toast confirms the rule count,
- the sidebar auto-collapses after 3 seconds.

### Explore the results

#### Console

The Console is a timestamped log of the file load, preprocessing, Apriori mining, rule
generation, warnings, and runtime errors.

#### Table

- Click column headers to sort.
- Use `Quick search` to filter antecedents and consequents.
- Toggle metric visibility with the metric chips.
- Use `Show graph` to switch to the graph tab.

#### Graph & Top 20

The split view contains:

- a Top-20 weighted consequent cost chart on the left,
- the rule network on the right.

Clicking a Top-20 bar filters the graph to the corresponding combination and replays the
bar animation.

## The rule graph

The rule graph is a D3 force-directed network.

### Visual encoding

- Nodes represent antecedent or consequent itemsets.
- Single-item nodes are one circle.
- Multi-item itemsets are drawn as touching clusters of circles rather than one large
  monolithic node.
- Edge color encodes confidence.
- Edge width encodes combination count.
- Node size encodes how frequently the node appears across visible rules.

### Controls

| Control | Effect |
| --- | --- |
| `Confidence %` | Show or hide percentage labels on edges |
| `Fullscreen` | Expand the graph inside the current tab |
| `New tab` | Open the current graph as a graph-only view |
| `Export PNG` | Save the current graph viewport as a PNG |
| `Max. edges` | Limit how many visible rules enter the graph |
| `Min. confidence` | Graph-only confidence threshold |
| `Graph search` | Filter by item, itemset text, `Mat_combination`, or `unique_ID` |
| `Fit graph` | Re-center and fit the current graph |

### Interaction model

- Mouse wheel: zoom
- Drag empty background: pan
- Drag a node: reposition it
- Click a node: focus that node and hide unrelated nodes/edges
- Click the same node again or click the background: clear focus
- Hover a node or edge: show a transient tooltip
- Click a node or edge: open the fixed detail panel

The graph detail panel includes:

- key metrics for the selected node or edge,
- the associated transaction IDs,
- a `Copy IDs` action.

Node hover currently shows, among other things:

- rule connections,
- combination count sum,
- node cost sum,
- transaction IDs.

### Fullscreen and new-tab modes

There are three graph contexts:

- normal split view,
- fullscreen within the current page,
- graph-only new-tab mode.

Fullscreen and graph-only mode are the most isolated rendering contexts and are also where
graph auto-resize is allowed.

## Filter presets

Filter presets are managed in the sidebar.

A preset captures:

- include terms,
- exclude terms,
- quick search,
- graph search,
- graph min confidence,
- graph edge limit,
- confidence-label toggle,
- visible metric columns.

There are two storage paths:

1. Live presets are stored in the browser under `localStorage`.
2. Presets can be exported to a JSON file and imported again later or on another machine.

This means presets are shareable, but the app does not automatically write them back into a
physical JSON file in the project folder while you work.

## Exports

### Rules export

`Export all` writes the full rule set to `.xlsx` using the currently selected visible
columns.

### Graph export

`Export PNG` saves the current graph viewport. If the graph-search field contains a number,
the first numeric run is used as a filename prefix:

- `12345678_rule-graph.png`
- otherwise `rule-graph.png`

### Preset export

Preset JSON export/import is versioned with `FILTER_PRESET_EXPORT_VERSION`, currently `1`.

## Metrics

For a rule `A => C`:

| Metric | Formula |
| --- | --- |
| Support | `support(A union C)` |
| Confidence | `support(A union C) / support(A)` |
| Lift | `confidence / support(C)` |
| Leverage | `support(A union C) - support(A) * support(C)` |
| Conviction | `(1 - support(C)) / (1 - confidence)` |
| Zhang's metric | see `zhangsMetric()` in `index.html` |

Cost-related fields:

- `Cost Antecedents (EUR)`
- `Cost Consequents (EUR)`
- `Cost Consequents x Combination Count (EUR)`
- `Cost Antecedent+Consequents (EUR)`

The metric formulas are intended to stay aligned with the Python reference implementation.

## Architecture

All application logic lives in the single `<script>` block in `index.html`.

High-level pipeline:

1. `handleFile` reads the workbook with SheetJS.
2. `preprocessRows` filters rows, derives unit prices, and builds transactions.
3. `apriori` mines frequent itemsets.
4. `buildRules` derives association rules and metrics.
5. `runAnalysis` validates inputs, orchestrates the pipeline, and writes results into
   shared state.
6. `renderTable`, `renderTopChart`, and `renderGraph` present the results.

Rendering model:

- plain DOM + D3,
- no framework,
- one central mutable `state` object,
- manual `render*()` calls after state updates.

## Persistence

The app stores runtime UI state in `localStorage`:

| Key | Purpose |
| --- | --- |
| `association-rule-filter-presets-v1` | Saved filter presets |
| `association-rule-sidebar-collapsed` | Sidebar collapsed state |
| `association-rule-theme` | Light/dark theme |
| `association-rule-graph-autoresize` | Graph auto-resize switch |
| `association-graph-<timestamp>-<rand>` | Temporary graph payload for new-tab mode |

Important nuance:

- The graph auto-resize setting is persisted globally.
- The actual `ResizeObserver` behavior is limited to fullscreen and graph-only mode because
  split-view auto-resize can trigger Safari/WebKit rendering problems and layout feedback.

## Browser support

Current Chrome, Edge, Firefox, and Safari are the intended targets.

The app relies on:

- ES2020+ JavaScript
- `crypto.subtle.digest`
- `BigInt`
- `canvas.toBlob`
- SVG + D3 rendering
- `localStorage`

`file://` and `http://localhost` are both viable ways to run the app locally.

## Known limitations and quirks

- Only the first worksheet is read.
- `unique_ID` is derived from `Mat_combination`, so collisions are possible when different
  item combinations share the same order-number set.
- `renderCharts()` catches graph errors and reports them via toast + console instead of
  crashing the page.
- The graph relies on SVG-to-canvas export; external cross-origin image content inside the
  SVG could break PNG export.
- Safari/WebKit required targeted rendering workarounds in the graph view:
  - frosted overlays inside the split-view graph are disabled in Safari normal mode,
  - expensive tooltip effects are reduced in Safari,
  - graph auto-resize is restricted to fullscreen and graph-only mode,
  - split-view graph rendering is sequenced carefully around Top-20 animation to reduce
    compositing artifacts.

## Development notes

There is no build system and no automated test suite in this directory. The normal workflow
is:

1. edit `index.html`,
2. reload the browser,
3. test with `Arbeitsdatei-Quelle.xlsx`,
4. verify Console, Table, Top 20, and Graph behavior.

When behavior changes materially, keep these files aligned:

- `README.md`
- `DESCRIPTION.md`
- `DESIGN.md`
- `AGENTS.md`
- the in-app `helpTopics` content inside `index.html`

## Third-party software

The app uses:

- SheetJS / `xlsx.full.min.js` for Excel input/output
- D3.js v7 / `d3.v7.min.js` for table/chart/graph rendering
- Space Grotesk and Source Sans 3 for typography

The HTML version does not use `mlxtend` or other Python mining libraries.

## Contact

For questions, contact Roland Emrich.
