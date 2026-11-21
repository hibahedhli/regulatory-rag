"""Génération de la réponse : Claude (API), Ollama (local) ou mode extractif sans LLM."""
from __future__ import annotations

import os

from app.config import Settings
from app.generation.prompt import SYSTEM_PROMPT, build_user_prompt
from app.rag.models import Hit


def _extractive(hits: list[Hit], note: str = "") -> str:
    if not hits:
        return "Je n'ai pas trouvé cette information dans les textes fournis."
    lines = [note] if note else []
    lines.append("Mode sans LLM — passages les plus pertinents :")
    for i, h in enumerate(hits[:3], start=1):
        excerpt = h.chunk.text.replace("\n", " ")
        excerpt = excerpt if len(excerpt) <= 400 else excerpt[:400].rsplit(" ", 1)[0] + "…"
        lines.append(f"- {h.chunk.article} : {excerpt} [{i}]")
    return "\n".join(lines)


def _anthropic(settings: Settings, system: str, user: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    msg = client.messages.create(
        model=settings.anthropic_model,
        max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


def _ollama(settings: Settings, system: str, user: str) -> str:
    import requests

    r = requests.post(
        f"{settings.ollama_url}/api/chat",
        json={
            "model": settings.ollama_model,
            "stream": False,
            "keep_alive": "10m",  # garde le modèle en mémoire entre deux questions
            "options": {"num_ctx": 4096, "temperature": 0.1},  # num_ctx : sinon le prompt est tronqué (2048 par défaut)
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        },
        timeout=600,  # un modèle local sans GPU peut être lent à la 1re réponse
    )
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


def generate_answer(settings: Settings, question: str, hits: list[Hit]) -> str:
    if not hits:
        return "Je n'ai pas trouvé cette information dans les textes fournis."
    provider = settings.llm_provider.lower()
    if provider == "none":
        return _extractive(hits)
    user = build_user_prompt(question, hits)
    try:
        if provider == "anthropic":
            return _anthropic(settings, SYSTEM_PROMPT, user)
        if provider == "ollama":
            return _ollama(settings, SYSTEM_PROMPT, user)
        raise ValueError(f"LLM_PROVIDER inconnu : {provider}")
    except Exception as exc:  # repli propre si l'API/le modèle est indisponible
        hint = ""
        if provider == "ollama":
            hint = f" Vérifie qu'Ollama est lancé et que le modèle '{settings.ollama_model}' est installé (`ollama list`)."
        return _extractive(hits, note=f"(LLM indisponible : {type(exc).__name__}.{hint})\n")
