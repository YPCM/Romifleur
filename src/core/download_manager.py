
import threading
import concurrent.futures
from .rom_manager import RomManager

class DownloadManager:
    def __init__(self, rom_manager: RomManager):
        self.rom_manager = rom_manager
        self.queue = [] # List of (Category, Console, Filename)
        self.is_downloading = False
        self.lock = threading.Lock()
        
    def add_to_queue(self, category, console, filename):
        # Avoid duplicates
        for item in self.queue:
            if item[2] == filename:
                return False
        
        self.queue.append((category, console, filename))
        return True

    def remove_from_queue(self, index):
        if 0 <= index < len(self.queue):
            del self.queue[index]
            return True
        return False

    def clear_queue(self):
        self.queue = []

    def start_download(self, progress_callback=None, completion_callback=None):
        if not self.queue or self.is_downloading:
            return

        self.is_downloading = True
        
        # Run in a separate thread to not block UI
        threading.Thread(target=self._worker, args=(list(self.queue), progress_callback, completion_callback)).start()

    def _worker(self, queue_items, progress_callback, completion_callback):
        total = len(queue_items)
        completed = 0
        max_workers = 3 
        
        def update_overall_progress(file_done, msg=""):
            nonlocal completed
            with self.lock:
                if file_done:
                    completed += 1
                
                prog = completed / total if total > 0 else 0
                status = f"Downloading... [{completed}/{total}]"
                if progress_callback:
                    progress_callback(prog, status)

        def download_task(item):
            cat, console, fname = item
            self.rom_manager.download_file(cat, console, fname, progress_callback=None)
            update_overall_progress(True)
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(download_task, item) for item in queue_items]
            concurrent.futures.wait(futures)
        
        self.is_downloading = False
        if completion_callback:
            completion_callback()
