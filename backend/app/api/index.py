from fastapi import APIRouter, Depends, HTTPException
from app.api.deps import get_search_service, require_admin
from app.core.config import Settings, get_settings
from app.schemas import IndexStatus
from app.services.indexer import IndexBuildError, rebuild_from_database
from app.services.search import SearchService

router = APIRouter(tags=["index"])

def _status(service: SearchService) -> IndexStatus:
    if service.artifact is None:
        return IndexStatus(ready=False)
    return IndexStatus(ready=True, **service.artifact.summary())

@router.get("/index/status", response_model=IndexStatus)
def index_status(service: SearchService = Depends(get_search_service)):
    return _status(service)

@router.post("/admin/index/rebuild", response_model=IndexStatus, dependencies=[Depends(require_admin)])
def rebuild_index(
    service: SearchService = Depends(get_search_service),
    settings: Settings = Depends(get_settings),
):
    # Re-read documents + entity dictionary from Neon, rebuild TF-IDF and entity index, hot-reload.
    try:
        rebuild_from_database(settings, service.preprocessor, service)
    except IndexBuildError as exc:
        raise HTTPException(409, str(exc)) from exc
    return _status(service)
