"""Run the CareerRAG command-line interface."""

import asyncio
from pathlib import Path

import chromadb
import typer
import uvicorn

from careerrag.config import (
    SETTING_ANTHROPIC_API_KEY,
    SETTING_MODEL,
    SETTING_PROVIDER,
    save_setting,
)
from careerrag.rag.chunker import chunk_document
from careerrag.rag.generator import PROVIDER_CLAUDE, PROVIDER_OLLAMA
from careerrag.rag.indexer import get_or_create_collection, index_chunks
from careerrag.rag.loader import load_document
from careerrag.rag.pipeline import stream_response
from careerrag.server.app import ServerConfig, create_app

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_STORE_PATH = ".careerrag/store"
SUPPORTED_EXTENSIONS = {".docx", ".md", ".pdf", ".txt"}

cli = typer.Typer(help="RAG-powered chat interface for career profiles")


@cli.command()
def init() -> None:
    """Configure the LLM provider and credentials."""
    provider = typer.prompt("LLM provider", default=PROVIDER_OLLAMA)
    save_setting(name=SETTING_PROVIDER, value=provider)
    model = typer.prompt("Model name", default="")
    save_setting(name=SETTING_MODEL, value=model)
    if provider == PROVIDER_CLAUDE:
        api_key = typer.prompt("Anthropic API key", hide_input=True)
        save_setting(name=SETTING_ANTHROPIC_API_KEY, value=api_key)
    typer.echo("Configuration saved to system keychain.")


def _index_documents(docs_path: Path, store_path: str) -> chromadb.Collection:
    collection = get_or_create_collection(path=store_path)
    count = 0
    for file_path in sorted(docs_path.iterdir()):
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        document = load_document(path=file_path)
        chunks = chunk_document(document=document)
        count += index_chunks(collection=collection, chunks=chunks)
    typer.echo(f"Indexed {count} chunks from {docs_path}.")
    return collection


@cli.command()
def index(
    docs: Path = typer.Option(..., help="Path to the documents directory"),
    store: str = typer.Option(DEFAULT_STORE_PATH, help="Path to the vector store"),
) -> None:
    """Index documents into the vector store."""
    _index_documents(docs_path=docs, store_path=store)


@cli.command()
def query(
    question: str = typer.Option(..., help="Question to ask"),
    store: str = typer.Option(DEFAULT_STORE_PATH, help="Path to the vector store"),
) -> None:
    """Stream an answer for the given question."""
    collection = get_or_create_collection(path=store)

    async def _run() -> None:
        async for token in stream_response(collection=collection, question=question):
            typer.echo(token, nl=False)
        typer.echo()

    asyncio.run(_run())


@cli.command()
def serve(
    docs: Path | None = typer.Option(None, help="Path to the documents directory"),
    name: str = typer.Option(..., help="Name to display in the chat UI"),
    store: str = typer.Option(DEFAULT_STORE_PATH, help="Path to the vector store"),
) -> None:
    """Start the web server, indexing documents if provided."""
    collection = get_or_create_collection(path=store)
    if docs:
        _index_documents(docs_path=docs, store_path=store)
    if collection.count() == 0:
        typer.echo("No documents indexed. Pass --docs <directory> to index documents.")
        raise typer.Exit(code=1)
    config = ServerConfig(collection=collection, name=name)
    web_app = create_app(config=config)
    uvicorn.run(web_app, host=DEFAULT_HOST, port=DEFAULT_PORT)


cli()
