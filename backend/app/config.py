import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "VoiceDesk — AI-Powered Voice Receptionist"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production-super-secure-32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database (Defaults to SQLite for local standalone development/test, overridden by env for PostgreSQL)
    DATABASE_URL: str = "sqlite:////tmp/voicedesk.db" if os.environ.get("VERCEL") else "sqlite:///./voicedesk.db"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "*"
    ]

    # Voice / Vapi Integration
    VAPI_API_KEY: str = ""
    VAPI_WEBHOOK_SECRET: str = "voicedesk-vapi-webhook-secret"
    VAPI_PHONE_NUMBER_ID: str = ""
    
    # AI / LLM / RAG
    OPENAI_API_KEY: str = ""
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    
    # Organization Defaults
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"
    
    # Storage
    STORAGE_DIR: str = "/tmp/voicedesk_data" if os.environ.get("VERCEL") else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
    UPLOAD_DIR: str = "/tmp/voicedesk_uploads" if os.environ.get("VERCEL") else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
try:
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
except Exception:
    pass
