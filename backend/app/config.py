import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Load .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseModel):
    BASE_DIR: Path = BASE_DIR
    TOOL_BUDGET: int = int(os.getenv("TOOL_BUDGET", "6"))
    RESERVE_CALLS: int = int(os.getenv("RESERVE_CALLS", "1"))
    MAX_DECIDE_ROUNDS: int = int(os.getenv("MAX_DECIDE_ROUNDS", "4"))
    QUESTION_TIMEOUT_S: int = int(os.getenv("QUESTION_TIMEOUT_S", "90"))
    HISTORY_TURNS: int = int(os.getenv("HISTORY_TURNS", "3"))
    MULTI_DOC_MODE: bool = os.getenv("MULTI_DOC_MODE", "false").lower() in ("true", "1")
    STRICT_NUMERIC_VERIFY: bool = os.getenv("STRICT_NUMERIC_VERIFY", "true").lower() in ("true", "1")
    PAGE_TEXT_CHAR_CAP: int = int(os.getenv("PAGE_TEXT_CHAR_CAP", "30000"))
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "50"))
    MAX_PAGES: int = int(os.getenv("MAX_PAGES", "500"))
    
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gemini-flash-latest")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.0"))
    
    ENABLE_OCR: bool = os.getenv("ENABLE_OCR", "false").lower() in ("true", "1")
    API_TOKEN: str = os.getenv("API_TOKEN", "")
    
    DB_PATH: Path = BASE_DIR / os.getenv("DB_PATH", "data/app.db")
    UPLOADS_DIR: Path = BASE_DIR / os.getenv("UPLOADS_DIR", "data/uploads")
    TRACES_DIR: Path = BASE_DIR / os.getenv("TRACES_DIR", "traces")
    KEEP_UPLOADS: bool = os.getenv("KEEP_UPLOADS", "true").lower() in ("true", "1")

settings = Settings()
