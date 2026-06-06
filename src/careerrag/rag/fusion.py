"""Merge ranked results from multiple search methods."""

from careerrag.rag.observer import log_step
from careerrag.rag.util import METADATA_SOURCE, ScoredChunk

PRIORITY_FUSION_BOOST = 0.03
RANK_SMOOTHING_FACTOR = 60


@log_step
def fuse_rankings(
    ranked_lists: list[list[ScoredChunk]], priority_source: str = ""
) -> list[ScoredChunk]:
    """Merge multiple ranked result lists into a single ranking."""
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
    if priority_source:
        for chunk_id, scored in chunk_map.items():
            source = scored.chunk.metadata.get(METADATA_SOURCE, "")
            if source == priority_source:
                fusion_scores[chunk_id] += PRIORITY_FUSION_BOOST
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
