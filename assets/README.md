# Assets

## Weather icons

Place **PNG** weather icons in this folder:

```
assets/
  icons/
    sun.png / sunny.png          ← clear, mainly_clear (small: forecast strip)
    sun_2x.png / sunny_2x.png   ← same, large (current weather, daytime)
    moon.png / sun_night.png / night.png   ← clear at night (small)
    moon_2x.png / sun_night_2x.png / night_2x.png   ← clear at night (large, current weather)
    cloud.png / cloud_2x.png
    rain.png / rain_2x.png
    snow.png / snow_2x.png
    storm.png / storm_2x.png
    fog.png / fog_2x.png
```

- **Small icons** (no `_2x`): used in the 5-day forecast strip.  
- **Large icons** (`_2x` in filename): used for current weather. If a `_2x` file is missing, the app uses the small icon and scales it up.
- **Night**: for clear sky at night the app shows a moon icon. Other conditions (e.g. mostly cloudy, hazy) can have night variants. **Put `n` before `2x`** for large night icons: e.g. **`mostlycloudyn2x.png`**, **`hazyn2x.png`**. Small night: **`*n.png`** (e.g. `mostlycloudyn.png`). Clear night: **`moon.png`** / **`moon_2x.png`** or **`sun_night.png`** / **`sun_night_2x.png`**. Only the current-weather icon switches to night; the forecast strip uses day icons.
- Use **transparent background**. Suggested: small ~64–110 px, large (2x) ~128–220 px; the app scales as needed.
- File names must match exactly (lowercase) or the app falls back to drawn shapes.

If a file is missing, the app draws a simple shape instead. You can add icons gradually.
