"""
Tests for PostgreSQL vector operations.
"""

import pytest
import numpy as np


@pytest.mark.integration
@pytest.mark.vector
class TestPGVectorOperations:
    """Test PostgreSQL vector similarity operations."""

    def test_vector_storage(self, sample_kb, clean_db, sample_embedding):
        """Test that we can store and retrieve vectors in NEW PGVectorStore schema."""
        import json

        table_name = sample_kb["table_name"]  # Should be 'data_test_kb'

        with clean_db.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {table_name} (text, metadata_, node_id, embedding)
                VALUES (%s, %s, %s, %s)
                RETURNING id, embedding
                """,
                ("Test content", json.dumps({}), "test_node", sample_embedding)
            )
            doc_id, retrieved_embedding = cur.fetchone()

        clean_db.commit()

        assert doc_id is not None
        assert len(retrieved_embedding) == 768
        np.testing.assert_array_almost_equal(retrieved_embedding, sample_embedding, decimal=6)

    def test_pg_manager_query_similar(self, sample_kb, sample_documents, clean_db):
        """Test the PostgresManager.query_similar() method."""
        from app.core.pg_manager import get_pg_manager

        pg_manager = get_pg_manager()
        query_embedding = sample_documents[0]["embedding"]

        results = pg_manager.query_similar(
            kb_id=sample_kb["id"],
            query_embedding=query_embedding,
            top_k=3
        )

        assert len(results) == 3
        assert results[0]["similarity"] > 0.99
