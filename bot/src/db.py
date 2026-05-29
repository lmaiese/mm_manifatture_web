"""SQLite persistence for conversation state and published products.

WAL mode is enabled at init so the inactivity job and the main handler loop
can read/write without blocking each other.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import SETTINGS


_SCHEMA = """
CREATE TABLE IF NOT EXISTS conversation_state (
    chat_id INTEGER PRIMARY KEY,
    state INTEGER,
    data TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS published_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    product_data TEXT,
    channels TEXT,
    published_at TEXT,
    scheduled_for TEXT
);
"""


def _connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or SETTINGS.db_path
    conn = sqlite3.connect(path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | None = None) -> None:
    conn = _connect(db_path)
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.executescript(_SCHEMA)
    finally:
        conn.close()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_state(chat_id: int, state: int, data: dict[str, Any]) -> None:
    payload = json.dumps(data, ensure_ascii=False, default=str)
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO conversation_state (chat_id, state, data, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET
                state=excluded.state,
                data=excluded.data,
                updated_at=excluded.updated_at
            """,
            (chat_id, state, payload, _now_iso()),
        )
    finally:
        conn.close()


def load_state(chat_id: int) -> tuple[int, dict[str, Any], str] | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT state, data, updated_at FROM conversation_state WHERE chat_id = ?",
            (chat_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    try:
        data = json.loads(row["data"]) if row["data"] else {}
    except json.JSONDecodeError:
        data = {}
    return row["state"], data, row["updated_at"]


def clear_state(chat_id: int) -> None:
    conn = _connect()
    try:
        conn.execute("DELETE FROM conversation_state WHERE chat_id = ?", (chat_id,))
    finally:
        conn.close()


def all_active_chats() -> list[tuple[int, str]]:
    """Returns [(chat_id, updated_at_iso), ...] for every saved conversation.

    Used by the inactivity job at startup to schedule per-chat pings.
    """
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT chat_id, updated_at FROM conversation_state"
        ).fetchall()
    finally:
        conn.close()
    return [(r["chat_id"], r["updated_at"]) for r in rows]


def save_product(
    chat_id: int,
    product: dict[str, Any],
    channels: dict[str, Any],
    scheduled_for: str | None = None,
) -> int:
    conn = _connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO published_products
                (chat_id, product_data, channels, published_at, scheduled_for)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                chat_id,
                json.dumps(product, ensure_ascii=False, default=str),
                json.dumps(channels, ensure_ascii=False),
                _now_iso(),
                scheduled_for,
            ),
        )
        return cur.lastrowid or 0
    finally:
        conn.close()
