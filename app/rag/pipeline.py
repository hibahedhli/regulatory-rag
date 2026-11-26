"""Pipeline RAG complet : ingestion, recherche (dense / BM25 / hybride), génération + citations."""
from __future__ import annotations

import json
import re
from pathlib import Path

from app.config import Settings
from app.generation.llm import generate_answer
from app.indexing.embedder import get_embedder
from app.ingestion.chunker import Chunk, chunk_document
from app.ingestion.loader import SUPPORTED, load_documents
from app.rag.models import Hit
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.dense import DenseRetriever, clear_index
from app.retrieval.hybrid import rrf_fuse
from app.retrieval.text import tokenize

MODES = ("hybrid", "dense", "bm25")
ABSENT_MESSAGE = "Je n'ai pas trouvé cette information dans les textes fournis."


class RAGPipeline:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.settings.index_dir.mkdir(parents=True, exist_ok=True)
        self._embedder = None
        self._dense: DenseRetriever | None = None
        self._reranker = None
        self.chunks: dict[str, Chunk] = {}
        self.bm25: BM25Retriever | None = None
        self._load_chunks()

    # ---------- propriétés paresseuses (évite de charger les modèles inutilement) ----------
    @property
    def embedder(self):
        if self._embedder is None:
            self._embedder = get_embedder(self.settings)
        return self._embedder

    @property
    def dense(self) -> DenseRetriever:
        if self._dense is None:
            self._dense = DenseRetriever(self.settings.index_dir, self.embedder)
        return self._dense

    @property
    def chunks_path(self) -> Path:
        return self.settings.index_dir / "chunks.jsonl"

    # ---------- indexation ----------
    def _load_chunks(self) -> None:
        self.chunks = {}
        if self.chunks_path.exists():
            for line in self.chunks_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    c = Chunk.from_dict(json.loads(line))
                    self.chunks[c.chunk_id] = c
        self.bm25 = BM25Retriever(list(self.chunks.values())) if self.chunks else None

    def is_ready(self) -> bool:
        return bool(self.chunks)

    def ingest(self) -> dict:
        docs = load_documents(self.settings.raw_dir)
        chunks: list[Chunk] = []
        for d in docs:
            chunks.extend(chunk_document(d, self.settings.chunk_max_words, self.settings.chunk_overlap_words))
        self.chunks_path.write_text("\n".join(json.dumps(c.to_dict(), ensure_ascii=False) for c in chunks), encoding="utf-8")
        if chunks:
            self.dense.rebuild(chunks)
        else:  # plus aucun document : on vide l'index sans charger de modèle
            self._dense = None
            clear_index(self.settings.index_dir)
        self._load_chunks()
        return {"documents": len(docs), "chunks": len(chunks)}

    def list_sources(self) -> list[Path]:
        raw = Path(self.settings.raw_dir)
        if not raw.exists():
            return []
        return sorted(p for p in raw.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED)

    def documents(self) -> list[dict]:
        """Un élément par fichier du dossier raw ; chunks = 0 si aucun texte n'a pu être extrait."""
        counts: dict[str, dict] = {}
        for c in self.chunks.values():
            d = counts.setdefault(c.source, {"title": c.title, "chunks": 0})
            d["chunks"] += 1
        return [
            {
                "filename": p.name,
                "title": counts.get(p.name, {}).get("title", p.name),
                "chunks": counts.get(p.name, {}).get("chunks", 0),
                "size_kb": round(p.stat().st_size / 1024, 1),
            }
            for p in self.list_sources()
        ]

    # ---------- recherche ----------
    def search(self, query: str, mode: str = "hybrid", top_k: int | None = None) -> list[Hit]:
        return self._retrieve(query, mode, top_k)[0]

    def search_with_relevance(self, query: str, mode: str = "hybrid", top_k: int | None = None) -> tuple[list[Hit], dict]:
        hits, dense = self._retrieve(query, mode, top_k)
        return hits, self.assess(query, hits, dense)

    def assess(self, query: str, hits: list[Hit], dense: list[tuple[str, float]]) -> dict:
        """Estime si les passages retrouvés répondent vraiment à la question.

        Deux signaux : la similarité vectorielle du meilleur passage, et le recouvrement lexical
        (part des mots de la question présents dans le meilleur passage). La réponse est jugée
        absente seulement si LES DEUX sont faibles, pour éviter de refuser une question reformulée.
        """
        if not hits:
            return {"dense_sim": None, "coverage": 0.0, "absent": True, "reason": "aucun passage retrouvé"}
        q = set(tokenize(query))
        coverage = 1.0
        if q:
            coverage = max(
                len(q & set(tokenize(f"{h.chunk.title} {h.chunk.section} {h.chunk.article} {h.chunk.text}"))) / len(q)
                for h in hits
            )
        dense_sim = max((sc for _, sc in dense), default=None)
        weak_cov = coverage < self.settings.min_coverage
        weak_sim = dense_sim is None or dense_sim < self.settings.min_similarity
        absent = weak_cov and weak_sim
        return {
            "dense_sim": None if dense_sim is None else round(dense_sim, 4),
            "coverage": round(coverage, 3),
            "absent": absent,
            "reason": "faible similarité et faible recouvrement lexical" if absent else "",
        }

    def _retrieve(self, query: str, mode: str, top_k: int | None) -> tuple[list[Hit], list[tuple[str, float]]]:
        if not self.is_ready():
            return [], []
        top_k = top_k or self.settings.top_k
        n = max(self.settings.candidates, top_k)
        dense = self.dense.search(query, n) if mode in ("hybrid", "dense") else []
        lexical = self.bm25.search(query, n) if (mode in ("hybrid", "bm25") and self.bm25) else []

        if mode == "hybrid":
            fused = rrf_fuse([dense, lexical])
        else:
            fused = dense or lexical

        d_rank = {cid: r for r, (cid, _) in enumerate(dense, 1)}
        b_rank = {cid: r for r, (cid, _) in enumerate(lexical, 1)}
        hits = [
            Hit(self.chunks[cid], score, {"dense_rank": d_rank.get(cid), "bm25_rank": b_rank.get(cid)})
            for cid, score in fused[:n]
            if cid in self.chunks
        ]

        if self.settings.reranker_enabled and hits:
            if self._reranker is None:
                from app.retrieval.reranker import CrossEncoderReranker

                self._reranker = CrossEncoderReranker(self.settings.reranker_model)
            ranked = self._reranker.rerank(query, [h.chunk for h in hits])
            by_id = {h.chunk.chunk_id: h for h in hits}
            hits = [Hit(c, s, by_id[c.chunk_id].detail | {"reranked": True}) for c, s in ranked]
        return hits[:top_k], dense

    # ---------- question / réponse ----------
    def ask(self, question: str, top_k: int | None = None, mode: str = "hybrid") -> dict:
        hits, rel = self.search_with_relevance(question, mode=mode, top_k=top_k)
        if rel["absent"]:  # pas d'appel au LLM : on évite toute invention
            answer, cited = ABSENT_MESSAGE, set()
        else:
            answer = generate_answer(self.settings, question, hits)
            cited = {int(n) for n in re.findall(r"\[(\d+)\]", answer)}
        sources = []
        for i, h in enumerate(hits, start=1):
            c = h.chunk
            excerpt = c.text.replace("\n", " ")
            sources.append(
                {
                    "n": i,
                    "doc_id": c.doc_id,
                    "title": c.title,
                    "section": c.section,
                    "article": c.article,
                    "page": c.page,
                    "score": round(h.score, 4),
                    "excerpt": excerpt if len(excerpt) <= 600 else excerpt[:600].rsplit(" ", 1)[0] + "…",
                    "cited": i in cited,
                }
            )
        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "mode": mode,
            "llm_provider": self.settings.llm_provider,
            "absent": rel["absent"],
            "relevance": rel,
        }
