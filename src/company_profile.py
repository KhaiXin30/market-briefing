from __future__ import annotations

import os
import time
from functools import lru_cache

import requests


FMP_BASE = "https://financialmodelingprep.com/api/v3"


@lru_cache(maxsize=256)
def fetch_profile(symbol: str) -> tuple[str, str] | None:
    if not symbol:
        return None
    time.sleep(1.5)
    summary = _fetch_yahoo_summary(symbol)
    if summary:
        return summary, "Yahoo Finance"
    fmp_summary = _fetch_fmp_profile(symbol)
    if fmp_summary:
        return fmp_summary, "FMP"
    from src.openfigi import fetch_openfigi_summary
    figi_summary = fetch_openfigi_summary(symbol)
    if figi_summary:
        return figi_summary, "OpenFIGI"
    return None


def _fetch_yahoo_summary(symbol: str) -> str | None:
    url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
    params = {"modules": "assetProfile"}
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
    except requests.RequestException:
        return None

    try:
        result = data.get("quoteSummary", {}).get("result", [])
        if not result:
            return None
        profile = result[0].get("assetProfile", {})
        return profile.get("longBusinessSummary")
    except (AttributeError, IndexError, KeyError, TypeError):
        return None


def _fetch_fmp_profile(symbol: str) -> str | None:
    api_key = os.getenv("FMP_API_KEY")
    if not api_key:
        return None
    url = f"{FMP_BASE}/profile/{symbol}"
    try:
        resp = requests.get(url, params={"apikey": api_key}, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
    except requests.RequestException:
        return None

    if isinstance(data, list) and data:
        return data[0].get("description")
    return None
