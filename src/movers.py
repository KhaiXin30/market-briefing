from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import List

import requests


FMP_STABLE_BASE = "https://financialmodelingprep.com/stable"


def _get_json(url: str, params: dict) -> list[dict]:
    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except requests.HTTPError as exc:
        if os.getenv("FMP_DEBUG") == "1":
            resp = exc.response
            if resp is not None:
                print(f"FMP error {resp.status_code} {resp.url}")
                print(resp.text[:500])
        return []


def fetch_fmp_movers(kind: str, limit: int = 5, as_of: datetime | None = None) -> List[dict]:
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        return []

    if kind not in {"gainers", "losers"}:
        raise ValueError("kind must be gainers or losers")

    endpoint = "biggest-gainers" if kind == "gainers" else "biggest-losers"
    url = f"{FMP_STABLE_BASE}/{endpoint}"
    data = _get_json(url, {"apikey": api_key})
    now = as_of or datetime.now(tz=timezone.utc)

    rows = []
    for item in data[:limit]:
        symbol = item.get("symbol") or ""
        name = item.get("name") or symbol
        change_pct = item.get("changesPercentage")
        price = item.get("price")
        pct_text = ""
        if change_pct is not None:
            try:
                pct_text = f"{float(change_pct):.2f}%"
            except (TypeError, ValueError):
                pct_text = str(change_pct)
        direction = "up" if kind == "gainers" else "down"
        label = "Gainer" if kind == "gainers" else "Loser"
        title = f"{label}: {symbol} {name} {direction} {pct_text}".strip()
        summary = f"Price: {price}" if price is not None else ""
        link = f"https://financialmodelingprep.com/quote/{symbol}"
        rows.append(
            {
                "title": title,
                "link": link,
                "published_at": now,
                "source": "FMP",
                "sector": "movers",
                "summary": summary,
            }
        )
    return rows


def fetch_fmp_quotes(symbols: List[str]) -> List[dict]:
    api_key = os.getenv("FMP_API_KEY")
    if not api_key or not symbols:
        return []
    url = f"{FMP_STABLE_BASE}/quote"
    results = []
    for symbol in symbols:
        data = _get_json(url, {"symbol": symbol, "apikey": api_key})
        if isinstance(data, dict) and data.get("Error Message"):
            data = []
        if isinstance(data, list) and data:
            results.extend(data)
            continue
        data = _get_json(f"{url}/{symbol}", {"apikey": api_key})
        if isinstance(data, dict) and data.get("Error Message"):
            data = []
        if isinstance(data, list) and data:
            results.extend(data)
    return results
