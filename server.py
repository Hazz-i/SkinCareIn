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
    try:
        init_db()
    except Exception as e:
        log_action("db", f"Database init notice: {e}", level="warning")
    # Start 24h background sync scheduler
    try:
        start_scheduler()
    except Exception as e:
        log_action("schedule", f"Scheduler start notice: {e}", level="warning")
    yield
    # Shutdown
    log_action("api", "Stopping services...")
    stop_scheduler()

from fastapi.responses import RedirectResponse

openapi_tags = [
    {
        "name": "Authentication",
        "description": "User registration, login, and profile management with JWT Bearer authentication and Role-Based Access Control (RBAC: `admin` & `user`).",
    },
    {
        "name": "Skincare Analysis & Recommender",
        "description": "Ingredient extraction & safety analysis via **LiteLLM**, facial skin type classification via **ResNet-50**, and personalized catalog recommendations.",
    },
    {
        "name": "Skincare News",
        "description": "Curated skincare and dermatology news with PostgreSQL caching (24-hour periodic sync) and 1-time lazy detail scraping.",
    },
    {
        "name": "Skincare Educations",
        "description": "Dermatological education guides and active ingredient topics with PostgreSQL caching and on-demand lazy scraping.",
    },
    {
        "name": "UV Index",
        "description": "Real-time UV Index reading and 5-day daily/hourly forecasts powered by **NOAA** via [uvindexapi.com](https://uvindexapi.com), with WHO risk levels, skincare guidance, and PostgreSQL caching (24-hour TTL). Data licensed under **CC BY-SA 4.0**.",
    },
    {
        "name": "Admin Operations",
        "description": "Administrative maintenance endpoints to manually trigger article resynchronization (Requires `admin` role).",
    },
    {
        "name": "Health",
        "description": "Health check endpoint for Nginx reverse proxy load balancer and uptime monitoring.",
    },
]

app = FastAPI(
    title=f"{settings.PROJECT_NAME}",
    description="""
## 🌿 SkinSight Skincare Intelligence API

Interactive OpenAPI / Swagger UI documentation for the **SkinSight** backend services.

### 🚀 Key Architectural Features:
- **JWT & Role-Based Access Control**: Secure authentication with `admin` and `user` privilege levels.
- **LiteLLM Multi-Model Orchestration**: Vision and LLM analysis with automated model fallback (Gemini 2.5 Flash -> Gemini 1.5 Flash).
- **Two-Tier Database Caching**: Article list feeds synced every 24 hours into PostgreSQL; full article content scraped once on-demand and cached permanently.
- **High-Availability Load Balancer**: Nginx reverse proxy on port `8888` distributing traffic across containerized API workers.
- **SlowAPI Rate Limiting**: Built-in rate limiting per IP to protect services from abusive traffic.

---
### 🔐 How to Authorize in Swagger UI:
1. Navigate to `POST /api/v1/auth/login` under the **Authentication** section.
2. Provide valid credentials (e.g., default admin: `admin@skinsight.com` / `Admin123!`).
3. Copy the `access_token` string from the JSON response.
4. Click the green **Authorize** padlock button at the top right of this page.
5. Paste the access token into the input box and click **Authorize**.
6. All protected user and admin endpoints are now unlocked for testing directly in this UI!
    """,
    version=settings.VERSION,
    openapi_tags=openapi_tags,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
        "docExpansion": "list",
        "tryItOutEnabled": True,
    },
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
    return {
        "message": "SkinSight API is running",
        "version": settings.VERSION,
        "docs": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json"
        }
    }

# Swagger UI redirect aliases
@app.get("/api/docs", include_in_schema=False)
@app.get("/api/v1/docs", include_in_schema=False)
@app.get("/swagger", include_in_schema=False)
def redirect_to_docs():
    return RedirectResponse(url="/docs")

# Mount all /api/v1 routes
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)