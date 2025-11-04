"""
Parser for agent-os tasks.md files.
Extracts spec and task information for Claude OS Kanban board.
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class TasksParser:
    """Parses agent-os tasks.md files into structured data."""

    def __init__(self, tasks_md_path: str):
        self.path = Path(tasks_md_path)
        self.content = ""
        if self.path.exists():
            with open(self.path, 'r', encoding='utf-8') as f:
                self.content = f.read()

    def parse(self) -> Dict:
        """Parse the tasks.md file and return structured data."""
        return {
            "metadata": self._parse_metadata(),
            "overview": self._parse_overview(),
            "tasks": self._parse_tasks()
        }

    def _parse_metadata(self) -> Dict:
        """Extract project metadata from the header."""
        metadata = {}

        # Extract project name
        project_match = re.search(r'\*\*Project:\*\*\s*(.+)', self.content)
        if project_match:
            metadata['project'] = project_match.group(1).strip()

        # Extract spec name
        spec_match = re.search(r'\*\*Spec:\*\*\s*(.+)', self.content)
        if spec_match:
            metadata['spec_name'] = spec_match.group(1).strip()

        # Extract created date
        created_match = re.search(r'\*\*Created:\*\*\s*(.+)', self.content)
        if created_match:
            metadata['created'] = created_match.group(1).strip()

        # Extract status
        status_match = re.search(r'\*\*Status:\*\*\s*(.+)', self.content)
        if status_match:
            metadata['status'] = status_match.group(1).strip().lower()

        return metadata

    def _parse_overview(self) -> Dict:
        """Extract project overview statistics."""
        overview = {}

        # Total tasks
        total_match = re.search(r'\*\*Total Tasks:\*\*\s*(\d+)', self.content)
        if total_match:
            overview['total_tasks'] = int(total_match.group(1))

        # Total estimated time
        time_match = re.search(r'\*\*Total Estimated Time:\*\*\s*(.+)', self.content)
        if time_match:
            overview['estimated_time'] = time_match.group(1).strip()

        # Number of phases
        phases_match = re.search(r'\*\*Number of Phases:\*\*\s*(\d+)', self.content)
        if phases_match:
            overview['phases'] = int(phases_match.group(1))

        # High-risk tasks
        risk_match = re.search(r'\*\*Number of High-Risk Tasks:\*\*\s*(\d+)', self.content)
        if risk_match:
            overview['high_risk_tasks'] = int(risk_match.group(1))

        return overview

    def _parse_tasks(self) -> List[Dict]:
        """Parse all tasks from the markdown."""
        tasks = []

        # Find all task sections (e.g., ### PHASE1-TASK1:)
        task_pattern = r'###\s+(PHASE\d+-TASK\d+):\s*(.+?)(?=###|\Z)'
        matches = re.finditer(task_pattern, self.content, re.DOTALL)

        for match in matches:
            task_code = match.group(1)
            task_content = match.group(2)

            task = self._parse_single_task(task_code, task_content)
            if task:
                tasks.append(task)

        return tasks

    def _parse_single_task(self, task_code: str, content: str) -> Optional[Dict]:
        """Parse a single task section."""
        task = {
            'task_code': task_code,
            'phase': self._extract_phase(task_code)
        }

        # Extract title
        title_match = re.search(r'\*\*Title:\*\*\s*(.+)', content)
        if title_match:
            task['title'] = title_match.group(1).strip()
        else:
            # Fallback: use first line after task code
            first_line = content.split('\n')[0].strip()
            task['title'] = first_line if first_line else task_code

        # Extract description
        desc_match = re.search(r'\*\*Description:\*\*\s*(.+?)(?=\*\*|$)', content, re.DOTALL)
        if desc_match:
            task['description'] = desc_match.group(1).strip()

        # Extract estimated time
        time_match = re.search(r'\*\*Estimated Time:\*\*\s*(.+)', content)
        if time_match:
            time_str = time_match.group(1).strip()
            task['estimated_minutes'] = self._parse_time_to_minutes(time_str)

        # Extract risk level
        risk_match = re.search(r'\*\*Risk Level:\*\*\s*(\w+)', content)
        if risk_match:
            task['risk_level'] = risk_match.group(1).strip().lower()

        # Extract dependencies
        dep_match = re.search(r'\*\*Dependencies:\*\*\s*(.+)', content)
        if dep_match:
            dep_str = dep_match.group(1).strip()
            if dep_str.lower() == 'none':
                task['dependencies'] = []
            else:
                # Parse task codes from dependency string
                dep_codes = re.findall(r'PHASE\d+-TASK\d+', dep_str)
                task['dependencies'] = dep_codes
        else:
            task['dependencies'] = []

        # Check if task is completed (has checkmark)
        if '✅' in content or 'COMPLETED' in content.upper():
            task['status'] = 'done'
        else:
            task['status'] = 'todo'

        return task

    def _extract_phase(self, task_code: str) -> str:
        """Extract phase number from task code."""
        match = re.search(r'PHASE(\d+)', task_code)
        if match:
            return f"Phase {match.group(1)}"
        return "Unknown Phase"

    def _parse_time_to_minutes(self, time_str: str) -> int:
        """Convert time string to minutes."""
        # Handle formats like: "5 minutes", "1-2 hours", "30 min", etc.
        time_str = time_str.lower()

        # Try to extract minutes
        min_match = re.search(r'(\d+)\s*(?:min|minute)', time_str)
        if min_match:
            return int(min_match.group(1))

        # Try to extract hours
        hour_match = re.search(r'(\d+)(?:-(\d+))?\s*(?:hour|hr)', time_str)
        if hour_match:
            hours = int(hour_match.group(1))
            if hour_match.group(2):  # Range like "1-2 hours"
                hours = (hours + int(hour_match.group(2))) / 2  # Use average
            return int(hours * 60)

        return 0  # Default if can't parse


def find_spec_folders(project_path: str) -> List[str]:
    """Find all spec folders in a project's agent-os directory."""
    agent_os_path = Path(project_path) / "agent-os" / "specs"

    if not agent_os_path.exists():
        return []

    spec_folders = []
    for folder in agent_os_path.iterdir():
        if folder.is_dir() and not folder.name.startswith('.'):
            spec_folders.append(str(folder))

    return spec_folders


def parse_spec_folder(spec_folder_path: str) -> Optional[Dict]:
    """Parse a complete spec folder including tasks.md."""
    spec_path = Path(spec_folder_path)

    if not spec_path.exists():
        return None

    # Extract spec name from folder name (e.g., 2025-10-29-manual-appointment-times)
    folder_name = spec_path.name
    date_match = re.match(r'(\d{4}-\d{2}-\d{2})-(.+)', folder_name)

    if date_match:
        date_str = date_match.group(1)
        spec_slug = date_match.group(2)
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')
        spec_slug = folder_name

    # Parse tasks.md if it exists
    tasks_md = spec_path / "tasks.md"
    if tasks_md.exists():
        parser = TasksParser(str(tasks_md))
        parsed = parser.parse()
    else:
        parsed = {"metadata": {}, "overview": {}, "tasks": []}

    return {
        "folder_name": folder_name,
        "slug": spec_slug,
        "path": str(spec_path),
        "date": date_str,
        "name": parsed['metadata'].get('spec_name', spec_slug.replace('-', ' ').title()),
        "metadata": parsed['metadata'],
        "overview": parsed['overview'],
        "tasks": parsed['tasks']
    }


if __name__ == "__main__":
    # Test with Pistn specs
    pistn_path = "/Users/iamanmp/Projects/pistn"
    spec_folders = find_spec_folders(pistn_path)

    print(f"Found {len(spec_folders)} specs in Pistn:")
    for folder in spec_folders:
        spec_data = parse_spec_folder(folder)
        if spec_data:
            print(f"\n📋 {spec_data['name']}")
            print(f"   Folder: {spec_data['folder_name']}")
            print(f"   Tasks: {len(spec_data['tasks'])}")
