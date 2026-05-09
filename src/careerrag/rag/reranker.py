"""Rescore document chunks using a cross-encoder model."""

from typing import Any

from sentence_transformers import CrossEncoder

from careerrag.rag.observer import log_step
from careerrag.rag.util import ScoredChunk

CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_cache: dict[str, Any] = {}


@log_step
def rerank_chunks(
    question: str, candidates: list[ScoredChunk], limit: int
) -> list[ScoredChunk]:
    """Rescore candidates with a cross-encoder."""
    if "model" not in _cache:
        _cache["model"] = CrossEncoder(CROSS_ENCODER_MODEL)
    cross_encoder = _cache["model"]
    pairs = [[question, scored.chunk.text] for scored in candidates]
    scores: list[float] = cross_encoder.predict(pairs).tolist()
    for scored, new_score in zip(candidates, scores, strict=True):
        scored.score = new_score
    candidates.sort(key=lambda scored: scored.score, reverse=True)
    return candidates[:limit]
