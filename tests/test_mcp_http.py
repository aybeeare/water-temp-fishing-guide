"""Tests for the HTTP MCP transport layer (FastMCP mounted in api/main.py).

What we cover:
  - Host header acceptance: the Railway 421 bug (host="0.0.0.0" fix)
  - MCP initialize: session ID returned, serverInfo correct
  - MCP tools/list: get_water_conditions present with correct schema
  - MCP tools/call: returns water data, strips Alexa fields
  - Integration: live Railway server is reachable and functional

The mcp_client fixture is MODULE-scoped because StreamableHTTPSessionManager
can only call .run() once per instance, and _fastmcp in api/main.py is a
module-level singleton. One TestClient is created for the whole module;
individual tests share it and httpx_mock handles per-test backend mocking.
"""
import json
import sqlite3
import pytest
import httpx
from pathlib import Path
from fastapi.testclient import TestClient


RAILWAY_HOST = "water-temp-fishing-guide-production.up.railway.app"
RAILWAY_URL  = f"https://{RAILWAY_HOST}"
SCHEMA_PATH  = Path(__file__).parent.parent / "db" / "schema.sql"

MCP_HEADERS = {
    "Content-Type": "application/json",
    "Accept":       "application/json, text/event-stream",
}

FAKE_FISHING_RESPONSE = {
    "site_id":         "8443970",
    "site_name":       "Boston Harbor, MA",
    "temp_f":          62.5,
    "temp_c":          16.9,
    "data_freshness":  "2026-07-05T12:00:00+00:00",
    "spoken_response": "The current water temperature at Boston Harbor is 62.5 degrees.",
    "sponsor_script":  "",
    "alexa_directive": {"type": "Connections.SendRequest", "name": "AddToShoppingCart", "payload": {}},
    "tides": [
        {"tide_type": "L", "tide_time": "2026-07-05 02:34", "height_ft": 1.23},
        {"tide_type": "H", "tide_time": "2026-07-05 08:45", "height_ft": 5.67},
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_sse(content: bytes) -> list[dict]:
    """Extract JSON-RPC objects from an SSE response body."""
    results = []
    for line in content.decode().splitlines():
        if line.startswith("data: "):
            results.append(json.loads(line[6:]))
    return results


def _init_payload() -> dict:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"},
        },
    }


def _do_initialize(client: TestClient, host: str = "testserver") -> str:
    """Run MCP initialize and return the mcp-session-id."""
    resp = client.post(
        "/mcp",
        json=_init_payload(),
        headers={**MCP_HEADERS, "Host": host},
    )
    assert resp.status_code == 200, f"initialize failed {resp.status_code}: {resp.text[:200]}"
    session_id = resp.headers.get("mcp-session-id", "")
    assert session_id, "Server must return mcp-session-id on initialize"
    return session_id


# ---------------------------------------------------------------------------
# Module-scoped fixture — one TestClient for the whole module.
# StreamableHTTPSessionManager.run() can only be called once per instance;
# a new TestClient per test would restart the lifespan and crash on the
# second test. Module scope starts the lifespan once and shares it.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def mcp_client(tmp_path_factory):
    import api.main as api_main

    # Minimal DB — schema only, no data needed since tool calls use httpx_mock
    db_file = str(tmp_path_factory.mktemp("mcp_http") / "test.db")
    conn = sqlite3.connect(db_file)
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()
    conn.close()

    original_db = api_main.DB_PATH
    api_main.DB_PATH = db_file

    with TestClient(api_main.app) as client:
        yield client

    api_main.DB_PATH = original_db


# ---------------------------------------------------------------------------
# Host header acceptance — regression tests for the Railway 421 bug
# ---------------------------------------------------------------------------

def test_railway_host_not_rejected(mcp_client):
    """Railway domain as Host must not return 421 after the host=0.0.0.0 fix."""
    resp = mcp_client.post(
        "/mcp",
        json=_init_payload(),
        headers={**MCP_HEADERS, "Host": RAILWAY_HOST},
    )
    assert resp.status_code != 421, "Railway Host header should no longer trigger 421"
    assert resp.status_code == 200


def test_proxy_host_accepted(mcp_client):
    """Any proxy Host header is accepted since DNS rebinding protection is off."""
    resp = mcp_client.post(
        "/mcp",
        json=_init_payload(),
        headers={**MCP_HEADERS, "Host": "server.smithery.ai"},
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# MCP initialize
# ---------------------------------------------------------------------------

def test_initialize_returns_session_id(mcp_client):
    """Server must issue an mcp-session-id for use in subsequent calls."""
    session_id = _do_initialize(mcp_client)
    assert len(session_id) > 8


def test_initialize_result_names_server(mcp_client):
    """Initialize response must identify the server as water-conditions."""
    resp = mcp_client.post("/mcp", json=_init_payload(), headers=MCP_HEADERS)
    events = _parse_sse(resp.content)
    assert events, "Initialize must return at least one SSE event"
    server_info = events[0].get("result", {}).get("serverInfo", {})
    assert server_info.get("name") == "water-conditions"


def test_initialize_declares_tools_capability(mcp_client):
    """Server must advertise the tools capability so clients know to call tools/list."""
    resp = mcp_client.post("/mcp", json=_init_payload(), headers=MCP_HEADERS)
    events = _parse_sse(resp.content)
    capabilities = events[0].get("result", {}).get("capabilities", {})
    assert "tools" in capabilities


# ---------------------------------------------------------------------------
# MCP tools/list
# ---------------------------------------------------------------------------

def test_tools_list_exposes_get_water_conditions(mcp_client):
    """tools/list must return get_water_conditions as an available tool."""
    session_id = _do_initialize(mcp_client)
    resp = mcp_client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        headers={**MCP_HEADERS, "mcp-session-id": session_id},
    )
    assert resp.status_code == 200
    events = _parse_sse(resp.content)
    tool_names = [t["name"] for t in events[0]["result"]["tools"]]
    assert "get_water_conditions" in tool_names


def test_tools_list_schema_has_location_and_coordinate_params(mcp_client):
    """The tool's inputSchema must declare location as a string param, and
    latitude/longitude as an alternative numeric input — none required
    individually, since the tool accepts location OR lat+lon."""
    session_id = _do_initialize(mcp_client)
    resp = mcp_client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        headers={**MCP_HEADERS, "mcp-session-id": session_id},
    )
    events = _parse_sse(resp.content)
    tool = next(t for t in events[0]["result"]["tools"] if t["name"] == "get_water_conditions")
    schema = tool["inputSchema"]
    assert schema["properties"]["location"]["type"] == "string"
    # latitude/longitude are Optional[float] -> FastMCP renders as anyOf[number, null]
    lat_types = {t.get("type") for t in schema["properties"]["latitude"]["anyOf"]}
    lon_types = {t.get("type") for t in schema["properties"]["longitude"]["anyOf"]}
    assert "number" in lat_types
    assert "number" in lon_types


def test_tools_list_description_mentions_water_and_temperature(mcp_client):
    """Tool description must help an LLM agent know when to invoke it."""
    session_id = _do_initialize(mcp_client)
    resp = mcp_client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        headers={**MCP_HEADERS, "mcp-session-id": session_id},
    )
    events = _parse_sse(resp.content)
    tool = next(t for t in events[0]["result"]["tools"] if t["name"] == "get_water_conditions")
    desc = tool.get("description", "").lower()
    assert "water" in desc and "temperature" in desc


# ---------------------------------------------------------------------------
# MCP tools/call
# mcp_client (module-scoped) listed before httpx_mock (function-scoped) in
# the test signature so the ASGI transport is already wired when httpx_mock
# begins intercepting new httpx clients for the inner /fishing-guide call.
# ---------------------------------------------------------------------------

def test_tools_call_returns_temp_and_location(mcp_client, httpx_mock):
    """tools/call must return temp_f and location from the backend."""
    httpx_mock.add_response(json=FAKE_FISHING_RESPONSE)
    session_id = _do_initialize(mcp_client)
    resp = mcp_client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_water_conditions", "arguments": {"location": "boston harbor"}},
        },
        headers={**MCP_HEADERS, "mcp-session-id": session_id},
    )
    assert resp.status_code == 200
    events = _parse_sse(resp.content)
    data = json.loads(events[0]["result"]["content"][0]["text"])
    assert data["temp_f"] == pytest.approx(62.5)
    assert "Boston Harbor" in data["location"]


def test_tools_call_strips_alexa_fields(mcp_client, httpx_mock):
    """Alexa-specific fields must not leak to MCP consumers."""
    httpx_mock.add_response(json=FAKE_FISHING_RESPONSE)
    session_id = _do_initialize(mcp_client)
    resp = mcp_client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_water_conditions", "arguments": {"location": "boston harbor"}},
        },
        headers={**MCP_HEADERS, "mcp-session-id": session_id},
    )
    events = _parse_sse(resp.content)
    data = json.loads(events[0]["result"]["content"][0]["text"])
    for field in ("alexa_directive", "secondary_directive", "spoken_response", "sponsor_script"):
        assert field not in data, f"Alexa field '{field}' must not reach MCP consumers"


def test_tools_call_includes_tides(mcp_client, httpx_mock):
    """Tide predictions from the backend must be present in the MCP response."""
    httpx_mock.add_response(json=FAKE_FISHING_RESPONSE)
    session_id = _do_initialize(mcp_client)
    resp = mcp_client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_water_conditions", "arguments": {"location": "boston harbor"}},
        },
        headers={**MCP_HEADERS, "mcp-session-id": session_id},
    )
    events = _parse_sse(resp.content)
    data = json.loads(events[0]["result"]["content"][0]["text"])
    assert "tides" in data
    assert len(data["tides"]) == 2
    tide_types = {t["type"] for t in data["tides"]}
    assert tide_types == {"high", "low"}


def test_tools_call_backend_404_returns_error(mcp_client, httpx_mock):
    """If the backend returns 404, the tool must return a readable error, not crash."""
    httpx_mock.add_response(status_code=404, text="Not found")
    session_id = _do_initialize(mcp_client)
    resp = mcp_client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_water_conditions", "arguments": {"location": "nowhere lake"}},
        },
        headers={**MCP_HEADERS, "mcp-session-id": session_id},
    )
    assert resp.status_code == 200
    events = _parse_sse(resp.content)
    text = events[0]["result"]["content"][0]["text"]
    assert "error" in text.lower() or "not found" in text.lower()


# ---------------------------------------------------------------------------
# Integration — live Railway server
# Run with: pytest -m integration
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_railway_mcp_initialize():
    """Live Railway endpoint must respond to MCP initialize without 421."""
    resp = httpx.post(
        f"{RAILWAY_URL}/mcp",
        json=_init_payload(),
        headers=MCP_HEADERS,
        timeout=20,
    )
    assert resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:300]}"
    assert "mcp-session-id" in resp.headers, "Missing mcp-session-id from live server"


@pytest.mark.integration
def test_railway_mcp_tools_list():
    """Live server must advertise get_water_conditions."""
    init = httpx.post(f"{RAILWAY_URL}/mcp", json=_init_payload(), headers=MCP_HEADERS, timeout=20)
    assert init.status_code == 200
    session_id = init.headers["mcp-session-id"]

    resp = httpx.post(
        f"{RAILWAY_URL}/mcp",
        json={"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        headers={**MCP_HEADERS, "mcp-session-id": session_id},
        timeout=20,
    )
    assert resp.status_code == 200
    events = _parse_sse(resp.content)
    tool_names = [t["name"] for t in events[0]["result"]["tools"]]
    assert "get_water_conditions" in tool_names


@pytest.mark.integration
def test_railway_mcp_tool_call_returns_real_data():
    """Full end-to-end: live server must return real water temp for Boston Harbor."""
    init = httpx.post(f"{RAILWAY_URL}/mcp", json=_init_payload(), headers=MCP_HEADERS, timeout=20)
    assert init.status_code == 200
    session_id = init.headers["mcp-session-id"]

    resp = httpx.post(
        f"{RAILWAY_URL}/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_water_conditions", "arguments": {"location": "boston harbor"}},
        },
        headers={**MCP_HEADERS, "mcp-session-id": session_id},
        timeout=30,
    )
    assert resp.status_code == 200
    events = _parse_sse(resp.content)
    data = json.loads(events[0]["result"]["content"][0]["text"])
    assert data.get("temp_f") is not None, "Live server must return a real temperature"
    assert "location" in data
