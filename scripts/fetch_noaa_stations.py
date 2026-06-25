"""
Fetches the full NOAA CO-OPS active station list, filters to stations that have
a 'Water Temperature' sensor, and writes them in beaches_list.txt pipe-delimited
format so check_beach_coverage.py can verify seatemperature.info coverage.

NOAA CO-OPS has ~301-317 active real-time stations total.  We fetch both the
default list and the meteorological-station list, union them, then check each
station's sensor hardware metadata for "Water Temperature".

Usage:
    pip install httpx
    python scripts/fetch_noaa_stations.py

Outputs:
    scripts/noaa_stations_full.txt              — all stations, grouped by state
    scripts/noaa_stations_coverage_input.txt    — flat, ready for check_beach_coverage.py

Next step:
    python scripts/check_beach_coverage.py --input scripts/noaa_stations_coverage_input.txt
"""
import asyncio
import re
import os
import sys

try:
    import httpx
except ImportError:
    print("Missing dependency: pip install httpx")
    sys.exit(1)

OUT_DIR   = os.path.dirname(os.path.abspath(__file__))
OUT_FULL  = os.path.join(OUT_DIR, "noaa_stations_full.txt")
OUT_DEDUP = os.path.join(OUT_DIR, "noaa_stations_coverage_input.txt")

STATIONS_URL = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json"
SENSORS_URL  = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations/{}.json?expand=sensors"

CONCURRENCY = 25

TERRITORY_STATES = {"PR", "VI", "GU", "AS"}


def slugify(text: str) -> str:
    # Strip trailing state abbreviation like ', MA' or ' MA'
    text = re.sub(r',?\s+[A-Z]{2}$', '', text.strip())
    text = re.sub(r'[^a-z0-9]+', '-', text.lower())
    return text.strip('-')


def name_variants(name: str, state: str) -> list[str]:
    base = slugify(name)
    if not base or len(base) < 3:
        return []
    variants = [base]

    geo_suffixes = [
        '-harbor', '-bay', '-beach', '-inlet', '-point', '-channel',
        '-river', '-sound', '-creek', '-pier', '-wharf', '-port',
        '-island', '-key', '-cove', '-pass', '-cut', '-entrance',
        '-station', '-light', '-bridge', '-shoal', '-reef', '-flats',
    ]
    for suffix in geo_suffixes:
        if base.endswith(suffix):
            short = base[:-len(suffix)]
            if len(short) > 3 and short not in variants:
                variants.append(short)
            break

    if state:
        state_slug = f"{base}-{state.lower()}"
        if state_slug not in variants:
            variants.append(state_slug)

    return variants


async def get_sensors(semaphore: asyncio.Semaphore,
                      client: httpx.AsyncClient,
                      station_id: str) -> list[str]:
    """Returns list of sensor names for this station, or [] on failure."""
    async with semaphore:
        try:
            r = await client.get(SENSORS_URL.format(station_id), timeout=12)
            if r.status_code != 200:
                return []
            # Response structure: {"stations": [{"sensors": {"sensors": [...]}}]}
            stations = r.json().get("stations", [])
            if not stations:
                return []
            sensor_block = stations[0].get("sensors", {})
            sensor_list  = sensor_block.get("sensors", [])
            return [s.get("name", "") for s in sensor_list]
        except Exception:
            return []


async def filter_temp_stations(stations: list[dict]) -> list[dict]:
    semaphore = asyncio.Semaphore(CONCURRENCY)
    done = 0

    async def check(st):
        nonlocal done
        names = await get_sensors(semaphore, client, st["id"])
        done += 1
        if done % 100 == 0 or done == len(stations):
            print(f"  [{done:3}/{len(stations)}] checked", flush=True)
        has_wt = any("water temperature" in n.lower() for n in names)
        return st if has_wt else None

    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[check(st) for st in stations])

    return [r for r in results if r is not None]


def fetch_all_stations() -> list[dict]:
    """Fetch both the default and met station lists, union by station ID."""
    by_id: dict[str, dict] = {}
    with httpx.Client() as client:
        for params in ["", "?type=met"]:
            url = STATIONS_URL + params
            print(f"  GET {url} ...", end=" ", flush=True)
            r = client.get(url, timeout=30)
            r.raise_for_status()
            batch = r.json().get("stations", [])
            print(f"{len(batch)} stations")
            for st in batch:
                if st.get("id"):
                    by_id[st["id"]] = st
    return list(by_id.values())


def write_output(rows: list[dict]):
    with open(OUT_FULL, "w", encoding="utf-8") as f:
        f.write("# Auto-generated from NOAA CO-OPS station sensor metadata\n")
        f.write("# Format: name | slug | state | country | noaa_station_id | notes\n")
        prev_state = None
        for r in sorted(rows, key=lambda x: (x["state"], x["name"])):
            if r["state"] != prev_state:
                f.write(f"\n# -- {r['state']} --\n")
                prev_state = r["state"]
            f.write(
                f"{r['name']:<40} | {r['slug']:<45} | "
                f"{r['state']:<4} | {r['country']:<20} | {r['noaa_id']} | {r['notes']}\n"
            )

    with open(OUT_DEDUP, "w", encoding="utf-8") as f:
        f.write("# NOAA-derived station slugs -- input for check_beach_coverage.py\n\n")
        for r in sorted(rows, key=lambda x: (x["state"], x["slug"])):
            f.write(
                f"{r['name']:<40} | {r['slug']:<45} | "
                f"{r['state']:<4} | {r['country']:<20} | {r['noaa_id']} | {r['notes']}\n"
            )


def main():
    print("Fetching NOAA station lists...")
    all_stations = fetch_all_stations()

    valid = [
        st for st in all_stations
        if st.get("id") and st.get("name") and
        not re.match(r'^\d+$', st["name"].strip()) and
        len(st["name"].strip()) >= 4
    ]
    print(f"\nTotal unique stations with usable names: {len(valid)}")
    print(f"Checking sensor metadata ({CONCURRENCY} concurrent requests)...")
    print(f"Estimated time: ~{max(1, len(valid) // CONCURRENCY // 2)} min\n")

    temp_stations = asyncio.run(filter_temp_stations(valid))
    print(f"\nStations with 'Water Temperature' sensor: {len(temp_stations)}")

    rows: list[dict] = []
    seen_slugs: set[str] = set()

    for st in temp_stations:
        name  = st["name"].strip()
        state = st.get("state", "").strip().upper()
        sid   = st["id"]
        country = "USA (Territory)" if state in TERRITORY_STATES else "USA"

        for slug in name_variants(name, state):
            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)
            rows.append({
                "name":    name,
                "slug":    slug,
                "state":   state or "--",
                "country": country,
                "noaa_id": sid,
                "notes":   "noaa-auto",
            })

    print(f"Total slug variants:                       {len(rows)}")
    write_output(rows)

    print(f"\nWrote: {OUT_FULL}")
    print(f"Wrote: {OUT_DEDUP}")
    print(f"\nNext step:")
    print(f"  python scripts/check_beach_coverage.py --input scripts/noaa_stations_coverage_input.txt")


if __name__ == "__main__":
    main()
