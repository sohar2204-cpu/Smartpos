@echo off
title SmartPOS - Stop
color 0C
cls

echo.
echo  ============================================
echo      SmartPOS - Stopping Server
echo  ============================================
echo.

echo  [*] Stopping SmartPOS...

:: Kill python processes running on port 8000
for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| find "8000" ^| find "LISTENING"') do (
    echo  [*] Stopping process %%p...
    taskkill /PID %%p /F >nul 2>&1
)

:: Also kill any django/python processes
taskkill /F /IM python.exe >nul 2>&1

echo  [OK] SmartPOS stopped.
echo.
timeout /t 2 /nobreak >nul