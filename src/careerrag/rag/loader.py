"""Load documents and extract structured elements."""

import html
import re
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter
from docling_core.types.doc.document import DoclingDocument, TableItem
from docling_core.types.doc.labels import DocItemLabel

from careerrag.rag.util import (
    KIND_BODY,
    KIND_CONTACT,
    KIND_HEADING,
    KIND_LIST_ITEM,
    DocumentElement,
    LoadedDocument,
)

CONTACT_MAX_LENGTH = 200
CONTACT_PATTERN = re.compile(
    r"[\w.+-]+@[\w-]+\.[\w.]+|https?://\S+|linkedin\.com/\S+|\+?\d[\d\s\-()]{7,}"
)
DOCLING_LABEL_MAP: dict[DocItemLabel | None, str] = {
    DocItemLabel.LIST_ITEM: KIND_LIST_ITEM,
    DocItemLabel.SECTION_HEADER: KIND_HEADING,
    DocItemLabel.TITLE: KIND_HEADING,
}


def _extract_elements(document: DoclingDocument) -> list[DocumentElement]:
    elements: list[DocumentElement] = []
    for item, _ in document.iterate_items():
        kind = DOCLING_LABEL_MAP.get(getattr(item, "label", None), KIND_BODY)
        text = html.unescape(
            item.export_to_markdown(doc=document)
            if isinstance(item, TableItem)
            else (getattr(item, "text", "") or "").strip()
        )
        if not text:
            continue
        if (
            kind == KIND_BODY
            and len(text) < CONTACT_MAX_LENGTH
            and CONTACT_PATTERN.match(text)
        ):
            kind = KIND_CONTACT
        elements.append(DocumentElement(kind=kind, text=text))
    return elements


def _load_file(path: Path) -> list[DocumentElement]:
    converter = DocumentConverter()
    result = converter.convert(str(path))
    return _extract_elements(document=result.document)


def _load_text(path: Path) -> list[DocumentElement]:
    text = path.read_text(encoding="utf-8")
    converter = DocumentConverter(allowed_formats=[InputFormat.MD])
    result = converter.convert_string(text, InputFormat.MD)
    return _extract_elements(document=result.document)


def load_document(path: Path) -> LoadedDocument:
    """Return structured elements and filename from a document path."""
    loaders = {
        ".docx": _load_file,
        ".md": _load_text,
        ".pdf": _load_file,
        ".txt": _load_text,
    }
    elements = loaders[path.suffix.lower()](path)
    return LoadedDocument(elements=elements, source=path.name)
