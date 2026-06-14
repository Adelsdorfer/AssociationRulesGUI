# DESIGN.md

Design system and visual implementation notes for `index.html`.

## Visual direction

Association Rules Studio uses a dark "Deep Space" visual system:

- deep indigo-black backgrounds
- layered nebula gradients
- subtle starfield texture
- glowing violet/cyan accents
- glass-like panels

The app also has a light theme, but the dark theme is the primary visual reference.

## Typography

- Display/headings: `Space Grotesk`
- Body/UI: `Source Sans 3`
- Monospace areas: `ui-monospace, SFMono-Regular, Menlo, Consolas`

The fonts are loaded from Google Fonts. Everything else is local.

## Design tokens

The CSS is token-driven via `:root`.

Primary tokens:

- `--ink`
- `--muted`
- `--bg`
- `--surface`
- `--surface-strong`
- `--line`
- `--line-strong`
- `--pine`
- `--moss`
- `--saffron`
- `--clay`
- `--blue`
- `--shadow`
- `--glow`
- `--radius-lg`
- `--radius-md`
- `--radius-sm`

Most non-graph UI retheming should happen by changing tokens first.

## Theme behavior

The theme toggle switches between dark and light mode by applying
`data-theme="light"` on the root element.

Dark theme:

- cosmic background gradients
- visible starfield
- frosted dark surfaces
- luminous accent controls

Light theme:

- bright paper-like surfaces
- removed starfield
- darker text and adjusted accent shades

Graph/chart text colors are partly theme-aware through the `chartInk()` helper in
JavaScript, not purely through CSS tokens.

## Layout

### App shell

- `.app-shell` is a two-column grid on desktop:
  - sidebar
  - workspace
- below `1180px`, it collapses to one column

### Sidebar

- sticky on large screens
- scrollable
- collapsible to icon width
- auto-collapses after a successful run

### Workspace

`.workspace` is the core right-side container and currently uses:

- `grid-template-rows: auto auto minmax(0, 1fr)`
- fixed viewport-relative height for stable split-view sizing

That row structure is important:

1. topbar
2. tabs
3. active panel

Do not move the expanding `minmax(0, 1fr)` row away from the panel area.

### Tabs and panels

Tabs:

- `Console`
- `Table`
- `Graph & Top 20`

Only `.panel.active` is displayed.

### Graph split layout

The graph panel contains `.chart-grid`, a two-column layout:

- left card: Top 20 weighted consequent costs
- right card: Rule Network

Desktop split view stretches the cards to the available workspace height. Mobile/narrow
layouts stack them vertically.

## Components

### Panels and cards

General panels use:

- translucent surfaces
- thin borders
- large radii
- strong shadow depth

### Pills and chips

Used for:

- version
- status
- stat chips
- filter counts
- graph status

They are rounded, compact, and use `--surface-strong`.

### Buttons

- Primary: violet/indigo emphasis
- Warm: gold emphasis
- Secondary: subdued glass action
- Graph actions: compact pill buttons on the graph card

### Console

The Console tab uses a near-black monospace surface designed to feel like a runtime log,
not a generic textarea.

### Help modal

The Help modal is a two-pane searchable knowledge panel:

- topic list on the left
- article body on the right

Its content mirrors the project documentation and should remain visually consistent with
the app theme in both dark and light modes.

## Graph-specific design

### Top 20 chart

- horizontal bars
- violet-to-cyan gradient
- click-through behavior into the graph
- replayed width animation on combination selection

### Rule graph

- D3 force-directed SVG
- confidence-driven edge color
- combination-count-driven edge width
- node-size scaling by visibility/frequency
- multi-item itemsets shown as touching multiple circles

### Graph detail surfaces

There are three separate surfaces around the graph:

1. transient hover tooltip
2. fixed detail panel
3. floating bottom controls

These are visually related but not technically interchangeable. The tooltip must stay very
lightweight because it moves often; the detail panel can be richer because it is static once
opened.

## Safari / WebKit rendering notes

This is the most sensitive design/implementation area in the project.

Current rules:

- In normal split view, Safari should not render live `backdrop-filter` overlays over the
  animating graph.
- Tooltip behavior is intentionally simplified in Safari.
- Split-view graph auto-resize is effectively disabled; resize observation is reserved for
  fullscreen and graph-only contexts.
- Split-view graph rendering and Top-20 animation are sequenced carefully to reduce
  WebKit compositing artifacts.

These are not cosmetic preferences. They are stability constraints.

## Motion

Motion is used deliberately:

- sidebar auto-collapse after successful runs
- Top-20 bar animation
- spinner during work
- starfield twinkle in dark mode
- tooltip fade

Respect `prefers-reduced-motion` when adding new motion.

## Responsive behavior

### Up to 1180px

- sidebar becomes non-sticky
- chart-grid stacks into one column

### Up to 720px

- topbar content stacks
- controls compress to one column
- graph area is reduced to a more manageable mobile height

## Retheming checklist

When changing the visual language:

1. update CSS tokens first
2. review hardcoded CSS colors
3. review D3-injected colors in JavaScript
4. review dark/light chart text via `chartInk()`
5. check graph control readability
6. verify Safari split view still behaves

## Documentation sync

If the visual or layout behavior changes materially, update:

- this `DESIGN.md`
- `README.md`
- relevant `helpTopics` content in `index.html`
