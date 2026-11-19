from fastapi import APIRouter, Depends
from app.api.deps import get_search_service
from app.core import db
from app.schemas import HealthResponse
from app.services.search import SearchService

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
def health(service: SearchService = Depends(get_search_service)):
    database_ok = db.ping()
    return HealthResponse(
        status="ok" if service.ready else "degraded",
        database="ok" if database_ok else "unavailable",
        index_ready=service.ready,
    )
