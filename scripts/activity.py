#!/usr/bin/env python3
"""
Print a summary of MCP tool call activity from the live Railway server.

Usage:
    ACTIVITY_API_KEY=<your-key> python scripts/activity.py

The key must match the ACTIVITY_API_KEY env var set on Railway.
"""
import os
import sys
import json
import httpx

RAILWAY_URL = "https://water-temp-fishing-guide-production.up.railway.app"
KEY = os.environ.get("ACTIVITY_API_KEY", "")

if not KEY:
    print("Error: set ACTIVITY_API_KEY env var")
    sys.exit(1)

try:
    resp = httpx.get(
        f"{RAILWAY_URL}/activity",
        headers={"X-Activity-Key": KEY},
        timeout=15,
    )
except httpx.RequestError as e:
    print(f"Connection error: {e}")
    sys.exit(1)

if resp.status_code == 403:
    print("Error: wrong API key")
    sys.exit(1)

if resp.status_code != 200:
    print(f"Unexpected status {resp.status_code}: {resp.text[:200]}")
    sys.exit(1)

data = resp.json()

print("\n=== Water Conditions — MCP Activity ===")
print(f"Total tool calls:       {data['total_calls']}")
print(f"Unique locations asked: {data['unique_locations']}")
print(f"Success rate:           {data['success_rate']}")

if data["top_locations"]:
    print("\nTop locations:")
    for loc, count in data["top_locations"]:
        print(f"  {count:4d}x  {loc}")

if data["recent"]:
    print("\nLast 50 calls:")
    print(f"  {'Timestamp':<20} {'Input':<28} {'Resolved':<28} {'Temp':>7}  Src")
    print("  " + "-" * 95)
    for r in data["recent"]:
        ts       = r["called_at"][:19].replace("T", " ")
        loc_in   = (r["location"] or "")[:27]
        loc_out  = (r["resolved_to"] or ("ERR: " + (r.get("error") or "")) )[:27]
        temp     = f"{r['temp_f']}°F" if r.get("temp_f") is not None else "—"
        src      = (r.get("source") or "")[:14]
        flag     = "" if r["success"] else " !"
        print(f"  {ts:<20} {loc_in:<28} {loc_out:<28} {temp:>7}  {src}{flag}")
