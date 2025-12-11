"""
Tests for rag_engine.py - RAG Engine functionality.
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from typing import List

from llama_index.core.schema import TextNode

from app.core.rag_engine import SimpleVectorRetriever, RAGEngine


class TestSimpleVectorRetriever:
    """Tests for SimpleVectorRetriever class."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager."""
        mock = MagicMock()
        mock.query_documents.return_value = {
            "ids": [["doc1", "doc2", "doc3"]],
            "documents": [["Content 1", "Content 2", "Content 3"]],
            "metadatas": [[{"filename": "a.txt"}, {"filename": "b.txt"}, {}]],
            "distances": [[0.1, 0.2, 0.3]]
        }
        return mock

    def test_init(self, mock_db_manager):
        """Test SimpleVectorRetriever initialization."""
        retriever = SimpleVectorRetriever(
            kb_name="test_kb",
            db_manager=mock_db_manager,
            similarity_top_k=5
        )
        assert retriever.kb_name == "test_kb"
        assert retriever.similarity_top_k == 5

    def test_retrieve_returns_text_nodes(self, mock_db_manager):
        """Test that retrieve returns TextNode objects."""
        retriever = SimpleVectorRetriever("test_kb", mock_db_manager, 10)

        query_embedding = [0.1] * 768
        nodes = retriever.retrieve("test query", query_embedding)

        assert len(nodes) == 3
        assert all(isinstance(n, TextNode) for n in nodes)

    def test_retrieve_preserves_content(self, mock_db_manager):
        """Test that retrieve preserves document content."""
        retriever = SimpleVectorRetriever("test_kb", mock_db_manager, 10)

        nodes = retriever.retrieve("query", [0.1] * 768)

        assert nodes[0].text == "Content 1"
        assert nodes[1].text == "Content 2"
        assert nodes[2].text == "Content 3"

    def test_retrieve_preserves_ids(self, mock_db_manager):
        """Test that retrieve preserves document IDs."""
        retriever = SimpleVectorRetriever("test_kb", mock_db_manager, 10)

        nodes = retriever.retrieve("query", [0.1] * 768)

        assert nodes[0].id_ == "doc1"
        assert nodes[1].id_ == "doc2"
        assert nodes[2].id_ == "doc3"

    def test_retrieve_calculates_similarity_score(self, mock_db_manager):
        """Test that similarity score is calculated correctly."""
        retriever = SimpleVectorRetriever("test_kb", mock_db_manager, 10)

        nodes = retriever.retrieve("query", [0.1] * 768)

        # Score = 1 - distance
        assert nodes[0].metadata["similarity_score"] == 0.9  # 1 - 0.1
        assert nodes[1].metadata["similarity_score"] == 0.8  # 1 - 0.2
        assert nodes[2].metadata["similarity_score"] == 0.7  # 1 - 0.3

    def test_retrieve_handles_empty_results(self, mock_db_manager):
        """Test retrieve handles empty results gracefully."""
        mock_db_manager.query_documents.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
            "distances": []
        }
        retriever = SimpleVectorRetriever("test_kb", mock_db_manager, 10)

        nodes = retriever.retrieve("query", [0.1] * 768)

        assert nodes == []

    def test_retrieve_handles_none_metadata(self, mock_db_manager):
        """Test retrieve handles None metadata."""
        mock_db_manager.query_documents.return_value = {
            "ids": [["doc1"]],
            "documents": [["Content"]],
            "metadatas": [[None]],
            "distances": [[0.1]]
        }
        retriever = SimpleVectorRetriever("test_kb", mock_db_manager, 10)

        nodes = retriever.retrieve("query", [0.1] * 768)

        assert len(nodes) == 1
        assert nodes[0].metadata["similarity_score"] == 0.9


class TestRAGEngineInit:
    """Tests for RAGEngine initialization."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all external dependencies."""
        with patch('app.core.rag_engine.get_sqlite_manager') as mock_db:
            with patch('app.core.rag_engine.Ollama') as mock_llm:
                with patch('app.core.rag_engine.OllamaEmbedding') as mock_embed:
                    with patch('app.core.rag_engine.Settings') as mock_settings:
                        # Configure mocks
                        mock_db_instance = MagicMock()
                        mock_db_instance.collection_exists.return_value = True
                        mock_db_instance.get_collection_metadata.return_value = {"kb_type": "generic"}
                        mock_db.return_value = mock_db_instance

                        mock_llm_instance = MagicMock()
                        mock_llm.return_value = mock_llm_instance

                        mock_embed_instance = MagicMock()
                        mock_embed.return_value = mock_embed_instance

                        yield {
                            "db": mock_db,
                            "db_instance": mock_db_instance,
                            "llm": mock_llm,
                            "embed": mock_embed,
                            "settings": mock_settings
                        }

    def test_init_success(self, mock_dependencies):
        """Test successful RAGEngine initialization."""
        engine = RAGEngine("test_collection")

        assert engine.collection_name == "test_collection"
        assert engine.kb_type == "generic"
        mock_dependencies["db_instance"].collection_exists.assert_called_with("test_collection")

    def test_init_collection_not_found(self, mock_dependencies):
        """Test initialization fails when collection doesn't exist."""
        mock_dependencies["db_instance"].collection_exists.return_value = False

        with pytest.raises(ValueError, match="Collection test_kb not found"):
            RAGEngine("test_kb")

    def test_init_creates_vector_retriever(self, mock_dependencies):
        """Test that initialization creates vector retriever."""
        engine = RAGEngine("test_collection")

        assert engine.vector_retriever is not None
        assert isinstance(engine.vector_retriever, SimpleVectorRetriever)


class TestRAGEngineQuery:
    """Tests for RAGEngine query methods."""

    @pytest.fixture
    def mock_engine(self):
        """Create a RAGEngine with mocked dependencies."""
        with patch('app.core.rag_engine.get_sqlite_manager') as mock_db:
            with patch('app.core.rag_engine.Ollama'):
                with patch('app.core.rag_engine.OllamaEmbedding') as mock_embed:
                    with patch('app.core.rag_engine.Settings'):
                        # Configure db mock
                        mock_db_instance = MagicMock()
                        mock_db_instance.collection_exists.return_value = True
                        mock_db_instance.get_collection_metadata.return_value = {"kb_type": "generic"}
                        mock_db_instance.query_documents.return_value = {
                            "ids": [["doc1", "doc2"]],
                            "documents": [["Answer content 1", "Answer content 2"]],
                            "metadatas": [[{"filename": "a.txt"}, {"filename": "b.txt"}]],
                            "distances": [[0.1, 0.2]]
                        }
                        mock_db.return_value = mock_db_instance

                        # Configure embed mock
                        mock_embed_instance = MagicMock()
                        mock_embed_instance.get_text_embedding.return_value = [0.1] * 768
                        mock_embed.return_value = mock_embed_instance

                        engine = RAGEngine("test_collection")
                        engine.embed_model = mock_embed_instance

                        yield engine

    def test_query_base_returns_answer(self, mock_engine):
        """Test that _query_base returns an answer."""
        with patch('app.core.rag_engine.get_response_synthesizer') as mock_synth:
            mock_response = MagicMock()
            mock_response.__str__ = lambda x: "Test answer"
            mock_synth.return_value.synthesize.return_value = mock_response

            result = mock_engine._query_base("test question", [0.1] * 768)

            assert "answer" in result
            assert "sources" in result

    def test_query_base_returns_sources(self, mock_engine):
        """Test that _query_base returns sources."""
        with patch('app.core.rag_engine.get_response_synthesizer') as mock_synth:
            mock_synth.return_value.synthesize.return_value = MagicMock(__str__=lambda x: "Answer")

            result = mock_engine._query_base("test question", [0.1] * 768)

            assert len(result["sources"]) == 2
            assert result["sources"][0]["text"] == "Answer content 1"
            assert result["sources"][1]["text"] == "Answer content 2"

    def test_query_base_handles_no_results(self, mock_engine):
        """Test _query_base handles no results."""
        mock_engine.db_manager.query_documents.return_value = {
            "ids": [],
            "documents": [],
            "metadatas": [],
            "distances": []
        }

        result = mock_engine._query_base("test question", [0.1] * 768)

        assert "No relevant information found" in result["answer"]
        assert result["sources"] == []

    def test_query_routes_to_base(self, mock_engine):
        """Test that query() routes to _query_base by default."""
        with patch.object(mock_engine, '_query_base') as mock_base:
            mock_base.return_value = {"answer": "Test", "sources": []}

            mock_engine.query("test question")

            mock_base.assert_called_once()

    def test_query_routes_to_hybrid(self, mock_engine):
        """Test that query() routes to _query_hybrid when use_hybrid=True."""
        with patch.object(mock_engine, '_query_hybrid') as mock_hybrid:
            mock_hybrid.return_value = {"answer": "Test", "sources": []}

            mock_engine.query("test question", use_hybrid=True)

            mock_hybrid.assert_called_once()

    def test_query_routes_to_agentic(self, mock_engine):
        """Test that query() routes to _query_agentic when use_agentic=True."""
        with patch.object(mock_engine, '_query_agentic') as mock_agentic:
            mock_agentic.return_value = {"answer": "Test", "sources": []}

            mock_engine.query("test question", use_agentic=True)

            mock_agentic.assert_called_once()

    def test_query_handles_exception(self, mock_engine):
        """Test that query() handles exceptions gracefully."""
        mock_engine.embed_model.get_text_embedding.side_effect = Exception("Embedding failed")

        result = mock_engine.query("test question")

        assert "Error executing query" in result["answer"]
        assert result["sources"] == []


class TestRAGEngineHelpers:
    """Tests for RAGEngine helper methods."""

    @pytest.fixture
    def mock_engine(self):
        """Create a RAGEngine with mocked dependencies."""
        with patch('app.core.rag_engine.get_sqlite_manager') as mock_db:
            with patch('app.core.rag_engine.Ollama'):
                with patch('app.core.rag_engine.OllamaEmbedding'):
                    with patch('app.core.rag_engine.Settings'):
                        mock_db_instance = MagicMock()
                        mock_db_instance.collection_exists.return_value = True
                        mock_db_instance.get_collection_metadata.return_value = {}
                        mock_db.return_value = mock_db_instance

                        yield RAGEngine("test_collection")

    def test_format_response(self, mock_engine):
        """Test _format_response method."""
        node = TextNode(
            text="Test content",
            id_="doc1",
            metadata={"filename": "test.txt", "similarity_score": 0.95}
        )

        result = mock_engine._format_response("Test answer", [node])

        assert result["answer"] == "Test answer"
        assert len(result["sources"]) == 1
        assert result["sources"][0]["text"] == "Test content"
        assert result["sources"][0]["score"] == 0.95
        # similarity_score should be removed from display metadata
        assert "similarity_score" not in result["sources"][0]["metadata"]
        assert result["sources"][0]["metadata"]["filename"] == "test.txt"

    def test_format_response_multiple_nodes(self, mock_engine):
        """Test _format_response with multiple nodes."""
        nodes = [
            TextNode(text="Content 1", id_="doc1", metadata={"similarity_score": 0.9}),
            TextNode(text="Content 2", id_="doc2", metadata={"similarity_score": 0.8}),
        ]

        result = mock_engine._format_response("Answer", nodes)

        assert len(result["sources"]) == 2

    def test_generate_fallback_answer_empty(self, mock_engine):
        """Test _generate_fallback_answer with no nodes."""
        result = mock_engine._generate_fallback_answer("test question", [])

        assert "No relevant information found" in result

    def test_generate_fallback_answer_with_nodes(self, mock_engine):
        """Test _generate_fallback_answer with nodes."""
        nodes = [
            TextNode(text="Content about the topic", metadata={"filename": "doc.txt"}),
        ]

        result = mock_engine._generate_fallback_answer("test question", nodes)

        assert "Content about the topic" in result
        assert "doc.txt" in result

    def test_reciprocal_rank_fusion(self, mock_engine):
        """Test _reciprocal_rank_fusion method."""
        node1 = TextNode(text="Node 1", id_="n1")
        node2 = TextNode(text="Node 2", id_="n2")
        node3 = TextNode(text="Node 3", id_="n3")

        results_list = [
            [node1, node2],  # List 1: n1 rank 1, n2 rank 2
            [node2, node3],  # List 2: n2 rank 1, n3 rank 2
        ]

        fused = mock_engine._reciprocal_rank_fusion(results_list)

        # node2 appears in both lists, should be ranked higher
        assert len(fused) > 0
        # The first result should be n2 (appears in both lists at good positions)
        node_ids = [n.id_ for n in fused]
        assert "n2" in node_ids

    def test_apply_reranking_no_reranker(self, mock_engine):
        """Test _apply_reranking when reranker is None."""
        mock_engine.reranker = None
        nodes = [TextNode(text="Test", id_="t1")]

        result = mock_engine._apply_reranking(nodes, "query")

        assert result == nodes

    def test_apply_reranking_with_reranker(self, mock_engine):
        """Test _apply_reranking with reranker."""
        mock_reranker = MagicMock()
        mock_reranker.postprocess_nodes.return_value = [TextNode(text="Reranked", id_="r1")]
        mock_engine.reranker = mock_reranker

        nodes = [TextNode(text="Original", id_="o1")]
        result = mock_engine._apply_reranking(nodes, "query")

        assert result[0].text == "Reranked"
        mock_reranker.postprocess_nodes.assert_called_once()


class TestRAGEngineHybrid:
    """Tests for RAGEngine hybrid query method."""

    @pytest.fixture
    def mock_engine(self):
        """Create a RAGEngine with mocked dependencies."""
        with patch('app.core.rag_engine.get_sqlite_manager') as mock_db:
            with patch('app.core.rag_engine.Ollama'):
                with patch('app.core.rag_engine.OllamaEmbedding'):
                    with patch('app.core.rag_engine.Settings'):
                        mock_db_instance = MagicMock()
                        mock_db_instance.collection_exists.return_value = True
                        mock_db_instance.get_collection_metadata.return_value = {}
                        mock_db_instance.query_documents.return_value = {
                            "ids": [["doc1"]],
                            "documents": [["Content"]],
                            "metadatas": [[{}]],
                            "distances": [[0.1]]
                        }
                        mock_db.return_value = mock_db_instance

                        yield RAGEngine("test_collection")

    def test_query_hybrid_fallback_no_bm25(self, mock_engine):
        """Test _query_hybrid falls back to base when BM25 not available."""
        mock_engine.bm25_retriever = None

        with patch.object(mock_engine, '_query_base') as mock_base:
            mock_base.return_value = {"answer": "Base answer", "sources": []}

            result = mock_engine._query_hybrid("question", [0.1] * 768)

            mock_base.assert_called_once()
            assert result["answer"] == "Base answer"


class TestRAGEngineAgentic:
    """Tests for RAGEngine agentic query method."""

    @pytest.fixture
    def mock_engine(self):
        """Create a RAGEngine with mocked dependencies."""
        with patch('app.core.rag_engine.get_sqlite_manager') as mock_db:
            with patch('app.core.rag_engine.Ollama'):
                with patch('app.core.rag_engine.OllamaEmbedding'):
                    with patch('app.core.rag_engine.Settings'):
                        mock_db_instance = MagicMock()
                        mock_db_instance.collection_exists.return_value = True
                        mock_db_instance.get_collection_metadata.return_value = {}
                        mock_db.return_value = mock_db_instance

                        yield RAGEngine("test_collection")

    def test_query_agentic_fallback_no_engine(self, mock_engine):
        """Test _query_agentic falls back to base when engine not available."""
        mock_engine.sub_question_engine = None

        with patch.object(mock_engine, '_query_base') as mock_base:
            mock_base.return_value = {"answer": "Base answer", "sources": []}

            result = mock_engine._query_agentic("question", [0.1] * 768)

            mock_base.assert_called_once()
            assert result["answer"] == "Base answer"
