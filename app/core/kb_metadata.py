"""
Knowledge base metadata management for UI display.
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

from app.core.pg_manager import get_pg_manager
from app.core.kb_types import KBType, get_kb_type_info, validate_kb_type

logger = logging.getLogger(__name__)


def generate_tags(file_type: str) -> List[str]:
    """
    Generate display tags based on file type.

    Args:
        file_type: File extension (e.g., '.py', '.md')

    Returns:
        List of tag strings
    """
    tag_map = {
        ".py": ["Code", "Python"],
        ".js": ["Code", "JavaScript"],
        ".jsx": ["Code", "React"],
        ".ts": ["Code", "TypeScript"],
        ".tsx": ["Code", "React", "TypeScript"],
        ".go": ["Code", "Go"],
        ".rs": ["Code", "Rust"],
        ".java": ["Code", "Java"],
        ".cpp": ["Code", "C++"],
        ".c": ["Code", "C"],
        ".h": ["Code", "Header"],
        ".md": ["Document", "Markdown"],
        ".txt": ["Document", "Text"],
        ".pdf": ["Document", "PDF"],
        ".json": ["Config", "JSON"],
        ".yaml": ["Config", "YAML"],
        ".yml": ["Config", "YAML"],
    }

    return tag_map.get(file_type.lower(), ["Document", "Unknown"])


def format_timestamp(iso_timestamp: str) -> str:
    """
    Format ISO timestamp for display.

    Args:
        iso_timestamp: ISO format timestamp string

    Returns:
        Formatted string (e.g., "Updated: 10/22/2025")
    """
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return f"Updated: {dt.strftime('%m/%d/%Y')}"
    except Exception:
        return "Updated: Unknown"


def get_documents_metadata(collection_name: str) -> List[Dict[str, any]]:
    """
    Get metadata for all documents in a collection.
    Groups chunks by filename and aggregates metadata.

    Args:
        collection_name: Name of the collection

    Returns:
        List of document metadata dicts
    """
    try:
        pg_manager = get_pg_manager()

        if not pg_manager.collection_exists(collection_name):
            logger.warning(f"Collection {collection_name} not found")
            return []

        # Get all documents with metadata
        results = pg_manager.get_documents_by_metadata(collection_name, where={})

        if not results:
            return []

        # Group chunks by filename
        docs_by_filename = defaultdict(list)
        for doc in results:
            metadata = doc.get("metadata", {})
            filename = metadata.get("filename", "unknown")
            docs_by_filename[filename].append(metadata)

        # Aggregate metadata for each document
        documents = []
        for filename, chunks in docs_by_filename.items():
            # Get metadata from first chunk
            first_chunk = chunks[0]
            file_type = first_chunk.get("file_type", "")
            upload_date = first_chunk.get("upload_date", "")

            documents.append({
                "filename": filename,
                "file_type": file_type,
                "tags": generate_tags(file_type),
                "upload_date": upload_date,
                "formatted_date": format_timestamp(upload_date),
                "chunk_count": len(chunks)
            })

        # Sort by upload date (newest first)
        documents.sort(
            key=lambda x: x.get("upload_date", ""),
            reverse=True
        )

        return documents

    except Exception as e:
        logger.error(f"Failed to get documents metadata: {e}")
        return []


def get_collection_stats(collection_name: str) -> Dict[str, any]:
    """
    Get statistics for a collection including KB type.

    Args:
        collection_name: Name of the collection

    Returns:
        dict: Statistics including total docs, chunks, last updated, and kb_type
    """
    try:
        pg_manager = get_pg_manager()

        if not pg_manager.collection_exists(collection_name):
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "last_updated": None,
                "kb_type": KBType.GENERIC.value
            }

        # Get KB type from collection metadata
        kb_metadata = pg_manager.get_collection_metadata(collection_name)
        kb_type = kb_metadata.get("kb_type", KBType.GENERIC.value) if kb_metadata else KBType.GENERIC.value

        # Get all documents with metadata
        results = pg_manager.get_documents_by_metadata(collection_name, where={})

        # Count unique documents
        unique_filenames = set(
            doc.get("metadata", {}).get("filename", "") for doc in results
        )

        # Get latest upload date
        upload_dates = [
            doc.get("metadata", {}).get("upload_date", "")
            for doc in results
            if doc.get("metadata", {}).get("upload_date")
        ]
        last_updated = max(upload_dates) if upload_dates else None

        return {
            "total_documents": len(unique_filenames),
            "total_chunks": len(results),
            "last_updated": last_updated,
            "kb_type": kb_type if isinstance(kb_type, str) else kb_type.value
        }

    except Exception as e:
        logger.error(f"Failed to get collection stats: {e}")
        return {
            "total_documents": 0,
            "total_chunks": 0,
            "last_updated": None,
            "kb_type": KBType.GENERIC.value
        }

def get_kb_type_badge(kb_type: KBType) -> str:
    """
    Generate HTML badge for KB type display in UI.

    Args:
        kb_type: The KB type

    Returns:
        HTML string for badge display

    Example:
        >>> get_kb_type_badge(KBType.AGENT_OS)
        '<span style="...">🤖 Agent OS Profile</span>'
    """
    info = get_kb_type_info(kb_type)

    return f'''
    <span style="
        background: {info.color}20;
        color: {info.color};
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        border: 1px solid {info.color}40;
        display: inline-block;
    ">
        {info.icon} {info.name}
    </span>
    '''


def get_kb_type_summary() -> Dict[str, int]:
    """
    Get summary of KB counts by type across all knowledge bases.

    Returns:
        Dict mapping KB type values to counts

    Example:
        {
            "generic": 2,
            "code": 5,
            "documentation": 3,
            "agent-os": 1
        }
    """
    try:
        pg_manager = get_pg_manager()
        collections = pg_manager.list_collections()

        # Count by type
        type_counts = {kb_type.value: 0 for kb_type in KBType}

        for col in collections:
            kb_type = col["metadata"].get("kb_type", KBType.GENERIC.value)
            if kb_type in type_counts:
                type_counts[kb_type] += 1
            else:
                # Handle unknown types
                type_counts[KBType.GENERIC.value] += 1

        return type_counts

    except Exception as e:
        logger.error(f"Failed to get KB type summary: {e}")
        return {kb_type.value: 0 for kb_type in KBType}


