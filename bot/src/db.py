"""SQLite persistence for conversation state and published products.

WAL mode is enabled at init so the inactivity job and the main handler loop
can read/write without blocking each other.
"""

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import SETTINGS

logger = logging.getLogger("db")


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

CREATE TABLE IF NOT EXISTS publication_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    product_data TEXT NOT NULL,
    enqueued_at TEXT NOT NULL,
    publish_at TEXT,
    status TEXT NOT NULL DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS follower_heatmap (
    day_of_week INTEGER NOT NULL,
    hour INTEGER NOT NULL,
    score REAL NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (day_of_week, hour)
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
        logger.info("db_initialized", extra={"path": str(db_path or SETTINGS.db_path)})
    except Exception as exc:
        logger.error("db_init_failed", extra={"error": str(exc)})
        raise
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


def enqueue_product(chat_id: int, product: dict[str, Any], publish_at: str | None = None) -> int:
    conn = _connect()
    try:
        cur = conn.execute(
            """
            INSERT INTO publication_queue (chat_id, product_data, enqueued_at, publish_at, status)
            VALUES (?, ?, ?, ?, 'pending')
            """,
            (chat_id, json.dumps(product, ensure_ascii=False, default=str), _now_iso(), publish_at),
        )
        row_id = cur.lastrowid or 0
        logger.info("product_enqueued", extra={"chat_id": chat_id, "row_id": row_id, "publish_at": publish_at})
        return row_id
    finally:
        conn.close()


def pop_due_queue_items(now_iso: str) -> list[tuple[int, int, dict[str, Any]]]:
    """Return and mark as 'processing' all pending items due by now_iso.

    Returns list of (row_id, chat_id, product_data).
    """
    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT id, chat_id, product_data FROM publication_queue
            WHERE status = 'pending' AND (publish_at IS NULL OR publish_at <= ?)
            ORDER BY enqueued_at ASC
            """,
            (now_iso,),
        ).fetchall()
        if not rows:
            return []
        ids = [r["id"] for r in rows]
        conn.execute(
            f"UPDATE publication_queue SET status='processing' WHERE id IN ({','.join('?' * len(ids))})",
            ids,
        )
    finally:
        conn.close()

    result: list[tuple[int, int, dict[str, Any]]] = []
    for r in rows:
        try:
            data = json.loads(r["product_data"])
        except json.JSONDecodeError:
            data = {}
        result.append((r["id"], r["chat_id"], data))
    return result


def mark_queue_item_done(row_id: int, status: str = "published") -> None:
    conn = _connect()
    try:
        conn.execute("UPDATE publication_queue SET status=? WHERE id=?", (status, row_id))
    finally:
        conn.close()


def upsert_heatmap(day_of_week: int, hour: int, score: float) -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO follower_heatmap (day_of_week, hour, score, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(day_of_week, hour) DO UPDATE SET score=excluded.score, updated_at=excluded.updated_at
            """,
            (day_of_week, hour, score, _now_iso()),
        )
    finally:
        conn.close()


def best_upcoming_slot(after_iso: str, slots: list[int]) -> str | None:
    """Return the next slot hour (from `slots`) that maximises heatmap score.

    Falls back to the earliest slot if heatmap is empty.
    `after_iso` is an ISO datetime string; we look at the next 24h.
    """
    from datetime import datetime, timezone, timedelta
    try:
        after = datetime.fromisoformat(after_iso)
    except ValueError:
        after = datetime.now(timezone.utc)

    conn = _connect()
    try:
        rows = conn.execute("SELECT day_of_week, hour, score FROM follower_heatmap").fetchall()
    finally:
        conn.close()

    heatmap: dict[tuple[int, int], float] = {(r["day_of_week"], r["hour"]): r["score"] for r in rows}

    candidates: list[tuple[datetime, float]] = []
    for offset_hours in range(1, 25):
        candidate = after + timedelta(hours=offset_hours)
        if candidate.hour in slots:
            score = heatmap.get((candidate.weekday(), candidate.hour), 0.0)
            candidates.append((candidate, score))

    if not candidates:
        return None

    best = max(candidates, key=lambda t: (t[1], -((t[0] - after).total_seconds())))
    return best[0].isoformat()


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
        row_id = cur.lastrowid or 0
        logger.info(
            "product_saved",
            extra={"chat_id": chat_id, "row_id": row_id, "scheduled_for": scheduled_for},
        )
        return row_id
    except Exception as exc:
        logger.error("product_save_failed", extra={"chat_id": chat_id, "error": str(exc)})
        raise
    finally:
        conn.close()
