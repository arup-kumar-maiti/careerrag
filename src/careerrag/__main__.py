"""Run the CareerRAG command-line interface."""

import asyncio
from pathlib import Path

import chromadb
import typer
import uvicorn

from careerrag.config import load_config
from careerrag.rag.chunker import chunk_document
from careerrag.rag.indexer import get_or_create_collection, index_chunks
from careerrag.rag.loader import load_document
from careerrag.rag.pipeline import stream_response
from careerrag.server.app import ServerConfig, create_app

SUPPORTED_EXTENSIONS = {".docx", ".md", ".pdf", ".txt"}

cli = typer.Typer(help="RAG-powered chat interface for career profiles")


def _index_documents(docs_path: Path, config: dict[str, object]) -> chromadb.Collection:
    store = str(config["store"])
    collection = get_or_create_collection(path=store)
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
) -> None:
    """Index documents into the vector store."""
    config = load_config()
    _index_documents(docs_path=docs, config=config)


@cli.command()
def query(
    question: str = typer.Option(..., help="Question to ask"),
) -> None:
    """Stream an answer for the given question."""
    config = load_config()
    store = str(config["store"])
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
) -> None:
    """Start the web server, indexing documents if provided."""
    config = load_config()
    store = str(config["store"])
    collection = get_or_create_collection(path=store)
    if docs:
        _index_documents(docs_path=docs, config=config)
    if collection.count() == 0:
        typer.echo("No documents indexed. Pass --docs <directory> to index documents.")
        raise typer.Exit(code=1)
    server_config = ServerConfig(collection=collection, name=name)
    host = str(config["host"])
    port = int(config["port"])
    web_app = create_app(config=server_config)
    uvicorn.run(app=web_app, host=host, port=port)


if __name__ == "__main__":
    cli()
