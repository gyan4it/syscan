# SysScan System Architecture

## 1. System Overview

SysScan is a Python-based system storage analysis tool that identifies large files and folders (>1GB) consuming unnecessary space on Windows systems. It uses parallel processing to achieve scan speeds of ~17 seconds for 200GB of storage.

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│  Command Line (system_cleaner.py) / Web (feedback.html) │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Core Engine (scan_system)                │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ Grid Creator  │  │ Parallel      │  │ Registry   │  │
│  │              │→│ Scanner       │→│ Analyzer    │  │
│  └──────────────┘  │ (ThreadPool) │  └────────────┘  │
│                    └──────────────┘                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ JSON Report  │  │ CSV Feedback │  │ Exclusions │  │
│  └──────────────┘  └──────────────┘  └────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 3. Component Details

### 3.1 Grid-Based Scanner (The Core Innovation)

**Problem:** Traditional scanners (os.walk, Get-ChildItem) scan sequentially -> Slow

**Solution:** Divide storage into "grid cells" (top-level directories) and scan in parallel

```python
# Traditional (Slow)
for dir in all_directories:
    size = calculate_size(dir)  # Sequential, ~minutes

# SysScan (Fast)
grid_cells = get_top_level_dirs(C:/)
with ThreadPoolExecutor(max_workers=16) as executor:
    futures = [executor.submit(calculate_size, cell) for cell in grid_cells]
    # Parallel, ~seconds
```

**Why it's fast:**
- Bypasses GIL for I/O-bound tasks (file size calculation)
- Uses os.scandir() (faster than os.walk)
- Dynamic worker scaling (CPU cores × 4, limited by available RAM)

### 3.2 Dynamic Worker Scaling

```python
cpu_count = os.cpu_count() or 4
try:
    # Get available RAM
    kernel32 = ctypes.windll.kernel32
    # ... memory query ...
    avail_mem_mb = memory.ullAvailPhys / (1024**2)
    mem_workers = max(8, int(avail_mem_mb / 50))  # 1 worker per 50MB
except:
    mem_workers = cpu_count * 4

optimal_workers = min(cpu_count * 4, mem_workers, 256)
```

**Example:**
- 8-core CPU, 16GB RAM -> 16 workers
- 4-core CPU, 8GB RAM -> 8 workers

### 3.3 Exclusion System

Prevents scanning user documents, system folders:

```python
EXCLUDES = [
    'C:/Users/*/Documents',     # User documents (keep)
    'C:/Users/*/Pictures',     # Photos (keep)
    'C:/Windows',               # System (never scan)
    'C:/Program Files',        # Installed apps (skip)
    'C:/ProgramData',          # System data (skip)
]
```

Uses `fnmatch` for wildcard matching.

### 3.4 Safety Mechanisms

1. **Admin Privilege Check**
   ```python
   if ctypes.windll.shell32.IsUserAnAdmin():
       return True
   ```

2. **Dry-Run Mode**
   ```bash
   python system_cleaner.py --dry-run  # No deletions
   ```

3. **Recycle Bin Support**
   ```python
   # Uses Windows API SHFileOperation
   send_to_recycle_bin(path)  # Restorable
   ```

4. **Confirmation Prompts**
   - Delete all remaining? [y/N]
   - Recycle Bin vs Permanent delete

### 3.5 Registry Analyzer

Scans Windows uninstall registry keys for orphaned entries:

```powershell
$regPaths = @(
    'HKLM:\Software\...\Uninstall\*',
    'HKCU:\Software\...\Uninstall\*'
)
# Check if uninstall path exists but program is gone
```

## 4. Data Flow

```
1. User runs: python system_cleaner.py
   ↓
2. Admin check (elevate if needed)
   ↓
3. Analyze storage (get total size)
   ↓
4. Create grid (scan_paths → grid_cells)
   ↓
5. Start parallel scan (ThreadPoolExecutor)
   ↓
6. For each grid cell:
   - Check exclusion list
   - Calculate directory size (os.scandir recursive)
   - If >1GB, add to found_items
   ↓
7. Scan registry for leftovers
   ↓
8. Generate report (JSON)
   ↓
9. User interaction:
   - Delete / Skip / View Tree / Quit / Delete All
   ↓
10. Perform deletion (Recycle Bin or Permanent)
```

## 5. Performance Metrics

| Metric | Value |
|--------|-------|
| Scan speed | ~17 seconds for 200GB |
| Grid cells | 150-200 for C:/Users |
| Parallel workers | 8-32 (dynamic) |
| Items found | 4-10 (typically) |
| Memory usage | ~100MB per worker |

## 6. Technology Stack

### Backend (Python)
- **concurrent.futures** - ThreadPoolExecutor for parallelism
- **ctypes** - Windows API calls (admin check, recycle bin)
- **subprocess** - PowerShell integration (registry scan)
- **os.scandir** - Fast directory traversal
- **fnmatch** - Exclusion pattern matching

### Frontend (HTML/JS)
- **Vanilla JS** - Feedback form handling
- **Fetch API** - Submit to Python server
- **CSS3** - Modern UI with gradients

### Server (Flask)
- **Flask** - Lightweight web server for feedback
- **Flask-CORS** - Cross-origin support
- **CSV module** - Feedback storage

## 7. Security Considerations

1. **Admin only when needed** - Dry-run doesn't require admin
2. **No remote code execution** - All operations local
3. **Exclusion system** - Protects user data
4. **Confirmation prompts** - Prevents accidental deletion
5. **MIT License** - Open source, auditable code

## 8. Scalability

### Current Limits
- Windows only (uses Windows-specific APIs)
- Single machine scan (no network scanning)
- Max 256 parallel workers

### Future Scaling
- Add Linux/macOS support (Phase 3 in roadmap)
- Network drive scanning
- Cloud storage integration
- Enterprise multi-machine support

## 9. Maintenance

### Code Structure
```
system_cleaner.py (309 lines)
├── Imports & Constants
├── run_as_admin()
├── send_to_recycle_bin()
├── progress_bar()
├── display_tree()
├── scan_registry_leftovers()
├── get_total_storage_size()
├── is_excluded()
├── scan_system()
│   ├── get_size_fast()
│   ├── process_item()
│   ├── collect_grid_cells()
│   └── scan_grid()
└── main()
```

### Testing
- Unit tests: `tests/test_scanner.py`
- Performance: `tests/test_performance.py`
- Integration: Manual testing with `--dry-run`

## 10. Conclusion

SysScan achieves its goal of fast, safe system storage analysis through:
1. **Grid-based parallel processing** (17s vs 10+ minutes)
2. **Smart targeting** (caches, logs, leftovers)
3. **Safety first** (dry-run, recycle bin, confirmations)
4. **Open architecture** (MIT license, extensible design)

---

**For contributors:** See CONTRIBUTING.md
**For API details:** See API.md
**For roadmap:** See README.md (Future Development section)
