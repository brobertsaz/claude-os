"""
Tests for RAG Engine.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.integration
@pytest.mark.rag
class TestRAGEngine:
    """Test RAG engine functionality."""
    
    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    def test_rag_engine_initialization(self, mock_embed, mock_llm, sample_kb, clean_db):
        """Test that RAG engine initializes correctly."""
        from app.core.rag_engine import RAGEngine
        
        engine = RAGEngine(sample_kb["name"])
        
        assert engine.collection_name == sample_kb["name"]
        assert engine.kb_id == sample_kb["id"]
        assert engine.llm is not None
        assert engine.embed_model is not None
    
    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    def test_query_with_no_documents(self, mock_embed, mock_llm, sample_kb, clean_db):
        """Test querying when no documents exist."""
        from app.core.rag_engine import RAGEngine
        
        # Mock embedding generation
        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = [0.1] * 768
        mock_embed.return_value = mock_embed_instance
        
        engine = RAGEngine(sample_kb["name"])
        result = engine.query("test question")
        
        assert result["answer"] == "Empty Response"
        assert len(result["sources"]) == 0
    
    @patch('app.core.rag_engine.Ollama')
    @patch('app.core.rag_engine.OllamaEmbedding')
    def test_query_with_documents(self, mock_embed, mock_llm, sample_kb, sample_documents, clean_db):
        """Test querying with documents."""
        from app.core.rag_engine import RAGEngine
        
        # Mock embedding generation
        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = sample_documents[0]["embedding"]
        mock_embed.return_value = mock_embed_instance
        
        # Mock LLM response
        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.message.content = "This is a test answer."
        mock_llm_instance.chat.return_value = mock_response
        mock_llm.return_value = mock_llm_instance
        
        engine = RAGEngine(sample_kb["name"])
        result = engine.query("test question")
        
        assert result["answer"] == "This is a test answer."
        assert len(result["sources"]) > 0
