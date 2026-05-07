# SysScan - System Storage Analyzer & Cleaner

## What is SysScan?

SysScan is an open-source, high-performance system storage analysis tool designed to identify large files and folders (>1GB) that accumulate over time from caches, logs, uninstalled application leftovers, and temporary files. It uses **grid-based parallel processing** to scan entire storage systems in seconds rather than minutes.

### Key Features:
- ⚡ **Ultra-fast scanning** - Scans 200+ GB in ~17 seconds using parallel processing
- 🎯 **Smart targeting** - Focuses on caches, logs, and uninstaller leftovers (not system files)
- 🛡️ **Safe operations** - Dry-run mode, recycle bin support, exclusion system
- 🔍 **Deep analysis** - Registry leftover detection, file tree views
- 📊 **Detailed reporting** - JSON reports, progress tracking, size breakdowns

---

## Why is it Required?

### The Problem:
Over time, every computer accumulates "digital clutter":
- **Cache files** from browsers, package managers (npm, pip)
- **Log files** that grow uncontrollably (opencode logs: 6GB+)
- **Uninstalled app leftovers** (registry entries pointing to deleted folders)
- **Temp files** and incomplete downloads
- **Mobile backups** (iPhone backups: 40GB+)

These files often consume **100-200GB** of storage without the user realizing it.

### The Solution:
SysScan identifies these space-wasters in seconds and helps you decide what to keep, what to delete, and what to move to external storage.

---

## System Architecture (As System Architect)

### Core Design Principles:
1. **Grid-Based Parallel Processing** - Storage is divided into "grid cells" (top-level directories), scanned in parallel
2. **I/O-Optimized** - Uses `os.scandir()` instead of slower `os.walk()`
3. **Non-Destructive** - Dry-run mode, multiple confirmation prompts, recycle bin support
4. **Extensible** - Modular design allows adding new scan types

### Technical Stack:
```
Frontend: Command-line interface (Python)
Backend: Python 3.8+ with:
  - concurrent.futures (ThreadPoolExecutor for parallelism)
  - ctypes (Windows API for admin checks, recycle bin)
  - subprocess (PowerShell integration for registry scans)
  - os.scandir (fast directory traversal)
```

### Data Flow:
```
User Input → Admin Check → Storage Analysis → Grid Creation → 
Parallel Scanning → Size Calculation → Registry Check → 
Report Generation → User Confirmation → Deletion (Recycle/Permanent)
```

---

## Working System (How it Works)

### 1. **Initialization**
- Checks for admin privileges (required for some system paths)
- Analyzes total storage size (210GB in test case)
- Estimates scan time based on storage size

### 2. **Grid Creation**
- Identifies top-level directories in scan paths (C:/Users → 159 grid cells)
- Applies exclusion filters (skip Documents, Pictures, Windows, etc.)

### 3. **Parallel Scanning**
- Uses ThreadPoolExecutor with dynamic worker count (16 workers for 8-core system)
- Each worker processes one grid cell independently
- Calculates directory sizes using recursive `os.scandir()`

### 4. **Registry Analysis**
- Scans Windows uninstall registry keys
- Identifies orphaned entries (program uninstalled but registry remains)
- Checks for invalid uninstall strings

### 5. **Report & Action**
- Displays found items sorted by size
- Offers options: Delete, View Tree, Skip, Quit, Delete All
- Supports Recycle Bin (restorable) or Permanent deletion
- Saves JSON report to Desktop

---

## Core In-Depth Detailing

### Grid-Based Scanner (The Secret Sauce)
```python
# Instead of scanning sequentially:
for dir in all_directories:
    calculate_size(dir)  # Slow!

# SysScan divides into grid and scans in parallel:
with ThreadPoolExecutor(max_workers=16) as executor:
    futures = {executor.submit(calculate_size, cell): cell for cell in grid}
    for future in as_completed(futures):
        result = future.result()  # Fast! ~17s for 200GB
```

### Dynamic Worker Scaling
- Calculates optimal workers: `min(cpu_cores * 4, available_memory / 50MB, 256)`
- Test system (8 cores, 16GB RAM) → 16 parallel workers
- More workers = faster scan (up to a point)

### Exclusion System
```python
EXCLUDES = [
    'C:/Users/*/Documents',  # User documents (keep)
    'C:/Users/*/Pictures',  # User photos (keep)
    'C:/Windows',            # System files (never delete)
    'C:/Program Files'       # Installed apps (skip)
]
```

### Safety Mechanisms
1. **Dry-Run Mode** (`--dry-run` or `-d`) - Scan only, no deletions
2. **Recycle Bin Support** - Files sent to Recycle Bin (restorable)
3. **Confirmation Prompts** - "Delete all remaining" asks for Y/N
4. **Tree View** - See folder contents before deleting
5. **Exclusion System** - Never touches user documents/system files

---

## Future Development (As System Analyst)

### Phase 1: Enhanced Scanning (3-6 months)
- [ ] **File type analysis** - Identify duplicate files, largest file types
- [ ] **Age-based filtering** - Find files not accessed in 6+ months
- [ ] **Visual disk usage** - Generate treemap visualizations
- [ ] **Scheduled scans** - Automatic weekly scans with email reports

### Phase 2: User Experience (6-12 months)
- [ ] **GUI interface** - Tkinter/PyQt graphical interface
- [ ] **Web dashboard** - Flask/Django web interface with charts
- [ ] **Notifications** - System tray alerts when storage >90% full
- [ ] **Smart recommendations** - AI-based suggestions for cleanup

### Phase 3: Platform Expansion (1-2 years)
- [ ] **Linux support** - Adapt for Linux filesystem (`/home`, `/var`, `/tmp`)
- [ ] **macOS support** - Support for macOS (`~/Library/Caches`, etc.)
- [ ] **Network drives** - Scan NAS, network shares
- [ ] **Cloud integration** - Identify large cloud sync folders (Dropbox, OneDrive)

### Phase 4: Enterprise Features (2+ years)
- [ ] **Centralized management** - Scan multiple computers from one console
- [ ] **Policy-based cleanup** - Define organization-wide cleanup rules
- [ ] **Audit logging** - Track all deletions with user, time, reason
- [ ] **Compliance reporting** - GDPR/HIPAA compliance reports

### Technical Improvements
- [ ] **Rust extensions** - Rewrite size calculation in Rust for 10x speed
- [ ] **SQLite database** - Store scan history instead of JSON
- [ ] **Plugin system** - Allow third-party scan modules
- [ ] **API endpoints** - REST API for integration with other tools

---

## Project Structure

```
SysScan/
├── README.md              # This file
├── LICENSE                # MIT License (open source)
├── system_cleaner.py     # Main scanner script
├── feedback.html         # User feedback page
├── feedback.csv          # Stored feedback (admin view)
├── docs/
│   ├── ARCHITECTURE.md  # Detailed system design
│   ├── API.md           # Internal API documentation
│   └── CONTRIBUTING.md # How to contribute
└── tests/
    ├── test_scanner.py   # Unit tests
    └── test_performance.py # Performance benchmarks
```

---

## Quick Start

```bash
# Clone/download the project
cd SysScan

# Run in dry-run mode (safe, no deletions)
python system_cleaner.py --dry-run

# Run with admin privileges to actually delete
python system_cleaner.py
```

---

## License

MIT License - Free to use, modify, and distribute. See LICENSE file for details.

---

## Contact & Feedback

We value your input! Help us improve SysScan:
- **Use the feedback form** (feedback.html) to share thoughts
- **Report issues** on GitHub (if applicable)
- **Suggest features** - See Future Development section above

---

**Built with ❤️ for system administrators, developers, and anyone who hates running out of disk space.**
