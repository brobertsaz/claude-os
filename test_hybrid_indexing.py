#!/usr/bin/env python3
"""
Test script for hybrid indexing system.

This demonstrates the new tree-sitter based indexing without requiring
full dependency installation.

To run the full test:
1. Fix venv or create new one:
   python3 -m venv venv_new
   source venv_new/bin/activate
   pip install -r requirements.txt

2. Run this script:
   python3 test_hybrid_indexing.py /path/to/pistn/project
"""

import sys
import time
from pathlib import Path

def test_imports():
    """Test if tree-sitter imports work."""
    print("Testing imports...")
    try:
        from app.core.tree_sitter_indexer import TreeSitterIndexer, Tag, RepoMap
        print("✅ tree_sitter_indexer module imported")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_basic_functionality():
    """Test basic indexer functionality with mock data."""
    print("\n Testing basic functionality...")

    try:
        from app.core.tree_sitter_indexer import Tag, RepoMap
        import networkx as nx
    except ImportError as e:
        print(f"❌ Dependencies missing: {e}")
        print("\nTo install dependencies:")
        print("  python3 -m venv venv_new")
        print("  source venv_new/bin/activate")
        print("  pip install tree-sitter tree-sitter-languages networkx")
        return False

    # Create mock tags
    tags = [
        Tag(
            file="app/models/user.rb",
            name="User",
            kind="class",
            line=1,
            signature="class User < ApplicationRecord"
        ),
        Tag(
            file="app/models/user.rb",
            name="authenticate",
            kind="method",
            line=10,
            signature="def authenticate(email, password)"
        ),
        Tag(
            file="app/controllers/sessions_controller.rb",
            name="SessionsController",
            kind="class",
            line=1,
            signature="class SessionsController < ApplicationController"
        ),
    ]

    # Create simple dependency graph
    graph = nx.MultiDiGraph()
    graph.add_node("app/models/user.rb")
    graph.add_node("app/controllers/sessions_controller.rb")
    graph.add_edge(
        "app/controllers/sessions_controller.rb",
        "app/models/user.rb",
        weight=1.0,
        symbol="User"
    )

    # Create mock repo map
    repo_map = RepoMap(
        tags=tags,
        dependency_graph=graph,
        file_index={
            "app/models/user.rb": tags[:2],
            "app/controllers/sessions_controller.rb": [tags[2]]
        },
        symbol_index={
            "User": [tags[0]],
            "authenticate": [tags[1]],
            "SessionsController": [tags[2]]
        },
        total_files=2,
        total_symbols=3,
        indexed_at=time.time()
    )

    print(f"✅ Created mock repo map with {repo_map.total_symbols} symbols")
    print(f"   Files: {', '.join(repo_map.file_index.keys())}")
    print(f"   Symbols: {', '.join(repo_map.symbol_index.keys())}")

    return True


def test_real_indexing(project_path: str):
    """Test real indexing on a project."""
    print(f"\n🚀 Testing real indexing on: {project_path}")

    if not Path(project_path).exists():
        print(f"❌ Project path does not exist: {project_path}")
        return False

    try:
        from app.core.tree_sitter_indexer import TreeSitterIndexer
    except ImportError as e:
        print(f"❌ Dependencies missing: {e}")
        return False

    try:
        # Create indexer
        cache_path = str(Path(project_path) / ".claude-os" / "tree_sitter_cache.db")
        indexer = TreeSitterIndexer(cache_path)

        print("⚡ Starting structural indexing...")
        start_time = time.time()

        # Index the directory
        repo_map = indexer.index_directory(project_path, token_budget=2048)

        elapsed = time.time() - start_time

        print(f"\n✅ Indexing complete!")
        print(f"   Time: {elapsed:.1f} seconds")
        print(f"   Files: {repo_map.total_files}")
        print(f"   Symbols: {repo_map.total_symbols}")

        # Show top 10 most important symbols
        print(f"\n🏆 Top 10 Most Important Symbols (by PageRank):")
        for i, tag in enumerate(repo_map.tags[:10], 1):
            print(f"   {i}. {tag.name} ({tag.kind}) in {tag.file}")
            print(f"      Importance: {tag.importance:.4f}")

        # Generate compact repo map
        print(f"\n📊 Generating compact repo map (1024 token budget)...")
        compact_map = indexer.generate_repo_map(repo_map.tags, token_budget=1024)
        print(f"   Token count: ~{len(compact_map) // 4}")
        print(f"\n   Preview (first 500 chars):")
        print(compact_map[:500])

        # Close indexer
        indexer.close()

        return True

    except Exception as e:
        print(f"❌ Indexing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("=" * 60)
    print("  Claude OS Hybrid Indexing Test")
    print("=" * 60)

    # Test 1: Imports
    if not test_imports():
        print("\n⚠️  Tree-sitter dependencies not installed")
        print("    Basic module structure is correct, but needs:")
        print("    - tree-sitter")
        print("    - tree-sitter-languages")
        print("    - networkx")
        return

    # Test 2: Basic functionality
    test_basic_functionality()

    # Test 3: Real indexing (if project path provided)
    if len(sys.argv) > 1:
        project_path = sys.argv[1]
        test_real_indexing(project_path)
    else:
        print("\n💡 To test on a real project, run:")
        print(f"   python3 {sys.argv[0]} /path/to/your/project")


if __name__ == "__main__":
    main()
