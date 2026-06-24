"""
Fallback scraper for seatemperature.info — used when a location has no USGS
station or as a global coverage complement (saltwater, international bodies).

URL patterns on seatemperature.info:
  Standard:       /{slug}-water-temperature.html
  State-qualified: /united-states/{state}/{slug}-water-temperature.html

Results are written into water_cache using the slug as site_id so the same
caching/staleness logic applies as for USGS data.
"""
import os
import re
import sqlite3
import logging
from datetime import datetime, timezone, date
from typing import Optional

import httpx
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)

DB_PATH       = os.environ.get("DB_PATH", "fishing.db")
BASE_URL      = "https://seatemperature.info"
CACHE_TTL_MINUTES = 30   # scraping is slower/less reliable — longer TTL
HEADERS       = {"User-Agent": "Mozilla/5.0 (compatible; FishingGuideBot/1.0)"}

# ---------------------------------------------------------------------------
# Disambiguation: slugs that 404 because the site needs a state qualifier.
# Maps slug → list of {path, name} options.
# ---------------------------------------------------------------------------
DISAMBIGUATION: dict[str, list[dict]] = {
    "ocean-city": [
        {"path": "/united-states/maryland/ocean-city-water-temperature.html",     "name": "Ocean City, Maryland"},
        {"path": "/united-states/new-jersey/ocean-city-water-temperature.html",   "name": "Ocean City, New Jersey"},
    ],
    "newport": [
        {"path": "/united-states/rhode-island/newport-water-temperature.html",    "name": "Newport, Rhode Island"},
        {"path": "/united-states/oregon/newport-water-temperature.html",          "name": "Newport, Oregon"},
    ],
    "long-beach": [
        {"path": "/united-states/california/long-beach-water-temperature.html",   "name": "Long Beach, California"},
        {"path": "/united-states/new-york/long-beach-water-temperature.html",     "name": "Long Beach, New York"},
    ],
    "portland": [
        {"path": "/united-states/maine/portland-water-temperature.html",          "name": "Portland, Maine"},
        {"path": "/united-states/oregon/portland-water-temperature.html",         "name": "Portland, Oregon"},
    ],
    "clearwater": [
        {"path": "/united-states/florida/clearwater-water-temperature.html",      "name": "Clearwater, Florida"},
        {"path": "/united-states/washington/clearwater-water-temperature.html",   "name": "Clearwater, Washington"},
    ],
    "gloucester": [
        {"path": "/united-states/massachusetts/gloucester-water-temperature.html","name": "Gloucester, Massachusetts"},
        {"path": "/united-states/virginia/gloucester-water-temperature.html",     "name": "Gloucester, Virginia"},
    ],
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slug_from_name(name: str) -> str:
    """'Lake Tahoe' → 'lake-tahoe'"""
    return re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")


def build_url(slug: str) -> str:
    return f"{BASE_URL}/{slug}-water-temperature.html"


def celsius_to_fahrenheit(c: float) -> float:
    return round(c * 9 / 5 + 32, 1)


def parse_temperature(text: str) -> Optional[dict]:
    """Return {temp_f, temp_c} from a text fragment, or None."""
    if not text:
        return None
    text = text.strip()

    # Explicit °C value
    m = re.search(r"(\d{1,3}(?:\.\d)?)\s*°?\s*C\b", text, re.IGNORECASE)
    if m:
        temp_c = float(m.group(1))
        return {"temp_c": round(temp_c, 2), "temp_f": celsius_to_fahrenheit(temp_c)}

    # Explicit °F value (2–3 digit to avoid false matches)
    m = re.search(r"(\d{2,3}(?:\.\d)?)\s*°?\s*F\b", text, re.IGNORECASE)
    if m:
        temp_f = float(m.group(1))
        temp_c = round((temp_f - 32) * 5 / 9, 2)
        return {"temp_f": round(temp_f, 1), "temp_c": temp_c}

    return None


def extract_temperature(html: str) -> Optional[dict]:
    """Three-strategy extraction matching the original Node.js waterScraper logic."""
    soup = BeautifulSoup(html, "html.parser")

    # Strategy 1 — explicit CSS selectors
    for selector in [
        ".current-temp", "#current-temp",
        ".temperature",  "#temperature",
        ".temp-value",   ".sea-temp",
        ".water-temp",   ".today-temp",
    ]:
        el = soup.select_one(selector)
        if el:
            result = parse_temperature(el.get_text())
            if result:
                return result

    # Strategy 2 — degree symbols in full body text
    body_text = soup.get_text(" ", strip=True)
    result = parse_temperature(body_text)
    if result:
        return result

    # Strategy 3 — table row containing "today / current / now"
    for row in soup.find_all("tr"):
        row_text = row.get_text()
        if not re.search(r"today|current|now", row_text, re.IGNORECASE):
            continue
        for td in row.find_all("td"):
            result = parse_temperature(td.get_text())
            if result:
                return result

    return None


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def get_disambiguation_options(slug: str) -> Optional[list[dict]]:
    """Return list of {path, name} if the slug is ambiguous, else None."""
    return DISAMBIGUATION.get(slug)


def scrape_temperature(slug: str, full_path: Optional[str] = None) -> Optional[dict]:
    """
    Fetch and parse a water temperature page.

    Args:
        slug:      location slug (e.g. 'lake-tahoe')
        full_path: override URL path for disambiguated locations
                   (e.g. '/united-states/maryland/ocean-city-water-temperature.html')

    Returns:
        {temp_f, temp_c, site_name, slug} or None on failure / 404.
    """
    url = f"{BASE_URL}{full_path}" if full_path else build_url(slug)
    site_name = full_path.split("/")[-1].replace("-water-temperature.html", "").replace("-", " ").title() \
                if full_path else slug.replace("-", " ").title()

    try:
        resp = httpx.get(url, headers=HEADERS, timeout=10,
                         follow_redirects=True,
                         # treat 4xx as non-exception so we can inspect status
                         )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        log.error("HTTP error scraping %s: %s", url, exc)
        return None

    result = extract_temperature(resp.text)
    if result is None:
        log.warning("Could not parse temperature from %s", url)
        return None

    return {**result, "site_name": site_name, "slug": slug}


def scrape_and_cache(slug: str, full_path: Optional[str] = None) -> Optional[dict]:
    """
    Scrape temperature and write it into water_cache.
    Returns the temperature dict or None.
    """
    data = scrape_temperature(slug, full_path)
    if data is None:
        return None

    now_utc = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT INTO water_cache (site_id, site_name, temp_f, temp_c, fetched_at, raw_datetime)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(site_id) DO UPDATE SET
               site_name  = excluded.site_name,
               temp_f     = excluded.temp_f,
               temp_c     = excluded.temp_c,
               fetched_at = excluded.fetched_at,
               raw_datetime = excluded.raw_datetime""",
        (slug, data["site_name"], data["temp_f"], data["temp_c"], now_utc, now_utc),
    )
    conn.commit()
    conn.close()
    log.info("Scraped and cached %s → %.1f°F", slug, data["temp_f"])
    return data


# ---------------------------------------------------------------------------
# Tide scraping
# ---------------------------------------------------------------------------

# Matches: "Low tide ⬇ 12:48 AM (00:48), Height: 0.79 ft"
#          "High tide ⬆ 6:58 AM (06:58), Height: 8.37 ft"
_TIDE_RE = re.compile(
    r'(Low|High)\s+tide\s+[⬇⬆]\s+\d{1,2}:\d{2}\s+[AP]M\s+\((\d{2}:\d{2})\)'
    r',\s+Height:\s+([\d.]+)\s+ft',
    re.IGNORECASE | re.UNICODE,
)


def scrape_tides(slug: str) -> list[dict]:
    """
    Fetch today's tides from seatemperature.info/{slug}-tides.html.
    Returns [{tide_type, tide_time, height_ft}] or [] on failure / no data.
    """
    url = f"{BASE_URL}/{slug}-tides.html"
    try:
        resp = httpx.get(url, headers=HEADERS, timeout=10, follow_redirects=True)
        if resp.status_code != 200:
            return []
    except httpx.HTTPError as exc:
        log.warning("Tide scrape failed for %s: %s", slug, exc)
        return []

    # Tide data spans multiple HTML elements — parse to plain text first
    text  = BeautifulSoup(resp.text, "html.parser").get_text(" ", strip=True)
    today = date.today().isoformat()
    tides = []
    for m in _TIDE_RE.finditer(text):
        tides.append({
            "tide_type": "H" if m.group(1).lower() == "high" else "L",
            "tide_time": f"{today} {m.group(2)}",
            "height_ft": float(m.group(3)),
        })
    return tides


def is_cache_fresh(slug: str) -> bool:
    """True if water_cache has a recent scrape entry for this slug."""
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT fetched_at FROM water_cache WHERE site_id = ?", (slug,)
    ).fetchone()
    conn.close()
    if not row:
        return False
    try:
        fetched = datetime.fromisoformat(row[0])
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - fetched).total_seconds() / 60
        return age < CACHE_TTL_MINUTES
    except ValueError:
        return False
