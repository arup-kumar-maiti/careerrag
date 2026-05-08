"""Define shared types, constants, and helpers for the RAG pipeline."""

from dataclasses import dataclass, field

KIND_BODY = "body"
KIND_CONTACT = "contact"
KIND_HEADING = "heading"
KIND_LIST_ITEM = "list_item"
METADATA_SECTION = "section"
METADATA_SOURCE = "source"
PROVIDER_CLAUDE = "claude"
PROVIDER_OLLAMA = "ollama"
SPAN_DIVERSITY = "diversity_selection"
SPAN_FUSION = "fusion"
SPAN_GENERATION = "generation"
SPAN_KEYWORD_SEARCH = "keyword_search"
SPAN_RERANKING = "reranking"
SPAN_RETRIEVAL = "retrieval_pipeline"
SPAN_STREAM = "stream_response"
SPAN_VECTOR_SEARCH = "vector_search"


@dataclass
class DocumentElement:
    """Represent a structural element of a document."""

    kind: str
    text: str


@dataclass
class LoadedDocument:
    """Represent a parsed document with structured elements."""

    elements: list[DocumentElement]
    source: str


@dataclass
class Chunk:
    """Represent a document chunk with metadata."""

    metadata: dict[str, str] = field(default_factory=dict)
    text: str = ""


@dataclass
class ScoredChunk:
    """Represent a chunk with a relevance score and optional embedding."""

    chunk: Chunk
    embedding: list[float] = field(default_factory=list)
    score: float = 0.0


def build_scored_chunk(
    metadata: object, text: object, embedding: object, score: float
) -> ScoredChunk:
    """Return a ScoredChunk from raw ChromaDB result fields."""
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
