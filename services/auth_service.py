# services/auth_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.user import User
from schemas.auth import UserRegisterRequest, UserLoginRequest
from core.security import hash_password, verify_password, create_access_token
from core.logger import log_action

class AuthService:
    @staticmethod
    def register_user(db: Session, request: UserRegisterRequest) -> User:
        # Check existing email or username
        if db.query(User).filter(User.email == request.email).first():
            log_action("auth", f"Registration failed: email {request.email} already registered", level="warning")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered.")
        
        if db.query(User).filter(User.username == request.username).first():
            log_action("auth", f"Registration failed: username {request.username} already taken", level="warning")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is already taken.")
        
        assigned_role = "admin" if request.role == "admin" else "user"
        new_user = User(
            email=request.email,
            username=request.username,
            hashed_password=hash_password(request.password),
            role=assigned_role
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        log_action("auth", f"User registered successfully: {new_user.email} (role: {new_user.role})")
        return new_user

    @staticmethod
    def authenticate_user(db: Session, request: UserLoginRequest) -> dict:
        user = db.query(User).filter(User.email == request.email).first()
        if not user or not verify_password(request.password, user.hashed_password):
            log_action("auth", f"Invalid login credentials for email: {request.email}", level="warning")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")
        
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive.")
        
        token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role})
        log_action("auth", f"User logged in successfully: {user.email} (role: {user.role})")
        return {"access_token": token, "token_type": "bearer", "role": user.role}
