"""Unit tests for ingest/noaa_ingest.py"""
import sqlite3
from datetime import datetime, timezone, timedelta, date

import pytest
from pytest_httpx import HTTPXMock

from ingest.noaa_ingest import (
    fetch_noaa_temperature,
    fetch_noaa_tides,
    is_cache_fresh,
    upsert_temperature,
    upsert_tides,
    NOAA_BASE,
)

# ---------------------------------------------------------------------------
# Sample API responses
# ---------------------------------------------------------------------------

TEMP_RESPONSE_OK = {
    "data": [
        {"t": "2024-06-23 12:00", "v": "72.5", "f": "0,0,0"},
        {"t": "2024-06-23 12:06", "v": "72.8", "f": "0,0,0"},
    ]
}

TEMP_RESPONSE_NO_SENSOR = {
    "error": {"message": "No data was found. This product may not be offered at this station."}
}

TIDES_RESPONSE_OK = {
    "predictions": [
        {"t": "2024-06-23 02:34", "v": "1.23", "type": "L"},
        {"t": "2024-06-23 08:45", "v": "5.67", "type": "H"},
        {"t": "2024-06-23 14:56", "v": "0.89", "type": "L"},
        {"t": "2024-06-23 21:12", "v": "6.12", "type": "H"},
    ]
}

TIDES_RESPONSE_ERROR = {
    "error": {"message": "No data was found."}
}

# ---------------------------------------------------------------------------
# Temperature fetch
# ---------------------------------------------------------------------------

def test_fetch_noaa_temperature_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=TEMP_RESPONSE_OK)
    result = fetch_noaa_temperature("8443970")
    assert result is not None
    assert result["temp_f"] == pytest.approx(72.8, abs=0.1)
    assert result["temp_c"] == pytest.approx(22.7, abs=0.2)
    assert "raw_datetime" in result

def test_fetch_noaa_temperature_no_sensor(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=TEMP_RESPONSE_NO_SENSOR)
    result = fetch_noaa_temperature("8443970")
    assert result is None

def test_fetch_noaa_temperature_http_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=500)
    result = fetch_noaa_temperature("8443970")
    assert result is None

def test_fetch_noaa_temperature_empty_data(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"data": []})
    result = fetch_noaa_temperature("8443970")
    assert result is None

# ---------------------------------------------------------------------------
# Tides fetch
# ---------------------------------------------------------------------------

def test_fetch_noaa_tides_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=TIDES_RESPONSE_OK)
    tides = fetch_noaa_tides("8443970")
    assert len(tides) == 4
    highs = [t for t in tides if t["tide_type"] == "H"]
    lows  = [t for t in tides if t["tide_type"] == "L"]
    assert len(highs) == 2
    assert len(lows)  == 2
    assert highs[0]["height_ft"] == pytest.approx(5.67, abs=0.01)
    assert lows[0]["height_ft"]  == pytest.approx(1.23, abs=0.01)

def test_fetch_noaa_tides_no_station(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=TIDES_RESPONSE_ERROR)
    tides = fetch_noaa_tides("8443970")
    assert tides == []

def test_fetch_noaa_tides_http_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=503)
    tides = fetch_noaa_tides("8443970")
    assert tides == []

# ---------------------------------------------------------------------------
# Cache freshness
# ---------------------------------------------------------------------------

def test_is_cache_fresh_missing(db_path):
    conn = sqlite3.connect(db_path)
    assert is_cache_fresh(conn, "8443970") is False
    conn.close()

def test_is_cache_fresh_recent(db_path):
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO water_cache (site_id, site_name, temp_f, temp_c, fetched_at) VALUES (?,?,?,?,?)",
        ("8443970", "Boston Harbor", 62.5, 16.9, now),
    )
    conn.commit()
    assert is_cache_fresh(conn, "8443970") is True
    conn.close()

def test_is_cache_fresh_stale(db_path):
    old = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO water_cache (site_id, site_name, temp_f, temp_c, fetched_at) VALUES (?,?,?,?,?)",
        ("8443970", "Boston Harbor", 62.5, 16.9, old),
    )
    conn.commit()
    assert is_cache_fresh(conn, "8443970") is False
    conn.close()

# ---------------------------------------------------------------------------
# Upsert tides
# ---------------------------------------------------------------------------

def test_upsert_tides_inserts_rows(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    tides = [
        {"tide_type": "H", "tide_time": "2024-06-23 08:45", "height_ft": 5.67},
        {"tide_type": "L", "tide_time": "2024-06-23 14:56", "height_ft": 0.89},
    ]
    upsert_tides(conn, "8443970", tides)
    conn.commit()
    rows = conn.execute("SELECT * FROM tide_cache WHERE site_id = '8443970'").fetchall()
    conn.close()
    assert len(rows) == 2
    assert rows[0]["tide_type"] in ("H", "L")

def test_upsert_tides_replaces_on_rerun(db_path):
    conn = sqlite3.connect(db_path)
    tides_a = [{"tide_type": "H", "tide_time": "2024-06-23 08:45", "height_ft": 5.67}]
    tides_b = [
        {"tide_type": "H", "tide_time": "2024-06-23 08:45", "height_ft": 5.90},
        {"tide_type": "L", "tide_time": "2024-06-23 14:56", "height_ft": 0.89},
    ]
    upsert_tides(conn, "8443970", tides_a)
    conn.commit()
    upsert_tides(conn, "8443970", tides_b)
    conn.commit()
    rows = conn.execute("SELECT * FROM tide_cache WHERE site_id = '8443970'").fetchall()
    conn.close()
    # Should have 2 rows from tides_b, not 3 (old + new)
    assert len(rows) == 2
