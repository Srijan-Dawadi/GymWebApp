@echo off
title GymApp - First Time Setup
color 0A

echo ============================================
echo   GymApp - First Time Setup
echo ============================================
echo.

:: Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:: Check Git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git is not installed or not in PATH.
    echo Please install Git from https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [OK] Python and Git found.
echo.

:: Create virtual environment
echo [1/5] Creating virtual environment...
python -m venv myenv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)
echo [OK] Virtual environment created.
echo.

:: Install dependencies
echo [2/5] Installing dependencies (this may take a few minutes)...
myenv\Scripts\pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo [OK] Dependencies installed.
echo.

:: Create .env file if it doesn't exist
echo [3/5] Setting up environment config...
if not exist .env (
    echo SECRET_KEY=gymapp-local-secret-key-change-this-in-production> .env
    echo DEBUG=False>> .env
    echo DATABASE_URL=sqlite:///db.sqlite3>> .env
    echo ALLOWED_HOSTS=localhost,127.0.0.1>> .env
    echo CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000>> .env
    echo [OK] .env file created.
) else (
    echo [OK] .env file already exists, skipping.
)
echo.

:: Run migrations
echo [4/5] Setting up database...
myenv\Scripts\python manage.py migrate --run-syncdb
if errorlevel 1 (
    echo [ERROR] Database setup failed.
    pause
    exit /b 1
)
echo [OK] Database ready.
echo.

:: Create superuser
echo [5/5] Creating admin account...
echo.
echo Enter the admin username (e.g. admin):
set /p ADMIN_USER=Username: 
echo Enter the admin password:
set /p ADMIN_PASS=Password: 

set DJANGO_SUPERUSER_USERNAME=%ADMIN_USER%
set DJANGO_SUPERUSER_PASSWORD=%ADMIN_PASS%
myenv\Scripts\python manage.py create_superuser
echo.

:: Collect static files
myenv\Scripts\python manage.py collectstatic --no-input --quiet

echo.
echo ============================================
echo   Setup Complete!
echo ============================================
echo.
echo To start GymApp, double-click "Start GymApp.bat" on your desktop.
echo.
echo Your login credentials:
echo   Username: %ADMIN_USER%
echo   Password: (the one you just entered)
echo.
pause
