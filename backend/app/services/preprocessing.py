from __future__ import annotations
import re
import unicodedata
from typing import Dict, List
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

_URL = re.compile(r"https?://\S+|www\.\S+")
_NON_ALNUM = re.compile(r"[^a-z0-9\s]")
_WS = re.compile(r"\s+")

def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = _URL.sub(" ", text)
    text = _NON_ALNUM.sub(" ", text)
    return _WS.sub(" ", text).strip()

def split_tokens(text: str) -> List[str]:
    return text.split()

class TextPreprocessor:
    def __init__(self) -> None:
        self._stemmer = StemmerFactory().create_stemmer()
        self._stopwords = frozenset(StopWordRemoverFactory().get_stop_words())
        self._stem_cache: Dict[str, str] = {}

    def _stem(self, token: str) -> str:
        cached = self._stem_cache.get(token)
        if cached is None:
            cached = self._stemmer.stem(token)
            self._stem_cache[token] = cached
        return cached

    def preprocess(self, text: str) -> List[str]:
        tokens = normalize_text(text).split()
        return [
            self._stem(t)
            for t in tokens
            if len(t) > 1 and t not in self._stopwords
        ]

    def preprocess_to_string(self, text: str) -> str:
        return " ".join(self.preprocess(text))
