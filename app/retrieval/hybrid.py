"""Fusion de classements par Reciprocal Rank Fusion (RRF) + reranking optionnel."""
from __future__ import annotations

from collections import defaultdict


def rrf_fuse(rankings: list[list[tuple[str, float]]], k: int = 60) -> list[tuple[str, float]]:
    scores: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, (cid, _) in enumerate(ranking, start=1):
            scores[cid] += 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
