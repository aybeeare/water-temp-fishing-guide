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
| `get_water_conditions` | Real-time temp + tides for any lake, river, ocean, bay, or beach |
| `get_tide_predictions` | Today's high/low tide schedule for coastal locations |

Both tools accept natural language location names. The backend handles
normalization, source selection (NOAA → USGS → scraper), caching, and fallback.

**Coverage:** 8,000+ locations, 91%+ success rate on North American queries.

## FastAPI (Railway) — shared with Alexa

Environment variables:
```
FASTAPI_URL            = https://water-temp-fishing-guide-production.up.railway.app
ENABLE_BAIT_SHOP       = false    ← Google Places disabled for MCP (save quota)
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

`get_water_conditions` returns:
```json
{
  "location": "Revere Beach",
  "temp_f": 63.3,
  "temp_c": 17.39,
  "source": "noaa",
  "tides": [
    { "type": "high", "time": "06:42", "height_ft": 8.3 },
    { "type": "low",  "time": "12:58", "height_ft": 1.1 }
  ],
  "data_freshness": "2026-06-25T20:52:29Z"
}
```

`get_tide_predictions` returns:
```json
{
  "location": "Boston Harbor",
  "date": "2026-06-25",
  "tides": [
    { "type": "high", "time": "06:42", "height_ft": 8.3 },
    { "type": "low",  "time": "12:58", "height_ft": 1.1 }
  ],
  "note": "Times are local to the station. Heights in feet above MLLW."
}
```

No `alexa_directive`, `spoken_response`, or `sponsor_script` — agents generate
their own natural language from the structured data.

## Registry Listings (to submit)

- Smithery: https://smithery.ai
- Glama: https://glama.ai
- mcp.so: https://mcp.so
- Anthropic MCP registry (when available)
