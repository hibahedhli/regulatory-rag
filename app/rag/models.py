from __future__ import annotations

from dataclasses import dataclass, field

from app.ingestion.chunker import Chunk


@dataclass
class Hit:
    chunk: Chunk
    score: float
    detail: dict = field(default_factory=dict)
