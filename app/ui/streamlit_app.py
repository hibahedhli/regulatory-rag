"""Interface Streamlit, style « conversation » (inspirée de Claude), thème sombre, rouge #af0c0c.

- Barre latérale : nouvelle conversation, documents (ajout / suppression), réglages.
- Zone centrale : conversation, réponses avec citations et sources, saisie en bas.
Aucun document n'est préchargé : l'utilisateur ajoute les siens.
"""
import html
import os
import re

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
FORMATS = ["pdf", "docx", "txt", "md", "html"]
SUGGESTIONS = [
    "Quelles sont les obligations principales ?",
    "Quels délais sont mentionnés ?",
    "Quelles sanctions sont prévues ?",
]

st.set_page_config(page_title="Assistant réglementaire", page_icon="✦", layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
:root{   --v: #6B507B;
    --vh: #594166;
    --vl: #FDFD96;

    --bg: #2B202E;
    --side: #241B27;
    --surf: #322638;
    --surf2: #2B202E;
    --bd: #514157;

    --ink: #F2EDF4;
    --muted: #B5A9BA;
    --soft: #D8CDDF;
      --serif:'Iowan Old Style','Palatino Linotype','Book Antiqua',Georgia,serif;}

header[data-testid="stHeader"]{background:transparent;}
.stApp{background:var(--bg);color:var(--ink);}
.block-container{max-width:800px;padding-top:2.2rem;padding-bottom:9rem;}
[data-testid="stSidebar"]{background:var(--side);border-right:1px solid var(--bd);}

/* ---------- accueil ---------- */
.hello{text-align:center;margin:11vh 0 30px 0;}
.hello .mark{font-size:2.8rem;color:var(--vl);line-height:1;}
.hello h1{font-family:var(--serif);font-weight:500;font-size:2.6rem;color:var(--ink);margin:12px 0 10px 0;padding:0;letter-spacing:-.01em;}
.hello p{color:var(--muted);font-size:1.05rem;margin:0;}

/* ---------- conversation ---------- */
.u-row{display:flex;justify-content:flex-end;margin:24px 0 14px 0;}
.u-bubble{background:var(--surf);border:1px solid var(--bd);color:var(--ink);padding:12px 18px;border-radius:20px 20px 6px 20px;max-width:82%;line-height:1.55;}
.a-row{display:flex;gap:14px;margin:6px 0 28px 0;}
.a-mark{flex:none;width:30px;height:30px;border-radius:50%;background:var(--v);color:#fff;display:flex;align-items:center;justify-content:center;font-size:.95rem;margin-top:2px;}
.a-body{flex:1;min-width:0;color:var(--ink);font-size:1.04rem;line-height:1.75;}
.cite{display:inline-flex;align-items:center;justify-content:center;min-width:19px;height:19px;padding:0 5px;border-radius:10px;
      background:rgba(175,12,12,.22);color:var(--vl);border:1px solid rgba(175,12,12,.55);font-size:.7rem;font-weight:700;margin:0 2px;vertical-align:2px;}
.pills{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px;}
.pill{display:inline-flex;gap:7px;align-items:center;border:1px solid var(--bd);border-radius:999px;padding:4px 12px 4px 5px;font-size:.8rem;color:var(--ink);background:var(--surf2);}
.pill i{font-style:normal;background:var(--v);color:#fff;border-radius:50%;width:18px;height:18px;display:inline-flex;align-items:center;justify-content:center;font-size:.68rem;font-weight:700;}
details.srcs{margin-top:12px;border:1px solid var(--bd);border-radius:14px;background:var(--surf2);padding:2px 16px;}
details.srcs summary{cursor:pointer;color:var(--muted);font-size:.86rem;padding:10px 0;font-weight:600;}
details.srcs summary:hover{color:var(--vl);}
.sr{padding:12px 0;border-top:1px solid var(--bd);}
.sr b{color:var(--ink);font-size:.9rem;} .sr .m{color:var(--muted);font-size:.8rem;margin-left:6px;}
.sr p{margin:6px 0 0 0;font-size:.86rem;line-height:1.55;color:var(--soft);}

/* ---------- barre latérale ---------- */
.brand{font-family:var(--serif);font-size:1.4rem;color:var(--ink);font-weight:600;display:flex;align-items:center;gap:8px;margin:4px 0 14px 0;}
.brand span{color:var(--vl);}
.side-label{font-size:.72rem;font-weight:800;letter-spacing:.09em;text-transform:uppercase;color:var(--muted);margin:20px 0 8px 0;}
.doc{font-size:.88rem;color:var(--ink);line-height:1.3;word-break:break-word;}
.doc small{display:block;color:var(--muted);font-size:.74rem;margin-top:2px;}
.doc .warn{color:#F59E0B;}
.side-note{color:var(--muted);font-size:.78rem;line-height:1.5;margin-top:18px;}

/* ---------- composants Streamlit ---------- */
[data-testid="stBottom"]>div{background:linear-gradient(to top,var(--bg) 72%,rgba(37,36,36,0));}
[data-testid="stChatInput"]{border:1px solid var(--bd);border-radius:26px;background:var(--surf);box-shadow:0 6px 22px rgba(0,0,0,.35);}
[data-testid="stChatInput"]:focus-within{border-color:var(--v);box-shadow: 0 6px 26px rgba(242,196,109,.25);}
[data-testid="stChatInput"] textarea{font-size:1.02rem;color:var(--ink);}
[data-testid="stChatInputSubmitButton"]{background:var(--v);color:#fff;border-radius:14px;}
.stButton>button{background:var(--surf);color:var(--ink);border:1px solid var(--bd);border-radius:14px;font-weight:600;}
.stButton>button:hover{background:#3A3636;border-color:var(--v);color:#fff;}
[data-testid="stBaseButton-primary"]{background:var(--v) !important;color:#fff !important;border:none !important;}
[data-testid="stBaseButton-primary"]:hover{background:var(--vh) !important;}
[data-testid="stFileUploader"] section{border:1.5px dashed var(--bd);border-radius:14px;background:var(--surf2);}
[data-testid="stExpander"]{border:1px solid var(--bd);border-radius:12px;background:var(--surf2);}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- utilitaires
def esc(text) -> str:
    return html.escape(str(text))


def short(text: str, n: int = 34) -> str:
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def call_api(method: str, path: str, timeout: int = 900, **kwargs):
    try:
        r = requests.request(method, f"{API_URL}{path}", timeout=timeout, **kwargs)
    except requests.RequestException:
        return None, "API injoignable. Lance d'abord `uvicorn app.api.main:app`."
    if not r.ok:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        return None, str(detail)
    return r.json(), None


def render_answer(text: str) -> str:
    safe = esc(text).replace("\n", "<br>")
    return re.sub(r"\[(\d+)\]", r'<span class="cite">\1</span>', safe)


def user_html(text: str) -> str:
    return f'<div class="u-row"><div class="u-bubble">{esc(text)}</div></div>'


def assistant_html(d: dict) -> str:
    sources = d.get("sources", [])
    cited = [s for s in sources if s["cited"]] or sources[:3]
    pills = "".join(f'<span class="pill"><i>{s["n"]}</i>{esc(s["article"])} · {esc(short(s["title"]))}</span>' for s in cited)
    rows = ""
    for s in sources:
        page = f" · p. {s['page']}" if s.get("page") else ""
        section = f"{esc(s['section'])} · " if s.get("section") else ""
        rows += (
            f'<div class="sr"><b>[{s["n"]}] {esc(s["title"])}</b>'
            f'<span class="m">{section}{esc(s["article"])}{page}</span><p>{esc(s["excerpt"])}</p></div>'
        )
    block = ""
    if sources:
        block = (
            f'<div class="pills">{pills}</div>'
            f'<details class="srcs"><summary>Voir les {len(sources)} passages consultés</summary>{rows}</details>'
        )
    return f'<div class="a-row"><div class="a-mark">✦</div><div class="a-body">{render_answer(d["answer"])}{block}</div></div>'


# ---------------------------------------------------------------- état
docs, doc_error = call_api("get", "/documents", timeout=15)
docs = docs or []
n_chunks = sum(d["chunks"] for d in docs)
st.session_state.setdefault("messages", [])
st.session_state.setdefault("uploader_key", 0)
messages = st.session_state["messages"]

# ---------------------------------------------------------------- barre latérale
with st.sidebar:
    st.markdown('<div class="brand"><span>✦</span> Assistant réglementaire</div>', unsafe_allow_html=True)
    if st.button("＋  Nouvelle conversation", use_container_width=True, type="primary"):
        st.session_state["messages"] = []
        st.rerun()

    st.markdown(f'<div class="side-label">Documents · {len(docs)}</div>', unsafe_allow_html=True)
    if not docs:
        st.caption("Aucun document. Ajoute les tiens ci-dessous.")
    for i, d in enumerate(docs):
        c1, c2 = st.columns([6, 1.3], vertical_alignment="center")
        meta = '<span class="warn">⚠ aucun texte extrait (PDF scanné ?)</span>' if d["chunks"] == 0 else f'{d["chunks"]} passages · {d["size_kb"]} Ko'
        c1.markdown(f'<div class="doc">{esc(short(d["title"], 60))}<small>{meta}</small></div>', unsafe_allow_html=True)
        if c2.button("✕", key=f"del_{i}", help="Supprimer ce document"):
            _, err = call_api("delete", f"/documents/{d['filename']}")
            if err:
                st.error(err)
            else:
                st.rerun()

    files = st.file_uploader(
        "Ajouter des documents", type=FORMATS, accept_multiple_files=True,
        label_visibility="collapsed", key=f"uploader_{st.session_state['uploader_key']}",
    )
    if st.button("Ajouter et indexer", disabled=not files, use_container_width=True):
        with st.spinner("Lecture et indexation…"):
            res, err = call_api("post", "/upload", files=[("files", (f.name, f.getvalue())) for f in files])
        if err:
            st.error(err)
        else:
            if res.get("rejected"):
                st.warning(f"Ignorés : {', '.join(res['rejected'])}")
            st.session_state["uploader_key"] += 1
            st.rerun()

    with st.expander("Réglages de recherche"):
        mode = st.selectbox("Mode", ["hybrid", "dense", "bm25"], help="hybrid = sens + mots-clés (recommandé)")
        top_k = st.slider("Passages consultés", 1, 10, 5)
    st.markdown(
        '<div class="side-note">Vérifie toujours la réponse dans les sources. '
        "L'outil aide à la recherche, il ne remplace pas un avis juridique.</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------- conversation
ready = n_chunks > 0 and not doc_error
typed = st.chat_input("Pose une question sur tes documents…" if ready else "Ajoute d'abord un document (panneau de gauche)", disabled=not ready)
prompt = typed or st.session_state.pop("pending", None)

if doc_error:
    st.error(doc_error)

if not messages and not prompt:
    if ready:
        st.markdown(
            '<div class="hello"><div class="mark">✦</div><h1>Que veux-tu savoir<br>sur tes textes ?</h1>'
            "<p>Pose ta question : la réponse cite les articles et les documents sources.</p></div>",
            unsafe_allow_html=True,
        )
        cols = st.columns(len(SUGGESTIONS))
        for col, text in zip(cols, SUGGESTIONS):
            if col.button(text, use_container_width=True):
                st.session_state["pending"] = text
                st.rerun()
    elif not doc_error:
        st.markdown(
            '<div class="hello"><div class="mark">✦</div><h1>Commence par ajouter<br>tes documents</h1>'
            "<p>Utilise le panneau de gauche (PDF, Word, TXT, Markdown ou HTML), puis pose tes questions ici.</p></div>",
            unsafe_allow_html=True,
        )

for m in messages:
    st.markdown(user_html(m["content"]) if m["role"] == "user" else assistant_html(m["data"]), unsafe_allow_html=True)

if prompt and ready:
    st.markdown(user_html(prompt), unsafe_allow_html=True)
    with st.spinner("Recherche dans tes documents…"):
        data, err = call_api("post", "/ask", timeout=600, json={"question": prompt, "top_k": top_k, "mode": mode})
    if err:
        st.error(err)
    else:
        messages.append({"role": "user", "content": prompt})
        messages.append({"role": "assistant", "data": data})
        st.rerun()
