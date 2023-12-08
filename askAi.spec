# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['askAi.py'],
    pathex=[],
    binaries=[],
    datas=[('./askAi.png', '.')],
    hiddenimports=['pyperclip', 'requests', 'pydantic'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='askAi',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['askAi.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='askAi',
)
app = BUNDLE(
    coll,
    name='askAi.app',
    icon='askAi.ico',
    bundle_identifier=None,
)
