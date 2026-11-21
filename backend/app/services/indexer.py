from __future__ import annotations
import csv
import logging
import math
import os
import re
import threading
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple
import joblib
from app.core import db
from app.core.config import BASE_DIR, Settings
from app.services import repository
from app.services.entity_recognizer import EntityDictionary
from app.services.preprocessing import TextPreprocessor, split_tokens

logger = logging.getLogger(__name__)

FORMAT_VERSION = 2  # v2 = From-Scratch Inverted Index + TF-IDF log10(N/df) + Entity Coverage (Notebook v5)
ENGINE_NAME = "v5-from-scratch"
_rebuild_lock = threading.Lock()


class IndexBuildError(RuntimeError):
    pass


# --- Exact From-Scratch IR Math Functions (100% identical to Notebook v5 & clean.ipynb) ---
def build_inverted_index(doc_tokens: Mapping[str, List[str]]) -> Dict[str, List[str]]:
    pairs: List[Tuple[str, str]] = []
    for doc_id, tokens in doc_tokens.items():
        for term in tokens:
            pairs.append((doc_id, term))

    pairs_sorted = sorted(pairs, key=lambda p: p[1])
    index: Dict[str, List[str]] = {}
    for doc_id, term in pairs_sorted:
        postings = index.setdefault(term, [])
        if doc_id not in postings:
            postings.append(doc_id)
    for term in index:
        index[term] = sorted(index[term])
    return index


def compute_tf(tokens: Sequence[str]) -> Dict[str, int]:
    return dict(Counter(tokens))


def tfidf_vector(tokens: Sequence[str], idf: Mapping[str, float]) -> Dict[str, float]:
    tf = compute_tf(tokens)
    return {t: tf[t] * idf[t] for t in tf if t in idf}


def dot_product(v1: Mapping[str, float], v2: Mapping[str, float]) -> float:
    if len(v1) > len(v2):
        v1, v2 = v2, v1
    return sum(w * v2[t] for t, w in v1.items() if t in v2)


def vector_length(v: Mapping[str, float]) -> float:
    return math.sqrt(sum(w * w for w in v.values()))


def cosine_similarity(
    q_vec: Mapping[str, float],
    d_vec: Mapping[str, float],
    q_len: Optional[float] = None,
    d_len: Optional[float] = None,
) -> float:
    ql = vector_length(q_vec) if q_len is None else q_len
    dl = vector_length(d_vec) if d_len is None else d_len
    denom = ql * dl
    if denom == 0.0:
        return 0.0
    return dot_product(q_vec, d_vec) / denom


def _clean_snippet(content: str, max_len: int) -> str:
    text = re.sub(r"\s+", " ", str(content or "")).strip()
    if len(text) <= max_len:
        return text
    cut = text[:max_len].rsplit(" ", 1)[0].strip()
    return (cut or text[:max_len].strip()) + "…"


@dataclass
class IndexArtifact:
    format_version: int
    built_at: str
    doc_ids: List[str]
    doc_meta: List[Dict[str, Any]]
    doc_contents: Dict[str, str]
    vocab: List[str]
    df_count: Dict[str, int]
    idf: Dict[str, float]
    doc_vectors: Dict[str, Dict[str, float]]
    doc_vector_lengths: Dict[str, float]
    entity_dictionary: EntityDictionary
    entity_ids: List[str]
    doc_entity_counts: Dict[str, Dict[str, int]]
    engine: str = ENGINE_NAME
    doc_idx_map: Dict[str, int] = field(init=False)
    entity_doc_counts: Dict[str, int] = field(init=False)

    def __post_init__(self) -> None:
        self.doc_idx_map = {did: i for i, did in enumerate(self.doc_ids)}
        counts: Dict[str, int] = defaultdict(int)
        for did in self.doc_ids:
            for eid, cnt in self.doc_entity_counts.get(did, {}).items():
                if cnt >= 1:
                    counts[eid] += 1
        self.entity_doc_counts = dict(counts)

    def summary(self) -> Dict[str, Any]:
        return {
            "engine": self.engine,
            "built_at": self.built_at,
            "num_documents": len(self.doc_ids),
            "num_terms": len(self.vocab),
            "num_entities": len(self.entity_ids),
        }


def build_artifact(
    documents: Sequence[Mapping],
    entities: Sequence[Mapping],
    aliases: Sequence[Mapping],
    preprocessor: TextPreprocessor,
    stored_doc_entities: Optional[Sequence[Mapping]] = None,
    snippet_length: int = 280,
    use_stored_processed_text: bool = True,
    use_stored_document_entities: bool = True,
) -> Tuple[IndexArtifact, List[tuple]]:
    if not documents:
        raise IndexBuildError("No documents found. Import documents first.")

    dictionary = EntityDictionary(entities, aliases)
    entity_ids = sorted(dictionary.entities)

    doc_ids: List[str] = []
    doc_meta: List[Dict[str, Any]] = []
    doc_contents: Dict[str, str] = {}
    doc_tokens: Dict[str, List[str]] = {}

    for d in documents:
        did = str(d["doc_id"])
        title = str(d.get("title") or "").strip()
        content = str(d.get("content") or "")
        media_raw = d.get("media")
        media = "IDN Times" if media_raw and "idn" in str(media_raw).lower() else (str(media_raw).strip() if media_raw else None)
        published = d.get("published_at")
        published_str = published.isoformat() if hasattr(published, "isoformat") else (str(published) if published else None)

        doc_ids.append(did)
        doc_contents[did] = content
        doc_meta.append(
            {
                "doc_id": did,
                "title": title,
                "media": media,
                "published_at": published_str,
                "topic": d.get("topic"),
                "url": d.get("url"),
                "author": d.get("author"),
                "snippet": _clean_snippet(content, snippet_length),
            }
        )

        stored = d.get("processed_text") if use_stored_processed_text else None
        if stored and str(stored).strip():
            tokens = split_tokens(str(stored))
        else:
            tokens = preprocessor.preprocess(f"{title} {content}")
        doc_tokens[did] = tokens

    # --- Text branch: Exact From-Scratch Inverted Index & TF-IDF (IDF = log10(N / df)) ---
    inverted_index = build_inverted_index(doc_tokens)
    n_docs = len(doc_ids)
    df_count = {term: len(postings) for term, postings in inverted_index.items()}
    idf = {term: math.log10(n_docs / d) for term, d in df_count.items()}
    vocab = sorted(idf)
    if not vocab:
        raise IndexBuildError("Could not build TF-IDF vocabulary: empty vocabulary.")

    doc_vectors = {did: tfidf_vector(doc_tokens[did], idf) for did in doc_ids}
    doc_vector_lengths = {did: vector_length(vec) for did, vec in doc_vectors.items()}

    # --- Entity branch: Authoritative document_entities from Neon DB (fallback: extract if empty) ---
    doc_entity_counts: Dict[str, Dict[str, int]] = {did: {} for did in doc_ids}
    doc_entity_rows: List[tuple] = []

    if use_stored_document_entities and stored_doc_entities:
        for row in stored_doc_entities:
            did = str(row["doc_id"])
            eid = str(row["entity_id"])
            cnt = int(row["mention_count"])
            if did in doc_entity_counts and eid in dictionary.entities and cnt >= 1:
                doc_entity_counts[did][eid] = cnt
                doc_entity_rows.append((did, eid, cnt))
    else:
        for d in documents:
            did = str(d["doc_id"])
            full_text = f"{d.get('title') or ''}\n{d.get('content') or ''}"
            raw_counts = dictionary.count(full_text, weighted=False)
            for eid, cnt in raw_counts.items():
                icnt = int(round(cnt))
                if icnt >= 1:
                    doc_entity_counts[did][eid] = icnt
                    doc_entity_rows.append((did, eid, icnt))

    artifact = IndexArtifact(
        format_version=FORMAT_VERSION,
        built_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        doc_ids=doc_ids,
        doc_meta=doc_meta,
        doc_contents=doc_contents,
        vocab=vocab,
        df_count=df_count,
        idf=idf,
        doc_vectors=doc_vectors,
        doc_vector_lengths=doc_vector_lengths,
        entity_dictionary=dictionary,
        entity_ids=entity_ids,
        doc_entity_counts=doc_entity_counts,
        engine=ENGINE_NAME,
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
        raise IndexBuildError(
            "Index artifact format is outdated (expected v5 from-scratch format v2). Rebuild the index."
        )
    return artifact


def rebuild_from_database(
    settings: Settings, preprocessor: TextPreprocessor, service=None
) -> IndexArtifact:
    if not _rebuild_lock.acquire(blocking=False):
        raise IndexBuildError("An index rebuild is already running.")
    try:
        with db.get_conn() as conn:
            documents = repository.fetch_documents_for_index(conn)
            entities, aliases = repository.fetch_entities_and_aliases(conn, settings.entity_status_list)
            stored_doc_entities = (
                repository.fetch_document_entities_for_index(conn)
                if settings.use_stored_document_entities
                else None
            )
            artifact, doc_entity_rows = build_artifact(
                documents=documents,
                entities=entities,
                aliases=aliases,
                preprocessor=preprocessor,
                stored_doc_entities=stored_doc_entities,
                snippet_length=settings.snippet_length,
                use_stored_processed_text=settings.use_stored_processed_text,
                use_stored_document_entities=settings.use_stored_document_entities,
            )
            if settings.persist_document_entities:
                repository.replace_document_entities(conn, doc_entity_rows)
        try:
            save_artifact(artifact, settings.artifact_path)
        except OSError as exc:
            logger.warning("Could not persist artifact to disk (%s); using in-memory artifact only.", exc)
        if service is not None:
            service.set_artifact(artifact)
        logger.info("Index rebuilt from Neon DB: %s", artifact.summary())
        return artifact
    finally:
        _rebuild_lock.release()


def _parse_corpus_sql_fallback(sql_path: Path) -> Dict[str, Dict[str, Any]]:
    """Parse 02_corpus_import.sql INSERT statements using quote-aware scanning."""
    text = sql_path.read_text(encoding="utf-8")
    docs_by_id: Dict[str, Dict[str, Any]] = {}
    header_re = re.compile(r"INSERT\s+INTO\s+documents\s*\([^)]+\)\s*VALUES\s*\(", re.IGNORECASE)

    for m in header_re.finditer(text):
        i, n = m.end(), len(text)
        fields: List[Optional[str]] = []
        while i < n:
            while i < n and text[i] in " \t\r\n,":
                i += 1
            if i >= n or text[i] == ")":
                break
            if text[i] == "'":
                i += 1
                buf = []
                while i < n:
                    if text[i] == "'":
                        if i + 1 < n and text[i + 1] == "'":
                            buf.append("'")
                            i += 2
                        else:
                            i += 1
                            break
                    else:
                        buf.append(text[i])
                        i += 1
                fields.append("".join(buf))
            else:
                start = i
                while i < n and text[i] not in ",)\r\n":
                    i += 1
                token = text[start:i].strip()
                fields.append(None if token.upper() == "NULL" else token)
        if len(fields) >= 8 and fields[0]:
            docs_by_id[fields[0]] = {
                "doc_id": fields[0],
                "title": fields[1],
                "published_at": fields[2],
                "media": fields[3],
                "topic": fields[4],
                "url": fields[5],
                "author": fields[6],
                "content": fields[7],
            }
    return docs_by_id


def rebuild_from_local_exports(
    settings: Settings, preprocessor: TextPreprocessor, service=None
) -> IndexArtifact:
    """
    Build the exact v5 IndexArtifact from the verified SQL + v3/v5 CSV exports in the repository.
    Useful for offline local development before DATABASE_URL is configured.
    """
    repo_root = BASE_DIR.parent
    sql_corpus = repo_root / "task-requirements" / "documentation" / "02_corpus_import.sql"
    prep_csv = repo_root / "doc" / "Experiment-Result" / "v3_result" / "corpus_preprocessed.csv"
    v5_dir = repo_root / "doc" / "Experiment-Result" / "v5_result"
    v4_dir = repo_root / "doc" / "Experiment-Result" / "v4_result"
    res_dir = v5_dir if (v5_dir / "entities.csv").exists() else v4_dir

    if not prep_csv.exists() or not (res_dir / "entities.csv").exists():
        raise IndexBuildError("Local verified corpus/entity exports not found in doc/Experiment-Result/.")

    raw_docs_map = _parse_corpus_sql_fallback(sql_corpus) if sql_corpus.exists() else {}

    documents: List[Dict[str, Any]] = []
    with prep_csv.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            did = row["doc_id"]
            raw = raw_docs_map.get(did, {})
            documents.append(
                {
                    "doc_id": did,
                    "title": raw.get("title") or row.get("title") or "",
                    "published_at": raw.get("published_at") or row.get("date") or None,
                    "media": raw.get("media") or row.get("media") or None,
                    "topic": raw.get("topic") or row.get("topic") or "motogp",
                    "url": raw.get("url") or row.get("url") or None,
                    "author": raw.get("author") or row.get("author") or None,
                    "content": raw.get("content") or row.get("text") or row.get("content") or "",
                    "processed_text": row.get("text_final") or "",
                }
            )

    with (res_dir / "entities.csv").open("r", encoding="utf-8") as f:
        entities = list(csv.DictReader(f))
    with (res_dir / "entity_aliases.csv").open("r", encoding="utf-8") as f:
        aliases = list(csv.DictReader(f))
    with (res_dir / "document_entities.csv").open("r", encoding="utf-8") as f:
        doc_entities = list(csv.DictReader(f))

    artifact, _ = build_artifact(
        documents=documents,
        entities=entities,
        aliases=aliases,
        preprocessor=preprocessor,
        stored_doc_entities=doc_entities,
        snippet_length=settings.snippet_length,
        use_stored_processed_text=True,
        use_stored_document_entities=True,
    )
    save_artifact(artifact, settings.artifact_path)
    if service is not None:
        service.set_artifact(artifact)
    logger.info("Index rebuilt from verified local exports: %s", artifact.summary())
    return artifact
