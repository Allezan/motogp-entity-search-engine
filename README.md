
# MotoGP Entity-Aware Search Engine

An Information Retrieval search engine for MotoGP news, designed to retrieve relevant articles through traditional text-based ranking and entity-aware retrieval.

> **Project Status:** In Development

## Overview

MotoGP Entity-Aware Search Engine is an academic Information Retrieval project that explores how domain-specific entity information can improve news retrieval.

The system uses **TF-IDF with Cosine Similarity** as its baseline retrieval method and introduces **Entity-Aware Search** as its specialization.

Unlike conventional keyword-based retrieval, Entity-Aware Search considers named entities such as riders, teams, manufacturers, and circuits to provide additional context during document ranking.

## Key Features

### Baseline Retrieval
- Text preprocessing and normalization.
- TF-IDF document representation.
- Cosine Similarity-based document ranking.

### Entity-Aware Search
- Domain-specific entity dictionary.
- Entity and alias recognition.
- Entity normalization and resolution.
- Entity-based document indexing.
- Combined text and entity relevance scoring.

### Search Evaluation
- Precision@K
- Recall
- Mean Average Precision (MAP)
- Baseline vs. Entity-Aware comparison.

*Features above describe the intended system design; implementation and evaluation are ongoing.*

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | Next.js, TypeScript |
| Styling | Tailwind CSS |
| Backend | Python, FastAPI |
| Database | Neon PostgreSQL |
| Database Driver | psycopg |
| Information Retrieval | scikit-learn |
| Text Processing | Sastrawi |
| Model Artifacts | Joblib |

## Dataset

The project uses a curated MotoGP news corpus containing **60 articles** from three Indonesian news publishers.

| Publisher | Articles |
|---|---:|
| Kompas | 20 |
| ANTARA | 20 |
| IDN Times | 20 |
| **Total** | **60** |

Each document contains metadata such as:
- Document ID
- Article title
- Publication date
- Publisher
- Topic
- Source URL
- Author
- Article content

The corpus is intended for academic experimentation and retrieval evaluation.

## System Architecture

The system is designed around two retrieval branches:

```text
                    User Query
                         |
                   Query Processing
                         |
              +----------+----------+
              |                     |
         Text Retrieval        Entity Retrieval
              |                     |
          TF-IDF +             Entity Dictionary
          Cosine Similarity    & Entity Index
              |                     |
              +----------+----------+
                         |
                   Score Fusion
                         |
                  Ranked Results
```

The baseline uses text similarity scores. The specialized system combines text relevance with entity relevance.

The initial score-fusion design is:

\[
S_{final} = \alpha S_{text} + \beta S_{entity}
\]

Where:
- `S_text`: Text similarity score.
- `S_entity`: Entity relevance score.
- `α` and `β`: Experimentally evaluated weighting parameters.

The weighting configuration is subject to experimentation and evaluation.

## Planned Repository Structure

```text
motogp-entity-search/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── public/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── services/
│   │   └── main.py
│   │
│   ├── artifacts/
│   └── requirements.txt
│
├── database/
│   └── schema.sql
│
├── docs/
│   └── evaluation/
│
├── .gitignore
└── README.md
```

## Getting Started

> Setup instructions will be updated as the application implementation progresses.

### Prerequisites

- Node.js
- Python
- PostgreSQL-compatible database
- Neon PostgreSQL account

### Environment Variables

Configuration examples will be provided when the application setup is finalized.

Do not commit credentials, API keys, or database connection strings to the repository.

## Evaluation Methodology

The project evaluates whether Entity-Aware Search improves retrieval effectiveness compared with the TF-IDF baseline.

Both retrieval methods will be evaluated using comparable queries and manually established relevance judgments.

Evaluation metrics:
- Precision@K
- Recall
- Mean Average Precision (MAP)

Queries will be categorized into:
- Queries containing recognized entities.
- Queries without recognized entities.

## Project Scope

This project focuses on:
- MotoGP news retrieval.
- Domain-specific entity recognition using a dictionary-based approach.
- Entity-aware document ranking.
- Comparative Information Retrieval evaluation.

It does not aim to develop or train a general-purpose Named Entity Recognition model.

## License

License information will be added later.
```
