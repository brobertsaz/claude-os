"""
Tests for embedding generation.
"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock


@pytest.mark.integration
@pytest.mark.embeddings
class TestOllamaEmbeddings:
    """Test Ollama embedding generation."""
    
    @patch('llama_index.embeddings.ollama.OllamaEmbedding')
    def test_embedding_generation(self, mock_ollama):
        """Test that embeddings are generated correctly."""
        # Mock the embedding model
        mock_instance = MagicMock()
        mock_instance.get_text_embedding.return_value = np.random.randn(768).tolist()
        mock_ollama.return_value = mock_instance
        
        from llama_index.embeddings.ollama import OllamaEmbedding
        
        embed_model = OllamaEmbedding(
            model_name="nomic-embed-text",
            base_url="http://localhost:11434"
        )
        
        embedding = embed_model.get_text_embedding("test text")
        
        assert len(embedding) == 768
        assert all(isinstance(x, float) for x in embedding)
    
    def test_embedding_consistency(self):
        """Test that same text produces same embedding."""
        from llama_index.embeddings.ollama import OllamaEmbedding
        
        embed_model = OllamaEmbedding(
            model_name="nomic-embed-text",
            base_url="http://localhost:11434"
        )
        
        text = "This is a test sentence for embedding consistency."
        
        embedding1 = embed_model.get_text_embedding(text)
        embedding2 = embed_model.get_text_embedding(text)
        
        # Should be identical (or very close due to floating point)
        np.testing.assert_array_almost_equal(embedding1, embedding2, decimal=5)
    
    def test_embedding_dimension(self):
        """Test that embeddings have correct dimension."""
        from llama_index.embeddings.ollama import OllamaEmbedding
        
        embed_model = OllamaEmbedding(
            model_name="nomic-embed-text",
            base_url="http://localhost:11434"
        )
        
        texts = [
            "Short text",
            "This is a longer text with more words and content.",
            "A" * 1000  # Very long text
        ]
        
        for text in texts:
            embedding = embed_model.get_text_embedding(text)
            assert len(embedding) == 768, f"Expected 768 dimensions, got {len(embedding)}"


@pytest.mark.unit
class TestEmbeddingUtils:
    """Test embedding utility functions."""
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation."""
        # Identical vectors should have similarity of 1.0
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        
        similarity = 1 - np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        assert abs(similarity) < 0.001  # Should be ~0 (distance), so similarity ~1
    
    def test_embedding_normalization(self):
        """Test that embeddings can be normalized."""
        embedding = np.random.randn(768)
        normalized = embedding / np.linalg.norm(embedding)
        
        # Normalized vector should have magnitude 1
        assert abs(np.linalg.norm(normalized) - 1.0) < 0.001
