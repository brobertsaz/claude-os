"""
File system watcher for Claude OS project hooks.
Automatically syncs KB folders when files change.
"""

import os
import logging
import time
import threading
from pathlib import Path
from typing import Dict, Optional, Callable, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

from app.core.hooks import ProjectHook
from app.core.config import Config

logger = logging.getLogger(__name__)


class ProjectFileHandler(FileSystemEventHandler):
    """Handles file system events for a project hook."""

    def __init__(self, project_id: int, mcp_type: str, on_change: Callable):
        """
        Initialize file handler.

        Args:
            project_id: ID of the project
            mcp_type: Type of MCP (knowledge_docs, etc.)
            on_change: Callback function when files change
        """
        self.project_id = project_id
        self.mcp_type = mcp_type
        self.on_change = on_change
        self.debounce_timer: Optional[threading.Timer] = None
        self.debounce_delay = 2.0  # Debounce for 2 seconds

    def on_modified(self, event: FileModifiedEvent):
        """Handle file modifications."""
        if event.is_directory:
            return

        self._debounce_sync()

    def on_created(self, event: FileCreatedEvent):
        """Handle file creation."""
        if event.is_directory:
            return

        self._debounce_sync()

    def _debounce_sync(self):
        """Debounce sync calls to avoid multiple rapid syncs."""
        # Cancel previous timer if it exists
        if self.debounce_timer:
            self.debounce_timer.cancel()

        # Create new timer
        self.debounce_timer = threading.Timer(self.debounce_delay, self._trigger_sync)
        self.debounce_timer.start()

    def _trigger_sync(self):
        """Trigger the sync callback."""
        try:
            logger.info(f"File change detected for project {self.project_id}/{self.mcp_type}")
            self.on_change()
        except Exception as e:
            logger.error(f"Error syncing on file change: {e}")


class ProjectWatcher:
    """Watches a single project's hooks."""

    def __init__(self, project_id: int):
        """
        Initialize project watcher.

        Args:
            project_id: ID of the project to watch
        """
        self.project_id = project_id
        self.hook = ProjectHook(project_id)
        self.observer: Optional[Observer] = None
        self.event_handlers: Dict[str, ProjectFileHandler] = {}
        self.watched_paths: Dict[str, str] = {}

    def start(self):
        """Start watching project folders."""
        logger.info(f"Starting file watcher for project {self.project_id}")

        # Get hook status
        status = self.hook.get_hook_status()

        if not status.get("hooks"):
            logger.info(f"No hooks configured for project {self.project_id}")
            return

        # Start observer
        self.observer = Observer()

        # Watch each enabled hook
        for mcp_type, hook_config in status["hooks"].items():
            if not hook_config.get("enabled"):
                continue

            folder_path = hook_config.get("folder_path")
            if not folder_path or not Path(folder_path).exists():
                logger.warning(f"Hook folder does not exist: {folder_path}")
                continue

            # Create event handler
            handler = ProjectFileHandler(
                self.project_id,
                mcp_type,
                lambda mt=mcp_type: self._on_folder_change(mt),
            )

            # Schedule observer
            self.observer.schedule(handler, folder_path, recursive=True)
            self.event_handlers[mcp_type] = handler
            self.watched_paths[mcp_type] = folder_path

            logger.info(f"Watching {mcp_type}: {folder_path}")

        # Start observer if we have paths to watch
        if self.watched_paths:
            self.observer.start()
            logger.info(f"File watcher started for project {self.project_id}")
        else:
            logger.info(f"No enabled hooks to watch for project {self.project_id}")

    def stop(self):
        """Stop watching project folders."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info(f"File watcher stopped for project {self.project_id}")
            self.observer = None
            self.event_handlers.clear()
            self.watched_paths.clear()

    def _on_folder_change(self, mcp_type: str):
        """Handle folder change."""
        try:
            logger.info(f"Syncing {mcp_type} for project {self.project_id}")
            result = self.hook.sync_kb_folder(mcp_type)

            if result.get("synced_files"):
                logger.info(
                    f"Synced {len(result['synced_files'])} files for {mcp_type}"
                )
        except Exception as e:
            logger.error(f"Error syncing {mcp_type}: {e}")

    def restart(self):
        """Restart watcher (useful when hooks change)."""
        self.stop()
        self.start()


class GlobalFileWatcher:
    """Manages file watchers for all projects."""

    def __init__(self):
        """Initialize global file watcher."""
        self.watchers: Dict[int, ProjectWatcher] = {}
        self.lock = threading.Lock()
        self.enabled = False

    def start_project(self, project_id: int):
        """Start watching a project."""
        with self.lock:
            if project_id in self.watchers:
                logger.warning(f"Watcher already exists for project {project_id}")
                return

            watcher = ProjectWatcher(project_id)
            watcher.start()
            self.watchers[project_id] = watcher

    def stop_project(self, project_id: int):
        """Stop watching a project."""
        with self.lock:
            if project_id not in self.watchers:
                return

            watcher = self.watchers.pop(project_id)
            watcher.stop()

    def restart_project(self, project_id: int):
        """Restart watcher for a project."""
        with self.lock:
            if project_id in self.watchers:
                self.watchers[project_id].restart()
            else:
                self.start_project(project_id)

    def start_all(self, project_ids: List[int]):
        """Start watching all projects."""
        logger.info(f"Starting file watchers for {len(project_ids)} projects")

        for project_id in project_ids:
            try:
                self.start_project(project_id)
            except Exception as e:
                logger.error(f"Error starting watcher for project {project_id}: {e}")

        self.enabled = True

    def stop_all(self):
        """Stop watching all projects."""
        with self.lock:
            for watcher in self.watchers.values():
                try:
                    watcher.stop()
                except Exception as e:
                    logger.error(f"Error stopping watcher: {e}")

            self.watchers.clear()
            self.enabled = False

    def get_status(self) -> Dict:
        """Get status of all watchers."""
        with self.lock:
            return {
                "enabled": self.enabled,
                "projects_watched": len(self.watchers),
                "projects": {
                    project_id: {
                        "watched_paths": watcher.watched_paths,
                        "event_handlers": list(watcher.event_handlers.keys()),
                    }
                    for project_id, watcher in self.watchers.items()
                },
            }


# Global instance
_global_watcher: Optional[GlobalFileWatcher] = None


def get_global_watcher() -> GlobalFileWatcher:
    """Get or create global file watcher."""
    global _global_watcher
    if _global_watcher is None:
        _global_watcher = GlobalFileWatcher()
    return _global_watcher
