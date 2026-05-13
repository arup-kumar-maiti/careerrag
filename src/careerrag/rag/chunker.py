"""Split structured document elements into searchable chunks."""

import re

from careerrag.rag.util import (
    KIND_HEADING,
    METADATA_SECTION,
    METADATA_SOURCE,
    Chunk,
    DocumentElement,
    LoadedDocument,
)

MAX_CHUNK_SIZE = 1000
MAX_OVERLAP_RATIO = 0.2
MIN_CHUNK_SIZE = 200
SENTENCE_TERMINATORS = re.compile(r"(?<=[.!?])\s+")
UNKNOWN_SECTION = "General"


def _group_elements_by_section(
    elements: list[DocumentElement],
) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    current_title = UNKNOWN_SECTION
    current_body: list[str] = []
    for element in elements:
        if element.kind == KIND_HEADING:
            if current_body:
                sections.append((current_title, current_body))
            current_title = element.text
            current_body = []
        else:
            current_body.append(element.text)
    if current_body:
        sections.append((current_title, current_body))
    return sections


def _merge_short_paragraphs(
    paragraphs: list[str], min_size: int, max_size: int
) -> list[str]:
    if not paragraphs:
        return []
    merged: list[str] = []
    current = paragraphs[0]
    for paragraph in paragraphs[1:]:
        combined = current + "\n" + paragraph
        if len(current) < min_size and len(combined) <= max_size:
            current = combined
        else:
            merged.append(current)
            current = paragraph
    merged.append(current)
    return merged


def _group_parts(parts: list[str], max_size: int) -> list[str]:
    if not parts:
        return []
    chunks: list[str] = []
    current = parts[0]
    for part in parts[1:]:
        combined = current + " " + part
        if len(combined) <= max_size:
            current = combined
        else:
            chunks.append(current)
            current = part
    if current:
        chunks.append(current)
    return chunks


def _split_on_spaces(text: str, max_size: int) -> list[str]:
    words = text.split(" ")
    if len(words) <= 1:
        return [text[i : i + max_size] for i in range(0, len(text), max_size)]
    return _group_parts(parts=words, max_size=max_size)


def _split_oversized(text: str, max_size: int) -> list[str]:
    if len(text) <= max_size:
        return [text]
    sentences = [
        sentence.strip()
        for sentence in SENTENCE_TERMINATORS.split(text)
        if sentence.strip()
    ]
    if len(sentences) > 1:
        return _group_parts(parts=sentences, max_size=max_size)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if len(lines) > 1:
        return _group_parts(parts=lines, max_size=max_size)
    return _split_on_spaces(text=text, max_size=max_size)


def _add_overlap(
    chunks: list[str], max_overlap_ratio: float, max_size: int
) -> list[str]:
    if len(chunks) <= 1:
        return chunks
    result: list[str] = [chunks[0]]
    for i in range(1, len(chunks)):
        overlap_budget = int(len(chunks[i]) * max_overlap_ratio)
        available = max_size - len(chunks[i]) - 1
        capped_overlap = min(overlap_budget, max(available, 0))
        if capped_overlap <= 0:
            result.append(chunks[i])
            continue
        previous = chunks[i - 1]
        overlap = previous[-capped_overlap:]
        space_index = overlap.find(" ")
        if space_index >= 0:
            overlap = overlap[space_index + 1 :]
        result.append(overlap + " " + chunks[i])
    return result


def chunk_document(document: LoadedDocument) -> list[Chunk]:
    """Split a loaded document into searchable chunks."""
    sections = _group_elements_by_section(elements=document.elements)
    chunks: list[Chunk] = []
    for section_title, paragraphs in sections:
        merged = _merge_short_paragraphs(
            paragraphs=paragraphs, min_size=MIN_CHUNK_SIZE, max_size=MAX_CHUNK_SIZE
        )
        split: list[str] = []
        for paragraph in merged:
            split.extend(_split_oversized(text=paragraph, max_size=MAX_CHUNK_SIZE))
        with_overlap = _add_overlap(
            chunks=split, max_overlap_ratio=MAX_OVERLAP_RATIO, max_size=MAX_CHUNK_SIZE
        )
        for chunk_text in with_overlap:
            chunks.append(
                Chunk(
                    metadata={
                        METADATA_SECTION: section_title,
                        METADATA_SOURCE: document.source,
                    },
                    text=chunk_text,
                )
            )
    return chunks
