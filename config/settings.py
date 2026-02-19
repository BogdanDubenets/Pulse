from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    # Telegram Bot Configuration
    BOT_TOKEN: SecretStr
    
    # Telegram Client Configuration (Telethon)
    API_ID: int
    API_HASH: str
    PHONE_NUMBER: str
    
    # Database Configuration
    DATABASE_URL: str
    
    # AI Configuration
    GEMINI_API_KEY: str
    OPENAI_API_KEY: Optional[str] = None
    
    # Redis Configuration
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    
    # App Settings
    LOG_LEVEL: str = "INFO"
    DIGEST_TIME: str = "20:00"
    WEBAPP_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

config = Settings()
# Triggering re-deployment
