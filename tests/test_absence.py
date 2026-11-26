"""Questions sans réponse, PDF multi-pages, rapport d'erreurs."""
import pytest

from app.config import ROOT, Settings
from app.evaluation.error_report import build_report
from app.evaluation.evaluate import load_questions
from app.rag.pipeline import ABSENT_MESSAGE, RAGPipeline

DEMO = ROOT / "demo" / "documents"
QUESTIONS = ROOT / "demo" / "eval_questions.json"


@pytest.fixture(scope="module")
def pipe(tmp_path_factory):
    p = RAGPipeline(Settings(raw_dir=DEMO, index_dir=tmp_path_factory.mktemp("idx"), embedding_backend="hashing", llm_provider="none"))
    p.ingest()
    return p


def test_off_topic_questions_are_refused(pipe):
    far = [q for q in load_questions(QUESTIONS) if q.get("answerable") is False and not q.get("near_miss")]
    assert len(far) >= 5
    for q in far:
        out = pipe.ask(q["question"])
        assert out["absent"] is True and out["answer"] == ABSENT_MESSAGE, q["question"]
        assert not any(s["cited"] for s in out["sources"])  # rien n'est présenté comme source citée


def test_valid_questions_are_not_refused(pipe):
    for q in load_questions(QUESTIONS):
        if q.get("answerable", True):
            assert pipe.ask(q["question"])["absent"] is False, q["question"]


def test_refusal_does_not_call_the_llm(tmp_path):
    p = RAGPipeline(Settings(raw_dir=DEMO, index_dir=tmp_path, embedding_backend="hashing", llm_provider="ollama", ollama_url="http://127.0.0.1:9"))
    p.ingest()
    out = p.ask("Quelle est la capitale de la France ?")
    assert out["answer"] == ABSENT_MESSAGE  # pas de « LLM indisponible » : le LLM n'est même pas appelé


def test_pdf_keeps_page_numbers(pipe):
    pdf = [c for c in pipe.chunks.values() if c.source == "circulaire_demo_marches_publics.pdf"]
    pages = {c.article: c.page for c in pdf}
    assert pages["Article 2"] == 1 and pages["Article 4"] == 2
    out = pipe.ask("Quelle garantie de bonne exécution est exigée du titulaire du marché ?")
    assert out["sources"][0]["page"] == 2


def test_no_title_only_preamble(pipe):
    assert not [c for c in pipe.chunks.values() if c.article == "Préambule" and c.text.strip() == c.title.strip()]


def test_error_report_has_at_least_five_cases(pipe):
    md, counts = build_report(pipe, 5, QUESTIONS, min_cases=5)
    assert md.count("## Cas ") >= 5 and "Ton analyse" in md
    assert counts["fausse_acceptation"] >= 1  # les questions « presque dans le corpus » sont bien listées
