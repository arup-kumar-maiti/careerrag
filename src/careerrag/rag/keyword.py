"""Search document chunks by keyword matching using BM25."""

import chromadb
from rank_bm25 import BM25Okapi

from careerrag.rag.util import ScoredChunk, build_scored_chunk


def search_keyword(
    collection: chromadb.Collection, question: str, limit: int
) -> list[ScoredChunk]:
    """Return chunks ranked by keyword relevance to the question."""
    all_docs = collection.get(include=["documents", "embeddings", "metadatas"])
    documents = all_docs.get("documents") or []
    if not documents:
        return []
    raw_embeddings = all_docs.get("embeddings")
    embeddings = list(raw_embeddings) if raw_embeddings is not None else []
    metadatas = all_docs.get("metadatas") or []
    tokenized = [document.lower().split() for document in documents]
    index = BM25Okapi(tokenized)
    scores = list(index.get_scores(question.lower().split()))
    ranked = sorted(
        range(len(scores)), key=lambda position: scores[position], reverse=True
    )[:limit]
    return [
        build_scored_chunk(
            metadata=metadatas[position] if position < len(metadatas) else {},
            text=documents[position],
            embedding=embeddings[position] if position < len(embeddings) else [],
            score=scores[position],
        )
        for position in ranked
        if scores[position] > 0
    ]
