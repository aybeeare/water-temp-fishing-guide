-- ── water_cache ──────────────────────────────────────────────────────────────
-- Populated by ingest/usgs_ingest.py on each fetch cycle.
-- site_id matches the USGS station number (e.g. '03290500').
CREATE TABLE IF NOT EXISTS water_cache (
    site_id       TEXT    PRIMARY KEY,
    site_name     TEXT    NOT NULL,
    temp_f        REAL,               -- NULL when sensor offline
    temp_c        REAL,
    temp_f_min    REAL,               -- coldest point (large water bodies only)
    temp_f_max    REAL,               -- warmest point (large water bodies only)
    fetched_at    TEXT    NOT NULL,   -- ISO-8601 UTC
    raw_datetime  TEXT                -- timestamp returned by USGS
);

-- ── fishing_logic ─────────────────────────────────────────────────────────────
-- Deterministic temperature-range → behavior + ASIN map.
-- Ranges are inclusive on both ends; logic layer selects the first match.
-- asin values are placeholders — replace with live Amazon Standard IDs.
CREATE TABLE IF NOT EXISTS fishing_logic (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    temp_min_f      REAL    NOT NULL,
    temp_max_f      REAL    NOT NULL,
    fish_behavior   TEXT    NOT NULL,   -- spoken to user verbatim
    recommended_gear TEXT   NOT NULL,   -- product label (not LLM-generated)
    asin            TEXT    NOT NULL,   -- Amazon ASIN for AddToShoppingCart
    water_type      TEXT    NOT NULL DEFAULT 'any',  -- 'freshwater' | 'saltwater' | 'any'
    target_species  TEXT    DEFAULT NULL,            -- NULL = generic fallback for any species
    secondary_asin  TEXT    DEFAULT NULL,            -- higher-ticket gear upsell ASIN
    secondary_gear  TEXT    DEFAULT NULL             -- upsell product label
);

CREATE INDEX IF NOT EXISTS idx_fishing_logic_temp
    ON fishing_logic (temp_min_f, temp_max_f);

-- ── local_sponsorships ────────────────────────────────────────────────────────
-- Paid placements: bait-and-tackle shops mapped to USGS site IDs.
-- audio_script is a static, pre-approved string — never LLM-generated.
CREATE TABLE IF NOT EXISTS local_sponsorships (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id       TEXT    NOT NULL,     -- USGS station number
    sponsor_name  TEXT    NOT NULL,
    audio_script  TEXT    NOT NULL,     -- read verbatim by Alexa
    active        INTEGER NOT NULL DEFAULT 1,  -- 1 = live, 0 = paused
    FOREIGN KEY (site_id) REFERENCES water_cache (site_id)
);

CREATE INDEX IF NOT EXISTS idx_sponsorships_site
    ON local_sponsorships (site_id, active);

-- ── location_aliases ──────────────────────────────────────────────────────────
-- Maps normalized user-spoken location names to a data source + identifier.
-- alias:   lowercase, hyphenated (e.g. 'lake-michigan', 'ocean-city')
-- site_id: USGS station number (source='usgs') OR seatemperature.info slug (source='scrape')
-- source:  'usgs'   → hit USGS IV API and water_cache by numeric station ID
--          'scrape' → hit seatemperature.info and cache under the slug as site_id
CREATE TABLE IF NOT EXISTS location_aliases (
    alias    TEXT PRIMARY KEY,
    site_id  TEXT NOT NULL,
    source   TEXT NOT NULL DEFAULT 'usgs'  -- 'usgs' | 'scrape'
);

CREATE INDEX IF NOT EXISTS idx_aliases_site
    ON location_aliases (site_id);

-- ── tide_cache ────────────────────────────────────────────────────────────────
-- Populated by ingest/noaa_ingest.py for NOAA coastal stations.
-- tide_type: 'H' (high) or 'L' (low)
-- tide_date: YYYY-MM-DD — cleared and rewritten each ingest cycle
CREATE TABLE IF NOT EXISTS tide_cache (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id     TEXT    NOT NULL,
    tide_type   TEXT    NOT NULL,
    tide_time   TEXT    NOT NULL,
    height_ft   REAL,
    fetched_at  TEXT    NOT NULL,
    tide_date   TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tide_cache_site
    ON tide_cache (site_id, tide_date);

-- ── site_species ──────────────────────────────────────────────────────────────
-- Maps a site_id (USGS station, NOAA station, or scrape slug) to its commonly
-- targeted fish species. Used to select species-appropriate gear recommendations.
-- species values: walleye, trout, salmon, northern_pike, largemouth_bass,
--                 smallmouth_bass, catfish, striped_bass, redfish, tarpon,
--                 bonefish, flounder, peacock_bass, yellowtail, halibut
CREATE TABLE IF NOT EXISTS site_species (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id  TEXT    NOT NULL,
    species  TEXT    NOT NULL,
    UNIQUE(site_id, species)
);

CREATE INDEX IF NOT EXISTS idx_site_species
    ON site_species (site_id);

-- ── bait_shop_cache ───────────────────────────────────────────────────────────
-- Nearest bait/tackle shop per station, refreshed daily via Google Places API.
-- open_now: 1=open, 0=closed, NULL=unknown (API didn't return hours)
CREATE TABLE IF NOT EXISTS bait_shop_cache (
    station_id   TEXT    PRIMARY KEY,
    shop_name    TEXT,
    shop_address TEXT,
    shop_rating  REAL,
    open_now     INTEGER,
    cached_date  TEXT    NOT NULL
);

-- ── api_call_log ──────────────────────────────────────────────────────────────
-- Daily call counter per external API — used to enforce rate limits.
CREATE TABLE IF NOT EXISTS api_call_log (
    api_name    TEXT NOT NULL,
    call_date   TEXT NOT NULL,
    call_count  INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (api_name, call_date)
);

-- ── tool_call_log ─────────────────────────────────────────────────────────────
-- One row per MCP tool invocation — logged by get_water_conditions.
-- success: 1 = returned data, 0 = error response
CREATE TABLE IF NOT EXISTS tool_call_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    called_at   TEXT    NOT NULL,   -- ISO-8601 UTC
    location    TEXT    NOT NULL,   -- raw user input
    resolved_to TEXT,               -- site_name returned by /fishing-guide
    temp_f      REAL,
    source      TEXT,               -- noaa / usgs / seatemperature.info
    success     INTEGER NOT NULL DEFAULT 1,
    error       TEXT
);

CREATE INDEX IF NOT EXISTS idx_tool_call_log_at
    ON tool_call_log (called_at DESC);
