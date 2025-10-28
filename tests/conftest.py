"""
Pytest configuration and shared fixtures for Claude OS tests.
"""

import os
import pytest
import tempfile
import json
from pathlib import Path
from typing import Generator, Dict, Any
from unittest.mock import Mock, MagicMock
import numpy as np

# Set test environment variables (only if not already set)
# Don't override SQLITE_DB_PATH globally - let tests use their own paths
if "SQLITE_DB_PATH" not in os.environ:
    os.environ["SQLITE_DB_PATH"] = os.getenv("TEST_SQLITE_DB_PATH", ":memory:")
os.environ.setdefault("OLLAMA_HOST", "http://localhost:11434")
os.environ.setdefault("EMBEDDING_MODEL", "nomic-embed-text")
os.environ.setdefault("LLM_MODEL", "llama3.1")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")


@pytest.fixture(scope="session")
def test_db_config() -> Dict[str, str]:
    """Database configuration for tests."""
    return {
        "db_path": os.getenv("SQLITE_DB_PATH"),
        "embedding_model": os.getenv("EMBEDDING_MODEL"),
        "llm_model": os.getenv("LLM_MODEL"),
    }


@pytest.fixture
def clean_db():
    """
    Create a clean SQLite database for each test.
    """
    from app.core.sqlite_manager import SQLiteManager

    # Use a temporary file for the test database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        temp_db_path = temp_file.name

    # Create and initialize the database
    manager = SQLiteManager(temp_db_path)

    yield manager

    # Clean up after test
    if Path(temp_db_path).exists():
        Path(temp_db_path).unlink()


@pytest.fixture
def sample_kb(clean_db):
    """Create a sample knowledge base for testing."""
    from app.core.kb_types import KBType

    kb_data = clean_db.create_collection(
        name="test_kb",
        kb_type=KBType.GENERIC,
        description="Test knowledge base"
    )

    return {
        "id": kb_data["id"],
        "name": "test_kb",
        "kb_type": KBType.GENERIC.value,
        "description": "Test knowledge base",
        "metadata": {}
    }


@pytest.fixture
def sample_embedding() -> list:
    """Generate a sample 768-dimensional embedding."""
    np.random.seed(42)  # For reproducibility
    return np.random.randn(768).tolist()


@pytest.fixture
def sample_documents(sample_kb, sample_embedding, clean_db):
    """Create sample documents with embeddings."""
    documents = []

    for i in range(5):
        # Generate slightly different embeddings
        np.random.seed(42 + i)
        embedding = np.random.randn(768).tolist()
        node_id = f"node_doc_{i}"
        text_content = f"This is test document {i} with some content about testing."
        metadata = {"filename": f"test_{i}.txt", "chunk_index": i}

        # Add document to collection
        doc_data = {
            "node_id": node_id,
            "text": text_content,
            "metadata": metadata,
            "embedding": embedding
        }

        # Store the document (implementation depends on SQLiteManager methods)
        # This is a placeholder - adjust based on actual SQLiteManager API
        documents.append(doc_data)

    return documents


@pytest.fixture
def mock_ollama_embedding():
    """Mock Ollama embedding model."""
    mock = MagicMock()
    mock.get_text_embedding.return_value = np.random.randn(768).tolist()
    return mock


@pytest.fixture
def mock_ollama_llm():
    """Mock Ollama LLM."""
    mock = MagicMock()
    mock_response = MagicMock()
    mock_response.message.content = "This is a test response from the LLM."
    mock.chat.return_value = mock_response
    return mock


@pytest.fixture
def sample_text_file(tmp_path):
    """Create a sample text file for testing."""
    file_path = tmp_path / "test_document.txt"
    file_path.write_text("This is a test document.\n\nIt has multiple paragraphs.\n\nFor testing purposes.")
    return file_path


@pytest.fixture
def sample_pdf_file(tmp_path):
    """Create a sample PDF file for testing (requires PyMuPDF)."""
    try:
        import fitz  # PyMuPDF

        file_path = tmp_path / "test_document.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "This is a test PDF document.\n\nIt has multiple paragraphs.\n\nFor testing purposes.")
        doc.save(str(file_path))
        doc.close()

        return file_path
    except ImportError:
        pytest.skip("PyMuPDF not installed")


@pytest.fixture
def sample_markdown_file(tmp_path):
    """Create a sample Markdown file for testing."""
    file_path = tmp_path / "test_document.md"
    content = """# Test Document

This is a test document.

## Section 1

Some content here.

## Section 2

More content here.
"""
    file_path.write_text(content)
    return file_path


@pytest.fixture
def api_client():
    """Create a test client for FastAPI."""
    from fastapi.testclient import TestClient
    from mcp_server.server import app

    return TestClient(app)


# Markers for test categorization
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests (fast, no external dependencies)")
    config.addinivalue_line("markers", "integration: Integration tests (require database, Ollama)")
    config.addinivalue_line("markers", "slow: Slow tests (may take several seconds)")
    config.addinivalue_line("markers", "embeddings: Tests involving embedding generation")
    config.addinivalue_line("markers", "vector: Tests involving vector operations")
    config.addinivalue_line("markers", "rag: Tests involving RAG engine")
    config.addinivalue_line("markers", "api: Tests involving API endpoints")