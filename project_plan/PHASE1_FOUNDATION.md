# Phase 1: Foundation (Months 1-3)

## Overview
**Duration:** 3 months  
**Goal:** Modularize existing code, create REST API, and establish WebSocket communication for real-time updates.

---

## Why This Phase?

### Problem Statement
The current SysScan is a **monolithic CLI script** (309 lines in one file). To transform it into a web application, we need:
1. **Separation of concerns** - Scanning, analysis, deletion must be independent modules
2. **API endpoints** - Web UI can't directly call Python functions
3. **Real-time communication** - Scan progress must update live in browser

### Current Limitations
- ❌ Single file architecture (not scalable)
- ❌ No API (can't integrate with web UI)
- ❌ No real-time updates (progress bar is terminal-only)
- ❌ Tightly coupled (scanner + deleter + UI all in one)

---

## How to Implement

### 1.1 Modularize Existing Code

**Current State:** `system_cleaner.py` (309 lines, monolithic)

**Target Structure:**
```
syscan_web/
├── agent/
│   ├── __init__.py
│   ├── scanner.py          # Grid-based parallel scanner (extracted)
│   ├── analyzer.py         # Registry + file type analysis
│   ├── deleter.py          # Recycle bin + permanent delete
│   └── utils.py            # Common utilities (exclusions, etc.)
├── server/
│   ├── __init__.py
│   ├── app.py              # Flask application factory
│   ├── api.py              # REST API endpoints
│   ├── websocket.py       # WebSocket handler (Socket.IO)
│   └── auth.py            # Authentication (Phase 4 prep)
├── common/
│   ├── __init__.py
│   ├── config.py           # Shared configuration
│   └── constants.py       # Exclusion lists, paths
└── tests/
    ├── test_scanner.py
    ├── test_analyzer.py
    └── test_api.py
```

**Implementation Steps:**

#### Step 1: Extract Scanner Module
```python
# agent/scanner.py
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from .utils import is_excluded, get_size_fast

class GridScanner:
    """Grid-based parallel scanner (extracted from system_cleaner.py)"""
    
    def __init__(self, scan_paths, exclusions):
        self.scan_paths = scan_paths
        self.exclusions = exclusions
        self.found_items = []
        self.lock = threading.Lock()
    
    def scan(self):
        """Main scan method - returns list of (path, size) tuples"""
        grid_cells = self._collect_grid_cells()
        
        with ThreadPoolExecutor(max_workers=16) as executor:
            futures = {executor.submit(self._process_item, cell): cell 
                        for cell in grid_cells}
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    with self.lock:
                        self.found_items.append(result)
        
        return sorted(self.found_items, key=lambda x: -x[1])
    
    def _collect_grid_cells(self):
        """Collect all items from scan paths"""
        cells = []
        for path in self.scan_paths:
            if os.path.exists(path):
                for entry in os.scandir(path):
                    item_path = os.path.normpath(entry.path)
                    if not is_excluded(item_path, self.exclusions):
                        cells.append(item_path)
        return cells
    
    def _process_item(self, item_path):
        """Process single item - check size"""
        if os.path.isdir(item_path):
            size = get_size_fast(item_path)
        else:
            size = os.path.getsize(item_path)
        
        if size > 1024**3:  # >1GB
            return (item_path, size)
        return None
```

#### Step 2: Extract Deleter Module
```python
# agent/deleter.py
import ctypes
from ctypes import wintypes

class FileDeleter:
    """Handles file deletion (recycle bin or permanent)"""
    
    def send_to_recycle_bin(self, path):
        """Send file/folder to Recycle Bin (restorable)"""
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
        
        op = SHFILEOPSTRUCT()
        op.wFunc = FO_DELETE
        op.pFrom = ctypes.c_wchar_p(path + '\0')
        op.fFlags = FOF_ALLOWUNDO
        
        ret = ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op))
        return ret == 0 and not op.fAnyOperationsAborted
    
    def permanent_delete(self, path):
        """Permanently delete (irreversible)"""
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
```

---

### 1.2 Create REST API (Flask)

**Goal:** Web UI can trigger scans, get results, and delete files via HTTP.

```python
# server/api.py
from flask import Flask, request, jsonify
from flask_socketio import SocketIO
from agent.scanner import GridScanner
from agent.deleter import FileDeleter

app = Flask(__name__)
socketio = SocketIO(app)
scanner = GridScanner(scan_paths=['C:/'], exclusions=[])
deleter = FileDeleter()

@app.route('/api/scan/start', methods=['POST'])
def start_scan():
    """Trigger scan on agent"""
    try:
        results = scanner.scan()
        return jsonify({
            'status': 'complete',
            'files': [
                {
                    'path': r[0],
                    'size_gb': r[1] / 1024**3,
                    'type': 'cache',  # Determined by analyzer
                    'stars': 5,
                    'reason': 'Safe to delete'
                } for r in results
            ]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete', methods=['POST'])
def delete_files():
    """Delete selected files"""
    data = request.json
    paths = data.get('paths', [])
    method = data.get('method', 'recycle')
    
    for path in paths:
        if method == 'recycle':
            deleter.send_to_recycle_bin(path)
        else:
            deleter.permanent_delete(path)
    
    return jsonify({'status': 'deleted'}), 200

# WebSocket for real-time progress
@socketio.on('scan_progress')
def handle_progress(data):
    """Send progress updates to UI"""
    socketio.emit('progress_update', {
        'percent': data['percent'],
        'current_file': data['current_file'],
        'found_count': data['found_count']
    })
```

---

### 1.3 WebSocket for Real-Time Progress

**Goal:** Browser shows live progress (17-second scan updates every 0.3s).

```javascript
// webui/src/components/ProgressBar.jsx
import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';

function ProgressBar() {
    const [progress, setProgress] = useState(0);
    const [currentFile, setCurrentFile] = useState('');
    const [found, setFound] = useState(0);
    
    useEffect(() => {
        const socket = io('http://localhost:5000');
        
        socket.on('progress_update', (data) => {
            setProgress(data.percent);
            setCurrentFile(data.current_file);
            setFound(data.found_count);
        });
        
        return () => socket.disconnect();
    }, []);
    
    return (
        <div className="progress-bar">
            <div>Currently scanning: {currentFile}</div>
            <progress value={progress} max="100" />
            <div>Found: {found} items</div>
        </div>
    );
}
```

---

## Impact Analysis

### Positive Impacts
| Impact Area | Before | After | Improvement |
|------------|--------|-------|--------------|
| **Code Organization** | 1 file (309 lines) | 4+ modules | ✅ Maintainable |
| **API Access** | None (CLI only) | 5+ REST endpoints | ✅ Web-ready |
| **Real-time Updates** | Terminal only | WebSocket live | ✅ User experience |
| **Testability** | Hard to test | Unit tests per module | ✅ Reliable |
| **Scalability** | Monolithic | Modular | ✅ Easy to extend |

### Risks
- ⚠️ **Breaking changes** - Existing CLI may break during refactoring
- ⚠️ **Time investment** - 3 months for "invisible" changes
- ⚠️ **Complexity increase** - More files, more concepts

### Mitigation
- Use **feature flags** to switch between old/new code
- **Maintain CLI** as wrapper around new modules
- **Write tests** before refactoring (TDD approach)

---

## Need Requirements

### Development Needs
| Resource | Requirement | Purpose |
|----------|--------------|---------|
| **Python 3.8+** | Required | Core language |
| **Flask + Socket.IO** | `pip install flask flask-socketio` | Web server |
| **React.js** | Node.js + npm | Web UI |
| **Testing framework** | `pip install pytest` | Quality assurance |

### Human Resources
- **1 Backend developer** (Python/Flask) - 3 months
- **1 Frontend developer** (React) - 2 months (starts month 2)
- **1 QA engineer** (Testing) - 1 month (starts month 3)

### Infrastructure
- **GitHub repo** - Version control
- **CI/CD pipeline** - Auto-test on commit
- **Local dev environment** - Windows + Python + Node.js

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|------------|
| Code coverage | >80% | `pytest --cov` |
| API response time | <100ms | Load testing |
| WebSocket latency | <50ms | Browser DevTools |
| Module count | 4+ modules | File structure |
| Test count | 20+ tests | `pytest --collect-only` |

---

## Deliverables

### End of Month 1:
- [ ] `agent/scanner.py` - Modularized scanner
- [ ] `agent/deleter.py` - Modularized deleter
- [ ] Unit tests for both modules

### End of Month 2:
- [ ] `server/api.py` - REST API with 5+ endpoints
- [ ] `server/websocket.py` - WebSocket handler
- [ ] Basic React app (Progress bar component)

### End of Month 3:
- [ ] All modules integrated
- [ ] 20+ unit tests passing
- [ ] Documentation updated (API.md)
- [ ] Demo: CLI triggers API → UI shows progress

---

**Phase 1 turns SysScan from a CLI tool into a modular, API-driven foundation ready for web UI integration.**
