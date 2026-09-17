# 🌿 SkinSight - AI-Powered Skincare & Dermatological Intelligence API

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![LiteLLM](https://img.shields.io/badge/LiteLLM-Integrated-purple.svg)](https://github.com/BerriAI/litellm)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)

**SkinSight** is an enterprise-grade backend platform providing intelligent skincare analysis, deep-learning-based facial skin classification (ResNet-50), multi-model ingredient safety analysis via **LiteLLM**, two-tier caching with **PostgreSQL**, robust **Role-Based Access Control (RBAC)**, and high-availability traffic distribution using an **Nginx Load Balancer**.

---

## 🚀 Key Features

### 1. 🔐 Authentication & RBAC (Role-Based Access Control)
- **Bcrypt Password Hashing & JWT Bearer Tokens:** Secure token generation and verification.
- **Hierarchical Roles:** Distinguishes between standard `user` and privileged `admin` permissions.
- **Auto-Seeded Administrator:** Seamless bootstrap of a default admin account on initial application startup.

### 2. 🧠 Multi-Model AI Vision & OCR via LiteLLM
- **Ingredient Extraction & Safety Analysis:** Analyzes product packaging images to extract active ingredients and evaluate risk profiles tailored to specific skin types.
- **Automated Fallback Orchestration:** Seamless fallback handling across models (Primary: `gemini/gemini-2.5-flash`, Fallback: `gemini/gemini-1.5-flash`).

### 3. 🔬 Deep Learning Skin Type Classification
- **ResNet-50 Architecture:** Classifies facial photograph inputs into dermatological skin categories (`dry`, `normal`, `oily`).
- **Personalized Catalog Recommendations:** Recommends curated skincare products matching the detected skin profile.

### 4. ⚡ Two-Tier Database Caching Architecture
- **24-Hour Periodic Sync:** News and educational topic feeds are stored in PostgreSQL and refreshed daily in the background via **APScheduler**.
- **1-Time Lazy Detail Caching:** Full article content is scraped once on initial user request, permanently stored in PostgreSQL, and served instantaneously on subsequent reads without redundant network calls.

### 5. 🛡️ High Availability, Rate Limiting & Tagged Logging
- **Nginx Reverse Proxy & Load Balancer:** Distributes traffic across containerized API worker nodes (`api1`, `api2`) on port `8888`.
- **SlowAPI Rate Limiter:** Protects endpoints against brute-force and DDoS attacks.
- **Tagged Action Logs:** Uniform structured log tags for rapid observability (`[auth]`, `[scrap]`, `[cache]`, `[db]`, `[llm]`, `[ratelimit]`, `[schedule]`, `[api]`).

---

## 🛠️ Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Framework** | [FastAPI](https://fastapi.tiangolo.com/) | High-performance async Python web framework |
| **Language** | [Python 3.11+](https://www.python.org/) | Modern typing, PEP 621 packaging |
| **Database** | [PostgreSQL 16](https://www.postgresql.org/) & [SQLAlchemy 2.0](https://www.sqlalchemy.org/) | Relational storage and ORM |
| **LLM Gateway** | [LiteLLM](https://github.com/BerriAI/litellm) | Multi-provider unified LLM proxy with fallback support |
| **Computer Vision** | [PyTorch](https://pytorch.org/), [Torchvision](https://pytorch.org/vision/), [OpenCV](https://opencv.org/) | ResNet-50 deep learning model and image preprocessing |
| **Scheduler** | [APScheduler](https://apscheduler.readthedocs.io/) | Background cron jobs for periodic cache synchronization |
| **Security** | [Passlib (Bcrypt)](https://passlib.readthedocs.io/) & [PyJWT](https://pyjwt.readthedocs.io/) | Cryptographic hashing and JWT token handling |
| **Reverse Proxy** | [Nginx](https://nginx.org/) | Load balancing reverse proxy on port 8888 |
| **Packaging** | `pyproject.toml` (PEP 621) | Modern declarative project metadata and dependencies |

---

## 📁 Project Structure

```text
SkinSight/
├── core/                  # Application core (config, database, security, limiter, logger)
│   ├── config.py          # Pydantic BaseSettings environment configuration
│   ├── database.py        # SQLAlchemy engine, session maker, and auto-seeding
│   ├── limiter.py         # SlowAPI rate limiting configuration
│   ├── logger.py          # Structured tagged action logging
│   └── security.py        # Bcrypt password hashing & JWT token operations
├── models/                # SQLAlchemy ORM database models
│   ├── article.py         # NewsArticle and NewsArticleDetail
│   ├── education.py       # EducationArticle and EducationArticleDetail
│   ├── product.py         # Product catalog
│   └── user.py            # User account & role definitions
├── routers/               # API route definitions (versioned under /api/v1)
│   ├── admin.py           # Admin maintenance & manual sync triggers
│   ├── api.py             # Main API aggregation router & health check
│   ├── auth.py            # Authentication endpoints (register, login, me)
│   ├── educations.py      # Education topic feeds & lazy-cached detail
│   ├── news.py            # News feeds & lazy-cached detail
│   └── skincare.py        # Ingredient scanning, skin prediction, and recommender
├── schemas/               # Pydantic request/response validation models
├── scheduler/             # APScheduler background tasks for 24h periodic sync
├── services/              # Business logic layer (Auth, LLM, News, Education, Skincare)
├── helper/                # Legacy utilities and model prediction helpers
├── nginx/                 # Nginx load balancer configuration
│   └── nginx.conf         # Round-robin reverse proxy configuration
├── tests/                 # Pytest test suite
├── docker-compose.yml     # Multi-container orchestration (postgres, api1, api2, nginx)
├── dockerfile             # Multi-stage optimized application container build
├── pyproject.toml         # PEP 621 standardized packaging and dependencies
├── project.toml           # Project metadata alias
└── server.py              # FastAPI application entrypoint and lifespan lifecycle
```

---

## ⚙️ Configuration (`.env`)

Copy the template environment file:
```bash
cp .env.example .env
```

Review and adjust variables as needed:
```env
# Database Configuration (PostgreSQL)
DATABASE_URL=postgresql://postgres:postgrespassword@localhost:5432/skinsight_db

# Security & JWT
JWT_SECRET=your_super_secret_jwt_key_here_minimum_32_characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Default Admin Account (Auto-seeded on first launch)
ADMIN_EMAIL=admin@skinsight.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=Admin123!

# Allowed CORS Origins (comma-separated)
CORS_ORIGIN=http://localhost:3000,http://localhost:8888

# LiteLLM & AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL=gemini/gemini-2.5-flash
LLM_FALLBACKS=gemini/gemini-1.5-flash

# Rate Limiting
RATE_LIMIT_DEFAULT=60/minute
RATE_LIMIT_HEAVY=10/minute
```

---

## 🏃 Getting Started

### Option 1: Running with Docker Compose (Recommended)
Spawns PostgreSQL 16, two API application instances (`api1`, `api2`), and the Nginx load balancer:

```bash
docker compose up --build -d
```

Check cluster status:
```bash
docker compose ps
```

### Option 2: Running Locally
1. **Activate Virtual Environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install Dependencies:**
   ```bash
   pip install -e .
   ```

3. **Start the Application:**
   ```bash
   python server.py
   ```
   The local service will listen directly at `http://localhost:8000`.

---

## 📖 API Documentation & Swagger UI

Interactive documentation is automatically generated and accessible in the browser:

| Interface | URL (via Nginx Port 8888) | URL (Direct API Port 8000) | Description |
| :--- | :--- | :--- | :--- |
| **Swagger UI** | `http://localhost:8888/docs` | `http://localhost:8000/docs` | Interactive API explorer & testing tool |
| **Swagger Alias** | `http://localhost:8888/api/docs` | `http://localhost:8000/api/docs` | Convenience redirect to Swagger UI |
| **ReDoc** | `http://localhost:8888/redoc` | `http://localhost:8000/redoc` | Clean, reader-friendly documentation |
| **OpenAPI Spec** | `http://localhost:8888/openapi.json` | `http://localhost:8000/openapi.json` | Raw OpenAPI 3.1 JSON specification |

### 🔑 Using Swagger "Authorize" (Bearer JWT)
1. Execute `POST /api/v1/auth/login` with admin credentials (`admin@skinsight.com` / `Admin123!`).
2. Copy the resulting `access_token` from the JSON response.
3. Click the green **Authorize** padlock button in the top-right corner of Swagger UI.
4. Paste the token into the prompt and confirm.
5. All protected endpoints are immediately unlocked for in-browser execution.

---

## 📡 API Endpoints Overview

All operational endpoints are versioned with the `/api/v1/` prefix:

### 1. Authentication (`/api/v1/auth`)
- `POST /api/v1/auth/register` — Register a new user account.
- `POST /api/v1/auth/login` — Authenticate and obtain JWT Bearer access token.
- `GET /api/v1/auth/me` — Retrieve the profile of the currently authenticated user *(Requires Token)*.

### 2. Skincare Intelligence (`/api/v1/skincare`)
- `POST /api/v1/skincare/read-ingredients` — Extract and assess ingredient safety via **LiteLLM**.
- `POST /api/v1/skincare/predict-skin` — Classify facial skin type (`dry`, `normal`, `oily`) via **ResNet-50**.
- `POST /api/v1/skincare/recommendations` — Fetch product recommendations tailored to a specific skin type.

### 3. News & Education Caching (`/api/v1/news`, `/api/v1/educations`)
- `GET /api/v1/news` — Retrieve cached skincare news list (paginated, 24h background sync).
- `POST /api/v1/news/detail` — Retrieve full news article (1-time lazy cache into database).
- `GET /api/v1/educations` — Retrieve cached education topics (paginated, 24h background sync).
- `POST /api/v1/educations/detail` — Retrieve full educational guide (1-time lazy cache into database).

### 4. Administrator Operations (`/api/v1/admin`)
- `POST /api/v1/admin/sync/news` — Manually trigger news scraping & sync *(Requires 'admin' role)*.
- `POST /api/v1/admin/sync/educations` — Manually trigger education scraping & sync *(Requires 'admin' role)*.

### 5. Health Monitoring (`/api/v1/health`)
- `GET /api/v1/health` — Inspect service uptime, status, and application version.

---

## 🧪 Running Automated Tests

Run the complete test suite using `pytest`:

```bash
pytest -v
```

---

## 📄 License

This project is licensed under the MIT License.
