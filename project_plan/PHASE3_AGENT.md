# Phase 3: Desktop Agent (Months 6-9)

## Overview
**Duration:** 3 months  
**Goal:** Build a lightweight desktop agent that users install on their systems for secure file system access.

---

## Why This Phase?

### Problem Statement
Browsers **can't access file systems** deeply (security sandbox). To scan a user's system:
1. **Need local permissions** - Read/write access to scan and delete files
2. **Need high performance** - Grid-based scanner must run locally
3. **Need real-time communication** - Send progress/results to web UI

### Current Limitations
- ❌ Web browsers limited to basic file inputs
- ❌ Can't scan `C:/Users` or registry from browser
- ❌ Can't send files to Recycle Bin via web

### Solution: Desktop Agent Architecture
```
User's Browser ←→ Web Server (Flask) ←→ Desktop Agent (Python)
                      ↑
                  WebSocket (Socket.IO)
                      ↓
              User's Local System
```

---

## How to Implement

### 3.1 Agent Core Structure

**Goal:** Create a standalone Python agent that runs on user's system.

```python
# agent/agent.py
import sys
import time
import socketio
from agent.scanner import GridScanner
from agent.deleter import FileDeleter
from agent.analyzer import FileAnalyzer

class SysScanAgent:
    """Desktop agent that communicates with web server"""
    
    def __init__(self, server_url='http://localhost:5000'):
        self.sio = socketio.Client()
        self.scanner = GridScanner()
        self.deleter = FileDeleter()
        self.analyzer = FileAnalyzer()
        self.server_url = server_url
        self.is_scanning = False
        
    def connect(self):
        """Connect to web server via WebSocket"""
        
        @self.sio.event
        def connect():
            print('✅ Connected to SysScan server')
            self.sio.emit('agent_status', {'status': 'ready', 'version': '1.0.0'})
        
        @self.sio.event
        def scan_command(data):
            """Handle scan command from server"""
            if data['action'] == 'start':
                paths = data.get('paths', ['C:/'])
                self.start_scan(paths)
            elif data['action'] == 'stop':
                self.stop_scan()
        
        @self.sio.event
        def delete_command(data):
            """Handle delete command from server"""
            paths = data.get('paths', [])
            method = data.get('method', 'recycle')
            self.delete_files(paths, method)
        
        try:
            self.sio.connect(self.server_url)
        except Exception as e:
            print(f'❌ Connection failed: {e}')
            sys.exit(1)
    
    def start_scan(self, paths):
        """Start scanning"""
        self.is_scanning = True
        self.sio.emit('scan_started', {'paths': paths})
        
        try:
            results = self.scanner.scan(paths)
            
            # Analyze results (add stars, reasons)
            analyzed = []
            for path, size in results:
                analysis = self.analyzer.analyze(path, size)
                analyzed.append({
                    'path': path,
                    'size_gb': size / 1024**3,
                    'stars': analysis['stars'],
                    'reason': analysis['reason'],
                    'type': analysis['type']
                })
            
            self.sio.emit('scan_complete', {'files': analyzed})
        except Exception as e:
            self.sio.emit('scan_error', {'error': str(e)})
        finally:
            self.is_scanning = False
    
    def stop_scan(self):
        """Stop ongoing scan"""
        self.scanner.stop()
        self.is_scanning = False
        self.sio.emit('scan_stopped', {})
    
    def delete_files(self, paths, method):
        """Delete files (recycle or permanent)"""
        results = []
        for path in paths:
            try:
                if method == 'recycle':
                    success = self.deleter.send_to_recycle_bin(path)
                else:
                    self.deleter.permanent_delete(path)
                    success = True
                
                results.append({'path': path, 'success': success})
            except Exception as e:
                results.append({'path': path, 'success': False, 'error': str(e)})
        
        self.sio.emit('delete_complete', {'results': results})
    
    def run(self):
        """Main loop"""
        print('🚀 SysScan Agent started')
        self.connect()
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print('\n👋 Agent shutting down...')
            self.sio.disconnect()

if __name__ == '__main__':
    agent = SysScanAgent()
    agent.run()
```

---

### 3.2 Agent Installer (Windows .exe)

**Goal:** Users download and install agent with one click.

#### Option A: PyInstaller (Simple)
```bash
# Create standalone .exe
pip install pyinstaller

# Create spec file
pyi-makespec --onefile --noconsole --name=SysScanAgent agent/agent.py

# Build
pyinstaller SysScanAgent.spec
# Output: dist/SysScanAgent.exe (single file, ~10MB)
```

#### Option B: NSIS Installer (Professional)
```nsis
; installer.nsi
OutFile "SysScanAgent_Setup.exe"
InstallDir "$PROGRAMFILES\SysScan"

Section "MainSection" SEC01
    File "SysScanAgent.exe"
    CreateShortcut "$DESKTOP\SysScan Agent.lnk" "$INSTDIR\SysScanAgent.exe"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Run" \
        "SysScanAgent" "$INSTDIR\SysScanAgent.exe"
SectionEnd
```

**User Experience:**
1. Download `SysScanAgent_Setup.exe`
2. Run installer (Next → Next → Finish)
3. Agent starts automatically (runs in background)
4. Browser opens `http://localhost:5000` with web UI

---

### 3.3 Auto-Update Mechanism

**Goal:** Agent updates itself automatically when new version available.

```python
# agent/updater.py
import requests
import os
import sys
import zipfile
from packaging import version

class AgentUpdater:
    def __init__(self, current_version='1.0.0'):
        self.current_version = current_version
        self.update_url = 'https://api.github.com/repos/syscan/syscan/releases/latest'
    
    def check_for_update(self):
        """Check if newer version available"""
        try:
            response = requests.get(self.update_url, timeout=10)
            latest = response.json()['tag_name']
            
            if version.parse(latest) > version.parse(self.current_version):
                return latest
        except:
            pass
        return None
    
    def download_and_install(self, version):
        """Download and install update"""
        url = f'https://github.com/syscan/syscan/releases/download/{version}/SysScanAgent.zip'
        
        # Download
        response = requests.get(url, stream=True)
        with open('update.zip', 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Extract
        with zipfile.ZipFile('update.zip', 'r') as zip_ref:
            zip_ref.extractall('update/')
        
        # Restart (Windows)
        os.execv('update/SysScanAgent.exe', sys.argv)
```

**Integration:**
```python
# In agent.py main loop
updater = AgentUpdater()
latest = updater.check_for_update()
if latest:
    print(f'🔄 Updating to {latest}...')
    updater.download_and_install(latest)
```

---

### 3.4 Cross-Platform Support (Linux/macOS)

**Goal:** Extend agent to Linux and macOS.

#### Linux Support
```python
# agent/platform/linux.py
import os
import subprocess

class LinuxScanner:
    def get_scan_paths(self):
        """Return Linux-specific paths"""
        return [
            '/home',
            '/var/tmp',
            '/tmp',
            os.path.expanduser('~/.cache'),
            os.path.expanduser('~/.local/share')
        ]
    
    def send_to_trash(self, path):
        """Send to Linux trash (uses trash-cli)"""
        subprocess.run(['trash', path])
```

#### macOS Support
```python
# agent/platform/macos.py
import os

class MacScanner:
    def get_scan_paths(self):
        """Return macOS-specific paths"""
        return [
            '/Users',
            os.path.expanduser('~/Library/Caches'),
            os.path.expanduser('~/Library/Logs'),
            os.path.expanduser('~/Library/Application Support')
        ]
    
    def send_to_trash(self, path):
        """Send to macOS trash"""
        os.system(f'osascript -e "tell app \\"Finder\\" to delete POSIX file \\"{path}\\""')
```

**Platform Detection:**
```python
# agent/scanner.py
import platform

def get_platform_scanner():
    system = platform.system()
    
    if system == 'Windows':
        from .platform.windows import WindowsScanner
        return WindowsScanner()
    elif system == 'Linux':
        from .platform.linux import LinuxScanner
        return LinuxScanner()
    elif system == 'Darwin':
        from .platform.macos import MacScanner
        return MacScanner()
    else:
        raise Exception(f'Unsupported platform: {system}')
```

---

## Impact Analysis

### Positive Impacts
| Impact Area | Before | After | Improvement |
|------------|--------|-------|--------------|
| **Platform Support** | Windows only | Windows + Linux + macOS | ✅ 3x reach |
| **User Experience** | CLI only | Installer → Auto-start | ✅ Professional |
| **Maintenance** | Manual updates | Auto-update | ✅ Always current |
| **Performance** | 17s scan | Same (local processing) | ✅ Unchanged |

### Risks
- ⚠️ **Code complexity** - 3x platforms = 3x code
- ⚠️ **Testing matrix** - Need to test on 3 OS types
- ⚠️ **Binary distribution** - .exe (Windows), .app (macOS), binary (Linux)

### Mitigation
- **Platform abstraction layer** - Common interface, platform-specific implementations
- **CI/CD for all platforms** - GitHub Actions with Windows/Linux/macOS runners
- **Virtual machines** - Test on clean installs of each OS

---

## Need Requirements

### Development Needs
| Resource | Requirement | Purpose |
|----------|--------------|---------|
| **PyInstaller** | `pip install pyinstaller` | Create .exe |
| **NSIS** | Windows installer creator | Professional installer |
| **Linux VM** | Ubuntu 20.04+ | Test Linux agent |
| **macOS VM** | macOS 11+ | Test macOS agent |

### Human Resources
- **1 Agent developer** (Python) - 3 months full-time
- **1 DevOps engineer** (CI/CD) - 1 month (setup)
- **1 QA engineer** (Cross-platform) - 1 month (testing)

### Infrastructure
- **GitHub Releases** - Host agent binaries
- **CDN** - Fast downloads worldwide
- **Update server** - Check latest version API

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|------------|
| **Installer size** | <15MB | File properties |
| **Startup time** | <3 seconds | `time python agent.py` |
| **Update success** | >95% | Log analysis |
| **Platform coverage** | 3 platforms | Windows + Linux + macOS |
| **User adoption** | 100+ installs | Download count |

---

## Deliverables

### End of Month 6:
- [ ] `agent/agent.py` - Core agent with WebSocket
- [ ] `agent/updater.py` - Auto-update mechanism
- [ ] Windows .exe using PyInstaller

### End of Month 7:
- [ ] NSIS installer script
- [ ] Linux support (`agent/platform/linux.py`)
- [ ] Basic macOS support (`agent/platform/macos.py`)

### End of Month 8:
- [ ] Cross-platform testing (3 VMs)
- [ ] Documentation (`docs/AGENT.md`)
- [ ] Demo: Install agent → Scan → Delete via web UI

---

**Phase 3 turns SysScan from a web-connected tool into a professional, cross-platform desktop agent that users can install and forget.**
