"""Recherche vectorielle avec ChromaDB (similarité cosinus)."""
from __future__ import annotations

from pathlib import Path

from app.indexing.embedder import Embedder
from app.ingestion.chunker import Chunk

COLLECTION = "regulations"


class DenseRetriever:
    def __init__(self, index_dir: Path, embedder: Embedder) -> None:
        import chromadb

        Path(index_dir).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(Path(index_dir) / "chroma"))
        self.embedder = embedder
        self.col = self.client.get_or_create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})

    def count(self) -> int:
        return self.col.count()

    def rebuild(self, chunks: list[Chunk]) -> None:
        try:
            self.client.delete_collection(COLLECTION)
        except Exception:
            pass
        self.col = self.client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})
        for i in range(0, len(chunks), 128):
            batch = chunks[i : i + 128]
            self.col.add(
                ids=[c.chunk_id for c in batch],
                embeddings=self.embedder.embed_documents([c.contextual_text for c in batch]),
                documents=[c.text for c in batch],
                metadatas=[
                    {"doc_id": c.doc_id, "title": c.title, "article": c.article, "section": c.section, "page": c.page or -1}
                    for c in batch
                ],
            )

    def search(self, query: str, n: int) -> list[tuple[str, float]]:
        total = self.count()
        if total == 0:
            return []
        res = self.col.query(query_embeddings=[self.embedder.embed_query(query)], n_results=min(n, total))
        return [(cid, 1.0 - dist) for cid, dist in zip(res["ids"][0], res["distances"][0])]


def clear_index(index_dir: Path) -> None:
    """Supprime la collection (utilisé quand le dernier document est retiré)."""
    import chromadb

    client = chromadb.PersistentClient(path=str(Path(index_dir) / "chroma"))
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
