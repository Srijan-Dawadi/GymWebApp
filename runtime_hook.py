# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller runtime hook for GymWebApp desktop.

Runs inside the bundled executable BEFORE main.py executes.
Sets up Django environment, runs migrations, prepares media/static dirs.
"""

import os
import sys
import shutil
from pathlib import Path


def _get_bundle_root():
    """Get the bundle root where PyInstaller extracts data files."""
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        return Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(sys.executable).parent
    # Development mode
    return Path(__file__).parent.parent


def _get_data_dir():
    """Get persistent data directory (per-user, writable)."""
    if sys.platform == 'win32':
        base = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
    elif sys.platform == 'darwin':
        base = Path.home() / 'Library' / 'Application Support'
    else:
        base = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local' / 'share'))

    data_dir = base / 'FiveStarFitness'
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def _setup_environment():
    """Configure Django settings and paths."""
    bundle_root = _get_bundle_root()
    data_dir = _get_data_dir()

    # Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gymapp.settings')

    # Python path
    for p in [str(bundle_root), str(bundle_root / 'gymapp')]:
        if p not in sys.path:
            sys.path.insert(0, p)

    # Writable directories
    os.environ['DATA_DIR'] = str(data_dir)
    os.environ['MEDIA_ROOT'] = str(data_dir / 'media')
    os.environ['DB_PATH'] = str(data_dir / 'db.sqlite3')

    # Django env vars (settings.py reads these via django-environ)
    if 'SECRET_KEY' not in os.environ:
        secret_file = data_dir / '.secret_key'
        if secret_file.exists():
            os.environ['SECRET_KEY'] = secret_file.read_text().strip()
        else:
            import secrets
            key = secrets.token_urlsafe(50)
            secret_file.write_text(key)
            os.environ['SECRET_KEY'] = key
    os.environ.setdefault('DEBUG', 'False')
    os.environ.setdefault('ALLOWED_HOSTS', 'localhost,127.0.0.1')
    os.environ.setdefault('CSRF_TRUSTED_ORIGINS', '')
    os.environ.setdefault('DATABASE_URL', f'sqlite:///{data_dir / "db.sqlite3"}')

    # Create subdirs
    (data_dir / 'media').mkdir(parents=True, exist_ok=True)
    (data_dir / 'logs').mkdir(parents=True, exist_ok=True)

    # Static files (served by WhiteNoise from bundle)
    os.environ['STATIC_ROOT'] = str(bundle_root / 'staticfiles')

    return bundle_root, data_dir


def _run_django_command(cmd):
    """Run a Django management command in-process."""
    from django.core.management import call_command
    try:
        call_command(*cmd)
        return True
    except Exception as e:
        print(f'[runtime_hook] Command error: {e}')
        return False


def _run_migrations():
    """Apply database migrations."""
    print('[runtime_hook] Running database migrations...')
    return _run_django_command(['migrate', '--noinput'])


def _collect_static():
    """Collect static files (optional, already bundled)."""
    print('[runtime_hook] Collecting static files...')
    return _run_django_command(['collectstatic', '--noinput', '--clear'])


def _create_superuser_if_needed():
    """Create default admin user if none exists."""
    try:
        import django
        django.setup()
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            print('[runtime_hook] Creating default admin user...')
            User.objects.create_superuser('admin', 'admin@localhost', 'admin123')
            print('[runtime_hook] Default admin created: admin / admin123')
    except Exception as e:
        print(f'[runtime_hook] Superuser creation skipped: {e}')


def main():
    """Main runtime hook entry point."""
    print('[runtime_hook] Initializing GymWebApp desktop...')

    bundle_root, data_dir = _setup_environment()
    print(f'[runtime_hook] Bundle root: {bundle_root}')
    print(f'[runtime_hook] Data dir: {data_dir}')

    # Initialize Django
    import django
    django.setup()

    # Run migrations
    if not _run_migrations():
        print('[runtime_hook] WARNING: Migrations failed, continuing anyway...')

    # Collect static (already bundled, but ensures manifest)
    _collect_static()

    # Create default admin
    _create_superuser_if_needed()

    print('[runtime_hook] Initialization complete')


if __name__ == '__main__':
    main()