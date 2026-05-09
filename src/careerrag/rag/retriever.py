"""Orchestrate the retrieval pipeline for document chunks."""

from dataclasses import dataclass

import chromadb

from careerrag.rag.fusion import fuse_rankings
from careerrag.rag.keyword import search_keyword
from careerrag.rag.observer import log_step
from careerrag.rag.reranker import rerank_chunks
from careerrag.rag.selector import diversify_candidates
from careerrag.rag.util import Chunk, ScoredChunk
from careerrag.rag.vector import search_vector


@dataclass
class RetrievalConfig:
    """Control retrieval pipeline stages and parameters."""

    candidate_count: int = 20
    diversity_enabled: bool = True
    diversity_weight: float = 0.5
    keyword_enabled: bool = True
    rerank_candidate_count: int = 10
    rerank_enabled: bool = False
    result_count: int = 5


def _gather_candidates(
    collection: chromadb.Collection, question: str, config: RetrievalConfig
) -> list[ScoredChunk]:
    search_results = [
        search_vector(
            collection=collection, question=question, limit=config.candidate_count
        )
    ]
    if config.keyword_enabled:
        search_results.append(
            search_keyword(
                collection=collection, question=question, limit=config.candidate_count
            )
        )
    if len(search_results) > 1:
        return fuse_rankings(ranked_lists=search_results)
    return search_results[0]


@log_step
def query_chunks(
    collection: chromadb.Collection,
    question: str,
    config: RetrievalConfig | None = None,
) -> list[Chunk]:
    """Retrieve the most relevant chunks for the given question."""
    if config is None:
        config = RetrievalConfig()
    candidates = _gather_candidates(
        collection=collection, question=question, config=config
    )
    if config.rerank_enabled:
        candidates = rerank_chunks(
            question=question,
            candidates=candidates,
            limit=config.rerank_candidate_count,
        )
    if config.diversity_enabled and candidates and candidates[0].embedding:
        candidates = diversify_candidates(
            candidates=candidates,
            query_embedding=candidates[0].embedding,
            limit=config.result_count,
            diversity_weight=config.diversity_weight,
        )
    else:
        candidates = candidates[: config.result_count]
    return [scored.chunk for scored in candidates]
