"""Conversation flow: PHOTO -> PRICE -> SIZE -> DESCRIPTION -> WHEN -> SLOT -> CATEGORY -> PREVIEW.

State is persisted to SQLite after every step so /riprendi works across
restarts and the inactivity job can ping idle conversations.
"""

import logging
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.error import BadRequest as TgBadRequest
from telegram.ext import ContextTypes

from .. import catalog as catalog_io
from .. import db
from ..ai.caption import CaptionError, CaptionResult, generate_captions
from ..cloudinary_uploader import UploadError, upload_photos
from ..config import SETTINGS
from ..messages import HELP_BY_STEP, MESSAGES, STEP_LABELS
from ..publisher import publish
from .safety import notify_admin, whitelist_guard

logger = logging.getLogger("conversation")

# Step constants
PHOTO, PRICE, SIZE, DESCRIPTION, WHEN, SLOT, CATEGORY, PREVIEW = range(8)

INACTIVITY_JOB_PREFIX = "inactivity_ping_"
MEDIA_GROUP_FLUSH_SECONDS = 1.5  # wait for the rest of an album before acking

# Callback data tokens
CB_PHOTO_DONE = "photo_done"
CB_SKIP = "skip"
CB_WHEN_NOW = "when_now"
CB_WHEN_SLOT = "when_slot"
CB_WHEN_AUTO = "when_auto"
CB_SLOT_PREFIX = "slot:"
CB_CAT_PREFIX = "cat:"
CB_CAT_NEW = "cat_new"
CB_PREVIEW_CONFIRM = "pv_confirm"
CB_PREVIEW_EDIT = "pv_edit"
CB_PREVIEW_CANCEL = "pv_cancel"
CB_EDIT_PREFIX = "edit:"
CB_SIZE_PREFIX = "size:"
CB_CANCEL_CONFIRM  = "cancel_yes"
CB_CANCEL_ABORT    = "cancel_no"
CB_PRICE_OK        = "price_ok"
CB_PRICE_REDO      = "price_redo"
CB_PRICE_PRESET    = "price_pre:"   # prefix + int amount
CB_PRICE_CUSTOM    = "price_custom"
_PRICE_PRESETS     = [15, 25, 35, 45]
_PRICE_HIGH_THRESHOLD = 1_000.0
CB_AI_USE = "ai_use"
CB_AI_USE_MINE = "ai_use_mine"
CB_AI_FALLBACK_CONFIRM = "ai_fb_confirm"
CB_AI_FALLBACK_CANCEL = "ai_fb_cancel"


# ---------- state helpers ----------


def _empty_state() -> dict[str, Any]:
    return {
        "photos": [],          # list of local file paths
        "price": None,         # float
        "size": None,          # str | None
        "description": None,   # str | None
        "when": None,          # "now" | "auto" | "slot"
        "slot": None,          # ISO datetime string when chosen
        "category": None,      # str
        "_edit_return": False, # if True, after current step go back to PREVIEW
        "_seen_media_groups": [],
        "_bot_msg_ids": [],    # message_ids of bot messages to delete on step advance
    }


def _persist(chat_id: int, step: int, data: dict[str, Any]) -> None:
    db.save_state(chat_id, step, data)


def _format_when(data: dict[str, Any]) -> str:
    if data.get("when") == "now":
        return "Adesso"
    if data.get("when") == "auto":
        return "Automatico"
    slot = data.get("slot")
    if slot:
        try:
            dt = datetime.fromisoformat(slot)
            return _slot_label(dt)
        except ValueError:
            return slot
    return "-"


def _format_price(price: float | None) -> str:
    if price is None:
        return "-"
    return f"EUR {price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _format_preview(data: dict[str, Any]) -> str:
    return MESSAGES["step_preview"].format(
        photos_count=len(data.get("photos") or []),
        price=_format_price(data.get("price")),
        size=data.get("size") or "-",
        description=data.get("description") or "-",
        when=_format_when(data),
        category=data.get("category") or "-",
    )


# ---------- inactivity job ----------


async def _inactivity_ping(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    chat_id = job.chat_id if job else None  # type: ignore[union-attr]
    if chat_id is None:
        return
    state = db.load_state(chat_id)
    if state is None:
        return
    _, _, updated_at = state
    scheduled_at = job.data.get("scheduled_at") if job and job.data else None  # type: ignore[union-attr]
    if scheduled_at is not None and updated_at > scheduled_at:
        # A newer user interaction already re-scheduled the job; skip stale ping.
        logger.info("inactivity_ping_skipped_stale", extra={"chat_id": chat_id})
        return
    try:
        await context.bot.send_message(chat_id=chat_id, text=MESSAGES["inactivity_ping"])
        logger.info("inactivity_ping_sent", extra={"chat_id": chat_id})
    except Exception as exc:  # noqa: BLE001
        logger.error("inactivity_ping_failed", extra={"chat_id": chat_id, "error": str(exc)})
        return
    # Re-schedule so the user keeps getting nudges until they act or cancel.
    _schedule_inactivity(context, chat_id)


def _schedule_inactivity(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    jq = context.application.job_queue
    if jq is None:
        return
    name = f"{INACTIVITY_JOB_PREFIX}{chat_id}"
    for job in jq.get_jobs_by_name(name):
        job.schedule_removal()
    jq.run_once(
        _inactivity_ping,
        when=timedelta(minutes=SETTINGS.inactivity_minutes),
        chat_id=chat_id,
        name=name,
        data={"scheduled_at": time.time()},
    )


def _cancel_inactivity(context: ContextTypes.DEFAULT_TYPE, chat_id: int) -> None:
    jq = context.application.job_queue
    if jq is None:
        return
    name = f"{INACTIVITY_JOB_PREFIX}{chat_id}"
    for job in jq.get_jobs_by_name(name):
        job.schedule_removal()


async def _delete_bot_msgs(chat_id: int, data: dict[str, Any], bot) -> None:
    """Delete all tracked bot messages for this flow. Fails silently per message."""
    for mid in data.pop("_bot_msg_ids", []):
        try:
            await bot.delete_message(chat_id=chat_id, message_id=mid)
        except Exception:
            pass


# ---------- step rendering ----------


def _photo_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(MESSAGES["photo_finish_button"], callback_data=CB_PHOTO_DONE)]]
    )


def _skip_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(MESSAGES["skip_button"], callback_data=CB_SKIP)]]
    )


_SIZE_OPTIONS = ["XS", "S", "M", "L", "XL", "XXL", "Unica"]


def _size_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(s, callback_data=f"{CB_SIZE_PREFIX}{s}")
            for s in _SIZE_OPTIONS[:4]
        ],
        [
            InlineKeyboardButton(s, callback_data=f"{CB_SIZE_PREFIX}{s}")
            for s in _SIZE_OPTIONS[4:]
        ],
        [InlineKeyboardButton(MESSAGES["skip_button"], callback_data=CB_SKIP)],
    ]
    return InlineKeyboardMarkup(rows)


def _when_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(MESSAGES["when_now_button"], callback_data=CB_WHEN_NOW)],
            [InlineKeyboardButton(MESSAGES["when_slot_button"], callback_data=CB_WHEN_SLOT)],
            [InlineKeyboardButton(MESSAGES["when_auto_button"], callback_data=CB_WHEN_AUTO)],
        ]
    )


def _generate_slots(now: datetime | None = None) -> list[datetime]:
    """Today 18:00, tomorrow 10:00, 18:00, 21:00. If today 18:00 already past, drop it."""
    now = now or datetime.now()
    today_18 = now.replace(hour=18, minute=0, second=0, microsecond=0)
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    slots: list[datetime] = []
    if today_18 > now:
        slots.append(today_18)
    slots.append(tomorrow.replace(hour=10))
    slots.append(tomorrow.replace(hour=18))
    slots.append(tomorrow.replace(hour=21))
    return slots


def _slot_label(dt: datetime, ref: datetime | None = None) -> str:
    ref = ref or datetime.now()
    today = ref.date()
    if dt.date() == today:
        prefix = "Oggi"
    elif dt.date() == (today + timedelta(days=1)):
        prefix = "Domani"
    else:
        prefix = dt.strftime("%d/%m")
    return f"{prefix} {dt.strftime('%H:%M')}"


def _slot_keyboard() -> InlineKeyboardMarkup:
    rows = []
    for dt in _generate_slots():
        rows.append([InlineKeyboardButton(_slot_label(dt), callback_data=f"{CB_SLOT_PREFIX}{dt.isoformat()}")])
    return InlineKeyboardMarkup(rows)


def _category_keyboard() -> InlineKeyboardMarkup:
    cats = catalog_io.list_categories()
    rows = []
    for c in cats:
        rows.append([InlineKeyboardButton(c, callback_data=f"{CB_CAT_PREFIX}{c}")])
    rows.append([InlineKeyboardButton(MESSAGES["category_new_button"], callback_data=CB_CAT_NEW)])
    return InlineKeyboardMarkup(rows)


def _price_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(MESSAGES["price_confirm_yes"], callback_data=CB_PRICE_OK),
            InlineKeyboardButton(MESSAGES["price_confirm_no"],  callback_data=CB_PRICE_REDO),
        ]
    ])


def _price_quick_keyboard() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for p in _PRICE_PRESETS:
        row.append(InlineKeyboardButton(f"€{p}", callback_data=f"{CB_PRICE_PRESET}{p}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton("✏️ Personalizzato", callback_data=CB_PRICE_CUSTOM)])
    return InlineKeyboardMarkup(rows)


def _cancel_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(MESSAGES["cmd_cancel_yes"], callback_data=CB_CANCEL_CONFIRM),
            InlineKeyboardButton(MESSAGES["cmd_cancel_no"],  callback_data=CB_CANCEL_ABORT),
        ]
    ])


def _preview_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(MESSAGES["preview_confirm_button"], callback_data=CB_PREVIEW_CONFIRM),
                InlineKeyboardButton(MESSAGES["preview_edit_button"], callback_data=CB_PREVIEW_EDIT),
            ],
            [InlineKeyboardButton(MESSAGES["preview_cancel_button"], callback_data=CB_PREVIEW_CANCEL)],
        ]
    )


def _ai_choice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(MESSAGES["ai_use_button"], callback_data=CB_AI_USE),
                InlineKeyboardButton(MESSAGES["ai_use_mine_button"], callback_data=CB_AI_USE_MINE),
            ],
            [InlineKeyboardButton(MESSAGES["preview_cancel_button"], callback_data=CB_PREVIEW_CANCEL)],
        ]
    )


def _ai_fallback_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(MESSAGES["ai_confirm_yes"], callback_data=CB_AI_FALLBACK_CONFIRM),
                InlineKeyboardButton(MESSAGES["ai_confirm_no"], callback_data=CB_AI_FALLBACK_CANCEL),
            ]
        ]
    )


def _edit_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(MESSAGES["edit_photo_button"], callback_data=f"{CB_EDIT_PREFIX}photo"),
                InlineKeyboardButton(MESSAGES["edit_price_button"], callback_data=f"{CB_EDIT_PREFIX}price"),
            ],
            [
                InlineKeyboardButton(MESSAGES["edit_size_button"], callback_data=f"{CB_EDIT_PREFIX}size"),
                InlineKeyboardButton(MESSAGES["edit_description_button"], callback_data=f"{CB_EDIT_PREFIX}description"),
            ],
            [
                InlineKeyboardButton(MESSAGES["edit_when_button"], callback_data=f"{CB_EDIT_PREFIX}when"),
                InlineKeyboardButton(MESSAGES["edit_category_button"], callback_data=f"{CB_EDIT_PREFIX}category"),
            ],
        ]
    )


async def _send_preview(
    chat_id: int,
    data: dict[str, Any],
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Send the PREVIEW step. Attempts AI caption generation; falls back explicitly."""
    bot = context.bot

    # If captions are already cached (e.g. user re-enters PREVIEW after edit), reuse them.
    if data.get("_ai_captions"):
        captions = data["_ai_captions"]
        text = MESSAGES["step_preview_ai"].format(
            photos_count=len(data.get("photos") or []),
            price=_format_price(data.get("price")),
            size=data.get("size") or "-",
            when=_format_when(data),
            category=data.get("category") or "-",
            description=data.get("description") or "-",
            ai_site=captions["site"],
            ai_instagram=captions["instagram"],
            ai_facebook=captions["facebook"],
        )
        msg = await bot.send_message(chat_id, text, reply_markup=_ai_choice_keyboard())
        data.setdefault("_bot_msg_ids", []).append(msg.message_id)
        return

    # No cached captions — try to generate them.
    if SETTINGS.anthropic_api_key:
        thinking_msg = await bot.send_message(chat_id, MESSAGES["ai_generating"])
        try:
            result = await generate_captions(
                description=data.get("description") or "",
                price=float(data.get("price") or 0.0),
                size=data.get("size"),
                category=data.get("category") or "",
            )
            data["_ai_captions"] = {
                "site": result.site,
                "instagram": result.instagram,
                "facebook": result.facebook,
            }
            # Persist cached captions so re-entering PREVIEW skips re-generation.
            state = db.load_state(chat_id)
            if state is not None:
                _persist(chat_id, PREVIEW, data)
            try:
                await thinking_msg.delete()
            except Exception:  # noqa: BLE001
                pass
            text = MESSAGES["step_preview_ai"].format(
                photos_count=len(data.get("photos") or []),
                price=_format_price(data.get("price")),
                size=data.get("size") or "-",
                when=_format_when(data),
                category=data.get("category") or "-",
                description=data.get("description") or "-",
                ai_site=result.site,
                ai_instagram=result.instagram,
                ai_facebook=result.facebook,
            )
            msg = await bot.send_message(chat_id, text, reply_markup=_ai_choice_keyboard())
            data.setdefault("_bot_msg_ids", []).append(msg.message_id)
            return
        except CaptionError as exc:
            logger.warning("caption_error_fallback", extra={"chat_id": chat_id, "error": str(exc)})
            try:
                await thinking_msg.delete()
            except Exception:  # noqa: BLE001
                pass
            # Explicit fallback confirmation — never silent.
            msg = await bot.send_message(chat_id, MESSAGES["ai_unavailable_confirm"], reply_markup=_ai_fallback_keyboard())
            data.setdefault("_bot_msg_ids", []).append(msg.message_id)
            return

    # No API key configured: show plain preview directly.
    msg = await bot.send_message(chat_id, _format_preview(data), reply_markup=_preview_keyboard())
    data.setdefault("_bot_msg_ids", []).append(msg.message_id)


async def _ask_for_step(
    chat_id: int,
    step: int,
    context: ContextTypes.DEFAULT_TYPE,
    data: dict[str, Any] | None = None,
) -> None:
    """Send the prompt + keyboard for `step`. Tracks message_id in data for later cleanup."""
    if data is None:
        data = {}
    bot = context.bot
    msg = None
    if step == PHOTO:
        msg = await bot.send_message(chat_id, MESSAGES["step_photo_request"], reply_markup=_photo_keyboard())
    elif step == PRICE:
        msg = await bot.send_message(chat_id, MESSAGES["step_price_request"], reply_markup=_price_quick_keyboard())
    elif step == SIZE:
        msg = await bot.send_message(chat_id, MESSAGES["step_size_request"], reply_markup=_size_keyboard())
    elif step == DESCRIPTION:
        msg = await bot.send_message(chat_id, MESSAGES["step_description_request"], reply_markup=_skip_keyboard())
    elif step == WHEN:
        msg = await bot.send_message(chat_id, MESSAGES["step_when_request"], reply_markup=_when_keyboard())
    elif step == SLOT:
        msg = await bot.send_message(chat_id, MESSAGES["step_slot_request"], reply_markup=_slot_keyboard())
    elif step == CATEGORY:
        msg = await bot.send_message(chat_id, MESSAGES["step_category_request"], reply_markup=_category_keyboard())
    elif step == PREVIEW:
        await _send_preview(chat_id, data, context)
        return  # _send_preview tracks its own message
    if msg is not None:
        data.setdefault("_bot_msg_ids", []).append(msg.message_id)


# ---------- price parsing ----------

_PRICE_RE = re.compile(r"[^\d,\.]")


def _parse_price(raw: str) -> float | None:
    if not raw:
        return None
    stripped = raw.strip()
    if stripped.startswith("-"):
        return None
    cleaned = _PRICE_RE.sub("", stripped)
    if not cleaned:
        return None

    dot_count = cleaned.count(".")
    comma_count = cleaned.count(",")

    if dot_count > 0 and comma_count > 0:
        # Both present: last separator is decimal (e.g. "1.234,56" or "1,234.56")
        last_dot = cleaned.rfind(".")
        last_comma = cleaned.rfind(",")
        if last_comma > last_dot:
            # Italian style: "1.234,56" → dot=thousands, comma=decimal
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            # English style: "1,234.56" → comma=thousands, dot=decimal
            cleaned = cleaned.replace(",", "")
    elif comma_count == 1:
        # Single comma: treat as decimal separator ("12,50")
        cleaned = cleaned.replace(",", ".")
    elif dot_count == 1:
        # Single dot: decimal separator only if it looks like one (≤2 digits after it)
        dot_pos = cleaned.index(".")
        after = cleaned[dot_pos + 1:]
        if len(after) <= 2:
            pass  # already valid float string
        else:
            # 3+ digits after dot → thousands separator ("1.234" → 1234)
            cleaned = cleaned.replace(".", "")
    # Multiple dots with no comma: strip all dots (e.g. "1.234.567" → thousands only)
    elif dot_count > 1:
        cleaned = cleaned.replace(".", "")

    try:
        value = float(cleaned)
    except ValueError:
        return None
    if value < 0:
        return None
    return value


# ---------- entry helpers ----------


async def start_new_flow(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = _empty_state()
    _persist(chat_id, PHOTO, data)
    _schedule_inactivity(context, chat_id)
    await _ask_for_step(chat_id, PHOTO, context, data)
    _persist(chat_id, PHOTO, data)


# ---------- photo handling (media groups) ----------


async def _flush_media_group(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Called once per media group after MEDIA_GROUP_FLUSH_SECONDS of quiet."""
    job = context.job
    if job is None:
        return
    chat_id = job.chat_id  # type: ignore[union-attr]
    payload = job.data or {}
    group_id = payload.get("group_id")
    state = db.load_state(chat_id)
    if state is None:
        return
    step, data, _ = state
    if step != PHOTO:
        return
    count = len(data.get("photos") or [])
    if count == 0:
        return
    try:
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=MESSAGES["photo_received"].format(count=count),
            reply_markup=_photo_keyboard(),
        )
        data.setdefault("_bot_msg_ids", []).append(msg.message_id)
        _persist(chat_id, PHOTO, data)
        logger.info(
            "media_group_flushed",
            extra={"chat_id": chat_id, "group_id": group_id, "photos": count},
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("media_group_flush_failed", extra={"chat_id": chat_id, "error": str(exc)})


async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await whitelist_guard(update, context):
        return
    chat = update.effective_chat
    message = update.effective_message
    if chat is None or message is None or not message.photo:
        return
    chat_id = chat.id

    state = db.load_state(chat_id)
    _is_new_flow = state is None
    if _is_new_flow:
        # User sent a photo without /nuovo — auto-start the flow on PHOTO
        data = _empty_state()
        step = PHOTO
    else:
        step, data, _ = state
        if step != PHOTO:
            await context.bot.send_message(chat_id, MESSAGES["unexpected_input"])
            return

    # Largest photo
    photo = message.photo[-1]
    SETTINGS.photos_dir.mkdir(parents=True, exist_ok=True)
    index = len(data.get("photos") or [])
    timestamp = int(time.time() * 1000)
    file_path = SETTINGS.photos_dir / f"{chat_id}_{timestamp}_{index}.jpg"
    try:
        tg_file = await photo.get_file()
        await tg_file.download_to_drive(custom_path=str(file_path))
    except Exception as exc:  # noqa: BLE001
        logger.error("photo_download_failed", extra={"chat_id": chat_id, "error": str(exc)})
        await context.bot.send_message(chat_id, MESSAGES["internal_error"])
        return

    data.setdefault("photos", []).append(str(file_path))
    _persist(chat_id, PHOTO, data)
    _schedule_inactivity(context, chat_id)

    logger.info(
        "photo_saved",
        extra={"chat_id": chat_id, "path": str(file_path), "count": len(data["photos"])},
    )

    group_id = message.media_group_id
    jq = context.application.job_queue
    if group_id and jq is not None:
        # Collapse a whole album into one ack instead of one per photo
        seen = data.setdefault("_seen_media_groups", [])
        job_name = f"mg_flush_{chat_id}_{group_id}"
        for job in jq.get_jobs_by_name(job_name):
            job.schedule_removal()
        jq.run_once(
            _flush_media_group,
            when=MEDIA_GROUP_FLUSH_SECONDS,
            chat_id=chat_id,
            name=job_name,
            data={"group_id": group_id},
        )
        if group_id not in seen:
            seen.append(group_id)
            _persist(chat_id, PHOTO, data)
        return

    if _is_new_flow:
        await context.bot.send_message(chat_id, MESSAGES["photo_flow_autostart"])
    msg = await context.bot.send_message(
        chat_id,
        MESSAGES["photo_received"].format(count=len(data["photos"])),
        reply_markup=_photo_keyboard(),
    )
    data.setdefault("_bot_msg_ids", []).append(msg.message_id)
    _persist(chat_id, PHOTO, data)


# ---------- text router (per step) ----------


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await whitelist_guard(update, context):
        return
    chat = update.effective_chat
    message = update.effective_message
    if chat is None or message is None or message.text is None:
        return
    chat_id = chat.id
    text = message.text.strip()

    state = db.load_state(chat_id)
    if state is None:
        await context.bot.send_message(chat_id, MESSAGES["help_idle"])
        return
    step, data, _ = state
    _schedule_inactivity(context, chat_id)

    if step == PHOTO:
        await context.bot.send_message(chat_id, MESSAGES["error_not_a_photo"])
        return

    if step == PRICE:
        price = _parse_price(text)
        if price is None:
            logger.warning("price_parse_failed", extra={"chat_id": chat_id, "raw": text})
            await context.bot.send_message(chat_id, MESSAGES["error_invalid_price"])
            return
        data["price"] = price
        if price >= _PRICE_HIGH_THRESHOLD and not data.get("_price_confirmed"):
            data["_price_high_pending"] = True
            _persist(chat_id, PRICE, data)
            await context.bot.send_message(
                chat_id,
                MESSAGES["price_confirm"].format(price=_format_price(price)),
                reply_markup=_price_confirm_keyboard(),
            )
            return
        data.pop("_price_high_pending", None)
        await _advance_after(chat_id, PRICE, data, context)
        return

    if step == SIZE:
        size_val = text.strip()
        data["size"] = size_val if size_val else None
        await _advance_after(chat_id, SIZE, data, context)
        return

    if step == DESCRIPTION:
        stripped = text.strip()
        if len(stripped) > 800:
            await context.bot.send_message(chat_id, MESSAGES["error_description_long"])
            return
        if len(stripped) < 10 and not data.get("_desc_short_warned"):
            data["_desc_short_warned"] = True
            _persist(chat_id, DESCRIPTION, data)
            await context.bot.send_message(
                chat_id,
                MESSAGES["error_description_short"],
                reply_markup=_skip_keyboard(),
            )
            return
        data["description"] = stripped
        data.pop("_desc_short_warned", None)
        await _advance_after(chat_id, DESCRIPTION, data, context)
        return

    if step == CATEGORY:
        # Only reached when user is typing a NEW category name
        if not data.get("_awaiting_new_category"):
            await context.bot.send_message(chat_id, MESSAGES["unexpected_input"])
            return
        cats = catalog_io.add_category(text)
        data["_awaiting_new_category"] = False
        data["category"] = text.strip().title()
        logger.info("category_added", extra={"chat_id": chat_id, "cat_name": text, "total": len(cats)})
        msg = await context.bot.send_message(chat_id, MESSAGES["category_added"].format(name=text.strip().title()))
        data.setdefault("_bot_msg_ids", []).append(msg.message_id)
        await _advance_after(chat_id, CATEGORY, data, context)
        return

    if step in (WHEN, SLOT, PREVIEW):
        await context.bot.send_message(chat_id, MESSAGES["use_buttons"])
        return


# ---------- step transition ----------


async def _advance_after(
    chat_id: int,
    completed: int,
    data: dict[str, Any],
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Persist completed step's data, then move to next state and prompt."""
    logger.info(
        "step_completed",
        extra={
            "chat_id": chat_id,
            "step": STEP_LABELS.get(completed, str(completed)),
            "data": {
                k: v for k, v in data.items() if not k.startswith("_")
            },
        },
    )

    # If user is editing a single field, jump back to PREVIEW
    if data.get("_edit_return"):
        data["_edit_return"] = False
        # Invalidate cached AI captions if the completed step affects caption content.
        if completed in (DESCRIPTION, CATEGORY, PRICE, SIZE):
            data.pop("_ai_captions", None)
        await _delete_bot_msgs(chat_id, data, context.bot)
        _persist(chat_id, PREVIEW, data)
        await _ask_for_step(chat_id, PREVIEW, context, data)
        _persist(chat_id, PREVIEW, data)
        return

    next_step = _next_step(completed, data)
    await _delete_bot_msgs(chat_id, data, context.bot)
    _persist(chat_id, next_step, data)
    await _ask_for_step(chat_id, next_step, context, data)
    _persist(chat_id, next_step, data)


def _next_step(current: int, data: dict[str, Any]) -> int:
    if current == PHOTO:
        return PRICE
    if current == PRICE:
        return SIZE
    if current == SIZE:
        return DESCRIPTION
    if current == DESCRIPTION:
        return WHEN
    if current == WHEN:
        # If user chose slot, SLOT step handled by callback. Now/auto skip to CATEGORY.
        if data.get("when") in ("now", "auto"):
            return CATEGORY
        return SLOT
    if current == SLOT:
        return CATEGORY
    if current == CATEGORY:
        return PREVIEW
    return PREVIEW


# ---------- callback router ----------


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await whitelist_guard(update, context):
        return
    query = update.callback_query
    if query is None or query.data is None:
        return
    chat = update.effective_chat
    if chat is None:
        return
    chat_id = chat.id
    data_token = query.data
    try:
        await query.answer()
    except TgBadRequest:
        return

    state = db.load_state(chat_id)
    if state is None:
        await context.bot.send_message(chat_id, MESSAGES["help_idle"])
        return
    step, data, _ = state
    _schedule_inactivity(context, chat_id)

    # --- PRICE QUICK SELECT ---
    if data_token.startswith(CB_PRICE_PRESET):
        if step != PRICE:
            return
        try:
            price = float(data_token[len(CB_PRICE_PRESET):])
        except ValueError:
            return
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:  # noqa: BLE001
            pass
        data["price"] = price
        data.pop("_price_high_pending", None)
        data.pop("_price_confirmed", None)
        await _advance_after(chat_id, PRICE, data, context)
        return

    if data_token == CB_PRICE_CUSTOM:
        if step != PRICE:
            return
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:  # noqa: BLE001
            pass
        msg = await context.bot.send_message(chat_id, MESSAGES["price_custom_request"])
        data.setdefault("_bot_msg_ids", []).append(msg.message_id)
        _persist(chat_id, PRICE, data)
        return

    # --- PRICE HIGH CONFIRM ---
    if data_token == CB_PRICE_OK:
        if step != PRICE:
            return
        data["_price_confirmed"] = True
        data.pop("_price_high_pending", None)
        await _advance_after(chat_id, PRICE, data, context)
        return
    if data_token == CB_PRICE_REDO:
        if step != PRICE:
            return
        data.pop("price", None)
        data.pop("_price_high_pending", None)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:  # noqa: BLE001
            pass
        msg = await context.bot.send_message(chat_id, MESSAGES["step_price_request"], reply_markup=_price_quick_keyboard())
        data.setdefault("_bot_msg_ids", []).append(msg.message_id)
        _persist(chat_id, PRICE, data)
        return

    # --- CANCEL CONFIRM ---
    if data_token == CB_CANCEL_CONFIRM:
        await cancel_flow(chat_id, context)
        return
    if data_token == CB_CANCEL_ABORT:
        await context.bot.send_message(chat_id, MESSAGES["cmd_cancel_no_msg"])
        return

    # --- PHOTO ---
    if data_token == CB_PHOTO_DONE:
        if step != PHOTO:
            logger.warning("callback_ignored", extra={"chat_id": chat_id, "token": data_token, "step": step})
            return
        if not data.get("photos"):
            await context.bot.send_message(chat_id, MESSAGES["error_no_photos_yet"])
            return
        await _advance_after(chat_id, PHOTO, data, context)
        return

    # --- SKIP (used by SIZE and DESCRIPTION) ---
    if data_token == CB_SKIP:
        if step == SIZE:
            data["size"] = None
            await _advance_after(chat_id, SIZE, data, context)
            return
        if step == DESCRIPTION:
            data["description"] = None
            await _advance_after(chat_id, DESCRIPTION, data, context)
            return
        return

    # --- SIZE predefined choice ---
    if data_token.startswith(CB_SIZE_PREFIX):
        if step != SIZE:
            return
        data["size"] = data_token[len(CB_SIZE_PREFIX):]
        await _advance_after(chat_id, SIZE, data, context)
        return

    # --- WHEN ---
    if data_token in (CB_WHEN_NOW, CB_WHEN_SLOT, CB_WHEN_AUTO):
        if step != WHEN:
            return
        if data_token == CB_WHEN_NOW:
            data["when"] = "now"
            data["slot"] = None
        elif data_token == CB_WHEN_AUTO:
            data["when"] = "auto"
            data["slot"] = None
        else:
            data["when"] = "slot"
        await _advance_after(chat_id, WHEN, data, context)
        return

    # --- SLOT ---
    if data_token.startswith(CB_SLOT_PREFIX):
        if step != SLOT:
            return
        data["slot"] = data_token[len(CB_SLOT_PREFIX) :]
        await _advance_after(chat_id, SLOT, data, context)
        return

    # --- CATEGORY ---
    if data_token == CB_CAT_NEW:
        if step != CATEGORY:
            return
        data["_awaiting_new_category"] = True
        _persist(chat_id, CATEGORY, data)
        await context.bot.send_message(chat_id, MESSAGES["step_category_new_request"])
        return

    if data_token.startswith(CB_CAT_PREFIX):
        if step != CATEGORY:
            return
        data["category"] = data_token[len(CB_CAT_PREFIX) :]
        data["_awaiting_new_category"] = False
        await _advance_after(chat_id, CATEGORY, data, context)
        return

    # --- AI CHOICE ---
    if data_token == CB_AI_USE:
        if step != PREVIEW:
            return
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:  # noqa: BLE001
            pass
        await _confirm_publish(chat_id, data, context)
        return

    if data_token == CB_AI_USE_MINE:
        if step != PREVIEW:
            return
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:  # noqa: BLE001
            pass
        data.pop("_ai_captions", None)
        await _confirm_publish(chat_id, data, context)
        return

    if data_token == CB_AI_FALLBACK_CONFIRM:
        if step != PREVIEW:
            return
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:  # noqa: BLE001
            pass
        await _confirm_publish(chat_id, data, context)
        return

    if data_token == CB_AI_FALLBACK_CANCEL:
        if step != PREVIEW:
            return
        await cancel_flow(chat_id, context)
        return

    # --- PREVIEW ---
    if data_token == CB_PREVIEW_CONFIRM:
        if step != PREVIEW:
            return
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:  # noqa: BLE001
            pass
        await _confirm_publish(chat_id, data, context)
        return

    if data_token == CB_PREVIEW_EDIT:
        if step != PREVIEW:
            return
        msg = await context.bot.send_message(chat_id, MESSAGES["edit_menu"], reply_markup=_edit_menu_keyboard())
        data.setdefault("_bot_msg_ids", []).append(msg.message_id)
        _persist(chat_id, PREVIEW, data)
        return

    if data_token == CB_PREVIEW_CANCEL:
        if step != PREVIEW:
            return
        await cancel_flow(chat_id, context)
        return

    if data_token.startswith(CB_EDIT_PREFIX):
        if step != PREVIEW:
            return
        field = data_token[len(CB_EDIT_PREFIX) :]
        target = {
            "photo": PHOTO,
            "price": PRICE,
            "size": SIZE,
            "description": DESCRIPTION,
            "when": WHEN,
            "category": CATEGORY,
        }.get(field)
        if target is None:
            return
        data["_edit_return"] = True
        if target == PHOTO:
            for p in data.get("photos") or []:
                try:
                    Path(p).unlink(missing_ok=True)
                except Exception:  # noqa: BLE001
                    pass
            data["photos"] = []
            data["_seen_media_groups"] = []
        _persist(chat_id, target, data)
        await _ask_for_step(chat_id, target, context, data)
        return


# ---------- confirm / cancel ----------


async def _confirm_publish(
    chat_id: int,
    data: dict[str, Any],
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    local_paths = data.get("photos") or []
    progress_msg = await context.bot.send_message(
        chat_id,
        MESSAGES["uploading_photos"].format(done=0, total=len(local_paths)),
    )

    async def _on_progress(done: int, total: int) -> None:
        try:
            await progress_msg.edit_text(MESSAGES["uploading_photos"].format(done=done, total=total))
        except Exception:  # noqa: BLE001
            pass

    try:
        photo_urls = await upload_photos(local_paths, on_progress=_on_progress)
    except UploadError as exc:
        logger.error("upload_error", extra={"chat_id": chat_id, "error": str(exc)})
        try:
            await progress_msg.delete()
        except Exception:  # noqa: BLE001
            pass
        await context.bot.send_message(chat_id, MESSAGES["upload_failed"])
        await notify_admin(context, f"upload_failed chat={chat_id} error={exc}")
        return

    try:
        await progress_msg.edit_text(MESSAGES["publishing"])
    except Exception:  # noqa: BLE001
        pass

    # Choose description: AI site caption if accepted, otherwise user text.
    captions = data.get("_ai_captions")
    description_site = captions["site"] if captions else (data.get("description") or "")
    description_instagram = captions["instagram"] if captions else (data.get("description") or "")
    description_facebook = captions["facebook"] if captions else (data.get("description") or "")

    from datetime import datetime, timezone as _tz

    product = {
        "photos": photo_urls,
        "price": data.get("price"),
        "size": data.get("size"),
        "description_site": description_site,
        "description_instagram": description_instagram,
        "description_facebook": description_facebook,
        "when": data.get("when"),
        "slot": data.get("slot"),
        "category": data.get("category"),
    }

    when = data.get("when")

    # "Automatico": find best upcoming slot and enqueue — queue_worker handles publishing.
    if when == "auto":
        from zoneinfo import ZoneInfo
        _italy = ZoneInfo("Europe/Rome")
        now_iso = datetime.now(_tz.utc).isoformat()
        publish_at = db.best_upcoming_slot(now_iso, SETTINGS.publication_slots)
        db.enqueue_product(chat_id, product, publish_at=publish_at)
        db.clear_state(chat_id)
        _cancel_inactivity(context, chat_id)
        if publish_at:
            dt_utc = datetime.fromisoformat(publish_at).replace(tzinfo=_tz.utc)
            dt_local = dt_utc.astimezone(_italy)
            slot_label = dt_local.strftime("%d/%m alle %H:%M")
        else:
            slot_label = "prossimo slot disponibile"
        try:
            await progress_msg.delete()
        except Exception:  # noqa: BLE001
            pass
        await context.bot.send_message(
            chat_id,
            f"✅ In coda! Pubblicherò il {slot_label}.",
        )
        return

    # "Adesso" or specific slot: publish immediately.
    try:
        result = await publish(product)
    except Exception as exc:  # noqa: BLE001
        logger.error("publish_failed", extra={"chat_id": chat_id, "error": str(exc)})
        try:
            await progress_msg.delete()
        except Exception:  # noqa: BLE001
            pass
        await context.bot.send_message(chat_id, MESSAGES["internal_error"])
        await notify_admin(context, f"publish_failed chat={chat_id} error={exc}")
        return

    scheduled_for = data.get("slot") if when == "slot" else None
    db.save_product(chat_id, product, result, scheduled_for=scheduled_for)
    db.clear_state(chat_id)
    _cancel_inactivity(context, chat_id)

    def _status(ok: bool) -> str:
        return "✅" if ok else "❌"

    try:
        await progress_msg.delete()
    except Exception:  # noqa: BLE001
        pass
    await context.bot.send_message(
        chat_id,
        MESSAGES["publish_ok"].format(
            category=data.get("category") or "-",
            site_icon="🌐",
            ig_icon="📸",
            fb_icon="👥",
            site=_status(result.get("site", False)),
            instagram=_status(result.get("instagram", False)),
            facebook=_status(result.get("facebook", False)),
        ),
    )

    if not result or not all(result.values()):
        await notify_admin(
            context,
            MESSAGES["publish_partial_alert"].format(chat_id=chat_id, result=result),
        )


async def cancel_flow(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = db.load_state(chat_id)
    if state is not None:
        # Clean up half-downloaded photos to keep the dir tidy
        _, data, _ = state
        for p in data.get("photos") or []:
            try:
                Path(p).unlink(missing_ok=True)
            except Exception:  # noqa: BLE001
                pass
        await _delete_bot_msgs(chat_id, data, context.bot)
    db.clear_state(chat_id)
    _cancel_inactivity(context, chat_id)
    await context.bot.send_message(chat_id, MESSAGES["cmd_cancelled"])
    logger.info("flow_cancelled", extra={"chat_id": chat_id})


# ---------- resume / state / help ----------


async def resume_flow(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    state = db.load_state(chat_id)
    if state is None:
        await context.bot.send_message(chat_id, MESSAGES["cmd_nothing_to_resume"])
        return False
    step, data, _ = state
    _schedule_inactivity(context, chat_id)
    await context.bot.send_message(chat_id, MESSAGES["cmd_resumed"])
    await _ask_for_step(chat_id, step, context, data)
    _persist(chat_id, step, data)
    return True


def help_for_current_step(chat_id: int) -> str:
    state = db.load_state(chat_id)
    if state is None:
        return MESSAGES["help_idle"]
    step, _, _ = state
    return HELP_BY_STEP.get(step, MESSAGES["help_idle"])


def status_for(chat_id: int) -> str:
    state = db.load_state(chat_id)
    if state is None:
        return MESSAGES["cmd_state_empty"]
    step, data, _ = state
    label = STEP_LABELS.get(step, str(step))
    summary_lines = []
    summary_lines.append(f"- foto: {len(data.get('photos') or [])}")
    price = data.get("price")
    summary_lines.append(f"- prezzo: {f'EUR {price:.2f}' if price is not None else '-'}")
    summary_lines.append(f"- taglia: {data.get('size') or '-'}")
    summary_lines.append(f"- descrizione: {data.get('description') or '-'}")
    summary_lines.append(f"- quando: {_format_when(data)}")
    summary_lines.append(f"- categoria: {data.get('category') or '-'}")
    return MESSAGES["cmd_state_header"].format(step=label, data="\n".join(summary_lines))


def has_active_flow(chat_id: int) -> bool:
    return db.load_state(chat_id) is not None


# ---------- startup: reschedule inactivity for existing chats ----------


def reschedule_all_inactivity(application) -> None:
    """Called at startup so persistent state still triggers timeouts."""
    jq = application.job_queue
    if jq is None:
        return
    for chat_id, _updated_at in db.all_active_chats():
        name = f"{INACTIVITY_JOB_PREFIX}{chat_id}"
        for job in jq.get_jobs_by_name(name):
            job.schedule_removal()
        jq.run_once(
            _inactivity_ping,
            when=timedelta(minutes=SETTINGS.inactivity_minutes),
            chat_id=chat_id,
            name=name,
        )
