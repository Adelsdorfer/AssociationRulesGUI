Association Analysis (Apriori) GUI

A desktop GUI (Tkinter) for mining association rules from Excel transaction data using mlxtend’s Apriori algorithm.
It reads transactions from Excel, computes frequent itemsets and association rules, lets you filter/sort results, and exports them back to Excel. Optional visualizations include a Top-20 combinations bar chart and a rule link graph (NetworkX).

Features

🧮 Apriori frequent itemset mining (configurable min_support, min_confidence)

📁 Simple Excel in → Excel out workflow

🧷 Auto-maps items to “order numbers” and builds stable 8-digit combination IDs

🔎 In-GUI filtering (exclude terms), column toggles for metrics, and sortable table

📊 Visualization:

Top 20 material combinations by combination_count

Directed rule link graph with confidence as edge weight

💾 Save full or filtered results to .xlsx or .csv

Demo

Main window: select input/output, set thresholds, run analysis, view results

Visualizations: Top-20 bar chart and confidence-weighted rule graph

Add screenshots here later (optional).

Requirements

Python 3.9+ (recommended)

Packages:

pandas

openpyxl (for Excel I/O)

mlxtend

matplotlib

networkx

tkinter (bundled with most Python installs on Windows/macOS; on some Linux distros install via system packages)

Install deps:

pip install pandas openpyxl mlxtend matplotlib networkx

Quick Start

Clone this repository and save the script as app.py (or keep your filename).

Prepare your Excel file (see Input data format below).

Run:

python app.py


In the GUI:

Choose Input file (Excel)

Choose Output file (Excel)

Set Min support and Min confidence

Click Run analysis

Use Show Top 20 or Show graph for visuals

Use Apply filter to exclude terms and Save filtered… to export your current view

Default paths in the GUI are Windows examples (e.g., C:\Assoziationsanalyse\SPC.xlsx). You can change them via the file pickers.

Input Data Format (Excel)

Your first three columns must be:

Transaction ID (e.g., order/visit/session)

Item (name/identifier)

Order number (used to build material combinations)

Example (first three columns only):

txn_id	item	order_no
1001	Monitor Color 19" A	08675402
1001	Cable Set X	10410796
1002	Monitor Color 19" A	08675402

The tool groups rows by Transaction ID into baskets of Items.

A mapping from Item → Order number is built from the (item, order_no) pairs (deduplicated).

Outputs

An Excel file with these columns (subset shown in the GUI can be toggled):

antecedents – Left-hand side items (comma-separated)

consequents – Right-hand side items (comma-separated)

support, confidence, lift, leverage, conviction, zhangs_metric

combination_count – Number of transactions containing all items in antecedents ∪ consequents

Mat_combination – Sorted, de-duplicated order_no combination joined by -
(derived via the Item → Order number map)

Mat_combination_id – Stable 8-digit ID for that combination (SHA-256 → modulo 10^8, with leading zeros replaced by 9s)

different items – Count of distinct items in antecedents ∪ consequents

How It Works (High Level)

Load Excel and detect the first three columns as id, item, order_no.

Group rows by id into transactions (lists of items).

One-hot encode transactions with TransactionEncoder.

Mine frequent itemsets with apriori(min_support=…).

Generate rules with association_rules(min_threshold=min_confidence).

Compute:

combination_count by counting rows matching all items of each rule

Mat_combination from mapped order numbers

Mat_combination_id via the hash function

Render results in a sortable/filterable Tkinter table and export to Excel/CSV.

Visualize Top-20 and optional rule link graph (NetworkX + Matplotlib).

GUI Tips

Exclude terms: enter comma-separated substrings. Rows whose antecedents or consequents contain any term are hidden.

Visible metrics: toggle checkboxes to show/hide columns (confidence is always visible).

Sorting: click any table header; repeated clicks toggle ascending/descending.

Save filtered…: exports exactly what you see (current visible columns, current filter).

Error Handling

The app validates:

Input file existence

min_support and min_confidence in (0, 1]

Presence of at least 3 columns in the Excel file

Exceptions are shown via a message box and appended to the in-app Log.

Known Limitations

The Item → Order number mapping assumes a consistent pairing in your dataset. If an item maps to multiple order numbers, the app will use what appears in the data (deduplicated per rule).

Very large datasets may be slow due to one-hot encoding and rule generation.

Development Notes

Main entry point: if __name__ == "__main__": App().mainloop()

Key modules used:

mlxtend.frequent_patterns (apriori, association_rules)

TransactionEncoder

networkx for the rule graph

matplotlib for plots

pandas/openpyxl for I/O

The link graph scales node sizes by aggregated combination_count involvement.

License

MIT — see LICENSE (feel free to replace with your preferred license).

Acknowledgements

Association Rule Mining via mlxtend
 by Sebastian Raschka

Network visualizations via NetworkX

GUI built with Tkinter
