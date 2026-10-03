import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from app.config import config
from app.handlers.start import start_command, help_command, reset_command
from app.handlers.resume import handle_document_upload
from app.handlers.jd import handle_text_message
from app.handlers.callbacks import handle_callback_query

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "😭 <b>Oops! Something unexpected happened on our side.</b>\n\n"
                "Please try again or tap /start to restart the check.",
                parse_mode="HTML"
            )
        except Exception:
            pass


def create_bot_app():
    if not config.has_telegram_token():
        raise ValueError(
            "TELEGRAM_BOT_TOKEN is not set in environment or .env file! "
            "Please configure TELEGRAM_BOT_TOKEN to launch the live bot."
        )

    builder = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN)
    app = builder.build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset_command))

    # Document uploads (PDF, DOCX, TXT)
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document_upload))

    # Text messages (Pasted Job Descriptions or queries)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    # Button Callbacks
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    # Global error handler
    app.add_error_handler(error_handler)

    return app
