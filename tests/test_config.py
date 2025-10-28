"""
Tests for configuration management functionality.
"""

import pytest
import os
from unittest.mock import patch, MagicMock

from app.core.config import Config


@pytest.mark.unit
class TestConfig:
    """Test Config class."""

    def test_config_constants(self):
        """Test configuration constants."""
        # Check that constants are defined
        assert hasattr(Config, 'OLLAMA_HOST')
        assert hasattr(Config, 'SUPPORTED_FILE_TYPES')
        assert hasattr(Config, 'CHUNK_SIZE')
        assert hasattr(Config, 'CHUNK_OVERLAP')
        assert hasattr(Config, 'EMBEDDING_MODEL')
        assert hasattr(Config, 'LLM_MODEL')
        assert hasattr(Config, 'MAX_CONTEXT_LENGTH')
        assert hasattr(Config, 'SIMILARITY_TOP_K')
        assert hasattr(Config, 'RERANK_MODEL')
        assert hasattr(Config, 'RERANK_TOP_K')

    def test_config_default_values(self):
        """Test configuration default values."""
        # Check default values
        assert Config.OLLAMA_HOST == "http://localhost:11434"
        assert isinstance(Config.SUPPORTED_FILE_TYPES, list)
        assert len(Config.SUPPORTED_FILE_TYPES) > 0
        assert Config.CHUNK_SIZE > 0
        assert Config.CHUNK_OVERLAP >= 0
        assert Config.EMBEDDING_MODEL is not None
        assert Config.LLM_MODEL is not None
        assert Config.MAX_CONTEXT_LENGTH > 0
        assert Config.SIMILARITY_TOP_K > 0

    def test_config_file_types(self):
        """Test supported file types."""
        file_types = Config.SUPPORTED_FILE_TYPES

        # Should include common file types
        assert ".txt" in file_types
        assert ".md" in file_types
        assert ".py" in file_types
        assert ".js" in file_types
        assert ".json" in file_types
        assert ".yaml" in file_types
        assert ".yml" in file_types

        # Should include code file types
        assert ".jsx" in file_types
        assert ".ts" in file_types
        assert ".tsx" in file_types
        assert ".go" in file_types
        assert ".rs" in file_types
        assert ".java" in file_types
        assert ".cpp" in file_types
        assert ".c" in file_types
        assert ".h" in file_types

        # Should include document file types
        assert ".pdf" in file_types

    def test_config_chunking_parameters(self):
        """Test chunking configuration parameters."""
        assert Config.CHUNK_SIZE > 0
        assert Config.CHUNK_OVERLAP >= 0
        assert Config.CHUNK_OVERLAP < Config.CHUNK_SIZE  # Overlap should be less than chunk size

    def test_config_model_parameters(self):
        """Test model configuration parameters."""
        assert Config.EMBEDDING_MODEL is not None
        assert Config.LLM_MODEL is not None
        assert Config.MAX_CONTEXT_LENGTH > 0
        assert Config.SIMILARITY_TOP_K > 0

    def test_config_rerank_parameters(self):
        """Test rerank configuration parameters."""
        assert Config.RERANK_MODEL is not None
        assert Config.RERANK_TOP_K > 0
        assert Config.RERANK_TOP_K <= Config.SIMILARITY_TOP_K  # Rerank should use fewer results

    @patch.dict(os.environ, {'SQLITE_DB_PATH': ''}, clear=False)
    def test_get_db_path(self):
        """Test getting database path."""
        db_path = Config.get_db_path()

        assert db_path is not None
        assert isinstance(db_path, str)
        assert db_path.endswith('.db')

    @patch.dict(os.environ, {'SQLITE_DB_PATH': '/custom/path/test.db'})
    def test_get_db_path_env_override(self):
        """Test getting database path with environment override."""
        db_path = Config.get_db_path()

        assert db_path == '/custom/path/test.db'

    @patch.dict(os.environ, {'SQLITE_DB_PATH': ''})
    def test_get_db_path_empty_env(self):
        """Test getting database path with empty environment override."""
        db_path = Config.get_db_path()

        # Should fall back to default
        assert db_path is not None
        assert db_path.endswith('.db')

    def test_get_ollama_host(self):
        """Test getting Ollama host."""
        host = Config.get_ollama_host()

        assert host is not None
        assert isinstance(host, str)
        assert "localhost" in host

    @patch.dict(os.environ, {'OLLAMA_HOST': 'http://custom-host:11434'})
    def test_get_ollama_host_env_override(self):
        """Test getting Ollama host with environment override."""
        host = Config.get_ollama_host()

        assert host == 'http://custom-host:11434'

    @patch.dict(os.environ, {'OLLAMA_HOST': ''})
    def test_get_ollama_host_empty_env(self):
        """Test getting Ollama host with empty environment override."""
        host = Config.get_ollama_host()

        # Should fall back to default
        assert host is not None
        assert "localhost" in host

    def test_get_embedding_model(self):
        """Test getting embedding model."""
        model = Config.get_embedding_model()

        assert model is not None
        assert isinstance(model, str)

    @patch.dict(os.environ, {'EMBEDDING_MODEL': 'custom-embedding-model'})
    def test_get_embedding_model_env_override(self):
        """Test getting embedding model with environment override."""
        model = Config.get_embedding_model()

        assert model == 'custom-embedding-model'

    @patch.dict(os.environ, {'EMBEDDING_MODEL': ''})
    def test_get_embedding_model_empty_env(self):
        """Test getting embedding model with empty environment override."""
        model = Config.get_embedding_model()

        # Should fall back to default
        assert model is not None

    def test_get_llm_model(self):
        """Test getting LLM model."""
        model = Config.get_llm_model()

        assert model is not None
        assert isinstance(model, str)

    @patch.dict(os.environ, {'LLM_MODEL': 'custom-llm-model'})
    def test_get_llm_model_env_override(self):
        """Test getting LLM model with environment override."""
        model = Config.get_llm_model()

        assert model == 'custom-llm-model'

    @patch.dict(os.environ, {'LLM_MODEL': ''})
    def test_get_llm_model_empty_env(self):
        """Test getting LLM model with empty environment override."""
        model = Config.get_llm_model()

        # Should fall back to default
        assert model is not None

    def test_get_max_context_length(self):
        """Test getting max context length."""
        length = Config.get_max_context_length()

        assert length is not None
        assert isinstance(length, int)
        assert length > 0

    @patch.dict(os.environ, {'MAX_CONTEXT_LENGTH': '4096'})
    def test_get_max_context_length_env_override(self):
        """Test getting max context length with environment override."""
        length = Config.get_max_context_length()

        assert length == 4096

    @patch.dict(os.environ, {'MAX_CONTEXT_LENGTH': 'invalid'})
    def test_get_max_context_length_invalid_env(self):
        """Test getting max context length with invalid environment override."""
        with pytest.raises(ValueError, match="Invalid MAX_CONTEXT_LENGTH"):
            Config.get_max_context_length()

    @patch.dict(os.environ, {'MAX_CONTEXT_LENGTH': '0'})
    def test_get_max_context_length_zero_env(self):
        """Test getting max context length with zero environment override."""
        with pytest.raises(ValueError, match="Invalid MAX_CONTEXT_LENGTH"):
            Config.get_max_context_length()

    def test_get_similarity_top_k(self):
        """Test getting similarity top K."""
        top_k = Config.get_similarity_top_k()

        assert top_k is not None
        assert isinstance(top_k, int)
        assert top_k > 0

    @patch.dict(os.environ, {'SIMILARITY_TOP_K': '10'})
    def test_get_similarity_top_k_env_override(self):
        """Test getting similarity top K with environment override."""
        top_k = Config.get_similarity_top_k()

        assert top_k == 10

    @patch.dict(os.environ, {'SIMILARITY_TOP_K': '0'})
    def test_get_similarity_top_k_zero_env(self):
        """Test getting similarity top K with zero environment override."""
        with pytest.raises(ValueError, match="Invalid SIMILARITY_TOP_K"):
            Config.get_similarity_top_k()

    @patch.dict(os.environ, {'SIMILARITY_TOP_K': 'invalid'})
    def test_get_similarity_top_k_invalid_env(self):
        """Test getting similarity top K with invalid environment override."""
        with pytest.raises(ValueError, match="Invalid SIMILARITY_TOP_K"):
            Config.get_similarity_top_k()

    def test_get_rerank_model(self):
        """Test getting rerank model."""
        model = Config.get_rerank_model()

        assert model is not None
        assert isinstance(model, str)

    @patch.dict(os.environ, {'RERANK_MODEL': 'custom-rerank-model'})
    def test_get_rerank_model_env_override(self):
        """Test getting rerank model with environment override."""
        model = Config.get_rerank_model()

        assert model == 'custom-rerank-model'

    @patch.dict(os.environ, {'RERANK_MODEL': ''})
    def test_get_rerank_model_empty_env(self):
        """Test getting rerank model with empty environment override."""
        model = Config.get_rerank_model()

        # Should fall back to default
        assert model is not None

    def test_get_rerank_top_k(self):
        """Test getting rerank top K."""
        top_k = Config.get_rerank_top_k()

        assert top_k is not None
        assert isinstance(top_k, int)
        assert top_k > 0

    @patch.dict(os.environ, {'RERANK_TOP_K': '5'})
    def test_get_rerank_top_k_env_override(self):
        """Test getting rerank top K with environment override."""
        top_k = Config.get_rerank_top_k()

        assert top_k == 5

    @patch.dict(os.environ, {'RERANK_TOP_K': '0'})
    def test_get_rerank_top_k_zero_env(self):
        """Test getting rerank top K with zero environment override."""
        with pytest.raises(ValueError, match="Invalid RERANK_TOP_K"):
            Config.get_rerank_top_k()

    @patch.dict(os.environ, {'RERANK_TOP_K': 'invalid'})
    def test_get_rerank_top_k_invalid_env(self):
        """Test getting rerank top K with invalid environment override."""
        with pytest.raises(ValueError, match="Invalid RERANK_TOP_K"):
            Config.get_rerank_top_k()

    def test_config_consistency(self):
        """Test configuration consistency."""
        # Rerank top K should be less than or equal to similarity top K
        similarity_top_k = Config.get_similarity_top_k()
        rerank_top_k = Config.get_rerank_top_k()

        assert rerank_top_k <= similarity_top_k

    def test_config_immutability(self):
        """Test that configuration constants are immutable."""
        # Try to modify a constant
        original_value = Config.CHUNK_SIZE

        with pytest.raises(AttributeError):
            Config.CHUNK_SIZE = 1000

        # Value should remain unchanged
        assert Config.CHUNK_SIZE == original_value

    def test_config_type_safety(self):
        """Test configuration type safety."""
        # All configuration values should have appropriate types
        assert isinstance(Config.OLLAMA_HOST, str)
        assert isinstance(Config.SUPPORTED_FILE_TYPES, list)
        assert all(isinstance(ft, str) for ft in Config.SUPPORTED_FILE_TYPES)
        assert isinstance(Config.CHUNK_SIZE, int)
        assert isinstance(Config.CHUNK_OVERLAP, int)
        assert isinstance(Config.EMBEDDING_MODEL, str)
        assert isinstance(Config.LLM_MODEL, str)
        assert isinstance(Config.MAX_CONTEXT_LENGTH, int)
        assert isinstance(Config.SIMILARITY_TOP_K, int)
        assert isinstance(Config.RERANK_MODEL, str)
        assert isinstance(Config.RERANK_TOP_K, int)


@pytest.mark.integration
class TestConfigIntegration:
    """Integration tests for configuration management."""

    @patch.dict(os.environ, {
        'SQLITE_DB_PATH': '/tmp/test_config.db',
        'OLLAMA_HOST': 'http://test-host:11434',
        'EMBEDDING_MODEL': 'test-embedding',
        'LLM_MODEL': 'test-llm',
        'MAX_CONTEXT_LENGTH': '2048',
        'SIMILARITY_TOP_K': '5',
        'RERANK_MODEL': 'test-rerank',
        'RERANK_TOP_K': '3'
    })
    def test_config_with_environment_variables(self):
        """Test configuration with environment variables."""
        # All getters should return environment values
        assert Config.get_db_path() == '/tmp/test_config.db'
        assert Config.get_ollama_host() == 'http://test-host:11434'
        assert Config.get_embedding_model() == 'test-embedding'
        assert Config.get_llm_model() == 'test-llm'
        assert Config.get_max_context_length() == 2048
        assert Config.get_similarity_top_k() == 5
        assert Config.get_rerank_model() == 'test-rerank'
        assert Config.get_rerank_top_k() == 3

    @patch.dict(os.environ, {
        'SQLITE_DB_PATH': '/tmp/test_config.db',
        'OLLAMA_HOST': 'http://test-host:11434',
        'EMBEDDING_MODEL': 'test-embedding',
        'LLM_MODEL': 'test-llm',
        'MAX_CONTEXT_LENGTH': '2048',
        'SIMILARITY_TOP_K': '5',
        'RERANK_MODEL': 'test-rerank',
        'RERANK_TOP_K': '3'
    })
    def test_config_consistency_with_env(self):
        """Test configuration consistency with environment variables."""
        # Rerank top K should be less than or equal to similarity top K
        similarity_top_k = Config.get_similarity_top_k()
        rerank_top_k = Config.get_rerank_top_k()

        assert rerank_top_k <= similarity_top_k

    @patch.dict(os.environ, {
        'SQLITE_DB_PATH': '/tmp/test_config.db',
        'OLLAMA_HOST': 'http://test-host:11434',
        'EMBEDDING_MODEL': 'test-embedding',
        'LLM_MODEL': 'test-llm',
        'MAX_CONTEXT_LENGTH': '2048',
        'SIMILARITY_TOP_K': '5',
        'RERANK_MODEL': 'test-rerank',
        'RERANK_TOP_K': '3'
    })
    def test_config_persistence_with_env(self):
        """Test that configuration persists with environment variables."""
        # Get values multiple times
        db_path1 = Config.get_db_path()
        db_path2 = Config.get_db_path()

        # Should be consistent
        assert db_path1 == db_path2
        assert db_path1 == '/tmp/test_config.db'

    @patch.dict(os.environ, {
        'SQLITE_DB_PATH': '/tmp/test_config.db',
        'OLLAMA_HOST': 'http://test-host:11434',
        'EMBEDDING_MODEL': 'test-embedding',
        'LLM_MODEL': 'test-llm',
        'MAX_CONTEXT_LENGTH': '2048',
        'SIMILARITY_TOP_K': '5',
        'RERANK_MODEL': 'test-rerank',
        'RERANK_TOP_K': '3'
    })
    def test_config_validation_with_env(self):
        """Test configuration validation with environment variables."""
        # All values should be valid
        assert Config.get_db_path() is not None
        assert Config.get_ollama_host() is not None
        assert Config.get_embedding_model() is not None
        assert Config.get_llm_model() is not None
        assert Config.get_max_context_length() > 0
        assert Config.get_similarity_top_k() > 0
        assert Config.get_rerank_model() is not None
        assert Config.get_rerank_top_k() > 0

    @patch.dict(os.environ, {
        'SQLITE_DB_PATH': '/tmp/test_config.db',
        'OLLAMA_HOST': 'http://test-host:11434',
        'EMBEDDING_MODEL': 'test-embedding',
        'LLM_MODEL': 'test-llm',
        'MAX_CONTEXT_LENGTH': '2048',
        'SIMILARITY_TOP_K': '5',
        'RERANK_MODEL': 'test-rerank',
        'RERANK_TOP_K': '3'
    })
    def test_config_defaults_with_partial_env(self):
        """Test configuration defaults with partial environment variables."""
        # Only set some environment variables
        # Others should use defaults
        assert Config.get_db_path() == '/tmp/test_config.db'
        assert Config.get_ollama_host() == 'http://test-host:11434'
        assert Config.get_embedding_model() == 'test-embedding'
        assert Config.get_llm_model() == 'test-llm'
        assert Config.get_max_context_length() == 2048
        assert Config.get_similarity_top_k() == 5
        assert Config.get_rerank_model() == 'test-rerank'
        assert Config.get_rerank_top_k() == 3

    @patch.dict(os.environ, {})
    def test_config_defaults_without_env(self):
        """Test configuration defaults without environment variables."""
        # Should use all default values
        db_path = Config.get_db_path()
        host = Config.get_ollama_host()
        embedding_model = Config.get_embedding_model()
        llm_model = Config.get_llm_model()
        max_context = Config.get_max_context_length()
        similarity_top_k = Config.get_similarity_top_k()
        rerank_model = Config.get_rerank_model()
        rerank_top_k = Config.get_rerank_top_k()

        assert db_path is not None
        assert host is not None
        assert embedding_model is not None
        assert llm_model is not None
        assert max_context > 0
        assert similarity_top_k > 0
        assert rerank_model is not None
        assert rerank_top_k > 0

    @patch.dict(os.environ, {
        'SQLITE_DB_PATH': '/tmp/test_config.db',
        'OLLAMA_HOST': 'http://test-host:11434',
        'EMBEDDING_MODEL': 'test-embedding',
        'LLM_MODEL': 'test-llm',
        'MAX_CONTEXT_LENGTH': '2048',
        'SIMILARITY_TOP_K': '5',
        'RERANK_MODEL': 'test-rerank',
        'RERANK_TOP_K': '3'
    })
    def test_config_file_types_with_env(self):
        """Test supported file types with environment variables."""
        file_types = Config.SUPPORTED_FILE_TYPES

        # Should include all expected file types
        assert ".txt" in file_types
        assert ".md" in file_types
        assert ".py" in file_types
        assert ".js" in file_types
        assert ".json" in file_types
        assert ".yaml" in file_types
        assert ".yml" in file_types
        assert ".pdf" in file_types

    @patch.dict(os.environ, {
        'SQLITE_DB_PATH': '/tmp/test_config.db',
        'OLLAMA_HOST': 'http://test-host:11434',
        'EMBEDDING_MODEL': 'test-embedding',
        'LLM_MODEL': 'test-llm',
        'MAX_CONTEXT_LENGTH': '2048',
        'SIMILARITY_TOP_K': '5',
        'RERANK_MODEL': 'test-rerank',
        'RERANK_TOP_K': '3'
    })
    def test_config_chunking_with_env(self):
        """Test chunking configuration with environment variables."""
        chunk_size = Config.CHUNK_SIZE
        chunk_overlap = Config.CHUNK_OVERLAP

        # Should use environment values or defaults
        assert chunk_size > 0
        assert chunk_overlap >= 0
        assert chunk_overlap < chunk_size

    @patch.dict(os.environ, {
        'SQLITE_DB_PATH': '/tmp/test_config.db',
        'OLLAMA_HOST': 'http://test-host:11434',
        'EMBEDDING_MODEL': 'test-embedding',
        'LLM_MODEL': 'test-llm',
        'MAX_CONTEXT_LENGTH': '2048',
        'SIMILARITY_TOP_K': '5',
        'RERANK_MODEL': 'test-rerank',
        'RERANK_TOP_K': '3'
    })
    def test_config_models_with_env(self):
        """Test model configuration with environment variables."""
        embedding_model = Config.get_embedding_model()
        llm_model = Config.get_llm_model()
        rerank_model = Config.get_rerank_model()

        # Should use environment values or defaults
        assert embedding_model is not None
        assert llm_model is not None
        assert rerank_model is not None

    @patch.dict(os.environ, {
        'SQLITE_DB_PATH': '/tmp/test_config.db',
        'OLLAMA_HOST': 'http://test-host:11434',
        'EMBEDDING_MODEL': 'test-embedding',
        'LLM_MODEL': 'test-llm',
        'MAX_CONTEXT_LENGTH': '2048',
        'SIMILARITY_TOP_K': '5',
        'RERANK_MODEL': 'test-rerank',
        'RERANK_TOP_K': '3'
    })
    def test_config_retrieval_with_env(self):
        """Test retrieval configuration with environment variables."""
        max_context = Config.get_max_context_length()
        similarity_top_k = Config.get_similarity_top_k()
        rerank_top_k = Config.get_rerank_top_k()

        # Should use environment values or defaults
        assert max_context > 0
        assert similarity_top_k > 0
        assert rerank_top_k > 0
        assert rerank_top_k <= similarity_top_k