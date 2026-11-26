"""Évaluation : qualité de la recherche ET détection des questions sans réponse.

Format du fichier de questions (JSON) :
  - question avec réponse : {"question", "expected_doc", "expected_article"}
  - question SANS réponse : {"question", "answerable": false}   (+ "near_miss": true si proche du corpus)

Usage :  python -m app.evaluation.evaluate [--k 5] [--questions fichier.json]
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from app.config import ROOT
from app.rag.pipeline import MODES, RAGPipeline

QUESTIONS = ROOT / "data" / "eval" / "eval_questions.json"


def load_questions(path: Path | str | None = None) -> list[dict]:
    return json.loads(Path(path or QUESTIONS).read_text(encoding="utf-8"))


def run_question(pipeline: RAGPipeline, item: dict, mode: str, k: int) -> dict:
    """Exécute une question et renvoie rang trouvé, passages et jugement de pertinence."""
    hits, rel = pipeline.search_with_relevance(item["question"], mode=mode, top_k=k)
    answerable = item.get("answerable", True)
    rank = None
    if answerable:
        rank = next(
            (i for i, h in enumerate(hits, 1) if h.chunk.doc_id == item["expected_doc"] and h.chunk.article == item["expected_article"]),
            None,
        )
    return {"item": item, "answerable": answerable, "hits": hits, "relevance": rel, "rank": rank, "refused": rel["absent"]}


def evaluate(pipeline: RAGPipeline, k: int = 5, questions_path: Path | str | None = None) -> dict:
    items = load_questions(questions_path)
    report = {}
    for mode in MODES:
        runs = [run_question(pipeline, it, mode, k) for it in items]
        ans = [r for r in runs if r["answerable"]]
        absent = [r for r in runs if not r["answerable"]]
        far = [r for r in absent if not r["item"].get("near_miss")]
        found = [r for r in ans if r["rank"]]
        report[mode] = {
            f"recall@{k}": round(len(found) / len(ans), 3) if ans else None,
            "mrr": round(sum(1 / r["rank"] for r in found) / len(ans), 3) if ans else None,
            "n_questions": len(ans),
            "n_absent": len(absent),
            "absent_refused": sum(r["refused"] for r in absent),
            "off_topic_refused": f"{sum(r['refused'] for r in far)}/{len(far)}",
            "false_refusals": sum(r["refused"] for r in ans),
        }
    return report


def calibration(pipeline: RAGPipeline, k: int, questions_path) -> dict:
    """Distribution des signaux de pertinence, pour choisir MIN_SIMILARITY / MIN_COVERAGE."""
    runs = [run_question(pipeline, it, "hybrid", k) for it in load_questions(questions_path)]
    out = {}
    for label, group in (("avec réponse", [r for r in runs if r["answerable"]]), ("sans réponse", [r for r in runs if not r["answerable"]])):
        for key in ("dense_sim", "coverage"):
            vals = [r["relevance"][key] for r in group if r["relevance"][key] is not None]
            if vals:
                out[(label, key)] = (min(vals), statistics.median(vals), max(vals))
    return out


def suggest_threshold(pipeline: RAGPipeline, k: int, questions_path) -> dict:
    """Cherche le MIN_SIMILARITY qui refuse le plus de questions hors-sujet sans refuser de question valable."""
    min_cov = pipeline.settings.min_coverage
    runs = [run_question(pipeline, it, "hybrid", k) for it in load_questions(questions_path)]
    sims = sorted({r["relevance"]["dense_sim"] for r in runs if r["relevance"]["dense_sim"] is not None})
    best = None
    for t in [0.0] + [s + 0.001 for s in sims]:
        def refused(r):
            rel = r["relevance"]
            return rel["coverage"] < min_cov and (rel["dense_sim"] is None or rel["dense_sim"] < t)
        far = [r for r in runs if not r["answerable"] and not r["item"].get("near_miss")]
        ans = [r for r in runs if r["answerable"]]
        score = (-sum(refused(r) for r in ans), sum(refused(r) for r in far), -t)
        if best is None or score > best[0]:
            best = (score, t, sum(refused(r) for r in far), len(far), sum(refused(r) for r in ans))
    return {"min_similarity": round(best[1], 3), "off_topic_refused": f"{best[2]}/{best[3]}", "false_refusals": best[4]}


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
    k = args.k
    rep = evaluate(p, k, args.questions)
    print(f"\n{'mode':<8} {'recall@' + str(k):<9} {'MRR':<6} {'hors-sujet refusées':<20} {'absentes refusées':<18} {'faux refus'}")
    for mode, m in rep.items():
        print(f"{mode:<8} {m[f'recall@{k}']!s:<9} {m['mrr']!s:<6} {m['off_topic_refused']:<20} {m['absent_refused']}/{m['n_absent']:<16} {m['false_refusals']}/{m['n_questions']}")
    print(f"\nSeuils actuels : MIN_SIMILARITY={p.settings.min_similarity}  MIN_COVERAGE={p.settings.min_coverage}")
    print("\nCalibration (mode hybrid) : min / médiane / max")
    for (label, key), (lo, med, hi) in calibration(p, k, args.questions).items():
        print(f"  {label:<13} {key:<10} {lo:.3f} / {med:.3f} / {hi:.3f}")
    sug = suggest_threshold(p, k, args.questions)
    print(f"\nSuggestion : MIN_SIMILARITY={sug['min_similarity']} (hors-sujet refusées {sug['off_topic_refused']}, faux refus {sug['false_refusals']})")
    print("  -> à mettre dans .env si tu veux l'appliquer, puis relancer. Refais ce calcul avec ton vrai corpus et ton vrai modèle.")
    Path(ROOT / "data" / "eval").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "eval" / "results.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
