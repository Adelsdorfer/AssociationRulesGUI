# Association Rules Studio — v1.0

Association Rules Studio is a single-file, fully client-side web application for
association-rule mining on Excel workbooks.

It reads transaction/item/order data from `.xlsx` or `.xls`, mines frequent itemsets with
Apriori, builds association rules in plain JavaScript, and presents the results in three
views:

- a Console tab for runtime logging,
- a sortable/filterable Table tab,
- a Graph & Top 20 tab with a weighted cost chart and an interactive D3 rule network.

The application is the browser counterpart to `AssociationRulesGUI.py`, but it does not use
`mlxtend` or any Python runtime. The full app lives in `index.html`, supported by vendored
copies of D3.js and SheetJS.

Key capabilities:

- configurable support, confidence, and itemset-size thresholds
- cost-aware metrics and weighted consequent-cost ranking
- click-through from Top 20 into the graph
- node/edge detail panel with copyable transaction IDs
- fullscreen graph, graph-only new-tab mode, and PNG export
- filter presets stored in the browser plus JSON export/import
- searchable in-app Help and dark/light themes

All processing happens locally in the browser.
