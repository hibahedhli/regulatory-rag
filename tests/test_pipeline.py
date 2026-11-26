import os
from pathlib import Path

import pytest

from app.config import ROOT, Settings
from app.evaluation.evaluate import evaluate
from app.rag.pipeline import RAGPipeline

DEMO = ROOT / "demo" / "documents"


@pytest.fixture(scope="module")
def pipe(tmp_path_factory):
    s = Settings(
        raw_dir=DEMO,
        index_dir=tmp_path_factory.mktemp("index"),
        embedding_backend="hashing",
        llm_provider="none",
    )
    p = RAGPipeline(s)
    stats = p.ingest()
    assert stats["documents"] == 7 and stats["chunks"] >= 40  # 7 documents : txt, md, html, docx, pdf
    return p


def test_hybrid_finds_right_article(pipe):
    hits = pipe.search("délai de notification d'une violation de données", mode="hybrid", top_k=3)
    assert hits[0].chunk.article == "Article 8"
    assert hits[0].chunk.doc_id == "loi-demo-protection-donnees"


def test_ask_returns_sources_and_citations(pipe):
    out = pipe.ask("Combien de jours de télétravail par semaine ?")
    assert out["sources"], "des sources doivent être renvoyées"
    assert out["sources"][0]["doc_id"] == "arrete-demo-teletravail"
    assert any(s["cited"] for s in out["sources"])


def test_evaluation_quality(pipe):
    rep = evaluate(pipe, k=5, questions_path=ROOT / "demo" / "eval_questions.json")
    assert rep["hybrid"]["recall@5"] >= 0.9
    assert rep["bm25"]["recall@5"] >= 0.9
    assert rep["hybrid"]["false_refusals"] == 0  # aucune question valable ne doit être refusée
    assert rep["hybrid"]["off_topic_refused"] == "7/7"


def test_documents_list_and_empty_corpus(tmp_path):
    raw = tmp_path / "raw"
    raw.mkdir()
    p = RAGPipeline(Settings(raw_dir=raw, index_dir=tmp_path / "idx", embedding_backend="hashing", llm_provider="none"))
    assert p.documents() == [] and not p.is_ready()
    assert p.search("test") == []                       # corpus vide : pas d'erreur
    assert p.ingest() == {"documents": 0, "chunks": 0}  # ingestion vide : pas d'erreur
    (raw / "a.txt").write_text("Article 1\nTexte de test assez long pour être gardé.", encoding="utf-8")
    p.ingest()
    assert [d["filename"] for d in p.documents()] == ["a.txt"] and p.documents()[0]["chunks"] == 1
