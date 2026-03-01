#!/bin/bash
# Fix LCD rotation to landscape on Raspberry Pi. Run on the Pi, then: sudo reboot
# Usage: sudo bash fix-rotation.sh   (or: bash fix-rotation.sh with sudo for the commands inside)

set -e
BOOT_CONF=""
[ -f /boot/firmware/config.txt ] && BOOT_CONF="/boot/firmware/config.txt"
[ -z "${BOOT_CONF}" ] && [ -f /boot/config.txt ] && BOOT_CONF="/boot/config.txt"

if [ -z "${BOOT_CONF}" ]; then
    echo "Could not find config.txt (not a Pi?)."
    exit 1
fi

echo "Setting display to landscape in ${BOOT_CONF}..."
sudo sed -i 's/^\(#\s*\)*display_rotate=.*/display_rotate=0/' "${BOOT_CONF}" 2>/dev/null || true
sudo sed -i 's/^\(#\s*\)*lcd_rotate=.*/lcd_rotate=0/' "${BOOT_CONF}" 2>/dev/null || true
if ! sudo grep -q "^display_rotate=0" "${BOOT_CONF}" 2>/dev/null; then
    echo "" | sudo tee -a "${BOOT_CONF}" >/dev/null
    echo "# Landscape for 8.8\" LCD" | sudo tee -a "${BOOT_CONF}" >/dev/null
    echo "display_rotate=0" | sudo tee -a "${BOOT_CONF}" >/dev/null
fi
if ! sudo grep -q "^lcd_rotate=0" "${BOOT_CONF}" 2>/dev/null; then
    echo "lcd_rotate=0" | sudo tee -a "${BOOT_CONF}" >/dev/null
fi
echo "Done. Reboot to apply:  sudo reboot"
