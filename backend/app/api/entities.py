from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_search_service
from app.core import db
from app.schemas import EntityOut, RecognizedEntity
from app.services import repository
from app.services.search import IndexNotReadyError, SearchService

router = APIRouter(prefix="/entities", tags=["entities"])

@router.get("", response_model=List[EntityOut])
def list_entities(category: Optional[str] = Query(None, description="Exact category value")):
    with db.get_conn() as conn:
        return repository.list_entities(conn, category)

@router.get("/recognize", response_model=List[RecognizedEntity])
def recognize(
    text: str = Query(..., min_length=1, max_length=2000),
    service: SearchService = Depends(get_search_service),
):
    # debugging
    if service.artifact is None:
        raise IndexNotReadyError("Index is not built yet.")
    dictionary = service.artifact.entity_dictionary
    out, seen = [], set()
    for m in dictionary.find_mentions(text):
        if m.entity_id in seen:
            continue
        seen.add(m.entity_id)
        info = dictionary.entities[m.entity_id]
        out.append(
            RecognizedEntity(
                entity_id=info.entity_id, name=info.name, category=info.category,
                matched_text=m.matched_text, ambiguous=m.weight < 1.0,
            )
        )
    return out
