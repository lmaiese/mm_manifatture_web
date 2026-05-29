"""Telegram bot entry point.

Run with:
    python -m src.main
or, from the bot/ dir:
    python src/main.py
"""

import logging

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

# Support both `python -m src.main` and `python src/main.py`
try:
    from .config import BOT_ROOT, SETTINGS
    from .db import init_db
    from .logging_setup import setup_logging
    from .handlers import commands as cmd
    from .handlers import conversation as conv
except ImportError:  # pragma: no cover - script-mode fallback
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.config import BOT_ROOT, SETTINGS  # type: ignore[no-redef]
    from src.db import init_db  # type: ignore[no-redef]
    from src.logging_setup import setup_logging  # type: ignore[no-redef]
    from src.handlers import commands as cmd  # type: ignore[no-redef]
    from src.handlers import conversation as conv  # type: ignore[no-redef]


logger = logging.getLogger("main")


async def _post_init(app: Application) -> None:
    conv.reschedule_all_inactivity(app)
    logger.info(
        "bot_post_init",
        extra={
            "allowed_chat_ids": SETTINGS.allowed_chat_ids,
            "admin_chat_id": SETTINGS.admin_chat_id,
            "inactivity_minutes": SETTINGS.inactivity_minutes,
        },
    )


async def _post_shutdown(_app: Application) -> None:
    logger.info("bot_stopping")


def build_app() -> Application:
    setup_logging(log_dir=BOT_ROOT / "logs")
    init_db()

    if not SETTINGS.telegram_token:
        raise RuntimeError("TELEGRAM_TOKEN missing in env")

    app = (
        Application.builder()
        .token(SETTINGS.telegram_token)
        .post_init(_post_init)
        .post_shutdown(_post_shutdown)
        .build()
    )

    app.add_handler(CommandHandler("nuovo", cmd.cmd_nuovo))
    app.add_handler(CommandHandler("annulla", cmd.cmd_annulla))
    app.add_handler(CommandHandler("riprendi", cmd.cmd_riprendi))
    app.add_handler(CommandHandler("aiuto", cmd.cmd_aiuto))
    app.add_handler(CommandHandler("stato", cmd.cmd_stato))

    app.add_handler(MessageHandler(filters.PHOTO, conv.on_photo))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, conv.on_text)
    )
    app.add_handler(CallbackQueryHandler(conv.on_callback))

    return app


def main() -> None:
    app = build_app()
    logger.info("bot_starting")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
