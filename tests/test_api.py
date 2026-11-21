from fastapi.testclient import TestClient

import app.api.main as api
from app.config import ROOT, Settings
from app.rag.pipeline import RAGPipeline

DEMO = ROOT / "demo" / "documents"


def test_api_flow_user_uploads_own_files(tmp_path):
    raw = tmp_path / "raw"  # corpus vide au départ : l'utilisateur apporte ses fichiers
    api.pipeline = RAGPipeline(Settings(raw_dir=raw, index_dir=tmp_path / "idx", embedding_backend="hashing", llm_provider="none"))
    with TestClient(api.app) as client:
        assert client.get("/health").json()["ready"] is False
        assert client.get("/documents").json() == []
        assert client.post("/ask", json={"question": "Quel délai de déclaration ?"}).status_code == 409

        files = [("files", (f.name, f.read_bytes())) for f in sorted(DEMO.glob("*.txt"))]
        files.append(("files", ("image.png", b"nope")))
        r = client.post("/upload", files=files)
        assert r.status_code == 200 and len(r.json()["saved"]) == 3 and r.json()["rejected"] == ["image.png"]

        assert len(client.get("/documents").json()) == 3
        r = client.post("/ask", json={"question": "Quelle durée de conservation des journaux de sécurité ?", "top_k": 3})
        assert r.status_code == 200 and r.json()["sources"]
        assert client.post("/ask", json={"question": "abc def", "mode": "x"}).status_code in (400, 422)

        assert client.delete("/documents/arrete_demo_teletravail.txt").status_code == 200
        assert len(client.get("/documents").json()) == 2
        assert client.delete("/documents/../secret.txt").status_code in (404, 422)
        assert client.delete("/documents/inconnu.txt").status_code == 404
        for name in ("loi_demo_protection_donnees.txt", "decret_demo_securite_si.txt"):
            client.delete(f"/documents/{name}")
        assert client.get("/health").json()["ready"] is False
