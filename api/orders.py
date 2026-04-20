from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "orders.json"


def _json_response(body: dict[str, Any], status: int = 200) -> tuple[str, int, dict[str, str]]:
    return (
        json.dumps(body, ensure_ascii=False),
        status,
        {
            "Content-Type": "application/json; charset=utf-8",
            "Cache-Control": "no-store",
            "Access-Control-Allow-Origin": "*",
        },
    )


def handler(request):
    if request.method == "OPTIONS":
        return (
            "",
            204,
            {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            },
        )

    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    orders = payload["orders"]
    sample_size = min(10, len(orders))
    selected = random.sample(orders, sample_size)
    for order in selected:
        base = int(order["simulatedCutlery"])
        order["options"] = [base + step for step in range(0, 6)]

    return _json_response(
        {
            "meta": payload["meta"],
            "orders": selected,
        }
    )
