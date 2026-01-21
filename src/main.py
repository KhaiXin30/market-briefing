from __future__ import annotations

import argparse
import os
from datetime import timedelta

from src import briefing
from src.config import env_var, load_config
from src.db import fetch_recent_articles, get_briefing, init_db, insert_articles, upsert_briefing

from src.movers import fetch_fmp_movers, fetch_fmp_quotes
from src.rss import fetch_feed, parse_entries
from src.send import send_email
from src.summarizer import summarize as hf_summarize


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Market briefing agent")
    parser.add_argument("--config", default=env_var("CONFIG_PATH", "config/sources.yaml"))
    parser.add_argument("--schema", default=env_var("SCHEMA_PATH", "sql/schema.sql"))
    parser.add_argument("--run-date", help="Override run date (YYYY-MM-DD) in ET")
    parser.add_argument("--no-send", action="store_true")
    parser.add_argument("--force-send", action="store_true")
    parser.add_argument("--force-rebuild", action="store_true", help="Rebuild briefing even if cached")
    return parser.parse_args()


def ingest_feeds(config_path: str, schema_path: str, run_dt) -> None:
    config = load_config(config_path)
    init_db(schema_path)

    entries = []
    for feed in config.feeds:
        parsed = fetch_feed(feed.url)
        entries.extend(parse_entries(parsed, feed.name, feed.sector, config.allowlist_domains))

    for feed in config.calendar_feeds:
        parsed = fetch_feed(feed.url)
        entries.extend(parse_entries(parsed, feed.name, "calendar", config.allowlist_domains))

    for feed in config.movers_feeds:
        parsed = fetch_feed(feed.url)
        entries.extend(parse_entries(parsed, feed.name, "movers", config.allowlist_domains))

    entries.extend(fetch_fmp_movers("gainers", as_of=run_dt))
    entries.extend(fetch_fmp_movers("losers", as_of=run_dt))

    insert_articles(entries)


def build_and_send(
    config_path: str,
    schema_path: str,
    send_enabled: bool,
    force_send: bool,
    run_date_override: str | None = None,
    force_rebuild: bool = False,
) -> str:
    run_dt = briefing.now_et()
    if run_date_override:
        run_dt = briefing.parse_run_date(run_date_override)
    ingest_feeds(config_path, schema_path, run_dt)
    edition = briefing.edition_type(run_dt)
    lookback = briefing.lookback_hours(run_dt)
    since = (run_dt - timedelta(hours=lookback)).isoformat()

    articles = fetch_recent_articles(since)
    summarizer = hf_summarize if os.getenv("HF_TOKEN") else None
    content = briefing.build_briefing(articles, edition, run_dt, summarizer=summarizer)
    config = load_config(config_path)
    portfolio_section = briefing.build_portfolio_section(
        articles,
        [p.__dict__ for p in config.portfolio],
    )
    portfolio_symbols = [p.symbol for p in config.portfolio]
    quotes = fetch_fmp_quotes(portfolio_symbols)
    portfolio_premarket = briefing.build_portfolio_premarket_section(quotes, portfolio_symbols)
    if portfolio_section:
        content = content.rstrip() + "\n" + "\n".join(portfolio_section) + "\n"
    if portfolio_premarket:
        content = content.rstrip() + "\n" + "\n".join(portfolio_premarket) + "\n"

    edition_date = run_dt.strftime("%Y-%m-%d")
    existing = None if force_rebuild else get_briefing(edition_date, edition)
    if existing:
        content = existing
    else:
        upsert_briefing(edition_date, edition, content)

    if send_enabled:
        subject = f"{edition.capitalize()} Market Briefing — {edition_date}"
        to_emails = [email.strip() for email in os.getenv("TO_EMAILS", "").split(",") if email.strip()]
        if not to_emails:
            raise RuntimeError("TO_EMAILS is required when sending")
        if not existing or force_send:
            send_email(subject, content, to_emails)
    return content


def main() -> None:
    args = parse_args()
    print("Running market briefing job...")
    content = build_and_send(
        args.config,
        args.schema,
        send_enabled=not args.no_send,
        force_send=args.force_send,
        run_date_override=args.run_date,
        force_rebuild=args.force_rebuild,
    )
    if args.no_send:
        print(content)
    else:
        print("Send attempted. Use --no-send to print content.")


if __name__ == "__main__":
    main()
