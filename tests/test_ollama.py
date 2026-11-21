"""Teste l'appel Ollama avec un faux serveur local (aucun vrai modèle nécessaire)."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from app.config import ROOT, Settings
from app.rag.pipeline import RAGPipeline

RECEIVED = {}


class FakeOllama(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        RECEIVED.update(body)
        out = json.dumps({"message": {"content": "Le délai est de 24 heures [1]."}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass


def _settings(tmp_path, url):
    return Settings(raw_dir=ROOT / "demo" / "documents", index_dir=tmp_path, embedding_backend="hashing",
                    llm_provider="ollama", ollama_url=url, ollama_model="mistral")


def test_ollama_generation(tmp_path):
    srv = HTTPServer(("127.0.0.1", 0), FakeOllama)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    p = RAGPipeline(_settings(tmp_path, f"http://127.0.0.1:{srv.server_port}"))
    p.ingest()
    out = p.ask("Sous quel délai déclarer un incident de cybersécurité majeur ?")
    srv.shutdown()
    assert out["answer"] == "Le délai est de 24 heures [1]."
    assert out["sources"][0]["cited"] is True
    assert RECEIVED["model"] == "mistral" and RECEIVED["options"]["num_ctx"] == 4096
    assert "EXTRAITS" in RECEIVED["messages"][1]["content"]  # le contexte est bien envoyé


def test_ollama_down_falls_back(tmp_path):
    p = RAGPipeline(_settings(tmp_path, "http://127.0.0.1:9"))  # port fermé
    p.ingest()
    out = p.ask("Combien de jours de télétravail par semaine ?")
    assert "LLM indisponible" in out["answer"] and "ollama list" in out["answer"]
    assert out["sources"]
