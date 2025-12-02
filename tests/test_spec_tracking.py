"""
Comprehensive tests for spec tracking and Kanban board functionality.
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.spec_parser import TasksParser, parse_spec_folder, find_spec_folders
from app.core.spec_manager import SpecManager


class TestTasksParser:
    """Tests for tasks.md parser."""

    def test_parse_metadata(self, tmp_path):
        """Test extracting metadata from tasks.md"""
        tasks_md = tmp_path / "tasks.md"
        tasks_md.write_text("""
# Group Account Rendering - Tasks Breakdown

**Project:** MyApp
**Spec:** Group Account Rendering
**Created:** 2025-10-15
**Status:** Ready for Implementation
        """)

        parser = TasksParser(str(tasks_md))
        parsed = parser.parse()

        assert parsed['metadata']['project'] == 'MyApp'
        assert parsed['metadata']['spec_name'] == 'Group Account Rendering'
        assert parsed['metadata']['created'] == '2025-10-15'
        assert 'ready' in parsed['metadata']['status'].lower()

    def test_parse_overview(self, tmp_path):
        """Test extracting overview statistics."""
        tasks_md = tmp_path / "tasks.md"
        tasks_md.write_text("""
**Total Tasks:** 77
**Total Estimated Time:** 13-18 hours
**Number of High-Risk Tasks:** 9
**Number of Phases:** 6
        """)

        parser = TasksParser(str(tasks_md))
        parsed = parser.parse()

        assert parsed['overview']['total_tasks'] == 77
        assert parsed['overview']['high_risk_tasks'] == 9
        assert parsed['overview']['phases'] == 6

    def test_parse_tasks(self, tmp_path):
        """Test parsing individual tasks."""
        tasks_md = tmp_path / "tasks.md"
        tasks_md.write_text("""
### PHASE1-TASK1: Create Concerns Directory

**Title:** Create `app/controllers/concerns` directory structure
**Description:** The concerns directory doesn't currently exist in the application.
**Estimated Time:** 5 minutes
**Dependencies:** None
**Risk Level:** Low

---

### PHASE1-TASK2: Create Basic Concern

**Title:** Create GroupAccountRendering concern skeleton
**Description:** Create the basic concern file.
**Estimated Time:** 10 minutes
**Dependencies:** PHASE1-TASK1
**Risk Level:** Medium
        """)

        parser = TasksParser(str(tasks_md))
        parsed = parser.parse()

        assert len(parsed['tasks']) == 2

        task1 = parsed['tasks'][0]
        assert task1['task_code'] == 'PHASE1-TASK1'
        assert task1['phase'] == 'Phase 1'
        assert 'concerns' in task1['title'].lower()
        assert task1['estimated_minutes'] == 5
        assert task1['risk_level'] == 'low'
        assert task1['dependencies'] == []

        task2 = parsed['tasks'][1]
        assert task2['task_code'] == 'PHASE1-TASK2'
        assert task2['estimated_minutes'] == 10
        assert task2['risk_level'] == 'medium'
        assert 'PHASE1-TASK1' in task2['dependencies']

    def test_parse_completed_tasks(self, tmp_path):
        """Test detecting completed tasks."""
        tasks_md = tmp_path / "tasks.md"
        tasks_md.write_text("""
### PHASE1-TASK1: ✅ COMPLETED

**Title:** Create directory
**Status:** Completed
        """)

        parser = TasksParser(str(tasks_md))
        parsed = parser.parse()

        assert len(parsed['tasks']) == 1
        assert parsed['tasks'][0]['status'] == 'done'


class TestSpecManager:
    """Tests for SpecManager database operations."""

    @pytest.fixture
    def db_path(self, tmp_path):
        """Create a temporary test database."""
        db_file = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        # Create projects table
        cursor.execute("""
            CREATE TABLE projects (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                path TEXT NOT NULL
            )
        """)

        # Create specs table
        cursor.execute("""
            CREATE TABLE specs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                slug TEXT NOT NULL,
                folder_name TEXT NOT NULL,
                path TEXT NOT NULL,
                total_tasks INTEGER DEFAULT 0,
                completed_tasks INTEGER DEFAULT 0,
                status TEXT DEFAULT 'planning',
                archived INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}'
            )
        """)

        # Create spec_tasks table
        cursor.execute("""
            CREATE TABLE spec_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                spec_id INTEGER NOT NULL,
                task_code TEXT NOT NULL,
                phase TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'todo',
                estimated_minutes INTEGER,
                actual_minutes INTEGER,
                risk_level TEXT,
                dependencies TEXT DEFAULT '[]',
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert test project
        cursor.execute("INSERT INTO projects (id, name, path) VALUES (1, 'Test Project', '/tmp/test')")

        conn.commit()
        conn.close()

        return str(db_file)

    def test_create_spec(self, db_path):
        """Test creating a spec."""
        manager = SpecManager(db_path)

        spec_data = {
            'folder_name': '2025-01-01-test-spec',
            'slug': 'test-spec',
            'name': 'Test Spec',
            'path': '/tmp/test/spec',
            'metadata': {},
            'tasks': [
                {
                    'task_code': 'PHASE1-TASK1',
                    'phase': 'Phase 1',
                    'title': 'Test Task',
                    'description': 'Test description',
                    'status': 'todo',
                    'estimated_minutes': 10,
                    'risk_level': 'low',
                    'dependencies': []
                }
            ]
        }

        result = manager.create_or_update_spec(1, spec_data)

        assert result['created'] is True
        assert result['spec_id'] == 1

    def test_get_project_specs(self, db_path):
        """Test retrieving specs for a project."""
        manager = SpecManager(db_path)

        # Create test specs
        spec1_data = {
            'folder_name': '2025-01-01-spec1',
            'slug': 'spec1',
            'name': 'Spec 1',
            'path': '/tmp/test/spec1',
            'metadata': {},
            'tasks': []
        }

        spec2_data = {
            'folder_name': '2025-01-02-spec2',
            'slug': 'spec2',
            'name': 'Spec 2',
            'path': '/tmp/test/spec2',
            'metadata': {},
            'tasks': []
        }

        manager.create_or_update_spec(1, spec1_data)
        manager.create_or_update_spec(1, spec2_data)

        specs = manager.get_project_specs(1)

        assert len(specs) == 2
        assert specs[0]['name'] in ['Spec 1', 'Spec 2']

    def test_archive_spec(self, db_path):
        """Test archiving a spec."""
        manager = SpecManager(db_path)

        spec_data = {
            'folder_name': '2025-01-01-test',
            'slug': 'test',
            'name': 'Test',
            'path': '/tmp/test',
            'metadata': {},
            'tasks': []
        }

        result = manager.create_or_update_spec(1, spec_data)
        spec_id = result['spec_id']

        # Archive the spec
        archive_result = manager.archive_spec(spec_id)
        assert archive_result['archived'] is True

        # Check it's excluded from default query
        specs = manager.get_project_specs(1)
        assert len(specs) == 0

        # Check it's included when requested
        specs_with_archived = manager.get_project_specs(1, include_archived=True)
        assert len(specs_with_archived) == 1
        assert specs_with_archived[0]['archived'] is True

    def test_update_task_status(self, db_path):
        """Test updating task status."""
        manager = SpecManager(db_path)

        spec_data = {
            'folder_name': '2025-01-01-test',
            'slug': 'test',
            'name': 'Test',
            'path': '/tmp/test',
            'metadata': {},
            'tasks': [
                {
                    'task_code': 'PHASE1-TASK1',
                    'phase': 'Phase 1',
                    'title': 'Task 1',
                    'status': 'todo',
                    'estimated_minutes': 10,
                    'risk_level': 'low',
                    'dependencies': []
                }
            ]
        }

        result = manager.create_or_update_spec(1, spec_data)
        spec_id = result['spec_id']

        tasks = manager.get_spec_tasks(spec_id)
        task_id = tasks[0]['id']

        # Update to in_progress
        update_result = manager.update_task_status(task_id, 'in_progress')
        assert update_result['success'] is True
        assert update_result['old_status'] == 'todo'
        assert update_result['new_status'] == 'in_progress'

        # Verify spec completed_tasks count
        spec = manager.get_project_specs(1)[0]
        assert spec['completed_tasks'] == 0

        # Complete the task
        manager.update_task_status(task_id, 'done', 15)

        # Verify spec updated
        spec = manager.get_project_specs(1)[0]
        assert spec['completed_tasks'] == 1
        assert spec['status'] == 'completed'

    def test_status_auto_update(self, db_path):
        """Test automatic status updates based on completion."""
        manager = SpecManager(db_path)

        spec_data = {
            'folder_name': '2025-01-01-test',
            'slug': 'test',
            'name': 'Test',
            'path': '/tmp/test',
            'metadata': {},
            'tasks': [
                {'task_code': 'T1', 'phase': 'P1', 'title': 'Task 1', 'status': 'todo', 'estimated_minutes': 10, 'risk_level': 'low', 'dependencies': []},
                {'task_code': 'T2', 'phase': 'P1', 'title': 'Task 2', 'status': 'todo', 'estimated_minutes': 10, 'risk_level': 'low', 'dependencies': []}
            ]
        }

        result = manager.create_or_update_spec(1, spec_data)
        spec_id = result['spec_id']

        # Initial status should be 'planning'
        spec = manager.get_project_specs(1)[0]
        assert spec['status'] == 'planning'
        assert spec['progress'] == 0

        # Complete one task
        tasks = manager.get_spec_tasks(spec_id)
        manager.update_task_status(tasks[0]['id'], 'done')

        spec = manager.get_project_specs(1)[0]
        assert spec['status'] == 'in_progress'
        assert spec['progress'] == 50.0

        # Complete second task
        manager.update_task_status(tasks[1]['id'], 'done')

        spec = manager.get_project_specs(1)[0]
        assert spec['status'] == 'completed'
        assert spec['progress'] == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
