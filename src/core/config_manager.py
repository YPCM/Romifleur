
import os
import json
import sys

class ConfigManager:
    def __init__(self, settings_file="settings.json", consoles_file="consoles.json"):
        self.settings_file = settings_file
        self.consoles_file = consoles_file
        self.settings = self.load_settings()
        self.consoles = self.load_consoles()

    def get_resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def load_settings(self):
        """Load user settings."""
        # Check standard data path first? For now keep local compatibility
        path = os.path.join(os.getcwd(), "data", self.settings_file)
        if not os.path.exists(path):
            path = self.settings_file # Fallback to root

        try:
            if os.path.exists(path):
                with open(path, "r") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading settings: {e}")
        
        return {"roms_path": "ROMs", "ra_api_key": ""}

    def save_settings(self):
        """Save user settings."""
        # Save to data/ if it exists, else root
        data_dir = os.path.join(os.getcwd(), "data")
        if os.path.exists(data_dir):
            path = os.path.join(data_dir, self.settings_file)
        else:
            path = self.settings_file

        try:
            with open(path, "w") as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_consoles(self):
        """Load static console catalog."""
        try:
            # Consoles file is a resource, not user data
            # Check config/ folder or root or resource path
            paths_to_try = [
                self.get_resource_path(os.path.join("config", self.consoles_file)),
                self.get_resource_path(self.consoles_file),
                "consoles.json"
            ]
            
            for path in paths_to_try:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading consoles: {e}")
            return {}

    def get_download_path(self):
        path = self.settings.get("roms_path", "ROMs")
        if not os.path.isabs(path):
            path = os.path.abspath(path)
            
        if not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
            except:
                default = os.path.abspath("ROMs")
                os.makedirs(default, exist_ok=True)
                return default
        return path
