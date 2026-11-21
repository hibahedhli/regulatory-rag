"""Évaluation du retrieval : recall@k et MRR pour dense / BM25 / hybride.

Usage :  python -m app.evaluation.evaluate [--k 5]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.config import ROOT
from app.rag.pipeline import MODES, RAGPipeline

QUESTIONS = ROOT / "data" / "eval" / "eval_questions.json"


def evaluate(pipeline: RAGPipeline, k: int = 5, questions_path: Path | None = None) -> dict:
    items = json.loads(Path(questions_path or QUESTIONS).read_text(encoding="utf-8"))
    report = {}
    for mode in MODES:
        hits_at_k, rr = 0, 0.0
        for it in items:
            hits = pipeline.search(it["question"], mode=mode, top_k=k)
            rank = next(
                (i for i, h in enumerate(hits, 1) if h.chunk.doc_id == it["expected_doc"] and h.chunk.article == it["expected_article"]),
                None,
            )
            if rank:
                hits_at_k += 1
                rr += 1.0 / rank
        n = len(items)
        report[mode] = {f"recall@{k}": round(hits_at_k / n, 3), "mrr": round(rr / n, 3), "n_questions": n}
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--questions", default=str(QUESTIONS), help="fichier JSON de questions")
    args = ap.parse_args()
    if not Path(args.questions).exists():
        raise SystemExit(f"Fichier de questions introuvable : {args.questions}\nVoir le README (section Évaluation).")
    p = RAGPipeline()
    if not p.is_ready():
        p.ingest()
    rep = evaluate(p, args.k, args.questions)
    print(f"{'mode':<8} {'recall@' + str(args.k):<10} {'MRR':<6}")
    for mode, m in rep.items():
        print(f"{mode:<8} {m[f'recall@{args.k}']:<10} {m['mrr']:<6}")
    out = Path(ROOT / "data" / "eval" / "results.json")
    out.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
