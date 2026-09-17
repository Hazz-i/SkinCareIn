# 🌿 Architecture Specification: User Onboarding, Google OAuth, Email Verification & Personalized Dashboard

- **Topic:** User Onboarding, Google OAuth 2.0 (ID Token), Dual Email Verification (Link + OTP), Dermatological Ingredient Avoidance Matrix, and Mobile-First Personalized Dashboard
- **Date:** 2026-09-17
- **Status:** Approved / Ready for Implementation Planning
- **Target Platform:** Mobile-First (Flutter / React Native) & Web SPA compatible REST API

---

## 1. Executive Summary

This specification defines the architecture for SkinSight's expanded identity, onboarding, and personalized dashboard subsystems. It upgrades the core identity lifecycle from a simple email/password store to a modern, multi-provider, verified authentication system tailored for mobile applications. 

The implementation introduces:
1. **Extended User Entity:** Unified storage of identity attributes (`first_name`, `last_name`, `age`, `gender`, `skin_type`, `avoided_ingredients: JSON`, `is_onboarded`, `is_verified`, `auth_provider`, `role="member"`).
2. **Dual-Channel Email Verification:** Verification via email link (`GET /verify-email`) and 6-digit OTP code (`POST /verify-otp`), with console logging fallback for development/testing environments without configured SMTP.
3. **Native Google OAuth:** Direct Google ID Token validation (`POST /auth/google`) for seamless one-tap sign-in on mobile devices.
4. **Onboarding Workflow:** Post-login state evaluation (`is_onboarded`) guiding users to provide dermatological preferences (`POST /auth/onboarding`).
5. **Dermatological Ingredient Avoidance Matrix:** A medical-grade knowledge base categorizing prohibited cosmetic ingredients by skin type (`sensitive`, `oily`, `dry`, `combination`, `acne-prone`, `normal`).
6. **Mobile-First Personalized Dashboard:** A central feed (`GET /dashboard`) combining user health summaries, dermatological warnings, custom-filtered product recommendations (negative ingredient filtering), and cached scientific education/news previews.

---

## 2. User Lifecycle State Machine

```
[ Unregistered User ]
       │
       ├────────────────────────────────────────┐
       │ (Email / Password)                     │ (Google Sign-In)
       ▼                                        ▼
[ POST /auth/register ]                  [ POST /auth/google ]
  - role: "member"                         - role: "member"
  - is_verified: false                     - is_verified: true (auto)
  - is_onboarded: false                    - auth_provider: "google"
  - Generates 6-digit OTP & token          - First/Last name populated
  - Sends verification email               │
       │                                        │
       ▼                                        │
[ Email Verification ]                          │
  - GET /verify-email?token=...  OR             │
  - POST /verify-otp (6 digits)                 │
  - is_verified -> true                         │
       │                                        │
       ▼                                        │
[ POST /auth/login ]                            │
  - Gated: Requires is_verified == true         │
       │                                        │
       └──────────────────┬─────────────────────┘
                          ▼
            [ JWT Token Issued ]
              - access_token
              - is_onboarded: false
                          │
                          ▼
            [ POST /auth/onboarding ]
              - Age, Gender, Skin Type
              - Avoided Ingredients Array
              - is_onboarded -> true
                          │
                          ▼
             [ Active Verified Member ]
              - GET /api/v1/dashboard
              - Full Skincare AI & Catalog Access
```

---

## 3. Database Schema & Model Extensions (`models/user.py`)

The PostgreSQL `users` table is modified to incorporate identity, verification, and dermatological profile fields in a unified table structure:

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True) # Nullable for OAuth users
    
    # Profile & Demographic Information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True) # "male", "female", "other"
    
    # Dermatological Profile
    skin_type = Column(String(50), nullable=True) # "dry", "normal", "oily", "combination", "sensitive", "acne-prone"
    avoided_ingredients = Column(JSON, default=list, nullable=False) # List of prohibited ingredient strings
    
    # Security & RBAC Roles
    role = Column(String(20), default="member", nullable=False) # "member" or "admin"
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_onboarded = Column(Boolean, default=False, nullable=False)
    auth_provider = Column(String(20), default="local", nullable=False) # "local" or "google"
    
    # Verification Tokens
    verification_token = Column(String(255), nullable=True, index=True)
    verification_otp = Column(String(10), nullable=True, index=True)
    otp_expires_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

---

## 4. Dermatological Knowledge Base (`helper/ingredients.py`)

A structured dictionary provides dermatological rules, scientific justifications, and risk categories for each skin classification:

```python
SKIN_TYPE_EXCEPTIONS = {
    "sensitive": [
        {"name": "Fragrance", "category": "Sensitizer", "reason": "Causes contact dermatitis, stinging, and micro-inflammation."},
        {"name": "Alcohol Denat", "category": "Drying Alcohol", "reason": "Strips intercellular lipids and damages weakened skin barriers."},
        {"name": "Essential Oils", "category": "Volatile Botanical", "reason": "Contains terpenes (linalool, limonene) that trigger flare-ups."},
        {"name": "Sodium Lauryl Sulfate", "category": "Harsh Surfactant", "reason": "Disrupts the acid mantle and produces severe barrier disruption."},
        {"name": "Oxybenzone", "category": "Chemical UV Filter", "reason": "High incidence of photoallergic contact sensitization."},
        {"name": "Synthetic Dyes", "category": "Colorant", "reason": "Artificial color additives often provoke inflammatory reactions."}
    ],
    "oily": [
        {"name": "Coconut Oil", "category": "Comedogenic Lipid", "reason": "Kizman Comedogenicity Scale rating 4-5; rapidly occludes follicular openings."},
        {"name": "Mineral Oil", "category": "Heavy Occlusive", "reason": "Forms heavy film on epidermis, trapping excess sebum in hyperseborrheic skin."},
        {"name": "Lanolin", "category": "Comedogenic Wax", "reason": "Promotes microcomedone formation in oil-rich follicular environments."},
        {"name": "Isopropyl Myristate", "category": "Comedogenic Ester", "reason": "Penetrates and clogs follicular infundibulum, aggravating acne."},
        {"name": "Cocoa Butter", "category": "Heavy Lipid", "reason": "Extremely rich in saturated fats that occlude pores."}
    ],
    "dry": [
        {"name": "Alcohol Denat", "category": "Drying Alcohol", "reason": "Accelerates transepidermal water loss (TEWL) and causes flaking."},
        {"name": "Isopropyl Alcohol", "category": "Astringent Alcohol", "reason": "Dehydrates the stratum corneum, compromising natural moisturizing factors (NMF)."},
        {"name": "High-dose Salicylic Acid", "category": "BHA Keratolytic", "reason": "Depletes residual epidermal lipids without sufficient barrier replenishment."},
        {"name": "Kaolin / Bentonite Clay", "category": "Adsorbent", "reason": "Excessively adsorbs moisture and protective sebum from hyposeborrheic skin."},
        {"name": "Witch Hazel (Ethanol distilled)", "category": "Astringent", "reason": "High tannin and alcohol content induce excessive tissue tightness and dehydration."}
    ],
    "combination": [
        {"name": "Coconut Oil", "category": "Comedogenic Lipid", "reason": "Triggers follicular clogging on the seborrheic T-Zone."},
        {"name": "High-grade Alcohol Denat", "category": "Drying Alcohol", "reason": "Aggravates dehydration and dryness on the lateral cheeks/U-Zone."}
    ],
    "acne-prone": [
        {"name": "Isopropyl Palmitate", "category": "Comedogenic Ester", "reason": "Known hyperkeratotic trigger leading to comedogenesis."},
        {"name": "Ethylhexyl Palmitate", "category": "Comedogenic Solvent", "reason": "Proven high comedogenicity; accelerates Cutibacterium acnes proliferation."},
        {"name": "Algae Extract", "category": "Irritant / Comedogenic", "reason": "Can inflame sebaceous canals and accelerate follicular hyperkeratosis."},
        {"name": "Laureth-4", "category": "Comedogenic Emulsifier", "reason": "High comedogenic score (5/5); direct contributor to breakout cycles."},
        {"name": "D&C Red Dyes", "category": "Comedogenic Colorant", "reason": "Coal tar derivatives specifically associated with acne cosmetica."}
    ],
    "normal": [
        {"name": "Harsh Physical Scrubs (Walnut/Apricot)", "category": "Physical Exfoliant", "reason": "Produces micro-tears on healthy stratum corneum."},
        {"name": "Concentrated Sulfates", "category": "Harsh Surfactant", "reason": "Unnecessary harsh stripping of balanced lipid barrier."}
    ]
}
```

### Knowledge Base Endpoint
- `GET /api/v1/skincare/ingredients-to-avoid?skin_type={type}`
  - Returns the curated exception list and dermatological guidance for the requested skin type.
  - Enables mobile apps to populate interactive onboarding chips and checklist suggestions.

---

## 5. Authentication & Identity Subsystem

### 5.1 Registration (`POST /api/v1/auth/register`)
- **Input:** `UserRegisterRequest` (`email`, `username`, `password`)
- **Action:**
  1. Validates unique `email` and `username`.
  2. Hashes password using `passlib[bcrypt]`.
  3. Generates:
     - `verification_token`: Cryptographically secure URL-safe token (UUID / HMAC).
     - `verification_otp`: 6-digit numeric string (`000000` - `999999`).
     - `otp_expires_at`: `datetime.utcnow() + timedelta(minutes=15)`.
  4. Saves user with `role="member"`, `is_verified=False`, `is_onboarded=False`, `auth_provider="local"`.
  5. Dispatches verification email via SMTP service (or logs token & OTP to application logger if SMTP credentials in `.env` are unset).
- **Response:**
  ```json
  {
    "message": "Registration successful. Please verify your email with the 6-digit code or link sent to your inbox.",
    "email": "user@example.com",
    "is_verified": false
  }
  ```

### 5.2 Email Verification Endpoints
- **Web/Link Verification:** `GET /api/v1/auth/verify-email?token={token}`
  - Validates token against database; marks `is_verified=True`, nullifies token.
  - Returns confirmation message/HTML page for mobile browser redirects.
- **Mobile OTP Verification:** `POST /api/v1/auth/verify-otp`
  - Input: `{ "email": "user@example.com", "otp": "123456" }`
  - Validates OTP and checks `otp_expires_at > now()`.
  - Marks `is_verified=True`.
- **Resend Verification:** `POST /api/v1/auth/resend-verification`
  - Input: `{ "email": "user@example.com" }`
  - Regenerates token and OTP, resets expiration, and resends email.

### 5.3 Login (`POST /api/v1/auth/login`)
- Validates password against `hashed_password`.
- **Verification Gate:** If `user.is_verified is False`, raises `HTTP 403 Forbidden` with `"Email not verified. Please verify your email using the OTP code sent to your inbox."`
- Returns:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "role": "member",
    "is_onboarded": false
  }
  ```

### 5.4 Google OAuth (`POST /api/v1/auth/google`)
- **Input:** `{ "id_token": "eyJhbGci..." }`
- **Action:**
  1. Validates ID Token with Google token verification endpoint (`https://oauth2.googleapis.com/tokeninfo?id_token=...` or `google-auth` SDK).
  2. Extracts `email`, `given_name`, `family_name`, and `sub`.
  3. If user exists:
     - Updates `first_name` and `last_name` if previously unset.
  4. If user is new:
     - Creates user with `role="member"`, `is_verified=True` (since Google pre-verifies email), `is_onboarded=False`, `auth_provider="google"`.
     - Sets `first_name` and `last_name` from Google payload.
  5. Returns JWT `access_token`, `role`, and `is_onboarded`.

---

## 6. Onboarding Subsystem (`POST /api/v1/auth/onboarding`)

- **Security:** Requires Bearer JWT Token (`get_current_user`).
- **Request Payload:**
  ```json
  {
    "first_name": "Wahid",
    "last_name": "Hasyim",
    "age": 24,
    "gender": "male",
    "skin_type": "oily",
    "avoided_ingredients": [
      "Coconut Oil",
      "Mineral Oil",
      "Fragrance"
    ]
  }
  ```
- **Validation:**
  - `age`: Positive integer between 10 and 120.
  - `gender`: One of `"male"`, `"female"`, `"other"`.
  - `skin_type`: One of `"dry"`, `"normal"`, `"oily"`, `"combination"`, `"sensitive"`, `"acne-prone"`.
  - `avoided_ingredients`: List of strings (max 50 items).
- **Action:**
  - Updates the authenticated user's record.
  - Sets `is_onboarded = True`.
  - Commits to PostgreSQL.
- **Response:** Updated `UserProfileResponse`.

---

## 7. Personalized Dashboard Subsystem (`GET /api/v1/dashboard`)

- **Security:** Requires Bearer JWT Token.
- **Data Flow & Aggregation:**
  1. **User Profile Overview:** Returns authenticated user's name, age, skin type, and avoided ingredients.
  2. **Dermatological Care Guide:** Tailored skin care tips and forbidden ingredients for the user's `skin_type` from `helper/ingredients.py`.
  3. **Personalized Product Recommendations:**
     - Queries `products` table in PostgreSQL matching user's `skin_type`.
     - **Negative Filtering Algorithm:** Iterates through candidate products and strictly discards any product where `product.ingredients` contains any item in `user.avoided_ingredients` (case-insensitive substring match).
     - Limits output to top 6 curated, safe products.
  4. **Live Content Feeds:**
     - Retrieves 3 latest Lab Muffin educational articles from `education_articles` cache.
     - Retrieves 3 latest BeautyJournal articles from `news_articles` cache.
- **Response Structure:**
  ```json
  {
    "user_summary": {
      "id": 1,
      "name": "Wahid Hasyim",
      "email": "user@example.com",
      "age": 24,
      "gender": "male",
      "skin_type": "oily",
      "avoided_ingredients": ["Coconut Oil", "Mineral Oil", "Fragrance"]
    },
    "skin_health_tips": [
      "Use lightweight, gel-based or water-based hydrating serums.",
      "Incorporate Niacinamide and Zinc PCA to regulate sebum production."
    ],
    "dermatological_warnings": [
      {
        "name": "Coconut Oil",
        "category": "Comedogenic Lipid",
        "reason": "Rapidly occludes follicular openings."
      }
    ],
    "recommended_products": [
      {
        "id": 10,
        "title": "Purifying Gel Cleanser",
        "image_url": "https://example.com/img.jpg",
        "description": "Oil-free gel cleanser for oily and acne-prone skin.",
        "ingredients": "Water, Glycerin, Niacinamide, Salicylic Acid, Camellia Sinensis Leaf Extract"
      }
    ],
    "recent_educations": [
      {
        "title": "How Sunscreen Works",
        "link": "https://labmuffin.com/how-sunscreen-works/",
        "image_url": "https://labmuffin.com/wp-content/uploads/sunscreen.jpg",
        "date": "2026-09-15"
      }
    ],
    "recent_news": [
      {
        "title": "Niacinamide Benefits",
        "link": "https://www.beautyjournal.id/beauty-az/niacinamide",
        "image_url": "https://images.soco.id/beautyjournal/niacinamide.jpg",
        "date": "2026-08-10"
      }
    ]
  }
  ```

---

## 8. Mobile Menu API Mapping

| Mobile Screen / Menu | HTTP Method & Path | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| **Splash / Auth Check** | `GET /api/v1/auth/me` | Bearer Token | Evaluates `is_verified` and `is_onboarded` to route navigation. |
| **Sign In** | `POST /api/v1/auth/login` | None | Authenticates email/password credentials. |
| **Sign Up** | `POST /api/v1/auth/register` | None | Registers account and initiates email OTP dispatch. |
| **OTP Verification** | `POST /api/v1/auth/verify-otp` | None | Verifies 6-digit OTP code on mobile screen. |
| **Google Sign-In** | `POST /api/v1/auth/google` | None | Validates Google ID Token from native mobile SDK. |
| **Onboarding Form** | `POST /api/v1/auth/onboarding` | Bearer Token | Submits age, gender, skin type, and avoided ingredients. |
| **Ingredients Helper** | `GET /api/v1/skincare/ingredients-to-avoid` | None | Fetches suggested avoidance list for selected skin type. |
| **1. 🏠 Dashboard** | `GET /api/v1/dashboard` | Bearer Token | Main home screen (user summary, products, articles). |
| **2. 📚 Education & News** | `GET /api/v1/educations`, `GET /api/v1/news` | None | Paginated scientific guides and infinite scroll news. |
| **3. 🔍 Scan Ingredients** | `POST /api/v1/skincare/read-ingredients` | Bearer Token (Optional) | AI OCR with personalized warnings against user's avoided list. |
| **4. 🧴 Product Catalog** | `GET /api/v1/skincare/products`, `POST /recommendations` | None | Complete product browsing with skin type filters. |
| **5. 👤 Profile & Settings**| `GET /api/v1/auth/me`, `PUT /api/v1/auth/profile` | Bearer Token | Profile view and preferences management. |

---

## 9. Error Handling & Edge Cases

1. **Unverified Login Attempt:** Returns `403 Forbidden` with `"Email not verified. Please check your inbox for verification code."`
2. **Expired OTP:** Returns `400 Bad Request` with `"Verification code has expired. Please request a new code."`
3. **Google ID Token Invalid/Expired:** Returns `401 Unauthorized` with `"Invalid Google identity token."`
4. **Duplicate Email/Username:** Returns `400 Bad Request` with specific field conflict description.
5. **SMTP Offline / Unconfigured:** System falls back gracefully to tagged logging (`log_action("auth", f"MOCK EMAIL: Token={token}, OTP={otp}")`), allowing frictionless local testing and automated CI test execution.

---

## 10. Verification & Test Plan

1. **Unit Tests (`tests/test_auth_flow.py`):**
   - Test registration with OTP generation.
   - Test OTP validation success and expiration rejection.
   - Test login blocked when `is_verified=False`.
   - Test login allowed with `is_onboarded=False` returning in token response.
   - Test Google ID Token mock verification.
2. **Onboarding & Knowledge Base Tests (`tests/test_onboarding.py`):**
   - Test `GET /skincare/ingredients-to-avoid` for all skin classifications.
   - Test `POST /auth/onboarding` updating user fields and setting `is_onboarded=True`.
3. **Dashboard Tests (`tests/test_dashboard.py`):**
   - Test `GET /api/v1/dashboard` returning user summary, dermatological tips, and cached news/educations.
   - Test negative product filtering: verify products containing user's `avoided_ingredients` are excluded from recommendations.
