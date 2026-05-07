# AGENTS.md - Quick Reference for SysCan Repository

## Repository Overview

**Purpose:** System storage analyzer & cleaner that scans 200GB in ~17 seconds using grid-based parallel processing.

**Current State:** Phase 1 Foundation (Months 1-3 in progress)
- Monolithic CLI: `system_cleaner.py` (309 lines)
- Web app folder: `SysScan/` (feedback form, Flask server)
- Development plans: `project_plan/` (5 phase documents)

---

## Essential Commands

### Git Operations (via PowerShell script)
```powershell
# Check status
.\git_manager.ps1 status

# Pull latest
.\git_manager.ps1 pull

# Commit with message
.\git_manager.ps1 commit "Your message here"

# Push to GitHub
.\git_manager.ps1 push

# Create new branch
.\git_manager.ps1 branch feature-name
```

**Note:** Token is stored in `~/.git-credentials` (NOT in scripts). Remote: `https://github.com/gyan4it/syscan.git`

### Python Development
```bash
# Run scanner (dry-run, no deletions)
python system_cleaner.py --dry-run

# Run feedback server
cd SysScan
python feedback_server.py
# Access: http://localhost:5000
# Admin panel: http://localhost:5000/admin

# Create ZIP package
cd SysScan
python package.py
```

### Web UI (Phase 2+)
```bash
# Install dependencies
cd SysScan/webui
npm install

# Start dev server
npm start
# Access: http://localhost:3000
```

---

## Architecture (Key Facts)

### Current (Phase 1 Start)
```
system_cleaner.py (309 lines, monolithic)
├── scan_system()      → Grid-based parallel scanner
├── send_to_recycle_bin() → Windows API (recycle bin)
├── scan_registry_leftovers() → PowerShell registry scan
└── progress_bar()   → Terminal progress display
```

### Target (End of Phase 1)
```
syscan_web/
├── agent/
│   ├── scanner.py     # GridScanner class (extracted)
│   ├── analyzer.py    # FileAnalyzer class
│   ├── deleter.py    # FileDeleter class
│   └── utils.py       # Shared utilities
├── server/
│   ├── app.py         # Flask app factory
│   ├── api.py         # REST endpoints
│   └── websocket.py  # Socket.IO handler
└── common/
    ├── config.py      # Shared config
    └── constants.py  # Paths, exclusions
```

---

## Package Boundaries

| Directory | Ownership | Purpose |
|-----------|------------|---------|
| `./` (root) | Phase 1 dev | Monolithic CLI, Git scripts |
| `SysScan/` | Web app | User feedback, download page |
| `project_plan/` | Documentation | Phase-wise development plans |
| `syscan_web/` (Phase 1) | Backend team | Modular Python packages |
| `syscan_web/webui/` (Phase 2) | Frontend team | React application |

---

## Testing

### Current Testing
```bash
# Run scanner in dry-run mode (no deletions)
python system_cleaner.py --dry-run

# Test feedback server
cd SysScan
python feedback_server.py &
curl http://localhost:5000/api/feedback -X POST -H "Content-Type: application/json" -d "{\"name\":\"Test\",\"type\":\"bug\",\"message\":\"Test\"}"

# View feedback (admin)
curl http://localhost:5000/admin
```

### Phase 1+ Testing (Target)
```bash
# Run unit tests
pytest tests/ -v --cov

# Test API endpoints
pytest tests/test_api.py -v

# Load testing (API response <100ms)
locust -f tests/load_test.py --host=http://localhost:5000
```

---

## Important Constraints

### Security
- ⚠️ **Token in `~/.git-credentials`** - Never commit tokens to repo
- ⚠️ **GitHub Push Protection** - Blocks commits with secrets
- ✅ **`.gitignore`** - Excludes `__pycache__/`, `*.pyc`, `.env`

### Platform
- **Windows-only** (current) - Uses `ctypes.windll` for recycle bin
- **Phase 3** - Will add Linux/macOS support (`agent/platform/`)

### Performance
- **Scan speed:** ~17 seconds for 200GB (16 parallel workers)
- **Worker scaling:** `min(cpu_cores * 4, avail_mem/50MB, 256)`
- **Grid cells:** ~150-200 for `C:/Users`

---

## Development Workflow

### Phase 1: Foundation (Current)
```bash
# 1. Create feature branch
.\git_manager.ps1 branch phase1-foundation

# 2. Modularize (Week 1-4)
# Extract scanner.py, deleter.py, analyzer.py

# 3. Create API (Week 5-8)
# Build server/api.py with REST endpoints

# 4. Test & commit
pytest tests/ -v --cov
.\git_manager.ps1 commit "Phase 1: Modularization complete"

# 5. Push
.\git_manager.ps1 push
```

### Code Style
- **Python:** PEP 8 (4 spaces, clear variable names)
- **JavaScript:** ES6+, JSX for React components
- **Documentation:** Docstrings for all functions

---

## References

| Document | Location | Purpose |
|-----------|----------|---------|
| **Quick Start** | `SysScan/README.md` | User documentation |
| **Phase Plans** | `project_plan/PHASE*.md` | Development roadmap |
| **Architecture** | `SysScan/docs/ARCHITECTURE.md` | System design |
| **Contributing** | `SysScan/docs/CONTRIBUTING.md` | How to contribute |
| **License** | `SysScan/LICENSE` | MIT License |

---

## Gotchas & Quirks

### PowerShell vs Bash
- **Use `.\script.ps1`** for PowerShell scripts (not `bash script.sh`)
- **Git commands** work in both, but script execution differs

### Path Separators
- **Python:** Uses `os.path.normpath()` to handle `/` vs `\`
- **PowerShell:** Uses `\` in paths
- **Git:** Auto-converts LF ↔ CRLF (warning is normal)

### GitHub Push Protection
- **Never put tokens in files** - Use `~/.git-credentials`
- **If push blocked:** Check commit history for leaked secrets
- **Fix:** `git reset --hard <clean-commit>` then force push

---

## Quick Ramp-Up (3 Files to Read)

1. **`system_cleaner.py`** (309 lines) - Current monolithic CLI
2. **`project_plan/PHASE1_FOUNDATION.md`** - Phase 1 tasks
3. **`SysScan/README.md`** - User-facing documentation

**After reading these 3 files, you'll understand 80%+ of the codebase.**

---

**Last updated:** 2026-05-06
**Maintainer:** gyan4it
**Repo:** https://github.com/gyan4it/syscan
