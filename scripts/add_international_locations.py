"""
Curated international expansion — a hand-picked list of well-known global
water bodies (beaches, seas, islands, lakes) not derived from OSM, since the
North-America-bounded OSM pipeline (build_osm_beach_list.py) never covered
anything outside NA + Caribbean.

For each candidate:
  1. Skip if already in location_aliases (any source)
  2. Test slug (and simple variants) against seatemperature.info
  3. On a hit: geocode the display name via ingest.geocode_ingest, insert
     into scrape_location_index, and emit an ALIAS_SEED-ready line

Requires GOOGLE_PLACES_API_KEY — run via `railway run python scripts/add_international_locations.py`
so the real key + elevated DAILY_GEOCODING_LIMIT apply.

Outputs:
  scripts/international_aliases_to_add.txt   -- ready-to-paste ALIAS_SEED rows
  scripts/international_not_covered.txt      -- candidates with no seatemp.info page
"""
import os
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone

import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingest.geocode_ingest import geocode_location

DB_PATH = os.environ.get("DB_PATH", "fishing.db")
SEATEMP_BASE = "https://seatemperature.info"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; FishingGuideBot/1.0)"}
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_ALIASES = os.path.join(SCRIPTS_DIR, "international_aliases_to_add.txt")
OUT_MISS = os.path.join(SCRIPTS_DIR, "international_not_covered.txt")

# ---------------------------------------------------------------------------
# Candidate list — well-known international water bodies, by region.
# Not exhaustive; a first pass at global spread for the geocoding fallback.
# ---------------------------------------------------------------------------
CANDIDATES = [
    # Major seas / oceans / gulfs / straits not already covered
    "Red Sea", "Arabian Sea", "Indian Ocean", "South China Sea", "Coral Sea",
    "Tasman Sea", "Persian Gulf", "Aegean Sea", "Ionian Sea", "Tyrrhenian Sea",
    "Sea of Japan", "Yellow Sea", "Gulf of Thailand", "Bay of Bengal",
    "Strait of Gibraltar", "Dead Sea", "Sea of Galilee", "Caspian Sea",
    "Lake Victoria", "Lake Tanganyika", "Gulf of Aden", "Andaman Sea",
    "Java Sea", "Bosphorus", "Strait of Malacca", "Gulf of Oman",

    # Europe — beaches, islands, coastal towns
    "Mykonos", "Santorini", "Ibiza", "Formentera", "Costa del Sol",
    "Algarve", "Amalfi Coast", "Capri", "Cinque Terre", "Lake Como",
    "Lake Garda", "French Riviera", "Nice", "Cannes", "Monaco",
    "Dubrovnik", "Split", "Hvar", "Corfu", "Crete", "Rhodes", "Zakynthos",
    "Marbella", "Benidorm", "Faro", "Sylt", "Paros", "Naxos",
    "Lake Geneva", "Lake Constance", "Loch Ness", "Isle of Skye",
    "Costa Brava", "Costa Blanca", "Sardinia", "Sicily", "Elba",

    # Middle East
    "Dubai", "Abu Dhabi", "Eilat", "Sharm El Sheikh", "Hurghada",
    "Doha", "Muscat", "Dahab",

    # Asia
    "Phuket", "Koh Samui", "Krabi", "Bali", "Gili Islands", "Boracay",
    "Palawan", "Langkawi", "Penang", "Sentosa", "Ha Long Bay",
    "Nha Trang", "Da Nang", "Goa", "Andaman Islands", "Maldives",
    "Okinawa", "Jeju Island", "Busan", "Sanya", "Hainan",
    "Koh Lanta", "Mumbai", "Chennai", "Colombo", "Phi Phi Islands",

    # Africa
    "Zanzibar", "Mombasa", "Cape Town", "Durban", "Seychelles",
    "Mauritius", "Agadir", "Casablanca", "Alexandria",

    # Oceania
    "Gold Coast", "Bondi Beach", "Byron Bay", "Whitsundays",
    "Perth", "Fiji", "Tahiti", "Bora Bora", "Auckland", "Lake Taupo",

    # South America
    "Rio de Janeiro", "Ipanema", "Buzios", "Florianopolis",
    "Punta del Este", "Cartagena", "Galapagos", "Lake Titicaca",
]

def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text.strip("-")


def check_seatemp(client, slug: str) -> bool:
    url = f"{SEATEMP_BASE}/{slug}-water-temperature.html"
    try:
        r = client.get(url, headers=HEADERS, timeout=8, follow_redirects=True)
        return r.status_code == 200
    except Exception:
        return False


def main():
    conn = sqlite3.connect(DB_PATH)
    existing = {r[0] for r in conn.execute("SELECT alias FROM location_aliases").fetchall()}

    hits, misses = [], []
    alias_rows = []

    with httpx.Client() as client:
        for name in CANDIDATES:
            slug = slugify(name)
            if slug in existing:
                print(f"  skip (already aliased): {name}")
                continue

            if not check_seatemp(client, slug):
                misses.append(name)
                continue

            coords = geocode_location(name)
            if coords is None:
                print(f"  seatemp hit but geocode failed: {name}")
                misses.append(name)
                continue

            lat, lon = coords
            now_utc = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """INSERT INTO scrape_location_index (slug, site_name, lat, lon, fetched_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(slug) DO UPDATE SET
                       site_name = excluded.site_name, lat = excluded.lat,
                       lon = excluded.lon, fetched_at = excluded.fetched_at""",
                (slug, name, lat, lon, now_utc),
            )
            conn.execute(
                "INSERT OR REPLACE INTO location_aliases (alias, site_id, source) VALUES (?, ?, 'scrape')",
                (slug, slug),
            )
            conn.commit()

            hits.append((name, slug, lat, lon))
            alias_rows.append(f'    ("{slug}",{" " * max(1, 30 - len(slug))}"{slug}",  "scrape"),  # {name}')
            print(f"  HIT: {name} -> {slug} ({lat:.4f}, {lon:.4f})")

    conn.close()

    with open(OUT_ALIASES, "w", encoding="utf-8") as f:
        f.write("# International locations confirmed on seatemperature.info + geocoded\n")
        f.write("# Add these rows to ALIAS_SEED in db/init_db.py\n\n")
        f.write("\n".join(alias_rows))

    with open(OUT_MISS, "w", encoding="utf-8") as f:
        f.write("# Candidates with no seatemperature.info page (or geocode failure)\n\n")
        f.write("\n".join(misses))

    print(f"\nTotal candidates: {len(CANDIDATES)}")
    print(f"Hits (added):     {len(hits)}")
    print(f"Misses:           {len(misses)}")
    print(f"\nWrote: {OUT_ALIASES}")
    print(f"Wrote: {OUT_MISS}")


if __name__ == "__main__":
    main()
