"""Run the full RAG pipeline from question to streamed answer."""

from collections.abc import AsyncGenerator

import chromadb

from careerrag.rag.generator import stream_answer
from careerrag.rag.prompt import SYSTEM_INSTRUCTION, format_user_message
from careerrag.rag.retriever import query_chunks


async def stream_response(
    collection: chromadb.Collection, question: str, provider: str = "", model: str = ""
) -> AsyncGenerator[str, None]:
    """Stream answer tokens for a question against the given collection."""
    chunks = query_chunks(collection=collection, question=question)
    message = format_user_message(question=question, chunks=chunks)
    async for token in stream_answer(
        system=SYSTEM_INSTRUCTION,
        message=message,
        provider=provider,
        model=model,
    ):
        yield token
