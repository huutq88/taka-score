"""Database Access Layer cho taka-score.

Kết nối với Neo4j để lấy metadata của chương truyện và Postgres để lấy văn bản thô.
Sử dụng chung cấu hình và mô hình giống như taka-voice.
"""
from __future__ import annotations

import os
import sys
from typing import Any

from neo4j import GraphDatabase

_driver_instance = None
_pg_pool = None


# ──────────────────────────────────────────────────────────────
# Neo4j Graph DB Connection
# ──────────────────────────────────────────────────────────────

def _get_neo4j_driver():
    global _driver_instance
    if _driver_instance is None:
        uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        user = os.environ.get("NEO4J_USER", "neo4j")
        password = os.environ.get("NEO4J_PASSWORD", "")
        _driver_instance = GraphDatabase.driver(uri, auth=(user, password))
        
        # Pool preservation patch
        _original_close = _driver_instance.close
        _driver_instance.close = lambda: None
        _driver_instance._real_close = _original_close
        
    return _driver_instance


def _get_database() -> str:
    return os.environ.get("NEO4J_DATABASE", "neo4j")


def _read_single(cypher: str, **params: Any) -> dict[str, Any] | None:
    driver = _get_neo4j_driver()
    try:
        with driver.session(database=_get_database()) as session:
            record = session.run(cypher, **params).single()
            return record.data() if record else None
    finally:
        driver._real_close()


def fetch_chapter_metadata(chapter_id: str) -> dict[str, Any] | None:
    """Lấy document_id và title của chapter từ Neo4j."""
    query = """
    MATCH (s:Story)-[:HAS_CHAPTER]->(c:Chapter {id: $chapter_id})
    RETURN c.id AS id,
           c.document_id AS document_id,
           c.idx AS idx,
           c.title AS title,
           s.id AS story_id,
           s.title AS story_title
    """
    return _read_single(query, chapter_id=chapter_id)


# ──────────────────────────────────────────────────────────────
# Postgres Document Fetcher
# ──────────────────────────────────────────────────────────────

def fetch_postgres_document(document_id: str) -> str | None:
    """Tải nội dung văn bản thô của chương từ Postgres DB."""
    global _pg_pool
    postgres_uri = os.environ.get("POSTGRES_URI")
    if not postgres_uri:
        print("POSTGRES_URI not set, skipping document fetch.", file=sys.stderr)
        return None
    try:
        import psycopg2
        from psycopg2 import pool
        
        if _pg_pool is None:
            _pg_pool = pool.ThreadedConnectionPool(1, 5, postgres_uri)
            
        conn = _pg_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT d.content FROM agent_documents ad "
                    "JOIN documents d ON ad.document_id = d.id "
                    "WHERE ad.id::text = %s",
                    (document_id,),
                )
                row = cur.fetchone()
                if row and row[0]:
                    return row[0]
        finally:
            _pg_pool.putconn(conn)
    except Exception as e:
        print(f"Error fetching document {document_id} from Postgres DB: {e}", file=sys.stderr)
    return None
