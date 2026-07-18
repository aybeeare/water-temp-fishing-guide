import sqlite3
import pytest
from pathlib import Path


SCHEMA_PATH = Path(__file__).parent.parent / "db" / "schema.sql"


@pytest.fixture
def db_path(tmp_path):
    """Fresh SQLite DB with full schema applied."""
    db_file = str(tmp_path / "test_fishing.db")
    conn = sqlite3.connect(db_file)
    conn.executescript(SCHEMA_PATH.read_text())
    conn.commit()
    conn.close()
    return db_file


@pytest.fixture
def seeded_db(db_path):
    """DB with minimal seed data for logic + alias tests."""
    conn = sqlite3.connect(db_path)
    conn.executemany(
        "INSERT INTO fishing_logic (temp_min_f, temp_max_f, fish_behavior, recommended_gear, asin, water_type) VALUES (?,?,?,?,?,?)",
        [
            (60, 72, "Bass pre-spawn feeding.", "Topwater Lure Pack", "B0FRESHASIN1", "freshwater"),
            (65, 78, "Excellent inshore action.", "Saltwater Jig Kit",  "B0SALTYASIN1", "saltwater"),
        ],
    )
    conn.executemany(
        "INSERT INTO location_aliases (alias, site_id, source) VALUES (?,?,?)",
        [
            ("lake-michigan",   "04085427",  "usgs"),
            ("boston-harbor",   "8443970",   "noaa"),
            ("ocean-city",      "ocean-city","scrape"),
            ("lake-tahoe",      "lake-tahoe","scrape"),
        ],
    )
    conn.executemany(
        "INSERT INTO water_cache (site_id, site_name, temp_f, temp_c, fetched_at, raw_datetime) VALUES (?,?,?,?,?,?)",
        [
            ("04085427", "Lake Michigan at Milwaukee, WI", 68.0, 20.0, "2099-01-01T00:00:00+00:00", None),
            ("8443970",  "Boston Harbor, MA",              62.5, 16.9, "2099-01-01T00:00:00+00:00", None),
            ("lake-tahoe","Lake Tahoe",                    58.0, 14.4, "2099-01-01T00:00:00+00:00", None),
        ],
    )
    conn.executemany(
        "INSERT INTO noaa_station_index (station_id, site_name, lat, lon, state, fetched_at) VALUES (?,?,?,?,?,?)",
        [
            ("8443970", "Boston Harbor, MA", 42.3548, -71.0512, "MA", "2099-01-01T00:00:00+00:00"),
            ("9410170", "San Diego, CA",     32.7142, -117.1736, "CA", "2099-01-01T00:00:00+00:00"),
        ],
    )
    conn.executemany(
        "INSERT INTO scrape_location_index (slug, site_name, lat, lon, fetched_at) VALUES (?,?,?,?,?)",
        [
            ("lake-tahoe", "Lake Tahoe", 39.0968, -120.0324, "2099-01-01T00:00:00+00:00"),
        ],
    )
    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def patch_db(seeded_db, monkeypatch):
    """Monkeypatch DB_PATH in all modules that read it."""
    import ingest.usgs_ingest          as usgs
    import ingest.noaa_ingest          as noaa
    import ingest.noaa_station_index   as noaa_index
    import ingest.scrape_location_index as scrape_index
    import ingest.geocode_ingest       as geocode
    import ingest.sea_temp_scraper     as scraper
    import ingest.places_ingest        as places
    import api.main                    as api_main

    monkeypatch.setattr(usgs,        "DB_PATH", seeded_db)
    monkeypatch.setattr(noaa,        "DB_PATH", seeded_db)
    monkeypatch.setattr(noaa_index,  "DB_PATH", seeded_db)
    monkeypatch.setattr(scrape_index,"DB_PATH", seeded_db)
    monkeypatch.setattr(geocode,     "DB_PATH", seeded_db)
    monkeypatch.setattr(scraper,     "DB_PATH", seeded_db)
    monkeypatch.setattr(places,      "DB_PATH", seeded_db)
    monkeypatch.setattr(api_main,    "DB_PATH", seeded_db)
    return seeded_db
