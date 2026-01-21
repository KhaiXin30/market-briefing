from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Callable, Iterable, Optional

from zoneinfo import ZoneInfo


ET = ZoneInfo("America/New_York")

JARGON_MAP = {
    "CPI": "Consumer Price Index",
    "PPI": "Producer Price Index",
    "FOMC": "Federal Open Market Committee",
    "GDP": "gross domestic product",
    "ADR": "American depositary receipt",
    "EPS": "earnings per share",
    "ETF": "exchange-traded fund",
}

GAINER_WORDS = re.compile(r"\b(gain|gains|rally|surge|jump|rise|up)\b", re.I)
LOSER_WORDS = re.compile(r"\b(drop|drops|fall|falls|slip|down|plunge)\b", re.I)


def now_et() -> datetime:
    return datetime.now(tz=ET)


def parse_run_date(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=ET)


def edition_type(dt: datetime) -> str:
    return "weekend" if dt.weekday() >= 5 else "weekday"


def lookback_hours(dt: datetime) -> int:
    return 72 if edition_type(dt) == "weekend" else 24


def explain_jargon(text: str) -> str:
    if not text:
        return text
    for term, explanation in JARGON_MAP.items():
        pattern = rf"\b{re.escape(term)}\b"
        if re.search(pattern, text) and f"{term} [" not in text:
            text = re.sub(pattern, f"{term} [{explanation}]", text)
    return text


def concise_summary(text: str) -> str:
    if not text:
        return text
    for sep in [". ", "? ", "! "]:
        if sep in text:
            return text.split(sep)[0].strip() + sep.strip()
    return text


def _shorten(text: str, max_chars: int = 140) -> str:
    if not text:
        return text
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


def _extract_company_candidates(title: str) -> list[str]:
    if not title:
        return []
    cleaned = re.sub(r"^(Gainer:|Loser:)\s*", "", title).strip()
    parts = cleaned.split()
    if not parts:
        return []
    symbol = parts[0]
    rest = cleaned[len(symbol):].strip()
    for marker in [" up ", " down "]:
        if marker in rest:
            rest = rest.split(marker)[0].strip()
            break
    raw = rest.strip()
    suffixes = [
        "Class A Ordinary Shares",
        "Ordinary Shares",
        "Class A",
        "Class B",
        "S.A.",
        "Ltd",
        "Limited",
        "Inc.",
        "Inc",
        "Corp.",
        "Corp",
        "Holdings",
        "Holding",
        "Company",
    ]
    trimmed = raw
    for suffix in suffixes:
        if trimmed.endswith(suffix):
            trimmed = trimmed[: -len(suffix)].strip()
    trimmed_parts = trimmed.split()
    if trimmed_parts and trimmed_parts[0].isupper() and len(trimmed_parts[0]) <= 5:
        trimmed = " ".join(trimmed_parts[1:]).strip()
    candidates = [raw, trimmed]
    return [c for c in candidates if c]


def format_bullet(
    title: str,
    summary: str,
    source: str,
    link: str,
    summarizer: Optional[Callable[[str], Optional[str]]] = None,
) -> str:
    title = explain_jargon(title)
    summary = explain_jargon(summary)
    if summarizer:
        prompt = (
            "Write 1 sentence in a neutral, journalistic tone. "
            "Use only facts from the snippet; no preface or labels.\n"
            f"Title: {title}\nSnippet: {summary}"
        )
        model_summary = summarizer(prompt)
        if model_summary:
            cleaned = model_summary.strip()
            cleaned = re.sub(r"\(Note:.*?\)", "", cleaned, flags=re.I).strip()
            cleaned = cleaned.replace("Here's a market briefing summary:", "").strip()
            summary = cleaned
    summary = concise_summary(summary)
    if summary:
        return f"- {title} — {summary} ({source}, {link})"
    return f"- {title} ({source}, {link})"


def select_top(items: Iterable[dict], limit: int) -> list[dict]:
    items = [item for item in items if item.get("title") and item.get("link")]
    return items[:limit]


def select_balanced(items: Iterable[dict], limit: int) -> list[dict]:
    items = [item for item in items if item.get("title") and item.get("link")]
    seen = set()
    picked = []
    for item in items:
        source = item.get("source", "")
        if source and source not in seen:
            picked.append(item)
            seen.add(source)
        if len(picked) >= limit:
            return picked
    for item in items:
        if item in picked:
            continue
        picked.append(item)
        if len(picked) >= limit:
            break
    return picked


def build_briefing(
    articles: list[dict],
    edition: str,
    run_dt: datetime,
    summarizer: Optional[Callable[[str], Optional[str]]] = None,
) -> str:
    from src.company_profile import fetch_profile

    company_cache: dict[str, str] = {}
    by_sector = {}
    movers = []
    calendar = []
    general = []

    for article in articles:
        sector = article.get("sector", "unknown")
        if sector == "movers":
            movers.append(article)
        elif sector == "calendar":
            calendar.append(article)
        else:
            general.append(article)
            by_sector.setdefault(sector, []).append(article)

    content = []
    heading = "Pre-Market Edition" if edition == "weekday" else "Weekend Wrap"
    content.append(f"{heading} — {run_dt.strftime('%Y-%m-%d')}\n")

    top_items = select_balanced(general, 5)
    top_items_10 = select_balanced(general, 10)
    content.append("Overnight / Must-Know (Top 5)")
    if top_items_10 and summarizer:
        prompt_lines = ["Summarize the 10 items into exactly 5 bullets for a market briefing.",
                        "Rules: Use only the provided items, no new facts. Each bullet must start with '-' and end with (Source, URL).",
                        "No preface, no notes, no commentary.",
                        "Items:"]
        for idx, item in enumerate(top_items_10, start=1):
            title = item.get("title", "")
            snippet = item.get("summary", "")
            source = item.get("source", "")
            link = item.get("link", "")
            prompt_lines.append(f"{idx}. {title} | {snippet} | {source} | {link}")
        model_summary = summarizer("\n".join(prompt_lines))
        if model_summary:
            cleaned = model_summary.replace("Here are 5 bullets summarizing the provided market briefing items:", "").strip()
            cleaned = re.sub(r"\\(Note:.*?\\)", "", cleaned, flags=re.I)
            lines = [
                line.strip()
                for line in cleaned.splitlines()
                if line.strip() and "note:" not in line.lower()
            ]
            bullets = [line for line in lines if line.startswith(("-", "•"))]
            if bullets:
                normalized = [("- " + line.lstrip("-• ").strip()) for line in bullets]
                has_links = all("http" in bullet for bullet in normalized[:5])
                if len(normalized) >= 5 and has_links:
                    content.extend(normalized[:5])
                else:
                    content.extend(
                        [
                            format_bullet(
                                item["title"],
                                item.get("summary", ""),
                                item["source"],
                                item["link"],
                                summarizer=summarizer,
                            )
                            for item in top_items
                        ]
                    )
            else:
                content.extend(lines[:5])
        else:
            content.extend(
                [
                    format_bullet(
                        item["title"],
                        item.get("summary", ""),
                        item["source"],
                        item["link"],
                        summarizer=summarizer,
                    )
                    for item in top_items
                ]
            )
    else:
        if top_items:
            content.extend(
                [
                    format_bullet(
                        item["title"],
                        item.get("summary", ""),
                        item["source"],
                        item["link"],
                        summarizer=summarizer,
                    )
                    for item in top_items
                ]
            )
        else:
            content.append("- No verified RSS updates in the last window.")

    content.append("\nSector Snapshot")
    sector_order = ["tech", "semiconductors", "oil_gas", "retail"]
    for sector in sector_order:
        items = select_top(by_sector.get(sector, []), 1)
        if items:
            item = items[0]
            content.append(
                format_bullet(
                    item["title"],
                    item.get("summary", ""),
                    item["source"],
                    item["link"],
                    summarizer=summarizer,
                )
            )
        else:
            content.append(f"- {sector.replace('_', ' ').title()}: No major RSS updates.")

    if edition == "weekday":
        content.append("\nMovers (US + ADRs)")
        gainers = []
        losers = []
        for mover in movers:
            title = mover.get("title", "")
            source = mover.get("source", "")
            if source == "FMP":
                title_lower = title.lower()
                if "loser:" in title_lower or "down" in title_lower or re.search(r"-\\d", title_lower):
                    losers.append(mover)
                else:
                    gainers.append(mover)
            else:
                if GAINER_WORDS.search(title):
                    gainers.append(mover)
                if LOSER_WORDS.search(title):
                    losers.append(mover)
        gainers = select_top(gainers, 5)
        losers = select_top(losers, 5)
        if gainers:
            content.append("Gainers")
            content.extend(
                [
                    format_bullet(
                        item["title"],
                        _augment_mover_summary(item, fetch_profile, company_cache),
                        item["source"],
                        item["link"],
                        summarizer=None,
                    )
                    for item in gainers
                ]
            )
        else:
            content.append("- Gainers: No verified free-source movers.")
        if losers:
            content.append("Losers")
            content.extend(
                [
                    format_bullet(
                        item["title"],
                        _augment_mover_summary(item, fetch_profile, company_cache),
                        item["source"],
                        item["link"],
                        summarizer=None,
                    )
                    for item in losers
                ]
            )
        else:
            content.append("- Losers: No verified free-source movers.")

        content.append("\nToday's Calendar")
    else:
        content.append("\nWeek-Ahead Calendar")

    calendar_items = select_top(calendar, 5)
    if calendar_items:
        content.extend(
            [
                format_bullet(
                    item["title"],
                    item.get("summary", ""),
                    item["source"],
                    item["link"],
                    summarizer=summarizer,
                )
                for item in calendar_items
            ]
        )
    else:
        content.append("- No major macro events in RSS sources.")

    return "\n".join(content).strip() + "\n"


def build_portfolio_section(articles: list[dict], portfolio: list[dict]) -> list[str]:
    if not portfolio:
        return []
    lines = ["\nPortfolio Watch"]
    hits = []
    for item in portfolio:
        keywords = item.get("keywords", [])
        if not keywords:
            continue
        pattern = re.compile(r"|".join(re.escape(k) for k in keywords), re.I)
        for article in articles:
            haystack = f"{article.get('title','')} {article.get('summary','')}"
            if pattern.search(haystack):
                hits.append(article)
                break
    hits = select_top(hits, 5)
    if hits:
        lines.extend(
            [
                format_bullet(
                    item["title"],
                    item.get("summary", ""),
                    item["source"],
                    item["link"],
                )
                for item in hits
            ]
        )
    else:
        lines.append("- No portfolio-related RSS updates.")
    return lines


def build_portfolio_premarket_section(quotes: list[dict], symbols: list[str]) -> list[str]:
    lines = ["\nPortfolio Premarket"]
    if not quotes:
        if symbols:
            lines.append("- No premarket quotes returned for portfolio symbols.")
        else:
            lines.append("- No portfolio symbols configured.")
        return lines
    for quote in quotes:
        symbol = quote.get("symbol", "")
        name = quote.get("name", "")
        price = quote.get("price")
        change_pct = quote.get("changesPercentage")
        previous_close = quote.get("previousClose")
        change = quote.get("change")
        pct_text = "n/a"
        if change_pct is not None:
            try:
                pct_text = f"{float(change_pct):+.2f}%"
            except (TypeError, ValueError):
                pct_text = str(change_pct)
        elif change is not None and previous_close:
            try:
                pct = (float(change) / float(previous_close)) * 100
                pct_text = f"{pct:+.2f}%"
            except (TypeError, ValueError, ZeroDivisionError):
                pct_text = "n/a"
        elif price is not None and previous_close:
            try:
                pct = ((float(price) - float(previous_close)) / float(previous_close)) * 100
                pct_text = f"{pct:+.2f}%"
            except (TypeError, ValueError, ZeroDivisionError):
                pct_text = "n/a"
        price_text = f"{price}" if price is not None else "n/a"
        label = f"- {symbol} {name} {price_text} ({pct_text})".strip()
        lines.append(label)
    return lines


def _augment_mover_summary(
    item: dict,
    fetch_summary_func,
    cache: dict,
) -> str:
    summary = item.get("summary", "")
    title = item.get("title", "")
    symbol = title.split()[1] if title.startswith(("Gainer:", "Loser:")) else title.split()[0]
    candidates = _extract_company_candidates(title)
    company_name = candidates[0] if candidates else ""
    if not symbol:
        return summary
    if symbol in cache:
        about_info = cache[symbol]
    else:
        about_info = fetch_summary_func(symbol, company_name)
        cache[symbol] = about_info
    if not about_info:
        if summary:
            return f"{summary} | About: profile not found."
        return "About: profile not found."
    about, source = about_info
    about_text = _shorten(concise_summary(about), 140)
    if summary:
        return f"{summary} | About ({source}): {about_text}"
    return f"About ({source}): {about_text}"
