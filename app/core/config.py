"""
Configuration management for Claude OS.
Centralizes all application settings with environment variable support.
"""

import os
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Central configuration for Claude OS application."""

    # Ollama Configuration
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:latest")  # Upgraded to faster 8B model
    OLLAMA_EMBED_MODEL: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

    # SQLite Database Configuration (replaces PostgreSQL)
    # Always use absolute path to avoid issues when running from different directories
    _default_db_path = str(Path(__file__).parent.parent.parent / "data" / "claude-os.db")
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", _default_db_path)

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

    # RAG Configuration (Optimized for M4 Pro with 48GB RAM)
    CHUNK_SIZE: int = 512  # Reduced to prevent Ollama crashes
    CHUNK_OVERLAP: int = 128  # Proportional overlap
    TOP_K_RETRIEVAL: int = 20  # More chunks with plenty of RAM
    RERANK_TOP_N: int = 10  # More reranked results
    SIMILARITY_THRESHOLD: float = 0.25  # Lower threshold for broader matches

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
    def get_db_path(cls) -> str:
        """Get the SQLite database path."""
        db_path = Path(cls.SQLITE_DB_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return str(db_path)

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

