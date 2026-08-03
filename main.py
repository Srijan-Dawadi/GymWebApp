#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Five Star Fitness - Desktop Entry Point

Sets up Django environment, runs migrations, starts WSGI server,
then opens native webview window.
"""

import os
import sys
import time
import threading
from pathlib import Path

import webview


# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────
APP_NAME = 'Five Star Fitness'
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
MIN_WIDTH = 1024
MIN_HEIGHT = 700

HEALTH_CHECK_TIMEOUT = 60


# ──────────────────────────────────────────────────────────────
# Desktop Environment Setup
# ──────────────────────────────────────────────────────────────
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
        # Trick: opening a UDP socket to a public IP reveals the outbound interface IP
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


def setup_desktop_environment():
    """Configure Django settings and paths for desktop mode."""
    if getattr(sys, 'frozen', False):
        bundle_dir = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(sys.executable).parent
    else:
        bundle_dir = Path(__file__).parent.resolve()

    data_dir = _get_data_dir()

    os.environ['DJANGO_SETTINGS_MODULE'] = 'gymapp.settings'

    for p in [str(bundle_dir), str(bundle_dir / 'gymapp')]:
        if p not in sys.path:
            sys.path.insert(0, p)

    os.environ['DATA_DIR'] = str(data_dir)
    os.environ['MEDIA_ROOT'] = str(data_dir / 'media')
    os.environ['DB_PATH'] = str(data_dir / 'db.sqlite3')
    os.environ['STATIC_ROOT'] = str(bundle_dir / 'staticfiles')

    if 'SECRET_KEY' not in os.environ:
        secret_file = data_dir / '.secret_key'
        if secret_file.exists():
            os.environ['SECRET_KEY'] = secret_file.read_text().strip()
        else:
            import secrets as _secrets
            key = _secrets.token_urlsafe(50)
            secret_file.write_text(key)
            os.environ['SECRET_KEY'] = key

    os.environ.setdefault('DEBUG', 'False')

    # ── LAN access: office PCs reach the app via http://<this-ip>:8765 ──
    # Allow localhost plus every discovered local IP, and register matching
    # CSRF-trusted origins so POST forms work from other machines.
    lan_ips = _get_lan_ips()
    allowed_hosts = ['localhost', '127.0.0.1'] + lan_ips
    csrf_origins = ['http://localhost:8765', 'http://127.0.0.1:8765']
    csrf_origins += [f'http://{ip}:8765' for ip in lan_ips]
    os.environ.setdefault('ALLOWED_HOSTS', ','.join(allowed_hosts))
    os.environ.setdefault('CSRF_TRUSTED_ORIGINS', ','.join(csrf_origins))
    os.environ.setdefault('DATABASE_URL', f'sqlite:///{data_dir / "db.sqlite3"}')

    (data_dir / 'media').mkdir(parents=True, exist_ok=True)
    (data_dir / 'logs').mkdir(parents=True, exist_ok=True)

    return bundle_dir, data_dir


def _bootstrap_superuser(data_dir):
    """Create the initial superuser if none exists.

    Instead of a hardcoded default password, a strong one-time password is
    generated and the user is forced to change it on first login.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    if User.objects.filter(is_superuser=True).exists():
        print('[Setup] Superuser already exists')
        return

    import secrets as _secrets
    password = _secrets.token_urlsafe(12)
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
        print(f'[Setup] Superuser "admin" created. One-time password saved to: {creds_file}')
    except OSError as e:
        print(f'[Setup] Superuser "admin" created, but could not save credentials file: {e}')
    print('[Setup] Credentials: username=admin  (password is in the file above)')
    print('[Setup] IMPORTANT: the admin must change this password on first login.')


def initialize_django():
    """Set up Django: migrations, static files, default admin."""
    import django
    django.setup()
    print('[Setup] Django initialized')

    from django.core.management import call_command

    print('[Setup] Running migrations...')
    try:
        call_command('migrate', '--noinput')
        print('[Setup] Migrations complete')
    except Exception as e:
        print(f'[Setup] Migration error: {e}')

    print('[Setup] Collecting static files...')
    try:
        call_command('collectstatic', '--noinput', '--clear')
        print('[Setup] Static files collected')
    except Exception as e:
        print(f'[Setup] Static collect error: {e}')

    try:
        _bootstrap_superuser(_get_data_dir())
    except Exception as e:
        print(f'[Setup] Superuser creation skipped: {e}')


# ──────────────────────────────────────────────────────────────
# Django Server Management
# ──────────────────────────────────────────────────────────────
class DjangoServer:
    """Runs Django via WSGI in a background thread."""

    def __init__(self):
        self.server = None
        self.port = 8765
        self.url = f'http://127.0.0.1:{self.port}'
        self._ready = threading.Event()
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()

    def _run_server(self):
        from django.core.wsgi import get_wsgi_application

        application = get_wsgi_application()

        # Bind to all interfaces so office PCs can reach the app over the LAN.
        host = '0.0.0.0'

        try:
            # Prefer Waitress: threaded + stable on Windows.
            from waitress import create_server
            print(f'[Server] Starting (Waitress) on http://0.0.0.0:{self.port}...')
            self.server = create_server(application, host=host, port=self.port, threads=8)
            self._ready.set()
            self.server.run()
            return
        except ImportError:
            pass

        # Fallback: stdlib wsgiref (single-threaded, dev only)
        from wsgiref.simple_server import make_server
        print(f'[Server] Starting (wsgiref) on http://0.0.0.0:{self.port}...')
        self.server = make_server(host, self.port, application)
        self._ready.set()
        self.server.serve_forever()

    def wait_ready(self, timeout=HEALTH_CHECK_TIMEOUT):
        print('[Server] Waiting for server to start...')
        return self.url if self._ready.wait(timeout=timeout) else None

    def stop(self):
        if self.server:
            print('[Server] Stopping...')
            try:
                self.server.close()
            except AttributeError:
                pass
            try:
                self.server.shutdown()
            except AttributeError:
                pass
            self.server = None


# ──────────────────────────────────────────────────────────────
# WebView Window
# ──────────────────────────────────────────────────────────────
def create_window(url):
    window = webview.create_window(
        title=APP_NAME,
        url=url,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=(MIN_WIDTH, MIN_HEIGHT),
        resizable=True,
        fullscreen=False,
        minimized=False,
        on_top=False,
        confirm_close=True,
        background_color='#0a0a0a',
    )
    return window


# ──────────────────────────────────────────────────────────────
# Main Entry Point
# ──────────────────────────────────────────────────────────────
def main():
    print(f'=== {APP_NAME} Desktop ===')
    print(f'Python: {sys.version.split()[0]}')
    print(f'Platform: {sys.platform}')

    # 1. Set up desktop environment (env vars, paths, secrets)
    bundle_dir, data_dir = setup_desktop_environment()
    print(f'[Setup] Bundle dir: {bundle_dir}')
    print(f'[Setup] Data dir: {data_dir}')

    # 2. Initialize Django (migrations, admin user)
    initialize_django()

    # 3. Start WSGI server
    server = DjangoServer()
    server.start()

    url = server.wait_ready()
    if not url:
        print('FATAL: Django server failed to start')
        server.stop()
        sys.exit(1)

    # 4. Create native window
    window = create_window(url)

    # 5. Handle cleanup on close
    def on_closing():
        print('[Main] Window closing, shutting down...')
        server.stop()

    window.events.closing += on_closing

    # 6. Start webview event loop (blocks until window closed)
    webview.start(debug=False, storage_path=str(Path.home() / '.fivestarfitness_webview'))

    # 7. Cleanup
    server.stop()
    print('[Main] Shutdown complete')


if __name__ == '__main__':
    try:
        import webview
    except ImportError:
        print('ERROR: pywebview not installed. Run: pip install pywebview')
        sys.exit(1)

    if sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            pass

    main()
