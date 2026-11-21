"""Interroge en ligne de commande :  python -m scripts.ask "votre question" """
import json
import sys

from app.rag.pipeline import RAGPipeline

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or input("Question : ")
    out = RAGPipeline().ask(q)
    print("\n" + out["answer"] + "\n")
    for s in out["sources"]:
        page = f", p. {s['page']}" if s["page"] else ""
        print(f"  [{s['n']}] {s['title']} — {s['article']}{page} (score {s['score']}){' *' if s['cited'] else ''}")
