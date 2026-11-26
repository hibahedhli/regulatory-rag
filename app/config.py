"""Configuration centralisée, lue depuis les variables d'environnement (.env)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:  # python-dotenv est optionnel
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

ROOT = Path(__file__).resolve().parent.parent


def _s(name: str, default: str) -> str:
    return os.getenv(name, default)


def _i(name: str, default: int) -> int:
    return int(os.getenv(name, default))


def _b(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    raw_dir: Path = field(default_factory=lambda: Path(_s("RAW_DIR", str(ROOT / "data" / "raw"))))
    index_dir: Path = field(default_factory=lambda: Path(_s("INDEX_DIR", str(ROOT / "data" / "index"))))

    embedding_backend: str = field(default_factory=lambda: _s("EMBEDDING_BACKEND", "sentence-transformers"))
    embedding_model: str = field(default_factory=lambda: _s("EMBEDDING_MODEL", "intfloat/multilingual-e5-small"))

    chunk_max_words: int = field(default_factory=lambda: _i("CHUNK_MAX_WORDS", 220))
    chunk_overlap_words: int = field(default_factory=lambda: _i("CHUNK_OVERLAP_WORDS", 40))

    top_k: int = field(default_factory=lambda: _i("TOP_K", 5))
    candidates: int = field(default_factory=lambda: _i("CANDIDATES", 20))
    reranker_enabled: bool = field(default_factory=lambda: _b("RERANKER_ENABLED", False))
    reranker_model: str = field(default_factory=lambda: _s("RERANKER_MODEL", "BAAI/bge-reranker-v2-m3"))

    # Détection des questions sans réponse dans le corpus (voir README, « Réponses absentes »)
    min_similarity: float | None = None  # similarité cosinus minimale ; défaut selon le modèle d'embedding
    min_coverage: float = field(default_factory=lambda: float(_s("MIN_COVERAGE", "0.34")))

    llm_provider: str = field(default_factory=lambda: _s("LLM_PROVIDER", "none"))
    ollama_url: str = field(default_factory=lambda: _s("OLLAMA_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: _s("OLLAMA_MODEL", "mistral"))

    def __post_init__(self) -> None:
        if self.min_similarity is None:
            default = "0.25" if self.embedding_backend == "hashing" else "0.78"
            self.min_similarity = float(_s("MIN_SIMILARITY", default))