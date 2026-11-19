from __future__ import annotations
from typing import Any, Dict, List, Optional, Sequence, Tuple
import psycopg

# ---------- documents ----------
def fetch_documents_for_index(conn: psycopg.Connection) -> List[Dict[str, Any]]:
    return conn.execute(
        "SELECT doc_id, title, published_at, media, topic, url, author, content, processed_text "
        "FROM documents ORDER BY doc_id"
    ).fetchall()

def list_documents(
    conn: psycopg.Connection, limit: int, offset: int, media: Optional[str]
) -> Tuple[List[Dict[str, Any]], int]:
    where, params = "", []
    if media:
        where, params = "WHERE media ILIKE %s", [media]
    total = conn.execute(f"SELECT count(*) AS n FROM documents {where}", params).fetchone()["n"]
    rows = conn.execute(
        f"SELECT doc_id, title, published_at, media, topic, url, author "
        f"FROM documents {where} ORDER BY published_at DESC NULLS LAST, doc_id "
        f"LIMIT %s OFFSET %s",
        [*params, limit, offset],
    ).fetchall()
    return rows, total

def get_document(conn: psycopg.Connection, doc_id: str) -> Optional[Dict[str, Any]]:
    return conn.execute(
        "SELECT doc_id, title, published_at, media, topic, url, author, content "
        "FROM documents WHERE doc_id = %s",
        [doc_id],
    ).fetchone()

def get_document_entities(conn: psycopg.Connection, doc_id: str) -> List[Dict[str, Any]]:
    return conn.execute(
        "SELECT e.entity_id, e.canonical_name AS name, e.category, de.mention_count "
        "FROM document_entities de JOIN entities e USING (entity_id) "
        "WHERE de.doc_id = %s ORDER BY de.mention_count DESC, e.canonical_name",
        [doc_id],
    ).fetchall()

def upsert_documents(conn: psycopg.Connection, docs: Sequence[Dict[str, Any]]) -> int:
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO documents (doc_id, title, published_at, media, topic, url, author, content, processed_text) "
            "VALUES (%(doc_id)s, %(title)s, %(published_at)s, %(media)s, %(topic)s, %(url)s, %(author)s, "
            "        %(content)s, %(processed_text)s) "
            "ON CONFLICT (doc_id) DO UPDATE SET title = EXCLUDED.title, published_at = EXCLUDED.published_at, "
            "media = EXCLUDED.media, topic = EXCLUDED.topic, url = EXCLUDED.url, author = EXCLUDED.author, "
            "content = EXCLUDED.content, "
            "processed_text = COALESCE(EXCLUDED.processed_text, documents.processed_text), "
            "updated_at = now()",
            list(docs),
        )
    return len(docs)

# ---------- entities ----------
def fetch_entities_and_aliases(
    conn: psycopg.Connection, statuses: Sequence[str] = ()
) -> Tuple[List[Dict], List[Dict]]:
    """Entity dictionary for the indexer; optionally restricted to given verification_status values."""
    if statuses:
        entities = conn.execute(
            "SELECT entity_id, canonical_name, category FROM entities "
            "WHERE verification_status = ANY(%s) ORDER BY entity_id",
            [list(statuses)],
        ).fetchall()
    else:
        entities = conn.execute(
            "SELECT entity_id, canonical_name, category FROM entities ORDER BY entity_id"
        ).fetchall()
    aliases = conn.execute("SELECT entity_id, alias, normalized_alias FROM entity_aliases").fetchall()
    return entities, aliases

def list_entities(conn: psycopg.Connection, category: Optional[str]) -> List[Dict[str, Any]]:
    where, params = "", []
    if category:
        where, params = "WHERE e.category = %s", [category]
    return conn.execute(
        "SELECT e.entity_id, e.canonical_name AS name, e.category, e.description, e.verification_status, "
        "       COALESCE(array_agg(DISTINCT a.alias) FILTER (WHERE a.alias IS NOT NULL), ARRAY[]::text[]) AS aliases "
        f"FROM entities e LEFT JOIN entity_aliases a USING (entity_id) {where} "
        "GROUP BY e.entity_id ORDER BY e.category, e.canonical_name",
        params,
    ).fetchall()

def upsert_entity(
    conn: psycopg.Connection, entity_id: str, name: str, category: str,
    aliases: Sequence[str], normalize, verification_status: str = "unverified",
) -> None:
    conn.execute(
        "INSERT INTO entities (entity_id, canonical_name, category, verification_status) "
        "VALUES (%s, %s, %s, %s) "
        "ON CONFLICT (entity_id) DO UPDATE SET canonical_name = EXCLUDED.canonical_name, category = EXCLUDED.category",
        [entity_id, name, category, verification_status],
    )
    for alias in dict.fromkeys(aliases):
        conn.execute(
            "INSERT INTO entity_aliases (entity_id, alias, normalized_alias) "
            "SELECT %s, %s, %s WHERE NOT EXISTS "
            "(SELECT 1 FROM entity_aliases WHERE entity_id = %s AND normalized_alias = %s)",
            [entity_id, alias, normalize(alias), entity_id, normalize(alias)],
        )

def replace_document_entities(conn: psycopg.Connection, rows: Sequence[tuple]) -> None:
    conn.execute("DELETE FROM document_entities")
    if rows:
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO document_entities (doc_id, entity_id, mention_count) VALUES (%s, %s, %s)",
                list(rows),
            )

# ---------- evaluation ----------
_EVAL_SELECT = (
    "SELECT q.query_id, q.query_text, "
    "       COALESCE(array_agg(j.doc_id ORDER BY j.doc_id) FILTER (WHERE j.relevance > 0), ARRAY[]::text[]) AS relevant_doc_ids "
    "FROM evaluation_queries q LEFT JOIN relevance_judgments j USING (query_id) "
)

def list_eval_queries(conn: psycopg.Connection) -> List[Dict[str, Any]]:
    return conn.execute(_EVAL_SELECT + "GROUP BY q.query_id ORDER BY q.query_id").fetchall()


def create_eval_query(conn: psycopg.Connection, query_text: str, relevant_doc_ids: Sequence[str]) -> Dict[str, Any]:
    qid = conn.execute(
        "INSERT INTO evaluation_queries (query_text) VALUES (%s) RETURNING query_id", [query_text]
    ).fetchone()["query_id"]
    ids = list(dict.fromkeys(relevant_doc_ids))
    if ids:
        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO relevance_judgments (query_id, doc_id, relevance) VALUES (%s, %s, 1)",
                [(qid, d) for d in ids],
            )
    return {"query_id": qid, "query_text": query_text, "relevant_doc_ids": ids}

def delete_eval_query(conn: psycopg.Connection, query_id: int) -> bool:
    return conn.execute("DELETE FROM evaluation_queries WHERE query_id = %s", [query_id]).rowcount > 0
