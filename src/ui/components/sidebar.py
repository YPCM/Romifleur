
import customtkinter as ctk
import os
from ...utils.image_utils import ImageUtils

class Sidebar(ctk.CTkFrame):
    def __init__(self, master, app_context, on_console_select, **kwargs):
        super().__init__(master, **kwargs)
        self.app = app_context
        self.on_console_select = on_console_select
        
        self.category_frames = {}
        self.category_buttons = {}
        self.active_btn = None
        
        self._setup_ui()
        self._populate_list()

    def _setup_ui(self):
        # Logo
        self._setup_logo()
        
        # Open Folder Button
        self.open_folder_btn = ctk.CTkButton(self, text="Open ROMs Folder", fg_color="#555", command=self._open_roms_folder)
        self.open_folder_btn.pack(padx=20, pady=(0, 10))

        # Settings (Bottom)
        self.settings_btn = ctk.CTkButton(self, text="Settings ⚙️", fg_color="transparent", border_width=1, 
                                          command=self._open_settings)
        self.settings_btn.pack(side="bottom", padx=20, pady=20, fill="x")
        
        # Console List
        self.console_list_frame = ctk.CTkScrollableFrame(self, label_text="Consoles")
        self.console_list_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def _setup_logo(self):
        # Try to find logo in assets or root
        # We need a standard way to find assets. 
        # For now, look in current directory as per original code, or assets/
        candidates = ["logo-romifleur.png", "Romifleur_logo.png", "assets/logo-romifleur.png"]
        logo_img = None
        
        for c in candidates:
            # Check relative to CWD (root)
            path = os.path.abspath(c)
            logo_img = ImageUtils.load_image(path, size=(180, 180))
            if logo_img: break
            
        if logo_img:
            self.logo_label = ctk.CTkLabel(self, text="", image=logo_img)
        else:
            self.logo_label = ctk.CTkLabel(self, text="Romifleur", font=ctk.CTkFont(size=20, weight="bold"))
        
        self.logo_label.pack(padx=20, pady=20)

    def _populate_list(self):
        consoles = self.app.rom_manager.consoles
        # Iterate over categories
        for category, consoles_data in consoles.items():
            self._create_category_group(category, consoles_data)

    def _create_category_group(self, category, consoles_data):
        group_frame = ctk.CTkFrame(self.console_list_frame, fg_color="transparent")
        group_frame.pack(fill="x", pady=2)

        # Header Button
        header_frame = ctk.CTkFrame(group_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=0)
        
        content_frame = ctk.CTkFrame(group_frame, fg_color="transparent")
        content_frame.pack(fill="x", padx=10, pady=0)
        
        def toggle_category(cat=category):
            frame = self.category_frames[cat]
            btn = self.category_buttons[cat]
            if frame.winfo_viewable():
                frame.pack_forget()
                btn.configure(text=f"▶ {cat}")
            else:
                frame.pack(fill="x", padx=10, pady=0)
                btn.configure(text=f"▼ {cat}")

        btn = ctk.CTkButton(header_frame, text=f"▼ {category}", fg_color="#333", hover_color="#444", 
                            anchor="w", command=toggle_category, font=("Arial", 13, "bold"))
        btn.pack(fill="x")
        
        self.category_frames[category] = content_frame
        self.category_buttons[category] = btn

        sorted_keys = sorted(consoles_data.keys(), key=lambda k: consoles_data[k]['name'])
        for key in sorted_keys:
            name = consoles_data[key].get('name', key)
            c_btn = ctk.CTkButton(content_frame, text=name, anchor="w", fg_color="transparent", 
                                  hover_color="#3A3A3A", height=24,
                                  command=lambda col=category, k=key: self._handle_selection(col, k))
            c_btn.pack(fill="x", pady=1)
            
            # Store if we need to access via key later, but for now active_btn is enough tracking via clicking
            # Actually we need the button instance to change its color inside lambda, 
            # but better to pass the click event or binding, or just better structure.
            # Lambda constraints: We can't easily pass self.c_btn because it's overwritten
            # Let's use a factory or immediate binding. 
            
            # Better approach:
            self._bind_button(c_btn, category, key)

    def _bind_button(self, btn, category, key):
        btn.configure(command=lambda: self._handle_selection(btn, category, key))

    def _handle_selection(self, btn, category, key):
        # Reset previous
        if self.active_btn:
            self.active_btn.configure(fg_color="transparent")
            
        # Set new
        self.active_btn = btn
        self.active_btn.configure(fg_color=["#3a7ebf", "#1f538d"]) # Standard active blue
        
        # Callback
        self.on_console_select(category, key)

    def _open_roms_folder(self):
        path = self.app.config.get_download_path()
        import platform
        import subprocess
        
        if not os.path.exists(path):
            return
            
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def _open_settings(self):
        # Import dynamically to avoid circular import if SettingsWindow is in same package
        # For now assume we pass a callback or signal to Main Window to open settings? 
        # Or just open a Toplevel here.
        from ...ui.settings_window import SettingsWindow
        SettingsWindow(self.winfo_toplevel(), self.app)
