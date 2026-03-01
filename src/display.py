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


_WHITE = (255, 255, 255)
# White vertical lines between forecast columns (mirror reference layout)
_SEP_COLOR = (255, 255, 255)


def _blit_text(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    x: int,
    y: int,
    anchor: str = "center",
    color: tuple = _WHITE,
) -> None:
    """Draw text in the given color. anchor: 'center', 'midleft', 'topleft', 'midbottom', 'midtop', etc."""
    surf = font.render(text, True, color)
    rect = surf.get_rect(**{anchor: (x, y)})
    surface.blit(surf, rect)


def draw(surface: pygame.Surface, config: dict, weather_data: Optional[dict], now: datetime.datetime) -> None:
    """Draw full layout: black background, white text; scaled for 1920x480 with minimal dead space."""
    w = surface.get_width()
    h = surface.get_height()
    surface.fill((0, 0, 0))

    time_24 = config.get("display", {}).get("time_format_24", False)
    left_third = w // 3
    right_start = left_third
    white = _WHITE

    # ---- Font sizes: time dominant; date proportional to time; then current temp, H/L, forecast ----
    time_font = pygame.font.Font(None, 180)
    date_font = pygame.font.Font(None, 96)   # proportional to time (e.g. ~half)
    cur_font = pygame.font.Font(None, 108)
    hl_font = pygame.font.Font(None, 58)
    day_font = pygame.font.Font(None, 52)
    temp_font = pygame.font.Font(None, 48)

    if time_24:
        time_str = now.strftime("%H:%M")
        colon_pos = time_str.index(":")
    else:
        time_str = now.strftime("%I:%M%p")
        colon_pos = time_str.index(":") if ":" in time_str else -1

    # ---- Left: Time and date — vertically centered in left third to fill space ----
    y_time = h // 2 - 80
    if colon_pos >= 0:
        part1 = time_str[:colon_pos]
        part2 = time_str[colon_pos + 1:]
        s1 = time_font.render(part1, True, white)
        s2 = time_font.render(part2, True, white)
        total_w = s1.get_width() + s2.get_width() + 24
        x_start = (left_third - total_w) // 2
        _blit_text(surface, time_font, part1, x_start, y_time - s1.get_height() // 2, "topleft")
        colon_x = x_start + s1.get_width() + 12
        _draw_time_colon(surface, colon_x, y_time, 180, white)
        _blit_text(surface, time_font, part2, colon_x + 16, y_time - s2.get_height() // 2, "topleft")
    else:
        _blit_text(surface, time_font, time_str, left_third // 2, y_time, "center")

    # Date vertically aligned with time: just below it with a small gap (no large dead space)
    date_str = now.strftime("%A, %b ") + str(now.day)
    time_height = time_font.get_height()
    date_gap = 14
    date_y = y_time + time_height // 2 + date_gap + date_font.get_height() // 2
    _blit_text(surface, date_font, date_str, left_third // 2, date_y, "center")

    # ---- Right: 5-day forecast column layout (same col_w for alignment); current weather above, aligned with first column ----
    current = (weather_data or {}).get("current")
    forecast = (weather_data or {}).get("forecast") or []
    strip_y = h - 200
    strip_h = 180
    col_w = (w - right_start - 40) // 5
    # Center of first column (Mon) — current weather icon lines up with this
    first_col_center = right_start + 20 + col_w // 2

    if current:
        temp = current.get("temp")
        high = current.get("high")
        low = current.get("low")
        condition = current.get("condition", "unknown")
        is_day = current.get("is_day", 1)
        icon_t = _icon_type(condition)
        if not is_day and icon_t == "sun":
            icon_t = "moon"
        # Current weather top aligned with top of time (08:15AM)
        icon_x = first_col_center
        cur_y = y_time - time_font.get_height() // 2
        icon_y = cur_y + 55
        _draw_icon(surface, icon_x, icon_y, icon_t, 58, white, use_2x=True, is_night=not is_day)
        temp_x = icon_x + 110
        temp_y = cur_y + 18
        if temp is not None:
            _blit_text(surface, cur_font, f"{int(round(temp))}°", temp_x, temp_y, "topleft")
        hl_x = icon_x + 270
        if high is not None and low is not None:
            _blit_text(surface, hl_font, f"H{int(round(high))}°", hl_x, temp_y, "topleft")
            _blit_text(surface, hl_font, f"L{int(round(low))}°", hl_x, temp_y + hl_font.get_height() + 6, "topleft")

    # ---- 5-day forecast: same column centers so current weather and Mon align ----
    num_days = min(5, len(forecast))
    if num_days > 0:
        for i in range(num_days):
            day_data = forecast[i]
            cx = right_start + 20 + (i * col_w) + col_w // 2
            day_name = day_data.get("day_name", "—")
            _blit_text(surface, day_font, day_name, cx, strip_y + 32, "midbottom")
            cond = day_data.get("condition", "unknown")
            _draw_icon(surface, cx, strip_y + 95, _icon_type(cond), 38, white, use_2x=False)
            t = day_data.get("temp")
            if t is not None:
                _blit_text(surface, temp_font, f"{int(round(t))}°", cx, strip_y + 145, "midtop")
            if i < num_days - 1:
                sx = right_start + 20 + (i + 1) * col_w
                pygame.draw.line(surface, _SEP_COLOR, (sx, strip_y), (sx, strip_y + strip_h), 1)
