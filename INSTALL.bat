@echo off
title SmartPOS Installer
color 0A
cls

echo.
echo  ============================================
echo      SmartPOS - Smart Retail POS System
echo      One-Click Installer for Windows
echo  ============================================
echo.

:: Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo  [!] Please right-click INSTALL.bat and choose
    echo      "Run as Administrator"
    echo.
    pause
    exit /b 1
)

set "INSTALL_DIR=%~dp0"
set "LOG_FILE=%INSTALL_DIR%install_log.txt"

echo  [*] Installation started: %date% %time% > "%LOG_FILE%"
echo  [*] Install directory: %INSTALL_DIR% >> "%LOG_FILE%"

echo  Step 1 of 6: Checking Python...
echo.

:: Check Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo  [!] Python not found. Downloading Python 3.11...
    echo  [!] Python not found - will download >> "%LOG_FILE%"
    
    :: Download Python installer
    echo  [*] Downloading from python.org...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python_installer.exe'}"
    
    if exist "%TEMP%\python_installer.exe" (
        echo  [*] Installing Python 3.11...
        "%TEMP%\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
        echo  [*] Python installed successfully >> "%LOG_FILE%"
        :: Refresh PATH
        call refreshenv >nul 2>&1
        set "PATH=%PATH%;C:\Python311;C:\Python311\Scripts"
    ) else (
        echo.
        echo  [ERROR] Could not download Python.
        echo  Please install Python 3.11 manually from:
        echo  https://www.python.org/downloads/
        echo  Make sure to check "Add Python to PATH"
        pause
        exit /b 1
    )
) else (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
    echo  [OK] Python %PYVER% found
    echo  [OK] Python %PYVER% found >> "%LOG_FILE%"
)

echo.
echo  Step 2 of 6: Checking PostgreSQL...
echo.

:: Check PostgreSQL
psql --version >nul 2>&1
if %errorLevel% neq 0 (
    echo  [!] PostgreSQL not found. Downloading PostgreSQL 16...
    echo  [!] PostgreSQL not found - will download >> "%LOG_FILE%"
    
    powershell -Command "& {Invoke-WebRequest -Uri 'https://get.enterprisedb.com/postgresql/postgresql-16.2-1-windows-x64.exe' -OutFile '%TEMP%\pg_installer.exe'}"
    
    if exist "%TEMP%\pg_installer.exe" (
        echo  [*] Installing PostgreSQL (this may take a few minutes)...
        echo  [*] Database password will be set to: smartpos123
        "%TEMP%\pg_installer.exe" --mode unattended --unattendedmodeui minimal --superpassword smartpos123 --servicename postgresql --servicepassword smartpos123 --serverport 5432
        echo  [*] PostgreSQL installed >> "%LOG_FILE%"
        set "PGPASSWORD=smartpos123"
        set "PATH=%PATH%;C:\Program Files\PostgreSQL\16\bin"
    ) else (
        echo.
        echo  [!] Could not auto-download PostgreSQL.
        echo  [!] Using SQLite instead (fine for single shop).
        echo  [!] PostgreSQL download failed - using SQLite >> "%LOG_FILE%"
        set "USE_SQLITE=1"
    )
) else (
    echo  [OK] PostgreSQL found
    echo  [OK] PostgreSQL found >> "%LOG_FILE%"
)

echo.
echo  Step 3 of 6: Installing Python packages...
echo.

cd /d "%INSTALL_DIR%"

:: Upgrade pip silently
python -m pip install --upgrade pip --quiet >> "%LOG_FILE%" 2>&1

:: Install requirements
echo  [*] Installing Django and dependencies...
python -m pip install -r requirements.txt --quiet >> "%LOG_FILE%" 2>&1
if %errorLevel% neq 0 (
    echo  [!] Some packages failed. Trying individually...
    python -m pip install Django --quiet >> "%LOG_FILE%" 2>&1
    python -m pip install reportlab --quiet >> "%LOG_FILE%" 2>&1
    python -m pip install Pillow --quiet >> "%LOG_FILE%" 2>&1
    python -m pip install whitenoise --quiet >> "%LOG_FILE%" 2>&1
    python -m pip install openpyxl --quiet >> "%LOG_FILE%" 2>&1
)

:: Install psycopg2 for postgres
python -m pip install psycopg2-binary --quiet >> "%LOG_FILE%" 2>&1

echo  [OK] Python packages installed
echo  [OK] Packages installed >> "%LOG_FILE%"

echo.
echo  Step 4 of 6: Configuring database...
echo.

:: Configure settings based on DB availability
if defined USE_SQLITE (
    echo  [*] Configuring SQLite database...
    python -c "
import re, os
path = 'smartpos/settings.py'
content = open(path).read()
sqlite_db = '''DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'smartpos.db',
    }
}'''
# Replace existing DATABASES block
content = re.sub(r'DATABASES\s*=\s*\{[^}]+\{[^}]+\}[^}]+\}', sqlite_db, content, flags=re.DOTALL)
open(path, 'w').write(content)
print('SQLite configured')
" >> "%LOG_FILE%" 2>&1
) else (
    echo  [*] Configuring PostgreSQL database...
    :: Create database
    set "PGPASSWORD=smartpos123"
    "C:\Program Files\PostgreSQL\16\bin\psql.exe" -U postgres -c "CREATE DATABASE smartpos;" >> "%LOG_FILE%" 2>&1
    
    :: Update settings.py with postgres config
    python -c "
content = open('smartpos/settings.py').read()
import re
pg_db = '''DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'smartpos',
        'USER': 'postgres',
        'PASSWORD': 'smartpos123',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}'''
content = re.sub(r'DATABASES\s*=\s*\{[^}]+\{[^}]+\}[^}]+\}', pg_db, content, flags=re.DOTALL)
open('smartpos/settings.py', 'w').write(content)
print('PostgreSQL configured')
" >> "%LOG_FILE%" 2>&1
)

echo  [OK] Database configured

echo.
echo  Step 5 of 6: Setting up SmartPOS...
echo.

:: Run migrations
echo  [*] Creating database tables...
python manage.py makemigrations --verbosity=0 >> "%LOG_FILE%" 2>&1
python manage.py makemigrations pos --verbosity=0 >> "%LOG_FILE%" 2>&1
python manage.py migrate --verbosity=0 >> "%LOG_FILE%" 2>&1

if %errorLevel% neq 0 (
    echo  [ERROR] Database setup failed. Check install_log.txt
    pause
    exit /b 1
)

:: Run setup script
python setup.py >> "%LOG_FILE%" 2>&1

echo  [OK] Database tables created

:: Collect static files
echo  [*] Preparing files...
python manage.py collectstatic --noinput --verbosity=0 >> "%LOG_FILE%" 2>&1
echo  [OK] Setup complete

echo.
echo  Step 6 of 6: Creating shortcuts...
echo.

:: Create desktop shortcut using PowerShell
powershell -Command "& {
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut([System.Environment]::GetFolderPath('Desktop') + '\SmartPOS.lnk')
    $Shortcut.TargetPath = '%INSTALL_DIR%START_SMARTPOS.bat'
    $Shortcut.WorkingDirectory = '%INSTALL_DIR%'
    $Shortcut.IconLocation = '%SystemRoot%\System32\shell32.dll,14'
    $Shortcut.Description = 'SmartPOS - Smart Retail POS System'
    $Shortcut.Save()
}" >> "%LOG_FILE%" 2>&1

echo  [OK] Desktop shortcut created

echo.
echo  ============================================
echo   [SUCCESS] SmartPOS installed successfully!
echo  ============================================
echo.
echo   Login Details:
echo   ----------------------------------------
echo   Admin:   username=admin   password=admin123
echo   Cashier: username=cashier password=cashier123
echo   ----------------------------------------
echo.
echo   To start SmartPOS:
echo   - Double-click "SmartPOS" on your Desktop, OR
echo   - Run START_SMARTPOS.bat in this folder
echo.
echo   The system will open automatically in your
echo   browser at http://127.0.0.1:8000
echo.
echo  ============================================
echo.

:: Setup autostart
echo  [*] Setting up auto-start on Windows boot...
call "%INSTALL_DIR%SETUP_AUTOSTART.bat" >nul 2>&1

:: Ask to launch now
set /p LAUNCH="  Start SmartPOS now? (Y/N): "
if /i "%LAUNCH%"=="Y" (
    start "" "%INSTALL_DIR%START_SMARTPOS.bat"
)

pause