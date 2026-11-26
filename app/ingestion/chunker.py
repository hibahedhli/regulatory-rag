"""Découpage structurel : un chunk = un article (sous-découpé s'il est trop long)."""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict

from .loader import RawDocument

ARTICLE_RE = re.compile(
    r"^\s*(?:#+\s*)?(?:\*\*)?"
    r"(?:(?:Article|Art\.?)\s+(?P<n>premier|1er|\d+(?:\s*(?:bis|ter|quater|quinquies))?)"
    r"|الفصل\s+(?P<ar>\S+))"
    r"(?:\*\*)?\s*[:.\-–—]?\s*(?P<rest>.*)$",
    re.IGNORECASE,
)
STRUCT_RE = re.compile(
    r"^\s*(?:#+\s*)?(?P<h>(?:TITRE|CHAPITRE|SECTION|LIVRE|PARTIE|الباب|القسم)\b.*)$",
    re.IGNORECASE,
)


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    article: str  # "Article 12", "Article 5 bis" ou "Préambule"
    section: str  # dernier titre/chapitre rencontré
    page: int | None
    text: str
    source: str = ""  # nom du fichier d'origine

    @property
    def contextual_text(self) -> str:
        """Texte envoyé à l'embedding : le contexte (titre, chapitre, article) améliore la recherche."""
        head = " — ".join(p for p in (self.title, self.section, self.article) if p)
        return f"{head}\n{self.text}"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Chunk":
        return cls(**d)

    @property
    def reference(self) -> str:
        ref = f"{self.title}, {self.article}"
        if self.page:
            ref += f" (p. {self.page})"
        return ref


def normalize_article(raw: str) -> str:
    raw = " ".join(raw.lower().split())
    if raw in {"premier", "1er"}:
        raw = "1"
    return f"Article {raw}"


def _windows(words: list[str], size: int, overlap: int) -> list[list[str]]:
    if len(words) <= size:
        return [words]
    step = max(1, size - overlap)
    out, start = [], 0
    while start < len(words):
        out.append(words[start : start + size])
        if start + size >= len(words):
            break
        start += step
    return out


def chunk_document(doc: RawDocument, max_words: int = 220, overlap: int = 40) -> list[Chunk]:
    chunks: list[Chunk] = []
    seq = 0
    section = ""
    article = "Préambule"
    buf: list[str] = []
    buf_page: int | None = None

    def flush() -> None:
        nonlocal seq, buf, buf_page
        lines = [ln.strip() for ln in buf if ln.strip()]
        buf = []
        if not lines:
            return
        text = "\n".join(lines)
        words = text.split()
        if article == "Préambule" and (len(words) < 8 or " ".join(words).lower() == " ".join(doc.title.split()).lower()):
            return  # en-tête sans contenu (ou simple répétition du titre, déjà ajouté à chaque passage)
        parts = [text] if len(words) <= max_words else [" ".join(w) for w in _windows(words, max_words, overlap)]
        for part in parts:
            seq += 1
            chunks.append(Chunk(f"{doc.doc_id}#{seq:04d}", doc.doc_id, doc.title, article, section, buf_page, part, doc.source))

    for page, page_text in doc.pages:
        for line in page_text.splitlines():
            m_art = ARTICLE_RE.match(line)
            m_struct = None if m_art else STRUCT_RE.match(line)
            if m_art:
                flush()
                article = normalize_article(m_art.group("n") or m_art.group("ar"))
                buf_page = page
                rest = (m_art.group("rest") or "").strip()
                if rest:
                    buf.append(rest)
            elif m_struct:
                flush()
                section = m_struct.group("h").strip()
                buf_page = page
            else:
                if not buf:
                    buf_page = page
                buf.append(line)
    flush()
    return chunks
