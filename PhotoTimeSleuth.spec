# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['PhotoTimeSleuth\\app.py'],
    pathex=["."],
    binaries=[],
    datas=[
        ('PhotoTimeSleuth/templates/', 'PhotoTimeSleuth/templates'),
        ('PhotoTimeSleuth/static', 'PhotoTimeSleuth/static'),
        ('PhotoTimeSleuth/default_bday.txt', 'PhotoTimeSleuth'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PhotoTimeSleuth',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
