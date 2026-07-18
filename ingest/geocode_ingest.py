"""
Google Geocoding API — converts a raw location string into (lat, lon), used
as the last-resort fallback in api/main.py when both location_aliases and the
direct scrape-slug guess fail to resolve a string location.

Same Google Cloud key family as ingest/places_ingest.py (Geocoding and Places
are sibling Maps Platform APIs) — reuses GOOGLE_PLACES_API_KEY rather than a
new secret, but the Geocoding API must be separately enabled for that key in
Google Cloud Console (Maps Platform APIs are individually toggled per key even
when sharing authentication).

Rate-limited the same way as places_ingest.py: a daily counter row in
api_call_log (api_name='google_geocoding'), independent of the Places budget.

Env vars:
  GOOGLE_PLACES_API_KEY   required for live lookups (shared with Places)
  DAILY_GEOCODING_LIMIT   max Geocoding API calls per day (default: 50)
"""
import os
import sqlite3
import logging
from datetime import date
from typing import Optional

import httpx

log = logging.getLogger(__name__)

DB_PATH         = os.environ.get("DB_PATH", "fishing.db")
API_KEY         = os.environ.get("GOOGLE_PLACES_API_KEY", "")
MAX_DAILY_CALLS = int(os.environ.get("DAILY_GEOCODING_LIMIT", "50"))
GEOCODE_URL     = "https://maps.googleapis.com/maps/api/geocode/json"


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

def _get_daily_count(conn: sqlite3.Connection) -> int:
    today = date.today().isoformat()
    row = conn.execute(
        "SELECT call_count FROM api_call_log WHERE api_name='google_geocoding' AND call_date=?",
        (today,),
    ).fetchone()
    return row[0] if row else 0


def _increment_count(conn: sqlite3.Connection) -> None:
    today = date.today().isoformat()
    conn.execute(
        """INSERT INTO api_call_log (api_name, call_date, call_count) VALUES ('google_geocoding', ?, 1)
           ON CONFLICT(api_name, call_date) DO UPDATE SET call_count = call_count + 1""",
        (today,),
    )


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def geocode_location(query: str) -> Optional[tuple[float, float]]:
    """
    Convert a raw location string to (lat, lon) via the Geocoding API.

    Checks the daily call budget first; returns None without an HTTP call if
    the key is missing or the budget is exhausted. Returns None (not an
    exception) on any failure — a geocoding miss should degrade the caller to
    its existing 404, never crash the request.
    """
    if not API_KEY:
        log.warning("GOOGLE_PLACES_API_KEY not set — skipping geocoding")
        return None

    conn = sqlite3.connect(DB_PATH)
    daily_count = _get_daily_count(conn)
    if daily_count >= MAX_DAILY_CALLS:
        log.info("Daily Geocoding API limit (%d) reached — skipping geocode of %r", MAX_DAILY_CALLS, query)
        conn.close()
        return None

    _increment_count(conn)
    conn.commit()
    conn.close()

    try:
        resp = httpx.get(GEOCODE_URL, params={"address": query, "key": API_KEY}, timeout=10)
        data = resp.json()
    except Exception as exc:
        log.warning("Geocoding request failed for %r: %s", query, exc)
        return None

    if data.get("status") != "OK":
        log.info("Geocoding %r → status %s, no coordinates", query, data.get("status"))
        return None

    results = data.get("results", [])
    if not results:
        return None

    try:
        loc = results[0]["geometry"]["location"]
        return float(loc["lat"]), float(loc["lng"])
    except (KeyError, TypeError, ValueError) as exc:
        log.warning("Unexpected geocoding response shape for %r: %s", query, exc)
        return None
