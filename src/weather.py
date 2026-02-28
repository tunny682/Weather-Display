"""
Weather API client. Fetches current conditions and forecast from Open-Meteo (or configurable API).
Returns a normalized structure for the display to use.
"""
import datetime
import logging
from typing import Any, Optional

import requests

# WMO weather codes: map to simple condition names for icons
# https://open-meteo.com/en/docs#api-form
WMO_TO_CONDITION = {
    0: "clear",
    1: "mainly_clear",
    2: "partly_cloudy",
    3: "overcast",
    45: "fog",
    48: "fog",
    51: "drizzle",
    53: "drizzle",
    55: "drizzle",
    61: "rain",
    63: "rain",
    65: "rain",
    71: "snow",
    73: "snow",
    75: "snow",
    77: "snow",
    80: "rain",
    81: "rain",
    82: "rain",
    85: "snow",
    86: "snow",
    95: "thunderstorm",
    96: "thunderstorm",
    99: "thunderstorm",
}


def _condition_from_code(code: int) -> str:
    return WMO_TO_CONDITION.get(code, "unknown")


def fetch_weather(config: dict) -> Optional[dict[str, Any]]:
    """
    Fetch weather from the API using config['weather'].
    Returns a normalized dict:
      current: { temp, condition_code, condition, high, low }
      forecast: [ { day_name, condition_code, condition, temp }, ... ]  (5 days)
    Returns None on error (and logs).
    """
    cfg = config.get("weather", {})
    base = (cfg.get("api_base_url") or "").rstrip("/")
    lat = cfg.get("latitude")
    lon = cfg.get("longitude")
    if not base or lat is None or lon is None:
        logging.warning("weather config missing api_base_url, latitude, or longitude")
        return None

    # Open-Meteo style: one URL for current + daily
    if "open-meteo.com" in base:
        return _fetch_open_meteo(base, lat, lon, cfg)
    # Add more backends here (e.g. OpenWeatherMap) if needed
    logging.warning("Unknown API base URL; only Open-Meteo is supported for now")
    return None


def _fetch_open_meteo(base: str, lat: float, lon: float, cfg: dict) -> Optional[dict[str, Any]]:
    # timezone required when using daily; "time" is returned automatically with daily
    tz = cfg.get("timezone", "auto")
    url = (
        f"{base}"
        f"?latitude={lat}&longitude={lon}"
        "&current=temperature_2m,weather_code"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min"
        f"&timezone={tz}"
        "&forecast_days=7"
    )
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
    except requests.RequestException as e:
        logging.exception("Weather API request failed: %s", e)
        return None
    except ValueError as e:
        logging.exception("Weather API invalid JSON: %s", e)
        return None

    current = data.get("current") or {}
    daily = data.get("daily") or {}
    times = daily.get("time") or []
    codes = daily.get("weather_code") or []
    max_t = daily.get("temperature_2m_max") or []
    min_t = daily.get("temperature_2m_min") or []

    temp_now = current.get("temperature_2m")
    code_now = current.get("weather_code", 0)
    # Today's high/low from daily index 0
    high = max_t[0] if max_t else temp_now
    low = min_t[0] if min_t else temp_now

    # Next 5 days (indices 1..5)
    forecast = []
    for i in range(1, min(6, len(times))):
        t = times[i]
        code = codes[i] if i < len(codes) else 0
        temp = max_t[i] if i < len(max_t) else None
        try:
            dt = datetime.datetime.fromisoformat(t.replace("Z", "+00:00"))
            day_name = dt.strftime("%a")  # Mon, Tue, ...
        except (TypeError, ValueError):
            day_name = str(t)[:3]
        forecast.append({
            "day_name": day_name,
            "condition_code": code,
            "condition": _condition_from_code(code),
            "temp": temp,
        })

    return {
        "current": {
            "temp": temp_now,
            "condition_code": code_now,
            "condition": _condition_from_code(code_now),
            "high": high,
            "low": low,
        },
        "forecast": forecast,
    }
