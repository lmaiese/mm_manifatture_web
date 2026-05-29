"""Whitelist gate and small safety helpers."""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from ..config import SETTINGS

logger = logging.getLogger("safety")


def is_allowed(chat_id: int) -> bool:
    # Empty whitelist = open mode (useful for local dev). In prod set the env var.
    if not SETTINGS.allowed_chat_ids:
        return True
    return chat_id in SETTINGS.allowed_chat_ids


async def whitelist_guard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Returns True if processing should continue. False = drop silently."""
    chat = update.effective_chat
    if chat is None:
        return False
    if is_allowed(chat.id):
        return True
    user = update.effective_user
    logger.warning(
        "blocked_unauthorized_chat",
        extra={"chat_id": chat.id, "user_id": getattr(user, "id", None)},
    )
    return False


async def notify_admin(context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    if SETTINGS.admin_chat_id is None:
        return
    try:
        await context.bot.send_message(chat_id=SETTINGS.admin_chat_id, text=text)
    except Exception as exc:  # noqa: BLE001
        logger.error("admin_notify_failed", extra={"error": str(exc)})
