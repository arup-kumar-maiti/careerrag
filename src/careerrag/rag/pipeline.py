"""Run the full RAG pipeline from question to streamed answer."""

from collections.abc import AsyncGenerator
from dataclasses import fields
from typing import Any

import chromadb

from careerrag.config import load_config
from careerrag.rag.generator import stream_answer
from careerrag.rag.prompt import SYSTEM_INSTRUCTION, format_user_message
from careerrag.rag.retriever import RetrievalConfig, query_chunks

_TYPE_MAP: dict[str, type[Any]] = {"bool": bool, "float": float, "int": int}


def _build_retrieval_config(config: dict[str, Any]) -> RetrievalConfig:
    overrides = {}
    for field in fields(RetrievalConfig):
        if field.name in config:
            converter = (
                _TYPE_MAP.get(field.type, str)
                if isinstance(field.type, str)
                else field.type
            )
            overrides[field.name] = converter(config[field.name])
    return RetrievalConfig(**overrides)


async def stream_response(
    collection: chromadb.Collection, question: str
) -> AsyncGenerator[str, None]:
    """Stream answer tokens for a question against the given collection."""
    config = load_config()
    retrieval_config = _build_retrieval_config(config=config)
    chunks = query_chunks(
        collection=collection, question=question, config=retrieval_config
    )
    message = format_user_message(question=question, chunks=chunks)
    async for token in stream_answer(
        system=SYSTEM_INSTRUCTION,
        message=message,
        provider=str(config["provider"]),
        model=str(config["model"]),
    ):
        yield token
