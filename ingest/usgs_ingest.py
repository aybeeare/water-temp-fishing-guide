"""
USGS Water Data ingestion — fetches real-time water temperature (parameter
code 00010) for a configured list of site IDs and caches results in SQLite.

Run on a schedule (e.g. every 15 minutes via cron or APScheduler) so the
API delivery layer always reads from cache rather than hitting USGS live.

USGS Instantaneous Values endpoint:
  https://waterservices.usgs.gov/nwis/iv/
  ?sites=<comma-separated-site-ids>
  &parameterCd=00010
  &format=json

api.data.gov key provides up to 1,000 requests/hour free of charge.
Set the key in the environment:  export USGS_API_KEY=your_key_here
"""
import os
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_PATH     = os.environ.get("DB_PATH", "fishing.db")
USGS_API_KEY = os.environ.get("USGS_API_KEY", "DEMO_KEY")  # replace before prod

USGS_IV_URL = "https://waterservices.usgs.gov/nwis/iv/"

# Add / remove site IDs here.  Find IDs at https://waterdata.usgs.gov/nwis
TARGET_SITES: list[str] = [
    "04085427",  # Lake Michigan at Milwaukee, WI
    "04085068",  # Lake Michigan near Calumet, IL
    "040851385", # Lake Superior at Duluth, MN
    "04002000",  # Lake Superior near Sault Ste. Marie
    "04010500",  # Lake Superior at Portage Entry, MI
    "04063700",  # Lake Huron at Mackinaw City, MI
    "04124000",  # Lake Michigan at Muskegon, MI
    "04173500",  # Lake Erie at Toledo, OH
    "04214500",  # Lake Erie at Buffalo, NY
    "04240010",  # Lake Ontario at Oswego, NY
    "01372500",  # Hudson River at Poughkeepsie, NY
    "01646500",  # Potomac River (Chesapeake watershed), MD
    "02084557",  # Neuse River (NC coastal)
    "07010000",  # Mississippi River at St. Louis, MO
    "06935965",  # Missouri River at Hermann, MO
    "03612500",  # Ohio River at Metropolis, IL
    "09380000",  # Colorado River at Lees Ferry, AZ
    "12472600",  # Columbia River at Vernita, WA
    "14211720",  # Willamette River at Portland, OR
    "11447650",  # Sacramento River at Freeport, CA
    "02232500",  # St. Johns River, FL (near Lake George)
    "02306647",  # Tampa Bay tributary, FL
    "08116650",  # San Jacinto River (Galveston Bay watershed), TX
]

CACHE_TTL_MINUTES = 15  # do not re-fetch a site fresher than this

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def celsius_to_fahrenheit(c: float) -> float:
    return round(c * 9 / 5 + 32, 1)


def parse_usgs_response(data: dict) -> list[dict]:
    """Extract site_id, site_name, temp_c, temp_f, raw_datetime from USGS JSON."""
    results = []
    for ts in data.get("value", {}).get("timeSeries", []):
        try:
            site_id   = ts["sourceInfo"]["siteCode"][0]["value"]
            site_name = ts["sourceInfo"]["siteName"]
            values    = ts["values"][0]["value"]
            if not values:
                log.warning("No values returned for site %s", site_id)
                continue
            latest = values[-1]
            raw_val = latest.get("value")
            if raw_val is None or raw_val == "-999999":
                log.warning("Sensor offline for site %s", site_id)
                results.append({"site_id": site_id, "site_name": site_name,
                                 "temp_c": None, "temp_f": None,
                                 "raw_datetime": latest.get("dateTime")})
                continue
            temp_c = float(raw_val)
            results.append({
                "site_id":      site_id,
                "site_name":    site_name,
                "temp_c":       round(temp_c, 2),
                "temp_f":       celsius_to_fahrenheit(temp_c),
                "raw_datetime": latest.get("dateTime"),
            })
        except (KeyError, IndexError, ValueError) as exc:
            log.error("Parse error on time series entry: %s", exc)
    return results


def sites_needing_refresh(conn: sqlite3.Connection, site_ids: list[str]) -> list[str]:
    """Return site IDs whose cache is older than CACHE_TTL_MINUTES or missing."""
    placeholders = ",".join("?" * len(site_ids))
    rows = conn.execute(
        f"""SELECT site_id, fetched_at FROM water_cache
            WHERE site_id IN ({placeholders})""",
        site_ids,
    ).fetchall()
    cached = {r[0]: r[1] for r in rows}
    now   = datetime.now(timezone.utc)
    stale = []
    for sid in site_ids:
        if sid not in cached:
            stale.append(sid)
            continue
        try:
            fetched = datetime.fromisoformat(cached[sid])
            if fetched.tzinfo is None:
                fetched = fetched.replace(tzinfo=timezone.utc)
            age_minutes = (now - fetched).total_seconds() / 60
            if age_minutes >= CACHE_TTL_MINUTES:
                stale.append(sid)
        except ValueError:
            stale.append(sid)
    return stale


def fetch_usgs(site_ids: list[str]) -> Optional[dict]:
    params = {
        "sites":       ",".join(site_ids),
        "parameterCd": "00010",
        "format":      "json",
    }
    headers = {"X-Api-Key": USGS_API_KEY}
    try:
        resp = httpx.get(USGS_IV_URL, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPError as exc:
        log.error("USGS HTTP error: %s", exc)
        return None


def upsert_cache(conn: sqlite3.Connection, records: list[dict]) -> None:
    now_utc = datetime.now(timezone.utc).isoformat()
    conn.executemany(
        """INSERT INTO water_cache (site_id, site_name, temp_f, temp_c, fetched_at, raw_datetime)
           VALUES (:site_id, :site_name, :temp_f, :temp_c, :fetched_at, :raw_datetime)
           ON CONFLICT(site_id) DO UPDATE SET
               site_name    = excluded.site_name,
               temp_f       = excluded.temp_f,
               temp_c       = excluded.temp_c,
               fetched_at   = excluded.fetched_at,
               raw_datetime = excluded.raw_datetime""",
        [{**r, "fetched_at": now_utc} for r in records],
    )
    conn.commit()


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_ingest(site_ids: list[str] = TARGET_SITES) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    stale = sites_needing_refresh(conn, site_ids)
    if not stale:
        log.info("All %d sites are fresh — skipping fetch.", len(site_ids))
        conn.close()
        return

    log.info("Fetching %d stale / new sites from USGS …", len(stale))

    # USGS accepts up to 100 sites per request; chunk if needed.
    CHUNK = 100
    all_records: list[dict] = []
    for i in range(0, len(stale), CHUNK):
        chunk = stale[i : i + CHUNK]
        data  = fetch_usgs(chunk)
        if data:
            all_records.extend(parse_usgs_response(data))

    if all_records:
        upsert_cache(conn, all_records)
        log.info("Cached %d temperature readings.", len(all_records))
    else:
        log.warning("No records returned from USGS.")

    conn.close()


if __name__ == "__main__":
    run_ingest()
