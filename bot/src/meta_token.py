"""Meta Graph API token management.

Stores long-lived tokens in SQLite, handles the 60-day refresh via the
Meta token exchange endpoint, and fires a Telegram alert to Luigi 7 days
before expiry.

Token lifecycle:
  short-lived (1h) → exchange → long-lived (60d) → store → refresh at day 53
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import aiohttp

from .config import SETTINGS

logger = logging.getLogger("meta_token")

_GRAPH_BASE = "https://graph.facebook.com/v19.0"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta_tokens (
    key TEXT PRIMARY KEY,
    token TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def _connect() -> Any:
    import sqlite3
    conn = sqlite3.connect(SETTINGS.db_path, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript(_SCHEMA)
    return conn


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


# ---------- storage ----------


def save_token(key: str, token: str, expires_at: datetime) -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO meta_tokens (key, token, expires_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                token=excluded.token,
                expires_at=excluded.expires_at,
                updated_at=excluded.updated_at
            """,
            (key, token, _iso(expires_at), _iso(_now())),
        )
        logger.info("token_saved", extra={"key": key, "expires_at": _iso(expires_at)})
    finally:
        conn.close()


def load_token(key: str) -> tuple[str, datetime] | None:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT token, expires_at FROM meta_tokens WHERE key = ?", (key,)
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    try:
        expires_at = datetime.fromisoformat(row["expires_at"])
    except ValueError:
        return None
    return row["token"], expires_at


def days_until_expiry(key: str) -> int | None:
    result = load_token(key)
    if result is None:
        return None
    _, expires_at = result
    delta = expires_at - _now()
    return max(0, delta.days)


# ---------- token exchange ----------


async def exchange_for_long_lived(
    short_lived_token: str,
    app_id: str,
    app_secret: str,
) -> tuple[str, datetime]:
    """Exchange a short-lived user token for a long-lived one (60 days)."""
    url = f"{_GRAPH_BASE}/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_lived_token,
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            data = await resp.json()
            if "error" in data:
                raise ValueError(f"Meta token exchange failed: {data['error']}")
            token = data["access_token"]
            # expires_in is in seconds; default 60 days if missing
            expires_in = int(data.get("expires_in", 60 * 24 * 3600))
            expires_at = _now() + timedelta(seconds=expires_in)
            logger.info("token_exchanged", extra={"expires_at": _iso(expires_at)})
            return token, expires_at


# ---------- expiry check (called at startup and by daily job) ----------


async def check_token_expiry(notify_fn: Any | None = None) -> None:
    """Logs a warning and optionally calls notify_fn(message) if any token expires within 7 days."""
    keys = ["instagram", "facebook"]
    for key in keys:
        days = days_until_expiry(key)
        if days is None:
            logger.warning("token_not_found", extra={"key": key})
            continue
        if days <= 7:
            msg = f"⚠️ Token Meta ({key}) scade tra {days} giorni. Rinnova il token."
            logger.warning("token_expiry_alert", extra={"key": key, "days": days})
            if notify_fn is not None:
                try:
                    await notify_fn(msg)
                except Exception as exc:
                    logger.error("token_expiry_notify_failed", extra={"key": key, "error": str(exc)})
