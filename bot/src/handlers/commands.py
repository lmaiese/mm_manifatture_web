"""/nuovo, /annulla, /riprendi, /aiuto, /stato.

Handlers are thin — most logic lives in conversation.py.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from ..messages import MESSAGES
from . import conversation as conv
from .safety import whitelist_guard

logger = logging.getLogger("commands")


async def cmd_nuovo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await whitelist_guard(update, context):
        return
    chat = update.effective_chat
    if chat is None:
        return
    chat_id = chat.id
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
    await conv.cancel_flow(chat.id, context)


async def cmd_riprendi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await whitelist_guard(update, context):
        return
    chat = update.effective_chat
    if chat is None:
        return
    await conv.resume_flow(chat.id, context)


async def cmd_aiuto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await whitelist_guard(update, context):
        return
    chat = update.effective_chat
    if chat is None:
        return
    await context.bot.send_message(chat.id, conv.help_for_current_step(chat.id))


async def cmd_stato(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await whitelist_guard(update, context):
        return
    chat = update.effective_chat
    if chat is None:
        return
    await context.bot.send_message(chat.id, conv.status_for(chat.id))
