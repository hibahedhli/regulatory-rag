"""Prompts : réponse strictement ancrée dans les extraits, avec citations numérotées."""
from __future__ import annotations

from app.rag.models import Hit

SYSTEM_PROMPT = """Tu es un assistant de recherche dans des textes réglementaires.
Règles strictes :
1. Réponds UNIQUEMENT à partir des extraits numérotés fournis. N'utilise aucune connaissance extérieure.
2. Après chaque affirmation, cite la ou les sources entre crochets, par exemple [1] ou [1][3].
3. Si les extraits ne contiennent pas la réponse, dis exactement : "Je n'ai pas trouvé cette information dans les textes fournis." et n'invente rien.
4. Réponds en français, de façon claire et concise. Ne donne pas d'avis juridique personnalisé.
5. Si les extraits se contredisent ou si des textes semblent de dates différentes, signale-le."""


def build_user_prompt(question: str, hits: list[Hit]) -> str:
    blocks = []
    for i, h in enumerate(hits, start=1):
        c = h.chunk
        page = f", p. {c.page}" if c.page else ""
        blocks.append(f"[{i}] {c.title} — {c.section + ' — ' if c.section else ''}{c.article}{page}\n{c.text}")
    context = "\n\n".join(blocks)
    return f"EXTRAITS :\n{context}\n\nQUESTION : {question}\n\nRÉPONSE (avec citations [n]) :"
