#!/usr/bin/env python3
"""
Smart Code Indexer for Claude OS
Intelligently chunks and indexes ALL code files in a project.
Supports multiple languages and formats.
"""

import os
import re
import time
from pathlib import Path
from typing import List, Dict, Tuple
import urllib.request
import urllib.error
import json


class CodeIndexer:
    """Intelligently index project code for semantic search."""

    def __init__(self, project_path: str, project_id: int, api_url: str = "http://localhost:8051", max_files: int = 150):
        self.project_path = Path(project_path).resolve()
        self.project_id = project_id
        self.api_url = api_url
        self.max_files = max_files  # Limit for faster indexing

        # File patterns to index
        self.include_patterns = {
            'rb': ['app/**/*.rb', 'lib/**/*.rb', 'spec/**/*.rb', 'config/**/*.rb'],
            'js': ['app/javascript/**/*.js', 'app/assets/javascripts/**/*.js', '**/*.js'],
            'ts': ['**/*.ts', '**/*.tsx'],
            'jsx': ['**/*.jsx'],
            'json': ['package.json', 'Gemfile.lock', '*.json'],
            'yaml': ['**/*.yml', '**/*.yaml'],
            'md': ['README.md', '**/*.md'],
        }

        # Directories to skip
        self.skip_dirs = {
            '.git', 'node_modules', '.venv', 'venv', '__pycache__',
            'dist', 'build', '.next', '.nuxt', 'coverage', 'tmp',
            '.claude-os', '.env', '.DS_Store', '.bundle', 'vendor',
            'test', 'tests', 'spec', 'specs', '__tests__', '.turbo'
        }

        self.indexed_count = 0
        self.indexed_files = []

    def _should_skip(self, path: Path) -> bool:
        """Check if path should be skipped."""
        for skip_dir in self.skip_dirs:
            if skip_dir in path.parts:
                return True
        return False

    def _find_files(self) -> List[Path]:
        """Find all indexable files in project, prioritizing source files."""
        source_files = []
        config_files = []
        doc_files = []

        for root, dirs, filenames in os.walk(self.project_path):
            # Remove skip directories
            dirs[:] = [d for d in dirs if d not in self.skip_dirs]

            for filename in filenames:
                filepath = Path(root) / filename
                if self._should_skip(filepath):
                    continue

                # Check file extension and categorize
                if filepath.suffix in ['.rb', '.js', '.ts', '.tsx', '.jsx']:
                    source_files.append(filepath)
                elif filepath.suffix in ['.json', '.yml', '.yaml']:
                    config_files.append(filepath)
                elif filepath.suffix in ['.md']:
                    doc_files.append(filepath)

        # Combine in priority order: source files, config files, docs
        files = sorted(source_files) + sorted(config_files) + sorted(doc_files)

        # Limit to max_files for faster indexing
        files = files[:self.max_files]

        return files

    def _parse_ruby(self, content: str, filepath: str) -> List[Dict]:
        """Parse Ruby file into logical chunks."""
        chunks = []
        lines = content.split('\n')
        current_class = None
        current_method = None
        buffer = []
        buffer_start = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Class definition
            if stripped.startswith('class '):
                if buffer:
                    chunks.append({
                        'type': 'method' if current_method else 'block',
                        'name': current_method or current_class or 'code',
                        'class': current_class,
                        'file': str(Path(filepath).relative_to(self.project_path)),
                        'line': buffer_start,
                        'content': '\n'.join(buffer),
                        'language': 'ruby'
                    })
                    buffer = []

                match = re.match(r'class\s+(\w+)', stripped)
                if match:
                    current_class = match.group(1)
                    current_method = None
                    buffer_start = i

            # Method definition
            elif stripped.startswith('def '):
                if buffer and current_method:
                    chunks.append({
                        'type': 'method',
                        'name': current_method,
                        'class': current_class,
                        'file': str(Path(filepath).relative_to(self.project_path)),
                        'line': buffer_start,
                        'content': '\n'.join(buffer),
                        'language': 'ruby'
                    })
                    buffer = []

                match = re.match(r'def\s+(\w+)', stripped)
                if match:
                    current_method = match.group(1)
                    buffer_start = i

            buffer.append(line)

        # Add final chunk
        if buffer:
            chunks.append({
                'type': 'method' if current_method else 'class' if current_class else 'file',
                'name': current_method or current_class or Path(filepath).name,
                'class': current_class,
                'file': str(Path(filepath).relative_to(self.project_path)),
                'line': buffer_start,
                'content': '\n'.join(buffer),
                'language': 'ruby'
            })

        return chunks

    def _parse_javascript(self, content: str, filepath: str) -> List[Dict]:
        """Parse JavaScript/TypeScript file into logical chunks."""
        chunks = []
        lines = content.split('\n')
        current_class = None
        current_function = None
        buffer = []
        buffer_start = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Class definition
            if stripped.startswith('class '):
                if buffer:
                    chunks.append({
                        'type': 'function' if current_function else 'block',
                        'name': current_function or current_class or 'code',
                        'class': current_class,
                        'file': str(Path(filepath).relative_to(self.project_path)),
                        'line': buffer_start,
                        'content': '\n'.join(buffer),
                        'language': 'javascript'
                    })
                    buffer = []

                match = re.match(r'class\s+(\w+)', stripped)
                if match:
                    current_class = match.group(1)
                    current_function = None
                    buffer_start = i

            # Function definition
            elif any(stripped.startswith(prefix) for prefix in ['function ', 'const ', 'let ', 'var ', 'async function', 'export ']):
                if buffer and current_function:
                    chunks.append({
                        'type': 'function',
                        'name': current_function,
                        'class': current_class,
                        'file': str(Path(filepath).relative_to(self.project_path)),
                        'line': buffer_start,
                        'content': '\n'.join(buffer),
                        'language': 'javascript'
                    })
                    buffer = []

                # Extract function name
                match = re.search(r'(?:function|const|let|var)\s+(\w+)', stripped)
                if match:
                    current_function = match.group(1)
                    buffer_start = i

            buffer.append(line)

        # Add final chunk
        if buffer:
            chunks.append({
                'type': 'function' if current_function else 'class' if current_class else 'file',
                'name': current_function or current_class or Path(filepath).name,
                'class': current_class,
                'file': str(Path(filepath).relative_to(self.project_path)),
                'line': buffer_start,
                'content': '\n'.join(buffer),
                'language': 'javascript'
            })

        return chunks

    def _chunk_file(self, filepath: Path) -> List[Dict]:
        """Chunk a file into logical units based on language."""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Skip empty files
            if not content.strip():
                return []

            # Parse based on file type
            if filepath.suffix == '.rb':
                return self._parse_ruby(content, str(filepath))
            elif filepath.suffix in ['.js', '.jsx', '.ts', '.tsx']:
                return self._parse_javascript(content, str(filepath))
            else:
                # For other files, treat as single chunk
                return [{
                    'type': 'file',
                    'name': filepath.name,
                    'file': str(filepath.relative_to(self.project_path)),
                    'line': 0,
                    'content': content,
                    'language': filepath.suffix.lstrip('.')
                }]

        except Exception as e:
            print(f"⚠️  Error chunking {filepath}: {e}")
            return []

    def _ingest_chunk(self, chunk: Dict, kb_name: str) -> bool:
        """Ingest a single chunk to project-index MCP."""
        try:
            payload = {
                "filename": chunk['file'],
                "content": chunk['content'],
                "mcp_type": "project_index",
                "metadata": {
                    "type": chunk['type'],
                    "name": chunk['name'],
                    "class": chunk.get('class'),
                    "line": chunk['line'],
                    "language": chunk['language']
                }
            }

            req_url = f"{self.api_url}/api/projects/{self.project_id}/ingest-document"
            payload_json = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                req_url,
                data=payload_json,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status in [200, 201]:
                    return True
                return False

        except Exception as e:
            print(f"⚠️  Error ingesting chunk: {e}")
            return False

    def run(self) -> Dict:
        """Index the entire project."""
        print(f"\n🔍 Indexing all code files in {self.project_path.name}...")

        # Get all files
        files = self._find_files()
        print(f"📂 Found {len(files)} files to index")

        kb_name = f"{self.project_path.name}-project_index"

        # Index each file
        total_chunks = 0
        for filepath in files:
            chunks = self._chunk_file(filepath)

            for chunk in chunks:
                if self._ingest_chunk(chunk, kb_name):
                    total_chunks += 1

            # Progress indicator
            if (len(self.indexed_files) + 1) % 10 == 0:
                print(f"  ✓ Indexed {len(self.indexed_files) + 1}/{len(files)} files...")

            self.indexed_files.append(str(filepath.relative_to(self.project_path)))

        self.indexed_count = total_chunks

        print(f"✅ Indexing complete!")
        print(f"   📦 {total_chunks} chunks indexed from {len(files)} files")
        print(f"   📍 Indexed to: {kb_name}")

        return {
            "total_files": len(files),
            "total_chunks": total_chunks,
            "files_indexed": self.indexed_files
        }
