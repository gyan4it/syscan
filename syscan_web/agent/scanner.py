"""
Grid-based parallel scanner for system storage analysis.
Extract from system_cleaner.py - provides GridScanner class.
"""

import os
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event

def is_excluded(path, exclude_patterns):
    """Check if path matches any exclusion pattern (supports * wildcard)"""
    import fnmatch
    path_normalized = path.replace('\\', '/')
    for pattern in exclude_patterns:
        pattern_normalized = pattern.replace('\\', '/')
        if fnmatch.fnmatch(path_normalized, pattern_normalized):
            return True
    return False

class GridScanner:
    """Grid-based parallel scanner optimized for Windows systems."""

    # Default exclusion patterns (wildcards supported with *)
    DEFAULT_EXCLUDES = [
        'C:/Users/*/Documents',
        'C:/Users/*/Pictures',
        'C:/Users/*/Videos',
        'C:/Users/*/Music',
        'C:/Users/*/Desktop',
        'C:/Windows',
        'C:/ProgramData',
        'C:/Program Files',
        'C:/Program Files (x86)',
        'C:/Users/All Users',
        'C:/Users/Default',
        'C:/Users/Default User',
        'C:/Users/Public'
    ]

    # Specific paths to scan (in addition to C:/)
    SPECIFIC_PATHS = [
        os.path.expandvars(r'%APPDATA%\Apple Computer\MobileSync\Backup'),
        os.path.expandvars(r'%USERPROFILE%\.local\share\opencode\log'),
        os.path.expandvars(r'%LOCALAPPDATA%\npm-cache'),
        os.path.expandvars(r'%TEMP%'),
        os.path.expandvars(r'%LOCALAPPDATA%\Temp'),
        os.path.expandvars(r'%USERPROFILE%\AppData\Local\Docker'),
        os.path.expandvars(r'%USERPROFILE%\AppData\Local\Google\Chrome\User Data\Default\Cache'),
        os.path.expandvars(r'%USERPROFILE%\AppData\Local\Microsoft\Edge\User Data\Default\Cache')
    ]

    def __init__(self, excludes=None, specific_paths=None):
        self.excludes = excludes if excludes else self.DEFAULT_EXCLUDES
        self.specific_paths = specific_paths if specific_paths else self.SPECIFIC_PATHS
        self.found_items = []
        self.items_lock = threading.Lock()
        self.scan_complete = Event()
        self.current_scan_info = ['']
        self.start_time = None

    def get_size_fast(self, path):
        """Fast size calculation using os.scandir"""
        total = 0
        try:
            for entry in os.scandir(path):
                try:
                    if entry.is_file(follow_symlinks=False):
                        total += entry.stat(follow_symlinks=False).st_size
                    elif entry.is_dir(follow_symlinks=False):
                        total += self.get_size_fast(entry.path)
                except (PermissionError, OSError):
                    pass
        except (PermissionError, OSError):
            pass
        return total

    def process_item(self, item_path):
        """Process a single item - check size and return if >1GB"""
        try:
            if is_excluded(item_path, self.excludes):
                return None
            if os.path.isdir(item_path):
                size = self.get_size_fast(item_path)
            else:
                size = os.path.getsize(item_path)
            if size > 1024**3:  # >1GB
                return (item_path, size)
        except:
            pass
        return None

    def collect_grid_cells(self):
        """Collect all items from scan paths to create grid cells"""
        cells = []
        scan_paths = ['C:/'] + [p.replace('\\', '/') for p in self.specific_paths if os.path.exists(p)]
        scan_paths_norm = [os.path.normpath(p) for p in scan_paths]

        for path in scan_paths:
            if not os.path.exists(path):
                continue
            try:
                for entry in os.scandir(path):
                    item_path = os.path.normpath(entry.path)
                    # Skip root-level scan folders
                    if item_path in scan_paths_norm:
                        continue
                    # Skip direct user profile root (hardcoded check from original)
                    if item_path.lower() == os.path.normpath('C:/Users/Gyan4').lower():
                        continue
                    # Check exclusions
                    if is_excluded(item_path, self.excludes):
                        continue
                    cells.append(item_path)
            except (PermissionError, OSError):
                pass
        return cells

    def get_optimal_workers(self):
        """Calculate optimal worker count based on system resources."""
        cpu_count = os.cpu_count() or 4
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong),
                            ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong),
                            ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong),
                            ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong),
                            ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            memory = MEMORYSTATUSEX()
            memory.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            kernel32.GlobalMemoryStatusEx(ctypes.byref(memory))
            avail_mem_mb = memory.ullAvailPhys / (1024**2)
            mem_workers = max(8, int(avail_mem_mb / 50))
        except:
            mem_workers = cpu_count * 4
        return min(cpu_count * 4, mem_workers, 256)

    def scan_grid(self):
        """Scan storage using grid-based parallel processing."""
        grid_cells = self.collect_grid_cells()
        total_cells = len(grid_cells)
        optimal_workers = self.get_optimal_workers()

        print(f'Scanning {total_cells} grid cells with {optimal_workers} parallel workers...')

        completed = [0]
        with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
            future_to_cell = {executor.submit(self.process_item, cell): cell for cell in grid_cells}
            for future in as_completed(future_to_cell):
                try:
                    result = future.result()
                    if result:
                        with self.items_lock:
                            self.found_items.append(result)
                        self.current_scan_info[0] = result[0][:60]
                    completed[0] += 1
                    if completed[0] % 10 == 0:
                        elapsed = time.time() - self.start_time
                        with self.items_lock:
                            count = len(self.found_items)
                        print(f'[{self.format_time(elapsed)}] Progress: {completed[0]}/{total_cells} cells | Found: {count}')
                except:
                    pass

    def format_time(self, seconds):
        """Format seconds into human-readable time."""
        if seconds < 60:
            return f'{int(seconds)}s'
        elif seconds < 3600:
            return f'{int(seconds / 60)}m {int(seconds % 60)}s'
        else:
            return f'{int(seconds / 3600)}h {int((seconds % 3600) / 60)}m'

    def scan(self, progress_callback=None):
        """Main scan method. Returns sorted list of (path, size) tuples."""
        self.found_items = []
        self.start_time = time.time()

        print('Starting scan...')
        self.scan_grid()
        self.scan_complete.set()

        elapsed = time.time() - self.start_time
        print(f"[{self.format_time(elapsed)}] Scan complete! Total found: {len(self.found_items)}")

        return sorted(self.found_items, key=lambda x: -x[1])
