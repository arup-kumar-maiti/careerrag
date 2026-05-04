# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-04

### Added

- Chat web UI with FastAPI and SSE streaming.
- ChromaDB vector store with auto-embeddings via sentence-transformers.
- CLI with init, index, query, and serve commands.
- Cross-encoder reranking for precise relevance judgments.
- Document loading via Docling for PDF, DOCX, Markdown, and plain text.
- Hybrid retrieval with vector search and BM25 keyword search.
- LLM streaming via Ollama and Claude.
- MMR diversity selection across overlapping documents.
- Reciprocal rank fusion of ranked results.
- Secret management via environment variables.
- Section-aware chunker with paragraph merging, sentence-level splitting, and overlap.
- System prompt with career-specific guardrails.
- YAML configuration file with auto-defaults.
