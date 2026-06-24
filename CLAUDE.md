# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

An Alexa voice skill that delivers real-time water temperature and fishing recommendations, backed by an Amazon affiliate pipeline. A FastAPI backend orchestrates data from USGS (freshwater), NOAA CO-OPS (coastal + tides), and a fallback web scraper (seatemperature.info). Fish behavioral logic and gear ASINs live in SQLite; Alexa manages a two-turn cart confirmation flow.

## Commands

```bash
# Initialize the database (required before first run)
python db/init_db.py

# Run the API server
uvicorn api.main:app --reload

# Run all tests
pytest

# Run a single test file
pytest tests/test_api.py -v

# Run only tests that hit live external APIs
pytest -m integration

# Run tests excluding live network calls
pytest -m "not integration"
```

**Deployment:** Build command is `python db/init_db.py`; start command is `uvicorn api.main:app --host 0.0.0.0 --port $PORT` (Railway.app target).

## Deployment Modes

Full deployment details live in `deployments/alexa.md` and `deployments/mcp.md`. Summary:

| Mode | Adapter | Notes |
|---|---|---|
| Alexa | `alexa_bridge/` → Lambda | Full feature set, cart directives, bait shop |
| MCP | `mcp_server/server.py` → stdio | Strips Alexa fields, returns structured JSON for agents |
| REST | Direct HTTP | Same FastAPI endpoint, no adapter needed |

## Environment Variables

| Variable | Default | Notes |
|---|---|---|
| `DB_PATH` | `fishing.db` | |
| `ASSOCIATES_TRACKING_ID` | `watertemperat-20` | Affiliate revenue |
| `GOOGLE_PLACES_API_KEY` | — | Required for bait shop lookup |
| `DAILY_PLACES_LIMIT` | `50` | Google Places free tier guard |
| `USGS_API_KEY` | `DEMO_KEY` | Set for production throughput |
| `FASTAPI_URL` | — | Required in Lambda and MCP server env |
| `ENABLE_BAIT_SHOP` | `true` | Set `false` for MCP/agent deployments to save Places quota |

## Architecture

### Three-Tier System

```
[Alexa Device]
      ↓ ASK JSON
[Lambda: alexa_bridge/handler.py]
      ↓ HTTP GET /fishing-guide
[FastAPI: api/main.py]
      ↓
[SQLite: fishing.db]  ←  [Ingest: ingest/*.py] (on-demand or scheduled)
```

### Data Source Priority

1. **USGS** (`ingest/usgs_ingest.py`) — freshwater sites, parameter code 00010, 15-min TTL
2. **NOAA CO-OPS** (`ingest/noaa_ingest.py`) — coastal sites + tide predictions, 20-min TTL
3. **Scraper** (`ingest/sea_temp_scraper.py`) — seatemperature.info, international/fallback, 30-min TTL

Source is determined by `location_aliases.source` column (`'usgs'` | `'noaa'` | `'scrape'`). The API never picks the source at runtime — it's encoded in the alias table.

### Location Resolution Flow

User says "Lake Michigan" → Alexa normalizes → FastAPI calls `normalize_location()` → `"lake-michigan"` → `location_aliases` lookup → `site_id=04085427, source='usgs'` → check `water_cache` freshness → call ingest if stale → lookup `fishing_logic` by temp + water type + species.

### Fishing Logic Lookup

`fishing_logic` table drives all recommendations. Generic rows (no `target_species`) are fallbacks; species-specific rows take priority. Query is: find first row where `temp_min ≤ temp_f ≤ temp_max`, `water_type` matches, ordered by `(species NOT NULL) DESC`. Each row includes a primary ASIN and a behavior description used in the spoken response.

### Alexa Two-Turn Cart Flow

Session attributes drive state:
1. Turn 1: speak conditions → set `awaiting_gear_question=true`
2. Turn 2 (YesIntent): speak gear name → set `awaiting_cart_confirm=true`, `pending_asin=...`
3. Turn 3 (YesIntent): send `Connections.SendRequest` directive → Alexa app shows cart modal
4. `Connections.Response` callback → confirm add, optionally offer secondary upsell

### Disambiguation

When a location slug maps to multiple options (e.g., `"ocean-city"` → MD or NJ), the API returns a `disambiguation` list of `DisambiguationOption` objects instead of data. The `ChoiceIntent` in the skill handles the follow-up.

## Key Database Tables

- **`water_cache`** — normalized temp readings from all three sources; keyed by `site_id`
- **`fishing_logic`** — deterministic temp-range → behavior + ASIN mappings; 26 generic + 32 species-specific rows
- **`location_aliases`** — 170+ mappings of spoken names → `(site_id, source)`; this is what determines which API gets called
- **`tide_cache`** — daily high/low predictions; cleared and rewritten each day
- **`site_species`** — maps station IDs to fish species present (influences which fishing_logic row wins)
- **`bait_shop_cache`** — nearest tackle shop per station, daily TTL, driven by `ingest/places_ingest.py`

## Testing Notes

`tests/conftest.py` provides `fresh_db` and `seeded_db` fixtures that spin up isolated in-memory databases and monkeypatch `DB_PATH` across all modules. HTTP calls in unit tests use `pytest-httpx`. Integration tests (marked `@pytest.mark.integration`) require live access to USGS, NOAA, and seatemperature.info.

## Scraper Resilience

`ingest/sea_temp_scraper.py` uses a three-strategy extraction approach per page: CSS selector → body text regex → table parsing. Tides are scraped separately via regex from tide subpages. This is the most fragile part of the system — treat scraper changes carefully.

## Google Places Rate Limiting

`ingest/places_ingest.py` tracks daily call count in `api_call_log` and enforces `DAILY_PLACES_LIMIT` (default 50) to stay within the free tier. The bait shop data is cached daily per station, so calls are rare after initial population.
