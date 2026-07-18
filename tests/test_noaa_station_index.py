"""Unit tests for ingest/noaa_station_index.py"""
import sqlite3

import pytest
from pytest_httpx import HTTPXMock

from ingest.geo import haversine_km
from ingest.noaa_station_index import (
    fetch_noaa_station_index,
    upsert_station_index,
    find_nearest_noaa_station,
)

# ---------------------------------------------------------------------------
# Pure math
# ---------------------------------------------------------------------------

def test_haversine_km_same_point_is_zero():
    assert haversine_km(42.35, -71.05, 42.35, -71.05) == pytest.approx(0.0, abs=1e-6)

def test_haversine_km_boston_to_nyc():
    # Boston, MA to New York, NY — real-world distance ~306 km
    result = haversine_km(42.3601, -71.0589, 40.7128, -74.0060)
    assert result == pytest.approx(306, rel=0.02)

# ---------------------------------------------------------------------------
# Sample API response
# ---------------------------------------------------------------------------

STATIONS_RESPONSE_OK = {
    "stations": [
        {"id": "8443970", "name": "Boston Harbor, MA", "lat": 42.3548, "lng": -71.0512, "state": "MA"},
        {"id": "9410170", "name": "San Diego, CA",     "lat": 32.7142, "lng": -117.1736, "state": "CA"},
        {"id": "0000000", "name": "MISSING COORDS",    "lat": None,    "lng": None,       "state": None},
    ]
}

# ---------------------------------------------------------------------------
# Fetch + parse
# ---------------------------------------------------------------------------

def test_fetch_noaa_station_index_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=STATIONS_RESPONSE_OK)
    stations = fetch_noaa_station_index()
    assert len(stations) == 2  # third entry skipped for missing coords
    boston = next(s for s in stations if s["station_id"] == "8443970")
    assert boston["site_name"] == "Boston Harbor, MA"
    assert boston["lat"] == pytest.approx(42.3548)
    assert boston["lon"] == pytest.approx(-71.0512)
    assert boston["state"] == "MA"

def test_fetch_noaa_station_index_http_error_after_retries(httpx_mock: HTTPXMock):
    # 3 attempts, each needs its own registered response in this pytest-httpx version
    for _ in range(3):
        httpx_mock.add_response(status_code=503)
    stations = fetch_noaa_station_index()
    assert stations == []

# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------

def test_upsert_station_index_writes(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    written = upsert_station_index(conn, [
        {"station_id": "8443970", "site_name": "Boston Harbor, MA", "lat": 42.3548, "lon": -71.0512, "state": "MA"},
    ])
    row = conn.execute("SELECT * FROM noaa_station_index WHERE station_id = '8443970'").fetchone()
    conn.close()
    assert written == 1
    assert row["site_name"] == "Boston Harbor, MA"
    assert row["lat"] == pytest.approx(42.3548)

def test_upsert_station_index_overwrites(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    upsert_station_index(conn, [
        {"station_id": "8443970", "site_name": "Old Name", "lat": 0.0, "lon": 0.0, "state": "MA"},
    ])
    upsert_station_index(conn, [
        {"station_id": "8443970", "site_name": "Boston Harbor, MA", "lat": 42.3548, "lon": -71.0512, "state": "MA"},
    ])
    row = conn.execute("SELECT * FROM noaa_station_index WHERE station_id = '8443970'").fetchone()
    conn.close()
    assert row["site_name"] == "Boston Harbor, MA"
    assert row["lat"] == pytest.approx(42.3548)

def test_upsert_station_index_empty_list_is_noop(db_path):
    conn = sqlite3.connect(db_path)
    written = upsert_station_index(conn, [])
    count = conn.execute("SELECT COUNT(*) FROM noaa_station_index").fetchone()[0]
    conn.close()
    assert written == 0
    assert count == 0

# ---------------------------------------------------------------------------
# Nearest-neighbor lookup
# ---------------------------------------------------------------------------

def test_find_nearest_noaa_station_picks_closest(seeded_db):
    # seeded_db has Boston Harbor (MA) and San Diego (CA) — query near Boston
    conn = sqlite3.connect(seeded_db)
    conn.row_factory = sqlite3.Row
    result = find_nearest_noaa_station(conn, 42.36, -71.06, max_km=80)
    conn.close()
    assert result is not None
    assert result["station_id"] == "8443970"
    assert result["distance_km"] < 5

def test_find_nearest_noaa_station_beyond_threshold(seeded_db):
    conn = sqlite3.connect(seeded_db)
    conn.row_factory = sqlite3.Row
    # Query somewhere in the middle of nowhere, far from both seeded stations
    result = find_nearest_noaa_station(conn, 45.0, -105.0, max_km=80)
    conn.close()
    assert result is None

def test_find_nearest_noaa_station_no_stations(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    result = find_nearest_noaa_station(conn, 42.36, -71.06, max_km=80)
    conn.close()
    assert result is None


# ---------------------------------------------------------------------------
# Live API integration
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_fetch_noaa_station_index_live():
    """Live call returns a plausible number of water-temp stations."""
    stations = fetch_noaa_station_index()
    assert len(stations) > 100, "Expected at least 100 NOAA water-temp stations"
    for s in stations[:5]:
        assert -90 <= s["lat"] <= 90
        assert -180 <= s["lon"] <= 180
