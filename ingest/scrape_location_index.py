"""
Scrape-location spatial index — a one-time geocoding backfill of every
scrape-source slug already known in location_aliases, used as the last-resort
tier in coordinate resolution (api/main.py's resolve_coordinates) for
coordinates with no nearby USGS/NOAA station.

seatemperature.info pages expose no coordinates of their own (confirmed: no
JSON-LD geo data, no map embed, no meta tags), so this can't be scraped —
each slug's display name is geocoded via ingest/geocode_ingest.py instead.

This is a manual/occasional backfill, not a TTL-cycled ingest — same posture
as ingest/noaa_station_index.py. Run standalone:
    python -m ingest.scrape_location_index
"""
import os
import re
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from ingest.geo import haversine_km
from ingest.geocode_ingest import geocode_location
from ingest.sea_temp_scraper import HEADERS, build_url

log = logging.getLogger(__name__)

DB_PATH = os.environ.get("DB_PATH", "fishing.db")


# ---------------------------------------------------------------------------
# Slug enumeration
# ---------------------------------------------------------------------------

def enumerate_scrape_slugs(conn: sqlite3.Connection) -> list[str]:
    """Distinct scrape-source slugs from the live table — not ALIAS_SEED
    directly, since INSERT OR REPLACE collisions in init_db.py mean the seed
    array and the live table can diverge; the live table is the accurate
    source of truth for what's actually resolvable today."""
    rows = conn.execute(
        "SELECT DISTINCT site_id FROM location_aliases WHERE source = 'scrape'"
    ).fetchall()
    return [r[0] for r in rows]


# ---------------------------------------------------------------------------
# Backfill
# ---------------------------------------------------------------------------

_PAREN_PLACE_RE = re.compile(r"\(in [^,()]+, ([^()]+)\)")


def page_region(html: str) -> list[str]:
    """Region names for a seatemperature.info page, broadest first.

    Uses the breadcrumb ("Home > Senegal > Saint Louis" → ["Senegal"]). Lake hub
    pages have no country in the breadcrumb, so fall back to the countries in
    "(in Coppet, Switzerland)" style notes in the page copy.
    """
    soup = BeautifulSoup(html, "html.parser")
    crumb = soup.select_one("div.x21")
    if crumb:
        parts = [a.get_text(strip=True) for a in crumb.find_all("a")]
        parts = [p for p in parts if p and p.lower() != "home"]
        if parts:
            return parts
    m = _PAREN_PLACE_RE.search(soup.get_text(" ", strip=True))
    return [m.group(1).strip()] if m else []


def qualified_name(slug: str, html: Optional[str] = None) -> str:
    """'saint-louis' → 'Saint Louis, Senegal' so geocoding lands in the right country."""
    base = slug.replace("-", " ").title()
    if html is None:
        try:
            resp = httpx.get(build_url(slug), headers=HEADERS, timeout=15, follow_redirects=True)
            html = resp.text if resp.status_code == 200 else ""
        except httpx.HTTPError:
            html = ""
    region = page_region(html) if html else []
    if not region:
        return base
    # Most specific region, then country: "Boston, Massachusetts, United States"
    parts = [base, region[-1]]
    if region[0] != region[-1]:
        parts.append(region[0])
    return ", ".join(parts)


def backfill_scrape_location_index(conn: sqlite3.Connection) -> int:
    """
    Geocode every known scrape slug and upsert into scrape_location_index.
    Skips (logs, non-fatal) slugs that fail to geocode — some short/ambiguous
    names (e.g. 'portland') may geocode to the wrong place; accepted
    imprecision for v1, not blocking the rest of the backfill.

    Returns the number of rows written.
    """
    slugs = enumerate_scrape_slugs(conn)
    now_utc = datetime.now(timezone.utc).isoformat()
    written = 0

    for slug in slugs:
        site_name = slug.replace("-", " ").title()
        # Qualify with the page's country so e.g. 'saint-louis' (Senegal)
        # doesn't geocode to St. Louis, Missouri.
        coords = geocode_location(qualified_name(slug))
        if coords is None:
            log.info("Could not geocode scrape slug %r — skipping", slug)
            continue

        lat, lon = coords
        conn.execute(
            """INSERT INTO scrape_location_index (slug, site_name, lat, lon, fetched_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(slug) DO UPDATE SET
                   site_name  = excluded.site_name,
                   lat        = excluded.lat,
                   lon        = excluded.lon,
                   fetched_at = excluded.fetched_at""",
            (slug, site_name, lat, lon, now_utc),
        )
        conn.commit()
        written += 1

    return written


# ---------------------------------------------------------------------------
# Nearest-neighbor lookup
# ---------------------------------------------------------------------------

def find_nearest_scrape_location(conn: sqlite3.Connection, lat: float, lon: float,
                                  max_km: float = 150.0) -> Optional[dict]:
    """Linear scan over scrape_location_index. Returns
    {slug, site_name, lat, lon, distance_km} for the closest location within
    max_km, or None."""
    rows = conn.execute(
        "SELECT slug, site_name, lat, lon FROM scrape_location_index"
    ).fetchall()

    best = None
    best_dist = float("inf")
    for row in rows:
        dist = haversine_km(lat, lon, row["lat"], row["lon"])
        if dist < best_dist:
            best_dist = dist
            best = row

    if best is None or best_dist > max_km:
        return None

    return {
        "slug":        best["slug"],
        "site_name":   best["site_name"],
        "lat":         best["lat"],
        "lon":         best["lon"],
        "distance_km": round(best_dist, 2),
    }


# ---------------------------------------------------------------------------
# Main entry point — manual/occasional backfill, no TTL gate
# ---------------------------------------------------------------------------

def run_backfill() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    written = backfill_scrape_location_index(conn)
    conn.close()
    log.info("Scrape location index backfill complete — wrote %d locations.", written)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_backfill()
