from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_search_service
from app.core import db
from app.schemas import DocumentDetail, DocumentList
from app.services import repository
from app.services.search import SearchService

router = APIRouter(prefix="/documents", tags=["documents"])


def _list_from_artifact(service: SearchService, limit: int, offset: int, media: Optional[str]):
    art = service.artifact
    if art is None:
        raise HTTPException(503, "Database unavailable and search index is not loaded.")
    items = list(art.doc_meta)
    if media:
        m_low = media.strip().lower()
        items = [d for d in items if (d.get("media") or "").lower() == m_low]
    items.sort(key=lambda d: (d.get("published_at") or "", d["doc_id"]), reverse=True)
    total = len(items)
    sliced = [
        {
            "doc_id": d["doc_id"],
            "title": d["title"],
            "published_at": d.get("published_at"),
            "media": d.get("media"),
            "topic": d.get("topic"),
            "url": d.get("url"),
            "author": d.get("author"),
        }
        for d in items[offset : offset + limit]
    ]
    return {"total": total, "limit": limit, "offset": offset, "items": sliced}


def _detail_from_artifact(service: SearchService, doc_id: str):
    art = service.artifact
    if art is None:
        raise HTTPException(503, "Database unavailable and search index is not loaded.")
    idx = art.doc_idx_map.get(doc_id)
    if idx is None:
        raise HTTPException(404, "Document not found.")
    meta = art.doc_meta[idx]
    ent_counts = art.doc_entity_counts.get(doc_id, {})
    entities = []
    for eid, cnt in ent_counts.items():
        info = art.entity_dictionary.entities.get(eid)
        if info and cnt >= 1:
            entities.append(
                {
                    "entity_id": info.entity_id,
                    "name": info.name,
                    "category": info.category,
                    "mention_count": int(cnt),
                }
            )
    entities.sort(key=lambda e: (-e["mention_count"], e["name"]))
    return {
        "doc_id": meta["doc_id"],
        "title": meta["title"],
        "published_at": meta.get("published_at"),
        "media": meta.get("media"),
        "topic": meta.get("topic"),
        "url": meta.get("url"),
        "author": meta.get("author"),
        "content": art.doc_contents.get(doc_id, meta.get("snippet", "")),
        "entities": entities,
    }


@router.get("", response_model=DocumentList)
def list_documents(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    media: Optional[str] = Query(None, description="Case-insensitive exact media/publisher name"),
    service: SearchService = Depends(get_search_service),
):
    try:
        with db.get_conn() as conn:
            rows, total = repository.list_documents(conn, limit, offset, media)
        return {"total": total, "limit": limit, "offset": offset, "items": rows}
    except Exception:  # noqa: BLE001
        return _list_from_artifact(service, limit, offset, media)


@router.get("/{doc_id}", response_model=DocumentDetail)
def get_document(
    doc_id: str,
    service: SearchService = Depends(get_search_service),
):
    try:
        with db.get_conn() as conn:
            doc = repository.get_document(conn, doc_id)
            if doc is None:
                raise HTTPException(404, "Document not found.")
            doc["entities"] = repository.get_document_entities(conn, doc_id)
        return doc
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
        return _detail_from_artifact(service, doc_id)
