"""Log retrieval pipeline steps automatically via a decorator."""

import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from careerrag.rag.util import METADATA_SECTION, METADATA_SOURCE, ScoredChunk

F = TypeVar("F", bound=Callable[..., Any])

TEXT_PREVIEW_LIMIT = 200

logger = logging.getLogger(__name__)


def _log_scored_chunks(name: str, chunks: list[ScoredChunk]) -> None:
    logger.debug("%s returned %d chunks", name, len(chunks))
    for index, scored in enumerate(chunks):
        logger.debug(
            "  [%d] score=%.4f source=%s section=%s text=%s",
            index,
            scored.score,
            scored.chunk.metadata.get(METADATA_SOURCE, ""),
            scored.chunk.metadata.get(METADATA_SECTION, ""),
            scored.chunk.text[:TEXT_PREVIEW_LIMIT],
        )


def log_step(func: F) -> F:
    """Log each retrieval step automatically."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if "question" in kwargs:
            logger.info("%s query=%s", func.__name__, kwargs["question"])
        result = func(*args, **kwargs)
        if isinstance(result, list) and result and isinstance(result[0], ScoredChunk):
            _log_scored_chunks(func.__name__, result)
        elif isinstance(result, list):
            logger.debug("%s returned %d items", func.__name__, len(result))
        return result

    return cast("F", wrapper)
