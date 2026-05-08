"""Search document chunks by semantic similarity using ChromaDB."""

import chromadb

from careerrag.rag.tracing import SPAN_VECTOR_SEARCH, trace_step
from careerrag.rag.util import ScoredChunk, build_scored_chunk


@trace_step(SPAN_VECTOR_SEARCH)
def search_vector(
    collection: chromadb.Collection, question: str, limit: int
) -> list[ScoredChunk]:
    """Return chunks ranked by semantic similarity to the question."""
    results = collection.query(
        query_texts=[question],
        n_results=limit,
        include=["distances", "documents", "embeddings", "metadatas"],
    )
    distances = (results.get("distances") or [[]])[0]
    documents = (results.get("documents") or [[]])[0]
    raw_embeddings = results.get("embeddings")
    embeddings = list(raw_embeddings[0]) if raw_embeddings is not None else []
    metadatas = (results.get("metadatas") or [[]])[0]
    return [
        build_scored_chunk(
            metadata=metadata, text=text, embedding=embedding, score=1 - distance
        )
        for distance, text, embedding, metadata in zip(
            distances, documents, embeddings, metadatas, strict=True
        )
    ]
