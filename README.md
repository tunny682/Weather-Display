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

On a Pi (e.g. Raspberry Pi 5) with the 8.8" LCD connected:

**Download the install script**

```bash
wget https://raw.githubusercontent.com/tunny682/Weather-Display/master/setup.sh
```

**Install the software:**

```bash
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
- Configures a **systemd user service** so the display auto-starts after you log in (graphical session).

To run the display manually: `cd ~/weather-display && .venv/bin/python src/main.py`. Set `display.fullscreen` to `true` in `config.json` for kiosk use.

## License

Use and modify as you like.
