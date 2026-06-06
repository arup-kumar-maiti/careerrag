# Changelog

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.0] - 2026-06-06

### Added

- Boilerplate filtering for short fragments, contact blocks, and all-question chunks.
- Explicit embedding model configuration in indexer with `BAAI/bge-large-en-v1.5`.
- Near-duplicate deduplication with word-overlap threshold before diversity selection.
- Priority source boosting in fusion ranking.
- Section metadata enrichment in indexed documents for improved search coverage.

### Changed

- Default `candidate_count` from 40 to 60.
- Diversity selection from file-level to section-level caps for finer-grained control.
- Diversity source cap from soft fallback to hard limit.

### Fixed

- Contact info chunks bypassing the boilerplate filter due to bare domains and phone numbers.
- Duplicate section prefix in LLM context by stripping enriched text on retrieval.
- Stale `candidate_count` default in README.

## [1.4.0] - 2026-05-09

### Added

- `log_step` decorator in `observer.py` for automatic retrieval pipeline logging.
- Structured logging for query, chunk count, scores, and metadata at each retrieval step.

### Changed

- Replace Phoenix tracing with Python `logging` via decorator.

### Removed

- Arize Phoenix and OpenTelemetry tracing dependencies.
- `phoenix_port` configuration key.
- `tracing.py` module.

### Fixed

- Rewrite docstrings across the codebase to describe what functions do, not what they return.

## [1.3.0] - 2026-05-09

### Added

- `deploy` command to install as a systemd service via launchpad.

### Changed

- Rewrite deployment guide for systemd-based workflow.

## [1.2.3] - 2026-05-08

### Fixed

- Bind Phoenix to `0.0.0.0` for container accessibility.

## [1.2.2] - 2026-05-08

### Fixed

- Use `PHOENIX_PORT` environment variable instead of deprecated `port` parameter.

## [1.2.1] - 2026-05-08

### Fixed

- Upgrade pip in Dockerfile to resolve arize-phoenix dependency conflicts.

## [1.2.0] - 2026-05-08

### Added

- Deployment guide for VPS with Dokploy and Cloudflare.
- Phoenix tracing UI for retrieval pipeline observability.
- `trace_step` decorator for automatic OpenTelemetry span instrumentation.
- Tracing spans for vector search, keyword search, fusion, reranking, diversity selection, and generation.

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
