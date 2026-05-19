import os

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Telegram
    telegram_bot_token: str = ""
    telegram_admin_id: int = 0

    # Database
    database_url: str = os.getenv("DATABASE_URL", "")
    redis_url: str = "redis://redis:6379/0"

    # AI
    openrouter_api_key: str = ""
    gemini_api_key: str = ""
    deepseek_api_key: str = ""

    # Security
    secret_key: str = os.getenv("SECRET_KEY", "")
    jwt_secret: str = os.getenv("JWT_SECRET", "")

    # Mini App
    webapp_url: str = "http://localhost:3000"
    next_public_api_url: str = "http://localhost:8000"

    # OCR
    ocr_enabled: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
