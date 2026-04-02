@echo off
title SmartPOS - Remove Auto Start
color 0C
cls

echo.
echo  ============================================
echo   SmartPOS - Remove Auto Start
echo  ============================================
echo.

:: Remove from startup folder
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
if exist "%STARTUP_DIR%\SmartPOS.vbs" (
    del "%STARTUP_DIR%\SmartPOS.vbs" >nul
    echo  [OK] Removed from Windows Startup folder
)

:: Remove from task scheduler
schtasks /delete /tn "SmartPOS AutoStart" /f >nul 2>&1
if %errorLevel% == 0 (
    echo  [OK] Removed from Task Scheduler
)

:: Stop running server
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| find "8000" ^| find "LISTENING"') do (
    taskkill /PID %%p /F >nul 2>&1
)

echo.
echo  [OK] SmartPOS auto-start has been removed.
echo  SmartPOS will no longer start automatically.
echo.
pause