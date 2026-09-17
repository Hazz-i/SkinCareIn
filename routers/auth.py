# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from core.database import get_db
from core.security import security_bearer, decode_access_token
from models.user import User
from schemas.auth import UserRegisterRequest, UserLoginRequest, TokenResponse, UserProfileResponse
from services.auth_service import AuthService
from core.logger import log_action

router = APIRouter(tags=["Authentication"])

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    db: Session = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autentikasi diperlukan. Sertakan Bearer token pada header Authorization.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    token = credentials.credentials
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token payload invalid.")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User tidak ditemukan.")
    return user

def require_role(allowed_roles: list):
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            log_action("auth", f"Unauthorized role access: user {user.email} with role {user.role} attempted {allowed_roles}", level="warning")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Akses ditolak: role tidak memadai.")
        return user
    return role_checker

@router.post("/register", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED, summary="Registrasi Pengguna Baru")
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """Mendaftarkan akun pengguna baru dengan role default `user`."""
    return AuthService.register_user(db, request)

@router.post("/login", response_model=TokenResponse, summary="Login Pengguna & Dapatkan JWT Access Token")
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """Autentikasi akun pengguna/admin menggunakan username/email dan password. Mengembalikan Bearer JWT access token."""
    return AuthService.authenticate_user(db, request)

@router.get("/me", response_model=UserProfileResponse, summary="Ambil Profil Pengguna Saat Ini")
def get_me(user: User = Depends(get_current_user)):
    """Mengambil data profil akun pengguna yang sedang login berdasarkan Bearer token pada header Authorization."""
    return user
