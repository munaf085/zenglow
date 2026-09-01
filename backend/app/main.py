"""
Zenglow FastAPI application entry point.
"""
import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    PaymentError,
    RateLimitError,
    SlotUnavailableError,
    TenantIsolationError,
    ValidationError,
    ZenglowException,
)
from app.core.logging import setup_logging

setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("zenglow_startup", version=settings.APP_VERSION, env=settings.ENVIRONMENT)
    yield
    logger.info("zenglow_shutdown")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Zenglow — All-in-one SaaS platform for salons, spas & wellness businesses",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_url="/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request ID Middleware ─────────────────────────────────────────────────────
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response


# ── Exception Handlers ────────────────────────────────────────────────────────
def _error_response(status_code: int, code: str, message: str, details: dict = None):
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details or {}}},
    )


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return _error_response(status.HTTP_404_NOT_FOUND, exc.code, exc.message)


@app.exception_handler(AuthenticationError)
async def auth_error_handler(request: Request, exc: AuthenticationError):
    return _error_response(status.HTTP_401_UNAUTHORIZED, exc.code, exc.message)


@app.exception_handler(AuthorizationError)
async def authz_error_handler(request: Request, exc: AuthorizationError):
    return _error_response(status.HTTP_403_FORBIDDEN, exc.code, exc.message)


@app.exception_handler(TenantIsolationError)
async def tenant_error_handler(request: Request, exc: TenantIsolationError):
    # Return 404 to avoid leaking resource existence
    return _error_response(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Resource not found")


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    return _error_response(status.HTTP_409_CONFLICT, exc.code, exc.message)


@app.exception_handler(ValidationError)
async def validation_handler(request: Request, exc: ValidationError):
    return _error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, exc.code, exc.message, exc.details)


@app.exception_handler(SlotUnavailableError)
async def slot_handler(request: Request, exc: SlotUnavailableError):
    return _error_response(status.HTTP_409_CONFLICT, exc.code, exc.message)


@app.exception_handler(PaymentError)
async def payment_handler(request: Request, exc: PaymentError):
    return _error_response(status.HTTP_402_PAYMENT_REQUIRED, exc.code, exc.message)


@app.exception_handler(BusinessRuleError)
async def business_rule_handler(request: Request, exc: BusinessRuleError):
    return _error_response(status.HTTP_400_BAD_REQUEST, exc.code, exc.message)


@app.exception_handler(RateLimitError)
async def rate_limit_handler(request: Request, exc: RateLimitError):
    return _error_response(status.HTTP_429_TOO_MANY_REQUESTS, exc.code, exc.message)


@app.exception_handler(ZenglowException)
async def zenglow_exception_handler(request: Request, exc: ZenglowException):
    return _error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, exc.code, exc.message)


# ── Routers ───────────────────────────────────────────────────────────────────
from app.api.v1 import (  # noqa
    auth, businesses, staff, services,
    bookings, payments, admin, customers, reviews, users, uploads, verification,
    inventory, memberships, packages, gift_cards, pos, reports, subscriptions,
)

PREFIX = settings.API_V1_PREFIX

app.include_router(auth.router, prefix=PREFIX)
app.include_router(businesses.router, prefix=PREFIX)
app.include_router(staff.router, prefix=PREFIX)
app.include_router(services.router, prefix=PREFIX)
app.include_router(bookings.router, prefix=PREFIX)
app.include_router(payments.router, prefix=PREFIX)
app.include_router(customers.router, prefix=PREFIX)
app.include_router(reviews.router, prefix=PREFIX)
app.include_router(users.router, prefix=PREFIX)
app.include_router(uploads.router, prefix=PREFIX)
app.include_router(verification.router, prefix=PREFIX)
app.include_router(inventory.router, prefix=PREFIX)
app.include_router(memberships.router, prefix=PREFIX)
app.include_router(packages.router, prefix=PREFIX)
app.include_router(gift_cards.router, prefix=PREFIX)
app.include_router(pos.router, prefix=PREFIX)
app.include_router(reports.router, prefix=PREFIX)
app.include_router(subscriptions.router, prefix=PREFIX)
app.include_router(admin.router, prefix=PREFIX)

# ── Static file serving for local storage uploads ─────────────────────────────
import os
from fastapi.staticfiles import StaticFiles

uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(uploads_dir, exist_ok=True)
try:
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")
except Exception:
    pass  # uploads dir may be empty on first start — that is fine


# ── Health Endpoints ──────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "service": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/ready", tags=["health"])
async def readiness():
    """Check that DB and Redis are reachable."""
    checks = {}
    try:
        from app.db.session import engine
        async with engine.connect() as conn:
            await conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    try:
        from app.db.redis import get_redis_client
        r = await get_redis_client()
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"

    all_ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "ready" if all_ok else "degraded", "checks": checks},
    )


@app.get("/live", tags=["health"])
async def liveness():
    return {"status": "alive"}
