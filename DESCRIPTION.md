# Association Rules Studio — v1.0

**Association Rules Studio** is a single-file, fully client-side web app for
**market-basket / association-rule mining** on Excel data. Load a workbook, mine frequent
itemsets with **Apriori**, generate association rules with a full suite of interestingness
metrics, and explore everything through a sortable table, a Top-20 cost chart, and an
interactive force-directed rule network — all in a dark "deep space" UI.

It is a browser port of the Python tool `AssociationRulesGUI.py`: **no server, no build
step, no installation, and no `mlxtend` dependency**. Apriori, frequent-itemset generation,
and rule generation are implemented from scratch in plain JavaScript. Open `index.html` and
it runs, fully offline.

## Highlights

- **Zero install, fully offline** — one `index.html` plus two vendored libraries (SheetJS, D3).
- **Excel in, Excel out** — read `.xlsx`/`.xls`, export rules back to `.xlsx`.
- **From-scratch Apriori** with configurable support, confidence, and max itemset size.
- **Full metric suite** — support, confidence, lift, leverage, conviction, Zhang's metric,
  combination count, plus cost-based metrics.
- **Interactive results** — sortable/searchable table, Top-20 cost chart, and a zoomable,
  draggable rule graph with PNG export.
- **Filter presets** — save, load, and share reusable filter configurations.
- **Privacy first** — all processing happens locally; your data never leaves the browser.

## Version 1.0

This is the **initial public release**. Licensed under **GPL-3.0**.
