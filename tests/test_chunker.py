from app.ingestion.chunker import chunk_document, normalize_article
from app.ingestion.loader import RawDocument

TEXT = """Loi test
TITRE I – GÉNÉRAL
Article premier
Texte de l'article un qui contient plusieurs mots pour dépasser le seuil minimal.
Article 2 bis
Texte de l'article deux bis.
CHAPITRE 2 – SUITE
Article 3 : Texte de l'article trois.
"""


def _doc(text=TEXT):
    return RawDocument("loi-test", "Loi test", "t.txt", [(None, text)])


def test_normalize():
    assert normalize_article("premier") == "Article 1"
    assert normalize_article("1er") == "Article 1"
    assert normalize_article("2  BIS") == "Article 2 bis"


def test_chunk_by_article_with_section():
    chunks = chunk_document(_doc())
    arts = [c.article for c in chunks]
    assert arts == ["Article 1", "Article 2 bis", "Article 3"]
    assert chunks[0].section.startswith("TITRE I")
    assert chunks[2].section.startswith("CHAPITRE 2")
    assert chunks[2].text == "Texte de l'article trois."


def test_long_article_is_split_with_overlap():
    long = "Article 1\n" + " ".join(f"mot{i}" for i in range(500))
    chunks = chunk_document(_doc(long), max_words=100, overlap=20)
    assert len(chunks) > 4
    assert all(c.article == "Article 1" for c in chunks)
    assert len({c.chunk_id for c in chunks}) == len(chunks)
    assert chunks[0].text.split()[-20:] == chunks[1].text.split()[:20]


def test_page_tracking():
    doc = RawDocument("d", "D", "d.pdf", [(1, "Article 1\nUn texte assez long pour le test."), (2, "Article 2\nAutre texte de test.")])
    chunks = chunk_document(doc)
    assert [c.page for c in chunks] == [1, 2]
