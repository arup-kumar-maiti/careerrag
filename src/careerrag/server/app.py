"""Serve the CareerRAG chat application."""

import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel

APP_TITLE = "CareerRAG"
CONTENT_TYPE_SSE = "text/event-stream"
DONE_SIGNAL = "data: [DONE]\n\n"
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
MOCK_RESPONSE = (
    "This is a placeholder response streamed from the backend. "
    "Once the RAG pipeline is connected, answers will be grounded "
    "in the uploaded documents."
)
STREAM_CHUNK_DELAY = 0.02


class ChatRequest(BaseModel):
    """Represent an incoming chat message."""

    message: str


def _render_template(environment: Environment, name: str) -> str:
    template = environment.get_template("chat.html")
    return template.render(name=name)


async def _stream_mock_response() -> AsyncGenerator[str, None]:
    words = MOCK_RESPONSE.split(" ")
    for i, word in enumerate(words):
        token = word if i == 0 else " " + word
        yield f"data: {token}\n\n"
        await asyncio.sleep(STREAM_CHUNK_DELAY)
    yield DONE_SIGNAL


def create_app(name: str) -> FastAPI:
    """Return a configured FastAPI application."""
    app = FastAPI(title=APP_TITLE)
    app.mount(
        "/static",
        StaticFiles(directory=FRONTEND_DIR / "static"),
        name="static",
    )

    templates = Environment(
        autoescape=True,
        loader=FileSystemLoader(FRONTEND_DIR / "templates"),
    )

    @app.get("/", response_class=HTMLResponse)
    async def render_index() -> str:
        return _render_template(templates, name)

    @app.post("/api/chat")
    async def handle_chat(request: ChatRequest) -> StreamingResponse:
        return StreamingResponse(
            _stream_mock_response(),
            media_type=CONTENT_TYPE_SSE,
        )

    return app
