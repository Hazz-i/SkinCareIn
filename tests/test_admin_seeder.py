import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from core.database import Base
from models.user import User
from core.security import verify_password

def test_hardcoded_admin_seeder():
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    db = TestingSession()
    # Execute seeding logic
    from core.database import init_db
    import core.database
    original_engine = core.database.engine
    original_session = core.database.SessionLocal

    core.database.engine = test_engine
    core.database.SessionLocal = TestingSession
    try:
        init_db()
        admin = db.query(User).filter(User.email == "admin@gmail.com").first()
        assert admin is not None
        assert admin.username == "admin"
        assert admin.role == "admin"
        assert admin.skin_type == "normal"
        assert admin.is_verified is True
        assert admin.is_onboarded is True
        assert admin.age == 28
        assert admin.gender == "male"
        assert admin.first_name == "Admin"
        assert len(admin.avoided_ingredients) > 0
        assert verify_password("password12345", admin.hashed_password) is True
    finally:
        core.database.engine = original_engine
        core.database.SessionLocal = original_session
        db.close()
