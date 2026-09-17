# SkinCareIn Architecture Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform SkinCareIn into a modular, production-ready FastAPI backend featuring PostgreSQL, JWT Role-Based Access Control (`admin`/`user`), LiteLLM integration for vision/OCR, two-tier DB caching for news/education (daily 24h sync for lists, 1-time lazy cache for details), SlowAPI rate limiting, tagged action logging, and Nginx load balancing over `/api/v1/` routes.

**Architecture:** Clean Modular Architecture dividing the codebase into `core/` (config, database, security, limiter, logger), `models/` (SQLAlchemy ORM), `schemas/` (Pydantic), `services/` (business logic), `routers/` (FastAPI v1 endpoints mounted under `/api/v1`), `scheduler/` (APScheduler), and `nginx/` (Reverse Proxy Load Balancer).

**Tech Stack:** FastAPI, Uvicorn, PostgreSQL 16, SQLAlchemy 2.0, psycopg2-binary, LiteLLM, APScheduler, SlowAPI, PyJWT, passlib[bcrypt], PyTorch, OpenCV, BeautifulSoup4, Requests, Docker & Nginx.

**Spec:** [`docs/superpowers/specs/2026-09-17-skincarein-architecture-improvements-design.md`](file:///D:/my-projects/SkinCareIn/docs/superpowers/specs/2026-09-17-skincarein-architecture-improvements-design.md)

## Global Constraints
- All public endpoints must be mounted under the `/api/v1/` prefix.
- All actions must output structured tagged logs with format `[TAG] YYYY-MM-DD HH:MM:SS - message` where tag is one of: `[auth]`, `[scrap]`, `[cache]`, `[db]`, `[llm]`, `[ratelimit]`, `[schedule]`, `[api]`.
- List articles and educations must update once per 24 hours in the background and serve instantly from PostgreSQL.
- Article and education details must use lazy caching: scraped once on first access and cached permanently in PostgreSQL without re-scraping on subsequent requests.
- Passwords must be hashed using bcrypt; authentication uses JWT bearer tokens with role verification (`admin` vs `user`).
- LLM invocations must use `litellm.acompletion` with model fallback capability.

---

### Task 1: Core Configuration, Dependencies & Tagged Action Logger

**Files:**
- Modify: `requirements.txt`
- Create: `core/__init__.py`
- Create: `core/config.py`
- Create: `core/logger.py`
- Modify: `.env.example`
- Test: `tests/test_core_config.py`

**Interfaces:**
- Consumes: Environment variables (`DATABASE_URL`, `JWT_SECRET`, `LLM_MODEL`, etc.)
- Produces:
  - `core.config.settings`: Pydantic `Settings` instance
  - `core.logger.log_action(tag: str, message: str, level: str = "info") -> None`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_core_config.py
import pytest
from core.config import Settings
from core.logger import format_action_log

def test_settings_default_values():
    settings = Settings(
        DATABASE_URL="postgresql://postgres:postgres@localhost:5432/skincare_db",
        JWT_SECRET="test_secret_key_1234567890_min32chars"
    )
    assert settings.API_V1_PREFIX == "/api/v1"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 1440
    assert settings.LLM_MODEL == "gemini/gemini-2.5-flash"

def test_format_action_log():
    log_msg = format_action_log("scrap", "Fetching articles from Kompas")
    assert log_msg.startswith("[scrap]")
    assert "Fetching articles from Kompas" in log_msg
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_core_config.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'core'`

- [ ] **Step 3: Update requirements and implement config & logger**

Add to `requirements.txt`:
```txt
pydantic-settings>=2.2.0
psycopg2-binary>=2.9.9
litellm>=1.40.0
apscheduler>=3.10.4
slowapi>=0.1.9
passlib[bcrypt]>=1.7.4
pyjwt>=2.8.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.27.0
```

Write `core/__init__.py`:
```python
# core/__init__.py
```

Write `core/config.py`:
```python
# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "SkinCareIn API"
    VERSION: str = "2.0.0"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/skinsight_db"
    
    # Security
    JWT_SECRET: str = "change_this_in_production_super_secret_key_minimum_32_characters"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours
    
    # CORS
    CORS_ORIGIN: str = "http://localhost:3000,http://localhost:8888"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGIN.split(",") if origin.strip()]

    # LLM (LiteLLM)
    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "gemini/gemini-2.5-flash"
    LLM_FALLBACKS: str = "gemini/gemini-1.5-flash"

    # Rate Limiting
    RATE_LIMIT_DEFAULT: str = "60/minute"
    RATE_LIMIT_HEAVY: str = "10/minute"

settings = Settings()
```

Write `core/logger.py`:
```python
# core/logger.py
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("skincarein")

def format_action_log(tag: str, message: str) -> str:
    clean_tag = tag.strip("[]").lower()
    return f"[{clean_tag}] {message}"

def log_action(tag: str, message: str, level: str = "info") -> None:
    formatted = format_action_log(tag, message)
    if level == "error":
        logger.error(formatted)
    elif level == "warning":
        logger.warning(formatted)
    else:
        logger.info(formatted)
```

Update `.env.example`:
```env
# Database Configuration (PostgreSQL)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/skinsight_db

# Security
JWT_SECRET=your_super_secret_jwt_key_here_minimum_32_characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# CORS
CORS_ORIGIN=http://localhost:3000,http://localhost:8888

# LiteLLM & Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini/gemini-2.5-flash
LLM_FALLBACKS=gemini/gemini-1.5-flash
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_core_config.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add requirements.txt core/ tests/test_core_config.py .env.example
git commit -m "feat(core): add configuration, dependencies, and tagged action logger"
```

---

### Task 2: PostgreSQL Database Engine & Base ORM Models

**Files:**
- Create: `core/database.py`
- Create: `models/__init__.py`
- Create: `models/user.py`
- Create: `models/product.py`
- Create: `models/article.py`
- Create: `models/education.py`
- Test: `tests/test_database_models.py`

**Interfaces:**
- Consumes: `core.config.settings.DATABASE_URL`
- Produces:
  - `core.database.Base`, `core.database.engine`, `core.database.SessionLocal`, `core.database.get_db`
  - ORM Models: `User`, `Product`, `NewsArticle`, `NewsArticleDetail`, `EducationArticle`, `EducationArticleDetail`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_database_models.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base
from models.user import User
from models.article import NewsArticle, NewsArticleDetail
from models.education import EducationArticle, EducationArticleDetail
from models.product import Product

# Use SQLite in-memory for testing ORM definitions
TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)

def test_create_user_model(db_session):
    user = User(username="testuser", email="test@example.com", hashed_password="pw", role="user")
    db_session.add(user)
    db_session.commit()
    assert user.id is not None
    assert user.role == "user"

def test_create_article_and_detail_cache_models(db_session):
    article = NewsArticle(title="News 1", link="https://kompas.com/news1", page_number=1)
    detail = NewsArticleDetail(article_link="https://kompas.com/news1", title="News 1", content_markdown="Full content")
    db_session.add_all([article, detail])
    db_session.commit()
    assert article.id is not None
    assert detail.id is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_database_models.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'models'`

- [ ] **Step 3: Implement database connection and ORM models**

Write `core/database.py`:
```python
# core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings
from core.logger import log_action

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    log_action("db", "Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    log_action("db", "Database tables initialization complete.")
```

Write `models/user.py`:
```python
# models/user.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False) # 'admin' or 'user'
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

Write `models/product.py`:
```python
# models/product.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from core.database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    price = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(Text, nullable=True)
    link = Column(Text, nullable=True)
    ingredients = Column(Text, nullable=True)
    type = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

Write `models/article.py`:
```python
# models/article.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from core.database import Base

class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    link = Column(String(1000), unique=True, index=True, nullable=False)
    image_url = Column(Text, nullable=True)
    date = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)
    page_number = Column(Integer, default=1, nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class NewsArticleDetail(Base):
    __tablename__ = "news_article_details"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    article_link = Column(String(1000), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    cover_image = Column(Text, nullable=True)
    date = Column(String(100), nullable=True)
    source = Column(String(100), nullable=True)
    author = Column(String(150), nullable=True)
    content_markdown = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

Write `models/education.py`:
```python
# models/education.py
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from core.database import Base

class EducationArticle(Base):
    __tablename__ = "education_articles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    link = Column(String(1000), unique=True, index=True, nullable=False)
    image_url = Column(Text, nullable=True)
    snippet = Column(Text, nullable=True)
    date = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)
    page_number = Column(Integer, default=1, nullable=False)
    fetched_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class EducationArticleDetail(Base):
    __tablename__ = "education_article_details"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    article_link = Column(String(1000), unique=True, index=True, nullable=False)
    title = Column(String(500), nullable=False)
    author = Column(String(150), nullable=True)
    date = Column(String(100), nullable=True)
    cover_image = Column(Text, nullable=True)
    content_markdown = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

Write `models/__init__.py`:
```python
# models/__init__.py
from models.user import User
from models.product import Product
from models.article import NewsArticle, NewsArticleDetail
from models.education import EducationArticle, EducationArticleDetail

__all__ = [
    "User",
    "Product",
    "NewsArticle",
    "NewsArticleDetail",
    "EducationArticle",
    "EducationArticleDetail"
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_database_models.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/database.py models/ tests/test_database_models.py
git commit -m "feat(database): configure PostgreSQL engine and define ORM models"
```

---

### Task 3: Security, JWT & Role-Based Authentication Router

**Files:**
- Create: `core/security.py`
- Create: `schemas/auth.py`
- Create: `services/auth_service.py`
- Create: `routers/auth.py`
- Test: `tests/test_auth.py`

**Interfaces:**
- Consumes: `core.database.get_db`, `models.user.User`, `core.config.settings`
- Produces:
  - Endpoints: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/me`
  - Dependencies: `get_current_user`, `require_role(["admin"])`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_auth.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base, get_db
from routers.auth import router as auth_router

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()
app.include_router(auth_router, prefix="/api/v1/auth")

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_register_and_login_flow():
    # 1. Register user
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": "user@example.com",
        "username": "user1",
        "password": "password123",
        "role": "user"
    })
    assert reg_resp.status_code == 201
    data = reg_resp.json()
    assert data["email"] == "user@example.com"
    assert data["role"] == "user"

    # 2. Login
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "user@example.com",
        "password": "password123"
    })
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 3. Get profile (/me)
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "user1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_auth.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'routers.auth'`

- [ ] **Step 3: Implement security, schemas, service, and router**

Write `core/security.py`:
```python
# core/security.py
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security_bearer = HTTPBearer()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token tidak valid atau telah kedaluwarsa.",
            headers={"WWW-Authenticate": "Bearer"}
        )
```

Write `schemas/auth.py`:
```python
# schemas/auth.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserRegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    role: Optional[str] = "user" # 'admin' or 'user'

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str

class UserProfileResponse(BaseModel):
    id: int
    email: str
    username: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
```

Write `services/auth_service.py`:
```python
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
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email sudah terdaftar.")
        
        if db.query(User).filter(User.username == request.username).first():
            log_action("auth", f"Registration failed: username {request.username} already taken", level="warning")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username sudah digunakan.")
        
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
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email atau password salah.")
        
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Akun tidak aktif.")
        
        token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role})
        log_action("auth", f"User logged in successfully: {user.email} (role: {user.role})")
        return {"access_token": token, "token_type": "bearer", "role": user.role}
```

Write `routers/auth.py`:
```python
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

@router.post("/register", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    return AuthService.register_user(db, request)

@router.post("/login", response_model=TokenResponse)
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    return AuthService.authenticate_user(db, request)

@router.get("/me", response_model=UserProfileResponse)
def get_me(user: User = Depends(get_current_user)):
    return user
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_auth.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/security.py schemas/auth.py services/auth_service.py routers/auth.py tests/test_auth.py
git commit -m "feat(auth): implement JWT authentication, user registration, and RBAC"
```

---

### Task 4: LiteLLM Vision Service for Skincare OCR

**Files:**
- Create: `services/llm_service.py`
- Test: `tests/test_llm_service.py`

**Interfaces:**
- Consumes: `core.config.settings.LLM_MODEL`, `core.config.settings.GEMINI_API_KEY`
- Produces: `LLMService.extract_ingredients_from_image(base64_image: str) -> str`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_llm_service.py
import pytest
from unittest.mock import AsyncMock, patch
from services.llm_service import LLMService

@pytest.mark.asyncio
async def test_llm_service_extract_ingredients():
    llm_service = LLMService()
    fake_response = AsyncMock()
    fake_choice = AsyncMock()
    fake_choice.message.content = "Water, Glycerin, Niacinamide, Centella Asiatica"
    fake_response.choices = [fake_choice]

    with patch("litellm.acompletion", new=AsyncMock(return_value=fake_response)):
        result = await llm_service.extract_ingredients_from_image("fake_base64_string")
        assert "Niacinamide" in result
        assert "Centella Asiatica" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm_service.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'services.llm_service'`

- [ ] **Step 3: Implement LLMService**

Write `services/llm_service.py`:
```python
# services/llm_service.py
import os
import litellm
from core.config import settings
from core.logger import log_action

class LLMService:
    def __init__(self):
        self.model = settings.LLM_MODEL
        self.fallbacks = [m.strip() for m in settings.LLM_FALLBACKS.split(",") if m.strip()]
        litellm.drop_params = True

    async def extract_ingredients_from_image(self, base64_image: str) -> str:
        prompt = (
            "cari ingredients/bahan/komposisi dalam gambar ini dan berikan hasilnya dalam format teks biasa "
            "tanpa markdown atau formatting lainnya. buang teks yang tidak relevan seperti nama brand, nama produk, "
            "atau informasi lain yang tidak berkaitan dengan bahan, serta jika tidak terdapat ingredients sama sekali, "
            "tampilkan ingredients not found."
        )
        log_action("llm", f"Sending vision OCR prompt via LiteLLM with model: {self.model}")
        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }],
                fallbacks=self.fallbacks,
                api_key=settings.GEMINI_API_KEY
            )
            extracted_text = response.choices[0].message.content
            log_action("llm", f"LiteLLM extraction completed ({len(extracted_text)} chars)")
            return extracted_text.strip()
        except Exception as e:
            log_action("llm", f"LiteLLM invocation failed: {str(e)}", level="error")
            raise RuntimeError(f"Gagal memproses gambar dengan AI: {str(e)}")

llm_service = LLMService()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm_service.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add services/llm_service.py tests/test_llm_service.py
git commit -m "feat(llm): implement unified LiteLLM vision service with fallback"
```

---

### Task 5: News Scraping with 24h List Caching & 1x Lazy Detail Caching

**Files:**
- Create: `schemas/news.py`
- Create: `services/news_service.py`
- Create: `routers/news.py`
- Test: `tests/test_news_service.py`

**Interfaces:**
- Consumes: `models.article.NewsArticle`, `models.article.NewsArticleDetail`, `helper.news.get_news`, `helper.news.get_news_list`
- Produces:
  - Endpoints: `GET /api/v1/news`, `POST /api/v1/news/detail`
  - Methods: `NewsService.get_cached_news_list`, `NewsService.get_or_scrape_news_detail`, `NewsService.sync_news_from_source`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_news_service.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base
from models.article import NewsArticle, NewsArticleDetail
from services.news_service import NewsService
from unittest.mock import patch

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_lazy_cache_news_detail(db):
    test_link = "https://www.kompas.com/skincare-article-1"
    
    # 1. First access (cache MISS) -> triggers scrape and saves to DB
    fake_scraped = [{
        "Title": "Scraped Title",
        "Cover_Image": "https://img.com/pic.jpg",
        "Date": "2026-09-17",
        "Source": "Kompas",
        "Author": "Editor",
        "Content": "Scraped article body text"
    }]
    with patch("helper.news.get_news", return_value=fake_scraped):
        detail = NewsService.get_or_scrape_news_detail(db, test_link)
        assert detail.title == "Scraped Title"
        assert db.query(NewsArticleDetail).filter_by(article_link=test_link).count() == 1

    # 2. Second access (cache HIT) -> loads from DB without calling scraper
    with patch("helper.news.get_news", side_effect=Exception("Should not be called")):
        cached_detail = NewsService.get_or_scrape_news_detail(db, test_link)
        assert cached_detail.title == "Scraped Title"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_news_service.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'schemas.news'`

- [ ] **Step 3: Implement schemas, news service and router**

Write `schemas/news.py`:
```python
# schemas/news.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class NewsItemSchema(BaseModel):
    id: Optional[int] = None
    title: str
    link: str
    image_url: Optional[str] = None
    date: Optional[str] = None
    category: Optional[str] = None

    class Config:
        from_attributes = True

class NewsListResponse(BaseModel):
    articles: List[NewsItemSchema]
    total: int
    page: int

class NewsDetailRequest(BaseModel):
    article_link: str = Field(..., description="URL berita kompas yang ingin dibuka")

class NewsDetailResponse(BaseModel):
    title: str
    cover_image: Optional[str] = None
    date: Optional[str] = None
    source: Optional[str] = None
    author: Optional[str] = None
    content_markdown: str

    class Config:
        from_attributes = True
```

Write `services/news_service.py`:
```python
# services/news_service.py
from datetime import datetime
from sqlalchemy.orm import Session
from models.article import NewsArticle, NewsArticleDetail
from helper.news import get_news_list, get_news
from core.logger import log_action
from fastapi import HTTPException

class NewsService:
    @staticmethod
    def sync_news_from_source(db: Session, max_pages: int = 3) -> int:
        log_action("scrap", f"Starting background sync of news list (pages 1 to {max_pages})...")
        synced_count = 0
        for page in range(1, max_pages + 1):
            scraped_data = get_news_list(page=page)
            articles = scraped_data.get("Article_List", [])
            for item in articles:
                link = item.get("Link")
                if not link:
                    continue
                existing = db.query(NewsArticle).filter(NewsArticle.link == link).first()
                if existing:
                    existing.title = item.get("Title", existing.title)
                    existing.image_url = item.get("Image", existing.image_url)
                    existing.date = item.get("Date", existing.date)
                    existing.category = item.get("Category", existing.category)
                    existing.fetched_at = datetime.utcnow()
                else:
                    new_art = NewsArticle(
                        title=item.get("Title", ""),
                        link=link,
                        image_url=item.get("Image", ""),
                        date=item.get("Date", ""),
                        category=item.get("Category", ""),
                        page_number=page,
                        fetched_at=datetime.utcnow()
                    )
                    db.add(new_art)
                    synced_count += 1
            db.commit()
        log_action("db", f"Synchronized news articles cache. Added {synced_count} new records.")
        return synced_count

    @staticmethod
    def get_cached_news_list(db: Session, page: int = 1, page_size: int = 15) -> dict:
        total = db.query(NewsArticle).count()
        # If DB is empty, trigger an initial sync
        if total == 0:
            NewsService.sync_news_from_source(db, max_pages=2)
            total = db.query(NewsArticle).count()

        offset = (page - 1) * page_size
        articles = db.query(NewsArticle).order_by(NewsArticle.fetched_at.desc()).offset(offset).limit(page_size).all()
        log_action("db", f"Returned {len(articles)} cached news articles for page {page}")
        return {"articles": articles, "total": total, "page": page}

    @staticmethod
    def get_or_scrape_news_detail(db: Session, article_link: str) -> NewsArticleDetail:
        # Check cache
        cached = db.query(NewsArticleDetail).filter(NewsArticleDetail.article_link == article_link).first()
        if cached:
            log_action("cache", f"Cache HIT for news detail: {article_link}")
            return cached

        # Cache MISS -> scrape once
        log_action("cache", f"Cache MISS for news detail: {article_link} -> scraping from source...")
        scraped = get_news(article_link)
        if not scraped:
            log_action("scrap", f"Article detail not found on source: {article_link}", level="error")
            raise HTTPException(status_code=404, detail="Detail berita tidak ditemukan.")

        item = scraped[0]
        new_detail = NewsArticleDetail(
            article_link=article_link,
            title=item.get("Title", ""),
            cover_image=item.get("Cover_Image") or item.get("ImageUrl") or "",
            date=item.get("Date", ""),
            source=item.get("Source", "Kompas.com"),
            author=item.get("Author", ""),
            content_markdown=item.get("Content", "")
        )
        db.add(new_detail)
        db.commit()
        db.refresh(new_detail)
        log_action("db", f"Saved new article detail permanently to DB for link: {article_link}")
        return new_detail
```

Write `routers/news.py`:
```python
# routers/news.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db
from schemas.news import NewsListResponse, NewsDetailRequest, NewsDetailResponse
from services.news_service import NewsService

router = APIRouter(tags=["Skincare News"])

@router.get("", response_model=NewsListResponse)
def get_news(page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    """Mengambil daftar berita skincare (disajikan cepat dari cache PostgreSQL)"""
    return NewsService.get_cached_news_list(db, page=page)

@router.post("/detail", response_model=NewsDetailResponse)
def get_news_detail(request: NewsDetailRequest, db: Session = Depends(get_db)):
    """Mengambil detail berita (Lazy Cache: scrape 1x saat pertama kali diakses)"""
    return NewsService.get_or_scrape_news_detail(db, request.article_link)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_news_service.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add schemas/news.py services/news_service.py routers/news.py tests/test_news_service.py
git commit -m "feat(news): implement 24h list caching and 1x lazy detail caching for news"
```

---

### Task 6: Education Scraping with 24h List Caching & 1x Lazy Detail Caching

**Files:**
- Create: `schemas/education.py`
- Create: `services/education_service.py`
- Create: `routers/educations.py`
- Test: `tests/test_education_service.py`

**Interfaces:**
- Consumes: `models.education.EducationArticle`, `models.education.EducationArticleDetail`, `helper.educations.get_educations_details`, `helper.educations.get_educations_list`
- Produces:
  - Endpoints: `GET /api/v1/educations`, `POST /api/v1/educations/detail`
  - Methods: `EducationService.get_cached_educations_list`, `EducationService.get_or_scrape_education_detail`, `EducationService.sync_educations_from_source`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_education_service.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database import Base
from models.education import EducationArticle, EducationArticleDetail
from services.education_service import EducationService
from unittest.mock import patch

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

def test_lazy_cache_education_detail(db):
    test_link = "https://www.eduskincare.eu.org/edu-1"
    fake_scraped = {
        "Title": "Edu Title",
        "Author": "Doctor",
        "Date": "2026-09-17",
        "Cover_Image": "https://img.com/edu.jpg",
        "Content": "Edu article body content"
    }
    with patch("helper.educations.get_educations_details", return_value=fake_scraped):
        detail = EducationService.get_or_scrape_education_detail(db, test_link)
        assert detail.title == "Edu Title"
        assert db.query(EducationArticleDetail).filter_by(article_link=test_link).count() == 1

    # Second request hits cache
    with patch("helper.educations.get_educations_details", side_effect=Exception("Should not be called")):
        cached = EducationService.get_or_scrape_education_detail(db, test_link)
        assert cached.title == "Edu Title"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_education_service.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'schemas.education'`

- [ ] **Step 3: Implement schemas, education service, and router**

Write `schemas/education.py`:
```python
# schemas/education.py
from pydantic import BaseModel, Field
from typing import List, Optional

class EducationItemSchema(BaseModel):
    id: Optional[int] = None
    title: str
    link: str
    image_url: Optional[str] = None
    snippet: Optional[str] = None
    date: Optional[str] = None
    category: Optional[str] = None

    class Config:
        from_attributes = True

class EducationListResponse(BaseModel):
    educations: List[EducationItemSchema]
    total: int
    page: int

class EducationDetailRequest(BaseModel):
    article_link: str = Field(..., description="URL artikel edukasi yang ingin dibuka")

class EducationDetailResponse(BaseModel):
    title: str
    author: Optional[str] = None
    date: Optional[str] = None
    cover_image: Optional[str] = None
    content_markdown: str

    class Config:
        from_attributes = True
```

Write `services/education_service.py`:
```python
# services/education_service.py
from datetime import datetime
from sqlalchemy.orm import Session
from models.education import EducationArticle, EducationArticleDetail
from helper.educations import get_educations_list, get_educations_details
from core.logger import log_action
from fastapi import HTTPException

class EducationService:
    @staticmethod
    def sync_educations_from_source(db: Session, max_pages: int = 2) -> int:
        log_action("scrap", f"Starting background sync of education topics (pages 1 to {max_pages})...")
        synced_count = 0
        for page in range(1, max_pages + 1):
            scraped_data, _ = get_educations_list(page_number=page)
            for item in scraped_data:
                link = item.get("Link")
                if not link:
                    continue
                existing = db.query(EducationArticle).filter(EducationArticle.link == link).first()
                if existing:
                    existing.title = item.get("Title", existing.title)
                    existing.image_url = item.get("Image", existing.image_url)
                    existing.snippet = item.get("Snippet", existing.snippet)
                    existing.date = str(item.get("Date", existing.date))
                    existing.category = item.get("Category", existing.category)
                    existing.fetched_at = datetime.utcnow()
                else:
                    new_edu = EducationArticle(
                        title=item.get("Title", ""),
                        link=link,
                        image_url=item.get("Image", ""),
                        snippet=item.get("Snippet", ""),
                        date=str(item.get("Date", "")),
                        category=item.get("Category", ""),
                        page_number=page,
                        fetched_at=datetime.utcnow()
                    )
                    db.add(new_edu)
                    synced_count += 1
            db.commit()
        log_action("db", f"Synchronized education topics cache. Added {synced_count} new records.")
        return synced_count

    @staticmethod
    def get_cached_educations_list(db: Session, page: int = 1, page_size: int = 15) -> dict:
        total = db.query(EducationArticle).count()
        if total == 0:
            EducationService.sync_educations_from_source(db, max_pages=1)
            total = db.query(EducationArticle).count()

        offset = (page - 1) * page_size
        items = db.query(EducationArticle).order_by(EducationArticle.fetched_at.desc()).offset(offset).limit(page_size).all()
        log_action("db", f"Returned {len(items)} cached education topics for page {page}")
        return {"educations": items, "total": total, "page": page}

    @staticmethod
    def get_or_scrape_education_detail(db: Session, article_link: str) -> EducationArticleDetail:
        cached = db.query(EducationArticleDetail).filter(EducationArticleDetail.article_link == article_link).first()
        if cached:
            log_action("cache", f"Cache HIT for education detail: {article_link}")
            return cached

        log_action("cache", f"Cache MISS for education detail: {article_link} -> scraping from EduSkincare...")
        scraped = get_educations_details(article_link)
        if not scraped:
            log_action("scrap", f"Education detail not found on source: {article_link}", level="error")
            raise HTTPException(status_code=404, detail="Detail artikel edukasi tidak ditemukan.")

        new_detail = EducationArticleDetail(
            article_link=article_link,
            title=scraped.get("Title", ""),
            author=scraped.get("Author", "EduSkincare Team"),
            date=str(scraped.get("Date", "")),
            cover_image=scraped.get("Cover_Image", ""),
            content_markdown=scraped.get("Content", "")
        )
        db.add(new_detail)
        db.commit()
        db.refresh(new_detail)
        log_action("db", f"Saved new education detail permanently to DB for link: {article_link}")
        return new_detail
```

Write `routers/educations.py`:
```python
# routers/educations.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.database import get_db
from schemas.education import EducationListResponse, EducationDetailRequest, EducationDetailResponse
from services.education_service import EducationService

router = APIRouter(tags=["Skincare Educations"])

@router.get("", response_model=EducationListResponse)
def get_educations(page: int = Query(1, ge=1), db: Session = Depends(get_db)):
    """Mengambil daftar artikel edukasi skincare (disajikan dari cache PostgreSQL)"""
    return EducationService.get_cached_educations_list(db, page=page)

@router.post("/detail", response_model=EducationDetailResponse)
def get_education_detail(request: EducationDetailRequest, db: Session = Depends(get_db)):
    """Mengambil detail artikel edukasi (Lazy Cache: scrape 1x saat pertama kali diakses)"""
    return EducationService.get_or_scrape_education_detail(db, request.article_link)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_education_service.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add schemas/education.py services/education_service.py routers/educations.py tests/test_education_service.py
git commit -m "feat(education): implement 24h list caching and 1x lazy detail caching for educations"
```

---

### Task 7: Background APScheduler (24-Hour Sync) & Admin Management Endpoints

**Files:**
- Create: `scheduler/__init__.py`
- Create: `scheduler/jobs.py`
- Create: `routers/admin.py`
- Test: `tests/test_scheduler_admin.py`

**Interfaces:**
- Consumes: `services.news_service.NewsService`, `services.education_service.EducationService`, `routers.auth.require_role(["admin"])`
- Produces:
  - Scheduler functions: `start_scheduler()`, `stop_scheduler()`
  - Admin endpoints: `POST /api/v1/admin/sync/news`, `POST /api/v1/admin/sync/educations`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scheduler_admin.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routers.admin import router as admin_router
from routers.auth import get_current_user
from models.user import User
from unittest.mock import patch

app = FastAPI()
app.include_router(admin_router, prefix="/api/v1/admin")

# Mock user dependency
def override_admin_user():
    return User(id=1, email="admin@example.com", username="admin", role="admin")

def override_normal_user():
    return User(id=2, email="user@example.com", username="user", role="user")

client = TestClient(app)

def test_admin_sync_endpoints_access_control():
    # 1. Access as non-admin -> 403 Forbidden
    app.dependency_overrides[get_current_user] = override_normal_user
    resp = client.post("/api/v1/admin/sync/news")
    assert resp.status_code == 403

    # 2. Access as admin -> 200 OK
    app.dependency_overrides[get_current_user] = override_admin_user
    with patch("services.news_service.NewsService.sync_news_from_source", return_value=10):
        resp_admin = client.post("/api/v1/admin/sync/news")
        assert resp_admin.status_code == 200
        assert resp_admin.json()["synced_count"] == 10
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_scheduler_admin.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'routers.admin'`

- [ ] **Step 3: Implement scheduler jobs and admin router**

Write `scheduler/__init__.py`:
```python
# scheduler/__init__.py
```

Write `scheduler/jobs.py`:
```python
# scheduler/jobs.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from core.database import SessionLocal
from services.news_service import NewsService
from services.education_service import EducationService
from core.logger import log_action

scheduler = AsyncIOScheduler()

def run_daily_scraping_sync():
    log_action("schedule", "Running daily 24-hour scraping synchronization for articles and educations...")
    db = SessionLocal()
    try:
        news_synced = NewsService.sync_news_from_source(db, max_pages=3)
        edu_synced = EducationService.sync_educations_from_source(db, max_pages=2)
        log_action("schedule", f"Daily sync finished. Synced {news_synced} news, {edu_synced} educations.")
    except Exception as e:
        log_action("schedule", f"Error during scheduled daily sync: {str(e)}", level="error")
    finally:
        db.close()

def start_scheduler():
    scheduler.add_job(
        run_daily_scraping_sync,
        trigger=IntervalTrigger(hours=24),
        id="daily_scraping_sync",
        name="Sync articles and educations daily",
        replace_existing=True
    )
    scheduler.start()
    log_action("schedule", "APScheduler started (running every 24 hours).")

def stop_scheduler():
    scheduler.shutdown()
    log_action("schedule", "APScheduler stopped.")
```

Write `routers/admin.py`:
```python
# routers/admin.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.database import get_db
from routers.auth import require_role
from services.news_service import NewsService
from services.education_service import EducationService
from core.logger import log_action

router = APIRouter(tags=["Admin Operations"])

@router.post("/sync/news")
def sync_news_manual(
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["admin"]))
):
    """Trigger manual re-sync of news articles from source (Khusus Admin)"""
    log_action("admin", f"Manual news sync triggered by admin: {admin_user.email}")
    count = NewsService.sync_news_from_source(db, max_pages=3)
    return {"status": "success", "message": f"Berhasil sinkronisasi {count} berita terbaru.", "synced_count": count}

@router.post("/sync/educations")
def sync_educations_manual(
    db: Session = Depends(get_db),
    admin_user=Depends(require_role(["admin"]))
):
    """Trigger manual re-sync of education topics from source (Khusus Admin)"""
    log_action("admin", f"Manual educations sync triggered by admin: {admin_user.email}")
    count = EducationService.sync_educations_from_source(db, max_pages=2)
    return {"status": "success", "message": f"Berhasil sinkronisasi {count} topik edukasi terbaru.", "synced_count": count}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_scheduler_admin.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scheduler/ routers/admin.py tests/test_scheduler_admin.py
git commit -m "feat(scheduler): implement 24h APScheduler sync and admin manual trigger endpoints"
```

---

### Task 8: Skincare Endpoints Refactoring under `/api/v1/skincare`

**Files:**
- Create: `schemas/skincare.py`
- Create: `services/skincare_service.py`
- Create: `routers/skincare.py`
- Test: `tests/test_skincare_router.py`

**Interfaces:**
- Consumes: `services.llm_service.llm_service`, `helper.functions`, `helper.recommendations`
- Produces:
  - `POST /api/v1/skincare/read-ingredients`
  - `POST /api/v1/skincare/predict-skin`
  - `POST /api/v1/skincare/recommendations`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_skincare_router.py
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from routers.skincare import router as skincare_router
from unittest.mock import patch, AsyncMock

app = FastAPI()
app.include_router(skincare_router, prefix="/api/v1/skincare")
client = TestClient(app)

def test_skincare_recommendations_endpoint():
    fake_recs = {
        "recommendations": [{"product_name": "Moisturizer", "price": "50000", "product_image": "", "product_link": "", "match_reason": "Good for oily"}],
        "total_found": 1,
        "recommendation_count": 1,
        "skin_type": "oily"
    }
    with patch("helper.recommendations.get_skin_type_recommendations", return_value=fake_recs):
        resp = client.post("/api/v1/skincare/recommendations", json={"skin_type": "oily", "top_k": 5})
        assert resp.status_code == 200
        assert resp.json()["recommendation_count"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_skincare_router.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'schemas.skincare'`

- [ ] **Step 3: Implement skincare schemas, service, and router**

Write `schemas/skincare.py`:
```python
# schemas/skincare.py
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class SkinTypeEnum(str, Enum):
    oily = "oily"
    dry = "dry"
    normal = "normal"
    acne = "acne"
    sensitive = "sensitive"

class ProductRecommendation(BaseModel):
    product_name: str
    product_image: str
    product_link: str
    price: str
    similarity_score: float = 0.0

class HarmfulIngredientDetail(BaseModel):
    name: str
    reason: str

class ReadIngredientsRecommendations(BaseModel):
    products: List[ProductRecommendation] = []
    recommendation_count: int = 0

class ReadIngredientsResponse(BaseModel):
    extracted_ingredients: List[str]
    harmful_ingredients_found: List[HarmfulIngredientDetail]
    is_safe: bool
    total_harmful_ingredients: int
    recommendations: ReadIngredientsRecommendations

class PredictSkinResponse(BaseModel):
    dry: float
    normal: float
    oily: float
    predicted_label: str

class RecommendationsRequest(BaseModel):
    skin_type: SkinTypeEnum
    top_k: int = Field(default=10, ge=1, le=20)

class SkinTypeRecommendation(BaseModel):
    product_name: str
    product_image: str
    product_link: str
    price: str
    match_reason: str

class RecommendationsResponse(BaseModel):
    recommendations: List[SkinTypeRecommendation]
    total_found: int
    skin_type: SkinTypeEnum
    recommendation_count: int
```

Write `services/skincare_service.py`:
```python
# services/skincare_service.py
import base64
from fastapi import HTTPException, UploadFile
from helper.functions import (
    get_image_from_url, clean_extracted_text, parse_ingredients_to_list,
    get_ingredients_to_avoid, find_harmful_ingredients_with_details,
    predict_skin_type_from_image, load_resnet_skin_classifier, get_skin_type_label_mapping
)
from helper.recommendations import get_skincare_recommendations
from services.llm_service import llm_service
from core.logger import log_action

# Load ResNet once
resnet_model, resnet_transform = load_resnet_skin_classifier()
skin_label_mapping = get_skin_type_label_mapping()

class SkincareService:
    @staticmethod
    async def analyze_ingredients(file: UploadFile, image_url: str, skin_type: str):
        log_action("api", f"Processing /read-ingredients for skin_type: {skin_type}")
        if file:
            image_bytes = await file.read()
        elif image_url:
            image_bytes = get_image_from_url(image_url)
        else:
            raise HTTPException(status_code=400, detail="File gambar atau URL gambar diperlukan.")

        base64_str = base64.b64encode(image_bytes).decode("utf-8")
        extracted_text = await llm_service.extract_ingredients_from_image(base64_str)
        cleaned_text = clean_extracted_text(extracted_text)

        if cleaned_text.lower() == "ingredients not found" or len(cleaned_text.split()) < 3:
            return {
                "extracted_ingredients": ["ingredients not found"],
                "harmful_ingredients_found": [],
                "is_safe": False,
                "total_harmful_ingredients": 0,
                "recommendations": {"products": [], "recommendation_count": 0}
            }

        ingredients_list = parse_ingredients_to_list(cleaned_text)
        avoid_list = get_ingredients_to_avoid(skin_type)
        harmful_found = find_harmful_ingredients_with_details(cleaned_text, avoid_list, skin_type)
        is_safe = len(harmful_found) == 0

        # Similar recommendations
        recs = get_skincare_recommendations(input_ingredients=ingredients_list, skin_type=skin_type, top_k=5)
        simplified_recs = []
        for rec in recs.get("recommendations", []):
            simplified_recs.append({
                "product_name": rec.get("product_name", "Unknown"),
                "product_image": rec.get("product_image", "Unknown"),
                "product_link": rec.get("product_link", "Unknown"),
                "price": rec.get("price", "Unknown"),
                "similarity_score": rec.get("similarity_score", 0.0)
            })

        return {
            "extracted_ingredients": ingredients_list,
            "harmful_ingredients_found": harmful_found,
            "is_safe": is_safe,
            "total_harmful_ingredients": len(harmful_found),
            "recommendations": {"products": simplified_recs, "recommendation_count": len(simplified_recs)}
        }

    @staticmethod
    async def predict_skin(file: UploadFile, image_url: str):
        log_action("api", "Processing /predict-skin request")
        if file:
            image_bytes = await file.read()
        elif image_url:
            image_bytes = get_image_from_url(image_url)
        else:
            raise HTTPException(status_code=400, detail="File gambar atau URL gambar diperlukan.")

        prediction = predict_skin_type_from_image(image_bytes, resnet_model, resnet_transform, skin_label_mapping)
        log_action("api", f"Prediction completed: {prediction.get('predicted_label')}")
        return prediction
```

Write `routers/skincare.py`:
```python
# routers/skincare.py
from fastapi import APIRouter, File, UploadFile, Form, Depends
from schemas.skincare import (
    SkinTypeEnum, ReadIngredientsResponse, PredictSkinResponse,
    RecommendationsRequest, RecommendationsResponse
)
from services.skincare_service import SkincareService
from helper.recommendations import get_skin_type_recommendations

router = APIRouter(tags=["Skincare Analysis & Recommender"])

@router.post("/read-ingredients", response_model=ReadIngredientsResponse)
async def read_ingredients(
    file: UploadFile = File(None),
    image_url: str = Form(None),
    skin_type: SkinTypeEnum = Form(...)
):
    """Scan gambar kemasan skincare untuk ekstraksi bahan via LiteLLM dan analisis keamanan"""
    return await SkincareService.analyze_ingredients(file, image_url, skin_type)

@router.post("/predict-skin", response_model=PredictSkinResponse)
async def predict_skin(
    file: UploadFile = File(None),
    image_url: str = Form(None)
):
    """Prediksi tipe kulit (dry, normal, oily) dari foto wajah via model ResNet-50"""
    return await SkincareService.predict_skin(file, image_url)

@router.post("/recommendations", response_model=RecommendationsResponse)
def get_recommendations(request: RecommendationsRequest):
    """Rekomendasi produk berdasarkan tipe kulit pengguna dari katalog database"""
    recs = get_skin_type_recommendations(request.skin_type, request.top_k)
    return {
        "recommendations": recs.get("recommendations", []),
        "total_found": recs.get("total_found", 0),
        "skin_type": request.skin_type,
        "recommendation_count": recs.get("recommendation_count", 0)
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_skincare_router.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add schemas/skincare.py services/skincare_service.py routers/skincare.py tests/test_skincare_router.py
git commit -m "feat(skincare): refactor skincare analysis and recommender endpoints under /api/v1/skincare"
```

---

### Task 9: API Aggregator Router, Rate Limiting (SlowAPI), CORS & App Lifespan

**Files:**
- Create: `core/limiter.py`
- Create: `routers/api.py`
- Modify: `server.py`
- Test: `tests/test_app_integration.py`

**Interfaces:**
- Consumes: All routers (`auth`, `skincare`, `news`, `educations`, `admin`), `scheduler.jobs.start_scheduler`, `scheduler.jobs.stop_scheduler`
- Produces: Complete running FastAPI application mounted at `/api/v1`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_app_integration.py
import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def test_api_v1_health_and_root():
    # Root check
    resp_root = client.get("/")
    assert resp_root.status_code == 200

    # API v1 Health check
    resp_health = client.get("/api/v1/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] == "ok"
    assert resp_health.json()["version"] == "2.0.0"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_app_integration.py -v`  
Expected: FAIL because `/api/v1/health` does not exist yet.

- [ ] **Step 3: Implement limiter, API aggregator, and server.py**

Write `core/limiter.py`:
```python
# core/limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address
from core.config import settings

limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT])
```

Write `routers/api.py`:
```python
# routers/api.py
from fastapi import APIRouter
from routers.auth import router as auth_router
from routers.skincare import router as skincare_router
from routers.news import router as news_router
from routers.educations import router as educations_router
from routers.admin import router as admin_router
from core.config import settings

api_router = APIRouter()

@api_router.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(skincare_router, prefix="/skincare")
api_router.include_router(news_router, prefix="/news")
api_router.include_router(educations_router, prefix="/educations")
api_router.include_router(admin_router, prefix="/admin")
```

Modify `server.py`:
```python
# server.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from core.config import settings
from core.limiter import limiter
from core.database import init_db
from core.logger import log_action
from scheduler.jobs import start_scheduler, stop_scheduler
from routers.api import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    log_action("api", f"Starting {settings.PROJECT_NAME} v{settings.VERSION}...")
    # Initialize DB tables
    init_db()
    # Start 24h background sync scheduler
    start_scheduler()
    yield
    # Shutdown
    log_action("api", "Stopping services...")
    stop_scheduler()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="SkinSight & Skincare Intelligence API with PostgreSQL, LiteLLM, and JWT RBAC",
    version=settings.VERSION,
    lifespan=lifespan
)

# Attach Rate Limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Attach CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root route
@app.get("/")
def index():
    return {"message": "SkinCareIn API is running", "docs": "/docs", "version": settings.VERSION}

# Mount all /api/v1 routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_app_integration.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/limiter.py routers/api.py server.py tests/test_app_integration.py
git commit -m "feat(api): aggregate all routers under /api/v1 with SlowAPI and CORS middleware"
```

---

### Task 10: Docker Compose Cluster with Nginx Load Balancer & PostgreSQL

**Files:**
- Create: `nginx/nginx.conf`
- Modify: `dockerfile`
- Modify: `docker-compose.yml`

**Interfaces:**
- Consumes: `dockerfile`, `.env`
- Produces: Container cluster with Nginx at port `8888` balancing traffic to `api1` and `api2` connected to `postgres:16`

- [ ] **Step 1: Write Nginx load balancer configuration**

Write `nginx/nginx.conf`:
```nginx
# nginx/nginx.conf
events { worker_connections 1024; }

http {
    upstream backend_cluster {
        server api1:8000;
        server api2:8000;
    }

    server {
        listen 8888;
        client_max_body_size 25M;

        location / {
            proxy_pass http://backend_cluster;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 90s;
            proxy_read_timeout 180s;
        }
    }
}
```

- [ ] **Step 2: Update Dockerfile**

Modify `dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including PostgreSQL client libs and OpenCV requirements
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Update Docker Compose**

Modify `docker-compose.yml`:
```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: skincare_postgres
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgrespassword
      POSTGRES_DB: skinsight_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - skincare_network

  api1:
    build:
      context: .
      dockerfile: dockerfile
    restart: always
    depends_on:
      - postgres
    environment:
      - DATABASE_URL=postgresql://postgres:postgrespassword@postgres:5432/skinsight_db
    env_file:
      - .env
    networks:
      - skincare_network

  api2:
    build:
      context: .
      dockerfile: dockerfile
    restart: always
    depends_on:
      - postgres
    environment:
      - DATABASE_URL=postgresql://postgres:postgrespassword@postgres:5432/skinsight_db
    env_file:
      - .env
    networks:
      - skincare_network

  nginx:
    image: nginx:alpine
    container_name: skincare_load_balancer
    restart: always
    ports:
      - "8888:8888"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - api1
      - api2
    networks:
      - skincare_network

volumes:
  postgres_data:

networks:
  skincare_network:
    driver: bridge
```

- [ ] **Step 4: Verify syntax and configuration**

Run syntax checks on `nginx/nginx.conf` and `docker-compose.yml`.

- [ ] **Step 5: Commit**

```bash
git add nginx/ dockerfile docker-compose.yml
git commit -m "feat(infra): setup Nginx load balancer and Docker Compose cluster with PostgreSQL"
```
