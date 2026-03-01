#!/bin/bash
# Weather Display - Raspberry Pi install script
#
# On the Pi, run one of:
#   git clone https://github.com/tunny682/Weather-Display.git && cd Weather-Display && bash setup.sh
#   (recommended; avoids 404 if the raw file URL fails)
#
# Or:  wget .../setup.sh && bash setup.sh  (use your repo's raw URL; branch may be main or master)
#
# Then:  sudo reboot

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

# XDG Autostart: run when user logs into the desktop (works with autologin on Pi)
# Supported by LXDE (Bookworm), labwc (Trixie), and most desktop environments
AUTOSTART_DIR="${HOME}/.config/autostart"
mkdir -p "${AUTOSTART_DIR}"
cat > "${AUTOSTART_DIR}/weather-display.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Weather Display
Comment=Weather and time display for 8.8" LCD
Exec=${INSTALL_DIR}/.venv/bin/python ${INSTALL_DIR}/src/main.py
Path=${INSTALL_DIR}
X-GNOME-Autostart-enabled=true
EOF
echo "Configured desktop autostart (runs when you log in)."

# Optional: systemd user service (backup; enable linger so it can run at boot)
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
systemctl --user daemon-reload 2>/dev/null || true
systemctl --user enable weather-display.service 2>/dev/null || true

# Enable linger so user session (and user services) persist at boot (helps some setups)
if command -v loginctl &>/dev/null; then
    loginctl enable-linger "${USER}" 2>/dev/null || true
fi

# Enable desktop autologin so the Pi boots straight to desktop with no login (no keyboard needed)
LIGHTDM_CONF="/etc/lightdm/lightdm.conf"
if [ -f "${LIGHTDM_CONF}" ]; then
    if ! grep -q "^autologin-user=" "${LIGHTDM_CONF}" 2>/dev/null; then
        echo "Enabling desktop autologin for user ${USER} (no keyboard needed at boot)..."
        if sudo grep -q "^\[Seat:" "${LIGHTDM_CONF}" 2>/dev/null; then
            sudo sed -i "/^\[Seat:/a autologin-user=${USER}\nautologin-user-timeout=0" "${LIGHTDM_CONF}" 2>/dev/null || true
        fi
    else
        sudo sed -i "s/^autologin-user=.*/autologin-user=${USER}/" "${LIGHTDM_CONF}" 2>/dev/null || true
        sudo sed -i "s/^#*autologin-user-timeout=.*/autologin-user-timeout=0/" "${LIGHTDM_CONF}" 2>/dev/null || true
    fi
else
    echo "To boot without a login screen, enable autologin: sudo raspi-config → System Options → Boot / Auto Login → Desktop Autologin"
fi

# Force fullscreen and 1920x480 in config for LCD
if [ -f "${INSTALL_DIR}/config.json" ]; then
    sed -i 's/"fullscreen"\s*:\s*false/"fullscreen": true/' "${INSTALL_DIR}/config.json" 2>/dev/null || true
    sed -i 's/"width"\s*:\s*[0-9]*/"width": 1920/' "${INSTALL_DIR}/config.json" 2>/dev/null || true
    sed -i 's/"height"\s*:\s*[0-9]*/"height": 480/' "${INSTALL_DIR}/config.json" 2>/dev/null || true
fi

# Set Pi display output to 1920x480 for the 8.8" LCD (desktop and app will use this)
BOOT_CONF=""
[ -f /boot/firmware/config.txt ] && BOOT_CONF="/boot/firmware/config.txt"
[ -z "${BOOT_CONF}" ] && [ -f /boot/config.txt ] && BOOT_CONF="/boot/config.txt"
if [ -n "${BOOT_CONF}" ]; then
    if ! sudo grep -q "hdmi_cvt=1920 480" "${BOOT_CONF}" 2>/dev/null; then
        echo "Setting display resolution to 1920x480 for LCD..."
        { echo ""; echo "# Weather Display 8.8\" LCD (1920x480)"; echo "hdmi_cvt=1920 480 60 6 0 0 0"; echo "hdmi_group=2"; echo "hdmi_mode=87"; } | sudo tee -a "${BOOT_CONF}" >/dev/null
    fi
else
    echo "To use the LCD at 1920x480, add to /boot/firmware/config.txt (or /boot/config.txt):"
    echo "  hdmi_cvt=1920 480 60 6 0 0 0"
    echo "  hdmi_group=2"
    echo "  hdmi_mode=87"
fi

# Trixie / labwc: also add to labwc autostart if present
LABWC_AUTOSTART="${HOME}/.config/labwc/autostart"
if [ -d "${HOME}/.config/labwc" ]; then
    mkdir -p "${LABWC_AUTOSTART}"
    cp "${AUTOSTART_DIR}/weather-display.desktop" "${LABWC_AUTOSTART}/" 2>/dev/null || true
fi

echo ""
echo "=== Installation complete ==="
echo "  Install directory: ${INSTALL_DIR}"
echo "  Autologin + autostart: Pi will boot to desktop and start the app with no keyboard."
echo "  Run manually:  cd ${INSTALL_DIR} && .venv/bin/python src/main.py"
echo "  Reboot once:  sudo reboot"
echo ""
