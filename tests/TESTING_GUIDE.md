# Claude OS Testing Guide

## 🎯 Overview

This guide provides comprehensive information about testing Claude OS, a production-grade RAG system.

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [CI/CD Integration](#cicd-integration)
6. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.11+** with pytest
2. **Ollama** running locally (for integration tests)

### Run All Tests

```bash
./scripts/run_tests.sh
```

That's it! The script will:
- ✅ Check dependencies
- ✅ Create test database if needed
- ✅ Run all tests
- ✅ Show coverage report

---

## 📁 Test Structure

```
tests/
├── __init__.py                 # Test package
├── conftest.py                 # Shared fixtures
├── pytest.ini                  # Pytest configuration
├── README.md                   # Quick reference
├── TEST_COVERAGE.md            # Coverage details
├── TESTING_GUIDE.md            # This file
│
├── test_pg_vector.py           # Vector operations
├── test_rag_engine.py          # RAG engine
├── test_embeddings.py          # Embedding generation
├── test_document_processing.py # Document ingestion
├── test_api.py                 # API endpoints
└── test_pg_manager.py          # Database operations
```

### Test Categories

| Category | Marker | Description |
|----------|--------|-------------|
| Unit | `@pytest.mark.unit` | Fast, isolated tests |
| Integration | `@pytest.mark.integration` | Tests with external services |
| Vector | `@pytest.mark.vector` | Vector operations |
| RAG | `@pytest.mark.rag` | RAG engine tests |
| API | `@pytest.mark.api` | API endpoint tests |
| Embeddings | `@pytest.mark.embeddings` | Embedding generation |
| Slow | `@pytest.mark.slow` | Tests >5 seconds |

---

## 🏃 Running Tests

### Basic Commands

```bash
# All tests
./scripts/run_tests.sh

# With coverage report
./scripts/run_tests.sh --coverage

# Verbose output
./scripts/run_tests.sh --verbose
```

### By Category

```bash
# Unit tests only (fast)
./scripts/run_tests.sh --unit

# Integration tests
./scripts/run_tests.sh --integration

# Vector operations
./scripts/run_tests.sh --vector

# RAG engine
./scripts/run_tests.sh --rag

# API endpoints
./scripts/run_tests.sh --api
```

### Advanced Usage

```bash
# Specific test file
pytest tests/test_pg_vector.py

# Specific test function
pytest tests/test_pg_vector.py::TestPGVectorOperations::test_vector_storage

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Run tests matching pattern
pytest -k "vector"
```

---

## ✍️ Writing Tests

### Test Template

```python
"""
Tests for [component name].
"""

import pytest


@pytest.mark.unit  # or integration, vector, etc.
class TestMyComponent:
    """Test [component] functionality."""
    
    def test_basic_functionality(self, sample_kb, clean_db):
        """Test that [feature] works correctly."""
        # Arrange
        input_data = "test input"
        
        # Act
        result = my_function(input_data)
        
        # Assert
        assert result == expected_output
        assert result.status == "success"
```

### Using Fixtures

```python
def test_with_fixtures(self, sample_kb, sample_documents, clean_db):
    """Test using multiple fixtures."""
    # sample_kb: Pre-created knowledge base
    # sample_documents: 5 documents with embeddings
    # clean_db: Clean database connection
    
    result = query_kb(sample_kb["name"], "test query")
    assert len(result["sources"]) > 0
```

### Mocking External Services

```python
from unittest.mock import patch, MagicMock

@patch('app.core.rag_engine.Ollama')
def test_with_mock_llm(self, mock_llm):
    """Test with mocked LLM."""
    # Setup mock
    mock_instance = MagicMock()
    mock_instance.chat.return_value.message.content = "Test response"
    mock_llm.return_value = mock_instance
    
    # Test
    result = my_function()
    assert result == "Test response"
```

### Best Practices

1. **One assertion per test** (when possible)
2. **Descriptive test names** (`test_vector_similarity_with_empty_kb`)
3. **Use fixtures** for common setup
4. **Mock external services** in unit tests
5. **Test edge cases** (empty input, invalid data, etc.)
6. **Clean up after tests** (use fixtures with cleanup)

---

## 🔄 CI/CD Integration

### GitHub Actions

Tests run automatically on:
- ✅ Push to `main` or `develop`
- ✅ Pull requests
- ✅ Manual workflow dispatch

See `.github/workflows/tests.yml` for configuration.

### Local Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
./scripts/run_tests.sh --unit
if [ $? -ne 0 ]; then
    echo "Tests failed! Commit aborted."
    exit 1
fi
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## 🐛 Troubleshooting

### Ollama Connection Errors

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

### Import Errors

```bash
# Ensure you're in project root
cd /path/to/claude-os

# Install dependencies
pip install -r requirements.txt
```

### Fixture Not Found

Make sure `conftest.py` is in the `tests/` directory and contains the fixture definition.

### Test Database Pollution

```bash
# Drop and recreate test database
dropdb codeforge_test
createdb codeforge_test
psql -d codeforge_test -c "CREATE EXTENSION vector"
psql -d codeforge_test -f app/core/schema.sql
```

---

## 📊 Coverage Reports

### Generate HTML Report

```bash
./scripts/run_tests.sh --coverage
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Goals

- **Overall**: 85%
- **Critical paths**: 90%+
- **New code**: 80%+

---

## 🎓 Learning Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development)

---

## 📝 Checklist for New Features

- [ ] Write tests first (TDD)
- [ ] Use appropriate markers
- [ ] Add fixtures if reusable
- [ ] Test happy path
- [ ] Test edge cases
- [ ] Test error handling
- [ ] Run `./scripts/run_tests.sh`
- [ ] Verify >80% coverage
- [ ] Update documentation

---

> **Remember**: Good tests are the foundation of reliable software! 🚀

