from __future__ import annotations
import logging
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.router import api_router
from app.core import db
from app.core.config import get_settings
from app.services.search import IndexNotReadyError, SearchService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("app")

_init_lock = threading.Lock()


def ensure_initialized(app: FastAPI) -> SearchService:
    """
    Idempotent lazy initializer so the app works identically in both
    long-running Uvicorn (lifespan) and Vercel Python Serverless functions.
    """
    existing = getattr(app.state, "search_service", None)
    if existing is not None:
        return existing

    with _init_lock:
        existing = getattr(app.state, "search_service", None)
        if existing is not None:
            return existing

        settings = get_settings()
        try:
            db.init_pool(settings)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Database pool not configured (%s); serving from loaded index artifact until DATABASE_URL is set.",
                exc,
            )
        if not settings.admin_api_key:
            logger.warning("ADMIN_API_KEY is not set: admin/write endpoints are open (dev only).")

        service = SearchService(settings)
        service.try_load()
        app.state.search_service = service
        return service


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_initialized(app)
    yield
    db.close_pool()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", tags=["root"])
    async def root():
        return {
            "service": settings.app_name,
            "engine": "v5-from-scratch",
            "health": f"{settings.api_prefix}/health",
            "docs": "/docs",
        }

    @app.exception_handler(IndexNotReadyError)
    async def _index_not_ready(_: Request, exc: IndexNotReadyError):
        return JSONResponse(
            status_code=503,
            content={"detail": "Search index is not built. Call POST /api/v1/admin/index/rebuild."},
        )

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
