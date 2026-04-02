@echo off
title SmartPOS - Network Mode
color 0B
cls

echo.
echo  ============================================
echo   SmartPOS - Network Mode (All Devices)
echo  ============================================
echo.

cd /d "%~dp0"

:: Get IP address
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| find "IPv4"') do (
    set IP=%%a
    goto FOUND_IP
)
:FOUND_IP
set IP=%IP: =%

echo  [*] Starting SmartPOS in network mode...
echo.
echo  ============================================
echo   Access SmartPOS from any device on WiFi:
echo.
echo   This PC:        http://127.0.0.1:8000
echo   Other devices:  http://%IP%:8000
echo  ============================================
echo.
echo   Keep this window open while using SmartPOS.
echo.

python manage.py runserver 0.0.0.0:8000