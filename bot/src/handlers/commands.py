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
        title = (p.get("title") or p.get("category") or "-")
        price = conv._format_price(p.get("price"))
        published_at = (p.get("_published_at") or "")[:16].replace("T", " ")
        lines.append(MESSAGES["cmd_lista_item"].format(
            title=title, price=price, when=published_at
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


async def cmd_venduto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List available products and let the user mark one as sold."""
    if not await whitelist_guard(update, context):
        return
    chat = update.effective_chat
    if chat is None:
        return
    chat_id = chat.id
    logger.info("cmd_invoked", extra={"cmd": "venduto", "chat_id": chat_id})

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from ..publisher.site import read_available_from_github
    from .conversation import CB_AVAIL_SEL_SOLD

    loading_msg = await context.bot.send_message(chat_id, MESSAGES["cmd_venduto_loading"])
    products = await read_available_from_github()

    try:
        await loading_msg.delete()
    except Exception:  # noqa: BLE001
        pass

    if not products:
        await context.bot.send_message(chat_id, MESSAGES["cmd_venduto_empty"])
        return

    rows = []
    for p in products:
        pid = p.get("id") or ""
        if not pid:
            continue
        rows.append([InlineKeyboardButton(conv._product_label(p), callback_data=f"{CB_AVAIL_SEL_SOLD}{pid}")])

    if not rows:
        await context.bot.send_message(chat_id, MESSAGES["cmd_venduto_empty"])
        return

    await context.bot.send_message(
        chat_id,
        MESSAGES["cmd_venduto_list_header"],
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def cmd_disponibile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List sold products and let the user mark one as available again."""
    if not await whitelist_guard(update, context):
        return
    chat = update.effective_chat
    if chat is None:
        return
    chat_id = chat.id
    logger.info("cmd_invoked", extra={"cmd": "disponibile", "chat_id": chat_id})

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from ..publisher.site import read_sold_from_github
    from .conversation import CB_AVAIL_SEL_AVAIL

    loading_msg = await context.bot.send_message(chat_id, MESSAGES["cmd_disponibile_loading"])
    products = await read_sold_from_github()

    try:
        await loading_msg.delete()
    except Exception:  # noqa: BLE001
        pass

    if not products:
        await context.bot.send_message(chat_id, MESSAGES["cmd_disponibile_empty"])
        return

    rows = []
    for p in products:
        pid = p.get("id") or ""
        if not pid:
            continue
        rows.append([InlineKeyboardButton(conv._product_label(p), callback_data=f"{CB_AVAIL_SEL_AVAIL}{pid}")])

    if not rows:
        await context.bot.send_message(chat_id, MESSAGES["cmd_disponibile_empty"])
        return

    await context.bot.send_message(
        chat_id,
        MESSAGES["cmd_disponibile_list_header"],
        reply_markup=InlineKeyboardMarkup(rows),
    )


async def cmd_rimuovi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await whitelist_guard(update, context):
        return
    chat = update.effective_chat
    if chat is None:
        return
    chat_id = chat.id
    logger.info("cmd_invoked", extra={"cmd": "rimuovi", "chat_id": chat_id})

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from ..publisher.site import read_published_from_github
    from .conversation import CB_REMOVE_SEL

    loading_msg = await context.bot.send_message(chat_id, MESSAGES["cmd_rimuovi_loading"])
    products = await read_published_from_github()

    try:
        await loading_msg.delete()
    except Exception:  # noqa: BLE001
        pass

    if products is None:
        await context.bot.send_message(chat_id, MESSAGES["cmd_rimuovi_error"])
        return

    if not products:
        await context.bot.send_message(chat_id, MESSAGES["cmd_rimuovi_empty"])
        return

    rows = []
    for p in products:
        pid = p.get("id") or ""
        if not pid:
            continue
        price = f"€{float(p.get('price') or 0):.2f}".replace(".", ",")
        raw_title = (p.get("title") or "").strip()
        if not raw_title:
            desc = (p.get("description_site") or "").strip()
            raw_title = (desc[:38] + "…") if len(desc) > 38 else desc
        if not raw_title:
            raw_title = p.get("category") or "?"
        label = f"{raw_title} — {price}"
        rows.append([InlineKeyboardButton(label, callback_data=f"{CB_REMOVE_SEL}{pid}")])

    if not rows:
        await context.bot.send_message(chat_id, MESSAGES["cmd_rimuovi_empty"])
        return

    await context.bot.send_message(
        chat_id,
        MESSAGES["cmd_rimuovi_list_header"],
        reply_markup=InlineKeyboardMarkup(rows),
    )
