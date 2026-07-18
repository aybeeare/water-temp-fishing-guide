"""Unit tests for ingest/scrape_location_index.py"""
import sqlite3

import pytest

import ingest.scrape_location_index as index_mod
from ingest.scrape_location_index import (
    enumerate_scrape_slugs,
    backfill_scrape_location_index,
    find_nearest_scrape_location,
)

# ---------------------------------------------------------------------------
# Slug enumeration
# ---------------------------------------------------------------------------

def test_enumerate_scrape_slugs(db_path):
    conn = sqlite3.connect(db_path)
    conn.executemany(
        "INSERT INTO location_aliases (alias, site_id, source) VALUES (?,?,?)",
        [
            ("lake-tahoe", "lake-tahoe", "scrape"),
            ("tahoe",      "lake-tahoe", "scrape"),  # same slug, different alias
            ("ocean-city", "ocean-city", "scrape"),
            ("boston-harbor", "8443970", "noaa"),    # not scrape — excluded
        ],
    )
    conn.commit()
    slugs = enumerate_scrape_slugs(conn)
    conn.close()
    assert set(slugs) == {"lake-tahoe", "ocean-city"}

def test_enumerate_scrape_slugs_empty(db_path):
    conn = sqlite3.connect(db_path)
    slugs = enumerate_scrape_slugs(conn)
    conn.close()
    assert slugs == []

# ---------------------------------------------------------------------------
# Backfill
# ---------------------------------------------------------------------------

def test_backfill_scrape_location_index_writes_rows(db_path, monkeypatch):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "INSERT INTO location_aliases (alias, site_id, source) VALUES ('lake-tahoe', 'lake-tahoe', 'scrape')"
    )
    conn.commit()

    monkeypatch.setattr(index_mod, "geocode_location", lambda query: (39.0968, -120.0324))

    written = backfill_scrape_location_index(conn)
    row = conn.execute("SELECT * FROM scrape_location_index WHERE slug = 'lake-tahoe'").fetchone()
    conn.close()

    assert written == 1
    assert row["site_name"] == "Lake Tahoe"
    assert row["lat"] == pytest.approx(39.0968)
    assert row["lon"] == pytest.approx(-120.0324)

def test_backfill_scrape_location_index_skips_failed_geocode(db_path, monkeypatch):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "INSERT INTO location_aliases (alias, site_id, source) VALUES ('nowhere-fictional', 'nowhere-fictional', 'scrape')"
    )
    conn.commit()

    monkeypatch.setattr(index_mod, "geocode_location", lambda query: None)

    written = backfill_scrape_location_index(conn)
    count = conn.execute("SELECT COUNT(*) FROM scrape_location_index").fetchone()[0]
    conn.close()

    assert written == 0
    assert count == 0

def test_backfill_scrape_location_index_overwrites(db_path, monkeypatch):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "INSERT INTO location_aliases (alias, site_id, source) VALUES ('lake-tahoe', 'lake-tahoe', 'scrape')"
    )
    conn.commit()

    monkeypatch.setattr(index_mod, "geocode_location", lambda query: (0.0, 0.0))
    backfill_scrape_location_index(conn)

    monkeypatch.setattr(index_mod, "geocode_location", lambda query: (39.0968, -120.0324))
    backfill_scrape_location_index(conn)

    row = conn.execute("SELECT * FROM scrape_location_index WHERE slug = 'lake-tahoe'").fetchone()
    conn.close()
    assert row["lat"] == pytest.approx(39.0968)

# ---------------------------------------------------------------------------
# Nearest-neighbor lookup
# ---------------------------------------------------------------------------

def test_find_nearest_scrape_location_picks_closest(seeded_db):
    # seeded_db has a 'lake-tahoe' entry — query near it
    conn = sqlite3.connect(seeded_db)
    conn.row_factory = sqlite3.Row
    result = find_nearest_scrape_location(conn, 39.10, -120.03, max_km=150)
    conn.close()
    assert result is not None
    assert result["slug"] == "lake-tahoe"
    assert result["distance_km"] < 5

def test_find_nearest_scrape_location_beyond_threshold(seeded_db):
    conn = sqlite3.connect(seeded_db)
    conn.row_factory = sqlite3.Row
    result = find_nearest_scrape_location(conn, 0.0, 0.0, max_km=150)
    conn.close()
    assert result is None

def test_find_nearest_scrape_location_no_entries(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    result = find_nearest_scrape_location(conn, 39.10, -120.03, max_km=150)
    conn.close()
    assert result is None
