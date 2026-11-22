# MotoGP Entity-Aware Search Engine

An Information Retrieval (IR) web application for searching Indonesian MotoGP news articles, combining a **from-scratch TF-IDF + Cosine Similarity** baseline with a domain-specific **Entity-Aware Search** specialization.

> **Live Deployment (Vercel):**
>
> - **Web App (Frontend SSR):** https://motogp-entity-search-engine.vercel.app
> - **REST API (Backend):** https://motogp-entity-search-backend.vercel.app
> - **Interactive API Docs (Swagger):** https://motogp-entity-search-backend.vercel.app/docs

![MotoGP Entity-Aware Search Engine — Homepage](doc/preview/MotoGP%20Entity-Aware%20Search%20Homepage.png)

---

## Overview

Conventional keyword search struggles when users query MotoGP news using rider nicknames (_Pecco_, _El Diablo_, _La Bestia_, _The Doctor_), racing number codes (_MM93_, _FB63_), or team/circuit aliases that differ from the exact words printed in an article.

This project implements and evaluates two independently executable retrieval pipelines:

1. **Baseline Retrieval (`baseline`)** — From-scratch Inverted Index, TF-IDF ($\text{IDF}(t) = \log_{10}(N / \text{df}(t))$), and Cosine Similarity ($S_{\text{text}}$).
2. **Entity-Aware Retrieval (`entity`)** — Dictionary-based entity & alias recognition (_Longest-Match-First_ + word-boundary span masking), Query Entity Coverage scoring ($S_{\text{entity}}$) over an entity index in Neon PostgreSQL, linear score fusion ($S_{\text{final}} = \alpha S_{\text{text}} + \beta S_{\text{entity}}$), and automatic **Fallback Behavior** for non-entity queries.

---

## Key Features

### Information Retrieval Engine (100% From-Scratch)

- **Consistent Indonesian Preprocessing:** NFKD accent folding (`Márquez → marquez`), URL/newsroom noise cleanup, alphanumeric tokenization (`[a-z0-9]+`), pure-digit filtering (retaining domain tokens such as `fp1`, `moto2`, `vr46`), Sastrawi + domain stopword removal preserving negation (`tidak`, `bukan`, `jangan`, `tanpa`, `belum`), MotoGP term normalization, and cached Sastrawi stemming.
- **From-Scratch Vector Space Model:** Custom Inverted Index, $\text{IDF}(t) = \log_{10}(N / \text{df}(t))$, dot product, vector length, and Cosine Similarity with zero external ML/IR library dependency (`scikit-learn` is not used in the production engine).
- **3-Source Verified Entity Dictionary:** **95 canonical entities** and **390 aliases** curated from the 60-article corpus, official `motogp.com` grid/calendar records, and external motorsport sources (Wikipedia/Crash.net/Motorsport).
- **Automatic Fallback Behavior:** When no MotoGP entity is detected in a query ($E_Q = \emptyset$), the engine falls back strictly to Baseline TF-IDF without injecting artificial entity scores.

### Web Application (Server-Side Rendered)

- **Next.js App Router SSR:** Search, Compare, Article Detail (`/articles/[docId]`), and Entity Dictionary (`/entities`, `/entities/[entityId]`) are rendered server-side via React Server Components with server-to-server calls to FastAPI.
- **Side-by-Side Compare Mode:** Compares Baseline TF-IDF and Entity-Aware rankings side by side with live rank-delta indicators (`▲ +N`, `▼ -N`, `NEW`) and configurable $(\alpha, \beta)$ weight presets.
- **Telemetry & Transparency:** Displays recognized query entities (with alias provenance), fallback status, per-article score breakdown (`S_final`, `S_text`, `S_entity`), and full original news content with entity mention counts.

---

## Technology Stack

| Component               | Technology                                               |
| :---------------------- | :------------------------------------------------------- |
| **Frontend**            | Next.js 14 (App Router, SSR), TypeScript, Tailwind CSS   |
| **Backend**             | Python, FastAPI, Uvicorn, Pydantic v2                    |
| **Database**            | Neon PostgreSQL (Serverless)                             |
| **Database Driver**     | `psycopg` v3 (`psycopg[binary,pool]`)                    |
| **IR Engine**           | Pure Python From-Scratch TF-IDF & Entity Coverage (`v5`) |
| **Indonesian NLP**      | PySastrawi (cached stemming + stopwords)                 |
| **Index Serialization** | Joblib (`backend/artifacts/index.joblib`)                |
| **Hosting**             | Vercel (Frontend + Zero-Config FastAPI Backend)          |

---

## Dataset & Entity Dictionary

### News Corpus (`documents`)

Curated corpus of **60 MotoGP news articles** from three Indonesian publishers:

| Publisher | Articles |
| :-------- | -------: |
| Kompas    |       20 |
| ANTARA    |       20 |
| IDN Times |       20 |
| **Total** |   **60** |

- **Indexed Unique Vocabulary:** `1,890` stemmed terms (`documents.processed_text`)
- Original article text is preserved intact in `documents.content`.

### Entity Dictionary (`entities`, `entity_aliases`, `document_entities`)

| Category     |                                        Canonical Entities |
| :----------- | --------------------------------------------------------: |
| Rider        |                                                        50 |
| Team         |                                                        15 |
| Manufacturer |                                                        10 |
| Circuit      |                                                        20 |
| **Total**    | **95 entities · 390 aliases · 597 document-entity links** |

- **3-Source Alias Provenance:** `116` corpus-derived aliases, `192` official `motogp.com` forms & racing number codes (`MM93`, `FB63`, etc.), and `82` external nicknames/prototype bike codes/GP-to-circuit aliases.

---

## System Architecture

```text
                       User Request (Browser)
                                 |
                      Next.js Server (SSR / RSC)
                                 |  Server-to-Server (BACKEND_API_URL)
                      FastAPI Backend (Vercel)
                                 |
                 +---------------+---------------+
                 |                               |
          Text Retrieval                 Entity Retrieval
     (From-Scratch TF-IDF +         (Longest-Match Dictionary +
        Cosine Similarity)            Neon document_entities)
                 |                               |
                 +---------------+---------------+
                                 |
                    Hybrid Score Fusion (v5)
              S_final = alpha * S_text + beta * S_entity
                                 |
                          Ranked Results
```

### Scoring Formulas

- **Entity Relevance (Query Entity Coverage):**
  $$S_{\text{entity}}(D, Q) = \frac{|E_Q \cap E_D|}{|E_Q|}$$
- **Hybrid Final Score (default $\alpha = 0.8,\ \beta = 0.2$):**
  $$S_{\text{final}}(D, Q) = \alpha \cdot S_{\text{text}}(D, Q) + \beta \cdot S_{\text{entity}}(D, Q)$$
- **Fallback Rule:** If $E_Q = \emptyset$, then $S_{\text{entity}} = 0$ and $S_{\text{final}} = S_{\text{text}}$.

---

## Evaluation Results

Evaluated on **8 human-judged test queries (`Q1`–`Q8`)** spanning 4 balanced query types (**Entity Pendek**, **Entity Panjang**, **Non-Entity Pendek**, **Non-Entity Panjang**), using **TREC Depth-15 Pooling** (`Top-15 Baseline ∪ Top-15 Entity-Aware`, `138` unique query–document pairs) assessed by **2 independent human judges (`Dwimas`, `Marshall`) + 1 validator (`Ale`)** and reproduced via [`backend/scripts/run_human_evaluation.py`](backend/scripts/run_human_evaluation.py).

### 1. Entity Recognition Validation (12 Gold Standard Articles)

- **True Positives:** `118` | **False Positives:** `0` | **False Negatives:** `0`
- **Micro-Precision:** `1.0000` | **Micro-Recall:** `1.0000` | **Micro-F1:** `1.0000`

### 2. Inter-Annotator Agreement (Cohen's Kappa)

- **All Sheet Judgements ($N = 240$):** Observed agreement `87.08%` (`209/240`), **$\kappa = 0.7288$** (*Substantial Agreement*, Landis & Koch)
- **Deduplicated Union Pool ($N = 138$):** Observed agreement `86.96%` (`120/138`), **$\kappa = 0.7225$** (*Substantial Agreement*)

### 3. Document Retrieval Comparison ($\alpha = 0.8,\ \beta = 0.2$)

| Query Group                            | System                      | Precision@5  | Precision@10 |       Recall@10        |          MAP           |   MRR    |
| :------------------------------------- | :-------------------------- | :----------: | :----------: | :--------------------: | :--------------------: | :------: |
| **All Queries (`Q1`–`Q8`)**            | Baseline (TF-IDF)           |   `0.6250`   |   `0.4625`   |        `0.7842`        |        `0.7709`        | `0.9375` |
|                                        | **Proposed (Entity-Aware)** | **`0.6500`** | **`0.5250`** | **`0.8506` (+6.64%)**  | **`0.8162` (+4.53%)**  | `0.9375` |
| **Entity-Based (`Q1`–`Q4`)**           | Baseline (TF-IDF)           |   `0.7000`   |   `0.5500`   |        `0.7737`        |        `0.7115`        | `0.8750` |
|                                        | **Proposed (Entity-Aware)** | **`0.7500`** | **`0.6750`** | **`0.9066` (+13.29%)** | **`0.8021` (+9.06%)**  | `0.8750` |
| **Subgroup: Entity Pendek (`Q1`–`Q2`)**| Baseline (TF-IDF)           |   `0.6000`   |   `0.5000`   |        `0.6308`        |        `0.6128`        | `0.7500` |
|                                        | **Proposed (Entity-Aware)** | **`0.8000`** | **`0.7500`** | **`0.8846` (+25.38%)** | **`0.7602` (+14.74%)** | `0.7500` |
| **Subgroup: Entity Panjang (`Q3`–`Q4`)**| Baseline (TF-IDF)          |   `0.8000`   |   `0.6000`   |        `0.9167`        |        `0.8102`        | `1.0000` |
|                                        | **Proposed (Entity-Aware)** |   `0.7000`   |   `0.6000`   | **`0.9286` (+1.19%)**  | **`0.8440` (+3.38%)**  | `1.0000` |
| **Non-Entity / Fallback (`Q5`–`Q8`)**  | Baseline & Proposed         |   `0.5500`   |   `0.3750`   |        `0.7946`        | `0.8302` _(Identical)_ | `1.0000` |

Human relevance judgements and full CSV evaluation outputs (`cohens_kappa_report.csv`, `evaluation_metrics_summary.csv`, `evaluation_metrics_per_query.csv`, `ranking_comparison_baseline_vs_entity_aware.csv`, `alpha_beta_sensitivity.csv`) are stored in [`doc/evaluation/results/`](doc/evaluation/results/).

---

## REST API Endpoints

| Method | Endpoint                       | Description                                                               |
| :----- | :----------------------------- | :------------------------------------------------------------------------ |
| `GET`  | `/`                            | Service metadata & links to docs/health                                   |
| `GET`  | `/api/v1/health`               | API health, Neon PostgreSQL status, and index readiness                   |
| `GET`  | `/api/v1/index/status`         | Active index summary (`engine`, document/term/entity counts)              |
| `GET`  | `/api/v1/search`               | Search documents (`q`, `mode=entity\|baseline`, `top_k`, `alpha`, `beta`) |
| `GET`  | `/api/v1/search/compare`       | Side-by-side Baseline vs Entity-Aware search results                      |
| `GET`  | `/api/v1/documents`            | Paginated document list with optional `media` filter                      |
| `GET`  | `/api/v1/documents/{doc_id}`   | Full original article content and indexed entities                        |
| `GET`  | `/api/v1/entities`             | List all verified entities with aliases (`category` filter supported)     |
| `GET`  | `/api/v1/entities/{entity_id}` | Entity profile, aliases, official reference, and related articles         |
| `GET`  | `/api/v1/entities/recognize`   | Debug entity recognition on arbitrary text (`text`)                       |
| `POST` | `/api/v1/admin/index/rebuild`  | Rebuild & hot-reload index from Neon PostgreSQL                           |
| `GET`  | `/api/v1/evaluation/run`       | Run live `Precision@K`, `Recall@K`, and `MAP` evaluation                  |

---

## Repository Structure

```text
motogp-entity-search-engine/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI routers (search, documents, entities, health, index, evaluation)
│   │   ├── core/           # Settings (config.py) and psycopg connection pool (db.py)
│   │   ├── services/       # From-scratch TF-IDF indexer, search, entity recognizer, preprocessing, DB repo
│   │   ├── main.py         # FastAPI entrypoint (Vercel zero-config)
│   │   └── schemas.py      # Pydantic response models
│   ├── artifacts/
│   │   └── index.joblib    # Prebuilt v5 from-scratch index artifact
│   ├── scripts/            # build_index.py, run_human_evaluation.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── articles/[docId]/   # SSR Article Detail page + loading skeleton
│   │   ├── entities/           # SSR Entity Directory & [entityId] Detail pages
│   │   ├── icon.svg            # Motorsport Editorial browser tab favicon
│   │   ├── layout.tsx          # Google Fonts (Barlow Condensed, Titillium Web, Plus Jakarta Sans, JetBrains Mono)
│   │   └── page.tsx            # SSR Search & Compare workspace with Suspense streaming
│   ├── components/             # Motorsport Editorial UI components
│   ├── lib/                    # Server API client, types, formatters
│   ├── public/                 # MotoGP hero background & logo
│   └── .env.local.example
├── doc/
│   ├── corpus(combined)/       # Original Excel corpus
│   ├── evaluation/             # Human relevance judgements (Q1-Q8) & official evaluation CSVs
│   ├── Experiment-Result/      # Historical Colab experiment CSV outputs (v2-v5)
│   └── preview/                # README preview screenshots
└── README.md
```

---

## Getting Started (Local Development)

### Prerequisites

- **Python 3.11+**
- **Node.js 18+**
- **Neon PostgreSQL** connection string (optional for offline artifact testing, required for live DB queries)

### 1. Backend Setup (`http://localhost:8000`)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\pip.exe install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env` and set your Neon PostgreSQL connection string (`DATABASE_URL=...`), then run:

```powershell
# Optional: rebuild index directly from Neon PostgreSQL
.\.venv\Scripts\python.exe -m scripts.build_index

# Start FastAPI server
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup (`http://localhost:3000`)

```powershell
cd frontend
npm ci
copy .env.local.example .env.local
npm run dev
```

Open **http://localhost:3000** in your browser.

---

## Deployment (Vercel)

Both services are deployed as independent Vercel projects from this monorepo:

1. **Backend Project (`Root Directory: backend`, Framework Preset: `FastAPI`):**
   - Environment variables: `DATABASE_URL` (Neon `-pooler` URL), `DEFAULT_ALPHA=0.8`, `DEFAULT_BETA=0.2`, `USE_STORED_PROCESSED_TEXT=true`, `USE_STORED_DOCUMENT_ENTITIES=true`, `CORS_ORIGINS=http://localhost:3000,https://<frontend-domain>`.
2. **Frontend Project (`Root Directory: frontend`, Framework Preset: `Next.js`):**
   - Environment variable: `BACKEND_API_URL=https://<backend-domain>`.
