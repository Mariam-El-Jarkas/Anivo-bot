import json
import os
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(os.getenv("ANIVO_DB_PATH", "data/anivo.db"))
DEFAULT_RETENTION_DAYS = 7


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS seen_posts "
        "(post_id TEXT PRIMARY KEY, seen_at REAL NOT NULL)"
    )
    connection.execute(
        "CREATE TABLE IF NOT EXISTS cache "
        "(cache_key TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at REAL NOT NULL)"
    )
    return connection


def load():
    connection = _connect()
    try:
        rows = connection.execute("SELECT post_id FROM seen_posts").fetchall()
        return {
            "initialized": bool(rows),
            "seen": [row[0] for row in rows],
        }
    finally:
        connection.close()


def save(state):
    connection = _connect()
    try:
        now = time.time()
        connection.executemany(
            "INSERT OR IGNORE INTO seen_posts(post_id, seen_at) VALUES (?, ?)",
            [(post_id, now) for post_id in state.get("seen", [])],
        )
        prune(
            days=int(os.getenv("ANIVO_RETENTION_DAYS", DEFAULT_RETENTION_DAYS)),
            connection=connection,
        )
        connection.commit()
    finally:
        connection.close()


def prune(days=DEFAULT_RETENTION_DAYS, connection=None):
    close_connection = connection is None
    connection = connection or _connect()
    try:
        cutoff = time.time() - max(1, days) * 24 * 60 * 60
        connection.execute("DELETE FROM seen_posts WHERE seen_at < ?", (cutoff,))
        connection.commit()
    finally:
        if close_connection:
            connection.close()


def get_cache(cache_key):
    connection = _connect()
    try:
        row = connection.execute(
            "SELECT payload FROM cache WHERE cache_key = ?", (cache_key,)
        ).fetchone()
        return json.loads(row[0]) if row else None
    finally:
        connection.close()


def set_cache(cache_key, payload):
    connection = _connect()
    try:
        connection.execute(
            "INSERT OR REPLACE INTO cache(cache_key, payload, updated_at) "
            "VALUES (?, ?, ?)",
            (cache_key, json.dumps(payload, ensure_ascii=False), time.time()),
        )
        connection.commit()
    finally:
        connection.close()
