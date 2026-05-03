"""Store and manage document chunks in ChromaDB."""

import hashlib
from typing import TYPE_CHECKING, cast

import chromadb

from careerrag.rag.util import METADATA_SECTION, METADATA_SOURCE, Chunk

if TYPE_CHECKING:
    from chromadb.api.types import Metadata

COLLECTION_NAME = "career_chunks"
DEFAULT_STORE_PATH = ".careerrag/store"


def create_collection(path: str = DEFAULT_STORE_PATH) -> chromadb.Collection:
    """Return a ChromaDB collection backed by persistent storage at the given path."""
    client = chromadb.PersistentClient(path=path)
    return client.get_or_create_collection(name=COLLECTION_NAME)


def _generate_chunk_id(source: str, section: str, text: str) -> str:
    content = f"{source}:{section}:{text}"
    return hashlib.sha256(content.encode()).hexdigest()


def index_chunks(collection: chromadb.Collection, chunks: list[Chunk]) -> int:
    """Upsert chunks into the collection and return the count stored."""
    if not chunks:
        return 0
    ids = [
        _generate_chunk_id(
            source=chunk.metadata[METADATA_SOURCE],
            section=chunk.metadata[METADATA_SECTION],
            text=chunk.text,
        )
        for chunk in chunks
    ]
    documents = [chunk.text for chunk in chunks]
    metadatas = cast("list[Metadata]", [chunk.metadata for chunk in chunks])
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return len(chunks)


def remove_source(collection: chromadb.Collection, source: str) -> None:
    """Delete all chunks from the given source document."""
    collection.delete(where={METADATA_SOURCE: source})
