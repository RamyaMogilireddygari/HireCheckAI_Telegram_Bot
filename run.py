import os
import sys
import logging
import asyncio
from app.config import config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("HireCheck")

BANNER = r"""
=====================================================
  __  __ _          ___ _               _      _   ___ 
 |  \/  (_)        / __| |_  ___  __   | |    /_\ |_ _|
 | |\/| | |  _    | (__| ' \/ -_)/ _|  | |__ / _ \ | | 
 |_|  |_|_| (_)    \___|_||_\___|\__|  |____/_/ \_\___|
                                                       
   "Before you hit Apply, let AI hit you with the reality check." 😭
=====================================================
"""


async def run_demo_cli():
    print(BANNER)
    print("🚀 Running HireCheck AI Demo / CLI Test Mode...\n")
    from app.handlers.callbacks import SAMPLE_RESUME_TEXT, SAMPLE_JD_TEXT
    from app.services.ai_service import AIService
    from app.services.formatter import TelegramFormatter

    print("📄 Analyzing sample candidate (Alex Chen) against AI/ML Engineer JD...\n")
    result = await AIService.analyze_resume(
        resume_text=SAMPLE_RESUME_TEXT,
        jd_text=SAMPLE_JD_TEXT,
        resume_name="Alex_Resume_ML.pdf",
        resume_id=1
    )

    print("🎯 MAIN RESULT:\n")
    print(TelegramFormatter.main_result(result))
    print("\n" + "=" * 50 + "\n")
    print("🧠 SCORE BREAKDOWN:\n")
    print(TelegramFormatter.why_score(result))
    print("\n" + "=" * 50 + "\n")
    print("🔥 RESUME ROAST:\n")
    print(TelegramFormatter.roast_message(result))
    print("\n" + "=" * 50 + "\n")
    print("🚨 BIGGEST GAP:\n")
    print(TelegramFormatter.biggest_gap_message(result))
    print("\n" + "=" * 50 + "\n")
    print("👀 RECRUITER POV:\n")
    print(TelegramFormatter.recruiter_pov_message(result))
    print("\n" + "=" * 50 + "\n")
    print("✅ Demo test completed successfully! HireCheck AI engine is working perfectly. 🔥")


def main():
    print(BANNER)

    if "--demo" in sys.argv or "--test" in sys.argv:
        asyncio.run(run_demo_cli())
        return

    if not config.has_telegram_token():
        logger.warning(
            "\n⚠️  TELEGRAM_BOT_TOKEN is not configured in .env!\n"
            "👉 Please create or edit .env and add:\n"
            "   TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather\n"
            "   AI_API_KEY=your_gemini_or_openai_api_key (optional, fallback engine active)\n\n"
            "💡 You can also test the full AI engine right now in CLI mode using:\n"
            "   python run.py --demo\n"
        )
        sys.exit(1)

    from app.bot import create_bot_app
    logger.info("Starting HireCheck AI Telegram bot...")
    app = create_bot_app()
    logger.info("Bot initialized successfully! Polling for Telegram messages...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
