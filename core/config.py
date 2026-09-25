# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "SkinSight API"
    VERSION: str = "2.0.0"

    # Deployment environment: "local" (development) or "production".
    # In "local" the email verification step is bypassed so you can register and sign in
    # immediately: any 6-digit OTP is accepted and an unverified account is never blocked
    # from logging in. Set this to "production" to enforce the real emailed OTP.
    APP_ENV: str = "local"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/skinsight_db"
    
    # Security
    JWT_SECRET: str = "change_this_in_production_super_secret_key_minimum_32_characters"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours
    
    # Default Admin Seed (Fallback defaults; seeder is hardcoded in core.database)
    ADMIN_EMAIL: str = "admin@gmail.com"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "password12345"

    # CORS
    CORS_ORIGIN: str = "http://localhost:3000,http://localhost:8888"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGIN.split(",") if origin.strip()]

    @property
    def is_local_env(self) -> bool:
        """True for local/dev/test runs where the email verification gate is relaxed."""
        return self.APP_ENV.strip().lower() in ("local", "development", "dev", "test")

    @property
    def email_verification_required(self) -> bool:
        """Whether a real emailed OTP must be verified before an account can log in."""
        return not self.is_local_env

    # LLM (LiteLLM)
    # Works with any OpenAI-compatible gateway (9Router, LiteLLM proxy, OpenRouter, ...).
    # Set LLM_API_BASE to that gateway's URL and prefix LLM_MODEL with `openai/`, e.g.
    #   LLM_API_BASE=http://localhost:20128/v1
    #   LLM_MODEL=openai/vertex/gemini-2.5-flash
    # Leave LLM_API_BASE empty to talk to Google Gemini directly with GEMINI_API_KEY.
    LLM_API_BASE: str = ""
    LLM_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "gemini/gemini-2.5-flash"
    LLM_FALLBACKS: str = "gemini/gemini-1.5-flash"

    # UV Index API (https://uvindexapi.com)
    UV_INDEX_API_BASE_URL: str = "https://uvindexapi.com/api/v1"
    UV_INDEX_API_TIMEOUT: int = 15
    UV_INDEX_CACHE_TTL_HOURS: int = 24

    # Rate Limiting
    RATE_LIMIT_DEFAULT: str = "60/minute"
    RATE_LIMIT_HEAVY: str = "10/minute"

    # SMTP Email Configuration
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    SMTP_FROM: str = "no-reply@skinsight.com"
    APP_BASE_URL: str = "http://localhost:8888"

settings = Settings()
