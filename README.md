# Association Analysis (Apriori) GUI

A desktop GUI (Tkinter) for mining association rules from Excel transaction data using **mlxtend’s Apriori** algorithm.  
It reads transactions from Excel, computes frequent itemsets and association rules, lets you filter/sort results, and exports them back to Excel. Optional visualizations include a **Top-20 combinations bar chart** and a **rule link graph** (NetworkX).

## Features

- 🧮 Apriori frequent itemset mining (configurable `min_support`, `min_confidence`)
- 📁 Simple Excel in → Excel out workflow
- 🧷 Auto-maps items to “order numbers” and builds stable 8-digit combination IDs
- 🔎 In-GUI filtering (exclude terms), column toggles for metrics, and sortable table
- 📊 Visualization:
  - Top 20 material combinations by `combination_count`
  - Directed rule link graph with confidence as edge weight
- 💾 Save **full** or **filtered** results to `.xlsx` or `.csv`

## Demo

- **Main window**: select input/output, set thresholds, run analysis, view results
- **Visualizations**: Top-20 bar chart and confidence-weighted rule graph

> _Add screenshots here later (optional)._

## Requirements

- Python 3.9+ (recommended)
- Packages:
  - `pandas`
  - `openpyxl` (for Excel I/O)
  - `mlxtend`
  - `matplotlib`
  - `networkx`
  - `tkinter` (bundled on Windows/macOS; on some Linux distros install via system packages)

Install dependencies:

```bash
pip install pandas openpyxl mlxtend matplotlib networkx
