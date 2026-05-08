"""Run the CareerRAG command-line interface."""

import asyncio
import os
import shutil
import subprocess
import sys
from pathlib import Path

import chromadb
import typer
import uvicorn

from careerrag.config import DEFAULT_CONFIG, load_config, save_config
from careerrag.rag.chunker import chunk_document
from careerrag.rag.indexer import get_or_create_collection, index_chunks
from careerrag.rag.loader import load_document
from careerrag.rag.pipeline import stream_response
from careerrag.rag.tracing import initialize_tracing
from careerrag.server.app import ServerConfig, create_app

API_KEY_ENV_VAR = "ANTHROPIC_API_KEY"
LAUNCHPAD_BINARY = "launchpad"
SERVICE_NAME = "careerrag"
SUPPORTED_EXTENSIONS = {".docx", ".md", ".pdf", ".txt"}

cli = typer.Typer(help="RAG-powered chat interface for career profiles")


@cli.command()
def init() -> None:
    """Create a default configuration file."""
    save_config(config=DEFAULT_CONFIG)
    typer.echo(
        "Created .careerrag/config.yml. Review settings before running other commands."
    )


def _index_documents(docs_path: Path, config: dict[str, object]) -> chromadb.Collection:
    store = str(config["vector_store"])
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
    """Answer a question from indexed documents."""
    config = load_config()
    store = str(config["vector_store"])
    collection = get_or_create_collection(path=store)

    async def _run() -> None:
        async for token in stream_response(collection=collection, question=question):
            typer.echo(token, nl=False)
        typer.echo()

    asyncio.run(_run())


@cli.command()
def serve(
    docs: Path | None = typer.Option(None, help="Path to the documents directory"),
) -> None:
    """Start the web server, indexing documents if provided."""
    config = load_config()
    phoenix_port = int(config["phoenix_port"])
    initialize_tracing(port=phoenix_port)
    store = str(config["vector_store"])
    collection = get_or_create_collection(path=store)
    if docs:
        _index_documents(docs_path=docs, config=config)
    if collection.count() == 0:
        typer.echo("No documents indexed. Pass --docs <directory> to index documents.")
        raise typer.Exit(code=1)
    name = str(config["username"])
    server_config = ServerConfig(collection=collection, name=name)
    host = str(config["server_host"])
    port = int(config["server_port"])
    web_app = create_app(config=server_config)
    uvicorn.run(app=web_app, host=host, port=port)


def _check_launchpad() -> None:
    if not shutil.which(LAUNCHPAD_BINARY):
        typer.echo("launchpad CLI not found.")
        raise typer.Exit(code=1)


def _build_deploy_command() -> list[str]:
    venv_bin = Path(sys.executable).parent
    binary_path = venv_bin / SERVICE_NAME
    working_directory = str(Path.cwd())
    command = [
        LAUNCHPAD_BINARY,
        "service",
        "create",
        "--name",
        SERVICE_NAME,
        "--cmd",
        str(binary_path) + " serve",
        "--dir",
        working_directory,
    ]
    api_key = os.environ.get(API_KEY_ENV_VAR, "")
    if api_key:
        command.extend(["--env", f"{API_KEY_ENV_VAR}={api_key}"])
    return command


@cli.command()
def deploy() -> None:
    """Deploy the application as a background service."""
    _check_launchpad()
    command = _build_deploy_command()
    subprocess.run(command, check=True)


if __name__ == "__main__":
    cli()
