"""Merge ranked results from multiple search methods using reciprocal rank fusion."""

from careerrag.rag.tracing import SPAN_FUSION, trace_step
from careerrag.rag.util import ScoredChunk

RANK_SMOOTHING_FACTOR = 60


@trace_step(SPAN_FUSION)
def fuse_rankings(ranked_lists: list[list[ScoredChunk]]) -> list[ScoredChunk]:
    """Merge multiple ranked result lists using reciprocal rank fusion."""
    chunk_map: dict[str, ScoredChunk] = {}
    fusion_scores: dict[str, float] = {}
    for ranked_list in ranked_lists:
        for rank, scored in enumerate(ranked_list, start=1):
            chunk_id = scored.chunk.text
            if chunk_id not in chunk_map:
                chunk_map[chunk_id] = scored
            fusion_scores[chunk_id] = fusion_scores.get(chunk_id, 0.0) + 1 / (
                RANK_SMOOTHING_FACTOR + rank
            )
    sorted_ids = sorted(
        fusion_scores, key=lambda chunk_id: fusion_scores[chunk_id], reverse=True
    )
    return [
        ScoredChunk(
            chunk=chunk_map[chunk_id].chunk,
            embedding=chunk_map[chunk_id].embedding,
            score=fusion_scores[chunk_id],
        )
        for chunk_id in sorted_ids
    ]
