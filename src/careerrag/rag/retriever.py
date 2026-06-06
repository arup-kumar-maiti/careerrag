"""Orchestrate the retrieval pipeline for document chunks."""

import re
from dataclasses import dataclass

import chromadb

from careerrag.rag.fusion import fuse_rankings
from careerrag.rag.keyword import search_keyword
from careerrag.rag.observer import log_step
from careerrag.rag.reranker import rerank_chunks
from careerrag.rag.selector import DiversityParams, diversify_candidates
from careerrag.rag.util import Chunk, ScoredChunk
from careerrag.rag.vector import search_vector

CONTACT_PATTERNS = [
    re.compile(r"\S+@\S+\.\S+"),
    re.compile(r"https?://\S+"),
    re.compile(r"\S+\.\w{2,4}/\S+"),
    re.compile(r"[+]?\d[\d\s\-]{7,}"),
]
DEFAULT_CANDIDATE_COUNT = 60
DEFAULT_RERANK_CANDIDATE_COUNT = 50
DEFAULT_RESULT_COUNT = 12
DUPLICATE_OVERLAP_THRESHOLD = 0.8
LINK_DENSITY_THRESHOLD = 0.4
MINIMUM_SENTENCE_COUNT = 2
MINIMUM_TEXT_LENGTH = 80
QUESTION_ENDING = "?"
QUESTION_RATIO_THRESHOLD = 0.8
SENTENCE_ENDING = re.compile(r"[.?!]")


@dataclass
class RetrievalConfig:
    """Control retrieval pipeline stages and parameters."""

    candidate_count: int = DEFAULT_CANDIDATE_COUNT
    diversity_enabled: bool = True
    diversity_weight: float = 0.5
    keyword_enabled: bool = True
    priority_source: str = ""
    rerank_candidate_count: int = DEFAULT_RERANK_CANDIDATE_COUNT
    rerank_enabled: bool = False
    result_count: int = DEFAULT_RESULT_COUNT


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
        return fuse_rankings(
            ranked_lists=search_results,
            priority_source=config.priority_source.lower(),
        )
    return search_results[0]


def _is_contact_block(text: str) -> bool:
    words = text.split()
    if not words:
        return True
    contact_hits = sum(len(p.findall(text)) for p in CONTACT_PATTERNS)
    return contact_hits / len(words) >= LINK_DENSITY_THRESHOLD


def _is_all_questions(text: str) -> bool:
    endings = SENTENCE_ENDING.findall(text)
    if len(endings) < MINIMUM_SENTENCE_COUNT:
        return False
    question_count = endings.count(QUESTION_ENDING)
    return question_count / len(endings) >= QUESTION_RATIO_THRESHOLD


def _is_boilerplate(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < MINIMUM_TEXT_LENGTH:
        return True
    if _is_contact_block(text=stripped):
        return True
    return _is_all_questions(text=stripped)


def _filter_boilerplate(candidates: list[ScoredChunk]) -> list[ScoredChunk]:
    return [c for c in candidates if not _is_boilerplate(text=c.chunk.text)]


def _compute_word_overlap(text_a: str, text_b: str) -> float:
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = len(words_a & words_b)
    smaller = min(len(words_a), len(words_b))
    return intersection / smaller


def _deduplicate(candidates: list[ScoredChunk]) -> list[ScoredChunk]:
    kept: list[ScoredChunk] = []
    for candidate in candidates:
        is_duplicate = any(
            _compute_word_overlap(candidate.chunk.text, existing.chunk.text)
            >= DUPLICATE_OVERLAP_THRESHOLD
            for existing in kept
        )
        if not is_duplicate:
            kept.append(candidate)
    return kept


def _apply_diversity(
    candidates: list[ScoredChunk], config: RetrievalConfig
) -> list[ScoredChunk]:
    query_embedding = next(
        (scored.embedding for scored in candidates if scored.embedding), []
    )
    if not config.diversity_enabled or not candidates or not query_embedding:
        return candidates[: config.result_count]
    params = DiversityParams(
        diversity_weight=config.diversity_weight,
        limit=config.result_count,
        priority_source=config.priority_source.lower(),
    )
    return diversify_candidates(
        candidates=candidates,
        query_embedding=query_embedding,
        params=params,
    )


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
    candidates = _filter_boilerplate(candidates=candidates)
    candidates = _deduplicate(candidates=candidates)
    if config.rerank_enabled:
        candidates = rerank_chunks(
            question=question,
            candidates=candidates,
            limit=config.rerank_candidate_count,
        )
    candidates = _apply_diversity(candidates=candidates, config=config)
    return [scored.chunk for scored in candidates]
