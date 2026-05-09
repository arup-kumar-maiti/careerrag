"""Select diverse document chunks using Maximal Marginal Relevance."""

import math
from dataclasses import dataclass, field

from careerrag.rag.observer import log_step
from careerrag.rag.util import METADATA_SOURCE, ScoredChunk

MAX_CHUNKS_PER_SOURCE = 3
SOURCE_REDUNDANCY_PENALTY = 0.3


@dataclass
class _DiversityState:
    """Track selection state during diversity picking."""

    selected: list[ScoredChunk] = field(default_factory=list)
    source_counts: dict[str, int] = field(default_factory=dict)


def _get_source(scored: ScoredChunk) -> str:
    return scored.chunk.metadata.get(METADATA_SOURCE, "")


def _pick_initial(
    candidates: list[ScoredChunk], remaining: list[int], state: _DiversityState
) -> None:
    best = max(remaining, key=lambda i: candidates[i].score)
    state.selected.append(candidates[best])
    source = _get_source(scored=candidates[best])
    state.source_counts[source] = state.source_counts.get(source, 0) + 1
    remaining.remove(best)


def _eligible_indices(
    candidates: list[ScoredChunk], remaining: list[int], state: _DiversityState
) -> list[int]:
    filtered = [
        i
        for i in remaining
        if state.source_counts.get(_get_source(scored=candidates[i]), 0)
        < MAX_CHUNKS_PER_SOURCE
    ]
    return filtered if filtered else remaining


def _compute_similarity(embedding_a: list[float], embedding_b: list[float]) -> float:
    dot_product = sum(x * y for x, y in zip(embedding_a, embedding_b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in embedding_a))
    norm_b = math.sqrt(sum(y * y for y in embedding_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def _score_candidate(
    candidate: ScoredChunk,
    state: _DiversityState,
    query_embedding: list[float],
    diversity_weight: float,
) -> float:
    relevance = _compute_similarity(
        embedding_a=query_embedding, embedding_b=candidate.embedding
    )
    redundancy = max(
        _compute_similarity(embedding_a=candidate.embedding, embedding_b=pick.embedding)
        for pick in state.selected
    )
    score = diversity_weight * relevance - (1 - diversity_weight) * redundancy
    source = _get_source(scored=candidate)
    score -= SOURCE_REDUNDANCY_PENALTY * state.source_counts.get(source, 0)
    return score


@log_step
def diversify_candidates(
    candidates: list[ScoredChunk],
    query_embedding: list[float],
    limit: int,
    diversity_weight: float,
) -> list[ScoredChunk]:
    """Select diverse candidates by relevance and novelty."""
    if len(candidates) <= limit:
        return candidates
    state = _DiversityState()
    remaining = list(range(len(candidates)))
    _pick_initial(candidates=candidates, remaining=remaining, state=state)
    while len(state.selected) < limit and remaining:
        eligible = _eligible_indices(
            candidates=candidates, remaining=remaining, state=state
        )
        best_index = max(
            eligible,
            key=lambda i: _score_candidate(
                candidate=candidates[i],
                state=state,
                query_embedding=query_embedding,
                diversity_weight=diversity_weight,
            ),
        )
        state.selected.append(candidates[best_index])
        source = _get_source(scored=candidates[best_index])
        state.source_counts[source] = state.source_counts.get(source, 0) + 1
        remaining.remove(best_index)
    return state.selected
