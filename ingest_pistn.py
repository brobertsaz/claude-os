#!/usr/bin/env python3
"""
Ingestion script for Pistn Agent OS profile.
Optimized for Claude CLI MCP integration.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.pg_manager import get_pg_manager
from app.core.agent_os_ingestion import AgentOSIngestion
from mcp_server.server import get_cached_rag_engine


def main():
    """Ingest Pistn Agent OS profile with optimizations."""

    kb_name = "pistn"
    profile_path = "/Users/iamanmp/Projects/pistn/agent-os"

    print("🚀 Ingesting Pistn Agent OS Profile")
    print("=" * 50)

    # Step 1: Create or verify knowledge base
    pg_manager = get_pg_manager()

    if not pg_manager.collection_exists(kb_name):
        print(f"Creating knowledge base: {kb_name}")
        from app.core.kb_types import KBType
        success = pg_manager.create_collection(
            name=kb_name,
            kb_type=KBType.AGENT_OS,
            description="Pistn project knowledge base with Agent OS profile"
        )
        if not success:
            print("❌ Failed to create knowledge base")
            return
        print(f"✅ Created Agent OS knowledge base: {kb_name}")
    else:
        print(f"✅ Knowledge base '{kb_name}' already exists")

    # Step 2: Ingest the Agent OS profile
    print(f"\n📁 Ingesting from: {profile_path}")
    print("This will process:")
    print("  • 14 standards files (coding conventions, API design, etc.)")
    print("  • 3 product files (mission, roadmap, tech stack)")
    print("  • 2 role definitions (implementers, verifiers)")
    print("  • 32 spec files (detailed feature implementations)")
    print("  • 1 config file")

    ingestion = AgentOSIngestion(pg_manager)

    try:
        stats = ingestion.ingest_profile(
            kb_name=kb_name,
            profile_path=profile_path
        )

        print(f"\n✅ Successfully ingested {stats.get('documents_processed', 0)} documents")

        if 'documents_by_type' in stats:
            print("\n📊 Document breakdown by type:")
            for doc_type, count in stats['documents_by_type'].items():
                print(f"  • {doc_type}: {count} documents")

        # Step 3: Pre-warm the cache for better performance
        print("\n🔥 Pre-warming RAGEngine cache...")
        engine = get_cached_rag_engine(kb_name)
        print("✅ Cache warmed - first queries will be faster")

        # Step 4: Provide usage examples
        print("\n" + "=" * 50)
        print("🎯 PISTN KNOWLEDGE BASE READY!")
        print("=" * 50)

        print("\n📝 Most Useful Files for Claude CLI:\n")

        print("1️⃣ CRITICAL FOR UNDERSTANDING PROJECT:")
        print("  • product/mission.md - Project vision and goals")
        print("  • product/tech-stack.md - Technology choices")
        print("  • standards/global/conventions.md - Overall conventions")
        print("  • standards/global/coding-style.md - Coding standards")

        print("\n2️⃣ BACKEND DEVELOPMENT:")
        print("  • standards/backend/api.md - API design patterns")
        print("  • standards/backend/models.md - Database models")
        print("  • standards/backend/queries.md - Query patterns")

        print("\n3️⃣ FRONTEND DEVELOPMENT:")
        print("  • standards/frontend/components.md - Component patterns")
        print("  • standards/frontend/css.md - Styling conventions")
        print("  • standards/frontend/accessibility.md - A11y requirements")

        print("\n4️⃣ RECENT FEATURE IMPLEMENTATIONS:")
        print("  • specs/2025-10-14-account-users-devise/* - User authentication")
        print("  • specs/2025-10-15-group-account-rendering/* - Account rendering")

        print("\n" + "=" * 50)
        print("🔍 EXAMPLE QUERIES FOR CLAUDE CLI:")
        print("=" * 50)

        print("""
# Fast queries (5-10s with cache):
1. "What is the Pistn project mission?"
2. "Show me the API design standards"
3. "What are the frontend component conventions?"

# Medium queries (10-15s with cache):
1. "How should I implement user authentication in Pistn?"
2. "Explain the database model patterns used in Pistn"
3. "What are the CSS and styling guidelines?"

# Complex queries (15-20s but comprehensive):
1. "Explain the complete group account rendering implementation"
2. "How does Pistn handle user accounts with Devise?"
3. "What are all the testing requirements for new features?"
""")

        print("\n💡 OPTIMIZATION TIPS:")
        print("  • First query will be slower (builds cache)")
        print("  • Subsequent queries use cache (5-10s faster)")
        print("  • Be specific in queries for faster responses")
        print("  • Use 'get_standards' for quick standard lookups")

    except Exception as e:
        print(f"\n❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n✨ Done! Your Pistn knowledge base is ready for Claude CLI!")


if __name__ == "__main__":
    main()