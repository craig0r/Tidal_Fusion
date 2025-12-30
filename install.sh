#!/bin/bash
set -e

# Repository configuration
GITHUB_REPO="craig0r/Tidal_Fusion"

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     ASSET_NAME="tidal_fusion_linux";;
    Darwin*)    ASSET_NAME="tidal_fusion_macos";;
    *)          echo "Unsupported OS: ${OS}"; exit 1;;
esac

echo "--- Tidal Fusion Installer ---"
echo "Fetching latest release from: $GITHUB_REPO"
echo "Platform: $OS"

# Download
DOWNLOAD_URL="https://github.com/${GITHUB_REPO}/releases/latest/download/${ASSET_NAME}"
echo "Downloading $ASSET_NAME..."
if command -v curl >/dev/null 2>&1; then
    curl -L -f -o tidal_fusion "$DOWNLOAD_URL"
elif command -v wget >/dev/null 2>&1; then
    wget -O tidal_fusion "$DOWNLOAD_URL"
else
    echo "Error: Neither curl nor wget found."
    exit 1
fi

chmod +x tidal_fusion

# Install
echo "Installing to /usr/local/bin..."
if [ -w "/usr/local/bin" ]; then
    mv tidal_fusion /usr/local/bin/tidal_fusion
else
    sudo mv tidal_fusion /usr/local/bin/tidal_fusion
fi

# Log Directory setup
echo "Configuring /var/log/tidal_fusion..."
if [ ! -d "/var/log/tidal_fusion" ]; then
    sudo mkdir -p /var/log/tidal_fusion
fi

# Determine Group (users vs staff vs current)
GROUP="users"
if ! getent group "$GROUP" >/dev/null 2>&1 && ! dscl . -list /Groups "$GROUP" >/dev/null 2>&1; then
    GROUP="staff"
    if ! getent group "$GROUP" >/dev/null 2>&1 && ! dscl . -list /Groups "$GROUP" >/dev/null 2>&1; then
        GROUP=$(id -gn)
    fi
fi

echo "Setting log directory permissions (Group: $GROUP)..."
sudo chown root:$GROUP /var/log/tidal_fusion
sudo chmod 775 /var/log/tidal_fusion

echo "--- Installation Complete ---"
echo "Start by running: tidal_fusion"
