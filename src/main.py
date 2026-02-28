"""
Weather Display - Main entry point.
Runs the display loop; loads config from project root.
"""
import os
import sys
import json
import time
import datetime

import pygame

from weather import fetch_weather
from display import draw as draw_display


def load_config():
    """Load config.json from project root (parent of src/)."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(project_root, "config.json")
    if not os.path.isfile(config_path):
        print("config.json not found. Copy config.json.example to config.json and edit it.")
        sys.exit(1)
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in config.json: {e}")
        sys.exit(1)
    except OSError as e:
        print(f"Cannot read config.json: {e}")
        sys.exit(1)


def main():
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

    try:
        if fullscreen:
            screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
        else:
            screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    except pygame.error as e:
        print(f"Cannot set display mode {width}x{height}: {e}")
        pygame.quit()
        sys.exit(1)

    pygame.display.set_caption("Weather Display")

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

        draw_display(screen, config, weather_data, datetime.datetime.now())
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
