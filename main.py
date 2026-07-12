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
    os.environ.setdefault('ALLOWED_HOSTS', 'localhost,127.0.0.1')
    os.environ.setdefault('CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1:8765')
    os.environ.setdefault('DATABASE_URL', f'sqlite:///{data_dir / "db.sqlite3"}')

    (data_dir / 'media').mkdir(parents=True, exist_ok=True)
    (data_dir / 'logs').mkdir(parents=True, exist_ok=True)

    return bundle_dir, data_dir


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
        from django.contrib.auth import get_user_model
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@localhost', 'admin123')
            print('[Setup] Default admin created: admin / admin123')
        else:
            print('[Setup] Admin user already exists')
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
        from wsgiref.simple_server import make_server
        from django.core.wsgi import get_wsgi_application

        application = get_wsgi_application()
        print(f'[Server] Starting on {self.url}...')
        self.server = make_server('127.0.0.1', self.port, application)
        self._ready.set()
        self.server.serve_forever()

    def wait_ready(self, timeout=HEALTH_CHECK_TIMEOUT):
        print('[Server] Waiting for server to start...')
        return self.url if self._ready.wait(timeout=timeout) else None

    def stop(self):
        if self.server:
            print('[Server] Stopping...')
            self.server.shutdown()
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
