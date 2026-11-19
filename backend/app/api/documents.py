from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from app.core import db
from app.schemas import DocumentDetail, DocumentList
from app.services import repository

router = APIRouter(prefix="/documents", tags=["documents"])

@router.get("", response_model=DocumentList)
def list_documents(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    media: Optional[str] = Query(None, description="Case-insensitive exact media/publisher name"),
):
    with db.get_conn() as conn:
        rows, total = repository.list_documents(conn, limit, offset, media)
    return {"total": total, "limit": limit, "offset": offset, "items": rows}

@router.get("/{doc_id}", response_model=DocumentDetail)
def get_document(doc_id: str):
    with db.get_conn() as conn:
        doc = repository.get_document(conn, doc_id)
        if doc is None:
            raise HTTPException(404, "Document not found.")
        doc["entities"] = repository.get_document_entities(conn, doc_id)
    return doc
