"""
MCP server adapter — exposes the fishing guide API as a tool callable by
Claude, ChatGPT, Cursor, and any other MCP-compliant agent.

The FastAPI backend does all the real work. This is just a protocol translator
(the same role Lambda plays for Alexa).

Run locally:
    pip install mcp httpx
    FASTAPI_URL=https://your-app.up.railway.app python mcp_server/server.py

The MCP host (e.g. Claude Desktop) connects to this process via stdio.
"""
import asyncio
import os
import httpx
import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

FASTAPI_URL = os.environ.get("FASTAPI_URL", "http://localhost:8000")

server = Server("fishing-water-guide")


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_fishing_conditions",
            description=(
                "Get live water temperature, fish behavior, tide predictions, and gear "
                "recommendations for a fishing location. Uses real-time USGS, NOAA, and "
                "web data — not training data. Call this whenever a user asks about "
                "current fishing conditions, water temperature, or what to fish with."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": (
                            "The fishing location as a natural language name. "
                            "Examples: 'Lake Michigan', 'Boston Harbor', 'Florida Keys', "
                            "'Potomac River', 'Puget Sound', 'Amazon River'."
                        ),
                    }
                },
                "required": ["location"],
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name != "get_fishing_conditions":
        raise ValueError(f"Unknown tool: {name}")

    location = arguments.get("location", "").strip()
    if not location:
        return [types.TextContent(type="text", text="Error: location is required.")]

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.get(
                f"{FASTAPI_URL}/fishing-guide",
                params={"location": location},
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            return [types.TextContent(type="text", text=f"API error {e.response.status_code}: {e.response.text}")]
        except Exception as e:
            return [types.TextContent(type="text", text=f"Request failed: {e}")]

    # Strip Alexa-specific fields — agents don't need cart directives
    agent_view = {k: v for k, v in data.items() if k not in (
        "alexa_directive", "secondary_directive", "spoken_response", "sponsor_script"
    )}

    import json
    return [types.TextContent(type="text", text=json.dumps(agent_view, indent=2))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
