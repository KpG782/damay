"""FastAPI application entrypoint.

Run:
    uv run uvicorn main:app --reload

OpenAPI: /docs  /redoc
Health:  /healthz
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from damay_api import __version__
from damay_api.clients.stellar import get_stellar, reset_stellar_singleton
from damay_api.clients.supabase import get_supabase, reset_supabase_singleton
from damay_api.clients.twilio import get_twilio, reset_twilio_singleton
from damay_api.config import get_settings
from damay_api.middleware import (
    IdempotencyMiddleware,
    LoggingMiddleware,
    RequestIdMiddleware,
    configure_logging,
)
from damay_api.middleware.idempotency import InMemoryIdempotencyStore
from damay_api.middleware.logging import get_logger
from damay_api.middleware.rate_limit import limiter, rate_limit_handler
from damay_api.middleware.request_id import current_request_id
from damay_api.routers import (
    contributions as contributions_router,
)
from damay_api.routers import (
    health as health_router,
)
from damay_api.routers import (
    members as members_router,
)
from damay_api.routers import (
    reputation as reputation_router,
)
from damay_api.routers import (
    rounds as rounds_router,
)

# WhatsApp router is owned by the whatsapp-integrator agent.
# Plug it in here once it's ready — do not edit the webhooks.py file itself.
try:
    from damay_api.routers import webhooks as webhooks_router
except Exception:  # pragma: no cover - integrator may not have finalized yet
    webhooks_router = None  # type: ignore[assignment]


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(level=settings.log_level)
    log = get_logger("damay.lifespan")
    log.info("startup", version=__version__, env=settings.node_env)

    supabase = await get_supabase(settings)
    stellar = get_stellar(settings)
    twilio = get_twilio(settings)

    # Schedule background workers when not in test mode.
    scheduler = None
    if settings.node_env != "test":
        from damay_api.workers.scheduler import WorkerScheduler

        scheduler = WorkerScheduler(settings, supabase, stellar)
        scheduler.start()

    app.state.settings = settings
    app.state.supabase = supabase
    app.state.stellar = stellar
    app.state.twilio = twilio
    app.state.scheduler = scheduler

    try:
        yield
    finally:
        log.info("shutdown")
        if scheduler is not None:
            await scheduler.shutdown()
        await supabase.aclose()
        await stellar.aclose()
        await twilio.aclose()
        reset_supabase_singleton()
        reset_stellar_singleton()
        reset_twilio_singleton()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(level=settings.log_level)

    app = FastAPI(
        title="DAMAY API",
        version=__version__,
        description=(
            "Backend gateway for the DAMAY paluwagan protocol. "
            "Organizer endpoints + Stellar/Twilio async glue."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ---- Middleware (added bottom-up; outermost runs first) -----------------
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.app_url] if settings.app_url else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(
        IdempotencyMiddleware,
        store=InMemoryIdempotencyStore(),
    )
    app.add_middleware(RequestIdMiddleware)

    # ---- Rate limiter -------------------------------------------------------
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

    # ---- Routers ------------------------------------------------------------
    app.include_router(health_router.router)
    app.include_router(rounds_router.router)
    app.include_router(members_router.router)
    app.include_router(contributions_router.router)
    app.include_router(reputation_router.router)

    # NOTE: whatsapp-integrator OWNS this router. Their module declares its
    # own paths (`/webhooks/twilio` + `/dev/simulate-message`). We just wire.
    if webhooks_router is not None:
        try:
            app.include_router(webhooks_router.router, prefix="/v1")
        except Exception as e:  # pragma: no cover
            get_logger("damay.lifespan").warning(
                "webhooks_include_failed", error=str(e)
            )

    # ---- Exception handlers (envelope per ARCHITECTURE.md §2.1) -------------
    @app.exception_handler(HTTPException)
    async def _http_exc_handler(request: Request, exc: HTTPException) -> JSONResponse:
        detail = exc.detail
        if isinstance(detail, dict) and "code" in detail:
            code = detail["code"]
            message = detail.get("message", "")
            extra = {k: v for k, v in detail.items() if k not in {"code", "message"}}
        else:
            code = _default_code_for_status(exc.status_code)
            message = str(detail) if detail else ""
            extra = {}
        body = {
            "error": {
                "code": code,
                "message": message,
                "request_id": current_request_id(),
            }
        }
        if extra:
            body["error"]["details"] = extra
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request payload failed validation.",
                    "request_id": current_request_id(),
                    "details": {"errors": exc.errors()},
                }
            },
        )

    @app.exception_handler(Exception)
    async def _generic_exc_handler(request: Request, exc: Exception) -> JSONResponse:
        get_logger("damay.error").error("unhandled_exception", error=str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred.",
                    "request_id": current_request_id(),
                }
            },
        )

    return app


def _default_code_for_status(code: int) -> str:
    return {
        400: "VALIDATION_ERROR",
        401: "UNAUTHENTICATED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        429: "RATE_LIMITED",
        503: "UPSTREAM_UNAVAILABLE",
    }.get(code, "INTERNAL_ERROR")


app = create_app()
