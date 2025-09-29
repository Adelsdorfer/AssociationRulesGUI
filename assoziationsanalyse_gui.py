import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
import hashlib
import re
import os
import traceback
import sys
 
 

plt.rcParams['figure.autolayout'] = True


def create_unique_8digit_id(combination_string: str) -> str:
    sha_value = hashlib.sha256(combination_string.encode("utf-8")).hexdigest()
    hash_int = int(sha_value, 16)
    mod_value = hash_int % 10 ** 8
    mod_str = str(mod_value).zfill(8)
    mod_str = re.sub(r'^(0+)', lambda m: '9' * len(m.group(1)), mod_str)
    return mod_str


def run_analysis(input_path: str, output_path: str, min_support: float, min_confidence: float, show_graph: bool, log, on_results=None):
    def log_print(msg):
        log.configure(state="normal")
        log.insert("end", msg + "\n")
        log.see("end")
        log.configure(state="disabled")
        log.update_idletasks()

    try:
        log_print(f"Reading Excel file: {input_path}")
        df = pd.read_excel(input_path, engine='openpyxl')

        if df.shape[1] < 3:
            raise ValueError("The Excel file must contain at least three columns (e.g., transaction ID, item, order number).")

        id_column = df.columns[0]
        item_column = df.columns[1]
        bestellnummer_column = df.columns[2]

        log_print(f"Detected columns -> ID: {id_column}, Item: {item_column}, Order no.: {bestellnummer_column}")

        unique_items = df[[item_column, bestellnummer_column]].drop_duplicates()
        item_bestell_map = dict(zip(unique_items[item_column], unique_items[bestellnummer_column]))

        grouped = df.groupby(id_column)[item_column].apply(
            lambda x: [str(item).strip() for item in x if pd.notna(item)]
        ).reset_index(name='Items')

        transactions = grouped['Items'].tolist()
        if not transactions:
            raise ValueError("No transactions found. Please check your data.")

        log_print("Transforming transactions (one-hot encoding)")
        te = TransactionEncoder()
        te_ary = te.fit(transactions).transform(transactions)
        df_transformed = pd.DataFrame(te_ary, columns=te.columns_)

        log_print(f"Mining frequent itemsets (min_support={min_support})")
        frequent_itemsets = apriori(df_transformed, min_support=min_support, use_colnames=True)

        log_print(f"Generating association rules (min_confidence={min_confidence})")
        rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)

        if rules.empty:
            log_print("No rules found with the selected thresholds.")
        else:
            log_print(f"Rules found: {len(rules)}")

        # combination_count
        log_print("Calculating combination_count")
        rules['combination_count'] = rules.apply(
            lambda row: df_transformed.loc[
                  (df_transformed[list(row['antecedents'])].all(axis=1)) &
                  (df_transformed[list(row['consequents'])].all(axis=1))
            ].shape[0],
            axis=1
        )

        # Mat_combination
        log_print("Creating Mat_combination and ID")

        def get_mat_combination(row):
            items_in_rule = row['antecedents'].union(row['consequents'])
            bestellnummern = []
            for item in items_in_rule:
                if item in item_bestell_map:
                    bestellnummern.append(str(item_bestell_map[item]))
            bestellnummern = sorted(set(bestellnummern))
            return '-'.join(bestellnummern)

        rules['Mat_combination'] = rules.apply(get_mat_combination, axis=1)
        rules['Mat_combination_id'] = rules['Mat_combination'].apply(create_unique_8digit_id)

        # different items
        rules['different items'] = rules.apply(
            lambda row: len(row['antecedents'].union(row['consequents'])),
            axis=1
        )

        # Sets zu Strings
        rules['antecedents'] = rules['antecedents'].apply(lambda x: ', '.join(sorted(list(x))))
        rules['consequents'] = rules['consequents'].apply(lambda x: ', '.join(sorted(list(x))))

        # Export
        rules_export = rules[[
            'antecedents',
            'consequents',
            'support',
            'confidence',
            'lift',
            'leverage',
            'conviction',
            'zhangs_metric',
            'combination_count',
            'Mat_combination',
            'Mat_combination_id',
            'different items'
        ]]

        out_dir = os.path.dirname(output_path) or "."
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        log_print(f"Exporting to: {output_path}")
        rules_export.to_excel(output_path, index=False)
        log_print("Export completed.")

        # Callback with results for UI table
        if on_results is not None:
            try:
                on_results(rules_export)
            except Exception:
                pass

        # Optional: directed rule graph (confidence as weight)
        if show_graph and not rules.empty:
            log_print("Creating link graph...")
            G = nx.DiGraph()

            # Kanten hinzufügen
            for _, row in rules.iterrows():
                G.add_edge(
                    row['antecedents'],
                    row['consequents'],
                    weight=row['confidence'],
                    combination_count=row['combination_count']
                )

            node_sizes = {}
            for node in G.nodes():
                total_count = rules.apply(
                    lambda row: row['combination_count']
                    if (node in row['antecedents']) or (node in row['consequents'])
                    else 0,
                    axis=1
                ).sum()
                node_sizes[node] = total_count

            min_size = 300
            max_size = 3000
            counts = list(node_sizes.values())
            if counts:
                min_count = min(counts)
                max_count = max(counts)
                if max_count == min_count:
                    scaled_sizes = {node: (min_size + max_size) / 2 for node in node_sizes}
                else:
                    scaled_sizes = {
                        node: min_size + (size - min_count) / (max_count - min_count) * (max_size - min_size)
                        for node, size in node_sizes.items()
                    }
            else:
                scaled_sizes = {node: min_size for node in node_sizes}

            pos = nx.spring_layout(G, dim=2, k=0.3, scale=20.0, center=None, iterations=100)
            edges = G.edges(data=True)

            nx.draw_networkx_edges(
                G, pos, edgelist=edges, arrowstyle='-|>', arrowsize=7,
                edge_color=[d['weight'] for (u, v, d) in edges],
                edge_cmap=plt.cm.Blues, width=2
            )
            nx.draw_networkx_nodes(
                G, pos,
                node_size=[scaled_sizes[node] for node in G.nodes()],
                node_color='skyblue'
            )
            nx.draw_networkx_labels(G, pos, font_size=9, font_color='purple')
            edge_labels = {(u, v): f"{d['weight']:.2f}" for u, v, d in G.edges(data=True)}
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red', font_size=8)

            plt.title('Assoziationsregeln Link-Graph (basierend auf Konfidenzniveau)')
            plt.axis('off')
            plt.show()


        log_print(f"Done: Association rules exported to: {output_path}")

    except Exception as e:
        err = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        log_print("ERROR:\n" + err)
        messagebox.showerror("Error", str(e))


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Association Analysis (Apriori) – GUI")
        self.geometry("1800x950")
        self._apply_theme()

        self.input_path = tk.StringVar(value=r"C:\\Assoziationsanalyse\\SPC.xlsx")
        self.output_path = tk.StringVar(value=r"C:\\Assoziationsanalyse\\SPC_Regeln.xlsx")
        self.min_support = tk.StringVar(value="0.001")
        self.min_confidence = tk.StringVar(value="0.15")
        self.show_graph = tk.BooleanVar(value=False)

        # Data storage for results
        self._rules_df = None           # full results DataFrame
        self._filtered_df = None        # filtered view
        self._sort_state = {}           # column -> ascending bool

        self._build()

    def _build(self):
        pad = {"padx": 8, "pady": 6}

        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True, **pad)

        # Input file
        ttk.Label(frm, text="Input file (Excel):").grid(row=0, column=0, sticky="w")
        ent_in = ttk.Entry(frm, textvariable=self.input_path, width=70)
        ent_in.grid(row=0, column=1, sticky="we", **pad)
        ttk.Button(frm, text="Browse...", command=self.browse_input).grid(row=0, column=2, **pad)

        # Output file
        ttk.Label(frm, text="Output file (Excel):").grid(row=1, column=0, sticky="w")
        ent_out = ttk.Entry(frm, textvariable=self.output_path, width=70)
        ent_out.grid(row=1, column=1, sticky="we", **pad)
        ttk.Button(frm, text="Save as...", command=self.browse_output).grid(row=1, column=2, **pad)

        # Params
        ttk.Label(frm, text="Min support:").grid(row=2, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.min_support, width=15).grid(row=2, column=1, sticky="w", **pad)

        ttk.Label(frm, text="Min confidence:").grid(row=3, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.min_confidence, width=15).grid(row=3, column=1, sticky="w", **pad)

        # Action buttons
        actions = ttk.Frame(frm, style="App.TFrame")
        actions.grid(row=5, column=1, sticky="w", **pad)
        ttk.Button(actions, text="Run analysis", style="Primary.TButton", command=self.on_run).pack(side="left", padx=3)
        ttk.Button(actions, text="Show Top 20", style="Accent.TButton", command=self.show_top20).pack(side="left", padx=3)
        ttk.Button(actions, text="Show graph", style="Accent.TButton", command=self.show_rule_graph).pack(side="left", padx=3)

        # Log
        ttk.Label(frm, text="Log:").grid(row=6, column=0, sticky="nw")
        self.txt_log = tk.Text(frm, height=10, state="disabled", bg="#D9ECFF", fg="#0F1C2E")
        self.txt_log.grid(row=6, column=1, columnspan=2, sticky="nsew", **pad)

        # Results filter controls
        ttk.Label(frm, text="Exclude (terms, comma-separated):").grid(row=7, column=0, sticky="w")
        self.exclude_entry = ttk.Entry(frm)
        self.exclude_entry.grid(row=7, column=1, sticky="we", **pad)
        btns = ttk.Frame(frm, style="App.TFrame")
        btns.grid(row=7, column=2, sticky="e", **pad)
        ttk.Button(btns, text="Apply filter", style="Accent.TButton", command=self.apply_filter).pack(side="left", padx=3)
        ttk.Button(btns, text="Reset", style="Accent.TButton", command=self.reset_filter).pack(side="left", padx=3)
        ttk.Button(btns, text="Save filtered...", style="Accent.TButton", command=self.save_filtered).pack(side="left", padx=3)

        # Metric column toggles (confidence always visible)
        toggles = ttk.Labelframe(frm, text="Visible metrics", style="App.TLabelframe")
        toggles.grid(row=8, column=1, columnspan=2, sticky="we", **pad)
        self.metric_vars = {
            'support': tk.BooleanVar(value=False),
            'lift': tk.BooleanVar(value=False),
            'leverage': tk.BooleanVar(value=False),
            'conviction': tk.BooleanVar(value=False),
            'zhangs_metric': tk.BooleanVar(value=False),
            'combination_count': tk.BooleanVar(value=False),
            'Mat_combination': tk.BooleanVar(value=False),
            'Mat_combination_id': tk.BooleanVar(value=False),
            'different items': tk.BooleanVar(value=False),
        }
        # Arrange checkboxes in a grid
        row_i, col_i = 0, 0
        for key, label in [
            ('support', 'Support'),
            ('lift', 'Lift'),
            ('leverage', 'Leverage'),
            ('conviction', 'Conviction'),
            ('zhangs_metric', 'Zhangs Metric'),
            ('combination_count', 'Combination Count'),
            ('Mat_combination', 'Mat_combination'),
            ('Mat_combination_id', 'Mat_combination_id'),
            ('different items', 'Different Items'),
        ]:
            cb = ttk.Checkbutton(toggles, text=label, variable=self.metric_vars[key], command=self.update_visible_columns)
            cb.grid(row=row_i, column=col_i, padx=6, pady=4, sticky="w")
            col_i += 1
            if col_i >= 3:
                col_i = 0
                row_i += 1

        # Results table
        ttk.Label(frm, text="Results:").grid(row=9, column=0, sticky="nw")
        self.tree = ttk.Treeview(frm, columns=(
            'antecedents','consequents','support','confidence','lift','leverage','conviction','zhangs_metric',
            'combination_count','Mat_combination','Mat_combination_id','different items'
        ), show='headings', height=10)

        # Define headings with sort commands
        for col, text in [
            ('antecedents','Antecedents'),('consequents','Consequents'),('support','Support'),('confidence','Confidence'),
            ('lift','Lift'),('leverage','Leverage'),('conviction','Conviction'),('zhangs_metric','Zhangs Metric'),
            ('combination_count','Combination Count'),('Mat_combination','Mat_combination'),('Mat_combination_id','Mat_combination_id'),
            ('different items','Different Items')
        ]:
            self.tree.heading(col, text=text, command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=120, stretch=True)

        # Scrollbars
        vsb = ttk.Scrollbar(frm, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(frm, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=9, column=1, columnspan=1, sticky="nsew", **pad)
        vsb.grid(row=9, column=2, sticky="ns")
        hsb.grid(row=10, column=1, sticky="we", **pad)

        # Footer / Copyright
        footer = ttk.Label(frm, text="© Roland Emrich", foreground="#333333", background="#D9ECFF")
        footer.grid(row=11, column=1, sticky="e", **pad)

        # Resizing behavior
        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(6, weight=0)
        frm.rowconfigure(9, weight=1)

    def _apply_theme(self):
        base_bg = "#D9ECFF"  # light blue
        base_fg = "#0F1C2E"
        accent = "#FFA500"   # orange
        primary = "#E53935"  # red

        # Root bg
        self.configure(bg=base_bg)

        style = ttk.Style(self)
        try:
            # Use default theme as base
            current = style.theme_use()
        except Exception:
            pass

        # General backgrounds
        style.configure("TFrame", background=base_bg)
        style.configure("App.TFrame", background=base_bg)
        style.configure("TLabel", background=base_bg, foreground=base_fg)
        style.configure("TLabelframe", background=base_bg, foreground=base_fg)
        style.configure("App.TLabelframe", background=base_bg, foreground=base_fg)
        style.configure("TLabelframe.Label", background=base_bg, foreground=base_fg)

        # Buttons (always black text)
        style.configure("TButton", background=base_bg, foreground="#000000", padding=6)
        style.map("TButton",
                  background=[('active', '#CBE5FF')],
                  foreground=[('active', '#000000'), ('pressed', '#000000')])
        style.configure("Accent.TButton", background=accent, foreground="#000000")
        style.map("Accent.TButton",
                  background=[('active', '#FFB347')],
                  foreground=[('active', '#000000'), ('pressed', '#000000')])
        style.configure("Primary.TButton", background=primary, foreground="#000000")
        style.map("Primary.TButton",
                  background=[('active', '#EF5350')],
                  foreground=[('active', '#000000'), ('pressed', '#000000')])

        # Checkbuttons (label background light blue)
        style.configure("TCheckbutton", background=base_bg, foreground=base_fg)

        # Treeview colors
        style.configure("Treeview",
                        background="#EFF7FF",
                        fieldbackground="#EFF7FF",
                        foreground=base_fg)
        style.configure("Treeview.Heading", background="#BFE2FF", foreground=base_fg)

    def browse_input(self):
        path = filedialog.askopenfilename(
            title="Eingabedatei wählen",
            filetypes=[("Excel-Dateien", "*.xlsx *.xls"), ("Alle Dateien", "*.*")]
        )
        if path:
            self.input_path.set(path)

    def browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Ausgabedatei wählen",
            defaultextension=".xlsx",
            filetypes=[("Excel-Datei", "*.xlsx")]
        )
        if path:
            self.output_path.set(path)

    def on_run(self):
        try:
            input_path = self.input_path.get().strip()
            output_path = self.output_path.get().strip()
            min_support = float(self.min_support.get().strip().replace(",", "."))
            min_confidence = float(self.min_confidence.get().strip().replace(",", "."))

            if not os.path.isfile(input_path):
                messagebox.showwarning("Notice", "Input file does not exist.")
                return
            if not (0 < min_support <= 1):
                messagebox.showwarning("Notice", "Min support must be between 0 and 1.")
                return
            if not (0 < min_confidence <= 1):
                messagebox.showwarning("Notice", "Min confidence must be between 0 and 1.")
                return

            run_analysis(
                input_path=input_path,
                output_path=output_path,
                min_support=min_support,
                min_confidence=min_confidence,
                show_graph=False,
                log=self.txt_log,
                on_results=self.on_results_ready
            )
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values for support/confidence.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # Results handling
    def on_results_ready(self, df: pd.DataFrame):
        self._rules_df = df.copy()
        self._filtered_df = df.copy()
        self._sort_state = {}
        self.refresh_table()

    def get_exclude_terms(self):
        raw = self.exclude_entry.get().strip()
        if not raw:
            return []
        return [t.strip().lower() for t in raw.split(',') if t.strip()]

    def apply_filter(self):
        if self._rules_df is None:
            return
        terms = self.get_exclude_terms()
        if not terms:
            self._filtered_df = self._rules_df.copy()
        else:
            def exclude_row(row):
                a = str(row['antecedents']).lower()
                c = str(row['consequents']).lower()
                return any(term in a or term in c for term in terms)
            mask = self._rules_df.apply(exclude_row, axis=1)
            self._filtered_df = self._rules_df.loc[~mask].copy()
        self.refresh_table()

    def reset_filter(self):
        self.exclude_entry.delete(0, 'end')
        if self._rules_df is not None:
            self._filtered_df = self._rules_df.copy()
            self._sort_state = {}
            self.refresh_table()

    def refresh_table(self):
        # Clear
        for i in self.tree.get_children():
            self.tree.delete(i)
        if self._filtered_df is None or self._filtered_df.empty:
            return
        # Determine visible columns
        cols = self.current_visible_columns()
        # Ensure tree shows correct columns and headings
        self.tree['columns'] = cols
        for c in cols:
            # Re-set heading to keep sort handler
            nice = {
                'antecedents': 'Antecedents', 'consequents': 'Consequents', 'support': 'Support', 'confidence': 'Confidence',
                'lift': 'Lift', 'leverage': 'Leverage', 'conviction': 'Conviction', 'zhangs_metric': 'Zhangs Metric',
                'combination_count': 'Combination Count', 'Mat_combination': 'Mat_combination', 'Mat_combination_id': 'Mat_combination_id',
                'different items': 'Different Items'
            }[c]
            self.tree.heading(c, text=nice, command=lambda cc=c: self.sort_by_column(cc))
            self.tree.column(c, width=120, stretch=True)
        # Insert rows
        for _, row in self._filtered_df.iterrows():
            row_map = {
                'antecedents': row['antecedents'],
                'consequents': row['consequents'],
                'support': f"{row['support']:.6f}" if pd.notna(row['support']) else "",
                'confidence': f"{row['confidence']:.6f}" if pd.notna(row['confidence']) else "",
                'lift': f"{row['lift']:.6f}" if pd.notna(row['lift']) else "",
                'leverage': f"{row['leverage']:.6f}" if pd.notna(row['leverage']) else "",
                'conviction': f"{row['conviction']:.6f}" if pd.notna(row['conviction']) else "",
                'zhangs_metric': f"{row['zhangs_metric']:.6f}" if pd.notna(row['zhangs_metric']) else "",
                'combination_count': int(row['combination_count']) if pd.notna(row['combination_count']) else "",
                'Mat_combination': row['Mat_combination'],
                'Mat_combination_id': row['Mat_combination_id'],
                'different items': int(row['different items']) if pd.notna(row['different items']) else "",
            }
            values = [row_map[c] for c in cols]
            self.tree.insert('', 'end', values=values)

    def sort_by_column(self, column):
        if self._filtered_df is None or self._filtered_df.empty:
            return
        ascending = self._sort_state.get(column, True)
        # Choose dtype-aware sorting
        try:
            if column in {'support','confidence','lift','leverage','conviction','zhangs_metric'}:
                self._filtered_df[column] = pd.to_numeric(self._filtered_df[column], errors='coerce')
            elif column in {'combination_count','different items'}:
                self._filtered_df[column] = pd.to_numeric(self._filtered_df[column], errors='coerce').astype('Int64')
        except Exception:
            pass
        self._filtered_df = self._filtered_df.sort_values(by=column, ascending=ascending, kind='mergesort')
        self._sort_state[column] = not ascending
        self.refresh_table()

    def save_filtered(self):
        if self._filtered_df is None or self._filtered_df.empty:
            messagebox.showinfo("Info", "No filtered results to save.")
            return
        cols = self.current_visible_columns()
        # Guard missing columns in df
        cols = [c for c in cols if c in self._filtered_df.columns]
        if not cols:
            messagebox.showinfo("Info", "No visible columns to save.")
            return
        df = self._filtered_df[cols].copy()
        path = filedialog.asksaveasfilename(
            title="Save filtered results",
            defaultextension=".xlsx",
            filetypes=[("Excel file", "*.xlsx"), ("CSV file", "*.csv")]
        )
        if not path:
            return
        try:
            if path.lower().endswith('.csv'):
                df.to_csv(path, index=False, encoding='utf-8-sig')
            else:
                df.to_excel(path, index=False)
            messagebox.showinfo("Saved", f"Filtered results saved to: {path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def current_visible_columns(self):
        # Confidence is always visible; antecedents/consequents always visible
        cols = ['antecedents', 'consequents', 'confidence']
        for key, var in self.metric_vars.items():
            if var.get():
                cols.append(key)
        # Ensure unique order (dict preserves order already)
        seen = set()
        ordered = []
        for c in cols:
            if c not in seen:
                seen.add(c)
                ordered.append(c)
        return ordered

    def update_visible_columns(self):
        # Just refresh table with new column set
        self.refresh_table()

    def show_top20(self):
        if self._rules_df is None or self._rules_df.empty:
            messagebox.showinfo("Info", "No results available. Run analysis first.")
            return
        try:
            df = self._rules_df
            if 'combination_count' not in df.columns:
                messagebox.showinfo("Info", "'combination_count' not available.")
                return
            top = df.sort_values('combination_count', ascending=False).head(20).copy()
            if top.empty:
                messagebox.showinfo("Info", "No data for Top 20 chart.")
                return
            fig, ax = plt.subplots(figsize=(12, 7))
            labels = top['Mat_combination'] if 'Mat_combination' in top.columns else (top['antecedents'] + ' -> ' + top['consequents'])
            ax.barh(range(len(top)), top['combination_count'], color='#4C78A8')
            ax.set_yticks(range(len(top)))
            def trunc(s, n=60):
                s = str(s)
                return s if len(s) <= n else s[:n-1] + '…'
            ax.set_yticklabels([trunc(s) for s in labels])
            ax.invert_yaxis()
            ax.set_xlabel('Combination count')
            ax.set_title('Top 20 material combinations by combination count')
            plt.tight_layout()
            plt.show()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def show_rule_graph(self):
        if self._rules_df is None or self._rules_df.empty:
            messagebox.showinfo("Info", "No results available. Run analysis first.")
            return
        try:
            rules = self._rules_df
            # Need antecedents/consequents and confidence/combination_count; ensure presence
            required = {'antecedents','consequents','confidence','combination_count'}
            if not required.issubset(set(rules.columns)):
                messagebox.showinfo("Info", "Required columns not available for graph.")
                return
            G = nx.DiGraph()
            for _, row in rules.iterrows():
                G.add_edge(row['antecedents'], row['consequents'], weight=row['confidence'], combination_count=row['combination_count'])

            node_sizes = {}
            for node in G.nodes():
                total_count = rules.apply(
                    lambda r: r['combination_count'] if (node in r['antecedents']) or (node in r['consequents']) else 0,
                    axis=1
                ).sum()
                node_sizes[node] = total_count

            min_size = 300
            max_size = 3000
            counts = list(node_sizes.values())
            if counts:
                min_count = min(counts); max_count = max(counts)
                if max_count == min_count:
                    scaled_sizes = {node: (min_size + max_size) / 2 for node in node_sizes}
                else:
                    scaled_sizes = {node: min_size + (size - min_count) / (max_count - min_count) * (max_size - min_size) for node, size in node_sizes.items()}
            else:
                scaled_sizes = {node: min_size for node in node_sizes}

            pos = nx.spring_layout(G, dim=2, k=0.3, scale=20.0, center=None, iterations=100)
            edges = G.edges(data=True)

            nx.draw_networkx_edges(
                G, pos, edgelist=edges, arrowstyle='-|>', arrowsize=7,
                edge_color=[d['weight'] for (u, v, d) in edges], edge_cmap=plt.cm.Blues, width=2
            )
            nx.draw_networkx_nodes(G, pos, node_size=[scaled_sizes[node] for node in G.nodes()], node_color='skyblue')
            nx.draw_networkx_labels(G, pos, font_size=9, font_color='purple')
            edge_labels = {(u, v): f"{d['weight']:.2f}" for u, v, d in G.edges(data=True)}
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red', font_size=8)
            plt.title('Association rules link graph (by confidence)')
            plt.axis('off')
            plt.show()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    


if __name__ == "__main__":
    App().mainloop()
