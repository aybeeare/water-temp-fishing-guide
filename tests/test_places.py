"""Integration tests for Google Places API key validation — requires live network."""
import os
import pytest
import sqlite3

import ingest.places_ingest as places


BOSTON_HARBOR_STATION = "8443970"
BOSTON_HARBOR_COORDS  = (42.3584, -71.0522)


@pytest.fixture
def fresh_places_db(tmp_path, monkeypatch):
    from pathlib import Path
    schema = (Path(__file__).parent.parent / "db" / "schema.sql").read_text()
    db_file = str(tmp_path / "places_test.db")
    conn = sqlite3.connect(db_file)
    conn.executescript(schema)
    conn.commit()
    conn.close()
    monkeypatch.setattr(places, "DB_PATH", db_file)
    return db_file


@pytest.mark.integration
def test_places_api_key_is_set():
    """Fail fast if the env var isn't configured before running live tests."""
    assert os.environ.get("GOOGLE_PLACES_API_KEY"), (
        "GOOGLE_PLACES_API_KEY is not set — export it before running integration tests"
    )


@pytest.mark.integration
def test_places_returns_result_for_boston(monkeypatch):
    """_fetch_from_places hits the live API and returns a shop near Boston Harbor."""
    monkeypatch.setattr(places, "API_KEY", os.environ.get("GOOGLE_PLACES_API_KEY", ""))

    result = places._fetch_from_places(*BOSTON_HARBOR_COORDS)

    assert result is not None, "Expected at least one bait/tackle shop near Boston Harbor"
    assert result.get("name"), "Shop result missing 'name'"
    assert result.get("address"), "Shop result missing 'address'"


@pytest.mark.integration
def test_places_response_shape(monkeypatch):
    """Response dict has the four fields the rest of the app expects."""
    monkeypatch.setattr(places, "API_KEY", os.environ.get("GOOGLE_PLACES_API_KEY", ""))

    result = places._fetch_from_places(*BOSTON_HARBOR_COORDS)

    assert result is not None
    assert set(result.keys()) >= {"name", "address", "rating", "open_now"}
    assert isinstance(result["name"], str)
    assert isinstance(result["address"], str)


@pytest.mark.integration
def test_lookup_bait_shop_caches_result(fresh_places_db, monkeypatch):
    """lookup_bait_shop writes to bait_shop_cache so second call skips the API."""
    monkeypatch.setattr(places, "API_KEY", os.environ.get("GOOGLE_PLACES_API_KEY", ""))

    first  = places.lookup_bait_shop(BOSTON_HARBOR_STATION)
    second = places.lookup_bait_shop(BOSTON_HARBOR_STATION)

    assert first == second, "Cached result differs from live result"

    conn = sqlite3.connect(fresh_places_db)
    row = conn.execute(
        "SELECT shop_name FROM bait_shop_cache WHERE station_id = ?",
        (BOSTON_HARBOR_STATION,),
    ).fetchone()
    conn.close()
    assert row is not None, "Expected a row written to bait_shop_cache"
