import os
from dataclasses import dataclass
from typing import List

import yaml
from dotenv import load_dotenv


@dataclass
class Feed:
    name: str
    url: str
    sector: str


@dataclass
class SimpleFeed:
    name: str
    url: str


@dataclass
class PortfolioItem:
    symbol: str
    name: str
    keywords: List[str]


@dataclass
class AppConfig:
    allowlist_domains: List[str]
    feeds: List[Feed]
    calendar_feeds: List[SimpleFeed]
    movers_feeds: List[SimpleFeed]
    portfolio: List[PortfolioItem]


def load_config(path: str) -> AppConfig:
    load_dotenv()
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    feeds = [Feed(**item) for item in raw.get("feeds", [])]
    calendar_feeds = [SimpleFeed(**item) for item in raw.get("calendar_feeds", [])]
    movers_feeds = [SimpleFeed(**item) for item in raw.get("movers_feeds", [])]
    portfolio = [PortfolioItem(**item) for item in raw.get("portfolio", [])]

    return AppConfig(
        allowlist_domains=raw.get("allowlist_domains", []),
        feeds=feeds,
        calendar_feeds=calendar_feeds,
        movers_feeds=movers_feeds,
        portfolio=portfolio,
    )


def env_var(name: str, default: str = "") -> str:
    return os.getenv(name, default)
