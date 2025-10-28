"""
Comprehensive tests for RAG Engine functionality.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from app.core.rag_engine import RAGEngine, SimpleVectorRetriever
from app.core.kb_types import KBType


@pytest.mark.unit
class TestSimpleVectorRetriever:
    """Test SimpleVectorRetriever class."""

    def test_vector_retriever_initialization(self):
        """Test vector retriever initialization."""
        mock_db = Mock()
        retriever = SimpleVectorRetriever("test_kb", mock_db, similarity_top_k=5)

        assert retriever.kb_name == "test_kb"
        assert retriever.db_manager == mock_db
        assert retriever.similarity_top_k == 5

    def test_vector_retriever_retrieve_with_results(self):
        """Test vector retrieval with results."""
        mock_db = Mock()
        mock_results = {
            "ids": [["doc1", "doc2"]],
            "documents": [["Content 1", "Content 2"]],
            "metadatas": [[{"filename": "file1.txt"}, {"filename": "file2.txt"}]],
            "distances": [[0.1, 0.2]]
        }
        mock_db.query_documents.return_value = mock_results

        retriever = SimpleVectorRetriever("test_kb", mock_db)
        nodes = retriever.retrieve("test query", [0.1] * 768)

        assert len(nodes) == 2
        assert nodes[0].text == "Content 1"
        assert nodes[0].id_ == "doc1"
        assert nodes[0].metadata["filename"] == "file1.txt"
        assert nodes[0].metadata["similarity_score"] == 0.9  # 1 - 0.1

    def test_vector_retriever_retrieve_empty(self):
        """Test vector retrieval with no results."""
        mock_db = Mock()
        mock_results = {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        mock_db.query_documents.return_value = mock_results

        retriever = SimpleVectorRetriever("test_kb", mock_db)
        nodes = retriever.retrieve("test query", [0.1] * 768)

        assert len(nodes) == 0

    def test_vector_retriever_retrieve_none_metadata(self):
        """Test vector retrieval with None metadata."""
        mock_db = Mock()
        mock_results = {
            "ids": [["doc1"]],
            "documents": [["Content 1"]],
            "metadatas": [[None]],
            "distances": [[0.1]]
        }
        mock_db.query_documents.return_value = mock_results

        retriever = SimpleVectorRetriever("test_kb", mock_db)
        nodes = retriever.retrieve("test query", [0.1] * 768)

        assert len(nodes) == 1
        assert nodes[0].metadata == {"similarity_score": 0.9}


@pytest.mark.integration
@pytest.mark.rag
class TestRAGEngineComprehensive:
    """Comprehensive RAG engine tests."""

    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    @patch('app.core.rag_engine.get_sqlite_manager')
    def test_rag_engine_initialization_generic_kb(self, mock_get_db, mock_embed, mock_llm, sample_kb, clean_db):
        """Test RAG engine initialization for generic KB."""
        # Mock database manager
        mock_db = Mock()
        mock_db.collection_exists.return_value = True
        mock_db.get_collection_metadata.return_value = {"kb_type": "generic"}
        mock_get_db.return_value = mock_db

        # Mock embedding model
        mock_embed_instance = MagicMock()
        mock_embed.return_value = mock_embed_instance

        # Mock LLM
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        engine = RAGEngine(sample_kb["name"])

        assert engine.collection_name == sample_kb["name"]
        assert engine.kb_type == "generic"
        assert engine.llm is not None
        assert engine.embed_model is not None
        assert engine.vector_retriever is not None

    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    @patch('app.core.rag_engine.get_sqlite_manager')
    def test_rag_engine_initialization_agent_os_kb(self, mock_get_db, mock_embed, mock_llm, clean_db):
        """Test RAG engine initialization for Agent OS KB."""
        # Create Agent OS KB
        mock_db = Mock()
        mock_db.collection_exists.return_value = True
        mock_db.get_collection_metadata.return_value = {"kb_type": "agent-os"}
        mock_get_db.return_value = mock_db

        mock_embed_instance = MagicMock()
        mock_embed.return_value = mock_embed_instance
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        engine = RAGEngine("agent_os_kb")

        assert engine.kb_type == "agent-os"

    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    @patch('app.core.rag_engine.get_sqlite_manager')
    def test_rag_engine_initialization_nonexistent_kb(self, mock_get_db, mock_embed, mock_llm, clean_db):
        """Test RAG engine initialization with non-existent KB."""
        mock_db = Mock()
        mock_db.collection_exists.return_value = False
        mock_get_db.return_value = mock_db

        with pytest.raises(ValueError, match="not found"):
            RAGEngine("nonexistent_kb")

    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    @patch('app.core.rag_engine.get_sqlite_manager')
    def test_query_base_strategy(self, mock_get_db, mock_embed, mock_llm, sample_kb, sample_documents, clean_db):
        """Test base query strategy."""
        # Setup mocks
        mock_db = Mock()
        mock_db.collection_exists.return_value = True
        mock_db.get_collection_metadata.return_value = {"kb_type": "generic"}
        mock_get_db.return_value = mock_db

        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = [0.1] * 768
        mock_embed.return_value = mock_embed_instance

        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        # Mock vector retriever
        mock_retriever = Mock()
        mock_nodes = [Mock(text="Test content", id_="doc1", metadata={"filename": "test.txt"})]
        mock_retriever.retrieve.return_value = mock_nodes

        # Mock response synthesizer
        with patch('app.core.rag_engine.get_response_synthesizer') as mock_synthesizer:
            mock_response = Mock()
            mock_response.__str__ = Mock(return_value="Test answer")
            mock_synthesizer.return_value.synthesize.return_value = mock_response

            engine = RAGEngine(sample_kb["name"])
            engine.vector_retriever = mock_retriever

            result = engine.query("test question")

            assert result["answer"] == "Test answer"
            assert len(result["sources"]) > 0

    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    @patch('app.core.rag_engine.get_sqlite_manager')
    def test_query_with_no_sources(self, mock_get_db, mock_embed, mock_llm, sample_kb, clean_db):
        """Test query when no sources are found."""
        mock_db = Mock()
        mock_db.collection_exists.return_value = True
        mock_db.get_collection_metadata.return_value = {"kb_type": "generic"}
        mock_get_db.return_value = mock_db

        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = [0.1] * 768
        mock_embed.return_value = mock_embed_instance
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        # Mock empty retriever
        mock_retriever = Mock()
        mock_retriever.retrieve.return_value = []

        engine = RAGEngine(sample_kb["name"])
        engine.vector_retriever = mock_retriever

        result = engine.query("test question")

        assert "No relevant information found" in result["answer"]
        assert len(result["sources"]) == 0

    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    @patch('app.core.rag_engine.get_sqlite_manager')
    def test_query_with_synthesis_error(self, mock_get_db, mock_embed, mock_llm, sample_kb, sample_documents, clean_db):
        """Test query when synthesis fails."""
        mock_db = Mock()
        mock_db.collection_exists.return_value = True
        mock_db.get_collection_metadata.return_value = {"kb_type": "generic"}
        mock_get_db.return_value = mock_db

        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = [0.1] * 768
        mock_embed.return_value = mock_embed_instance
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        # Mock retriever with results
        mock_retriever = Mock()
        mock_nodes = [Mock(text="Test content", id_="doc1", metadata={"filename": "test.txt"})]
        mock_retriever.retrieve.return_value = mock_nodes

        # Mock synthesizer that raises exception
        with patch('app.core.rag_engine.get_response_synthesizer') as mock_synthesizer:
            mock_synthesizer.return_value.synthesize.side_effect = Exception("Synthesis failed")

            engine = RAGEngine(sample_kb["name"])
            engine.vector_retriever = mock_retriever

            result = engine.query("test question")

            # Should use fallback answer
            assert "Based on the available documentation" in result["answer"]
            assert len(result["sources"]) > 0

    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    @patch('app.core.rag_engine.get_sqlite_manager')
    def test_query_hybrid_strategy(self, mock_get_db, mock_embed, mock_llm, sample_kb, clean_db):
        """Test hybrid query strategy."""
        mock_db = Mock()
        mock_db.collection_exists.return_value = True
        mock_db.get_collection_metadata.return_value = {"kb_type": "generic"}
        mock_get_db.return_value = mock_db

        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = [0.1] * 768
        mock_embed.return_value = mock_embed_instance
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        engine = RAGEngine(sample_kb["name"])
        engine.bm25_retriever = None  # No BM25 retriever

        # Hybrid should fall back to base when BM25 not available
        result = engine.query("test question", use_hybrid=True)

        # Should still return a result
        assert "answer" in result
        assert "sources" in result

    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    @patch('app.core.rag_engine.get_sqlite_manager')
    def test_query_agentic_strategy(self, mock_get_db, mock_embed, mock_llm, sample_kb, clean_db):
        """Test agentic query strategy."""
        mock_db = Mock()
        mock_db.collection_exists.return_value = True
        mock_db.get_collection_metadata.return_value = {"kb_type": "generic"}
        mock_get_db.return_value = mock_db

        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = [0.1] * 768
        mock_embed.return_value = mock_embed_instance
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        engine = RAGEngine(sample_kb["name"])
        engine.sub_question_engine = None  # No agentic engine

        # Agentic should fall back to base when not available
        result = engine.query("test question", use_agentic=True)

        # Should still return a result
        assert "answer" in result
        assert "sources" in result

    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    @patch('app.core.rag_engine.get_sqlite_manager')
    def test_query_with_reranking(self, mock_get_db, mock_embed, mock_llm, sample_kb, clean_db):
        """Test query with reranking enabled."""
        mock_db = Mock()
        mock_db.collection_exists.return_value = True
        mock_db.get_collection_metadata.return_value = {"kb_type": "generic"}
        mock_get_db.return_value = mock_db

        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = [0.1] * 768
        mock_embed.return_value = mock_embed_instance
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        engine = RAGEngine(sample_kb["name"])
        engine.reranker = None  # Reranker disabled by default

        result = engine.query("test question", use_rerank=True)

        # Should still work without reranker
        assert "answer" in result
        assert "sources" in result

    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    @patch('app.core.rag_engine.get_sqlite_manager')
    def test_query_error_handling(self, mock_get_db, mock_embed, mock_llm, sample_kb, clean_db):
        """Test query error handling."""
        mock_db = Mock()
        mock_db.collection_exists.return_value = True
        mock_db.get_collection_metadata.return_value = {"kb_type": "generic"}
        mock_get_db.return_value = mock_db

        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.side_effect = Exception("Embedding failed")
        mock_embed.return_value = mock_embed_instance
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        engine = RAGEngine(sample_kb["name"])

        result = engine.query("test question")

        assert "Error executing query" in result["answer"]
        assert len(result["sources"]) == 0


@pytest.mark.unit
class TestRAGEngineHelpers:
    """Test RAG engine helper methods."""

    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    @patch('app.core.rag_engine.get_sqlite_manager')
    def test_reciprocal_rank_fusion(self, mock_get_db, mock_embed, mock_llm, clean_db):
        """Test reciprocal rank fusion."""
        mock_db = Mock()
        mock_db.collection_exists.return_value = True
        mock_db.get_collection_metadata.return_value = {"kb_type": "generic"}
        mock_get_db.return_value = mock_db

        mock_embed_instance = MagicMock()
        mock_embed.return_value = mock_embed_instance
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        engine = RAGEngine("test_kb")

        # Create mock nodes
        node1 = Mock()
        node1.id_ = "doc1"
        node2 = Mock()
        node2.id_ = "doc2"
        node3 = Mock()
        node3.id_ = "doc3"

        # Test RRF with overlapping results
        results_list = [
            [node1, node2],  # First retriever
            [node2, node3],  # Second retriever
        ]

        fused = engine._reciprocal_rank_fusion(results_list, k=60)

        # Should have all 3 nodes
        assert len(fused) == 3

        # node2 should be ranked higher (appears in both lists)
        node2_index = fused.index(node2)
        node1_index = fused.index(node1)
        node3_index = fused.index(node3)

        assert node2_index < node1_index
        assert node2_index < node3_index

    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    @patch('app.core.rag_engine.get_sqlite_manager')
    def test_format_response(self, mock_get_db, mock_embed, mock_llm, clean_db):
        """Test response formatting."""
        mock_db = Mock()
        mock_db.collection_exists.return_value = True
        mock_db.get_collection_metadata.return_value = {"kb_type": "generic"}
        mock_get_db.return_value = mock_db

        mock_embed_instance = MagicMock()
        mock_embed.return_value = mock_embed_instance
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        engine = RAGEngine("test_kb")

        # Create mock response and nodes
        response = Mock()
        response.__str__ = Mock(return_value="Test answer")

        node1 = Mock()
        node1.text = "Content 1"
        node1.metadata = {"filename": "file1.txt", "similarity_score": 0.9}

        node2 = Mock()
        node2.text = "Content 2"
        node2.metadata = {"filename": "file2.txt", "similarity_score": 0.8}

        result = engine._format_response(response, [node1, node2])

        assert result["answer"] == "Test answer"
        assert len(result["sources"]) == 2

        # Check first source
        source1 = result["sources"][0]
        assert source1["text"] == "Content 1"
        assert source1["metadata"]["filename"] == "file1.txt"
        assert "similarity_score" not in source1["metadata"]  # Should be removed
        assert source1["score"] == 0.9

    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    @patch('app.core.rag_engine.get_sqlite_manager')
    def test_generate_fallback_answer(self, mock_get_db, mock_embed, mock_llm, clean_db):
        """Test fallback answer generation."""
        mock_db = Mock()
        mock_db.collection_exists.return_value = True
        mock_db.get_collection_metadata.return_value = {"kb_type": "generic"}
        mock_get_db.return_value = mock_db

        mock_embed_instance = MagicMock()
        mock_embed.return_value = mock_embed_instance
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        engine = RAGEngine("test_kb")

        # Create mock nodes
        node1 = Mock()
        node1.text = "This is the first document with important information."
        node1.metadata = {"filename": "doc1.txt"}

        node2 = Mock()
        node2.text = "This is the second document with more details."
        node2.metadata = {"filename": "doc2.txt"}

        answer = engine._generate_fallback_answer("test question", [node1, node2])

        assert "Based on the available documentation" in answer
        assert "doc1.txt" in answer
        assert "doc2.txt" in answer
        assert "first document" in answer
        assert "second document" in answer

    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    @patch('app.core.rag_engine.get_sqlite_manager')
    def test_generate_fallback_answer_empty(self, mock_get_db, mock_embed, mock_llm, clean_db):
        """Test fallback answer generation with no nodes."""
        mock_db = Mock()
        mock_db.collection_exists.return_value = True
        mock_db.get_collection_metadata.return_value = {"kb_type": "generic"}
        mock_get_db.return_value = mock_db

        mock_embed_instance = MagicMock()
        mock_embed.return_value = mock_embed_instance
        mock_llm_instance = MagicMock()
        mock_llm.return_value = mock_llm_instance

        engine = RAGEngine("test_kb")

        answer = engine._generate_fallback_answer("test question", [])

        assert "No relevant information found" in answer