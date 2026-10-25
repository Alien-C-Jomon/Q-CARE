@echo off
title Q-Care Launcher
color 0F

echo ========================================
echo          Q-CARE V8 LAUNCHER
echo ========================================
echo.
echo [1/3] Starting Q-Care backend...

start "Q-Care Backend" cmd /k "cd /d "%~dp0backend" && call qcare-env\Scripts\activate.bat && python app.py"

echo [2/3] Waiting for Flask to initialize...
timeout /t 4 /nobreak >nul

echo [3/3] Opening Q-Care frontend...
start "" "%~dp0frontend\index.html"

echo.
echo Q-Care launch commands completed.
echo Keep the backend window open while using Q-Care.
echo.
timeout /t 3 /nobreak >nul
exit