Get real-time water temperature and tide prediction data for any lake, river, ocean, bay, or beach by name or latitude/longitude coordinates. Data sourced live from NOAA CO-OPS, USGS, and seatemperature.info, with automatic nearest-station matching for coordinate inputs. Coverage includes 8,000+ named locations across North America and major international bodies, with string to coordinate geocoding for fallback.

mcp-name: io.github.aybeeare/water-conditions

## Roadmap: national sensor network expansion

Today's accuracy hierarchy is USGS/NOAA (real government sensors, ground-truth
for the exact station) > seatemperature.info (best-guess aggregator, no known
dedicated sensor network, used for everywhere else via geocoding). The plan is
to extend the *first* tier — real sensor networks, wired in the same way as
USGS/NOAA — country by country, rather than leaning on the aggregator fallback
long-term. Goal: a genuine "super API" blending national sensor networks the
way this project already blends USGS + NOAA.

**Confirmed and ready to integrate (free, open, no API key required):**
- **UK Environment Agency** — best next candidate. Hydrology API (river
  flows/levels/groundwater, ~8,000 stations, 15-min resolution) + Flood
  Monitoring API (river/tide levels) — same openness and simplicity as
  USGS/NOAA, Open Government Licence.
- **France SHOM/REFMAR** — ~100 real-time tide gauges, Licence Etalab 2.0.

**Investigated, more complex integration:**
- **Copernicus Marine Service** (EU/global sea surface temperature,
  satellite + in-situ) — free and authoritative, but the bulk data products
  are scientific-grade (NetCDF via a Python toolbox) rather than simple
  per-station JSON. Has a REST "In Situ Dashboard" worth a closer look.

**Investigated, unclear near-term path:**
- **East Asia** (Japan JMA/JODC, Korea KMA) — both have relevant agencies,
  but access looked more fragmented/licensed than the UK case in an initial
  search (Japan's tide data appears to route through an authorized
  distributor, not a clean open endpoint). Needs real investigation before
  committing — not a near-term target.

North America (USGS/NOAA) + Europe (UK EA, France SHOM) covers the current
priority footprint well. Everything else stays on the geocoding +
seatemperature.info fallback until/unless a specific region's sensor network
turns out to be worth the integration effort.

## Checking MCP activity (owner only)

Every call to the `get_water_conditions` tool is logged in the database. To pull a summary from the live server:

**1. One-time setup** — set `ACTIVITY_API_KEY` in Railway (already done). Note the value somewhere safe.

**2. Run the activity script** — open a terminal in this project folder and run these two commands:

```powershell
$env:ACTIVITY_API_KEY="your-secret-here"
python scripts/activity.py
```

This prints total calls, unique locations queried, success rate, and the last 50 individual calls with timestamps and temperatures.

The `$env:` line only needs to be run once per terminal session. After that you can re-run `python scripts/activity.py` as many times as you like.
