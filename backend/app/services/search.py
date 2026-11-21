from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional, Tuple
from app.core.config import Settings
from app.services.indexer import (
    IndexArtifact,
    cosine_similarity,
    load_artifact,
    tfidf_vector,
    vector_length,
)
from app.services.preprocessing import TextPreprocessor

logger = logging.getLogger(__name__)

MODES = ("baseline", "entity")


class IndexNotReadyError(RuntimeError):
    pass


class SearchService:
    """
    Search service aligned 100% with Notebook v5:
    - Baseline: From-scratch TF-IDF (IDF = log10(N / df)) + Cosine Similarity (S_text).
    - Entity-Aware: Query Entity Coverage S_entity = |E_Q ∩ E_D| / |E_Q| over Neon `document_entities`.
    - Hybrid Fusion: S_final = alpha * S_text + beta * S_entity (default alpha=0.8, beta=0.2).
    - Fallback Behavior: When E_Q is empty, returns pure Baseline TF-IDF (S_entity = 0, S_final = S_text).
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.preprocessor = TextPreprocessor()
        self.artifact: Optional[IndexArtifact] = None

    # ---- lifecycle -------------------------------------------------------
    def try_load(self) -> bool:
        path = self.settings.artifact_path
        if not path.exists():
            logger.warning("No index artifact at %s. Build it via build_index.py or rebuild endpoint.", path)
            return False
        try:
            self.set_artifact(load_artifact(path))
            return True
        except Exception:  # noqa: BLE001
            logger.exception("Failed to load index artifact.")
            return False

    def set_artifact(self, artifact: IndexArtifact) -> None:
        # Warm stem cache with indexed vocabulary just like Notebook v5
        self.preprocessor.warm_cache(artifact.vocab)
        self.artifact = artifact

    @property
    def ready(self) -> bool:
        return self.artifact is not None

    def _require(self) -> IndexArtifact:
        if self.artifact is None:
            raise IndexNotReadyError("Index is not built yet.")
        return self.artifact

    # ---- scoring (100% identical to Notebook v5) -------------------------
    def _text_scores(self, art: IndexArtifact, query: str) -> Tuple[Dict[str, float], str]:
        q_tokens = self.preprocessor.preprocess(query)
        q_clean = " ".join(q_tokens)
        if not q_tokens:
            return {did: 0.0 for did in art.doc_ids}, q_clean

        q_vec = tfidf_vector(q_tokens, art.idf)
        q_len = vector_length(q_vec)
        if q_len == 0.0:
            return {did: 0.0 for did in art.doc_ids}, q_clean

        scores = {
            did: float(
                cosine_similarity(
                    q_vec,
                    art.doc_vectors[did],
                    q_len=q_len,
                    d_len=art.doc_vector_lengths[did],
                )
            )
            for did in art.doc_ids
        }
        return scores, q_clean

    def _score(
        self, art: IndexArtifact, query: str, mode: str, alpha: float, beta: float
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], str, bool]:
        if mode == "entity_aware":
            mode = "entity"
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")

        s_text_map, q_clean = self._text_scores(art, query)
        recognized = art.entity_dictionary.detect_unique(query)
        eq_ids = [e["entity_id"] for e in recognized]
        fallback = (mode == "entity" and len(eq_ids) == 0)

        if mode == "entity" and not fallback and alpha == 0 and beta == 0:
            raise ValueError("alpha and beta cannot both be zero.")

        scored_rows: List[Dict[str, Any]] = []
        for idx, did in enumerate(art.doc_ids):
            st = s_text_map[did]
            doc_ents = art.doc_entity_counts.get(did, {})
            matched_ids = [eid for eid in eq_ids if doc_ents.get(eid, 0) >= 1]

            if mode == "baseline" or fallback:
                se = 0.0
                sf = st
            else:
                se = len(matched_ids) / float(len(eq_ids))
                sf = alpha * st + beta * se

            matched_names = [
                art.entity_dictionary.entities[eid].name
                for eid in matched_ids
                if eid in art.entity_dictionary.entities
            ]
            scored_rows.append(
                {
                    "idx": idx,
                    "doc_id": did,
                    "score": float(sf),
                    "text_score": float(st),
                    "entity_score": float(se),
                    "matched_entities": matched_names if (mode == "entity" and not fallback) else [],
                }
            )

        # Exact deterministic tie-breaking identical to Notebook v5: (-S_final, doc_id)
        scored_rows.sort(key=lambda r: (-r["score"], r["doc_id"]))
        return scored_rows, recognized, q_clean, fallback

    # ---- public API ------------------------------------------------------
    def query_has_entities(self, query: str) -> bool:
        return bool(self._require().entity_dictionary.detect_unique(query))

    def rank(self, query: str, mode: str, alpha: float, beta: float) -> List[str]:
        art = self._require()
        scored_rows, _, _, _ = self._score(art, query, mode, alpha, beta)
        return [r["doc_id"] for r in scored_rows]

    def search(
        self,
        query: str,
        mode: str = "entity",
        top_k: int = 10,
        alpha: Optional[float] = None,
        beta: Optional[float] = None,
    ) -> Dict[str, Any]:
        art = self._require()
        norm_mode = "entity" if mode == "entity_aware" else mode
        a = self.settings.default_alpha if alpha is None else alpha
        b = self.settings.default_beta if beta is None else beta

        scored_rows, recognized, q_clean, fallback = self._score(art, query, norm_mode, a, b)

        positive_rows = [r for r in scored_rows if r["score"] > 0.0]
        total = len(positive_rows)

        results: List[Dict[str, Any]] = []
        for rank, row in enumerate(positive_rows[:top_k], start=1):
            meta = art.doc_meta[row["idx"]]
            results.append(
                {
                    **meta,
                    "rank": rank,
                    "score": round(row["score"], 6),
                    "text_score": round(row["text_score"], 6),
                    "entity_score": round(row["entity_score"], 6),
                    "matched_entities": row["matched_entities"],
                }
            )

        return {
            "query": query,
            "preprocessed_query": q_clean,
            "mode": norm_mode,
            "alpha": a if norm_mode == "entity" else None,
            "beta": b if norm_mode == "entity" else None,
            "recognized_entities": recognized,
            "entity_fallback": fallback,
            "total": total,
            "results": results,
        }
