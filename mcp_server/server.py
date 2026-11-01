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
    pip install water-conditions-mcp
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
import os

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

try:
    from mcp_server import formatting
except ImportError:  # run directly as `python mcp_server/server.py`
    import formatting

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
        name=formatting.TOOL_NAME,
        title="Water Conditions",
        description=formatting.TOOL_DESCRIPTION,
        inputSchema=formatting.INPUT_SCHEMA,
        outputSchema=formatting.OUTPUT_SCHEMA,
        annotations=formatting.TOOL_ANNOTATIONS,
    ),
]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> types.CallToolResult:
    if name != formatting.TOOL_NAME:
        raise ValueError(f"Unknown tool: {name}")
    return await formatting.get_conditions(
        FASTAPI_URL,
        arguments.get("location", ""),
        arguments.get("latitude"),
        arguments.get("longitude"),
        client="mcp-stdio",
        agent=_client_name(),
    )


def _client_name() -> str | None:
    """Name the host reported at initialize (e.g. 'claude-ai'), for the backend's query log."""
    try:
        info = server.request_context.session.client_params.clientInfo
        return f"{info.name}/{info.version}" if info.version else info.name
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def _main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream,
            server.create_initialization_options()
        )


def main():
    asyncio.run(_main())


if __name__ == "__main__":
    main()
