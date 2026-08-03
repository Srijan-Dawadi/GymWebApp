# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for 5 Star Fitness Gym Management System.

Build:
    pyinstaller gymapp.spec

Output:
    dist/GymWebApp/          (one-folder mode, faster startup)
    dist/GymWebApp.exe       (one-file mode, slower startup, single file)

For production, use one-folder mode with pyupdater for differential updates.
"""

import os
import sys
from pathlib import Path

# ── Project paths ───────────────────────────────────────────────────
ROOT = Path(__file__).parent.resolve()
SRC = ROOT / 'gymapp'
MANAGE = ROOT / 'manage.py'

# ── Version ─────────────────────────────────────────────────────────
# Update this on each release; pyupdater uses it for delta updates
VERSION = '1.0.0'

# ── Hidden imports (modules PyInstaller can't auto-detect) ─────────
hiddenimports = [
    # Django internals
    'django.contrib.auth.hashers',
    'django.contrib.contenttypes',
    'django.contrib.messages.context_processors',
    'django.core.mail.backends.smtp',
    'django.db.backends.sqlite3',
    'django.db.backends.postgresql',
    'django.template.loaders.filesystem',
    'django.template.loaders.app_directories',
    'django.templatetags.static',
    'django.templatetags.tz',

    # Project apps
    'accounts',
    'accounts.mixins',
    'accounts.views',
    'accounts.middleware',
    'accounts.dashboard_views',
    'accounts.reports_views',
    'accounts.user_views',
    'accounts.urls',
    'accounts.dashboard_urls',
    'members',
    'members.models',
    'members.views',
    'members.forms',
    'members.urls',
    'members.admin',
    'members.tests',
    'members.management.commands.sync_member_statuses',
    'billing',
    'billing.models',
    'billing.views',
    'billing.forms',
    'billing.urls',
    'billing.admin',
    'billing.tests',
    'billing.context_processors',
    'attendance',
    'attendance.models',
    'attendance.views',
    'attendance.urls',
    'attendance.admin',
    'attendance.tests',
    'inventory',
    'inventory.models',
    'inventory.views',
    'inventory.urls',
    'inventory.admin',
    'inventory.tests',
    'cafe',
    'cafe.models',
    'cafe.views',
    'cafe.urls',
    'cafe.admin',
    'cafe.tests',

    # Face recognition
    'face_service',
    'insightface',
    'insightface.app',
    'insightface.model_zoo',
    'onnxruntime',
    'onnxruntime.capi',
    'cv2',
    'numpy',
    'numpy.core.multiarray',
    'numpy.lib.format',

    # Stdlib modules often missed
    'json',
    'csv',
    'threading',
    'datetime',
    'decimal',
    'base64',
    'hashlib',
    'hmac',
    'secrets',
    'pathlib',
    'importlib',
    'importlib.metadata',
    'pkgutil',
    'collections.abc',
]

# ── Data files (templates, static, models, media) ──────────────────
# Format: (source_path, destination_path_in_bundle)
datas = [
    # Templates
    (str(ROOT / 'templates'), 'templates'),

    # Static files (face-api models, etc.)
    (str(ROOT / 'static'), 'static'),

    # Management commands
    (str(ROOT / 'members' / 'management'), 'members/management'),

    # Migrations (needed for first-run migrate)
    (str(ROOT / 'members' / 'migrations'), 'members/migrations'),
    (str(ROOT / 'billing' / 'migrations'), 'billing/migrations'),
    (str(ROOT / 'attendance' / 'migrations'), 'attendance/migrations'),
    (str(ROOT / 'inventory' / 'migrations'), 'inventory/migrations'),
    (str(ROOT / 'cafe' / 'migrations'), 'cafe/migrations'),
    (str(ROOT / 'accounts' / 'migrations'), 'accounts/migrations'),

    # Requirements (for pyupdater metadata)
    (str(ROOT / 'requirements.txt'), '.'),

    # Manage.py
    (str(MANAGE), '.'),
]

# ── Exclude unnecessary modules to reduce size ─────────────────────
excludes = [
    'tkinter', 'matplotlib', 'pytest', 'IPython', 'jupyter',
    'notebook', 'sphinx', 'docutils', 'pygments',
    'setuptools', 'pip', 'wheel', 'pkg_resources',
    'test', 'tests', 'testing',
]

# ── Binary dependencies (ONNX, OpenCV, InsightFace models) ─────────
# These are large; PyInstaller will bundle them automatically via hiddenimports
# But we need to ensure the antispoof model is included
binaries = []

antispoof_model = ROOT / 'static' / 'antispoof' / 'antispoof.onnx'
if antispoof_model.exists():
    binaries.append((str(antispoof_model), 'static/antispoof'))

# ── Runtime hook: set up Django settings, run migrations ──────────
runtime_hooks = [
    'runtime_hook.py',  # We'll create this next
]

# ── Analysis ───────────────────────────────────────────────────────
a = Analysis(
    [str(MANAGE)],
    pathex=[str(ROOT), str(SRC)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=runtime_hooks,
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# ── Filter out test files and other junk ──────────────────────────
a.datas = [x for x in a.datas if '__pycache__' not in x[0] and '.pyc' not in x[0]]
a.binaries = [x for x in a.binaries if '__pycache__' not in x[0]]

# ── PYZ (compressed bytecode) ─────────────────────────────────────
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# ── Executable ─────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GymWebApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX if available (install: apt install upx / brew install upx)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set False for GUI-only (but we need console for logs)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / 'static' / 'icon.ico') if (ROOT / 'static' / 'icon.ico').exists() else None,
)

# ── One-folder bundle (recommended for pyupdater) ─────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GymWebApp',
)