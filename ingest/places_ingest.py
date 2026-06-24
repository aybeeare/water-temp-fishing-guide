"""
Google Places Nearby Search — finds the closest bait/tackle shop to a station
and caches the result for the day.

One API call per unique station per calendar day. A hard daily cap (DAILY_PLACES_LIMIT)
prevents runaway spend; the $200/month Google credit covers ~6,250 calls so the
default cap of 50/day stays well within the free tier.

Env vars:
  GOOGLE_PLACES_API_KEY   required for live lookups
  DAILY_PLACES_LIMIT      max Places API calls per day (default: 50)
"""
import os
import sqlite3
import logging
from datetime import date
from typing import Optional

import httpx

log = logging.getLogger(__name__)

DB_PATH          = os.environ.get("DB_PATH", "fishing.db")
API_KEY          = os.environ.get("GOOGLE_PLACES_API_KEY", "")
MAX_DAILY_CALLS  = int(os.environ.get("DAILY_PLACES_LIMIT", "50"))
SEARCH_RADIUS_M  = 16000   # 10 miles
PLACES_URL       = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

# ---------------------------------------------------------------------------
# Station coordinates — lat/lng for NOAA and major USGS stations.
# Used as the search origin for the Places API call.
# ---------------------------------------------------------------------------
STATION_COORDS: dict[str, tuple[float, float]] = {
    # ── NOAA coastal stations ──────────────────────────────────────────────
    "8443970": (42.3584, -71.0522),   # Boston Harbor, MA
    "8461490": (41.3554, -72.0950),   # New London, CT
    "8510560": (41.0707, -71.9601),   # Montauk, NY
    "8516945": (40.4668, -74.0094),   # Sandy Hook, NJ
    "8518750": (40.6996, -74.0133),   # New York Harbor, NY
    "8519483": (40.6426, -73.6208),   # Freeport, NY
    "8531680": (40.4702, -74.0099),   # Perth Amboy, NJ
    "8534720": (39.3550, -74.4183),   # Atlantic City, NJ
    "8557380": (38.7814, -75.1190),   # Lewes, DE
    "8570283": (38.5763, -76.0677),   # Chesapeake Bay Bridge, MD
    "8594900": (38.8726, -77.0217),   # Washington DC
    "8638610": (36.9468, -76.3302),   # Sewells Point, VA
    "8651370": (35.9083, -75.6674),   # Duck, NC
    "8656483": (34.2275, -77.7943),   # Wilmington, NC
    "8658120": (34.7106, -76.6697),   # Beaufort, NC
    "8661070": (33.6553, -78.9280),   # Springmaid Pier, SC
    "8665530": (32.7816, -79.9256),   # Charleston, SC
    "8670870": (32.0366, -80.9001),   # Fort Pulaski, GA
    "8720218": (30.3939, -81.5978),   # Jacksonville, FL
    "8723214": (25.7617, -80.1918),   # Miami, FL
    "8724580": (24.5551, -81.8068),   # Key West, FL
    "8725520": (26.6479, -81.8679),   # Fort Myers, FL
    "8726520": (27.7676, -82.6272),   # Tampa Bay, FL
    "8727520": (29.1319, -83.0318),   # Cedar Key, FL
    "8735180": (30.2503, -88.0748),   # Dauphin Island, AL
    "8747437": (30.3606, -89.0928),   # Bay Waveland, MS
    "8761724": (29.2633, -89.9571),   # Grand Isle, LA
    "8764227": (29.7628, -91.8377),   # Cypremort Point, LA
    "8771450": (29.3013, -94.7977),   # Galveston, TX
    "8775870": (28.0208, -97.0472),   # Rockport, TX
    "8779748": (26.0640, -97.1571),   # South Padre Island, TX
    "9410170": (32.7142, -117.1736),  # San Diego, CA
    "9410230": (32.8669, -117.2571),  # La Jolla, CA
    "9410840": (33.7200, -118.2720),  # Santa Monica, CA
    "9413450": (36.6051, -121.8925),  # Monterey, CA
    "9414290": (37.8063, -122.4650),  # San Francisco, CA
    "9415020": (38.2233, -122.9543),  # Point Reyes, CA
    "9419750": (41.7456, -124.1836),  # Crescent City, CA
    "9435380": (44.6244, -124.0519),  # Newport, OR
    "9439040": (46.2076, -123.7693),  # Astoria, OR
    "9444900": (48.1126, -122.7593),  # Port Townsend, WA
    "9447130": (47.6026, -122.3393),  # Seattle, WA
    "9449880": (48.5148, -122.6131),  # Anacortes, WA
    "9452210": (57.0514, -135.3361),  # Sitka, AK
    "9455920": (59.4469, -151.7286),  # Homer, AK
    "1612340": (21.3069, -157.8583),  # Honolulu, HI
    "1617760": (20.8947, -156.4700),  # Kahului, Maui, HI
    # ── Great Lakes NOAA ───────────────────────────────────────────────────
    "9063020": (42.8789, -78.8911),   # Buffalo, NY
    "9052000": (43.9625, -76.4696),   # Oswego, NY
    "9044020": (42.3350, -83.0458),   # Detroit, MI
    "9075080": (46.5009, -84.3478),   # Sault Ste. Marie, MI
    "9087044": (43.0643, -86.2178),   # Muskegon, MI
    "9099004": (46.7697, -92.0942),   # Duluth, MN
    # ── USGS freshwater stations ───────────────────────────────────────────
    "04085427": (44.0170, -86.2428),  # Lake Michigan at Milwaukee, WI
    "04085068": (43.0681, -87.8973),  # Menomonee River, WI
    "03290500": (38.2542, -85.7669),  # Ohio River at Louisville, KY
    "01646500": (38.9478, -77.1217),  # Potomac River, DC
    "08279500": (36.5767, -105.6492), # Rio Grande, NM
    "09380000": (36.8631, -111.5878), # Colorado River, AZ
    "14211720": (45.5234, -122.6762), # Willamette River, OR
    "12114500": (47.5712, -122.1934), # Cedar River, WA
}


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

def _get_daily_count(conn: sqlite3.Connection) -> int:
    today = date.today().isoformat()
    row = conn.execute(
        "SELECT call_count FROM api_call_log WHERE api_name='google_places' AND call_date=?",
        (today,),
    ).fetchone()
    return row[0] if row else 0


def _increment_count(conn: sqlite3.Connection) -> None:
    today = date.today().isoformat()
    conn.execute(
        """INSERT INTO api_call_log (api_name, call_date, call_count) VALUES ('google_places', ?, 1)
           ON CONFLICT(api_name, call_date) DO UPDATE SET call_count = call_count + 1""",
        (today,),
    )


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def _get_cached_shop(conn: sqlite3.Connection, station_id: str) -> Optional[dict]:
    today = date.today().isoformat()
    row = conn.execute(
        "SELECT shop_name, shop_address, shop_rating, open_now FROM bait_shop_cache "
        "WHERE station_id = ? AND cached_date = ?",
        (station_id, today),
    ).fetchone()
    if not row:
        return None
    return {
        "name":    row["shop_name"],
        "address": row["shop_address"],
        "rating":  row["shop_rating"],
        "open_now": bool(row["open_now"]) if row["open_now"] is not None else None,
    }


def _cache_shop(conn: sqlite3.Connection, station_id: str, shop: Optional[dict]) -> None:
    today = date.today().isoformat()
    if shop:
        conn.execute(
            """INSERT OR REPLACE INTO bait_shop_cache
               (station_id, shop_name, shop_address, shop_rating, open_now, cached_date)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (station_id, shop["name"], shop["address"],
             shop.get("rating"), 1 if shop.get("open_now") else 0, today),
        )
    else:
        # Cache a null result so we don't retry for this station today
        conn.execute(
            """INSERT OR REPLACE INTO bait_shop_cache
               (station_id, shop_name, shop_address, shop_rating, open_now, cached_date)
               VALUES (?, NULL, NULL, NULL, NULL, ?)""",
            (station_id, today),
        )


# ---------------------------------------------------------------------------
# Places API call
# ---------------------------------------------------------------------------

def _fetch_from_places(lat: float, lng: float) -> Optional[dict]:
    if not API_KEY:
        log.warning("GOOGLE_PLACES_API_KEY not set — skipping bait shop lookup")
        return None
    try:
        resp = httpx.get(
            PLACES_URL,
            params={
                "location":  f"{lat},{lng}",
                "radius":    SEARCH_RADIUS_M,
                "keyword":   "bait tackle fishing shop",
                "type":      "store",
                "key":       API_KEY,
            },
            timeout=5,
        )
        data = resp.json()
    except Exception as exc:
        log.warning("Google Places request failed: %s", exc)
        return None

    results = data.get("results", [])
    if not results:
        return None

    top = results[0]
    hours = top.get("opening_hours", {})
    return {
        "name":     top.get("name"),
        "address":  top.get("vicinity"),
        "rating":   top.get("rating"),
        "open_now": hours.get("open_now"),
    }


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def lookup_bait_shop(station_id: str) -> Optional[dict]:
    """
    Return the nearest bait/tackle shop for a station.
    Checks the daily cache first; only calls the Places API on a cache miss
    and if the daily call budget has not been exceeded.

    Returns {name, address, rating, open_now} or None.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cached = _get_cached_shop(conn, station_id)
    if cached is not None:
        conn.close()
        return cached if cached["name"] else None  # None name = cached miss

    coords = STATION_COORDS.get(station_id)
    if not coords:
        conn.close()
        return None

    daily_count = _get_daily_count(conn)
    if daily_count >= MAX_DAILY_CALLS:
        log.info("Daily Places API limit (%d) reached — skipping shop lookup", MAX_DAILY_CALLS)
        conn.close()
        return None

    _increment_count(conn)
    shop = _fetch_from_places(*coords)
    _cache_shop(conn, station_id, shop)
    conn.commit()
    conn.close()

    log.info("Places API: station %s → %s (%d calls today)",
             station_id, shop["name"] if shop else "no result", daily_count + 1)
    return shop


def format_shop_speech(shop: Optional[dict]) -> str:
    """Build a natural spoken mention of the nearby shop, or empty string."""
    if not shop or not shop.get("name"):
        return ""
    name    = shop["name"]
    address = shop.get("address", "")
    open_now = shop.get("open_now")

    if open_now is True:
        status = "open right now"
    elif open_now is False:
        status = "closed right now"
    else:
        status = None

    parts = [f"The nearest bait shop is {name}"]
    if address:
        parts.append(f"at {address}")
    if status:
        parts[0] = parts[0] + f", {status},"
    return " ".join(parts) + "."
