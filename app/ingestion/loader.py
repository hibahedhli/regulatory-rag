"""Chargement des documents sources (PDF, TXT, MD, HTML) avec numéro de page."""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

SUPPORTED = {".pdf", ".txt", ".md", ".html", ".htm"}


@dataclass
class RawDocument:
    doc_id: str
    title: str
    source: str
    # liste de (numéro de page ou None, texte de la page)
    pages: list[tuple[int | None, str]] = field(default_factory=list)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower() or "doc"


class _TextExtractor(HTMLParser):
    BLOCKS = {"p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "section", "article"}

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self._skip += 1
        if tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self._skip = max(0, self._skip - 1)
        if tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def _first_line(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip().lstrip("#").strip()
        if line:
            return line[:200] if len(line) <= 200 else fallback
    return fallback


def _load_pdf(path: Path) -> RawDocument:
    import fitz  # PyMuPDF

    pages: list[tuple[int | None, str]] = []
    with fitz.open(path) as pdf:
        meta_title = (pdf.metadata or {}).get("title") or ""
        for i, page in enumerate(pdf, start=1):
            pages.append((i, page.get_text("text")))
    first = pages[0][1] if pages else ""
    title = meta_title.strip() or _first_line(first, path.stem)
    return RawDocument(slugify(path.stem), title, path.name, pages)


def _load_text(path: Path) -> RawDocument:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if path.suffix.lower() in {".html", ".htm"}:
        parser = _TextExtractor()
        parser.feed(text)
        text = "".join(parser.parts)
    return RawDocument(slugify(path.stem), _first_line(text, path.stem), path.name, [(None, text)])


def load_documents(raw_dir: Path) -> list[RawDocument]:
    docs: list[RawDocument] = []
    seen: set[str] = set()
    for path in sorted(Path(raw_dir).rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED:
            continue
        try:
            doc = _load_pdf(path) if path.suffix.lower() == ".pdf" else _load_text(path)
            if doc.doc_id in seen:
                doc.doc_id = f"{doc.doc_id}-{path.suffix.lower().lstrip('.')}"
            seen.add(doc.doc_id)
            docs.append(doc)
        except Exception as exc:  # un fichier illisible ne doit pas bloquer l'indexation
            print(f"[loader] ignoré {path.name}: {exc}")
    return docs
