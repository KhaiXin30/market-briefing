from __future__ import annotations

import os
from typing import Iterable, Optional

import psycopg2
from psycopg2.extras import execute_values


def get_conn():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required")
    return psycopg2.connect(database_url)


def init_db(schema_path: str) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            with open(schema_path, "r", encoding="utf-8") as f:
                cur.execute(f.read())
        conn.commit()


def insert_articles(rows: Iterable[dict]) -> int:
    rows = list(rows)
    if not rows:
        return 0
    columns = [
        "title",
        "link",
        "published_at",
        "source",
        "sector",
        "summary",
    ]
    values = [[row.get(col) for col in columns] for row in rows]
    query = (
        "INSERT INTO articles (title, link, published_at, source, sector, summary) "
        "VALUES %s ON CONFLICT (link) DO NOTHING"
    )
    with get_conn() as conn:
        with conn.cursor() as cur:
            execute_values(cur, query, values)
        conn.commit()
    return len(values)


def fetch_recent_articles(since_iso: str) -> list[dict]:
    query = (
        "SELECT title, link, published_at, source, sector, summary "
        "FROM articles WHERE published_at >= %s OR published_at IS NULL "
        "ORDER BY published_at DESC NULLS LAST"
    )
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (since_iso,))
            rows = cur.fetchall()
    return [
        {
            "title": row[0],
            "link": row[1],
            "published_at": row[2],
            "source": row[3],
            "sector": row[4],
            "summary": row[5],
        }
        for row in rows
    ]


def upsert_briefing(edition_date: str, edition_type: str, content: str) -> None:
    word_count = len(content.split())
    query = (
        "INSERT INTO briefings (edition_date, edition_type, word_count, content) "
        "VALUES (%s, %s, %s, %s) "
        "ON CONFLICT (edition_date, edition_type) DO UPDATE "
        "SET word_count = EXCLUDED.word_count, content = EXCLUDED.content"
    )
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (edition_date, edition_type, word_count, content))
        conn.commit()


def get_briefing(edition_date: str, edition_type: str) -> Optional[str]:
    query = (
        "SELECT content FROM briefings WHERE edition_date = %s AND edition_type = %s"
    )
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(query, (edition_date, edition_type))
            row = cur.fetchone()
    return row[0] if row else None
