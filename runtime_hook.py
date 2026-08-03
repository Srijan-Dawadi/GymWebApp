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


def _get_lan_ips():
    """Best-effort list of this machine's IPv4 addresses (for LAN access)."""
    ips = set()
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ips.add(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    try:
        import socket
        ips.update(socket.gethostbyname_ex(socket.gethostname())[2])
    except Exception:
        pass
    return sorted(ips)


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

    # ── LAN access: office PCs reach the app via http://<this-ip>:8765 ──
    lan_ips = _get_lan_ips()
    allowed_hosts = ['localhost', '127.0.0.1'] + lan_ips
    csrf_origins = ['http://localhost:8765', 'http://127.0.0.1:8765']
    csrf_origins += [f'http://{ip}:8765' for ip in lan_ips]
    os.environ.setdefault('ALLOWED_HOSTS', ','.join(allowed_hosts))
    os.environ.setdefault('CSRF_TRUSTED_ORIGINS', ','.join(csrf_origins))
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


def _create_superuser_if_needed(data_dir):
    """Create the initial superuser if none exists.

    Uses a strong one-time password (never a hardcoded default) and forces
    the admin to change it on first login.
    """
    try:
        import django
        django.setup()
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if User.objects.filter(is_superuser=True).exists():
            print('[runtime_hook] Superuser already exists')
            return

        import secrets
        password = secrets.token_urlsafe(12)
        user = User.objects.create_superuser('admin', 'admin@localhost', password)

        profile = getattr(user, 'profile', None)
        if profile is not None:
            profile.must_change_password = True
            profile.save(update_fields=['must_change_password'])

        creds_file = data_dir / 'admin_credentials.txt'
        try:
            creds_file.write_text(
                '5 Star Fitness — First-run admin credentials\n'
                '-----------------------------------------------\n'
                f'Username: admin\n'
                f'One-time password: {password}\n'
                '\nYou MUST change this password on your first login.\n',
                encoding='utf-8',
            )
            print(f'[runtime_hook] Superuser "admin" created. One-time password saved to: {creds_file}')
        except OSError as e:
            print(f'[runtime_hook] Superuser "admin" created, but could not save credentials file: {e}')
        print('[runtime_hook] IMPORTANT: the admin must change this password on first login.')
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
    _create_superuser_if_needed(data_dir)

    print('[runtime_hook] Initialization complete')


if __name__ == '__main__':
    main()