"""Index and retrieve document chunks using ChromaDB."""

import hashlib
from typing import TYPE_CHECKING, cast

import chromadb

from careerrag.rag.chunker import Chunk

if TYPE_CHECKING:
    from chromadb.api.types import Metadata

COLLECTION_NAME = "career_chunks"
DEFAULT_STORE_PATH = ".careerrag/store"
QUERY_RESULT_LIMIT = 5


def _generate_chunk_id(source: str, section: str, text: str) -> str:
    content = f"{source}:{section}:{text}"
    return hashlib.sha256(content.encode()).hexdigest()


def create_collection(path: str = DEFAULT_STORE_PATH) -> chromadb.Collection:
    """Return a ChromaDB collection backed by persistent storage at the given path."""
    client = chromadb.PersistentClient(path=path)
    return client.get_or_create_collection(name=COLLECTION_NAME)


def index_chunks(collection: chromadb.Collection, chunks: list[Chunk]) -> int:
    """Upsert chunks into the collection and return the count stored."""
    if not chunks:
        return 0
    ids = [
        _generate_chunk_id(
            chunk.metadata["source"], chunk.metadata["section"], chunk.text
        )
        for chunk in chunks
    ]
    documents = [chunk.text for chunk in chunks]
    metadatas = cast("list[Metadata]", [chunk.metadata for chunk in chunks])
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return len(chunks)


def query_chunks(
    collection: chromadb.Collection, question: str, limit: int = QUERY_RESULT_LIMIT
) -> list[Chunk]:
    """Return the most relevant chunks for the given question."""
    results = collection.query(
        query_texts=[question],
        n_results=limit,
        include=["documents", "metadatas"],
    )
    chunks: list[Chunk] = []
    documents = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    for text, metadata in zip(documents, metadatas, strict=True):
        chunks.append(
            Chunk(
                metadata={key: str(value) for key, value in metadata.items()},
                text=str(text),
            )
        )
    return chunks


def remove_source(collection: chromadb.Collection, source: str) -> None:
    """Delete all chunks from the given source document."""
    collection.delete(where={"source": source})
