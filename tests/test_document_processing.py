"""
Tests for document processing and ingestion.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


@pytest.mark.integration
class TestDocumentIngestion:
    """Test document ingestion pipeline."""

    def test_text_file_ingestion(self, sample_kb, clean_db, sample_text_file):
        """Test ingesting a text file (requires llama_index)."""
        pytest.importorskip("llama_index", reason="llama_index required for ingestion")

        from app.core.ingestion import ingest_file

        # Mock embedding generation
        with patch('app.core.ingestion.OllamaEmbedding') as mock_embed:
            mock_instance = MagicMock()
            mock_instance.get_text_embedding.return_value = [0.1] * 768
            mock_embed.return_value = mock_instance

            result = ingest_file(
                file_path=str(sample_text_file),
                collection_name=sample_kb["name"],
                filename=sample_text_file.name
            )

            assert result["status"] == "success"
            assert result["chunks"] > 0

    def test_pdf_file_ingestion(self, sample_kb, clean_db, sample_pdf_file):
        """Test ingesting a PDF file (requires llama_index)."""
        pytest.importorskip("llama_index", reason="llama_index required for ingestion")

        from app.core.ingestion import ingest_file

        with patch('app.core.ingestion.OllamaEmbedding') as mock_embed:
            mock_instance = MagicMock()
            mock_instance.get_text_embedding.return_value = [0.1] * 768
            mock_embed.return_value = mock_instance

            result = ingest_file(
                file_path=str(sample_pdf_file),
                collection_name=sample_kb["name"],
                filename=sample_pdf_file.name
            )

            assert result["status"] == "success"
            assert result["chunks"] > 0

    def test_markdown_file_ingestion(self, sample_kb, clean_db, sample_markdown_file):
        """Test ingesting a Markdown file (requires llama_index)."""
        pytest.importorskip("llama_index", reason="llama_index required for ingestion")

        from app.core.ingestion import ingest_file

        with patch('app.core.ingestion.OllamaEmbedding') as mock_embed:
            mock_instance = MagicMock()
            mock_instance.get_text_embedding.return_value = [0.1] * 768
            mock_embed.return_value = mock_instance

            result = ingest_file(
                file_path=str(sample_markdown_file),
                collection_name=sample_kb["name"],
                filename=sample_markdown_file.name
            )

            assert result["status"] == "success"
            assert result["chunks"] > 0


@pytest.mark.unit
class TestDocumentChunking:
    """Test document chunking strategies."""

    def test_fixed_size_chunking(self):
        """Test fixed-size chunking."""
        text = "This is a test. " * 100  # Long text
        chunk_size = 100
        overlap = 20

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - overlap

        assert len(chunks) > 1
        assert all(len(chunk) <= chunk_size for chunk in chunks)

    def test_sentence_chunking(self):
        """Test sentence-based chunking."""
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        sentences = text.split('. ')

        assert len(sentences) == 4
        assert all(len(s) > 0 for s in sentences)


@pytest.mark.unit
class TestFileTypeDetection:
    """Test file type detection."""

    def test_detect_text_file(self, sample_text_file):
        """Test detecting text file type."""
        assert sample_text_file.suffix == ".txt"

    def test_detect_pdf_file(self, sample_pdf_file):
        """Test detecting PDF file type."""
        assert sample_pdf_file.suffix == ".pdf"

    def test_detect_markdown_file(self, sample_markdown_file):
        """Test detecting Markdown file type."""
        assert sample_markdown_file.suffix == ".md"
