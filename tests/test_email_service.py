import pytest
from services.email_service import EmailService
from core.config import settings

def test_send_verification_email_fallback(caplog):
    # Ensure SMTP_HOST is empty for test to trigger mock/fallback logging
    original_host = settings.SMTP_HOST
    settings.SMTP_HOST = ""
    try:
        success = EmailService.send_verification_email(
            email="newuser@example.com",
            token="secure_token_123",
            otp="654321"
        )
        assert success is True
    finally:
        settings.SMTP_HOST = original_host

def test_build_verification_content():
    content = EmailService.build_verification_message(
        email="test@example.com",
        token="test_token_abc",
        otp="123456"
    )
    assert "123456" in content["otp"]
    assert "test_token_abc" in content["link"]
    assert "test@example.com" in content["recipient"]
