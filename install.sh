#!/bin/bash

# Tidal Fusion Installer (Linux/Mac)
# Installs dependencies and builds the binary.

set -e

APP_NAME="tidal-fusion"
SRC_FILE="tidal_fusion.py"
REQUIREMENTS="requirements.txt"
INSTALL_DIR="/usr/local/bin"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Tidal Fusion Installer ===${NC}"

# 0. Prevent running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}Error: Please do not run this script as root/sudo.${NC}"
    echo "Run as a normal user. You will be prompted for your password during the final install step."
    exit 1
fi

# 1. Clean previous builds (Aggressive Clean)
echo "Cleaning previous build artifacts..."
rm -rf build dist "$APP_NAME.spec" __pycache__

# 2. Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed or not found in PATH.${NC}"
    echo "Please install Python 3 and try again."
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found${NC}"

# 3. Setup/Check venv & Dependencies
echo -e "${BLUE}Checking dependencies...${NC}"

# Check for PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    # Install to user location to avoid root requirement
    pip3 install --user --upgrade pyinstaller || { echo -e "${RED}Failed to install pyinstaller.${NC}"; exit 1; }
    
    # Ensure local bin is in path for this session if needed
    FULL_PATH="$(python3 -m site --user-base)/bin"
    export PATH="$PATH:$FULL_PATH"
fi

# Check for Requirements
if [ -f "$REQUIREMENTS" ]; then
    echo "Installing/Updating requirements..."
    pip3 install --user --upgrade -r "$REQUIREMENTS" || { echo -e "${RED}Failed to install requirements.${NC}"; exit 1; }
else
    echo -e "${RED}Warning: $REQUIREMENTS not found in $(pwd).${NC}"
fi

# 4. Build
echo -e "${BLUE}Building executable...${NC}"
# Use python -m PyInstaller to be safe about path
python3 -m PyInstaller --clean --onefile --name "$APP_NAME" "$SRC_FILE"

# 5. Install
echo -e "${BLUE}Installing to $INSTALL_DIR...${NC}"
echo "You may be prompted for your password to copy the binary."

if sudo cp "dist/$APP_NAME" "$INSTALL_DIR/"; then
    sudo chmod +x "$INSTALL_DIR/$APP_NAME"
    
    # 6. Cleanup
    echo "Cleaning up build artifacts..."
    rm -rf build dist "$APP_NAME.spec"

    echo -e "${GREEN}=== Installation Complete ===${NC}"
    echo -e "Binary installed at: ${GREEN}${INSTALL_DIR}/${APP_NAME}${NC}"
    echo "You can run the app with: $APP_NAME --help"
else
    echo -e "${RED}Installation failed (Current user ($USER) cannot write to $INSTALL_DIR).${NC}"
    echo "The executable is available in: dist/$APP_NAME"
    exit 1
fi
