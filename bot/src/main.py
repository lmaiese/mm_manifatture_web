import logging
from telegram.ext import Application, CommandHandler, MessageHandler, ConversationHandler, filters, CallbackQueryHandler
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

PHOTO, PRICE, NOTES, CONFIRM = range(4)


def main():
    token = os.environ["TELEGRAM_TOKEN"]
    app = Application.builder().token(token).build()

    # TODO Sprint 1: ConversationHandler per flusso PHOTO → PRICE → NOTES → CONFIRM
    # TODO Sprint 2: AI layer (Claude Haiku) + Cloudinary upload
    # TODO Sprint 3: publisher sito (catalog.json via PyGithub + Vercel deploy hook)
    # TODO Sprint 4: publisher Meta (Instagram Graph API + Facebook Graph API)

    logger.info("Bot avviato")
    app.run_polling()


if __name__ == "__main__":
    main()
