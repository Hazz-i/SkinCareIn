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

def _ensure_schema_upgrades():
    """Apply additive column migrations that `create_all` cannot handle on existing tables."""
    from sqlalchemy import inspect, text

    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    existing_columns = {column["name"] for column in inspector.get_columns("users")}
    if "date_of_birth" not in existing_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN date_of_birth DATE"))
        log_action("db", "Migrated users table: added date_of_birth column.")


def init_db():
    from models.user import User
    from core.security import hash_password

    log_action("db", "Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    _ensure_schema_upgrades()
    log_action("db", "Database tables initialization complete.")

    # Hardcoded default administrator credentials
    ADMIN_EMAIL = "admin@gmail.com"
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "password12345"

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if not admin:
            # Check if existing user with username 'admin' has a different email
            existing_user = db.query(User).filter(User.username == ADMIN_USERNAME).first()
            username_to_use = "admin_super" if existing_user else ADMIN_USERNAME

            default_admin = User(
                email=ADMIN_EMAIL,
                username=username_to_use,
                hashed_password=hash_password(ADMIN_PASSWORD),
                first_name="Admin",
                last_name="SkinSight",
                age=28,
                gender="male",
                skin_type="normal",
                avoided_ingredients=[
                    "Harsh Physical Scrubs (Walnut/Apricot)",
                    "Concentrated Sulfates"
                ],
                role="admin",
                is_active=True,
                is_verified=True,
                is_onboarded=True,
                auth_provider="local"
            )
            db.add(default_admin)
            db.commit()
            log_action("auth", f"Hardcoded default admin seeded: {ADMIN_EMAIL} (role: admin, skin_type: normal, onboarded: True)")
        else:
            # Ensure skin_type, avoided_ingredients, verification, and onboarding status are populated
            updated = False
            if not admin.skin_type:
                admin.skin_type = "normal"
                updated = True
            if not admin.avoided_ingredients:
                admin.avoided_ingredients = [
                    "Harsh Physical Scrubs (Walnut/Apricot)",
                    "Concentrated Sulfates"
                ]
                updated = True
            if not admin.is_verified:
                admin.is_verified = True
                updated = True
            if not admin.is_onboarded:
                admin.is_onboarded = True
                updated = True
            if updated:
                db.commit()
            log_action("auth", f"Admin account ready ({admin.email}, skin_type: {admin.skin_type})")
    except Exception as e:
        log_action("auth", f"Notice checking default admin account: {e}", level="warning")
    finally:
        db.close()
