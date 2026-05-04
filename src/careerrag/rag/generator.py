"""Stream answers from an LLM using Ollama or Claude."""

import json
from collections.abc import AsyncGenerator

import httpx
from anthropic import AsyncAnthropic

from careerrag.config import load_config
from careerrag.rag.util import PROVIDER_CLAUDE, PROVIDER_OLLAMA

DEFAULT_CLAUDE_MODEL = "claude-sonnet-4-20250514"
DEFAULT_OLLAMA_MODEL = "llama3.2"
MAX_RESPONSE_TOKENS = 4096


async def _stream_ollama(
    system: str, message: str, model: str
) -> AsyncGenerator[str, None]:
    config = load_config()
    ollama_url = str(config["ollama_url"])
    async with (
        httpx.AsyncClient() as client,
        client.stream(
            method="POST",
            url=ollama_url,
            json={
                "messages": [
                    {"content": system, "role": "system"},
                    {"content": message, "role": "user"},
                ],
                "model": model,
                "stream": True,
            },
        ) as response,
    ):
        async for line in response.aiter_lines():
            if line:
                chunk = json.loads(line)
                token = chunk.get("message", {}).get("content", "")
                if token:
                    yield token


async def _stream_claude(
    system: str, message: str, model: str
) -> AsyncGenerator[str, None]:
    client = AsyncAnthropic()
    async with client.messages.stream(
        model=model,
        max_tokens=MAX_RESPONSE_TOKENS,
        system=system,
        messages=[{"content": message, "role": "user"}],
    ) as stream:
        async for token in stream.text_stream:
            yield token


async def stream_answer(
    system: str, message: str, provider: str = PROVIDER_OLLAMA, model: str = ""
) -> AsyncGenerator[str, None]:
    """Stream answer tokens from the configured LLM provider."""
    if provider == PROVIDER_CLAUDE:
        resolved_model = model or DEFAULT_CLAUDE_MODEL
        async for token in _stream_claude(
            system=system, message=message, model=resolved_model
        ):
            yield token
    else:
        resolved_model = model or DEFAULT_OLLAMA_MODEL
        async for token in _stream_ollama(
            system=system, message=message, model=resolved_model
        ):
            yield token
