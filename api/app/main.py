"""
CIOTX API — FastAPI Application
Entry point with CORS, security headers, rate limiting, and all routes.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import settings
from app.database import init_db
from app.routes import auth, billing, github, projects, scans, vulns, webhooks


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    await init_db()
    yield


limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT])

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEV_MODE else None,
    redoc_url=None,
)

# ── Rate Limiting ────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── CORS ─────────────────────────────────────
# Derive allowed origins from DASHBOARD_URL automatically.
# Covers: configured domain (http + https), localhost dev, and direct port access.
def _build_cors_origins() -> list[str]:
    origins = set()
    base = settings.DASHBOARD_URL.rstrip("/")
    origins.add(base)
    # Always allow both http and https variants of the configured domain
    if base.startswith("https://"):
        origins.add(base.replace("https://", "http://"))
    elif base.startswith("http://"):
        origins.add(base.replace("http://", "https://"))
    # Strip port if present to also allow the bare domain
    from urllib.parse import urlparse
    parsed = urlparse(base)
    bare = f"{parsed.scheme}://{parsed.hostname}"
    origins.add(bare)
    origins.add(bare.replace("https://", "http://"))
    origins.add(bare.replace("http://", "https://"))
    # Direct container/port access (for dev and initial setup)
    origins.add(f"http://{parsed.hostname}:3000")
    origins.add(f"https://{parsed.hostname}:3000")
    # Always allow localhost for local dev
    origins.add("http://localhost:3000")
    origins.add("http://127.0.0.1:3000")
    return list(origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_build_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Internal-Key"],
    max_age=86400,
)

# ── Security Headers ─────────────────────────
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-XSS-Protection"] = "0"
    if not settings.DEV_MODE:
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https://avatars.githubusercontent.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
    return response


# ── Routes ───────────────────────────────────
app.include_router(auth.router, prefix="/v1")
app.include_router(billing.router, prefix="/v1")
app.include_router(projects.router, prefix="/v1")
app.include_router(scans.router, prefix="/v1")
app.include_router(vulns.router, prefix="/v1")
app.include_router(github.router, prefix="/v1")
app.include_router(webhooks.router, prefix="/v1")


# ── Health Check ─────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION, "dev_mode": settings.DEV_MODE}


@app.get("/v1/health")
async def health_v1():
    return {"status": "ok", "version": settings.APP_VERSION, "dev_mode": settings.DEV_MODE}


# ── Exception Handler ────────────────────────
import logging
import traceback

logger = logging.getLogger("ciotx")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred.",
            "detail": str(exc) if settings.DEV_MODE else None,
        },
    )
