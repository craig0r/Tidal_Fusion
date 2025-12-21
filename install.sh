#!/bin/bash

# Tidal Fusion Installer (Linux/Mac)
# Installs dependencies and builds the binary.

set -e

APP_NAME="tidal-fusion"
SRC_FILE="tidal_fusion.py"
REQUIREMENTS="requirements.txt"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Tidal Fusion Installer ===${NC}"

# 1. Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed or not found in PATH.${NC}"
    echo "Please install Python 3 and try again."
    exit 1
fi
echo -e "${GREEN}✓ Python 3 found${NC}"

# 2. Setup/Check venv & Dependencies
echo -e "${BLUE}Checking dependencies...${NC}"

# Try to install pyinstaller and requirements if missing
# If running as typical user, might need --user if not in a venv
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Attempting install..."
    pip3 install --user pyinstaller || { echo -e "${RED}Failed to install pyinstaller.${NC}"; exit 1; }
fi

if [ -f "$REQUIREMENTS" ]; then
    echo "Installing requirements..."
    pip3 install --user -r "$REQUIREMENTS" || { echo -e "${RED}Failed to install requirements.${NC}"; exit 1; }
else
    echo -e "${RED}Warning: $REQUIREMENTS not found.${NC}"
fi

# 3. Determine Install Location
if [ "$EUID" -eq 0 ]; then
    INSTALL_DIR="/usr/local/bin"
    echo -e "${BLUE}Running as root. Installing to: ${INSTALL_DIR}${NC}"
else
    INSTALL_DIR="$HOME/.local/bin"
    echo -e "${BLUE}Running as user. Installing to: ${INSTALL_DIR}${NC}"
    # Ensure dir exists
    mkdir -p "$INSTALL_DIR"
    
    # Check if in PATH
    case ":$PATH:" in
        *":$INSTALL_DIR:"*) ;;
        *) echo -e "${RED}Warning: $INSTALL_DIR is not in your PATH.${NC}";;
    esac
fi

# 4. Build
echo -e "${BLUE}Building executable...${NC}"
pyinstaller --clean --onefile --name "$APP_NAME" "$SRC_FILE"

# 5. Install
echo -e "${BLUE}Installing to $INSTALL_DIR...${NC}"
cp "dist/$APP_NAME" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/$APP_NAME"

# 6. Cleanup
echo "Cleaning up build artifacts..."
rm -rf build dist "$APP_NAME.spec"

echo -e "${GREEN}=== Installation Complete ===${NC}"
echo -e "Binary installed at: ${GREEN}${INSTALL_DIR}/${APP_NAME}${NC}"
echo "You can run the app with: $APP_NAME --help"
