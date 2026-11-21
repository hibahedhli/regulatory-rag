"""API FastAPI : /ask, /ingest, /upload, /documents, /health."""
from __future__ import annotations

import shutil
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.ingestion.loader import SUPPORTED
from app.rag.pipeline import MODES, RAGPipeline

pipeline: RAGPipeline | None = None


def get_pipeline() -> RAGPipeline:
    global pipeline
    if pipeline is None:
        pipeline = RAGPipeline()
    return pipeline


@asynccontextmanager
async def lifespan(_: FastAPI):
    p = get_pipeline()
    if not p.is_ready() and p.list_sources():  # réindexe au démarrage si des fichiers existent déjà
        p.ingest()
    yield


app = FastAPI(title="Assistant de recherche – textes réglementaires", version="1.0.0", lifespan=lifespan)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3)
    top_k: int = Field(5, ge=1, le=20)
    mode: str = Field("hybrid", description="hybrid | dense | bm25")


@app.get("/health")
def health():
    p = get_pipeline()
    return {"status": "ok", "ready": p.is_ready(), "chunks": len(p.chunks), "llm": p.settings.llm_provider}


@app.get("/documents")
def documents():
    return get_pipeline().documents()


@app.post("/ask")
def ask(req: AskRequest):
    if req.mode not in MODES:
        raise HTTPException(400, f"mode invalide, choisir parmi {MODES}")
    p = get_pipeline()
    if not p.is_ready():
        raise HTTPException(409, "Index vide : ajoutez des documents puis appelez /ingest.")
    return p.ask(req.question, top_k=req.top_k, mode=req.mode)


@app.post("/ingest")
def ingest():
    return get_pipeline().ingest()


@app.post("/upload")
async def upload(files: list[UploadFile] = File(...)):
    p = get_pipeline()
    p.settings.raw_dir.mkdir(parents=True, exist_ok=True)
    saved, rejected = [], []
    for f in files:
        name = Path(f.filename or "").name
        if Path(name).suffix.lower() not in SUPPORTED:
            rejected.append(name or "(sans nom)")
            continue
        with (p.settings.raw_dir / name).open("wb") as out:
            shutil.copyfileobj(f.file, out)
        saved.append(name)
    if not saved:
        raise HTTPException(400, f"Aucun fichier valide. Formats acceptés : {sorted(SUPPORTED)}")
    return {"saved": saved, "rejected": rejected, **p.ingest()}


@app.delete("/documents/{filename}")
def delete_document(filename: str):
    p = get_pipeline()
    target = (p.settings.raw_dir / Path(filename).name).resolve()
    if target.parent != Path(p.settings.raw_dir).resolve() or not target.is_file():
        raise HTTPException(404, "Document introuvable.")
    target.unlink()
    return {"deleted": target.name, **p.ingest()}
