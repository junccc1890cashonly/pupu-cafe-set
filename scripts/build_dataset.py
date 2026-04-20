from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path


SOURCE_CSV = Path(
    "/Users/junc/Desktop/PUPU3/项目：餐饮配件/"
    "【餐饮】餐饮项目C端订单餐具配置一次性取数「20260224-20260319」_v4_562371776253148455_20260416102013.csv"
)
OUTPUT_JSON = Path("/Users/junc/Documents/PUPU2026/cutlery-survey/data/orders.json")
OUTPUT_CSV = Path("/Users/junc/Documents/PUPU2026/cutlery-survey/data/orders_diff_gte_5.csv")

SIDE_CATEGORIES = {"主菜类", "主食类", "佐餐凉卤", "烧烤炸物"}


def _to_float(value: str | None) -> float:
    if value in (None, "", "nan", "NaN"):
        return 0.0
    return float(value)


def calc_simulated_cutlery(cutlery_type: str, combo_qty: float, side_weight: float) -> int:
    if cutlery_type == "无需餐具":
        return 0
    return int(combo_qty) + math.floor(side_weight / 650)


def build_survey_orders() -> dict[str, object]:
    orders: dict[str, dict[str, object]] = {}

    with SOURCE_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            order_no = row["订单号"]
            order = orders.setdefault(
                order_no,
                {
                    "orderNo": order_no,
                    "cutleryType": "",
                    "merchantCutlery": 0.0,
                    "actualCutlery": 0.0,
                    "comboQty": 0.0,
                    "sideWeight": 0.0,
                    "items": [],
                },
            )

            qty = _to_float(row["商品数量"])
            weight = _to_float(row["销售单位净重"])
            merchant = _to_float(row["商家按量提供餐具数量"])
            actual = _to_float(row["实际履约中式餐具包数量"])

            order["merchantCutlery"] = max(float(order["merchantCutlery"]), merchant)
            order["actualCutlery"] = max(float(order["actualCutlery"]), actual)

            if row["餐具选择类型"] == "无需餐具":
                order["cutleryType"] = "无需餐具"
            elif not order["cutleryType"] and row["餐具选择类型"]:
                order["cutleryType"] = row["餐具选择类型"]

            if row["三级财务类别"] == "套餐组合":
                order["comboQty"] = float(order["comboQty"]) + qty

            is_side = (
                row["二级财务类别"] == "中式餐食部"
                and row["三级财务类别"] in SIDE_CATEGORIES
                and row["四级财务类别"] != "汤羹类"
            )
            if is_side:
                order["sideWeight"] = float(order["sideWeight"]) + weight * qty

            order["items"].append(
                {
                    "name": row["商品名称"],
                    "quantity": int(qty),
                    "category": row["三级财务类别"],
                }
            )

    survey_orders = []
    survey_csv_rows = []
    for order in orders.values():
        simulated = calc_simulated_cutlery(
            str(order["cutleryType"]), float(order["comboQty"]), float(order["sideWeight"])
        )
        diff = int(float(order["actualCutlery"]) - simulated)
        if diff < 5:
            continue

        survey_orders.append(
            {
                "orderNo": order["orderNo"],
                "cutleryType": order["cutleryType"],
                "merchantCutlery": int(float(order["merchantCutlery"])),
                "actualCutlery": int(float(order["actualCutlery"])),
                "simulatedCutlery": int(simulated),
                "comboQty": int(float(order["comboQty"])),
                "sideWeight": int(float(order["sideWeight"])),
                "diff": diff,
                "items": order["items"],
            }
        )
        survey_csv_rows.append(
            {
                "订单号": order["orderNo"],
                "餐具选择类型": order["cutleryType"],
                "商家按量提供餐具数量": int(float(order["merchantCutlery"])),
                "实际履约中式餐具包数量": int(float(order["actualCutlery"])),
                "仿真中式餐具包数量": int(simulated),
                "套餐组合数量": int(float(order["comboQty"])),
                "配菜总重量": int(float(order["sideWeight"])),
                "diff": diff,
            }
        )

    survey_orders.sort(key=lambda item: item["orderNo"])
    survey_csv_rows.sort(key=lambda item: item["订单号"])

    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "订单号",
                "餐具选择类型",
                "商家按量提供餐具数量",
                "实际履约中式餐具包数量",
                "仿真中式餐具包数量",
                "套餐组合数量",
                "配菜总重量",
                "diff",
            ],
        )
        writer.writeheader()
        writer.writerows(survey_csv_rows)

    payload = {
        "meta": {
            "source_csv": str(SOURCE_CSV),
            "order_count": len(survey_orders),
            "rule_summary": [
                "汤类不纳入配菜重量",
                "餐具选择类型=无需餐具时仿真值为0",
                "套餐组合数量全部计入基础包",
                "套餐外配菜按每650g增加1个中式餐具包",
            ],
        },
        "orders": survey_orders,
    }
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> None:
    payload = build_survey_orders()
    print(f"Saved {payload['meta']['order_count']} survey orders to {OUTPUT_JSON}")
    print(f"Saved csv to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
