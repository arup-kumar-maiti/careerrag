"""Split structured document elements into searchable chunks."""

import re
from dataclasses import dataclass, field

from careerrag.rag.loader import (
    KIND_CONTACT,
    KIND_HEADING,
    KIND_SEPARATOR,
    KIND_TITLE,
    DocumentElement,
    LoadedDocument,
)

BOUNDARY_KINDS = {KIND_HEADING, KIND_SEPARATOR}
MAX_CHUNK_SIZE = 1000
MIN_CHUNK_SIZE = 100
OVERLAP_SIZE = 100
SENTENCE_TERMINATORS = re.compile(r"(?<=[.!?])\s+")
SKIP_KINDS = {KIND_CONTACT, KIND_TITLE}
UNKNOWN_SECTION = "General"


@dataclass
class Chunk:
    """Represent a document chunk with metadata."""

    metadata: dict[str, str] = field(default_factory=dict)
    text: str = ""


def _group_elements_by_section(
    elements: list[DocumentElement],
) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    current_title = UNKNOWN_SECTION
    current_body: list[str] = []
    for element in elements:
        if element.kind in SKIP_KINDS:
            continue
        if element.kind in BOUNDARY_KINDS:
            if current_body:
                sections.append((current_title, current_body))
            current_title = (
                element.text if element.kind == KIND_HEADING else UNKNOWN_SECTION
            )
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


def _split_on_sentences(text: str) -> list[str]:
    parts = SENTENCE_TERMINATORS.split(text)
    return [part.strip() for part in parts if part.strip()]


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


def _split_on_lines(text: str) -> list[str]:
    return [line.strip() for line in text.split("\n") if line.strip()]


def _split_on_spaces(text: str, max_size: int) -> list[str]:
    words = text.split(" ")
    if len(words) <= 1:
        return [text[i : i + max_size] for i in range(0, len(text), max_size)]
    chunks: list[str] = []
    current = words[0]
    for word in words[1:]:
        combined = current + " " + word
        if len(combined) <= max_size:
            current = combined
        else:
            chunks.append(current)
            current = word
    if current:
        chunks.append(current)
    return chunks


def _split_oversized(text: str, max_size: int) -> list[str]:
    if len(text) <= max_size:
        return [text]
    sentences = _split_on_sentences(text)
    if len(sentences) > 1:
        return _group_parts(sentences, max_size)
    lines = _split_on_lines(text)
    if len(lines) > 1:
        return _group_parts(lines, max_size)
    return _split_on_spaces(text, max_size)


def _add_overlap(chunks: list[str], overlap_size: int, max_size: int) -> list[str]:
    if len(chunks) <= 1 or overlap_size <= 0:
        return chunks
    result: list[str] = [chunks[0]]
    for i in range(1, len(chunks)):
        previous = chunks[i - 1]
        available = max_size - len(chunks[i]) - 1
        capped_overlap = min(overlap_size, max(available, 0))
        if capped_overlap <= 0:
            result.append(chunks[i])
            continue
        overlap = previous[-capped_overlap:]
        space_index = overlap.find(" ")
        if space_index >= 0:
            overlap = overlap[space_index + 1 :]
        result.append(overlap + " " + chunks[i])
    return result


def chunk_document(document: LoadedDocument) -> list[Chunk]:
    """Split a loaded document into chunks with section metadata."""
    sections = _group_elements_by_section(document.elements)
    chunks: list[Chunk] = []
    for section_title, paragraphs in sections:
        merged = _merge_short_paragraphs(paragraphs, MIN_CHUNK_SIZE, MAX_CHUNK_SIZE)
        split: list[str] = []
        for paragraph in merged:
            split.extend(_split_oversized(paragraph, MAX_CHUNK_SIZE))
        with_overlap = _add_overlap(split, OVERLAP_SIZE, MAX_CHUNK_SIZE)
        for chunk_text in with_overlap:
            chunks.append(
                Chunk(
                    metadata={"section": section_title, "source": document.source},
                    text=chunk_text,
                )
            )
    return chunks
