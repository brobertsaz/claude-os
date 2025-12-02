"""
Tests for KB metadata and types functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from app.core.kb_metadata import (
    generate_tags,
    format_timestamp,
    get_documents_metadata,
    get_collection_stats,
    get_kb_type_badge,
    get_kb_type_summary
)
from app.core.kb_types import (
    KBType,
    KBMetadata,
    KBTypeInfo,
    get_kb_type_info,
    validate_kb_type,
    get_kb_type_display_name,
    get_all_kb_types,
    get_kb_type_choices
)


@pytest.mark.unit
class TestKBMetadata:
    """Test KBMetadata class."""

    def test_kb_metadata_creation(self):
        """Test KBMetadata creation with default values."""
        metadata = KBMetadata()

        assert metadata.kb_type == KBType.GENERIC
        assert metadata.description == ""
        assert isinstance(metadata.created_at, str)
        assert metadata.tags == []

    def test_kb_metadata_creation_with_values(self):
        """Test KBMetadata creation with custom values."""
        test_date = "2023-01-01T00:00:00"
        metadata = KBMetadata(
            kb_type=KBType.CODE,
            description="Test code KB",
            created_at=test_date,
            tags=["python", "javascript"]
        )

        assert metadata.kb_type == KBType.CODE
        assert metadata.description == "Test code KB"
        assert metadata.created_at == test_date
        assert metadata.tags == ["python", "javascript"]

    def test_kb_metadata_to_dict(self):
        """Test KBMetadata to_dict conversion."""
        metadata = KBMetadata(
            kb_type=KBType.DOCUMENTATION,
            description="Test docs",
            tags=["api", "guide"]
        )

        result = metadata.to_dict()

        assert result["kb_type"] == "documentation"
        assert result["description"] == "Test docs"
        assert result["created_at"] == metadata.created_at
        assert result["tags"] == "api,guide"  # Comma-separated

    def test_kb_metadata_from_dict(self):
        """Test KBMetadata from_dict creation."""
        data = {
            "kb_type": "agent-os",
            "description": "Test Agent OS",
            "created_at": "2023-01-01T00:00:00",
            "tags": "standard,workflow,spec"
        }

        metadata = KBMetadata.from_dict(data)

        assert metadata.kb_type == KBType.AGENT_OS
        assert metadata.description == "Test Agent OS"
        assert metadata.created_at == "2023-01-01T00:00:00"
        assert metadata.tags == ["standard", "workflow", "spec"]

    def test_kb_metadata_from_dict_empty_tags(self):
        """Test KBMetadata from_dict with empty tags."""
        data = {
            "kb_type": "generic",
            "description": "Test generic",
            "created_at": "2023-01-01T00:00:00",
            "tags": ""
        }

        metadata = KBMetadata.from_dict(data)

        assert metadata.tags == []

    def test_kb_metadata_from_dict_no_tags(self):
        """Test KBMetadata from_dict with no tags field."""
        data = {
            "kb_type": "generic",
            "description": "Test generic",
            "created_at": "2023-01-01T00:00:00"
        }

        metadata = KBMetadata.from_dict(data)

        assert metadata.tags == []

    def test_kb_metadata_from_dict_invalid_type(self):
        """Test KBMetadata from_dict with invalid type raises error."""
        data = {
            "kb_type": "invalid_type",
            "description": "Test invalid",
            "created_at": "2023-01-01T00:00:00",
            "tags": ""
        }

        # Implementation raises ValueError for invalid types
        with pytest.raises(ValueError):
            KBMetadata.from_dict(data)


@pytest.mark.unit
class TestKBType:
    """Test KBType enum."""

    def test_kb_type_values(self):
        """Test KBType enum values."""
        assert KBType.GENERIC.value == "generic"
        assert KBType.CODE.value == "code"
        assert KBType.DOCUMENTATION.value == "documentation"
        assert KBType.AGENT_OS.value == "agent-os"

    def test_kb_type_string_representation(self):
        """Test KBType value representation."""
        # Use .value for the string value
        assert KBType.GENERIC.value == "generic"
        assert KBType.CODE.value == "code"
        assert KBType.DOCUMENTATION.value == "documentation"
        assert KBType.AGENT_OS.value == "agent-os"

    def test_kb_type_comparison(self):
        """Test KBType comparison."""
        assert KBType.GENERIC == "generic"
        assert KBType.GENERIC != KBType.CODE
        assert KBType.GENERIC == KBType.GENERIC


@pytest.mark.unit
class TestKBTypeFunctions:
    """Test KB type utility functions."""

    def test_validate_kb_type_valid(self):
        """Test validate_kb_type with valid types."""
        assert validate_kb_type("generic") == KBType.GENERIC
        assert validate_kb_type("code") == KBType.CODE
        assert validate_kb_type("documentation") == KBType.DOCUMENTATION
        assert validate_kb_type("agent-os") == KBType.AGENT_OS

    def test_validate_kb_type_invalid(self):
        """Test validate_kb_type with invalid types."""
        assert validate_kb_type("invalid") is None
        assert validate_kb_type("") is None
        assert validate_kb_type("unknown") is None

    def test_get_kb_type_info(self):
        """Test get_kb_type_info function."""
        # Test each type
        for kb_type in KBType:
            info = get_kb_type_info(kb_type)

            assert isinstance(info, KBTypeInfo)
            assert info.icon is not None
            assert info.color is not None
            assert info.name is not None
            assert info.description is not None
            assert isinstance(info.use_cases, list)

    def test_get_kb_type_info_default(self):
        """Test get_kb_type_info with invalid type (should return default)."""
        info = get_kb_type_info("invalid_type")

        # Should return GENERIC info
        assert info.icon == "📦"
        assert info.name == "Generic"

    def test_get_kb_type_display_name(self):
        """Test get_kb_type_display_name function."""
        generic_display = get_kb_type_display_name(KBType.GENERIC)
        assert "📦" in generic_display
        assert "Generic" in generic_display

        code_display = get_kb_type_display_name(KBType.CODE)
        assert "💻" in code_display
        assert "Code Repository" in code_display

    def test_get_all_kb_types(self):
        """Test get_all_kb_types function."""
        all_types = get_all_kb_types()

        assert isinstance(all_types, list)
        assert len(all_types) == 4
        assert KBType.GENERIC in all_types
        assert KBType.CODE in all_types
        assert KBType.DOCUMENTATION in all_types
        assert KBType.AGENT_OS in all_types

    def test_get_kb_type_choices(self):
        """Test get_kb_type_choices function."""
        choices = get_kb_type_choices()

        assert isinstance(choices, dict)
        assert len(choices) == 4

        # Check that all display names are keys
        display_names = list(choices.keys())
        assert any("📦 Generic" in name for name in display_names)
        assert any("💻 Code Repository" in name for name in display_names)
        assert any("📚 Documentation" in name for name in display_names)
        assert any("🤖 Agent OS Profile" in name for name in display_names)

        # Check that all types are values
        type_values = list(choices.values())
        assert KBType.GENERIC in type_values
        assert KBType.CODE in type_values
        assert KBType.DOCUMENTATION in type_values
        assert KBType.AGENT_OS in type_values


@pytest.mark.unit
class TestKBMetadataFunctions:
    """Test KB metadata utility functions."""

    def test_generate_tags(self):
        """Test generate_tags function."""
        # Test known file types
        assert generate_tags(".py") == ["Code", "Python"]
        assert generate_tags(".js") == ["Code", "JavaScript"]
        assert generate_tags(".jsx") == ["Code", "React"]
        assert generate_tags(".ts") == ["Code", "TypeScript"]
        assert generate_tags(".tsx") == ["Code", "React", "TypeScript"]
        assert generate_tags(".go") == ["Code", "Go"]
        assert generate_tags(".rs") == ["Code", "Rust"]
        assert generate_tags(".java") == ["Code", "Java"]
        assert generate_tags(".cpp") == ["Code", "C++"]
        assert generate_tags(".c") == ["Code", "C"]
        assert generate_tags(".h") == ["Code", "Header"]
        assert generate_tags(".md") == ["Document", "Markdown"]
        assert generate_tags(".txt") == ["Document", "Text"]
        assert generate_tags(".pdf") == ["Document", "PDF"]
        assert generate_tags(".json") == ["Config", "JSON"]
        assert generate_tags(".yaml") == ["Config", "YAML"]
        assert generate_tags(".yml") == ["Config", "YAML"]

        # Test unknown file type
        assert generate_tags(".xyz") == ["Document", "Unknown"]
        assert generate_tags("") == ["Document", "Unknown"]

    def test_generate_tags_case_insensitive(self):
        """Test generate_tags function is case insensitive."""
        assert generate_tags(".PY") == ["Code", "Python"]
        assert generate_tags(".JS") == ["Code", "JavaScript"]
        assert generate_tags(".MD") == ["Document", "Markdown"]

    def test_format_timestamp_valid(self):
        """Test format_timestamp with valid timestamp."""
        timestamp = "2023-01-15T14:30:00"
        formatted = format_timestamp(timestamp)

        assert formatted == "Updated: 01/15/2023"

    def test_format_timestamp_invalid(self):
        """Test format_timestamp with invalid timestamp."""
        formatted = format_timestamp("invalid-timestamp")

        assert formatted == "Updated: Unknown"

    def test_format_timestamp_none(self):
        """Test format_timestamp with None."""
        formatted = format_timestamp(None)

        assert formatted == "Updated: Unknown"

    def test_get_kb_type_badge(self):
        """Test get_kb_type_badge function."""
        badge = get_kb_type_badge(KBType.GENERIC)

        assert "📦" in badge
        assert "Generic" in badge
        assert "background:" in badge
        assert "color:" in badge
        assert "padding:" in badge
        assert "border-radius:" in badge
        assert "display:" in badge

    def test_get_kb_type_badge_all_types(self):
        """Test get_kb_type_badge for all types."""
        for kb_type in KBType:
            badge = get_kb_type_badge(kb_type)

            # Should contain icon and name
            info = get_kb_type_info(kb_type)
            assert info.icon in badge
            assert info.name in badge
            # Should contain color
            assert info.color in badge

    def test_get_kb_type_summary(self):
        """Test get_kb_type_summary function."""
        # Mock database manager
        with patch('app.core.kb_metadata.get_sqlite_manager') as mock_get_db:
            mock_db = MagicMock()
            mock_db.list_collections.return_value = [
                {"metadata": {"kb_type": "generic"}},
                {"metadata": {"kb_type": "code"}},
                {"metadata": {"kb_type": "code"}},
                {"metadata": {"kb_type": "documentation"}},
                {"metadata": {"kb_type": "agent-os"}}
            ]
            mock_get_db.return_value = mock_db

            summary = get_kb_type_summary()

            assert summary["generic"] == 1
            assert summary["code"] == 2
            assert summary["documentation"] == 1
            assert summary["agent-os"] == 1

    def test_get_kb_type_summary_with_unknown_types(self):
        """Test get_kb_type_summary with unknown types."""
        # Mock database manager
        with patch('app.core.kb_metadata.get_sqlite_manager') as mock_get_db:
            mock_db = MagicMock()
            mock_db.list_collections.return_value = [
                {"metadata": {"kb_type": "generic"}},
                {"metadata": {"kb_type": "unknown_type"}},
                {"metadata": {"kb_type": "another_unknown"}}
            ]
            mock_get_db.return_value = mock_db

            summary = get_kb_type_summary()

            # Unknown types should be counted as generic
            assert summary["generic"] == 3  # 1 real + 2 unknown
            assert summary["code"] == 0
            assert summary["documentation"] == 0
            assert summary["agent-os"] == 0

    def test_get_kb_type_summary_empty(self):
        """Test get_kb_type_summary with no collections."""
        # Mock database manager
        with patch('app.core.kb_metadata.get_sqlite_manager') as mock_get_db:
            mock_db = MagicMock()
            mock_db.list_collections.return_value = []
            mock_get_db.return_value = mock_db

            summary = get_kb_type_summary()

            # All counts should be 0
            for kb_type in KBType:
                assert summary[kb_type.value] == 0


@pytest.mark.integration
class TestKBMetadataIntegration:
    """Integration tests for KB metadata functionality."""

    @patch('app.core.kb_metadata.get_sqlite_manager')
    def test_get_documents_metadata_real_data(self, mock_get_db, sample_kb, sample_documents):
        """Test get_documents_metadata with real data."""
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = True
        mock_db.get_documents_by_metadata.return_value = [
            {
                "metadata": {
                    "filename": "test_0.txt",
                    "file_type": ".txt",
                    "upload_date": "2023-01-01T00:00:00",
                    "chunk_index": 0
                }
            },
            {
                "metadata": {
                    "filename": "test_0.txt",
                    "file_type": ".txt",
                    "upload_date": "2023-01-01T00:00:00",
                    "chunk_index": 1
                }
            },
            {
                "metadata": {
                    "filename": "test_1.txt",
                    "file_type": ".txt",
                    "upload_date": "2023-01-02T00:00:00",
                    "chunk_index": 0
                }
            }
        ]
        mock_get_db.return_value = mock_db

        metadata = get_documents_metadata(sample_kb["name"])

        # Should group chunks by filename
        assert len(metadata) == 2  # 2 unique filenames

        # Check first document
        doc0 = next(doc for doc in metadata if doc["filename"] == "test_0.txt")
        assert doc0["file_type"] == ".txt"
        assert doc0["tags"] == ["Document", "Text"]
        assert doc0["upload_date"] == "2023-01-01T00:00:00"
        assert doc0["formatted_date"] == "Updated: 01/01/2023"
        assert doc0["chunk_count"] == 2  # 2 chunks for this file

    @patch('app.core.kb_metadata.get_sqlite_manager')
    def test_get_collection_stats_real_data(self, mock_get_db, sample_kb, sample_documents):
        """Test get_collection_stats with real data."""
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = True
        mock_db.get_collection_metadata.return_value = {
            "kb_type": "code",
            "description": "Test code KB",
            "created_at": "2023-01-01T00:00:00"
        }
        mock_db.get_documents_by_metadata.return_value = [
            {"metadata": {"filename": "test_0.txt", "upload_date": "2023-01-01T00:00:00"}},
            {"metadata": {"filename": "test_0.txt", "upload_date": "2023-01-01T00:00:00"}},
            {"metadata": {"filename": "test_1.txt", "upload_date": "2023-01-02T00:00:00"}}
        ]
        mock_get_db.return_value = mock_db

        stats = get_collection_stats(sample_kb["name"])

        assert stats["total_documents"] == 2  # 2 unique filenames
        assert stats["total_chunks"] == 3  # 3 total chunks
        assert stats["last_updated"] == "2023-01-02T00:00:00"  # Latest upload
        assert stats["kb_type"] == "code"

    @patch('app.core.kb_metadata.get_sqlite_manager')
    def test_get_collection_stats_nonexistent_kb(self, mock_get_db):
        """Test get_collection_stats with non-existent KB."""
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = False
        mock_get_db.return_value = mock_db

        stats = get_collection_stats("nonexistent_kb")

        # Should return default stats
        assert stats["total_documents"] == 0
        assert stats["total_chunks"] == 0
        assert stats["last_updated"] is None
        assert stats["kb_type"] == "generic"

    @patch('app.core.kb_metadata.get_sqlite_manager')
    def test_get_collection_stats_empty_kb(self, mock_get_db, sample_kb):
        """Test get_collection_stats with empty KB."""
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = True
        mock_db.get_collection_metadata.return_value = {
            "kb_type": "generic",
            "description": "Empty KB",
            "created_at": "2023-01-01T00:00:00"
        }
        mock_db.get_documents_by_metadata.return_value = []
        mock_get_db.return_value = mock_db

        stats = get_collection_stats(sample_kb["name"])

        assert stats["total_documents"] == 0
        assert stats["total_chunks"] == 0
        assert stats["last_updated"] is None
        assert stats["kb_type"] == "generic"

    @patch('app.core.kb_metadata.get_sqlite_manager')
    def test_get_documents_metadata_sorted_by_date(self, mock_get_db, sample_kb):
        """Test that get_documents_metadata sorts by upload date."""
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = True

        # Create documents with different dates
        docs = []
        for i in range(5):
            upload_date = f"2023-01-{i:02d}T00:00:00"
            docs.append({
                "metadata": {
                    "filename": f"test_{i}.txt",
                    "upload_date": upload_date,
                    "chunk_index": 0
                }
            })

        # Shuffle to test sorting
        import random
        random.shuffle(docs)

        mock_db.get_documents_by_metadata.return_value = docs
        mock_get_db.return_value = mock_db

        metadata = get_documents_metadata(sample_kb["name"])

        # Should be sorted by date (newest first)
        dates = [doc["upload_date"] for doc in metadata]
        assert dates == sorted(dates, reverse=True)

        # First should be newest (01-05)
        assert metadata[0]["filename"] == "test_4.txt"
        # Last should be oldest (01-01)
        assert metadata[-1]["filename"] == "test_0.txt"

    @patch('app.core.kb_metadata.get_sqlite_manager')
    def test_get_documents_metadata_error_handling(self, mock_get_db):
        """Test get_documents_metadata error handling."""
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = True
        mock_db.get_documents_by_metadata.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_db

        metadata = get_documents_metadata("test_kb")

        # Should return empty list on error
        assert metadata == []

    @patch('app.core.kb_metadata.get_sqlite_manager')
    def test_get_collection_stats_error_handling(self, mock_get_db):
        """Test get_collection_stats error handling."""
        mock_db = MagicMock()
        mock_db.collection_exists.return_value = True
        mock_db.get_collection_metadata.side_effect = Exception("Database error")
        mock_db.get_documents_by_metadata.side_effect = Exception("Database error")
        mock_get_db.return_value = mock_db

        stats = get_collection_stats("test_kb")

        # Should return default stats on error
        assert stats["total_documents"] == 0
        assert stats["total_chunks"] == 0
        assert stats["last_updated"] is None
        assert stats["kb_type"] == "generic"