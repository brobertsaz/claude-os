"""
Configuration management for Claude OS.
Centralizes all application settings with environment variable support.
"""

import os
from pathlib import Path
from typing import Dict, List, Any

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ConfigMeta(type):
    """Metaclass to make Config class attributes immutable."""

    def __setattr__(cls, name: str, value: Any) -> None:
        """Prevent modification of configuration class attributes."""
        raise AttributeError(f"Configuration attribute '{name}' is read-only and cannot be modified")


class Config(metaclass=ConfigMeta):
    """Central configuration for Claude OS application."""

    # Ollama Configuration
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:latest")  # Upgraded to faster 8B model
    OLLAMA_EMBED_MODEL: str = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

    # Model Configuration
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama3.1")

    # Context and Retrieval Configuration
    MAX_CONTEXT_LENGTH: int = int(os.getenv("MAX_CONTEXT_LENGTH", "4096"))
    SIMILARITY_TOP_K: int = int(os.getenv("SIMILARITY_TOP_K", "20"))

    # Reranking Configuration
    ENABLE_RERANKER: bool = os.getenv("ENABLE_RERANKER", "false").lower() in ("true", "1", "yes")
    RERANK_MODEL: str = os.getenv("RERANK_MODEL", "cross-encoder/mmarco-mMiniLMv2-L12-H384")
    RERANK_TOP_K: int = int(os.getenv("RERANK_TOP_K", "10"))

    # SQLite Database Configuration
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
    def get_ollama_host(cls) -> str:
        """Get the Ollama host."""
        host = os.getenv("OLLAMA_HOST") or ""
        return host if host else cls.OLLAMA_HOST

    @classmethod
    def get_db_path(cls) -> str:
        """Get the SQLite database path."""
        db_path_env = os.getenv("SQLITE_DB_PATH") or ""
        if not db_path_env:
            # Return default path
            default_path = str(Path(__file__).parent.parent.parent / "data" / "claude-os.db")
            try:
                Path(default_path).parent.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError):
                pass  # Directory creation failed, but we'll return the path anyway
            return default_path
        # Return the exact path as provided, without trying to create directories
        return db_path_env

    @classmethod
    def get_embedding_model(cls) -> str:
        """Get the embedding model."""
        model = os.getenv("EMBEDDING_MODEL") or ""
        return model if model else cls.EMBEDDING_MODEL

    @classmethod
    def get_llm_model(cls) -> str:
        """Get the LLM model."""
        model = os.getenv("LLM_MODEL") or ""
        return model if model else cls.LLM_MODEL

    @classmethod
    def get_max_context_length(cls) -> int:
        """Get the max context length."""
        try:
            length_str = os.getenv("MAX_CONTEXT_LENGTH") or ""
            if not length_str:
                return cls.MAX_CONTEXT_LENGTH
            length = int(length_str)
            if length <= 0:
                raise ValueError("Invalid MAX_CONTEXT_LENGTH: must be greater than 0")
            return length
        except ValueError as e:
            raise ValueError("Invalid MAX_CONTEXT_LENGTH: must be a positive integer") from e

    @classmethod
    def get_similarity_top_k(cls) -> int:
        """Get the similarity top K."""
        try:
            top_k_str = os.getenv("SIMILARITY_TOP_K") or ""
            if not top_k_str:
                return cls.SIMILARITY_TOP_K
            top_k = int(top_k_str)
            if top_k <= 0:
                raise ValueError("Invalid SIMILARITY_TOP_K: must be greater than 0")
            return top_k
        except ValueError as e:
            raise ValueError("Invalid SIMILARITY_TOP_K: must be a positive integer") from e

    @classmethod
    def get_rerank_model(cls) -> str:
        """Get the rerank model."""
        model = os.getenv("RERANK_MODEL") or ""
        return model if model else cls.RERANK_MODEL

    @classmethod
    def get_rerank_top_k(cls) -> int:
        """Get the rerank top K."""
        try:
            top_k_str = os.getenv("RERANK_TOP_K") or ""
            if not top_k_str:
                return cls.RERANK_TOP_K
            top_k = int(top_k_str)
            if top_k <= 0:
                raise ValueError("Invalid RERANK_TOP_K: must be greater than 0")
            return top_k
        except ValueError as e:
            raise ValueError("Invalid RERANK_TOP_K: must be a positive integer") from e

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

    @classmethod
    def validate_config(cls) -> None:
        """
        Validate required configuration and environment variables.
        Raises ValueError if critical configuration is missing or invalid.
        """
        errors = []

        # Validate Ollama host is set
        if not cls.OLLAMA_HOST:
            errors.append("OLLAMA_HOST must be set")

        # Validate database path is valid
        try:
            db_path = Path(cls.get_db_path())
            if not db_path.parent.exists():
                try:
                    db_path.parent.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(f"Cannot create database directory: {e}")
        except Exception as e:
            errors.append(f"Invalid database path: {e}")

        # Validate MCP server port is valid
        if not (1 <= cls.MCP_SERVER_PORT <= 65535):
            errors.append(f"MCP_SERVER_PORT must be between 1-65535, got {cls.MCP_SERVER_PORT}")

        # Validate RAG configuration values
        if cls.CHUNK_SIZE <= 0:
            errors.append(f"CHUNK_SIZE must be positive, got {cls.CHUNK_SIZE}")
        if cls.CHUNK_OVERLAP < 0 or cls.CHUNK_OVERLAP >= cls.CHUNK_SIZE:
            errors.append(f"CHUNK_OVERLAP must be between 0 and CHUNK_SIZE, got {cls.CHUNK_OVERLAP}")
        if cls.TOP_K_RETRIEVAL <= 0:
            errors.append(f"TOP_K_RETRIEVAL must be positive, got {cls.TOP_K_RETRIEVAL}")

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValueError(error_msg)

