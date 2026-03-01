"""
Renders the weather display layout: time/date left, current weather + 5-day forecast right.
Layout matches the 8.8" LCD design (1920x480).
"""
import datetime
import os
from typing import Any, Optional

import pygame

# Project root (parent of src/) for resolving assets
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ICONS_DIR = os.path.join(_PROJECT_ROOT, "assets", "icons")
_icon_cache: dict[str, pygame.Surface] = {}


# Condition name -> icon type (matches assets/icons filenames: partlycloudy, mostlycloudy, hazy, etc.)
def _icon_type(condition: str) -> str:
    if condition in ("clear", "mainly_clear"):
        return "sun"
    if condition == "partly_cloudy":
        return "partlycloudy"
    if condition in ("overcast", "cloudy"):
        return "mostlycloudy"
    if "rain" in condition or "drizzle" in condition:
        return "rain"
    if "snow" in condition:
        return "snow"
    if "thunderstorm" in condition:
        return "storm"
    if "fog" in condition:
        return "hazy"
    return "mostlycloudy"


# Optional alternate filenames (e.g. sunny.png for sun). 2x = larger current-weather icon.
# Night: use for clear sky at night (moon). Forecast strip always uses day icons.
_ICON_ALIASES: dict[str, list[str]] = {
    "sun": ["sun", "sunny"],
    "moon": ["moon", "sun_night", "night"],
    "mostlycloudy": ["mostlycloudy", "cloudy"],
}


def _load_icon(icon_type: str, use_2x: bool = False, is_night: bool = False) -> Optional[pygame.Surface]:
    """Load icon PNG from assets/icons. use_2x=True for large; is_night=True tries *n.png or *n2x.png (n before 2x)."""
    cache_key = f"{icon_type}_2x_night" if (use_2x and is_night) else (f"{icon_type}_2x" if use_2x else icon_type)
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]
    if use_2x and is_night:
        # Night 2x: n before 2x (e.g. mostlycloudyn2x.png) or n after 2x (e.g. mostlycloudy2xn.png)
        names = [
            f"{icon_type}n2x.png", f"{icon_type}_n2x.png", f"{icon_type}n_2x.png",
            f"{icon_type}2xn.png", f"{icon_type}_2xn.png",
        ] + [f"{alt}n2x.png" for alt in _ICON_ALIASES.get(icon_type, []) if alt != icon_type]
        names += [f"{alt}2xn.png" for alt in _ICON_ALIASES.get(icon_type, []) if alt != icon_type]
    elif use_2x:
        names = [f"{icon_type}_2x.png", f"{icon_type}2x.png"] + [
            f"{alt}_2x.png" for alt in _ICON_ALIASES.get(icon_type, []) if alt != icon_type
        ] + [f"{alt}2x.png" for alt in _ICON_ALIASES.get(icon_type, []) if alt != icon_type]
    else:
        if is_night:
            names = [f"{icon_type}n.png", f"{icon_type}_n.png", f"{icon_type}.png"]
        else:
            names = [f"{icon_type}.png"] + [
                f"{alt}.png" for alt in _ICON_ALIASES.get(icon_type, []) if alt != icon_type
            ]
    for name in names:
        path = os.path.join(_ICONS_DIR, name)
        if os.path.isfile(path):
            try:
                img = pygame.image.load(path)
                if img.get_alpha() is None:
                    img.set_colorkey((0, 0, 0))
                _icon_cache[cache_key] = img
                return img
            except (pygame.error, OSError):
                pass
    # If 2x night not found, try day 2x; if 2x not found, try non-2x (scaled up)
    if use_2x and is_night:
        img = _load_icon(icon_type, use_2x=True, is_night=False)
        if img is not None:
            _icon_cache[cache_key] = img
        return _icon_cache.get(cache_key)
    if use_2x:
        img = _load_icon(icon_type, use_2x=False, is_night=is_night)
        if img is not None:
            _icon_cache[cache_key] = img
        return _icon_cache.get(cache_key)
    _icon_cache[cache_key] = None
    return None


def _draw_icon(
    surface: pygame.Surface,
    x: int,
    y: int,
    icon_type: str,
    size: int,
    color: tuple,
    use_2x: bool = False,
    is_night: bool = False,
) -> None:
    """Draw icon at (x,y) center. use_2x=True uses *_2x.png; is_night=True tries *n.png / *2xn.png."""
    img = _load_icon(icon_type, use_2x=use_2x, is_night=is_night)
    if img is not None:
        # Scale so the icon fits in a 2*size box and center at (x, y)
        iw, ih = img.get_width(), img.get_height()
        max_side = max(iw, ih, 1)
        scale = (2 * size) / max_side
        w, h = int(iw * scale), int(ih * scale)
        scaled = pygame.transform.smoothscale(img, (w, h))
        rect = scaled.get_rect(center=(x, y))
        surface.blit(scaled, rect)
        return
    # Fallback: draw simple shapes
    if icon_type == "sun":
        pygame.draw.circle(surface, (255, 220, 0), (x, y), size)
    elif icon_type == "moon":
        pygame.draw.circle(surface, (220, 220, 230), (x, y), size)
    elif icon_type in ("partlycloudy", "mostlycloudy", "cloud"):
        r = size
        pygame.draw.circle(surface, color, (x - r // 2, y), r // 2)
        pygame.draw.circle(surface, color, (x, y - r // 4), r // 2)
        pygame.draw.circle(surface, color, (x + r // 2, y), r // 2)
        pygame.draw.ellipse(surface, color, (x - r, y - r // 4, r * 2, r))
    elif icon_type == "rain":
        pygame.draw.circle(surface, color, (x - size // 2, y), size // 3)
        pygame.draw.circle(surface, color, (x + size // 2, y), size // 3)
        for i in range(-1, 2):
            pygame.draw.line(surface, color, (x + i * 4, y + size // 2), (x + i * 4, y + size), 2)
    else:
        _draw_icon(surface, x, y, "cloud", size, color)


def _draw_time_colon(surface: pygame.Surface, x: int, y: int, size: int, color: tuple) -> None:
    """Draw two stacked squares as colon (like the reference)."""
    h = max(2, size // 12)
    w = max(2, size // 12)
    gap = size // 6
    top = (x - w // 2, y - gap // 2 - h)
    bot = (x - w // 2, y + gap // 2)
    pygame.draw.rect(surface, color, (*top, w, h))
    pygame.draw.rect(surface, color, (*bot, w, h))


def draw(surface: pygame.Surface, config: dict, weather_data: Optional[dict], now: datetime.datetime) -> None:
    """Draw full layout: black background, time/date left, weather right."""
    w = surface.get_width()
    h = surface.get_height()
    surface.fill((0, 0, 0))

    time_24 = config.get("display", {}).get("time_format_24", False)
    left_third = w // 3
    right_start = left_third

    # ---- Left: Time and date ----
    time_font = pygame.font.Font(None, 120)
    date_font = pygame.font.Font(None, 56)
    white = (255, 255, 255)

    if time_24:
        time_str = now.strftime("%H:%M")
        colon_pos = time_str.index(":")
    else:
        time_str = now.strftime("%I:%M%p").lstrip("0")  # 2:08PM
        if ":" in time_str:
            colon_pos = time_str.index(":")
        else:
            colon_pos = -1

    # Time: render in segments so we can replace the colon with two squares
    if colon_pos >= 0:
        part1 = time_str[:colon_pos]
        part2 = time_str[colon_pos + 1:]
        s1 = time_font.render(part1, True, white)
        s2 = time_font.render(part2, True, white)
        total_w = s1.get_width() + s2.get_width() + 20  # gap for colon
        x_start = (left_third - total_w) // 2
        y_time = h // 3
        surface.blit(s1, (x_start, y_time - s1.get_height() // 2))
        colon_x = x_start + s1.get_width() + 10
        _draw_time_colon(surface, colon_x, y_time, 120, white)
        surface.blit(s2, (colon_x + 12, y_time - s2.get_height() // 2))
    else:
        time_surf = time_font.render(time_str, True, white)
        tr = time_surf.get_rect(centerx=left_third // 2, centery=h // 3)
        surface.blit(time_surf, tr)

    # e.g. "Monday, Feb 9" (Windows lacks %-d, so use day number)
    date_str = now.strftime("%A, %b ") + str(now.day)
    date_surf = date_font.render(date_str, True, white)
    date_rect = date_surf.get_rect(centerx=left_third // 2, centery=h // 3 + 70)
    surface.blit(date_surf, date_rect)

    # ---- Right: Current weather + 5-day forecast ----
    cur_font = pygame.font.Font(None, 72)
    hl_font = pygame.font.Font(None, 42)
    day_font = pygame.font.Font(None, 36)
    temp_font = pygame.font.Font(None, 32)

    current = (weather_data or {}).get("current")
    forecast = (weather_data or {}).get("forecast") or []

    # Current weather block (top right)
    block_w = w - right_start - 40
    cur_y = 40
    if current:
        temp = current.get("temp")
        high = current.get("high")
        low = current.get("low")
        condition = current.get("condition", "unknown")
        is_day = current.get("is_day", 1)
        icon_t = _icon_type(condition)
        if not is_day and icon_t == "sun":
            icon_t = "moon"
        # Icon, then current temp, then H/L stacked
        icon_x = right_start + 60
        icon_y = cur_y + 50
        _draw_icon(surface, icon_x, icon_y, icon_t, 44, white, use_2x=True, is_night=not is_day)
        if temp is not None:
            temp_str = f"{int(round(temp))}°"
            ts = cur_font.render(temp_str, True, white)
            surface.blit(ts, (right_start + 120, cur_y + 20))
        if high is not None and low is not None:
            hl1 = hl_font.render(f"H{int(round(high))}°", True, white)
            hl2 = hl_font.render(f"L{int(round(low))}°", True, white)
            surface.blit(hl1, (right_start + 220, cur_y + 35))
            surface.blit(hl2, (right_start + 220, cur_y + 35 + hl1.get_height() + 4))

    # 5-day forecast (bottom right, horizontal strip)
    num_days = min(5, len(forecast))
    if num_days > 0:
        strip_y = h - 140
        col_w = (w - right_start - 40) // 5
        sep_color = (80, 80, 80)
        for i in range(num_days):
            day_data = forecast[i]
            cx = right_start + 20 + (i * col_w) + col_w // 2
            # Day name
            day_name = day_data.get("day_name", "—")
            day_surf = day_font.render(day_name, True, white)
            surface.blit(day_surf, day_surf.get_rect(centerx=cx, bottom=strip_y + 25))
            # Icon
            cond = day_data.get("condition", "unknown")
            _draw_icon(surface, cx, strip_y + 55, _icon_type(cond), 28, white, use_2x=False)
            # Temp
            t = day_data.get("temp")
            if t is not None:
                temp_s = temp_font.render(f"{int(round(t))}°", True, white)
                surface.blit(temp_s, temp_s.get_rect(centerx=cx, top=strip_y + 85))
            # Vertical separator to the right (except last)
            if i < num_days - 1:
                sx = right_start + 20 + (i + 1) * col_w
                pygame.draw.line(surface, sep_color, (sx, strip_y), (sx, strip_y + 120), 1)
