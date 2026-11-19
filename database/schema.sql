-- MotoGP Entity-Aware Search Engine: Neon PostgreSQL schema.
-- Matches the existing ER diagram. Every statement is IF NOT EXISTS, so tables
-- that already exist in Neon are left untouched; only missing ones are created.

CREATE TABLE IF NOT EXISTS documents (
    doc_id          TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    published_at    DATE,
    media           TEXT,
    topic           TEXT,
    url             TEXT,
    author          TEXT,
    content         TEXT NOT NULL,
    processed_text  TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS entities (
    entity_id            TEXT PRIMARY KEY,
    canonical_name       TEXT NOT NULL,
    category             TEXT,
    description          TEXT,
    source_url           TEXT,
    verification_status  TEXT,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS entity_aliases (
    alias_id          SERIAL PRIMARY KEY,
    entity_id         TEXT NOT NULL REFERENCES entities (entity_id) ON DELETE CASCADE,
    alias             TEXT NOT NULL,
    normalized_alias  TEXT
);
CREATE INDEX IF NOT EXISTS idx_entity_aliases_entity ON entity_aliases (entity_id);

CREATE TABLE IF NOT EXISTS document_entities (
    doc_id         TEXT    NOT NULL REFERENCES documents (doc_id) ON DELETE CASCADE,
    entity_id      TEXT    NOT NULL REFERENCES entities (entity_id) ON DELETE CASCADE,
    mention_count  INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (doc_id, entity_id)
);

-- New tables (not in the ER diagram): evaluation queries + manual relevance judgments
CREATE TABLE IF NOT EXISTS evaluation_queries (
    query_id    SERIAL PRIMARY KEY,
    query_text  TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS relevance_judgments (
    query_id   INTEGER  NOT NULL REFERENCES evaluation_queries (query_id) ON DELETE CASCADE,
    doc_id     TEXT     NOT NULL REFERENCES documents (doc_id) ON DELETE CASCADE,
    relevance  SMALLINT NOT NULL DEFAULT 1 CHECK (relevance >= 0),
    PRIMARY KEY (query_id, doc_id)
);
