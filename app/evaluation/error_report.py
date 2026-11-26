"""Rapport d'erreurs : liste les questions mal traitées, avec ce qui a été retrouvé à la place.

Sert de base à l'analyse demandée (au moins 5 erreurs ou résultats peu pertinents).

Usage :  python -m app.evaluation.error_report [--k 5] [--questions fichier.json] [--min-cases 5]
Produit : data/eval/error_report.md
"""
from __future__ import annotations

import argparse
from pathlib import Path

from app.config import ROOT
from app.evaluation.evaluate import MODES, QUESTIONS, load_questions, run_question
from app.rag.pipeline import RAGPipeline

OUT = ROOT / "data" / "eval" / "error_report.md"

TYPES = {
    "echec": "Bonne réponse non retrouvée",
    "mal_classe": "Résultat peu pertinent (bon passage mal classé)",
    "faux_refus": "Faux refus (question valable déclarée sans réponse)",
    "fausse_acceptation": "Question sans réponse acceptée à tort",
    "fragile": "Succès fragile (à surveiller)",
}


def classify(r: dict) -> str | None:
    if r["answerable"]:
        if r["refused"]:
            return "faux_refus"
        if r["rank"] is None:
            return "echec"
        if r["rank"] > 1:
            return "mal_classe"
        return None
    return None if r["refused"] else "fausse_acceptation"


def probable_cause(kind: str, r: dict) -> str:
    item, hits, rel = r["item"], r["hits"], r["relevance"]
    if kind == "faux_refus":
        return "Seuils trop stricts (MIN_COVERAGE / MIN_SIMILARITY) : la question est reformulée avec des mots absents du texte."
    if kind == "fausse_acceptation":
        if item.get("near_miss"):
            return ("Question proche du corpus : les mots et le sens correspondent à des articles existants, donc les signaux de "
                    "pertinence ne peuvent pas détecter l'absence. Seul le LLM (prompt) peut refuser dans ce cas.")
        return "Seuils trop permissifs : similarité et recouvrement jugés suffisants pour une question hors corpus."
    top = hits[0].chunk if hits else None
    if kind in ("echec", "mal_classe") and top:
        if top.article == "Préambule":
            return "Le passage d'en-tête du texte (titre, visas) est retrouvé car il contient les mots du titre, sans contenu utile."
        if top.doc_id != item["expected_doc"]:
            return (f"Confusion entre textes : « {top.article} » de {top.doc_id} traite un sujet voisin "
                    "(même vocabulaire : délai, durée, amende…) et passe devant le bon passage.")
        return "Confusion entre articles du même texte : un article voisin partage plus de mots avec la question."
    if kind == "fragile":
        return "Bon passage en 1re position, mais avec une faible marge ou un faible recouvrement lexical."
    return ""


def snippet(text: str, n: int = 220) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + "…"


def build_report(pipeline: RAGPipeline, k: int, questions_path, min_cases: int, mode: str = "hybrid") -> tuple[str, dict]:
    items = load_questions(questions_path)
    by_mode = {m: [run_question(pipeline, it, m, k) for it in items] for m in MODES}
    runs = by_mode[mode]

    cases = [(classify(r), i, r) for i, r in enumerate(runs) if classify(r)]
    n_real = len(cases)
    if n_real < min_cases:  # pas assez d'erreurs : on ajoute les succès les plus fragiles
        done = {i for _, i, _ in cases}
        fragile = []
        for i, r in enumerate(runs):
            if i in done or not r["answerable"] or r["rank"] != 1:
                continue
            margin = r["hits"][0].score - (r["hits"][1].score if len(r["hits"]) > 1 else 0)
            fragile.append((r["relevance"]["coverage"], margin, i, r))
        fragile.sort(key=lambda x: (x[0], x[1]))
        cases += [("fragile", i, r) for _, _, i, r in fragile[: min_cases - n_real]]

    counts = {t: sum(1 for c, _, _ in cases if c == t) for t in TYPES}
    lines = [f"# Rapport d'erreurs : mode `{mode}`, k = {k}", ""]
    lines.append(f"Questions : {len(items)} · cas à analyser : {len(cases)} (dont {n_real} erreurs réelles)")
    lines += ["", "| Type | Nombre |", "|---|---|"] + [f"| {TYPES[t]} | {n} |" for t, n in counts.items() if n]
    for n_case, (kind, i, r) in enumerate(cases, 1):
        item, rel = r["item"], r["relevance"]
        lines += ["", f"## Cas {n_case} : {TYPES[kind]}", "", f"**Question :** {item['question']}"]
        if r["answerable"]:
            rank = f"rang {r['rank']}" if r["rank"] else f"absent du top {k}"
            lines.append(f"**Attendu :** {item['expected_doc']} · {item['expected_article']} → {rank}")
        else:
            lines.append("**Attendu :** aucune réponse dans le corpus" + (f" ({item['note']})" if item.get("note") else ""))
        lines.append(f"**Pertinence estimée :** similarité = {rel['dense_sim']}, recouvrement = {rel['coverage']}, "
                     f"jugée {'ABSENTE' if rel['absent'] else 'présente'}")
        ranks = []
        for m in MODES:
            rm = by_mode[m][i]
            ranks.append(f"{m}: {rm['rank'] or '—'}" if rm["answerable"] else f"{m}: {'refusée' if rm['refused'] else 'acceptée'}")
        lines.append("**Par mode :** " + " · ".join(ranks))
        lines += ["", "**Passages retrouvés :**", ""]
        for j, h in enumerate(r["hits"][:3], 1):
            page = f", p. {h.chunk.page}" if h.chunk.page else ""
            lines.append(f"{j}. `{h.chunk.doc_id}` · {h.chunk.article}{page} (score {h.score:.4f}) : {snippet(h.chunk.text)}")
        lines += ["", f"**Cause probable (automatique) :** {probable_cause(kind, r)}", "", "**Ton analyse :** _à compléter (pourquoi, et quelle amélioration proposer)._"]
    return "\n".join(lines) + "\n", counts


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--questions", default=str(QUESTIONS))
    ap.add_argument("--min-cases", type=int, default=5, help="nombre minimal de cas listés (complété par des succès fragiles)")
    ap.add_argument("--mode", default="hybrid", choices=MODES)
    args = ap.parse_args()
    if not Path(args.questions).exists():
        raise SystemExit(f"Fichier de questions introuvable : {args.questions}")
    p = RAGPipeline()
    if not p.is_ready():
        p.ingest()
    md, counts = build_report(p, args.k, args.questions, args.min_cases, args.mode)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(md, encoding="utf-8")
    print(f"Rapport écrit : {OUT}")
    for t, n in counts.items():
        if n:
            print(f"  {TYPES[t]} : {n}")
