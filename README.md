# CareerRAG

RAG-powered chat interface for career profiles. Load resumes, reviews, and career documents — then ask questions and get answers grounded in the actual content.

## Pipeline

```
Documents → Loader → Chunker → Retriever → LLM
```

### Loader

Convert PDF, DOCX, Markdown, and plain text into structured elements. Powered by [Docling](https://github.com/docling-project/docling) — ML-based layout detection that understands headings, tables, lists, and contact information without manual rules.

### Chunker

Split documents into retrieval-optimized chunks. Section-aware: uses document headings as boundaries so chunks stay within a single topic. Merges short paragraphs to avoid tiny fragments. Splits oversized content at sentence boundaries. Adds 20% overlap between consecutive chunks so context at boundaries is never lost.

### Retriever

Find the most relevant chunks for a question. Three-stage pipeline:

**Hybrid search** — Combines semantic search (ChromaDB embeddings via sentence-transformers) with keyword search (BM25). Semantic search understands meaning: "cloud infrastructure" finds "Azure, Synapse, Event Hubs". Keyword search catches exact terms: "Jordan's email" finds "jordan@jordanreyes.dev". Neither alone covers both — together they do.

**Reranking** *(optional)* — A cross-encoder model reads the question and each candidate chunk together, producing a precise relevance score. First-stage retrieval scores chunks independently; reranking understands the relationship between question and answer. Requires `pip install careerrag[rerank]`.

**MMR (Maximal Marginal Relevance)** — Selects diverse results. Without it, querying "leadership skills" across multiple annual reviews returns five chunks saying the same thing. MMR picks the most relevant chunk first, then each subsequent chunk must be relevant *and* different from what is already selected.

## Install

```bash
pip install careerrag
```

For cross-encoder reranking:

```bash
pip install careerrag[rerank]
```

## Supported formats

PDF, DOCX, Markdown (.md), plain text (.txt).
