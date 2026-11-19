from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_search_service
from app.core.config import Settings, get_settings
from app.schemas import CompareResponse, SearchMode, SearchResponse
from app.services.search import SearchService

router = APIRouter(tags=["search"])

def _weights(settings: Settings, alpha: Optional[float], beta: Optional[float]):
    a = settings.default_alpha if alpha is None else alpha
    b = settings.default_beta if beta is None else beta
    if a == 0 and b == 0:
        raise HTTPException(422, "alpha and beta cannot both be zero.")
    return a, b

@router.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1, max_length=300, description="Search query"),
    mode: SearchMode = Query("entity", description="baseline = TF-IDF only; entity = text + entity fusion"),
    top_k: int = Query(10, ge=1, le=50),
    alpha: Optional[float] = Query(None, ge=0, description="Weight of text score"),
    beta: Optional[float] = Query(None, ge=0, description="Weight of entity score"),
    service: SearchService = Depends(get_search_service),
    settings: Settings = Depends(get_settings),
):
    a, b = _weights(settings, alpha, beta)
    return service.search(q, mode, top_k, a, b)

@router.get("/search/compare", response_model=CompareResponse)
def compare(
    q: str = Query(..., min_length=1, max_length=300),
    top_k: int = Query(10, ge=1, le=50),
    alpha: Optional[float] = Query(None, ge=0),
    beta: Optional[float] = Query(None, ge=0),
    service: SearchService = Depends(get_search_service),
    settings: Settings = Depends(get_settings),
):
    # Baseline and entity-aware results side by side (for the comparison UI)
    a, b = _weights(settings, alpha, beta)
    return {
        "baseline": service.search(q, "baseline", top_k, a, b),
        "entity": service.search(q, "entity", top_k, a, b),
    }
