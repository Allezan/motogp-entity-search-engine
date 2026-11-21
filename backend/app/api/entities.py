from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_search_service
from app.core import db
from app.schemas import EntityDetailOut, EntityOut, RecognizedEntity
from app.services import repository
from app.services.search import IndexNotReadyError, SearchService

router = APIRouter(prefix="/entities", tags=["entities"])


def _list_from_artifact(service: SearchService, category: Optional[str]) -> List[dict]:
    art = service.artifact
    if art is None:
        raise HTTPException(503, "Database unavailable and search index is not loaded.")
    cat_low = category.strip().lower() if category else None
    out = []
    for info in art.entity_dictionary.entities.values():
        if cat_low and (info.category or "").lower() != cat_low:
            continue
        out.append(
            {
                "entity_id": info.entity_id,
                "name": info.name,
                "category": info.category,
                "description": info.description,
                "source_url": info.source_url,
                "verification_status": info.verification_status,
                "aliases": list(info.aliases),
                "document_count": art.entity_doc_counts.get(info.entity_id, 0),
            }
        )
    out.sort(key=lambda e: (e["category"] or "", e["name"]))
    return out


def _detail_from_artifact(service: SearchService, entity_id: str) -> dict:
    art = service.artifact
    if art is None:
        raise HTTPException(503, "Database unavailable and search index is not loaded.")
    info = art.entity_dictionary.entities.get(entity_id)
    if info is None:
        raise HTTPException(404, "Entity not found.")
    docs = []
    for idx, did in enumerate(art.doc_ids):
        cnt = art.doc_entity_counts.get(did, {}).get(entity_id, 0)
        if cnt >= 1:
            meta = art.doc_meta[idx]
            docs.append(
                {
                    "doc_id": did,
                    "title": meta["title"],
                    "media": meta.get("media"),
                    "published_at": meta.get("published_at"),
                    "url": meta.get("url"),
                    "mention_count": int(cnt),
                }
            )
    docs.sort(key=lambda d: (-d["mention_count"], d["doc_id"]))
    return {
        "entity_id": info.entity_id,
        "name": info.name,
        "category": info.category,
        "description": info.description,
        "source_url": info.source_url,
        "verification_status": info.verification_status,
        "aliases": list(info.aliases),
        "document_count": len(docs),
        "documents": docs,
    }


@router.get("", response_model=List[EntityOut])
def list_entities(
    category: Optional[str] = Query(None, description="Optional category filter (Rider, Team, Manufacturer, Circuit)"),
    service: SearchService = Depends(get_search_service),
):
    try:
        with db.get_conn() as conn:
            return repository.list_entities(conn, category)
    except Exception:  # noqa: BLE001
        return _list_from_artifact(service, category)


@router.get("/recognize", response_model=List[RecognizedEntity])
def recognize(
    text: str = Query(..., min_length=1, max_length=2000),
    service: SearchService = Depends(get_search_service),
):
    if service.artifact is None:
        raise IndexNotReadyError("Index is not built yet.")
    return [
        RecognizedEntity(**item)
        for item in service.artifact.entity_dictionary.detect_unique(text)
    ]


@router.get("/{entity_id}", response_model=EntityDetailOut)
def get_entity(
    entity_id: str,
    service: SearchService = Depends(get_search_service),
):
    try:
        with db.get_conn() as conn:
            detail = repository.get_entity_detail(conn, entity_id)
            if detail is None:
                raise HTTPException(404, "Entity not found.")
            return detail
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
        return _detail_from_artifact(service, entity_id)
