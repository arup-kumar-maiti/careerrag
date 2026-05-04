"""Define the CareerRAG web application."""

import json
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from pathlib import Path

import chromadb
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

from careerrag.rag.pipeline import stream_response

CONTENT_TYPE_SSE = "text/event-stream"
DONE_SIGNAL = "data: [DONE]\n\n"
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
SSE_DATA_FORMAT = "data: {}\n\n"


class ChatRequest(BaseModel):
    """Represent an incoming chat message."""

    message: str


@dataclass
class ServerConfig:
    """Represent the server runtime configuration."""

    collection: chromadb.Collection
    name: str


async def _format_sse(question: str, config: ServerConfig) -> AsyncGenerator[str, None]:
    async for token in stream_response(collection=config.collection, question=question):
        yield SSE_DATA_FORMAT.format(json.dumps(token))
    yield DONE_SIGNAL


def create_app(config: ServerConfig) -> FastAPI:
    """Return a FastAPI application wired to the RAG pipeline."""
    app = FastAPI(title="CareerRAG")
    app.mount(
        path="/static",
        app=StaticFiles(directory=FRONTEND_DIR / "static"),
        name="static",
    )

    templates = Environment(
        autoescape=True,
        loader=FileSystemLoader(FRONTEND_DIR / "templates"),
    )

    @app.get("/", response_class=HTMLResponse)
    async def render_index() -> str:
        return templates.get_template("chat.html").render(name=config.name)

    @app.post("/api/chat")
    async def handle_chat(request: ChatRequest) -> StreamingResponse:
        return StreamingResponse(
            content=_format_sse(question=request.message, config=config),
            media_type=CONTENT_TYPE_SSE,
        )

    return app
