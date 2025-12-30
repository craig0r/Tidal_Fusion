@echo off
setlocal

set "GITHUB_REPO=craig0r/Tidal_Fusion"
set "ASSET_NAME=tidal_fusion_windows.exe"
set "URL=https://github.com/%GITHUB_REPO%/releases/latest/download/%ASSET_NAME%"

echo --- Tidal Fusion Installer ---
echo Fetching latest release from: %GITHUB_REPO%

REM Download using PowerShell
echo Downloading %ASSET_NAME%...
powershell -Command "try { Invoke-WebRequest -Uri '%URL%' -OutFile 'tidal_fusion.exe' -ErrorAction Stop } catch { exit 1 }"

if errorlevel 1 (
    echo.
    echo Error: Failed to download release. 
    echo Please ensure the release exists at: %URL%
    pause
    exit /b 1
)

if not exist tidal_fusion.exe (
    echo Error: Download file missing.
    pause
    exit /b 1
)

REM Install
set "INSTALL_DIR=%LocalAppData%\Programs\TidalFusion"
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo Installing to %INSTALL_DIR%...
move /Y tidal_fusion.exe "%INSTALL_DIR%\tidal_fusion.exe"

REM Log Directory
set "LOG_DIR=%ProgramData%\TidalFusion"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo Configuring Log Directory (%LOG_DIR%)...
icacls "%LOG_DIR%" /grant Users:(OI)(CI)M /T >nul 2>&1

echo.
echo --- Installation Complete ---
echo Executable is in: %INSTALL_DIR%\tidal_fusion.exe
echo Please ensure this folder is in your PATH.
echo.
pause
