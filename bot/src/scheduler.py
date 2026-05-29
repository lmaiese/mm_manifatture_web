"""Daily jobs: publication queue worker, token expiry check, optional report.

Jobs registered in main.py via app.job_queue:
  - queue_worker: runs every minute, publishes due items
  - token_check: runs once/day at 08:00, alerts if Meta tokens expire in ≤7 days
  - daily_report: runs once/day at 09:00 if DAILY_REPORT_ENABLED=1
"""

import logging
from datetime import datetime, timezone
from typing import Any

from telegram.ext import ContextTypes

from . import db
from .config import SETTINGS
from .publisher import publish

logger = logging.getLogger("scheduler")


# ---------- queue worker ----------


async def queue_worker(context: ContextTypes.DEFAULT_TYPE) -> None:
    now_iso = datetime.now(timezone.utc).isoformat()
    items = db.pop_due_queue_items(now_iso)
    if not items:
        return

    for row_id, chat_id, product in items:
        logger.info("queue_worker_processing", extra={"row_id": row_id, "chat_id": chat_id})
        try:
            result = await publish(product)
            db.mark_queue_item_done(row_id, status="published")
            db.save_product(chat_id, product, result)

            def _status(ok: bool) -> str:
                return "✅" if ok else "❌"

            await context.bot.send_message(
                chat_id,
                f"Pubblicato! 🎉\n\n"
                f"🌐 Sito: {_status(result.get('site', False))}\n"
                f"📸 Instagram: {_status(result.get('instagram', False))}\n"
                f"👥 Facebook: {_status(result.get('facebook', False))}",
            )
            logger.info("queue_item_published", extra={"row_id": row_id, "result": result})
        except Exception as exc:
            db.mark_queue_item_done(row_id, status="failed")
            logger.error("queue_item_failed", extra={"row_id": row_id, "error": str(exc)})
            if SETTINGS.admin_chat_id:
                try:
                    await context.bot.send_message(
                        SETTINGS.admin_chat_id,
                        f"⚠️ Queue item {row_id} failed: {exc}",
                    )
                except Exception:
                    pass


# ---------- token expiry check ----------


async def token_expiry_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    from .meta_token import check_token_expiry

    async def _notify(msg: str) -> None:
        if SETTINGS.admin_chat_id:
            await context.bot.send_message(SETTINGS.admin_chat_id, msg)

    await check_token_expiry(notify_fn=_notify)


# ---------- daily report ----------


async def daily_report(context: ContextTypes.DEFAULT_TYPE) -> None:
    if not SETTINGS.daily_report_enabled:
        return
    if not SETTINGS.admin_chat_id:
        return

    conn = db._connect()
    try:
        today = datetime.now(timezone.utc).date().isoformat()
        rows = conn.execute(
            "SELECT channels FROM published_products WHERE published_at >= ?",
            (today,),
        ).fetchall()
    finally:
        conn.close()

    import json
    total = len(rows)
    site_ok = ig_ok = fb_ok = 0
    for r in rows:
        try:
            ch = json.loads(r["channels"])
        except Exception:
            ch = {}
        if ch.get("site"):
            site_ok += 1
        if ch.get("instagram"):
            ig_ok += 1
        if ch.get("facebook"):
            fb_ok += 1

    msg = (
        f"📊 Report giornaliero\n\n"
        f"Prodotti pubblicati oggi: {total}\n"
        f"🌐 Sito: {site_ok}/{total}\n"
        f"📸 Instagram: {ig_ok}/{total}\n"
        f"👥 Facebook: {fb_ok}/{total}"
    )
    await context.bot.send_message(SETTINGS.admin_chat_id, msg)
    logger.info("daily_report_sent", extra={"total": total})
