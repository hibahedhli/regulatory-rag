from docx import Document

from app.ingestion.chunker import chunk_document
from app.ingestion.loader import SUPPORTED, load_documents


def _make_docx(path):
    d = Document()
    d.core_properties.title = "Décret fictif Word"
    d.add_heading("Décret fictif Word", level=1)
    d.add_heading("CHAPITRE I – GÉNÉRAL", level=2)
    d.add_paragraph("Article premier")
    d.add_paragraph("Le présent décret fixe les règles applicables aux organismes concernés par le texte.")
    d.add_paragraph("Article 2")
    d.add_paragraph("Les sanctions sont indiquées dans le tableau suivant.")
    t = d.add_table(rows=2, cols=2)
    t.cell(0, 0).text, t.cell(0, 1).text = "Infraction", "Amende"
    t.cell(1, 0).text, t.cell(1, 1).text = "Retard de notification", "50 000 dinars"
    d.save(path)


def test_docx_is_supported_and_chunked(tmp_path):
    assert ".docx" in SUPPORTED
    _make_docx(tmp_path / "decret.docx")
    docs = load_documents(tmp_path)
    assert len(docs) == 1 and docs[0].title == "Décret fictif Word" and docs[0].source == "decret.docx"
    chunks = chunk_document(docs[0])
    assert [c.article for c in chunks] == ["Article 1", "Article 2"]
    assert chunks[0].section.startswith("CHAPITRE I")
    assert "Retard de notification | 50 000 dinars" in chunks[1].text  # le tableau est bien lu
    assert chunks[1].source == "decret.docx"


def test_corrupt_docx_does_not_block_others(tmp_path):
    (tmp_path / "casse.docx").write_bytes(b"pas un vrai docx")
    (tmp_path / "ok.txt").write_text("Article 1\nUn texte valide et assez long pour être gardé ici.", encoding="utf-8")
    docs = load_documents(tmp_path)
    assert [d.source for d in docs] == ["ok.txt"]
