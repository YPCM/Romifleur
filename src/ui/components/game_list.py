
import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import threading

class GameList(ctk.CTkFrame):
    def __init__(self, master, app_context, on_add_queue, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app_context
        self.on_add_queue = on_add_queue
        
        self.current_results = []
        self.selected_files = set()
        
        self._setup_ui()

    def _setup_ui(self):
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Header (Filters)
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_filter_change)
        self.search_entry = ctk.CTkEntry(self.header, placeholder_text="Search games...", textvariable=self.search_var, width=300)
        self.search_entry.pack(side="left", padx=(0, 10))
        
        self.region_var = ctk.StringVar(value="Europe")
        self.region_opt = ctk.CTkOptionMenu(self.header, values=["All Regions", "Europe", "USA", "Japan"], 
                                            command=self._on_filter_change, variable=self.region_var, width=120)
        self.region_opt.pack(side="left", padx=10)
        
        self.exclude_switch = ctk.CTkSwitch(self.header, text="No Demo/Beta", command=self._on_filter_change)
        self.exclude_switch.select()
        self.exclude_switch.pack(side="left", padx=10)
        
        # Info Label
        self.info_label = ctk.CTkLabel(self, text="Select a console to begin", font=ctk.CTkFont(size=16))
        self.info_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 10))
        
        # Treeview
        self.tree_frame = ctk.CTkFrame(self)
        self.tree_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)
        
        self._setup_tree()
        
        # Actions
        self.action_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=20)
        
        self.best_btn = ctk.CTkButton(self.action_frame, text="Load Best Games", fg_color="green", command=self._load_best_games)
        self.best_btn.pack(side="left", padx=10)
        
        self.add_btn = ctk.CTkButton(self.action_frame, text="Add to Queue ➡️", command=self._add_selected)
        self.add_btn.pack(side="right")
        
        ctk.CTkButton(self.action_frame, text="Select All", width=100, fg_color="#444", command=self._toggle_select_all).pack(side="right", padx=10)

    def _setup_tree(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", fieldbackground="#2b2b2b", foreground="white", 
                        borderwidth=0, rowheight=30, font=("Arial", 12))
        style.configure("Treeview.Heading", background="#1f1f1f", foreground="white", relief="flat", font=("Arial", 12, "bold"))
        style.map("Treeview", background=[('selected', '#1f538d')])
        
        self.tree = ttk.Treeview(self.tree_frame, columns=("Select", "RA", "Name"), show="headings", selectmode="extended")
        self.tree.heading("Select", text="[x]")
        self.tree.heading("RA", text="RA")
        self.tree.heading("Name", text="Game Title")
        
        self.tree.column("Select", width=40, anchor="center")
        self.tree.column("RA", width=40, anchor="center")
        self.tree.column("Name", width=450)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        self.tree.bind("<Button-1>", self._on_click)

    def load_console(self, category, console_key):
        self.current_category = category
        self.current_console = console_key
        
        name = self.app.rom_manager.consoles[category][console_key]['name']
        self.info_label.configure(text=f"Loading {name}...")
        
        # Async load
        threading.Thread(target=self._fetch_and_show, args=(category, console_key)).start()

    def _fetch_and_show(self, category, console_key):
        self.app.rom_manager.fetch_file_list(category, console_key)
        self.after(0, self._apply_filters)

    def _on_filter_change(self, *args):
        if hasattr(self, 'current_console'):
            self._apply_filters()

    def _apply_filters(self):
        region_map = {
            "Europe": ["(Europe)", "(France)", "(Fr)", "(Germany)", "(De)", "(Spain)", "(Es)", "(Italy)", "(It)"],
            "USA": ["(USA)", "(US)"],
            "Japan": ["(Japan)", "(JP)", "(In)"],
            "All Regions": []
        }
        
        self.app.rom_manager.filters["region"] = region_map.get(self.region_var.get(), [])
        self.app.rom_manager.filters["exclude"] = ["(Demo)", "(Beta)", "(Proto)", "(Kiosk)", "(Sample)", "(Unl)"] if self.exclude_switch.get() else []
        
        query = self.search_var.get()
        results = self.app.rom_manager.search(self.current_category, self.current_console, query)
        
        self._populate_tree(results)

    def _populate_tree(self, files):
        self.tree.delete(*self.tree.get_children())
        self.current_results = files
        
        # Fetch RA support
        ra_games = self.app.ra_manager.get_supported_games(self.current_console)
        
        for f in files:
            is_ra = self.app.ra_manager.is_compatible(f, ra_games)
            ra_icon = "🏆" if is_ra else "❌"
            self.tree.insert("", "end", values=("☐", ra_icon, f))
            
        self.info_label.configure(text=f"{len(files)} games found")

    def _on_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            col = self.tree.identify_column(event.x)
            if col == "#1":
                row_id = self.tree.identify_row(event.y)
                if row_id:
                    vals = self.tree.item(row_id, "values")
                    new_val = "☑" if vals[0] == "☐" else "☐"
                    self.tree.item(row_id, values=(new_val, vals[1], vals[2]))

    def _toggle_select_all(self):
        children = self.tree.get_children()
        if not children: return
        first = self.tree.item(children[0], "values")[0]
        new = "☑" if first == "☐" else "☐"
        for item in children:
            v = self.tree.item(item, "values")
            self.tree.item(item, values=(new, v[1], v[2]))

    def _add_selected(self):
        items = []
        # Check checkboxes
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            if vals[0] == "☑":
                items.append(vals[2])
        
        # Check selection if no checkboxes
        if not items:
            for item in self.tree.selection():
                vals = self.tree.item(item, "values")
                items.append(vals[2])
                
        if items and self.on_add_queue:
            self.on_add_queue(self.current_category, self.current_console, items)

    def _load_best_games(self):
        # Implementation similar to main logic but simplified helper
        if not hasattr(self, 'current_console'): return
        
        config = self.app.rom_manager.consoles[self.current_category][self.current_console]
        best_list = config.get("best_games", [])
        
        # We need to filter current results to find matches
        matches = []
        available = self.app.rom_manager.fetch_file_list(self.current_category, self.current_console) # get raw list
        
        # Simple match
        found_set = set()
        for bg in best_list:
            for av in available:
                if bg.lower() in av.lower():
                    # Check if allowed by current filters?
                    # Ideally yes. But "Best Games" usually implies overriding filters?
                    # Let's stick to showing them in the list.
                    if av not in found_set:
                        matches.append(av)
                        found_set.add(av)
                        break # Find first match for this game? Or all? User might want revisions.
        
        self.search_var.set("") # Clear search
        self._populate_tree(matches)
