# Installation Guide

## Prerequisites
- **Python 3.8+**: Ensure Python is installed and added to your system PATH.
    - [Download Python](https://www.python.org/downloads/)
- **Tidal Account**: A valid subscription is required.

## Automated Installation (Recommended)
The installer scripts will attempt to install dependencies (including `tidalapi` and `pyinstaller`) and build the binary.

### Linux / macOS
1. Open a terminal in the project directory.
2. Run the install script:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
   - **Root/Sudo**: Installs to `/usr/local/bin`.
   - **User**: Installs to `~/.local/bin` (Ensure this is in your PATH).

### Windows
1. Double-click `install.bat`.
   - **Admin**: Installs to `%ProgramFiles%\TidalFusion`.
   - **User**: Installs to `%LocalAppData%\Programs\TidalFusion`.
2. Follow the on-screen prompt to add the installation folder to your `PATH` if necessary.

## Manual Installation
If the scripts fail, you can build manually:

1. **Install Requirements**:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```
2. **Build**:
   ```bash
   pyinstaller --onefile --name tidal-fusion tidal_fusion.py
   ```
3. **Install**:
   - Copy the generated file from `dist/` to your preferred location (e.g., `/usr/local/bin` or a folder in your PATH).
