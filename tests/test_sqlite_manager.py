"""
Tests for SQLite database manager operations.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

from app.core.sqlite_manager import SQLiteManager, generate_slug, get_sqlite_manager
from app.core.kb_types import KBType


@pytest.mark.unit
class TestSQLiteManager:
    """Test SQLite manager basic operations."""

    def test_generate_slug(self):
        """Test slug generation function."""
        test_cases = [
            ("My Agent OS", "my-agent-os"),
            ("My Code Base!", "my-code-base"),
            ("Test_KB 123", "test-kb-123"),
            ("Hello World", "hello-world"),
            ("Multiple   Spaces", "multiple-spaces"),
            ("Special@#$%Chars", "specialchars"),
            ("", ""),
        ]

        for input_name, expected_slug in test_cases:
            result = generate_slug(input_name)
            assert result == expected_slug, f"Failed for input: {input_name}"

    def test_sqlite_manager_initialization(self):
        """Test SQLite manager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            manager = SQLiteManager(str(db_path))

            assert manager.db_path == str(db_path)
            assert Path(db_path).exists()

    def test_create_collection(self, clean_db):
        """Test creating a knowledge base collection."""
        result = clean_db.create_collection(
            name="test_collection",
            kb_type=KBType.GENERIC,
            description="Test collection",
            tags=["test", "example"]
        )

        assert result["name"] == "test_collection"
        assert result["kb_type"] == "generic"
        assert result["description"] == "Test collection"
        assert "id" in result
        assert "slug" in result
        assert "created_at" in result

    def test_create_collection_duplicate_name(self, clean_db):
        """Test creating collection with duplicate name."""
        # Create first collection
        clean_db.create_collection("duplicate_test", KBType.GENERIC)

        # Try to create duplicate
        with pytest.raises(ValueError, match="already exists"):
            clean_db.create_collection("duplicate_test", KBType.CODE)

    def test_create_collection_slug_conflict(self, clean_db):
        """Test creating collection with slug conflict."""
        # Create first collection
        clean_db.create_collection("Test Collection", KBType.GENERIC)

        # Try to create collection with similar slug
        with pytest.raises(ValueError, match="slug conflict"):
            clean_db.create_collection("test-collection", KBType.CODE)

    def test_list_collections(self, clean_db):
        """Test listing all collections."""
        # Create a sample kb first
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        collections = clean_db.list_collections()

        assert isinstance(collections, list)
        assert len(collections) >= 1
        assert any(col["name"] == kb_data["name"] for col in collections)

    def test_get_collection_metadata(self, clean_db):
        """Test getting collection metadata."""
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        metadata = clean_db.get_collection_metadata(kb_data["name"])

        assert metadata["kb_type"] == KBType.GENERIC.value
        assert "description" in metadata
        assert "created_at" in metadata

    def test_get_collection_metadata_not_found(self, clean_db):
        """Test getting metadata for non-existent collection."""
        with pytest.raises(ValueError, match="not found"):
            clean_db.get_collection_metadata("nonexistent_collection")

    def test_delete_collection(self, clean_db):
        """Test deleting a collection."""
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        # Verify collection exists
        assert clean_db.collection_exists(kb_data["name"])

        # Delete it
        result = clean_db.delete_collection(kb_data["name"])
        assert result is True

        # Verify it's gone
        assert not clean_db.collection_exists(kb_data["name"])

    def test_delete_collection_not_found(self, clean_db):
        """Test deleting non-existent collection."""
        result = clean_db.delete_collection("nonexistent_collection")
        assert result is False

    def test_collection_exists(self, clean_db):
        """Test checking if collection exists."""
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        assert clean_db.collection_exists(kb_data["name"]) is True
        assert clean_db.collection_exists("nonexistent_collection") is False

    def test_get_collection_count(self, clean_db):
        """Test getting document count for collection."""
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        # Add some documents
        documents = ["Test document 1", "Test document 2"]
        embeddings = [[0.1] * 768, [0.2] * 768]
        metadatas = [{"filename": "doc1.txt"}, {"filename": "doc2.txt"}]
        ids = ["doc1", "doc2"]

        clean_db.add_documents(
            kb_name=kb_data["name"],
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        count = clean_db.get_collection_count(kb_data["name"])
        assert count == 2

    def test_get_collection_count_empty(self, clean_db):
        """Test getting document count for empty collection."""
        # Create empty collection
        clean_db.create_collection("empty_collection", KBType.GENERIC)

        count = clean_db.get_collection_count("empty_collection")
        assert count == 0

    def test_get_collection_by_id(self, clean_db):
        """Test getting collection by ID."""
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        collection = clean_db.get_collection_by_id(kb_data["id"])
        assert collection is not None
        assert collection["name"] == kb_data["name"]
        assert collection["id"] == kb_data["id"]

    def test_get_collection_by_id_not_found(self, clean_db):
        """Test getting non-existent collection by ID."""
        collection = clean_db.get_collection_by_id(99999)
        assert collection is None

    def test_list_collections_by_type(self, clean_db):
        """Test listing collections filtered by type."""
        # Create collections of different types
        clean_db.create_collection("generic_kb", KBType.GENERIC)
        clean_db.create_collection("code_kb", KBType.CODE)
        clean_db.create_collection("docs_kb", KBType.DOCUMENTATION)

        # Get only code collections
        code_collections = clean_db.list_collections_by_type(KBType.CODE)
        assert len(code_collections) == 1
        assert code_collections[0]["metadata"]["kb_type"] == "code"

    def test_get_kb_by_slug(self, clean_db):
        """Test getting KB by slug."""
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        kb_name = clean_db.get_kb_by_slug(kb_data["slug"])
        assert kb_name == kb_data["name"]

    def test_get_kb_by_slug_not_found(self, clean_db):
        """Test getting non-existent KB by slug."""
        kb_name = clean_db.get_kb_by_slug("nonexistent-slug")
        assert kb_name is None

    def test_slug_exists(self, clean_db):
        """Test checking if slug exists."""
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        assert clean_db.slug_exists(kb_data["slug"]) is True
        assert clean_db.slug_exists("nonexistent-slug") is False


@pytest.mark.integration
class TestSQLiteManagerDocuments:
    """Test SQLite manager document operations."""

    def test_add_documents(self, clean_db):
        """Test adding documents to collection."""
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        documents = ["Test document 1", "Test document 2"]
        embeddings = [[0.1] * 768, [0.2] * 768]
        metadatas = [{"filename": "doc1.txt"}, {"filename": "doc2.txt"}]
        ids = ["doc1", "doc2"]

        clean_db.add_documents(
            kb_name=kb_data["name"],
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        # Verify documents were added
        count = clean_db.get_collection_count(kb_data["name"])
        assert count == 2

    def test_add_documents_nonexistent_collection(self, clean_db):
        """Test adding documents to non-existent collection."""
        with pytest.raises(ValueError, match="not found"):
            clean_db.add_documents(
                kb_name="nonexistent_collection",
                documents=["test"],
                embeddings=[[0.1] * 768],
                metadatas=[{}],
                ids=["test"]
            )

    def test_get_documents_by_metadata(self, clean_db):
        """Test retrieving documents by metadata filter."""
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        # Add documents with metadata
        for i in range(5):
            np.random.seed(42 + i)
            embedding = np.random.randn(768).tolist()
            clean_db.add_documents(
                kb_name=kb_data["name"],
                documents=[f"This is test document {i}"],
                embeddings=[embedding],
                metadatas=[{"filename": f"test_{i}.txt", "chunk_index": i}],
                ids=[f"node_doc_{i}"]
            )

        # Get all documents
        all_docs = clean_db.get_documents_by_metadata(
            kb_name=kb_data["name"],
            where={}
        )
        assert len(all_docs) == 5

        # Filter by filename
        filtered_docs = clean_db.get_documents_by_metadata(
            kb_name=kb_data["name"],
            where={"filename": "test_0.txt"}
        )
        assert len(filtered_docs) == 1
        assert filtered_docs[0]["metadata"]["filename"] == "test_0.txt"

    def test_query_documents(self, clean_db):
        """Test querying documents by vector similarity."""
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        # Add documents
        for i in range(5):
            np.random.seed(42 + i)
            embedding = np.random.randn(768).tolist()
            clean_db.add_documents(
                kb_name=kb_data["name"],
                documents=[f"This is test document {i}"],
                embeddings=[embedding],
                metadatas=[{"filename": f"test_{i}.txt"}],
                ids=[f"node_doc_{i}"]
            )

        query_embedding = [0.1] * 768
        results = clean_db.query_documents(
            kb_name=kb_data["name"],
            query_embedding=query_embedding,
            n_results=3
        )

        assert "ids" in results
        assert "documents" in results
        assert "metadatas" in results
        assert "distances" in results
        assert len(results["ids"][0]) <= 3

    def test_query_documents_nonexistent_collection(self, clean_db):
        """Test querying non-existent collection."""
        with pytest.raises(ValueError, match="not found"):
            clean_db.query_documents(
                kb_name="nonexistent_collection",
                query_embedding=[0.1] * 768
            )

    def test_query_similar(self, clean_db):
        """Test querying similar documents by KB ID."""
        kb_data = clean_db.create_collection(
            name="test_kb",
            kb_type=KBType.GENERIC,
            description="Test knowledge base"
        )

        # Add documents
        for i in range(5):
            np.random.seed(42 + i)
            embedding = np.random.randn(768).tolist()
            clean_db.add_documents(
                kb_name=kb_data["name"],
                documents=[f"This is test document {i}"],
                embeddings=[embedding],
                metadatas=[{"filename": f"test_{i}.txt"}],
                ids=[f"node_doc_{i}"]
            )

        query_embedding = [0.1] * 768
        results = clean_db.query_similar(
            kb_id=kb_data["id"],
            query_embedding=query_embedding,
            top_k=3
        )

        assert isinstance(results, list)
        assert len(results) <= 3

        if results:  # If we have results
            for result in results:
                assert "doc_id" in result
                assert "text" in result
                assert "metadata" in result
                assert "similarity" in result
                assert isinstance(result["similarity"], float)


@pytest.mark.integration
class TestSQLiteManagerProjects:
    """Test SQLite manager project operations."""

    def test_create_project(self, clean_db):
        """Test creating a project."""
        result = clean_db.create_project(
            name="test_project",
            path="/path/to/project",
            description="Test project",
            metadata={"type": "test"}
        )

        assert result["name"] == "test_project"
        assert result["path"] == "/path/to/project"
        assert result["description"] == "Test project"
        assert result["metadata"]["type"] == "test"
        assert "id" in result
        assert "created_at" in result

    def test_create_project_duplicate(self, clean_db):
        """Test creating duplicate project."""
        clean_db.create_project("duplicate_project", "/path/1")

        with pytest.raises(ValueError, match="already exists"):
            clean_db.create_project("duplicate_project", "/path/2")

    def test_get_project(self, clean_db):
        """Test getting project by ID."""
        created = clean_db.create_project("test_project", "/path/to/project")
        retrieved = clean_db.get_project(created["id"])

        assert retrieved is not None
        assert retrieved["name"] == "test_project"
        assert retrieved["path"] == "/path/to/project"

    def test_get_project_not_found(self, clean_db):
        """Test getting non-existent project."""
        project = clean_db.get_project(99999)
        assert project is None

    def test_list_projects(self, clean_db):
        """Test listing all projects."""
        # Create multiple projects
        clean_db.create_project("project1", "/path/1")
        clean_db.create_project("project2", "/path/2")

        projects = clean_db.list_projects()
        assert len(projects) >= 2

        project_names = [p["name"] for p in projects]
        assert "project1" in project_names
        assert "project2" in project_names

    def test_assign_kb_to_project(self, clean_db):
        """Test assigning KB to project."""
        # Create project and KB
        project = clean_db.create_project("test_project", "/path")
        kb = clean_db.create_collection("test_kb", KBType.GENERIC)

        # Assign KB to project
        assignment = clean_db.assign_kb_to_project(
            project_id=project["id"],
            kb_id=kb["id"],
            mcp_type="knowledge_docs"
        )

        assert assignment["project_id"] == project["id"]
        assert assignment["kb_id"] == kb["id"]
        assert assignment["mcp_type"] == "knowledge_docs"

    def test_get_project_kbs(self, clean_db):
        """Test getting KB assignments for project."""
        # Create project and KBs
        project = clean_db.create_project("test_project", "/path")
        kb1 = clean_db.create_collection("kb1", KBType.GENERIC)
        kb2 = clean_db.create_collection("kb2", KBType.CODE)

        # Assign KBs
        clean_db.assign_kb_to_project(project["id"], kb1["id"], "knowledge_docs")
        clean_db.assign_kb_to_project(project["id"], kb2["id"], "project_profile")

        # Get assignments
        kbs = clean_db.get_project_kbs(project["id"])
        assert kbs["knowledge_docs"] == kb1["id"]
        assert kbs["project_profile"] == kb2["id"]

    def test_get_project_mcps_detailed(self, clean_db):
        """Test getting detailed MCP info for project."""
        # Create project and KB
        project = clean_db.create_project("test_project", "/path")
        kb = clean_db.create_collection("test_kb", KBType.GENERIC)

        # Assign KB
        clean_db.assign_kb_to_project(project["id"], kb["id"], "knowledge_docs")

        # Get detailed info
        mcps = clean_db.get_project_mcps_detailed(project["id"])
        assert "knowledge_docs" in mcps
        assert mcps["knowledge_docs"]["kb_id"] == kb["id"]
        assert mcps["knowledge_docs"]["kb_name"] == "test_kb"

    def test_set_kb_folder(self, clean_db):
        """Test setting KB folder configuration."""
        project = clean_db.create_project("test_project", "/path")

        folder_config = clean_db.set_kb_folder(
            project_id=project["id"],
            mcp_type="knowledge_docs",
            folder_path="/path/to/docs",
            auto_sync=True
        )

        assert folder_config["project_id"] == project["id"]
        assert folder_config["mcp_type"] == "knowledge_docs"
        assert folder_config["folder_path"] == "/path/to/docs"
        assert folder_config["auto_sync"] is True

    def test_get_kb_folders(self, clean_db):
        """Test getting KB folder configurations."""
        project = clean_db.create_project("test_project", "/path")

        # Set multiple folder configs
        clean_db.set_kb_folder(project["id"], "knowledge_docs", "/docs", True)
        clean_db.set_kb_folder(project["id"], "project_profile", "/profile", False)

        # Get all configs
        folders = clean_db.get_kb_folders(project["id"])
        assert folders["knowledge_docs"]["folder_path"] == "/docs"
        assert folders["knowledge_docs"]["auto_sync"] is True
        assert folders["project_profile"]["folder_path"] == "/profile"
        assert folders["project_profile"]["auto_sync"] is False


@pytest.mark.unit
class TestSQLiteManagerSingleton:
    """Test SQLite manager singleton pattern."""

    def test_get_sqlite_manager_singleton(self):
        """Test that get_sqlite_manager returns singleton."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"

            manager1 = get_sqlite_manager(str(db_path))
            manager2 = get_sqlite_manager(str(db_path))

            # Should be the same instance
            assert manager1 is manager2

    def test_get_sqlite_manager_default_path(self):
        """Test get_sqlite_manager with default path."""
        # This should use the default path from Config
        manager = get_sqlite_manager()
        assert manager is not None
        assert hasattr(manager, 'db_path')
