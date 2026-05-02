"""Test the document loading and chunking pipeline end-to-end."""

from pathlib import Path

from careerrag.rag.chunker import MAX_CHUNK_SIZE, chunk_document
from careerrag.rag.loader import load_document

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _verify_pipeline(path: Path) -> None:
    result = load_document(path)
    chunks = chunk_document(result.text, result.source)
    assert len(chunks) > 0
    assert all(len(chunk.text) <= MAX_CHUNK_SIZE for chunk in chunks)
    assert all(chunk.metadata["source"] == path.name for chunk in chunks)
    sections = {chunk.metadata["section"] for chunk in chunks}
    assert len(sections) > 1


def test_pdf_pipeline() -> None:
    """Load a PDF resume, chunk it, and verify structure."""
    _verify_pipeline(FIXTURES_DIR / "sample-resume.pdf")


def test_docx_pipeline() -> None:
    """Load a DOCX resume, chunk it, and verify structure."""
    _verify_pipeline(FIXTURES_DIR / "sample-resume.docx")
