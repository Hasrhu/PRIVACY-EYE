"""
Privacy Eye — FastAPI Backend Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import structlog

from app.core.config import settings
from app.core.logging import configure_logging
from app.database.session import engine
from app.database import models  # noqa: F401 — ensure models are registered
from app.api.v1 import router as api_v1_router
from app.core.middleware import RateLimitMiddleware, RequestIDMiddleware

configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup & shutdown."""
    logger.info("Privacy Eye API starting", version=settings.APP_VERSION, env=settings.APP_ENV)
    # Auto-create tables if they don't exist
    from app.database.session import Base, engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Warm up ML models on startup
    from app.services.ml_service import ml_service
    await ml_service.warmup()
    yield
    logger.info("Privacy Eye API shutting down")


app = FastAPI(
    title="Privacy Eye API",
    description=(
        "AI-powered digital authenticity and deepfake detection platform. "
        "Results are probabilistic indicators — not definitive conclusions."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    lifespan=lifespan,
)

# ── Middleware ──────────────────────────────────────────────────────────────
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware, calls=settings.RATE_LIMIT_PER_MINUTE, period=60)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # Restrict in production
)

# ── Routes ──────────────────────────────────────────────────────────────────
app.include_router(api_v1_router, prefix="/api/v1")


@app.get("/", tags=["Health"])
async def root():
    return {"service": "Privacy Eye API", "status": "operational", "version": settings.APP_VERSION}


@app.get("/api/v1/health", tags=["Health"])
async def health():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "env": settings.APP_ENV,
    }
