# seed_users.py
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from core.database import SessionLocal, init_db
from models.user import User

def seed_users():
    """Manual trigger to initialize tables and seed hardcoded default administrator."""
    print("=== SkinSight Database User Seeder ===")
    try:
        init_db()
    except Exception as e:
        print(f"[WARNING] init_db warning: {e}")

    db = SessionLocal()
    try:
        admin_email = "admin@gmail.com"
        user = db.query(User).filter(User.email == admin_email).first()
        if user:
            print(f"[OK] Default admin user ready:")
            print(f"  * Email               : {user.email}")
            print(f"  * Username            : {user.username}")
            print(f"  * Role                : {user.role}")
            print(f"  * Full Name           : {user.first_name} {user.last_name}")
            print(f"  * Age                 : {user.age}")
            print(f"  * Gender              : {user.gender}")
            print(f"  * Skin Type           : {user.skin_type}")
            print(f"  * Avoided Ingredients : {user.avoided_ingredients}")
            print(f"  * Is Verified         : {user.is_verified}")
            print(f"  * Is Onboarded        : {user.is_onboarded}")
            print(f"  * Auth Provider       : {user.auth_provider}")
        else:
            print(f"[NOTICE] Admin user ({admin_email}) was not found in database session.")
    except Exception as e:
        print(f"[ERROR] Database connection or verification note: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_users()
