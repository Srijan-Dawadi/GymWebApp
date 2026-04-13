@echo off
title GymApp
color 0A

:: Get the directory where this bat file lives
set APP_DIR=%~dp0

:: Move to app directory
cd /d "%APP_DIR%"

echo ============================================
echo   GymApp - Starting...
echo ============================================
echo.

:: Pull latest updates from GitHub silently
echo Checking for updates...
git pull --quiet 2>nul
if errorlevel 1 (
    echo [!] Could not check for updates (no internet or git issue). Continuing...
) else (
    echo [OK] App is up to date.
)
echo.

:: Run any new migrations silently
myenv\Scripts\python manage.py migrate --run-syncdb --no-input >nul 2>&1

:: Collect static files silently
myenv\Scripts\python manage.py collectstatic --no-input --quiet >nul 2>&1

:: Open browser after a short delay
echo Opening GymApp in browser...
timeout /t 2 /nobreak >nul
start "" "http://localhost:8000"

:: Start the server (this window stays open while app is running)
echo.
echo ============================================
echo   GymApp is running!
echo   Open your browser at: http://localhost:8000
echo.
echo   DO NOT close this window while using the app.
echo   To stop the app, close this window.
echo ============================================
echo.
myenv\Scripts\python manage.py runserver 127.0.0.1:8000

:: If server stops for any reason
echo.
echo GymApp has stopped.
pause
