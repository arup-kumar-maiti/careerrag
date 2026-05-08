"""Trace RAG pipeline steps with Phoenix and OpenTelemetry."""

import inspect
import json
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

import phoenix as px
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from careerrag.rag.util import METADATA_SECTION, METADATA_SOURCE, ScoredChunk

F = TypeVar("F", bound=Callable[..., Any])

SPAN_DIVERSITY = "diversity_selection"
SPAN_FUSION = "fusion"
SPAN_GENERATION = "generation"
SPAN_KEYWORD_SEARCH = "keyword_search"
SPAN_RERANKING = "reranking"
SPAN_RETRIEVAL = "retrieval_pipeline"
SPAN_STREAM = "stream_response"
SPAN_VECTOR_SEARCH = "vector_search"
TEXT_PREVIEW_LIMIT = 200
TRACER_NAME = "careerrag"


def _get_tracer() -> trace.Tracer:
    return trace.get_tracer(TRACER_NAME)


def _set_span_params(
    span: trace.Span,
    kwargs: dict[str, Any],
    query_param: str,
    trace_params: list[str] | None,
) -> None:
    if query_param and query_param in kwargs:
        span.set_attribute("query", str(kwargs[query_param]))
    for param in trace_params or []:
        if param in kwargs:
            span.set_attribute(param, str(kwargs[param]))


def _build_async_wrapper(
    func: F, span_name: str, query_param: str, trace_params: list[str] | None
) -> F:
    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        tracer = _get_tracer()
        with tracer.start_as_current_span(span_name) as span:
            _set_span_params(span, kwargs, query_param, trace_params)
            async for item in func(*args, **kwargs):
                yield item

    return cast("F", async_wrapper)


def _format_scored_chunks(chunks: list[ScoredChunk]) -> str:
    return json.dumps(
        [
            {
                "score": round(scored.score, 4),
                "section": scored.chunk.metadata.get(METADATA_SECTION, ""),
                "source": scored.chunk.metadata.get(METADATA_SOURCE, ""),
                "text": scored.chunk.text[:TEXT_PREVIEW_LIMIT],
            }
            for scored in chunks
        ]
    )


def _build_sync_wrapper(
    func: F, span_name: str, query_param: str, trace_params: list[str] | None
) -> F:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        tracer = _get_tracer()
        with tracer.start_as_current_span(span_name) as span:
            _set_span_params(span, kwargs, query_param, trace_params)
            result = func(*args, **kwargs)
            if isinstance(result, list):
                span.set_attribute("result_count", len(result))
                if result and isinstance(result[0], ScoredChunk):
                    span.set_attribute("results", _format_scored_chunks(result))
            return result

    return cast("F", wrapper)


def trace_step(
    span_name: str,
    query_param: str = "",
    trace_params: list[str] | None = None,
) -> Callable[[F], F]:
    """Wrap a function with a span that records retrieval results."""

    def decorator(func: F) -> F:
        if inspect.isasyncgenfunction(func):
            return _build_async_wrapper(func, span_name, query_param, trace_params)
        return _build_sync_wrapper(func, span_name, query_param, trace_params)

    return decorator


def initialize_tracing(port: int) -> None:
    """Launch Phoenix and configure OpenTelemetry to export traces."""
    px.launch_app(port=port)
    provider = TracerProvider()
    endpoint = f"http://localhost:{port}/v1/traces"
    exporter = OTLPSpanExporter(endpoint=endpoint)
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
