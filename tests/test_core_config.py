# tests/test_core_config.py
import logging
import pytest
from core.config import Settings
from core.logger import format_action_log, log_action

def test_settings_default_values(tmp_path, monkeypatch):
    # Settings resolves `.env` relative to the cwd, and importing LiteLLM calls load_dotenv()
    # (which pushes .env into os.environ). Blank both sources so this asserts the real class
    # defaults instead of whatever the local machine happens to be configured with.
    monkeypatch.chdir(tmp_path)
    for key in (
        "PROJECT_NAME",
        "API_V1_PREFIX",
        "ADMIN_EMAIL",
        "ADMIN_USERNAME",
        "ADMIN_PASSWORD",
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "LLM_MODEL",
        "LLM_FALLBACKS",
        "LLM_API_BASE",
        "LLM_API_KEY",
        "GEMINI_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)

    settings = Settings(
        DATABASE_URL="postgresql://postgres:postgres@localhost:5432/skinsight_db",
        JWT_SECRET="test_secret_key_1234567890_min32chars"
    )
    assert settings.PROJECT_NAME == "SkinSight API"
    assert settings.ADMIN_EMAIL == "admin@gmail.com"
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 1440
    assert settings.LLM_MODEL == "gemini/gemini-2.5-flash"
    assert settings.LLM_API_BASE == ""

def test_cors_origins_list():
    settings = Settings(
        CORS_ORIGIN="http://localhost:3000,http://localhost:8888, "
    )
    assert settings.cors_origins_list == ["http://localhost:3000", "http://localhost:8888"]

def test_format_action_log():
    log_msg = format_action_log("scrap", "Fetching articles from Kompas")
    assert log_msg.startswith("[scrap]")
    assert "Fetching articles from Kompas" in log_msg

def test_log_action_levels(caplog):
    with caplog.at_level(logging.INFO):
        log_action("scrap", "Scraping started", level="info")
        log_action("db", "Connection warning", level="warning")
        log_action("auth", "Invalid token", level="error")
    assert "[scrap] Scraping started" in caplog.text
    assert "[db] Connection warning" in caplog.text
    assert "[auth] Invalid token" in caplog.text
