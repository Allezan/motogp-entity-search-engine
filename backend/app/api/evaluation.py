from typing import List, Optional
import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.deps import get_search_service, require_admin
from app.core import db
from app.core.config import Settings, get_settings
from app.schemas import EvaluationQueryIn, EvaluationQueryOut, EvaluationReport
from app.services import repository
from app.services.evaluation import evaluate
from app.services.search import SearchService

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

@router.get("/queries", response_model=List[EvaluationQueryOut])
def list_queries():
    with db.get_conn() as conn:
        return repository.list_eval_queries(conn)

@router.post(
    "/queries", response_model=List[EvaluationQueryOut], status_code=201,
    dependencies=[Depends(require_admin)],
)
def create_queries(payload: List[EvaluationQueryIn]):
    # Add evaluation queries together with their manually judged relevant doc_ids.
    try:
        with db.get_conn() as conn:
            return [
                repository.create_eval_query(conn, q.query_text, q.relevant_doc_ids)
                for q in payload
            ]
    except psycopg.errors.ForeignKeyViolation as exc:
        raise HTTPException(422, "One or more doc_ids do not exist in `documents`.") from exc


@router.delete("/queries/{query_id}", status_code=204, dependencies=[Depends(require_admin)])
def delete_query(query_id: int):
    with db.get_conn() as conn:
        if not repository.delete_eval_query(conn, query_id):
            raise HTTPException(404, "Query not found.")


@router.get("/run", response_model=EvaluationReport)
def run_evaluation(
    k: int = Query(5, ge=1, le=50),
    alpha: Optional[float] = Query(None, ge=0),
    beta: Optional[float] = Query(None, ge=0),
    service: SearchService = Depends(get_search_service),
    settings: Settings = Depends(get_settings),
):
    # Precision@K, Recall@K and MAP for baseline vs entity-aware
    a = settings.default_alpha if alpha is None else alpha
    b = settings.default_beta if beta is None else beta
    if a == 0 and b == 0:
        raise HTTPException(422, "alpha and beta cannot both be zero.")
    with db.get_conn() as conn:
        queries = repository.list_eval_queries(conn)
    if not queries:
        raise HTTPException(409, "No evaluation queries yet. POST /evaluation/queries first.")
    return evaluate(service, queries, k, a, b)
