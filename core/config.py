# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "SkinCareIn API"
    VERSION: str = "2.0.0"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/skinsight_db"
    
    # Security
    JWT_SECRET: str = "change_this_in_production_super_secret_key_minimum_32_characters"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours
    
    # CORS
    CORS_ORIGIN: str = "http://localhost:3000,http://localhost:8888"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGIN.split(",") if origin.strip()]

    # LLM (LiteLLM)
    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "gemini/gemini-2.5-flash"
    LLM_FALLBACKS: str = "gemini/gemini-1.5-flash"

    # Rate Limiting
    RATE_LIMIT_DEFAULT: str = "60/minute"
    RATE_LIMIT_HEAVY: str = "10/minute"

settings = Settings()
