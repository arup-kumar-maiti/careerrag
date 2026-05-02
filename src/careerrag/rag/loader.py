"""Load documents from files and extract plain text."""

import re
from dataclasses import dataclass
from pathlib import Path

import fitz
from docx import Document

HEADING_STYLE_PREFIX = "Heading"
MULTIPLE_SPACES = re.compile(r" {2,}")
NOISE_CHARACTERS = re.compile(r"[\xa0\xad\u200b\ufeff]+")
PARAGRAPH_SEPARATOR = "\n\n"
TEXT_ENCODING = "utf-8"


@dataclass
class LoadedDocument:
    """Represent extracted document content with its source filename."""

    source: str
    text: str


def _load_docx(path: Path) -> str:
    doc = Document(str(path))
    parts: list[str] = []
    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if not text:
            continue
        if paragraph.style and paragraph.style.name.startswith(HEADING_STYLE_PREFIX):
            parts.append(text + ":")
        else:
            parts.append(text)
    return PARAGRAPH_SEPARATOR.join(parts)


def _load_pdf(path: Path) -> str:
    doc = fitz.open(path)
    pages = [page.get_text() for page in doc]
    doc.close()
    text = PARAGRAPH_SEPARATOR.join(pages)
    text = NOISE_CHARACTERS.sub(" ", text)
    return MULTIPLE_SPACES.sub(" ", text)


def _load_text(path: Path) -> str:
    return path.read_text(encoding=TEXT_ENCODING)


def load_document(path: Path) -> LoadedDocument:
    """Return the extracted text and filename from a document path."""
    loaders = {
        ".docx": _load_docx,
        ".md": _load_text,
        ".pdf": _load_pdf,
        ".txt": _load_text,
    }
    text = loaders[path.suffix.lower()](path)
    return LoadedDocument(source=path.name, text=text)
