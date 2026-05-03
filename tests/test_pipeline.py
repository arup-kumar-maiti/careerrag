"""Test the document loading, chunking, and retrieval pipeline."""

import tempfile
from pathlib import Path

from careerrag.rag.chunker import MAX_CHUNK_SIZE, chunk_document
from careerrag.rag.constant import METADATA_SECTION, METADATA_SOURCE
from careerrag.rag.loader import load_document
from careerrag.rag.retriever import (
    create_collection,
    index_chunks,
    query_chunks,
    remove_source,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _verify_pipeline(path: Path) -> None:
    document = load_document(path)
    chunks = chunk_document(document)
    assert len(chunks) > 0
    assert all(len(chunk.text) <= MAX_CHUNK_SIZE for chunk in chunks)
    assert all(chunk.metadata[METADATA_SOURCE] == path.name for chunk in chunks)
    sections = {chunk.metadata[METADATA_SECTION] for chunk in chunks}
    assert len(sections) > 1
    with tempfile.TemporaryDirectory() as store_path:
        collection = create_collection(path=store_path)
        index_chunks(collection, chunks)
        results = query_chunks(collection, "experience")
        assert len(results) > 0
        assert results[0].metadata[METADATA_SOURCE] == path.name
        contact_results = query_chunks(collection, "contact information", limit=1)
        assert any("@" in result.text for result in contact_results)
        index_chunks(collection, chunks)
        assert collection.count() == len(chunks)
        remove_source(collection, path.name)
        assert collection.count() == 0


def test_pdf_pipeline() -> None:
    """Load, chunk, index, query, re-index, and remove a PDF resume."""
    _verify_pipeline(FIXTURES_DIR / "sample-resume.pdf")


def test_docx_pipeline() -> None:
    """Load, chunk, index, query, re-index, and remove a DOCX resume."""
    _verify_pipeline(FIXTURES_DIR / "sample-resume.docx")
