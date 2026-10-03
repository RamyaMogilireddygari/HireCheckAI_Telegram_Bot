import asyncio
import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from app.session import session_manager, UserSession
from app.services.ai_service import AIService
from app.services.formatter import TelegramFormatter
from app.handlers.keyboards import (
    main_result_keyboard,
    battle_keyboard,
    welcome_keyboard,
    resume_uploaded_keyboard,
)

logger = logging.getLogger(__name__)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    message = update.message
    if not user or not message or not message.text:
        return

    text = message.text.strip()
    session = session_manager.get_session(user.id)

    # If no resumes uploaded yet
    if not session.resumes:
        # If user typed something like /start or hello
        if text.startswith("/"):
            return
        await message.reply_text(
            "📄 <b>I need at least one resume first!</b> 😭\n\n"
            "Drop your resume file (PDF or DOCX) below, and then we'll check the Job Description.",
            parse_mode=ParseMode.HTML,
            reply_markup=welcome_keyboard()
        )
        return

    # User has resumes -> treat text as Job Description!
    if len(text) < 30:
        await message.reply_text(
            "👀 <b>That Job Description looks a bit short!</b>\n\n"
            "Please paste a more detailed Job Description or upload the JD file so I can give you an accurate match.",
            parse_mode=ParseMode.HTML
        )
        return

    session.set_jd(text, source_type="text")
    await run_analysis_flow(update, context, session)


async def run_analysis_flow(update: Update, context: ContextTypes.DEFAULT_TYPE, session: UserSession) -> None:
    user = update.effective_user
    chat_id = update.effective_chat.id if update.effective_chat else user.id

    if not session.resumes or not session.jd:
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ <b>Missing resume or Job Description.</b> Please start again with /start.",
            parse_mode=ParseMode.HTML
        )
        return

    # Send initial loading message
    loading_msg = await context.bot.send_message(
        chat_id=chat_id,
        text="📄 <i>Reading your resume(s)...</i>",
        parse_mode=ParseMode.HTML
    )

    try:
        await asyncio.sleep(0.4)
        await loading_msg.edit_text(
            "💼 <i>Reading the Job Description...</i>",
            parse_mode=ParseMode.HTML
        )

        await asyncio.sleep(0.4)
        await loading_msg.edit_text(
            "🧠 <i>Matching skills & checking receipts...</i>",
            parse_mode=ParseMode.HTML
        )

        session.results.clear()
        total_resumes = len(session.resumes)

        # Analyze each resume
        for idx, resume in enumerate(session.resumes, 1):
            if total_resumes > 1:
                await loading_msg.edit_text(
                    f"🔎 <i>Analyzing resume {idx} of {total_resumes} (<code>{TelegramFormatter.escape(resume.filename)}</code>)...</i>",
                    parse_mode=ParseMode.HTML
                )

            analysis = await AIService.analyze_resume(
                resume_text=resume.text,
                jd_text=session.jd.text,
                resume_name=resume.filename,
                resume_id=resume.id
            )
            session.results[resume.id] = analysis

        await loading_msg.edit_text(
            "🎯 <i>Calculating final scores... Almost there 👀</i>",
            parse_mode=ParseMode.HTML
        )
        await asyncio.sleep(0.4)
        await loading_msg.delete()

        # Render outputs
        if total_resumes > 1:
            # Multi-resume Battle!
            ranked_results = sorted(session.results.values(), key=lambda x: x.score, reverse=True)
            winner = ranked_results[0]
            session.current_resume_id = winner.resume_id
            session.active_view = "battle"

            battle_text = TelegramFormatter.resume_battle(list(session.results.values()))
            await context.bot.send_message(
                chat_id=chat_id,
                text=battle_text,
                parse_mode=ParseMode.HTML,
                reply_markup=battle_keyboard(winner.resume_id)
            )
        else:
            # Single resume Main Result
            single_res = session.resumes[0]
            session.current_resume_id = single_res.id
            session.active_view = "main"
            result = session.results[single_res.id]

            main_text = TelegramFormatter.main_result(result, total_resumes=1, current_idx=1)
            await context.bot.send_message(
                chat_id=chat_id,
                text=main_text,
                parse_mode=ParseMode.HTML,
                reply_markup=main_result_keyboard(is_multi=False, current_resume_id=single_res.id, total_resumes=1),
                disable_web_page_preview=True
            )
    except Exception as e:
        logger.error(f"Error in analysis flow: {e}", exc_info=True)
        try:
            await loading_msg.edit_text(
                "😭 <b>Something went wrong while analyzing.</b>\n\n"
                "Give me a second and try again with /start.",
                parse_mode=ParseMode.HTML
            )
        except Exception:
            await context.bot.send_message(
                chat_id=chat_id,
                text="😭 <b>Something went wrong while analyzing.</b> Please try again with /start.",
                parse_mode=ParseMode.HTML
            )
