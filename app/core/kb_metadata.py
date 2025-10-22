"""
Knowledge base metadata management for UI display.
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

from app.core.chroma_manager import get_chroma_manager

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
        chroma_manager = get_chroma_manager()
        collection = chroma_manager.get_collection(collection_name)
        
        if not collection:
            logger.warning(f"Collection {collection_name} not found")
            return []
        
        # Get all documents with metadata
        results = collection.get(include=["metadatas"])
        
        if not results or not results.get("metadatas"):
            return []
        
        # Group chunks by filename
        docs_by_filename = defaultdict(list)
        for metadata in results["metadatas"]:
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
    Get statistics for a collection.
    
    Args:
        collection_name: Name of the collection
    
    Returns:
        dict: Statistics including total docs, chunks, last updated
    """
    try:
        chroma_manager = get_chroma_manager()
        collection = chroma_manager.get_collection(collection_name)
        
        if not collection:
            return {
                "total_documents": 0,
                "total_chunks": 0,
                "last_updated": None
            }
        
        # Get all metadata
        results = collection.get(include=["metadatas"])
        metadatas = results.get("metadatas", [])
        
        # Count unique documents
        unique_filenames = set(
            m.get("filename", "") for m in metadatas
        )
        
        # Get latest upload date
        upload_dates = [
            m.get("upload_date", "") for m in metadatas if m.get("upload_date")
        ]
        last_updated = max(upload_dates) if upload_dates else None
        
        return {
            "total_documents": len(unique_filenames),
            "total_chunks": len(metadatas),
            "last_updated": last_updated
        }
        
    except Exception as e:
        logger.error(f"Failed to get collection stats: {e}")
        return {
            "total_documents": 0,
            "total_chunks": 0,
            "last_updated": None
        }

