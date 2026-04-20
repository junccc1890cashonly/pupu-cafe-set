from __future__ import annotations

import json
import os
import sqlite3
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Any


LOCAL_DB = Path(__file__).resolve().parent.parent / "data" / "submissions.sqlite3"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _kv_config() -> tuple[str, str] | None:
    url = os.getenv("KV_REST_API_URL")
    token = os.getenv("KV_REST_API_TOKEN")
    if url and token:
        return url.rstrip("/"), token
    return None


def _kv_request(payload: list[Any]) -> Any:
    cfg = _kv_config()
    if cfg is None:
        raise RuntimeError("KV not configured")
    base_url, token = cfg
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(url=base_url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _save_to_kv(record: dict[str, Any]) -> None:
    key = "cutlery-survey:submissions"
    _kv_request(["RPUSH", key, json.dumps(record, ensure_ascii=False)])


def _read_from_kv() -> list[dict[str, Any]]:
    key = "cutlery-survey:submissions"
    response = _kv_request(["LRANGE", key, 0, -1])
    raw_items = response.get("result", [])
    parsed: list[dict[str, Any]] = []
    for item in raw_items:
        try:
            value = json.loads(item)
            if isinstance(value, dict):
                parsed.append(value)
        except (TypeError, json.JSONDecodeError):
            continue
    return parsed


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


class handler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        records, storage = _read_records()
        self._send_json({"storage": storage, "submissions": records})

    def do_POST(self) -> None:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
        payload = json.loads(raw)
        answers = payload.get("answers", [])

        if not isinstance(answers, list) or not answers:
            self._send_json({"error": "answers is required"}, 400)
            return

        record = {
            "submittedAt": _now_iso(),
            "answers": answers,
        }
        storage = _save_record(record)
        self._send_json({"ok": True, "storage": storage, "submittedAt": record["submittedAt"]}, 201)
