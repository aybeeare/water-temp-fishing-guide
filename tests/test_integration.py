"""
Integration tests — hit live USGS and NOAA APIs.
Run with:  pytest -m integration -v
Skipped by default in normal test runs.
"""
import pytest
from ingest.usgs_ingest import fetch_usgs, parse_usgs_response
from ingest.noaa_ingest import fetch_noaa_temperature, fetch_noaa_tides


@pytest.mark.integration
def test_usgs_mississippi_live():
    """
    Fetch live data for Mississippi River at St. Louis (07010000).
    This is primarily a streamflow gauge — parameter 00010 (water temp) may
    not be active. We verify the API responds without error and any returned
    temperatures are plausible. An empty result is acceptable.
    """
    data = fetch_usgs(["07010000"])
    assert data is not None, "USGS API returned no data at all"
    results = parse_usgs_response(data)
    # If the gauge has a temp sensor today, validate the reading
    for r in results:
        if r["temp_f"] is not None:
            assert 32 <= r["temp_f"] <= 110, f"Implausible temp: {r['temp_f']}°F"


@pytest.mark.integration
def test_usgs_columbia_river_live():
    """
    Columbia River at Vernita (12472600).
    NOTE: Many USGS sites only measure streamflow, not temperature (param 00010).
    An empty result is valid — we verify the API responds and data shape is correct.
    """
    data = fetch_usgs(["12472600"])
    assert data is not None
    results = parse_usgs_response(data)
    for r in results:
        if r["temp_f"] is not None:
            assert 32 <= r["temp_f"] <= 90, f"Implausible temp: {r['temp_f']}°F"


@pytest.mark.integration
def test_usgs_lake_michigan_live():
    """Fetch live water temp for Lake Michigan at Milwaukee (04085427)."""
    data = fetch_usgs(["04085427"])
    assert data is not None
    results = parse_usgs_response(data)
    assert len(results) >= 1


@pytest.mark.integration
def test_noaa_boston_temperature_live():
    """Fetch live water temp from NOAA Boston Harbor (8443970)."""
    result = fetch_noaa_temperature("8443970")
    # Boston may have temp sensor — if available, validate range
    if result is not None:
        assert 28 <= result["temp_f"] <= 90, f"Implausible temp: {result['temp_f']}°F"
        assert "raw_datetime" in result


@pytest.mark.integration
def test_noaa_boston_tides_live():
    """Fetch today's tide predictions from NOAA Boston Harbor (8443970)."""
    tides = fetch_noaa_tides("8443970")
    # Boston Harbor always has tide predictions
    assert len(tides) >= 2, "Expected at least 2 tide events today"
    for t in tides:
        assert t["tide_type"] in ("H", "L")
        assert t["height_ft"] is not None
        assert t["height_ft"] > 0


@pytest.mark.integration
def test_noaa_key_west_tides_live():
    """Key West (8724580) should have 2 tides per day (diurnal pattern)."""
    tides = fetch_noaa_tides("8724580")
    assert len(tides) >= 1


@pytest.mark.integration
def test_noaa_seattle_tides_live():
    """Seattle (9447130) — Puget Sound has strong mixed semidiurnal tides."""
    tides = fetch_noaa_tides("9447130")
    assert len(tides) >= 2
    highs = [t for t in tides if t["tide_type"] == "H"]
    lows  = [t for t in tides if t["tide_type"] == "L"]
    assert len(highs) >= 1
    assert len(lows)  >= 1
