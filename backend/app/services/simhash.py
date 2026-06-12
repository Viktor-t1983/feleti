"""SimHash — locality-sensitive hashing for de-duplication of text articles.

Computes a 64-bit fingerprint such that similar documents
produce similar hashes (differ by few bits).
"""

from __future__ import annotations

import hashlib
import re
from typing import Sequence

# Words shorter than this are ignored
_MIN_WORD_LEN = 3

# Stop words (Russian + English)
_STOP_WORDS: frozenset[str] = frozenset({
    "и", "в", "во", "не", "что", "он", "на", "я", "с", "со",
    "как", "а", "то", "все", "она", "так", "его", "но", "да",
    "ты", "к", "у", "же", "вы", "за", "бы", "по", "из", "им",
    "от", "о", "об", "для", "или", "это", "этот", "чтобы",
    "ещё", "уже", "будет", "при", "нет", "быть", "был",
    "the", "a", "an", "and", "or", "but", "in", "on", "at",
    "to", "for", "of", "with", "by", "is", "are", "was", "were",
})


def _tokenize(text: str) -> list[str]:
    """Split text into words, lowercase, filter stop-words and short words."""
    words = re.findall(r"[а-яёa-z-]+", text.lower())
    return [w for w in words if w not in _STOP_WORDS and len(w) >= _MIN_WORD_LEN]


def _hash_64(token: str) -> int:
    """Compute a 64-bit hash for a token using MD5."""
    h = hashlib.md5(token.encode("utf-8"), usedforsecurity=False)
    return int.from_bytes(h.digest()[:8], "big", signed=False)


def compute(text: str) -> int:
    """Compute 64-bit SimHash fingerprint for the given text."""
    tokens = _tokenize(text)
    if not tokens:
        return 0

    # Count term frequencies
    freqs: dict[str, int] = {}
    for t in tokens:
        freqs[t] = freqs.get(t, 0) + 1

    v = [0] * 64

    for token, freq in freqs.items():
        h = _hash_64(token)
        for i in range(64):
            if (h >> i) & 1:
                v[i] += freq
            else:
                v[i] -= freq

    fp = 0
    for i in range(64):
        if v[i] > 0:
            fp |= 1 << i

    return fp


def hamming_distance(a: int, b: int) -> int:
    """Number of differing bits between two 64-bit fingerprints."""
    x = (a ^ b) & ((1 << 64) - 1)
    # Popcount
    return x.bit_count() if hasattr(int, "bit_count") else bin(x).count("1")


def is_duplicate(fp: int, existing: Sequence[int], threshold: int = 3) -> bool:
    """Check if *fp* is a near-duplicate of any existing fingerprint."""
    for efp in existing:
        if efp == 0:
            continue
        if efp == fp:
            return True
        if hamming_distance(fp, efp) <= threshold:
            return True
    return False
