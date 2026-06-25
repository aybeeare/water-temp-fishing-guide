"""
NOAA CO-OPS ingestion — fetches real-time water temperature AND tide predictions
for coastal US stations. No API key required.

Water temperature endpoint:
  https://api.tidesandcurrents.noaa.gov/api/prod/datagetter
  ?product=water_temperature&station={id}&date=latest&units=english&time_zone=gmt&format=json

Tide predictions endpoint:
  https://api.tidesandcurrents.noaa.gov/api/prod/datagetter
  ?product=predictions&station={id}&date=today&datum=MLLW
  &units=english&time_zone=lst_ldt&interval=hilo&format=json

Results are written to:
  water_cache  — temperature (same schema as USGS entries)
  tide_cache   — today's high/low predictions
"""
import os
import sqlite3
import logging
from datetime import datetime, timezone, date
from typing import Optional

import httpx

log = logging.getLogger(__name__)

DB_PATH          = os.environ.get("DB_PATH", "fishing.db")
NOAA_BASE        = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
CACHE_TTL_MINUTES = 20
APP_NAME         = "FishingGuideSkill"

# ---------------------------------------------------------------------------
# NOAA station registry
# Each entry: (station_id, display_name)
# Find more at: https://tidesandcurrents.noaa.gov/stations.html
# ---------------------------------------------------------------------------
NOAA_STATIONS: list[tuple[str, str]] = [
    # ── Northeast ────────────────────────────────────────────────────────
    ("8443970",  "Boston Harbor, MA"),
    ("8461490",  "New London, CT"),
    ("8510560",  "Montauk, NY"),
    ("8516945",  "Sandy Hook, NJ"),
    ("8518750",  "The Battery, New York Harbor, NY"),
    ("8534720",  "Atlantic City, NJ"),
    ("8557380",  "Lewes, DE"),
    # ── Mid-Atlantic ─────────────────────────────────────────────────────
    ("8570283",  "Ocean City, MD"),
    ("8575512",  "Annapolis, MD"),
    ("8638610",  "Sewells Point, VA"),
    # ── Southeast ────────────────────────────────────────────────────────
    ("8651370",  "Duck, NC"),
    ("8656483",  "Beaufort, NC"),
    ("8661070",  "Springmaid Pier, SC"),
    ("8665530",  "Charleston, SC"),
    ("8670870",  "Fort Pulaski, GA"),
    ("8720218",  "Mayport, FL"),
    ("8723214",  "Virginia Key, FL"),
    ("8724580",  "Key West, FL"),
    ("8725520",  "Fort Myers, FL"),
    ("8726520",  "St. Petersburg, FL"),
    ("8727520",  "Cedar Key, FL"),
    # ── Gulf Coast ───────────────────────────────────────────────────────
    ("8735180",  "Dauphin Island, AL"),
    ("8761724",  "Grand Isle, LA"),
    ("8771341",  "Galveston Bay Entrance, TX"),
    ("8771450",  "Galveston Pier 21, TX"),
    ("8775870",  "Rockport, TX"),
    ("8779748",  "South Padre Island, TX"),
    # ── West Coast ───────────────────────────────────────────────────────
    ("9410170",  "San Diego, CA"),
    ("9410230",  "La Jolla, CA"),
    ("9410840",  "Santa Monica, CA"),
    ("9413450",  "Monterey, CA"),
    ("9414290",  "San Francisco, CA"),
    ("9415020",  "Point Reyes, CA"),
    ("9419750",  "Crescent City, CA"),
    ("9435380",  "South Beach (Newport), OR"),
    ("9439040",  "Astoria, OR"),
    ("9444900",  "Port Townsend, WA"),
    ("9447130",  "Seattle, WA"),
    ("9449880",  "Friday Harbor, WA"),
    # ── Alaska ───────────────────────────────────────────────────────────
    ("9452210",  "Juneau, AK"),
    ("9455920",  "Anchorage, AK"),
    ("9461380",  "Kodiak, AK"),
    # ── Hawaii ───────────────────────────────────────────────────────────
    ("1612340",  "Honolulu, HI"),
    ("1617760",  "Kahului (Maui), HI"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _common_params(station_id: str) -> dict:
    return {
        "station":     station_id,
        "units":       "english",
        "format":      "json",
        "application": APP_NAME,
    }


def fetch_noaa_temperature(station_id: str) -> Optional[dict]:
    """Returns {temp_f, raw_datetime} or None if sensor unavailable."""
    params = {
        **_common_params(station_id),
        "product":   "water_temperature",
        "date":      "latest",
        "time_zone": "gmt",
    }
    last_exc = None
    for attempt in range(3):
        if attempt:
            import time
            time.sleep(0.5 * attempt)  # 0.5s, then 1s
        try:
            resp = httpx.get(NOAA_BASE, params=params, timeout=10)
            resp.raise_for_status()
            body = resp.json()
            break
        except httpx.HTTPError as exc:
            log.warning("NOAA temp HTTP error for %s (attempt %d/3): %s", station_id, attempt + 1, exc)
            last_exc = exc
    else:
        log.error("NOAA temp failed after 3 attempts for %s: %s", station_id, last_exc)
        return None

    if "error" in body:
        log.warning("NOAA temp unavailable for %s: %s", station_id, body["error"].get("message"))
        return None

    data = body.get("data", [])
    if not data:
        return None

    try:
        temp_f = float(data[-1]["v"])
        raw_dt = data[-1]["t"]
        temp_c = round((temp_f - 32) * 5 / 9, 2)
        return {"temp_f": round(temp_f, 1), "temp_c": temp_c, "raw_datetime": raw_dt}
    except (KeyError, ValueError, IndexError) as exc:
        log.error("NOAA temp parse error for %s: %s", station_id, exc)
        return None


def fetch_noaa_tides(station_id: str) -> list[dict]:
    """Returns list of {tide_type, tide_time, height_ft} for today, or []."""
    params = {
        **_common_params(station_id),
        "product":   "predictions",
        "date":      "today",
        "datum":     "MLLW",
        "time_zone": "lst_ldt",
        "interval":  "hilo",
    }
    last_exc = None
    for attempt in range(3):
        if attempt:
            import time
            time.sleep(0.5 * attempt)
        try:
            resp = httpx.get(NOAA_BASE, params=params, timeout=10)
            resp.raise_for_status()
            body = resp.json()
            break
        except httpx.HTTPError as exc:
            log.warning("NOAA tides HTTP error for %s (attempt %d/3): %s", station_id, attempt + 1, exc)
            last_exc = exc
    else:
        log.error("NOAA tides failed after 3 attempts for %s: %s", station_id, last_exc)
        return []

    if "error" in body:
        log.warning("NOAA tides unavailable for %s: %s", station_id, body["error"].get("message"))
        return []

    tides = []
    for entry in body.get("predictions", []):
        try:
            tides.append({
                "tide_type":  entry["type"],          # 'H' or 'L'
                "tide_time":  entry["t"],              # e.g. "2024-06-23 06:42"
                "height_ft":  round(float(entry["v"]), 2),
            })
        except (KeyError, ValueError):
            continue
    return tides


def is_cache_fresh(conn: sqlite3.Connection, station_id: str) -> bool:
    row = conn.execute(
        "SELECT fetched_at FROM water_cache WHERE site_id = ?", (station_id,)
    ).fetchone()
    if not row:
        return False
    try:
        fetched = datetime.fromisoformat(row[0])
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - fetched).total_seconds() / 60 < CACHE_TTL_MINUTES
    except ValueError:
        return False


def upsert_temperature(conn: sqlite3.Connection, station_id: str,
                        site_name: str, temp_data: Optional[dict]) -> None:
    now_utc = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """INSERT INTO water_cache (site_id, site_name, temp_f, temp_c, fetched_at, raw_datetime)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(site_id) DO UPDATE SET
               site_name    = excluded.site_name,
               temp_f       = excluded.temp_f,
               temp_c       = excluded.temp_c,
               fetched_at   = excluded.fetched_at,
               raw_datetime = excluded.raw_datetime""",
        (
            station_id, site_name,
            temp_data["temp_f"]       if temp_data else None,
            temp_data["temp_c"]       if temp_data else None,
            now_utc,
            temp_data["raw_datetime"] if temp_data else None,
        ),
    )


def upsert_tides(conn: sqlite3.Connection, station_id: str, tides: list[dict]) -> None:
    if not tides:
        return
    today     = date.today().isoformat()
    now_utc   = datetime.now(timezone.utc).isoformat()
    # Clear today's existing predictions for this station before reinserting
    conn.execute(
        "DELETE FROM tide_cache WHERE site_id = ? AND tide_date = ?",
        (station_id, today),
    )
    conn.executemany(
        """INSERT INTO tide_cache (site_id, tide_type, tide_time, height_ft, fetched_at, tide_date)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [(station_id, t["tide_type"], t["tide_time"], t["height_ft"], now_utc, today)
         for t in tides],
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_noaa_ingest(stations: list[tuple[str, str]] = NOAA_STATIONS) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    refreshed = 0
    for station_id, site_name in stations:
        if is_cache_fresh(conn, station_id):
            continue

        temp_data = fetch_noaa_temperature(station_id)
        tides     = fetch_noaa_tides(station_id)

        upsert_temperature(conn, station_id, site_name, temp_data)
        upsert_tides(conn, station_id, tides)
        refreshed += 1

    conn.commit()
    conn.close()

    if refreshed:
        log.info("NOAA ingest complete — refreshed %d stations.", refreshed)
    else:
        log.info("NOAA ingest — all stations fresh, nothing to fetch.")


def run_noaa_ingest_for(station_id: str, site_name: str) -> None:
    """Fetch a single station on demand (called by the API when cache is cold)."""
    conn = sqlite3.connect(DB_PATH)
    temp_data = fetch_noaa_temperature(station_id)
    tides     = fetch_noaa_tides(station_id)
    upsert_temperature(conn, station_id, site_name, temp_data)
    upsert_tides(conn, station_id, tides)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    run_noaa_ingest()
