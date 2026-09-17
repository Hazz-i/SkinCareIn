# 🌿 SkinSight - AI-Powered Skincare & Dermatological Intelligence API

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Scrapling](https://img.shields.io/badge/Scrapling-0.4+-FF5722.svg?logo=python&logoColor=white)](https://github.com/d4vinci/Scrapling)
[![LiteLLM](https://img.shields.io/badge/LiteLLM-Multi--Model-purple.svg)](https://github.com/BerriAI/litellm)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**SkinSight** is an enterprise-grade backend platform providing intelligent skincare analysis, deep-learning-based facial skin classification (ResNet-50), multi-model ingredient safety analysis via **LiteLLM**, web scraping powered by **Scrapling**, two-tier caching with **PostgreSQL**, robust **Role-Based Access Control (RBAC)**, and high-availability traffic distribution using an **Nginx Load Balancer**.

---

## 🚀 Key Features

### 1. 🔐 Authentication & RBAC (Role-Based Access Control)
- **Bcrypt Password Hashing & JWT Bearer Tokens:** Cryptographically secure token signing and verification.
- **Hierarchical Role System:** Distinguishes between standard `user` and privileged `admin` capabilities.
- **Auto-Seeded Administrator:** Seamless bootstrap of a default administrator account on application startup (`admin@skinsight.com` / `Admin123!`).

### 2. 🧠 Multi-Model AI Vision & OCR via LiteLLM
- **Ingredient Extraction & Safety Analysis:** Analyzes product packaging images to extract active ingredients and evaluate risk profiles tailored to specific skin types.
- **Automated Fallback Orchestration:** Seamless fallback handling across models (Primary: `gemini/gemini-2.5-flash`, Fallback: `gemini/gemini-1.5-flash`).

### 3. 🔬 Deep Learning Skin Type Classification
- **ResNet-50 Convolutional Network:** Classifies facial photographs into dermatological categories (`dry`, `normal`, `oily`).
- **Curated Recommendations:** Recommends relevant skincare products matching the detected skin profile.

### 4. ⚡ Two-Tier Caching & Modern Web Scraping (Scrapling)
- **Powered by Scrapling:** High-performance web scraping engine equipped with intelligent CSS/XPath selectors and automatic HTML-to-Markdown conversion.
- **Education Provider ([Lab Muffin Beauty Science](https://labmuffin.com/)):** Scrapes cosmetic science articles with full multi-page pagination support (`/page/{n}/`).
- **News & Encyclopedia Provider ([BeautyJournal Beauty A-Z](https://www.beautyjournal.id/beauty-az)):** Ingests skincare news & ingredient encyclopedia items supporting its **infinite scroll** mechanism via `skip` & `limit` query parameters.
- **24-Hour Background Periodic Sync:** Topic feeds are cached in PostgreSQL and refreshed daily in the background via **APScheduler**.
- **1-Time Lazy Detail Caching:** Full article content is scraped once on initial access, permanently stored in PostgreSQL, and served instantaneously on subsequent reads.

### 5. 🛡️ High Availability, Rate Limiting & Tagged Logging
- **Nginx Reverse Proxy & Load Balancer:** Distributes incoming traffic across containerized API worker nodes (`api1`, `api2`) on port `8888`.
- **SlowAPI Rate Limiter:** Protects endpoints against brute-force and abuse.
- **Uniform Tagged Logging:** Structured log tags for rapid observability (`[auth]`, `[scrap]`, `[cache]`, `[db]`, `[llm]`, `[ratelimit]`, `[schedule]`, `[api]`).

---

## 🛠️ Tech Stack

| Component | Technology | Description |
| :--- | :--- | :--- |
| **Framework** | [FastAPI](https://fastapi.tiangolo.com/) | High-performance async Python web framework |
| **Language** | [Python 3.11+](https://www.python.org/) | Modern typing, PEP 621 packaging |
| **Database** | [PostgreSQL 16](https://www.postgresql.org/) & [SQLAlchemy 2.0](https://www.sqlalchemy.org/) | Relational database storage and ORM |
| **Scraping Engine** | [Scrapling](https://github.com/d4vinci/Scrapling) | Fast scraper with anti-bot bypass & adaptive selectors |
| **LLM Gateway** | [LiteLLM](https://github.com/BerriAI/litellm) | Multi-provider unified LLM proxy with fallback support |
| **Computer Vision** | [PyTorch](https://pytorch.org/), [Torchvision](https://pytorch.org/vision/), [OpenCV](https://opencv.org/) | ResNet-50 deep learning model and image preprocessing |
| **Scheduler** | [APScheduler](https://apscheduler.readthedocs.io/) | Background cron jobs for 24-hour cache synchronization |
| **Security** | [Passlib (Bcrypt)](https://passlib.readthedocs.io/) & [PyJWT](https://pyjwt.readthedocs.io/) | Password hashing and JWT Bearer token management |
| **Reverse Proxy** | [Nginx](https://nginx.org/) | Load balancing reverse proxy on port 8888 |
| **Packaging** | `pyproject.toml` (PEP 621) | Declarative project metadata and dependency specification |

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
├── helper/                # Scrapling scrapers & computer vision helpers
│   ├── educations.py      # Lab Muffin scraper with multi-page pagination
│   ├── news.py            # BeautyJournal scraper with infinite scroll
│   ├── functions.py       # ResNet-50 classification & image processing
│   └── ingredients.py     # Ingredient safety reference lists
├── nginx/                 # Nginx load balancer configuration
│   └── nginx.conf         # Round-robin reverse proxy configuration
├── tests/                 # Automated test suite
│   ├── test_scrapling_scrapers.py # Unit tests for LabMuffin & BeautyJournal scrapers
│   ├── test_education_service.py  # Education caching tests
│   ├── test_news_service.py       # News caching tests
│   └── ...                        # Integration, auth, and database tests
├── docker-compose.yml     # Multi-container orchestration (postgres, api1, api2, nginx)
├── dockerfile             # Multi-stage optimized application container build
├── pyproject.toml         # PEP 621 standardized packaging and dependencies
├── project.toml           # Project metadata alias
├── seed_db.py             # Script to seed product dataset into database
└── server.py              # FastAPI application entrypoint and lifespan lifecycle
```

---

## ⚙️ Configuration (`.env`)

Create your local `.env` configuration file from the provided example:

```bash
cp .env.example .env
```

### Environment Variables Reference

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://postgres:postgrespassword@localhost:5432/skinsight_db` | PostgreSQL connection string |
| `JWT_SECRET` | `your_super_secret_jwt_key_here_minimum_32_characters` | Secret key for signing JWT tokens |
| `JWT_ALGORITHM` | `HS256` | Algorithm used for JWT encoding |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | Token expiration duration in minutes (24 hours) |
| `ADMIN_EMAIL` | `admin@skinsight.com` | Email of the default administrator account |
| `ADMIN_USERNAME` | `admin` | Username of the default administrator account |
| `ADMIN_PASSWORD` | `Admin123!` | Password of the default administrator account |
| `CORS_ORIGIN` | `http://localhost:3000,http://localhost:8888` | Comma-separated list of allowed CORS origins |
| `GEMINI_API_KEY` | `your_gemini_api_key_here` | Google Gemini API key for LiteLLM Vision / OCR |
| `LLM_MODEL` | `gemini/gemini-2.5-flash` | Primary vision LLM model |
| `LLM_FALLBACKS` | `gemini/gemini-1.5-flash` | Comma-separated fallback models |
| `RATE_LIMIT_DEFAULT` | `60/minute` | Default endpoint rate limit |
| `RATE_LIMIT_HEAVY` | `10/minute` | Strict rate limit for compute-heavy endpoints |

---

## 🏃 How to Run the Application

You can run SkinSight using **Docker Compose** (recommended for production and evaluation) or **Locally** using Python.

### Option 1: Running with Docker Compose (Recommended)

Docker Compose starts a complete cluster: **PostgreSQL 16**, two load-balanced API application instances (**`api1`**, **`api2`**), and the **Nginx Load Balancer**.

1. **Build and start the cluster:**
   ```bash
   docker compose up --build -d
   ```

2. **Verify container status:**
   ```bash
   docker compose ps
   ```
   You should see `skinsight_postgres`, `api1`, `api2`, and `skinsight_load_balancer` in healthy running states.

3. **Stream application logs:**
   ```bash
   docker compose logs -f
   ```

4. **Access the application:**
   - **Load-Balanced API & Swagger UI:** [http://localhost:8888/docs](http://localhost:8888/docs)
   - **Health Check:** [http://localhost:8888/api/v1/health](http://localhost:8888/api/v1/health)

5. **Stop the cluster:**
   ```bash
   docker compose down
   ```

---

### Option 2: Running Locally with `uv` (Fastest Python Tooling)

If you have [uv](https://github.com/astral-sh/uv) installed, setup takes just seconds:

1. **Create and activate a virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     uv venv
     .venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS:**
     ```bash
     uv venv
     source .venv/bin/activate
     ```

2. **Install dependencies in editable mode:**
   ```bash
   uv pip install -e ".[dev]"
   ```

3. **Start PostgreSQL:**
   Ensure a local PostgreSQL instance is running, or start a lightweight Docker container for the database:
   ```bash
   docker run -d --name skinsight_postgres -e POSTGRES_DB=skinsight_db -e POSTGRES_PASSWORD=postgrespassword -p 5432:5432 postgres:16-alpine
   ```

4. **Start the FastAPI server:**
   ```bash
   python server.py
   ```
   The application will listen directly at [http://localhost:8000](http://localhost:8000).

---

### Option 3: Running Locally with Standard Python & `pip`

1. **Create and activate virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS:**
     ```bash
     python -m venv .venv
     source .venv/bin/activate
     ```

2. **Upgrade pip and install project dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -e ".[dev]"
   ```

3. **Run the server:**
   ```bash
   python server.py
   ```

---

## 🗄️ Database Initialization & Dataset Seeding

1. **Automatic Database Bootstrap:**
   On application startup (`server.py` lifespan lifecycle), SQLAlchemy automatically creates all necessary database tables (`users`, `news_articles`, `news_article_details`, `education_articles`, `education_article_details`, `products`). The default administrator account (`admin@skinsight.com`) is auto-seeded if not already present.

2. **Product Catalog Dataset Seeding (Optional):**
   To populate the `products` table with skincare catalog items from `processed_data.csv`:
   ```bash
   python seed_db.py
   ```

---

## 📖 API Documentation & Swagger UI

SkinSight comes with interactive OpenAPI documentation accessible in any web browser:

| Documentation Interface | Load-Balanced URL (Port 8888) | Direct API URL (Port 8000) | Description |
| :--- | :--- | :--- | :--- |
| **Swagger UI** | [http://localhost:8888/docs](http://localhost:8888/docs) | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive testing console |
| **Swagger Alias** | [http://localhost:8888/api/docs](http://localhost:8888/api/docs) | [http://localhost:8000/api/docs](http://localhost:8000/api/docs) | Convenience redirect |
| **ReDoc** | [http://localhost:8888/redoc](http://localhost:8888/redoc) | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Clean readable documentation |
| **OpenAPI Schema** | [http://localhost:8888/openapi.json](http://localhost:8888/openapi.json) | [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json) | OpenAPI 3.1 specification JSON |

### 🔑 How to Authorize in Swagger UI (Bearer JWT)

1. Open Swagger UI at [http://localhost:8888/docs](http://localhost:8888/docs) (or `http://localhost:8000/docs`).
2. Expand `POST /api/v1/auth/login`, click **Try it out**, and authenticate:
   ```json
   {
     "email": "admin@skinsight.com",
     "password": "Admin123!"
   }
   ```
3. Copy the `access_token` value from the JSON response.
4. Scroll to the top of the Swagger page and click the green **Authorize 🔓** button.
5. Enter the token in the format: `Bearer <your_access_token>` (or simply paste the token).
6. Click **Authorize**. All protected endpoints (e.g., `/api/v1/auth/me`, `/api/v1/admin/*`) are now unlocked for testing directly in the browser.

---

## 📡 API Endpoints Reference

All endpoints are organized under `/api/v1/`:

### 1. Authentication (`/api/v1/auth`)
- `POST /api/v1/auth/register` — Register a new standard user account.
- `POST /api/v1/auth/login` — Authenticate and receive a JWT Bearer access token.
- `GET /api/v1/auth/me` — Retrieve current authenticated user profile *(Requires Token)*.

### 2. Skincare Intelligence (`/api/v1/skincare`)
- `POST /api/v1/skincare/read-ingredients` — Extract and assess skincare ingredients from product images via **LiteLLM**.
- `POST /api/v1/skincare/predict-skin` — Classify skin condition (`dry`, `normal`, `oily`) from facial photos via **ResNet-50**.
- `POST /api/v1/skincare/recommendations` — Query product recommendations matching a specified skin type.

### 3. News & Education Caching (`/api/v1/news`, `/api/v1/educations`)
- `GET /api/v1/news` — Retrieve cached BeautyJournal news & beauty A-Z items (supports infinite scroll pagination via `page`, refreshed daily).
- `POST /api/v1/news/detail` — Retrieve full BeautyJournal article/glossary detail (scraped once, permanently cached in PostgreSQL).
- `GET /api/v1/educations` — Retrieve cached Lab Muffin science education list (supports multi-page pagination via `page`, refreshed daily).
- `POST /api/v1/educations/detail` — Retrieve full Lab Muffin article formatted in clean Markdown (lazy cached in PostgreSQL).

### 4. Administrator Operations (`/api/v1/admin`)
- `POST /api/v1/admin/sync/news` — Manually trigger background scraping & cache update for news *(Requires 'admin' role)*.
- `POST /api/v1/admin/sync/educations` — Manually trigger background scraping & cache update for education *(Requires 'admin' role)*.

### 5. Health Check (`/api/v1/health`)
- `GET /api/v1/health` — Returns system health, uptime, and version status.

---

## 🧪 Automated Testing

SkinSight includes a comprehensive test suite built with **pytest**.

1. **Run the full test suite:**
   ```bash
   pytest -v
   ```
   Or using python:
   ```bash
   python -m pytest -v
   ```

2. **Run the Scrapling scrapers test suite:**
   ```bash
   pytest tests/test_scrapling_scrapers.py -v
   ```

3. **Run caching service tests:**
   ```bash
   pytest tests/test_education_service.py tests/test_news_service.py -v
   ```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
