"""
MCP server — exposes real-time water temperature, tide, and conditions data
as tools callable by Claude, ChatGPT, Cursor, and any MCP-compliant agent.

Data sources (in priority order):
  1. NOAA CO-OPS API      — US coastal stations, authoritative sensor data
  2. USGS NWIS API        — US freshwater rivers and lakes
  3. seatemperature.info  — global coastal/beach coverage, scraped fallback

The FastAPI backend on Railway handles all data fetching, caching, and
fallback logic. This server is a protocol translator: MCP in, HTTP out.

Run locally:
    pip install mcp httpx
    FASTAPI_URL=https://water-temp-fishing-guide-production.up.railway.app python mcp_server/server.py

Connect from Claude Desktop (~/.claude_desktop_config.json):
    {
      "mcpServers": {
        "water-conditions": {
          "command": "python",
          "args": ["/path/to/mcp_server/server.py"],
          "env": { "FASTAPI_URL": "https://water-temp-fishing-guide-production.up.railway.app" }
        }
      }
    }
"""
import asyncio
import json
import os

import httpx
import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

FASTAPI_URL = os.environ.get(
    "FASTAPI_URL",
    "https://water-temp-fishing-guide-production.up.railway.app"
)

server = Server("water-conditions")

# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS = [
    types.Tool(
        name="get_water_conditions",
        description=(
            "Get real-time water temperature and tide predictions for any lake, river, "
            "ocean, bay, or beach location. Data sourced live from NOAA CO-OPS, USGS, "
            "and seatemperature.info — not from training data. "
            "Coverage: 8,000+ locations across North America and major international bodies. "
            "Use this tool whenever a user asks about: current water temperature, beach or "
            "swimming conditions, boating conditions, surfing conditions, fishing conditions, "
            "tide times, or any question requiring real-time water data."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": (
                        "Water body name as natural language. "
                        "Examples: 'Lake Michigan', 'Revere Beach', 'Chesapeake Bay', "
                        "'Cape Cod', 'Galveston Island', 'Puget Sound', 'Florida Keys', "
                        "'Potomac River', 'Waikiki Beach', 'Gulf of Mexico'."
                    ),
                }
            },
            "required": ["location"],
        },
    ),
    types.Tool(
        name="get_tide_predictions",
        description=(
            "Get today's high and low tide predictions for a coastal location. "
            "Returns tide type (high/low), time, and height in feet. "
            "Data sourced from NOAA CO-OPS tide prediction API for US coastal stations, "
            "with seatemperature.info as fallback for international locations. "
            "Use this tool when a user specifically asks about tide times, tide schedule, "
            "or high/low tide for a beach or coastal location."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": (
                        "Coastal location name. "
                        "Examples: 'Sandy Hook NJ', 'Boston Harbor', 'Key West', "
                        "'San Francisco Bay', 'Puget Sound', 'Cape Hatteras'."
                    ),
                }
            },
            "required": ["location"],
        },
    ),
]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "get_water_conditions":
        return await _get_water_conditions(arguments)
    if name == "get_tide_predictions":
        return await _get_tide_predictions(arguments)
    raise ValueError(f"Unknown tool: {name}")


# ---------------------------------------------------------------------------
# get_water_conditions
# ---------------------------------------------------------------------------

async def _get_water_conditions(arguments: dict) -> list[types.TextContent]:
    location = arguments.get("location", "").strip()
    if not location:
        return [_error("location is required")]

    data, err = await _fetch(f"{FASTAPI_URL}/fishing-guide", {"location": location})
    if err:
        return [_error(err)]

    tides = data.get("tides") or []
    tide_list = [
        {
            "type":      "high" if t["tide_type"] == "H" else "low",
            "time":      t["tide_time"].split(" ")[-1] if " " in t["tide_time"] else t["tide_time"],
            "height_ft": t["height_ft"],
        }
        for t in tides
    ]

    result = {
        "location":       data.get("site_name", location),
        "temp_f":         data.get("temp_f"),
        "temp_c":         data.get("temp_c"),
        "temp_f_min":     data.get("temp_f_min"),
        "temp_f_max":     data.get("temp_f_max"),
        "source":         _source_label(data.get("site_id", "")),
        "tides":          tide_list,
        "data_freshness": data.get("data_freshness"),
        "coverage_note":  _coverage_note(data),
    }

    # Remove None values for clean output
    result = {k: v for k, v in result.items() if v is not None}

    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


# ---------------------------------------------------------------------------
# get_tide_predictions
# ---------------------------------------------------------------------------

async def _get_tide_predictions(arguments: dict) -> list[types.TextContent]:
    location = arguments.get("location", "").strip()
    if not location:
        return [_error("location is required")]

    data, err = await _fetch(f"{FASTAPI_URL}/fishing-guide", {"location": location})
    if err:
        return [_error(err)]

    tides = data.get("tides") or []
    if not tides:
        return [_error(
            f"No tide predictions available for {location}. "
            "Tide data is only available for coastal locations with NOAA stations."
        )]

    tide_list = [
        {
            "type":      "high" if t["tide_type"] == "H" else "low",
            "time":      t["tide_time"].split(" ")[-1] if " " in t["tide_time"] else t["tide_time"],
            "height_ft": t["height_ft"],
        }
        for t in tides
    ]

    result = {
        "location": data.get("site_name", location),
        "date":     _today(),
        "tides":    tide_list,
        "note":     "Times are local to the station. Heights in feet above MLLW.",
    }

    return [types.TextContent(type="text", text=json.dumps(result, indent=2))]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _fetch(url: str, params: dict) -> tuple[dict, str]:
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 404:
                return {}, f"Location not found. Try a more specific name or nearby location."
            resp.raise_for_status()
            return resp.json(), None
        except httpx.HTTPStatusError as e:
            return {}, f"API error {e.response.status_code}"
        except httpx.TimeoutException:
            return {}, "Request timed out — the data source may be temporarily slow"
        except Exception as e:
            return {}, f"Request failed: {type(e).__name__}"


def _error(msg: str) -> types.TextContent:
    return types.TextContent(type="text", text=json.dumps({"error": msg}))


def _source_label(site_id: str) -> str:
    if not site_id:
        return "unknown"
    if site_id.isdigit() and len(site_id) == 7:
        return "noaa"
    if site_id.isdigit() and len(site_id) >= 8:
        return "usgs"
    return "seatemperature.info"


def _coverage_note(data: dict) -> str | None:
    if data.get("temp_f_min") and data.get("temp_f_max"):
        return "Range reflects readings across the water body, not a single point."
    return None


def _today() -> str:
    from datetime import date
    return date.today().isoformat()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
