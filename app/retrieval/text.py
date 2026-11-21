"""Normalisation et tokenisation légère (français) partagées par BM25 et l'embedder hors ligne."""
from __future__ import annotations

import re
import unicodedata

STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "du", "de", "d", "l", "et", "ou", "a", "au", "aux", "en",
    "est", "sont", "que", "qui", "quoi", "dans", "par", "pour", "sur", "ce", "cette", "ces", "se",
    "sa", "son", "ses", "il", "elle", "ils", "elles", "on", "ne", "pas", "plus", "avec", "tout",
    "quel", "quelle", "quels", "quelles", "doit", "doivent", "peut", "peuvent", "etre", "avoir",
}


def strip_accents(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def tokenize(text: str) -> list[str]:
    text = strip_accents(text.lower())
    tokens = []
    for tok in re.findall(r"\w+", text, flags=re.UNICODE):
        if tok in STOPWORDS or (len(tok) < 2 and not tok.isdigit()):
            continue
        if len(tok) > 4 and tok.endswith(("s", "x")):  # pluriels
            tok = tok[:-1]
        tokens.append(tok)
    return tokens
