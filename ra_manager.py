import requests
import json
import os
import re
from difflib import SequenceMatcher

class RetroAchievementsManager:
    BASE_URL = "https://retroachievements.org/API"
    
    # Mapping Renifleur Console Names -> RA Console IDs
    CONSOLE_MAP = {
        # Romifleur Keys
        "NES": 7,
        "SNES": 3,
        "N64": 2,
        "GameCube": 16,
        "GB": 4,
        "GBC": 6,
        "GBA": 5,
        "NDS": 18,
        "MasterSystem": 11,
        "MegaDrive": 1,
        "Saturn": 39,
        "Dreamcast": 40,
        "GameGear": 15,
        "PS1": 12,
        "PSP": 41,
        "PS2": 21,
        "NeoGeo": 24, 
        "PC_Engine": 8,
        "Atari2600": 25,
        "Wii": 19,
        "3DS": 62,

        # # Full RA List (IDs based on API fetch)
        # "Genesis/Mega Drive": 1,
        # "Nintendo 64": 2,
        # "SNES/Super Famicom": 3,
        # "Game Boy": 4,
        # "Game Boy Advance": 5,
        # "Game Boy Color": 6,
        # "NES/Famicom": 7,
        # "PC Engine/TurboGrafx-16": 8,
        # "Sega CD": 9,
        # "32X": 10,
        # "Master System": 11,
        # "PlayStation": 12,
        # "Atari Lynx": 13,
        # "Neo Geo Pocket": 14,
        # "Game Gear": 15,
        # "GameCube": 16,
        # "Atari Jaguar": 17,
        # "Nintendo DS": 18,
        # "Wii": 19,
        # "Wii U": 20,
        # "PlayStation 2": 21,
        # "Xbox": 22,
        # "Magnavox Odyssey 2": 23,
        # "Pokemon Mini": 24,
        # "Atari 2600": 25,
        # "DOS": 26,
        # "Arcade": 27,
        # "Virtual Boy": 28,
        # "MSX": 29,
        # "Commodore 64": 30,
        # "ZX81": 31,
        # "Oric": 32,
        # "SG-1000": 33,
        # "VIC-20": 34,
        # "Amiga": 35,
        # "Atari ST": 36,
        # "Amstrad CPC": 37,
        # "Apple II": 38,
        # "Saturn": 39,
        # "Dreamcast": 40,
        # "PlayStation Portable": 41,
        # "Philips CD-i": 42,
        # "3DO Interactive Multiplayer": 43,
        # "ColecoVision": 44,
        # "Intellivision": 45,
        # "Vectrex": 46,
        # "PC-8000/8800": 47,
        # "PC-9800": 48,
        # "PC-FX": 49,
        # "Atari 5200": 50,
        # "Atari 7800": 51,
        # "Sharp X68000": 52,
        # "WonderSwan": 53,
        # "Cassette Vision": 54,
        # "Super Cassette Vision": 55,
        # "Neo Geo CD": 56,
        # "Fairchild Channel F": 57,
        # "FM Towns": 58,
        # "ZX Spectrum": 59,
        # "Game & Watch": 60,
        # "Nokia N-Gage": 61,
        # "Nintendo 3DS": 62,
        # "Watara Supervision": 63,
        # "Sharp X1": 64,
        # "TIC-80": 65,
        # "Thomson TO8": 66,
        # "PC-6000": 67,
        # "Sega Pico": 68,
        # "Mega Duck": 69,
        # "Zeebo": 70,
        # "Arduboy": 71,
        # "WASM-4": 72,
        # "Arcadia 2001": 73,
        # "Interton VC 4000": 74,
        # "Elektor TV Games Computer": 75,
        # "PC Engine CD/TurboGrafx-CD": 76,
        # "Atari Jaguar CD": 77,
        # "Nintendo DSi": 78,
        # "TI-83": 79,
        # "Uzebox": 80,
        # "Famicom Disk System": 81,
        # "Hubs": 100,
        # "Events": 101,
        # "Standalone": 102
    }

    def __init__(self, api_key=None):
        self.api_key = api_key
        self.cache_file = "ra_cache.json"
        self.cache = self._load_cache()
        
    def _load_cache(self):
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_cache(self):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=4)
        except Exception as e:
            print(f"Error saving RA cache: {e}")

    def get_console_id(self, console_key):
        # Handle special cases if needed
        if console_key == "NeoGeo": # Renifleur's NeoGeo is actually NGPC url
            return 29 # Neo Geo Pocket Color
        return self.CONSOLE_MAP.get(console_key)

    def fetch_game_list(self, console_id):
        """Fetch game list from RA API or Cache."""
        if not self.api_key:
            return []

        str_id = str(console_id)
        if str_id in self.cache:
            return self.cache[str_id]

        print(f"Fetching RA list for Console ID {console_id}...")
        try:
            url = f"{self.BASE_URL}/API_GetGameList.php"
            params = {
                "y": self.api_key,
                "i": console_id,
                "f": 1 # Only games with achievements
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Simplify data for cache: Title only is enough for matching?
            # Or Title + ID
            simplified = [{"Title": g["Title"], "ID": g["ID"]} for g in data]
            
            self.cache[str_id] = simplified
            self._save_cache()
            return simplified
            
        except Exception as e:
            print(f"RA API Error: {e}")
            return []

    def get_supported_games(self, console_key):
        cid = self.get_console_id(console_key)
        if not cid: return []
        return self.fetch_game_list(cid)

    def is_compatible(self, filename, ra_games):
        """
        Check if filename likely matches a game in the RA list.
        Uses basic cleaning and fuzzy matching.
        """
        # 1. Clean filename (remove extension, regions, tags)
        clean_name = os.path.splitext(filename)[0]
        # Remove (...) and [...] tags
        clean_name = re.sub(r'\s*[\(\[].*?[\)\]]', '', clean_name).strip().lower()
        
        # 2. Heuristic Check
        # Most No-Intro names match RA titles closely.
        for game in ra_games:
            ra_title = game["Title"].lower()
            # Remove tags from RA title too if any
            ra_title = re.sub(r'\s*[\(\[].*?[\)\]]', '', ra_title).strip()
            
            if clean_name == ra_title:
                return True
                
            # If standard exact match fails, try simple inclusion for long titles
            if len(clean_name) > 10 and clean_name in ra_title:
                return True
                
        return False
