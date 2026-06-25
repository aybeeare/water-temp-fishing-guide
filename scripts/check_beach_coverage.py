"""
Checks each beach in beaches_list.txt (or a custom --input file) against
seatemperature.info and (optionally) the NOAA Tides & Currents API.

Usage:
    pip install httpx beautifulsoup4
    python scripts/check_beach_coverage.py
    python scripts/check_beach_coverage.py --input scripts/noaa_stations_coverage_input.txt

Outputs (named by input file stem):
    scripts/<stem>_results.csv       — full results
    scripts/<stem>_seatemp.txt       — slugs confirmed on seatemperature.info
    scripts/<stem>_aliases.txt       — ready-to-paste alias rows for init_db.py
"""
import argparse
import csv
import time
import re
import os
import sys

try:
    import httpx
except ImportError:
    print("Missing dependency: pip install httpx")
    sys.exit(1)

parser = argparse.ArgumentParser()
parser.add_argument(
    "--input", "-i",
    default=None,
    help="Path to pipe-delimited input file (default: beaches_list.txt in repo root)",
)
args, _ = parser.parse_known_args()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

if args.input:
    INPUT_FILE = os.path.abspath(args.input)
    stem = os.path.splitext(os.path.basename(INPUT_FILE))[0]
else:
    INPUT_FILE = os.path.join(BASE_DIR, "beaches_list.txt")
    stem = "beach_coverage"

OUT_CSV     = os.path.join(SCRIPTS_DIR, f"{stem}_results.csv")
OUT_SEATEMP = os.path.join(SCRIPTS_DIR, f"{stem}_seatemp.txt")
OUT_ALIASES = os.path.join(SCRIPTS_DIR, f"{stem}_aliases.txt")

SEATEMP_BASE = "https://seatemperature.info"
NOAA_API     = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations/{}.json"
HEADERS      = {"User-Agent": "Mozilla/5.0 (compatible; FishingGuideBot/1.0)"}
DELAY        = 0.5   # seconds between requests — be polite


def parse_beaches(filepath):
    beaches = []
    with open(filepath, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 5:
                continue
            beaches.append({
                "name":    parts[0],
                "slug":    parts[1],
                "state":   parts[2],
                "country": parts[3],
                "noaa_id": parts[4] if parts[4] != "scrape" else "",
                "notes":   parts[5] if len(parts) > 5 else "",
            })
    return beaches


def check_seatemp(slug, client):
    url = f"{SEATEMP_BASE}/{slug}-water-temperature.html"
    try:
        r = client.get(url, headers=HEADERS, timeout=10, follow_redirects=True)
        if r.status_code == 200:
            # Parse to plain text so HTML entities don't fool the regex
            try:
                from bs4 import BeautifulSoup
                text = BeautifulSoup(r.text, "html.parser").get_text(" ", strip=True)
            except ImportError:
                text = re.sub(r'<[^>]+>', ' ', r.text)
                text = text.replace("&deg;", "°").replace("&#176;", "°")
            has_temp = bool(re.search(r'\d{2,3}(?:\.\d)?\s*°?\s*[FC]\b', text))
            return "yes" if has_temp else "page_exists_no_temp"
        return "no"
    except Exception as e:
        return f"error:{e}"


def check_noaa(station_id, client):
    if not station_id or station_id == "scrape":
        return "n/a"
    url = NOAA_API.format(station_id)
    try:
        r = client.get(url, timeout=10)
        if r.status_code == 200:
            return "valid"
        return f"http_{r.status_code}"
    except Exception as e:
        return f"error:{e}"


def main():
    beaches = parse_beaches(INPUT_FILE)
    print(f"Loaded {len(beaches)} beaches. Checking coverage...")
    print(f"Estimated time: ~{len(beaches) * DELAY * 2 / 60:.1f} minutes\n")

    results = []
    seatemp_hits = []
    alias_rows   = []

    with httpx.Client() as client:
        for i, b in enumerate(beaches, 1):
            print(f"[{i:3}/{len(beaches)}] {b['name']:<30}", end=" ", flush=True)

            seatemp = check_seatemp(b["slug"], client)
            time.sleep(DELAY)

            noaa_ok = check_noaa(b["noaa_id"], client)
            time.sleep(DELAY)

            status = f"seatemp={seatemp} noaa={noaa_ok}"
            print(status)

            row = {**b, "seatemp_covered": seatemp, "noaa_valid": noaa_ok}
            results.append(row)

            if seatemp in ("yes", "page_exists_no_temp"):
                seatemp_hits.append(b["slug"])

            if seatemp in ("yes", "page_exists_no_temp") and b["noaa_id"] and noaa_ok == "valid":
                alias_rows.append(
                    f'    ("{b["slug"]}",{" " * max(1, 40 - len(b["slug"]))}'
                    f'"{b["noaa_id"]}",  "noaa"),  # {b["name"]}, {b["state"]}'
                )

    # Write CSV
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    # Write seatemp coverage list
    with open(OUT_SEATEMP, "w", encoding="utf-8") as f:
        f.write("\n".join(seatemp_hits))

    # Write alias rows ready to paste into init_db.py
    with open(OUT_ALIASES, "w", encoding="utf-8") as f:
        f.write("# Add these rows to ALIAS_SEED in db/init_db.py\n")
        f.write("\n".join(alias_rows))

    covered = sum(1 for r in results if r["seatemp_covered"] in ("yes", "page_exists_no_temp"))
    noaa_ok = sum(1 for r in results if r["noaa_valid"] == "valid")
    print(f"\nDone.")
    print(f"  seatemperature.info coverage: {covered}/{len(results)}")
    print(f"  NOAA stations verified:       {noaa_ok}/{len(results)}")
    print(f"  Results CSV:   {OUT_CSV}")
    print(f"  Seatemp list:  {OUT_SEATEMP}")
    print(f"  Alias rows:    {OUT_ALIASES}")


if __name__ == "__main__":
    main()
