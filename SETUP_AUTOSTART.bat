@echo off
title SmartPOS - Auto Start Setup
color 0A
cls

echo.
echo  ============================================
echo   SmartPOS - Setup Auto Start on Windows Boot
echo  ============================================
echo.

:: Check admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo  [!] Please right-click and "Run as Administrator"
    pause
    exit /b 1
)

set "INSTALL_DIR=%~dp0"
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "TASK_NAME=SmartPOS AutoStart"

echo  Choose auto-start method:
echo.
echo  [1] Windows Startup Folder (Simple - starts when user logs in)
echo  [2] Windows Task Scheduler (Better - starts even before login)
echo.
set /p CHOICE="  Enter 1 or 2: "

if "%CHOICE%"=="1" goto STARTUP_FOLDER
if "%CHOICE%"=="2" goto TASK_SCHEDULER
goto STARTUP_FOLDER

:STARTUP_FOLDER
echo.
echo  [*] Adding SmartPOS to Windows Startup...

:: Create a VBS launcher (runs silently without black window)
echo Set WshShell = CreateObject("WScript.Shell") > "%TEMP%\smartpos_launcher.vbs"
echo WshShell.CurrentDirectory = "%INSTALL_DIR%" >> "%TEMP%\smartpos_launcher.vbs"
echo WshShell.Run "cmd /c cd /d ""%INSTALL_DIR%"" && python manage.py runserver 127.0.0.1:8000", 0, False >> "%TEMP%\smartpos_launcher.vbs"

:: Copy launcher to startup folder
copy "%TEMP%\smartpos_launcher.vbs" "%STARTUP_DIR%\SmartPOS.vbs" >nul

:: Also create desktop shortcut to open browser
powershell -Command "& {
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut([System.Environment]::GetFolderPath('Desktop') + '\Open SmartPOS.lnk')
    $Shortcut.TargetPath = 'http://127.0.0.1:8000'
    $Shortcut.Description = 'Open SmartPOS in Browser'
    $Shortcut.Save()
}" >nul 2>&1

echo  [OK] SmartPOS will now start automatically when Windows starts!
echo.
echo  ============================================
echo   Setup Complete!
echo  ============================================
echo.
echo   - SmartPOS starts automatically on boot
echo   - No black window will appear
echo   - Double-click "Open SmartPOS" on Desktop
echo     to open it in browser anytime
echo.
echo   To REMOVE auto-start later, delete this file:
echo   %STARTUP_DIR%\SmartPOS.vbs
echo.
goto DONE

:TASK_SCHEDULER
echo.
echo  [*] Creating Windows Task Scheduler entry...

:: Create XML for task scheduler
echo ^<?xml version="1.0" encoding="UTF-16"?^> > "%TEMP%\smartpos_task.xml"
echo ^<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task"^> >> "%TEMP%\smartpos_task.xml"
echo   ^<Triggers^> >> "%TEMP%\smartpos_task.xml"
echo     ^<BootTrigger^> >> "%TEMP%\smartpos_task.xml"
echo       ^<Enabled^>true^</Enabled^> >> "%TEMP%\smartpos_task.xml"
echo       ^<Delay^>PT10S^</Delay^> >> "%TEMP%\smartpos_task.xml"
echo     ^</BootTrigger^> >> "%TEMP%\smartpos_task.xml"
echo   ^</Triggers^> >> "%TEMP%\smartpos_task.xml"
echo   ^<Principals^> >> "%TEMP%\smartpos_task.xml"
echo     ^<Principal^> >> "%TEMP%\smartpos_task.xml"
echo       ^<RunLevel^>HighestAvailable^</RunLevel^> >> "%TEMP%\smartpos_task.xml"
echo     ^</Principal^> >> "%TEMP%\smartpos_task.xml"
echo   ^</Principals^> >> "%TEMP%\smartpos_task.xml"
echo   ^<Settings^> >> "%TEMP%\smartpos_task.xml"
echo     ^<MultipleInstancesPolicy^>IgnoreNew^</MultipleInstancesPolicy^> >> "%TEMP%\smartpos_task.xml"
echo     ^<DisallowStartIfOnBatteries^>false^</DisallowStartIfOnBatteries^> >> "%TEMP%\smartpos_task.xml"
echo     ^<StopIfGoingOnBatteries^>false^</StopIfGoingOnBatteries^> >> "%TEMP%\smartpos_task.xml"
echo     ^<ExecutionTimeLimit^>PT0S^</ExecutionTimeLimit^> >> "%TEMP%\smartpos_task.xml"
echo     ^<RestartOnFailure^> >> "%TEMP%\smartpos_task.xml"
echo       ^<Interval^>PT1M^</Interval^> >> "%TEMP%\smartpos_task.xml"
echo       ^<Count^>3^</Count^> >> "%TEMP%\smartpos_task.xml"
echo     ^</RestartOnFailure^> >> "%TEMP%\smartpos_task.xml"
echo   ^</Settings^> >> "%TEMP%\smartpos_task.xml"
echo   ^<Actions^> >> "%TEMP%\smartpos_task.xml"
echo     ^<Exec^> >> "%TEMP%\smartpos_task.xml"
echo       ^<Command^>python^</Command^> >> "%TEMP%\smartpos_task.xml"
echo       ^<Arguments^>manage.py runserver 127.0.0.1:8000^</Arguments^> >> "%TEMP%\smartpos_task.xml"
echo       ^<WorkingDirectory^>%INSTALL_DIR%^</WorkingDirectory^> >> "%TEMP%\smartpos_task.xml"
echo     ^</Exec^> >> "%TEMP%\smartpos_task.xml"
echo   ^</Actions^> >> "%TEMP%\smartpos_task.xml"
echo ^</Task^> >> "%TEMP%\smartpos_task.xml"

:: Register the task
schtasks /create /tn "%TASK_NAME%" /xml "%TEMP%\smartpos_task.xml" /f >nul 2>&1

if %errorLevel% == 0 (
    echo  [OK] Task Scheduler entry created!
) else (
    echo  [!] Task Scheduler failed. Using Startup Folder instead...
    goto STARTUP_FOLDER
)

:: Desktop shortcut to open browser
powershell -Command "& {
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut([System.Environment]::GetFolderPath('Desktop') + '\Open SmartPOS.lnk')
    $Shortcut.TargetPath = 'http://127.0.0.1:8000'
    $Shortcut.Description = 'Open SmartPOS in Browser'
    $Shortcut.Save()
}" >nul 2>&1

echo.
echo  ============================================
echo   Setup Complete!
echo  ============================================
echo.
echo   - SmartPOS starts automatically on every boot
echo   - Starts 10 seconds after Windows loads
echo   - Restarts automatically if it ever crashes
echo   - Double-click "Open SmartPOS" on Desktop
echo.
echo   To REMOVE auto-start later, run:
echo   schtasks /delete /tn "SmartPOS AutoStart" /f
echo.

:DONE
echo  Starting SmartPOS now to test...
echo.
timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:8000"

:: Start server in background now too
start /min "" python manage.py runserver 127.0.0.1:8000

pause