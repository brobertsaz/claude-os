"""
Pytest configuration and shared fixtures for Claude OS tests.
"""

import os
import pytest
import psycopg2
from typing import Generator, Dict, Any
from unittest.mock import Mock, MagicMock
import numpy as np

# Set test environment variables
os.environ["POSTGRES_HOST"] = os.getenv("TEST_POSTGRES_HOST", "localhost")
os.environ["POSTGRES_PORT"] = os.getenv("TEST_POSTGRES_PORT", "5432")
os.environ["POSTGRES_DB"] = os.getenv("TEST_POSTGRES_DB", "codeforge_test")
os.environ["POSTGRES_USER"] = os.getenv("TEST_POSTGRES_USER", os.getenv("USER", "postgres"))
os.environ["OLLAMA_HOST"] = os.getenv("TEST_OLLAMA_HOST", "http://localhost:11434")


@pytest.fixture(scope="session")
def test_db_config() -> Dict[str, str]:
    """Database configuration for tests."""
    return {
        "host": os.getenv("POSTGRES_HOST"),
        "port": int(os.getenv("POSTGRES_PORT")),
        "database": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
    }


@pytest.fixture(scope="session")
def db_connection(test_db_config):
    """
    Create a test database connection.
    This is a session-scoped fixture that creates the test database once.
    """
    # Connect to default postgres database to create test database
    conn = psycopg2.connect(
        host=test_db_config["host"],
        port=test_db_config["port"],
        database="postgres",
        user=test_db_config["user"],
    )
    conn.autocommit = True

    with conn.cursor() as cur:
        # Drop and recreate test database
        cur.execute(f"DROP DATABASE IF EXISTS {test_db_config['database']}")
        cur.execute(f"CREATE DATABASE {test_db_config['database']}")

    conn.close()

    # Connect to test database
    test_conn = psycopg2.connect(**test_db_config)

    # Create pgvector extension
    with test_conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
    test_conn.commit()

    # Load schema
    with open("app/core/schema_pgvector.sql", "r") as f:
        schema_sql = f.read()

    with test_conn.cursor() as cur:
        cur.execute(schema_sql)
    test_conn.commit()

    yield test_conn

    # Cleanup
    test_conn.close()

    # Drop test database
    conn = psycopg2.connect(
        host=test_db_config["host"],
        port=test_db_config["port"],
        database="postgres",
        user=test_db_config["user"],
    )
    conn.autocommit = True

    with conn.cursor() as cur:
        cur.execute(f"DROP DATABASE IF EXISTS {test_db_config['database']}")

    conn.close()


@pytest.fixture
def clean_db(db_connection):
    """
    Clean database before each test.
    This is a function-scoped fixture that cleans tables before each test.
    Works with NEW PGVectorStore schema (data_{kb_name} tables).
    """
    with db_connection.cursor() as cur:
        # Get all KB table names
        cur.execute("SELECT table_name FROM knowledge_bases WHERE table_name IS NOT NULL")
        kb_tables = cur.fetchall()

        # Truncate each KB data table
        for (table_name,) in kb_tables:
            try:
                cur.execute(f"TRUNCATE TABLE {table_name} CASCADE")
            except Exception:
                # Table might not exist, skip it
                pass

        # Truncate knowledge_bases table
        cur.execute("TRUNCATE TABLE knowledge_bases CASCADE")
    db_connection.commit()

    yield db_connection


@pytest.fixture
def sample_kb(clean_db):
    """Create a sample knowledge base for testing with NEW PGVectorStore schema."""
    import json

    table_name = "data_test_kb"
    embed_dim = 768

    with clean_db.cursor() as cur:
        # Insert KB metadata with NEW schema columns
        # Note: metadata must be JSON string, not dict
        cur.execute(
            """
            INSERT INTO knowledge_bases (name, kb_type, description, metadata, table_name, embed_dim)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            ("test_kb", "GENERIC", "Test knowledge base", json.dumps({}), table_name, embed_dim)
        )
        kb_id = cur.fetchone()[0]

        # Create the actual data table using helper function
        cur.execute("SELECT create_kb_table(%s, %s, %s)", ("test_kb", table_name, embed_dim))

    clean_db.commit()

    return {
        "id": kb_id,
        "name": "test_kb",
        "kb_type": "GENERIC",
        "table_name": table_name,
        "embed_dim": embed_dim
    }


@pytest.fixture
def sample_embedding() -> list:
    """Generate a sample 768-dimensional embedding."""
    np.random.seed(42)  # For reproducibility
    return np.random.randn(768).tolist()


@pytest.fixture
def sample_documents(sample_kb, sample_embedding, clean_db):
    """Create sample documents with embeddings in NEW PGVectorStore schema."""
    import json

    documents = []
    table_name = sample_kb["table_name"]  # Should be 'data_test_kb'

    for i in range(5):
        # Generate slightly different embeddings
        np.random.seed(42 + i)
        embedding = np.random.randn(768).tolist()
        node_id = f"node_doc_{i}"
        text_content = f"This is test document {i} with some content about testing."
        metadata = {"filename": f"test_{i}.txt", "chunk_index": i}

        with clean_db.cursor() as cur:
            # Insert into data_test_kb table with NEW schema columns
            # Note: metadata_ is JSON type, needs JSON string
            cur.execute(
                f"""
                INSERT INTO {table_name} (text, metadata_, node_id, embedding)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (text_content, json.dumps(metadata), node_id, embedding)
            )
            doc_id = cur.fetchone()[0]

        documents.append({
            "id": doc_id,
            "node_id": node_id,
            "text": text_content,
            "metadata": metadata,
            "embedding": embedding
        })

    clean_db.commit()

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

