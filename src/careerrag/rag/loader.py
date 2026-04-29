"""Load documents from files and extract plain text."""

from pathlib import Path

import fitz
from docx import Document
from striprtf.striprtf import rtf_to_text

PARAGRAPH_SEPARATOR = "\n\n"
TEXT_ENCODING = "utf-8"


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


def _load_rtf(path: Path) -> str:
    raw = path.read_text(encoding=TEXT_ENCODING)
    result: str = rtf_to_text(raw)
    return result


def _load_text(path: Path) -> str:
    return path.read_text(encoding=TEXT_ENCODING)


def load_document(path: Path) -> tuple[str, str]:
    """Return the extracted text and filename from a document path."""
    loaders = {
        ".docx": _load_docx,
        ".md": _load_text,
        ".pdf": _load_pdf,
        ".rtf": _load_rtf,
        ".txt": _load_text,
    }
    text = loaders[path.suffix.lower()](path)
    return text, path.name
