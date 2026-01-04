import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
import threading
from rom_manager import RomManager

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Romifleur - Ultimate ROM Downloader")
        self.geometry("1000x600")
        
        self.manager = RomManager()
        self.selected_category = None
        self.selected_console = None
        
        self._setup_ui()
        
    def _setup_ui(self):
        # Layout: grid 1 row, 2 cols (Sidebar, Main)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # --- Sidebar ---
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="Romifleur", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(padx=20, pady=20)
        
        # Scrollable list for consoles
        self.console_list_frame = ctk.CTkScrollableFrame(self.sidebar, label_text="Consoles")
        self.console_list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self._populate_console_list()
        
        # --- Main Area ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(2, weight=1) # List area expands
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Header (Search & Filters)
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self._on_search_change)
        self.search_entry = ctk.CTkEntry(self.header_frame, placeholder_text="Search games...", textvariable=self.search_var, width=300)
        self.search_entry.pack(side="left", padx=(0, 10))
        
        # Region Dropdown
        self.region_var = ctk.StringVar(value="Europe")
        self.region_option = ctk.CTkOptionMenu(self.header_frame, values=["All Regions", "Europe", "USA", "Japan"], 
                                             command=self._refresh_list, variable=self.region_var, width=120)
        self.region_option.pack(side="left", padx=10)

        self.exclude_switch = ctk.CTkSwitch(self.header_frame, text="No Demo/Beta", command=self._refresh_list)
        self.exclude_switch.select()
        self.exclude_switch.pack(side="left", padx=10)
        
        # Info Label (Selected Console)
        self.info_label = ctk.CTkLabel(self.main_frame, text="Select a console to begin", font=ctk.CTkFont(size=16))
        self.info_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 10))

        # Game List (Treeview style using standard tk for performance with many items, styled dark)
# ... (skip to _refresh_list)
# We need to find _refresh_list which is further down.
# replace_file_content works on contiguous blocks. 
# I will use multi_replace to handle both the UI setup and the logic update.

        # Game List (Treeview style using standard tk for performance with many items, styled dark)
        # CustomTkinter doesn't have a native Treeview yet, wrapping ttk.Treeview
        self.tree_frame = ctk.CTkFrame(self.main_frame)
        self.tree_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.tree_frame.grid_columnconfigure(0, weight=1)
        self.tree_frame.grid_rowconfigure(0, weight=1)
        
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("Treeview", background="#2b2b2b", fieldbackground="#2b2b2b", foreground="white", borderwidth=0)
        self.style.configure("Treeview.Heading", background="#1f1f1f", foreground="white", relief="flat")
        self.style.map("Treeview", background=[('selected', '#1f538d')])
        
        # Add "Select" column for checkboxes
        self.tree = ttk.Treeview(self.tree_frame, columns=("Select", "Name", "Status"), show="headings", selectmode="extended")
        self.tree.heading("Select", text="[x]")
        self.tree.heading("Name", text="Game Title")
        self.tree.heading("Status", text="Status")
        
        self.tree.column("Select", width=40, anchor="center")
        self.tree.column("Name", width=400)
        self.tree.column("Status", width=100, anchor="center")
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.bind("<Button-1>", self._on_tree_click) # Bind click for checkboxes
        
        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        
        # Actions Frame
        self.action_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.action_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=20)
        
        self.download_btn = ctk.CTkButton(self.action_frame, text="Download Selected", command=self._start_download)
        self.download_btn.pack(side="right")

        self.select_all_btn = ctk.CTkButton(self.action_frame, text="Select All", command=self._select_all_toggle, width=100, fg_color="#444")
        self.select_all_btn.pack(side="right", padx=10)
        
        self.best_btn = ctk.CTkButton(self.action_frame, text="Load Best Games", fg_color="green", command=self._load_best_games)
        self.best_btn.pack(side="left", padx=10)
        
        self.progress_bar = ctk.CTkProgressBar(self.action_frame, orientation="horizontal")
        self.progress_bar.set(0)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=20)
        self.progress_bar.pack_forget() # Hide initially

    def _populate_console_list(self):
        # Group by Category
        # But for simpler UI, just flat list or headers?
        # Let's use simple buttons for now.
        
        consoles = self.manager.get_console_list() # (Cat, Key, Name)
        # Sort by Name
        consoles.sort(key=lambda x: x[2])
        
        for cat, key, name in consoles:
            btn = ctk.CTkButton(self.console_list_frame, text=name, anchor="w", fg_color="transparent", border_width=1,
                                command=lambda c=cat, k=key, n=name: self._select_console(c, k, n))
            btn.pack(fill="x", pady=2)

    def _select_console(self, category, key, name):
        self.selected_category = category
        self.selected_console = key
        self.info_label.configure(text=f"Loading {name}...")
        self.update()
        
        # Disable search temporarily?
        threading.Thread(target=self._fetch_and_show, args=(category, key, name)).start()

    def _fetch_and_show(self, category, key, name):
        # Fetch (Scrape)
        self.manager.fetch_file_list(category, key)
        
        # Update UI in main thread
        self.after(0, lambda: self._update_view_after_load(name))

    def _update_view_after_load(self, name):
        self.info_label.configure(text=f"{name} - {len(self.manager.cache.get(f'{self.selected_category}_{self.selected_console}', []))} files found")
        self._refresh_list()

    def _refresh_list(self, *args):
        if not self.selected_console: return
        
        # Region Mapping
        region_map = {
            "Europe": ["(Europe)", "(France)", "(Fr)", "(Germany)", "(De)", "(Spain)", "(Es)", "(Italy)", "(It)"],
            "USA": ["(USA)", "(US)"],
            "Japan": ["(Japan)", "(JP)", "(In)"], # (In) sometimes used? No, keep it safe.
            "All Regions": []
        }
        selected_region = self.region_var.get()
        
        # Update filters in manager
        self.manager.filters["region"] = region_map.get(selected_region, [])
        self.manager.filters["exclude"] = ["(Demo)", "(Beta)", "(Proto)", "(Kiosk)", "(Sample)", "(Unl)"] if self.exclude_switch.get() else []
        self.manager.filters["deduplicate"] = True # Always True for GUI to look clean?
        
        query = self.search_var.get()
        results = self.manager.search(self.selected_category, self.selected_console, query)
        
        # Populate Tree
        self.tree.delete(*self.tree.get_children())
        for r in results:
            self.tree.insert("", "end", values=("☐", r, "Online"))

    def _on_tree_click(self, event):
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x)
            if column == "#1": # The 'Select' column
                item_id = self.tree.identify_row(event.y)
                current_values = self.tree.item(item_id, "values")
                if current_values:
                    # Toggle checkbox
                    new_val = "☑" if current_values[0] == "☐" else "☐"
                    self.tree.item(item_id, values=(new_val, current_values[1], current_values[2]))
                    return "break" # Prevent default selection behavior if clicking checkbox

    def _select_all_toggle(self):
        # Toggle based on first item
        children = self.tree.get_children()
        if not children: return
        
        first_val = self.tree.item(children[0], "values")[0]
        new_val = "☑" if first_val == "☐" else "☐"
        
        for item in children:
            vals = self.tree.item(item, "values")
            self.tree.item(item, values=(new_val, vals[1], vals[2]))

    def _on_search_change(self, *args):
        # Debounce? For now direct call is fine for local list filtering (fast enough implementation in python)
        self._refresh_list()
        
    def _load_best_games(self):
        if not self.selected_console: return
        # Logic to filter by BEST_GAMES whitelist (TODO: Add whitelist to consoles.json)
        # For now, just a placeholder or filter the query with the whitelist from manager?
        
        # We need the list from the catalog data
        config = self.manager.consoles.get(self.selected_category, {}).get(self.selected_console, {})
        best = config.get("best_games", [])
        
        # Filter current list to only showing these
        # Or just replace the tree view?
        # Actually, let's just populate the tree with these specifically IF they exist in possible downloads
        
        # Currently the 'search' method filters the *available* files. 
        # Ideally we search for these names.
        
        self.tree.delete(*self.tree.get_children())
        available = self.manager.cache.get(f"{self.selected_category}_{self.selected_console}", [])
        
        # Fuzzy match or Containment?
        for bg in best:
            # Find matching file in available
            for av in available:
                if bg.lower() in av.lower() and self.manager._get_score(av) > 0: # Simple check
                    self.tree.insert("", "end", values=("☐", av, "Best Of"))

    def _start_download(self):
        # Gather checked items AND selected items (hybrid approach or strictly checked?)
        # Let's prioritize checked items. If none checked, use selection.
        
        checked_items = []
        for item in self.tree.get_children():
            vals = self.tree.item(item, "values")
            if vals[0] == "☑":
                checked_items.append(vals[1])
                
        if not checked_items:
            # Fallback to standard selection
            selected_items = self.tree.selection()
            if selected_items:
               checked_items = [self.tree.item(i)['values'][1] for i in selected_items]
        
        if not checked_items: return
        
        filenames = checked_items
        
        self.download_btn.configure(state="disabled", text="Downloading Batch...")
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=20)
        self.progress_bar.set(0)
        
        threading.Thread(target=self._batch_download_worker, args=(filenames,)).start()

    def _batch_download_worker(self, filenames):
        import concurrent.futures
        
        total = len(filenames)
        completed = 0
        max_workers = 5 # Parallel downloads
        
        lock = threading.Lock()
        
        def update_overall_progress(file_done):
            nonlocal completed
            with lock:
                if file_done:
                    completed += 1
                prog = completed / total
                status = f"Downloading... [{completed}/{total}]"
                self.after(0, lambda p=prog, s=status: self._update_progress(p, s))

        def download_task(fname):
            # We ignore individual file progress for the global bar to avoid jitter
            # But we could log it or show it if we had a detailed view.
            # For now, just wait for completion.
            self.manager.download_file(self.selected_category, self.selected_console, fname, progress_callback=None)
            update_overall_progress(True)

        # Initial Status
        self.after(0, lambda: self._update_progress(0, f"Starting {total} downloads..."))

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(download_task, f) for f in filenames]
            concurrent.futures.wait(futures)
        
        self.after(0, lambda: self._finish_download(True))

    def _update_progress(self, progress, status):
        self.progress_bar.set(progress)
        self.info_label.configure(text=status)

    def _finish_download(self, success):
        self.download_btn.configure(state="normal", text="Download Selected")
        self.progress_bar.pack_forget()
        self.info_label.configure(text="Batch Download Complete!")

if __name__ == "__main__":
    app = App()
    app.mainloop()
