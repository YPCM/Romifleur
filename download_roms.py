import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import unquote, urljoin
import tqdm
import sys
import zipfile
import py7zr
import shutil
import concurrent.futures

# Configuration
ROM_DIR = "ROMs"
MAX_WORKERS = 5  # Number of parallel downloads

PLATFORMS = {
    "GBA": {
        "url": "https://archive.org/download/ef_gba_no-intro_2024-02-21/",
        "exts": (".zip", ".7z"),
    },
    "NDS": {
        "urls": [
            "https://archive.org/download/ni-n-ds-dec_202401/",
            "https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Nintendo%20DS%20(Decrypted)/",
        ],
        "exts": (".zip", ".7z", ".nds"),
    },
    "PS1": {
        "url": "https://myrient.erista.me/files/Redump/Sony%20-%20PlayStation/",
        "exts": (".zip", ".7z", ".chd"),
    },
    "N64": {
         "url": "https://myrient.erista.me/files/No-Intro/Nintendo%20-%20Nintendo%2064%20(BigEndian)/",
         "exts": (".zip", ".7z", ".z64", ".n64"),
    },
    "GameCube": {
        "url": "https://myrient.erista.me/files/Redump/Nintendo%20-%20GameCube%20-%20NKit%20RVZ%20%5Bzstd-19-128k%5D/",
        "exts": (".zip", ".7z", ".rvz", ".iso"),
    },
    "MegaDrive": {
        "url": "https://myrient.erista.me/files/No-Intro/Sega%20-%20Mega%20Drive%20-%20Genesis/",
        "exts": (".zip", ".7z", ".md", ".bin"),
    },
    "Dreamcast": {
        "url": "https://myrient.erista.me/files/Redump/Sega%20-%20Dreamcast/",
        "exts": (".zip", ".7z", ".chd", ".gdi"),
    },
    "PSP": {
         "urls": [
             "https://archive.org/download/ef_sony_psp_part_1of3/",
             "https://archive.org/download/ef_sony_psp_part_2of3/",
             "https://archive.org/download/ef_sony_psp_part_3of3/",
         ],
         "exts": (".iso", ".zip", ".7z"),
    },
    "Saturn": {
        "url": "https://myrient.erista.me/files/Redump/Sega%20-%20Saturn/",
        "exts": (".zip", ".7z", ".bin", ".cue"),
    }
}

FILTERS = ["(Europe)", "(France)", "(Fr)"]
EXCLUDE_FILTERS = ["(Demo)", "(Beta)", "(Proto)", "(Kiosk)", "(Sample)", "(Unl)"]
BEST_GAMES_ONLY = True

# ... (BEST_GAMES dict remains unchanged, skipping lines for brevity if possible, but replace_file_content needs contiguous block. 
# actually I can just target the area around FILTERS and should_download.
# Let me look at the file content again. I need to be careful not to overwrite the massive BEST_GAMES dict if I can avoid it.
# BEST_GAMES starts at line 61. FILTERS is at 58.
# should_download is at 108.
# I will make two edits in one call if possible using multi_replace? No, replace_file_content is single block.
# strict replace_file_content usage.
# I will allow myself to use multi_replace for this.



BEST_GAMES = {
    # ... (previous entries) ...
    "Saturn": [
        "Panzer Dragoon Saga", "Nights Into Dreams", "Sega Rally", "Virtua Fighter 2", "Radiant Silvergun",
        "Guardian Heroes", "Saturn Bomberman", "Panzer Dragoon Zwei", "Shining Force III", "Dragon Force",
        "Street Fighter Alpha 3", "Legend of Oasis", "X-Men Vs. Street Fighter", "Burning Rangers", "Fighters Megamix"
    ],
    "GBA": [
        "Aria of Sorrow", "Metroid Fusion", "Minish Cap", "Golden Sun", "Advance Wars", 
        "Superstar Saga", "Tactics Advance", "Pokemon Emerald", "Zero Mission", 
        "Link to the Past", "WarioWare", "Fire Emblem", "Super Circuit", "Super Mario Advance 4", "Astro Boy"
    ],
    "NDS": [
        "Chinatown Wars", "Chrono Trigger", "Mario Kart DS", "Bowser's Inside Story", "Phantom Hourglass",
        "Dual Strike", "Dawn of Sorrow", "World Ends with You", "New Super Mario Bros", "HeartGold", "SoulSilver",
        "Ghost Trick", "999", "Professor Layton", "Dragon Quest IX", "Elite Beat Agents"
    ],
    "PS1": [
        "Metal Gear Solid", "Final Fantasy VII", "Symphony of the Night", "Tekken 3", "Tony Hawk's Pro Skater 2",
        "Resident Evil 2", "Gran Turismo 2", "Silent Hill", "Crash Bandicoot 3", "Warped", "Spyro the Dragon",
        "Tomb Raider", "Vagrant Story", "Final Fantasy IX", "Chrono Cross", "Medal of Honor"
    ],
    "N64": [
        "Ocarina of Time", "Super Mario 64", "GoldenEye", "Majora's Mask", "Banjo-Kazooie",
        "Mario Kart 64", "Perfect Dark", "Super Smash Bros", "Paper Mario", "Lylat Wars", "Star Fox 64",
        "Diddy Kong Racing", "Bad Fur Day", "Wave Race", "Donkey Kong 64", "1080"
    ],
    "GameCube": [
        "Metroid Prime", "Wind Waker", "Resident Evil 4", "Melee", "Thousand-Year Door",
        "Eternal Darkness", "Double Dash", "Twilight Princess", "SoulCalibur II", "Super Mario Sunshine",
        "Pikmin", "Twin Snakes", "Luigi's Mansion", "Path of Radiance", "Sands of Time"
    ],
    "Dreamcast": [
        "SoulCalibur", "Jet Set Radio", "Jet Grind Radio", "Skies of Arcadia", "Crazy Taxi", "Marvel vs. Capcom 2",
        "Code: Veronica", "Phantasy Star Online", "Shenmue", "Sonic Adventure", "Power Stone 2",
        "Ikaruga", "Samba de Amigo", "Quake III", "Rez"
    ],
    "PSP": [
        "Ghost of Sparta", "Persona 3", "Crisis Core", "Peace Walker", "Monster Hunter Freedom Unite",
        "Birth by Sleep", "Lumines", "War of the Lions", "Vice City Stories", "Liberty City Stories",
        "Chains of Olympus", "Jeanne d'Arc", "Valkyria Chronicles 2", "Tactics Ogre", "Daxter"
    ],
    "MegaDrive": [
        "Sonic the Hedgehog 2", "Streets of Rage 2", "Gunstar Heroes", "Phantasy Star IV", "Bloodlines", "New Generation",
        "Sonic 3", "Sonic & Knuckles", "Hard Corps", "Probotector", "Shining Force II", "Rocket Knight Adventures",
        "Aladdin", "Beyond Oasis", "Story of Thor", "Comix Zone", "Shinobi III", "Golden Axe"
    ]
}

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def should_download(filename, platform):
    # 0. Check Exclusions
    for ex in EXCLUDE_FILTERS:
        if ex.lower() in filename.lower():
            return False

    # 1. Filter by Region/Language
    region_match = False
    for f in FILTERS:
        if f.lower() in filename.lower():
            region_match = True
            break
    if not region_match:
        return False

    # 2. Filter by Best Games (if enabled)
    if BEST_GAMES_ONLY:
        if platform not in BEST_GAMES:
            return True # If no best list, download all matching filters (or maybe False? Let's say True for now)
        
        game_match = False
        allowed_games = BEST_GAMES[platform]
        for game_keyword in allowed_games:
            # Simple substring match
            if game_keyword.lower() in filename.lower():
                game_match = True
                break
        
        if not game_match:
            return False

    return True

def get_links(url, exts, platform):
    print(f"Fetching list from {url}...")
    try:
        r = requests.get(url)
        r.raise_for_status()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []

    soup = BeautifulSoup(r.text, 'html.parser')
    links = []
    for a in soup.find_all('a'):
        href = a.get('href')
        if not href:
            continue
        filename = unquote(href)
        
        if filename.endswith("/") or filename == "../":
            continue
            
        if not filename.lower().endswith(tuple(exts)):
            continue

        if should_download(filename, platform):
            full_url = urljoin(url, href)
            links.append((filename, full_url))
            
    return links

def is_already_processed(filename, dest_dir):
    """
    Checks if the file is already downloaded or extracted.
    1. Check if the archive exists.
    2. Check if a file/folder with the same base name exists (indicating extraction).
    """
    if os.path.exists(os.path.join(dest_dir, filename)):
        return True
    
    base_name = os.path.splitext(filename)[0]
    
    # Check for any file in dest_dir that has the same base name (ignoring extension)
    # This covers games extracted to .iso, .nds, .gba, etc.
    try:
        for f in os.listdir(dest_dir):
            if os.path.splitext(f)[0] == base_name:
                return True
    except OSError:
        pass
        
    return False

def extract_and_cleanup(filepath):
    """Extracts zip/7z and deletes the archive."""
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    base_name, ext = os.path.splitext(filename)
    
    try:
        extracted = False
        if ext.lower() == ".zip":
            try:
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    zip_ref.extractall(directory)
                extracted = True
            except zipfile.BadZipFile:
                print(f"Error: {filename} is a bad zip file. Deleting to retry later.")
                os.remove(filepath)
                return

        elif ext.lower() == ".7z":
            try:
                with py7zr.SevenZipFile(filepath, 'r') as archive:
                    archive.extractall(directory)
                extracted = True
            except py7zr.exceptions.Bad7zFile:
                print(f"Error: {filename} is a bad 7z file. Deleting to retry later.")
                os.remove(filepath)
                return
            
        if extracted:
            os.remove(filepath)
        
    except Exception as e:
        print(f"Error extracting {filename}: {e}")

def cleanup_temp_files(root_dir):
    print("Cleaning up residual .tmp files...")
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".tmp"):
                filepath = os.path.join(root, file)
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"Could not remove {filepath}: {e}")

def download_and_process(url, dest_dir, filename, progress_bar):
    filepath = os.path.join(dest_dir, filename)
    temp_filepath = filepath + ".tmp"
    
    try:
        if is_already_processed(filename, dest_dir):
            progress_bar.update(1)
            return

        tqdm.tqdm.write(f"[{filename}] Starting download...")
        
        # Added timeout to prevent hanging indefinitely
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status() 
        
        total_size = int(response.headers.get('content-length', 0))
        size_str = f"{total_size / (1024*1024):.2f} MB" if total_size > 0 else "Unknown size"
        tqdm.tqdm.write(f"[{filename}] Size: {size_str}")
        
        with open(temp_filepath, 'wb') as file:
            for data in response.iter_content(1024*1024): 
                file.write(data)
        
        os.replace(temp_filepath, filepath)
        tqdm.tqdm.write(f"[{filename}] Download complete.")
        
        if filename.lower().endswith(('.zip', '.7z')):
            tqdm.tqdm.write(f"[{filename}] Extracting...")
            extract_and_cleanup(filepath)
            tqdm.tqdm.write(f"[{filename}] Extraction complete.")
            
    except requests.exceptions.RequestException as re:
        tqdm.tqdm.write(f"Network Error {filename}: {re}")
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
    except Exception as e:
        tqdm.tqdm.write(f"Error processing {filename}: {e}")
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)
    finally:
        progress_bar.update(1)

def main():
    check_only = "--check" in sys.argv
    ensure_dir(ROM_DIR)
    
    if not check_only:
        cleanup_temp_files(ROM_DIR)
    
    all_tasks = [] # List of (url, dest_dir, filename)
    
    # 1. Gather all tasks
    for platform, data in PLATFORMS.items():
        print(f"\n--- Gathering links for {platform} ---")
        dest_dir = os.path.join(ROM_DIR, platform)
        ensure_dir(dest_dir)
        
        urls = data.get("urls", [data.get("url")])
        for url in urls:
            if not url: continue
            
            links = get_links(url, data["exts"], platform)
            print(f"Found {len(links)} matching files in {url}.")
            
            for filename, link in links:
                all_tasks.append((platform, link, dest_dir, filename))

    total_files = len(all_tasks)
    print(f"\nTotal files to process: {total_files}")
    
    # DEDUPLICATION LOGIC
    # Group by Platform + Base Title
    # Score: Rev/vX = +10*X. (France) = +1.
    
    import re
    
    def get_base_title(filename):
        # Remove extension
        name = os.path.splitext(filename)[0]
        
        def replace_params(match):
            content = match.group(0)
            if "disc" in content.lower() or "disk" in content.lower():
                 return content # Keep it
            return "" # Remove it
            
        base = re.sub(r'\s*\([^)]+\)', replace_params, name)
        return base.strip()

    def get_score(filename):
        score = 0
        
        # Revision score
        # (Rev X)
        rev_match = re.search(r'\(Rev\s*(\d+)\)', filename, re.IGNORECASE)
        if rev_match:
            score += int(rev_match.group(1)) * 10
        
        # (vX.X)
        v_match = re.search(r'\(v(\d+(?:\.\d+)?)\)', filename, re.IGNORECASE)
        if v_match:
             try:
                score += float(v_match.group(1)) * 10
             except: pass
             
        # Region preference
        if "(France)" in filename or "(Fr)" in filename:
            score += 2
        elif "(Europe)" in filename:
            score += 1
            
        return score

    print("Deduplicating list...")
    # Map: (Platform, BaseTitle) -> (Score, TaskItem)
    best_candidates = {}
    
    for item in all_tasks:
        platform, link, dest_dir, filename = item
        base_title = get_base_title(filename)
        score = get_score(filename)
        
        key = (platform, base_title)
        
        if key not in best_candidates:
            best_candidates[key] = (score, item)
        else:
            current_best_score, _ = best_candidates[key]
            if score > current_best_score:
                best_candidates[key] = (score, item)
    
    # Reconstruct tasks list
    final_tasks = [val[1] for val in best_candidates.values()]
    print(f"Reduced from {len(all_tasks)} to {len(final_tasks)} files after deduplication.")

    all_tasks = final_tasks # Override all_tasks for both Dry Run and Download

    if check_only:
        print("\n[DRY RUN] Files identified (Deduplicated):")
        for platform, link, dest_dir, filename in all_tasks:
            status = "Existing" if is_already_processed(filename, dest_dir) else "New"
            print(f"[{platform}] {filename} ({status})")
        return

    # 2. Process tasks in parallel
    print(f"\nStarting downloads with {MAX_WORKERS} workers...")
    
    tasks_to_run = []
    skipped_count = 0
    
    for item in all_tasks:
        _, link, dest_dir, filename = item
        if is_already_processed(filename, dest_dir):
            skipped_count += 1
        else:
            tasks_to_run.append(item)
            
    print(f"Skipping {skipped_count} already downloaded/extracted files.")
    print(f" downloading {len(tasks_to_run)} new files...")
    
    with tqdm.tqdm(total=len(tasks_to_run), unit='file') as pbar:
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = []
            for platform, link, dest_dir, filename in tasks_to_run:
                futures.append(
                    executor.submit(download_and_process, link, dest_dir, filename, pbar)
                )
            
            # Wait for all to complete
            concurrent.futures.wait(futures)

if __name__ == "__main__":
    main()
