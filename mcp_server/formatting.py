"""
Turns a /fishing-guide API response into the agent-facing JSON returned by the
get_water_conditions MCP tool. Shared by the stdio server (mcp_server/server.py)
and the streamable-HTTP tool mounted in api/main.py so both answer the same way.
"""
from typing import Optional

# Ask the backend to skip the bait shop lookup: agents never see it, and each
# lookup spends Google Places quota.
QUERY_EXTRAS = {"bait_shop": "false"}


def query_params(location: str, latitude: Optional[float], longitude: Optional[float]) -> dict:
    base = {"location": location} if location else {"lat": latitude, "lon": longitude}
    return {**base, **QUERY_EXTRAS}


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
    options = data.get("disambiguation")
    if options:
        labels = [o["label"] for o in options]
        return {
            "needs_clarification": True,
            "message": (
                f"'{query}' matches more than one place. Ask the user which one they "
                "mean, then call get_water_conditions again with that option as location."
            ),
            "options": labels,
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
