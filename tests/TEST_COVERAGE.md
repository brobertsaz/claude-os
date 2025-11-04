# Claude OS Test Coverage

## Overview

Comprehensive test suite for Claude OS RAG system covering all critical components.

## Test Files

### 1. `test_rag_engine.py` - RAG Engine
**Purpose**: Test RAG query execution and response generation

**Tests**:
- ✅ RAG engine initialization
- ✅ Query with no documents (empty KB)
- ✅ Query with documents (full pipeline)
- ✅ LLM integration
- ✅ Source retrieval and formatting

**Coverage**: End-to-end RAG pipeline, LLM integration, context retrieval

---

### 3. `test_embeddings.py` - Embedding Generation
**Purpose**: Test embedding model and vector operations

**Tests**:
- ✅ Ollama embedding generation
- ✅ Embedding consistency (same text → same embedding)
- ✅ Embedding dimension validation (768)
- ✅ Variable text length handling
- ✅ Cosine similarity calculation
- ✅ Vector normalization

**Coverage**: Embedding generation, vector math, model consistency

---

### 4. `test_document_processing.py` - Document Ingestion
**Purpose**: Test document processing and chunking

**Tests**:
- ✅ Text file ingestion
- ✅ PDF file ingestion
- ✅ Markdown file ingestion
- ✅ Fixed-size chunking
- ✅ Sentence-based chunking
- ✅ File type detection

**Coverage**: Document parsing, chunking strategies, file handling

---

### 5. `test_api.py` - FastAPI Endpoints
**Purpose**: Test all API endpoints

**Tests**:
- ✅ List knowledge bases
- ✅ Create knowledge base
- ✅ Delete knowledge base
- ✅ Get KB statistics
- ✅ List documents
- ✅ Chat endpoint (query)
- ✅ Chat with empty KB
- ✅ Chat with invalid KB
- ✅ Health check endpoint
- ✅ Document upload (text files)
- ✅ Invalid file type handling

**Coverage**: API endpoints, request/response validation, error handling

---

## Test Categories (Markers)

### Unit Tests (`@pytest.mark.unit`)
- Fast, no external dependencies
- Test individual functions and utilities
- Mock external services

### Integration Tests (`@pytest.mark.integration`)
- Require database and/or Ollama
- Test component interactions
- Use real services

### Specific Markers
- `@pytest.mark.vector` - Vector operations
- `@pytest.mark.rag` - RAG engine tests
- `@pytest.mark.api` - API endpoint tests
- `@pytest.mark.embeddings` - Embedding generation
- `@pytest.mark.slow` - Tests that take >5 seconds

---

## Running Tests

### All tests:
```bash
./scripts/run_tests.sh
```

### Unit tests only (fast):
```bash
./scripts/run_tests.sh --unit
```

### Integration tests:
```bash
./scripts/run_tests.sh --integration
```

### Specific category:
```bash
./scripts/run_tests.sh --vector
./scripts/run_tests.sh --rag
./scripts/run_tests.sh --api
```

### With coverage:
```bash
./scripts/run_tests.sh --coverage
```

---

## Test Fixtures

### Database Fixtures
- `test_db_config` - Test database configuration
- `db_connection` - Session-scoped database connection
- `clean_db` - Clean database before each test
- `sample_kb` - Sample knowledge base
- `sample_documents` - Sample documents with embeddings

### Data Fixtures
- `sample_embedding` - 768-dimensional embedding
- `sample_text_file` - Sample text file
- `sample_pdf_file` - Sample PDF file
- `sample_markdown_file` - Sample Markdown file

### Mock Fixtures
- `mock_ollama_embedding` - Mock embedding model
- `mock_ollama_llm` - Mock LLM
- `api_client` - FastAPI test client

---

## Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| PostgreSQL Manager | 90% | TBD |
| RAG Engine | 85% | TBD |
| Document Processing | 80% | TBD |
| API Endpoints | 90% | TBD |
| Embeddings | 85% | TBD |
| **Overall** | **85%** | **TBD** |

---

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run tests
  run: |
    pytest --cov=app --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

---

## Known Issues / TODO

- [ ] Add performance benchmarks
- [ ] Add stress tests for concurrent queries
- [ ] Add tests for different chunking strategies
- [ ] Add tests for hybrid search (BM25 + vector)
- [ ] Add tests for reranking
- [ ] Add tests for different LLM models
- [ ] Add tests for error recovery
- [ ] Add tests for rate limiting

---

## Contributing

When adding new features:

1. **Write tests first** (TDD approach)
2. **Use appropriate markers** (`@pytest.mark.unit`, etc.)
3. **Add fixtures** to `conftest.py` if reusable
4. **Update this document** with new test coverage
5. **Ensure >80% coverage** for new code

---

## Test Data

Test data is generated using:
- **Faker** - For realistic test data
- **NumPy** - For random embeddings (seeded for reproducibility)
- **Fixtures** - For consistent test scenarios

All test data is isolated and cleaned up after tests.

