# -*- mode: python ; coding: utf-8 -*-
# 群小二 - PyInstaller打包配置（桌面GUI版本）

import os

block_cipher = None

# 项目路径
BASE_DIR = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['src/desktop_gui.py'],
    pathex=[BASE_DIR],
    binaries=[],
    datas=[
        ('data', 'data'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        'flask',
        'openai',
        'pandas',
        'sqlite3',
        'dotenv',
        'customtkinter',
        'tkinter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'numpy.testing',
        'nicegui',
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
    [],
    name='QunXiaoer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    windowed=True,  # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标: icon='icon.ico'
)
