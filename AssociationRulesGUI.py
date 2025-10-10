import tkinter as tk
import tkinter.font as tkfont
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


def run_analysis(input_path: str, output_path: str, min_support: float, min_confidence: float, show_graph: bool, log, on_results=None, *, include_zero_consumption: bool = False, exclude_terms=None, include_terms=None):
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

        normalized_excludes = []
        if exclude_terms:
            try:
                normalized_excludes = [str(term).strip().lower() for term in exclude_terms if str(term).strip()]
            except Exception:
                normalized_excludes = []
        if normalized_excludes:
            log_print(f"Applying exclude terms before analysis: {', '.join(normalized_excludes)}")
            before_rows = len(df)
            def should_drop(value):
                if pd.isna(value):
                    return False
                val = str(value).lower()
                return any(term in val for term in normalized_excludes)
            mask = df[item_column].apply(should_drop)
            df = df.loc[~mask].copy()
            removed = before_rows - len(df)
            log_print(f"Excluded {removed} rows based on terms.")
            if df.empty:
                raise ValueError("All rows removed by exclude filter. Adjust the exclude terms or input data.")

        normalized_includes = []
        if include_terms:
            try:
                normalized_includes = [str(term).strip().lower() for term in include_terms if str(term).strip()]
            except Exception:
                normalized_includes = []
        if normalized_includes:
            log_print(f"Applying include-only terms before analysis: {', '.join(normalized_includes)}")
            before_rows = len(df)
            def should_keep(value):
                if pd.isna(value):
                    return False
                val = str(value).lower()
                return any(term in val for term in normalized_includes)
            mask = df[item_column].apply(should_keep)
            df = df.loc[mask].copy()
            retained = len(df)
            removed = before_rows - retained
            log_print(f"Include filter kept {retained} rows and removed {removed} rows.")
            if df.empty:
                raise ValueError("No rows retained after include filter. Adjust the include terms or input data.")

        consumption_column = df.columns[3] if df.shape[1] >= 4 else None
        if consumption_column is not None:
            log_print(f"Using column '{consumption_column}' as consumption indicator.")
            if include_zero_consumption:
                log_print("Including ordered spare parts with consumption = 0 in the analysis.")
            else:
                numeric_consumption = pd.to_numeric(df[consumption_column], errors='coerce')
                before_count = len(df)
                df = df[numeric_consumption > 0]
                removed_count = before_count - len(df)
                log_print(f"Excluded {removed_count} rows with consumption <= 0.")
                if df.empty:
                    raise ValueError("No rows left after filtering for consumption > 0. Adjust the setting or the input data.")
        else:
            log_print("Consumption column (4th column) not found. Proceeding without consumption filter.")

        df[item_column] = df[item_column].apply(lambda val: str(val).strip() if pd.notna(val) else val)

        price_column = df.columns[4] if df.shape[1] >= 5 else None
        item_price_map = {}
        if price_column is not None:
            log_print(f"Using column '{price_column}' as price indicator.")
            numeric_price = pd.to_numeric(df[price_column], errors='coerce')
            if consumption_column is not None:
                numeric_consumption_for_price = pd.to_numeric(df[consumption_column], errors='coerce')
            else:
                numeric_consumption_for_price = pd.Series([pd.NA] * len(df))
            unit_prices = []
            zero_qty_count = 0
            for price_val, qty_val in zip(numeric_price, numeric_consumption_for_price):
                if pd.isna(price_val):
                    unit_prices.append(pd.NA)
                    continue
                qty = float(qty_val) if pd.notna(qty_val) else None
                if qty is not None and qty > 0:
                    unit_prices.append(float(price_val) / qty)
                else:
                    unit_prices.append(float(price_val))
                    if consumption_column is not None:
                        zero_qty_count += 1
            if zero_qty_count:
                log_print(f"Encountered {zero_qty_count} rows with zero/invalid consumption while deriving unit prices; used total price instead.")
            df['_unit_price'] = unit_prices
            price_map_series = (
                df[[item_column, '_unit_price']].dropna(subset=['_unit_price']).groupby(item_column)['_unit_price'].mean()
            )
            item_price_map = price_map_series.to_dict()
            log_print(f"Derived unit prices for {len(item_price_map)} distinct items.")
            df.drop(columns=['_unit_price'], inplace=True, errors='ignore')
        else:
            log_print("Price column (5th column) not found. Price-based metrics will be empty.")

        unique_items = df[[item_column, bestellnummer_column]].drop_duplicates()
        item_bestell_map = dict(zip(unique_items[item_column], unique_items[bestellnummer_column]))

        grouped = df.groupby(id_column)[item_column].apply(
            lambda x: [str(item).strip() for item in x if pd.notna(item)]
        ).reset_index(name='Items')
        grouped = grouped[grouped['Items'].map(bool)]
        if grouped.empty:
            raise ValueError("No transactions found after applying filters. Adjust the settings or data.")

        transactions = grouped['Items'].tolist()

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

        def get_mat_combination_items(row):
            items_in_rule = row['antecedents'].union(row['consequents'])
            names = sorted({str(item).strip() for item in items_in_rule if pd.notna(item)})
            return ', '.join(names)

        rules['Mat_combination_items'] = rules.apply(get_mat_combination_items, axis=1)
        rules['unique_ID'] = rules['Mat_combination'].apply(create_unique_8digit_id)

        missing_price_items = set()

        def sum_prices(item_set):
            total = 0.0
            has_price = False
            for item in item_set:
                price_val = item_price_map.get(item)
                if price_val is None or pd.isna(price_val):
                    missing_price_items.add(item)
                    continue
                total += float(price_val)
                has_price = True
            return total if has_price else pd.NA

        rules['cost_antecedents'] = rules['antecedents'].apply(sum_prices)
        rules['cost_consequents'] = rules['consequents'].apply(sum_prices)

        def weighed_consequent_cost(row):
            cost_c = row['cost_consequents']
            count = row['combination_count']
            if pd.isna(cost_c) or pd.isna(count):
                return pd.NA
            try:
                return float(cost_c) * float(count)
            except Exception:
                return pd.NA

        rules['cost_consequents_weighted'] = rules.apply(weighed_consequent_cost, axis=1)

        def combine_prices(row):
            a = row['cost_antecedents']
            b = row['cost_consequents']
            has_a = pd.notna(a)
            has_b = pd.notna(b)
            if not has_a and not has_b:
                return pd.NA
            total = (float(a) if has_a else 0.0) + (float(b) if has_b else 0.0)
            return total

        rules['cost_total'] = rules.apply(combine_prices, axis=1)
        if missing_price_items:
            preview = sorted(list(missing_price_items))[:10]
            suffix = "..." if len(missing_price_items) > 10 else ""
            log_print(f"Price information missing for {len(missing_price_items)} items; treated as zero in sums: {', '.join(preview)}{suffix}")

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
            'cost_antecedents',
            'cost_consequents',
            'cost_consequents_weighted',
            'cost_total',
            'Mat_combination',
            'Mat_combination_items',
            'unique_ID',
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

            # Kanten hinzufÃ¼gen
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


class Tooltip:
    """Lightweight tooltip helper for Tk/ttk widgets."""

    def __init__(self, widget, text: str, *, delay: int = 400):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._after_id = None
        self._tip_window = None
        self.widget.bind("<Enter>", self._schedule, add="+")
        self.widget.bind("<Leave>", self._hide, add="+")
        self.widget.bind("<FocusOut>", self._hide, add="+")
        self.widget.bind("<Destroy>", self._hide, add="+")

    def update_text(self, text: str):
        self.text = text

    def show_now(self):
        self._cancel_pending()
        self._show()

    def _cancel_pending(self):
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _schedule(self, _event=None):
        self._cancel_pending()
        if not self.text:
            return
        if self.delay == 0:
            self._show()
        else:
            self._after_id = self.widget.after(self.delay, self._show)

    def _show(self):
        if self._tip_window or not self.text:
            return
        try:
            x = self.widget.winfo_rootx() + 12
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        except Exception:
            return
        self._tip_window = tk.Toplevel(self.widget)
        self._tip_window.wm_overrideredirect(True)
        self._tip_window.wm_transient(self.widget)
        self._tip_window.wm_geometry(f"+{x}+{y}")
        label = ttk.Label(self._tip_window, text=self.text, style="Tooltip.TLabel", padding=(8, 4))
        label.pack()

    def _hide(self, _event=None):
        self._cancel_pending()
        if self._tip_window is not None:
            try:
                self._tip_window.destroy()
            except Exception:
                pass
            self._tip_window = None


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Association Analysis (Apriori) GUI')
        self.geometry('1800x950')
        self.minsize(1200, 820)
        self.option_add('*tearOff', False)

        self._buttons_to_toggle = []
        self._tooltips = []
        self._validation_rules = {}
        self._validation_tooltips = {}
        self._quick_search_job = None
        self._log_visible = True
        self._current_tree_columns = ()
        self._autosized_columns = set()
        self._context_item = None
        self._context_column_name = None

        self._rules_df = None
        self._filtered_df = None
        self._visible_df = None
        self._sort_state = {}
        self._current_sort_column = None
        self._current_sort_ascending = True
        self._total_rules_count = 0
        self._visible_rules_count = 0
        self._last_export_path = 'N/A'

        self._column_labels = {
            'antecedents': 'Antecedents',
            'consequents': 'Consequents',
            'support': 'Support',
            'confidence': 'Confidence',
            'lift': 'Lift',
            'leverage': 'Leverage',
            'conviction': 'Conviction',
            'zhangs_metric': 'Zhangs Metric',
            'combination_count': 'Combination Count',
            'cost_antecedents': 'Cost Antecedents (EUR)',
            'cost_consequents': 'Cost Consequents (EUR)',
            'cost_consequents_weighted': 'Cost Consequents x Combination Count (EUR)',
            'cost_total': 'Cost Antecedent+Consequents (EUR)',
            'Mat_combination': 'Mat_combination',
            'unique_ID': 'unique_ID',
            'different items': 'Different Items',
        }
        self._numeric_columns = {
            'support',
            'confidence',
            'lift',
            'leverage',
            'conviction',
            'zhangs_metric',
            'combination_count',
            'cost_antecedents',
            'cost_consequents',
            'cost_consequents_weighted',
            'cost_total',
            'different items',
        }
        self._six_decimal_columns = {
            'support',
            'confidence',
            'lift',
            'leverage',
            'conviction',
            'zhangs_metric',
        }
        self._two_decimal_columns = {
            'cost_antecedents',
            'cost_consequents',
            'cost_consequents_weighted',
            'cost_total',
        }
        self._int_columns = {'combination_count', 'different items'}

        self.input_path = tk.StringVar(value=r'C:\Assoziationsanalyse\SPC.xlsx')
        self.output_path = tk.StringVar(value=r'C:\Assoziationsanalyse\SPC_Regeln.xlsx')
        self.min_support = tk.StringVar(value='0.001')
        self.min_confidence = tk.StringVar(value='0.15')
        self.show_graph = tk.BooleanVar(value=False)
        self.include_zero_consumption = tk.BooleanVar(value=False)
        self.quick_search_var = tk.StringVar()
        self.status_var = tk.StringVar(value='Rules: 0 | Visible: 0 | Last export: N/A')

        self._apply_theme()
        self._build()
        self._bind_shortcuts()

        self.quick_search_var.trace_add('write', self._on_quick_search_change)
        self._update_status_bar()

    def _build(self):
        base_pad = {'padx': 8, 'pady': 6}
        group_pad = {'padx': 10, 'pady': 8}

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        root = ttk.Frame(self, padding=(8, 6))
        root.grid(row=0, column=0, sticky='nsew')
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        self.main_paned = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_paned.grid(row=0, column=0, sticky='nsew')

        controls_container = ttk.Frame(self.main_paned, style='Surface.TFrame')
        controls_container.columnconfigure(0, weight=1)
        controls_container.rowconfigure(0, weight=1)
        self.main_paned.add(controls_container, weight=1)

        self.controls_notebook = ttk.Notebook(controls_container)
        self.controls_notebook.grid(row=0, column=0, sticky='nsew')

        inputs_tab = ttk.Frame(self.controls_notebook, padding=(10, 8))
        filters_tab = ttk.Frame(self.controls_notebook, padding=(10, 8))
        self.controls_notebook.add(inputs_tab, text='Inputs')
        self.controls_notebook.add(filters_tab, text='Filters & Columns')

        inputs_tab.columnconfigure(1, weight=1)

        ttk.Label(inputs_tab, text='Input file (Excel):').grid(row=0, column=0, sticky='w', pady=(0, 6))
        self.input_entry = ttk.Entry(inputs_tab, textvariable=self.input_path, style='Standard.TEntry')
        self.input_entry.grid(row=0, column=1, sticky='ew', pady=(0, 6))
        btn_browse_in = self._register_button(
            ttk.Button(inputs_tab, text='Browse...', style='Tertiary.TButton', command=self.browse_input)
        )
        btn_browse_in.grid(row=0, column=2, sticky='e', padx=(8, 0), pady=(0, 6))
        self._add_tooltip(btn_browse_in, 'Select the Excel workbook to analyze (Ctrl+O)')

        ttk.Label(inputs_tab, text='Output file (Excel):').grid(row=1, column=0, sticky='w', pady=(0, 6))
        self.output_entry = ttk.Entry(inputs_tab, textvariable=self.output_path, style='Standard.TEntry')
        self.output_entry.grid(row=1, column=1, sticky='ew', pady=(0, 6))
        btn_browse_out = self._register_button(
            ttk.Button(inputs_tab, text='Save as...', style='Tertiary.TButton', command=self.browse_output)
        )
        btn_browse_out.grid(row=1, column=2, sticky='e', padx=(8, 0), pady=(0, 6))
        self._add_tooltip(btn_browse_out, 'Choose where the exported rules file will be written')

        ttk.Label(inputs_tab, text='Min support:').grid(row=2, column=0, sticky='w', pady=(0, 6))
        self.min_support_entry = ttk.Entry(inputs_tab, textvariable=self.min_support, width=14, style='Standard.TEntry')
        self.min_support_entry.grid(row=2, column=1, sticky='w', pady=(0, 6))
        self._register_numeric_validation(
            self.min_support_entry,
            self.min_support,
            0.0,
            1.0,
            'Fraction between 0 and 1 (example: 0.001)'
        )

        ttk.Label(inputs_tab, text='Min confidence:').grid(row=3, column=0, sticky='w', pady=(0, 6))
        self.min_confidence_entry = ttk.Entry(inputs_tab, textvariable=self.min_confidence, width=14, style='Standard.TEntry')
        self.min_confidence_entry.grid(row=3, column=1, sticky='w', pady=(0, 6))
        self._register_numeric_validation(
            self.min_confidence_entry,
            self.min_confidence,
            0.0,
            1.0,
            'Fraction between 0 and 1 (example: 0.15)'
        )

        include_chk = ttk.Checkbutton(
            inputs_tab,
            text='Include ordered spare parts (consumption = 0)',
            variable=self.include_zero_consumption
        )
        include_chk.grid(row=4, column=0, columnspan=3, sticky='w', pady=(0, 6))
        self._add_tooltip(include_chk, 'If enabled, items with zero consumption remain in the dataset')

        action_row = ttk.Frame(inputs_tab)
        action_row.grid(row=5, column=0, columnspan=3, sticky='ew', pady=(12, 0))
        action_row.columnconfigure(2, weight=1)

        self.btn_run = self._register_button(
            ttk.Button(action_row, text='Run analysis', style='Accent.TButton', command=self.on_run)
        )
        self.btn_run.grid(row=0, column=0, padx=(0, 8))
        self._add_tooltip(self.btn_run, 'Execute the Apriori analysis (F5)')

        self.btn_stop = ttk.Button(action_row, text='Stop', style='Tertiary.TButton', state='disabled', command=self.on_stop)
        self.btn_stop.grid(row=0, column=1, padx=(0, 8))
        self._add_tooltip(self.btn_stop, 'Stopping is not available while the analysis runs synchronously')

        self.progress = ttk.Progressbar(action_row, mode='indeterminate')
        self.progress.grid(row=0, column=2, sticky='ew')
        self.progress.grid_remove()

        filters_tab.columnconfigure(0, weight=1)
        filters_tab.rowconfigure(2, weight=1)

        text_filters = ttk.Labelframe(filters_tab, text='Text filters')
        text_filters.grid(row=0, column=0, sticky='ew', **group_pad)
        text_filters.columnconfigure(1, weight=1)

        ttk.Label(text_filters, text='Include only (comma separated):').grid(row=0, column=0, sticky='w', pady=(0, 6))
        self.include_entry = ttk.Entry(text_filters, style='Standard.TEntry')
        self.include_entry.grid(row=0, column=1, sticky='ew', pady=(0, 6))
        self._add_tooltip(self.include_entry, 'Keep rules containing any of these terms')

        ttk.Label(text_filters, text='Exclude terms (comma separated):').grid(row=1, column=0, sticky='w')
        self.exclude_entry = ttk.Entry(text_filters, style='Standard.TEntry')
        self.exclude_entry.grid(row=1, column=1, sticky='ew')
        self._add_tooltip(self.exclude_entry, 'Remove rules containing any of these terms')

        filter_buttons = ttk.Frame(text_filters)
        filter_buttons.grid(row=2, column=0, columnspan=2, sticky='ew', pady=(10, 0))
        filter_buttons.columnconfigure(2, weight=1)

        self.btn_apply_filter = self._register_button(
            ttk.Button(filter_buttons, text='Apply filter', style='Primary.TButton', command=self.apply_filter)
        )
        self.btn_apply_filter.grid(row=0, column=0, padx=(0, 8))
        self._add_tooltip(self.btn_apply_filter, 'Apply include/exclude filters to the loaded rules')

        self.btn_reset_filter = self._register_button(
            ttk.Button(filter_buttons, text='Reset', style='Tertiary.TButton', command=self.reset_filter)
        )
        self.btn_reset_filter.grid(row=0, column=1)
        self._add_tooltip(self.btn_reset_filter, 'Clear all text filters')

        metrics_group = ttk.Labelframe(filters_tab, text='Visible metrics')
        metrics_group.grid(row=2, column=0, sticky='nsew', **group_pad)
        metrics_group.columnconfigure(0, weight=1)
        metrics_group.rowconfigure(0, weight=1)

        metrics_canvas = tk.Canvas(metrics_group, highlightthickness=0, borderwidth=0, background=self._colors['canvas'])
        metrics_canvas.grid(row=0, column=0, sticky='nsew')
        metrics_scroll = ttk.Scrollbar(metrics_group, orient='vertical', command=metrics_canvas.yview)
        metrics_scroll.grid(row=0, column=1, sticky='ns')
        metrics_canvas.configure(yscrollcommand=metrics_scroll.set)

        metrics_inner = ttk.Frame(metrics_canvas, style='Surface.TFrame')
        metrics_window = metrics_canvas.create_window((0, 0), window=metrics_inner, anchor='nw')

        def _sync_metrics_width(event):
            metrics_canvas.itemconfigure(metrics_window, width=event.width)

        metrics_inner.bind('<Configure>', lambda event: metrics_canvas.configure(scrollregion=metrics_canvas.bbox('all')))
        metrics_canvas.bind('<Configure>', _sync_metrics_width)

        metrics_inner.columnconfigure(0, weight=1)
        metrics_inner.columnconfigure(1, weight=1)

        metric_items = [
            ('support', 'Support'),
            ('lift', 'Lift'),
            ('leverage', 'Leverage'),
            ('conviction', 'Conviction'),
            ('zhangs_metric', 'Zhangs Metric'),
            ('combination_count', 'Combination Count'),
            ('cost_antecedents', 'Cost Antecedents (EUR)'),
            ('cost_consequents', 'Cost Consequents (EUR)'),
            ('cost_consequents_weighted', 'Cost Consequents x Combination Count (EUR)'),
            ('cost_total', 'Cost Antecedent+Consequents (EUR)'),
            ('Mat_combination', 'Mat_combination'),
            ('unique_ID', 'unique_ID'),
            ('different items', 'Different Items'),
        ]

        self.metric_vars = {}
        self._metric_order = []
        for index, (key, label) in enumerate(metric_items):
            var = tk.BooleanVar(value=False)
            self.metric_vars[key] = var
            self._metric_order.append(key)
            row = index // 2
            column = index % 2
            cb = ttk.Checkbutton(metrics_inner, text=label, variable=var, command=self.update_visible_columns)
            cb.grid(row=row, column=column, sticky='w', padx=6, pady=4)

        results_container = ttk.Frame(self.main_paned, style='Surface.TFrame')
        results_container.columnconfigure(0, weight=1)
        results_container.rowconfigure(0, weight=5)
        results_container.rowconfigure(2, weight=2)
        self.main_paned.add(results_container, weight=3)
        self.results_container = results_container

        self.results_notebook = ttk.Notebook(results_container)
        self.results_notebook.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)

        results_tab = ttk.Frame(self.results_notebook, padding=(10, 8))
        charts_tab = ttk.Frame(self.results_notebook, padding=(10, 8))
        self.results_notebook.add(results_tab, text='Results')
        self.results_notebook.add(charts_tab, text='Charts')

        results_tab.columnconfigure(0, weight=1)
        results_tab.rowconfigure(1, weight=1)

        search_frame = ttk.Frame(results_tab)
        search_frame.grid(row=0, column=0, sticky='ew', pady=(0, 8))
        search_frame.columnconfigure(1, weight=1)

        ttk.Label(search_frame, text='Quick search:').grid(row=0, column=0, sticky='w')
        self.quick_search_entry = ttk.Entry(search_frame, textvariable=self.quick_search_var, style='Standard.TEntry')
        self.quick_search_entry.grid(row=0, column=1, sticky='ew', padx=(8, 6))
        self._add_tooltip(self.quick_search_entry, 'Filter visible rows by matching antecedents or consequents (Ctrl+F)')

        clear_search = ttk.Button(search_frame, text='Clear', style='Tertiary.TButton', command=lambda: self.quick_search_var.set(''))
        clear_search.grid(row=0, column=2, padx=(0, 8))

        self.btn_save_filtered = self._register_button(
            ttk.Button(search_frame, text='Save filtered...', style='Primary.TButton', command=self.save_filtered)
        )
        self.btn_save_filtered.grid(row=0, column=3, sticky='e')
        self._add_tooltip(self.btn_save_filtered, 'Export the currently visible rows (Ctrl+S)')

        tree_frame = ttk.Frame(results_tab, style='Surface.TFrame')
        tree_frame.grid(row=1, column=0, sticky='nsew')
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_frame, show='headings', selectmode='extended')
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        vsb.grid(row=0, column=1, sticky='ns')
        hsb = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.tree.xview)
        hsb.grid(row=1, column=0, sticky='ew')
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.tag_configure('even', background=self._colors['tree_even'])
        self.tree.tag_configure('odd', background=self._colors['tree_odd'])
        self._add_tooltip(self.tree, 'Right-click for copy or export options')

        self.tree_menu = tk.Menu(self, tearoff=False)
        self.tree_menu.add_command(label='Copy row', command=self._copy_selected_row)
        self.tree_menu.add_command(label='Copy cell', command=self._copy_selected_cell)
        self.tree_menu.add_separator()
        self.tree_menu.add_command(label='Export visible columns...', command=self._export_visible_columns)
        self.tree.bind('<Button-3>', self._on_tree_right_click)
        self.tree.bind('<Control-Button-1>', self._on_tree_right_click)
        self.tree.bind('<Control-c>', self._copy_selected_row_event)
        self.tree.bind('<Command-c>', self._copy_selected_row_event)

        charts_tab.columnconfigure(0, weight=1)
        charts_tab.rowconfigure(1, weight=1)

        charts_toolbar = ttk.Frame(charts_tab)
        charts_toolbar.grid(row=0, column=0, sticky='w', pady=(0, 8))

        self.btn_show_top20 = self._register_button(
            ttk.Button(charts_toolbar, text='Show Top 20', style='Primary.TButton', command=self.show_top20)
        )
        self.btn_show_top20.pack(side='left', padx=(0, 8))
        self._add_tooltip(self.btn_show_top20, 'Render the Top 20 combinations bar chart')

        self.btn_show_graph = self._register_button(
            ttk.Button(charts_toolbar, text='Show graph', style='Primary.TButton', command=self.show_rule_graph)
        )
        self.btn_show_graph.pack(side='left')
        self._add_tooltip(self.btn_show_graph, 'Visualize rules as a network graph')

        charts_placeholder = ttk.Frame(charts_tab, style='Card.TFrame')
        charts_placeholder.grid(row=1, column=0, sticky='nsew')
        ttk.Label(charts_placeholder, text='Charts open in separate matplotlib windows.', style='Muted.TLabel').place(relx=0.5, rely=0.5, anchor='center')

        log_header = ttk.Frame(results_container, padding=(4, 0))
        log_header.grid(row=1, column=0, sticky='ew')
        log_header.columnconfigure(0, weight=1)

        self.log_toggle_button = ttk.Button(log_header, text='Hide log v', style='Link.TButton', command=self._toggle_log_panel)
        self.log_toggle_button.grid(row=0, column=0, sticky='w')
        self.btn_clear_log = ttk.Button(log_header, text='Clear log', style='Tertiary.TButton', command=self._clear_log)
        self.btn_clear_log.grid(row=0, column=1, sticky='e')

        self.log_container = ttk.Frame(results_container, style='Surface.TFrame', padding=(0, 4))
        self.log_container.grid(row=2, column=0, sticky='nsew')
        self.log_container.columnconfigure(0, weight=1)
        self.log_container.rowconfigure(0, weight=1)

        self.txt_log = tk.Text(
            self.log_container,
            height=8,
            state='disabled',
            wrap='word',
            bg=self._colors['log_bg'],
            fg=self._colors['log_fg'],
            relief='flat'
        )
        self.txt_log.grid(row=0, column=0, sticky='nsew')
        log_scroll = ttk.Scrollbar(self.log_container, orient='vertical', command=self.txt_log.yview)
        log_scroll.grid(row=0, column=1, sticky='ns')
        self.txt_log.configure(yscrollcommand=log_scroll.set)

        status_frame = ttk.Frame(root, style='Status.TFrame', padding=(10, 4))
        status_frame.grid(row=1, column=0, sticky='ew', pady=(8, 0))
        status_frame.columnconfigure(0, weight=0)
        status_frame.columnconfigure(1, weight=1)
        ttk.Label(status_frame, text='Roland Emrich', style='Muted.TLabel').grid(row=0, column=0, sticky='w')
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, style='Status.TLabel', anchor='e')
        self.status_label.grid(row=0, column=1, sticky='e')

        self._configure_log_weights()

    def _register_button(self, btn: ttk.Button) -> ttk.Button:
        self._buttons_to_toggle.append(btn)
        return btn

    def _add_tooltip(self, widget, text):
        tooltip = Tooltip(widget, text)
        self._tooltips.append(tooltip)
        return tooltip

    def _register_numeric_validation(self, entry, variable, minimum, maximum, tooltip_text):
        self._validation_rules[entry] = (variable, minimum, maximum, tooltip_text)
        tooltip = self._add_tooltip(entry, tooltip_text)
        self._validation_tooltips[entry] = {'tooltip': tooltip, 'default': tooltip_text}
        entry.bind('<FocusOut>', lambda _event, ent=entry: self._validate_numeric_entry(ent), add='+')

    def _validate_numeric_entry(self, entry):
        variable, minimum, maximum, default_text = self._validation_rules[entry]
        raw = variable.get().strip().replace(',', '.')
        try:
            value = float(raw)
        except ValueError:
            self._mark_entry_invalid(entry, 'Enter a numeric value between 0 and 1')
            return False
        if not (minimum < value <= maximum):
            self._mark_entry_invalid(entry, f'Value must be between {minimum} and {maximum}')
            return False
        self._clear_entry_validation(entry)
        variable.set(str(value))
        return True

    def _mark_entry_invalid(self, entry, message):
        tooltip_info = self._validation_tooltips.get(entry)
        if tooltip_info:
            tooltip_info['tooltip'].update_text(message)
            tooltip_info['tooltip'].show_now()
        entry.configure(style='Invalid.TEntry')

    def _clear_entry_validation(self, entry):
        entry.configure(style='Standard.TEntry')
        tooltip_info = self._validation_tooltips.get(entry)
        if tooltip_info:
            tooltip_info['tooltip'].update_text(tooltip_info['default'])

    def _validate_all_numeric(self):
        for entry in self._validation_rules:
            if not self._validate_numeric_entry(entry):
                entry.focus_set()
                return False
        return True

    def _bind_shortcuts(self):
        self.bind('<Control-o>', lambda _event: self.browse_input())
        self.bind('<Control-s>', lambda _event: self.save_filtered())
        self.bind('<F5>', lambda _event: self.on_run())
        self.bind('<Control-f>', lambda _event: self._focus_quick_search())

    def _focus_quick_search(self):
        self.results_notebook.select(0)
        self.quick_search_entry.focus_set()
        self.quick_search_entry.select_range(0, 'end')

    def _on_quick_search_change(self, *_args):
        if self._quick_search_job is not None:
            self.after_cancel(self._quick_search_job)
        self._quick_search_job = self.after(200, self.refresh_table)

    def _toggle_log_panel(self):
        self._log_visible = not self._log_visible
        if self._log_visible:
            self.log_container.grid()
            self.log_toggle_button.configure(text='Hide log v')
        else:
            self.log_container.grid_remove()
            self.log_toggle_button.configure(text='Show log >')
        self._configure_log_weights()

    def _configure_log_weights(self):
        if self._log_visible:
            self.results_container.rowconfigure(0, weight=5)
            self.results_container.rowconfigure(2, weight=2)
        else:
            self.results_container.rowconfigure(0, weight=1)
            self.results_container.rowconfigure(2, weight=0)

    def _clear_log(self):
        self.txt_log.configure(state='normal')
        self.txt_log.delete('1.0', 'end')
        self.txt_log.configure(state='disabled')

    def _on_tree_right_click(self, event):
        item = self.tree.identify_row(event.y)
        column_id = self.tree.identify_column(event.x)
        self._context_item = item
        if item:
            self.tree.selection_set(item)
        else:
            self.tree.selection_remove(self.tree.selection())
        self._context_column_name = None
        if column_id.startswith('#'):
            index = int(column_id[1:]) - 1
            columns = self.tree['columns']
            if 0 <= index < len(columns):
                self._context_column_name = columns[index]
        self._show_tree_menu(event)

    def _show_tree_menu(self, event):
        try:
            self.tree_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.tree_menu.grab_release()

    def _copy_selected_row_event(self, _event=None):
        self._copy_selected_row()
        return 'break'

    def _copy_selected_row(self):
        selection = self.tree.selection()
        if not selection:
            return
        lines = []
        for iid in selection:
            values = self.tree.item(iid).get('values', [])
            lines.append('\t'.join(str(value) for value in values))
        text = '\n'.join(lines)
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)

    def _copy_selected_cell(self):
        if not self._context_item or not self._context_column_name:
            return
        columns = self.tree['columns']
        try:
            index = columns.index(self._context_column_name)
        except ValueError:
            return
        values = self.tree.item(self._context_item).get('values', [])
        if 0 <= index < len(values):
            self.clipboard_clear()
            self.clipboard_append(str(values[index]))

    def _export_visible_columns(self):
        self.save_filtered()

    def _get_sort_indicator(self, column):
        if column == self._current_sort_column:
            return ' ?' if self._current_sort_ascending else ' ?'
        return ''

    def _format_row(self, row, columns):
        return [self._format_cell(row, column) for column in columns]

    def _format_cell(self, row, column):
        if column not in row:
            return ''
        value = row[column]
        if pd.isna(value):
            return ''
        try:
            if column in self._six_decimal_columns:
                return f'{float(value):.6f}'
            if column in self._two_decimal_columns:
                return f'{float(value):.2f}'
            if column in self._int_columns:
                return f'{int(float(value))}'
        except Exception:
            pass
        return str(value)

    def _autosize_columns(self, rows, columns):
        if not rows:
            return
        for index, column in enumerate(columns):
            if column in self._autosized_columns:
                continue
            header = self._column_labels.get(column, column.title())
            width = self._tree_heading_font.measure(header) + 24
            for values in rows[:200]:
                if index < len(values):
                    width = max(width, self._tree_font.measure(str(values[index])) + 24)
            width = min(max(width, 80), 420)
            self.tree.column(column, width=width)
            self._autosized_columns.add(column)

    def _update_status_bar(self):
        export_text = self._last_export_path if self._last_export_path and self._last_export_path != 'N/A' else 'N/A'
        self.status_var.set(f'Rules: {self._total_rules_count} | Visible: {self._visible_rules_count} | Last export: {export_text}')

    def _set_buttons_state(self, disable: bool):
        state = 'disabled' if disable else 'normal'
        for btn in self._buttons_to_toggle:
            try:
                btn.configure(state=state)
            except Exception:
                pass
        if disable:
            self.progress.grid()
            self.progress.start(12)
            try:
                self.configure(cursor='watch')
            except Exception:
                pass
        else:
            self.progress.stop()
            self.progress.grid_remove()
            try:
                self.configure(cursor='')
            except Exception:
                pass


    def _apply_theme(self):
        self._colors = {
            'background': '#f4f6fb',
            'surface': '#ffffff',
            'surface_alt': '#ecf1fb',
            'canvas': '#ffffff',
            'accent': '#2563eb',
            'accent_hover': '#1d4ed8',
            'accent_fg': '#ffffff',
            'primary_text': '#1f2937',
            'muted_text': '#4b5563',
            'tree_even': '#ffffff',
            'tree_odd': '#f2f6ff',
            'log_bg': '#111827',
            'log_fg': '#e5e7eb',
        }

        self.configure(bg=self._colors['background'])

        style = ttk.Style(self)
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass

        default_font = tkfont.nametofont('TkDefaultFont')
        default_font.configure(size=max(default_font.cget('size') + 1, 11))
        heading_font = tkfont.nametofont('TkHeadingFont')
        heading_font.configure(size=default_font.cget('size'), weight='bold')
        self._tree_font = default_font
        self._tree_heading_font = heading_font

        style.configure(
            '.',
            background=self._colors['surface'],
            foreground=self._colors['primary_text'],
            font=default_font
        )
        style.configure('Surface.TFrame', background=self._colors['surface'])
        style.configure('Card.TFrame', background=self._colors['surface'], relief='solid', borderwidth=1)
        style.configure('TLabel', background=self._colors['surface'], foreground=self._colors['primary_text'])
        style.configure('Muted.TLabel', background=self._colors['surface'], foreground=self._colors['muted_text'])
        style.configure('Tooltip.TLabel', background='#1f2937', foreground='#f9fafb', font=(default_font.actual('family'), 9))

        style.configure('Accent.TButton',
                        background=self._colors['accent'],
                        foreground=self._colors['accent_fg'],
                        padding=(16, 8))
        style.map('Accent.TButton',
                  background=[('disabled', '#9db5f9'), ('pressed', self._colors['accent_hover']), ('active', self._colors['accent_hover'])],
                  foreground=[('disabled', '#ffffff')])

        style.configure('Primary.TButton',
                        background='#3b82f6',
                        foreground='#ffffff',
                        padding=(14, 6))
        style.map('Primary.TButton',
                  background=[('disabled', '#c7d8fb'), ('pressed', '#2563eb'), ('active', '#2563eb')],
                  foreground=[('disabled', '#f5f5f5')])

        style.configure('Tertiary.TButton',
                        background='#e2e8f0',
                        foreground=self._colors['primary_text'],
                        padding=(12, 6))
        style.map('Tertiary.TButton',
                  background=[('disabled', '#eef2f6'), ('pressed', '#cfd8e3'), ('active', '#cfd8e3')])

        style.configure('Link.TButton',
                        background=self._colors['surface'],
                        foreground=self._colors['accent'],
                        padding=(0, 0),
                        relief='flat')
        style.map('Link.TButton',
                  foreground=[('active', self._colors['accent_hover']), ('pressed', self._colors['accent_hover'])])

        style.configure('Standard.TEntry',
                        fieldbackground=self._colors['surface'],
                        foreground=self._colors['primary_text'],
                        padding=6)
        style.configure('Invalid.TEntry',
                        fieldbackground='#ffecec',
                        foreground='#b3261e',
                        padding=6)

        style.configure('TCheckbutton', background=self._colors['surface'], foreground=self._colors['primary_text'])

        style.configure('Treeview',
                        background=self._colors['surface'],
                        fieldbackground=self._colors['surface'],
                        foreground=self._colors['primary_text'],
                        rowheight=28,
                        font=default_font)
        style.configure('Treeview.Heading',
                        background=self._colors['surface_alt'],
                        foreground=self._colors['primary_text'],
                        font=heading_font)
        style.map('Treeview.Heading',
                  background=[('pressed', self._colors['accent']), ('active', self._colors['accent'])],
                  foreground=[('pressed', '#ffffff'), ('active', '#ffffff')])

        style.configure('Status.TFrame', background=self._colors['surface_alt'])
        style.configure('Status.TLabel', background=self._colors['surface_alt'], foreground=self._colors['muted_text'], anchor='e')


    def browse_input(self):
        path = filedialog.askopenfilename(
            title="Select input file",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if path:
            self.input_path.set(path)

    def browse_output(self):
        path = filedialog.asksaveasfilename(
            title="Select output file",
            defaultextension=".xlsx",
            filetypes=[("Excel file", "*.xlsx")]
        )
        if path:
            self.output_path.set(path)

    def on_run(self):
        if not self._validate_all_numeric():
            return
        try:
            input_path = self.input_path.get().strip()
            output_path = self.output_path.get().strip()
            min_support = float(self.min_support.get().strip().replace(',', '.'))
            min_confidence = float(self.min_confidence.get().strip().replace(',', '.'))

            if not os.path.isfile(input_path):
                messagebox.showwarning('Notice', 'Input file does not exist.')
                return
            if not (0 < min_support <= 1):
                messagebox.showwarning('Notice', 'Min support must be between 0 and 1.')
                return
            if not (0 < min_confidence <= 1):
                messagebox.showwarning('Notice', 'Min confidence must be between 0 and 1.')
                return

            self._set_buttons_state(True)
            self.update_idletasks()
            try:
                run_analysis(
                    input_path=input_path,
                    output_path=output_path,
                    min_support=min_support,
                    min_confidence=min_confidence,
                    show_graph=False,
                    log=self.txt_log,
                    on_results=self.on_results_ready,
                    include_zero_consumption=self.include_zero_consumption.get(),
                    exclude_terms=self.get_exclude_terms(),
                    include_terms=self.get_include_terms()
                )
            finally:
                self._set_buttons_state(False)
        except ValueError:
            messagebox.showerror('Error', 'Please enter valid numeric values for support/confidence.')
        except Exception as e:
            messagebox.showerror('Error', str(e))


    def on_stop(self):
        messagebox.showinfo('Info', 'Stopping the analysis is not available in the current version.')


    # Results handling
    def on_results_ready(self, df: pd.DataFrame):
        self._rules_df = df.copy()
        self._filtered_df = df.copy()
        self._visible_df = None
        self._sort_state = {}
        self._current_sort_column = None
        self._autosized_columns = set()
        self._total_rules_count = len(df)
        self.quick_search_var.set('')
        self.refresh_table()


    def get_include_terms(self):
        raw = self.include_entry.get().strip()
        if not raw:
            return []
        return [t.strip().lower() for t in raw.split(',') if t.strip()]

    def get_exclude_terms(self):
        raw = self.exclude_entry.get().strip()
        if not raw:
            return []
        return [t.strip().lower() for t in raw.split(',') if t.strip()]

    def apply_filter(self):
        if self._rules_df is None:
            return
        include_terms = self.get_include_terms()
        exclude_terms = self.get_exclude_terms()
        df = self._rules_df.copy()

        if include_terms:
            def include_row(row):
                a = str(row['antecedents']).lower()
                c = str(row['consequents']).lower()
                return any(term in a or term in c for term in include_terms)
            mask_include = df.apply(include_row, axis=1)
            df = df.loc[mask_include].copy()

        if exclude_terms and not df.empty:
            def exclude_row(row):
                a = str(row['antecedents']).lower()
                c = str(row['consequents']).lower()
                return any(term in a or term in c for term in exclude_terms)
            mask_exclude = df.apply(exclude_row, axis=1)
            df = df.loc[~mask_exclude].copy()

        self._filtered_df = df
        self._autosized_columns = set()
        self.refresh_table()

    def reset_filter(self):
        self.include_entry.delete(0, 'end')
        self.exclude_entry.delete(0, 'end')
        if self._rules_df is not None:
            self._filtered_df = self._rules_df.copy()
            self._autosized_columns = set()
            self._sort_state = {}
            self.refresh_table()

    def refresh_table(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)

        if self._filtered_df is None or self._filtered_df.empty:
            self._visible_rules_count = 0
            self._visible_df = None
            self._update_status_bar()
            return

        df = self._filtered_df
        search = self.quick_search_var.get().strip().lower()
        if search:
            mask = df.apply(
                lambda row: search in str(row.get('antecedents', '')).lower() or search in str(row.get('consequents', '')).lower(),
                axis=1
            )
            df_view = df.loc[mask].copy()
        else:
            df_view = df.copy()

        if df_view.empty:
            self._visible_rules_count = 0
            self._visible_df = df_view
            self._update_status_bar()
            return

        columns = self.current_visible_columns()
        if self._current_sort_column and self._current_sort_column not in columns:
            self._current_sort_column = None
        if tuple(columns) != self._current_tree_columns:
            self._current_tree_columns = tuple(columns)
            self._autosized_columns = set()

        self.tree['columns'] = columns

        for column in columns:
            label = self._column_labels.get(column, column.title())
            indicator = self._get_sort_indicator(column)
            anchor = 'e' if column in self._numeric_columns else 'w'
            self.tree.heading(column, text=f'{label}{indicator}', command=lambda c=column: self.sort_by_column(c))
            self.tree.column(column, anchor=anchor, stretch=True, minwidth=80)

        formatted_rows = []
        for index, (_, row) in enumerate(df_view.iterrows()):
            formatted = self._format_row(row, columns)
            formatted_rows.append(formatted)
            tag = 'even' if index % 2 == 0 else 'odd'
            self.tree.insert('', 'end', values=formatted, tags=(tag,))

        self._visible_df = df_view
        self._visible_rules_count = len(formatted_rows)
        self._update_status_bar()
        self._autosize_columns(formatted_rows, columns)


    def sort_by_column(self, column):
        if self._filtered_df is None or self._filtered_df.empty:
            return
        ascending = self._sort_state.get(column, True)
        try:
            if column in {'support', 'confidence', 'lift', 'leverage', 'conviction', 'zhangs_metric', 'cost_antecedents', 'cost_consequents', 'cost_consequents_weighted', 'cost_total'}:
                self._filtered_df[column] = pd.to_numeric(self._filtered_df[column], errors='coerce')
            elif column in {'combination_count', 'different items'}:
                self._filtered_df[column] = pd.to_numeric(self._filtered_df[column], errors='coerce').astype('Int64')
        except Exception:
            pass
        self._filtered_df = self._filtered_df.sort_values(by=column, ascending=ascending, kind='mergesort')
        self._sort_state[column] = not ascending
        self._current_sort_column = column
        self._current_sort_ascending = ascending
        self.refresh_table()


    def save_filtered(self):
        if self._filtered_df is None or self._filtered_df.empty:
            messagebox.showinfo('Info', 'No filtered results to save.')
            return
        cols = self.current_visible_columns()
        cols = [c for c in cols if c in self._filtered_df.columns]
        if not cols:
            messagebox.showinfo('Info', 'No visible columns to save.')
            return
        source_df = self._visible_df if self._visible_df is not None else self._filtered_df
        if source_df.empty:
            messagebox.showinfo('Info', 'No data to save.')
            return
        df = source_df[cols].copy()
        path = filedialog.asksaveasfilename(
            title='Save filtered results',
            defaultextension='.xlsx',
            filetypes=[('Excel file', '*.xlsx'), ('CSV file', '*.csv')]
        )
        if not path:
            return
        try:
            if path.lower().endswith('.csv'):
                df.to_csv(path, index=False, encoding='utf-8-sig')
            else:
                df.to_excel(path, index=False)
            messagebox.showinfo('Saved', f'Filtered results saved to: {path}')
            self._last_export_path = path
            self._update_status_bar()
        except Exception as e:
            messagebox.showerror('Error', str(e))


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
            required = {'unique_ID', 'cost_consequents_weighted'}
            if not required.issubset(df.columns):
                messagebox.showinfo("Info", "Required columns not available.")
                return
            temp = df.dropna(subset=['unique_ID']).copy()
            if temp.empty:
                messagebox.showinfo("Info", "No data for Top 20 chart.")
                return
            temp['unique_ID'] = temp['unique_ID'].astype(str)
            temp['cost_consequents_weighted'] = pd.to_numeric(
                temp['cost_consequents_weighted'], errors='coerce'
            ).fillna(0)
            aggregated = (
                temp.groupby('unique_ID')['cost_consequents_weighted']
                .sum()
                .sort_values(ascending=False)
            )
            if aggregated.empty:
                messagebox.showinfo("Info", "No data for Top 20 chart.")
                return
            top = aggregated.head(20)
            meta = None
            label_column = None
            if 'Mat_combination_items' in temp.columns:
                label_column = 'Mat_combination_items'
            elif 'Mat_combination' in temp.columns:
                label_column = 'Mat_combination'
            if label_column is not None:
                meta = (
                    temp[['unique_ID', label_column]]
                    .dropna(subset=[label_column])
                    .drop_duplicates(subset='unique_ID')
                    .set_index('unique_ID')[label_column]
                )
            labels = []
            for mat_id, total in top.items():
                mat_id_str = str(mat_id)
                label = mat_id_str
                if meta is not None and mat_id in meta.index:
                    combo = meta.loc[mat_id]
                    if isinstance(combo, str) and combo.strip():
                        label = f"{combo} ({mat_id_str})"
                labels.append(label)
            fig, ax = plt.subplots(figsize=(12, 7))
            ax.barh(range(len(top)), top.values, color='#4C78A8')
            ax.set_yticks(range(len(top)))
            def trunc(s, n=80):
                s = str(s)
                return s if len(s) <= n else s[: n - 3] + '...'
            ax.set_yticklabels([trunc(label) for label in labels])
            ax.invert_yaxis()
            ax.set_xlabel('Sum of cost_consequents Ã— combination count (EUR)')
            ax.set_title('Top 20 combinations by weighted consequent cost')
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






