#!/usr/bin/env python3
"""
Print a summary of queries from the live Railway server's query log
(Alexa, MCP and direct REST calls), or download the raw rows as CSV.

Usage:
    ACTIVITY_API_KEY=<your-key> python scripts/activity.py
    python scripts/activity.py --days 30 --channel mcp-stdio
    python scripts/activity.py --days 3650 --csv query_log.csv   # full backup

The key must match the ACTIVITY_API_KEY env var set on Railway.
"""
import argparse
import os
import sys

import httpx

RAILWAY_URL = "https://water-temp-fishing-guide-production.up.railway.app"
KEY = os.environ.get("ACTIVITY_API_KEY", "")


def fetch(params: dict) -> httpx.Response:
    try:
        resp = httpx.get(f"{RAILWAY_URL}/activity", headers={"X-Activity-Key": KEY},
                         params=params, timeout=60)
    except httpx.RequestError as e:
        sys.exit(f"Connection error: {e}")
    if resp.status_code == 403:
        sys.exit("Error: wrong API key")
    if resp.status_code != 200:
        sys.exit(f"Unexpected status {resp.status_code}: {resp.text[:200]}")
    return resp


def print_counts(title: str, counts: dict) -> None:
    if counts:
        print(f"\n{title}:")
        for key, n in counts.items():
            print(f"  {n:5d}  {key}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7, help="look-back window (default 7)")
    ap.add_argument("--channel", choices=["alexa", "mcp-http", "mcp-stdio", "rest"])
    ap.add_argument("--limit", type=int, default=50, help="recent calls to list (default 50)")
    ap.add_argument("--csv", metavar="FILE", help="save every row in the window to FILE instead")
    args = ap.parse_args()

    if not KEY:
        sys.exit("Error: set ACTIVITY_API_KEY env var")

    params = {"days": args.days, "limit": args.limit}
    if args.channel:
        params["channel"] = args.channel

    if args.csv:
        resp = fetch({**params, "format": "csv"})
        with open(args.csv, "w", encoding="utf-8", newline="") as f:
            f.write(resp.text)
        print(f"Saved {max(resp.text.count(chr(10)) - 1, 0)} rows to {args.csv}")
        return

    data = fetch(params).json()
    scope = f" ({args.channel})" if args.channel else ""
    print(f"\n=== Water Conditions — last {data['window_days']} days{scope} ===")
    print(f"Calls in window:  {data['total_calls']}")
    print(f"All-time calls:   {data['all_time_calls']}  (logging since {data['logging_since'] or '—'})")
    print(f"Log file:         {data['log_db']}")

    print_counts("By channel", data["by_channel"])
    print_counts("By outcome", data["by_outcome"])
    print_counts("By MCP client", data["by_agent"])
    print_counts("Top queries", data["top_queries"])

    if data["recent"]:
        print(f"\nLast {len(data['recent'])} calls:")
        print(f"  {'Timestamp (UTC)':<20} {'Channel':<10} {'Query':<26} {'Resolved':<26} {'Temp':>7}  Outcome")
        print("  " + "-" * 104)
        for r in data["recent"]:
            ts     = r["called_at"][:19].replace("T", " ")
            query  = (r["query"] or r["site_id_query"]
                      or (f"{r['lat']},{r['lon']}" if r["lat"] is not None else ""))[:25]
            out    = (r["resolved_to"] or "")[:25]
            temp   = f"{r['temp_f']}°F" if r.get("temp_f") is not None else "—"
            print(f"  {ts:<20} {r['channel']:<10} {query:<26} {out:<26} {temp:>7}  {r['outcome']}")


if __name__ == "__main__":
    main()
