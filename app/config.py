import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()

    # AI Configuration
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "auto").strip().lower()
    AI_API_KEY: str = (
        os.getenv("AI_API_KEY", "")
        or os.getenv("GEMINI_API_KEY", "")
        or os.getenv("OPENAI_API_KEY", "")
    ).strip()
    AI_MODEL: str = os.getenv("AI_MODEL", "gemini-2.0-flash").strip()
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", "").strip()

    # Bot limits
    MAX_RESUMES_PER_USER: int = int(os.getenv("MAX_RESUMES_PER_USER", "5"))
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "15"))
    MAX_EXTRACTED_CHARS: int = 30000

    # Paths
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    COURSES_FILE: Path = DATA_DIR / "courses.json"
    TEMP_DIR: Path = BASE_DIR / "temp_uploads"

    @classmethod
    def has_telegram_token(cls) -> bool:
        return bool(cls.TELEGRAM_BOT_TOKEN and cls.TELEGRAM_BOT_TOKEN != "your_token_here")

    @classmethod
    def has_ai_key(cls) -> bool:
        return bool(cls.AI_API_KEY and "your_" not in cls.AI_API_KEY)


config = Config()
config.TEMP_DIR.mkdir(parents=True, exist_ok=True)
config.DATA_DIR.mkdir(parents=True, exist_ok=True)
