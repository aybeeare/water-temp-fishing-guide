"""Unit tests for ingest/sea_temp_scraper.py"""
import pytest
from pytest_httpx import HTTPXMock

from ingest.sea_temp_scraper import (
    slug_from_name,
    parse_temperature,
    extract_temperature,
    get_disambiguation_options,
    scrape_temperature,
    build_url,
)

# ---------------------------------------------------------------------------
# Slug normalization
# ---------------------------------------------------------------------------

def test_slug_from_name_simple():
    assert slug_from_name("Lake Tahoe") == "lake-tahoe"

def test_slug_from_name_multiple_spaces():
    assert slug_from_name("Long Island Sound") == "long-island-sound"

def test_slug_from_name_already_lower():
    assert slug_from_name("ocean-city") == "ocean-city"

def test_slug_from_name_strips_special_chars():
    assert slug_from_name("St. Johns River!") == "st-johns-river"

def test_slug_from_name_leading_trailing():
    assert slug_from_name("  Pacific Ocean  ") == "pacific-ocean"

# ---------------------------------------------------------------------------
# Temperature text parsing
# ---------------------------------------------------------------------------

def test_parse_temperature_celsius():
    result = parse_temperature("18.5 °C")
    assert result["temp_c"] == pytest.approx(18.5, abs=0.01)
    assert result["temp_f"] == pytest.approx(65.3, abs=0.1)

def test_parse_temperature_fahrenheit():
    result = parse_temperature("72°F")
    assert result["temp_f"] == pytest.approx(72.0, abs=0.01)
    assert result["temp_c"] == pytest.approx(22.2, abs=0.1)

def test_parse_temperature_no_match():
    assert parse_temperature("No data available") is None

def test_parse_temperature_empty():
    assert parse_temperature("") is None

def test_parse_temperature_celsius_no_space():
    result = parse_temperature("Water is 21°C today")
    assert result["temp_c"] == pytest.approx(21.0, abs=0.01)

# ---------------------------------------------------------------------------
# HTML extraction strategies
# ---------------------------------------------------------------------------

HTML_CSS_SELECTOR = """
<html><body>
  <div class="current-temp">18.5 °C</div>
</body></html>
"""

HTML_BODY_TEXT = """
<html><body>
  <p>The current water temperature is 22 °C near the shore.</p>
</body></html>
"""

HTML_TABLE = """
<html><body>
  <table>
    <tr><td>Month</td><td>Temp</td></tr>
    <tr><td>Today (Current)</td><td>19.5 °C</td></tr>
  </table>
</body></html>
"""

HTML_NO_TEMP = """
<html><body><p>Welcome to our site. No temperature available.</p></body></html>
"""

def test_extract_temperature_css_selector():
    result = extract_temperature(HTML_CSS_SELECTOR)
    assert result is not None
    assert result["temp_c"] == pytest.approx(18.5, abs=0.01)

def test_extract_temperature_body_text():
    result = extract_temperature(HTML_BODY_TEXT)
    assert result is not None
    assert result["temp_c"] == pytest.approx(22.0, abs=0.01)

def test_extract_temperature_table():
    result = extract_temperature(HTML_TABLE)
    assert result is not None
    assert result["temp_c"] == pytest.approx(19.5, abs=0.01)

def test_extract_temperature_none_found():
    result = extract_temperature(HTML_NO_TEMP)
    assert result is None

# ---------------------------------------------------------------------------
# Disambiguation
# ---------------------------------------------------------------------------

def test_disambiguation_ocean_city():
    options = get_disambiguation_options("ocean-city")
    assert options is not None
    assert len(options) == 2
    names = [o["name"] for o in options]
    assert any("Maryland" in n for n in names)
    assert any("New Jersey" in n for n in names)

def test_disambiguation_unknown_slug():
    assert get_disambiguation_options("lake-tahoe") is None

def test_disambiguation_portland():
    options = get_disambiguation_options("portland")
    assert options is not None
    assert len(options) == 2

# ---------------------------------------------------------------------------
# HTTP scrape (mocked)
# ---------------------------------------------------------------------------

def test_scrape_temperature_success(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=build_url("lake-tahoe"),
        html='<html><body><div class="current-temp">16.5 °C</div></body></html>',
        status_code=200,
    )
    result = scrape_temperature("lake-tahoe")
    assert result is not None
    assert result["temp_c"] == pytest.approx(16.5, abs=0.01)
    assert result["temp_f"] == pytest.approx(61.7, abs=0.1)
    assert result["slug"]   == "lake-tahoe"

def test_scrape_temperature_404(httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=build_url("nonexistent-lake"), status_code=404)
    result = scrape_temperature("nonexistent-lake")
    assert result is None

def test_scrape_temperature_no_parseable_temp(httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=build_url("mystery-lake"),
        html="<html><body><p>Under maintenance</p></body></html>",
        status_code=200,
    )
    result = scrape_temperature("mystery-lake")
    assert result is None

def test_scrape_temperature_full_path(httpx_mock: HTTPXMock):
    full_path = "/united-states/maryland/ocean-city-water-temperature.html"
    httpx_mock.add_response(
        url=f"https://seatemperature.info{full_path}",
        html='<html><body><p>Water temperature is 20 °C.</p></body></html>',
        status_code=200,
    )
    result = scrape_temperature("ocean-city", full_path=full_path)
    assert result is not None
    assert result["temp_c"] == pytest.approx(20.0, abs=0.01)
