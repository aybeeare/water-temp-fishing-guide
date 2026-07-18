"""Unit tests for ingest/geocode_ingest.py"""
import os
import sqlite3
from datetime import date

import pytest
from pytest_httpx import HTTPXMock

import ingest.geocode_ingest as geocode_mod
from ingest.geocode_ingest import geocode_location

# ---------------------------------------------------------------------------
# Sample API responses
# ---------------------------------------------------------------------------

GEOCODE_RESPONSE_OK = {
    "status": "OK",
    "results": [
        {
            "formatted_address": "Lake Tahoe, CA, USA",
            "geometry": {"location": {"lat": 39.0968, "lng": -120.0324}},
        }
    ],
}

GEOCODE_RESPONSE_ZERO_RESULTS = {"status": "ZERO_RESULTS", "results": []}

GEOCODE_RESPONSE_ERROR = {"status": "OVER_QUERY_LIMIT", "results": []}

# ---------------------------------------------------------------------------
# Geocoding
# ---------------------------------------------------------------------------

def test_geocode_location_success(db_path, monkeypatch, httpx_mock: HTTPXMock):
    monkeypatch.setattr(geocode_mod, "DB_PATH", db_path)
    monkeypatch.setattr(geocode_mod, "API_KEY", "fake-key")
    httpx_mock.add_response(json=GEOCODE_RESPONSE_OK)

    result = geocode_location("Lake Tahoe")

    assert result is not None
    lat, lon = result
    assert lat == pytest.approx(39.0968)
    assert lon == pytest.approx(-120.0324)

def test_geocode_location_zero_results(db_path, monkeypatch, httpx_mock: HTTPXMock):
    monkeypatch.setattr(geocode_mod, "DB_PATH", db_path)
    monkeypatch.setattr(geocode_mod, "API_KEY", "fake-key")
    httpx_mock.add_response(json=GEOCODE_RESPONSE_ZERO_RESULTS)

    assert geocode_location("zxqwerty fictional lake") is None

def test_geocode_location_error_status(db_path, monkeypatch, httpx_mock: HTTPXMock):
    monkeypatch.setattr(geocode_mod, "DB_PATH", db_path)
    monkeypatch.setattr(geocode_mod, "API_KEY", "fake-key")
    httpx_mock.add_response(json=GEOCODE_RESPONSE_ERROR)

    assert geocode_location("Lake Tahoe") is None

def test_geocode_location_http_error(db_path, monkeypatch, httpx_mock: HTTPXMock):
    monkeypatch.setattr(geocode_mod, "DB_PATH", db_path)
    monkeypatch.setattr(geocode_mod, "API_KEY", "fake-key")
    httpx_mock.add_response(status_code=500)

    assert geocode_location("Lake Tahoe") is None

def test_geocode_location_no_api_key(db_path, monkeypatch):
    monkeypatch.setattr(geocode_mod, "DB_PATH", db_path)
    monkeypatch.setattr(geocode_mod, "API_KEY", "")

    assert geocode_location("Lake Tahoe") is None

def test_geocode_location_malformed_response(db_path, monkeypatch, httpx_mock: HTTPXMock):
    monkeypatch.setattr(geocode_mod, "DB_PATH", db_path)
    monkeypatch.setattr(geocode_mod, "API_KEY", "fake-key")
    httpx_mock.add_response(json={"status": "OK", "results": [{"formatted_address": "nowhere"}]})

    assert geocode_location("Lake Tahoe") is None

# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

def test_geocode_location_daily_limit_reached(db_path, monkeypatch):
    monkeypatch.setattr(geocode_mod, "DB_PATH", db_path)
    monkeypatch.setattr(geocode_mod, "API_KEY", "fake-key")
    monkeypatch.setattr(geocode_mod, "MAX_DAILY_CALLS", 1)

    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO api_call_log (api_name, call_date, call_count) VALUES ('google_geocoding', ?, 1)",
        (date.today().isoformat(),),
    )
    conn.commit()
    conn.close()

    # No httpx_mock registered — a real HTTP call here would fail the test,
    # proving the daily-limit check short-circuits before any request fires.
    assert geocode_location("Lake Tahoe") is None

def test_geocode_location_increments_count(db_path, monkeypatch, httpx_mock: HTTPXMock):
    monkeypatch.setattr(geocode_mod, "DB_PATH", db_path)
    monkeypatch.setattr(geocode_mod, "API_KEY", "fake-key")
    httpx_mock.add_response(json=GEOCODE_RESPONSE_OK)

    geocode_location("Lake Tahoe")

    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT call_count FROM api_call_log WHERE api_name='google_geocoding' AND call_date=?",
        (date.today().isoformat(),),
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == 1


# ---------------------------------------------------------------------------
# Live API integration
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_geocoding_api_key_is_set():
    assert os.environ.get("GOOGLE_PLACES_API_KEY"), (
        "GOOGLE_PLACES_API_KEY is not set — export it before running integration tests"
    )

@pytest.mark.integration
def test_geocode_location_live_returns_coordinates(monkeypatch):
    """Live call to the Geocoding API resolves a well-known place."""
    monkeypatch.setattr(geocode_mod, "API_KEY", os.environ.get("GOOGLE_PLACES_API_KEY", ""))

    result = geocode_location("Lake Tahoe")

    assert result is not None, "Geocoding returned None — check API key or Geocoding API enablement"
    lat, lon = result
    assert 38 <= lat <= 40
    assert -121 <= lon <= -119
