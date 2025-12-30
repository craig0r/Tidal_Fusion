#!/bin/bash
set -e

echo "--- Tidal Fusion Build & Install ---"

# 1. Setup Virtual Environment
if [ -d ".venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf .venv
fi

echo "Creating virtual environment..."
python3 -m venv .venv

# Check if pip exists (Debian/Ubuntu often omit EnsurePip)
if [ ! -f ".venv/bin/pip" ]; then
    echo "Error: pip not found in .venv."
    echo "On Debian/Ubuntu, you may need to run: sudo apt install python3-venv python3-full"
    exit 1
fi

# 2. Install Dependencies
echo "Installing dependencies..."
# Use explicit paths to ensure we are using the venv
./.venv/bin/pip install --upgrade pip > /dev/null
./.venv/bin/pip install -r requirements.txt > /dev/null
./.venv/bin/pip install pyinstaller > /dev/null

# 3. Build
echo "Building binary..."
./.venv/bin/pyinstaller --onefile --name tidal-fusion tidal_fusion.py

# 4. Install
echo "Installing to /usr/local/bin..."
if [ -w "/usr/local/bin" ]; then
    mv dist/tidal-fusion /usr/local/bin/tidal-fusion
else
    sudo mv dist/tidal-fusion /usr/local/bin/tidal-fusion
fi

# 5. Create Log Directory
echo "Configuring /var/log/tidal_fusion..."
if [ ! -d "/var/log/tidal_fusion" ]; then
    sudo mkdir -p /var/log/tidal_fusion
fi

# Set permissions (Try 'users', fallback to 'staff' for macOS, or current group)
# 'id -gn' gets current group name
GROUP="users"
if ! getent group "$GROUP" >/dev/null 2>&1 && ! dscl . -list /Groups "$GROUP" >/dev/null 2>&1; then
    GROUP="staff"
    if ! getent group "$GROUP" >/dev/null 2>&1 && ! dscl . -list /Groups "$GROUP" >/dev/null 2>&1; then
        GROUP=$(id -gn)
    fi
fi

echo "Setting group ownership to '$GROUP'..."
sudo chown root:$GROUP /var/log/tidal_fusion
sudo chmod 775 /var/log/tidal_fusion

echo "--- Installation Complete ---"
echo "Run 'tidal-fusion' to start."
