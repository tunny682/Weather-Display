# Display rotation

**The display has no input** (no keyboard/touch), so rotation is fully automatic: the script defaults to `ROTATE=right` (same as the Canterrain working example). Setup creates `rotate.conf` with `ROTATE=right` if it doesn’t exist. No user action is required on the unit.

If you need a different orientation (e.g. after testing via SSH), edit or create `~/weather-display/rotate.conf` with one of: `ROTATE=normal`, `ROTATE=right`, `ROTATE=left`, `ROTATE=inverted`, then reboot.

---

## Troubleshooting

If the desktop or weather app is still in the wrong orientation, try these steps (e.g. over SSH).

## 1. Try different rotation directions

The script supports `normal`, `right`, `left`, `inverted`. Some 8.8" panels need `right` or `left` instead of `normal`.

**Run by hand** (replace `~/weather-display` with your install path if different):

```bash
# Try rotating to "right" (90° clockwise) - like the Canterrain working example
cd ~/weather-display
DISPLAY=:0 XAUTHORITY=$HOME/.Xauthority ROTATE=right bash rotate_display.sh

# If that’s wrong, try "left" (90° counter-clockwise)
ROTATE=left bash rotate_display.sh

# Or back to landscape with no rotation
ROTATE=normal bash rotate_display.sh
```

If one of these fixes the desktop, make it permanent:

```bash
echo "ROTATE=right" > ~/weather-display/rotate.conf
# or  ROTATE=left   or  ROTATE=normal
```

Then reboot. The script reads `rotate.conf` when it runs.

## 2. Check that the rotate script is running

```bash
# User service (runs at login)
systemctl --user status rotate-display.service

# See if xrandr sees your display
DISPLAY=:0 xrandr -q
```

If `xrandr -q` doesn’t list your 8.8" LCD, the panel may be driven by a different stack (e.g. DSI). In that case rotation may only work via the boot config (next step).

## 3. Boot config (config.txt)

If xrandr/wlr-randr don’t affect the display, set rotation in the Pi boot config and reboot:

```bash
sudo nano /boot/firmware/config.txt
# or:  sudo nano /boot/config.txt
```

Add or edit (only one uncommented line):

- `display_rotate=0`  — landscape
- `display_rotate=1`  — portrait (90° right)
- `display_rotate=2`  — landscape upside-down
- `display_rotate=3`  — portrait (90° left)

Try `0` first; if the image is still wrong, try `1` or `3`. Then reboot.

## 4. App-only correction (software rotation)

If the desktop stays wrong but you only need the weather app to look right:

- When the OS reports a **portrait** resolution (e.g. 480×1920), the app already draws to a buffer and rotates it. Tweak in `config.json`:
  - `"software_rotate": -90`  or  `"software_rotate": 90`
- If the OS reports **landscape** (1920×480) but the physical panel shows it rotated, the driver/config.txt rotation (step 3) or the desktop rotate script (step 1) must fix the whole display; the app can’t fix that alone.
