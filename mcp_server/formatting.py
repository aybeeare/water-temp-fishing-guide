"""
Shared core of the get_water_conditions MCP tool, used by the stdio server
(mcp_server/server.py) and the streamable-HTTP tool mounted in api/main.py so
both declare the same schemas and answer the same way.

Results carry structuredContent that matches WaterConditions (the tool's
declared outputSchema) plus the same JSON as text for older clients. Failures
are isError results with a plain-text message and no structured content.
"""
import json
from typing import Literal, Optional

import httpx
import mcp.types as types
from pydantic import BaseModel, Field

TOOL_NAME = "get_water_conditions"

TOOL_DESCRIPTION = (
    "Get real-time water temperature and tide prediction data for any lake, river, "
    "ocean, bay, or beach by name or latitude/longitude coordinates. Data sourced "
    "live from NOAA CO-OPS, USGS, and seatemperature.info — not from training data — "
    "with automatic nearest-station matching for coordinate inputs. Coverage includes "
    "8,000+ named locations across North America and major international bodies, "
    "with string to coordinate geocoding for fallback. "
    "Use this whenever a user asks about current water temperature, beach or "
    "swimming conditions, boating, surfing, fishing, tide times, or any question "
    "requiring real-time water data. "
    "If the name is ambiguous the result has needs_clarification=true and a list of "
    "options: ask the user, then call again with the chosen option as location."
)

LOCATION_DESCRIPTION = (
    "Water body name as natural language. Examples: 'Lake Michigan', 'Revere Beach', "
    "'Chesapeake Bay', 'Cape Cod', 'Galveston Island', 'Puget Sound', 'Florida Keys', "
    "'Potomac River', 'Waikiki Beach'. Provide this OR latitude+longitude."
)
LATITUDE_DESCRIPTION = (
    "Latitude in decimal degrees, for nearest-station lookup when no location name "
    "is available. Requires longitude."
)
LONGITUDE_DESCRIPTION = (
    "Longitude in decimal degrees, for nearest-station lookup when no location name "
    "is available. Requires latitude."
)

INPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "location":  {"type": "string", "description": LOCATION_DESCRIPTION},
        "latitude":  {"type": "number", "minimum": -90,  "maximum": 90,  "description": LATITUDE_DESCRIPTION},
        "longitude": {"type": "number", "minimum": -180, "maximum": 180, "description": LONGITUDE_DESCRIPTION},
    },
}

# Read-only lookup against live outside data sources.
TOOL_ANNOTATIONS = types.ToolAnnotations(
    title="Water Conditions",
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=True,
)

# Ask the backend to skip the bait shop lookup: agents never see it, and each
# lookup spends Google Places quota.
QUERY_EXTRAS = {"bait_shop": "false"}


# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------

class Tide(BaseModel):
    type:      Literal["high", "low"]
    time:      str             = Field(description="Local time at the station, HH:MM")
    height_ft: Optional[float] = Field(None, description="Predicted height in feet")


class WaterConditions(BaseModel):
    """A reading for the requested place, or a request to clarify which place was meant."""

    location: Optional[str] = Field(None, description="Name of the station or place the reading is for")
    temp_f: Optional[float] = Field(None, description="Water temperature, °F. Absent when no current reading exists (see note)")
    temp_c: Optional[float] = Field(None, description="Water temperature, °C")
    temp_f_min: Optional[float] = Field(None, description="Low end of today's range across the water body, °F")
    temp_f_max: Optional[float] = Field(None, description="High end of today's range across the water body, °F")
    source: Optional[Literal["usgs", "noaa", "seatemperature.info", "unknown"]] = Field(
        None, description="Where the temperature came from")
    tides: list[Tide] = Field(default_factory=list, description="Today's high/low tide predictions; empty for non-tidal water")
    observed_at: Optional[str] = Field(None, description="ISO-8601 UTC time the reading was taken")
    data_freshness: Optional[str] = Field(None, description="ISO-8601 UTC time the reading was fetched")
    distance_km: Optional[float] = Field(None, description="Distance from the requested coordinates to the station")
    coverage_note: Optional[str] = Field(None, description="Present when temp_f_min/temp_f_max describe a whole water body")
    note: Optional[str] = Field(None, description="Why there is no temperature, when temp_f is absent")
    needs_clarification: bool = Field(False, description="True when the name matched several places; see options")
    message: Optional[str] = Field(None, description="What to do next when needs_clarification is true")
    options: Optional[list[str]] = Field(None, description="Place names to choose from; call again with one as location")


OUTPUT_SCHEMA = WaterConditions.model_json_schema()


# ---------------------------------------------------------------------------
# Backend call
# ---------------------------------------------------------------------------

class ConditionsError(Exception):
    """A lookup that failed; the message is safe to show the agent."""


def query_params(location: str, latitude: Optional[float], longitude: Optional[float],
                 client: Optional[str] = None, agent: Optional[str] = None) -> dict:
    """client/agent tag the request in the backend's query log."""
    base = {"location": location} if location else {"lat": latitude, "lon": longitude}
    tags = {k: v for k, v in (("client", client), ("agent", agent)) if v}
    return {**base, **QUERY_EXTRAS, **tags}


def validate_arguments(location: str, latitude: Optional[float], longitude: Optional[float]) -> None:
    if not location and (latitude is None or longitude is None):
        raise ConditionsError("Provide location, or both latitude and longitude.")


async def fetch_conditions(base_url: str, params: dict, timeout: float = 15) -> dict:
    """GET /fishing-guide. Raises ConditionsError with an agent-readable message."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.get(f"{base_url}/fishing-guide", params=params)
        except httpx.TimeoutException:
            raise ConditionsError("Request timed out — the data source may be temporarily slow; try again.")
        except httpx.HTTPError as e:
            raise ConditionsError(f"Request failed: {type(e).__name__}")
    if resp.status_code == 404:
        raise ConditionsError("Location not found. Try a more specific name or nearby coordinates.")
    if resp.status_code >= 400:
        raise ConditionsError(f"Backend error {resp.status_code}")
    return resp.json()


# ---------------------------------------------------------------------------
# Response shaping
# ---------------------------------------------------------------------------

def source_label(data: dict) -> str:
    """Prefer the backend's explicit source; infer from the station ID for older backends."""
    if data.get("source"):
        return data["source"]
    site_id = str(data.get("site_id") or "")
    if not site_id:
        return "unknown"
    if site_id.isdigit() and len(site_id) == 7:
        return "noaa"
    if site_id.isdigit() and len(site_id) >= 8:
        return "usgs"
    return "seatemperature.info"


def format_conditions(data: dict, query: str) -> dict:
    """Backend response → dict matching WaterConditions (None fields dropped)."""
    options = data.get("disambiguation")
    if options:
        return {
            "needs_clarification": True,
            "message": (
                f"'{query}' matches more than one place. Ask the user which one they "
                f"mean, then call {TOOL_NAME} again with that option as location."
            ),
            "options": [o["label"] for o in options],
            "tides": [],
        }

    tide_list = [
        {
            "type":      "high" if t["tide_type"] == "H" else "low",
            "time":      t["tide_time"].split(" ")[-1] if " " in t["tide_time"] else t["tide_time"],
            "height_ft": t["height_ft"],
        }
        for t in (data.get("tides") or [])
    ]

    result = {
        "location":       data.get("site_name", query),
        "temp_f":         data.get("temp_f"),
        "temp_c":         data.get("temp_c"),
        "temp_f_min":     data.get("temp_f_min"),
        "temp_f_max":     data.get("temp_f_max"),
        "source":         source_label(data),
        "tides":          tide_list,
        "observed_at":    data.get("observed_at"),
        "data_freshness": data.get("data_freshness"),
        "distance_km":    data.get("distance_km"),
    }
    if data.get("temp_f_min") and data.get("temp_f_max"):
        result["coverage_note"] = "Range reflects readings across the water body, not a single point."
    if data.get("temp_f") is None:
        result["note"] = data.get("spoken_response") or "No current temperature reading is available."

    return {k: v for k, v in result.items() if v is not None}


def success_result(conditions: dict) -> types.CallToolResult:
    """Structured result, checked against the declared output schema."""
    WaterConditions.model_validate(conditions)
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=json.dumps(conditions, indent=2))],
        structuredContent=conditions,
    )


def error_result(message: str) -> types.CallToolResult:
    return types.CallToolResult(
        content=[types.TextContent(type="text", text=message)],
        isError=True,
    )


async def get_conditions(base_url: str, location: str, latitude: Optional[float],
                         longitude: Optional[float], client: Optional[str] = None,
                         agent: Optional[str] = None) -> types.CallToolResult:
    """The whole tool: validate, call the backend, shape the result."""
    location = (location or "").strip()
    try:
        validate_arguments(location, latitude, longitude)
        data = await fetch_conditions(base_url, query_params(location, latitude, longitude, client, agent))
    except ConditionsError as e:
        return error_result(str(e))
    return success_result(format_conditions(data, location or f"{latitude},{longitude}"))
