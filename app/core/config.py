"""
Configuration management for Code-Forge.
Centralizes all application settings with environment variable support.
"""

import os
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Central configuration for Code-Forge application."""

    # Ollama Configuration
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:latest")  # Upgraded to faster 8B model
    OLLAMA_EMBED_MODEL: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

    # ChromaDB Configuration
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "chromadb")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8000"))

    # MCP Server Configuration
    MCP_SERVER_HOST: str = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
    MCP_SERVER_PORT: int = int(os.getenv("MCP_SERVER_PORT", "8051"))

    # Supported File Types
    SUPPORTED_FILE_TYPES: List[str] = [
        ".md", ".txt", ".pdf",
        ".py", ".js", ".jsx", ".ts", ".tsx",
        ".json", ".yaml", ".yml",
        ".go", ".rs", ".java", ".cpp", ".c", ".h"
    ]

    # RAG Configuration
    CHUNK_SIZE: int = 1024
    CHUNK_OVERLAP: int = 200
    TOP_K_RETRIEVAL: int = 15  # Increased to retrieve more context from 51 docs
    RERANK_TOP_N: int = 8  # Top chunks after reranking (increased for better context)
    SIMILARITY_THRESHOLD: float = 0.5  # Lowered to include more relevant chunks

    # KB Type Configuration
    DEFAULT_KB_TYPE: str = os.getenv("DEFAULT_KB_TYPE", "generic")

    # Type-specific RAG strategy recommendations
    # These are suggested defaults - users can override via UI
    KB_TYPE_RAG_DEFAULTS: Dict[str, Dict[str, bool]] = {
        "generic": {
            "hybrid": False,
            "rerank": False,
            "agentic": False
        },
        "code": {
            "hybrid": True,   # Code benefits from keyword + semantic search
            "rerank": True,   # Reranking helps with code relevance
            "agentic": False
        },
        "documentation": {
            "hybrid": True,   # Docs benefit from hybrid search
            "rerank": True,   # Reranking improves doc relevance
            "agentic": False
        },
        "agent-os": {
            "hybrid": True,   # Agent OS specs benefit from hybrid search
            "rerank": True,   # Reranking for spec relevance
            "agentic": True   # Agentic RAG for complex spec queries
        }
    }

    # Storage Configuration
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/workspace/data/uploads")

    @classmethod
    def get_ollama_url(cls) -> str:
        """Get the full Ollama API URL."""
        return cls.OLLAMA_HOST

    @classmethod
    def get_chroma_url(cls) -> str:
        """Get the full ChromaDB URL."""
        return f"http://{cls.CHROMA_HOST}:{cls.CHROMA_PORT}"

    @classmethod
    def get_mcp_url(cls) -> str:
        """Get the full MCP server URL."""
        return f"http://{cls.MCP_SERVER_HOST}:{cls.MCP_SERVER_PORT}"

    @classmethod
    def is_supported_file(cls, filename: str) -> bool:
        """Check if a file type is supported."""
        return any(filename.lower().endswith(ext) for ext in cls.SUPPORTED_FILE_TYPES)

    @classmethod
    def ensure_upload_dir(cls) -> Path:
        """Ensure upload directory exists and return Path object."""
        upload_path = Path(cls.UPLOAD_DIR)
        upload_path.mkdir(parents=True, exist_ok=True)
        return upload_path

