# Assistant de recherche dans les textes réglementaires (RAG)

Permet de poser des questions en langage naturel sur un ensemble de textes réglementaires et d'obtenir
des réponses **accompagnées des références aux documents sources** (document, chapitre, article, page).

> Le projet est livré **sans aucun document** : l'utilisateur ajoute ses propres fichiers (PDF, DOCX, TXT, MD, HTML) depuis l'onglet « Mes documents » de l'interface (ou en les déposant dans `data/raw/`).
> Le dossier `demo/` contient 7 textes **fictifs** et 32 questions, uniquement pour tester l'outil ou les tests automatiques.

## Architecture

```
            INDEXATION (hors ligne)                              REQUÊTE (en ligne)
 data/raw ─► loader ─► chunker par ARTICLE ─► embeddings         Question
 (PDF/TXT/    (texte + n° page)  (titre, chapitre,    │             │
  DOCX/MD/HTML)                        article, page)      ▼             ├─► recherche vectorielle (ChromaDB)
                                              ChromaDB (vecteurs)   ├─► BM25 (mots-clés, n° d'articles)
                                              chunks.jsonl (BM25)   ▼
                                                              fusion RRF ─► reranker (optionnel)
                                                                    ▼
                                                      LLM (Ollama / extractif)
                                                      prompt contraint + citations [n]
                                                                    ▼
                                                      Réponse + sources (doc, article, page, extrait)

   FastAPI : /ask  /ingest  /upload  /documents  /health          UI Streamlit        Évaluation (recall@k, MRR)
```

### Structure du projet

```
app/
  config.py              # paramètres (.env)
  ingestion/loader.py    # lecture PDF/DOCX/TXT/MD/HTML, n° de page
  ingestion/chunker.py   # découpage par article + contexte (titre/chapitre)
  indexing/embedder.py   # sentence-transformers (multilingue) ou hashing (hors ligne)
  retrieval/dense.py     # recherche vectorielle ChromaDB
  retrieval/bm25.py      # recherche lexicale
  retrieval/hybrid.py    # fusion RRF
  retrieval/reranker.py  # cross-encoder (optionnel)
  generation/prompt.py   # prompt système + contexte numéroté
  generation/llm.py      # Ollama ou mode extractif (repli automatique)
  rag/pipeline.py        # orchestration : ingest / search / ask
  api/main.py            # API FastAPI
  ui/streamlit_app.py    # interface
  evaluation/evaluate.py     # recall@k, MRR, détection des questions sans réponse, calibration des seuils
  evaluation/error_report.py # rapport d'erreurs (Markdown) pour l'analyse
scripts/                 # ingest.py, ask.py (CLI)
tests/                   # chunker, pipeline, API
data/raw/                # documents de l'utilisateur (vide au départ)
data/eval/               # jeu de questions, tests_manuels.md, error_report.md (analyses)
demo/                    # 7 textes fictifs (txt, md, html, docx, pdf) + 32 questions de démo (optionnel)
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
| `ollama` | Modèle local (`OLLAMA_URL`, `OLLAMA_MODEL`, ex. `mistral`) |

Si le LLM est indisponible, le système retombe automatiquement sur le mode extractif.

### Embeddings

- Par défaut : `intfloat/multilingual-e5-small` (français/arabe/anglais, léger). Pour plus de qualité : `BAAI/bge-m3`.
- `EMBEDDING_BACKEND=hashing` : embeddings hors ligne sans téléchargement (tests, démo rapide ; qualité limitée).
- Après changement de modèle d'embedding ou de paramètres de découpage : relancer `python -m scripts.ingest`.

## Réponses absentes

Une question dont la réponse n'est pas dans les documents doit recevoir « Je n'ai pas trouvé cette information… »,
pas une réponse inventée. Deux signaux sont calculés pour chaque question :

- **similarité** : cosinus entre la question et le meilleur passage (`MIN_SIMILARITY`) ;
- **recouvrement lexical** : part des mots de la question présents dans le meilleur passage (`MIN_COVERAGE`, 0.34 par défaut).

La question est jugée **sans réponse** seulement si les **deux** signaux sont faibles (cela évite de refuser une question
reformulée avec d'autres mots). Dans ce cas le LLM n'est pas appelé, et l'interface affiche un bandeau « Aucune réponse
dans tes documents » avec les passages les plus proches, repliés.

**Limite connue** : une question *proche du corpus* mais sans réponse (ex. « quelle amende pour le non-respect du
télétravail ? » alors qu'aucun article ne prévoit de sanction) partage des mots et un sens avec de vrais articles : elle
n'est pas détectée par ces seuils. Seul le prompt (« réponds uniquement à partir des extraits ») peut alors faire refuser
le LLM, sans garantie. Ces cas apparaissent dans le rapport d'erreurs.

**Seuils** : `MIN_SIMILARITY` dépend du modèle d'embedding. La valeur par défaut pour `multilingual-e5-small` (0.78) est une
estimation non vérifiée : calibre-la avec `python -m app.evaluation.evaluate` (voir ci-dessous), qui propose une valeur.

## Évaluation

Le **jeu d'évaluation** est une liste de questions dont tu connais la réponse (ou l'absence de réponse). Il sert à
mesurer la qualité de la recherche et de la détection d'absence avec des chiffres, et à comparer `dense`, `bm25` et `hybrid`.
Crée `data/eval/eval_questions.json` (30 à 50 questions sur TES documents, dont une part sans réponse) :

```json
[
  {"question": "Quel est le délai de déclaration d'un incident ?",
   "expected_doc": "nom-du-fichier-sans-extension", "expected_article": "Article 6"},
  {"question": "Quelle est la capitale de la France ?", "answerable": false},
  {"question": "Quelle amende pour le non-respect du télétravail ?", "answerable": false, "near_miss": true,
   "note": "proche du corpus mais sans réponse"}
]
```
`expected_doc` = nom du fichier en minuscules, sans extension, tirets à la place des espaces et symboles
(`Loi 09-08.pdf` -> `loi-09-08`). `near_miss` marque les questions sans réponse mais proches du sujet : elles sont
comptées à part, car les seuils ne peuvent pas les détecter.

```bash
python -m app.evaluation.evaluate --k 5            # recall@k, MRR, refus, calibration, suggestion de MIN_SIMILARITY
python -m app.evaluation.error_report --k 5        # écrit data/eval/error_report.md
# avec les textes de démo (copiés dans data/raw) :
python -m app.evaluation.evaluate --questions demo/eval_questions.json
```
Métriques : **recall@k** (le bon article est-il dans les k premiers ?), **MRR** (à quel rang ?), **hors-sujet refusées**
(questions sans rapport correctement refusées), **faux refus** (questions valables refusées à tort, doit rester à 0).

### Analyse des erreurs (livrable)

`error_report` liste, pour chaque cas problématique : la question, le passage attendu et son rang, les 3 passages
retrouvés, le rang dans chaque mode, une cause probable automatique, et un espace « Ton analyse » à compléter.
Types de cas : bonne réponse non retrouvée, bon passage mal classé (résultat peu pertinent), faux refus, question sans
réponse acceptée à tort. S'il y a moins de 5 erreurs, il complète avec les succès les plus fragiles (`--min-cases`).
Pour chaque cas, explique la cause (vocabulaire différent, articles voisins, textes qui se ressemblent, découpage…)
et propose une amélioration.

### Résultats rendus

- `data/eval/tests_manuels.md` : 22 questions testées à la main dans l'interface (7 sans réponse, 8 avec réponse, 7 pièges), avec le résultat de chacune (19 réussies, 3 échecs).
- `data/eval/error_report.md` : rapport de l'évaluation automatique (32 questions, mode `hybrid`, k = 5), complété avec les analyses : 11 cas, dont 7 erreurs réelles, 1 limite et 3 succès fragiles.

Attention : `python -m app.evaluation.error_report` réécrit `error_report.md` et efface les analyses. Sauvegarde le fichier avant de relancer la commande.

## Construire ton corpus

L'énoncé demande plusieurs textes réglementaires publics ou fictifs. Conseils :

- **5 à 10 documents**, de formats variés (PDF texte, DOCX, HTML) pour montrer la robustesse de l'extraction.
- **Inclure des textes qui se ressemblent** (ex. deux textes avec des délais ou des durées de conservation différents) :
  c'est ce qui produit des erreurs intéressantes à analyser.
- **Inclure au moins un cas difficile** (PDF sur deux colonnes, tableaux, article très long).
- Pistes de sources publiques, **à vérifier toi-même** (existence, version à jour, conditions de réutilisation) :
  Journal officiel de la République tunisienne (JORT), site de l'Instance nationale de protection des données
  personnelles (INPDP), EUR-Lex (RGPD), Légifrance.
- Garde les **références exactes** de chaque texte (titre, numéro, date) pour ton rapport.
- Les documents ajoutés par l'interface restent dans `data/raw/`, ignoré par Git : ils ne sont pas publiés sur GitHub.

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

- Anciens fichiers Word `.doc` : non supportés (les convertir en `.docx`).
- PDF scannés : ajouter de l'OCR (`pytesseract`).
- Question proche du corpus mais sans réponse : non détectable par les seuils (voir « Réponses absentes »).
- Gestion des versions/abrogations : ajouter une date de version en métadonnée et filtrer à la recherche.
- Références croisées entre articles (« voir article 8 ») : étendre automatiquement le contexte.
- Reformulation de la question (query rewriting) et historique de conversation.
- L'outil aide à la recherche ; il ne remplace pas un avis juridique.
