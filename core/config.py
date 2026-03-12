from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    # --- CORE ---
    ENV: str = "development"
    PORT: int = 8001
    DEBUG: bool = True
    
    # --- PATHS ---
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    LOGS_DIR: str = os.path.join(BASE_DIR, "logs")

    # --- SECURITY ---
    ALLOWED_ORIGINS: List[str] = ["*"] # TODO: Restrict in Prod

    # --- LLM DEFAULTS ---
    DEFAULT_PROVIDER: str = "gemini"
    DEFAULT_MODEL: str = "gemini-2.0-flash-001"
    
    class Config:
        env_file = ".env"
        extra = "ignore" # Allow extra keys in .env

# Global Singleton
settings = Settings()

# Ensure critical dirs exist
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.LOGS_DIR, exist_ok=True)
