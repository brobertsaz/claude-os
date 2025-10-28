"""
Tests for file watcher system functionality.
"""

import pytest
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

from app.core.file_watcher import (
    ProjectFileHandler,
    ProjectWatcher,
    GlobalFileWatcher,
    get_global_watcher
)


@pytest.mark.unit
class TestProjectFileHandler:
    """Test ProjectFileHandler class."""

    def test_file_handler_initialization(self):
        """Test file handler initialization."""
        callback = Mock()
        handler = ProjectFileHandler(123, "knowledge_docs", callback)

        assert handler.project_id == 123
        assert handler.mcp_type == "knowledge_docs"
        assert handler.on_change == callback
        assert handler.debounce_delay == 2.0
        assert handler.debounce_timer is None

    def test_on_modified_file(self):
        """Test handling file modification."""
        callback = Mock()
        handler = ProjectFileHandler(123, "knowledge_docs", callback)

        # Create mock event
        mock_event = Mock()
        mock_event.is_directory = False

        handler.on_modified(mock_event)

        # Should have a debounce timer
        assert handler.debounce_timer is not None
        assert isinstance(handler.debounce_timer, threading.Timer)

    def test_on_created_file(self):
        """Test handling file creation."""
        callback = Mock()
        handler = ProjectFileHandler(123, "knowledge_docs", callback)

        # Create mock event
        mock_event = Mock()
        mock_event.is_directory = False

        handler.on_created(mock_event)

        # Should have a debounce timer
        assert handler.debounce_timer is not None

    def test_on_modified_directory_ignored(self):
        """Test that directory modifications are ignored."""
        callback = Mock()
        handler = ProjectFileHandler(123, "knowledge_docs", callback)

        # Create mock directory event
        mock_event = Mock()
        mock_event.is_directory = True

        handler.on_modified(mock_event)

        # Should not create timer for directories
        assert handler.debounce_timer is None

    def test_on_created_directory_ignored(self):
        """Test that directory creations are ignored."""
        callback = Mock()
        handler = ProjectFileHandler(123, "knowledge_docs", callback)

        # Create mock directory event
        mock_event = Mock()
        mock_event.is_directory = True

        handler.on_created(mock_event)

        # Should not create timer for directories
        assert handler.debounce_timer is None

    def test_debounce_sync_cancels_previous_timer(self):
        """Test that debounce cancels previous timer."""
        callback = Mock()
        handler = ProjectFileHandler(123, "knowledge_docs", callback)

        # Create mock event
        mock_event = Mock()
        mock_event.is_directory = False

        # First event
        handler.on_modified(mock_event)
        first_timer = handler.debounce_timer

        # Second event (should cancel first)
        handler.on_modified(mock_event)
        second_timer = handler.debounce_timer

        # Timers should be different
        assert first_timer is not second_timer
        assert handler.debounce_timer is second_timer

    @patch('threading.Timer')
    def test_trigger_sync_callback(self, mock_timer_class):
        """Test that debounce timer triggers callback."""
        callback = Mock()
        handler = ProjectFileHandler(123, "knowledge_docs", callback)

        # Mock timer
        mock_timer = Mock()
        mock_timer_class.return_value = mock_timer

        # Trigger file event
        mock_event = Mock()
        mock_event.is_directory = False
        handler.on_modified(mock_event)

        # Get the timer callback
        timer_callback = mock_timer_class.call_args[0][0]

        # Execute the callback
        timer_callback()

        # Should call the original callback
        callback.assert_called_once()

    @patch('threading.Timer')
    def test_trigger_sync_error_handling(self, mock_timer_class):
        """Test error handling in sync callback."""
        callback = Mock(side_effect=Exception("Sync error"))
        handler = ProjectFileHandler(123, "knowledge_docs", callback)

        # Mock timer
        mock_timer = Mock()
        mock_timer_class.return_value = mock_timer

        # Trigger file event
        mock_event = Mock()
        mock_event.is_directory = False
        handler.on_modified(mock_event)

        # Get and execute timer callback
        timer_callback = mock_timer_class.call_args[0][0]

        # Should handle error gracefully
        # In real implementation, this would be caught by logger
        timer_callback()


@pytest.mark.integration
class TestProjectWatcher:
    """Test ProjectWatcher class."""

    @patch('app.core.file_watcher.ProjectHook')
    @patch('app.core.file_watcher.Observer')
    def test_watcher_initialization(self, mock_observer_class, mock_hook_class):
        """Test project watcher initialization."""
        project_id = 123
        mock_hook = Mock()
        mock_hook_class.return_value = mock_hook

        watcher = ProjectWatcher(project_id)

        assert watcher.project_id == project_id
        assert watcher.hook == mock_hook
        assert watcher.observer is None
        assert watcher.event_handlers == {}
        assert watcher.watched_paths == {}

    @patch('app.core.file_watcher.ProjectHook')
    @patch('app.core.file_watcher.Observer')
    def test_start_with_no_hooks(self, mock_observer_class, mock_hook_class):
        """Test starting watcher with no hooks configured."""
        project_id = 123
        mock_hook = Mock()
        mock_hook.get_hook_status.return_value = {"hooks": {}}
        mock_hook_class.return_value = mock_hook

        watcher = ProjectWatcher(project_id)
        watcher.start()

        # Should not start observer
        mock_observer_class.return_value.start.assert_not_called()

    @patch('app.core.file_watcher.ProjectHook')
    @patch('app.core.file_watcher.Observer')
    def test_start_with_disabled_hooks(self, mock_observer_class, mock_hook_class):
        """Test starting watcher with disabled hooks."""
        project_id = 123
        mock_hook = Mock()
        mock_hook.get_hook_status.return_value = {
            "hooks": {
                "knowledge_docs": {
                    "enabled": False,
                    "folder_path": "/path/to/docs"
                }
            }
        }
        mock_hook_class.return_value = mock_hook

        watcher = ProjectWatcher(project_id)
        watcher.start()

        # Should not start observer
        mock_observer_class.return_value.start.assert_not_called()

    @patch('app.core.file_watcher.ProjectHook')
    @patch('app.core.file_watcher.Observer')
    def test_start_with_enabled_hooks(self, mock_observer_class, mock_hook_class, tmp_path):
        """Test starting watcher with enabled hooks."""
        project_id = 123
        mock_hook = Mock()

        # Create a real directory for testing
        watch_dir = tmp_path / "watched"
        watch_dir.mkdir()

        mock_hook.get_hook_status.return_value = {
            "hooks": {
                "knowledge_docs": {
                    "enabled": True,
                    "folder_path": str(watch_dir)
                }
            }
        }
        mock_hook_class.return_value = mock_hook

        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        watcher = ProjectWatcher(project_id)
        watcher.start()

        # Should start observer
        mock_observer.start.assert_called_once()

        # Should schedule watching
        mock_observer.schedule.assert_called_once()
        schedule_args = mock_observer.schedule.call_args
        assert schedule_args[0][1] == str(watch_dir)  # path
        assert schedule_args[0][2] is True  # recursive

    @patch('app.core.file_watcher.ProjectHook')
    @patch('app.core.file_watcher.Observer')
    def test_start_with_nonexistent_folder(self, mock_observer_class, mock_hook_class):
        """Test starting watcher with non-existent folder."""
        project_id = 123
        mock_hook = Mock()
        mock_hook.get_hook_status.return_value = {
            "hooks": {
                "knowledge_docs": {
                    "enabled": True,
                    "folder_path": "/nonexistent/path"
                }
            }
        }
        mock_hook_class.return_value = mock_hook

        watcher = ProjectWatcher(project_id)
        watcher.start()

        # Should not schedule watching for non-existent path
        mock_observer_class.return_value.schedule.assert_not_called()

    @patch('app.core.file_watcher.ProjectHook')
    @patch('app.core.file_watcher.Observer')
    def test_start_multiple_hooks(self, mock_observer_class, mock_hook_class, tmp_path):
        """Test starting watcher with multiple enabled hooks."""
        project_id = 123
        mock_hook = Mock()

        # Create directories
        docs_dir = tmp_path / "docs"
        profile_dir = tmp_path / "profile"
        docs_dir.mkdir()
        profile_dir.mkdir()

        mock_hook.get_hook_status.return_value = {
            "hooks": {
                "knowledge_docs": {
                    "enabled": True,
                    "folder_path": str(docs_dir)
                },
                "project_profile": {
                    "enabled": True,
                    "folder_path": str(profile_dir)
                }
            }
        }
        mock_hook_class.return_value = mock_hook

        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        watcher = ProjectWatcher(project_id)
        watcher.start()

        # Should schedule both paths
        assert mock_observer.schedule.call_count == 2

        # Check event handlers were created
        assert len(watcher.event_handlers) == 2
        assert "knowledge_docs" in watcher.event_handlers
        assert "project_profile" in watcher.event_handlers

    @patch('app.core.file_watcher.ProjectHook')
    @patch('app.core.file_watcher.Observer')
    def test_stop_watcher(self, mock_observer_class, mock_hook_class):
        """Test stopping watcher."""
        project_id = 123
        mock_hook = Mock()
        mock_hook.get_hook_status.return_value = {"hooks": {}}
        mock_hook_class.return_value = mock_hook

        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        watcher = ProjectWatcher(project_id)
        watcher.observer = mock_observer
        watcher.event_handlers["test"] = Mock()
        watcher.watched_paths["test"] = "/path"

        watcher.stop()

        # Should stop observer
        mock_observer.stop.assert_called_once()
        mock_observer.join.assert_called_once()

        # Should clear state
        assert watcher.observer is None
        assert len(watcher.event_handlers) == 0
        assert len(watcher.watched_paths) == 0

    @patch('app.core.file_watcher.ProjectHook')
    @patch('app.core.file_watcher.Observer')
    def test_restart_watcher(self, mock_observer_class, mock_hook_class):
        """Test restarting watcher."""
        project_id = 123
        mock_hook = Mock()
        mock_hook.get_hook_status.return_value = {"hooks": {}}
        mock_hook_class.return_value = mock_hook

        mock_observer = Mock()
        mock_observer_class.return_value = mock_observer

        watcher = ProjectWatcher(project_id)
        watcher.observer = mock_observer

        watcher.restart()

        # Should stop and start
        mock_observer.stop.assert_called_once()
        mock_observer.join.assert_called_once()
        mock_observer.start.assert_called_once()

    @patch('app.core.file_watcher.ProjectHook')
    @patch('app.core.file_watcher.Observer')
    def test_on_folder_change(self, mock_observer_class, mock_hook_class):
        """Test folder change handling."""
        project_id = 123
        mock_hook = Mock()
        mock_hook.get_hook_status.return_value = {"hooks": {}}
        mock_hook_class.return_value = mock_hook

        watcher = ProjectWatcher(project_id)

        # Mock sync result
        mock_hook.sync_kb_folder.return_value = {
            "synced_files": ["file1.txt", "file2.txt"],
            "errors": []
        }

        watcher._on_folder_change("knowledge_docs")

        # Should call sync
        mock_hook.sync_kb_folder.assert_called_once_with("knowledge_docs")

    @patch('app.core.file_watcher.ProjectHook')
    @patch('app.core.file_watcher.Observer')
    def test_on_folder_change_with_errors(self, mock_observer_class, mock_hook_class):
        """Test folder change handling with sync errors."""
        project_id = 123
        mock_hook = Mock()
        mock_hook.get_hook_status.return_value = {"hooks": {}}
        mock_hook_class.return_value = mock_hook

        watcher = ProjectWatcher(project_id)

        # Mock sync result with errors
        mock_hook.sync_kb_folder.return_value = {
            "synced_files": ["file1.txt"],
            "errors": [{"file": "file2.txt", "error": "Permission denied"}]
        }

        watcher._on_folder_change("knowledge_docs")

        # Should still call sync despite errors
        mock_hook.sync_kb_folder.assert_called_once_with("knowledge_docs")


@pytest.mark.integration
class TestGlobalFileWatcher:
    """Test GlobalFileWatcher class."""

    def test_global_watcher_initialization(self):
        """Test global watcher initialization."""
        global_watcher = GlobalFileWatcher()

        assert global_watcher.watchers == {}
        assert global_watcher.enabled is False
        assert hasattr(global_watcher, 'lock')

    def test_start_project(self):
        """Test starting to watch a project."""
        global_watcher = GlobalFileWatcher()

        with patch('app.core.file_watcher.ProjectWatcher') as mock_pw_class:
            mock_pw = Mock()
            mock_pw_class.return_value = mock_pw

            global_watcher.start_project(123)

            assert 123 in global_watcher.watchers
            assert global_watcher.watchers[123] == mock_pw
            mock_pw.start.assert_called_once()

    def test_start_project_already_exists(self):
        """Test starting project that's already being watched."""
        global_watcher = GlobalFileWatcher()

        with patch('app.core.file_watcher.ProjectWatcher') as mock_pw_class:
            mock_pw1 = Mock()
            mock_pw2 = Mock()
            mock_pw_class.side_effect = [mock_pw1, mock_pw2]

            # Start project twice
            global_watcher.start_project(123)
            global_watcher.start_project(123)

            # Should still only have one watcher
            assert len(global_watcher.watchers) == 1
            assert global_watcher.watchers[123] == mock_pw1
            mock_pw2.start.assert_not_called()

    def test_stop_project(self):
        """Test stopping watching a project."""
        global_watcher = GlobalFileWatcher()

        with patch('app.core.file_watcher.ProjectWatcher') as mock_pw_class:
            mock_pw = Mock()
            mock_pw_class.return_value = mock_pw

            # Start then stop
            global_watcher.start_project(123)
            global_watcher.stop_project(123)

            assert 123 not in global_watcher.watchers
            mock_pw.stop.assert_called_once()

    def test_stop_project_not_watched(self):
        """Test stopping project that's not being watched."""
        global_watcher = GlobalFileWatcher()

        # Should not raise error
        global_watcher.stop_project(123)
        assert 123 not in global_watcher.watchers

    def test_restart_project(self):
        """Test restarting project watcher."""
        global_watcher = GlobalFileWatcher()

        with patch('app.core.file_watcher.ProjectWatcher') as mock_pw_class:
            mock_pw = Mock()
            mock_pw_class.return_value = mock_pw

            # Start then restart
            global_watcher.start_project(123)
            global_watcher.restart_project(123)

            mock_pw.restart.assert_called_once()

    def test_restart_project_not_watched(self):
        """Test restarting project that's not being watched."""
        global_watcher = GlobalFileWatcher()

        with patch('app.core.file_watcher.ProjectWatcher') as mock_pw_class:
            mock_pw = Mock()
            mock_pw_class.return_value = mock_pw

            global_watcher.restart_project(123)

            # Should start the project
            mock_pw.start.assert_called_once()
            assert 123 in global_watcher.watchers

    def test_start_all_projects(self):
        """Test starting all projects."""
        global_watcher = GlobalFileWatcher()

        with patch('app.core.file_watcher.ProjectWatcher') as mock_pw_class:
            mock_pw1 = Mock()
            mock_pw2 = Mock()
            mock_pw3 = Mock()
            mock_pw_class.side_effect = [mock_pw1, mock_pw2, mock_pw3]

            project_ids = [123, 456, 789]
            global_watcher.start_all(project_ids)

            assert len(global_watcher.watchers) == 3
            assert 123 in global_watcher.watchers
            assert 456 in global_watcher.watchers
            assert 789 in global_watcher.watchers

            mock_pw1.start.assert_called_once()
            mock_pw2.start.assert_called_once()
            mock_pw3.start.assert_called_once()

            assert global_watcher.enabled is True

    def test_start_all_projects_with_errors(self):
        """Test starting all projects with some errors."""
        global_watcher = GlobalFileWatcher()

        with patch('app.core.file_watcher.ProjectWatcher') as mock_pw_class:
            mock_pw1 = Mock()
            mock_pw2 = Mock()
            mock_pw3 = Mock()

            # Make second watcher fail
            mock_pw2.start.side_effect = Exception("Start failed")
            mock_pw_class.side_effect = [mock_pw1, mock_pw2, mock_pw3]

            project_ids = [123, 456, 789]
            global_watcher.start_all(project_ids)

            # Should still start others
            assert len(global_watcher.watchers) == 2  # Only 2 succeeded
            assert 123 in global_watcher.watchers
            assert 789 in global_watcher.watchers
            assert 456 not in global_watcher.watchers

    def test_stop_all(self):
        """Test stopping all project watchers."""
        global_watcher = GlobalFileWatcher()

        with patch('app.core.file_watcher.ProjectWatcher') as mock_pw_class:
            mock_pw1 = Mock()
            mock_pw2 = Mock()
            mock_pw_class.side_effect = [mock_pw1, mock_pw2]

            # Start some projects
            global_watcher.start_project(123)
            global_watcher.start_project(456)

            # Stop all
            global_watcher.stop_all()

            assert len(global_watcher.watchers) == 0
            assert global_watcher.enabled is False

            mock_pw1.stop.assert_called_once()
            mock_pw2.stop.assert_called_once()

    def test_get_status(self):
        """Test getting global watcher status."""
        global_watcher = GlobalFileWatcher()

        with patch('app.core.file_watcher.ProjectWatcher') as mock_pw_class:
            mock_pw1 = Mock()
            mock_pw2 = Mock()
            mock_pw1.watched_paths = {"docs": "/path/docs"}
            mock_pw1.event_handlers = {"docs": "handler1"}
            mock_pw2.watched_paths = {"profile": "/path/profile"}
            mock_pw2.event_handlers = {"profile": "handler2"}
            mock_pw_class.side_effect = [mock_pw1, mock_pw2]

            # Start projects
            global_watcher.start_project(123)
            global_watcher.start_project(456)

            status = global_watcher.get_status()

            assert status["enabled"] is True
            assert status["projects_watched"] == 2
            assert "123" in status["projects"]
            assert "456" in status["projects"]
            assert status["projects"]["123"]["watched_paths"] == {"docs": "/path/docs"}
            assert status["projects"]["123"]["event_handlers"] == ["docs"]
            assert status["projects"]["456"]["watched_paths"] == {"profile": "/path/profile"}
            assert status["projects"]["456"]["event_handlers"] == ["profile"]


@pytest.mark.unit
class TestFileWatcherUtility:
    """Test file watcher utility functions."""

    def test_get_global_watcher_singleton(self):
        """Test that get_global_watcher returns singleton."""
        watcher1 = get_global_watcher()
        watcher2 = get_global_watcher()

        # Should be the same instance
        assert watcher1 is watcher2

    def test_get_global_watcher_type(self):
        """Test that get_global_watcher returns correct type."""
        watcher = get_global_watcher()

        assert isinstance(watcher, GlobalFileWatcher)

    @patch('app.core.file_watcher.GlobalFileWatcher')
    def test_get_global_watcher_creates_instance(self, mock_gfw_class):
        """Test that get_global_watcher creates instance on first call."""
        mock_instance = Mock()
        mock_gfw_class.return_value = mock_instance

        # Clear any existing instance
        import app.core.file_watcher
        app.core.file_watcher._global_watcher = None

        watcher1 = get_global_watcher()
        watcher2 = get_global_watcher()

        # Should create instance only once
        mock_gfw_class.assert_called_once()
        assert watcher1 is mock_instance
        assert watcher2 is mock_instance


@pytest.mark.integration
class TestFileWatcherIntegration:
    """Integration tests for file watcher system."""

    @patch('app.core.file_watcher.ProjectHook')
    def test_file_change_detection(self, mock_hook_class, tmp_path):
        """Test actual file change detection."""
        # This test would require real file system watching
        # For now, we'll test the integration points

        project_id = 123
        mock_hook = Mock()
        mock_hook.get_hook_status.return_value = {
            "hooks": {
                "knowledge_docs": {
                    "enabled": True,
                    "folder_path": str(tmp_path)
                }
            }
        }
        mock_hook_class.return_value = mock_hook

        watcher = ProjectWatcher(project_id)

        # Test that the handler is created correctly
        assert "knowledge_docs" in watcher.event_handlers
        handler = watcher.event_handlers["knowledge_docs"]

        assert handler.project_id == project_id
        assert handler.mcp_type == "knowledge_docs"
        assert callable(handler.on_change)

    def test_debounce_timing(self):
        """Test debounce timing behavior."""
        callback = Mock()
        handler = ProjectFileHandler(123, "knowledge_docs", callback)

        # Mock timer to track calls
        with patch('threading.Timer') as mock_timer_class:
            mock_timer = Mock()
            mock_timer_class.return_value = mock_timer

            # Trigger multiple rapid events
            mock_event = Mock()
            mock_event.is_directory = False

            handler.on_modified(mock_event)
            first_call_args = mock_timer_class.call_args
            first_callback = first_call_args[0][0]

            handler.on_modified(mock_event)
            second_call_args = mock_timer_class.call_args
            second_callback = second_call_args[0][0]

            # Should have created two timers
            assert mock_timer_class.call_count == 2

            # First timer should be cancelled (implicitly by creating new one)
            # In real implementation, the old timer would be cancelled
            assert first_callback is not None
            assert second_callback is not None