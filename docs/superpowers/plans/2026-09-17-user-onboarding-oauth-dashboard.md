# User Onboarding, Email Verification & Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement extended user model, dual-channel email verification (OTP + Link), post-login onboarding workflow, dermatological knowledge base, and mobile-first personalized dashboard with negative ingredient filtering. (Google OAuth deferred per user request).

**Architecture:** Extend FastAPI identity subsystem with verification tokens and post-login onboarding state (`is_onboarded`), add SMTP email service with logger fallback, upgrade ingredient exceptions into a structured dermatological dictionary, and aggregate dashboard insights with negative ingredient matching against user-specified allergens.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, PostgreSQL, Pydantic v2, Python 3.12, smtplib.

**Spec:** docs/superpowers/specs/2026-09-17-user-onboarding-oauth-dashboard-design.md

## Global Constraints
- Language: All code comments, docstrings, log messages, and error descriptions must be in English.
- Logging: Use tagged logging via `log_action(tag, message)` with standard tags `[auth]`, `[db]`, `[api]`.
- Default Role: Registered users must have default role `member`. Admin seeded users have `admin`.
- Python Environment: Must run with `.venv\Scripts\python.exe` (Python 3.12).
- Google OAuth is deferred for later phase; `auth_provider` defaults to `"local"`.
- Backward Compatibility: Keep existing function signatures and routes functional while extending capabilities.

---

### Task 1: Extend User Entity Model

**Files:**
- Modify: `models/user.py`
- Modify: `core/database.py` (ensure admin seeding initializes new fields)
- Test: `tests/test_user_model.py`

**Interfaces:**
- Consumes: `core.database.Base`
- Produces: `models.user.User` with columns:
  - `id`: int PK
  - `email`: str, unique, not null
  - `username`: str, unique, not null
  - `hashed_password`: str, nullable (for future OAuth compatibility)
  - `first_name`: str, nullable
  - `last_name`: str, nullable
  - `age`: int, nullable
  - `gender`: str, nullable
  - `skin_type`: str, nullable
  - `avoided_ingredients`: JSON, default=list, nullable=False
  - `role`: str, default="member", nullable=False
  - `is_active`: bool, default=True, nullable=False
  - `is_verified`: bool, default=False, nullable=False
  - `is_onboarded`: bool, default=False, nullable=False
  - `auth_provider`: str, default="local", nullable=False
  - `verification_token`: str, nullable=True, index=True
  - `verification_otp`: str, nullable=True, index=True
  - `otp_expires_at`: DateTime, nullable=True
  - `created_at`: DateTime, default=datetime.utcnow
  - `updated_at`: DateTime, default=datetime.utcnow, onupdate=datetime.utcnow

- [ ] **Step 1: Write the failing test**
Create `tests/test_user_model.py` checking the User model fields and default values.
- [ ] **Step 2: Run test to verify it fails**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_user_model.py -v`
- [ ] **Step 3: Update `models/user.py` and `core/database.py`**
Add the new columns to `models/user.py`. Update `init_db()` in `core/database.py` to seed admin with `role="admin"`, `is_verified=True`, `is_onboarded=True`.
- [ ] **Step 4: Run test to verify it passes**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_user_model.py -v`
- [ ] **Step 5: Commit**
`git add models/user.py core/database.py tests/test_user_model.py && git commit -m "feat: extend User model with onboarding and verification attributes"`

---

### Task 2: Dermatological Knowledge Base & Ingredients Helper

**Files:**
- Modify: `helper/ingredients.py`
- Modify: `routers/skincare.py`
- Test: `tests/test_ingredients_helper.py`

**Interfaces:**
- Consumes: None
- Produces:
  - `SKIN_TYPE_EXCEPTIONS`: dict mapping 6 skin types (`sensitive`, `oily`, `dry`, `combination`, `acne-prone`, `normal`) to lists of `{"name": str, "category": str, "reason": str}`.
  - Backward compatibility aliases: `ingredients_avoid_oily`, `ingredients_avoid_dry`, `ingredients_avoid_normal`, `ingredients_avoid_acne`, `ingredients_avoid_sensitive`.
  - Endpoint `GET /api/v1/skincare/ingredients-to-avoid?skin_type={type}` returning `{ "skin_type": str, "exceptions": list, "tips": list }`.

- [ ] **Step 1: Write the failing test**
Create `tests/test_ingredients_helper.py` asserting all 6 skin types in `SKIN_TYPE_EXCEPTIONS` and testing the new endpoint logic.
- [ ] **Step 2: Run test to verify it fails**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_ingredients_helper.py -v`
- [ ] **Step 3: Update `helper/ingredients.py` and `routers/skincare.py`**
Implement the structured knowledge dictionary, preserve aliases, and add `GET /ingredients-to-avoid`.
- [ ] **Step 4: Run test to verify it passes**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_ingredients_helper.py -v`
- [ ] **Step 5: Commit**
`git add helper/ingredients.py routers/skincare.py tests/test_ingredients_helper.py && git commit -m "feat: structured dermatological knowledge base and ingredients avoidance endpoint"`

---

### Task 3: Configuration & Email Verification Service

**Files:**
- Modify: `core/config.py`
- Modify: `.env` and `.env.example`
- Create: `services/email_service.py`
- Test: `tests/test_email_service.py`

**Interfaces:**
- Consumes: `core.config.settings`
- Produces:
  - `EmailService.send_verification_email(email: str, token: str, otp: str) -> bool`
  - Graceful fallback: logs `[auth] Verification email dispatched to ... OTP: ..., Token: ...` when SMTP host is unset or unavailable.

- [ ] **Step 1: Write the failing test**
Create `tests/test_email_service.py` testing email sending with console/mock fallback.
- [ ] **Step 2: Run test to verify it fails**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_email_service.py -v`
- [ ] **Step 3: Update `core/config.py`, `.env`, `.env.example`, and create `services/email_service.py`**
Add SMTP settings (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`, `APP_BASE_URL`). Implement `EmailService`.
- [ ] **Step 4: Run test to verify it passes**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_email_service.py -v`
- [ ] **Step 5: Commit**
`git add core/config.py .env.example services/email_service.py tests/test_email_service.py && git commit -m "feat: add email verification service with SMTP and console fallback"`

---

### Task 4: Auth Schemas & Service Expansion (Register, OTP, Link, Login Gate)

**Files:**
- Modify: `schemas/auth.py`
- Modify: `services/auth_service.py`
- Test: `tests/test_auth_service.py`

**Interfaces:**
- Consumes: `models.user.User`, `services.email_service.EmailService`, `core.security.*`
- Produces:
  - `AuthService.register_user`: sets `role="member"`, generates token + OTP + 15m expiration, triggers `send_verification_email`, returns registration status dict.
  - `AuthService.verify_email(token: str)`: marks `is_verified=True`.
  - `AuthService.verify_otp(email: str, otp: str)`: validates code and expiration, marks `is_verified=True`.
  - `AuthService.resend_verification(email: str)`: regenerates token + OTP and resends.
  - `AuthService.authenticate_user`: verifies password, validates `is_verified` (raises 403 if False), returns token payload with `is_onboarded`.

- [ ] **Step 1: Write the failing test**
Create `tests/test_auth_service.py` testing registration, unverified login block, OTP verification, and resend.
- [ ] **Step 2: Run test to verify it fails**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_auth_service.py -v`
- [ ] **Step 3: Implement schemas and service methods**
Update `schemas/auth.py` with `VerifyOTPRequest`, `ResendVerificationRequest`, `RegisterResponse`, and update `TokenResponse` with `is_onboarded`. Update `services/auth_service.py`.
- [ ] **Step 4: Run test to verify it passes**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_auth_service.py -v`
- [ ] **Step 5: Commit**
`git add schemas/auth.py services/auth_service.py tests/test_auth_service.py && git commit -m "feat: expand auth service with email verification and login verification gate"`

---

### Task 5: Auth Router Endpoints & Onboarding Flow

**Files:**
- Modify: `schemas/auth.py` (add OnboardingRequest, UpdateProfileRequest, UserProfileResponse with new fields)
- Modify: `services/auth_service.py` (add `complete_onboarding`, `update_profile`)
- Modify: `routers/auth.py` (add `/verify-email`, `/verify-otp`, `/resend-verification`, `/onboarding`, `/profile`)
- Test: `tests/test_onboarding.py`

**Interfaces:**
- Consumes: `get_current_user`, `AuthService`
- Produces:
  - `GET /api/v1/auth/verify-email?token=...`
  - `POST /api/v1/auth/verify-otp`
  - `POST /api/v1/auth/resend-verification`
  - `POST /api/v1/auth/onboarding` (updates first/last name, age, gender, skin_type, avoided_ingredients, sets `is_onboarded=True`)
  - `PUT /api/v1/auth/profile`
  - Updated `GET /api/v1/auth/me` returning all user profile attributes.

- [ ] **Step 1: Write the failing test**
Create `tests/test_onboarding.py` verifying onboarding validation, profile updating, and onboarding completion state.
- [ ] **Step 2: Run test to verify it fails**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_onboarding.py -v`
- [ ] **Step 3: Implement onboarding and profile endpoints**
Update `schemas/auth.py`, `services/auth_service.py`, and `routers/auth.py`.
- [ ] **Step 4: Run test to verify it passes**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_onboarding.py -v`
- [ ] **Step 5: Commit**
`git add schemas/auth.py services/auth_service.py routers/auth.py tests/test_onboarding.py && git commit -m "feat: add onboarding, verification, and profile management endpoints"`

---

### Task 6: Mobile-First Personalized Dashboard Subsystem

**Files:**
- Create: `schemas/dashboard.py`
- Create: `services/dashboard_service.py`
- Create: `routers/dashboard.py`
- Modify: `routers/api.py` (include dashboard router)
- Test: `tests/test_dashboard.py`

**Interfaces:**
- Consumes: `models.user.User`, `models.product.Product`, `models.education.EducationArticle`, `models.article.NewsArticle`, `helper.ingredients.SKIN_TYPE_EXCEPTIONS`
- Produces:
  - `GET /api/v1/dashboard`
  - Negative ingredient filtering: excludes any product whose `ingredients` contains any item in `user.avoided_ingredients` (case-insensitive substring match).
  - Returns:
    - `user_summary`: id, name, email, age, gender, skin_type, avoided_ingredients
    - `skin_health_tips`: customized guidance based on skin_type
    - `dermatological_warnings`: exception objects from `SKIN_TYPE_EXCEPTIONS`
    - `recommended_products`: safe products filtered by user skin type and negative ingredient rules
    - `recent_educations`: 3 latest educational guides
    - `recent_news`: 3 latest beauty news/glossary items

- [ ] **Step 1: Write the failing test**
Create `tests/test_dashboard.py` asserting dashboard response structure and verifying that products containing avoided ingredients are strictly omitted.
- [ ] **Step 2: Run test to verify it fails**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_dashboard.py -v`
- [ ] **Step 3: Implement Dashboard schemas, service, router, and wire to `routers/api.py`**
Implement negative ingredient filtering algorithm, tips mapping, and wire endpoint.
- [ ] **Step 4: Run test to verify it passes**
Run: `.\.venv\Scripts\python.exe -m pytest tests/test_dashboard.py -v`
- [ ] **Step 5: Commit**
`git add schemas/dashboard.py services/dashboard_service.py routers/dashboard.py routers/api.py tests/test_dashboard.py && git commit -m "feat: personalized dashboard with negative ingredient filtering"`

---

### Task 7: Full Integration Verification & Documentation

**Files:**
- Modify: `README.md`
- Run full pytest test suite: `.\.venv\Scripts\python.exe -m pytest -v`
- Test: all unit and integration tests

- [ ] **Step 1: Run full test suite across the repository**
Run: `.\.venv\Scripts\python.exe -m pytest -v`
Ensure all tests pass with 0 failures.
- [ ] **Step 2: Update README.md**
Document the new auth endpoints, onboarding flow, ingredients avoidance matrix, and dashboard API.
- [ ] **Step 3: Commit and finalize**
`git add README.md && git commit -m "docs: document user onboarding, email verification, and dashboard endpoints"`
