import os
import sys
import ctypes
import subprocess
import json
import time
import shutil
import threading
from ctypes import wintypes
from threading import Event
from concurrent.futures import ThreadPoolExecutor, as_completed

# PowerShell script constants
# Removed - using Python-based scanner for speed

PS_REGISTRY_LEFTOVERS = """
$regPaths = @(
    'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',
    'HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',
    'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*'
)
$leftovers = @()
foreach ($regPath in $regPaths) {{
    Get-ItemProperty $regPath -ErrorAction SilentlyContinue | ForEach-Object {{
        $installLocation = $_.InstallLocation
        $uninstallString = $_.UninstallString
        $displayName = $_.DisplayName
        if (-not $displayName) {{ return }}
        if ($installLocation -and (Test-Path $installLocation)) {{
            $hasExe = Get-ChildItem -Path $installLocation -Filter "*.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
            if (-not $hasExe) {{
                $leftovers += $installLocation
            }}
        }}
        if ($uninstallString) {{
            $path = $uninstallString -replace '.*?"([^"]+)".*', '$1' -replace '^([^"]+)\\.exe.*', '$1'
            if ($path -and $path -match '^[A-Za-z]:\\\\') {{
                $uninstallerExists = Test-Path $path
                $parentDir = Split-Path $path -Parent
                if (-not $uninstallerExists -and $parentDir -and (Test-Path $parentDir)) {{
                    $hasOtherExe = Get-ChildItem -Path $parentDir -Filter "*.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
                    if (-not $hasOtherExe) {{
                        $leftovers += $parentDir
                    }}
                }}
            }}
        }}
    }}
}}
$leftovers | Sort-Object -Unique | ForEach-Object {{ Write-Output $_ }}
"""

PS_GET_STORAGE_SIZE = """
$drive = Get-PSDrive C
$total = [math]::Round($drive.Used / 1GB, 2)
Write-Output $total
"""

def run_as_admin():
    if ctypes.windll.shell32.IsUserAnAdmin():
        return True
    script = os.path.abspath(sys.argv[0])
    args = ' '.join([f'"{arg}"' if ' ' in arg else arg for arg in sys.argv[1:]])
    ret = ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, f'"{script}" {args}', None, 1)
    if ret > 32:
        sys.exit(0)
    else:
        print("Failed to elevate to admin privileges.")
        sys.exit(1)

def send_to_recycle_bin(path):
    class SHFILEOPSTRUCT(ctypes.Structure):
        _fields_ = [
            ('hwnd', wintypes.HWND),
            ('wFunc', wintypes.UINT),
            ('pFrom', wintypes.LPCWSTR),
            ('pTo', wintypes.LPCWSTR),
            ('fFlags', wintypes.UINT),
            ('fAnyOperationsAborted', wintypes.BOOL),
            ('hNameMapping', wintypes.LPVOID),
            ('lpszProgressTitle', wintypes.LPCWSTR)
        ]
    FO_DELETE = 3
    FOF_ALLOWUNDO = 0x40
    FOF_NOCONFIRMATION = 0x10
    FOF_SILENT = 0x4

    op = SHFILEOPSTRUCT()
    op.wFunc = FO_DELETE
    op.pFrom = ctypes.c_wchar_p(path + '\0')
    op.fFlags = FOF_ALLOWUNDO | FOF_NOCONFIRMATION | FOF_SILENT

    ret = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
    return ret == 0 and not op.fAnyOperationsAborted

def progress_bar(percent, prefix='Progress', suffix='', length=20):
    filled = int(length * percent // 100)
    bar = '#' * filled + '-' * (length - filled)
    print(f'{prefix} |{bar}| {percent}% {suffix}')
    sys.stdout.flush()

def display_tree(path, max_depth=3, current_depth=0):
    if current_depth > max_depth:
        return
    try:
        items = os.listdir(path)
    except:
        return
    for i, item in enumerate(items):
        is_last = i == len(items) - 1
        prefix = '└── ' if is_last else '├── '
        indent = '    ' * current_depth
        full_path = os.path.join(path, item)
        if os.path.isdir(full_path):
            print(f'{indent}{prefix}{item}/')
            display_tree(full_path, max_depth, current_depth + 1)
        else:
            try:
                size = os.path.getsize(full_path)
                print(f'{indent}{prefix}{item} ({size / 1024 / 1024:.1f} MB)')
            except:
                print(f'{indent}{prefix}{item} (size unavailable)')

def scan_registry_leftovers():
    try:
        result = subprocess.run(
            ['powershell', '-Command', PS_REGISTRY_LEFTOVERS],
            capture_output=True,
            text=True,
            timeout=60
        )
        leftovers = []
        for line in result.stdout.strip().split('\n'):
            path = line.strip()
            if path and os.path.exists(path):
                size = 0
                try:
                    for root, dirs, files in os.walk(path):
                        for f in files:
                            try:
                                size += os.path.getsize(os.path.join(root, f))
                            except:
                                pass
                except:
                    pass
                leftovers.append((path, size))
        return leftovers
    except Exception as e:
        print(f'\nError scanning registry: {e}')
        return []

def get_total_storage_size():
    try:
        result = subprocess.run(['powershell', '-Command', PS_GET_STORAGE_SIZE], capture_output=True, text=True, timeout=10)
        return float(result.stdout.strip())
    except:
        return 100.0

def estimate_scan_time(total_gb):
    # Assume ~2GB per second scan rate for PowerShell
    seconds = total_gb / 2.0
    return seconds

def format_time(seconds):
    if seconds < 60:
        return f'{int(seconds)}s'
    elif seconds < 3600:
        return f'{int(seconds / 60)}m {int(seconds % 60)}s'
    else:
        return f'{int(seconds / 3600)}h {int((seconds % 3600) / 60)}m'

def is_excluded(path, exclude_patterns):
    """Check if path matches any exclusion pattern (supports * wildcard)"""
    import fnmatch
    path_normalized = path.replace('\\', '/')
    for pattern in exclude_patterns:
        pattern_normalized = pattern.replace('\\', '/')
        if fnmatch.fnmatch(path_normalized, pattern_normalized):
            return True
    return False

def scan_system():
    items = []
    scan_paths = [
        'C:/'
    ]
    specific_paths = [
        os.path.expandvars(r'%APPDATA%\Apple Computer\MobileSync\Backup'),
        os.path.expandvars(r'%USERPROFILE%\.local\share\opencode\log'),
        os.path.expandvars(r'%LOCALAPPDATA%\npm-cache'),
        os.path.expandvars(r'%TEMP%'),
        os.path.expandvars(r'%LOCALAPPDATA%\Temp'),
        os.path.expandvars(r'%USERPROFILE%\AppData\Local\Docker'),
        os.path.expandvars(r'%USERPROFILE%\AppData\Local\Google\Chrome\User Data\Default\Cache'),
        os.path.expandvars(r'%USERPROFILE%\AppData\Local\Microsoft\Edge\User Data\Default\Cache')
    ]
    for p in specific_paths:
        if os.path.exists(p):
            scan_paths.append(p.replace('\\', '/'))

    # Exclusion patterns (wildcards supported with *)
    EXCLUDES = [
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

    # Normalize scan_paths for comparison
    scan_paths_norm = [os.path.normpath(p) for p in scan_paths]

    # Phase1: Analyze storage
    print('Analyzing storage...')
    total_gb = get_total_storage_size()
    est_time = estimate_scan_time(total_gb)
    print(f'Total storage: {total_gb} GB')
    print(f'Estimated scan time: {format_time(est_time)}')
    print()
    print('Starting scan...')
    print()

    # Phase2: Grid-based parallel scan
    found_items = []
    items_lock = threading.Lock()
    scan_complete = Event()
    current_scan_info = ['']

    def get_size_fast(path):
        """Fast size calculation using os.scandir"""
        total = 0
        try:
            for entry in os.scandir(path):
                try:
                    if entry.is_file(follow_symlinks=False):
                        total += entry.stat(follow_symlinks=False).st_size
                    elif entry.is_dir(follow_symlinks=False):
                        total += get_size_fast(entry.path)
                except (PermissionError, OSError):
                    pass
        except (PermissionError, OSError):
            pass
        return total

    def process_item(item_path):
        """Process a single item - check size and return if >1GB"""
        try:
            if is_excluded(item_path, EXCLUDES):
                return None
            if os.path.isdir(item_path):
                size = get_size_fast(item_path)
            else:
                size = os.path.getsize(item_path)
            if size > 1024**3:  # >1GB
                return (item_path, size)
        except:
            pass
        return None

    def collect_grid_cells():
        """Collect all items from scan paths to create grid cells"""
        cells = []
        for path in scan_paths:
            if not os.path.exists(path):
                continue
            try:
                for entry in os.scandir(path):
                    item_path = os.path.normpath(entry.path)
                    # Skip root-level scan folders
                    if item_path in scan_paths_norm:
                        continue
                    # Skip direct user profile root
                    if item_path.lower() == os.path.normpath('C:/Users/Gyan4').lower():
                        continue
                    # Check exclusions
                    if is_excluded(item_path, EXCLUDES):
                        continue
                    cells.append(item_path)
            except (PermissionError, OSError):
                pass
        return cells

    def scan_grid():
        """Scan storage using grid-based parallel processing optimized for system capabilities"""
        # Collect all items from scan paths (the grid cells)
        grid_cells = collect_grid_cells()
        total_cells = len(grid_cells)

        # Dynamically calculate optimal worker count based on system
        cpu_count = os.cpu_count() or 4
        # For I/O-bound tasks, use more threads than CPU cores
        # Each thread needs ~50MB RAM estimate, limit by available memory
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
            mem_workers = max(8, int(avail_mem_mb / 50))  # 1 worker per 50MB available
        except:
            mem_workers = cpu_count * 4

        # Use optimal worker count: more threads for I/O-bound, capped at 256
        optimal_workers = min(cpu_count * 4, mem_workers, 256)
        print(f'Scanning {total_cells} grid cells with {optimal_workers} parallel workers...')

        completed = [0]

        # Use ThreadPoolExecutor (better for I/O-bound tasks, no pickling issues)
        with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
            future_to_cell = {executor.submit(process_item, cell): cell for cell in grid_cells}
            for future in as_completed(future_to_cell):
                try:
                    result = future.result()
                    if result:
                        with items_lock:
                            found_items.append(result)
                        current_scan_info[0] = result[0][:60]
                    completed[0] += 1
                    if completed[0] % 10 == 0:
                        print(f'[{format_time(time.time() - start_time)}] Progress: {completed[0]}/{total_cells} cells | Found: {len(found_items)} items')
                except:
                    pass

    def do_scan():
        scan_grid()
        scan_complete.set()

    scan_thread = threading.Thread(target=do_scan, daemon=True)
    scan_thread.start()

    start_time = time.time()
    last_status = ['']
    while not scan_complete.is_set():
        elapsed = time.time() - start_time
        with items_lock:
            count = len(found_items)
        status = current_scan_info[0] if current_scan_info[0] else 'Scanning...'
        if status != last_status[0]:
            print(f"[{format_time(elapsed)}] {status[:60]} | Found: {count}")
            last_status[0] = status
        time.sleep(0.5)
    print(f"[{format_time(time.time() - start_time)}] Scan complete! Total found: {len(found_items)}")

    scan_thread.join(timeout=1)

    print('Scanning registry...')
    registry_leftovers = scan_registry_leftovers()
    found_items.extend(registry_leftovers)

    print('Scan complete!')
    return sorted(found_items, key=lambda x: -x[1])

def main():
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv
    try:
        if not dry_run:
            run_as_admin()
        print('Starting system scan for large files/folders (>1GB)...')
        if dry_run:
            print('[DRY RUN MODE - No changes will be made]')
        items = scan_system()
    except KeyboardInterrupt:
        print('\n\nScan cancelled by user.')
        return
    if not items:
        print('No large items found.')
        return
    print(f'\nFound {len(items)} large items:')
    for idx, (path, size) in enumerate(items):
        print(f'{idx+1}. {path} ({size / 1024 / 1024 / 1024:.2f} GB)')
    report = [{'path': p, 'size_gb': s / 1024 / 1024 / 1024} for p, s in items]
    desktop = os.path.join(os.path.expanduser('~'), 'Desktop')
    system_checking_dir = os.path.join(desktop, 'SystemChecking')
    os.makedirs(system_checking_dir, exist_ok=True)
    with open(os.path.join(system_checking_dir, 'cleanup_report.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    if dry_run:
        print('\n[DRY RUN] No deletions performed. Report saved.')
        return

    delete_all = False
    for path, size in items:
        delete_item = False
        if delete_all:
            delete_item = True
        else:
            print(f'\nItem: {path} ({size / 1024 / 1024 / 1024:.2f} GB)')
            resp = input('[y] Delete | [t] View tree | [n] Skip | [q] Quit | [r] Delete all remaining: ').strip().lower()
            if resp == 'q':
                break
            elif resp == 'r':
                total_remaining = sum(s for p, s in items[items.index((path, size)):] ) / 1024 / 1024 / 1024
                confirm = input(f'Delete ALL remaining items ({total_remaining:.2f} GB)? [y/N]: ').strip().lower()
                if confirm == 'y':
                    delete_all = True
                    delete_item = True
                else:
                    continue
            elif resp == 't':
                print(f'Tree view for {path}:')
                display_tree(path, max_depth=5)
                continue
            elif resp == 'n':
                continue
            else:
                delete_item = True
        if delete_item:
            del_type = input('Delete method: [r] Recycle Bin (restorable) | [p] Permanent: ').strip().lower()
            if del_type == 'r':
                print(f'Sending {path} to Recycle Bin...')
                if send_to_recycle_bin(path):
                    print('Success.')
                else:
                    print('Failed to send to Recycle Bin.')
            else:
                print(f'Permanently deleting {path}...')
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    print('Success.')
                except Exception as e:
                    print(f'Error: {e}')

if __name__ == '__main__':
    main()
