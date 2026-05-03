"""Merge ranked results from multiple search methods using reciprocal rank fusion."""

from careerrag.rag.util import ScoredChunk

RRF_K_PARAMETER = 60


def fuse_rankings(ranked_lists: list[list[ScoredChunk]]) -> list[ScoredChunk]:
    """Merge multiple ranked result lists using reciprocal rank fusion."""
    chunk_map: dict[str, ScoredChunk] = {}
    rrf_scores: dict[str, float] = {}
    for ranked_list in ranked_lists:
        for rank, scored in enumerate(ranked_list, start=1):
            chunk_id = scored.chunk.text
            if chunk_id not in chunk_map:
                chunk_map[chunk_id] = scored
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + 1 / (
                RRF_K_PARAMETER + rank
            )
    sorted_ids = sorted(rrf_scores, key=lambda cid: rrf_scores[cid], reverse=True)
    return [
        ScoredChunk(
            chunk=chunk_map[chunk_id].chunk,
            embedding=chunk_map[chunk_id].embedding,
            score=rrf_scores[chunk_id],
        )
        for chunk_id in sorted_ids
    ]
