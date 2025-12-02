"""
Tests for Agent OS parser and ingestion functionality.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.core.agent_os_parser import AgentOSParser, AgentOSDocument, AgentOSContentType
from app.core.agent_os_ingestion import AgentOSIngestion
from app.core.sqlite_manager import SQLiteManager
from app.core.kb_types import KBType


@pytest.mark.unit
class TestAgentOSDocument:
    """Test AgentOSDocument dataclass."""

    def test_agent_os_document_creation(self):
        """Test creating an AgentOSDocument."""
        doc = AgentOSDocument(
            content_type=AgentOSContentType.STANDARD,
            title="Test Standard",
            content="Test content",
            file_path="/path/to/standard.yml",
            metadata={"version": "1.0", "category": "coding"}
        )

        assert doc.content_type == AgentOSContentType.STANDARD
        assert doc.title == "Test Standard"
        assert doc.content == "Test content"
        assert doc.file_path == "/path/to/standard.yml"
        assert doc.metadata["version"] == "1.0"
        assert doc.metadata["category"] == "coding"

    def test_agent_os_document_to_dict(self):
        """Test converting AgentOSDocument to dictionary."""
        doc = AgentOSDocument(
            content_type=AgentOSContentType.AGENT,
            title="Test Agent",
            content="Agent content",
            file_path="/path/to/agent.yml",
            metadata={"type": "test"}
        )

        doc_dict = doc.to_dict()

        assert doc_dict["content_type"] == "agent"
        assert doc_dict["title"] == "Test Agent"
        assert doc_dict["content"] == "Agent content"
        assert doc_dict["file_path"] == "/path/to/agent.yml"
        assert doc_dict["metadata"]["type"] == "test"


@pytest.mark.unit
class TestAgentOSParser:
    """Test AgentOSParser functionality."""

    def test_parser_initialization(self):
        """Test parser initialization."""
        parser = AgentOSParser()

        assert parser.DIRECTORY_TYPE_MAP == {
            "standards": AgentOSContentType.STANDARD,
            "agents": AgentOSContentType.AGENT,
            "workflows": AgentOSContentType.WORKFLOW,
            "commands": AgentOSContentType.COMMAND,
            "product": AgentOSContentType.PRODUCT,
            "specs": AgentOSContentType.SPEC,
        }
        assert parser.SUPPORTED_EXTENSIONS == {".yml", ".yaml", ".md"}

    def test_parse_nonexistent_directory(self):
        """Test parsing non-existent directory."""
        parser = AgentOSParser()

        with pytest.raises(ValueError, match="Directory does not exist"):
            parser.parse_directory("/nonexistent/path")

    def test_parse_not_a_directory(self):
        """Test parsing path that is not a directory."""
        parser = AgentOSParser()

        with tempfile.NamedTemporaryFile() as f:
            with pytest.raises(ValueError, match="Path is not a directory"):
                parser.parse_directory(f.name)

    def test_parse_invalid_agent_os_profile(self, tmp_path):
        """Test parsing directory without Agent OS structure."""
        parser = AgentOSParser()

        # Create directory without expected subdirectories
        invalid_dir = tmp_path / "invalid_profile"
        invalid_dir.mkdir()
        (invalid_dir / "random_file.txt").write_text("Not an Agent OS profile")

        with pytest.raises(ValueError, match="Not a valid Agent OS profile"):
            parser.parse_directory(str(invalid_dir))

    def test_parse_valid_agent_os_profile(self, tmp_path):
        """Test parsing valid Agent OS profile."""
        parser = AgentOSParser()

        # Create Agent OS directory structure
        profile_dir = tmp_path / "test_profile"
        profile_dir.mkdir()

        # Create subdirectories
        (profile_dir / "standards").mkdir()
        (profile_dir / "agents").mkdir()
        (profile_dir / "workflows").mkdir()

        # Add some files
        (profile_dir / "standards" / "python.yml").write_text("name: Python Standard")
        (profile_dir / "agents" / "test_agent.yml").write_text("name: Test Agent")
        (profile_dir / "workflows" / "deploy.yml").write_text("name: Deploy Workflow")

        documents = parser.parse_directory(str(profile_dir))

        assert len(documents) == 3

        # Check document types
        doc_types = [doc.content_type for doc in documents]
        assert AgentOSContentType.STANDARD in doc_types
        assert AgentOSContentType.AGENT in doc_types
        assert AgentOSContentType.WORKFLOW in doc_types

    def test_parse_yaml_file(self, tmp_path):
        """Test parsing YAML file."""
        parser = AgentOSParser()

        yaml_content = """
name: Test Standard
description: A test coding standard
version: 1.0
category: coding
rules:
  - name: naming_convention
    description: Use snake_case for variables
  - name: max_line_length
    description: Keep lines under 80 characters
"""
        yaml_file = tmp_path / "test.yml"
        yaml_file.write_text(yaml_content)

        doc = parser._parse_file(
            yaml_file,
            AgentOSContentType.STANDARD,
            tmp_path
        )

        assert doc is not None
        assert doc.content_type == AgentOSContentType.STANDARD
        assert doc.title == "Test Standard"
        assert "A test coding standard" in doc.content
        assert doc.metadata["version"] == 1.0  # YAML parses 1.0 as float
        assert doc.metadata["category"] == "coding"
        assert "naming_convention" in doc.content

    def test_parse_markdown_file(self, tmp_path):
        """Test parsing Markdown file."""
        parser = AgentOSParser()

        md_content = """# Test Workflow

This is a test workflow document.

## Steps

1. First step
2. Second step
3. Third step

## Notes

Important notes about the workflow.
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(md_content)

        doc = parser._parse_file(
            md_file,
            AgentOSContentType.WORKFLOW,
            tmp_path
        )

        assert doc is not None
        assert doc.content_type == AgentOSContentType.WORKFLOW
        assert doc.title == "Test Workflow"
        assert "This is a test workflow document" in doc.content
        assert doc.metadata["file_type"] == "markdown"

    def test_parse_empty_yaml_file(self, tmp_path):
        """Test parsing empty YAML file."""
        parser = AgentOSParser()

        empty_file = tmp_path / "empty.yml"
        empty_file.write_text("")

        doc = parser._parse_file(
            empty_file,
            AgentOSContentType.STANDARD,
            tmp_path
        )

        assert doc is None

    def test_parse_invalid_yaml_file(self, tmp_path):
        """Test parsing invalid YAML file."""
        parser = AgentOSParser()

        invalid_file = tmp_path / "invalid.yml"
        invalid_file.write_text("invalid: yaml: content: [")

        doc = parser._parse_file(
            invalid_file,
            AgentOSContentType.STANDARD,
            tmp_path
        )

        assert doc is None

    def test_yaml_to_text_conversion(self):
        """Test YAML to text conversion."""
        parser = AgentOSParser()

        yaml_data = {
            "name": "Test Standard",
            "description": "Test description",
            "rules": [
                {"name": "rule1", "description": "First rule"},
                {"name": "rule2", "description": "Second rule"}
            ],
            "settings": {
                "strict": True,
                "version": "1.0"
            }
        }

        text = parser._yaml_to_text(yaml_data, "Test Standard")

        assert "# Test Standard" in text
        assert "## Description" in text
        assert "Test description" in text
        assert "## Rules" in text
        assert "rule1" in text
        assert "First rule" in text
        assert "rule2" in text
        assert "Second rule" in text
        assert "## Settings" in text
        assert "strict" in text
        assert "True" in text

    def test_parse_content_directory(self, tmp_path):
        """Test parsing content directory."""
        parser = AgentOSParser()

        content_dir = tmp_path / "standards"
        content_dir.mkdir()

        # Create nested structure
        (content_dir / "subdir").mkdir()
        (content_dir / "subdir" / "nested.yml").write_text("name: Nested")
        (content_dir / "root.yml").write_text("name: Root")
        (content_dir / "ignore.txt").write_text("Should be ignored")

        documents = parser._parse_content_directory(
            content_dir,
            AgentOSContentType.STANDARD
        )

        assert len(documents) == 2  # Only YAML files

        titles = [doc.title for doc in documents]
        assert "Nested" in titles
        assert "Root" in titles


@pytest.mark.integration
class TestAgentOSIngestion:
    """Test AgentOSIngestion functionality."""

    @patch('app.core.agent_os_ingestion.OllamaEmbedding')
    def test_ingest_profile_success(self, mock_embed, clean_db, tmp_path):
        """Test successful Agent OS profile ingestion."""
        # Setup mock embedding
        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = [0.1] * 768
        mock_embed.return_value = mock_embed_instance

        # Create KB first
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        # Create Agent OS profile
        profile_dir = tmp_path / "test_profile"
        profile_dir.mkdir()

        (profile_dir / "standards").mkdir()
        (profile_dir / "agents").mkdir()

        (profile_dir / "standards" / "python.yml").write_text("name: Python Standard")
        (profile_dir / "agents" / "test_agent.yml").write_text("name: Test Agent")

        # Create ingestion instance with the fixture db
        ingestion = AgentOSIngestion(clean_db)

        result = ingestion.ingest_profile(kb_data["name"], str(profile_dir))

        assert result["success"] is True
        assert result["total_documents"] == 2
        assert "standard" in result["documents_by_type"]
        assert "agent" in result["documents_by_type"]
        assert result["documents_by_type"]["standard"] == 1
        assert result["documents_by_type"]["agent"] == 1

    def test_ingest_profile_nonexistent_kb(self, clean_db, tmp_path):
        """Test ingesting profile to non-existent KB."""
        ingestion = AgentOSIngestion(clean_db)

        profile_dir = tmp_path / "test_profile"
        profile_dir.mkdir()

        with pytest.raises(ValueError, match="does not exist"):
            ingestion.ingest_profile("nonexistent_kb", str(profile_dir))

    def test_ingest_profile_invalid_path(self, clean_db):
        """Test ingesting profile with invalid path."""
        # Create KB first
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        ingestion = AgentOSIngestion(clean_db)

        with pytest.raises(ValueError, match="Failed to parse"):
            ingestion.ingest_profile(kb_data["name"], "/nonexistent/path")

    def test_ingest_profile_empty(self, clean_db, tmp_path):
        """Test ingesting empty profile (no valid Agent OS structure)."""
        # Create KB first
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        ingestion = AgentOSIngestion(clean_db)

        # Create empty profile directory (no Agent OS subdirectories)
        profile_dir = tmp_path / "empty_profile"
        profile_dir.mkdir()

        # Empty profile without Agent OS structure raises ValueError
        with pytest.raises(ValueError, match="Failed to parse"):
            ingestion.ingest_profile(kb_data["name"], str(profile_dir))

    @patch('app.core.agent_os_ingestion.OllamaEmbedding')
    def test_ingest_profile_with_batch_processing(self, mock_embed, clean_db, tmp_path):
        """Test profile ingestion with batch processing."""
        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = [0.1] * 768
        mock_embed.return_value = mock_embed_instance

        # Create KB first
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        # Create profile with many documents
        profile_dir = tmp_path / "large_profile"
        profile_dir.mkdir()

        (profile_dir / "standards").mkdir()

        # Create 5 documents
        for i in range(5):
            (profile_dir / "standards" / f"standard_{i}.yml").write_text(f"name: Standard {i}")

        ingestion = AgentOSIngestion(clean_db)

        # Use small batch size to test batching
        result = ingestion.ingest_profile(kb_data["name"], str(profile_dir), batch_size=2)

        assert result["success"] is True
        assert result["total_documents"] == 5
        assert result["documents_by_type"]["standard"] == 5

    @patch('app.core.agent_os_ingestion.OllamaEmbedding')
    def test_ingest_batch_with_embedding_failure(self, mock_embed, clean_db, tmp_path):
        """Test batch ingestion with embedding failures."""
        # Mock embedding to fail for all documents after first batch
        mock_embed_instance = MagicMock()
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # First 2 succeed
                return [0.1] * 768
            else:  # Rest fail
                raise Exception("Embedding failed")

        mock_embed_instance.get_text_embedding.side_effect = side_effect
        mock_embed.return_value = mock_embed_instance

        # Create KB first
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        # Create profile
        profile_dir = tmp_path / "test_profile"
        profile_dir.mkdir()
        (profile_dir / "standards").mkdir()

        for i in range(4):
            (profile_dir / "standards" / f"standard_{i}.yml").write_text(f"name: Standard {i}")

        ingestion = AgentOSIngestion(clean_db)

        result = ingestion.ingest_profile(kb_data["name"], str(profile_dir))

        # With embedding failures, the ingestion reports errors
        # The result includes information about what failed
        assert result["total_documents"] == 4
        assert "errors" in result

    @patch('app.core.agent_os_ingestion.OllamaEmbedding')
    def test_get_profile_stats(self, mock_embed, clean_db, tmp_path):
        """Test getting profile statistics."""
        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = [0.1] * 768
        mock_embed.return_value = mock_embed_instance

        # Create KB first
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        # Create and ingest profile
        profile_dir = tmp_path / "stats_profile"
        profile_dir.mkdir()

        (profile_dir / "standards").mkdir()
        (profile_dir / "agents").mkdir()
        (profile_dir / "workflows").mkdir()

        (profile_dir / "standards" / "python.yml").write_text("name: Python")
        (profile_dir / "agents" / "test.yml").write_text("name: Test Agent")
        (profile_dir / "workflows" / "deploy.yml").write_text("name: Deploy")
        (profile_dir / "workflows" / "test.yml").write_text("name: Test Workflow")

        ingestion = AgentOSIngestion(clean_db)

        # Ingest first
        ingestion.ingest_profile(kb_data["name"], str(profile_dir))

        # Get stats
        stats = ingestion.get_profile_stats(kb_data["name"])

        assert stats["total_documents"] == 4
        assert stats["documents_by_type"]["standard"] == 1
        assert stats["documents_by_type"]["agent"] == 1
        assert stats["documents_by_type"]["workflow"] == 2

    def test_get_profile_stats_empty_kb(self, clean_db):
        """Test getting stats for KB with no Agent OS content."""
        # Create KB first
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        ingestion = AgentOSIngestion(clean_db)

        stats = ingestion.get_profile_stats(kb_data["name"])

        assert stats["total_documents"] == 0
        assert stats["documents_by_type"] == {}

    @patch('app.core.agent_os_ingestion.OllamaEmbedding')
    def test_search_by_type(self, mock_embed, clean_db, tmp_path):
        """Test searching Agent OS content by type."""
        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = [0.1] * 768
        mock_embed.return_value = mock_embed_instance

        # Create KB first
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        # Create and ingest profile
        profile_dir = tmp_path / "search_profile"
        profile_dir.mkdir()

        (profile_dir / "standards").mkdir()
        (profile_dir / "agents").mkdir()

        (profile_dir / "standards" / "python.yml").write_text("name: Python Standard\ndescription: For Python code")
        (profile_dir / "agents" / "test.yml").write_text("name: Test Agent\ndescription: For testing")

        ingestion = AgentOSIngestion(clean_db)

        ingestion.ingest_profile(kb_data["name"], str(profile_dir))

        # Search by type
        results = ingestion.search_by_type(
            kb_data["name"],
            AgentOSContentType.STANDARD,
            limit=10
        )

        # Should return results for standard type
        assert len(results) == 1
        assert results[0]["metadata"]["content_type"] == "standard"

    @patch('app.core.agent_os_ingestion.OllamaEmbedding')
    def test_search_by_type_with_query(self, mock_embed, clean_db, tmp_path):
        """Test searching Agent OS content by type with query."""
        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = [0.1] * 768
        mock_embed.return_value = mock_embed_instance

        # Create KB first
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        # Create and ingest profile
        profile_dir = tmp_path / "query_profile"
        profile_dir.mkdir()

        (profile_dir / "standards").mkdir()

        (profile_dir / "standards" / "python.yml").write_text("name: Python Standard")
        (profile_dir / "standards" / "javascript.yml").write_text("name: JavaScript Standard")

        ingestion = AgentOSIngestion(clean_db)

        ingestion.ingest_profile(kb_data["name"], str(profile_dir))

        # Search with query - should return results
        results = ingestion.search_by_type(
            kb_data["name"],
            AgentOSContentType.STANDARD,
            query="Python",
            limit=10
        )

        # Should find results with query
        assert len(results) >= 1

    def test_search_by_type_nonexistent_kb(self, clean_db):
        """Test searching by type in non-existent KB."""
        ingestion = AgentOSIngestion(clean_db)

        results = ingestion.search_by_type(
            "nonexistent_kb",
            AgentOSContentType.STANDARD
        )

        assert results == []

    @patch('app.core.agent_os_ingestion.OllamaEmbedding')
    def test_search_by_type_no_results(self, mock_embed, clean_db):
        """Test searching by type with no results."""
        mock_embed_instance = MagicMock()
        mock_embed_instance.get_text_embedding.return_value = [0.1] * 768
        mock_embed.return_value = mock_embed_instance

        # Create KB first
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        ingestion = AgentOSIngestion(clean_db)

        results = ingestion.search_by_type(
            kb_data["name"],
            AgentOSContentType.SPEC,  # No specs in KB
            limit=10
        )

        assert results == []


@pytest.mark.unit
class TestAgentOSContentType:
    """Test AgentOSContentType enum."""

    def test_content_type_values(self):
        """Test content type enum values."""
        assert AgentOSContentType.STANDARD.value == "standard"
        assert AgentOSContentType.AGENT.value == "agent"
        assert AgentOSContentType.WORKFLOW.value == "workflow"
        assert AgentOSContentType.COMMAND.value == "command"
        assert AgentOSContentType.PRODUCT.value == "product"
        assert AgentOSContentType.SPEC.value == "spec"
        assert AgentOSContentType.UNKNOWN.value == "unknown"

    def test_content_type_comparison(self):
        """Test content type comparison."""
        assert AgentOSContentType.STANDARD == "standard"
        assert AgentOSContentType.STANDARD != AgentOSContentType.AGENT
        assert AgentOSContentType.STANDARD != "agent"

    def test_content_type_string_representation(self):
        """Test content type string representation."""
        assert str(AgentOSContentType.STANDARD) == "standard"
        assert str(AgentOSContentType.AGENT) == "agent"
