"""
Tests for RAG Engine.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.integration
@pytest.mark.rag
class TestRAGEngine:
    """Test RAG engine functionality."""

    @patch('app.core.rag_engine.Settings')
    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    @patch('app.core.rag_engine.get_sqlite_manager')
    def test_rag_engine_initialization(self, mock_get_db, mock_embed, mock_llm, mock_settings, sample_kb, clean_db):
        """Test that RAG engine initializes correctly."""
        # Configure mocks
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = True
        mock_db.get_collection_metadata.return_value = {"kb_type": "generic", "id": sample_kb["id"]}
        mock_get_db.return_value = mock_db

        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        mock_embed_instance = MagicMock()
        mock_embed.return_value = mock_embed_instance

        from app.core.rag_engine import RAGEngine

        engine = RAGEngine(sample_kb["name"])

        assert engine.collection_name == sample_kb["name"]
        assert engine.llm == mock_llm_instance
        assert engine.embed_model == mock_embed_instance
        mock_db.collection_exists.assert_called_with(sample_kb["name"])

    @patch('app.core.rag_engine.Settings')
    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    @patch('app.core.rag_engine.get_sqlite_manager')
    def test_rag_engine_collection_not_found(self, mock_get_db, mock_embed, mock_llm, mock_settings, sample_kb):
        """Test that RAG engine raises error for non-existent collection."""
        # Configure mocks
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = False
        mock_get_db.return_value = mock_db

        from app.core.rag_engine import RAGEngine

        with pytest.raises(ValueError, match="Collection .* not found"):
            RAGEngine("nonexistent_collection")

    @patch('app.core.rag_engine.Settings')
    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    @patch('app.core.rag_engine.get_sqlite_manager')
    def test_query_with_no_documents(self, mock_get_db, mock_embed, mock_llm, mock_settings, sample_kb):
        """Test querying when no documents exist."""
        # Configure mocks
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = True
        mock_db.get_collection_metadata.return_value = {"kb_type": "generic", "id": sample_kb["id"]}
        mock_db.query_documents.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }
        mock_get_db.return_value = mock_db

        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = [0.1] * 768
        mock_embed.return_value = mock_embed_instance

        from app.core.rag_engine import RAGEngine

        engine = RAGEngine(sample_kb["name"])
        result = engine.query("test question")

        # When no documents found, returns "No relevant information found"
        assert "No relevant information found" in result["answer"]
        assert len(result["sources"]) == 0

    @patch('app.core.rag_engine.Settings')
    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    @patch('app.core.rag_engine.get_sqlite_manager')
    def test_query_with_documents(self, mock_get_db, mock_embed, mock_llm, mock_settings, sample_kb, sample_embedding):
        """Test querying with documents returns sources."""
        # Configure mocks
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = True
        mock_db.get_collection_metadata.return_value = {"kb_type": "generic", "id": sample_kb["id"]}
        mock_db.query_documents.return_value = {
            "ids": [["doc1"]],
            "documents": [["This is test content about the topic."]],
            "metadatas": [[{"source": "test.md"}]],
            "distances": [[0.2]]
        }
        mock_get_db.return_value = mock_db

        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.message.content = "This is a test answer."
        mock_llm_instance.chat.return_value = mock_response
        mock_llm.return_value = mock_llm_instance

        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = sample_embedding
        mock_embed.return_value = mock_embed_instance

        from app.core.rag_engine import RAGEngine

        engine = RAGEngine(sample_kb["name"])
        result = engine.query("test question")

        # Result should contain answer and sources
        assert result["answer"] is not None
        assert len(result["sources"]) == 1
        assert result["sources"][0]["text"] == "This is test content about the topic."


@pytest.mark.unit
class TestSimpleVectorRetriever:
    """Test SimpleVectorRetriever functionality."""

    def test_retriever_initialization(self, sample_kb, clean_db):
        """Test that retriever initializes correctly."""
        from app.core.rag_engine import SimpleVectorRetriever

        retriever = SimpleVectorRetriever(sample_kb["name"], clean_db, similarity_top_k=5)

        assert retriever.kb_name == sample_kb["name"]
        assert retriever.db_manager == clean_db
        assert retriever.similarity_top_k == 5

    def test_retriever_with_results(self, sample_kb, clean_db, sample_embedding):
        """Test retriever returns results correctly."""
        from app.core.rag_engine import SimpleVectorRetriever

        # add_documents signature: (kb_name, documents, embeddings, metadatas, ids)
        clean_db.add_documents(
            sample_kb["name"],
            ["Test content 1", "Test content 2"],  # documents
            [sample_embedding, sample_embedding],  # embeddings
            [{"source": "file1.md"}, {"source": "file2.md"}],  # metadatas
            ["doc1", "doc2"]  # ids
        )

        retriever = SimpleVectorRetriever(sample_kb["name"], clean_db, similarity_top_k=5)
        nodes = retriever.retrieve("test query", sample_embedding)

        assert len(nodes) >= 1
        assert nodes[0].text in ["Test content 1", "Test content 2"]

    def test_retriever_with_no_results(self, sample_kb, clean_db, sample_embedding):
        """Test retriever with empty KB."""
        from app.core.rag_engine import SimpleVectorRetriever

        retriever = SimpleVectorRetriever(sample_kb["name"], clean_db, similarity_top_k=5)
        nodes = retriever.retrieve("test query", sample_embedding)

        assert len(nodes) == 0
