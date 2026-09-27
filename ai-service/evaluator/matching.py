"""
Concept coverage + semantic similarity.

This is the DETERMINISTIC half of the evaluation engine. It never calls an LLM.
Everything here is reproducible: same input -> same numbers, every time.
That property is what makes the score defensible to a judge.

Two backends:
  1. sentence-transformers (all-MiniLM-L6-v2) if installed -- semantic matching,
     so "token expiry" matches "short-lived access tokens".
  2. Lexical fallback (token overlap + fuzzy ratio) if the model is unavailable.
     Slightly blunter, but the service still runs offline. Never crashes.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Iterable, Sequence

# Concept is "covered" at or above this similarity.
COVERAGE_THRESHOLD = 0.55
# Below this, a concept is definitely absent (used for the partial-credit band).
PARTIAL_THRESHOLD = 0.40

_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being", "and",
    "or", "but", "if", "then", "than", "that", "this", "these", "those", "of",
    "to", "in", "on", "for", "with", "as", "by", "at", "from", "it", "its",
    "we", "i", "you", "they", "he", "she", "do", "does", "did", "can", "could",
    "will", "would", "should", "have", "has", "had", "not", "no", "so", "also",
    "there", "their", "which", "when", "how", "what", "why", "about",
}


def tokenize(text: str) -> list[str]:
    """Lowercase word tokens, stopwords removed, 2+ chars."""
    words = re.findall(r"[a-z0-9_+#.]+", (text or "").lower())
    return [w for w in words if len(w) > 1 and w not in _STOPWORDS]


# ---------------------------------------------------------------------------
# Embedding backend (optional)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _load_model():
    """
    Load MiniLM once. Returns None if unavailable -- caller falls back to lexical.
    Cached so the model is never loaded twice in one process.
    """
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        return SentenceTransformer("all-MiniLM-L6-v2")
    except Exception:
        return None


def embedding_backend_available() -> bool:
    return _load_model() is not None


def _embed(texts: Sequence[str]):
    model = _load_model()
    if model is None:
        return None
    import numpy as np

    vecs = model.encode(list(texts), normalize_embeddings=True)
    return np.asarray(vecs, dtype="float32")


# ---------------------------------------------------------------------------
# Similarity
# ---------------------------------------------------------------------------

def _token_match(a: str, b: str) -> float:
    """Fuzzy match between two single tokens. Handles rotate/rotation, token/tokens."""
    if a == b:
        return 1.0
    # Shared stem: 'rotation' vs 'rotate' share 'rotat'.
    n = min(len(a), len(b))
    prefix = 0
    while prefix < n and a[prefix] == b[prefix]:
        prefix += 1
    if prefix >= 4 and prefix >= 0.6 * n:
        return 0.9
    ratio = SequenceMatcher(None, a, b).ratio()
    return ratio if ratio >= 0.8 else 0.0


def _lexical_similarity(concept: str, text: str) -> float:
    """
    Directional similarity: how much of `concept` appears in `text`.

    Deterministic, no model needed. Each concept token finds its best fuzzy
    match among the text's tokens; the mean of those is the score. Directional
    on purpose -- a 200-word answer containing the concept should score high,
    and symmetric overlap would punish it for its length.
    """
    ca, tb = tokenize(concept), tokenize(text)
    if not ca or not tb:
        return 0.0
    per_token = [max((_token_match(c, t) for t in tb), default=0.0) for c in ca]
    mean = sum(per_token) / len(per_token)
    # Small bonus when the concept appears as a contiguous phrase.
    if concept.lower().strip() in (text or "").lower():
        mean = max(mean, 0.85)
    return max(0.0, min(1.0, mean))


def semantic_similarity(a: str, b: str) -> float:
    """Cosine similarity if embeddings are available, else lexical. [0, 1]."""
    if not (a or "").strip() or not (b or "").strip():
        return 0.0
    vecs = _embed([a, b])
    if vecs is None:
        return _lexical_similarity(a, b)
    cos = float(vecs[0] @ vecs[1])
    # MiniLM cosines are roughly [-1, 1]; clamp negatives to 0.
    return max(0.0, min(1.0, cos))


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?;\n])\s+", (text or "").strip())
    out = [p.strip() for p in parts if len(p.strip()) > 2]
    return out or ([text.strip()] if (text or "").strip() else [])


# ---------------------------------------------------------------------------
# Concept coverage
# ---------------------------------------------------------------------------

class ConceptMatch:
    """One expected concept, and how well the answer covered it."""

    __slots__ = ("concept", "score", "evidence")

    def __init__(self, concept: str, score: float, evidence: str) -> None:
        self.concept = concept
        self.score = round(score, 4)
        self.evidence = evidence

    @property
    def covered(self) -> bool:
        return self.score >= COVERAGE_THRESHOLD

    @property
    def partial(self) -> bool:
        return PARTIAL_THRESHOLD <= self.score < COVERAGE_THRESHOLD

    def as_dict(self) -> dict:
        return {
            "concept": self.concept,
            "score": self.score,
            "covered": self.covered,
            "partial": self.partial,
            "evidence": self.evidence,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ConceptMatch {self.concept!r} {self.score:.2f}>"


def match_concepts(answer: str, expected_concepts: Iterable[str]) -> list[ConceptMatch]:
    """
    For each expected concept, find the best-matching sentence in the answer.

    Sentence-level rather than whole-answer, so a long rambling answer that
    happens to nail one concept in one sentence gets credit for it -- and a
    verbose answer doesn't dilute its own similarity score.
    """
    concepts = [c for c in (expected_concepts or []) if (c or "").strip()]
    if not concepts:
        return []

    sents = _sentences(answer)
    if not sents:
        return [ConceptMatch(c, 0.0, "") for c in concepts]

    matches: list[ConceptMatch] = []

    vecs = _embed(list(concepts) + sents)
    if vecs is not None:
        cvecs, svecs = vecs[: len(concepts)], vecs[len(concepts):]
        sims = cvecs @ svecs.T  # (n_concepts, n_sentences)
        for i, concept in enumerate(concepts):
            j = int(sims[i].argmax())
            matches.append(
                ConceptMatch(concept, max(0.0, float(sims[i][j])), sents[j])
            )
        return matches

    for concept in concepts:
        best_score, best_sent = 0.0, ""
        for s in sents:
            sc = _lexical_similarity(concept, s)
            if sc > best_score:
                best_score, best_sent = sc, s
        matches.append(ConceptMatch(concept, best_score, best_sent))
    return matches


def coverage_ratio(matches: Sequence[ConceptMatch]) -> float:
    """
    Fraction of expected concepts covered, with half credit for partials.
    Returns 0.0 for an empty concept list (no concepts -> nothing proven).
    """
    if not matches:
        return 0.0
    score = sum(1.0 if m.covered else 0.5 if m.partial else 0.0 for m in matches)
    return score / len(matches)
