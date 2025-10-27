# Claude OS Test Suite

Comprehensive tests for the Claude OS RAG system.

## Setup

1. **Install test dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create test database:**
   ```bash
   createdb codeforge_test
   psql -d codeforge_test -c "CREATE EXTENSION vector"
   ```

3. **Set environment variables (optional):**
   ```bash
   export TEST_POSTGRES_HOST=localhost
   export TEST_POSTGRES_PORT=5432
   export TEST_POSTGRES_DB=codeforge_test
   export TEST_POSTGRES_USER=$USER
   export TEST_OLLAMA_HOST=http://localhost:11434
   ```

## Running Tests

### Run all tests:
```bash
pytest
```

### Run specific test categories:
```bash
# Unit tests only (fast, no external dependencies)
pytest -m unit

# Integration tests (require database, Ollama)
pytest -m integration

# Vector operation tests
pytest -m vector

# RAG engine tests
pytest -m rag

# API endpoint tests
pytest -m api
```

### Run specific test files:
```bash
pytest tests/test_pg_vector.py
pytest tests/test_rag_engine.py
pytest tests/test_api.py
```

### Run with coverage:
```bash
pytest --cov=app --cov-report=html
# Open htmlcov/index.html to view coverage report
```

### Run with verbose output:
```bash
pytest -v
```

### Run and stop on first failure:
```bash
pytest -x
```

## Test Structure

- **`conftest.py`** - Shared fixtures and configuration
- **`test_pg_vector.py`** - PostgreSQL vector operations
- **`test_rag_engine.py`** - RAG engine functionality
- **`test_embeddings.py`** - Embedding generation
- **`test_document_processing.py`** - Document ingestion and chunking
- **`test_api.py`** - FastAPI endpoints

## Test Markers

Tests are categorized with markers:

- `@pytest.mark.unit` - Fast unit tests, no external dependencies
- `@pytest.mark.integration` - Integration tests requiring database/Ollama
- `@pytest.mark.slow` - Tests that may take several seconds
- `@pytest.mark.embeddings` - Tests involving embedding generation
- `@pytest.mark.vector` - Tests involving vector operations
- `@pytest.mark.rag` - Tests involving RAG engine
- `@pytest.mark.api` - Tests involving API endpoints

## Fixtures

Common fixtures available in all tests:

- `test_db_config` - Database configuration
- `db_connection` - Test database connection (session-scoped)
- `clean_db` - Clean database before each test
- `sample_kb` - Sample knowledge base
- `sample_embedding` - Sample 768-dimensional embedding
- `sample_documents` - Sample documents with embeddings
- `mock_ollama_embedding` - Mock Ollama embedding model
- `mock_ollama_llm` - Mock Ollama LLM
- `sample_text_file` - Sample text file
- `sample_pdf_file` - Sample PDF file
- `sample_markdown_file` - Sample Markdown file
- `api_client` - FastAPI test client

## CI/CD Integration

Tests can be run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pytest --cov=app --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Troubleshooting

### Database connection errors:
- Ensure PostgreSQL is running
- Verify test database exists: `psql -l | grep codeforge_test`
- Check environment variables

### Ollama connection errors:
- Ensure Ollama is running: `curl http://localhost:11434/api/tags`
- Check TEST_OLLAMA_HOST environment variable

### Import errors:
- Ensure you're in the project root directory
- Install all dependencies: `pip install -r requirements.txt`

