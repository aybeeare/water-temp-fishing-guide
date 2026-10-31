"""Tests for the permanent query log (api/query_log.py) and the /activity view."""
import csv
import io
import sqlite3
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import api.query_log as query_log
from mcp_server.formatting import query_params


def rows(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    out = [dict(r) for r in conn.execute("SELECT * FROM query_log ORDER BY id")]
    conn.close()
    return out


@pytest.fixture
def client(patch_db):
    import api.main as api_main
    return TestClient(api_main.app)


# ---------------------------------------------------------------------------
# Channel detection
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("client_param, ua, expected", [
    ("mcp-http",  "python-httpx/0.28", "mcp-http"),
    ("mcp-stdio", None,                "mcp-stdio"),
    (None,        "Python-urllib/3.12", "alexa"),
    (None,        "python-httpx/0.27.0", "mcp-stdio"),   # PyPI clients before 1.3.0
    (None,        "curl/8.4.0",        "rest"),
    ("bogus",     "Mozilla/5.0",       "rest"),
])
def test_infer_channel(client_param, ua, expected):
    assert query_log.infer_channel(client_param, ua) == expected


def test_record_never_raises(monkeypatch, tmp_path):
    monkeypatch.setattr(query_log, "LOG_DB_PATH", str(tmp_path / "missing-dir" / "x" / "log.db"))
    query_log.record(channel="rest", outcome="ok", status_code=200)  # creates dirs
    monkeypatch.setattr(query_log, "LOG_DB_PATH", str(tmp_path))       # a directory: write fails
    query_log.record(channel="rest", outcome="ok", status_code=200)    # must not raise


# ---------------------------------------------------------------------------
# /fishing-guide writes one row per request
# ---------------------------------------------------------------------------

def test_successful_lookup_is_logged(client, isolated_query_log):
    with patch("api.main.run_ingest"):
        resp = client.get("/fishing-guide", params={"location": "lake michigan", "client": "mcp-http",
                                                    "agent": "claude-ai/1.0"})
    assert resp.status_code == 200
    [row] = rows(isolated_query_log)
    assert row["channel"] == "mcp-http"
    assert row["agent"] == "claude-ai/1.0"
    assert row["query"] == "lake michigan"
    assert row["site_id"] == "04085427"
    assert row["resolved_to"] == resp.json()["site_name"]
    assert row["outcome"] == "ok"
    assert row["status_code"] == 200
    assert row["temp_f"] == 68.0
    assert row["latency_ms"] >= 0


def test_not_found_is_logged(client, isolated_query_log):
    with patch("api.main.is_cache_fresh", return_value=False), \
         patch("api.main.scrape_and_cache", return_value=None), \
         patch("api.main.geocode_location", return_value=None):
        resp = client.get("/fishing-guide", params={"location": "zxqwerty fictional lake"})
    assert resp.status_code == 404
    [row] = rows(isolated_query_log)
    assert row["outcome"] == "not_found"
    assert row["status_code"] == 404
    assert "zxqwerty" in row["error"]


def test_bad_request_is_logged(client, isolated_query_log):
    resp = client.get("/fishing-guide", params={"lat": 42.36})
    assert resp.status_code == 400
    [row] = rows(isolated_query_log)
    assert row["outcome"] == "bad_request"
    assert row["lat"] == 42.36


def test_clarification_is_logged(client, isolated_query_log):
    resp = client.get("/fishing-guide", params={"location": "ocean city"})
    assert resp.json()["disambiguation"]
    [row] = rows(isolated_query_log)
    assert row["outcome"] == "clarification"


def test_coordinates_are_logged(client, isolated_query_log):
    with patch("api.main.find_nearest_usgs_site", return_value=None), \
         patch("api.main.find_nearest_noaa_station", return_value=None):
        client.get("/fishing-guide", params={"lat": 0.0, "lon": 0.0})
    [row] = rows(isolated_query_log)
    assert (row["lat"], row["lon"]) == (0.0, 0.0)
    assert row["outcome"] == "not_found"


# ---------------------------------------------------------------------------
# /activity
# ---------------------------------------------------------------------------

@pytest.fixture
def keyed(monkeypatch):
    import api.main as api_main
    monkeypatch.setattr(api_main, "ACTIVITY_API_KEY", "secret")
    return {"X-Activity-Key": "secret"}


def _seed(n_alexa=2, n_mcp=3):
    for _ in range(n_alexa):
        query_log.record(channel="alexa", query="boston", outcome="ok", status_code=200)
    for _ in range(n_mcp):
        query_log.record(channel="mcp-http", agent="claude-ai", query="lake erie",
                         outcome="ok", status_code=200)


def test_activity_requires_key(client, keyed):
    assert client.get("/activity").status_code == 403
    assert client.get("/activity", headers={"X-Activity-Key": "wrong"}).status_code == 403


def test_activity_summary(client, keyed):
    _seed()
    body = client.get("/activity", headers=keyed).json()
    assert body["total_calls"] == 5
    assert body["by_channel"] == {"mcp-http": 3, "alexa": 2}
    assert body["by_agent"]["claude-ai"] == 3
    assert body["top_queries"]["lake erie"] == 3
    assert len(body["recent"]) == 5


def test_activity_channel_filter(client, keyed):
    _seed()
    body = client.get("/activity", headers=keyed, params={"channel": "alexa"}).json()
    assert body["total_calls"] == 2
    assert body["all_time_calls"] == 5


def test_activity_csv_export(client, keyed):
    _seed()
    resp = client.get("/activity", headers=keyed, params={"format": "csv"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    parsed = list(csv.DictReader(io.StringIO(resp.text)))
    assert len(parsed) == 5
    assert parsed[0]["channel"] == "alexa"


# ---------------------------------------------------------------------------
# MCP clients tag their requests
# ---------------------------------------------------------------------------

def test_query_params_tags():
    p = query_params("Lake Erie", None, None, client="mcp-stdio", agent="claude-ai")
    assert p == {"location": "Lake Erie", "bait_shop": "false", "client": "mcp-stdio", "agent": "claude-ai"}
    assert "agent" not in query_params("Lake Erie", None, None, client="mcp-stdio")
