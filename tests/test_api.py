"""Tests for api/main.py — endpoint logic with mocked DB and ingestion."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


def make_client(patch_db):
    import api.main as api_main
    return TestClient(api_main.app)


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------

def test_health_ok(patch_db):
    client = make_client(patch_db)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "water_cache" in body["db"]
    assert body["db"]["location_aliases"] > 0
    assert body["db"]["fishing_logic"] > 0


# ---------------------------------------------------------------------------
# /fishing-guide — input validation
# ---------------------------------------------------------------------------

def test_no_params_returns_400(patch_db):
    client = make_client(patch_db)
    resp = client.get("/fishing-guide")
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# /fishing-guide — USGS path (cache hit)
# ---------------------------------------------------------------------------

def test_usgs_cache_hit_by_location(patch_db):
    """lake-michigan alias → site 04085427 → already in seeded water_cache."""
    with patch("api.main.run_ingest") as mock_ingest:
        client = make_client(patch_db)
        resp = client.get("/fishing-guide", params={"location": "lake michigan"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["temp_f"] == pytest.approx(68.0, abs=0.1)
    assert "Lake Michigan" in body["site_name"]
    assert "68" in body["spoken_response"]
    # Should NOT have triggered a live ingest — data was fresh
    mock_ingest.assert_not_called()


def test_usgs_cache_miss_triggers_ingest(patch_db, monkeypatch):
    """Unknown USGS site ID → triggers run_ingest."""
    import sqlite3, api.main as api_main

    def fake_ingest(site_ids):
        conn = sqlite3.connect(patch_db)
        conn.execute(
            "INSERT INTO water_cache (site_id, site_name, temp_f, temp_c, fetched_at) VALUES (?,?,?,?,?)",
            ("99999999", "Fake River", 55.0, 12.8, "2099-01-01T00:00:00+00:00"),
        )
        conn.commit()
        conn.close()

    monkeypatch.setattr(api_main, "run_ingest", fake_ingest)
    client = make_client(patch_db)
    resp = client.get("/fishing-guide", params={"site_id": "99999999"})
    assert resp.status_code == 200
    assert resp.json()["temp_f"] == pytest.approx(55.0, abs=0.1)


# ---------------------------------------------------------------------------
# /fishing-guide — NOAA path (cache hit + tides)
# ---------------------------------------------------------------------------

def test_noaa_cache_hit_with_tides(patch_db):
    """boston-harbor alias → NOAA station 8443970 → cache hit → includes tide speech."""
    import sqlite3
    from datetime import date

    # Seed tide data for today
    conn = sqlite3.connect(patch_db)
    today = date.today().isoformat()
    conn.executemany(
        "INSERT INTO tide_cache (site_id, tide_type, tide_time, height_ft, fetched_at, tide_date) VALUES (?,?,?,?,?,?)",
        [
            ("8443970", "L", f"{today} 02:34", 1.23, "2099-01-01T00:00:00+00:00", today),
            ("8443970", "H", f"{today} 08:45", 5.67, "2099-01-01T00:00:00+00:00", today),
            ("8443970", "L", f"{today} 14:56", 0.89, "2099-01-01T00:00:00+00:00", today),
            ("8443970", "H", f"{today} 21:12", 6.12, "2099-01-01T00:00:00+00:00", today),
        ],
    )
    conn.commit()
    conn.close()

    with patch("api.main.run_noaa_ingest_for"):
        client = make_client(patch_db)
        resp = client.get("/fishing-guide", params={"location": "boston harbor"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["temp_f"] == pytest.approx(62.5, abs=0.1)
    assert body["tides"] is not None
    assert len(body["tides"]) == 4
    assert "Today's tides" in body["spoken_response"]
    # Tide types should be H and L
    types = {t["tide_type"] for t in body["tides"]}
    assert types == {"H", "L"}


# ---------------------------------------------------------------------------
# /fishing-guide — scrape path (cache hit)
# ---------------------------------------------------------------------------

def test_scrape_cache_hit(patch_db):
    """lake-tahoe alias → scrape source → served from seeded water_cache."""
    with patch("api.main.is_cache_fresh", return_value=True), \
         patch("api.main.scrape_and_cache"), \
         patch("api.main.scrape_tides", return_value=[]):
        client = make_client(patch_db)
        resp = client.get("/fishing-guide", params={"location": "lake tahoe"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["temp_f"] == pytest.approx(58.0, abs=0.1)
    assert body["tides"] is None   # scrape sources don't provide tides


# ---------------------------------------------------------------------------
# /fishing-guide — disambiguation
# ---------------------------------------------------------------------------

def test_disambiguation_response(patch_db):
    """ocean-city alias is ambiguous → returns disambiguation list."""
    client = make_client(patch_db)
    resp = client.get("/fishing-guide", params={"location": "ocean city"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["disambiguation"] is not None
    assert len(body["disambiguation"]) == 2
    assert body["temp_f"] is None
    assert "Maryland" in body["spoken_response"] or "New Jersey" in body["spoken_response"]


# ---------------------------------------------------------------------------
# /fishing-guide — 404 for truly unknown location
# ---------------------------------------------------------------------------

def test_unknown_location_404(patch_db):
    """No alias + scrape returns nothing → 404."""
    with patch("api.main.is_cache_fresh", return_value=False), \
         patch("api.main.scrape_and_cache", return_value=None):
        client = make_client(patch_db)
        resp = client.get("/fishing-guide", params={"location": "zxqwerty fictional lake"})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# /fishing-guide — coordinate-based resolution
# ---------------------------------------------------------------------------

def test_coordinates_resolve_to_noaa(patch_db):
    """NOAA candidate closer than USGS candidate → resolves via NOAA, cache hit."""
    noaa_hit = {"station_id": "8443970", "site_name": "Boston Harbor, MA", "lat": 42.3548, "lon": -71.0512, "distance_km": 2.1}
    with patch("api.main.find_nearest_noaa_station", return_value=noaa_hit), \
         patch("api.main.find_nearest_usgs_site", return_value=None), \
         patch("api.main.run_noaa_ingest_for"):
        client = make_client(patch_db)
        resp = client.get("/fishing-guide", params={"lat": 42.36, "lon": -71.06})

    assert resp.status_code == 200
    body = resp.json()
    assert body["site_id"] == "8443970"
    assert body["temp_f"] == pytest.approx(62.5, abs=0.1)
    assert body["resolved_via"] == "coordinates"
    assert body["distance_km"] == pytest.approx(2.1)


def test_coordinates_resolve_to_usgs(patch_db):
    """USGS candidate closer than NOAA candidate → resolves via USGS, cache hit."""
    usgs_hit = {"site_id": "04085427", "site_name": "Lake Michigan at Milwaukee, WI", "lat": 43.0, "lon": -87.9, "distance_km": 1.5}
    noaa_hit = {"station_id": "8443970", "site_name": "Boston Harbor, MA", "lat": 42.3548, "lon": -71.0512, "distance_km": 40.0}
    with patch("api.main.find_nearest_usgs_site", return_value=usgs_hit), \
         patch("api.main.find_nearest_noaa_station", return_value=noaa_hit), \
         patch("api.main.run_ingest"):
        client = make_client(patch_db)
        resp = client.get("/fishing-guide", params={"lat": 43.0, "lon": -87.9})

    assert resp.status_code == 200
    body = resp.json()
    assert body["site_id"] == "04085427"
    assert body["temp_f"] == pytest.approx(68.0, abs=0.1)
    assert body["resolved_via"] == "coordinates"
    assert body["distance_km"] == pytest.approx(1.5)


async def test_coordinates_noaa_wins_tie_break_when_usgs_not_decisively_closer(patch_db):
    """USGS is numerically closer (14km, e.g. a small pond) but NOAA (65km,
    e.g. a real coastal station) still wins, since USGS isn't within the
    override radius — regression test for the Fresh Pond / Marblehead case."""
    import api.main as api_main
    usgs_hit = {"site_id": "422302071083801", "site_name": "FRESH POND, CAMBRIDGE, MA",
                "lat": 42.38, "lon": -71.15, "distance_km": 14.0}
    noaa_hit = {"station_id": "8454000", "site_name": "Providence, RI",
                "lat": 41.807, "lon": -71.401, "distance_km": 65.0}
    with patch("api.main.find_nearest_usgs_site", return_value=usgs_hit), \
         patch("api.main.find_nearest_noaa_station", return_value=noaa_hit):
        resolved_id, source, distance_km, site_name = await api_main.resolve_coordinates(42.4251, -70.9828)

    assert source == "noaa"
    assert resolved_id == "8454000"
    assert distance_km == pytest.approx(65.0)


async def test_coordinates_usgs_wins_when_within_override_radius(patch_db):
    """USGS wins over a farther NOAA candidate when it's within the small
    override radius — i.e. you're essentially at that specific water body."""
    import api.main as api_main
    usgs_hit = {"site_id": "04085427", "site_name": "Lake Michigan at Milwaukee, WI",
                "lat": 43.0, "lon": -87.9, "distance_km": 3.0}
    noaa_hit = {"station_id": "8443970", "site_name": "Boston Harbor, MA",
                "lat": 42.3548, "lon": -71.0512, "distance_km": 40.0}
    with patch("api.main.find_nearest_usgs_site", return_value=usgs_hit), \
         patch("api.main.find_nearest_noaa_station", return_value=noaa_hit):
        resolved_id, source, distance_km, site_name = await api_main.resolve_coordinates(43.0, -87.9)

    assert source == "usgs"
    assert resolved_id == "04085427"


def test_coordinates_no_station_within_threshold_returns_404(patch_db):
    with patch("api.main.find_nearest_usgs_site", return_value=None), \
         patch("api.main.find_nearest_noaa_station", return_value=None):
        client = make_client(patch_db)
        resp = client.get("/fishing-guide", params={"lat": 0.0, "lon": 0.0})

    assert resp.status_code == 404


def test_coordinates_missing_lon_returns_400(patch_db):
    client = make_client(patch_db)
    resp = client.get("/fishing-guide", params={"lat": 42.36})
    assert resp.status_code == 400


def test_location_takes_precedence_over_coordinates(patch_db):
    """When both location and lat/lon are given, the existing alias path wins
    and coordinate resolution is never invoked."""
    with patch("api.main.run_ingest"), \
         patch("api.main.resolve_coordinates") as mock_resolve_coords:
        client = make_client(patch_db)
        resp = client.get("/fishing-guide", params={"location": "lake michigan", "lat": 0.0, "lon": 0.0})

    assert resp.status_code == 200
    assert resp.json()["resolved_via"] == "alias"
    mock_resolve_coords.assert_not_called()


def test_coordinates_falls_back_to_scrape_tier(patch_db):
    """Neither USGS nor NOAA qualifies → falls back to the nearest known
    scrape_location_index entry (seeded 'lake-tahoe' at 39.0968, -120.0324)."""
    with patch("api.main.find_nearest_usgs_site", return_value=None), \
         patch("api.main.find_nearest_noaa_station", return_value=None), \
         patch("api.main.scrape_tides", return_value=[]):
        client = make_client(patch_db)
        resp = client.get("/fishing-guide", params={"lat": 39.10, "lon": -120.03})

    assert resp.status_code == 200
    body = resp.json()
    assert body["site_id"] == "lake-tahoe"
    assert body["temp_f"] == pytest.approx(58.0, abs=0.1)
    assert body["resolved_via"] == "coordinates"
    assert body["tides"] is None


# ---------------------------------------------------------------------------
# /fishing-guide — geocoding fallback for failed string locations
# ---------------------------------------------------------------------------

def test_geocoded_fallback_after_alias_and_scrape_miss(patch_db):
    """Alias miss + scrape-slug-guess miss → geocode the string → resolves
    via the coordinate path (here, to the seeded NOAA cache hit)."""
    with patch("api.main.is_cache_fresh", return_value=False), \
         patch("api.main.scrape_and_cache", return_value=None), \
         patch("api.main.geocode_location", return_value=(42.36, -71.06)), \
         patch("api.main.resolve_coordinates", return_value=("8443970", "noaa", 2.1, "Boston Harbor, MA")), \
         patch("api.main.run_noaa_ingest_for"):
        client = make_client(patch_db)
        resp = client.get("/fishing-guide", params={"location": "some obscure real place"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["temp_f"] == pytest.approx(62.5, abs=0.1)
    assert body["resolved_via"] == "geocoded"
    assert body["distance_km"] == pytest.approx(2.1)
    assert "Some Obscure Real Place" in body["site_name"]


def test_geocoded_fallback_returns_404_when_geocoding_fails(patch_db):
    """Alias miss + scrape miss + geocoding also returns nothing → generic 404."""
    with patch("api.main.is_cache_fresh", return_value=False), \
         patch("api.main.scrape_and_cache", return_value=None), \
         patch("api.main.geocode_location", return_value=None):
        client = make_client(patch_db)
        resp = client.get("/fishing-guide", params={"location": "zxqwerty fictional lake"})

    assert resp.status_code == 404


def test_geocoded_fallback_returns_404_when_resolve_coordinates_finds_nothing(patch_db):
    """Geocoding succeeds but resolve_coordinates finds nothing within any
    threshold (raises 404 internally) → falls through to the existing
    generic 404 rather than propagating the coordinate-specific message."""
    from fastapi import HTTPException

    with patch("api.main.is_cache_fresh", return_value=False), \
         patch("api.main.scrape_and_cache", return_value=None), \
         patch("api.main.geocode_location", return_value=(0.0, 0.0)), \
         patch("api.main.resolve_coordinates", side_effect=HTTPException(status_code=404, detail="no station nearby")):
        client = make_client(patch_db)
        resp = client.get("/fishing-guide", params={"location": "zxqwerty fictional lake"})

    assert resp.status_code == 404
    assert "No temperature data found" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Spoken response content
# ---------------------------------------------------------------------------

def test_spoken_response_includes_fishing_logic(patch_db):
    """68°F lake michigan hits the 60–72 freshwater logic row → gear in speech."""
    with patch("api.main.run_ingest"):
        client = make_client(patch_db)
        resp = client.get("/fishing-guide", params={"location": "lake michigan"})

    body = resp.json()
    assert "Bass" in body["spoken_response"]        # fish_behavior text
    assert "Topwater" in body["spoken_response"]    # recommended_gear
    assert body["alexa_directive"] is not None
    assert body["alexa_directive"]["payload"]["items"][0]["asin"] == "B0FRESHASIN1"


def test_alexa_directive_structure(patch_db):
    """Directive must follow Connections.SendRequest / AddToShoppingCart shape."""
    with patch("api.main.run_ingest"):
        client = make_client(patch_db)
        resp = client.get("/fishing-guide", params={"location": "lake michigan"})

    directive = resp.json()["alexa_directive"]
    assert directive["type"] == "Connections.SendRequest"
    assert directive["name"] == "AddToShoppingCart"
    assert "associatedId" in directive["payload"]
    assert directive["payload"]["type"] == "BuyShoppingProducts"


# ---------------------------------------------------------------------------
# Scraper fallback when primary source has no temperature
# ---------------------------------------------------------------------------

def test_scraper_fallback_used_when_temp_is_none(patch_db, monkeypatch):
    """
    If the primary source (USGS/NOAA) returns a row with temp_f=NULL,
    the API should fall back to seatemperature.info scraping before
    declaring the sensor offline.
    """
    import sqlite3, api.main as api_main

    # Overwrite seeded row with NULL temperature to simulate offline sensor
    conn = sqlite3.connect(patch_db)
    conn.execute(
        "INSERT OR REPLACE INTO water_cache (site_id, site_name, temp_f, temp_c, fetched_at) VALUES (?,?,?,?,?)",
        ("04085427", "Lake Michigan at Milwaukee, WI", None, None, "2099-01-01T00:00:00+00:00"),
    )
    conn.commit()
    conn.close()

    # Fallback scraper returns a temperature
    monkeypatch.setattr(api_main, "scrape_and_cache", lambda slug: {
        "temp_f": 65.0, "temp_c": 18.3, "site_name": "Lake Michigan", "slug": slug
    })

    client = make_client(patch_db)
    resp = client.get("/fishing-guide", params={"location": "lake michigan"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["temp_f"] == pytest.approx(65.0, abs=0.1)
    assert "65" in body["spoken_response"]
    assert "offline" not in body["spoken_response"]


def test_sensor_offline_when_fallback_also_fails(patch_db, monkeypatch):
    """
    If both the primary source and the scraper return no temperature,
    the response should say the sensor is offline (not a 500 error).
    """
    import sqlite3, api.main as api_main

    # Overwrite seeded row with NULL temperature to simulate offline sensor
    conn = sqlite3.connect(patch_db)
    conn.execute(
        "INSERT OR REPLACE INTO water_cache (site_id, site_name, temp_f, temp_c, fetched_at) VALUES (?,?,?,?,?)",
        ("04085427", "Lake Michigan at Milwaukee, WI", None, None, "2099-01-01T00:00:00+00:00"),
    )
    conn.commit()
    conn.close()

    # Scraper also fails
    monkeypatch.setattr(api_main, "scrape_and_cache", lambda slug: None)

    client = make_client(patch_db)
    resp = client.get("/fishing-guide", params={"location": "lake michigan"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["temp_f"] is None
    assert "offline" in body["spoken_response"].lower()
