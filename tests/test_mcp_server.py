"""
Tests for mcp_server/server.py — simulates the two-step MCP handshake
without a real LLM agent.

Step 1 (capability discovery): verify list_tools() returns the correct
        tool definition so an LLM agent can understand what we offer.

Step 2 (tool invocation): verify call_tool() correctly calls the FastAPI
        backend, strips Alexa-specific fields, and returns valid JSON.
"""
import json
import os
import pytest
from pytest_httpx import HTTPXMock

mcp = pytest.importorskip("mcp", reason="mcp package not installed — run: pip install mcp")

import mcp.types as types
from mcp_server.server import list_tools, call_tool


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

FAKE_API_RESPONSE = {
    "site_id":          "8443970",
    "site_name":        "Boston Harbor",
    "temp_f":           58.6,
    "temp_c":           14.78,
    "data_freshness":   "2026-06-24T18:00:00+00:00",
    "spoken_response":  "The current water temperature at Boston Harbor is 58.6 degrees.",
    "sponsor_script":   "",
    "recommended_gear": "Berkley Gulp Saltwater Shrimp",
    "secondary_gear":   None,
    "nearby_shop":      {"name": "P & J Bait Shop", "address": "1397 Dorchester Ave"},
    "tides": [
        {"tide_type": "L", "tide_time": "2026-06-24 01:41", "height_ft": 1.16},
        {"tide_type": "H", "tide_time": "2026-06-24 07:56", "height_ft": 8.7},
    ],
    "alexa_directive":      {"type": "Connections.SendRequest", "name": "AddToShoppingCart", "payload": {}},
    "secondary_directive":  None,
    "species":              ["flounder", "striped_bass"],
    "disambiguation":       None,
}

ALEXA_ONLY_FIELDS = {"alexa_directive", "secondary_directive", "spoken_response", "sponsor_script",
                     "nearby_shop", "recommended_gear"}


# ---------------------------------------------------------------------------
# Step 1 — Capability discovery
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_handshake_step1_returns_one_tool():
    """LLM asks 'what tools do you have?' — we must return exactly one."""
    tools = await list_tools()
    assert len(tools) == 1


@pytest.mark.asyncio
async def test_handshake_step1_tool_name():
    """Tool name must be stable — LLM agents reference it by name in code."""
    tools = await list_tools()
    assert tools[0].name == "get_water_conditions"


@pytest.mark.asyncio
async def test_handshake_step1_tool_has_description():
    """Description is what the LLM reads to decide whether to call us."""
    tools = await list_tools()
    desc = tools[0].description
    assert desc and len(desc) > 20


@pytest.mark.asyncio
async def test_handshake_step1_input_schema():
    """Input schema must declare location as a string param, and
    latitude/longitude as an alternative numeric input — none required
    individually, since the tool accepts location OR lat+lon."""
    tools = await list_tools()
    schema = tools[0].inputSchema
    assert schema["type"] == "object"
    assert "location" in schema["properties"]
    assert schema["properties"]["location"]["type"] == "string"
    assert schema["properties"]["latitude"]["type"] == "number"
    assert schema["properties"]["longitude"]["type"] == "number"


# ---------------------------------------------------------------------------
# Step 2 — Tool invocation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_handshake_step2_returns_text_content(httpx_mock: HTTPXMock):
    """call_tool() must return a list of TextContent — the MCP wire format."""
    httpx_mock.add_response(json=FAKE_API_RESPONSE)
    result = await call_tool("get_water_conditions", {"location": "boston harbor"})
    assert not result.isError
    assert len(result.content) == 1
    assert result.content[0].type == "text"


@pytest.mark.asyncio
async def test_handshake_step2_response_is_valid_json(httpx_mock: HTTPXMock):
    """The TextContent payload must be valid JSON the LLM can parse."""
    httpx_mock.add_response(json=FAKE_API_RESPONSE)
    result = await call_tool("get_water_conditions", {"location": "boston harbor"})
    data = json.loads(result.content[0].text)
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_handshake_step2_alexa_fields_stripped(httpx_mock: HTTPXMock):
    """Alexa cart directives and spoken_response must not reach LLM agents."""
    httpx_mock.add_response(json=FAKE_API_RESPONSE)
    result = await call_tool("get_water_conditions", {"location": "boston harbor"})
    data = json.loads(result.content[0].text)
    for field in ALEXA_ONLY_FIELDS:
        assert field not in data, f"Alexa field '{field}' should be stripped from MCP response"


@pytest.mark.asyncio
async def test_handshake_step2_core_fields_present(httpx_mock: HTTPXMock):
    """Core fishing data fields must be present for the LLM to reason over."""
    httpx_mock.add_response(json=FAKE_API_RESPONSE)
    result = await call_tool("get_water_conditions", {"location": "boston harbor"})
    data = json.loads(result.content[0].text)
    for field in ("temp_f", "temp_c", "source", "tides", "data_freshness"):
        assert field in data, f"Expected field '{field}' in MCP response"


@pytest.mark.asyncio
async def test_handshake_step2_empty_location_returns_error():
    """Empty location must return a clean error string, not raise an exception."""
    result = await call_tool("get_water_conditions", {"location": ""})
    assert result.isError
    assert result.structuredContent is None
    assert "provide location" in result.content[0].text.lower()


@pytest.mark.asyncio
async def test_handshake_step2_disambiguation_returns_options(httpx_mock: HTTPXMock):
    """Ambiguous names must surface the choices so the agent can ask the user."""
    httpx_mock.add_response(json={
        **FAKE_API_RESPONSE, "temp_f": None, "temp_c": None, "tides": None,
        "disambiguation": [
            {"label": "Ocean City, Maryland",   "slug": "/a"},
            {"label": "Ocean City, New Jersey", "slug": "/b"},
        ],
    })
    result = await call_tool("get_water_conditions", {"location": "ocean city"})
    data = json.loads(result.content[0].text)
    assert data["needs_clarification"] is True
    assert data["options"] == ["Ocean City, Maryland", "Ocean City, New Jersey"]
    request = httpx_mock.get_requests()[0]
    assert request.url.params["bait_shop"] == "false"


@pytest.mark.asyncio
async def test_handshake_step2_unknown_tool_raises():
    """Unknown tool names must raise — LLM should never call a tool we didn't advertise."""
    with pytest.raises(ValueError, match="Unknown tool"):
        await call_tool("get_weather_forecast", {"location": "boston"})


@pytest.mark.asyncio
async def test_handshake_step2_api_error_returns_message(httpx_mock: HTTPXMock):
    """If the FastAPI backend returns an error, return a readable message not a crash."""
    httpx_mock.add_response(status_code=404, text="Not found")
    result = await call_tool("get_water_conditions", {"location": "nowhere"})
    assert result.isError
    assert "not found" in result.content[0].text.lower()


# ---------------------------------------------------------------------------
# Output schema — callers type-check structuredContent against it
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tool_declares_output_schema_and_annotations():
    tool = (await list_tools())[0]
    assert tool.outputSchema["type"] == "object"
    assert {"temp_f", "source", "tides", "needs_clarification", "options"} <= set(tool.outputSchema["properties"])
    assert tool.annotations.readOnlyHint is True
    assert tool.inputSchema["properties"]["latitude"]["maximum"] == 90


@pytest.mark.asyncio
async def test_structured_content_matches_output_schema(httpx_mock: HTTPXMock):
    import jsonschema
    schema = (await list_tools())[0].outputSchema
    httpx_mock.add_response(json=FAKE_API_RESPONSE)
    result = await call_tool("get_water_conditions", {"location": "boston harbor"})
    jsonschema.validate(result.structuredContent, schema)
    assert json.loads(result.content[0].text) == result.structuredContent
    assert result.structuredContent["temp_f"] == 58.6


@pytest.mark.asyncio
async def test_clarification_matches_output_schema(httpx_mock: HTTPXMock):
    import jsonschema
    schema = (await list_tools())[0].outputSchema
    httpx_mock.add_response(json={**FAKE_API_RESPONSE, "temp_f": None, "disambiguation": [
        {"label": "Ocean City, Maryland", "slug": "/a"}]})
    result = await call_tool("get_water_conditions", {"location": "ocean city"})
    jsonschema.validate(result.structuredContent, schema)
    assert result.structuredContent["needs_clarification"] is True


@pytest.mark.asyncio
async def test_server_dispatch_validates_output(httpx_mock: HTTPXMock):
    """Through the real request handler, which enforces the declared schema."""
    httpx_mock.add_response(json=FAKE_API_RESPONSE)
    from mcp_server.server import server
    await server.request_handlers[types.ListToolsRequest](types.ListToolsRequest(method="tools/list"))
    req = types.CallToolRequest(method="tools/call", params=types.CallToolRequestParams(
        name="get_water_conditions", arguments={"location": "boston harbor"}))
    res = (await server.request_handlers[types.CallToolRequest](req)).root
    assert not res.isError
    assert res.structuredContent["location"] == "Boston Harbor"


# ---------------------------------------------------------------------------
# Integration — calls live Railway deployment
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.asyncio
async def test_mcp_integration_full_handshake():
    """Full two-step handshake against the live Railway deployment."""
    fastapi_url = os.environ.get("FASTAPI_URL", "")
    if not fastapi_url:
        pytest.skip("FASTAPI_URL not set — skipping live MCP integration test")

    # Step 1
    tools = await list_tools()
    assert tools[0].name == "get_water_conditions"

    # Step 2
    result = await call_tool("get_water_conditions", {"location": "boston harbor"})
    data = json.loads(result.content[0].text)
    assert data.get("temp_f") is not None
    for field in ALEXA_ONLY_FIELDS:
        assert field not in data
