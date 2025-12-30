@echo off
setlocal
echo --- Tidal Fusion Build & Install ---

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Please install Python 3.10+.
    pause
    exit /b 1
)

REM 1. Setup Virtual Environment
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate.bat

REM 2. Install Dependencies
echo Installing dependencies...
pip install --upgrade pip >nul
pip install -r requirements.txt >nul
pip install pyinstaller >nul

REM 3. Build
echo Building binary...
pyinstaller --onefile --name tidal_fusion tidal_fusion.py

REM 4. Install
REM Using LocalAppData for user-level install without Admin
set "INSTALL_DIR=%LocalAppData%\Programs\TidalFusion"
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo Installing to %INSTALL_DIR%...
move /Y dist\tidal_fusion.exe "%INSTALL_DIR%\tidal_fusion.exe"

REM 5. Create Log Directory
set "LOG_DIR=%ProgramData%\TidalFusion"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM Grant 'Users' group modify access
echo Setting permissions on %LOG_DIR%...
icacls "%LOG_DIR%" /grant Users:(OI)(CI)M /T >nul 2>&1

echo.
echo --- Installation Complete ---
echo Executable installed to: %INSTALL_DIR%\tidal_fusion.exe
echo Please ensure this folder is in your PATH.
echo.
pause
