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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)