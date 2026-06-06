"""Select diverse document chunks to reduce redundancy."""

import math
from dataclasses import dataclass, field

from careerrag.rag.observer import log_step
from careerrag.rag.util import METADATA_SECTION, METADATA_SOURCE, ScoredChunk

MAX_CHUNKS_PER_SOURCE = 3
MAX_PRIORITY_CHUNKS_PER_SOURCE = 5
PRIORITY_BOOST = 0.25
PRIORITY_RELEVANCE_THRESHOLD = 0.15
SOURCE_REDUNDANCY_PENALTY = 0.3


@dataclass
class DiversityParams:
    """Configure the diversity selection stage."""

    diversity_weight: float = 0.5
    limit: int = 12
    priority_source: str = ""


@dataclass
class _DiversityState:
    params: DiversityParams
    selected: list[ScoredChunk] = field(default_factory=list)
    source_counts: dict[str, int] = field(default_factory=dict)


def _get_source(scored: ScoredChunk) -> str:
    source = scored.chunk.metadata.get(METADATA_SOURCE, "")
    section = scored.chunk.metadata.get(METADATA_SECTION, "")
    if section:
        return f"{source}:{section}"
    return source


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
    priority = state.params.priority_source
    return [
        i
        for i in remaining
        if state.source_counts.get(_get_source(scored=candidates[i]), 0)
        < (
            MAX_PRIORITY_CHUNKS_PER_SOURCE
            if priority and _get_source(scored=candidates[i]).startswith(priority)
            else MAX_CHUNKS_PER_SOURCE
        )
    ]


def _compute_similarity(embedding_a: list[float], embedding_b: list[float]) -> float:
    dot_product = sum(x * y for x, y in zip(embedding_a, embedding_b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in embedding_a))
    norm_b = math.sqrt(sum(y * y for y in embedding_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


def _apply_priority_boost(
    state: _DiversityState, source: str, relevance: float, score: float
) -> float:
    if not state.params.priority_source or not source.startswith(
        state.params.priority_source
    ):
        return score
    if relevance < PRIORITY_RELEVANCE_THRESHOLD:
        return score
    return score + PRIORITY_BOOST


def _score_candidate(
    candidate: ScoredChunk, state: _DiversityState, query_embedding: list[float]
) -> float:
    relevance = _compute_similarity(
        embedding_a=query_embedding, embedding_b=candidate.embedding
    )
    redundancy = max(
        _compute_similarity(embedding_a=candidate.embedding, embedding_b=pick.embedding)
        for pick in state.selected
    )
    score = (
        state.params.diversity_weight * relevance
        - (1 - state.params.diversity_weight) * redundancy
    )
    source = _get_source(scored=candidate)
    score -= SOURCE_REDUNDANCY_PENALTY * state.source_counts.get(source, 0)
    return _apply_priority_boost(
        state=state, source=source, relevance=relevance, score=score
    )


def _pick_next(
    candidates: list[ScoredChunk],
    remaining: list[int],
    state: _DiversityState,
    query_embedding: list[float],
) -> bool:
    eligible = _eligible_indices(
        candidates=candidates, remaining=remaining, state=state
    )
    if not eligible:
        return False
    best_index = max(
        eligible,
        key=lambda i: _score_candidate(
            candidate=candidates[i],
            state=state,
            query_embedding=query_embedding,
        ),
    )
    state.selected.append(candidates[best_index])
    source = _get_source(scored=candidates[best_index])
    state.source_counts[source] = state.source_counts.get(source, 0) + 1
    remaining.remove(best_index)
    return True


@log_step
def diversify_candidates(
    candidates: list[ScoredChunk], query_embedding: list[float], params: DiversityParams
) -> list[ScoredChunk]:
    """Select diverse candidates by relevance and novelty."""
    if len(candidates) <= params.limit:
        return candidates
    state = _DiversityState(params=params)
    remaining = list(range(len(candidates)))
    _pick_initial(candidates=candidates, remaining=remaining, state=state)
    while len(state.selected) < params.limit and remaining:
        picked = _pick_next(
            candidates=candidates,
            remaining=remaining,
            state=state,
            query_embedding=query_embedding,
        )
        if not picked:
            break
    return state.selected
