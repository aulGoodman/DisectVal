# -*- mode: python ; coding: utf-8 -*-
"""
DisectVal PyInstaller Spec File
Builds 3 executables at the repository root:
- Setup.exe: Dependency installation and initial setup
- Dev.exe: Developer mode with full permissions (requires dev credentials)
- UserVersion.exe: Standard user version

Build command: pyinstaller DisectVal.spec
"""

block_cipher = None

# Common analysis settings
common_hiddenimports = [
    'disectval',
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
    'disectval.config.feature_flags',
    'disectval.training',
    'disectval.training.sync',
    'disectval.games',
    'disectval.games.profiles',
    'disectval.games.launcher',
    'customtkinter',
    'PIL',
    'cv2',
    'numpy',
    'psutil',
    'yaml',
    'cryptography',
    'bcrypt',
    'requests',
]

# ==================== Setup.exe ====================
setup_a = Analysis(
    ['src/disectval/setup_entry.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=common_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
setup_pyz = PYZ(setup_a.pure, setup_a.zipped_data, cipher=block_cipher)

setup_exe = EXE(
    setup_pyz,
    setup_a.scripts,
    setup_a.binaries,
    setup_a.datas,
    [],
    name='Setup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Console for setup to show progress
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

# ==================== Dev.exe ====================
dev_a = Analysis(
    ['src/disectval/dev_entry.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=common_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
dev_pyz = PYZ(dev_a.pure, dev_a.zipped_data, cipher=block_cipher)

dev_exe = EXE(
    dev_pyz,
    dev_a.scripts,
    dev_a.binaries,
    dev_a.datas,
    [],
    name='Dev',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

# ==================== UserVersion.exe ====================
user_a = Analysis(
    ['src/disectval/user_entry.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=common_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
user_pyz = PYZ(user_a.pure, user_a.zipped_data, cipher=block_cipher)

user_exe = EXE(
    user_pyz,
    user_a.scripts,
    user_a.binaries,
    user_a.datas,
    [],
    name='UserVersion',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
