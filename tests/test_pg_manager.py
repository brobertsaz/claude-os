"""
Tests for PostgreSQL manager.
"""

import pytest


@pytest.mark.integration
class TestPostgresManager:
    """Test PostgreSQL manager functionality."""

    def test_create_collection(self, clean_db):
        """Test creating a knowledge base collection with NEW PGVectorStore schema."""
        from app.core.pg_manager import get_pg_manager
        from app.core.kb_types import KBType

        pg_manager = get_pg_manager()

        result = pg_manager.create_collection(
            name="test_collection",
            kb_type=KBType.GENERIC,
            description="Test collection"
        )

        # NEW: create_collection returns Dict with KB metadata
        assert isinstance(result, dict)
        assert result['name'] == 'test_collection'
        assert result['table_name'] == 'data_test_collection'
        assert result['embed_dim'] == 768
        assert pg_manager.collection_exists("test_collection")

        # Verify the data table was created
        with clean_db.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'data_test_collection'
                )
            """)
            table_exists = cur.fetchone()[0]
        assert table_exists is True

    def test_list_collections(self, sample_kb, clean_db):
        """Test listing collections."""
        from app.core.pg_manager import get_pg_manager

        pg_manager = get_pg_manager()
        collections = pg_manager.list_collections()

        assert isinstance(collections, list)
        assert len(collections) > 0
        assert any(c["name"] == sample_kb["name"] for c in collections)

    def test_delete_collection(self, clean_db):
        """Test deleting a collection and its data table."""
        from app.core.pg_manager import get_pg_manager
        from app.core.kb_types import KBType

        pg_manager = get_pg_manager()

        # Create a collection
        pg_manager.create_collection(
            name="collection_to_delete",
            kb_type=KBType.GENERIC,
            description="Will be deleted"
        )

        # Verify table exists before deletion
        with clean_db.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'data_collection_to_delete'
                )
            """)
            table_exists_before = cur.fetchone()[0]
        assert table_exists_before is True

        # Delete it
        result = pg_manager.delete_collection("collection_to_delete")

        assert result is True
        assert not pg_manager.collection_exists("collection_to_delete")

        # Verify table was dropped
        with clean_db.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'data_collection_to_delete'
                )
            """)
            table_exists_after = cur.fetchone()[0]
        assert table_exists_after is False

    def test_get_collection_stats(self, sample_kb, sample_documents, clean_db):
        """Test getting collection statistics using SQL function."""
        # NEW: Use get_kb_stats() SQL function instead of non-existent method
        table_name = sample_kb["table_name"]

        with clean_db.cursor() as cur:
            cur.execute("SELECT * FROM get_kb_stats(%s)", (table_name,))
            result = cur.fetchone()

        # Result is tuple: (total_documents, avg_text_length, total_size_bytes)
        total_documents, avg_text_length, total_size_bytes = result

        assert total_documents == len(sample_documents)
        assert avg_text_length > 0
        assert total_size_bytes > 0

    def test_add_document(self, sample_kb, clean_db, sample_embedding):
        """Test adding documents using add_documents() method (requires llama_index)."""
        pytest.importorskip("llama_index", reason="llama_index required for add_documents()")

        from app.core.pg_manager import get_pg_manager

        pg_manager = get_pg_manager()

        # NEW: Use add_documents() (plural) instead of add_document() (singular)
        pg_manager.add_documents(
            kb_name=sample_kb["name"],
            documents=["New document content"],
            embeddings=[sample_embedding],
            metadatas=[{"filename": "new.txt"}],
            ids=["new_doc"]
        )

        # Verify document was added
        table_name = sample_kb["table_name"]
        with clean_db.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {table_name} WHERE node_id = %s", ("new_doc",))
            count = cur.fetchone()[0]

        assert count == 1

    def test_connection_pooling(self, clean_db):
        """Test connection pool management."""
        from app.core.pg_manager import get_pg_manager

        pg_manager = get_pg_manager()

        # Get multiple connections
        conn1 = pg_manager.get_connection()
        conn2 = pg_manager.get_connection()

        assert conn1 is not None
        assert conn2 is not None

        # Return connections
        pg_manager.return_connection(conn1)
        pg_manager.return_connection(conn2)


@pytest.mark.unit
class TestDatabaseSchema:
    """Test database schema validation."""

    def test_knowledge_bases_table_exists(self, clean_db):
        """Test that knowledge_bases table exists."""
        with clean_db.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'knowledge_bases'
                )
            """)
            exists = cur.fetchone()[0]

        assert exists is True

    def test_documents_table_exists(self, sample_kb, clean_db):
        """Test that KB data table exists (NEW schema uses data_{kb_name} tables)."""
        # NEW: Check for data_test_kb table instead of documents table
        with clean_db.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'data_test_kb'
                )
            """)
            exists = cur.fetchone()[0]

        assert exists is True

    def test_vector_extension_installed(self, clean_db):
        """Test that pgvector extension is installed."""
        with clean_db.cursor() as cur:
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM pg_extension
                    WHERE extname = 'vector'
                )
            """)
            exists = cur.fetchone()[0]

        assert exists is True
