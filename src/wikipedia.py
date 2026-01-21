from __future__ import annotations

import requests
from urllib.parse import quote


def _search_title(query: str) -> str | None:
    params = {
        "action": "opensearch",
        "search": query,
        "limit": 1,
        "namespace": 0,
        "format": "json",
    }
    try:
        resp = requests.get("https://en.wikipedia.org/w/api.php", params=params, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if isinstance(data, list) and len(data) >= 2 and data[1]:
            return data[1][0]
    except requests.RequestException:
        return None
    return None


def fetch_summary(title: str) -> str | None:
    if not title:
        return None
    resolved = _search_title(title) or title
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(resolved)}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data.get("extract")
    except requests.RequestException:
        return None
