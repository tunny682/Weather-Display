"""
Weather Display - Main entry point.
Runs the display loop; loads config from project root.
Prompts for location and clock format when config.json is missing.
Use --setup-only to run config setup only (no display; for Pi install script).
"""
import os
import sys
import json
import time
import datetime

import requests


def _project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _geocode(city: str, state: str, country: str = "US") -> tuple[float, float] | None:
    """Return (latitude, longitude) for city, state, country using Nominatim. Returns None on failure."""
    q = f"{city}, {state}, {country}"
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": q, "format": "json", "limit": 1}
    headers = {"User-Agent": "WeatherDisplay/1.0"}
    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        return (lat, lon)
    except (requests.RequestException, KeyError, ValueError, IndexError):
        return None


def _run_setup() -> None:
    """Prompt for city, state, and 12/24h; geocode and write config.json."""
    project_root = _project_root()
    example_path = os.path.join(project_root, "config.json.example")
    config_path = os.path.join(project_root, "config.json")
    if not os.path.isfile(example_path):
        print("config.json.example not found. Cannot run setup.")
        sys.exit(1)

    print("Welcome! Set your location and preferences.\n")
    city = input("City (e.g. Denver): ").strip() or "New York"
    state = input("State (e.g. CO or Colorado): ").strip() or "NY"
    country = input("Country (default US): ").strip() or "US"

    print("\n12-hour (e.g. 2:30 PM) or 24-hour (e.g. 14:30)?")
    use_24 = input("Enter 12 or 24 (default 12): ").strip().lower() in ("24", "24h", "24-hour")

    print("\nLooking up coordinates...")
    coords = _geocode(city, state, country)
    if not coords:
        print("Could not find that location. Using default (New York).")
        lat, lon = 40.7128, -74.0060
        location_display = "New York, NY, US"
    else:
        lat, lon = coords
        location_display = f"{city}, {state}, {country}"

    with open(example_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    config.setdefault("weather", {})["latitude"] = lat
    config.setdefault("weather", {})["longitude"] = lon
    config.setdefault("weather", {})["location_display"] = location_display
    config.setdefault("display", {})["time_format_24"] = use_24

    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)

    print(f"Saved config to config.json ({location_display}).\n")


def load_config():
    """Load config.json from project root. If missing, run setup (prompt location + clock), then load."""
    project_root = _project_root()
    config_path = os.path.join(project_root, "config.json")
    example_path = os.path.join(project_root, "config.json.example")
    if not os.path.isfile(config_path):
        if os.path.isfile(example_path):
            _run_setup()
        else:
            print("config.json not found. Copy config.json.example to config.json and edit it.")
            sys.exit(1)
    if not os.path.isfile(config_path):
        sys.exit(1)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in config.json: {e}")
        sys.exit(1)
    except OSError as e:
        print(f"Cannot read config: {e}")
        sys.exit(1)


def main():
    import pygame
    from weather import fetch_weather
    from display import draw as draw_display

    config = load_config()
    display_cfg = config.get("display", {})
    width = display_cfg.get("width", 1920)
    height = display_cfg.get("height", 480)
    fullscreen = display_cfg.get("fullscreen", False)

    # Ensure sane resolution (e.g. for LCD 1920x480)
    try:
        width = max(320, min(4096, int(width)))
        height = max(240, min(2160, int(height)))
    except (TypeError, ValueError):
        width, height = 1920, 480

    try:
        pygame.init()
    except pygame.error as e:
        print(f"Pygame init failed: {e}")
        sys.exit(1)

    # Fullscreen: use always-on-top so window stays above taskbar (like Electron kiosk)
    fullscreen_flags = pygame.FULLSCREEN | pygame.NOFRAME
    if fullscreen and sys.platform != "win32":
        try:
            fullscreen_flags |= pygame.WINDOW_ALWAYS_ON_TOP
        except AttributeError:
            fullscreen_flags |= 0x00010000  # SDL_WINDOW_ALWAYS_ON_TOP
    try:
        if fullscreen:
            screen = pygame.display.set_mode((width, height), fullscreen_flags)
        else:
            screen = pygame.display.set_mode((width, height), pygame.RESIZABLE | pygame.NOFRAME)
    except pygame.error as e:
        print(f"Cannot set display mode {width}x{height}: {e}")
        pygame.quit()
        sys.exit(1)

    pygame.display.set_caption("Weather Display")

    # If the display is portrait (e.g. OS gave 480x1920), draw to a landscape buffer and rotate for correct orientation
    actual_w, actual_h = screen.get_width(), screen.get_height()
    use_software_rotate = actual_w < actual_h
    if use_software_rotate:
        buffer = pygame.Surface((width, height))
        # Rotation angle to show our 1920x480 layout correctly on portrait display: -90 = CCW
        rotate_degrees = int(display_cfg.get("software_rotate", -90))
    else:
        buffer = None
        rotate_degrees = 0

    clock = pygame.time.Clock()
    running = True

    # Weather: fetch at startup and refresh on interval
    weather_data = fetch_weather(config)
    last_weather_time = time.time()
    refresh_minutes = config.get("weather", {}).get("refresh_minutes", 15)
    refresh_seconds = max(60, refresh_minutes * 60)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # Refresh weather on interval
        now_ts = time.time()
        if now_ts - last_weather_time >= refresh_seconds:
            weather_data = fetch_weather(config)
            last_weather_time = now_ts

        if use_software_rotate and buffer is not None:
            draw_display(buffer, config, weather_data, datetime.datetime.now())
            rotated = pygame.transform.rotate(buffer, rotate_degrees)
            # Center the rotated buffer; clamp so we never blit with negative x/y
            rw, rh = rotated.get_size()
            x = max(0, (actual_w - rw) // 2)
            y = max(0, (actual_h - rh) // 2)
            screen.fill((0, 0, 0))
            screen.blit(rotated, (x, y))
        else:
            draw_display(screen, config, weather_data, datetime.datetime.now())
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    if "--setup-only" in sys.argv:
        _run_setup()
        sys.exit(0)
    main()
