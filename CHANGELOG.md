# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-05-08

### Added

- Deployment guide for VPS with Dokploy and Cloudflare.
- Phoenix tracing UI for retrieval pipeline observability.
- Tracing spans for vector search, keyword search, fusion, reranking, diversity selection, and generation.
- `trace_step` decorator for automatic OpenTelemetry span instrumentation.

### Changed

- Change default server host from `127.0.0.1` to `0.0.0.0`.
- Move `--name` CLI flag to `username` config key with `John Doe` default.
- Pin transitive dependencies to prevent pip resolution-too-deep errors.
- Rename config keys for clarity: `host` to `server_host`, `port` to `server_port`, `store` to `vector_store`.

## [1.1.0] - 2026-05-07

### Added

- Docker image publishing to GHCR in the release workflow.
- Dockerfile with versioned build argument for container deployments.
- PyPI version and download badges in README.

### Fixed

- Add SSE streaming headers for proper event delivery.
- Deduplicate chunks before upserting to ChromaDB.

## [1.0.0] - 2026-05-04

### Added

- Chat web UI with FastAPI, SSE streaming, and markdown rendering.
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
