from __future__ import annotations
from typing import Dict, List, Optional, Sequence, Set
from app.services.search import SearchService

METRICS = ("precision_at_k", "recall_at_k", "average_precision")

def precision_at_k(ranked: Sequence[str], relevant: Set[str], k: int) -> float:
    return sum(1 for d in ranked[:k] if d in relevant) / k

def recall_at_k(ranked: Sequence[str], relevant: Set[str], k: int) -> float:
    return sum(1 for d in ranked[:k] if d in relevant) / len(relevant)

def average_precision(ranked: Sequence[str], relevant: Set[str]) -> float:
    # AP over the full ranked list (documents with score > 0)
    hits, total = 0, 0.0
    for i, d in enumerate(ranked, start=1):
        if d in relevant:
            hits += 1
            total += hits / i
    return total / len(relevant)

def _metrics(ranked: Sequence[str], relevant: Set[str], k: int) -> Dict[str, float]:
    return {
        "precision_at_k": precision_at_k(ranked, relevant, k),
        "recall_at_k": recall_at_k(ranked, relevant, k),
        "average_precision": average_precision(ranked, relevant),
    }

def _mean(rows: List[Dict[str, float]]) -> Dict[str, float]:
    return {m: round(sum(r[m] for r in rows) / len(rows), 4) for m in METRICS}

def evaluate(
    service: SearchService,
    queries: Sequence[Dict],
    k: int,
    alpha: float,
    beta: float,
) -> Dict:
    per_query, skipped = [], 0
    for q in queries:
        relevant = set(q["relevant_doc_ids"])
        if not relevant:
            skipped += 1  # recall/AP undefined without judgments
            continue
        text = q["query_text"]
        per_query.append(
            {
                "query_id": q["query_id"],
                "query_text": text,
                "has_entities": service.query_has_entities(text),
                "num_relevant": len(relevant),
                "baseline": _metrics(service.rank(text, "baseline", alpha, beta), relevant, k),
                "entity": _metrics(service.rank(text, "entity", alpha, beta), relevant, k),
            }
        )

    def summarize(rows: List[Dict]) -> Optional[Dict]:
        if not rows:
            return None
        base, ent = _mean([r["baseline"] for r in rows]), _mean([r["entity"] for r in rows])
        return {
            "num_queries": len(rows),
            "baseline": base,
            "entity": ent,
            "delta": {m: round(ent[m] - base[m], 4) for m in METRICS},
        }

    return {
        "k": k,
        "alpha": alpha,
        "beta": beta,
        "num_queries": len(per_query),
        "skipped_queries": skipped,
        "summary": {
            "all": summarize(per_query),
            "with_entities": summarize([r for r in per_query if r["has_entities"]]),
            "without_entities": summarize([r for r in per_query if not r["has_entities"]]),
        },
        "per_query": per_query,
    }
