"""Indexe les documents de data/raw :  python -m scripts.ingest"""
from app.rag.pipeline import RAGPipeline

if __name__ == "__main__":
    print(RAGPipeline().ingest())
