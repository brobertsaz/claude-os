"""
PostgreSQL + pgvector database manager for Code-Forge.
Replaces ChromaDB with a more robust, ACID-compliant solution.
"""

import os
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from psycopg2.pool import SimpleConnectionPool
import numpy as np

from app.core.config import Config
from app.core.kb_types import KBType, KBMetadata


def generate_slug(name: str) -> str:
    """
    Generate a URL-friendly slug from a KB name.

    Examples:
        "Pistn Agent OS" -> "pistn-agent-os"
        "My Code Base!" -> "my-code-base"
        "Test_KB 123" -> "test-kb-123"
    """
    # Convert to lowercase
    slug = name.lower()
    # Replace spaces and underscores with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    # Remove any characters that aren't alphanumeric or hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


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
        tags: List[str] = None,
        embed_dim: int = 768
    ) -> Dict[str, Any]:
        """Create a new knowledge base with PGVectorStore table."""
        import json

        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Generate URL-friendly slug
                slug = generate_slug(name)

                # Sanitize name for table name
                table_name = f"data_{name.lower().replace(' ', '_').replace('-', '_')}"

                # Prepare metadata (tags go in metadata JSON, not separate column)
                metadata = {}
                if tags:
                    metadata["tags"] = tags

                # Insert KB metadata (no tags column in NEW schema)
                cur.execute(
                    """
                    INSERT INTO knowledge_bases (name, slug, kb_type, description, metadata, table_name, embed_dim)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, name, slug, kb_type, description, created_at, metadata, table_name, embed_dim
                    """,
                    (name, slug, kb_type.value, description, json.dumps(metadata), table_name, embed_dim)
                )
                result = cur.fetchone()

                # Create the PGVectorStore table using the helper function
                cur.execute("SELECT create_kb_table(%s, %s, %s)", (name, table_name, embed_dim))

            conn.commit()
            return dict(result)
        except psycopg2.IntegrityError as e:
            conn.rollback()
            if 'slug' in str(e):
                raise ValueError(f"A knowledge base with a similar name already exists (slug conflict: '{slug}')")
            raise ValueError(f"Knowledge base '{name}' already exists")
        finally:
            self.return_connection(conn)

    def delete_collection(self, name: str) -> bool:
        """Delete a knowledge base and its PGVectorStore table."""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get table name before deleting
                cur.execute("SELECT table_name FROM knowledge_bases WHERE name = %s", (name,))
                result = cur.fetchone()

                if not result:
                    return False

                table_name = result['table_name']

                # Drop the PGVectorStore table if it exists
                if table_name:
                    cur.execute("SELECT drop_kb_table(%s)", (table_name,))

                # Delete KB metadata
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
                    SELECT name, slug, kb_type, description, created_at, metadata
                    FROM knowledge_bases
                    ORDER BY created_at DESC
                    """
                )
                results = cur.fetchall()

            return [
                {
                    "name": row["name"],
                    "slug": row.get("slug") or generate_slug(row["name"]),  # Fallback for old KBs
                    "metadata": {
                        "kb_type": row["kb_type"],
                        "description": row["description"] or "",
                        "created_at": row["created_at"].isoformat() if row["created_at"] else "",
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
                    SELECT name, kb_type, description, created_at, metadata
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
        """Add documents to a knowledge base using PGVectorStore schema."""
        from llama_index.core.schema import TextNode
        from llama_index.vector_stores.postgres import PGVectorStore

        conn = self.get_connection()
        try:
            # Get KB metadata
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, table_name, embed_dim FROM knowledge_bases WHERE name = %s",
                    (kb_name,)
                )
                result = cur.fetchone()
                if not result:
                    raise ValueError(f"Knowledge base '{kb_name}' not found")

                kb_id = result['id']
                table_name = result['table_name']
                embed_dim = result['embed_dim']

                if not table_name:
                    raise ValueError(f"Knowledge base '{kb_name}' has not been migrated to PGVectorStore schema")
        finally:
            self.return_connection(conn)

        # Create PGVectorStore instance
        pg_user = os.getenv("POSTGRES_USER", os.getenv("USER", "postgres"))
        pg_password = os.getenv("POSTGRES_PASSWORD", "")
        pg_host = os.getenv("POSTGRES_HOST", "localhost")
        pg_port = os.getenv("POSTGRES_PORT", "5432")
        pg_db = os.getenv("POSTGRES_DB", "codeforge")

        # PGVectorStore automatically adds 'data_' prefix to table names
        # Our schema already has 'data_' prefix, so we need to strip it
        pgvector_table_name = table_name.removeprefix('data_')

        # Use individual parameters to avoid async connection string issues
        vector_store = PGVectorStore.from_params(
            host=pg_host,
            port=pg_port,
            database=pg_db,
            user=pg_user,
            password=pg_password,
            table_name=pgvector_table_name,  # PGVectorStore will add 'data_' prefix
            embed_dim=embed_dim,
            perform_setup=False  # Don't recreate tables
        )

        # Create TextNode objects for llama_index
        nodes = []
        for doc, emb, meta, doc_id in zip(documents, embeddings, metadatas, ids):
            # Add kb_id to metadata
            meta_with_kb = {**meta, "kb_id": str(kb_id)}

            node = TextNode(
                text=doc,
                id_=doc_id,
                embedding=emb,
                metadata=meta_with_kb
            )
            nodes.append(node)

        # Add nodes to vector store
        vector_store.add(nodes)

    def get_documents_by_metadata(
        self,
        kb_name: str,
        where: Dict[str, Any],
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get documents filtered by metadata from NEW PGVectorStore schema."""
        conn = self.get_connection()
        try:
            # Get table name for this KB
            with conn.cursor() as cur:
                cur.execute("SELECT table_name FROM knowledge_bases WHERE name = %s", (kb_name,))
                result = cur.fetchone()
                if not result or not result[0]:
                    return []
                table_name = result[0]

            # Build WHERE clause for JSONB metadata_ column
            where_conditions = []
            params = []
            for key, value in where.items():
                where_conditions.append(f"metadata_->>%s = %s")
                params.extend([key, str(value)])

            where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE"

            # Query NEW schema: data_{kb_name} table with columns: id, text, metadata_, node_id, embedding
            query = f"""
                SELECT node_id, text, metadata_
                FROM {table_name}
                WHERE {where_clause}
            """
            if limit:
                query += f" LIMIT {limit}"

            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                results = cur.fetchall()
                # Return with 'metadata' key (not 'metadata_') for compatibility
                return [
                    {
                        "node_id": row["node_id"],
                        "text": row["text"],
                        "metadata": row["metadata_"]
                    }
                    for row in results
                ]
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
        """Check if a knowledge base exists by name."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT EXISTS(SELECT 1 FROM knowledge_bases WHERE name = %s)", (kb_name,))
                return cur.fetchone()[0]
        finally:
            self.return_connection(conn)

    def get_kb_by_slug(self, slug: str) -> Optional[str]:
        """Get KB name by slug. Returns None if not found."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM knowledge_bases WHERE slug = %s", (slug,))
                result = cur.fetchone()
                return result[0] if result else None
        finally:
            self.return_connection(conn)

    def slug_exists(self, slug: str) -> bool:
        """Check if a slug exists."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT EXISTS(SELECT 1 FROM knowledge_bases WHERE slug = %s)", (slug,))
                return cur.fetchone()[0]
        finally:
            self.return_connection(conn)

    def get_collection_count(self, kb_name: str) -> int:
        """Get document count for a knowledge base."""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get table name
                cur.execute("SELECT table_name FROM knowledge_bases WHERE name = %s", (kb_name,))
                result = cur.fetchone()

                if not result or not result['table_name']:
                    return 0

                table_name = result['table_name']

                # Count documents in PGVectorStore table
                cur.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                count_result = cur.fetchone()
                return count_result['count'] if count_result else 0
        finally:
            self.return_connection(conn)

    def close(self):
        """Close all connections in the pool."""
        if self.pool:
            self.pool.closeall()
    def query_similar(
        self,
        kb_id: int,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query for similar documents using vector similarity.
        Works with NEW PGVectorStore schema (data_{kb_name} tables).

        Args:
            kb_id: Knowledge base ID
            query_embedding: Query embedding vector
            top_k: Number of results to return

        Returns:
            List of similar documents with text, metadata, and similarity score
        """
        import logging
        logger = logging.getLogger(__name__)

        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Get table name for this KB
                cur.execute("SELECT table_name FROM knowledge_bases WHERE id = %s", (kb_id,))
                result = cur.fetchone()
                if not result or not result['table_name']:
                    logger.warning(f"No table found for kb_id={kb_id}")
                    return []

                table_name = result['table_name']

                # Convert embedding list to PostgreSQL vector format string
                # Format: '[0.123, 0.456, ...]'
                embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
                logger.info(f"Query embedding dimension: {len(query_embedding)}")
                logger.info(f"Querying kb_id={kb_id}, table={table_name}, top_k={top_k}")

                # Query for similar documents using cosine similarity
                # NEW schema uses 'text' and 'metadata_' columns
                query = f"""
                    SELECT
                        text,
                        metadata_ as metadata,
                        node_id,
                        1 - (embedding <=> %s::vector) as similarity
                    FROM {table_name}
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """
                logger.info(f"Executing query with params: top_k={top_k}")

                # Pass the embedding as a string with ::vector cast
                cur.execute(query, (embedding_str, embedding_str, top_k))

                results = cur.fetchall()
                logger.info(f"PostgreSQL returned {len(results)} results")
                if results:
                    logger.info(f"First result similarity: {results[0].get('similarity')}")
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error in query_similar: {e}")
            raise
        finally:
            self.return_connection(conn)


# Singleton instance
_pg_manager = None


def get_pg_manager() -> PostgresManager:
    """Get or create the PostgresManager singleton."""
    global _pg_manager
    if _pg_manager is None:
        _pg_manager = PostgresManager()
    return _pg_manager

