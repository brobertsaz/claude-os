# Testing Guide for Claude OS

This document provides comprehensive information about testing the Claude OS application.

## Test Structure

The test suite is organized into the following structure:

```
tests/
├── conftest.py                 # Pytest configuration and fixtures
├── test_api.py                 # API endpoint tests
├── test_document_processing.py  # Document processing tests
├── test_embeddings.py           # Embedding generation tests
├── test_rag_engine.py          # Basic RAG engine tests
├── test_sqlite_manager.py      # Database operations tests
├── test_rag_engine_comprehensive.py  # Comprehensive RAG engine tests
├── test_ingestion_comprehensive.py  # Document ingestion tests
├── test_agent_os.py            # Agent OS parser and ingestion tests
├── test_conversation_watcher.py  # Conversation monitoring tests
├── test_file_watcher.py         # File system monitoring tests
├── test_hooks.py               # Project hooks tests
├── test_health.py              # Health check tests
├── test_kb_metadata.py          # Knowledge base metadata tests
├── test_learning_jobs.py        # Learning job processing tests
├── test_markdown_preprocessor.py # Markdown preprocessing tests
├── test_redis_config.py        # Redis configuration tests
├── test_config.py              # Configuration management tests
└── TEST_COVERAGE.md           # Test coverage documentation
```

## Running Tests

### Prerequisites

Before running tests, ensure you have the following installed:

```bash
pip install pytest pytest-cov pytest-mock
```

### Running All Tests

To run the entire test suite:

```bash
pytest tests/
```

### Running Specific Test Files

To run a specific test file:

```bash
pytest tests/test_sqlite_manager.py
```

### Running Tests by Category

To run tests by category using markers:

```bash
# Unit tests only
pytest -m unit tests/

# Integration tests only
pytest -m integration tests/

# API tests only
pytest -m api tests/

# RAG tests only
pytest -m rag tests/

# Embedding tests only
pytest -m embeddings tests/

# Document processing tests only
pytest -m document_processing tests/
```

### Running Tests with Coverage

To run tests with coverage report:

```bash
pytest --cov=app tests/
```

To generate an HTML coverage report:

```bash
pytest --cov=app --cov-report=html tests/
```

The coverage report will be generated in `htmlcov/` directory.

### Running Tests in Parallel

To run tests in parallel for faster execution:

```bash
pytest -n auto tests/
```

### Running Tests with Verbose Output

To run tests with verbose output:

```bash
pytest -v tests/
```

### Running Tests with Specific Python Version

To run tests with a specific Python version:

```bash
python3.9 -m pytest tests/
```

## Test Fixtures

The test suite uses the following fixtures:

### Database Fixtures

- `clean_db`: Provides a clean database for each test
- `sample_kb`: Creates a sample knowledge base
- `sample_documents`: Creates sample documents with embeddings

### File Fixtures

- `sample_text_file`: Creates a sample text file
- `sample_pdf_file`: Creates a sample PDF file
- `sample_markdown_file`: Creates a sample Markdown file

### API Fixtures

- `api_client`: Provides a test API client

## Test Configuration

### Environment Variables

The following environment variables can be used to configure test behavior:

```bash
# Database path
export SQLITE_DB_PATH=/tmp/test.db

# Ollama configuration
export OLLAMA_HOST=http://localhost:11434

# Embedding model
export EMBEDDING_MODEL=nomic-embed-text

# LLM model
export LLM_MODEL=llama3.1

# Redis configuration
export REDIS_HOST=localhost
export REDIS_PORT=6379
```

### Test Configuration

The test suite can be configured using `pytest.ini` or `pyproject.toml`:

```ini
[tool:pytest]
testpaths = tests
python_files = tests
python_classes = test_*
python_functions = test_*
addopts =
    --strict-markers
    --disable-warnings
    --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    api: API tests
    rag: RAG tests
    embeddings: Embedding tests
    document_processing: Document processing tests
```

## Test Categories

### Unit Tests

Unit tests focus on testing individual components in isolation:

- **SQLite Manager**: Database operations, collections, and queries
- **RAG Engine**: Retrieval, synthesis, and query processing
- **Document Processing**: Text extraction, chunking, and metadata
- **Agent OS**: Profile parsing, content type detection, and ingestion
- **Conversation Watcher**: Trigger detection, confidence scoring, and insight generation
- **File Watcher**: File monitoring, debouncing, and event handling
- **Hooks System**: Hook management, folder synchronization, and error handling
- **Health Checks**: Service monitoring, timeout handling, and status reporting
- **KB Metadata**: Type validation, metadata formatting, and UI display
- **Learning Jobs**: Job processing, user confirmation, and MCP ingestion
- **Markdown Preprocessor**: Frontmatter extraction, header normalization, and content cleaning
- **Redis Configuration**: Connection management, pub/sub, and job queuing
- **Configuration Management**: Environment variables, validation, and defaults

### Integration Tests

Integration tests focus on testing component interactions:

- **API Integration**: End-to-end API testing
- **Database Integration**: Real database operations
- **File System Integration**: Real file operations
- **Service Integration**: Real service connections

### API Tests

API tests focus on testing HTTP endpoints:

- **Knowledge Base API**: CRUD operations for knowledge bases
- **Document API**: Upload, retrieval, and management
- **Chat API**: Query processing and response generation
- **Health API**: Service status and monitoring

## Test Data

### Sample Data

The test suite uses carefully crafted sample data:

- **Documents**: Various file types and content
- **Knowledge Bases**: Different types and configurations
- **Projects**: Different structures and configurations
- **Conversations**: Various trigger patterns and contexts

### Test Scenarios

The test suite covers various scenarios:

- **Happy Paths**: Normal operation scenarios
- **Error Paths**: Exception and error handling
- **Edge Cases**: Boundary conditions and unusual inputs
- **Performance**: Large data sets and complex operations

## Debugging Tests

### Identifying Issues

When a test fails:

1. Check the test output for error messages
2. Examine the traceback for failure location
3. Review the test code for logic errors
4. Check the application code for bugs
5. Verify test data and fixtures

### Common Issues

Common test issues and solutions:

- **Database Locks**: Ensure tests clean up database connections
- **File Permissions**: Ensure tests have appropriate file permissions
- **Service Dependencies**: Ensure required services are running
- **Timing Issues**: Use appropriate waits and timeouts
- **Mock Configuration**: Ensure mocks are properly configured

### Debugging Tools

Use these tools for debugging:

```bash
# Run with debugger
pytest --pdb tests/

# Stop on first failure
pytest -x tests/

# Run with logging
pytest --log-cli-level=DEBUG tests/

# Run with coverage and debugging
pytest --cov=app --cov-report=html --pdb tests/
```

## Continuous Integration

### GitHub Actions

The test suite is designed to run in GitHub Actions:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10]
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-mock
    - name: Run tests
      run: |
        pytest --cov=app --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### Local Development

For local development:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
pytest tests/
```

## Best Practices

### Writing Tests

Follow these best practices when writing tests:

1. **Descriptive Names**: Use clear, descriptive test names
2. **Single Assertion**: Each test should have one primary assertion
3. **Test Isolation**: Tests should not depend on each other
4. **Mock External Dependencies**: Use mocks for external services
5. **Clean Up**: Ensure tests clean up resources
6. **Test Data**: Use realistic but simple test data
7. **Error Testing**: Test both success and failure scenarios

### Test Organization

Organize tests effectively:

1. **Group Related Tests**: Group related tests together
2. **Use Fixtures**: Use fixtures for common setup
3. **Mark Tests**: Use markers for test categorization
4. **Document Tests**: Add clear documentation for complex tests
5. **Avoid Duplication**: Don't duplicate test logic

### Coverage Goals

Aim for these coverage goals:

1. **Line Coverage**: > 80% of code lines
2. **Branch Coverage**: > 80% of code branches
3. **Function Coverage**: > 90% of functions
4. **Component Coverage**: All major components tested

## Troubleshooting

### Common Test Failures

Common test failures and solutions:

1. **Import Errors**: Check import paths and dependencies
2. **Database Errors**: Check database setup and cleanup
3. **Timeout Errors**: Increase timeouts or check performance
4. **Mock Errors**: Verify mock configuration
5. **Assertion Errors**: Check test logic and expected values

### Performance Issues

Performance-related test issues:

1. **Slow Tests**: Optimize test data and algorithms
2. **Memory Leaks**: Ensure proper cleanup
3. **Resource Contention**: Use appropriate isolation
4. **Flaky Tests**: Add proper waits and synchronization

### Environment Issues

Environment-related test issues:

1. **Path Issues**: Use absolute paths and proper joining
2. **Permission Issues**: Check file and directory permissions
3. **Dependency Issues**: Verify all dependencies are installed
4. **Configuration Issues**: Check environment variables and settings

## Contributing

### Adding Tests

To add new tests:

1. **Create Test File**: Add test file in appropriate directory
2. **Follow Conventions**: Use existing test patterns and conventions
3. **Add Fixtures**: Add fixtures for common setup if needed
4. **Update Documentation**: Update test documentation
5. **Run Tests**: Ensure new tests pass

### Test Review Process

Test review process:

1. **Code Review**: All tests go through code review
2. **Test Coverage**: Ensure adequate test coverage
3. **Test Quality**: Verify test quality and maintainability
4. **Documentation**: Ensure test documentation is updated
5. **Integration**: Verify tests work in integration environment

This testing guide provides comprehensive information for testing the Claude OS application. Follow these guidelines to ensure high-quality tests and reliable test execution.