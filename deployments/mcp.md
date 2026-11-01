# MCP Server Deployment

**Target:** Any MCP-compliant AI agent (Claude Desktop, ChatGPT, Cursor, etc.)

## Architecture

```
LLM Agent → MCP server (mcp_server/server.py) → FastAPI (Railway) → NOAA / USGS / seatemperature.info
```

The MCP server is a lightweight stdio process the LLM host spawns locally.
It translates MCP tool calls into HTTP requests to the shared FastAPI backend on Railway.

## Tools Exposed

| Tool | Description |
|---|---|
| `get_water_conditions` | Real-time temp + today's tides for any lake, river, ocean, bay, or beach, by name or lat/lon |

Tide predictions are included in the `get_water_conditions` response; there is
no separate tide tool. The tool accepts natural language location names. The backend handles
normalization, source selection (NOAA → USGS → scraper), caching, and fallback.

**Coverage:** 8,000+ locations, 91%+ success rate on North American queries.

## FastAPI (Railway) — shared with Alexa

Environment variables:
```
FASTAPI_URL            = https://water-temp-fishing-guide-production.up.railway.app
ENABLE_BAIT_SHOP       = true     ← leave on: Alexa shares this backend
ASSOCIATES_TRACKING_ID = watertemperat-20
```

## MCP Server Setup

Install dependencies:
```bash
pip install mcp httpx
```

Run:
```bash
FASTAPI_URL=https://water-temp-fishing-guide-production.up.railway.app python mcp_server/server.py
```

## Claude Desktop config (~/.claude/claude_desktop_config.json)

```json
{
  "mcpServers": {
    "water-conditions": {
      "command": "python",
      "args": ["/path/to/water-temp-fishing-guide/mcp_server/server.py"],
      "env": {
        "FASTAPI_URL": "https://water-temp-fishing-guide-production.up.railway.app"
      }
    }
  }
}
```

## Response Schema

The MCP server calls `/fishing-guide` with `bait_shop=false`, so agent
queries never spend Google Places quota (Alexa queries still get the shop).

The tool declares an `outputSchema` (the `WaterConditions` model in
`mcp_server/formatting.py`), and every successful result carries a matching
`structuredContent` object, plus the same JSON as text for older clients. It
also declares `readOnlyHint`/`idempotentHint`/`openWorldHint` annotations. The
hosted endpoint, the stdio package and `/.well-known/mcp/server-card.json` all
use those same definitions.

Failures (location not found, missing arguments, backend timeout) are
`isError: true` results with a plain-text message and no `structuredContent`.

A successful `get_water_conditions` result:
```json
{
  "location": "Chesapeake Bay",
  "temp_f": 63.7,
  "temp_c": 17.61,
  "source": "noaa",
  "tides": [
    { "type": "high", "time": "01:25", "height_ft": 2.49 },
    { "type": "low",  "time": "07:28", "height_ft": 0.34 }
  ],
  "observed_at": "2026-10-31T18:36:00+00:00",
  "data_freshness": "2026-10-31T18:44:03Z"
}
```

- `source` is where the temperature actually came from (`noaa`, `usgs`, or
  `seatemperature.info`). It can differ from the matched station when that
  station's sensor is offline and the scraper filled in.
- `observed_at` is when the reading was taken. Readings older than
  `STALE_READING_HOURS` (default 24) are never returned as current.
- `distance_km` appears for coordinate lookups.
- `note` appears when no current temperature is available.

Ambiguous names return a clarification instead of data:
```json
{
  "needs_clarification": true,
  "message": "'Ocean City' matches more than one place. Ask the user which one they mean, then call get_water_conditions again with that option as location.",
  "options": ["Ocean City, Maryland", "Ocean City, New Jersey"],
  "tides": []
}
```

No `alexa_directive`, `spoken_response`, or `sponsor_script` — agents generate
their own natural language from the structured data.

## Registry Listings (to submit)

- Smithery: https://smithery.ai
- Glama: https://glama.ai
- mcp.so: https://mcp.so
- Anthropic MCP registry (when available)
