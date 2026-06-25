"""
Queries OpenStreetMap (via Overpass API) for all named beaches, bays, harbors,
lakes, and coastal swim areas across North America, then:

  1. Tests each against seatemperature.info (slug match)
  2. For misses, finds the nearest NOAA station that reports water temperature
  3. Outputs a comprehensive alias list ready to paste into db/init_db.py

This is the canonical coverage-expansion script: it starts from what people
actually call places, not from what monitoring networks call their stations.

Usage:
    pip install httpx
    python scripts/build_osm_beach_list.py

Outputs:
    scripts/osm_beaches_raw.json            -- raw Overpass results (cached)
    scripts/osm_seatemp_hits.txt            -- slugs confirmed on seatemperature.info
    scripts/osm_noaa_fallback.txt           -- slugs resolved to nearest NOAA station
    scripts/osm_aliases_to_add.txt          -- ready-to-paste init_db.py rows
    scripts/osm_not_covered.txt             -- locations with no coverage path found

Runs in stages so you can Ctrl-C and resume (raw JSON is cached).
"""
import asyncio
import csv
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')

try:
    import httpx
except ImportError:
    print("pip install httpx")
    sys.exit(1)

SCRIPTS_DIR  = os.path.dirname(os.path.abspath(__file__))
CACHE_FILE   = os.path.join(SCRIPTS_DIR, "osm_beaches_raw.json")
OUT_HITS     = os.path.join(SCRIPTS_DIR, "osm_seatemp_hits.txt")
OUT_NOAA     = os.path.join(SCRIPTS_DIR, "osm_noaa_fallback.txt")
OUT_ALIASES  = os.path.join(SCRIPTS_DIR, "osm_aliases_to_add.txt")
OUT_MISS     = os.path.join(SCRIPTS_DIR, "osm_not_covered.txt")

# Overpass API — North America bounding box (lat_min, lon_min, lat_max, lon_max)
# 15°N – 85°N, 170°W – 52°W covers continental NA + HI + Alaska + Caribbean
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
# North America bounding box: (lat_min, lon_min, lat_max, lon_max)
# Excludes coastline tag (too noisy) — focuses on named beach/bay/harbor/lake features
OVERPASS_QUERY = """\
[out:json][timeout:180];
(
  node[natural=beach][name](15,-170,85,-52);
  way[natural=beach][name](15,-170,85,-52);
  node[tourism=beach][name](15,-170,85,-52);
  way[tourism=beach][name](15,-170,85,-52);
  node[natural=bay][name](15,-170,85,-52);
  way[natural=bay][name](15,-170,85,-52);
  node[natural=harbour][name](15,-170,85,-52);
  way[natural=harbour][name](15,-170,85,-52);
  node[harbour=yes][name](15,-170,85,-52);
);
out center;\
"""

SEATEMP_CONCURRENCY = 30
SEATEMP_BASE        = "https://seatemperature.info"
NOAA_TEMP_API       = (
    "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    "?station={}&product=water_temperature&date=latest&units=english&time_zone=gmt&format=json"
)
NOAA_STATIONS_URL   = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json"

HEADERS = {"User-Agent": "Mozilla/5.0 (FishingGuideBot; contact: github.com/watertempfishing)"}


# ---------------------------------------------------------------------------
# Slug utilities
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    return text.strip('-')


def slug_variants(name: str, state: str = "", country: str = "") -> list[str]:
    """Generate the slugs we should try on seatemperature.info."""
    base = slugify(name)
    if not base or len(base) < 3:
        return []

    variants = [base]

    # Drop trailing "beach" / "bay" / "harbor" for shorter variant
    for suffix in ['-beach', '-bay', '-harbor', '-lake', '-river', '-sound', '-cove', '-inlet']:
        if base.endswith(suffix):
            short = base[:-len(suffix)]
            if len(short) > 2 and short not in variants:
                variants.append(short)
            break

    # State-qualified variant
    if state:
        state_slug = slugify(state)
        # Use 2-letter abbreviation form if state is long
        q = f"{base}-{state_slug[:2] if len(state_slug) > 6 else state_slug}"
        if q not in variants:
            variants.append(q)

    return variants


# ---------------------------------------------------------------------------
# Stage 1: fetch OSM data
# ---------------------------------------------------------------------------

def fetch_osm_beaches() -> list[dict]:
    if os.path.exists(CACHE_FILE):
        print(f"Using cached OSM data: {CACHE_FILE}")
        with open(CACHE_FILE, encoding='utf-8') as f:
            return json.load(f)

    print("Fetching North American beaches from OpenStreetMap Overpass API...")
    print("(Large query — may take 60-120 seconds)")
    body = urllib.parse.urlencode({"data": OVERPASS_QUERY}).encode()
    req  = urllib.request.Request(
        OVERPASS_URL, data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent":   "FishingGuideBot/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=200) as resp:
        raw = json.loads(resp.read())

    elements = raw.get("elements", [])
    beaches = []
    for el in elements:
        name = el.get("tags", {}).get("name", "").strip()
        if not name:
            continue
        # Prefer center for ways, direct coords for nodes
        lat = el.get("center", {}).get("lat") or el.get("lat")
        lon = el.get("center", {}).get("lon") or el.get("lon")
        if lat is None or lon is None:
            continue
        beaches.append({
            "name":    name,
            "lat":     float(lat),
            "lon":     float(lon),
            "state":   el.get("tags", {}).get("addr:state", ""),
            "country": el.get("tags", {}).get("addr:country", "US"),
            "osm_id":  el.get("id"),
        })

    # Deduplicate by name+approximate location (same name within 5km = same beach)
    seen: set[str] = set()
    unique = []
    for b in beaches:
        key = f"{slugify(b['name'])}-{round(b['lat'],1)}-{round(b['lon'],1)}"
        if key not in seen:
            seen.add(key)
            unique.append(b)

    print(f"  {len(elements)} OSM elements -> {len(unique)} unique named locations")
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique, f)
    return unique


# ---------------------------------------------------------------------------
# Stage 2: check seatemperature.info for each slug variant
# ---------------------------------------------------------------------------

async def check_seatemp(semaphore, client, slug) -> bool:
    url = f"{SEATEMP_BASE}/{slug}-water-temperature.html"
    async with semaphore:
        try:
            r = await client.get(url, timeout=8, follow_redirects=True)
            return r.status_code == 200
        except Exception:
            return False


async def run_seatemp_checks(beaches: list[dict]) -> list[dict]:
    """Returns beaches annotated with seatemp_slug (or None)."""
    semaphore = asyncio.Semaphore(SEATEMP_CONCURRENCY)
    done = 0

    async def check_one(beach):
        nonlocal done
        variants = slug_variants(beach["name"], beach.get("state", ""))
        for slug in variants:
            ok = await check_seatemp(semaphore, client, slug)
            if ok:
                beach["seatemp_slug"] = slug
                break
        else:
            beach["seatemp_slug"] = None
        done += 1
        if done % 200 == 0 or done == len(beaches):
            hits = sum(1 for b in beaches if b.get("seatemp_slug"))
            print(f"  [{done:5}/{len(beaches)}] checked, {hits} seatemp hits so far", flush=True)
        return beach

    async with httpx.AsyncClient(headers=HEADERS) as client:
        results = await asyncio.gather(*[check_one(b) for b in beaches])

    return results


# ---------------------------------------------------------------------------
# Stage 3: nearest NOAA station for misses
# ---------------------------------------------------------------------------

def haversine(lat1, lon1, lat2, lon2) -> float:
    """Distance in km between two lat/lon points."""
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_noaa_stations_with_temp() -> list[dict]:
    """Load the NOAA stations that have water temp — uses our pre-built list if available."""
    noaa_input = os.path.join(SCRIPTS_DIR, "noaa_stations_coverage_input.txt")
    if os.path.exists(noaa_input):
        # Parse the pre-built list (name | slug | state | country | station_id | notes)
        stations = []
        seen = set()
        with open(noaa_input, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = [p.strip() for p in line.split('|')]
                if len(parts) < 5:
                    continue
                sid = parts[4]
                if sid in seen:
                    continue
                seen.add(sid)
                stations.append({"id": sid, "name": parts[0], "state": parts[2]})
        print(f"  Loaded {len(stations)} NOAA water-temp stations from pre-built list")
        return stations

    # Fallback: fetch from API
    print("  Fetching NOAA station coordinates from API...")
    with httpx.Client() as client:
        r = client.get(NOAA_STATIONS_URL, timeout=30)
        all_stations = r.json().get("stations", [])
    print(f"  {len(all_stations)} total NOAA stations fetched")
    return all_stations


def fetch_noaa_coordinates() -> dict[str, tuple[float, float]]:
    """Returns {station_id: (lat, lon)} for all NOAA stations."""
    print("  Fetching NOAA station coordinates...")
    with httpx.Client() as client:
        r = client.get(NOAA_STATIONS_URL, timeout=30)
        stations = r.json().get("stations", [])
    coords = {}
    for st in stations:
        sid = st.get("id")
        lat = st.get("lat")
        lng = st.get("lng")
        if sid and lat and lng:
            coords[sid] = (float(lat), float(lng))
    return coords


def find_nearest_noaa(lat: float, lon: float,
                      station_coords: dict[str, tuple[float, float]],
                      max_km: float = 100) -> tuple[str | None, float]:
    best_id, best_dist = None, float("inf")
    for sid, (slat, slon) in station_coords.items():
        d = haversine(lat, lon, slat, slon)
        if d < best_dist:
            best_dist = d
            best_id = sid
    if best_dist > max_km:
        return None, best_dist
    return best_id, best_dist


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    # Stage 1
    beaches = fetch_osm_beaches()
    print(f"\nTotal unique named locations: {len(beaches)}")

    # Stage 2 — seatemperature.info check
    print(f"\nChecking seatemperature.info with {SEATEMP_CONCURRENCY} concurrent requests...")
    print(f"Estimated time: ~{max(1, len(beaches) // SEATEMP_CONCURRENCY // 4)} min\n")
    beaches = asyncio.run(run_seatemp_checks(beaches))

    seatemp_hits  = [b for b in beaches if b["seatemp_slug"]]
    seatemp_miss  = [b for b in beaches if not b["seatemp_slug"]]
    print(f"\nSeatemperature.info:  {len(seatemp_hits)} hits / {len(seatemp_miss)} misses")

    # Stage 3 — NOAA fallback for misses
    print("\nLoading NOAA stations for fallback matching...")
    noaa_stations = load_noaa_stations_with_temp()
    print("Fetching NOAA station coordinates...")
    station_coords = fetch_noaa_coordinates()

    # Only keep coords for stations that have water temp
    temp_station_ids = {st["id"] for st in noaa_stations}
    temp_coords = {sid: coords for sid, coords in station_coords.items()
                   if sid in temp_station_ids}
    print(f"  {len(temp_coords)} water-temp stations with coordinates")

    noaa_resolved = []
    not_covered   = []

    for b in seatemp_miss:
        nearest_sid, dist_km = find_nearest_noaa(b["lat"], b["lon"], temp_coords, max_km=80)
        if nearest_sid:
            b["noaa_sid"]  = nearest_sid
            b["noaa_dist"] = round(dist_km, 1)
            noaa_resolved.append(b)
        else:
            not_covered.append(b)

    print(f"NOAA fallback resolved:       {len(noaa_resolved)}")
    print(f"No coverage path:             {len(not_covered)}")

    # Write outputs
    alias_rows = []

    with open(OUT_HITS, 'w', encoding='utf-8') as f:
        f.write("# Beaches confirmed on seatemperature.info\n")
        f.write("# name | seatemp_slug | lat | lon\n\n")
        for b in sorted(seatemp_hits, key=lambda x: x["name"]):
            slug = b["seatemp_slug"]
            f.write(f"{b['name']:<40} | {slug:<45} | {b['lat']:.4f} | {b['lon']:.4f}\n")
            alias_rows.append(
                f'    ("{slugify(b["name"])}",' + ' ' * max(1, 38 - len(slugify(b['name']))) +
                f'"{slug}",  "scrape"),  # {b["name"]}'
            )
            # Also add the seatemp slug as its own alias if different from the name slug
            if slug != slugify(b["name"]):
                alias_rows.append(
                    f'    ("{slug}",' + ' ' * max(1, 38 - len(slug)) +
                    f'"{slug}",  "scrape"),  # {b["name"]} (seatemp canonical)'
                )

    with open(OUT_NOAA, 'w', encoding='utf-8') as f:
        f.write("# Beaches resolved to nearest NOAA water-temp station\n")
        f.write("# name | noaa_station | dist_km | lat | lon\n\n")
        for b in sorted(noaa_resolved, key=lambda x: x["name"]):
            f.write(f"{b['name']:<40} | {b['noaa_sid']} | {b['noaa_dist']:5.1f} km | "
                    f"{b['lat']:.4f} | {b['lon']:.4f}\n")
            name_slug = slugify(b["name"])
            alias_rows.append(
                f'    ("{name_slug}",' + ' ' * max(1, 38 - len(name_slug)) +
                f'"{b["noaa_sid"]}",  "noaa"),   # {b["name"]} ({b["noaa_dist"]:.0f}km to station)'
            )

    with open(OUT_ALIASES, 'w', encoding='utf-8') as f:
        f.write("# Add these rows to ALIAS_SEED in db/init_db.py\n")
        f.write("# Generated by build_osm_beach_list.py from OpenStreetMap data\n\n")
        f.write("\n".join(alias_rows))

    with open(OUT_MISS, 'w', encoding='utf-8') as f:
        f.write("# Locations with no coverage path (>80km from NOAA, not on seatemp.info)\n\n")
        for b in sorted(not_covered, key=lambda x: x["name"]):
            f.write(f"{b['name']:<40} | {b['lat']:.4f} | {b['lon']:.4f}\n")

    print(f"\nWrote: {OUT_HITS}")
    print(f"Wrote: {OUT_NOAA}")
    print(f"Wrote: {OUT_ALIASES}")
    print(f"Wrote: {OUT_MISS}")
    print(f"\nTotal alias rows generated: {len(alias_rows)}")
    print(f"\nNext step: review {os.path.basename(OUT_ALIASES)} and paste into db/init_db.py")


if __name__ == "__main__":
    main()
