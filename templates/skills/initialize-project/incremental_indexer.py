#!/usr/bin/env python3
"""
Incremental Code Indexer - expands project index with unindexed files
Called periodically by git hook to gradually build full project index
"""

import os
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from code_indexer import CodeIndexer


class IncrementalIndexer:
    """Expand project index with previously unindexed files."""

    def __init__(self, project_path: str, project_id: int, api_url: str = "http://localhost:8051"):
        self.project_path = Path(project_path).resolve()
        self.project_id = project_id
        self.api_url = api_url
        self.state_file = self.project_path / ".claude-os" / ".index_state"

    def _get_indexed_files(self) -> set:
        """Query project-index MCP to get list of already indexed files."""
        try:
            # This would query the MCP to get indexed files
            # For now, we'll track locally in the state file
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    return set(data.get('indexed_files', []))
            return set()
        except Exception as e:
            print(f"⚠️  Could not read indexed files: {e}")
            return set()

    def _find_all_code_files(self) -> list:
        """Find all code files in project."""
        code_extensions = {'.rb', '.js', '.ts', '.tsx', '.jsx', '.json', '.yml', '.yaml', '.md'}
        skip_dirs = {
            '.git', 'node_modules', '.venv', 'venv', '__pycache__',
            'dist', 'build', '.next', '.nuxt', 'coverage', 'tmp',
            '.claude-os', '.env', '.DS_Store', '.bundle', 'vendor',
            'test', 'tests', 'spec', 'specs', '__tests__', '.turbo'
        }

        files = []
        for root, dirs, filenames in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in skip_dirs]

            for filename in filenames:
                filepath = Path(root) / filename
                if filepath.suffix in code_extensions:
                    rel_path = str(filepath.relative_to(self.project_path))
                    files.append(rel_path)

        return sorted(files)

    def _save_state(self, indexed_files: set):
        """Save indexing state."""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump({
                    'indexed_files': sorted(list(indexed_files)),
                    'total_files': len(indexed_files)
                }, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save state: {e}")

    def expand_index(self, batch_size: int = 30) -> dict:
        """Index next batch of unindexed files."""
        print(f"\n🔄 Expanding project index...")

        all_files = self._find_all_code_files()
        indexed_files = self._get_indexed_files()
        unindexed = [f for f in all_files if f not in indexed_files]

        if not unindexed:
            print(f"✅ All {len(all_files)} files already indexed!")
            return {"indexed": 0, "total_files": len(all_files), "status": "complete"}

        # Index next batch
        batch = unindexed[:batch_size]
        print(f"📂 Found {len(unindexed)} unindexed files, indexing next {len(batch)}...")

        indexer = CodeIndexer(str(self.project_path), self.project_id, self.api_url)
        indexed_count = 0
        chunk_count = 0

        for file_path in batch:
            full_path = self.project_path / file_path
            if not full_path.exists():
                continue

            try:
                chunks = indexer._chunk_file(full_path)
                for chunk in chunks:
                    if indexer._ingest_chunk(chunk, f"{self.project_path.name}-project_index"):
                        chunk_count += 1
                indexed_count += 1
            except Exception as e:
                print(f"⚠️  Error indexing {file_path}: {e}")

        # Update state
        new_indexed = indexed_files | set(batch)
        self._save_state(new_indexed)

        progress = f"{len(new_indexed)}/{len(all_files)}"
        print(f"✅ Expansion complete: {chunk_count} chunks from {indexed_count} files")
        print(f"   📊 Total indexed: {progress} ({100*len(new_indexed)//len(all_files)}%)")

        return {
            "indexed": indexed_count,
            "chunks": chunk_count,
            "progress": f"{len(new_indexed)}/{len(all_files)}",
            "percentage": 100 * len(new_indexed) // len(all_files),
            "status": "in_progress" if len(new_indexed) < len(all_files) else "complete"
        }


def main():
    if len(sys.argv) < 3:
        print("Usage: incremental_indexer.py <project_id> <project_path> [api_url] [batch_size]")
        sys.exit(1)

    try:
        project_id = int(sys.argv[1])
        project_path = sys.argv[2]
        api_url = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8051"
        batch_size = int(sys.argv[4]) if len(sys.argv) > 4 else 30

        indexer = IncrementalIndexer(project_path, project_id, api_url)
        result = indexer.expand_index(batch_size)

        # Exit with status code
        sys.exit(0 if result['status'] == 'complete' else 0)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
