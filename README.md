Get real-time water temperature and tide prediction data for any lake, river, ocean, bay, or beach by name or latitude/longitude coordinates. Data sourced live from NOAA CO-OPS, USGS, and seatemperature.info, with automatic nearest-station matching for coordinate inputs. Coverage includes 8,000+ named locations across North America and major international bodies, with string to coordinate geocoding for fallback.

mcp-name: io.github.aybeeare/water-conditions

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
