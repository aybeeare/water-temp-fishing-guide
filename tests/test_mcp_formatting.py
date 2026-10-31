"""Tests for mcp_server/formatting.py — the agent-facing response shape."""
from mcp_server.formatting import format_conditions, query_params, source_label


def test_query_params_skip_bait_shop():
    assert query_params("Lake Tahoe", None, None) == {"location": "Lake Tahoe", "bait_shop": "false"}
    assert query_params("", 42.0, -71.0) == {"lat": 42.0, "lon": -71.0, "bait_shop": "false"}


def test_disambiguation_becomes_clarification():
    data = {
        "site_id": "ocean-city", "site_name": "Ocean City", "temp_f": None,
        "disambiguation": [
            {"label": "Ocean City, Maryland",   "slug": "/united-states/maryland/ocean-city-water-temperature.html"},
            {"label": "Ocean City, New Jersey", "slug": "/united-states/new-jersey/ocean-city-water-temperature.html"},
        ],
    }
    result = format_conditions(data, "Ocean City")
    assert result["needs_clarification"] is True
    assert result["options"] == ["Ocean City, Maryland", "Ocean City, New Jersey"]
    assert "temp_f" not in result


def test_explicit_source_beats_site_id_inference():
    # NOAA station matched, but its sensor was offline and the scraper filled in
    assert source_label({"site_id": "8443970", "source": "seatemperature.info"}) == "seatemperature.info"
    assert source_label({"site_id": "8443970"}) == "noaa"
    assert source_label({"site_id": "04085427"}) == "usgs"


def test_missing_temperature_includes_note():
    data = {"site_id": "x", "site_name": "X", "temp_f": None, "temp_c": None,
            "spoken_response": "The sensor at X is currently offline."}
    result = format_conditions(data, "X")
    assert result["note"] == "The sensor at X is currently offline."


def test_normal_response_shape():
    data = {"site_id": "8573364", "site_name": "Chesapeake Bay", "temp_f": 63.7, "temp_c": 17.61,
            "source": "noaa", "observed_at": "2026-10-31T18:36:00+00:00",
            "data_freshness": "2026-10-31T18:44:03+00:00",
            "tides": [{"tide_type": "H", "tide_time": "2026-10-31 01:25", "height_ft": 2.49}],
            "alexa_directive": {"x": 1}, "spoken_response": "..."}
    result = format_conditions(data, "Chesapeake Bay")
    assert result["tides"] == [{"type": "high", "time": "01:25", "height_ft": 2.49}]
    assert result["observed_at"] == "2026-10-31T18:36:00+00:00"
    assert "alexa_directive" not in result and "note" not in result
