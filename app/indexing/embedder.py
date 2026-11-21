"""Embeddings : sentence-transformers (réel) ou hashing (hors ligne, pour tests/démo)."""
from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod

import numpy as np

from app.config import Settings
from app.retrieval.text import tokenize


class Embedder(ABC):
    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    def embed_query(self, text: str) -> list[float]: ...


class HashingEmbedder(Embedder):
    """Sac de mots + bigrammes projeté par hachage. Pas de téléchargement, qualité modeste."""

    def __init__(self, dim: int = 768) -> None:
        self.dim = dim

    def _vec(self, text: str) -> list[float]:
        v = np.zeros(self.dim, dtype=np.float32)
        toks = tokenize(text)
        feats = [(t, 1.0) for t in toks] + [(f"{a}_{b}", 0.5) for a, b in zip(toks, toks[1:])]
        for feat, w in feats:
            h = int(hashlib.md5(feat.encode()).hexdigest(), 16)
            v[h % self.dim] += w if (h >> 64) & 1 else -w
        n = np.linalg.norm(v)
        return (v / n if n else v).tolist()

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)


class SentenceTransformerEmbedder(Embedder):
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        self.is_e5 = "e5" in model_name.lower()

    def embed_documents(self, texts):
        if self.is_e5:
            texts = [f"passage: {t}" for t in texts]
        return self.model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False).tolist()

    def embed_query(self, text):
        if self.is_e5:
            text = f"query: {text}"
        return self.model.encode([text], normalize_embeddings=True)[0].tolist()


def get_embedder(settings: Settings) -> Embedder:
    if settings.embedding_backend == "hashing":
        return HashingEmbedder()
    return SentenceTransformerEmbedder(settings.embedding_model)
