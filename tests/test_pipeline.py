"""Test the document loading, chunking, and retrieval pipeline."""

import tempfile
from pathlib import Path

import chromadb

import careerrag.config as config_module
from careerrag.config import DEFAULT_CONFIG, load_config, save_config
from careerrag.rag.chunker import MAX_CHUNK_SIZE, chunk_document
from careerrag.rag.indexer import get_or_create_collection, index_chunks, remove_source
from careerrag.rag.loader import load_document
from careerrag.rag.prompt import SYSTEM_INSTRUCTION, format_user_message
from careerrag.rag.retriever import RetrievalConfig, query_chunks
from careerrag.rag.util import METADATA_SECTION, METADATA_SOURCE, Chunk

FIXTURES_DIR = Path(__file__).parent / "fixtures"
FULL_PIPELINE_CONFIG = RetrievalConfig(
    diversity_enabled=True, rerank_enabled=True, result_count=3
)
SINGLE_RESULT_CONFIG = RetrievalConfig(
    diversity_enabled=False, rerank_enabled=False, result_count=1
)
VECTOR_ONLY_CONFIG = RetrievalConfig(
    keyword_enabled=False, diversity_enabled=False, rerank_enabled=False, result_count=3
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
        collection = get_or_create_collection(path=store_path)
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


def test_config_lifecycle() -> None:
    """Save, load, and merge configuration with defaults."""
    with tempfile.TemporaryDirectory() as tmp:
        config_dir = Path(tmp) / ".careerrag"
        config_file = config_dir / "config.yml"

        original_dir = config_module.CONFIG_DIR
        original_file = config_module.CONFIG_FILE
        config_module.CONFIG_DIR = config_dir
        config_module.CONFIG_FILE = config_file

        try:
            save_config(config=DEFAULT_CONFIG)
            assert config_file.exists()
            loaded = load_config()
            assert loaded["provider"] == "ollama"
            assert loaded["model"] == "llama3.2"
            save_config(
                config={"provider": "claude", "model": "claude-sonnet-4-20250514"}
            )
            merged = load_config()
            assert merged["provider"] == "claude"
            assert merged["model"] == "claude-sonnet-4-20250514"
            assert merged["host"] == "127.0.0.1"
        finally:
            config_module.CONFIG_DIR = original_dir
            config_module.CONFIG_FILE = original_file


def test_prompt_formatting() -> None:
    """Format chunks into a user message with section and source headers."""
    chunks = [
        Chunk(
            metadata={METADATA_SECTION: "Skills", METADATA_SOURCE: "resume.pdf"},
            text="Python, Go, Rust",
        ),
        Chunk(
            metadata={METADATA_SECTION: "Experience", METADATA_SOURCE: "resume.pdf"},
            text="Built distributed systems",
        ),
    ]
    message = format_user_message(question="What languages?", chunks=chunks)
    assert "Context:" in message
    assert "Question: What languages?" in message
    assert "[Skills | resume.pdf]" in message
    assert "[Experience | resume.pdf]" in message
    assert "Python, Go, Rust" in message
    assert SYSTEM_INSTRUCTION not in message
