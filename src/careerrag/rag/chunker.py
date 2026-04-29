"""Split documents into searchable chunks with section metadata."""

import re
from dataclasses import dataclass, field

HEADER_PATTERN = re.compile(
    r"^(?:#{1,3}\s+.+|[A-Z][A-Za-z\s/&]{2,30}:\s*$|[A-Z][A-Z\s]{2,30}$)",
    re.MULTILINE,
)
HEADER_PREFIX = re.compile(r"^#+\s*")
MAX_CHUNK_SIZE = 1000
MIN_CHUNK_SIZE = 100
OVERLAP_SIZE = 100
SECTION_SEPARATOR = "\n\n"
SENTENCE_TERMINATORS = re.compile(r"(?<=[.!?])\s+")
UNKNOWN_SECTION = "General"


@dataclass
class Chunk:
    """Represent a document chunk with metadata."""

    metadata: dict[str, str] = field(default_factory=dict)
    text: str = ""


def _detect_sections(text: str) -> list[tuple[str, str]]:
    matches = list(HEADER_PATTERN.finditer(text))
    if not matches:
        return [(UNKNOWN_SECTION, text.strip())]
    sections: list[tuple[str, str]] = []
    if matches[0].start() > 0:
        preamble = text[: matches[0].start()].strip()
        if preamble:
            sections.append((UNKNOWN_SECTION, preamble))
    for i, match in enumerate(matches):
        title = match.group().strip().rstrip(":")
        title = HEADER_PREFIX.sub("", title)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[match.end() : end].strip()
        if body:
            sections.append((title, body))
    return sections


def _merge_short_paragraphs(
    paragraphs: list[str], min_size: int, max_size: int
) -> list[str]:
    if not paragraphs:
        return []
    merged: list[str] = []
    current = paragraphs[0]
    for paragraph in paragraphs[1:]:
        combined = current + SECTION_SEPARATOR + paragraph
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


def chunk_document(text: str, source: str) -> list[Chunk]:
    """Split a document into chunks with section metadata."""
    sections = _detect_sections(text)
    chunks: list[Chunk] = []
    for section_title, section_body in sections:
        paragraphs = [
            p.strip() for p in section_body.split(SECTION_SEPARATOR) if p.strip()
        ]
        merged = _merge_short_paragraphs(paragraphs, MIN_CHUNK_SIZE, MAX_CHUNK_SIZE)
        split: list[str] = []
        for paragraph in merged:
            split.extend(_split_oversized(paragraph, MAX_CHUNK_SIZE))
        with_overlap = _add_overlap(split, OVERLAP_SIZE, MAX_CHUNK_SIZE)
        for chunk_text in with_overlap:
            chunks.append(
                Chunk(
                    metadata={"section": section_title, "source": source},
                    text=chunk_text,
                )
            )
    return chunks
