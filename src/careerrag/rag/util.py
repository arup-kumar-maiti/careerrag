"""Provide shared types, constants, and helpers for the RAG pipeline."""

from dataclasses import dataclass, field

KIND_BODY = "body"
KIND_CONTACT = "contact"
KIND_HEADING = "heading"
KIND_LIST_ITEM = "list_item"
METADATA_SECTION = "section"
METADATA_SOURCE = "source"
PROVIDER_CLAUDE = "claude"
PROVIDER_OLLAMA = "ollama"


@dataclass
class DocumentElement:
    """Hold a single structural element from a parsed document."""

    kind: str
    text: str


@dataclass
class LoadedDocument:
    """Hold a fully parsed document ready for chunking."""

    elements: list[DocumentElement]
    source: str


@dataclass
class Chunk:
    """Hold a searchable text segment from a document."""

    metadata: dict[str, str] = field(default_factory=dict)
    text: str = ""


@dataclass
class ScoredChunk:
    """Pair a document chunk with its retrieval score."""

    chunk: Chunk
    embedding: list[float] = field(default_factory=list)
    score: float = 0.0


def build_scored_chunk(
    metadata: object, text: object, embedding: object, score: float
) -> ScoredChunk:
    """Convert raw query result fields into a scored chunk."""
    parsed_metadata = (
        {key: str(value) for key, value in metadata.items()}
        if isinstance(metadata, dict)
        else {}
    )
    parsed_embedding = list(embedding) if isinstance(embedding, list) else []
    return ScoredChunk(
        chunk=Chunk(metadata=parsed_metadata, text=str(text)),
        embedding=parsed_embedding,
        score=score,
    )
