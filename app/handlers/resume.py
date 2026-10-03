import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from app.config import config
from app.session import session_manager
from app.services.document_parser import DocumentParser, DocumentParsingError
from app.services.formatter import TelegramFormatter
from app.handlers.keyboards import resume_uploaded_keyboard

logger = logging.getLogger(__name__)


async def handle_document_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.message
    if not user or not message or not message.document:
        return

    doc = message.document
    filename = doc.file_name or "document.pdf"
    file_size_mb = (doc.file_size or 0) / (1024 * 1024)

    if file_size_mb > config.MAX_FILE_SIZE_MB:
        await message.reply_text(
            f"⚠️ <b>File too large!</b>\n\n"
            f"Your file is {file_size_mb:.1f} MB. Max allowed is {config.MAX_FILE_SIZE_MB} MB.\n"
            f"Please upload a smaller file.",
            parse_mode=ParseMode.HTML
        )
        return

    # Check extension
    valid_exts = [".pdf", ".docx", ".doc", ".txt"]
    if not any(filename.lower().endswith(ext) for ext in valid_exts):
        await message.reply_text(
            "👀 <b>I can't read that file type yet.</b>\n\n"
            "Please upload a <b>PDF</b> or <b>DOCX</b> resume.",
            parse_mode=ParseMode.HTML
        )
        return

    session = session_manager.get_session(user.id)

    # Check max resume count
    if len(session.resumes) >= config.MAX_RESUMES_PER_USER and session.jd is None:
        await message.reply_text(
            f"⚠️ <b>Maximum {config.MAX_RESUMES_PER_USER} resumes reached for this session.</b>\n\n"
            f"Tap <b>[ 💼 I'm Done ]</b> to drop the Job Description or reset to start fresh.",
            parse_mode=ParseMode.HTML,
            reply_markup=resume_uploaded_keyboard(len(session.resumes))
        )
        return

    # Inform user extraction is starting
    status_msg = await message.reply_text(
        f"📄 <i>Reading {TelegramFormatter.escape(filename)}...</i>",
        parse_mode=ParseMode.HTML
    )

    try:
        tg_file = await context.bot.get_file(doc.file_id)
        file_bytes = await tg_file.download_as_bytearray()
        extracted_text = DocumentParser.extract_from_file(filename, bytes(file_bytes))

        # Check if user already has resumes and is uploading JD as a document
        # If user explicitly had 1+ resumes and clicked "drop JD" or caption says JD
        caption = (message.caption or "").lower()
        is_jd_caption = any(k in caption for k in ["jd", "job description", "job_description", "role"])

        if session.resumes and (is_jd_caption or session.active_view == "awaiting_jd"):
            session.set_jd(extracted_text, source_type="file", filename=filename)
            await status_msg.delete()
            from app.handlers.jd import run_analysis_flow
            await run_analysis_flow(update, context, session)
            return

        # Otherwise store as Resume
        resume_doc = session.add_resume(filename=filename, text=extracted_text)
        session.active_view = "resume_uploaded"

        await status_msg.edit_text(
            text=TelegramFormatter.resume_received_message(filename, len(session.resumes)),
            parse_mode=ParseMode.HTML,
            reply_markup=resume_uploaded_keyboard(len(session.resumes))
        )
    except DocumentParsingError as de:
        logger.warning(f"Parsing error for user {user.id}: {de}")
        await status_msg.edit_text(
            f"💀 <b>Extraction failed:</b>\n\n"
            f"{str(de)}\n\n"
            f"Please try uploading a text-based PDF or paste your resume content directly.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Error handling document upload: {e}", exc_info=True)
        await status_msg.edit_text(
            "😭 <b>Something went wrong while reading your document.</b>\n\n"
            "Please try uploading again or paste text directly.",
            parse_mode=ParseMode.HTML
        )
