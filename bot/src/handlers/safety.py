"""Whitelist gate and small safety helpers."""

import logging
import os

from telegram import Update
from telegram.ext import ContextTypes

from ..config import SETTINGS

logger = logging.getLogger("safety")

# Set DEV_OPEN_MODE=1 in .env to bypass whitelist during local development only.
_DEV_OPEN_MODE = os.environ.get("DEV_OPEN_MODE", "0") == "1"


def is_allowed(chat_id: int) -> bool:
    if _DEV_OPEN_MODE:
        logger.warning("dev_open_mode_active", extra={"chat_id": chat_id})
        return True
    if not SETTINGS.allowed_chat_ids:
        return False
    return chat_id in SETTINGS.allowed_chat_ids


async def whitelist_guard(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> bool:
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


def is_admin(chat_id: int) -> bool:
    return SETTINGS.admin_chat_id is not None and chat_id == SETTINGS.admin_chat_id


async def admin_guard(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Returns True only for the configured admin chat. Drops silently otherwise."""
    chat = update.effective_chat
    if chat is None:
        return False
    if is_admin(chat.id):
        return True
    logger.warning("blocked_non_admin", extra={"chat_id": chat.id})
    return False


async def notify_admin(context: ContextTypes.DEFAULT_TYPE, text: str) -> None:
    if SETTINGS.admin_chat_id is None:
        return
    try:
        await context.bot.send_message(chat_id=SETTINGS.admin_chat_id, text=text)
    except Exception as exc:  # noqa: BLE001
        logger.error("admin_notify_failed", extra={"error": str(exc)})
