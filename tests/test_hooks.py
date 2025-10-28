"""
Tests for hooks system functionality.
"""

import pytest
import tempfile
import json
import hashlib
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from app.core.hooks import ProjectHook, get_project_hook
from app.core.sqlite_manager import SQLiteManager


@pytest.mark.unit
class TestProjectHook:
    """Test ProjectHook class."""

    def test_hook_initialization(self, clean_db):
        """Test hook initialization."""
        # Create a project first
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", "/path/to/project")

        hook = ProjectHook(project["id"])

        assert hook.project_id == project["id"]
        assert hook.db_manager == db_manager
        assert hook.hooks_config_path.name == "hooks.json"

    def test_get_hooks_config_path(self, clean_db):
        """Test hooks config path generation."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", "/path/to/project")

        hook = ProjectHook(project["id"])
        config_path = hook._get_hooks_config_path()

        expected_path = Path("/path/to/project") / ".claude-os" / "hooks.json"
        assert config_path == expected_path

    def test_load_hooks_config_not_exists(self, clean_db):
        """Test loading hooks config when file doesn't exist."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", "/path/to/project")

        hook = ProjectHook(project["id"])
        config = hook._load_hooks_config()

        # Should return default config
        assert config["version"] == "1.0"
        assert config["project_id"] == project["id"]
        assert config["hooks"] == {}
        assert "created_at" in config

    def test_load_hooks_config_exists(self, clean_db, tmp_path):
        """Test loading existing hooks config."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        # Create hooks config file
        hooks_dir = Path(tmp_path) / ".claude-os"
        hooks_dir.mkdir()
        config_file = hooks_dir / "hooks.json"

        existing_config = {
            "version": "1.0",
            "project_id": project["id"],
            "created_at": "2023-01-01T00:00:00",
            "hooks": {
                "knowledge_docs": {
                    "enabled": True,
                    "folder_path": "/docs"
                }
            }
        }

        config_file.write_text(json.dumps(existing_config))

        hook = ProjectHook(project["id"])
        config = hook._load_hooks_config()

        assert config == existing_config

    def test_save_hooks_config(self, clean_db, tmp_path):
        """Test saving hooks config."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        hook = ProjectHook(project["id"])

        # Modify config
        config = hook._load_hooks_config()
        config["hooks"]["test_hook"] = {"enabled": True}

        hook._save_hooks_config(config)

        # Verify file was saved
        config_file = Path(tmp_path) / ".claude-os" / "hooks.json"
        assert config_file.exists()

        saved_config = json.loads(config_file.read_text())
        assert saved_config["hooks"]["test_hook"]["enabled"] is True
        assert "updated_at" in saved_config

    def test_enable_kb_autosync_success(self, clean_db, tmp_path):
        """Test enabling KB autosync successfully."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        # Create folder to watch
        watch_dir = tmp_path / "docs"
        watch_dir.mkdir()

        hook = ProjectHook(project["id"])

        result = hook.enable_kb_autosync(
            mcp_type="knowledge_docs",
            folder_path=str(watch_dir),
            file_patterns=["*.md", "*.txt"]
        )

        assert result["enabled"] is True
        assert result["mcp_type"] == "knowledge_docs"
        assert result["folder_path"] == str(watch_dir)
        assert result["file_patterns"] == ["*.md", "*.txt"]
        assert "created_at" in result
        assert "last_sync" in result
        assert "synced_files" in result

    def test_enable_kb_autosync_invalid_folder(self, clean_db, tmp_path):
        """Test enabling KB autosync with invalid folder."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        hook = ProjectHook(project["id"])

        with pytest.raises(ValueError, match="Folder does not exist"):
            hook.enable_kb_autosync(
                mcp_type="knowledge_docs",
                folder_path="/nonexistent/folder"
            )

    def test_enable_kb_autosync_invalid_mcp_type(self, clean_db, tmp_path):
        """Test enabling KB autosync with invalid MCP type."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        hook = ProjectHook(project["id"])

        with pytest.raises(ValueError, match="Invalid MCP type"):
            hook.enable_kb_autosync(
                mcp_type="invalid_type",
                folder_path=str(tmp_path)
            )

    def test_enable_kb_autosync_default_patterns(self, clean_db, tmp_path):
        """Test enabling KB autosync with default file patterns."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        watch_dir = tmp_path / "docs"
        watch_dir.mkdir()

        hook = ProjectHook(project["id"])

        result = hook.enable_kb_autosync(
            mcp_type="knowledge_docs",
            folder_path=str(watch_dir)
            # No file_patterns specified
        )

        # Should use default patterns from Config
        assert "file_patterns" in result
        assert len(result["file_patterns"]) > 0

    def test_disable_kb_autosync(self, clean_db, tmp_path):
        """Test disabling KB autosync."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        hook = ProjectHook(project["id"])

        # First enable it
        hook.enable_kb_autosync(
            mcp_type="knowledge_docs",
            folder_path=str(tmp_path)
        )

        # Then disable it
        hook.disable_kb_autosync("knowledge_docs")

        # Check config was updated
        config = hook._load_hooks_config()
        assert config["hooks"]["knowledge_docs"]["enabled"] is False

    def test_disable_kb_autosync_not_found(self, clean_db, tmp_path):
        """Test disabling KB autosync for non-existent hook."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        hook = ProjectHook(project["id"])

        with pytest.raises(ValueError, match="Hook for .* not found"):
            hook.disable_kb_autosync("nonexistent_hook")

    @patch('app.core.hooks.ingest_documents')
    def test_sync_kb_folder_success(self, mock_ingest, clean_db, tmp_path):
        """Test successful KB folder sync."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        # Create KB
        kb = db_manager.create_collection("test_kb", "generic")
        db_manager.assign_kb_to_project(project["id"], kb["id"], "knowledge_docs")

        # Create files to sync
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        (docs_dir / "file1.txt").write_text("Content 1")
        (docs_dir / "file2.md").write_text("# Content 2")
        (docs_dir / "ignore.xyz").write_text("Should be ignored")

        # Enable hook
        hook = ProjectHook(project["id"])
        hook.enable_kb_autosync(
            mcp_type="knowledge_docs",
            folder_path=str(docs_dir),
            file_patterns=[".txt", ".md"]
        )

        result = hook.sync_kb_folder("knowledge_docs")

        assert result["mcp_type"] == "knowledge_docs"
        assert result["folder_path"] == str(docs_dir)
        assert result["synced_files"] == 2
        assert result["skipped_files"] == 0
        assert result["errors"] == 0
        assert len(result["files_synced"]) == 2
        assert "file1.txt" in str(result["files_synced"])
        assert "file2.md" in str(result["files_synced"])

        # Check ingest was called
        mock_ingest.assert_called_once()

    @patch('app.core.hooks.ingest_documents')
    def test_sync_kb_folder_with_unchanged_files(self, mock_ingest, clean_db, tmp_path):
        """Test KB folder sync with unchanged files."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        # Create KB
        kb = db_manager.create_collection("test_kb", "generic")
        db_manager.assign_kb_to_project(project["id"], kb["id"], "knowledge_docs")

        # Create files
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        test_file = docs_dir / "file1.txt"
        test_file.write_text("Content 1")

        # Enable hook
        hook = ProjectHook(project["id"])
        hook.enable_kb_autosync(
            mcp_type="knowledge_docs",
            folder_path=str(docs_dir),
            file_patterns=[".txt"]
        )

        # First sync
        hook.sync_kb_folder("knowledge_docs")

        # Reset mock
        mock_ingest.reset_mock()

        # Second sync (should skip unchanged file)
        result = hook.sync_kb_folder("knowledge_docs")

        assert result["synced_files"] == 0
        assert result["skipped_files"] == 1
        assert result["errors"] == 0

        # Ingest should not be called for unchanged files
        mock_ingest.assert_not_called()

    @patch('app.core.hooks.ingest_documents')
    def test_sync_kb_folder_with_errors(self, mock_ingest, clean_db, tmp_path):
        """Test KB folder sync with ingestion errors."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        # Create KB
        kb = db_manager.create_collection("test_kb", "generic")
        db_manager.assign_kb_to_project(project["id"], kb["id"], "knowledge_docs")

        # Create files
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "file1.txt").write_text("Content 1")
        (docs_dir / "file2.txt").write_text("Content 2")

        # Mock ingest to fail for second file
        mock_ingest.side_effect = [
            None,  # Success for first file
            Exception("Ingestion failed")  # Fail for second
        ]

        # Enable hook
        hook = ProjectHook(project["id"])
        hook.enable_kb_autosync(
            mcp_type="knowledge_docs",
            folder_path=str(docs_dir),
            file_patterns=[".txt"]
        )

        result = hook.sync_kb_folder("knowledge_docs")

        assert result["synced_files"] == 1
        assert result["skipped_files"] == 0
        assert result["errors"] == 1
        assert len(result["errors"]) == 1
        assert "Ingestion failed" in result["errors"][0]["error"]

    def test_sync_kb_folder_not_enabled(self, clean_db, tmp_path):
        """Test syncing folder for hook that's not enabled."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        hook = ProjectHook(project["id"])

        with pytest.raises(ValueError, match="Hook for .* not found"):
            hook.sync_kb_folder("knowledge_docs")

    def test_sync_kb_folder_no_kb_assigned(self, clean_db, tmp_path):
        """Test syncing folder when no KB is assigned."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        # Create docs dir but don't assign KB
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        hook = ProjectHook(project["id"])
        hook.enable_kb_autosync(
            mcp_type="knowledge_docs",
            folder_path=str(docs_dir)
        )

        with pytest.raises(ValueError, match="No KB assigned"):
            hook.sync_kb_folder("knowledge_docs")

    def test_sync_all_folders(self, clean_db, tmp_path):
        """Test syncing all enabled folders."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        # Create KBs
        kb1 = db_manager.create_collection("kb1", "generic")
        kb2 = db_manager.create_collection("kb2", "generic")
        db_manager.assign_kb_to_project(project["id"], kb1["id"], "knowledge_docs")
        db_manager.assign_kb_to_project(project["id"], kb2["id"], "project_profile")

        # Create folders
        docs_dir = tmp_path / "docs"
        profile_dir = tmp_path / "profile"
        docs_dir.mkdir()
        profile_dir.mkdir()

        (docs_dir / "file1.txt").write_text("Docs content")
        (profile_dir / "file2.txt").write_text("Profile content")

        # Enable hooks
        hook = ProjectHook(project["id"])
        hook.enable_kb_autosync("knowledge_docs", str(docs_dir))
        hook.enable_kb_autosync("project_profile", str(profile_dir))

        with patch('app.core.hooks.ingest_documents') as mock_ingest:
            mock_ingest.return_value = None

            results = hook.sync_all_folders()

            assert "knowledge_docs" in results
            assert "project_profile" in results
            assert results["knowledge_docs"]["synced_files"] == 1
            assert results["project_profile"]["synced_files"] == 1

    def test_get_hook_status_single(self, clean_db, tmp_path):
        """Test getting status for single hook."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        hook = ProjectHook(project["id"])
        hook.enable_kb_autosync(
            mcp_type="knowledge_docs",
            folder_path=str(tmp_path)
        )

        status = hook.get_hook_status("knowledge_docs")

        assert status["enabled"] is True
        assert status["folder_path"] == str(tmp_path)
        assert "file_patterns" in status
        assert "created_at" in status

    def test_get_hook_status_all(self, clean_db, tmp_path):
        """Test getting status for all hooks."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        hook = ProjectHook(project["id"])
        hook.enable_kb_autosync("knowledge_docs", str(tmp_path))
        hook.enable_kb_autosync("project_profile", str(tmp_path))

        status = hook.get_hook_status()

        assert status["project_id"] == project["id"]
        assert status["total_hooks"] == 2
        assert status["enabled_hooks"] == 2
        assert "knowledge_docs" in status["hooks"]
        assert "project_profile" in status["hooks"]
        assert status["hooks_config_path"] == str(hook.hooks_config_path)

    def test_get_hook_status_not_found(self, clean_db, tmp_path):
        """Test getting status for non-existent hook."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        hook = ProjectHook(project["id"])

        status = hook.get_hook_status("nonexistent_hook")

        assert "error" in status
        assert "not found" in status["error"]

    def test_compute_file_hash(self, tmp_path):
        """Test file hash computation."""
        hook = ProjectHook(999)  # Dummy project ID

        # Create test file
        test_file = tmp_path / "test.txt"
        test_content = "Test content for hashing"
        test_file.write_text(test_content)

        computed_hash = hook._compute_file_hash(test_file)

        # Compute expected hash
        expected_hash = hashlib.sha256(test_content.encode()).hexdigest()

        assert computed_hash == expected_hash

    def test_compute_file_hash_binary(self, tmp_path):
        """Test file hash computation for binary file."""
        hook = ProjectHook(999)  # Dummy project ID

        # Create binary file
        test_file = tmp_path / "test.bin"
        test_content = b"\x00\x01\x02\x03\x04\x05"
        test_file.write_bytes(test_content)

        computed_hash = hook._compute_file_hash(test_file)

        # Compute expected hash
        expected_hash = hashlib.sha256(test_content).hexdigest()

        assert computed_hash == expected_hash


@pytest.mark.unit
class TestProjectHookUtility:
    """Test ProjectHook utility functions."""

    def test_get_project_hook(self, clean_db):
        """Test get_project_hook utility function."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", "/path/to/project")

        hook1 = get_project_hook(project["id"])
        hook2 = get_project_hook(project["id"])

        # Should return new instances each time
        assert hook1 is not hook2
        assert hook1.project_id == project["id"]
        assert hook2.project_id == project["id"]
        assert hook1.db_manager == db_manager
        assert hook2.db_manager == db_manager

    def test_get_project_hook_different_projects(self, clean_db):
        """Test get_project_hook with different projects."""
        db_manager = SQLiteManager()
        project1 = db_manager.create_project("project1", "/path/1")
        project2 = db_manager.create_project("project2", "/path/2")

        hook1 = get_project_hook(project1["id"])
        hook2 = get_project_hook(project2["id"])

        assert hook1.project_id == project1["id"]
        assert hook2.project_id == project2["id"]
        assert hook1.project_id != hook2.project_id

    @patch('app.core.hooks.ProjectHook')
    def test_get_project_hook_with_invalid_project(self, mock_hook_class, clean_db):
        """Test get_project_hook with invalid project ID."""
        mock_hook_class.side_effect = ValueError("Project not found")

        with pytest.raises(ValueError, match="Project not found"):
            get_project_hook(99999)


@pytest.mark.integration
class TestProjectHookIntegration:
    """Integration tests for ProjectHook."""

    def test_full_hook_lifecycle(self, clean_db, tmp_path):
        """Test complete hook lifecycle."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        # Create KB
        kb = db_manager.create_collection("test_kb", "generic")
        db_manager.assign_kb_to_project(project["id"], kb["id"], "knowledge_docs")

        # Create folder and files
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        test_file = docs_dir / "test.txt"
        test_file.write_text("Initial content")

        # Enable hook
        hook = ProjectHook(project["id"])
        result = hook.enable_kb_autosync(
            mcp_type="knowledge_docs",
            folder_path=str(docs_dir)
        )

        assert result["enabled"] is True

        # Sync (should ingest file)
        with patch('app.core.hooks.ingest_documents') as mock_ingest:
            mock_ingest.return_value = None

            sync_result = hook.sync_kb_folder("knowledge_docs")
            assert sync_result["synced_files"] == 1
            mock_ingest.assert_called_once()

        # Modify file and sync again (should ingest again)
        test_file.write_text("Modified content")

        with patch('app.core.hooks.ingest_documents') as mock_ingest:
            mock_ingest.return_value = None

            sync_result = hook.sync_kb_folder("knowledge_docs")
            assert sync_result["synced_files"] == 1
            mock_ingest.assert_called_once()

        # Disable hook
        hook.disable_kb_autosync("knowledge_docs")

        status = hook.get_hook_status("knowledge_docs")
        assert status["enabled"] is False

    def test_hook_config_persistence(self, clean_db, tmp_path):
        """Test that hook config persists across instances."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        # Create hook and enable autosync
        hook1 = ProjectHook(project["id"])
        hook1.enable_kb_autosync(
            mcp_type="knowledge_docs",
            folder_path=str(tmp_path),
            file_patterns=[".txt", ".md"]
        )

        # Create new instance
        hook2 = ProjectHook(project["id"])
        status = hook2.get_hook_status("knowledge_docs")

        # Should have persisted config
        assert status["enabled"] is True
        assert status["folder_path"] == str(tmp_path)
        assert status["file_patterns"] == [".txt", ".md"]

    def test_multiple_hooks_independence(self, clean_db, tmp_path):
        """Test that multiple hooks work independently."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        # Create KBs
        kb1 = db_manager.create_collection("kb1", "generic")
        kb2 = db_manager.create_collection("kb2", "generic")
        db_manager.assign_kb_to_project(project["id"], kb1["id"], "knowledge_docs")
        db_manager.assign_kb_to_project(project["id"], kb2["id"], "project_profile")

        # Create folders
        docs_dir = tmp_path / "docs"
        profile_dir = tmp_path / "profile"
        docs_dir.mkdir()
        profile_dir.mkdir()

        (docs_dir / "doc.txt").write_text("Docs content")
        (profile_dir / "profile.txt").write_text("Profile content")

        # Enable both hooks
        hook = ProjectHook(project["id"])
        hook.enable_kb_autosync("knowledge_docs", str(docs_dir))
        hook.enable_kb_autosync("project_profile", str(profile_dir))

        # Sync both
        with patch('app.core.hooks.ingest_documents') as mock_ingest:
            mock_ingest.return_value = None

            results = hook.sync_all_folders()

            # Both should have synced
            assert results["knowledge_docs"]["synced_files"] == 1
            assert results["project_profile"]["synced_files"] == 1

            # Should have called ingest twice
            assert mock_ingest.call_count == 2

    def test_hook_error_recovery(self, clean_db, tmp_path):
        """Test hook error recovery and resilience."""
        db_manager = SQLiteManager()
        project = db_manager.create_project("test_project", str(tmp_path))

        # Create KB
        kb = db_manager.create_collection("test_kb", "generic")
        db_manager.assign_kb_to_project(project["id"], kb["id"], "knowledge_docs")

        # Create folder with problematic file
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "good.txt").write_text("Good content")
        (docs_dir / "bad.txt").write_text("Bad content")

        # Enable hook
        hook = ProjectHook(project["id"])
        hook.enable_kb_autosync("knowledge_docs", str(docs_dir))

        # Mock ingest to fail for bad file
        with patch('app.core.hooks.ingest_documents') as mock_ingest:
            def ingest_side_effect(kb_name, documents, metadatas):
                # Fail if contains "bad"
                if any("bad" in meta.get("filename", "") for meta in metadatas):
                    raise Exception("Bad file detected")
                return None

            mock_ingest.side_effect = ingest_side_effect

            # Sync should handle error gracefully
            result = hook.sync_kb_folder("knowledge_docs")

            # Should have one success and one error
            assert result["synced_files"] == 1
            assert result["errors"] == 1
            assert "Bad file detected" in result["errors"][0]["error"]