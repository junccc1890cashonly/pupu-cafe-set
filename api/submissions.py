from __future__ import annotations

import json
import os
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LOCAL_DB = Path(__file__).resolve().parent.parent / "data" / "submissions.sqlite3"


def _json_response(body: dict[str, Any], status: int = 200) -> tuple[str, int, dict[str, str]]:
    return (
        json.dumps(body, ensure_ascii=False),
        status,
        {
            "Content-Type": "application/json; charset=utf-8",
            "Cache-Control": "no-store",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        },
    )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json_request(request) -> dict[str, Any]:
    raw = request.body
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    if not raw:
        return {}
    return json.loads(raw)


def _kv_config() -> tuple[str, str] | None:
    url = os.getenv("KV_REST_API_URL")
    token = os.getenv("KV_REST_API_TOKEN")
    if url and token:
        return url.rstrip("/"), token
    return None


def _kv_request(path: str, payload: dict[str, Any] | None = None) -> Any:
    cfg = _kv_config()
    if cfg is None:
        raise RuntimeError("KV not configured")
    base_url, token = cfg
    url = f"{base_url}{path}"
    body = None
    headers = {"Authorization": f"Bearer {token}"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url=url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _save_to_kv(record: dict[str, Any]) -> None:
    key = "cutlery-survey:submissions"
    _kv_request(f"/rpush/{urllib.parse.quote(key, safe='')}", {"items": [json.dumps(record, ensure_ascii=False)]})


def _read_from_kv() -> list[dict[str, Any]]:
    key = "cutlery-survey:submissions"
    response = _kv_request(f"/lrange/{urllib.parse.quote(key, safe='')}/0/-1")
    raw_items = response.get("result", [])
    return [json.loads(item) for item in raw_items]


def _db_path() -> Path:
    if os.access(LOCAL_DB.parent, os.W_OK):
        return LOCAL_DB
    return Path("/tmp/submissions.sqlite3")


def _ensure_sqlite() -> sqlite3.Connection:
    db_path = _db_path()
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submitted_at TEXT NOT NULL,
            payload TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def _save_to_sqlite(record: dict[str, Any]) -> None:
    conn = _ensure_sqlite()
    conn.execute(
        "INSERT INTO submissions (submitted_at, payload) VALUES (?, ?)",
        (record["submittedAt"], json.dumps(record, ensure_ascii=False)),
    )
    conn.commit()
    conn.close()


def _read_from_sqlite() -> list[dict[str, Any]]:
    conn = _ensure_sqlite()
    rows = conn.execute("SELECT payload FROM submissions ORDER BY id DESC").fetchall()
    conn.close()
    return [json.loads(row[0]) for row in rows]


def _save_record(record: dict[str, Any]) -> str:
    try:
        if _kv_config():
            _save_to_kv(record)
            return "vercel-kv"
    except (RuntimeError, urllib.error.URLError):
        pass
    _save_to_sqlite(record)
    return "sqlite"


def _read_records() -> tuple[list[dict[str, Any]], str]:
    try:
        if _kv_config():
            return _read_from_kv(), "vercel-kv"
    except (RuntimeError, urllib.error.URLError):
        pass
    return _read_from_sqlite(), "sqlite"


def handler(request):
    if request.method == "OPTIONS":
        return _json_response({}, 204)

    if request.method == "GET":
        records, storage = _read_records()
        return _json_response({"storage": storage, "submissions": records})

    if request.method != "POST":
        return _json_response({"error": "Method not allowed"}, 405)

    payload = _load_json_request(request)
    answers = payload.get("answers", [])
    if not isinstance(answers, list) or not answers:
        return _json_response({"error": "answers is required"}, 400)

    record = {
        "submittedAt": _now_iso(),
        "answers": answers,
    }
    storage = _save_record(record)
    return _json_response({"ok": True, "storage": storage, "submittedAt": record["submittedAt"]}, 201)
