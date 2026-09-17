# core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings
from core.logger import log_action

# Handle in-memory SQLite for testing or PostgreSQL for production
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from models.user import User
    from core.security import hash_password

    log_action("db", "Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    log_action("db", "Database tables initialization complete.")

    # Auto-seed default admin account if not exists
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.role == "admin").first()
        if not admin:
            default_admin = User(
                email=settings.ADMIN_EMAIL,
                username=settings.ADMIN_USERNAME,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                role="admin",
                is_active=True,
                is_verified=True,
                is_onboarded=True
            )
            db.add(default_admin)
            db.commit()
            log_action("auth", f"Default admin seeded successfully: {settings.ADMIN_EMAIL} (username: {settings.ADMIN_USERNAME})")
        else:
            log_action("auth", f"Admin account already exists ({admin.email}).")
    except Exception as e:
        log_action("auth", f"Notice checking default admin account: {e}", level="warning")
    finally:
        db.close()

