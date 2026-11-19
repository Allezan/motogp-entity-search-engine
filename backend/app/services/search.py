from __future__ import annotations
import logging
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.core.config import Settings
from app.services.indexer import IndexArtifact, load_artifact
from app.services.preprocessing import TextPreprocessor

logger = logging.getLogger(__name__)

MODES = ("baseline", "entity")

class IndexNotReadyError(RuntimeError):
    pass


class SearchService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.preprocessor = TextPreprocessor()
        self.artifact: Optional[IndexArtifact] = None

    # ---- lifecycle -------------------------------------------------------
    def try_load(self) -> bool:
        path = self.settings.artifact_path
        if not path.exists():
            logger.warning("No index artifact at %s. Build it via the rebuild endpoint.", path)
            return False
        try:
            self.set_artifact(load_artifact(path))
            return True
        except Exception:  # noqa: BLE001
            logger.exception("Failed to load index artifact.")
            return False

    def set_artifact(self, artifact: IndexArtifact) -> None:
        self.artifact = artifact  # single reference swap: safe for concurrent readers

    @property
    def ready(self) -> bool:
        return self.artifact is not None

    def _require(self) -> IndexArtifact:
        if self.artifact is None:
            raise IndexNotReadyError("Index is not built yet.")
        return self.artifact

    # ---- scoring ---------------------------------------------------------
    def _text_scores(self, art: IndexArtifact, query: str) -> np.ndarray:
        processed = self.preprocessor.preprocess_to_string(query)
        q_vec = art.vectorizer.transform([processed])
        if q_vec.nnz == 0:
            return np.zeros(len(art.doc_ids))
        return cosine_similarity(q_vec, art.tfidf_matrix).ravel()

    def _entity_scores(self, art: IndexArtifact, counts: Dict[str, float]) -> np.ndarray:
        q = np.zeros(len(art.entity_ids))
        for eid, c in counts.items():
            j = art.entity_col.get(eid)
            if j is not None:
                tf = 1.0 + math.log(c) if c >= 1.0 else c
                q[j] = tf * art.entity_idf[j]
        norm = np.linalg.norm(q)
        if norm == 0:
            return np.zeros(len(art.doc_ids))
        return np.asarray(art.entity_matrix.dot(q / norm)).ravel()

    def _score(
        self, art: IndexArtifact, query: str, mode: str, alpha: float, beta: float
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, float], bool]:
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")
        text = self._text_scores(art, query)
        counts = art.entity_dictionary.count(query)
        entity = np.zeros_like(text)
        fallback = False
        if mode == "baseline":
            final = text
        elif not counts:
            final, fallback = text, True  # no recognised entity -> pure text retrieval
        else:
            if alpha == 0 and beta == 0:
                raise ValueError("alpha and beta cannot both be zero.")
            entity = self._entity_scores(art, counts)
            final = alpha * text + beta * entity
        return text, entity, final, counts, fallback

    @staticmethod
    def _ranked_indices(final: np.ndarray, top_k: Optional[int]) -> np.ndarray:
        order = np.argsort(-final, kind="stable")
        order = order[final[order] > 0]
        return order if top_k is None else order[:top_k]

    # ---- public API ------------------------------------------------------
    def query_has_entities(self, query: str) -> bool:
        return bool(self._require().entity_dictionary.count(query))

    def rank(self, query: str, mode: str, alpha: float, beta: float) -> List[str]:
        art = self._require()
        _, _, final, _, _ = self._score(art, query, mode, alpha, beta)
        return [art.doc_ids[i] for i in self._ranked_indices(final, None)]

    def search(
        self, query: str, mode: str = "entity", top_k: int = 10,
        alpha: Optional[float] = None, beta: Optional[float] = None,
    ) -> Dict[str, Any]:
        art = self._require()
        alpha = self.settings.default_alpha if alpha is None else alpha
        beta = self.settings.default_beta if beta is None else beta
        text, entity, final, counts, fallback = self._score(art, query, mode, alpha, beta)

        order = self._ranked_indices(final, top_k)
        total = int((final > 0).sum())
        dictionary = art.entity_dictionary

        seen, recognized = set(), []
        for m in dictionary.find_mentions(query):
            if m.entity_id in seen:
                continue
            seen.add(m.entity_id)
            info = dictionary.entities[m.entity_id]
            recognized.append(
                {
                    "entity_id": info.entity_id,
                    "name": info.name,
                    "category": info.category,
                    "matched_text": m.matched_text,
                    "ambiguous": m.weight < 1.0,
                }
            )

        results = []
        for rank, i in enumerate(order, start=1):
            matched = []
            if mode == "entity" and counts:
                for eid in counts:
                    j = art.entity_col.get(eid)
                    if j is not None and art.entity_matrix[i, j] > 0:
                        matched.append(dictionary.entities[eid].name)
            results.append(
                {
                    **art.doc_meta[i],
                    "rank": rank,
                    "score": float(final[i]),
                    "text_score": float(text[i]),
                    "entity_score": float(entity[i]),
                    "matched_entities": matched,
                }
            )
        return {
            "query": query,
            "mode": mode,
            "alpha": alpha if mode == "entity" else None,
            "beta": beta if mode == "entity" else None,
            "recognized_entities": recognized,
            "entity_fallback": fallback,
            "total": total,
            "results": results,
        }
