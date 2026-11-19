from __future__ import annotations
import logging
import math
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple
import joblib
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
from app.core import db
from app.core.config import Settings
from app.services import repository
from app.services.entity_recognizer import EntityDictionary
from app.services.preprocessing import TextPreprocessor, split_tokens

logger = logging.getLogger(__name__)

FORMAT_VERSION = 1
_rebuild_lock = threading.Lock()

class IndexBuildError(RuntimeError):
    pass

@dataclass
class IndexArtifact:
    format_version: int
    built_at: str
    doc_ids: List[str]
    doc_meta: List[Dict[str, Any]]
    vectorizer: TfidfVectorizer
    tfidf_matrix: csr_matrix          # N x V, L2-normalised rows
    entity_dictionary: EntityDictionary
    entity_ids: List[str]             # column order of entity_matrix
    entity_idf: np.ndarray            # E
    entity_matrix: csr_matrix         # N x E, L2-normalised rows

    def __post_init__(self) -> None:
        self.entity_col = {eid: i for i, eid in enumerate(self.entity_ids)}

    def summary(self) -> Dict[str, Any]:
        return {
            "built_at": self.built_at,
            "num_documents": len(self.doc_ids),
            "num_terms": len(self.vectorizer.vocabulary_),
            "num_entities": len(self.entity_ids),
        }

def _tf(count: float) -> float:
    return 1.0 + math.log(count) if count >= 1.0 else count

def build_artifact(
    documents: Sequence[Mapping],
    entities: Sequence[Mapping],
    aliases: Sequence[Mapping],
    preprocessor: TextPreprocessor,
    title_boost: float = 3.0,
    snippet_length: int = 250,
    use_stored_processed_text: bool = False,
) -> Tuple[IndexArtifact, List[tuple]]:
    if not documents:
        raise IndexBuildError("No documents found. Import documents first.")

    dictionary = EntityDictionary(entities, aliases)
    entity_ids = sorted(dictionary.entities)
    col = {eid: i for i, eid in enumerate(entity_ids)}
    n_docs, n_ent = len(documents), len(entity_ids)

    doc_ids: List[str] = []
    doc_meta: List[Dict[str, Any]] = []
    processed_texts: List[str] = []
    doc_entity_rows: List[tuple] = []
    weighted_counts: List[Dict[int, float]] = []

    for d in documents:
        title, content = d.get("title") or "", d.get("content") or ""
        doc_ids.append(d["doc_id"])
        published = d.get("published_at")
        snippet = content[:snippet_length].strip()
        doc_meta.append(
            {
                "doc_id": d["doc_id"],
                "title": title,
                "media": d.get("media"),
                "published_at": published.isoformat() if hasattr(published, "isoformat") else published,
                "topic": d.get("topic"),
                "url": d.get("url"),
                "author": d.get("author"),
                "snippet": snippet + ("…" if len(content) > snippet_length else ""),
            }
        )
        stored = d.get("processed_text") if use_stored_processed_text else None
        processed_texts.append(stored or preprocessor.preprocess_to_string(f"{title}. {content}"))

        title_counts = dictionary.count(title)
        body_counts = dictionary.count(content)
        combined = dict(body_counts)
        for eid, c in title_counts.items():
            combined[eid] = combined.get(eid, 0.0) + c * title_boost
        weighted_counts.append(combined)
        raw_body = dictionary.count(content, weighted=False)
        raw_title = dictionary.count(title, weighted=False)
        for eid in set(raw_body) | set(raw_title):
            doc_entity_rows.append(
                (d["doc_id"], eid, int(raw_body.get(eid, 0) + raw_title.get(eid, 0)))
            )

    # --- Text branch: TF-IDF (L2-normalised, so dot product == cosine similarity)
    vectorizer = TfidfVectorizer(
        analyzer=split_tokens, sublinear_tf=True, smooth_idf=True, norm="l2"
    )
    try:
        tfidf_matrix = vectorizer.fit_transform(processed_texts).tocsr()
    except ValueError as exc:  # empty vocabulary
        raise IndexBuildError(f"Could not build TF-IDF vocabulary: {exc}") from exc

    # --- Entity branch: tf * idf per (document, entity), L2-normalised
    df = np.zeros(n_ent)
    for combined in weighted_counts:
        for eid in combined:
            df[col[eid]] += 1
    entity_idf = np.log((n_docs + 1) / (df + 1)) + 1.0

    rows, cols, data = [], [], []
    for i, combined in enumerate(weighted_counts):
        for eid, c in combined.items():
            j = col[eid]
            rows.append(i)
            cols.append(j)
            data.append(_tf(c) * entity_idf[j])
    entity_matrix = csr_matrix((data, (rows, cols)), shape=(n_docs, n_ent), dtype=np.float64)
    if n_ent > 0 and entity_matrix.nnz > 0:
        entity_matrix = normalize(entity_matrix, norm="l2", axis=1)

    artifact = IndexArtifact(
        format_version=FORMAT_VERSION,
        built_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        doc_ids=doc_ids,
        doc_meta=doc_meta,
        vectorizer=vectorizer,
        tfidf_matrix=tfidf_matrix,
        entity_dictionary=dictionary,
        entity_ids=entity_ids,
        entity_idf=entity_idf,
        entity_matrix=entity_matrix.tocsr(),
    )
    return artifact, doc_entity_rows

def save_artifact(artifact: IndexArtifact, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    joblib.dump(artifact, tmp, compress=3)
    os.replace(tmp, path)  # atomic swap

def load_artifact(path: Path) -> IndexArtifact:
    artifact = joblib.load(path)
    if getattr(artifact, "format_version", None) != FORMAT_VERSION:
        raise IndexBuildError("Index artifact format is outdated. Rebuild the index.")
    return artifact

def rebuild_from_database(settings: Settings, preprocessor: TextPreprocessor, service=None) -> IndexArtifact:
    if not _rebuild_lock.acquire(blocking=False):
        raise IndexBuildError("An index rebuild is already running.")
    try:
        with db.get_conn() as conn:
            documents = repository.fetch_documents_for_index(conn)
            entities, aliases = repository.fetch_entities_and_aliases(conn, settings.entity_status_list)
            artifact, doc_entity_rows = build_artifact(
                documents,
                entities,
                aliases,
                preprocessor,
                title_boost=settings.entity_title_boost,
                snippet_length=settings.snippet_length,
                use_stored_processed_text=settings.use_stored_processed_text,
            )
            if settings.persist_document_entities:
                repository.replace_document_entities(conn, doc_entity_rows)
        save_artifact(artifact, settings.artifact_path)
        if service is not None:
            service.set_artifact(artifact)
        logger.info("Index rebuilt: %s", artifact.summary())
        return artifact
    finally:
        _rebuild_lock.release()
