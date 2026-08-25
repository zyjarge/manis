# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for manis.

Build:
    pyinstaller manis.spec

The resulting .app lands in dist/manis.app.

This file is committed on purpose so the .app bundle is reproducible
from a fresh clone — no need to remember the --add-data / --windowed
flags.
"""

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('manis/web', 'manis/web')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # GUI stack we don't use — shrink the bundle
        'tkinter',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        'wx',
    ],
    noarchive=False,
    optimize=2,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='manis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    console=False,           # no Terminal.app window when launched from Finder
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='x86_64',    # Intel Mac; switch to 'arm64' on Apple Silicon,
                             # or None for the host arch
    codesign_identity=None,  # set to 'Developer ID Application: ...' for distribution
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=True,
    upx=False,
    upx_exclude=[],
    name='manis',
)

app = BUNDLE(
    coll,
    name='manis.app',
    icon=None,
    bundle_identifier='com.zhangyong.manis',
    info_plist={
        'CFBundleName': 'manis',
        'CFBundleDisplayName': 'manis - SSH Tunnel Manager',
        'CFBundleShortVersionString': '0.1.0',
        'CFBundleVersion': '0.1.0',
        'LSApplicationCategoryType': 'public.app-category.developer-tools',
        'LSMinimumSystemVersion': '11.0',
        'NSHighResolutionCapable': True,
        'NSAppleScriptEnabled': False,
    },
)