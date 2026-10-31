"""
USGS site spatial index — a local snapshot of every active USGS surface-water
site that reports live water temperature (parameter 00010).

Coordinate lookups used to query the USGS Site Service live with a bounding
box on every request. That call regularly takes 10+ seconds and timed out, so
inland coordinates fell through to the wrong source. Same posture as
ingest/noaa_station_index.py: pull once, refresh manually/rarely, and do the
nearest-neighbor search locally.

Run standalone:
    python -m ingest.usgs_site_index
"""
import os
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from ingest.geo import haversine_km
from ingest.usgs_ingest import (
    USGS_API_KEY,
    USGS_SITE_SERVICE_URL,
    USGS_SURFACE_WATER_SITE_TYPES,
    parse_usgs_rdb,
)

log = logging.getLogger(__name__)

DB_PATH = os.environ.get("DB_PATH", "fishing.db")

# 50 states + DC + Puerto Rico + US Virgin Islands
STATE_CODES = [
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "dc", "fl", "ga", "hi", "id",
    "il", "in", "ia", "ks", "ky", "la", "me", "md", "ma", "mi", "mn", "ms", "mo",
    "mt", "ne", "nv", "nh", "nj", "nm", "ny", "nc", "nd", "oh", "ok", "or", "pa",
    "ri", "sc", "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv", "wi", "wy", "pr",
    "vi",
]


def fetch_usgs_sites_for_state(state_cd: str) -> list[dict]:
    params = {
        "format":        "rdb",
        "stateCd":       state_cd,
        "parameterCd":   "00010",
        "siteType":      USGS_SURFACE_WATER_SITE_TYPES,
        "hasDataTypeCd": "iv",
        "siteStatus":    "active",
    }
    headers = {"X-Api-Key": USGS_API_KEY}
    for attempt in range(3):
        try:
            resp = httpx.get(USGS_SITE_SERVICE_URL, params=params, headers=headers, timeout=120)
            if resp.status_code == 404:   # USGS returns 404 when a state has no matches
                return []
            resp.raise_for_status()
            return [{**s, "state": state_cd.upper()} for s in parse_usgs_rdb(resp.text)]
        except httpx.HTTPError as exc:
            log.warning("USGS site index %s failed (attempt %d/3): %s", state_cd, attempt + 1, exc)
    return []


def upsert_site_index(conn: sqlite3.Connection, sites: list[dict]) -> int:
    if not sites:
        return 0
    now_utc = datetime.now(timezone.utc).isoformat()
    conn.executemany(
        """INSERT INTO usgs_site_index (site_id, site_name, lat, lon, state, fetched_at)
           VALUES (:site_id, :site_name, :lat, :lon, :state, :fetched_at)
           ON CONFLICT(site_id) DO UPDATE SET
               site_name  = excluded.site_name,
               lat        = excluded.lat,
               lon        = excluded.lon,
               state      = excluded.state,
               fetched_at = excluded.fetched_at""",
        [{**s, "fetched_at": now_utc} for s in sites],
    )
    conn.commit()
    return len(sites)


def nearest_usgs_sites(conn: sqlite3.Connection, lat: float, lon: float,
                       max_km: float, limit: int = 3) -> Optional[list[dict]]:
    """Closest indexed sites within max_km, nearest first.

    Returns None (not []) when the index is empty, so callers can tell
    "index not built" apart from "nothing nearby".
    """
    rows = conn.execute("SELECT site_id, site_name, lat, lon FROM usgs_site_index").fetchall()
    if not rows:
        return None
    ranked = sorted(
        ({"site_id": r[0], "site_name": r[1], "lat": r[2], "lon": r[3],
          "distance_km": round(haversine_km(lat, lon, r[2], r[3]), 2)} for r in rows),
        key=lambda s: s["distance_km"],
    )
    return [s for s in ranked if s["distance_km"] <= max_km][:limit]


def run_site_index_refresh() -> None:
    conn = sqlite3.connect(DB_PATH)
    total = 0
    for state_cd in STATE_CODES:
        sites = fetch_usgs_sites_for_state(state_cd)
        total += upsert_site_index(conn, sites)
        log.info("USGS site index: %s → %d sites", state_cd.upper(), len(sites))
    conn.close()
    log.info("USGS site index refresh complete — wrote %d sites.", total)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_site_index_refresh()
