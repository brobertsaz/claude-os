"""
File system watcher for agent-os specs.
Automatically syncs specs to database when tasks.md files change.
"""

import os
import logging
import threading
from pathlib import Path
from typing import Dict, Optional, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

from app.core.spec_manager import SpecManager
from app.core.spec_parser import parse_spec_folder
from app.core.sqlite_manager import get_sqlite_manager

logger = logging.getLogger(__name__)


class SpecFileHandler(FileSystemEventHandler):
    """Handles file system events for agent-os specs."""

    def __init__(self, project_id: int, project_path: str):
        """
        Initialize spec file handler.

        Args:
            project_id: ID of the project
            project_path: Path to the project root
        """
        self.project_id = project_id
        self.project_path = project_path
        self.spec_manager = SpecManager()
        self.debounce_timers: Dict[str, threading.Timer] = {}
        self.debounce_delay = 2.0  # Debounce for 2 seconds

    def on_modified(self, event: FileModifiedEvent):
        """Handle file modifications."""
        if event.is_directory:
            return

        # Only react to tasks.md or spec.md changes
        filename = Path(event.src_path).name
        if filename not in ['tasks.md', 'spec.md']:
            return

        self._debounce_sync(event.src_path)

    def on_created(self, event: FileCreatedEvent):
        """Handle file creation."""
        if event.is_directory:
            # New spec folder created - sync entire project
            self._debounce_sync_all()
            return

        # Only react to tasks.md or spec.md
        filename = Path(event.src_path).name
        if filename not in ['tasks.md', 'spec.md']:
            return

        self._debounce_sync(event.src_path)

    def _debounce_sync(self, file_path: str):
        """Debounce sync calls to avoid multiple rapid syncs."""
        # Get the spec folder (parent of tasks.md)
        spec_folder = str(Path(file_path).parent)

        # Cancel previous timer if it exists
        if spec_folder in self.debounce_timers:
            self.debounce_timers[spec_folder].cancel()

        # Create new timer
        timer = threading.Timer(
            self.debounce_delay,
            lambda: self._trigger_sync(spec_folder)
        )
        self.debounce_timers[spec_folder] = timer
        timer.start()

    def _debounce_sync_all(self):
        """Debounce full project sync."""
        key = "__all__"

        # Cancel previous timer if it exists
        if key in self.debounce_timers:
            self.debounce_timers[key].cancel()

        # Create new timer
        timer = threading.Timer(
            self.debounce_delay,
            self._trigger_sync_all
        )
        self.debounce_timers[key] = timer
        timer.start()

    def _trigger_sync(self, spec_folder: str):
        """Trigger sync for a specific spec."""
        try:
            spec_name = Path(spec_folder).name
            logger.info(f"Syncing spec: {spec_name} for project {self.project_id}")

            # Parse the spec
            spec_data = parse_spec_folder(spec_folder)
            if not spec_data:
                logger.warning(f"Failed to parse spec folder: {spec_folder}")
                return

            # Sync to database
            result = self.spec_manager.create_or_update_spec(self.project_id, spec_data)

            action = "Updated" if not result['created'] else "Created"
            task_count = len(spec_data['tasks'])
            logger.info(f"✅ {action} spec '{spec_data['name']}' with {task_count} tasks")

        except Exception as e:
            logger.error(f"Error syncing spec {spec_folder}: {e}", exc_info=True)

    def _trigger_sync_all(self):
        """Trigger sync for all specs in project."""
        try:
            logger.info(f"Syncing all specs for project {self.project_id}")
            result = self.spec_manager.sync_project_specs(self.project_id, self.project_path)
            logger.info(f"✅ Synced {result['synced']} new, updated {result['updated']} existing specs")
        except Exception as e:
            logger.error(f"Error syncing all specs: {e}", exc_info=True)


class SpecWatcher:
    """Watches agent-os specs folder for a project."""

    def __init__(self, project_id: int, project_path: str):
        """
        Initialize spec watcher.

        Args:
            project_id: ID of the project
            project_path: Path to the project root
        """
        self.project_id = project_id
        self.project_path = project_path
        self.specs_path = Path(project_path) / "agent-os" / "specs"
        self.observer: Optional[Observer] = None
        self.event_handler: Optional[SpecFileHandler] = None

    def start(self):
        """Start watching specs folder."""
        if not self.specs_path.exists():
            logger.warning(f"Specs folder does not exist: {self.specs_path}")
            logger.info(f"Creating specs folder: {self.specs_path}")
            self.specs_path.mkdir(parents=True, exist_ok=True)
            return

        logger.info(f"Starting spec watcher for project {self.project_id}")
        logger.info(f"Watching: {self.specs_path}")

        # Create observer
        self.observer = Observer()

        # Create event handler
        self.event_handler = SpecFileHandler(self.project_id, self.project_path)

        # Schedule observer
        self.observer.schedule(self.event_handler, str(self.specs_path), recursive=True)
        self.observer.start()

        logger.info(f"✅ Spec watcher started for project {self.project_id}")

    def stop(self):
        """Stop watching specs folder."""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info(f"Spec watcher stopped for project {self.project_id}")
            self.observer = None
            self.event_handler = None

    def restart(self):
        """Restart watcher."""
        self.stop()
        self.start()


class GlobalSpecWatcher:
    """Manages spec watchers for all projects."""

    def __init__(self):
        """Initialize global spec watcher."""
        self.watchers: Dict[int, SpecWatcher] = {}
        self.lock = threading.Lock()

    def start_project(self, project_id: int, project_path: str):
        """Start watching a project's specs."""
        with self.lock:
            if project_id in self.watchers:
                logger.info(f"Spec watcher already exists for project {project_id}, restarting...")
                self.watchers[project_id].restart()
                return

            watcher = SpecWatcher(project_id, project_path)
            watcher.start()
            self.watchers[project_id] = watcher

    def stop_project(self, project_id: int):
        """Stop watching a project's specs."""
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

    def start_all(self):
        """Start watching all projects."""
        # Get all projects from database
        db_manager = get_sqlite_manager()
        projects = db_manager.list_projects()

        logger.info(f"Starting spec watchers for {len(projects)} projects")

        for project in projects:
            try:
                self.start_project(project['id'], project['path'])
            except Exception as e:
                logger.error(f"Error starting spec watcher for project {project['id']}: {e}")

    def stop_all(self):
        """Stop watching all projects."""
        with self.lock:
            for watcher in self.watchers.values():
                try:
                    watcher.stop()
                except Exception as e:
                    logger.error(f"Error stopping spec watcher: {e}")

            self.watchers.clear()

    def get_status(self) -> Dict:
        """Get status of all spec watchers."""
        with self.lock:
            return {
                "enabled": len(self.watchers) > 0,
                "projects_watched": len(self.watchers),
                "projects": {
                    project_id: {
                        "project_path": watcher.project_path,
                        "specs_path": str(watcher.specs_path),
                        "watching": watcher.observer is not None
                    }
                    for project_id, watcher in self.watchers.items()
                }
            }


# Global instance
_global_spec_watcher: Optional[GlobalSpecWatcher] = None


def get_global_spec_watcher() -> GlobalSpecWatcher:
    """Get or create global spec watcher."""
    global _global_spec_watcher
    if _global_spec_watcher is None:
        _global_spec_watcher = GlobalSpecWatcher()
    return _global_spec_watcher
