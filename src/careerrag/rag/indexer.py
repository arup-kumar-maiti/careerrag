"""Store and manage document chunks in the vector store."""

import hashlib
from typing import TYPE_CHECKING, cast

import chromadb

from careerrag.rag.util import METADATA_SECTION, METADATA_SOURCE, Chunk

if TYPE_CHECKING:
    from chromadb.api.types import Metadata

COLLECTION_NAME = "careerrag_chunks"


def get_or_create_collection(path: str) -> chromadb.Collection:
    """Initialize the vector store collection."""
    client = chromadb.PersistentClient(path=path)
    return client.get_or_create_collection(name=COLLECTION_NAME)


def _generate_chunk_id(source: str, section: str, text: str) -> str:
    content = f"{source}:{section}:{text}"
    return hashlib.sha256(content.encode()).hexdigest()


def index_chunks(collection: chromadb.Collection, chunks: list[Chunk]) -> int:
    """Store document chunks in the vector store."""
    if not chunks:
        return 0
    seen: set[str] = set()
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[Metadata] = []
    for chunk in chunks:
        chunk_id = _generate_chunk_id(
            source=chunk.metadata[METADATA_SOURCE],
            section=chunk.metadata[METADATA_SECTION],
            text=chunk.text,
        )
        if chunk_id not in seen:
            seen.add(chunk_id)
            ids.append(chunk_id)
            documents.append(chunk.text)
            metadatas.append(cast("Metadata", chunk.metadata))
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return len(ids)


def remove_source(collection: chromadb.Collection, source: str) -> None:
    """Remove all indexed chunks for a source document."""
    collection.delete(where={METADATA_SOURCE: source.lower()})
