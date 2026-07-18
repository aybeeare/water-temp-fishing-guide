"""
FastAPI delivery layer — serves Alexa+ AI Action orchestration requests.

Two ways to query:
  GET /fishing-guide?site_id=8443970        ← direct station lookup (USGS or NOAA)
  GET /fishing-guide?location=boston+harbor ← alias lookup → USGS / NOAA / scrape

Data sources by location type:
  USGS   → inland freshwater (rivers, Great Lakes, reservoirs)
  NOAA   → US coastal saltwater; also provides tide predictions
  scrape → international / open ocean fallback via seatemperature.info

Environment variables:
  DB_PATH                  path to SQLite file (default: fishing.db)
  ASSOCIATES_TRACKING_ID   Amazon Associates tag (default: yourstore-20)
"""
import os
import re
import sqlite3
import logging
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone, date
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP

from ingest.usgs_ingest import run_ingest, find_nearest_usgs_site
from ingest.noaa_ingest import run_noaa_ingest_for, NOAA_STATIONS, upsert_tides
from ingest.noaa_station_index import find_nearest_noaa_station
from ingest.scrape_location_index import find_nearest_scrape_location
from ingest.geocode_ingest import geocode_location
from ingest.sea_temp_scraper import (
    scrape_and_cache,
    scrape_tides,
    is_cache_fresh,
    get_disambiguation_options,
)
from ingest.places_ingest import lookup_bait_shop, format_shop_speech

log = logging.getLogger("uvicorn.error")

# MCP server defined before FastAPI app so lifespan can reference it
_fastmcp = FastMCP("water-conditions", host="0.0.0.0")


@asynccontextmanager
async def _lifespan(app: FastAPI):
    async with _fastmcp.session_manager.run():
        yield


app = FastAPI(title="Fishing Water Temp — Alexa+ AI Action API", version="1.2.0", lifespan=_lifespan)

DB_PATH                = os.environ.get("DB_PATH", "fishing.db")
ASSOCIATES_TRACKING_ID = os.environ.get("ASSOCIATES_TRACKING_ID", "yourstore-20")
ENABLE_BAIT_SHOP       = os.environ.get("ENABLE_BAIT_SHOP", "true").lower() == "true"
ACTIVITY_API_KEY       = os.environ.get("ACTIVITY_API_KEY", "")

# Build a quick lookup: noaa station_id → display_name
NOAA_STATION_NAMES = {sid: name for sid, name in NOAA_STATIONS}

# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class TidePrediction(BaseModel):
    tide_type:  str            # 'H' or 'L'
    tide_time:  str            # local time string, e.g. "2024-06-23 06:42"
    height_ft:  Optional[float]


class AlexaDirective(BaseModel):
    type:    str = "Connections.SendRequest"
    name:    str = "AddToShoppingCart"
    payload: dict
    token:   str = "fishing-guide-cart-token"


class DisambiguationOption(BaseModel):
    label: str
    slug:  str


class FishingGuideResponse(BaseModel):
    site_id:               str
    site_name:             str
    temp_f:                Optional[float]
    temp_c:                Optional[float]
    temp_f_min:            Optional[float]         = None
    temp_f_max:            Optional[float]         = None
    data_freshness:        str
    spoken_response:       str
    sponsor_script:        str
    recommended_gear:      Optional[str]                  = None
    nearby_shop:           Optional[dict]                 = None
    tides:                 Optional[list[TidePrediction]] = None
    alexa_directive:       Optional[AlexaDirective]       = None
    secondary_directive:   Optional[AlexaDirective]       = None
    secondary_gear:        Optional[str]                  = None
    disambiguation:        Optional[list[DisambiguationOption]] = None
    species:               Optional[list[str]]            = None
    distance_km:           Optional[float]                = None  # populated only when resolved via lat/lon
    resolved_via:          Optional[str]                  = None  # "coordinates" | "alias" | "site_id" | "geocoded"


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def normalize_location(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower().strip()).strip("-")


def lookup_alias(conn: sqlite3.Connection, alias: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT site_id, source FROM location_aliases WHERE alias = ?", (alias,)
    ).fetchone()


def lookup_water_cache(conn: sqlite3.Connection, site_id: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM water_cache WHERE site_id = ?", (site_id,)
    ).fetchone()


def lookup_tides(conn: sqlite3.Connection, site_id: str) -> list[sqlite3.Row]:
    today = date.today().isoformat()
    return conn.execute(
        """SELECT tide_type, tide_time, height_ft FROM tide_cache
           WHERE site_id = ? AND tide_date = ?
           ORDER BY tide_time ASC""",
        (site_id, today),
    ).fetchall()


def lookup_site_species(conn: sqlite3.Connection, site_id: str) -> list[str]:
    rows = conn.execute(
        "SELECT species FROM site_species WHERE site_id = ?", (site_id,)
    ).fetchall()
    return [r["species"] for r in rows]


def lookup_fishing_logic(conn: sqlite3.Connection, temp_f: float, water_type: str,
                         species_list: list[str] = None) -> Optional[sqlite3.Row]:
    if species_list:
        placeholders = ",".join("?" * len(species_list))
        return conn.execute(
            f"""SELECT * FROM fishing_logic
                WHERE temp_min_f <= ? AND temp_max_f >= ?
                  AND (water_type = ? OR water_type = 'any')
                  AND (target_species IN ({placeholders}) OR target_species IS NULL)
                ORDER BY (target_species IS NOT NULL) DESC, temp_min_f DESC
                LIMIT 1""",
            (temp_f, temp_f, water_type, *species_list),
        ).fetchone()
    return conn.execute(
        """SELECT * FROM fishing_logic
           WHERE temp_min_f <= ? AND temp_max_f >= ?
             AND (water_type = ? OR water_type = 'any')
             AND target_species IS NULL
           ORDER BY temp_min_f DESC LIMIT 1""",
        (temp_f, temp_f, water_type),
    ).fetchone()


def lookup_sponsor(conn: sqlite3.Connection, site_id: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT audio_script FROM local_sponsorships WHERE site_id = ? AND active = 1 LIMIT 1",
        (site_id,),
    ).fetchone()


def infer_water_type(site_name: str) -> str:
    saltwater_kw = ["ocean", "sea", "bay", "gulf", "sound", "inlet",
                    "estuary", "harbor", "strait", "channel", "lagoon", "beach", "key"]
    return "saltwater" if any(kw in site_name.lower() for kw in saltwater_kw) else "freshwater"


def build_shopping_directive(asin: str) -> AlexaDirective:
    return AlexaDirective(
        payload={
            "type":         "BuyShoppingProducts",
            "items":        [{"asin": asin, "quantity": 1}],
            "associatedId": ASSOCIATES_TRACKING_ID,
        }
    )


def format_tide_speech(tides: list) -> str:
    """Convert tide rows into a natural spoken sentence."""
    highs = [t for t in tides if t["tide_type"] == "H"]
    lows  = [t for t in tides if t["tide_type"] == "L"]

    def describe(t) -> str:
        time_part = t["tide_time"].split(" ")[-1] if " " in t["tide_time"] else t["tide_time"]
        return f"{time_part} at {t['height_ft']} feet" if t["height_ft"] else time_part

    parts = []
    if highs:
        times = " and ".join(describe(t) for t in highs)
        parts.append(f"high tide{'s' if len(highs) > 1 else ''} at {times}")
    if lows:
        times = " and ".join(describe(t) for t in lows)
        parts.append(f"low tide{'s' if len(lows) > 1 else ''} at {times}")

    if not parts:
        return ""
    return "Today's tides: " + ", and ".join(parts) + \
           ". Fish are most active in the two hours around each tide change."


def build_spoken_response(site_name: str, temp_f: float, temp_c: float,
                           logic: Optional[sqlite3.Row],
                           tides: list,
                           sponsor_script: str,
                           species_list: list[str] = None,
                           shop: dict = None) -> str:
    parts = [
        f"The current water temperature at {site_name} is "
        f"{temp_f} degrees Fahrenheit, or {temp_c} degrees Celsius."
    ]
    if species_list:
        readable = [s.replace("_", " ") for s in species_list[:3]]
        if len(readable) == 1:
            parts.append(f"The main species here is {readable[0]}.")
        else:
            parts.append(
                f"Common species here include {', '.join(readable[:-1])} and {readable[-1]}."
            )
    tide_speech = format_tide_speech(tides)
    if tide_speech:
        parts.append(tide_speech)
    shop_speech = format_shop_speech(shop)
    if shop_speech:
        parts.append(shop_speech)
    if sponsor_script:
        parts.append(sponsor_script)
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Resolution helpers — one per source type
# ---------------------------------------------------------------------------

async def resolve_usgs(site_id: str) -> Optional[sqlite3.Row]:
    conn = get_db()
    row  = lookup_water_cache(conn, site_id)
    conn.close()
    if row is None:
        run_ingest(site_ids=[site_id])
        conn = get_db()
        row  = lookup_water_cache(conn, site_id)
        conn.close()
    return row


async def resolve_noaa(site_id: str) -> Optional[sqlite3.Row]:
    conn = get_db()
    row  = lookup_water_cache(conn, site_id)
    conn.close()
    if row is None:
        site_name = NOAA_STATION_NAMES.get(site_id, site_id)
        run_noaa_ingest_for(site_id, site_name)
        conn = get_db()
        row  = lookup_water_cache(conn, site_id)
        conn.close()
    return row


async def resolve_scrape(slug: str) -> Optional[sqlite3.Row]:
    if not is_cache_fresh(slug):
        scrape_and_cache(slug)
    conn = get_db()
    row  = lookup_water_cache(conn, slug)
    conn.close()
    return row


NOAA_MAX_DISTANCE_KM   = float(os.environ.get("NOAA_MAX_DISTANCE_KM", "80"))
USGS_MAX_DISTANCE_KM   = float(os.environ.get("USGS_MAX_DISTANCE_KM", "50"))
SCRAPE_MAX_DISTANCE_KM = float(os.environ.get("SCRAPE_MAX_DISTANCE_KM", "150"))
USGS_NOAA_OVERRIDE_KM  = float(os.environ.get("USGS_NOAA_OVERRIDE_KM", "10"))


async def resolve_coordinates(lat: float, lon: float) -> tuple[str, str, float, str]:
    """
    Given a raw (lat, lon), find the nearest real water-temperature station
    across all sources and pick a winner.

    Queries USGS (live bBox) and NOAA (local station_index) — never blends a
    freshwater and saltwater reading. Each candidate is discarded outright if
    it exceeds its own source's max-distance threshold, so a mediocre
    in-range USGS match can't beat a NOAA candidate that was excluded for
    being just outside the NOAA threshold (they're evaluated independently
    before comparison, not against a shared cutoff).

    When both qualify, NOAA wins by default even if it's farther away — NOAA
    CO-OPS only instruments major coastal/tidal stations, never small ponds,
    so its mere presence is a signal this is a significant body of water.
    USGS's live bBox search has no such filter and can surface a municipal
    reservoir a few km away that would otherwise out-compete a real coastal
    station tens of km out on raw distance alone. USGS only overrides NOAA
    when it's within USGS_NOAA_OVERRIDE_KM — i.e. close enough that you're
    essentially at that specific lake/pond/river, not just "in the region."

    If neither USGS nor NOAA has a qualifying candidate, falls back to the
    nearest known scrape_location_index entry (mainly international/remote
    coverage with no government sensor nearby) before giving up.

    Returns (resolved_id, source, distance_km, site_name).
    Raises HTTPException(404) if nothing qualifies from any source.
    """
    conn = get_db()
    noaa_candidate = find_nearest_noaa_station(conn, lat, lon, max_km=NOAA_MAX_DISTANCE_KM)
    conn.close()

    usgs_candidate = find_nearest_usgs_site(lat, lon, max_km=USGS_MAX_DISTANCE_KM)

    if usgs_candidate is None and noaa_candidate is None:
        conn = get_db()
        scrape_candidate = find_nearest_scrape_location(conn, lat, lon, max_km=SCRAPE_MAX_DISTANCE_KM)
        conn.close()
        if scrape_candidate is None:
            raise HTTPException(
                status_code=404,
                detail=f"No water-temperature station found near ({lat}, {lon}).",
            )
        return (scrape_candidate["slug"], "scrape",
                scrape_candidate["distance_km"], scrape_candidate["site_name"])

    if usgs_candidate is None:
        winner, source = noaa_candidate, "noaa"
    elif noaa_candidate is None:
        winner, source = usgs_candidate, "usgs"
    elif (usgs_candidate["distance_km"] < noaa_candidate["distance_km"]
          and usgs_candidate["distance_km"] <= USGS_NOAA_OVERRIDE_KM):
        winner, source = usgs_candidate, "usgs"
    else:
        winner, source = noaa_candidate, "noaa"

    resolved_id = winner["station_id"] if source == "noaa" else winner["site_id"]
    return resolved_id, source, winner["distance_km"], winner["site_name"]


# ---------------------------------------------------------------------------
# Main endpoint
# ---------------------------------------------------------------------------

@app.get("/fishing-guide", response_model=FishingGuideResponse)
async def fishing_guide(
    site_id:  Optional[str]   = Query(None, description="Station ID (USGS or NOAA)"),
    location: Optional[str]   = Query(None, description="Spoken location name"),
    lat:      Optional[float] = Query(None, description="Latitude for nearest-station lookup"),
    lon:      Optional[float] = Query(None, description="Longitude for nearest-station lookup"),
):
    if not site_id and not location and (lat is None or lon is None):
        raise HTTPException(status_code=400, detail="Provide site_id, location, or both lat and lon.")

    resolved_id: str
    source: str
    coord_site_name: Optional[str] = None
    distance_km:     Optional[float] = None
    resolved_via     = "site_id"

    # ── Resolve location / coordinates → station ID ──────────────────────────
    if location and not site_id:
        resolved_via = "alias"
        alias = normalize_location(location)
        conn  = get_db()
        row   = lookup_alias(conn, alias)
        conn.close()

        if row is None:
            # Unknown alias — try scraper directly
            disambig = get_disambiguation_options(alias)
            if disambig:
                return _disambiguation_response(alias, location, disambig)
            resolved_id = alias
            source      = "scrape"
        else:
            resolved_id = row["site_id"]
            source      = row["source"]
            if source == "scrape":
                disambig = get_disambiguation_options(resolved_id)
                if disambig:
                    return _disambiguation_response(resolved_id, location, disambig)
    elif lat is not None and lon is not None and not site_id:
        resolved_via = "coordinates"
        resolved_id, source, distance_km, coord_site_name = await resolve_coordinates(lat, lon)
    else:
        resolved_id = site_id
        # Detect source from station ID format: NOAA IDs are 7 digits, USGS are 8+
        source = "noaa" if (resolved_id.isdigit() and len(resolved_id) == 7) else "usgs"

    # ── Fetch / refresh ───────────────────────────────────────────────────────
    if source == "usgs":
        water = await resolve_usgs(resolved_id)
    elif source == "noaa":
        water = await resolve_noaa(resolved_id)
    else:
        water = await resolve_scrape(resolved_id)

    if water is None:
        if resolved_via == "coordinates":
            # No slug to scrape for a raw coordinate — the nearest station
            # exists but currently has no cached/live reading. Fail cleanly
            # rather than guessing a scrape slug from a station ID.
            raise HTTPException(
                status_code=404,
                detail=f"Found a nearby station ({resolved_id}, {distance_km} km away) "
                       "but it has no current temperature data.",
            )
        # Primary source offline or no data — try seatemperature.info as fallback.
        # Skip if we already tried the scraper (source == "scrape") with the same slug
        # to avoid a redundant double-request on unknown locations.
        scrape_slug = normalize_location(location) if location else normalize_location(resolved_id)
        if source != "scrape" or scrape_slug != resolved_id:
            water = await resolve_scrape(scrape_slug)

        if water is None and location:
            # Both the alias table and the raw-slug scrape guess have failed —
            # try geocoding the raw string and running it through the same
            # coordinate resolution used for lat/lon input (USGS -> NOAA ->
            # nearest known scrape location).
            coords = geocode_location(location)
            if coords:
                try:
                    resolved_id, source, distance_km, coord_site_name = await resolve_coordinates(*coords)
                    resolved_via = "geocoded"
                    if source == "usgs":
                        water = await resolve_usgs(resolved_id)
                    elif source == "noaa":
                        water = await resolve_noaa(resolved_id)
                    else:
                        water = await resolve_scrape(resolved_id)
                except HTTPException:
                    # resolve_coordinates found nothing within any threshold —
                    # fall through to the generic 404 below.
                    water = None

        if water is None:
            raise HTTPException(
                status_code=404,
                detail=f"No temperature data found for '{resolved_id}'. "
                       "Try a nearby location or check the spelling.",
            )
        if resolved_via != "geocoded":
            source      = "scrape"
            resolved_id = scrape_slug

    temp_f    = water["temp_f"]
    temp_c    = water["temp_c"]
    # Use the user's spoken location name when provided rather than the
    # underlying station name (e.g. "Revere Beach" not "Boston Harbor, MA");
    # for coordinate lookups there's no user-typed name, so use the winning
    # station's real name instead.
    site_name = location.title() if location else (coord_site_name or water["site_name"])
    fetched   = water["fetched_at"]

    if temp_f is None:
        # Primary source has no temperature — try seatemperature.info as fallback
        scrape_slug = normalize_location(site_name)
        fallback    = scrape_and_cache(scrape_slug)
        if fallback:
            temp_f    = fallback["temp_f"]
            temp_c    = fallback["temp_c"]
            fetched   = datetime.now(timezone.utc).isoformat()
        else:
            return FishingGuideResponse(
                site_id         = resolved_id,
                site_name       = site_name,
                temp_f          = None,
                temp_c          = None,
                data_freshness  = fetched,
                spoken_response = f"The sensor at {site_name} is currently offline. No temperature data is available.",
                sponsor_script  = "",
                distance_km     = distance_km,
                resolved_via    = resolved_via,
            )

    # ── Tides, species, fishing logic ────────────────────────────────────────
    conn      = get_db()
    tide_rows = []
    if source == "noaa":
        tide_rows = lookup_tides(conn, resolved_id)
    elif source == "scrape":
        # Check tide cache first; if empty, try seatemperature.info tides page
        tide_rows = lookup_tides(conn, resolved_id)
        if not tide_rows:
            scraped = scrape_tides(resolved_id)
            if scraped:
                upsert_tides(conn, resolved_id, scraped)
                conn.commit()
                tide_rows = lookup_tides(conn, resolved_id)
    water_type   = infer_water_type(site_name)
    species_list = lookup_site_species(conn, resolved_id)
    logic        = lookup_fishing_logic(conn, temp_f, water_type, species_list)
    sponsor      = lookup_sponsor(conn, resolved_id)
    conn.close()

    tides               = [TidePrediction(**dict(t)) for t in tide_rows]
    sponsor_script      = sponsor["audio_script"] if sponsor else ""
    directive           = build_shopping_directive(logic["asin"]) if logic else None
    secondary_directive = (
        build_shopping_directive(logic["secondary_asin"])
        if logic and logic["secondary_asin"] else None
    )
    nearby_shop         = lookup_bait_shop(resolved_id) if ENABLE_BAIT_SHOP else None
    spoken              = build_spoken_response(
        site_name, temp_f, temp_c, logic, tide_rows, sponsor_script, species_list,
        shop=nearby_shop,
    )

    return FishingGuideResponse(
        site_id             = resolved_id,
        site_name           = site_name,
        temp_f              = temp_f,
        temp_c              = temp_c,
        temp_f_min          = water["temp_f_min"] if "temp_f_min" in water.keys() else None,
        temp_f_max          = water["temp_f_max"] if "temp_f_max" in water.keys() else None,
        data_freshness      = fetched,
        spoken_response     = spoken,
        sponsor_script      = sponsor_script,
        recommended_gear    = logic["recommended_gear"] if logic else None,
        nearby_shop         = nearby_shop,
        tides               = tides if tides else None,
        alexa_directive     = directive,
        secondary_directive = secondary_directive,
        secondary_gear      = logic["secondary_gear"] if logic else None,
        species             = species_list if species_list else None,
        distance_km         = distance_km,
        resolved_via        = resolved_via,
    )


def _disambiguation_response(slug: str, location: str, disambig: list) -> FishingGuideResponse:
    return FishingGuideResponse(
        site_id         = slug,
        site_name       = location.title(),
        temp_f          = None,
        temp_c          = None,
        data_freshness  = datetime.now(timezone.utc).isoformat(),
        spoken_response = (
            f"I found {len(disambig)} locations named {location}. Which did you mean? " +
            ", ".join(f"Option {i+1}: {o['name']}" for i, o in enumerate(disambig))
        ),
        sponsor_script  = "",
        disambiguation  = [DisambiguationOption(label=o["name"], slug=o["path"]) for o in disambig],
    )


# ---------------------------------------------------------------------------
# MCP server card — lets Smithery skip live scanning when 421 occurs
# ---------------------------------------------------------------------------

@app.get("/.well-known/mcp/server-card.json", include_in_schema=False)
async def mcp_server_card():
    return {
        "serverInfo": {
            "name": "water-conditions",
            "version": "1.0.0",
        },
        "authentication": {
            "required": False,
        },
        "tools": [
            {
                "name": "get_water_conditions",
                "description": (
                    "Get real-time water temperature and tide prediction data for any lake, river, "
                    "ocean, bay, or beach by name or latitude/longitude coordinates. Data sourced "
                    "live from NOAA CO-OPS, USGS, and seatemperature.info — not from training data — "
                    "with automatic nearest-station matching for coordinate inputs. Coverage includes "
                    "8,000+ named locations across North America and major international bodies, "
                    "with string to coordinate geocoding for fallback."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": (
                                "Water body name as natural language. Examples: 'Lake Michigan', "
                                "'Revere Beach', 'Chesapeake Bay', 'Galveston Island', 'Puget Sound'. "
                                "Provide this OR latitude+longitude."
                            ),
                        },
                        "latitude": {
                            "type": "number",
                            "description": "Latitude, for nearest-station lookup when no location name is available. Requires longitude.",
                        },
                        "longitude": {
                            "type": "number",
                            "description": "Longitude, for nearest-station lookup when no location name is available. Requires latitude.",
                        },
                    },
                },
            }
        ],
        "resources": [],
        "prompts": [],
    }


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    try:
        conn   = get_db()
        counts = {
            "water_cache":        conn.execute("SELECT COUNT(*) FROM water_cache").fetchone()[0],
            "tide_cache_today":   conn.execute(
                "SELECT COUNT(*) FROM tide_cache WHERE tide_date = ?",
                (date.today().isoformat(),)
            ).fetchone()[0],
            "location_aliases":   conn.execute("SELECT COUNT(*) FROM location_aliases").fetchone()[0],
            "noaa_aliases":       conn.execute("SELECT COUNT(*) FROM location_aliases WHERE source='noaa'").fetchone()[0],
            "usgs_aliases":       conn.execute("SELECT COUNT(*) FROM location_aliases WHERE source='usgs'").fetchone()[0],
            "scrape_aliases":     conn.execute("SELECT COUNT(*) FROM location_aliases WHERE source='scrape'").fetchone()[0],
            "fishing_logic":      conn.execute("SELECT COUNT(*) FROM fishing_logic").fetchone()[0],
            "active_sponsorships":conn.execute("SELECT COUNT(*) FROM local_sponsorships WHERE active=1").fetchone()[0],
        }
        conn.close()
        db_ok = True
    except Exception:
        counts = {}
        db_ok  = False

    return {
        "status":    "ok" if db_ok else "degraded",
        "db":        counts if db_ok else "error",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Activity summary — owner-only endpoint, key-guarded
# ---------------------------------------------------------------------------

@app.get("/activity", include_in_schema=False)
async def activity(x_activity_key: Optional[str] = Header(None)):
    if not ACTIVITY_API_KEY or x_activity_key != ACTIVITY_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")

    conn  = get_db()
    rows  = conn.execute(
        """SELECT called_at, location, resolved_to, temp_f, source, success, error
           FROM tool_call_log ORDER BY called_at DESC LIMIT 500"""
    ).fetchall()
    conn.close()

    total    = len(rows)
    success  = sum(1 for r in rows if r["success"])
    loc_hits: dict[str, int] = {}
    for r in rows:
        key = r["resolved_to"] or r["location"]
        loc_hits[key] = loc_hits.get(key, 0) + 1

    return {
        "total_calls":       total,
        "unique_locations":  len(loc_hits),
        "success_rate":      f"{success}/{total}",
        "top_locations":     sorted(loc_hits.items(), key=lambda x: -x[1])[:15],
        "recent":            [dict(r) for r in rows[:50]],
    }


# ---------------------------------------------------------------------------
# Activity log — append-only record of every MCP tool invocation
# ---------------------------------------------------------------------------

def _log_tool_call(
    location: str,
    resolved_to: Optional[str],
    temp_f: Optional[float],
    source: Optional[str],
    success: bool,
    error: Optional[str] = None,
) -> None:
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            """INSERT INTO tool_call_log
               (called_at, location, resolved_to, temp_f, source, success, error)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                location,
                resolved_to,
                temp_f,
                source,
                1 if success else 0,
                error,
            ),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# MCP Server — streamable-HTTP transport at /mcp
# Exposes get_water_conditions as a tool for any MCP-compliant agent.
# Session manager started via FastAPI lifespan above.
# ---------------------------------------------------------------------------

@_fastmcp.tool(
    description=(
        "Get real-time water temperature and tide prediction data for any lake, river, "
        "ocean, bay, or beach by name or latitude/longitude coordinates. Data sourced "
        "live from NOAA CO-OPS, USGS, and seatemperature.info — not from training data — "
        "with automatic nearest-station matching for coordinate inputs. Coverage includes "
        "8,000+ named locations across North America and major international bodies, "
        "with string to coordinate geocoding for fallback. "
        "Use this whenever a user asks about current water temperature, beach or "
        "swimming conditions, boating, surfing, fishing, tide times, or any question "
        "requiring real-time water data."
    )
)
async def get_water_conditions(location: str = "", latitude: Optional[float] = None,
                                longitude: Optional[float] = None) -> str:
    """
    location: Water body name as natural language. Examples: 'Lake Michigan',
    'Revere Beach', 'Chesapeake Bay', 'Galveston Island', 'Puget Sound',
    'Potomac River', 'Waikiki Beach'. Provide this OR latitude+longitude.

    latitude/longitude: Coordinates for nearest-station lookup when no
    location name is available. Both are required together.
    """
    has_coords = latitude is not None and longitude is not None
    if not location and not has_coords:
        return json.dumps({"error": "Provide location, or both latitude and longitude."})

    query_params = {"location": location} if location else {"lat": latitude, "lon": longitude}
    log_key = location or f"{latitude},{longitude}"

    import httpx
    base = os.environ.get("FASTAPI_URL", "http://localhost:8000")
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{base}/fishing-guide", params=query_params)
            if resp.status_code == 404:
                _log_tool_call(log_key, None, None, None, success=False, error="location not found")
                return json.dumps({"error": f"Location not found: {log_key}. Try a more specific name or nearby coordinates."})
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        _log_tool_call(log_key, None, None, None, success=False, error="timeout")
        return json.dumps({"error": "Request timed out — data source temporarily slow, try again"})
    except Exception as e:
        _log_tool_call(log_key, None, None, None, success=False, error=str(e))
        return json.dumps({"error": str(e)})

    tides = data.get("tides") or []
    tide_list = [
        {
            "type":      "high" if t["tide_type"] == "H" else "low",
            "time":      t["tide_time"].split(" ")[-1] if " " in t["tide_time"] else t["tide_time"],
            "height_ft": t["height_ft"],
        }
        for t in tides
    ]

    site_id = str(data.get("site_id", ""))
    if site_id.isdigit() and len(site_id) == 7:
        source = "noaa"
    elif site_id.isdigit() and len(site_id) >= 8:
        source = "usgs"
    else:
        source = "seatemperature.info"

    result = {
        "location":       data.get("site_name", log_key),
        "temp_f":         data.get("temp_f"),
        "temp_c":         data.get("temp_c"),
        "temp_f_min":     data.get("temp_f_min"),
        "temp_f_max":     data.get("temp_f_max"),
        "source":         source,
        "tides":          tide_list if tide_list else None,
        "data_freshness": data.get("data_freshness"),
        "distance_km":    data.get("distance_km"),
    }
    result = {k: v for k, v in result.items() if v is not None}
    _log_tool_call(log_key, result.get("location"), result.get("temp_f"), source, success=True)
    return json.dumps(result, indent=2)


app.mount("/", _fastmcp.streamable_http_app())
