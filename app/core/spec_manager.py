"""
Spec Manager - Manages specs and tasks in the database.
"""

import sqlite3
import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from app.core.spec_parser import find_spec_folders, parse_spec_folder
from app.core.config import Config


class SpecManager:
    """Manages specs and tasks in the Claude OS database."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.SQLITE_DB_PATH

    def _get_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.db_path)

    def sync_project_specs(self, project_id: int, project_path: str) -> Dict:
        """Sync all specs from a project's agent-os folder."""
        spec_folders = find_spec_folders(project_path)

        synced = 0
        updated = 0
        errors = []

        for folder_path in spec_folders:
            try:
                spec_data = parse_spec_folder(folder_path)
                if spec_data:
                    result = self.create_or_update_spec(project_id, spec_data)
                    if result['created']:
                        synced += 1
                    else:
                        updated += 1
            except Exception as e:
                errors.append(f"Error parsing {folder_path}: {str(e)}")

        return {
            "synced": synced,
            "updated": updated,
            "total": len(spec_folders),
            "errors": errors
        }

    def create_or_update_spec(self, project_id: int, spec_data: Dict) -> Dict:
        """Create or update a spec and its tasks."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Check if spec exists
        cursor.execute("""
            SELECT id FROM specs
            WHERE project_id = ? AND folder_name = ?
        """, (project_id, spec_data['folder_name']))

        existing = cursor.fetchone()

        if existing:
            spec_id = existing[0]
            # Update existing spec
            cursor.execute("""
                UPDATE specs SET
                    name = ?,
                    slug = ?,
                    path = ?,
                    total_tasks = ?,
                    updated_at = CURRENT_TIMESTAMP,
                    metadata = ?
                WHERE id = ?
            """, (
                spec_data['name'],
                spec_data['slug'],
                spec_data['path'],
                len(spec_data['tasks']),
                json.dumps(spec_data['metadata']),
                spec_id
            ))
            created = False
        else:
            # Create new spec
            cursor.execute("""
                INSERT INTO specs (
                    project_id, name, slug, folder_name, path,
                    total_tasks, status, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_id,
                spec_data['name'],
                spec_data['slug'],
                spec_data['folder_name'],
                spec_data['path'],
                len(spec_data['tasks']),
                'planning',
                json.dumps(spec_data['metadata'])
            ))
            spec_id = cursor.lastrowid
            created = True

        # Delete existing tasks for this spec (we'll re-create them)
        cursor.execute("DELETE FROM spec_tasks WHERE spec_id = ?", (spec_id,))

        # Insert tasks
        for task in spec_data['tasks']:
            cursor.execute("""
                INSERT INTO spec_tasks (
                    spec_id, task_code, phase, title, description,
                    status, estimated_minutes, risk_level, dependencies
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                spec_id,
                task['task_code'],
                task.get('phase', 'Unknown'),
                task['title'],
                task.get('description', ''),
                task.get('status', 'todo'),
                task.get('estimated_minutes', 0),
                task.get('risk_level', 'medium'),
                json.dumps(task.get('dependencies', []))
            ))

        # Update completed_tasks count
        cursor.execute("""
            UPDATE specs SET completed_tasks = (
                SELECT COUNT(*) FROM spec_tasks
                WHERE spec_id = ? AND status = 'done'
            ) WHERE id = ?
        """, (spec_id, spec_id))

        conn.commit()
        conn.close()

        return {"created": created, "spec_id": spec_id}

    def get_project_specs(self, project_id: int, include_archived: bool = False) -> List[Dict]:
        """Get all specs for a project."""
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT id, name, slug, folder_name, path,
                   total_tasks, completed_tasks, status,
                   created_at, updated_at, metadata, archived
            FROM specs
            WHERE project_id = ?
        """

        if not include_archived:
            query += " AND archived = 0"

        query += " ORDER BY archived ASC, created_at DESC"

        cursor.execute(query, (project_id,))

        specs = []
        for row in cursor.fetchall():
            specs.append({
                "id": row[0],
                "name": row[1],
                "slug": row[2],
                "folder_name": row[3],
                "path": row[4],
                "total_tasks": row[5],
                "completed_tasks": row[6],
                "status": row[7],
                "progress": round((row[6] / row[5] * 100) if row[5] > 0 else 0, 1),
                "created_at": row[8],
                "updated_at": row[9],
                "metadata": json.loads(row[10]) if row[10] else {},
                "archived": bool(row[11])
            })

        conn.close()
        return specs

    def archive_spec(self, spec_id: int) -> Dict:
        """Archive a spec."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE specs SET archived = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (spec_id,))

        conn.commit()
        conn.close()

        return {"success": True, "spec_id": spec_id, "archived": True}

    def unarchive_spec(self, spec_id: int) -> Dict:
        """Unarchive a spec."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE specs SET archived = 0, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (spec_id,))

        conn.commit()
        conn.close()

        return {"success": True, "spec_id": spec_id, "archived": False}

    def get_spec_tasks(self, spec_id: int) -> List[Dict]:
        """Get all tasks for a spec."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, task_code, phase, title, description,
                   status, estimated_minutes, actual_minutes,
                   risk_level, dependencies, started_at, completed_at,
                   created_at, updated_at
            FROM spec_tasks
            WHERE spec_id = ?
            ORDER BY task_code
        """, (spec_id,))

        tasks = []
        for row in cursor.fetchall():
            tasks.append({
                "id": row[0],
                "task_code": row[1],
                "phase": row[2],
                "title": row[3],
                "description": row[4],
                "status": row[5],
                "estimated_minutes": row[6],
                "actual_minutes": row[7],
                "risk_level": row[8],
                "dependencies": json.loads(row[9]) if row[9] else [],
                "started_at": row[10],
                "completed_at": row[11],
                "created_at": row[12],
                "updated_at": row[13]
            })

        conn.close()
        return tasks

    def update_task_status(self, task_id: int, status: str, actual_minutes: int = None) -> Dict:
        """Update a task's status."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get current status
        cursor.execute("SELECT status, spec_id FROM spec_tasks WHERE id = ?", (task_id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return {"success": False, "error": "Task not found"}

        old_status = result[0]
        spec_id = result[1]

        # Update task
        updates = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
        params = [status]

        if status == 'in_progress' and old_status != 'in_progress':
            updates.append("started_at = CURRENT_TIMESTAMP")

        if status == 'done' and old_status != 'done':
            updates.append("completed_at = CURRENT_TIMESTAMP")

        if actual_minutes is not None:
            updates.append("actual_minutes = ?")
            params.append(actual_minutes)

        params.append(task_id)

        cursor.execute(f"""
            UPDATE spec_tasks SET {', '.join(updates)}
            WHERE id = ?
        """, params)

        # Update spec's completed_tasks count and status
        cursor.execute("""
            UPDATE specs SET
                completed_tasks = (
                    SELECT COUNT(*) FROM spec_tasks
                    WHERE spec_id = ? AND status = 'done'
                ),
                status = CASE
                    WHEN total_tasks = 0 THEN 'planning'
                    WHEN (SELECT COUNT(*) FROM spec_tasks WHERE spec_id = ? AND status = 'done') = 0 THEN 'planning'
                    WHEN (SELECT COUNT(*) FROM spec_tasks WHERE spec_id = ? AND status = 'done') = total_tasks THEN 'completed'
                    ELSE 'in_progress'
                END,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (spec_id, spec_id, spec_id, spec_id))

        conn.commit()
        conn.close()

        return {"success": True, "old_status": old_status, "new_status": status}

    def get_kanban_view(self, project_id: int) -> Dict:
        """Get kanban board view for a project."""
        specs = self.get_project_specs(project_id)

        kanban = {
            "project_id": project_id,
            "specs": [],
            "summary": {
                "total_specs": len(specs),
                "total_tasks": 0,
                "completed_tasks": 0
            }
        }

        for spec in specs:
            tasks = self.get_spec_tasks(spec['id'])

            # Group tasks by status
            task_groups = {
                "todo": [t for t in tasks if t['status'] == 'todo'],
                "in_progress": [t for t in tasks if t['status'] == 'in_progress'],
                "done": [t for t in tasks if t['status'] == 'done'],
                "blocked": [t for t in tasks if t['status'] == 'blocked']
            }

            kanban['specs'].append({
                **spec,
                "tasks": task_groups,
                "task_count_by_status": {
                    "todo": len(task_groups['todo']),
                    "in_progress": len(task_groups['in_progress']),
                    "done": len(task_groups['done']),
                    "blocked": len(task_groups['blocked'])
                }
            })

            kanban['summary']['total_tasks'] += spec['total_tasks']
            kanban['summary']['completed_tasks'] += spec['completed_tasks']

        return kanban
