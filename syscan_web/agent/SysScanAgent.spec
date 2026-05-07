# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for SysScan Agent (Phase 3).
Creates a standalone Windows .exe in directory mode (avoids permission issues).
"""

import sys
sys.setrecursionlimit(5000)

from PyInstaller.building.build_main import Analysis as ANALYSIS, PYZ, EXE, COLLECT

block_cipher = None


a = ANALYSIS(
    ['agent.py'],
    datas=[],
    hiddenimports=[
        'syscan_web.agent.scanner',
        'syscan_web.agent.analyzer',
        'syscan_web.agent.deleter',
        'syscan_web.agent.utils',
        'syscan_web.common.config',
        'syscan_web.common.constants',
        'socketio',
        'packaging',
        'requests',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'tensorflow',
        'torch',
        'keras',
        'sklearn',
        'numpy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='SysCanAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to avoid permission issues
    console=False,  # No console window (background agent)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='SysCanAgent'
)

# No COLLECT needed for single EXE build
