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
        "description": "Registrasi, login, dan manajemen profil pengguna dengan otentikasi JWT Bearer token dan Role-Based Access Control (RBAC: `admin` & `user`).",
    },
    {
        "name": "Skincare Analysis & Recommender",
        "description": "Analisis komposisi bahan skincare via **LiteLLM**, prediksi tipe kulit wajah via **ResNet-50**, dan rekomendasi katalog produk.",
    },
    {
        "name": "Skincare News",
        "description": "Daftar artikel berita kecantikan dengan auto-caching PostgreSQL (sinkronisasi harian 24 jam) dan lazy detail scraping 1x.",
    },
    {
        "name": "Skincare Educations",
        "description": "Daftar artikel edukasi dermatologi dan bahan aktif dengan auto-caching PostgreSQL dan lazy detail scraping 1x.",
    },
    {
        "name": "Admin Operations",
        "description": "Operasi khusus Administrator untuk memicu re-sinkronisasi scraping artikel secara manual (Memerlukan role `admin`).",
    },
    {
        "name": "Health",
        "description": "Health check endpoint untuk load balancer Nginx dan pemantauan status service.",
    },
]

app = FastAPI(
    title=f"{settings.PROJECT_NAME}",
    description="""
## 🌿 SkinSight Skincare Intelligence API

Dokumentasi interaktif OpenAPI / Swagger UI untuk backend **SkinSight**.

### 🚀 Fitur Arsitektur:
- **JWT & RBAC**: Autentikasi token JWT dengan role `admin` dan `user`.
- **LiteLLM**: Integrasi multi-model AI vision dan LLM dengan auto-fallback.
- **Lazy & Cron Caching**: Data berita & edukasi di-cache dalam PostgreSQL, disinkronisasi harian (24 jam), dan detail artikel di-scrape 1x saat pertama kali diakses.
- **Nginx Load Balancer**: Akses melalui reverse proxy port `8888` terdistribusi ke multiple API node (`api1`, `api2`).
- **SlowAPI Rate Limiting**: Proteksi endpoint dari request abuse.

---
### 🔐 Cara Menggunakan Fitur Authorize di Swagger UI:
1. Buka endpoint `POST /api/v1/auth/login` di bawah tag **Authentication**.
2. Masukkan username/email dan password (contoh admin default: `admin@skinsight.com` / `Admin123!`).
3. Salin nilai `access_token` dari respons JSON.
4. Klik tombol **Authorize** (ikon gembok) di sudut kanan atas halaman ini.
5. Masukkan access token pada kolom yang tersedia lalu klik **Authorize**.
6. Anda sekarang dapat langsung mengeksekusi endpoint khusus admin atau user terproteksi!
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