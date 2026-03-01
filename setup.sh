#!/bin/bash
# Weather Display - Raspberry Pi install script
#
# On the Pi, run:
#   wget https://raw.githubusercontent.com/tunny682/Weather-Display/master/setup.sh
#   bash setup.sh
#   sudo reboot
#
# Or if you already cloned the repo:  cd weather-display && bash setup.sh

set -e
REPO_URL="https://github.com/tunny682/Weather-Display.git"
INSTALL_DIR="${HOME}/weather-display"

echo "=== Weather Display installer (Raspberry Pi) ==="

# If we're not already inside the repo, clone it
if [ ! -f "src/main.py" ] && [ ! -f "config.json.example" ]; then
    echo "Cloning repository to ${INSTALL_DIR}..."
    if ! command -v git &>/dev/null; then
        echo "Installing git..."
        sudo apt-get update -qq
        sudo apt-get install -y -qq git
    fi
    rm -rf "${INSTALL_DIR}"
    git clone "${REPO_URL}" "${INSTALL_DIR}"
    cd "${INSTALL_DIR}"
else
    echo "Using existing repo at $(pwd)"
    INSTALL_DIR="$(pwd)"
    cd "${INSTALL_DIR}"
fi

# Resolve absolute path for systemd (Raspberry Pi)
if command -v realpath &>/dev/null; then
    INSTALL_DIR="$(realpath "${INSTALL_DIR}")"
elif [ -z "${INSTALL_DIR%%/*}" ]; then
    : # already absolute
else
    INSTALL_DIR="$(pwd)"
fi

# Install system dependencies (Python 3, venv, pip, SDL for PyGame)
echo "Installing system dependencies..."
if command -v apt-get &>/dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3 python3-pip python3-venv python3-tk git
    sudo apt-get install -y -qq libsdl2-2.0-0 libsdl2-image-2.0-0 libsdl2-mixer-2.0-0 libsdl2-ttf-2.0-0 || true
fi

# Create virtualenv and install Python dependencies
echo "Creating virtual environment and installing Python packages..."
python3 -m venv .venv
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt -q

# Create config from example if missing, then run interactive setup (location, 12/24h)
if [ ! -f config.json ]; then
    cp config.json.example config.json
fi
echo ""
echo "--- Set your location and preferences ---"
.venv/bin/python src/main.py --setup-only

# Auto-start: systemd (Bookworm/X11) and/or labwc autostart (Trixie/Wayland)
SERVICE_DIR="${HOME}/.config/systemd/user"
mkdir -p "${SERVICE_DIR}"
cat > "${SERVICE_DIR}/weather-display.service" << EOF
[Unit]
Description=Weather Display (8.8" LCD)
After=graphical-session.target

[Service]
Type=simple
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/.venv/bin/python src/main.py
Environment=DISPLAY=:0
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
EOF

echo "Enabling auto-start (systemd user service for Bookworm/X11)..."
systemctl --user daemon-reload
systemctl --user enable weather-display.service 2>/dev/null || true

# Trixie (Debian 13) / Raspberry Pi OS with Wayland uses labwc; add autostart so app runs in session
LABWC_AUTOSTART="${HOME}/.config/labwc/autostart"
if command -v labwc &>/dev/null || [ -d "${HOME}/.config/labwc" ]; then
    echo "Configuring labwc autostart (Trixie/Wayland)..."
    mkdir -p "${LABWC_AUTOSTART}"
    cat > "${LABWC_AUTOSTART}/weather-display.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Weather Display
Exec=${INSTALL_DIR}/.venv/bin/python ${INSTALL_DIR}/src/main.py
Path=${INSTALL_DIR}
X-GNOME-Autostart-enabled=true
EOF
    chmod +x "${LABWC_AUTOSTART}/weather-display.desktop" 2>/dev/null || true
fi

echo ""
echo "=== Installation complete ==="
echo "  Install directory: ${INSTALL_DIR}"
echo "  Run manually:  cd ${INSTALL_DIR} && .venv/bin/python src/main.py"
echo "  (Bookworm) Start service: systemctl --user start weather-display"
echo "  Reboot to start the display automatically:  sudo reboot"
echo ""
