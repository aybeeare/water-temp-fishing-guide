"""
Audit scrape_location_index for entries geocoded into the wrong country.

The original backfill geocoded bare slug names, so 'saint-louis' (a page about
Saint-Louis, Senegal) landed in St. Louis, Missouri and 'lake-geneva' (the
Swiss lake) landed in Wisconsin. Those entries make coordinate lookups return
readings from the other side of the world.

For each indexed slug this fetches the seatemperature.info page, reads the
country from its breadcrumb, and flags rows whose stored coordinates don't
match: a non-US page placed inside the US, or a US page placed outside it.

Usage:
    python scripts/audit_scrape_index.py              # report only → scripts/scrape_index_audit.csv
    python scripts/audit_scrape_index.py --drop       # also delete flagged rows
    python scripts/audit_scrape_index.py --regeocode  # re-geocode flagged rows with the
                                                      # country-qualified name (needs GOOGLE_PLACES_API_KEY)
"""
import argparse
import asyncio
import csv
import os
import sqlite3
import sys

import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ingest.scrape_location_index import page_region, qualified_name  # noqa: E402
from ingest.sea_temp_scraper import HEADERS, build_url                 # noqa: E402

DB_PATH  = os.environ.get("DB_PATH", "fishing.db")
OUT_CSV  = os.path.join(os.path.dirname(__file__), "scrape_index_audit.csv")
CONCURRENCY = 6

# Rough US boxes: (lat_min, lat_max, lon_min, lon_max)
US_BOXES = [
    (24.0, 49.5, -125.0, -66.5),    # contiguous
    (51.0, 72.0, -180.0, -129.0),   # Alaska
    (18.5, 22.5, -161.0, -154.5),   # Hawaii
    (17.5, 18.7, -68.0, -64.5),     # Puerto Rico / USVI
]
# Neighbors whose real locations overlap the rough US boxes
BORDER_COUNTRIES = {"Canada", "Mexico", "Bahamas", "Cuba", "Great Lakes"}
US_TERRITORIES   = {"Puerto Rico", "United States Virgin Islands"}


def in_us(lat: float, lon: float) -> bool:
    return any(a <= lat <= b and c <= lon <= d for a, b, c, d in US_BOXES)


def classify(region: list[str], lat: float, lon: float) -> str:
    if not region:
        return "unknown"
    country = region[0]
    if "United States" in country or country in US_TERRITORIES:
        return "ok" if in_us(lat, lon) else "MISMATCH"
    if country in BORDER_COUNTRIES:
        return "ok"
    return "MISMATCH" if in_us(lat, lon) else "ok"


async def fetch(client: httpx.AsyncClient, sem: asyncio.Semaphore, slug: str) -> str:
    async with sem:
        try:
            r = await client.get(build_url(slug))
            return r.text if r.status_code == 200 else ""
        except httpx.HTTPError:
            return ""


async def gather_pages(slugs: list[str]) -> list[str]:
    sem = asyncio.Semaphore(CONCURRENCY)
    async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
        return await asyncio.gather(*(fetch(client, sem, s) for s in slugs))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--drop", action="store_true", help="delete flagged rows")
    ap.add_argument("--regeocode", action="store_true", help="re-geocode flagged rows (needs Google key)")
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT slug, site_name, lat, lon FROM scrape_location_index").fetchall()
    print(f"Auditing {len(rows)} entries …")
    pages = asyncio.run(gather_pages([r[0] for r in rows]))

    results = []
    for (slug, name, lat, lon), html in zip(rows, pages):
        region = page_region(html) if html else []
        results.append({
            "slug": slug, "site_name": name, "lat": lat, "lon": lon,
            "page_region": " > ".join(region), "status": classify(region, lat, lon),
            "qualified_name": qualified_name(slug, html) if html else "",
        })

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        w.writeheader()
        w.writerows(results)

    flagged = [r for r in results if r["status"] == "MISMATCH"]
    unknown = sum(r["status"] == "unknown" for r in results)
    print(f"Flagged {len(flagged)} mismatches, {unknown} pages with no region info. Report: {OUT_CSV}")
    for r in flagged:
        print(f"  {r['slug']:<40} stored ({r['lat']:.2f}, {r['lon']:.2f})  page says: {r['page_region']}")

    if args.regeocode:
        from ingest.geocode_ingest import geocode_location
        fixed = 0
        for r in flagged:
            coords = geocode_location(r["qualified_name"])
            if coords and classify(r["page_region"].split(" > "), *coords) == "ok":
                conn.execute("UPDATE scrape_location_index SET lat = ?, lon = ? WHERE slug = ?",
                             (coords[0], coords[1], r["slug"]))
                fixed += 1
        conn.commit()
        print(f"Re-geocoded {fixed}/{len(flagged)} flagged entries.")
    elif args.drop:
        conn.executemany("DELETE FROM scrape_location_index WHERE slug = ?",
                         [(r["slug"],) for r in flagged])
        conn.commit()
        print(f"Deleted {len(flagged)} flagged entries.")
    conn.close()


if __name__ == "__main__":
    main()
