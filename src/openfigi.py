from __future__ import annotations

import os
import time
from functools import lru_cache

import requests


@lru_cache(maxsize=256)
def fetch_openfigi_summary(symbol: str) -> str | None:
    if not symbol:
        return None
    time.sleep(1.0)
    url = "https://api.openfigi.com/v3/mapping"
    payload = [{"idType": "TICKER", "idValue": symbol}]
    headers = {"Content-Type": "application/json"}
    api_key = os.getenv("OPENFIGI_API_KEY")
    if api_key:
        headers["X-OPENFIGI-APIKEY"] = api_key
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json()
    except requests.RequestException:
        return None

    if not isinstance(data, list) or not data:
        return None
    result = data[0]
    values = result.get("data", [])
    if not values:
        return None
    item = values[0]
    name = item.get("name")
    description = item.get("securityDescription") or item.get("securityType2")
    if name and description:
        return f"{name} — {description}"
    return name or description
