"""Reranking par cross-encoder (optionnel, activé via RERANKER_ENABLED=true)."""
from __future__ import annotations

from app.ingestion.chunker import Chunk


class CrossEncoderReranker:
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import CrossEncoder

        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, chunks: list[Chunk]) -> list[tuple[Chunk, float]]:
        if not chunks:
            return []
        scores = self.model.predict([(query, c.contextual_text) for c in chunks])
        return sorted(zip(chunks, map(float, scores)), key=lambda x: x[1], reverse=True)
