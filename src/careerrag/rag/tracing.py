"""Trace RAG pipeline steps with Phoenix and OpenTelemetry."""

import inspect
import json
import os
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

import phoenix
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from careerrag.rag.util import METADATA_SECTION, METADATA_SOURCE, ScoredChunk

F = TypeVar("F", bound=Callable[..., Any])

PHOENIX_TRACES_PATH = "/v1/traces"
TEXT_PREVIEW_LIMIT = 200
TRACER_NAME = "careerrag"


def _get_tracer() -> trace.Tracer:
    return trace.get_tracer(TRACER_NAME)


def _set_span_parameters(
    span: trace.Span,
    kwargs: dict[str, Any],
    query_parameter: str,
    trace_parameters: list[str] | None,
) -> None:
    if query_parameter and query_parameter in kwargs:
        span.set_attribute("query", str(kwargs[query_parameter]))
    for parameter in trace_parameters or []:
        if parameter in kwargs:
            span.set_attribute(parameter, str(kwargs[parameter]))


def _build_async_wrapper(
    func: F, span_name: str, query_parameter: str, trace_parameters: list[str] | None
) -> F:
    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        tracer = _get_tracer()
        with tracer.start_as_current_span(span_name) as span:
            _set_span_parameters(span, kwargs, query_parameter, trace_parameters)
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
    func: F, span_name: str, query_parameter: str, trace_parameters: list[str] | None
) -> F:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        tracer = _get_tracer()
        with tracer.start_as_current_span(span_name) as span:
            _set_span_parameters(span, kwargs, query_parameter, trace_parameters)
            result = func(*args, **kwargs)
            if isinstance(result, list):
                span.set_attribute("result_count", len(result))
                if result and isinstance(result[0], ScoredChunk):
                    span.set_attribute("results", _format_scored_chunks(result))
            return result

    return cast("F", wrapper)


def trace_step(
    span_name: str,
    query_parameter: str = "",
    trace_parameters: list[str] | None = None,
) -> Callable[[F], F]:
    """Wrap a function with a span that records retrieval results."""

    def decorator(func: F) -> F:
        if inspect.isasyncgenfunction(func):
            return _build_async_wrapper(
                func, span_name, query_parameter, trace_parameters
            )
        return _build_sync_wrapper(func, span_name, query_parameter, trace_parameters)

    return decorator


def initialize_tracing(port: int) -> None:
    """Launch Phoenix and configure OpenTelemetry to export traces."""
    os.environ["PHOENIX_HOST"] = "0.0.0.0"
    os.environ["PHOENIX_PORT"] = str(port)
    phoenix.launch_app()
    provider = TracerProvider()
    endpoint = f"http://localhost:{port}{PHOENIX_TRACES_PATH}"
    exporter = OTLPSpanExporter(endpoint=endpoint)
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
