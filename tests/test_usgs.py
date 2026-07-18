"""Unit tests for ingest/usgs_ingest.py"""
import os
import sqlite3
from datetime import datetime, timezone, timedelta

import pytest
from pytest_httpx import HTTPXMock

import ingest.usgs_ingest as usgs_mod
from ingest.usgs_ingest import (
    celsius_to_fahrenheit,
    parse_usgs_response,
    sites_needing_refresh,
    fetch_usgs,
    upsert_cache,
    USGS_IV_URL,
    build_bbox,
    parse_usgs_rdb,
    fetch_usgs_sites_in_bbox,
    find_nearest_usgs_site,
    USGS_SITE_SERVICE_URL,
)

# ---------------------------------------------------------------------------
# Pure math
# ---------------------------------------------------------------------------

def test_celsius_to_fahrenheit_freezing():
    assert celsius_to_fahrenheit(0) == 32.0

def test_celsius_to_fahrenheit_boiling():
    assert celsius_to_fahrenheit(100) == 212.0

def test_celsius_to_fahrenheit_body_temp():
    assert celsius_to_fahrenheit(37) == 98.6

def test_celsius_to_fahrenheit_typical_lake():
    result = celsius_to_fahrenheit(18.5)
    assert result == pytest.approx(65.3, abs=0.1)

# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

SAMPLE_USGS_RESPONSE = {
    "value": {
        "timeSeries": [
            {
                "sourceInfo": {
                    "siteName": "MISSISSIPPI RIVER AT ST. LOUIS, MO",
                    "siteCode": [{"value": "07010000"}],
                },
                "values": [
                    {"value": [{"value": "18.5", "dateTime": "2024-06-23T14:00:00.000-05:00"}]}
                ],
            }
        ]
    }
}

def test_parse_usgs_response_normal():
    results = parse_usgs_response(SAMPLE_USGS_RESPONSE)
    assert len(results) == 1
    r = results[0]
    assert r["site_id"]   == "07010000"
    assert r["site_name"] == "MISSISSIPPI RIVER AT ST. LOUIS, MO"
    assert r["temp_c"]    == pytest.approx(18.5, abs=0.01)
    assert r["temp_f"]    == pytest.approx(65.3, abs=0.1)

def test_parse_usgs_response_offline_sensor():
    data = {
        "value": {"timeSeries": [{
            "sourceInfo": {"siteName": "BROKEN GAUGE", "siteCode": [{"value": "99999999"}]},
            "values": [{"value": [{"value": "-999999", "dateTime": "2024-06-23T00:00:00.000Z"}]}],
        }]}
    }
    results = parse_usgs_response(data)
    assert len(results) == 1
    assert results[0]["temp_f"] is None
    assert results[0]["temp_c"] is None

def test_parse_usgs_response_empty_values():
    data = {
        "value": {"timeSeries": [{
            "sourceInfo": {"siteName": "EMPTY GAUGE", "siteCode": [{"value": "11111111"}]},
            "values": [{"value": []}],
        }]}
    }
    results = parse_usgs_response(data)
    assert results == []

def test_parse_usgs_response_multiple_sites():
    data = {
        "value": {"timeSeries": [
            {
                "sourceInfo": {"siteName": "SITE A", "siteCode": [{"value": "00000001"}]},
                "values": [{"value": [{"value": "10.0", "dateTime": "2024-06-23T00:00:00Z"}]}],
            },
            {
                "sourceInfo": {"siteName": "SITE B", "siteCode": [{"value": "00000002"}]},
                "values": [{"value": [{"value": "25.0", "dateTime": "2024-06-23T00:00:00Z"}]}],
            },
        ]}
    }
    results = parse_usgs_response(data)
    assert len(results) == 2
    assert results[0]["temp_f"] == pytest.approx(50.0, abs=0.1)
    assert results[1]["temp_f"] == pytest.approx(77.0, abs=0.1)

# ---------------------------------------------------------------------------
# Cache staleness
# ---------------------------------------------------------------------------

def test_sites_needing_refresh_all_missing(db_path):
    conn = sqlite3.connect(db_path)
    stale = sites_needing_refresh(conn, ["04085427", "07010000"])
    conn.close()
    assert set(stale) == {"04085427", "07010000"}

def test_sites_needing_refresh_fresh(db_path):
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO water_cache (site_id, site_name, temp_f, temp_c, fetched_at) VALUES (?,?,?,?,?)",
        ("04085427", "Lake Michigan", 68.0, 20.0, now),
    )
    conn.commit()
    stale = sites_needing_refresh(conn, ["04085427"])
    conn.close()
    assert stale == []

def test_sites_needing_refresh_stale(db_path):
    old = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO water_cache (site_id, site_name, temp_f, temp_c, fetched_at) VALUES (?,?,?,?,?)",
        ("04085427", "Lake Michigan", 68.0, 20.0, old),
    )
    conn.commit()
    stale = sites_needing_refresh(conn, ["04085427"])
    conn.close()
    assert "04085427" in stale

# ---------------------------------------------------------------------------
# HTTP fetch (mocked)
# ---------------------------------------------------------------------------

def test_fetch_usgs_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=SAMPLE_USGS_RESPONSE)
    result = fetch_usgs(["07010000"])
    assert result is not None
    assert "value" in result

def test_fetch_usgs_http_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=503)
    result = fetch_usgs(["07010000"])
    assert result is None

# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------

def test_upsert_cache_writes(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    records = [{"site_id": "07010000", "site_name": "Mississippi River", "temp_f": 75.0, "temp_c": 23.9, "raw_datetime": "2024-06-23T14:00:00Z"}]
    upsert_cache(conn, records)
    row = conn.execute("SELECT * FROM water_cache WHERE site_id = '07010000'").fetchone()
    conn.close()
    assert row["temp_f"] == pytest.approx(75.0, abs=0.01)

def test_upsert_cache_overwrites(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    records = [{"site_id": "07010000", "site_name": "Mississippi", "temp_f": 70.0, "temp_c": 21.1, "raw_datetime": None}]
    upsert_cache(conn, records)
    records[0]["temp_f"] = 72.0
    upsert_cache(conn, records)
    row = conn.execute("SELECT temp_f FROM water_cache WHERE site_id = '07010000'").fetchone()
    conn.close()
    assert row["temp_f"] == pytest.approx(72.0, abs=0.01)


# ---------------------------------------------------------------------------
# Coordinate-based spatial search
# ---------------------------------------------------------------------------

def test_build_bbox_format():
    bbox = build_bbox(38.65, -90.15, radius_deg=0.25)
    assert bbox == "-90.4000,38.4000,-89.9000,38.9000"

def test_build_bbox_west_south_east_north_order():
    bbox = build_bbox(10.0, 20.0, radius_deg=1.0)
    west, south, east, north = (float(x) for x in bbox.split(","))
    assert west  == pytest.approx(19.0)
    assert south == pytest.approx(9.0)
    assert east  == pytest.approx(21.0)
    assert north == pytest.approx(11.0)

SAMPLE_USGS_RDB = (
    "#\n"
    "# US Geological Survey\n"
    "agency_cd\tsite_no\tstation_nm\tsite_tp_cd\tdec_lat_va\tdec_long_va\n"
    "5s\t15s\t50s\t7s\t16s\t16s\n"
    "USGS\t07010000\tMississippi River at St. Louis, MO\tST\t38.629\t-90.1797778\n"
    "USGS\t99999999\tSITE WITH NO COORDS\tST\t\t\n"
)

def test_parse_usgs_rdb_extracts_sites_with_coords():
    sites = parse_usgs_rdb(SAMPLE_USGS_RDB)
    assert len(sites) == 1
    s = sites[0]
    assert s["site_id"]   == "07010000"
    assert s["site_name"] == "Mississippi River at St. Louis, MO"
    assert s["lat"] == pytest.approx(38.629)
    assert s["lon"] == pytest.approx(-90.1797778)

def test_parse_usgs_rdb_empty_text():
    assert parse_usgs_rdb("") == []

def test_parse_usgs_rdb_only_comments():
    assert parse_usgs_rdb("#\n# nothing here\n") == []

def test_fetch_usgs_sites_in_bbox_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(text=SAMPLE_USGS_RDB)
    sites = fetch_usgs_sites_in_bbox(38.65, -90.15)
    assert len(sites) == 1
    assert sites[0]["site_id"] == "07010000"

def test_fetch_usgs_sites_in_bbox_http_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=503)
    sites = fetch_usgs_sites_in_bbox(38.65, -90.15)
    assert sites == []

def test_find_nearest_usgs_site_verifies_live_data(httpx_mock: HTTPXMock):
    httpx_mock.add_response(text=SAMPLE_USGS_RDB)         # bbox site search
    httpx_mock.add_response(json=SAMPLE_USGS_RESPONSE)    # live IV verification, site_id matches
    result = find_nearest_usgs_site(38.65, -90.15, max_km=50)
    assert result is not None
    assert result["site_id"] == "07010000"
    assert "distance_km" in result

def test_find_nearest_usgs_site_beyond_threshold(httpx_mock: HTTPXMock):
    httpx_mock.add_response(text=SAMPLE_USGS_RDB)  # site is ~3km away, threshold excludes it
    result = find_nearest_usgs_site(38.65, -90.15, max_km=0.01)
    assert result is None

def test_find_nearest_usgs_site_no_candidates(httpx_mock: HTTPXMock):
    # In-bounds coordinate (middle of the US) so the coverage-area check
    # doesn't short-circuit before the HTTP call this test is exercising.
    httpx_mock.add_response(text="#\n# no data\n")
    result = find_nearest_usgs_site(39.0, -98.0)
    assert result is None

def test_find_nearest_usgs_site_outside_coverage_area_skips_http_call():
    # No httpx_mock registered — a real HTTP call here would fail the test,
    # proving the coverage-area check short-circuits before any request fires.
    result = find_nearest_usgs_site(41.855, 17.29)  # Adriatic Sea
    assert result is None


# ---------------------------------------------------------------------------
# Live API integration
# ---------------------------------------------------------------------------

# Potomac River at DC — reliable year-round gauge
LIVE_SITE_ID = "01646500"


@pytest.mark.integration
def test_usgs_api_key_is_set():
    assert os.environ.get("USGS_API_KEY"), (
        "USGS_API_KEY is not set — export it before running integration tests"
    )


@pytest.mark.integration
def test_fetch_usgs_live_returns_data(monkeypatch):
    """Live call to USGS IV API returns a parseable response for a known gauge."""
    monkeypatch.setattr(usgs_mod, "USGS_API_KEY", os.environ.get("USGS_API_KEY", "DEMO_KEY"))

    data = fetch_usgs([LIVE_SITE_ID])

    assert data is not None, "fetch_usgs returned None — check API key or network"
    assert "value" in data
    assert "timeSeries" in data["value"]
    assert len(data["value"]["timeSeries"]) > 0


@pytest.mark.integration
def test_usgs_live_parse_gives_temperature(monkeypatch):
    """Live data parses to a valid temperature reading (not offline sensor)."""
    monkeypatch.setattr(usgs_mod, "USGS_API_KEY", os.environ.get("USGS_API_KEY", "DEMO_KEY"))

    data = fetch_usgs([LIVE_SITE_ID])
    assert data is not None

    results = parse_usgs_response(data)
    assert len(results) == 1
    r = results[0]
    assert r["site_id"] == LIVE_SITE_ID
    assert r["temp_f"] is not None, "Sensor may be offline; try a different LIVE_SITE_ID"
    assert 32 <= r["temp_f"] <= 100, f"Temperature {r['temp_f']}°F outside plausible range"


@pytest.mark.integration
def test_find_nearest_usgs_site_live():
    """Live bbox + verification search near the Potomac at DC finds a real site."""
    result = find_nearest_usgs_site(38.8048, -77.0378, max_km=50)
    assert result is not None
    assert "site_id" in result
    assert "distance_km" in result
    assert result["distance_km"] <= 50
