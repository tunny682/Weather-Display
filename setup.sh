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
    sudo apt-get install -y -qq x11-xserver-utils || true
    sudo apt-get install -y -qq wlr-randr 2>/dev/null || true
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

# Rotation: no user input on the unit — script rotates desktop automatically (default: right, for 8.8" LCD)
[ -f "${INSTALL_DIR}/rotate_display.sh" ] && chmod +x "${INSTALL_DIR}/rotate_display.sh"
if [ -f "${INSTALL_DIR}/rotate_display.sh" ]; then
  # Default rotate.conf so rotation works without any input (display has no keyboard)
  [ ! -f "${INSTALL_DIR}/rotate.conf" ] && echo "ROTATE=right" > "${INSTALL_DIR}/rotate.conf"
  echo "Installing rotate-display service (runs at login, retries until display is ready)..."
  mkdir -p "${HOME}/.config/systemd/user"
  cat > "${HOME}/.config/systemd/user/rotate-display.service" << ROTEOF
[Unit]
Description=Rotate display for 8.8" LCD (no user input; uses rotate.conf or default right)
After=graphical-session.target graphical.target

[Service]
Type=oneshot
Environment=DISPLAY=:0
Environment=XAUTHORITY=%h/.Xauthority
ExecStart=${INSTALL_DIR}/rotate_display.sh
TimeoutSec=120

[Install]
WantedBy=default.target
ROTEOF
  systemctl --user daemon-reload 2>/dev/null || true
  systemctl --user enable rotate-display.service 2>/dev/null || true
fi

# Launcher: hide taskbar (and keep it hidden), rotate display, then start the app
LAUNCHER="${INSTALL_DIR}/start-weather-display.sh"
cat > "${LAUNCHER}" << EOF
#!/bin/sh
export DISPLAY=:0
export XAUTHORITY="\${XAUTHORITY:-\$HOME/.Xauthority}"
# Hide Pi taskbar; kill all lxpanel variants and keep killing in case session restarts it
killall lxpanel 2>/dev/null || true
pkill -f lxpanel 2>/dev/null || true
( while true; do sleep 1; killall lxpanel 2>/dev/null; pkill -f lxpanel 2>/dev/null; done ) &
# Rotate to landscape in background if script exists
[ -x "${INSTALL_DIR}/rotate_display.sh" ] && "${INSTALL_DIR}/rotate_display.sh" >/dev/null 2>&1 &
cd "${INSTALL_DIR}"
exec .venv/bin/python src/main.py
EOF
chmod +x "${LAUNCHER}"
echo "Created launcher: ${LAUNCHER}"

# Disable LXDE taskbar (lxpanel) for display-only/kiosk use: ensure user autostart exists (copy from global if missing), then disable lxpanel
LXDE_USER_DIR="${HOME}/.config/lxsession/LXDE-pi"
LXDE_AUTOSTART="${LXDE_USER_DIR}/autostart"
GLOBAL_PI="/etc/xdg/lxsession/LXDE-pi/autostart"
GLOBAL_LXDE="/etc/xdg/lxsession/LXDE/autostart"
if [ ! -f "${LXDE_AUTOSTART}" ]; then
  echo "Creating user LXDE autostart (so we can disable the taskbar)..."
  mkdir -p "${LXDE_USER_DIR}"
  if [ -f "${GLOBAL_PI}" ]; then
    cp "${GLOBAL_PI}" "${LXDE_AUTOSTART}"
  elif [ -f "${GLOBAL_LXDE}" ]; then
    cp "${GLOBAL_LXDE}" "${LXDE_AUTOSTART}"
  else
    echo "No global LXDE autostart found; launcher will hide taskbar with killall lxpanel."
  fi
fi
# Disable lxpanel in user LXDE-pi autostart
if [ -f "${LXDE_AUTOSTART}" ] && grep -q 'lxpanel' "${LXDE_AUTOSTART}" 2>/dev/null; then
  echo "Disabling lxpanel (taskbar) in user LXDE autostart..."
  sed -i.bak 's/^@lxpanel/#@lxpanel/; s/^lxpanel/#lxpanel/; s/^[[:space:]]*@lxpanel/#@lxpanel/; s/^[[:space:]]*lxpanel/#lxpanel/' "${LXDE_AUTOSTART}" 2>/dev/null || true
fi
# Disable lxpanel in any other user lxsession profile (e.g. LXDE, Default)
if [ -d "${HOME}/.config/lxsession" ]; then
  for USER_AUTOSTART in "${HOME}/.config/lxsession/"*/autostart; do
    if [ -f "${USER_AUTOSTART}" ] && [ "${USER_AUTOSTART}" != "${LXDE_AUTOSTART}" ] && grep -q 'lxpanel' "${USER_AUTOSTART}" 2>/dev/null; then
      echo "Disabling lxpanel in user autostart: ${USER_AUTOSTART}"
      sed -i.bak 's/^@lxpanel/#@lxpanel/; s/^lxpanel/#lxpanel/; s/^[[:space:]]*@lxpanel/#@lxpanel/; s/^[[:space:]]*lxpanel/#lxpanel/' "${USER_AUTOSTART}" 2>/dev/null || true
    fi
  done
fi
# Disable lxpanel in all global lxsession autostart files (any profile: LXDE-pi, LXDE, Default, etc.)
if [ -d /etc/xdg/lxsession ]; then
  for GLOBAL in /etc/xdg/lxsession/*/autostart; do
    if [ -f "${GLOBAL}" ] && grep -q 'lxpanel' "${GLOBAL}" 2>/dev/null; then
      echo "Disabling lxpanel in global autostart: ${GLOBAL}"
      sudo sed -i.bak 's/^@lxpanel/#@lxpanel/; s/^lxpanel/#lxpanel/; s/^[[:space:]]*@lxpanel/#@lxpanel/; s/^[[:space:]]*lxpanel/#lxpanel/' "${GLOBAL}" 2>/dev/null || true
    fi
  done
fi

# Use only the system service to start the app (avoid two instances from service + XDG autostart)
AUTOSTART_DIR="${HOME}/.config/autostart"
mkdir -p "${AUTOSTART_DIR}"
rm -f "${AUTOSTART_DIR}/weather-display.desktop"
SERVICE_DIR="${HOME}/.config/systemd/user"
mkdir -p "${SERVICE_DIR}"
if [ -f "${SERVICE_DIR}/weather-display.service" ]; then
  systemctl --user disable weather-display.service 2>/dev/null || true
  rm -f "${SERVICE_DIR}/weather-display.service"
  systemctl --user daemon-reload 2>/dev/null || true
fi

# System-level systemd service: starts app when display is ready (does not depend on desktop autostart)
SYSTEMD_SERVICE="/etc/systemd/system/weather-display.service"
echo "Installing system service for autostart at boot..."
sudo tee "${SYSTEMD_SERVICE}" >/dev/null << EOF
[Unit]
Description=Weather Display (8.8" LCD)
After=graphical.target

[Service]
Type=simple
User=${USER}
WorkingDirectory=${INSTALL_DIR}
ExecStartPre=/bin/sleep 5
ExecStart=${LAUNCHER}
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/${USER}/.Xauthority
Restart=on-failure
RestartSec=10

[Install]
WantedBy=graphical.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable weather-display.service
echo "Enabled weather-display.service (starts at boot when display is ready)."

# Single autostart via system service only (XDG/user service removed to prevent two app instances)
echo "Autostart: system service only (one instance)."

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

# Set 1920x480 in config; do not force fullscreen (user can set true in config.json if desired)
if [ -f "${INSTALL_DIR}/config.json" ]; then
    sed -i 's/"fullscreen"\s*:\s*true/"fullscreen": false/' "${INSTALL_DIR}/config.json" 2>/dev/null || true
    sed -i 's/"width"\s*:\s*[0-9]*/"width": 1920/' "${INSTALL_DIR}/config.json" 2>/dev/null || true
    sed -i 's/"height"\s*:\s*[0-9]*/"height": 480/' "${INSTALL_DIR}/config.json" 2>/dev/null || true
fi

# Set Pi display output to 1920x480 for the 8.8" LCD (desktop and app will use this)
BOOT_CONF=""
[ -f /boot/firmware/config.txt ] && BOOT_CONF="/boot/firmware/config.txt"
[ -z "${BOOT_CONF}" ] && [ -f /boot/config.txt ] && BOOT_CONF="/boot/config.txt"
if [ -n "${BOOT_CONF}" ]; then
    if ! sudo grep -q "hdmi_cvt=1920 480" "${BOOT_CONF}" 2>/dev/null; then
        echo "Setting display resolution to 1920x480 (landscape) for LCD..."
        { echo ""; echo "# Weather Display 8.8\" LCD (1920x480 landscape)"; echo "hdmi_cvt=1920 480 60 6 0 0 0"; echo "hdmi_group=2"; echo "hdmi_mode=87"; echo "display_rotate=0"; } | sudo tee -a "${BOOT_CONF}" >/dev/null
    fi
    # Force landscape: replace any existing rotation (0=0°, 2=180°). Also set lcd_rotate for DSI panels.
    echo "Forcing landscape (display_rotate=0, lcd_rotate=0)..."
    sudo sed -i 's/^\(#\s*\)*display_rotate=.*/display_rotate=0/' "${BOOT_CONF}" 2>/dev/null || true
    sudo sed -i 's/^\(#\s*\)*lcd_rotate=.*/lcd_rotate=0/' "${BOOT_CONF}" 2>/dev/null || true
    if ! sudo grep -q "^display_rotate=0" "${BOOT_CONF}" 2>/dev/null; then
        { echo ""; echo "# Landscape for 8.8\" LCD"; echo "display_rotate=0"; } | sudo tee -a "${BOOT_CONF}" >/dev/null
    fi
    if ! sudo grep -q "^lcd_rotate=0" "${BOOT_CONF}" 2>/dev/null; then
        echo "lcd_rotate=0" | sudo tee -a "${BOOT_CONF}" >/dev/null
    fi
else
    echo "To use the LCD at 1920x480 landscape, add to /boot/firmware/config.txt (or /boot/config.txt):"
    echo "  hdmi_cvt=1920 480 60 6 0 0 0"
    echo "  hdmi_group=2"
    echo "  hdmi_mode=87"
    echo "  display_rotate=0"
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
