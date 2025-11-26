# -*- mode: python ; coding: utf-8 -*-
"""
DisectVal PyInstaller Spec File
Build command: pyinstaller DisectVal.spec
The resulting executable will be created in the dist/ folder.
After building, copy DisectVal.exe from dist/ to the repository root.
"""

block_cipher = None

a = Analysis(
    ['src/disectval/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'disectval.auth',
        'disectval.auth.credentials',
        'disectval.auth.roles',
        'disectval.gui',
        'disectval.gui.theme',
        'disectval.gui.login_page',
        'disectval.gui.dashboard',
        'disectval.analysis',
        'disectval.analysis.video_analyzer',
        'disectval.utils',
        'disectval.utils.valorant_detector',
        'disectval.utils.windows_checker',
        'disectval.config',
        'disectval.config.settings',
        'customtkinter',
        'PIL',
        'cv2',
        'numpy',
        'psutil',
        'yaml',
        'cryptography',
        'bcrypt',
    ],
    hookspath=[],
    hooksconfig={},
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
    a.binaries,
    a.datas,
    [],
    name='DisectVal',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for GUI application (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here: icon='assets/icon.ico'
)
