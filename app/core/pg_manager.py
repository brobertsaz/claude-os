"""
PostgreSQL + pgvector database manager for Code-Forge.
Replaces ChromaDB with a more robust, ACID-compliant solution.
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import SimpleConnectionPool
import numpy as np

from app.core.config import Config
from app.core.kb_types import KBType, KBMetadata


class PostgresManager:
    """Manages PostgreSQL database operations with pgvector for embeddings."""

    def __init__(self):
        """Initialize connection pool."""
        # Build connection parameters
        conn_params = {
            "minconn": 1,
            "maxconn": 10,
            "host": os.getenv("POSTGRES_HOST", "localhost"),
            "port": int(os.getenv("POSTGRES_PORT", "5432")),
            "database": os.getenv("POSTGRES_DB", "codeforge"),
            "user": os.getenv("POSTGRES_USER", os.getenv("USER", "postgres")),
        }

        # Only add password if it's set (for local PostgreSQL with trust auth)
        password = os.getenv("POSTGRES_PASSWORD", "")
        if password:
            conn_params["password"] = password

        self.pool = SimpleConnectionPool(**conn_params)
        self._init_schema()

    def _init_schema(self):
        """Initialize database schema from schema.sql."""
        # Schema is managed externally - just verify connection
        # The schema.sql should be run manually on the local PostgreSQL
        pass

    def get_connection(self):
        """Get a connection from the pool."""
        return self.pool.getconn()

    def return_connection(self, conn):
        """Return a connection to the pool."""
        self.pool.putconn(conn)

    # Knowledge Base Operations

    def create_collection(
        self,
        name: str,
        kb_type: KBType = KBType.GENERIC,
        description: str = "",
        tags: List[str] = None
    ) -> Dict[str, Any]:
        """Create a new knowledge base."""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO knowledge_bases (name, kb_type, description, tags)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, name, kb_type, description, created_at, tags
                    """,
                    (name, kb_type.value, description, ",".join(tags) if tags else "")
                )
                result = cur.fetchone()
            conn.commit()
            return dict(result)
        except psycopg2.IntegrityError:
            conn.rollback()
            raise ValueError(f"Knowledge base '{name}' already exists")
        finally:
            self.return_connection(conn)

    def delete_collection(self, name: str) -> bool:
        """Delete a knowledge base and all its documents."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM knowledge_bases WHERE name = %s", (name,))
                deleted = cur.rowcount > 0
            conn.commit()
            return deleted
        finally:
            self.return_connection(conn)

    def list_collections(self) -> List[Dict[str, Any]]:
        """List all knowledge bases with metadata."""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT name, kb_type, description, created_at, tags, metadata
                    FROM knowledge_bases
                    ORDER BY created_at DESC
                    """
                )
                results = cur.fetchall()

            return [
                {
                    "name": row["name"],
                    "metadata": {
                        "kb_type": row["kb_type"],
                        "description": row["description"] or "",
                        "created_at": row["created_at"].isoformat() if row["created_at"] else "",
                        "tags": row["tags"] or "",
                        **row["metadata"]
                    }
                }
                for row in results
            ]
        finally:
            self.return_connection(conn)

    def get_collection_metadata(self, name: str) -> Dict[str, Any]:
        """Get metadata for a specific knowledge base."""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT kb_type, description, created_at, tags, metadata
                    FROM knowledge_bases
                    WHERE name = %s
                    """,
                    (name,)
                )
                row = cur.fetchone()

            if not row:
                raise ValueError(f"Knowledge base '{name}' not found")

            return {
                "kb_type": row["kb_type"],
                "description": row["description"] or "",
                "created_at": row["created_at"].isoformat() if row["created_at"] else "",
                "tags": row["tags"] or "",
                **row["metadata"]
            }
        finally:
            self.return_connection(conn)

    def list_collections_by_type(self, kb_type: KBType) -> List[Dict[str, Any]]:
        """List knowledge bases filtered by type."""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT name, kb_type, description, created_at, tags, metadata
                    FROM knowledge_bases
                    WHERE kb_type = %s
                    ORDER BY created_at DESC
                    """,
                    (kb_type.value,)
                )
                results = cur.fetchall()

            return [
                {
                    "name": row["name"],
                    "metadata": {
                        "kb_type": row["kb_type"],
                        "description": row["description"] or "",
                        "created_at": row["created_at"].isoformat() if row["created_at"] else "",
                        "tags": row["tags"] or "",
                        **row["metadata"]
                    }
                }
                for row in results
            ]
        finally:
            self.return_connection(conn)

    # Document Operations

    def add_documents(
        self,
        kb_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """Add documents to a knowledge base."""
        conn = self.get_connection()
        try:
            # Get KB ID
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM knowledge_bases WHERE name = %s", (kb_name,))
                result = cur.fetchone()
                if not result:
                    raise ValueError(f"Knowledge base '{kb_name}' not found")
                kb_id = result[0]

            # Insert documents
            with conn.cursor() as cur:
                for doc, emb, meta, doc_id in zip(documents, embeddings, metadatas, ids):
                    cur.execute(
                        """
                        INSERT INTO documents (kb_id, doc_id, content, embedding, metadata)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (kb_id, doc_id) DO UPDATE
                        SET content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata
                        """,
                        (kb_id, doc_id, doc, emb, Json(meta))
                    )
            conn.commit()
        finally:
            self.return_connection(conn)

    def get_documents_by_metadata(
        self,
        kb_name: str,
        where: Dict[str, Any],
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get documents filtered by metadata."""
        conn = self.get_connection()
        try:
            # Get KB ID
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM knowledge_bases WHERE name = %s", (kb_name,))
                result = cur.fetchone()
                if not result:
                    return []
                kb_id = result[0]

            # Build WHERE clause for JSONB metadata
            where_conditions = []
            params = [kb_id]
            for key, value in where.items():
                where_conditions.append(f"metadata->>%s = %s")
                params.extend([key, str(value)])

            where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE"

            query = f"""
                SELECT doc_id, content, metadata
                FROM documents
                WHERE kb_id = %s AND {where_clause}
            """
            if limit:
                query += f" LIMIT {limit}"

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                results = cur.fetchall()
                return [dict(row) for row in results]
        finally:
            self.return_connection(conn)

    def query_documents(
        self,
        kb_name: str,
        query_embedding: List[float],
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List]:
        """Query documents using vector similarity search."""
        conn = self.get_connection()
        try:
            # Get KB ID
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM knowledge_bases WHERE name = %s", (kb_name,))
                result = cur.fetchone()
                if not result:
                    raise ValueError(f"Knowledge base '{kb_name}' not found")
                kb_id = result[0]

            # Search documents
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT * FROM search_documents(%s, %s, %s, %s)
                    """,
                    (kb_id, query_embedding, n_results, Json(where) if where else None)
                )
                results = cur.fetchall()

            return {
                "ids": [[row["doc_id"] for row in results]],
                "documents": [[row["content"] for row in results]],
                "metadatas": [[row["metadata"] for row in results]],
                "distances": [[1 - row["similarity"] for row in results]]
            }
        finally:
            self.return_connection(conn)

    def collection_exists(self, kb_name: str) -> bool:
        """Check if a knowledge base exists."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT EXISTS(SELECT 1 FROM knowledge_bases WHERE name = %s)", (kb_name,))
                return cur.fetchone()[0]
        finally:
            self.return_connection(conn)

    def get_collection_count(self, kb_name: str) -> int:
        """Get document count for a knowledge base."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) FROM documents d
                    JOIN knowledge_bases kb ON d.kb_id = kb.id
                    WHERE kb.name = %s
                    """,
                    (kb_name,)
                )
                return cur.fetchone()[0]
        finally:
            self.return_connection(conn)

    def close(self):
        """Close all connections in the pool."""
        if self.pool:
            self.pool.closeall()


# Singleton instance
_pg_manager = None


def get_pg_manager() -> PostgresManager:
    """Get or create the PostgresManager singleton."""
    global _pg_manager
    if _pg_manager is None:
        _pg_manager = PostgresManager()
    return _pg_manager

