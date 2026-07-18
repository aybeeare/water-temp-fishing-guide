"""
NOAA CO-OPS station index — a one-time/occasional local mirror of every NOAA
station that reports a water-temperature sensor, used for coordinate-based
nearest-station lookup.

Unlike ingest/noaa_ingest.py (which fetches live readings on a 15-20min TTL
for a fixed set of stations), this module fetches the FULL station registry
from the metadata API and stores it locally, because:
  - NOAA CO-OPS has no server-side spatial (bbox/radius-by-coordinate) query,
    so nearest-neighbor search has to happen client-side against a local copy.
  - Station locations essentially never change, so there's no TTL — this is
    refreshed manually/rarely (see run_station_index_refresh), not per-request.

Metadata endpoint:
  https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json?type=watertemp

Results are written to noaa_station_index (site_id/name/lat/lon/state).
"""
import os
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from ingest.geo import haversine_km

log = logging.getLogger(__name__)

DB_PATH = os.environ.get("DB_PATH", "fishing.db")
NOAA_STATIONS_METADATA_URL = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json"


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def fetch_noaa_station_index() -> list[dict]:
    """Fetch every NOAA station with a water-temperature sensor.

    Returns [{station_id, site_name, lat, lon, state}, ...].
    """
    params = {"type": "watertemp"}
    last_exc = None
    for attempt in range(3):
        if attempt:
            import time
            time.sleep(0.5 * attempt)  # 0.5s, then 1s
        try:
            resp = httpx.get(NOAA_STATIONS_METADATA_URL, params=params, timeout=30)
            resp.raise_for_status()
            body = resp.json()
            break
        except httpx.HTTPError as exc:
            log.warning("NOAA station index HTTP error (attempt %d/3): %s", attempt + 1, exc)
            last_exc = exc
    else:
        log.error("NOAA station index fetch failed after 3 attempts: %s", last_exc)
        return []

    stations = []
    for st in body.get("stations", []):
        sid = st.get("id")
        lat = st.get("lat")
        lng = st.get("lng")
        if sid is None or lat is None or lng is None:
            continue
        stations.append({
            "station_id": sid,
            "site_name":  st.get("name") or sid,
            "lat":        float(lat),
            "lon":        float(lng),
            "state":      st.get("state"),
        })
    return stations


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------

def upsert_station_index(conn: sqlite3.Connection, stations: list[dict]) -> int:
    """Insert/update noaa_station_index rows. Returns the number written."""
    if not stations:
        return 0
    now_utc = datetime.now(timezone.utc).isoformat()
    conn.executemany(
        """INSERT INTO noaa_station_index (station_id, site_name, lat, lon, state, fetched_at)
           VALUES (:station_id, :site_name, :lat, :lon, :state, :fetched_at)
           ON CONFLICT(station_id) DO UPDATE SET
               site_name  = excluded.site_name,
               lat        = excluded.lat,
               lon        = excluded.lon,
               state      = excluded.state,
               fetched_at = excluded.fetched_at""",
        [{**s, "fetched_at": now_utc} for s in stations],
    )
    conn.commit()
    return len(stations)


# ---------------------------------------------------------------------------
# Nearest-neighbor lookup
# ---------------------------------------------------------------------------

def find_nearest_noaa_station(conn: sqlite3.Connection, lat: float, lon: float,
                               max_km: float = 80.0) -> Optional[dict]:
    """Linear scan over noaa_station_index (≤~250 rows — no spatial index needed).

    Returns {station_id, site_name, lat, lon, distance_km} for the closest
    station within max_km, or None if nothing qualifies.
    """
    rows = conn.execute(
        "SELECT station_id, site_name, lat, lon FROM noaa_station_index"
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
        "station_id":  best["station_id"],
        "site_name":   best["site_name"],
        "lat":         best["lat"],
        "lon":         best["lon"],
        "distance_km": round(best_dist, 2),
    }


# ---------------------------------------------------------------------------
# Main entry point — manual/occasional refresh, no TTL gate
# ---------------------------------------------------------------------------

def run_station_index_refresh() -> None:
    stations = fetch_noaa_station_index()
    if not stations:
        log.warning("No stations fetched — leaving existing noaa_station_index untouched.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    written = upsert_station_index(conn, stations)
    conn.close()
    log.info("NOAA station index refresh complete — wrote %d stations.", written)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_station_index_refresh()
