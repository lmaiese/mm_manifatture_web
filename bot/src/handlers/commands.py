"""/nuovo, /annulla, /riprendi, /aiuto, /stato.

Handlers are thin — most logic lives in conversation.py.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from .. import db
from ..messages import MESSAGES
from . import conversation as conv
from .safety import whitelist_guard  # noqa: F401 (re-exported for tests)

logger = logging.getLogger("commands")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await whitelist_guard(update, context):
        return
    chat = update.effective_chat
    if chat is None:
        return
    logger.info("cmd_invoked", extra={"cmd": "start", "chat_id": chat.id})
    await context.bot.send_message(chat.id, MESSAGES["welcome"])


async def cmd_nuovo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await whitelist_guard(update, context):
        return
    chat = update.effective_chat
    if chat is None:
        return
    chat_id = chat.id
    logger.info("cmd_invoked", extra={"cmd": "nuovo", "chat_id": chat_id})
    if conv.has_active_flow(chat_id):
        await context.bot.send_message(chat_id, MESSAGES["cmd_already_in_progress"])
        return
    await conv.start_new_flow(chat_id, context)
    logger.info("flow_started", extra={"chat_id": chat_id})


async def cmd_annulla(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await whitelist_guard(update, context):
        return
    chat = update.effective_chat
    if chat is None:
        return
    chat_id = chat.id
    logger.info("cmd_invoked", extra={"cmd": "annulla", "chat_id": chat_id})
    if conv.has_active_flow(chat_id):
        await context.bot.send_message(
            chat_id,
            MESSAGES["cmd_cancel_confirm"],
            reply_markup=conv._cancel_confirm_keyboard(),
        )
    else:
        await conv.cancel_flow(chat_id, context)


async def cmd_riprendi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await whitelist_guard(update, context):
        return
    chat = update.effective_chat
    if chat is None:
        return
    logger.info("cmd_invoked", extra={"cmd": "riprendi", "chat_id": chat.id})
    await conv.resume_flow(chat.id, context)


async def cmd_aiuto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await whitelist_guard(update, context):
        return
    chat = update.effective_chat
    if chat is None:
        return
    logger.info("cmd_invoked", extra={"cmd": "aiuto", "chat_id": chat.id})
    await context.bot.send_message(chat.id, conv.help_for_current_step(chat.id))


async def cmd_lista(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await whitelist_guard(update, context):
        return
    chat = update.effective_chat
    if chat is None:
        return
    chat_id = chat.id
    logger.info("cmd_invoked", extra={"cmd": "lista", "chat_id": chat_id})
    products = db.recent_products(chat_id, limit=5)
    if not products:
        await context.bot.send_message(chat_id, MESSAGES["cmd_lista_empty"])
        return
    lines = [MESSAGES["cmd_lista_header"]]
    for p in products:
        cat = p.get("category") or "-"
        price = conv._format_price(p.get("price"))
        published_at = (p.get("_published_at") or "")[:16].replace("T", " ")
        lines.append(MESSAGES["cmd_lista_item"].format(
            category=cat, price=price, when=published_at
        ))
    await context.bot.send_message(chat_id, "".join(lines))


async def cmd_stato(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await whitelist_guard(update, context):
        return
    chat = update.effective_chat
    if chat is None:
        return
    logger.info("cmd_invoked", extra={"cmd": "stato", "chat_id": chat.id})
    await context.bot.send_message(chat.id, conv.status_for(chat.id))
