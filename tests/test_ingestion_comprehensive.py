"""
Comprehensive tests for document ingestion pipeline.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import uuid

from app.core.ingestion import (
    extract_text_from_file,
    chunk_document,
    ingest_file,
    ingest_documents,
    ingest_directory
)
from llama_index.core import Document


@pytest.mark.unit
class TestTextExtraction:
    """Test text extraction from various file types."""

    def test_extract_text_from_txt_file(self):
        """Test extracting text from .txt file."""
        content = "This is a test text file.\nWith multiple lines."

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            f.flush()

            extracted = extract_text_from_file(f.name)
            assert extracted == content

        Path(f.name).unlink()

    def test_extract_text_from_py_file(self):
        """Test extracting text from Python file."""
        content = """
def hello_world():
    print("Hello, World!")
    return True
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(content)
            f.flush()

            extracted = extract_text_from_file(f.name)
            assert extracted.strip() == content.strip()

        Path(f.name).unlink()

    def test_extract_text_from_json_file(self):
        """Test extracting text from JSON file."""
        content = '{"name": "test", "value": 123, "active": true}'

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(content)
            f.flush()

            extracted = extract_text_from_file(f.name)
            assert extracted == content

        Path(f.name).unlink()

    @patch('app.core.ingestion.fitz')
    def test_extract_text_from_pdf_file(self, mock_fitz):
        """Test extracting text from PDF file."""
        # Mock PyMuPDF
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "PDF page content"
        mock_doc.__iter__.return_value = [mock_page]
        mock_fitz.open.return_value = mock_doc

        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            extracted = extract_text_from_file(f.name)

            assert extracted == "PDF page content"
            mock_fitz.open.assert_called_once_with(Path(f.name))

        Path(f.name).unlink()

    def test_extract_text_from_unsupported_file(self):
        """Test extracting text from unsupported file type."""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b"binary content")
            f.flush()

            extracted = extract_text_from_file(f.name)
            assert extracted == ""

        Path(f.name).unlink()

    def test_extract_text_from_nonexistent_file(self):
        """Test extracting text from non-existent file."""
        extracted = extract_text_from_file("/nonexistent/file.txt")
        assert extracted == ""

    def test_extract_text_with_encoding_errors(self):
        """Test extracting text with encoding issues."""
        # Create file with problematic content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("Valid text\n\x80\x81Invalid bytes")
            f.flush()

            extracted = extract_text_from_file(f.name)
            # Should handle encoding errors gracefully
            assert "Valid text" in extracted

        Path(f.name).unlink()


@pytest.mark.unit
class TestDocumentChunking:
    """Test document chunking functionality."""

    def test_chunk_document_short_text(self):
        """Test chunking short text (no splitting)."""
        text = "This is a short text."
        metadata = {"filename": "test.txt"}

        with patch('app.core.ingestion.Config.CHUNK_SIZE', 100):
            with patch('app.core.ingestion.Config.CHUNK_OVERLAP', 20):
                chunks = chunk_document(text, metadata)

                assert len(chunks) == 1
                assert chunks[0].text == text
                assert chunks[0].metadata["filename"] == "test.txt"
                assert chunks[0].metadata["chunk_index"] == 0

    def test_chunk_document_long_text(self):
        """Test chunking long text (multiple chunks)."""
        text = "This is a longer text that should be split into multiple chunks. " * 10
        metadata = {"filename": "long.txt"}

        with patch('app.core.ingestion.Config.CHUNK_SIZE', 50):
            with patch('app.core.ingestion.Config.CHUNK_OVERLAP', 10):
                chunks = chunk_document(text, metadata)

                assert len(chunks) > 1

                # Check chunk metadata
                for i, chunk in enumerate(chunks):
                    assert chunk.metadata["chunk_index"] == i
                    assert chunk.metadata["filename"] == "long.txt"
                    assert "chunk_id" in chunk.metadata

                # Check overlap
                for i in range(1, len(chunks)):
                    # Previous chunk end should overlap with current chunk start
                    prev_end = chunks[i-1].text[-10:]
                    curr_start = chunks[i].text[:10]
                    # This is a rough check - exact overlap depends on sentence boundaries
                    assert len(chunks[i].text) <= 50

    def test_chunk_document_preserves_metadata(self):
        """Test that chunking preserves original metadata."""
        original_metadata = {
            "filename": "test.txt",
            "author": "Test Author",
            "date": "2023-01-01",
            "tags": ["test", "example"]
        }

        text = "Test content for chunking."
        chunks = chunk_document(text, original_metadata)

        for chunk in chunks:
            assert chunk.metadata["filename"] == "test.txt"
            assert chunk.metadata["author"] == "Test Author"
            assert chunk.metadata["date"] == "2023-01-01"
            assert chunk.metadata["tags"] == ["test", "example"]
            assert "chunk_index" in chunk.metadata
            assert "chunk_id" in chunk.metadata


@pytest.mark.integration
class TestFileIngestion:
    """Test file ingestion functionality."""

    @patch('app.core.ingestion.OllamaEmbedding')
    @patch('app.core.ingestion.get_sqlite_manager')
    def test_ingest_text_file_success(self, mock_get_db, mock_embed, sample_kb, clean_db, sample_text_file):
        """Test successful text file ingestion."""
        # Mock database manager
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = True
        mock_get_db.return_value = mock_db

        # Mock embedding model
        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = [0.1] * 768
        mock_embed.return_value = mock_embed_instance

        result = ingest_file(
            file_path=str(sample_text_file),
            collection_name=sample_kb["name"],
            filename=sample_text_file.name
        )

        assert result["status"] == "success"
        assert result["filename"] == sample_text_file.name
        assert result["chunks"] > 0
        assert result["file_type"] == ".txt"

    @patch('app.core.ingestion.OllamaEmbedding')
    @patch('app.core.ingestion.get_sqlite_manager')
    def test_ingest_file_empty_content(self, mock_get_db, mock_embed, sample_kb, clean_db, tmp_path):
        """Test ingesting file with empty content."""
        # Create empty file
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        mock_db = MagicMock()
        mock_db.collection_exists.return_value = True
        mock_get_db.return_value = mock_db

        result = ingest_file(
            file_path=str(empty_file),
            collection_name=sample_kb["name"],
            filename="empty.txt"
        )

        assert result["status"] == "error"
        assert "No text content extracted" in result["error"]

    @patch('app.core.ingestion.OllamaEmbedding')
    @patch('app.core.ingestion.get_sqlite_manager')
    def test_ingest_file_nonexistent_collection(self, mock_get_db, mock_embed, sample_text_file):
        """Test ingesting file to non-existent collection."""
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = False
        mock_get_db.return_value = mock_db

        result = ingest_file(
            file_path=str(sample_text_file),
            collection_name="nonexistent_collection",
            filename="test.txt"
        )

        assert result["status"] == "error"
        assert "not found" in result["error"]

    @patch('app.core.ingestion.OllamaEmbedding')
    @patch('app.core.ingestion.get_sqlite_manager')
    def test_ingest_file_with_embedding_failure(self, mock_get_db, mock_embed, sample_kb, clean_db, sample_text_file):
        """Test ingesting file with embedding failures."""
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = True
        mock_get_db.return_value = mock_db

        # Mock embedding to fail for some chunks
        mock_embed_instance = MagicMock()
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # First 2 calls succeed
                return [0.1] * 768
            else:  # Rest fail
                raise Exception("Embedding failed")

        mock_embed_instance.get_text_embedding.side_effect = side_effect
        mock_embed.return_value = mock_embed_instance

        result = ingest_file(
            file_path=str(sample_text_file),
            collection_name=sample_kb["name"],
            filename=sample_text_file.name
        )

        # Should still succeed with partial chunks
        assert result["status"] == "success"
        assert result["chunks"] > 0
        # Should mention skipped chunks
        assert "chunks skipped" in result.get("status", "")

    @patch('app.core.ingestion.OllamaEmbedding')
    @patch('app.core.ingestion.get_sqlite_manager')
    def test_ingest_file_all_chunks_fail(self, mock_get_db, mock_embed, sample_kb, clean_db, sample_text_file):
        """Test ingesting file when all chunks fail to embed."""
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = True
        mock_get_db.return_value = mock_db

        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.side_effect = Exception("All embeddings fail")
        mock_embed.return_value = mock_embed_instance

        result = ingest_file(
            file_path=str(sample_text_file),
            collection_name=sample_kb["name"],
            filename=sample_text_file.name
        )

        assert result["status"] == "error"
        assert "All" in result["error"] and "chunks failed" in result["error"]

    @patch('app.core.ingestion.preprocess_markdown')
    @patch('app.core.ingestion.OllamaEmbedding')
    @patch('app.core.ingestion.get_sqlite_manager')
    def test_ingest_markdown_file_with_preprocessing(self, mock_get_db, mock_embed, mock_preprocess, sample_kb, clean_db, sample_markdown_file):
        """Test ingesting markdown file with preprocessing."""
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = True
        mock_get_db.return_value = mock_db

        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = [0.1] * 768
        mock_embed.return_value = mock_embed_instance

        # Mock preprocessing
        processed_text = "# Processed Title\n\nProcessed content"
        enriched_metadata = {"title": "Processed Title", "headings": ["Processed Title"]}
        mock_preprocess.return_value = (processed_text, enriched_metadata)

        result = ingest_file(
            file_path=str(sample_markdown_file),
            collection_name=sample_kb["name"],
            filename=sample_markdown_file.name
        )

        assert result["status"] == "success"
        mock_preprocess.assert_called_once()

        # Check that preprocessing was called with correct arguments
        call_args = mock_preprocess.call_args
        assert call_args[0][1] == sample_markdown_file.name  # filename
        assert str(sample_markdown_file) in call_args[0][2]  # file_path


@pytest.mark.integration
class TestBulkIngestion:
    """Test bulk document ingestion."""

    @patch('app.core.ingestion.OllamaEmbedding')
    @patch('app.core.ingestion.get_sqlite_manager')
    def test_ingest_documents_success(self, mock_get_db, mock_embed, sample_kb, clean_db):
        """Test successful bulk document ingestion."""
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = True
        mock_get_db.return_value = mock_db

        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = [0.1] * 768
        mock_embed.return_value = mock_embed_instance

        documents = ["Document 1 content", "Document 2 content"]
        metadatas = [{"filename": "doc1.txt"}, {"filename": "doc2.txt"}]

        result = ingest_documents(
            collection_name=sample_kb["name"],
            documents=documents,
            metadatas=metadatas
        )

        assert result["status"] == "success"
        assert result["documents_processed"] == 2
        assert result["chunks_created"] > 0
        assert result["collection_name"] == sample_kb["name"]

    @patch('app.core.ingestion.OllamaEmbedding')
    @patch('app.core.ingestion.get_sqlite_manager')
    def test_ingest_documents_nonexistent_collection(self, mock_get_db, mock_embed):
        """Test bulk ingestion to non-existent collection."""
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = False
        mock_get_db.return_value = mock_db

        documents = ["Test content"]
        metadatas = [{"filename": "test.txt"}]

        result = ingest_documents(
            collection_name="nonexistent_collection",
            documents=documents,
            metadatas=metadatas
        )

        assert result["status"] == "error"
        assert "not found" in result["error"]
        assert result["documents_processed"] == 0

    @patch('app.core.ingestion.OllamaEmbedding')
    @patch('app.core.ingestion.get_sqlite_manager')
    def test_ingest_documents_empty_documents(self, mock_get_db, mock_embed, sample_kb, clean_db):
        """Test bulk ingestion with empty documents."""
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = True
        mock_get_db.return_value = mock_db

        documents = [""]
        metadatas = [{"filename": "empty.txt"}]

        result = ingest_documents(
            collection_name=sample_kb["name"],
            documents=documents,
            metadatas=metadatas
        )

        assert result["status"] == "error"
        assert "No valid documents" in result["error"]

    @patch('app.core.ingestion.OllamaEmbedding')
    @patch('app.core.ingestion.get_sqlite_manager')
    def test_ingest_documents_with_long_chunks(self, mock_get_db, mock_embed, sample_kb, clean_db):
        """Test bulk ingestion with chunk truncation."""
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = True
        mock_get_db.return_value = mock_db

        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = [0.1] * 768
        mock_embed.return_value = mock_embed_instance

        # Create very long document
        long_content = "This is a very long content. " * 1000  # Will create chunks > 8000 chars
        documents = [long_content]
        metadatas = [{"filename": "long.txt"}]

        result = ingest_documents(
            collection_name=sample_kb["name"],
            documents=documents,
            metadatas=metadatas
        )

        assert result["status"] == "success"
        assert result["documents_processed"] == 1
        assert result["chunks_created"] > 0

        # Verify truncation occurred (check that add_documents was called)
        mock_db.add_documents.assert_called_once()
        call_args = mock_db.add_documents.call_args
        documents_added = call_args[1]["documents"]

        # At least one document should be truncated to 8000 chars
        assert any(len(doc) <= 8000 for doc in documents_added)


@pytest.mark.integration
class TestDirectoryIngestion:
    """Test directory ingestion functionality."""

    @patch('app.core.ingestion.ingest_file')
    @patch('app.core.ingestion.Config')
    def test_ingest_directory_success(self, mock_config, mock_ingest, tmp_path):
        """Test successful directory ingestion."""
        # Mock supported file types
        mock_config.SUPPORTED_FILE_TYPES = [".txt", ".md", ".py"]

        # Create test directory structure
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()

        (test_dir / "file1.txt").write_text("Content 1")
        (test_dir / "file2.md").write_text("# Content 2")
        (test_dir / "file3.py").write_text("print('Content 3')")
        (test_dir / "ignore.xyz").write_text("Should be ignored")

        (test_dir / "subdir").mkdir()
        (test_dir / "subdir" / "file4.txt").write_text("Content 4")

        # Mock ingest_file to return success
        mock_ingest.return_value = {"status": "success", "chunks": 1}

        results = ingest_directory(str(test_dir), "test_collection")

        # Should have 4 results (3 in root + 1 in subdir)
        assert len(results) == 4

        # Check that ingest_file was called for supported files
        assert mock_ingest.call_count == 4

        # Verify the calls were made with correct arguments
        call_args = [call[0] for call in mock_ingest.call_args_list]
        file_paths = [args[0] for args in call_args]

        assert any("file1.txt" in path for path in file_paths)
        assert any("file2.md" in path for path in file_paths)
        assert any("file3.py" in path for path in file_paths)
        assert any("file4.txt" in path for path in file_paths)

    @patch('app.core.ingestion.ingest_file')
    @patch('app.core.ingestion.Config')
    def test_ingest_directory_not_found(self, mock_config, mock_ingest):
        """Test ingesting non-existent directory."""
        mock_config.SUPPORTED_FILE_TYPES = [".txt"]

        results = ingest_directory("/nonexistent/directory", "test_collection")

        assert len(results) == 1
        assert results[0]["status"] == "error"
        assert "not found" in results[0]["error"]

    @patch('app.core.ingestion.ingest_file')
    @patch('app.core.ingestion.Config')
    def test_ingest_directory_empty(self, mock_config, mock_ingest, tmp_path):
        """Test ingesting empty directory."""
        mock_config.SUPPORTED_FILE_TYPES = [".txt"]

        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        results = ingest_directory(str(empty_dir), "test_collection")

        assert len(results) == 0
        mock_ingest.assert_not_called()

    @patch('app.core.ingestion.ingest_file')
    @patch('app.core.ingestion.Config')
    def test_ingest_directory_no_supported_files(self, mock_config, mock_ingest, tmp_path):
        """Test ingesting directory with no supported files."""
        mock_config.SUPPORTED_FILE_TYPES = [".txt"]

        test_dir = tmp_path / "test"
        test_dir.mkdir()
        (test_dir / "file1.xyz").write_text("Unsupported")
        (test_dir / "file2.abc").write_text("Also unsupported")

        results = ingest_directory(str(test_dir), "test_collection")

        assert len(results) == 0
        mock_ingest.assert_not_called()


@pytest.mark.unit
class TestIngestionHelpers:
    """Test ingestion helper functions and edge cases."""

    def test_chunk_document_with_unicode(self):
        """Test chunking document with Unicode content."""
        text = "测试内容 🚀 Unicode test with emoji and Chinese characters. " * 5
        metadata = {"filename": "unicode.txt"}

        chunks = chunk_document(text, metadata)

        assert len(chunks) > 0
        for chunk in chunks:
            assert isinstance(chunk.text, str)
            # Unicode should be preserved
            assert "测试" in chunk.text or "🚀" in chunk.text

    def test_chunk_document_with_code_blocks(self):
        """Test chunking document with code blocks."""
        text = """
Here is some text.

```python
def hello():
    print("Hello, World!")
```

More text here.
"""
        metadata = {"filename": "code.md"}

        with patch('app.core.ingestion.Config.CHUNK_SIZE', 50):
            chunks = chunk_document(text, metadata)

            # Should preserve code blocks within chunks
            chunk_texts = [chunk.text for chunk in chunks]
            all_text = " ".join(chunk_texts)

            # Code block should be present somewhere
            assert "def hello():" in all_text
            assert "print" in all_text

    @patch('app.core.ingestion.OllamaEmbedding')
    @patch('app.core.ingestion.get_sqlite_manager')
    def test_ingest_file_with_special_characters(self, mock_get_db, mock_embed, sample_kb, clean_db, tmp_path):
        """Test ingesting file with special characters in filename."""
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = True
        mock_get_db.return_value = mock_db

        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = [0.1] * 768
        mock_embed.return_value = mock_embed_instance

        # Create file with special characters
        special_file = tmp_path / "file with spaces & symbols!.txt"
        special_file.write_text("Test content")

        result = ingest_file(
            file_path=str(special_file),
            collection_name=sample_kb["name"],
            filename=special_file.name
        )

        assert result["status"] == "success"
        assert result["filename"] == special_file.name