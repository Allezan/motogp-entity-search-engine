from __future__ import annotations
from datetime import date
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

SearchMode = Literal["baseline", "entity"]
SearchModeInput = Literal["baseline", "entity", "entity_aware"]


class RecognizedEntity(BaseModel):
    entity_id: str
    name: str
    category: str
    matched_text: str
    ambiguous: bool = False


class SearchResult(BaseModel):
    rank: int
    doc_id: str
    title: str
    media: Optional[str] = None
    published_at: Optional[str] = None
    topic: Optional[str] = None
    url: Optional[str] = None
    author: Optional[str] = None
    snippet: str = ""
    score: float
    text_score: float
    entity_score: float
    matched_entities: List[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str
    preprocessed_query: str = ""
    mode: SearchMode
    alpha: Optional[float] = None
    beta: Optional[float] = None
    recognized_entities: List[RecognizedEntity]
    entity_fallback: bool = Field(
        False,
        description="True when mode=entity but the query has no recognised entity (text-only scoring used).",
    )
    total: int
    results: List[SearchResult]


class CompareResponse(BaseModel):
    baseline: SearchResponse
    entity: SearchResponse


class DocumentSummary(BaseModel):
    doc_id: str
    title: str
    published_at: Optional[date] = None
    media: Optional[str] = None
    topic: Optional[str] = None
    url: Optional[str] = None
    author: Optional[str] = None


class DocumentList(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[DocumentSummary]


class DocumentEntity(BaseModel):
    entity_id: str
    name: str
    category: Optional[str] = None
    mention_count: int


class DocumentDetail(DocumentSummary):
    content: str
    entities: List[DocumentEntity] = Field(default_factory=list)


class EntityOut(BaseModel):
    entity_id: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    verification_status: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)
    document_count: int = 0


class EntityDocumentRef(BaseModel):
    doc_id: str
    title: str
    media: Optional[str] = None
    published_at: Optional[str] = None
    url: Optional[str] = None
    mention_count: int


class EntityDetailOut(EntityOut):
    documents: List[EntityDocumentRef] = Field(default_factory=list)


class IndexStatus(BaseModel):
    ready: bool
    engine: Optional[str] = None
    built_at: Optional[str] = None
    num_documents: Optional[int] = None
    num_terms: Optional[int] = None
    num_entities: Optional[int] = None


class HealthResponse(BaseModel):
    status: str
    database: str
    index_ready: bool
    engine: str = "v5-from-scratch"


class EvaluationQueryIn(BaseModel):
    query_text: str = Field(min_length=1, max_length=300)
    relevant_doc_ids: List[str] = Field(default_factory=list)


class EvaluationQueryOut(BaseModel):
    query_id: int
    query_text: str
    relevant_doc_ids: List[str]


class MetricSet(BaseModel):
    precision_at_k: float
    recall_at_k: float
    average_precision: float = Field(description="AP per query; MAP when aggregated.")


class QueryEvaluation(BaseModel):
    query_id: int
    query_text: str
    has_entities: bool
    num_relevant: int
    baseline: MetricSet
    entity: MetricSet


class GroupSummary(BaseModel):
    num_queries: int
    baseline: MetricSet
    entity: MetricSet
    delta: MetricSet


class EvaluationReport(BaseModel):
    k: int
    alpha: float
    beta: float
    num_queries: int
    skipped_queries: int
    summary: Dict[str, Optional[GroupSummary]]
    per_query: List[QueryEvaluation]
