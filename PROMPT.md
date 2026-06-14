# Reconstruction Prompt For Codex 5.5 / Claude Opus 4.8

You are an expert coding model. Recreate a complete local web application project called
**Association Rules Studio** that matches the specification below as closely as possible.

This prompt is designed for **Codex 5.5** or **Claude Opus 4.8**. Assume you are working in
an existing local folder and should directly create or update files rather than writing a
high-level plan only.

Your goal is to reproduce the **resulting project**, not merely a simplified prototype.
Pay close attention to:

- exact functionality
- exact file structure
- UX details
- styling direction
- browser behavior
- Safari/WebKit constraints
- documentation parity

If a detail below appears unusually specific, keep it. Those details are intentional.

## Primary objective

Build a **single-file, fully client-side HTML application** for **market-basket /
association-rule mining** on Excel data. The app must:

- read `.xlsx` / `.xls`
- mine frequent itemsets with **Apriori**
- generate association rules in plain JavaScript
- show results in:
  - a **Console** tab
  - a **Table** tab
  - a **Graph & Top 20** tab
- run locally with **no server requirement**
- use **no build step**
- use **no framework**
- use **no mlxtend**

This is a browser port of a Python GUI reference file called
`AssociationRulesGUI.py`, but the web app must implement Apriori and rule generation
directly in JavaScript.

## Required project structure

Create or update these files:

- `index.html`
- `README.md`
- `AGENTS.md`
- `DESIGN.md`
- `DESCRIPTION.md`

Assume these local vendored files exist next to `index.html` and must be used instead of
package-manager dependencies:

- `d3.v7.min.js`
- `xlsx.full.min.js`

Also assume there is a sample workbook:

- `Arbeitsdatei-Quelle.xlsx`

Also include this example share/export artifact in the project:

- `association-rule-filter-presets.json`

Do not introduce build tooling, package manifests, framework scaffolding, or a backend.

## Non-negotiable architecture

### Single-file app

`index.html` must contain:

- HTML markup
- CSS in a `<style>` block
- JavaScript in a `<script>` block

No splitting into extra app source files unless absolutely necessary for static assets. The
core app must stay in one file.

### No framework

Use:

- plain DOM APIs
- D3.js for SVG/table/chart work
- SheetJS for Excel read/write

No React, Vue, Svelte, Angular, Vite, webpack, npm, etc.

### Offline-first

The app must work from:

- `file://.../index.html`
- or a simple static server like `python3 -m http.server`

## Functional scope

### 1. Input handling

The app reads the **first worksheet only**.

Read with the equivalent of:

```js
XLSX.utils.sheet_to_json(sheet, { header: 1, defval: null, raw: true })
```

Interpret columns **positionally**, not by header name:

1. transaction ID
2. item / material
3. order number
4. consumption (optional)
5. price (optional)

Requirements:

- at least 3 columns
- at least 2 rows total
- ignore empty rows
- trim items
- de-duplicate items within each transaction

If price and consumption are both available and consumption is greater than zero, derive a
unit price as:

```text
unit price = total price / consumption
```

### 2. Sidebar controls

Create a left sidebar containing:

- input file picker
- output file name input
- analysis thresholds
- text filters
- filter preset manager
- run/export actions
- subtle version/contact line for Roland Emrich

Required labels and defaults:

- `Output file name` default: `SPC_Rules.xlsx`
- `Min support` default: `0.003`
- `Min confidence` default: `0.10`
- `Max. itemset size` default: `4`
- `Table limit` default: `5000`
- checkbox `Include consumption = 0` default: enabled

Filter preset section must include:

- dropdown `Saved filters`
- `Save filter`
- `Delete filter`
- `Export JSON`
- `Import JSON`

Use a hidden file input for JSON import.

### 3. Text filter behavior

Before analysis, support:

- `Only items containing terms`
- `Exclude items`

Terms are:

- comma-separated
- case-insensitive
- trimmed

Important validation rule:

- the include field must contain either **zero terms** or **at least two terms**
- exactly one include term must abort analysis with a clear error

The same include/exclude terms must also be applied to the generated rules after analysis
when filtering the result set.

### 4. Core Apriori implementation

Implement Apriori from scratch in JavaScript.

Expected structure:

- preprocess rows into transactions
- count singleton itemsets
- generate higher-order candidates using classic **join + prune**
- stop at `maxItemsetSize`
- compute supports and counts

Use functions with concepts equivalent to:

- `preprocessRows`
- `createCandidates`
- `apriori`
- `buildRules`
- `zhangsMetric`
- `createUnique8DigitId`

### 5. Rule generation

For each frequent itemset of size >= 2:

- enumerate proper antecedent subsets
- derive consequents as complement
- compute all metrics
- keep only rules meeting `minConfidence`

Required rule fields:

- `antecedents`
- `consequents`
- `support`
- `confidence`
- `lift`
- `leverage`
- `conviction`
- `zhangs_metric`
- `combination_count`
- `cost_antecedents`
- `cost_consequents`
- `cost_consequents_weighted`
- `cost_total`
- `Mat_combination`
- `Mat_combination_items`
- `transaction_ids`
- `unique_ID`
- `different items`

### 6. Metrics

Support these formulas:

- `support(A union C)`
- `confidence = support(A union C) / support(A)`
- `lift = confidence / support(C)`
- `leverage = support(A union C) - support(A) * support(C)`
- `conviction = (1 - support(C)) / (1 - confidence)`, with `Infinity` if confidence is 1
- Zhang's metric in the range `[-1, 1]`

The output should remain conceptually aligned with the Python reference implementation.

### 7. unique_ID generation

Generate a deterministic 8-digit identifier from `Mat_combination` using a SHA-256-based
approach via browser crypto.

Important known caveat:

- collisions are still possible because `unique_ID` is derived from the order-number
  combination rather than the full item semantics

This caveat should be acknowledged in the documentation.

## UI layout

### Global structure

Use a two-column desktop layout:

- left: sidebar
- right: workspace

Below roughly `1180px`, collapse to one column.

The workspace must contain:

- a topbar
- a tab bar
- one active panel

Panels:

- `Console`
- `Table`
- `Graph & Top 20`

### Topbar

The topbar must include:

- title area
- current dataset name
- compact stat chips:
  - Transactions
  - Items
  - Rules
  - Visible
- theme toggle
- runtime status pill
- Help button

Do **not** include any graph resize toggle.

### Runtime status

Use a pill labeled `ready` when idle.

When analysis runs:

- switch away from ready
- show a spinner in the run button
- restore ready state when finished

### Sidebar auto-collapse

After a successful analysis:

- auto-collapse the sidebar after 3 seconds

Also provide a manual sidebar collapse/expand button and persist that state.

## Table behavior

The Table tab must support:

- sortable columns
- quick search on antecedents/consequents
- configurable metric visibility
- table row limit

Always-visible columns:

- Antecedents
- Consequents
- Confidence

Default visible optional columns:

- Support
- Lift
- Combination Count
- Different Items

Export all rules to Excel using the currently selected visible columns.

## Console behavior

The Console tab is a timestamped log view.

It should log:

- file loading
- detected columns
- text filtering effects
- consumption filtering effects
- price derivation notes
- frequent-itemset counts
- rule-generation progress
- missing price warnings
- success messages
- runtime errors

Use concise English log messages.

## Top-20 chart behavior

Build a horizontal Top-20 chart of **weighted consequent costs**.

This chart must:

- show the top 20 by `cost_consequents_weighted`
- use a violet-to-cyan gradient
- animate bar width on normal render
- replay the bar animation when a combination is selected
- allow clicking:
  - a bar
  - its y-axis label
  - its value label

Click behavior:

- fill the graph search field with the clicked combination ID
- set graph min-confidence to `0`
- open the Graph tab if needed
- render the graph filtered to that combination
- replay the Top-20 animation
- show a toast confirming the graph filter

Animation details:

- approximately `650ms`
- use a smooth easing like cubic-out
- respect `prefers-reduced-motion`

## Graph requirements

### General

Build a D3 force-directed rule graph in SVG.

Nodes are antecedent/consequent itemsets. Edges are rules.

Graph controls:

- `Confidence %` checkbox
- `Fullscreen`
- `New tab`
- `Export PNG`
- `Max. edges`
- `Min. confidence`
- `Graph search`
- `Fit graph`

### Encoding

- edge color = confidence
- edge width = combination count
- node size = visibility/frequency

Use a confidence gradient equivalent to:

- cyan -> violet -> magenta

### Compound itemsets as touching circles

This is important.

If a node represents more than one item, do **not** draw it as one single circle.

Instead:

- 2-item itemsets: two touching circles
- 3+ item itemsets: a touching cluster/ring of circles

Node size semantics:

- the overall compound node should still reflect the same logical size meaning as the
  single-node version
- individual child circles should not misleadingly imply a smaller node importance

### Interaction

Support:

- wheel zoom
- background pan
- draggable nodes
- click node to focus and hide unrelated graph parts
- click same node or background to clear focus
- hover tooltip on nodes and edges
- click node or edge to open a fixed detail panel

### Hover tooltip content

For node hover include:

- node label
- rule connections
- combination count sum
- node cost sum
- transaction IDs
- note that costs are counted once per visible combination

For edge hover include:

- source -> target
- confidence
- lift
- combination count
- transaction IDs
- combination text

### Fixed detail panel

A right-side floating detail panel inside the graph card must open on node or edge click.

For nodes include at least:

- Rule connections
- Combination count sum
- Node cost sum
- Items
- Transaction IDs count

For edges include at least:

- Confidence
- Lift
- Combination count
- Weighted cost
- Combination
- Transaction IDs count

The detail panel must also include:

- a textarea with the transaction IDs
- `Copy IDs` button

Clipboard behavior:

- if clipboard API works, copy and toast success
- otherwise focus/select the textarea and instruct the user to press Cmd+C

### Confidence labels

The `Confidence %` toggle must show percentage labels on edges.

Important edge case:

- if there are bidirectional or paired relationships, the graph must be able to display
  both confidence labels rather than visually collapsing them into one unreadable label
- use edge-label offsets or a similar strategy

### Graph search and filtering

Graph search must match against:

- antecedents
- consequents
- `Mat_combination_items`
- `Mat_combination`
- `unique_ID`

Graph filtering should use:

- graph-only min-confidence
- graph edge limit
- graph search field

### Graph ranking for visibility

When choosing which rules enter the graph, sort by a weighted score that favors:

- higher confidence
- meaningful combination count

A score like:

```text
confidence * log2(combination_count + 2)
```

is acceptable and should be used if you want to match this project closely.

### Fit graph

Implement manual fit-to-content with zoom transform.

Behavior:

- auto-fit after initial render should be non-animated
- manual `Fit graph` should animate
- use sensible padding
- clamp zoom scale to a stable range

### Fullscreen mode

Support in-page fullscreen for the graph card:

- `Fullscreen` button changes to `Exit fullscreen`
- `Escape` exits fullscreen
- the graph should refit after the transition

### New-tab graph-only mode

Support opening the current graph in a standalone tab by:

- storing a slim graph payload in `localStorage`
- opening the same page with query params like:
  - `graphOnly=1`
  - `graphKey=<payload key>`

In graph-only mode:

- hide sidebar
- hide topbar
- hide tabs
- hide table and console
- hide the left Top-20 card
- show only the graph card filling the page
- hide the `Fullscreen` and `New tab` buttons there

### PNG export

Export the current graph viewport to PNG by:

- cloning the live SVG
- serializing it
- drawing it to canvas
- filling the background with a graph-appropriate solid color

Filename rule:

- if `Graph search` contains a number, use the first digit run as a prefix:
  - `<number>_rule-graph.png`
- otherwise:
  - `rule-graph.png`

Use a higher-resolution export scale based on device pixel ratio.

## Filter presets

Implement filter presets stored in browser storage and shareable through JSON files.

Preset content must include:

- include terms
- exclude terms
- quick search
- graph search
- graph min confidence
- graph edge limit
- confidence-label toggle
- selected metric columns

Required behavior:

- save under arbitrary user-chosen names
- overwrite confirmation on existing names
- dropdown applies a preset immediately
- delete current preset
- export preset collection as JSON
- import preset collection from JSON
- store preset collection in `localStorage`

Use:

- storage key `association-rule-filter-presets-v1`
- export schema version `1`

Important clarification:

- live presets are stored in browser storage
- exported JSON is for sharing/transport
- do not automatically sync live presets back into a physical project JSON file

## Theme and visual design

### Overall look

Design the UI as a polished, intentional product, not a bland CRUD tool.

Target aesthetic:

- dark "Deep Space" theme
- layered nebula gradients
- subtle starfield texture
- glowing violet/cyan accents
- glass-like translucent panels
- warm gold accent for selected actions

There must also be a **light theme** toggle.

### Dark theme

Dark mode should feel premium and atmospheric:

- deep indigo/black background
- luminous but restrained accents
- readable contrast

### Light theme

Light mode must be properly designed, not an inverted afterthought.

Requirements:

- bright but soft paper-like surfaces
- dark readable graph text
- graph card, controls, detail panel, and tooltip must remain legible
- Safari light mode must not fall back to dark low-contrast graph overlays

### Typography

Use:

- expressive display font for headings, e.g. Space Grotesk
- clean readable UI/body font, e.g. Source Sans 3

### Theme persistence

Persist theme selection in browser storage under:

- `association-rule-theme`

## Help modal

Create a searchable in-app Help modal with:

- topic list on the left
- content pane on the right
- search field filtering topics by title/content

The Help content must be comprehensive and in English. It should cover:

- overview
- quick start
- input format
- thresholds
- text filters
- running the analysis
- table and Top 20
- rule graph
- metrics
- output columns
- filter presets
- exports
- architecture
- persistence & privacy
- browser support & limits
- open-source / licensing
- version & contact

This Help content should broadly mirror the Markdown docs.

### Open-source / licensing help topic

This topic should not be generic. It should explicitly list the third-party components used
by the delivered project and state that no Python mining dependency is used in the HTML
version.

Include at least:

- the app itself as GPL-3.0
- `SheetJS / xlsx` via `xlsx.full.min.js` for Excel read/write
- `D3.js v7` via `d3.v7.min.js` for table/chart/graph rendering
- `Space Grotesk` and `Source Sans 3` as the main UI fonts if you load them
- an explicit note that **no mlxtend** is used in the HTML version

If vendored files contain upstream attribution banners, preserve them.

## Browser storage

Use browser storage for:

- filter presets
- sidebar collapsed state
- theme
- graph-only transient payload

Suggested keys:

- `association-rule-filter-presets-v1`
- `association-rule-sidebar-collapsed`
- `association-rule-theme`
- `association-graph-<timestamp>-<rand>`

## Safari / WebKit requirements

This section is critical. Do not ignore it.

The graph must render cleanly in Safari, especially in normal split view.

You must incorporate targeted WebKit-aware behavior:

1. Do not use live `backdrop-filter` overlays over the animating graph in Safari split view.
2. Keep Safari tooltip behavior lightweight.
3. Round cursor-following tooltip positions to integer pixels.
4. Round relevant Safari SVG transforms/coordinates where appropriate to reduce subpixel
   artifacts.
5. Use `shape-rendering: geometricPrecision` selectively for graph shapes and Top-20 bars.
6. Do not apply `crispEdges` or precision hints globally to everything, especially not in a
   way that harms text quality.
7. Avoid `foreignObject` in the graph.
8. Avoid promoting `#ruleGraph` itself to a composited layer.
9. In Safari split view, avoid simultaneous heavy recomposition of the graph and Top-20
   animation.
10. Keep hover-highlighting behavior conservative in split view if it triggers WebKit
    artifacts.

Also preserve these practical behaviors:

- Top-20 click should show the filtered graph immediately
- split-view graph rendering should avoid stale ghost pixels
- fullscreen and graph-only mode can remain richer/more isolated

## Required UX copy and naming

Use English throughout the UI except for filenames already present in the repository.

Required names include:

- `Association Rules Studio`
- `Console`
- `Table`
- `Graph & Top 20`
- `Run analysis`
- `Export all`
- `Output file name`
- `Confidence %`
- `Fullscreen`
- `New tab`
- `Export PNG`
- `Copy IDs`
- `Help`

For subtle credit/contact, include:

```text
In case of questions, contact Roland Emrich
```

Place it subtly, not as a loud hero element.

Also match these small but intentional project details:

- app title: `Association Rules Studio`
- version string: `v1.0`
- document title should include the version
- the sidebar credit line can include the version above the contact line

## Documentation requirements

Also create/update these files in English:

- `README.md`
- `AGENTS.md`
- `DESIGN.md`
- `DESCRIPTION.md`

They must reflect the actual delivered app, not a generic template.

### README.md

Should document:

- what the app is
- repo contents
- sample workbook and example exported preset JSON
- input format
- defaults
- workflow
- table/graph behavior
- filter presets
- exports
- metrics
- persistence
- Safari quirks
- development notes

### AGENTS.md

Should document:

- architecture
- file roles
- important constraints
- graph behavior
- Safari/WebKit gotchas
- state model
- doc-sync expectations

### DESIGN.md

Should document:

- design language
- layout
- themes
- graph-specific visuals
- Safari rendering constraints
- responsive behavior

### DESCRIPTION.md

Should be a concise but accurate project summary.

## Technical behavior details to preserve

Implement these details if you want the recreation to match closely:

- use one central mutable `state` object
- use explicit `render*()` functions rather than reactive framework state
- sort final rules primarily by confidence, then lift
- expose a `ready` pill state in the topbar
- auto-collapse sidebar 3 seconds after successful analysis
- use a green ready state only when idle
- clear/rebuild graph fully on each graph render
- persist sidebar collapsed state
- allow manual graph focus clearing by background click
- keep console/table/graph tabs visually distinct
- keep graph detail panel copy-friendly
- keep Top-20 interactions tightly integrated with graph filtering

## Deliverable quality bar

This should feel like a polished serious local analysis tool, not a quick demo.

The implementation should be:

- visually intentional
- behaviorally complete
- internally coherent
- documented
- browser-aware

## Acceptance checklist

Your result is only acceptable if all of the following are true:

1. The app runs locally from `index.html` with vendored D3 and SheetJS.
2. The UI is in English.
3. The app has Console, Table, and Graph & Top 20 tabs.
4. Apriori and rule generation are implemented in JavaScript, not delegated to Python.
5. Excel import and Excel export work.
6. Filter presets work through browser storage and JSON import/export.
7. The Top-20 chart is clickable and drives the graph.
8. The graph supports zoom, pan, drag, focus, fullscreen, new-tab mode, confidence labels,
   PNG export, and detail panel with copyable transaction IDs.
9. Multi-item itemsets render as touching multiple circles.
10. Dark theme and light theme both look deliberate and readable.
11. Safari split-view graph behavior is treated as a first-class constraint.
12. Markdown docs are created and aligned with the implementation.

## Execution instruction

Do not answer with a high-level explanation only. Implement the project files directly.

When done:

- ensure the HTML app is coherent
- ensure the docs match the app
- ensure the project still respects the no-build, no-framework, offline-first constraint
