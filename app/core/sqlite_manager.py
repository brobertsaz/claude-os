"""
SQLite database manager for Claude OS with vector embedding support.
Uses single-file SQLite + sqlite-vec for vector similarity.
"""

import os
import json
import re
import sqlite3
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
from pathlib import Path
import numpy as np

from app.core.config import Config
from app.core.kb_types import KBType, KBMetadata


def generate_slug(name: str) -> str:
    """
    Generate a URL-friendly slug from a KB name.

    Examples:
        "Project Agent OS" -> "project-agent-os"
        "My Code Base!" -> "my-code-base"
        "Test_KB 123" -> "test-kb-123"
    """
    slug = name.lower()
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug


class SQLiteManager:
    """Manages SQLite database operations with vector embeddings using sqlite-vec."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize SQLite database manager."""
        if db_path is None:
            db_path = os.getenv("SQLITE_DB_PATH", Config.get_db_path())

        self.db_path = db_path

        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize schema
        self._init_schema()

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection with row factory for dict-like access."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_schema(self):
        """Initialize database schema from schema.sqlite."""
        schema_path = Path(__file__).parent.parent / "db" / "schema.sqlite"

        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        conn = self.get_connection()
        try:
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            conn.executescript(schema_sql)
            conn.commit()
        finally:
            conn.close()

    # Knowledge Base Operations

    def create_collection(
        self,
        name: str,
        kb_type: KBType = KBType.GENERIC,
        description: str = "",
        tags: List[str] = None,
        embed_dim: int = 768
    ) -> Dict[str, Any]:
        """Create a new knowledge base."""
        conn = self.get_connection()
        try:
            slug = generate_slug(name)

            metadata = {}
            if tags:
                metadata["tags"] = tags

            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO knowledge_bases (name, slug, kb_type, description, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, slug, kb_type.value, description, json.dumps(metadata))
            )
            conn.commit()
            kb_id = cursor.lastrowid

            return {
                "id": kb_id,
                "name": name,
                "slug": slug,
                "kb_type": kb_type.value,
                "description": description,
                "metadata": metadata,
                "created_at": datetime.now().isoformat()
            }
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if 'slug' in str(e):
                raise ValueError(f"A knowledge base with a similar name already exists (slug conflict: '{slug}')")
            raise ValueError(f"Knowledge base '{name}' already exists")
        finally:
            conn.close()

    def delete_collection(self, name: str) -> bool:
        """Delete a knowledge base and its documents."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM knowledge_bases WHERE name = ?", (name,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def list_collections(self) -> List[Dict[str, Any]]:
        """List all knowledge bases with metadata."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, slug, kb_type, description, created_at, metadata
                FROM knowledge_bases
                ORDER BY created_at DESC
                """
            )

            results = []
            for row in cursor.fetchall():
                metadata = json.loads(row['metadata']) if row['metadata'] else {}
                results.append({
                    "id": row['id'],
                    "name": row['name'],
                    "slug": row['slug'],
                    "metadata": {
                        "kb_type": row['kb_type'],
                        "description": row['description'] or "",
                        "created_at": row['created_at'],
                        **metadata
                    }
                })
            return results
        finally:
            conn.close()

    def get_collection_metadata(self, name: str) -> Dict[str, Any]:
        """Get metadata for a specific knowledge base."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT kb_type, description, created_at, metadata
                FROM knowledge_bases
                WHERE name = ?
                """,
                (name,)
            )
            row = cursor.fetchone()

            if not row:
                raise ValueError(f"Knowledge base '{name}' not found")

            metadata = json.loads(row['metadata']) if row['metadata'] else {}
            return {
                "kb_type": row['kb_type'],
                "description": row['description'] or "",
                "created_at": row['created_at'],
                **metadata
            }
        finally:
            conn.close()

    def get_collection_by_id(self, kb_id: int) -> Optional[Dict[str, Any]]:
        """Get knowledge base by ID."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, slug, kb_type, description, created_at, metadata
                FROM knowledge_bases
                WHERE id = ?
                """,
                (kb_id,)
            )
            row = cursor.fetchone()

            if not row:
                return None

            metadata = json.loads(row['metadata']) if row['metadata'] else {}
            return {
                "id": row['id'],
                "name": row['name'],
                "slug": row['slug'],
                "kb_type": row['kb_type'],
                "description": row['description'] or "",
                "created_at": row['created_at'],
                "metadata": metadata
            }
        finally:
            conn.close()

    def list_collections_by_type(self, kb_type: KBType) -> List[Dict[str, Any]]:
        """List knowledge bases filtered by type."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, kb_type, description, created_at, metadata
                FROM knowledge_bases
                WHERE kb_type = ?
                ORDER BY created_at DESC
                """,
                (kb_type.value,)
            )

            results = []
            for row in cursor.fetchall():
                metadata = json.loads(row['metadata']) if row['metadata'] else {}
                results.append({
                    "id": row['id'],
                    "name": row['name'],
                    "metadata": {
                        "kb_type": row['kb_type'],
                        "description": row['description'] or "",
                        "created_at": row['created_at'],
                        **metadata
                    }
                })
            return results
        finally:
            conn.close()

    # Document Operations

    def add_documents(
        self,
        kb_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """Add documents to a knowledge base with embeddings."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # Get KB ID
            cursor.execute("SELECT id FROM knowledge_bases WHERE name = ?", (kb_name,))
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Knowledge base '{kb_name}' not found")

            kb_id = result['id']

            # Add documents with embeddings
            for doc, emb, meta, doc_id in zip(documents, embeddings, metadatas, ids):
                meta_with_kb = {**meta, "kb_id": str(kb_id)}

                # Convert embedding to bytes for sqlite-vec
                emb_bytes = np.array(emb, dtype=np.float32).tobytes()

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO documents (kb_id, doc_id, content, embedding, metadata)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (kb_id, doc_id, doc, emb_bytes, json.dumps(meta_with_kb))
                )

            conn.commit()
        finally:
            conn.close()

    def get_file_hash_in_kb(self, kb_name: str, source_path: str) -> Optional[str]:
        """Get the stored file hash for a source_path in a KB (for change detection)."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM knowledge_bases WHERE name = ?", (kb_name,))
            result = cursor.fetchone()
            if not result:
                return None
            kb_id = result['id']
            cursor.execute(
                """
                SELECT json_extract(metadata, '$.file_hash') AS file_hash
                FROM documents
                WHERE kb_id = ? AND json_extract(metadata, '$.source_path') = ?
                LIMIT 1
                """,
                (kb_id, source_path)
            )
            row = cursor.fetchone()
            return row['file_hash'] if row and row['file_hash'] else None
        finally:
            conn.close()

    def delete_docs_not_in_paths(self, kb_name: str, source_paths: Set[str]) -> int:
        """Delete all docs whose source_path is not in source_paths (stale cleanup).

        Returns the number of deleted documents.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM knowledge_bases WHERE name = ?", (kb_name,))
            result = cursor.fetchone()
            if not result:
                return 0
            kb_id = result['id']
            paths_json = json.dumps(list(source_paths))
            cursor.execute(
                """
                DELETE FROM documents
                WHERE kb_id = ?
                  AND json_extract(metadata, '$.source_path') IS NOT NULL
                  AND json_extract(metadata, '$.source_path') NOT IN (
                      SELECT value FROM json_each(?)
                  )
                """,
                (kb_id, paths_json)
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def clear_documents(self, kb_name: str) -> int:
        """Delete all documents in a KB while keeping the KB record itself.

        Returns the number of deleted documents.
        """
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM knowledge_bases WHERE name = ?", (kb_name,))
            result = cursor.fetchone()
            if not result:
                return 0
            kb_id = result['id']
            cursor.execute("DELETE FROM documents WHERE kb_id = ?", (kb_id,))
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def get_documents_by_metadata(
        self,
        kb_name: str,
        where: Dict[str, Any],
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get documents filtered by metadata."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # Get KB ID
            cursor.execute("SELECT id FROM knowledge_bases WHERE name = ?", (kb_name,))
            result = cursor.fetchone()
            if not result:
                return []

            kb_id = result['id']

            # Build WHERE clause for JSON metadata
            where_conditions = ["kb_id = ?"]
            params = [kb_id]

            for key, value in where.items():
                where_conditions.append("json_extract(metadata, ?) = ?")
                params.extend([f"$.{key}", str(value)])

            where_clause = " AND ".join(where_conditions)

            query = f"""
                SELECT doc_id, content, metadata
                FROM documents
                WHERE {where_clause}
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, params)

            results = []
            for row in cursor.fetchall():
                metadata = json.loads(row['metadata']) if row['metadata'] else {}
                results.append({
                    "doc_id": row['doc_id'],
                    "text": row['content'],
                    "metadata": metadata
                })

            return results
        finally:
            conn.close()

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
            cursor = conn.cursor()

            # Get KB ID
            cursor.execute("SELECT id FROM knowledge_bases WHERE name = ?", (kb_name,))
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Knowledge base '{kb_name}' not found")

            kb_id = result['id']

            # Get all embeddings and compute cosine similarity in Python
            cursor.execute(
                """
                SELECT doc_id, content, embedding, metadata
                FROM documents
                WHERE kb_id = ?
                """,
                (kb_id,)
            )

            rows = cursor.fetchall()

            if not rows:
                return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

            # Convert embeddings and compute similarities
            query_vec = np.array(query_embedding, dtype=np.float32)
            similarities = []

            for row in rows:
                if row['embedding'] is None:
                    continue

                # Convert bytes back to array
                emb = np.frombuffer(row['embedding'], dtype=np.float32)

                # Cosine similarity
                dot_product = np.dot(query_vec, emb)
                norm_query = np.linalg.norm(query_vec)
                norm_emb = np.linalg.norm(emb)

                if norm_query > 0 and norm_emb > 0:
                    similarity = dot_product / (norm_query * norm_emb)
                else:
                    similarity = 0

                similarities.append((row['doc_id'], row['content'], row['metadata'], similarity))

            # Sort by similarity (descending) and take top n
            similarities.sort(key=lambda x: x[3], reverse=True)
            top_results = similarities[:n_results]

            # Format response like ChromaDB
            ids = [r[0] for r in top_results]
            documents = [r[1] for r in top_results]
            metadatas = [json.loads(r[2]) if r[2] else {} for r in top_results]
            distances = [1 - r[3] for r in top_results]  # Convert similarity to distance

            return {
                "ids": [ids],
                "documents": [documents],
                "metadatas": [metadatas],
                "distances": [distances]
            }
        finally:
            conn.close()

    def query_documents_multi_kb(
        self,
        kb_names: List[str],
        query_embedding: List[float],
        n_results: int = 10
    ) -> Dict[str, Any]:
        """Query documents across multiple knowledge bases, merge by score, deduplicate."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            query_vec = np.array(query_embedding, dtype=np.float32)
            all_results: List[Tuple[str, str, str, float, str]] = []  # (doc_id, content, metadata, similarity, kb_name)

            for kb_name in kb_names:
                cursor.execute("SELECT id FROM knowledge_bases WHERE name = ?", (kb_name,))
                row = cursor.fetchone()
                if not row:
                    continue
                kb_id = row['id']

                cursor.execute(
                    "SELECT doc_id, content, embedding, metadata FROM documents WHERE kb_id = ?",
                    (kb_id,)
                )
                for doc_row in cursor.fetchall():
                    if doc_row['embedding'] is None:
                        continue
                    emb = np.frombuffer(doc_row['embedding'], dtype=np.float32)
                    dot_product = np.dot(query_vec, emb)
                    norm_query = np.linalg.norm(query_vec)
                    norm_emb = np.linalg.norm(emb)
                    if norm_query > 0 and norm_emb > 0:
                        similarity = float(dot_product / (norm_query * norm_emb))
                    else:
                        similarity = 0.0
                    all_results.append((doc_row['doc_id'], doc_row['content'], doc_row['metadata'], similarity, kb_name))

            # Sort by similarity descending
            all_results.sort(key=lambda x: x[3], reverse=True)

            # Deduplicate by content prefix (first 200 chars)
            seen_prefixes: set = set()
            deduped: List[Tuple[str, str, str, float, str]] = []
            for r in all_results:
                prefix = (r[1] or "")[:200]
                if prefix in seen_prefixes:
                    continue
                seen_prefixes.add(prefix)
                deduped.append(r)

            top = deduped[:n_results]

            ids = [r[0] for r in top]
            documents = [r[1] for r in top]
            metadatas = []
            for r in top:
                meta = json.loads(r[2]) if r[2] else {}
                meta["_source_kb"] = r[4]
                metadatas.append(meta)
            scores = [r[3] for r in top]

            return {
                "ids": ids,
                "documents": documents,
                "metadatas": metadatas,
                "scores": scores
            }
        finally:
            conn.close()

    def collection_exists(self, kb_name: str) -> bool:
        """Check if a knowledge base exists."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT EXISTS(SELECT 1 FROM knowledge_bases WHERE name = ?)", (kb_name,))
            return cursor.fetchone()[0] > 0
        finally:
            conn.close()

    def get_kb_by_slug(self, slug: str) -> Optional[str]:
        """Get KB name by slug."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM knowledge_bases WHERE slug = ?", (slug,))
            result = cursor.fetchone()
            return result['name'] if result else None
        finally:
            conn.close()

    def slug_exists(self, slug: str) -> bool:
        """Check if a slug exists."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT EXISTS(SELECT 1 FROM knowledge_bases WHERE slug = ?)", (slug,))
            return cursor.fetchone()[0] > 0
        finally:
            conn.close()

    def get_collection_count(self, kb_name: str) -> int:
        """Get document count for a knowledge base."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # Get KB ID
            cursor.execute("SELECT id FROM knowledge_bases WHERE name = ?", (kb_name,))
            result = cursor.fetchone()
            if not result:
                return 0

            kb_id = result['id']

            # Count documents
            cursor.execute("SELECT COUNT(*) as count FROM documents WHERE kb_id = ?", (kb_id,))
            count_result = cursor.fetchone()
            return count_result['count'] if count_result else 0
        finally:
            conn.close()

    def query_similar(
        self,
        kb_id: int,
        query_embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Query for similar documents using vector similarity."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # Get all embeddings for this KB
            cursor.execute(
                """
                SELECT doc_id, content, metadata, embedding
                FROM documents
                WHERE kb_id = ?
                """,
                (kb_id,)
            )

            rows = cursor.fetchall()

            if not rows:
                return []

            # Compute similarities
            query_vec = np.array(query_embedding, dtype=np.float32)
            results = []

            for row in rows:
                if row['embedding'] is None:
                    continue

                emb = np.frombuffer(row['embedding'], dtype=np.float32)

                # Cosine similarity
                dot_product = np.dot(query_vec, emb)
                norm_query = np.linalg.norm(query_vec)
                norm_emb = np.linalg.norm(emb)

                if norm_query > 0 and norm_emb > 0:
                    similarity = dot_product / (norm_query * norm_emb)
                else:
                    similarity = 0

                metadata = json.loads(row['metadata']) if row['metadata'] else {}
                results.append({
                    "doc_id": row['doc_id'],
                    "text": row['content'],
                    "metadata": metadata,
                    "similarity": float(similarity)
                })

            # Sort by similarity and return top k
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:top_k]
        finally:
            conn.close()

    # Project Operations (new)

    def create_project(
        self,
        name: str,
        path: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new project."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            meta_json = json.dumps(metadata or {})

            cursor.execute(
                """
                INSERT INTO projects (name, path, description, metadata)
                VALUES (?, ?, ?, ?)
                """,
                (name, path, description, meta_json)
            )
            conn.commit()

            return {
                "id": cursor.lastrowid,
                "name": name,
                "path": path,
                "description": description,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat()
            }
        except sqlite3.IntegrityError as e:
            conn.rollback()
            raise ValueError(f"Project '{name}' or path '{path}' already exists")
        finally:
            conn.close()

    def get_project(self, project_id: int) -> Optional[Dict[str, Any]]:
        """Get project by ID."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, path, description, created_at, updated_at, metadata
                FROM projects
                WHERE id = ?
                """,
                (project_id,)
            )

            row = cursor.fetchone()
            if not row:
                return None

            return {
                "id": row['id'],
                "name": row['name'],
                "path": row['path'],
                "description": row['description'],
                "created_at": row['created_at'],
                "updated_at": row['updated_at'],
                "metadata": json.loads(row['metadata']) if row['metadata'] else {}
            }
        finally:
            conn.close()

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, path, description, created_at, updated_at, metadata
                FROM projects
                ORDER BY created_at DESC
                """
            )

            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row['id'],
                    "name": row['name'],
                    "path": row['path'],
                    "description": row['description'],
                    "created_at": row['created_at'],
                    "updated_at": row['updated_at'],
                    "metadata": json.loads(row['metadata']) if row['metadata'] else {}
                })
            return results
        finally:
            conn.close()

    def assign_kb_to_project(
        self,
        project_id: int,
        kb_id: int,
        mcp_type: str
    ) -> Dict[str, Any]:
        """Assign a knowledge base to a project for a specific MCP type."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO project_mcps (project_id, kb_id, mcp_type)
                VALUES (?, ?, ?)
                """,
                (project_id, kb_id, mcp_type)
            )
            conn.commit()

            return {
                "id": cursor.lastrowid,
                "project_id": project_id,
                "kb_id": kb_id,
                "mcp_type": mcp_type
            }
        except sqlite3.IntegrityError:
            conn.rollback()
            raise ValueError(f"Project {project_id} already has MCP type '{mcp_type}'")
        finally:
            conn.close()

    def get_project_kbs(self, project_id: int) -> Dict[str, int]:
        """Get KB IDs for all MCP types in a project."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT mcp_type, kb_id
                FROM project_mcps
                WHERE project_id = ?
                """,
                (project_id,)
            )

            return {row['mcp_type']: row['kb_id'] for row in cursor.fetchall()}
        finally:
            conn.close()

    def get_project_mcps_detailed(self, project_id: int) -> Dict[str, Dict[str, Any]]:
        """Get detailed MCP info (type, KB ID, KB name) for a project."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT pm.mcp_type, pm.kb_id, kb.name as kb_name
                FROM project_mcps pm
                JOIN knowledge_bases kb ON pm.kb_id = kb.id
                WHERE pm.project_id = ?
                """,
                (project_id,)
            )

            result = {}
            for row in cursor.fetchall():
                result[row['mcp_type']] = {
                    'kb_id': row['kb_id'],
                    'kb_name': row['kb_name']
                }
            return result
        finally:
            conn.close()

    def set_kb_folder(
        self,
        project_id: int,
        mcp_type: str,
        folder_path: str,
        auto_sync: bool = False
    ) -> Dict[str, Any]:
        """Set the folder path and auto-sync setting for a specific MCP type in a project."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            # Insert or replace
            cursor.execute(
                """
                INSERT INTO project_kb_folders (project_id, mcp_type, folder_path, auto_sync, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(project_id, mcp_type) DO UPDATE SET
                folder_path = excluded.folder_path,
                auto_sync = excluded.auto_sync,
                updated_at = CURRENT_TIMESTAMP
                """,
                (project_id, mcp_type, folder_path, 1 if auto_sync else 0)
            )
            conn.commit()

            return {
                "project_id": project_id,
                "mcp_type": mcp_type,
                "folder_path": folder_path,
                "auto_sync": auto_sync
            }
        finally:
            conn.close()

    def get_kb_folders(self, project_id: int) -> Dict[str, Dict[str, Any]]:
        """Get folder paths and auto-sync settings for all MCP types in a project."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT mcp_type, folder_path, auto_sync
                FROM project_kb_folders
                WHERE project_id = ?
                """,
                (project_id,)
            )

            return {
                row['mcp_type']: {
                    'folder_path': row['folder_path'],
                    'auto_sync': bool(row['auto_sync'])
                }
                for row in cursor.fetchall()
            }
        finally:
            conn.close()

    # Knowledge Lifecycle Operations

    def get_all_embeddings(self, kb_name: str, exclude_archived: bool = True) -> List[Dict[str, Any]]:
        """Get all documents with embeddings for pairwise similarity analysis."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM knowledge_bases WHERE name = ?", (kb_name,))
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Knowledge base '{kb_name}' not found")

            kb_id = result['id']
            cursor.execute(
                "SELECT doc_id, content, embedding, metadata FROM documents WHERE kb_id = ?",
                (kb_id,)
            )

            results = []
            for row in cursor.fetchall():
                metadata = json.loads(row['metadata']) if row['metadata'] else {}

                if exclude_archived and metadata.get("archived"):
                    continue

                embedding = None
                if row['embedding'] is not None:
                    embedding = np.frombuffer(row['embedding'], dtype=np.float32)

                results.append({
                    "doc_id": row['doc_id'],
                    "content": row['content'],
                    "embedding": embedding,
                    "metadata": metadata
                })

            return results
        finally:
            conn.close()

    def update_document_metadata(self, kb_name: str, doc_id: str, metadata_updates: Dict[str, Any]) -> bool:
        """Merge metadata updates into an existing document's metadata."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM knowledge_bases WHERE name = ?", (kb_name,))
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Knowledge base '{kb_name}' not found")

            kb_id = result['id']

            # Get current metadata
            cursor.execute(
                "SELECT metadata FROM documents WHERE kb_id = ? AND doc_id = ?",
                (kb_id, doc_id)
            )
            row = cursor.fetchone()
            if not row:
                return False

            current_metadata = json.loads(row['metadata']) if row['metadata'] else {}
            current_metadata.update(metadata_updates)

            cursor.execute(
                "UPDATE documents SET metadata = ? WHERE kb_id = ? AND doc_id = ?",
                (json.dumps(current_metadata), kb_id, doc_id)
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_documents_by_ids(self, kb_name: str, doc_ids: List[str]) -> int:
        """Bulk delete documents by doc_id list. Returns count deleted."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM knowledge_bases WHERE name = ?", (kb_name,))
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Knowledge base '{kb_name}' not found")

            kb_id = result['id']
            placeholders = ",".join(["?"] * len(doc_ids))
            cursor.execute(
                f"DELETE FROM documents WHERE kb_id = ? AND doc_id IN ({placeholders})",
                [kb_id] + list(doc_ids)
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def insert_lifecycle_log(
        self,
        kb_name: str,
        operation_type: str,
        status: str = "pending",
        input_doc_ids: List[str] = None,
        output_doc_ids: List[str] = None,
        details: Dict[str, Any] = None
    ) -> int:
        """Insert a lifecycle audit log entry. Returns log ID."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO lifecycle_log (kb_name, operation_type, status, input_doc_ids, output_doc_ids, details)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    kb_name,
                    operation_type,
                    status,
                    json.dumps(input_doc_ids or []),
                    json.dumps(output_doc_ids or []),
                    json.dumps(details or {})
                )
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def update_lifecycle_log(
        self,
        log_id: int,
        status: str,
        output_doc_ids: List[str] = None,
        details: Dict[str, Any] = None
    ) -> bool:
        """Update lifecycle log status and completion."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()

            updates = ["status = ?"]
            params = [status]

            if output_doc_ids is not None:
                updates.append("output_doc_ids = ?")
                params.append(json.dumps(output_doc_ids))

            if details is not None:
                updates.append("details = ?")
                params.append(json.dumps(details))

            if status in ("completed", "failed"):
                updates.append("completed_at = CURRENT_TIMESTAMP")

            params.append(log_id)
            cursor.execute(
                f"UPDATE lifecycle_log SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_lifecycle_logs(
        self,
        kb_name: str,
        operation_type: str = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Query lifecycle logs with optional filters."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            conditions = ["kb_name = ?"]
            params: list = [kb_name]

            if operation_type:
                conditions.append("operation_type = ?")
                params.append(operation_type)

            query = f"""
                SELECT id, kb_name, operation_type, status, input_doc_ids, output_doc_ids,
                       details, created_at, completed_at
                FROM lifecycle_log
                WHERE {' AND '.join(conditions)}
                ORDER BY created_at DESC
                LIMIT ?
            """
            params.append(limit)
            cursor.execute(query, params)

            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row['id'],
                    "kb_name": row['kb_name'],
                    "operation_type": row['operation_type'],
                    "status": row['status'],
                    "input_doc_ids": json.loads(row['input_doc_ids']) if row['input_doc_ids'] else [],
                    "output_doc_ids": json.loads(row['output_doc_ids']) if row['output_doc_ids'] else [],
                    "details": json.loads(row['details']) if row['details'] else {},
                    "created_at": row['created_at'],
                    "completed_at": row['completed_at']
                })
            return results
        finally:
            conn.close()

    def close(self):
        """Close database connections (no-op for SQLite)."""
        pass


# Singleton instance
_sqlite_manager = None


def get_sqlite_manager(db_path: Optional[str] = None) -> SQLiteManager:
    """Get or create the SQLiteManager singleton."""
    global _sqlite_manager
    if _sqlite_manager is None:
        _sqlite_manager = SQLiteManager(db_path)
    return _sqlite_manager
