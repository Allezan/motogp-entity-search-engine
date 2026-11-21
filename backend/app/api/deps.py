from __future__ import annotations
import secrets
from typing import Optional
from fastapi import Depends, Header, HTTPException, Request, status
from app.core.config import Settings, get_settings
from app.services.search import SearchService


def get_search_service(request: Request) -> SearchService:
    service = getattr(request.app.state, "search_service", None)
    if service is None:
        from app.main import ensure_initialized
        service = ensure_initialized(request.app)
    return service


def require_admin(
    x_api_key: Optional[str] = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    # admin api key is optional; if not set, all requests are allowed
    if not settings.admin_api_key:
        return
    if not x_api_key or not secrets.compare_digest(x_api_key, settings.admin_api_key):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or missing X-API-Key.")
