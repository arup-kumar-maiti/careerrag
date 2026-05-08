"""Select diverse document chunks using Maximal Marginal Relevance."""

import math

from careerrag.rag.tracing import trace_step
from careerrag.rag.util import SPAN_DIVERSITY, ScoredChunk


def _compute_similarity(embedding_a: list[float], embedding_b: list[float]) -> float:
    dot_product = sum(x * y for x, y in zip(embedding_a, embedding_b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in embedding_a))
    norm_b = math.sqrt(sum(y * y for y in embedding_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def _score_candidate_diversity(
    candidate: ScoredChunk,
    selected: list[ScoredChunk],
    query_embedding: list[float],
    diversity_weight: float,
) -> float:
    relevance = _compute_similarity(
        embedding_a=query_embedding, embedding_b=candidate.embedding
    )
    redundancy = max(
        _compute_similarity(embedding_a=candidate.embedding, embedding_b=pick.embedding)
        for pick in selected
    )
    return diversity_weight * relevance - (1 - diversity_weight) * redundancy


@trace_step(SPAN_DIVERSITY)
def diversify_candidates(
    candidates: list[ScoredChunk],
    query_embedding: list[float],
    limit: int,
    diversity_weight: float,
) -> list[ScoredChunk]:
    """Select diverse candidates by relevance and novelty."""
    if len(candidates) <= limit:
        return candidates
    selected: list[ScoredChunk] = []
    remaining = list(range(len(candidates)))
    best = max(remaining, key=lambda i: candidates[i].score)
    selected.append(candidates[best])
    remaining.remove(best)
    while len(selected) < limit and remaining:
        best_index = max(
            remaining,
            key=lambda i: _score_candidate_diversity(
                candidate=candidates[i],
                selected=selected,
                query_embedding=query_embedding,
                diversity_weight=diversity_weight,
            ),
        )
        selected.append(candidates[best_index])
        remaining.remove(best_index)
    return selected
