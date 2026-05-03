"""Rescore document chunks using a cross-encoder model."""

from typing import Any

from careerrag.rag.util import ScoredChunk

CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_cache: dict[str, Any] = {}


def _load_cross_encoder() -> Any:
    if "model" not in _cache:
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as error:
            raise ImportError(
                "Reranking requires sentence-transformers."
                " Install with: pip install careerrag[rerank]."
            ) from error
        _cache["model"] = CrossEncoder(CROSS_ENCODER_MODEL)
    return _cache["model"]


def rerank_chunks(
    question: str, candidates: list[ScoredChunk], limit: int
) -> list[ScoredChunk]:
    """Rescore candidates with a cross-encoder and return the top results."""
    cross_encoder = _load_cross_encoder()
    pairs = [[question, scored.chunk.text] for scored in candidates]
    scores: list[float] = cross_encoder.predict(pairs).tolist()
    for scored, new_score in zip(candidates, scores, strict=True):
        scored.score = new_score
    candidates.sort(key=lambda scored: scored.score, reverse=True)
    return candidates[:limit]
