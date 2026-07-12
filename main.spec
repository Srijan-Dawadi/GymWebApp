# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Five Star Fitness Desktop
===============================================
Build: pyinstaller --clean main.spec

Output:
- dist/FiveStarFitness/ (one-folder, recommended)
- dist/FiveStarFitness.exe (one-file, optional)

Key considerations:
- InsightFace models (~500MB) bundled via datas
- Anti-spoof ONNX model required
- face-api.js models for client-side detection
- All Django apps, templates, static files
- Runtime hook runs migrations on first launch
"""

import sys
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────
ROOT = Path(SPECPATH).resolve()

# InsightFace models - MUST be pre-downloaded:
# python -c "from insightface.app import FaceAnalysis; FaceAnalysis(name='buffalo_m').prepare()"
INSIGHTFACE_MODELS = Path.home() / '.insightface' / 'models' / 'buffalo_m'

# Anti-spoof model - YOU MUST PROVIDE THIS FILE
# Get from: https://github.com/Andy-yyf/Anti-Spoofing/blob/master/resources/anti_spoof_models/antispoof.onnx
ANTISPOOF_MODEL = ROOT / 'static' / 'antispoof' / 'antispoof.onnx'

# face-api.js models (included in repo)
FACE_API_MODELS = ROOT / 'static' / 'face-api' / 'models'

# ──────────────────────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────────────────────
if not INSIGHTFACE_MODELS.exists():
    print('WARNING: InsightFace models not found at', INSIGHTFACE_MODELS)
    print('Run: python -c "from insightface.app import FaceAnalysis; FaceAnalysis(name=\'buffalo_m\').prepare()"')

if not ANTISPOOF_MODEL.exists():
    print('WARNING: Anti-spoof model not found at', ANTISPOOF_MODEL)
    print('Download from: https://github.com/Andy-yyf/Anti-Spoofing/blob/master/resources/anti_spoof_models/antispoof.onnx')

# ──────────────────────────────────────────────────────────────
# Data files to bundle
# ──────────────────────────────────────────────────────────────
datas = [
    # Django project source
    ('gymapp', 'gymapp'),
    ('accounts', 'accounts'),
    ('members', 'members'),
    ('billing', 'billing'),
    ('attendance', 'attendance'),
    ('inventory', 'inventory'),
    ('cafe', 'cafe'),

    # Templates & static (collected at runtime too, but bundle for first run)
    ('templates', 'templates'),
    ('static', 'static'),

    # Migrations (required for runtime migration)
    ('members/migrations', 'members/migrations'),
    ('billing/migrations', 'billing/migrations'),
    ('attendance/migrations', 'attendance/migrations'),
    ('inventory/migrations', 'inventory/migrations'),
    ('cafe/migrations', 'cafe/migrations'),
    ('accounts/migrations', 'accounts/migrations'),

    # Management commands
    ('members/management', 'members/management'),

    # Manage.py
    ('manage.py', '.'),

    # Runtime hook
    ('runtime_hook.py', '.'),

    # Requirements (for metadata)
    ('requirements.txt', '.'),
]

# Add large ML models if they exist
if INSIGHTFACE_MODELS.exists():
    datas.append((str(INSIGHTFACE_MODELS), 'models/buffalo_m'))

if ANTISPOOF_MODEL.exists():
    datas.append((str(ANTISPOOF_MODEL), 'static/antispoof'))

if FACE_API_MODELS.exists():
    datas.append((str(FACE_API_MODELS), 'static/face-api/models'))

# ──────────────────────────────────────────────────────────────
# Hidden imports (modules PyInstaller can't auto-detect)
# ──────────────────────────────────────────────────────────────
hiddenimports = [
    # Django core
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
    'whitenoise',
    'whitenoise.middleware',
    'whitenoise.storage',

    # Project apps
    'accounts',
    'accounts.mixins',
    'accounts.views',
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

    # Face recognition stack
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

    # Stdlib
    'json', 'csv', 'threading', 'datetime', 'decimal',
    'base64', 'hashlib', 'hmac', 'secrets', 'pathlib',
    'importlib', 'importlib.metadata', 'pkgutil',
    'collections.abc',
]

# ──────────────────────────────────────────────────────────────
# Exclusions (reduce bundle size)
# ──────────────────────────────────────────────────────────────
excludes = [
    'tkinter', 'matplotlib', 'pytest', 'IPython', 'jupyter',
    'notebook', 'sphinx', 'docutils', 'pygments',
    'setuptools', 'pip', 'wheel', 'pkg_resources',
    'test', 'tests', 'testing',
]

# ──────────────────────────────────────────────────────────────
# Analysis
# ──────────────────────────────────────────────────────────────
a = Analysis(
    ['main.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Filter out __pycache__ and .pyc files
a.datas = [x for x in a.datas if '__pycache__' not in x[0] and '.pyc' not in x[0]]
a.binaries = [x for x in a.binaries if '__pycache__' not in x[0]]

# ──────────────────────────────────────────────────────────────
# PYZ (compressed bytecode)
# ──────────────────────────────────────────────────────────────
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# ──────────────────────────────────────────────────────────────
# Executable
# ──────────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FiveStarFitness',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / 'static' / 'icon.ico') if (ROOT / 'static' / 'icon.ico').exists() else None,
)

# ──────────────────────────────────────────────────────────────
# One-folder bundle (recommended for pyupdater)
# ──────────────────────────────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FiveStarFitness',
)