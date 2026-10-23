"""Cost of model calls from the provider price list (config.yaml evaluation.prices).

A price row applies to a call when its provider and model_id equal the call's. Cost of a call:
    (prompt tokens - cached tokens) x input price
    + cached tokens x cached input price (input price where none is listed)
    + completion tokens x output price
per million tokens. Reasoning tokens are part of the completion tokens in the OpenAI usage
format and are billed as output, so they are not added a second time. Image tokens are part of
the prompt tokens. A failed call that returned no usage costs nothing.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

PriceKey = tuple[str, str]


def _number(text: str | None) -> float | None:
    text = (text or "").strip()
    return float(text) if text else None


def load_prices(path: str | Path) -> dict[PriceKey, dict[str, Any]]:
    prices: dict[PriceKey, dict[str, Any]] = {}
    with Path(path).open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            provider, model = (row.get("provider") or "").strip(), (row.get("model_id") or "").strip()
            if not provider or not model or _number(row.get("input_per_million")) is None:
                continue
            prices[(provider, model)] = {
                "input_per_million": _number(row["input_per_million"]),
                "cached_input_per_million": _number(row.get("cached_input_per_million")),
                "output_per_million": _number(row.get("output_per_million")),
                "currency": row.get("currency"),
                "status": row.get("status"),
                "retrieved_on": row.get("retrieved_on"),
            }
    return prices


def call_cost(call: dict[str, Any], prices: dict[PriceKey, dict[str, Any]]) -> tuple[float | None, str | None]:
    """(cost, problem). Cost is None when no price row applies or the usage is incomplete."""
    if not call.get("usage"):
        return 0.0, None  # failed before the provider returned usage
    price = prices.get((call.get("provider"), call.get("model")))
    if price is None:
        return None, f"no price row for {call.get('provider')} / {call.get('model')}"
    prompt, completion = call.get("prompt_tokens"), call.get("completion_tokens")
    if prompt is None or completion is None or price["output_per_million"] is None:
        return None, "usage or output price missing"
    cached = call.get("cached_tokens") or 0
    cached_rate = price["cached_input_per_million"]
    if cached_rate is None:
        cached_rate = price["input_per_million"]
    cost = ((prompt - cached) * price["input_per_million"] + cached * cached_rate
            + completion * price["output_per_million"]) / 1_000_000
    return round(cost, 8), None


def run_cost(calls: list[dict[str, Any]], prices: dict[PriceKey, dict[str, Any]]) -> dict[str, Any]:
    total, problems, rows = 0.0, [], set()
    for call in calls:
        cost, problem = call_cost(call, prices)
        call["cost_usd"] = cost
        if problem:
            problems.append(problem)
        elif cost is not None:
            total += cost
            price = prices.get((call.get("provider"), call.get("model")))
            if price:
                rows.add((call["provider"], call["model"], price["status"], price["retrieved_on"]))
    return {
        "cost_usd": None if problems else round(total, 8),
        "problems": sorted(set(problems)),
        "price_rows": [{"provider": p, "model_id": m, "status": s, "retrieved_on": r} for p, m, s, r in sorted(rows)],
    }
