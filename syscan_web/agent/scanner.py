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

# Import constants from common module
from syscan_web.common.constants import DEFAULT_EXCLUDES, SPECIFIC_PATHS, MIN_SIZE_BYTES

def is_excluded(path, exclude_patterns):
    """
    Check if path matches any exclusion pattern (supports * wildcard).
    
    Args:
        path: Path to check
        exclude_patterns: List of patterns with wildcards
        
    Returns:
        True if path matches any exclusion pattern
    """
    import fnmatch
    path_normalized = path.replace('\\', '/')
    for pattern in exclude_patterns:
        pattern_normalized = pattern.replace('\\', '/')
        if fnmatch.fnmatch(path_normalized, pattern_normalized):
            return True
    return False

class GridScanner:
    """
    Grid-based parallel scanner optimized for Windows systems.
    
    Uses a grid-based approach where each top-level directory is a "cell"
    scanned in parallel using ThreadPoolExecutor.
    """
    
    # Use constants from common module instead of duplicating
    DEFAULT_EXCLUDES = DEFAULT_EXCLUDES
    SPECIFIC_PATHS = SPECIFIC_PATHS

    def __init__(self, excludes=None, specific_paths=None):
        """
        Initialize GridScanner.
        
        Args:
            excludes: Optional custom exclusion patterns (defaults to DEFAULT_EXCLUDES)
            specific_paths: Optional custom paths to scan (defaults to SPECIFIC_PATHS)
        """
        self.excludes = excludes if excludes else self.DEFAULT_EXCLUDES
        self.specific_paths = specific_paths if specific_paths else self.SPECIFIC_PATHS
        self.found_items = []
        self.items_lock = threading.Lock()
        self.scan_complete = Event()
        self.current_scan_info = ['']
        self.start_time = None
        self.scan_errors = []  # Track errors during scan

    def get_size_fast(self, path):
        """
        Fast size calculation using os.scandir.
        
        Args:
            path: Directory path to calculate size for
            
        Returns:
            Tuple of (total_size, error_count)
        """
        total = 0
        error_count = 0
        try:
            for entry in os.scandir(path):
                try:
                    if entry.is_file(follow_symlinks=False):
                        total += entry.stat(follow_symlinks=False).st_size
                    elif entry.is_dir(follow_symlinks=False):
                        size, errors = self.get_size_fast(entry.path)
                        total += size
                        error_count += errors
                except (PermissionError, OSError):
                    error_count += 1
        except (PermissionError, OSError):
            error_count += 1
        
        if error_count > 0:
            self.scan_errors.append((path, error_count))
        
        return total, error_count

    def process_item(self, item_path):
        """
        Process a single item - check size and return if >1GB.
        
        Args:
            item_path: Path to process
            
        Returns:
            Tuple (path, size) if size >1GB, None otherwise
        """
        try:
            if is_excluded(item_path, self.excludes):
                return None
            if os.path.isdir(item_path):
                size, errors = self.get_size_fast(item_path)
            else:
                size = os.path.getsize(item_path)
            if size > MIN_SIZE_BYTES:  # >1GB
                return (item_path, size)
        except (PermissionError, OSError, ValueError) as e:
            self.scan_errors.append((item_path, str(e)))
        return None

    def collect_grid_cells(self):
        """
        Collect all items from scan paths to create grid cells.
        
        Returns:
            List of paths to scan in parallel
        """
        cells = []
        scan_paths = ['C:/'] + [p.replace('\\', '/') for p in self.specific_paths if os.path.exists(p)]
        scan_paths_norm = [os.path.normpath(p) for p in scan_paths]

        current_user = os.environ.get('USERNAME', '')

        for path in scan_paths:
            if not os.path.exists(path):
                continue
            try:
                for entry in os.scandir(path):
                    item_path = os.path.normpath(entry.path)
                    # Skip root-level scan folders
                    if item_path in scan_paths_norm:
                        continue
                    # Skip direct user profile root (dynamic)
                    if current_user and item_path.lower() == os.path.normpath(f'C:/Users/{current_user}').lower():
                        continue
                    # Check exclusions
                    if is_excluded(item_path, self.excludes):
                        continue
                    cells.append(item_path)
            except (PermissionError, OSError):
                pass
        return cells

    def get_optimal_workers(self):
        """
        Calculate optimal worker count based on system resources.
        
        Returns:
            Optimal number of worker threads (capped at 256)
        """
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
                except Exception as e:
                    self.scan_errors.append(('future', str(e)))

        if self.scan_errors:
            print(f'\nWarning: {len(self.scan_errors)} errors during scan')

    def format_time(self, seconds):
        """
        Format seconds into human-readable time.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted string like "5m 30s" or "1h 20m"
        """
        if seconds < 60:
            return f'{int(seconds)}s'
        elif seconds < 3600:
            return f'{int(seconds / 60)}m {int(seconds % 60)}s'
        else:
            return f'{int(seconds / 3600)}h {int((seconds % 3600) / 60)}m'

    def scan(self, progress_callback=None):
        """
        Main scan method.
        
        Args:
            progress_callback: Optional callback function(percent, message)
            
        Returns:
            Sorted list of (path, size) tuples
        """
        self.found_items = []
        self.scan_errors = []
        self.start_time = time.time()

        print('Starting scan...')
        self.scan_grid()
        self.scan_complete.set()

        elapsed = time.time() - self.start_time
        print(f"[{self.format_time(elapsed)}] Scan complete! Total found: {len(self.found_items)}")
        
        if self.scan_errors:
            print(f"Warning: {len(self.scan_errors)} errors occurred during scan")

        return sorted(self.found_items, key=lambda x: -x[1])
