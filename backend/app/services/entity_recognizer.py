from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Set, Tuple
from app.services.preprocessing import normalize_ascii_lower


@dataclass(frozen=True)
class EntityInfo:
    entity_id: str
    name: str
    category: str
    description: Optional[str] = None
    source_url: Optional[str] = None
    verification_status: Optional[str] = None
    aliases: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Mention:
    entity_id: str
    matched_text: str
    start: int
    end: int
    weight: float  # 1 / number of candidate entities sharing this alias


class EntityDictionary:
    """
    Longest-Match-First + Word-Boundary + Span-Masking Entity Recognizer.
    Matches Notebook v5 (`detect_query_entities`) 100%.
    """

    def __init__(
        self,
        entities: Iterable[Mapping],
        aliases: Iterable[Mapping],
    ) -> None:
        raw_aliases_by_entity: Dict[str, List[str]] = {}
        alias_sets: Dict[str, Set[str]] = {}

        def add_alias(alias_text: Optional[str], entity_id: str, record_display: bool = False) -> None:
            raw = (alias_text or "").strip()
            if not raw:
                return
            if record_display:
                lst = raw_aliases_by_entity.setdefault(entity_id, [])
                if raw not in lst:
                    lst.append(raw)
            key = normalize_ascii_lower(raw)
            if key:
                alias_sets.setdefault(key, set()).add(entity_id)

        entity_rows = list(entities)
        valid_ids = {str(e["entity_id"]) for e in entity_rows}

        for e in entity_rows:
            eid = str(e["entity_id"])
            add_alias(e.get("canonical_name"), eid, record_display=False)

        for a in aliases:
            eid = str(a["entity_id"])
            if eid in valid_ids:
                add_alias(a.get("alias"), eid, record_display=True)
                add_alias(a.get("normalized_alias"), eid, record_display=False)

        self.entities: Dict[str, EntityInfo] = {}
        for e in entity_rows:
            eid = str(e["entity_id"])
            self.entities[eid] = EntityInfo(
                entity_id=eid,
                name=e["canonical_name"],
                category=e.get("category") or "",
                description=e.get("description"),
                source_url=e.get("source_url"),
                verification_status=e.get("verification_status"),
                aliases=tuple(raw_aliases_by_entity.get(eid, [])),
            )

        self.alias_map: Dict[str, List[str]] = {k: sorted(v) for k, v in alias_sets.items()}
        # Longest-Match-First ordering identical to Notebook v5
        self.sorted_aliases: List[str] = sorted(self.alias_map.keys(), key=lambda s: (-len(s), s))
        self._compiled_patterns: List[Tuple[str, re.Pattern]] = [
            (norm_al, re.compile(r"\b" + re.escape(norm_al) + r"\b", re.IGNORECASE))
            for norm_al in self.sorted_aliases
        ]

    def find_mentions(self, text: str) -> List[Mention]:
        """
        Detect entities using Longest-Match-First and span masking
        (so 'ducati lenovo team' is never falsely split into 'ducati').
        """
        work_text = normalize_ascii_lower(text)
        if not work_text:
            return []

        mentions: List[Mention] = []
        for norm_al, pat in self._compiled_patterns:
            matches = list(pat.finditer(work_text))
            if not matches:
                continue
            candidate_ids = self.alias_map[norm_al]
            weight = 1.0 / len(candidate_ids)
            for m in matches:
                for eid in candidate_ids:
                    mentions.append(Mention(eid, norm_al, m.start(), m.end(), weight))
            # Mask matched spans with spaces so shorter sub-aliases cannot overlap
            chars = list(work_text)
            for m in matches:
                for idx in range(m.start(), m.end()):
                    chars[idx] = " "
            work_text = "".join(chars)

        mentions.sort(key=lambda m: (m.start, -len(m.matched_text), m.entity_id))
        return mentions

    def detect_unique(self, text: str) -> List[Dict]:
        """Return unique recognized entities in detection order (Longest-Match-First)."""
        work_text = normalize_ascii_lower(text)
        if not work_text:
            return []

        detected: List[Dict] = []
        seen: Set[str] = set()
        for norm_al, pat in self._compiled_patterns:
            matches = list(pat.finditer(work_text))
            if not matches:
                continue
            candidate_ids = self.alias_map[norm_al]
            ambiguous = len(candidate_ids) > 1
            for eid in candidate_ids:
                if eid not in seen:
                    seen.add(eid)
                    info = self.entities[eid]
                    detected.append(
                        {
                            "entity_id": info.entity_id,
                            "name": info.name,
                            "category": info.category,
                            "matched_text": norm_al,
                            "ambiguous": ambiguous,
                        }
                    )
            chars = list(work_text)
            for m in matches:
                for idx in range(m.start(), m.end()):
                    chars[idx] = " "
            work_text = "".join(chars)
        return detected

    def count(self, text: str, weighted: bool = True) -> Dict[str, float]:
        counts: Dict[str, float] = {}
        for m in self.find_mentions(text):
            counts[m.entity_id] = counts.get(m.entity_id, 0.0) + (m.weight if weighted else 1.0)
        return counts
