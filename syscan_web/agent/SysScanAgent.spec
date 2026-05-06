# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for SysScan Agent (Phase 3).
Creates a standalone Windows .exe (no console).
"""

block_cipher = None


a = ANALYSIS(
    ['agent.py'],
    dat=[],
    hiddenimport=[
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
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SysScanAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window (background agent)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # Optional: Add icon if available
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.dat,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SysScanAgent',
)
