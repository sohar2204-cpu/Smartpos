@echo off
title SmartPOS - Starting...
color 0A
cls

echo.
echo  ============================================
echo      SmartPOS - Smart Retail POS System
echo  ============================================
echo.

cd /d "%~dp0"

:: Check if already running
netstat -an 2>nul | find "8000" | find "LISTENING" >nul
if %errorLevel% == 0 (
    echo  [OK] SmartPOS is already running!
    echo  [*] Opening browser...
    timeout /t 1 /nobreak >nul
    start "" "http://127.0.0.1:8000"
    exit /b 0
)

echo  [*] Starting SmartPOS server...
echo.

:: Start Django in background
start /min "SmartPOS Server" python manage.py runserver 127.0.0.1:8000

:: Wait for server to start
echo  [*] Waiting for server to start...
timeout /t 3 /nobreak >nul

:: Try to open browser (retry a few times)
set RETRIES=0
:RETRY
netstat -an 2>nul | find "8000" | find "LISTENING" >nul
if %errorLevel% == 0 (
    echo  [OK] Server is running!
    echo  [*] Opening SmartPOS in browser...
    start "" "http://127.0.0.1:8000"
    goto DONE
)
set /a RETRIES+=1
if %RETRIES% lss 5 (
    timeout /t 2 /nobreak >nul
    goto RETRY
)

echo  [!] Server took longer than expected.
echo  [*] Opening browser anyway...
start "" "http://127.0.0.1:8000"

:DONE
echo.
echo  ============================================
echo   SmartPOS is running at:
echo   http://127.0.0.1:8000
echo  ============================================
echo.
echo   Keep this window open while using SmartPOS.
echo   Close this window to shut down SmartPOS.
echo.
echo   Press Ctrl+C or close this window to stop.
echo  ============================================
echo.

:: Keep window open and show server output
python manage.py runserver 127.0.0.1:8000