# SysScan Web Application - Development Plan

## Executive Summary

**Current State:** Command-line Python tool that scans local Windows systems in 17 seconds using grid-based parallel processing.

**Vision:** Transform SysScan into a **full web application** where users worldwide can scan their systems remotely through a browser, get detailed recommendations with star ratings, select files via checkboxes with tree view, and perform safe deletions.

**Key Innovation:** Desktop-grade performance (17s for 200GB) delivered through a web interface.

---

## 1. Feasibility Study

### 1.1 Technical Feasibility

| Aspect | Analysis | Rating |
|--------|----------|--------|
| **Browser-based file system access** | Web APIs limited (Security). Need desktop agent. | ⚠️ Medium |
| **Scan speed** | Grid-based parallel + ThreadPool works perfectly | ✅ High |
| **Web framework** | Flask/Django can handle real-time progress | ✅ High |
| **Real-time updates** | WebSocket (Socket.IO) for live progress | ✅ High |
| **Cross-platform** | Currently Windows-only. Need Linux/macOS modules | ⚠️ Medium |
| **Security** | Remote file deletion is HIGH RISK. Needs auth + confirmation | ⚠️ Medium |

### 1.2 Architecture Options

**Option A: Pure Web (Browser-only)**
- ❌ **NOT FEASIBLE** - Browsers can't access file system deeply (security sandbox)

**Option B: Desktop Agent + Web Dashboard (RECOMMENDED)**
- ✅ **FEASIBLE** - Lightweight agent installed on user's system
- Agent scans locally (fast), sends results to web dashboard
- User interacts via browser → Commands sent to agent → Agent performs actions

**Option C: Cloud-based Scanning**
- ❌ **NOT FEASIBLE** - Can't scan user's local machine from cloud

### 1.3 Recommended Architecture: **Desktop Agent + Web UI**

```
┌─────────────────────────────────────────────────────────────┐
│                    User's Browser                        │
│         (Angular/React/Vue + Tailwind CSS)              │
│  - File tree with checkboxes                           │
│  - Star ratings & recommendations                     │
│  - Progress bar & statistics                        │
│  - Delete/Recycle buttons                           │
└─────────────────────────────────────────────────────────────┘
                          ↕ WebSocket / REST API
┌─────────────────────────────────────────────────────────────┐
│                  Web Server (Flask)                       │
│  - REST API endpoints                               │
│  - WebSocket for real-time updates                    │
│  - Serves web UI (static files)                    │
│  - Authentication & session management               │
└─────────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────────┐
│              Desktop Agent (Python)                      │
│  - Installed on user's system                       │
│  - Grid-based parallel scanner (16+ workers)          │
│  - File system access (full permissions)              │
│  - Performs deletions (recycle/permanent)            │
│  - Sends progress/results to web server             │
└─────────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────────┐
│                  User's System                           │
│  - C:/, D:/ drives                                │
│  - Registry (Windows)                               │
│  - Caches, logs, temp files                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Development Plan

### Phase 1: Foundation (Months 1-3)

#### 1.1 Modularize Existing Code
**Goal:** Break `system_cleaner.py` into reusable modules

```
syscan_web/
├── agent/
│   ├── __init__.py
│   ├── scanner.py          # Grid-based parallel scanner
│   ├── analyzer.py         # Registry + file type analysis
│   ├── deleter.py          # Recycle bin + permanent delete
│   └── utils.py            # Common utilities
├── server/
│   ├── __init__.py
│   ├── app.py              # Flask application
│   ├── api.py              # REST API endpoints
│   ├── websocket.py       # WebSocket handler
│   └── auth.py            # Authentication
├── webui/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileTree.jsx    # Tree view with checkboxes
│   │   │   ├── StarRating.jsx  # Star ratings
│   │   │   └── ProgressBar.jsx # Real-time progress
│   │   ├── App.jsx
│   │   └── index.js
│   ├── public/
│   └── package.json
├── common/
│   ├── config.py           # Shared configuration
│   └── constants.py       # Exclusion lists, etc.
└── tests/
    ├── test_agent.py
    └── test_api.py
```

**Tasks:**
- [ ] Extract `scan_system()` → `agent/scanner.py`
- [ ] Extract `send_to_recycle_bin()` → `agent/deleter.py`
- [ ] Extract registry scan → `agent/analyzer.py`
- [ ] Create `common/config.py` (scan paths, exclusions, etc.)

#### 1.2 Create REST API (Flask)
**Goal:** Agent can receive commands and send results

```python
# server/api.py
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/api/scan/start', methods=['POST'])
def start_scan():
    """Trigger scan on agent"""
    # Send command to agent via WebSocket
    socketio.emit('scan_command', {'action': 'start', 'paths': ['C:/']})
    return jsonify({'status': 'scanning'})

@app.route('/api/scan/stop', methods=['POST'])
def stop_scan():
    """Stop ongoing scan"""
    socketio.emit('scan_command', {'action': 'stop'})
    return jsonify({'status': 'stopped'})

@app.route('/api/files', methods=['GET'])
def get_files():
    """Return found files with details"""
    return jsonify({
        'files': [
            {
                'path': 'C:/Users/...',
                'size_gb': 5.2,
                'type': 'cache',
                'recommendation': 'safe_to_delete',
                'stars': 5,
                'reason': 'npm cache - can be re-downloaded'
            }
        ]
    })

@app.route('/api/delete', methods=['POST'])
def delete_files():
    """Delete selected files (recycle/permanent)"""
    data = request.json
    paths = data.get('paths', [])
    method = data.get('method', 'recycle')  # recycle or permanent
    # Send to agent
    socketio.emit('delete_command', {'paths': paths, 'method': method})
    return jsonify({'status': 'deleting'})
```

#### 1.3 Real-Time Progress via WebSocket
**Goal:** Show live scan progress in browser

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

        socket.on('scan_progress', (data) => {
            setProgress(data.percent);
            setCurrentFile(data.current_file);
            setFound(data.found_count);
        });

        return () => socket.disconnect();
    }, []);

    return (
        <div>
            <div>{currentFile}</div>
            <progress value={progress} max="100" />
            <div>Found: {found} items</div>
        </div>
    );
}
```

---

### Phase 2: Web UI Development (Months 3-6)

#### 2.1 File Tree with Checkboxes
**Goal:** Users can select individual files/folders

```jsx
// webui/src/components/FileTree.jsx
import React, { useState } from 'react';
import Tree from 'react-checkbox-tree';

function FileTree({ files }) {
    const [checked, setChecked] = useState([]);
    const [expanded, setExpanded] = useState([]);

    const treeData = files.map(file => ({
        value: file.path,
        label: `${file.path} (${file.size_gb} GB) ⭐${file.stars}`,
        children: file.children || []
    }));

    return (
        <div>
            <Tree
                nodes={treeData}
                checked={checked}
                expanded={expanded}
                onCheck={checked => setChecked(checked)}
                onExpand={expanded => setExpanded(expanded)}
            />
            <button onClick={() => deleteSelected(checked)}>
                Delete Selected ({checked.length} items)
            </button>
            <button onClick={() => setChecked(files.map(f => f.path))}>
                Select All
            </button>
        </div>
    );
}
```

#### 2.2 Star Ratings & Recommendations
**Goal:** Show why files should be deleted

```python
# agent/analyzer.py
def get_recommendation(file_path, size_gb):
    """Return star rating (1-5) and reason for deletion"""
    
    # npm cache
    if 'npm-cache' in file_path:
        return {
            'stars': 5,
            'recommendation': 'safe_to_delete',
            'reason': 'npm cache can be safely deleted. Packages can be re-downloaded.',
            'type': 'cache'
        }
    
    # iPhone backup
    if 'MobileSync' in file_path:
        return {
            'stars': 3,
            'recommendation': 'review_required',
            'reason': 'iPhone backup. Review if you still need this backup.',
            'type': 'backup'
        }
    
    # Log files
    if file_path.endswith('.log'):
        return {
            'stars': 5,
            'recommendation': 'safe_to_delete',
            'reason': 'Log file. Old logs can be safely deleted.',
            'type': 'log'
        }
    
    # System files (should not appear, but just in case)
    if is_system_file(file_path):
        return {
            'stars': 0,
            'recommendation': 'do_not_delete',
            'reason': 'System file. DO NOT DELETE.',
            'type': 'system'
        }
    
    return {
        'stars': 2,
        'recommendation': 'review_required',
        'reason': 'Unknown file type. Review before deleting.',
        'type': 'unknown'
    }
```

#### 2.3 Delete Options (Recycle vs Permanent)
**Goal:** User chooses deletion method

```jsx
function DeleteDialog({ selectedFiles }) {
    const [method, setMethod] = useState('recycle');

    return (
        <div className="delete-dialog">
            <h3>Delete {selectedFiles.length} items?</h3>
            <div className="total-size">
                Total: {calculateTotalSize(selectedFiles)} GB
            </div>
            
            <div className="method-selector">
                <label>
                    <input 
                        type="radio" 
                        name="method" 
                        value="recycle"
                        checked={method === 'recycle'}
                        onChange={() => setMethod('recycle')}
                    />
                    ♻️ Recycle Bin (Restorable)
                </label>
                <label>
                    <input 
                        type="radio" 
                        name="method" 
                        value="permanent"
                        checked={method === 'permanent'}
                        onChange={() => setMethod('permanent')}
                    />
                    ⚠️ Permanent Delete (Irreversible)
                </label>
            </div>

            <div className="file-preview">
                {selectedFiles.map(f => (
                    <div key={f.path}>
                        ⭐{f.stars} {f.path} - {f.reason}
                    </div>
                ))}
            </div>

            <button className="confirm-delete" onClick={() => performDelete(method)}>
                Confirm Delete
            </button>
        </div>
    );
}
```

---

### Phase 3: Desktop Agent (Months 6-9)

#### 3.1 Agent Installer
**Goal:** User downloads and installs lightweight agent

```python
# agent/agent.py
import sys
import socketio
import time
from scanner import GridScanner
from deleter import FileDeleter

class SysScanAgent:
    def __init__(self, server_url):
        self.sio = socketio.Client()
        self.scanner = GridScanner()
        self.deleter = FileDeleter()
        self.server_url = server_url
        
    def connect(self):
        @self.sio.event
        def connect():
            print('Connected to server')
            self.sio.emit('agent_status', {'status': 'ready'})
        
        @self.sio.event
        def scan_command(data):
            if data['action'] == 'start':
                self.start_scan(data.get('paths', ['C:/']))
            elif data['action'] == 'stop':
                self.stop_scan()
        
        @self.sio.event
        def delete_command(data):
            self.delete_files(data['paths'], data['method'])
        
        self.sio.connect(self.server_url)
    
    def start_scan(self, paths):
        results = self.scanner.scan(paths)
        self.sio.emit('scan_complete', {'files': results})
    
    def delete_files(self, paths, method):
        for path in paths:
            if method == 'recycle':
                self.deleter.send_to_recycle_bin(path)
            else:
                self.deleter.permanent_delete(path)
        self.sio.emit('delete_complete', {'status': 'done'})

if __name__ == '__main__':
    agent = SysScanAgent('http://localhost:5000')
    agent.connect()
    # Keep running
    while True:
        time.sleep(1)
```

#### 3.2 Auto-Update Mechanism
**Goal:** Agent updates itself automatically

```python
# agent/updater.py
import requests
import os
import sys
from packaging import version

def check_for_update():
    current_version = '1.0.0'
    response = requests.get('http://api.github.com/repos/syscan/syscan/releases/latest')
    latest = response.json()['tag_name']
    
    if version.parse(latest) > version.parse(current_version):
        download_and_install(latest)

def download_and_install(version):

    url = f'https://github.com/syscan/syscan/releases/download/{version}/agent.zip'
    # Download, extract, restart
    pass
```

---

### Phase 4: Security & Auth (Months 9-12)

#### 4.1 Authentication
**Goal:** Only authorized users can access their agent

```python
# server/auth.py
from flask_jwt_extended import JWTManager, create_access_token

jwt = JWTManager()

@app.route('/api/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    
    # Verify credentials (check against DB)
    if verify_user(username, password):
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    return jsonify({'msg': 'Bad credentials'}), 401

# Protect endpoints
from flask_jwt_extended import jwt_required

@app.route('/api/scan/start', methods=['POST'])
@jwt_required()
def start_scan():
    # Only authenticated users can start scans
    pass
```

#### 4.2 Confirmation for Deletions
**Goal:** Prevent accidental deletions

```javascript
function DeleteDialog({ selectedFiles }) {
    const [confirmText, setConfirmText] = useState('');
    const requiresConfirmation = selectedFiles.length > 10 || 
                                  selectedFiles.some(f => f.stars <= 2);
    
    return (
        <div>
            {requiresConfirmation && (
                <div className="confirmation">
                    <p>Type "DELETE" to confirm:</p>
                    <input 
                        value={confirmText}
                        onChange={e => setConfirmText(e.target.value)}
                    />
                </div>
            )}
            <button 
                disabled={requiresConfirmation && confirmText !== 'DELETE'}
                onClick={performDelete}
            >
                Confirm Delete
            </button>
        </div>
    );
}
```

---

## 3. Technology Stack

### Backend (Server + Agent)
- **Flask** - Lightweight web framework
- **Flask-SocketIO** - Real-time WebSocket communication
- **Flask-JWT-Extended** - Authentication
- **Python 3.8+** - Core language
- **concurrent.futures** - Parallel scanning (unchanged from original)

### Frontend (Web UI)
- **React.js** (or Vue.js/Angular) - Component-based UI
- **Tailwind CSS** - Modern styling
- **react-checkbox-tree** - Tree view with checkboxes
- **Socket.IO-client** - Real-time updates
- **Axios** - HTTP requests

### Database
- **SQLite** (Phase 1) - Local storage for scan history
- **PostgreSQL** (Phase 4) - For multi-user support

---

## 4. Implementation Timeline

```
Months 1-3:   Foundation
              ├── Modularize code
              ├── Create REST API
              └── WebSocket for real-time progress

Months 3-6:   Web UI
              ├── File tree with checkboxes
              ├── Star ratings & recommendations
              └── Delete dialog (recycle/permanent)

Months 6-9:   Desktop Agent
              ├── Agent installer (Windows .exe)
              ├── Auto-update mechanism
              └── Cross-platform support (Linux/macOS)

Months 9-12:  Security & Scale
              ├── Authentication (JWT)
              ├── Confirmation dialogs
              └── Multi-user support (enterprise)

Year 2:      Advanced Features
              ├── AI-based recommendations
              ├── Cloud sync (Dropbox, OneDrive)
              └── Mobile app (iOS/Android)
```

---

## 5. Key Challenges & Solutions

### Challenge 1: Browser Security Sandbox
**Problem:** Browsers can't access file system deeply.

**Solution:** Desktop agent architecture - agent runs locally with full permissions, communicates with web UI via WebSocket.

### Challenge 2: Real-Time Progress Updates
**Problem:** Scanning is fast (~17s), need smooth progress bar.

**Solution:** WebSocket emits progress every 0.3s with current file, found count, percent complete.

### Challenge 3: Large File Trees
**Problem:** 159+ grid cells, need efficient tree rendering.

**Solution:** Virtualized lists (react-window) + lazy loading for tree nodes.

### Challenge 4: Safe Deletions
**Problem:** Remote deletion is risky.

**Solution:** 
- Recycle bin as default (restorable)
- Confirmation for permanent delete
- "Select All" warns if system files detected
- Audit log for all deletions

---

## 6. Success Metrics

| Metric | Target |
|--------|--------|
| Scan speed | <20 seconds for 200GB |
| UI responsiveness | <100ms latency |
| User adoption | 1000+ downloads in first 6 months |
| Safety | 0 incidents of accidental system file deletion |
| User satisfaction | 4+ stars in feedback |

---

## 7. Next Steps

1. **Review this plan** - Provide feedback
2. **Choose tech stack** - React vs Vue, Flask vs Django
3. **Start Phase 1** - Modularize existing code
4. **Set up dev environment** - GitHub repo, CI/CD pipeline

---

**This plan transforms SysScan from a CLI tool into a world-class web application while maintaining the core 17-second scan speed that makes it special.**
