from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, Optional, Set
from app.services.preprocessing import normalize_text

@dataclass(frozen=True)
class EntityInfo:
    entity_id: str
    name: str
    category: str

@dataclass(frozen=True)
class Mention:
    entity_id: str
    matched_text: str
    start: int
    end: int
    weight: float  # 1 / number of candidate entities for this alias (ambiguity penalty)

class EntityDictionary:
    def __init__(
        self,
        entities: Iterable[Mapping],
        aliases: Iterable[Mapping],
    ) -> None:
        self.entities: Dict[str, EntityInfo] = {
            str(e["entity_id"]): EntityInfo(
                str(e["entity_id"]), e["canonical_name"], e.get("category") or ""
            )
            for e in entities
        }
        alias_sets: Dict[str, Set[str]] = {}

        def add(alias: Optional[str], entity_id: str) -> None:
            key = normalize_text(alias or "")
            if key:
                alias_sets.setdefault(key, set()).add(entity_id)

        for info in self.entities.values():
            add(info.name, info.entity_id)
        for a in aliases:
            eid = str(a["entity_id"])
            if eid in self.entities:
                add(a.get("alias"), eid)
                add(a.get("normalized_alias"), eid)

        self.alias_map: Dict[str, List[str]] = {k: sorted(v) for k, v in alias_sets.items()}
        self._pattern: Optional[re.Pattern] = None
        if self.alias_map:
            ordered = sorted(self.alias_map, key=lambda s: (-len(s), s))
            self._pattern = re.compile(
                r"\b(?:" + "|".join(re.escape(a) for a in ordered) + r")\b"
            )

    def find_mentions(self, text: str) -> List[Mention]:
        if not self._pattern:
            return []
        norm = normalize_text(text)
        mentions: List[Mention] = []
        for m in self._pattern.finditer(norm):
            ids = self.alias_map[m.group(0)]
            weight = 1.0 / len(ids)
            for eid in ids:
                mentions.append(Mention(eid, m.group(0), m.start(), m.end(), weight))
        return mentions

    def count(self, text: str, weighted: bool = True) -> Dict[str, float]:
        # entity_id -> number of mentions; ambiguous aliases count 1/n when weighted
        counts: Dict[str, float] = {}
        for m in self.find_mentions(text):
            counts[m.entity_id] = counts.get(m.entity_id, 0.0) + (m.weight if weighted else 1.0)
        return counts
