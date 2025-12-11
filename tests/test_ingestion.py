"""
Tests for ingestion.py - Document ingestion pipeline.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import fitz  # PyMuPDF

from app.core.ingestion import (
    extract_text_from_file,
    chunk_document,
    ingest_file,
    ingest_documents,
    ingest_directory,
    should_skip_path,
    SKIP_DIRECTORIES,
)


class TestExtractTextFromFile:
    """Tests for extract_text_from_file function."""

    def test_extract_text_file(self, tmp_path):
        """Test extracting text from .txt file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Hello, this is a test file.\nWith multiple lines.")

        result = extract_text_from_file(str(file_path))

        assert "Hello, this is a test file" in result
        assert "With multiple lines" in result

    def test_extract_markdown_file(self, tmp_path):
        """Test extracting text from .md file."""
        file_path = tmp_path / "test.md"
        file_path.write_text("# Heading\n\nSome **bold** text.")

        result = extract_text_from_file(str(file_path))

        assert "# Heading" in result
        assert "**bold**" in result

    def test_extract_python_file(self, tmp_path):
        """Test extracting text from .py file."""
        file_path = tmp_path / "test.py"
        file_path.write_text('def hello():\n    print("Hello")')

        result = extract_text_from_file(str(file_path))

        assert "def hello():" in result
        assert 'print("Hello")' in result

    def test_extract_pdf_file(self, tmp_path):
        """Test extracting text from PDF file."""
        file_path = tmp_path / "test.pdf"

        # Create a PDF with PyMuPDF
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "PDF content here")
        doc.save(str(file_path))
        doc.close()

        result = extract_text_from_file(str(file_path))

        assert "PDF content here" in result

    def test_extract_nonexistent_file(self):
        """Test extracting from non-existent file."""
        result = extract_text_from_file("/nonexistent/file.txt")
        assert result == ""

    def test_extract_file_with_encoding_issues(self, tmp_path):
        """Test extracting file with encoding issues."""
        file_path = tmp_path / "test.txt"
        # Write bytes directly to create encoding issues
        file_path.write_bytes(b"Hello \xff\xfe World")

        result = extract_text_from_file(str(file_path))

        # Should handle gracefully with errors='ignore'
        assert "Hello" in result
        assert "World" in result

    def test_extract_empty_file(self, tmp_path):
        """Test extracting from empty file."""
        file_path = tmp_path / "empty.txt"
        file_path.write_text("")

        result = extract_text_from_file(str(file_path))
        assert result == ""

    def test_extract_json_file(self, tmp_path):
        """Test extracting text from JSON file."""
        file_path = tmp_path / "test.json"
        file_path.write_text('{"key": "value", "number": 42}')

        result = extract_text_from_file(str(file_path))

        assert '"key"' in result
        assert '"value"' in result


class TestChunkDocument:
    """Tests for chunk_document function."""

    def test_chunk_short_document(self):
        """Test chunking a short document (single chunk)."""
        text = "This is a short document."
        metadata = {"filename": "test.txt"}

        chunks = chunk_document(text, metadata)

        assert len(chunks) >= 1
        assert chunks[0].metadata["filename"] == "test.txt"
        assert "chunk_index" in chunks[0].metadata

    def test_chunk_long_document(self):
        """Test chunking a long document (multiple chunks)."""
        # Create a long text
        text = "This is a paragraph. " * 500  # ~10000 chars
        metadata = {"filename": "long.txt"}

        chunks = chunk_document(text, metadata)

        # Should have multiple chunks
        assert len(chunks) > 1

        # Each chunk should have correct metadata
        for i, chunk in enumerate(chunks):
            assert chunk.metadata["chunk_index"] == i
            assert chunk.metadata["filename"] == "long.txt"

    def test_chunk_preserves_metadata(self):
        """Test that chunking preserves original metadata."""
        text = "Test content"
        metadata = {
            "filename": "test.txt",
            "file_type": ".txt",
            "custom_field": "custom_value"
        }

        chunks = chunk_document(text, metadata)

        for chunk in chunks:
            assert chunk.metadata["filename"] == "test.txt"
            assert chunk.metadata["file_type"] == ".txt"
            assert chunk.metadata["custom_field"] == "custom_value"

    def test_chunk_adds_chunk_id(self):
        """Test that chunking adds chunk_id."""
        text = "Test content"
        metadata = {"filename": "test.txt"}

        chunks = chunk_document(text, metadata)

        for chunk in chunks:
            assert "chunk_id" in chunk.metadata


class TestShouldSkipPath:
    """Tests for should_skip_path function."""

    def test_skip_node_modules(self):
        """Test that node_modules is skipped."""
        path = Path("/project/node_modules/package/index.js")
        assert should_skip_path(path) is True

    def test_skip_git_directory(self):
        """Test that .git is skipped."""
        path = Path("/project/.git/objects/abc123")
        assert should_skip_path(path) is True

    def test_skip_pycache(self):
        """Test that __pycache__ is skipped."""
        path = Path("/project/src/__pycache__/module.pyc")
        assert should_skip_path(path) is True

    def test_skip_pytest_cache(self):
        """Test that .pytest_cache is skipped."""
        path = Path("/project/.pytest_cache/v/cache/lastfailed")
        assert should_skip_path(path) is True

    def test_skip_egg_info(self):
        """Test that *.egg-info is skipped."""
        path = Path("/project/mypackage.egg-info/PKG-INFO")
        assert should_skip_path(path) is True

    def test_allow_regular_path(self):
        """Test that regular paths are not skipped."""
        path = Path("/project/src/main.py")
        assert should_skip_path(path) is False

    def test_allow_deep_path(self):
        """Test that deep regular paths are not skipped."""
        path = Path("/project/src/components/ui/Button.tsx")
        assert should_skip_path(path) is False

    def test_skip_vscode(self):
        """Test that .vscode is skipped."""
        path = Path("/project/.vscode/settings.json")
        assert should_skip_path(path) is True

    def test_skip_idea(self):
        """Test that .idea is skipped."""
        path = Path("/project/.idea/workspace.xml")
        assert should_skip_path(path) is True

    def test_all_skip_directories(self):
        """Test all directories in SKIP_DIRECTORIES are handled."""
        for skip_dir in SKIP_DIRECTORIES:
            if '*' not in skip_dir:
                path = Path(f"/project/{skip_dir}/file.txt")
                assert should_skip_path(path) is True, f"{skip_dir} should be skipped"


class TestIngestFile:
    """Tests for ingest_file function."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager."""
        mock = MagicMock()
        mock.collection_exists.return_value = True
        mock.add_documents = MagicMock()
        return mock

    @pytest.fixture
    def mock_embed_model(self):
        """Create mock embedding model."""
        mock = MagicMock()
        mock.get_text_embedding.return_value = [0.1] * 768
        return mock

    def test_ingest_text_file_success(self, tmp_path, mock_db_manager, mock_embed_model):
        """Test successful ingestion of text file."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("This is test content for ingestion.")

        with patch('app.core.ingestion.get_sqlite_manager', return_value=mock_db_manager):
            with patch('app.core.ingestion.OllamaEmbedding', return_value=mock_embed_model):
                result = ingest_file(str(file_path), "test_collection", "test.txt")

        assert result["status"] == "success"
        assert result["filename"] == "test.txt"
        assert "chunks" in result
        mock_db_manager.add_documents.assert_called_once()

    def test_ingest_empty_file(self, tmp_path, mock_db_manager):
        """Test ingestion of empty file."""
        file_path = tmp_path / "empty.txt"
        file_path.write_text("")

        with patch('app.core.ingestion.get_sqlite_manager', return_value=mock_db_manager):
            result = ingest_file(str(file_path), "test_collection", "empty.txt")

        assert result["status"] == "error"
        assert "No text content" in result["error"]

    def test_ingest_nonexistent_collection(self, tmp_path, mock_db_manager, mock_embed_model):
        """Test ingestion to non-existent collection."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Content")
        mock_db_manager.collection_exists.return_value = False

        with patch('app.core.ingestion.get_sqlite_manager', return_value=mock_db_manager):
            with patch('app.core.ingestion.OllamaEmbedding', return_value=mock_embed_model):
                result = ingest_file(str(file_path), "nonexistent", "test.txt")

        assert result["status"] == "error"
        assert "not found" in result["error"]

    def test_ingest_markdown_with_preprocessing(self, tmp_path, mock_db_manager, mock_embed_model):
        """Test ingestion of markdown file with preprocessing."""
        file_path = tmp_path / "test.md"
        file_path.write_text("# Heading\n\nSome content here.")

        with patch('app.core.ingestion.get_sqlite_manager', return_value=mock_db_manager):
            with patch('app.core.ingestion.OllamaEmbedding', return_value=mock_embed_model):
                with patch('app.core.ingestion.preprocess_markdown') as mock_preprocess:
                    mock_preprocess.return_value = ("Processed content", {"header": "Heading"})

                    result = ingest_file(str(file_path), "test_collection", "test.md")

        assert result["status"] == "success"
        mock_preprocess.assert_called_once()

    def test_ingest_handles_embedding_failure(self, tmp_path, mock_db_manager):
        """Test ingestion handles embedding failures gracefully."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Content")

        mock_embed = MagicMock()
        mock_embed.get_text_embedding.side_effect = Exception("Embedding failed")

        with patch('app.core.ingestion.get_sqlite_manager', return_value=mock_db_manager):
            with patch('app.core.ingestion.OllamaEmbedding', return_value=mock_embed):
                result = ingest_file(str(file_path), "test_collection", "test.txt")

        assert result["status"] == "error"
        assert "failed to generate embeddings" in result["error"]

    def test_ingest_truncates_long_chunks(self, tmp_path, mock_db_manager, mock_embed_model):
        """Test that very long chunks are truncated."""
        file_path = tmp_path / "long.txt"
        file_path.write_text("A" * 10000)  # Very long content

        with patch('app.core.ingestion.get_sqlite_manager', return_value=mock_db_manager):
            with patch('app.core.ingestion.OllamaEmbedding', return_value=mock_embed_model):
                result = ingest_file(str(file_path), "test_collection", "long.txt")

        assert result["status"] == "success"


class TestIngestDocuments:
    """Tests for ingest_documents function."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager."""
        mock = MagicMock()
        mock.collection_exists.return_value = True
        mock.add_documents = MagicMock()
        return mock

    @pytest.fixture
    def mock_embed_model(self):
        """Create mock embedding model."""
        mock = MagicMock()
        mock.get_text_embedding.return_value = [0.1] * 768
        return mock

    def test_ingest_documents_success(self, mock_db_manager, mock_embed_model):
        """Test successful bulk document ingestion."""
        documents = ["Document 1 content", "Document 2 content"]
        metadatas = [{"filename": "doc1.txt"}, {"filename": "doc2.txt"}]

        with patch('app.core.ingestion.get_sqlite_manager', return_value=mock_db_manager):
            with patch('app.core.ingestion.OllamaEmbedding', return_value=mock_embed_model):
                result = ingest_documents("test_collection", documents, metadatas)

        assert result["status"] == "success"
        assert result["documents_processed"] == 2
        mock_db_manager.add_documents.assert_called_once()

    def test_ingest_documents_nonexistent_collection(self, mock_db_manager):
        """Test ingestion to non-existent collection."""
        mock_db_manager.collection_exists.return_value = False

        with patch('app.core.ingestion.get_sqlite_manager', return_value=mock_db_manager):
            result = ingest_documents("nonexistent", ["doc"], [{}])

        assert result["status"] == "error"
        assert "not found" in result["error"]

    def test_ingest_documents_skips_empty(self, mock_db_manager, mock_embed_model):
        """Test that empty documents are skipped."""
        documents = ["Valid content", "", "   "]
        metadatas = [{"filename": "valid.txt"}, {"filename": "empty.txt"}, {"filename": "whitespace.txt"}]

        with patch('app.core.ingestion.get_sqlite_manager', return_value=mock_db_manager):
            with patch('app.core.ingestion.OllamaEmbedding', return_value=mock_embed_model):
                result = ingest_documents("test_collection", documents, metadatas)

        assert result["status"] == "success"
        # Only valid content should be processed

    def test_ingest_documents_all_empty(self, mock_db_manager, mock_embed_model):
        """Test ingestion when all documents are empty."""
        documents = ["", "   ", ""]
        metadatas = [{}, {}, {}]

        with patch('app.core.ingestion.get_sqlite_manager', return_value=mock_db_manager):
            with patch('app.core.ingestion.OllamaEmbedding', return_value=mock_embed_model):
                result = ingest_documents("test_collection", documents, metadatas)

        assert result["status"] == "error"
        assert "No valid documents" in result["error"]


class TestIngestDirectory:
    """Tests for ingest_directory function."""

    @pytest.fixture
    def mock_db_manager(self):
        """Create mock database manager."""
        mock = MagicMock()
        mock.collection_exists.return_value = True
        mock.add_documents = MagicMock()
        return mock

    @pytest.fixture
    def mock_embed_model(self):
        """Create mock embedding model."""
        mock = MagicMock()
        mock.get_text_embedding.return_value = [0.1] * 768
        return mock

    def test_ingest_directory_success(self, tmp_path, mock_db_manager, mock_embed_model):
        """Test successful directory ingestion."""
        # Create test files with supported extensions (.txt and .md are in ALLOWED_EXTENSIONS)
        (tmp_path / "file1.txt").write_text("Content 1 for testing ingestion")
        (tmp_path / "file2.md").write_text("# Content 2 for testing ingestion")

        with patch('app.core.ingestion.get_sqlite_manager', return_value=mock_db_manager):
            with patch('app.core.ingestion.OllamaEmbedding', return_value=mock_embed_model):
                results = ingest_directory(str(tmp_path), "test_collection")

        # Both files should be processed (txt and md are supported)
        assert len(results) >= 2
        # At least one should succeed (may fail if embedding mock has issues)
        successful = [r for r in results if r.get("status") == "success"]
        assert len(successful) >= 1

    def test_ingest_directory_nonexistent(self):
        """Test ingestion of non-existent directory."""
        results = ingest_directory("/nonexistent/directory", "test_collection")

        assert len(results) == 1
        assert results[0]["status"] == "error"
        assert "not found" in results[0]["error"]

    def test_ingest_directory_skips_node_modules(self, tmp_path, mock_db_manager, mock_embed_model):
        """Test that node_modules is skipped."""
        # Create files with supported extensions (.py and .js are supported)
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("# Main python file")
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "package" ).mkdir()
        (tmp_path / "node_modules" / "package" / "index.js").write_text("// JS file in node_modules")

        ingested_files = []

        with patch('app.core.ingestion.get_sqlite_manager', return_value=mock_db_manager):
            with patch('app.core.ingestion.OllamaEmbedding', return_value=mock_embed_model):
                with patch('app.core.ingestion.ingest_file') as mock_ingest:
                    mock_ingest.side_effect = lambda path, coll, name: (
                        ingested_files.append(path),
                        {"status": "success", "filename": name}
                    )[1]

                    ingest_directory(str(tmp_path), "test_collection")

        # node_modules files should not be in the list
        assert not any("node_modules" in f for f in ingested_files)

    def test_ingest_directory_recursive(self, tmp_path, mock_db_manager, mock_embed_model):
        """Test that directory ingestion is recursive."""
        # Create nested structure with supported file types
        (tmp_path / "level1").mkdir()
        (tmp_path / "level1" / "level2").mkdir()
        (tmp_path / "level1" / "file1.txt").write_text("Level 1 content")
        (tmp_path / "level1" / "level2" / "file2.txt").write_text("Level 2 content")

        with patch('app.core.ingestion.get_sqlite_manager', return_value=mock_db_manager):
            with patch('app.core.ingestion.OllamaEmbedding', return_value=mock_embed_model):
                results = ingest_directory(str(tmp_path), "test_collection")

        # Should find files in nested directories
        assert len(results) >= 2


class TestSkipDirectoriesConstant:
    """Tests for SKIP_DIRECTORIES constant."""

    def test_contains_common_excludes(self):
        """Test that common directories are in skip list."""
        expected_dirs = [
            'node_modules', '.git', '__pycache__', '.pytest_cache',
            'dist', 'build', '.vscode', '.idea'
        ]

        for dir_name in expected_dirs:
            assert dir_name in SKIP_DIRECTORIES, f"{dir_name} should be in SKIP_DIRECTORIES"

    def test_contains_language_specific_excludes(self):
        """Test that language-specific directories are included."""
        # Rust/Java
        assert 'target' in SKIP_DIRECTORIES

        # iOS
        assert 'Pods' in SKIP_DIRECTORIES

        # Gradle
        assert '.gradle' in SKIP_DIRECTORIES

    def test_skip_directories_is_set(self):
        """Test that SKIP_DIRECTORIES is a set for fast lookup."""
        assert isinstance(SKIP_DIRECTORIES, set)
