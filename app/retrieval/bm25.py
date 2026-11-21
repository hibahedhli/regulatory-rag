"""Recherche lexicale BM25 (indispensable pour les numéros d'articles et termes exacts)."""
from __future__ import annotations

from rank_bm25 import BM25Okapi

from app.ingestion.chunker import Chunk
from app.retrieval.text import tokenize


class BM25Retriever:
    def __init__(self, chunks: list[Chunk]) -> None:
        self.ids = [c.chunk_id for c in chunks]
        corpus = [tokenize(c.contextual_text) for c in chunks]
        self.bm25 = BM25Okapi(corpus) if corpus else None

    def search(self, query: str, n: int) -> list[tuple[str, float]]:
        if not self.bm25:
            return []
        scores = self.bm25.get_scores(tokenize(query))
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n]
        return [(self.ids[i], float(scores[i])) for i in order if scores[i] > 0]
