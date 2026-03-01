# Weather Display

A weather and time display for an **8.8" LCD** (1920×480), designed to run on **Raspberry Pi 5** or any PC. Uses the [Open-Meteo](https://open-meteo.com/) API (no API key required).

## Features

- **Time & date** — Large clock (12- or 24-hour) and date on the left
- **Current weather** — Temperature, high/low, and condition icon
- **5-day forecast** — Strip along the bottom with day, icon, and temperature
- **Configurable** — Location, time format, dimming, and blackout hours via `config.json`
- **Optional backlight control** — GPIO dimming/off when supported by the display

## Requirements

- Python 3.10+
- PyGame, requests, gpiozero (see `requirements.txt`)

## Run locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run (from project root; uses config.json.example if config.json is missing)
python src/main.py
```

Close the window or press **Escape** to exit.

## Configuration

Copy `config.json.example` to `config.json` and edit as needed:

| Section    | Keys              | Description                                      |
|-----------|-------------------|--------------------------------------------------|
| `weather` | `latitude`, `longitude` | Your location for weather data              |
| `weather` | `refresh_minutes` | How often to refresh the API (default 15)        |
| `weather` | `temperature_unit` | `"fahrenheit"` (imperial) or `"celsius"` (metric) |
| `display` | `time_format_24`  | `true` for 24-hour, `false` for 12-hour (AM/PM) |
| `display` | `software_rotate` | When display is portrait, rotate buffer: `-90` or `90` to fix orientation |
| `dimming` | `dim_start`, `dim_end` | Time window for reduced brightness        |
| `blackout`| `start`, `end`    | Time window for screen off (full black)          |
| `backlight` | `gpio`          | GPIO pin number for backlight PWM, or `null`     |

No API key is needed for Open-Meteo.

## Project structure

```
├── config.json.example   # Example config (copy to config.json)
├── requirements.txt
├── src/
│   ├── main.py            # Entry point, display loop
│   ├── display.py         # Layout and drawing
│   └── weather.py         # Open-Meteo API client
└── assets/icons/          # Optional weather icon images
```

## Raspberry Pi installation

Works on **Raspberry Pi OS Bookworm** (Debian 12, X11) and **Trixie** (Debian 13, Wayland/labwc). On a Pi (e.g. Raspberry Pi 5) with the 8.8" LCD connected, use one of these methods. Replace the repo URL with your own if you forked or use a different repo.

**Method 1 — Clone repo, then run setup (recommended; avoids 404 from raw URL)**

```bash
git clone https://github.com/tunny682/Weather-Display.git
cd Weather-Display
bash setup.sh
```

**Method 2 — Download script with wget, then run**

```bash
wget https://raw.githubusercontent.com/tunny682/Weather-Display/master/setup.sh
bash setup.sh
```

If you get a **404** with `wget`, the repo may use branch `main` or the URL may differ. Use Method 1 instead, or try:

```bash
wget https://raw.githubusercontent.com/tunny682/Weather-Display/main/setup.sh
bash setup.sh
```

**Reboot Raspberry Pi**

```bash
sudo reboot
```

After reboot the display should start automatically.

### What This Script Does

- Installs required system dependencies (Python 3, pip, venv, SDL libraries for PyGame).
- Clones the repository to `~/weather-display` (or uses the current directory if you already cloned it).
- Creates a Python virtualenv and installs packages from `requirements.txt`.
- Runs interactive setup (location and time format) and writes `config.json`.
- Sets **display resolution to 1920×480** and **landscape orientation** (`display_rotate=0`) in the Pi’s boot config so the 8.8" LCD shows correctly. The app uses 1920×480 from `config.json`.
- Enables **desktop autologin** (when using LightDM) so the Pi boots straight to the desktop with **no login screen and no keyboard required**.
- Adds **XDG autostart** so the weather app starts as soon as the desktop is ready.
- App launches in a **window** by default; set `"fullscreen": true` in `config.json` if you want it to take over the LCD.
- **rotate_display.sh** rotates the **entire desktop** (all connected outputs). **No user input on the display** — the script defaults to `ROTATE=right` (same as the working Canterrain example); setup creates `rotate.conf` with that so the unit works without a keyboard. It retries for up to 60s until X11 or Wayland is ready, then runs `xrandr --output <each> --rotate right` (or the value in `rotate.conf`). A systemd user service runs it at session start; the launcher also runs it when the app starts.

After reboot: power on with the LCD connected and the app starts automatically—no keyboard or interaction needed.

**If the app doesn’t autostart:** ensure autologin is enabled (e.g. **Raspberry Pi Configuration** → **System** → **Auto Login** → “Desktop auto login as user ‘pi’”), then reboot.

**If the display is still not rotating:** see **[ROTATION.md](ROTATION.md)**. Quick checks: (1) Try `ROTATE=right` or `ROTATE=left` when running `rotate_display.sh` (the working Canterrain example uses `right`). If one works, add `echo "ROTATE=right" > ~/weather-display/rotate.conf` and reboot. (2) If xrandr doesn’t list your LCD, set rotation in `/boot/firmware/config.txt` with `display_rotate=0` (or 1, 2, 3) and reboot.

To run the display manually: `cd ~/weather-display && .venv/bin/python src/main.py`.

## License

Use and modify as you like.
