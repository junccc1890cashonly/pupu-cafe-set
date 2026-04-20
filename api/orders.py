from __future__ import annotations

import json
import random
from http.server import BaseHTTPRequestHandler
from pathlib import Path


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "orders.json"


class handler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        orders = payload["orders"]
        sample_size = min(10, len(orders))
        selected = random.sample(orders, sample_size)

        sampled_orders = []
        for order in selected:
            copied = dict(order)
            base = int(copied["simulatedCutlery"])
            copied["options"] = [base + step for step in range(0, 6)]
            sampled_orders.append(copied)

        self._send_json(
            {
                "meta": payload["meta"],
                "orders": sampled_orders,
            }
        )
