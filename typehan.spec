# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None
base_dir = os.path.abspath('.')

a = Analysis(
    ['main.py'],
    pathex=[base_dir],
    binaries=[],
    datas=[
        ('data/builtin', 'data/builtin'),
        ('resources', 'resources'),
        ('图标.png', '.'),
        ('兔子.png', '.'),
        ('app.ico', '.'),
    ],
    hiddenimports=[
        'pypinyin',
        'pypinyin.style',
        'feedparser',
        'bs4',
        'lxml',
        'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'unittest', 'test', 'distutils',
        'setuptools', 'pip', 'numpy', 'scipy',
        'matplotlib', 'PIL', 'cv2',
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
    [],
    exclude_binaries=True,
    name='逐字拾光',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,         # hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='逐字拾光',
)
