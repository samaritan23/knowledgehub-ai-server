from pathlib import Path

import pypdf
from docx import Document

PDF = "application/pdf"
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MARKDOWN = "text/markdown"
TEXT = "text/plain"


def extract_pages(path: Path, media_type: str) -> list[dict]:
    if media_type == PDF:
        return _pdf_pages(path)
    if media_type == DOCX:
        return _docx_pages(path)
    if media_type == MARKDOWN:
        return _markdown_pages(path)
    if media_type == TEXT:
        text = path.read_text(encoding="utf-8")
        return [{"page": 1, "text": text}] if text.strip() else []
    raise ValueError("unsupported file type")


def _pdf_pages(path: Path) -> list[dict]:
    reader = pypdf.PdfReader(path)
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({"page": index, "text": text})
    return pages


def _docx_pages(path: Path) -> list[dict]:
    document = Document(path)
    sections: list[dict] = []
    number = 1
    current: list[str] = []
    for paragraph in document.paragraphs:
        style = paragraph.style.name if paragraph.style is not None else ""
        if style.startswith("Heading") and current:
            sections.append({"page": number, "text": "\n".join(current)})
            number += 1
            current = []
        if paragraph.text.strip():
            current.append(paragraph.text)
    if current:
        sections.append({"page": number, "text": "\n".join(current)})
    return sections


def _markdown_pages(path: Path) -> list[dict]:
    sections: list[dict] = []
    number = 1
    current: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#") and current:
            sections.append({"page": number, "text": "\n".join(current)})
            number += 1
            current = []
        if line.strip():
            current.append(line)
    if current:
        sections.append({"page": number, "text": "\n".join(current)})
    return sections
