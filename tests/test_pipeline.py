"""Test the document loading, chunking, and retrieval pipeline."""

import tempfile
from pathlib import Path

import chromadb

from careerrag.rag.chunker import MAX_CHUNK_SIZE, chunk_document
from careerrag.rag.indexer import create_collection, index_chunks, remove_source
from careerrag.rag.loader import load_document
from careerrag.rag.retriever import RetrievalConfig, query_chunks
from careerrag.rag.util import METADATA_SECTION, METADATA_SOURCE

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FULL_PIPELINE_CONFIG = RetrievalConfig(
    mmr_enabled=True, rerank_enabled=True, result_count=3
)
SINGLE_RESULT_CONFIG = RetrievalConfig(
    mmr_enabled=False, rerank_enabled=False, result_count=1
)
VECTOR_ONLY_CONFIG = RetrievalConfig(
    keyword_enabled=False, mmr_enabled=False, rerank_enabled=False, result_count=3
)


def _verify_retrieval(collection: chromadb.Collection, source: str) -> None:
    results = query_chunks(collection=collection, question="experience")
    assert len(results) > 0
    assert results[0].metadata[METADATA_SOURCE] == source
    contact_results = query_chunks(
        collection=collection,
        question="contact information",
        config=SINGLE_RESULT_CONFIG,
    )
    assert any("@" in result.text for result in contact_results)
    vector_results = query_chunks(
        collection=collection, question="experience", config=VECTOR_ONLY_CONFIG
    )
    assert len(vector_results) > 0
    full_results = query_chunks(
        collection=collection, question="experience", config=FULL_PIPELINE_CONFIG
    )
    assert len(full_results) > 0


def _verify_pipeline(path: Path) -> None:
    document = load_document(path=path)
    chunks = chunk_document(document=document)
    assert len(chunks) > 0
    assert all(chunk.text for chunk in chunks)
    assert all(len(chunk.text) <= MAX_CHUNK_SIZE for chunk in chunks)
    assert all(chunk.metadata[METADATA_SOURCE] == path.name for chunk in chunks)
    sections = {chunk.metadata[METADATA_SECTION] for chunk in chunks}
    assert len(sections) > 1
    with tempfile.TemporaryDirectory() as store_path:
        collection = create_collection(path=store_path)
        index_chunks(collection=collection, chunks=chunks)
        _verify_retrieval(collection=collection, source=path.name)
        index_chunks(collection=collection, chunks=chunks)
        assert collection.count() == len(chunks)
        remove_source(collection=collection, source=path.name)
        assert collection.count() == 0


def test_pdf_pipeline() -> None:
    """Load, chunk, index, query, re-index, and remove a PDF resume."""
    _verify_pipeline(path=FIXTURES_DIR / "sample-resume.pdf")


def test_docx_pipeline() -> None:
    """Load, chunk, index, query, re-index, and remove a DOCX resume."""
    _verify_pipeline(path=FIXTURES_DIR / "sample-resume.docx")
