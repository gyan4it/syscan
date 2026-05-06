"""
Constants for SysCan.
Shared paths, patterns, and default values.
"""

import os

# Root scan paths
DEFAULT_SCAN_PATHS = ['C:/']

# Specific paths to always scan (in addition to C:/)
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

# Minimum size to report (1 GB)
MIN_SIZE_BYTES = 1024 ** 3

# Scan performance
DEFAULT_MAX_WORKERS = 256
MEMORY_PER_WORKER_MB = 50

# Output paths
DEFAULT_REPORT_PATH = os.path.join(
    os.path.expanduser('~'),
    'Desktop',
    'SystemChecking',
    'cleanup_report.json'
)

# Registry paths to check for leftovers
REGISTRY_PATHS = [
    'HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',
    'HKLM:\\Software\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*',
    'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\*'
]

# API settings (for Phase 1+)
API_HOST = '127.0.0.1'
API_PORT = 5000
API_PREFIX = '/api'

# WebSocket settings
WS_NAMESPACE = '/scan'

# File extensions to skip during size calculation (temporary/small files)
SKIP_EXTENSIONS = ['.tmp', '.temp', '.log', '.cache']

# Performance targets (from project plan)
TARGET_SCAN_SPEED_GBPS = 2.0  # 2 GB/s scan rate
TARGET_API_RESPONSE_MS = 100   # API response <100ms
