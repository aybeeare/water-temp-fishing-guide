# MCP Server Deployment

**Target:** Any MCP-compliant AI agent (Claude Desktop, ChatGPT, Cursor, etc.)

## Architecture

```
LLM Agent → MCP server (mcp_server/server.py) → FastAPI (Railway) → SQLite + Ingest
```

The MCP server is a lightweight stdio process the LLM host spawns locally.
It translates MCP tool calls into HTTP requests to the shared FastAPI backend.

## FastAPI (Railway) — same instance as Alexa, or separate

Environment variables:
```
USGS_API_KEY           = <key>
ASSOCIATES_TRACKING_ID = watertemperat-20
ENABLE_BAIT_SHOP       = false       ← Google Places disabled (save quota)
```

The same Railway deployment can serve both Alexa and MCP consumers simultaneously.
Set `ENABLE_BAIT_SHOP=false` if Google Places quota is a concern at scale.

## MCP Server (runs locally on user's machine)

Install:
```bash
pip install mcp httpx
```

Run:
```bash
FASTAPI_URL=https://your-app.up.railway.app python mcp_server/server.py
```

## Claude Desktop config (~/.claude/claude_desktop_config.json)

```json
{
  "mcpServers": {
    "fishing-water-guide": {
      "command": "python",
      "args": ["/path/to/water-temp-fishing-guide/mcp_server/server.py"],
      "env": {
        "FASTAPI_URL": "https://your-app.up.railway.app"
      }
    }
  }
}
```

## What agents receive

The MCP response strips Alexa-specific fields and returns clean structured data:
- `temp_f`, `temp_c`, `data_freshness`
- `species`, `tides`
- `recommended_gear` (gear name, no cart directive)
- `disambiguation` (if location is ambiguous)

No `alexa_directive`, `spoken_response`, or `sponsor_script` — the LLM generates
its own natural language from the structured data.

## RapidAPI listing (future)

The FastAPI endpoint can be listed on RapidAPI directly without the MCP layer,
allowing developers to call it as a standard REST API.
