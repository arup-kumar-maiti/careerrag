"""Load documents from files and extract plain text."""

from dataclasses import dataclass
from pathlib import Path

import fitz
from docx import Document

PARAGRAPH_SEPARATOR = "\n\n"
TEXT_ENCODING = "utf-8"


@dataclass
class LoadedDocument:
    """Represent extracted document content with its source filename."""

    source: str
    text: str


def _load_docx(path: Path) -> str:
    doc = Document(str(path))
    return PARAGRAPH_SEPARATOR.join(
        paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()
    )


def _load_pdf(path: Path) -> str:
    doc = fitz.open(path)
    pages = [page.get_text() for page in doc]
    doc.close()
    return PARAGRAPH_SEPARATOR.join(pages)


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
