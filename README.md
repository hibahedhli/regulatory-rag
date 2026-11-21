# Assistant de recherche dans les textes réglementaires (RAG)

Permet de poser des questions en langage naturel sur un ensemble de textes réglementaires et d'obtenir
des réponses **accompagnées des références aux documents sources** (document, chapitre, article, page).

> Le projet est livré **sans aucun document** : l'utilisateur ajoute ses propres fichiers (PDF, TXT, MD, HTML) depuis l'onglet « Mes documents » de l'interface (ou en les déposant dans `data/raw/`).
> Le dossier `demo/` contient 3 textes **fictifs** et 12 questions, uniquement pour tester l'outil ou les tests automatiques.

## Architecture

```
            INDEXATION (hors ligne)                              REQUÊTE (en ligne)
 data/raw ─► loader ─► chunker par ARTICLE ─► embeddings         Question
 (PDF/TXT/    (texte + n° page)  (titre, chapitre,    │             │
  MD/HTML)                        article, page)      ▼             ├─► recherche vectorielle (ChromaDB)
                                              ChromaDB (vecteurs)   ├─► BM25 (mots-clés, n° d'articles)
                                              chunks.jsonl (BM25)   ▼
                                                              fusion RRF ─► reranker (optionnel)
                                                                    ▼
                                                      LLM (Claude / Ollama / extractif)
                                                      prompt contraint + citations [n]
                                                                    ▼
                                                      Réponse + sources (doc, article, page, extrait)

   FastAPI : /ask  /ingest  /upload  /documents  /health          UI Streamlit        Évaluation (recall@k, MRR)
```

### Structure du projet

```
app/
  config.py              # paramètres (.env)
  ingestion/loader.py    # lecture PDF/TXT/MD/HTML, n° de page
  ingestion/chunker.py   # découpage par article + contexte (titre/chapitre)
  indexing/embedder.py   # sentence-transformers (multilingue) ou hashing (hors ligne)
  retrieval/dense.py     # recherche vectorielle ChromaDB
  retrieval/bm25.py      # recherche lexicale
  retrieval/hybrid.py    # fusion RRF
  retrieval/reranker.py  # cross-encoder (optionnel)
  generation/prompt.py   # prompt système + contexte numéroté
  generation/llm.py      # Claude, Ollama ou mode extractif (repli automatique)
  rag/pipeline.py        # orchestration : ingest / search / ask
  api/main.py            # API FastAPI
  ui/streamlit_app.py    # interface
  evaluation/evaluate.py # recall@k et MRR par mode
scripts/                 # ingest.py, ask.py (CLI)
tests/                   # chunker, pipeline, API
data/raw/                # documents de l'utilisateur (vide au départ)
data/eval/               # ton jeu de questions d'évaluation (à créer)
demo/                    # textes fictifs + questions de démo (optionnel)
.streamlit/config.toml   # thème violet / blanc
```

## Installation

```bash
python -m venv .venv && source .venv/bin/activate     # Windows : .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # puis adapter
```

## Utilisation

```bash
uvicorn app.api.main:app --reload                     # terminal 1 : API -> http://localhost:8000/docs
streamlit run app/ui/streamlit_app.py                 # terminal 2 : UI  -> http://localhost:8501
```

1. Onglet **« Mes documents »** : ajoute tes fichiers, ils sont lus, découpés et indexés automatiquement.
2. Onglet **« Poser une question »** : la réponse s'affiche à gauche, les sources (document, article, page, extrait) à droite.

Ligne de commande (optionnel) : `python -m scripts.ingest` puis `python -m scripts.ask "ta question"`.
Pour essayer sans documents à toi : copie le contenu de `demo/documents/` dans `data/raw/` (ou envoie-les via l'interface).

Avec Docker : `docker compose up --build` (API :8000, UI :8501).

### Démarrage rapide avec Ollama (configuration par défaut du `.env` fourni)

```bash
# 1. Installer Ollama (ollama.com) puis télécharger un modèle
ollama pull mistral            # PC modeste : ollama pull llama3.2:3b  (et mettre OLLAMA_MODEL=llama3.2:3b dans .env)
# 2. Indexer et interroger
python -m scripts.ingest
python -m scripts.ask "Sous quel délai déclarer un incident de cybersécurité majeur ?"
```
Si la réponse indique « LLM indisponible » : lance Ollama et vérifie le nom du modèle avec `ollama list`.
Avec Docker, `docker-compose.yml` pointe déjà vers l'Ollama de ta machine (`host.docker.internal`).

### Choisir le LLM (`.env`)

| `LLM_PROVIDER` | Description |
|---|---|
| `none` | Mode extractif : renvoie les passages pertinents sans génération (aucune clé nécessaire) |
| `anthropic` | Claude via API (`ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`) |
| `ollama` | Modèle local (`OLLAMA_URL`, `OLLAMA_MODEL`, ex. `mistral`) |

Si le LLM est indisponible, le système retombe automatiquement sur le mode extractif.

### Embeddings

- Par défaut : `intfloat/multilingual-e5-small` (français/arabe/anglais, léger). Pour plus de qualité : `BAAI/bge-m3`.
- `EMBEDDING_BACKEND=hashing` : embeddings hors ligne sans téléchargement (tests, démo rapide ; qualité limitée).
- Après changement de modèle d'embedding ou de paramètres de découpage : relancer `python -m scripts.ingest`.

## Évaluation

Le **jeu d'évaluation** est une liste de questions dont tu connais la bonne réponse, avec l'article qui la contient.
Il sert à mesurer objectivement la qualité de la recherche (au lieu de juger « à l'œil ») et à comparer les modes
`dense`, `bm25` et `hybrid` (recall@k : le bon article est-il dans les k premiers ? MRR : à quel rang ?).

Crée `data/eval/eval_questions.json` (30 à 50 questions sur TES documents) :

```json
[
  {"question": "Quel est le délai de déclaration d'un incident ?",
   "expected_doc": "nom-du-fichier-sans-extension",
   "expected_article": "Article 6"}
]
```
`expected_doc` = nom du fichier en minuscules, sans extension, tirets à la place des espaces et symboles
(`Loi 09-08.pdf` -> `loi-09-08`). Puis :

```bash
python -m app.evaluation.evaluate --k 5
python -m app.evaluation.evaluate --k 5 --questions demo/eval_questions.json   # avec les textes de démo
```
Active `RERANKER_ENABLED=true` pour mesurer l'apport du reranking.

## Tests

```bash
pytest -q
```

## Choix de conception

- **Découpage par article** : un texte juridique est déjà structuré ; une citation « Article 8 » est ainsi exacte.
- **Contexte injecté dans l'embedding** (titre + chapitre + article) pour lever les ambiguïtés entre textes.
- **Recherche hybride (RRF)** : le vectoriel capte le sens, BM25 capte les termes exacts et numéros d'articles.
- **Prompt contraint** : réponse uniquement depuis les extraits, citations `[n]`, refus explicite si l'information est absente.
- **Repli sans LLM** : l'application reste utile même sans API.

## Limites et pistes d'amélioration

- PDF scannés : ajouter de l'OCR (`pytesseract`).
- Gestion des versions/abrogations : ajouter une date de version en métadonnée et filtrer à la recherche.
- Références croisées entre articles (« voir article 8 ») : étendre automatiquement le contexte.
- Reformulation de la question (query rewriting) et historique de conversation.
- L'outil aide à la recherche ; il ne remplace pas un avis juridique.
