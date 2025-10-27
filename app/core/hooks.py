"""
Hook system for Claude OS projects.
Manages automatic indexing of project folders when files change.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable
from datetime import datetime
import hashlib

from app.core.sqlite_manager import get_sqlite_manager
from app.core.config import Config
from app.core.ingestion import ingest_documents

logger = logging.getLogger(__name__)


class ProjectHook:
    """Manages hooks for a specific project."""

    def __init__(self, project_id: int):
        """Initialize hook manager for a project."""
        self.project_id = project_id
        self.db_manager = get_sqlite_manager()
        self.hooks_config_path = self._get_hooks_config_path()

    def _get_hooks_config_path(self) -> Path:
        """Get path to hooks configuration file."""
        project = self.db_manager.get_project(self.project_id)
        if not project:
            raise ValueError(f"Project {self.project_id} not found")

        project_path = Path(project["path"])
        hooks_dir = project_path / ".claude-os"
        hooks_dir.mkdir(parents=True, exist_ok=True)

        return hooks_dir / "hooks.json"

    def _load_hooks_config(self) -> Dict:
        """Load hooks configuration from file."""
        if self.hooks_config_path.exists():
            with open(self.hooks_config_path, 'r') as f:
                return json.load(f)
        return {
            "version": "1.0",
            "project_id": self.project_id,
            "created_at": datetime.now().isoformat(),
            "hooks": {}
        }

    def _save_hooks_config(self, config: Dict):
        """Save hooks configuration to file."""
        config["updated_at"] = datetime.now().isoformat()
        with open(self.hooks_config_path, 'w') as f:
            json.dump(config, f, indent=2)

    def enable_kb_autosync(
        self,
        mcp_type: str,
        folder_path: str,
        file_patterns: Optional[List[str]] = None
    ) -> Dict:
        """
        Enable automatic KB synchronization for a folder.

        Args:
            mcp_type: knowledge_docs, project_profile, project_index, project_memories
            folder_path: Path to folder to watch
            file_patterns: List of file patterns to include (e.g., ["*.md", "*.py"])

        Returns:
            Hook configuration
        """
        folder_path = Path(folder_path)
        if not folder_path.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")

        # Verify MCP type is valid
        valid_types = ["knowledge_docs", "project_profile", "project_index", "project_memories"]
        if mcp_type not in valid_types:
            raise ValueError(f"Invalid MCP type. Must be one of: {', '.join(valid_types)}")

        # Load config
        config = self._load_hooks_config()

        # Default patterns
        if file_patterns is None:
            file_patterns = Config.SUPPORTED_FILE_TYPES

        # Create hook
        hook_config = {
            "enabled": True,
            "mcp_type": mcp_type,
            "folder_path": str(folder_path),
            "file_patterns": file_patterns,
            "created_at": datetime.now().isoformat(),
            "last_sync": None,
            "synced_files": {}  # Track file hashes to detect changes
        }

        config["hooks"][mcp_type] = hook_config

        # Save config
        self._save_hooks_config(config)

        logger.info(f"Enabled KB autosync for {mcp_type}: {folder_path}")

        return hook_config

    def disable_kb_autosync(self, mcp_type: str):
        """Disable automatic KB synchronization for an MCP type."""
        config = self._load_hooks_config()

        if mcp_type in config["hooks"]:
            config["hooks"][mcp_type]["enabled"] = False
            self._save_hooks_config(config)
            logger.info(f"Disabled KB autosync for {mcp_type}")
        else:
            raise ValueError(f"Hook for {mcp_type} not found")

    def sync_kb_folder(self, mcp_type: str) -> Dict:
        """
        Manually sync a KB folder (useful for initial setup or forced refresh).

        Args:
            mcp_type: knowledge_docs, project_profile, project_index, project_memories

        Returns:
            Sync results
        """
        config = self._load_hooks_config()

        if mcp_type not in config["hooks"]:
            raise ValueError(f"Hook for {mcp_type} not found")

        hook = config["hooks"][mcp_type]
        folder_path = Path(hook["folder_path"])

        if not folder_path.exists():
            raise ValueError(f"Folder does not exist: {folder_path}")

        # Get KB for this MCP type
        project_kbs = self.db_manager.get_project_kbs(self.project_id)
        if mcp_type not in project_kbs:
            raise ValueError(f"No KB assigned for {mcp_type}")

        kb_id = project_kbs[mcp_type]

        # Get KB name from id
        all_collections = self.db_manager.list_collections()
        kb_name = None
        for kb in all_collections:
            if kb.get("id") == kb_id:
                kb_name = kb["name"]
                break

        if not kb_name:
            raise ValueError(f"KB not found for {mcp_type}")

        # Find all matching files
        synced_files = []
        skipped_files = []
        errors = []

        file_patterns = hook.get("file_patterns", Config.SUPPORTED_FILE_TYPES)

        for file_path in folder_path.rglob("*"):
            if file_path.is_file():
                # Check if file matches patterns
                if not any(file_path.suffix.lower() == pattern.lower() for pattern in file_patterns):
                    continue

                # Compute file hash
                file_hash = self._compute_file_hash(file_path)

                # Skip if file hasn't changed
                if file_path.name in hook.get("synced_files", {}):
                    if hook["synced_files"][file_path.name] == file_hash:
                        skipped_files.append(str(file_path))
                        continue

                # Ingest file
                try:
                    logger.info(f"Ingesting {file_path} into {kb_name}")

                    # Read file content
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # Ingest document
                    ingest_documents(
                        kb_name,
                        [content],
                        [{"filename": file_path.name, "path": str(file_path)}]
                    )

                    # Update hash
                    hook["synced_files"][file_path.name] = file_hash
                    synced_files.append(str(file_path))

                except Exception as e:
                    logger.error(f"Error ingesting {file_path}: {e}")
                    errors.append({"file": str(file_path), "error": str(e)})

        # Update last sync time
        hook["last_sync"] = datetime.now().isoformat()
        self._save_hooks_config(config)

        results = {
            "mcp_type": mcp_type,
            "folder_path": str(folder_path),
            "synced_files": len(synced_files),
            "skipped_files": len(skipped_files),
            "errors": len(errors),
            "files_synced": synced_files,
            "files_skipped": skipped_files,
            "errors": errors
        }

        logger.info(f"Sync complete for {mcp_type}: {len(synced_files)} synced, {len(skipped_files)} skipped, {len(errors)} errors")

        return results

    def sync_all_folders(self) -> Dict:
        """Sync all enabled KB folders for the project."""
        config = self._load_hooks_config()
        results = {}

        for mcp_type, hook in config["hooks"].items():
            if hook.get("enabled", False):
                try:
                    results[mcp_type] = self.sync_kb_folder(mcp_type)
                except Exception as e:
                    logger.error(f"Error syncing {mcp_type}: {e}")
                    results[mcp_type] = {
                        "error": str(e),
                        "mcp_type": mcp_type
                    }

        return results

    def get_hook_status(self, mcp_type: Optional[str] = None) -> Dict:
        """Get status of hooks for the project."""
        config = self._load_hooks_config()

        if mcp_type:
            if mcp_type not in config["hooks"]:
                return {"error": f"Hook for {mcp_type} not found"}
            return config["hooks"][mcp_type]

        return {
            "project_id": self.project_id,
            "hooks_config_path": str(self.hooks_config_path),
            "total_hooks": len(config["hooks"]),
            "enabled_hooks": sum(1 for h in config["hooks"].values() if h.get("enabled", False)),
            "hooks": config["hooks"]
        }

    @staticmethod
    def _compute_file_hash(file_path: Path) -> str:
        """Compute SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()


def get_project_hook(project_id: int) -> ProjectHook:
    """Get or create ProjectHook instance for a project."""
    return ProjectHook(project_id)
