# Assets

## Weather icons

Place **PNG** weather icons in `assets/icons/`. The app matches conditions to icon types and tries the filenames below (and `*2x.png` / `*_2x.png` for large).

| Condition        | Icon type       | Filenames (small / large 2x) |
|------------------|-----------------|------------------------------|
| Clear, mainly clear | sun         | sun.png, sunny.png / sun_2x.png, sunny_2x.png, sunny2x.png |
| Clear at night  | moon            | moon.png, sun_night.png, night.png / moon_2x.png, etc. |
| Partly cloudy   | partlycloudy    | partlycloudy.png / partlycloudy2x.png |
| Overcast, cloudy| mostlycloudy, cloudy | mostlycloudy.png, cloudy.png / mostlycloudy2x.png, cloudy2x.png |
| Rain, drizzle   | rain            | rain.png / rain2x.png |
| Snow            | snow            | snow.png / snow_2x.png, snow2x.png |
| Thunderstorm    | storm           | storm.png / storm2x.png |
| Fog             | hazy            | hazy.png / hazy2x.png |

- **Small** (no 2x): 5-day forecast strip. **Large** (`2x` or `_2x` in name): current weather. If a 2x file is missing, the app scales up the small icon.
- **Night**: clear → moon; other conditions can use **`*n.png`** (small) and **`*n2x.png`** or **`*2xn.png`** (large), e.g. mostlycloudyn.png, mostlycloudyn2x.png, mostlycloudy2xn.png, hazyn2x.png.
- **Transparent background**. Suggested size: small ~64–110 px, large ~128–220 px.
- Names must match (lowercase). Missing file → app draws a simple shape.
