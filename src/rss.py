from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlparse

import os

import feedparser
import requests


def _clean_html(text: Optional[str]) -> str:
    if not text:
        return ""
    return html.unescape(
        " ".join(text.replace("<br>", " ").replace("</p>", " ").split())
    )


def _domain_allowed(link: str, allowlist: List[str]) -> bool:
    try:
        domain = urlparse(link).netloc.lower()
    except ValueError:
        return False
    return any(domain.endswith(allowed) for allowed in allowlist)


def _link_accessible(link: str, timeout: int = 8) -> bool:
    try:
        resp = requests.head(link, allow_redirects=True, timeout=timeout)
        if resp.status_code < 400:
            return True
        resp = requests.get(link, allow_redirects=True, timeout=timeout)
        return resp.status_code < 400
    except requests.RequestException:
        return False


def fetch_feed(url: str, user_agent: str | None = None):
    ua = user_agent or "market-briefing-agent/1.0 (contact: kuankhaixin2003@gmail.com)"
    try:
        resp = requests.get(url, headers={"User-Agent": ua}, timeout=20)
    except requests.RequestException:
        return feedparser.parse("")
    if resp.status_code != 200:
        return feedparser.parse("")
    return feedparser.parse(resp.text)


def parse_entries(
    feed,
    source_name: str,
    sector: str,
    allowlist: List[str],
    max_future_minutes: int = 10,
) -> list[dict]:
    verify_links = os.getenv("VERIFY_LINKS") == "1"
    entries = []
    now_utc = datetime.now(tz=timezone.utc)
    future_cutoff = now_utc.timestamp() + (max_future_minutes * 60)
    for entry in feed.entries:
        link = entry.get("link", "")
        if link and not _domain_allowed(link, allowlist):
            continue
        if link and verify_links and not _link_accessible(link):
            continue
        published = entry.get("published") or entry.get("updated")
        published_at = None
        if published:
            try:
                published_at = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            except Exception:
                published_at = None
        if published_at and published_at.timestamp() > future_cutoff:
            continue
        summary = _clean_html(entry.get("summary", ""))
        entries.append(
            {
                "title": _clean_html(entry.get("title", "")),
                "link": link,
                "published_at": published_at,
                "source": source_name,
                "sector": sector,
                "summary": summary,
            }
        )
    return entries
