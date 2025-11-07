"""
Knowledge Exporter

Exports Claude OS knowledge bases to portable, standalone format.
Agnostic to consumer applications - produces standard SQLite database.
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import structlog

from app.core.sqlite_manager import get_sqlite_manager
from app.core.config import Config

logger = structlog.get_logger()


class KnowledgeExporter:
    """
    Exports knowledge bases to standalone SQLite format.

    Creates self-contained database with:
    - Documents (text content)
    - Embeddings (vector embeddings)
    - Metadata (sources, timestamps)
    - Manifest (export info)
    """

    EXPORT_FORMAT_VERSION = "1.0"

    def __init__(self):
        self.db_manager = get_sqlite_manager()
        self.config = Config()

    def export_project(
        self,
        project_name: str,
        kb_filter: Optional[str] = None,
        output_dir: str = "./exports",
        include_embeddings: bool = True,
        format: str = "sqlite"
    ) -> Dict[str, Any]:
        """
        Export a project's knowledge bases.

        Args:
            project_name: Name of the project to export
            kb_filter: Optional specific KB name to export (default: all KBs)
            output_dir: Directory for export files
            include_embeddings: Include vector embeddings (default: True)
            format: Export format (currently only 'sqlite' supported)

        Returns:
            Dictionary with export results:
            {
                "success": True,
                "export_file": "/path/to/export.db",
                "manifest_file": "/path/to/export.manifest.json",
                "stats": {...}
            }
        """
        try:
            logger.info("Starting knowledge export",
                       project_name=project_name,
                       kb_filter=kb_filter)

            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Generate filenames with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_filename = f"{project_name}_export_{timestamp}.db"
            manifest_filename = f"{project_name}_export_{timestamp}.manifest.json"

            export_file = output_path / export_filename
            manifest_file = output_path / manifest_filename

            # Get knowledge bases to export
            kbs_to_export = self._get_project_kbs(project_name, kb_filter)

            if not kbs_to_export:
                return {
                    "success": False,
                    "error": f"No knowledge bases found for project '{project_name}'"
                }

            logger.info(f"Found {len(kbs_to_export)} knowledge bases to export")

            # Create export database
            self._create_export_database(
                export_file=str(export_file),
                kbs=kbs_to_export,
                include_embeddings=include_embeddings
            )

            # Generate manifest
            manifest = self._create_manifest(
                project_name=project_name,
                kbs=kbs_to_export,
                export_file=str(export_file),
                include_embeddings=include_embeddings
            )

            # Write manifest file
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)

            logger.info("Export completed successfully",
                       export_file=str(export_file))

            return {
                "success": True,
                "export_file": str(export_file),
                "manifest_file": str(manifest_file),
                "stats": manifest["stats"]
            }

        except Exception as e:
            logger.error("Export failed", error=str(e), exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def _get_project_kbs(
        self,
        project_name: str,
        kb_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get knowledge bases for a project.

        Args:
            project_name: Project name
            kb_filter: Optional specific KB name

        Returns:
            List of KB metadata dictionaries
        """
        with self.db_manager.get_connection() as conn:
            if kb_filter:
                # Export specific KB
                query = """
                    SELECT id, name, kb_type, description, created_at
                    FROM knowledge_bases
                    WHERE name = ?
                """
                cursor = conn.execute(query, (kb_filter,))
            else:
                # Export all KBs matching project pattern
                query = """
                    SELECT id, name, kb_type, description, created_at
                    FROM knowledge_bases
                    WHERE name LIKE ?
                """
                cursor = conn.execute(query, (f"{project_name}-%",))

            kbs = []
            for row in cursor:
                kbs.append({
                    "id": row[0],
                    "name": row[1],
                    "kb_type": row[2],
                    "description": row[3],
                    "created_at": row[4]
                })

            return kbs

    def _create_export_database(
        self,
        export_file: str,
        kbs: List[Dict[str, Any]],
        include_embeddings: bool
    ):
        """
        Create the export SQLite database.

        Args:
            export_file: Path to export database file
            kbs: List of KBs to export
            include_embeddings: Whether to include embeddings
        """
        # Create new database
        export_conn = sqlite3.connect(export_file)
        export_conn.execute("PRAGMA journal_mode=WAL")

        try:
            # Create schema
            self._create_export_schema(export_conn, include_embeddings)

            # Export each KB
            for kb in kbs:
                self._export_kb(
                    export_conn=export_conn,
                    kb=kb,
                    include_embeddings=include_embeddings
                )

            export_conn.commit()

        finally:
            export_conn.close()

    def _create_export_schema(self, conn: sqlite3.Connection, include_embeddings: bool):
        """Create the export database schema."""

        # Knowledge bases table
        conn.execute("""
            CREATE TABLE knowledge_bases (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                kb_type TEXT,
                description TEXT,
                created_at TEXT,
                document_count INTEGER DEFAULT 0,
                embedding_model TEXT,
                embedding_dimensions INTEGER
            )
        """)

        # Documents table
        conn.execute("""
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY,
                kb_id INTEGER NOT NULL,
                kb_name TEXT NOT NULL,
                title TEXT,
                content TEXT NOT NULL,
                source_file TEXT,
                metadata TEXT,
                created_at TEXT,
                FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id)
            )
        """)

        conn.execute("""
            CREATE INDEX idx_documents_kb_id ON documents(kb_id)
        """)

        conn.execute("""
            CREATE INDEX idx_documents_kb_name ON documents(kb_name)
        """)

        if include_embeddings:
            # Embeddings table (using sqlite-vec extension if available)
            conn.execute("""
                CREATE TABLE embeddings (
                    id INTEGER PRIMARY KEY,
                    document_id INTEGER NOT NULL,
                    embedding BLOB NOT NULL,
                    model TEXT,
                    dimensions INTEGER,
                    FOREIGN KEY (document_id) REFERENCES documents(id)
                )
            """)

            conn.execute("""
                CREATE INDEX idx_embeddings_document_id ON embeddings(document_id)
            """)

        # Metadata table
        conn.execute("""
            CREATE TABLE export_metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Store format version
        conn.execute(
            "INSERT INTO export_metadata (key, value) VALUES (?, ?)",
            ("format_version", self.EXPORT_FORMAT_VERSION)
        )
        conn.execute(
            "INSERT INTO export_metadata (key, value) VALUES (?, ?)",
            ("exported_at", datetime.now().isoformat())
        )

        conn.commit()

    def _export_kb(
        self,
        export_conn: sqlite3.Connection,
        kb: Dict[str, Any],
        include_embeddings: bool
    ):
        """
        Export a single knowledge base.

        Args:
            export_conn: Export database connection
            kb: KB metadata
            include_embeddings: Whether to include embeddings
        """
        logger.info(f"Exporting KB: {kb['name']}")

        # Get documents from source database
        with self.db_manager.get_connection() as source_conn:
            # Get documents (using actual Claude OS schema)
            doc_query = """
                SELECT d.id, d.doc_id, d.content, d.metadata, d.created_at, d.embedding
                FROM documents d
                WHERE d.kb_id = ?
            """
            doc_cursor = source_conn.execute(doc_query, (kb['id'],))

            documents = []
            for row in doc_cursor:
                # Extract title from doc_id (e.g., "filename.md_0_hash" -> "filename.md")
                doc_id = row[1] or ""
                title = doc_id.split('_')[0] if '_' in doc_id else doc_id
                source_file = title

                documents.append({
                    "id": row[0],
                    "doc_id": row[1],
                    "title": title,
                    "content": row[2],
                    "source_file": source_file,
                    "metadata": row[3],
                    "created_at": row[4],
                    "embedding": row[5]
                })

            # Get embedding info if available
            embedding_info = self._get_embedding_info(source_conn, kb['id'])

        # Insert KB metadata
        export_conn.execute("""
            INSERT INTO knowledge_bases
            (id, name, kb_type, description, created_at, document_count, embedding_model, embedding_dimensions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            kb['id'],
            kb['name'],
            kb['kb_type'],
            kb['description'],
            kb['created_at'],
            len(documents),
            embedding_info.get('model'),
            embedding_info.get('dimensions')
        ))

        # Insert documents
        for doc in documents:
            cursor = export_conn.execute("""
                INSERT INTO documents (kb_id, kb_name, title, content, source_file, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                kb['id'],
                kb['name'],
                doc['title'],
                doc['content'],
                doc['source_file'],
                doc['metadata'],
                doc['created_at']
            ))

            new_doc_id = cursor.lastrowid

            # Insert embeddings if requested and available
            if include_embeddings and doc.get('embedding'):
                export_conn.execute("""
                    INSERT INTO embeddings (document_id, embedding, model, dimensions)
                    VALUES (?, ?, ?, ?)
                """, (
                    new_doc_id,
                    doc['embedding'],
                    embedding_info.get('model'),
                    embedding_info.get('dimensions')
                ))

        export_conn.commit()
        logger.info(f"Exported {len(documents)} documents from {kb['name']}")

    def _get_embedding_info(
        self,
        conn: sqlite3.Connection,
        kb_id: int
    ) -> Dict[str, Any]:
        """Get embedding model information for a KB."""
        # Try to get embedding info from a document's metadata
        try:
            cursor = conn.execute("""
                SELECT metadata, embedding FROM documents
                WHERE kb_id = ? AND embedding IS NOT NULL
                LIMIT 1
            """, (kb_id,))

            row = cursor.fetchone()
            if row:
                # Check if embedding exists and get its dimensions
                embedding_blob = row[1]
                if embedding_blob:
                    import numpy as np
                    embedding_array = np.frombuffer(embedding_blob, dtype=np.float32)
                    dimensions = len(embedding_array)

                    # Try to get model from metadata
                    model = "unknown"
                    if row[0]:
                        try:
                            metadata = json.loads(row[0])
                            model = metadata.get("embedding_model", "unknown")
                        except:
                            pass

                    return {"model": model, "dimensions": dimensions}
        except Exception as e:
            logger.warning(f"Could not get embedding info: {e}")

        return {"model": "unknown", "dimensions": 768}

    def _export_document_embedding(
        self,
        source_kb_name: str,
        source_doc_id: int,
        export_conn: sqlite3.Connection,
        export_doc_id: int,
        embedding_info: Dict[str, Any]
    ):
        """Export document embedding if available."""
        # This is a placeholder - actual implementation depends on
        # how Claude OS stores embeddings (could be in separate table,
        # in document metadata, or using sqlite-vec extension)

        # For now, we'll skip actual embedding export as it requires
        # understanding Claude OS's specific embedding storage format
        pass

    def _create_manifest(
        self,
        project_name: str,
        kbs: List[Dict[str, Any]],
        export_file: str,
        include_embeddings: bool
    ) -> Dict[str, Any]:
        """
        Create export manifest file.

        Args:
            project_name: Project name
            kbs: List of exported KBs
            export_file: Path to export file
            include_embeddings: Whether embeddings were included

        Returns:
            Manifest dictionary
        """
        file_size = os.path.getsize(export_file)

        # Count total documents
        total_docs = 0
        export_conn = sqlite3.connect(export_file)
        cursor = export_conn.execute("SELECT COUNT(*) FROM documents")
        total_docs = cursor.fetchone()[0]
        export_conn.close()

        manifest = {
            "format_version": self.EXPORT_FORMAT_VERSION,
            "exported_at": datetime.now().isoformat(),
            "project_name": project_name,
            "export_file": os.path.basename(export_file),
            "knowledge_bases": [
                {
                    "name": kb['name'],
                    "type": kb['kb_type'],
                    "description": kb.get('description', '')
                }
                for kb in kbs
            ],
            "stats": {
                "kb_count": len(kbs),
                "total_documents": total_docs,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "includes_embeddings": include_embeddings
            },
            "schema": {
                "tables": ["knowledge_bases", "documents", "embeddings" if include_embeddings else None, "export_metadata"],
                "format": "sqlite3",
                "version": "3.0"
            }
        }

        return manifest
