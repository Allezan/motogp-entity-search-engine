from __future__ import annotations
import re
import unicodedata
from typing import Dict, Iterable, List
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory

_URL = re.compile(r"https?://\S+|www\.\S+")
_TOKEN_RE = re.compile(r"[a-z0-9]+")
_WS = re.compile(r"\s+")

# Preserved negation words (aligned with Notebook v5 & AGENT.md Section 6)
NEGATION_WORDS = frozenset({"tidak", "bukan", "jangan", "tanpa", "belum"})

# Domain-specific extra stopwords (aligned with Notebook v5)
EXTRA_STOPWORDS = frozenset({
    "yang", "dan", "di", "ke", "dari", "ini", "itu", "dengan", "untuk", "pada", "adalah", "sebagai",
    "dalam", "atau", "juga", "akan", "telah", "sudah", "bisa", "dapat", "ada", "oleh", "karena",
    "tersebut", "lebih", "sangat", "masih", "namun", "tetapi", "tapi", "saat",
    "ketika", "setelah", "sebelum", "hingga", "sampai", "antara", "para", "ia", "dia", "mereka",
    "kami", "kita", "saya", "aku", "anda", "nya", "pun", "lah", "kah", "tah", "jadi", "menjadi",
    "buat", "kata", "ujar", "ungkap", "jelas", "tutur", "lanjut", "tambah", "sebut",
    "menurut", "dilansir", "dikutip", "kutip", "laman", "situs", "berita", "artikel", "halaman",
    "kompas", "idn", "times", "com", "id", "net", "org", "co", "uk", "www", "http", "https",
    "jakarta", "pewarta", "editor", "penulis", "reporter", "fotografer", "dok", "foto", "afp",
    "senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu",
    "januari", "februari", "maret", "april", "mei", "juni", "juli", "agustus", "september", "oktober", "november", "desember",
    "wib", "wita", "wit", "tahun", "bulan", "hari", "pekan", "jam", "menit", "detik",
    "hal", "kali", "satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan", "sepuluh",
    "pertama", "kedua", "ketiga", "keempat", "kelima", "keenam", "ketujuh", "kedelapan", "kesembilan", "kesepuluh",
    "selain", "sementara", "sedangkan", "meski", "meskipun", "walau", "walaupun", "jika", "kalau", "bila",
    "apabila", "sehingga", "agar", "supaya", "serta", "melalui", "terhadap", "tentang", "secara", "kembali",
    "terus", "langsung", "cukup", "paling", "banyak", "beberapa", "sejumlah", "seluruh", "semua", "setiap",
    "masing", "salah", "lain", "lainnya", "sendiri", "sama", "baru", "lama", "besar", "kecil", "tinggi", "rendah",
    "atas", "bawah", "depan", "belakang", "tengah", "luar", "awal", "akhir", "usai", "jelang", "menjelang",
})

# Domain normalization map (aligned 100% with Notebook v5)
TOKEN_NORMALIZATION_MAP: Dict[str, str] = {
    "pebalap": "balap", "pembalap": "balap", "membalap": "balap", "balapan": "balap", "pembalapnya": "balap", "pebalapnya": "balap",
    "mengaspal": "aspal", "berlaga": "laga", "bertarung": "tarung", "bersaing": "saing", "persaingan": "saing",
    "memimpin": "pimpin", "pemimpin": "pimpin", "tercepat": "cepat", "kecepatan": "cepat",
    "kemenangan": "menang", "memenangi": "menang", "memenangkan": "menang", "pemenang": "menang",
    "kesalahan": "salah", "permasalahan": "masalah", "pengembangan": "kembang", "mengembangkan": "kembang",
    "keputusan": "putus", "memutuskan": "putus", "kepindahan": "pindah", "berpindah": "pindah",
    "kehadiran": "hadir", "menghadiri": "hadir", "penampilan": "tampil", "menampilkan": "tampil",
    "pencapaian": "capai", "mencapai": "capai", "capaian": "capai", "catatan": "catat", "mencatatkan": "catat", "mencatat": "catat",
    "perolehan": "oleh", "memperoleh": "oleh", "peringkat": "ringkat", "kedudukan": "duduk",
    "kesempatan": "sempat", "kemampuan": "mampu", "kekuatan": "kuat", "memperkuat": "kuat",
    "keunggulan": "unggul", "mengungguli": "unggul", "diungguli": "unggul",
    "pertandingan": "tanding", "perlombaan": "lomba", "kejuaraan": "juara", "menjuarai": "juara",
    "peluncuran": "luncur", "meluncurkan": "luncur", "meluncur": "luncur",
    "penyelenggaraan": "selenggara", "menyelenggarakan": "selenggara",
    "perbedaan": "beda", "berbeda": "beda", "membedakan": "beda",
    "perubahan": "ubah", "mengubah": "ubah", "berubah": "ubah",
    "perbaikan": "baik", "memperbaiki": "baik", "peningkatan": "tingkat", "meningkatkan": "tingkat", "meningkat": "tingkat",
    "penurunan": "turun", "menurunkan": "turun", "menurun": "turun",
    "persiapan": "siap", "menyiapkan": "siap", "kesiapan": "siap",
    "pergelangan": "gelang", "harian": "hari", "alasan": "alas", "keluhkan": "keluh", "mengeluhkan": "keluh",
    "motogp": "motogp", "moto2": "moto2", "moto3": "moto3", "fp1": "fp1", "fp2": "fp2", "q1": "q1", "q2": "q2", "f1": "f1",
    "vr46": "vr46", "rc213v": "rc213v", "rc16": "rc16", "rsgp": "rsgp", "yzrm1": "yzrm1", "desmosedici": "desmosedici",
    "mandalika": "mandalika", "silverstone": "silverstone", "aragon": "aragon", "motorland": "motorland",
    "buriram": "buriram", "sepang": "sepang", "motegi": "motegi", "sachsenring": "sachsenring", "jerez": "jerez", "assen": "assen",
    "marquez": "marquez", "bagnaia": "bagnaia", "pecco": "pecco", "martin": "martin", "bezzecchi": "bezzecchi",
    "quartararo": "quartararo", "acosta": "acosta", "bastianini": "bastianini", "bestia": "bestia",
    "aldeguer": "aldeguer", "alseguer": "aldeguer", "giannantonio": "giannantonio", "diggia": "diggia",
    "morbidelli": "morbidelli", "marini": "marini", "vinales": "vinales", "mir": "mir", "zarco": "zarco",
    "rins": "rins", "binder": "binder", "miller": "miller", "razgatlioglu": "razgatlioglu", "razgatliolu": "razgatlioglu",
    "moreira": "moreira", "espargaro": "espargaro", "savadori": "savadori", "lecuona": "lecuona", "crutchlow": "crutchlow",
    "fernandez": "fernandez", "ogura": "ogura", "rossi": "rossi", "stoner": "stoner", "lorenzo": "lorenzo", "pedrosa": "pedrosa",
}


def normalize_ascii_lower(text: str) -> str:
    """Fold accents (NFKD -> ASCII), lowercase, and collapse whitespace (preserves hyphens)."""
    folded = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode("ascii")
    return _WS.sub(" ", folded.lower()).strip()


def normalize_text(text: str) -> str:
    """Fold accents, lowercase, strip URLs and punctuation (space-separated)."""
    folded = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode("ascii").lower()
    folded = _URL.sub(" ", folded)
    tokens = _TOKEN_RE.findall(folded)
    return " ".join(tokens)


def split_tokens(text: str) -> List[str]:
    return str(text or "").split()


class TextPreprocessor:
    """Preprocessing pipeline identical to Notebook v5 (preprocess_query_or_text)."""

    def __init__(self) -> None:
        self._stemmer = StemmerFactory().create_stemmer()
        sastrawi_sw = set(StopWordRemoverFactory().get_stop_words())
        self._stopwords = frozenset((sastrawi_sw | EXTRA_STOPWORDS) - NEGATION_WORDS)
        self._stem_cache: Dict[str, str] = {}

    def warm_cache(self, tokens: Iterable[str]) -> None:
        """Pre-populate stem cache with already-stemmed corpus vocabulary tokens."""
        for tok in tokens:
            if tok:
                self._stem_cache[tok] = tok

    def _stem(self, token: str) -> str:
        cached = self._stem_cache.get(token)
        if cached is None:
            cached = self._stemmer.stem(token)
            self._stem_cache[token] = cached
        return cached

    def preprocess(self, text: str) -> List[str]:
        folded = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode("ascii").lower()
        folded = _URL.sub(" ", folded)
        tokens = _TOKEN_RE.findall(folded)

        final_tokens: List[str] = []
        for tok in tokens:
            if tok.isdigit() or len(tok) < 2:
                continue
            if tok in self._stopwords:
                continue
            if tok in TOKEN_NORMALIZATION_MAP:
                stemmed = TOKEN_NORMALIZATION_MAP[tok]
            else:
                stemmed = self._stem(tok)
                stemmed = TOKEN_NORMALIZATION_MAP.get(stemmed, stemmed)
            if stemmed and len(stemmed) >= 2 and not stemmed.isdigit() and stemmed not in self._stopwords:
                final_tokens.append(stemmed)
        return final_tokens

    def preprocess_to_string(self, text: str) -> str:
        return " ".join(self.preprocess(text))
