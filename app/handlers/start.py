import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from app.session import session_manager
from app.services.formatter import TelegramFormatter
from app.handlers.keyboards import welcome_keyboard

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return

    session = session_manager.reset_session(user.id)
    msg = TelegramFormatter.welcome_message()

    if update.message:
        await update.message.reply_text(
            text=msg,
            parse_mode=ParseMode.HTML,
            reply_markup=welcome_keyboard(),
            disable_web_page_preview=True
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = TelegramFormatter.how_it_works_message()
    if update.message:
        await update.message.reply_text(
            text=msg,
            parse_mode=ParseMode.HTML,
            reply_markup=welcome_keyboard(),
            disable_web_page_preview=True
        )


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user:
        return

    session_manager.reset_session(user.id)
    msg = (
        "🔄 <b>Session reset!</b>\n\n"
        "Send me your resume (PDF/DOCX) or tap below to start."
    )
    if update.message:
        await update.message.reply_text(
            text=msg,
            parse_mode=ParseMode.HTML,
            reply_markup=welcome_keyboard()
        )
