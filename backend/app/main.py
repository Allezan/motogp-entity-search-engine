from __future__ import annotations
import logging
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    try:
        db.init_pool(settings)
    except Exception:  # noqa: BLE001  (search still works from the artifact)
        logger.exception("Database pool could not be initialised; DB-backed endpoints will fail.")
    if not settings.admin_api_key:
        logger.warning("ADMIN_API_KEY is not set: admin/write endpoints are open (dev only).")

    service = SearchService(settings)
    service.try_load()
    app.state.search_service = service
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

    @app.exception_handler(IndexNotReadyError)
    async def _index_not_ready(_: Request, exc: IndexNotReadyError):
        return JSONResponse(
            status_code=503,
            content={"detail": "Search index is not built. Call POST /api/v1/admin/index/rebuild."},
        )

    app.include_router(api_router, prefix=settings.api_prefix)
    return app

app = create_app()
