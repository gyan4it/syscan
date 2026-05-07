# SysCan - System Storage Analyzer & Cleaner

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/gyan4it/syscan)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue)](https://www.python.org)
[![React](https://img.shields.io/badge/react-18.2-61dafb)](https://reactjs.org)
[![TensorFlow](https://img.shields.io/badge/tensorflow-2.x-ff6f00)](https://www.tensorflow.org)

**SysCan** is an open-source, high-performance system storage analysis tool that identifies large files and folders (>1GB) using **grid-based parallel processing**. What used to take 10+ minutes now takes ~17 seconds for 200GB of storage.

---

## 🎉 **Features**

### Core Features
- ⚡ **Ultra-fast scanning** - 200GB in ~17 seconds using parallel processing
- 🎯 **Smart targeting** - Focuses on caches, logs, and uninstaller leftovers
- 🛡️ **Safe operations** - Dry-run mode, recycle bin support, exclusion system
- 🔍 **Deep analysis** - Registry leftover detection, file tree views
- 📊 **Detailed reporting** - JSON reports, progress tracking, size breakdowns

### Web Application (Phase 2+)
- 🌐 **React Web UI** - Modern interface with Tailwind CSS
- 🔐 **JWT Authentication** - Secure login with refresh tokens
- ⚙️ **Real-time progress** - WebSocket updates during scans
- ⭐ **Star ratings** - AI-powered deletion recommendations
- ☑️ **File tree** - Checkbox selection with expand/collapse

### Desktop Agent (Phase 3)
- 🖥️ **Cross-platform** - Windows, Linux, macOS support
- 📦 **Standalone EXE** - No Python required (10.4MB executable)
- 🔄 **Auto-updater** - Checks GitHub for new releases
- 📦 **NSIS Installer** - Professional Windows installer (10.3MB)

### Advanced Features (Phase 5)
- 🤖️ **AI Engine** - TensorFlow neural network for deletion predictions
- ☁️ **Cloud integration** - Simulated OneDrive, Dropbox, Google Drive support
- 📊 **Audit logging** - Track all user actions with IP addresses
- 🔒 **Rate limiting** - Prevent API abuse (configurable limits)

---

## 📁 **Project Structure**

```
syscan/
├── syscan_web/              # Main application (Phase 1-5)
│   ├── agent/               # Desktop agent (Windows EXE, cross-platform)
│   │   ├── agent.py          # Main agent with WebSocket client
│   │   ├── scanner.py       # Grid-based parallel scanner
│   │   ├── analyzer.py      # File analysis + star ratings
│   │   ├── deleter.py       # Safe file deletion (recycle/permanent)
│   │   ├── utils.py         # Shared utilities
│   │   ├── updater.py       # Auto-update checker
│   │   ├── SysCanAgent.exe  # Standalone EXE (10.4MB)
│   │   ├── SysScanAgent_Setup.exe  # NSIS installer (10.3MB)
│   │   └── install.ps1      # PowerShell installer
│   ├── server/              # Flask REST API + WebSocket server
│   │   ├── main.py          # Entry point
│   │   ├── app.py           # Flask app factory
│   │   ├── api.py           # REST endpoints (/scan, /items, etc.)
│   │   ├── auth.py          # JWT authentication + audit logs
│   │   ├── ai_engine.py     # TensorFlow AI predictions
│   │   ├── cloud_integration.py  # Cloud storage support
│   │   ├── websocket.py    # Socket.IO real-time updates
│   │   └── auth.db          # SQLite database
│   ├── webui/               # React frontend
│   │   ├── src/
│   │   │   ├── App.jsx          # Main component
│   │   │   ├── components/     # React components
│   │   │   │   ├── ProgressBar.jsx
│   │   │   │   ├── FileTree.jsx
│   │   │   │   ├── StarRating.jsx
│   │   │   │   └── DeleteDialog.jsx
│   │   │   └── index.js
│   │   ├── public/
│   │   ├── build/              # Production build (88kB JS)
│   │   └── cypress/           # E2E tests (8/8 passing)
│   ├── common/               # Shared modules
│   │   ├── config.py        # Configuration
│   │   └── constants.py    # Exclusion lists, paths
│   └── tests/                # Python unit tests
├── docs/                    # Documentation
│   ├── README.md           # This file
│   ├── ARCHITECTURE.md     # System design
│   ├── CONTRIBUTING.md     # How to contribute
│   ├── AGENTS.md           # Quick reference for agents
│   ├── reports/            # Phase completion reports
│   └── session-notes/      # Session summaries
├── project_plan/             # Development roadmap
│   ├── WEBSYS_CAN_PLAN.md
│   ├── PHASE1_FOUNDATION.md
│   ├── PHASE2_WEBUI.md
│   ├── PHASE3_AGENT.md
│   ├── PHASE4_SECURITY.md
│   ├── PHASE5_ADVANCED.md
│   └── QUICK_REFERENCE.md
├── legacy/                   # Old files (before modularization)
│   ├── original-cli/       # Original system_cleaner.py
│   ├── SysScan/           # Old web app (feedback form)
│   └── scripts/           # Utility scripts
├── venv/                     # Python virtual environment
├── .gitignore
├── LICENSE                   # MIT License
└── README.md                # This file
```

---

## 🚀 **Quick Start**

### Option 1: Desktop Agent (Easiest)
1. Download `SysScanAgent_Setup.exe` from [Releases](https://github.com/gyan4it/syscan/releases)
2. Run installer as Administrator
3. Agent starts automatically + opens http://localhost:5000

### Option 2: Python CLI (Developers)
```bash
# Clone repo
git clone https://github.com/gyan4it/syscan.git
cd syscan

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -r SysScan/requirements.txt

# Run scanner (dry-run = no deletions)
python syscan_web/agent/scanner.py --dry-run
```

### Option 3: Full Web Application
```bash
# Terminal 1: Start Flask server
cd syscan/syscan_web/server
$env:FLASK_APP="main.py"
venv\Scripts\python.exe main.py

# Terminal 2: Start React dev server
cd syscan/syscan_web/webui
npm install
npm start

# Open browser: http://localhost:3000
```

---

## 🔧 **API Endpoints**

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/health` | GET | Health check | ❌ |
| `/api` | GET | API root + endpoint list | ❌ |
| `/api/auth/login` | POST | Login (returns JWT) | ❌ |
| `/api/auth/refresh` | POST | Refresh token | ❌ |
| `/api/scan` | POST | Start system scan | ❌ |
| `/api/scan/status` | GET | Get scan progress | ❌ |
| `/api/items` | GET | List found items | ❌ |
| `/api/items/<path>` | DELETE | Delete specific item | ✅ |
| `/api/report` | GET | Get analysis report | ❌ |
| `/api/export` | GET | Export JSON report | ❌ |

---

## 🧪 **Testing**

### Python Tests
```bash
cd syscan/syscan_web
venv\Scripts\python.exe -m pytest tests/ -v --cov
```

### Cypress E2E Tests
```bash
cd syscan/syscan_web/webui
npx cypress run  # Headless
npx cypress open  # Interactive
```

**Current Status:** 8/8 Cypress tests passing ✅

---

## 📊 **Technology Stack**

| Component | Technology |
|-----------|-------------|
| **Backend (Server)** | Python 3.8+, Flask, Flask-SocketIO |
| **Backend (Agent)** | Python 3.8+, GridScanner, WebSocket |
| **Frontend** | React 18, Tailwind CSS, Socket.IO-client |
| **AI Engine** | TensorFlow 2.x, Keras |
| **Database** | SQLite (dev), PostgreSQL (prod) |
| **Testing** | pytest, Cypress |
| **Build** | PyInstaller (EXE), NSIS (installer), npm |

---

## 🛡️ **Security**

- ✅ JWT authentication with refresh tokens
- ✅ Rate limiting (configurable per endpoint)
- ✅ Audit logging (user actions + IP addresses)
- ✅ Recycle bin support (restorable deletions)
- ✅ Dry-run mode (scan only, no deletions)
- ✅ Exclusion system (protects user documents)
- ✅ Input validation on all endpoints

---

## 📦 **Releases**

| Version | Date | Description |
|--------|------|-------------|
| **v1.0.0** | 2026-05-07 | Phase 1-5 complete (Web UI, Agent, AI, Security) |
| **v0.1.0** | 2026-05-06 | Phase 1 complete (Modularization + API) |
| **v0.0.1** | 2026-05-06 | Initial CLI release |

👉 **[Download Latest Release](https://github.com/gyan4it/syscan/releases/latest)**

---

## 🤝 **Contributing**

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

**Quick steps:**
1. Fork the repo
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📄 **License**

MIT License - Free to use, modify, and distribute.

See [LICENSE](LICENSE) for details.

---

## 📧 **Contact & Feedback**

- **GitHub Issues:** https://github.com/gyan4it/syscan/issues
- **Email:** admin@systemchecking.com
- **Feedback Form:** Run `feedback_server.py` in `legacy/SysScan/`

---

**Built with ❤️ for system administrators, developers, and anyone who hates running out of disk space.**
