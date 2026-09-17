# SkinCareIn System Architecture & Improvement Design Spec

**Date**: 2026-09-17  
**Status**: Draft / Under Review  
**Author**: Antigravity Pair Programming Assistant  

---

## 1. Overview & Objectives

This document defines the architectural redesign and feature enhancements for **SkinCareIn (SkinSight API)**. The platform transitions from a single-file script architecture with a MySQL database to an enterprise-grade, modular, and resilient backend powered by **FastAPI**, **PostgreSQL**, **LiteLLM**, **APScheduler**, **SlowAPI**, and **Nginx Load Balancer**.

### Core Requirements
1. **API Versioning & Standardized Prefixes**: All API routes must start with `/api/v1/`.
2. **Authentication & Role-Based Access Control (RBAC)**: JWT-based authentication supporting `admin` and `user` roles with bcrypt-hashed passwords.
3. **Database Migration to PostgreSQL**: Full integration with PostgreSQL 16 via SQLAlchemy ORM models.
4. **LiteLLM Integration**: Unified, provider-agnostic interface for vision & OCR extraction, replacing direct Google GenAI SDK.
5. **Two-Tier Scraping & Database Caching Strategy**:
   - **Articles & Education Lists**: Cached in PostgreSQL, updated automatically once every 24 hours via APScheduler background job (with manual admin trigger endpoints).
   - **Articles & Education Details**: Cached on-demand (lazy caching). First request scrapes and saves to DB; all subsequent requests hit the DB without re-scraping.
6. **Rate Limiting & CORS**: SlowAPI rate limiter with custom request tiers and multi-origin CORS support.
7. **Load Balancing**: Nginx reverse proxy load balancer distributing traffic across multiple FastAPI container replicas.
8. **Tagged Action Logging**: Standardized console/file logs categorized with explicit tags (`[auth]`, `[scrap]`, `[cache]`, `[db]`, `[llm]`, `[ratelimit]`, `[schedule]`, `[api]`).

---

## 2. Directory & Component Structure

The repository is organized following Clean Architecture principles:

```plaintext
SkinCareIn/
├── core/
│   ├── config.py              # Centralized configuration (Pydantic Settings)
│   ├── database.py            # PostgreSQL engine, sessionmaker, and Base
│   ├── security.py            # Password hashing (bcrypt) & JWT token handling
│   ├── limiter.py             # SlowAPI Rate Limiter setup
│   └── logger.py              # Tagged Action Logger
├── models/                    # SQLAlchemy ORM Models
│   ├── __init__.py
│   ├── user.py                # Users and roles (admin / user)
│   ├── product.py             # Skincare products catalog
│   ├── article.py             # News list and news details cache tables
│   └── education.py           # Education list and education details cache tables
├── schemas/                   # Pydantic validation models
│   ├── __init__.py
│   ├── auth.py                # Register, Login, Token, UserProfile
│   ├── skincare.py            # OCR request/response, Face predict, Recommendations
│   ├── news.py                # News list, pagination, and detail schemas
│   └── education.py           # Education list, pagination, and detail schemas
├── services/                  # Business logic
│   ├── auth_service.py        # Authentication & user management logic
│   ├── llm_service.py         # LiteLLM completion wrapper & fallback
│   ├── news_service.py        # News scraping & DB caching operations
│   ├── education_service.py   # Education scraping & DB caching operations
│   └── skincare_service.py    # ResNet-50 prediction, TF-IDF Recommender, OpenCV
├── routers/                   # API v1 Route Controllers
│   ├── __init__.py
│   ├── api.py                 # Aggregator router mounting /api/v1
│   ├── auth.py                # /api/v1/auth/*
│   ├── skincare.py            # /api/v1/skincare/*
│   ├── news.py                # /api/v1/news/*
│   ├── educations.py          # /api/v1/educations/*
│   └── admin.py               # /api/v1/admin/*
├── scheduler/
│   ├── __init__.py
│   └── jobs.py                # APScheduler 24h background sync jobs
├── nginx/
│   └── nginx.conf             # Nginx reverse proxy and upstream round-robin config
├── helper/                    # Preserved legacy utilities (gradually imported by services)
├── utils/                     # Details.json and shared constants
├── dockerfile                 # Container image specification
├── docker-compose.yml         # Compose configuration (PostgreSQL + Replicas + Nginx)
├── server.py                  # FastAPI application entrypoint
└── requirements.txt           # Python dependencies
```

---

## 3. Database Schema (PostgreSQL)

### 3.1 `users`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID / Integer | PRIMARY KEY, AUTO_INCREMENT | Unique user ID |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | User login email |
| `username` | VARCHAR(100) | UNIQUE, NOT NULL | User handle |
| `hashed_password`| VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| `role` | VARCHAR(20) | NOT NULL, DEFAULT 'user' | 'admin' or 'user' |
| `is_active` | BOOLEAN | DEFAULT TRUE | Account active flag |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Registration timestamp |

### 3.2 `products`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Product ID |
| `title` | VARCHAR(500) | NOT NULL | Product name |
| `price` | VARCHAR(100) | NULLABLE | Product price string |
| `description` | TEXT | NULLABLE | Cleaned description text |
| `image_url` | TEXT | NULLABLE | URL of product image |
| `link` | TEXT | NULLABLE | URL to product source/store |
| `ingredients` | TEXT | NULLABLE | Extracted raw ingredients |
| `type` | VARCHAR(100) | NULLABLE | Brand or product category |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Record creation date |

### 3.3 `news_articles` (List Cache)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Article list item ID |
| `title` | VARCHAR(500) | NOT NULL | Article title |
| `link` | VARCHAR(1000) | UNIQUE, NOT NULL, INDEX | Source link on Kompas |
| `image_url` | TEXT | NULLABLE | Thumbnail image URL |
| `date` | VARCHAR(100) | NULLABLE | Published date string |
| `category` | VARCHAR(100) | NULLABLE | News category |
| `page_number` | Integer | DEFAULT 1 | Page index from scraping |
| `fetched_at` | TIMESTAMP | DEFAULT NOW() | Last scraped timestamp |

### 3.4 `news_article_details` (Detail Cache - Permanent / 1x Lazy)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Detail record ID |
| `article_link` | VARCHAR(1000) | UNIQUE, NOT NULL, INDEX | Link identifying article |
| `title` | VARCHAR(500) | NOT NULL | Full article title |
| `cover_image` | TEXT | NULLABLE | High-res cover image URL |
| `date` | VARCHAR(100) | NULLABLE | Parsed publication date |
| `source` | VARCHAR(100) | NULLABLE | Source publisher |
| `author` | VARCHAR(150) | NULLABLE | Writer / editor |
| `content_markdown` | TEXT | NOT NULL | Full article text/markdown |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Date scraped and cached |

### 3.5 `education_articles` (List Cache)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Education item ID |
| `title` | VARCHAR(500) | NOT NULL | Education topic title |
| `link` | VARCHAR(1000) | UNIQUE, NOT NULL, INDEX | Article link |
| `image_url` | TEXT | NULLABLE | Thumbnail image |
| `snippet` | TEXT | NULLABLE | Summary snippet |
| `date` | VARCHAR(100) | NULLABLE | Publication date |
| `category` | VARCHAR(100) | NULLABLE | Category |
| `page_number` | Integer | DEFAULT 1 | Page number |
| `fetched_at` | TIMESTAMP | DEFAULT NOW() | Last scraped timestamp |

### 3.6 `education_article_details` (Detail Cache - Permanent / 1x Lazy)
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | PRIMARY KEY, AUTO_INCREMENT | Education detail ID |
| `article_link` | VARCHAR(1000) | UNIQUE, NOT NULL, INDEX | Unique link to article |
| `title` | VARCHAR(500) | NOT NULL | Full title |
| `author` | VARCHAR(150) | NULLABLE | Author name |
| `date` | VARCHAR(100) | NULLABLE | Published date |
| `cover_image` | TEXT | NULLABLE | Main image URL |
| `content_markdown` | TEXT | NOT NULL | Full body content |
| `created_at` | TIMESTAMP | DEFAULT NOW() | Date scraped and cached |

---

## 4. API Endpoints Specification (`/api/v1/`)

All endpoints are grouped under the `/api/v1/` prefix.

### 4.1 Authentication & Profile (`/api/v1/auth`)
- **`POST /api/v1/auth/register`**:
  - Request: `{ "email": "...", "username": "...", "password": "..." }`
  - Response: Created user representation (excluding password hash).
- **`POST /api/v1/auth/login`**:
  - Request: `OAuth2PasswordRequestForm` or JSON credentials.
  - Response: `{ "access_token": "...", "token_type": "bearer", "role": "user" }`
- **`GET /api/v1/auth/me`**:
  - Requires: Bearer token header.
  - Response: Current user details and role.

### 4.2 Skincare Analysis & Recommendations (`/api/v1/skincare`)
- **`POST /api/v1/skincare/read-ingredients`**:
  - Request: Multipart Form (`file`: UploadFile optional, `image_url`: string optional, `skin_type`: enum).
  - Rate Limit: `10/minute`.
  - Logic: LiteLLM vision OCR -> parse ingredients -> check harmful ingredients per skin type -> compute TF-IDF recommendations from DB.
- **`POST /api/v1/skincare/predict-skin`**:
  - Request: Multipart Form (`file`: UploadFile optional, `image_url`: string optional).
  - Rate Limit: `10/minute`.
  - Logic: OpenCV facial validation -> ResNet-50 deep learning model -> dry/normal/oily probabilities.
- **`POST /api/v1/skincare/recommendations`**:
  - Request: JSON `{ "skin_type": "oily", "top_k": 10 }`.
  - Logic: Query products matching skin type criteria.

### 4.3 News (`/api/v1/news`)
- **`GET /api/v1/news`** (or `POST /api/v1/news` with page parameter):
  - Request: Query param `page: int = 1`.
  - Logic: Read cached articles from `news_articles` table. Zero scraping delay.
- **`POST /api/v1/news/detail`**:
  - Request: `{ "article_link": "..." }`.
  - Logic:
    1. Check `news_article_details` table by `article_link`.
    2. If found -> return cached detail immediately (`[cache] Cache HIT`).
    3. If not found -> scrape from Kompas once, save to `news_article_details`, return result (`[scrap] Cache MISS`).

### 4.4 Educations (`/api/v1/educations`)
- **`GET /api/v1/educations`** (or `POST /api/v1/educations` with page parameter):
  - Request: Query param `page: int = 1`.
  - Logic: Read cached education topics from `education_articles` table.
- **`POST /api/v1/educations/detail`**:
  - Request: `{ "article_link": "..." }`.
  - Logic:
    1. Check `education_article_details` table by `article_link`.
    2. If found -> return cached detail (`[cache] Cache HIT`).
    3. If not found -> scrape from EduSkincare once, save to DB, return result (`[scrap] Cache MISS`).

### 4.5 Admin Endpoints (`/api/v1/admin`)
- **`POST /api/v1/admin/sync/news`**:
  - Requires: Bearer Token with role `admin`.
  - Action: Trigger immediate re-scraping of news list and upsert into database.
- **`POST /api/v1/admin/sync/educations`**:
  - Requires: Bearer Token with role `admin`.
  - Action: Trigger immediate re-scraping of education list and upsert into database.

### 4.6 Health Check
- **`GET /api/v1/health`** and **`GET /`**:
  - Returns service status, database connectivity status, and version.

---

## 5. LiteLLM Integration Design

LiteLLM (`litellm`) provides a unified SDK call for over 100 LLMs.

### Implementation in `services/llm_service.py`
```python
import os
import litellm
from core.logger import log_action

class LLMService:
    def __init__(self):
        self.model = os.getenv("LLM_MODEL", "gemini/gemini-2.5-flash")
        self.fallback_models = os.getenv("LLM_FALLBACKS", "gemini/gemini-1.5-flash").split(",")
        litellm.drop_params = True

    async def extract_ingredients_from_image(self, base64_image: str) -> str:
        prompt = (
            "Cari ingredients/bahan/komposisi dalam gambar ini dan berikan hasilnya dalam format "
            "teks biasa tanpa markdown atau formatting lainnya. Buang teks yang tidak relevan seperti "
            "nama brand atau informasi lain yang tidak berkaitan dengan bahan. Jika tidak terdapat "
            "ingredients sama sekali, tampilkan 'ingredients not found'."
        )
        log_action("llm", f"Sending OCR request using model {self.model}")
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
                fallbacks=self.fallback_models
            )
            extracted_text = response.choices[0].message.content
            log_action("llm", f"Received response ({len(extracted_text)} chars)")
            return extracted_text
        except Exception as e:
            log_action("llm", f"Error during LiteLLM invocation: {str(e)}", level="error")
            raise
```

---

## 6. Background Scheduling & Caching Lifecycle

### 6.1 Daily 24-Hour Synchronization Job
- `APScheduler` is configured within `scheduler/jobs.py` and started during FastAPI `lifespan`.
- Runs every 24 hours (`IntervalTrigger(hours=24)` or cron at `02:00` daily).
- Process:
  1. Scrapes the latest 3-5 pages of Kompas Skincare News.
  2. Upserts articles into `news_articles` (updates `fetched_at` timestamp).
  3. Scrapes latest pages of EduSkincare.
  4. Upserts articles into `education_articles`.
  5. Emits tagged logs `[schedule] ...` and `[db] ...`.

### 6.2 Lazy On-Demand Detail Caching Flow
```
User Request Detail (/api/v1/news/detail)
                 │
        Query DB for link?
        ├─── YES ───> [cache] Cache HIT -> Return DB record immediately (0ms scrape)
        │
        └─── NO ────> [cache] Cache MISS
                          │
                   [scrap] Scrape source URL 1x
                          │
                   [db] Save to news_article_details
                          │
                   Return newly cached record to user
```

---

## 7. Rate Limiting, CORS & Logging

### 7.1 Rate Limiting (`slowapi`)
- Limiter initialized with `get_remote_address` or authenticated user ID.
- Default limit: `60/minute` on general read endpoints.
- Heavy limit: `10/minute` on `/api/v1/skincare/read-ingredients` and `/api/v1/skincare/predict-skin`.
- Standard headers included in responses: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

### 7.2 CORS
- `CORSMiddleware` configured with origins loaded from `CORS_ORIGIN` (split by comma) and localhost defaults.

### 7.3 Tagged Action Logger (`core/logger.py`)
Standard format:
```
[TAG] YYYY-MM-DD HH:MM:SS - Message
```
Supported Tags:
- `[auth]` : User login, registration, token validation, permission checks.
- `[scrap]` : Outgoing web scraper requests, HTML parsing progress.
- `[cache]` : Cache HIT and Cache MISS occurrences.
- `[db]` : Database connections, queries, upserts.
- `[llm]` : LiteLLM prompt dispatch, token usage, fallback triggers.
- `[ratelimit]` : Rate limit throttling events.
- `[schedule]` : Background cron execution milestones.
- `[api]` : Inbound requests and outbound status codes.

---

## 8. Deployment Architecture: Nginx Load Balancer & Docker Compose

### 8.1 Docker Compose Services
- **`postgres`**: Official `postgres:16-alpine` container with named volume `postgres_data`. Exposes port `5432` internally.
- **`api1` & `api2`**: Two separate containers built from `dockerfile`. Each runs `uvicorn server:app --host 0.0.0.0 --port 8000`.
- **`nginx`**: Reverse proxy and load balancer mapped to host port `8888:8888`.

### 8.2 Nginx Configuration (`nginx/nginx.conf`)
```nginx
events { worker_connections 1024; }

http {
    upstream backend_cluster {
        server api1:8000;
        server api2:8000;
    }

    server {
        listen 8888;
        client_max_body_size 20M;

        location / {
            proxy_pass http://backend_cluster;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_read_timeout 120s;
        }
    }
}
```

---

## 9. Verification & Testing Plan

1. **Database & ORM**:
   - Verify PostgreSQL connection and table creation via SQLAlchemy startup event or Alembic/init script.
   - Verify data seeding script populates `products` table in PostgreSQL.
2. **Auth & RBAC**:
   - Register a new user (`POST /api/v1/auth/register`).
   - Login and receive JWT (`POST /api/v1/auth/login`).
   - Access protected user route (`GET /api/v1/auth/me`).
   - Attempt access to admin endpoint (`POST /api/v1/admin/sync/news`) with `user` role (must return 403 Forbidden).
   - Access admin endpoint with `admin` role (must succeed 200 OK).
3. **LiteLLM**:
   - Call `/api/v1/skincare/read-ingredients` with a sample skincare label image.
   - Confirm LiteLLM handles the request and logs `[llm]` properly.
4. **Caching & 24h Sync**:
   - Call `/api/v1/news/detail` twice with the same link.
   - Confirm first request logs `[scrap] Cache MISS` and saves to DB.
   - Confirm second request logs `[cache] Cache HIT` and queries DB without scraping.
5. **Rate Limiting & CORS**:
   - Send > 10 requests within a minute to `/api/v1/skincare/read-ingredients` and verify `429 Too Many Requests`.
   - Inspect CORS headers for allowed origins.
6. **Load Balancer**:
   - Fire requests through `http://localhost:8888/api/v1/health` and verify alternating logs between `api1` and `api2`.
