import pytest
from datetime import datetime
from models.user import User

def test_user_model_fields_and_defaults():
    user = User(
        email="member@example.com",
        username="member1",
        hashed_password="hashed_secret"
    )
    # Check default values
    assert user.role == "member"
    assert user.is_active is True
    assert user.is_verified is False
    assert user.is_onboarded is False
    assert user.auth_provider == "local"
    assert user.avoided_ingredients == [] or user.avoided_ingredients is None

def test_user_model_full_attributes():
    now = datetime.utcnow()
    user = User(
        email="test@example.com",
        username="tester",
        hashed_password="secret_password",
        first_name="Jane",
        last_name="Doe",
        age=25,
        gender="female",
        skin_type="sensitive",
        avoided_ingredients=["Fragrance", "Alcohol Denat"],
        role="member",
        is_active=True,
        is_verified=True,
        is_onboarded=True,
        auth_provider="local",
        verification_token="token_abc",
        verification_otp="123456",
        otp_expires_at=now
    )
    assert user.first_name == "Jane"
    assert user.last_name == "Doe"
    assert user.age == 25
    assert user.gender == "female"
    assert user.skin_type == "sensitive"
    assert user.avoided_ingredients == ["Fragrance", "Alcohol Denat"]
    assert user.verification_token == "token_abc"
    assert user.verification_otp == "123456"
    assert user.otp_expires_at == now
