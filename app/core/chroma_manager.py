"""
ChromaDB client manager for knowledge base operations.
Implements singleton pattern for connection reuse.
"""

import logging
from typing import List, Optional

import chromadb
from chromadb.config import Settings

from app.core.config import Config

logger = logging.getLogger(__name__)


class ChromaManager:
    """Singleton manager for ChromaDB operations."""
    
    _instance = None
    _client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB HTTP client."""
        try:
            self._client = chromadb.HttpClient(
                host=Config.CHROMA_HOST,
                port=Config.CHROMA_PORT
            )
            logger.info(f"ChromaDB client initialized: {Config.get_chroma_url()}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise
    
    def get_client(self) -> chromadb.HttpClient:
        """Get the ChromaDB client instance."""
        if self._client is None:
            self._initialize_client()
        return self._client
    
    def list_collections(self) -> List[str]:
        """
        List all collection names.
        
        Returns:
            List of collection names
        """
        try:
            collections = self._client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []
    
    def create_collection(self, name: str) -> bool:
        """
        Create a new collection (knowledge base).
        
        Args:
            name: Collection name
        
        Returns:
            bool: True if successful
        """
        try:
            self._client.get_or_create_collection(name=name)
            logger.info(f"Collection created: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create collection {name}: {e}")
            return False
    
    def delete_collection(self, name: str) -> bool:
        """
        Delete a collection.
        
        Args:
            name: Collection name
        
        Returns:
            bool: True if successful
        """
        try:
            self._client.delete_collection(name=name)
            logger.info(f"Collection deleted: {name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete collection {name}: {e}")
            return False
    
    def get_collection(self, name: str) -> Optional[chromadb.Collection]:
        """
        Get a collection by name.
        
        Args:
            name: Collection name
        
        Returns:
            Collection object or None if not found
        """
        try:
            return self._client.get_collection(name=name)
        except Exception as e:
            logger.warning(f"Collection {name} not found: {e}")
            return None
    
    def get_collection_count(self, name: str) -> int:
        """
        Get the number of documents in a collection.
        
        Args:
            name: Collection name
        
        Returns:
            int: Document count (0 if collection not found)
        """
        try:
            collection = self.get_collection(name)
            if collection:
                return collection.count()
            return 0
        except Exception as e:
            logger.error(f"Failed to get count for {name}: {e}")
            return 0
    
    def collection_exists(self, name: str) -> bool:
        """
        Check if a collection exists.
        
        Args:
            name: Collection name
        
        Returns:
            bool: True if collection exists
        """
        return name in self.list_collections()


# Global singleton instance
_chroma_manager = None


def get_chroma_manager() -> ChromaManager:
    """Get the global ChromaManager instance."""
    global _chroma_manager
    if _chroma_manager is None:
        _chroma_manager = ChromaManager()
    return _chroma_manager

