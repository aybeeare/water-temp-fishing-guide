"""
Permanent log of every /fishing-guide request: Alexa, MCP (hosted and stdio)
and direct REST calls.

Lives in its own SQLite file, separate from fishing.db. fishing.db is reference
data rebuilt from git on every deploy, so anything written there is lost on
redeploy. On Railway, attach a volume and the log goes to
$RAILWAY_VOLUME_MOUNT_PATH/query_log.db automatically; set LOG_DB_PATH to
override.
"""
import logging
import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional

log = logging.getLogger("uvicorn.error")

_VOLUME = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
LOG_DB_PATH = os.environ.get(
    "LOG_DB_PATH",
    os.path.join(_VOLUME, "query_log.db") if _VOLUME else "query_log.db",
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS query_log (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    called_at     TEXT    NOT NULL,   -- ISO-8601 UTC
    channel       TEXT    NOT NULL,   -- alexa | mcp-http | mcp-stdio | rest
    agent         TEXT,               -- MCP client name when known, e.g. claude-ai
    user_agent    TEXT,
    query         TEXT,               -- location text as sent
    lat           REAL,
    lon           REAL,
    site_id_query TEXT,               -- explicit ?site_id=
    resolved_via  TEXT,               -- alias | coordinates | site_id
    site_id       TEXT,               -- station / slug it resolved to
    resolved_to   TEXT,               -- display name returned
    source        TEXT,               -- usgs | noaa | seatemperature.info
    temp_f        REAL,
    distance_km   REAL,
    outcome       TEXT    NOT NULL,   -- ok | no_reading | clarification | not_found | bad_request | error
    status_code   INTEGER NOT NULL,
    error         TEXT,
    latency_ms    INTEGER
);
CREATE INDEX IF NOT EXISTS idx_query_log_called_at ON query_log (called_at DESC);
CREATE INDEX IF NOT EXISTS idx_query_log_channel   ON query_log (channel, called_at DESC);
"""

COLUMNS = [
    "called_at", "channel", "agent", "user_agent", "query", "lat", "lon",
    "site_id_query", "resolved_via", "site_id", "resolved_to", "source",
    "temp_f", "distance_km", "outcome", "status_code", "error", "latency_ms",
]

CHANNELS = {"alexa", "mcp-http", "mcp-stdio", "rest"}


_ready: set[str] = set()


def connect() -> sqlite3.Connection:
    """Open the log DB, creating the file and table on first use."""
    if LOG_DB_PATH not in _ready:
        parent = os.path.dirname(LOG_DB_PATH)
        if parent:
            os.makedirs(parent, exist_ok=True)
        conn = sqlite3.connect(LOG_DB_PATH, timeout=5)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(SCHEMA)
        conn.close()
        _ready.add(LOG_DB_PATH)
    conn = sqlite3.connect(LOG_DB_PATH, timeout=5)
    conn.row_factory = sqlite3.Row
    return conn


def init_log_db() -> None:
    """Create the log table at startup. Warns when running on Railway without
    a volume, because the log would then be wiped on the next deploy."""
    connect().close()
    if os.environ.get("RAILWAY_ENVIRONMENT") and not _VOLUME and "LOG_DB_PATH" not in os.environ:
        log.warning("No Railway volume attached: query log at %s will be lost on redeploy", LOG_DB_PATH)
    else:
        log.info("Query log: %s", LOG_DB_PATH)


def infer_channel(client: Optional[str], user_agent: Optional[str]) -> str:
    """Explicit ?client= wins. Otherwise guess from the User-Agent: the Alexa
    Lambda uses urllib, and the PyPI stdio server uses httpx (the hosted MCP
    tool also uses httpx but always sends client=mcp-http)."""
    if client in CHANNELS:
        return client
    ua = (user_agent or "").lower()
    if ua.startswith("python-urllib"):
        return "alexa"
    if ua.startswith("python-httpx"):
        return "mcp-stdio"
    return "rest"


def record(**fields) -> None:
    """Append one row. Never raises: logging must not break a request."""
    fields.setdefault("called_at", datetime.now(timezone.utc).isoformat())
    row = [fields.get(c) for c in COLUMNS]
    try:
        conn = connect()
        conn.execute(
            f"INSERT INTO query_log ({', '.join(COLUMNS)}) VALUES ({', '.join('?' * len(COLUMNS))})",
            row,
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        log.warning("Query log write failed: %s", exc)
