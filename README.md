<!DOCTYPE html>

<title>Association Analysis (Apriori) GUI</title>
<style>
  :root { --fg:#222; --muted:#666; --bg:#fff; --border:#e5e7eb; }
  body { margin: 2rem; font-family: system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,Cantarell,"Helvetica Neue",Arial,"Noto Sans","Apple Color Emoji","Segoe UI Emoji"; color: var(--fg); background: var(--bg); line-height: 1.55; }
  h1, h2, h3 { line-height: 1.25; }
  h1 { font-size: 1.9rem; margin-bottom: .6rem; }
  h2 { font-size: 1.35rem; margin-top: 2rem; }
  h3 { font-size: 1.1rem; margin-top: 1.2rem; }
  p { margin: .6rem 0; }
  ul, ol { margin: .5rem 0 .8rem 1.4rem; }
  code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; }
  pre { background: #0b1020; color: #e6edf3; padding: 1rem; border-radius: .5rem; overflow: auto; }
  pre code { background: transparent; padding: 0; }
  code.inline { background: #f3f4f6; padding: .15rem .35rem; border-radius: .35rem; }
  blockquote { border-left: 4px solid var(--border); color: var(--muted); padding: .5rem 1rem; margin: 1rem 0; background: #fafafa; }
  table { width: 100%; border-collapse: collapse; margin: .8rem 0; }
  th, td { border: 1px solid var(--border); padding: .5rem .6rem; text-align: left; }
  thead th { background: #f8fafc; }
  .muted { color: var(--muted); }
  .kbd { border:1px solid var(--border); border-bottom-width:2px; padding:.05rem .35rem; border-radius:.25rem; background:#fafafa; font-family:inherit; }
</style>
</head>
<body>

<h1>Association Analysis (Apriori) GUI</h1>
<p>A desktop GUI (Tkinter) for mining association rules from Excel transaction data using <strong>mlxtend’s Apriori</strong> algorithm.
It reads transactions from Excel, computes frequent itemsets and association rules, lets you filter/sort results, and exports them back to Excel. Optional visualizations include a <strong>Top-20 combinations bar chart</strong> and a <strong>rule link graph</strong> (NetworkX).</p>

<h2>Features</h2>
<ul>
  <li>Apriori frequent itemset mining (configurable <code class="inline">min_support</code>, <code class="inline">min_confidence</code>)</li>
  <li>Simple Excel in → Excel out workflow</li>
  <li>Auto-maps items to “order numbers” and builds stable 8-digit combination IDs</li>
  <li>In-GUI filtering (exclude terms), column toggles for metrics, and sortable table</li>
  <li>Visualization:
    <ul>
      <li>Top 20 material combinations by <code class="inline">combination_count</code></li>
      <li>Directed rule link graph with confidence as edge weight</li>
    </ul>
  </li>
  <li>Save <strong>full</strong> or <strong>filtered</strong> results to <code class="inline">.xlsx</code> or <code class="inline">.csv</code></li>
</ul>

<h2>Demo</h2>
<ul>
  <li><strong>Main window</strong>: select input/output, set thresholds, run analysis, view results</li>
  <li><strong>Visualizations</strong>: Top-20 bar chart and confidence-weighted rule graph</li>
</ul>
<blockquote>
  <em>Add screenshots here later (optional).</em>
</blockquote>

<h2>Requirements</h2>
<ul>
  <li>Python 3.9+ (recommended)</li>
  <li>Packages:
    <ul>
      <li><code class="inline">pandas</code></li>
      <li><code class="inline">openpyxl</code> (for Excel I/O)</li>
      <li><code class="inline">mlxtend</code></li>
      <li><code class="inline">matplotlib</code></li>
      <li><code class="inline">networkx</code></li>
      <li><code class="inline">tkinter</code> (bundled on Windows/macOS; on some Linux distros install via system packages)</li>
    </ul>
  </li>
</ul>

<p>Install dependencies:</p>
<pre><code>pip install pandas openpyxl mlxtend matplotlib networkx
</code></pre>

<h2>Quick Start</h2>
<ol>
  <li><strong>Clone</strong> this repository and save the script as <code class="inline">app.py</code> (or keep your filename).</li>
  <li><strong>Prepare your Excel file</strong> (see <em>Input data format</em> below).</li>
  <li><strong>Run</strong>:</li>
</ol>

<pre><code>python app.py
</code></pre>

<p>In the GUI:</p>
<ul>
  <li>Choose <strong>Input file (Excel)</strong></li>
  <li>Choose <strong>Output file (Excel)</strong></li>
  <li>Set <strong>Min support</strong> and <strong>Min confidence</strong></li>
  <li>Click <strong>Run analysis</strong></li>
  <li>Use <strong>Show Top 20</strong> or <strong>Show graph</strong> for visuals</li>
  <li>Use <strong>Apply filter</strong> to exclude terms and <strong>Save filtered…</strong> to export your current view</li>
</ul>

<p class="muted">Default paths in the GUI are Windows examples (e.g., <code class="inline">C:\Assoziationsanalyse\SPC.xlsx</code>). You can change them via the file pickers.</p>

<h2>Input Data Format (Excel)</h2>
<p>Your <strong>first three columns</strong> must be:</p>
<ol>
  <li><strong>Transaction ID</strong> (e.g., order/visit/session)</li>
  <li><strong>Item</strong> (name/identifier)</li>
  <li><strong>Order number</strong> (used to build material combinations)</li>
</ol>

<table>
  <thead>
    <tr>
      <th>txn_id</th>
      <th>item</th>
      <th>order_no</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1001</td>
      <td>Monitor Color 19&quot; A</td>
      <td>08675402</td>
    </tr>
    <tr>
      <td>1001</td>
      <td>Cable Set X</td>
      <td>10410796</td>
    </tr>
    <tr>
      <td>1002</td>
      <td>Monitor Color 19&quot; A</td>
      <td>08675402</td>
    </tr>
  </tbody>
</table>

<ul>
  <li>The tool groups rows by <strong>Transaction ID</strong> into baskets of <strong>Items</strong>.</li>
  <li>A mapping from <strong>Item → Order number</strong> is built from the (item, order_no) pairs (deduplicated).</li>
</ul>

<h2>Outputs</h2>
<p>An Excel file with these columns (subset shown in the GUI can be toggled):</p>
<ul>
  <li><code class="inline">antecedents</code> – Left-hand side items (comma-separated)</li>
  <li><code class="inline">consequents</code> – Right-hand side items (comma-separated)</li>
  <li><code class="inline">support</code>, <code class="inline">confidence</code>, <code class="inline">lift</code>, <code class="inline">leverage</code>, <code class="inline">conviction</code>, <code class="inline">zhangs_metric</code></li>
  <li><code class="inline">combination_count</code> – Number of transactions containing <strong>all</strong> items in antecedents ∪ consequents</li>
  <li><code class="inline">Mat_combination</code> – Sorted, de-duplicated <strong>order_no</strong> combination joined by <code class="inline">-</code></li>
  <li><code class="inline">Mat_combination_id</code> – <strong>Stable 8-digit ID</strong> for that combination (SHA-256 → modulo 10^8, with leading zeros replaced by 9s)</li>
  <li><code class="inline">different items</code> – Count of distinct items in antecedents ∪ consequents</li>
</ul>

<h2>How It Works (High Level)</h2>
<ol>
  <li><strong>Load Excel</strong> and detect the first three columns as <em>id</em>, <em>item</em>, <em>order_no</em>.</li>
  <li><strong>Group</strong> rows by <em>id</em> into transactions (lists of items).</li>
  <li><strong>One-hot encode</strong> transactions with <code class="inline">TransactionEncoder</code>.</li>
  <li><strong>Mine</strong> frequent itemsets with <code class="inline">apriori(min_support=…)</code>.</li>
  <li><strong>Generate rules</strong> with <code class="inline">association_rules(min_threshold=min_confidence)</code>.</li>
  <li><strong>Compute</strong>:
    <ul>
      <li><code class="inline">combination_count</code> by counting rows matching all items of each rule</li>
      <li><code class="inline">Mat_combination</code> from mapped order numbers</li>
      <li><code class="inline">Mat_combination_id</code> via the hash function</li>
    </ul>
  </li>
  <li><strong>Render</strong> results in a sortable/filterable Tkinter table and <strong>export</strong> to Excel/CSV.</li>
  <li><strong>Visualize</strong> Top-20 and optional <strong>rule link graph</strong> (NetworkX + Matplotlib).</li>
</ol>

<h2>GUI Tips</h2>
<ul>
  <li><strong>Exclude terms</strong>: enter comma-separated substrings. Rows whose <strong>antecedents or consequents</strong> contain any term are hidden.</li>
  <li><strong>Visible metrics</strong>: toggle checkboxes to show/hide columns (confidence is always visible).</li>
  <li><strong>Sorting</strong>: click any table header; repeated clicks toggle ascending/descending.</li>
  <li><strong>Save filtered…</strong>: exports exactly what you see (current visible columns, current filter).</li>
</ul>

<h2>Error Handling</h2>
<ul>
  <li>Validates input file existence</li>
  <li>Validates that <code class="inline">min_support</code> and <code class="inline">min_confidence</code> are in <code class="inline">(0, 1]</code></li>
  <li>Requires at least <strong>3 columns</strong> in the Excel file</li>
  <li>Exceptions are shown via a message box and appended to the in-app <strong>Log</strong>.</li>
</ul>

<h2>Known Limitations</h2>
<ul>
  <li>The <strong>Item → Order number</strong> mapping assumes a consistent pairing in your dataset. If an item maps to multiple order numbers, the app will use what appears in the data (deduplicated per rule).</li>
  <li>Very large datasets may be slow due to one-hot encoding and rule generation.</li>
</ul>

<h2>Development Notes</h2>
<ul>
  <li>Main entry point: <code class="inline">if __name__ == "__main__": App().mainloop()</code></li>
  <li>Key modules:
    <ul>
      <li><code class="inline">mlxtend.frequent_patterns</code> (<code class="inline">apriori</code>, <code class="inline">association_rules</code>)</li>
      <li><code class="inline">TransactionEncoder</code></li>
      <li><code class="inline">networkx</code> for the rule graph</li>
      <li><code class="inline">matplotlib</code> for plots</li>
      <li><code class="inline">pandas</code>/<code class="inline">openpyxl</code> for I/O</li>
    </ul>
  </li>
  <li>The link graph scales node sizes by aggregated <code class="inline">combination_count</code> involvement.</li>
</ul>

<h2>License</h2>
<p>MIT — see <code class="inline">LICENSE</code> (feel free to replace with your preferred license).</p>

<h2>Acknowledgements</h2>
<ul>
  <li>Association Rule Mining via <a href="https://rasbt.github.io/mlxtend/" target="_blank" rel="noopener noreferrer">mlxtend</a> by Sebastian Raschka</li>
  <li>Network visualizations via NetworkX</li>
  <li>GUI built with Tkinter</li>
</ul>

</body>
</html>
