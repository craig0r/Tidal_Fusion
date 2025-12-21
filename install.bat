@echo off
setlocal
title Tidal Fusion Installer

echo === Tidal Fusion Installer ===

REM 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found. Please install Python 3.
    pause
    exit /b 1
)
echo [OK] Python found.

REM 2. Install Dependencies
echo [INFO] Installing/Updating dependencies...
pip install --upgrade -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

echo [INFO] Installing/Updating PyInstaller...
pip install --upgrade pyinstaller
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install PyInstaller.
    pause
    exit /b 1
)

REM 3. Build
echo [INFO] Building executable...
pyinstaller --clean --onefile --name "tidal-fusion" "tidal_fusion.py"
if %errorlevel% neq 0 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

REM 4. Install Location
REM Check if running as Admin (simple check)
net session >nul 2>&1
if %errorlevel% == 0 (
    echo [INFO] Running as Admin.
    set "INSTALL_DIR=%ProgramFiles%\TidalFusion"
) else (
    echo [INFO] Running as User.
    set "INSTALL_DIR=%LocalAppData%\Programs\TidalFusion"
)

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo [INFO] Installing to %INSTALL_DIR%...
copy /Y "dist\tidal-fusion.exe" "%INSTALL_DIR%\"

REM 5. Cleanup
echo [INFO] Cleaning up...
rmdir /s /q build dist 2>nul
del tidal-fusion.spec 2>nul

echo.
echo === Installation Complete ===
echo Binary installed at: %INSTALL_DIR%\tidal-fusion.exe
echo.
echo NOTE: Please add "%INSTALL_DIR%" to your PATH manually if you want to run it from anywhere.
pause
