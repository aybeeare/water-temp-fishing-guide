"""Unit tests for ingest/usgs_ingest.py"""
import sqlite3
from datetime import datetime, timezone, timedelta

import pytest
from pytest_httpx import HTTPXMock

from ingest.usgs_ingest import (
    celsius_to_fahrenheit,
    parse_usgs_response,
    sites_needing_refresh,
    fetch_usgs,
    upsert_cache,
    USGS_IV_URL,
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
