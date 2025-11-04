"""
MCP Server for Claude OS.
Exposes RAG functionality via Model Context Protocol with HTTP transport.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import requests
from typing import Optional
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.sqlite_manager import get_sqlite_manager
from app.core.config import Config
from app.core.kb_metadata import get_collection_stats, get_documents_metadata
from app.core.kb_types import KBType
from app.core.rag_engine import RAGEngine
from app.core.agent_os_ingestion import AgentOSIngestion
from app.core.agent_os_parser import AgentOSContentType
from app.core.hooks import get_project_hook
from app.core.file_watcher import get_global_watcher
from app.core.spec_manager import SpecManager
from functools import lru_cache
import time
from threading import Lock

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# RAGEngine cache with TTL - Optimized for M4 Pro with 48GB RAM
RAG_ENGINE_CACHE = {}
RAG_ENGINE_CACHE_LOCK = Lock()
RAG_ENGINE_CACHE_TTL = 3600  # 1 hour TTL with plenty of RAM

# Initialize FastAPI
app = FastAPI(title="Claude OS MCP Server")

# Add CORS middleware with security-conscious defaults
# In production, set ALLOWED_ORIGINS env var to your specific domains
allowed_origins_str = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:8051,http://127.0.0.1:5173,http://127.0.0.1:8051"
)
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # Restricted to specific origins for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

def get_cached_rag_engine(kb_name: str) -> RAGEngine:
    """
    Get or create a cached RAGEngine instance.
    Implements singleton pattern with TTL to avoid recreating engines for every query.

    Args:
        kb_name: Name of the knowledge base

    Returns:
        Cached or new RAGEngine instance
    """
    global RAG_ENGINE_CACHE

    with RAG_ENGINE_CACHE_LOCK:
        current_time = time.time()

        # Check if engine exists and is not expired
        if kb_name in RAG_ENGINE_CACHE:
            engine, timestamp = RAG_ENGINE_CACHE[kb_name]
            if current_time - timestamp < RAG_ENGINE_CACHE_TTL:
                logger.info(f"Using cached RAGEngine for {kb_name} (age: {current_time - timestamp:.1f}s)")
                return engine
            else:
                logger.info(f"RAGEngine cache expired for {kb_name}, creating new instance")
                del RAG_ENGINE_CACHE[kb_name]

        # Create new engine
        logger.info(f"Creating new RAGEngine for {kb_name}")
        start_time = time.time()
        engine = RAGEngine(kb_name)
        creation_time = time.time() - start_time
        logger.info(f"RAGEngine created for {kb_name} in {creation_time:.2f}s")

        # Cache the engine
        RAG_ENGINE_CACHE[kb_name] = (engine, current_time)

        # Clean up old entries (keep max 50 engines in cache with 48GB RAM)
        if len(RAG_ENGINE_CACHE) > 50:
            oldest_kb = min(RAG_ENGINE_CACHE.items(), key=lambda x: x[1][1])[0]
            del RAG_ENGINE_CACHE[oldest_kb]
            logger.info(f"Evicted oldest RAGEngine from cache: {oldest_kb}")

        return engine


# MCP Tools Registry
TOOLS = {
    "search_knowledge_base": {
        "description": "Search a knowledge base using RAG with optional advanced features",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kb_name": {"type": "string", "description": "Name of the knowledge base to search"},
                "query": {"type": "string", "description": "The search query"},
                "use_hybrid": {"type": "boolean", "description": "Enable hybrid search (vector + BM25)", "default": False},
                "use_rerank": {"type": "boolean", "description": "Enable reranking for better relevance", "default": False},
                "use_agentic": {"type": "boolean", "description": "Enable agentic RAG for complex queries", "default": False}
            },
            "required": ["kb_name", "query"]
        }
    },
    "list_knowledge_bases": {
        "description": "List all available knowledge bases with type metadata",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    "list_knowledge_bases_by_type": {
        "description": "List knowledge bases filtered by type (e.g., agent-os, code, documentation)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kb_type": {
                    "type": "string",
                    "description": "KB type to filter by",
                    "enum": ["generic", "code", "documentation", "agent-os"]
                }
            },
            "required": ["kb_type"]
        }
    },
    "create_knowledge_base": {
        "description": "Create a new knowledge base with specified type",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Name for the new knowledge base"},
                "kb_type": {
                    "type": "string",
                    "description": "Type of knowledge base",
                    "enum": ["generic", "code", "documentation", "agent-os"],
                    "default": "generic"
                },
                "description": {"type": "string", "description": "Optional description", "default": ""}
            },
            "required": ["name"]
        }
    },
    "get_kb_stats": {
        "description": "Get statistics for a knowledge base",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kb_name": {"type": "string", "description": "Name of the knowledge base"}
            },
            "required": ["kb_name"]
        }
    },
    "list_documents": {
        "description": "List all documents in a knowledge base",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kb_name": {"type": "string", "description": "Name of the knowledge base"}
            },
            "required": ["kb_name"]
        }
    },
    "ingest_agent_os_profile": {
        "description": "Ingest an Agent OS profile directory into a knowledge base",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kb_name": {"type": "string", "description": "Name of the Agent OS knowledge base"},
                "profile_path": {"type": "string", "description": "Path to the Agent OS profile directory"}
            },
            "required": ["kb_name", "profile_path"]
        }
    },
    "get_agent_os_stats": {
        "description": "Get statistics about Agent OS content in a knowledge base",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kb_name": {"type": "string", "description": "Name of the Agent OS knowledge base"}
            },
            "required": ["kb_name"]
        }
    },
    "get_standards": {
        "description": "Get coding standards from an Agent OS knowledge base",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kb_name": {"type": "string", "description": "Name of the Agent OS knowledge base"},
                "query": {"type": "string", "description": "Optional search query to filter standards", "default": ""}
            },
            "required": ["kb_name"]
        }
    },
    "get_workflows": {
        "description": "Get development workflows from an Agent OS knowledge base",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kb_name": {"type": "string", "description": "Name of the Agent OS knowledge base"},
                "query": {"type": "string", "description": "Optional search query to filter workflows", "default": ""}
            },
            "required": ["kb_name"]
        }
    },
    "get_specs": {
        "description": "Get feature specifications from an Agent OS knowledge base",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kb_name": {"type": "string", "description": "Name of the Agent OS knowledge base"},
                "query": {"type": "string", "description": "Optional search query to filter specs", "default": ""}
            },
            "required": ["kb_name"]
        }
    },
    "get_product_context": {
        "description": "Get product vision and context from an Agent OS knowledge base",
        "inputSchema": {
            "type": "object",
            "properties": {
                "kb_name": {"type": "string", "description": "Name of the Agent OS knowledge base"}
            },
            "required": ["kb_name"]
        }
    }
}


# Tool implementation functions
async def search_knowledge_base(kb_name: str, query: str, use_hybrid: bool = False,
                                use_rerank: bool = False, use_agentic: bool = False) -> dict:
    """Search a knowledge base using RAG with cached engine for performance."""
    try:
        start_time = time.time()

        db_manager = get_sqlite_manager()
        if not db_manager.collection_exists(kb_name):
            return {"error": f"Knowledge base '{kb_name}' not found", "answer": "", "sources": []}

        count = db_manager.get_collection_count(kb_name)
        if count == 0:
            return {"error": f"Knowledge base '{kb_name}' is empty", "answer": "", "sources": []}

        # Use cached RAGEngine instance instead of creating new one
        rag_engine = get_cached_rag_engine(kb_name)

        query_start = time.time()
        result = rag_engine.query(question=query, use_hybrid=use_hybrid,
                                 use_rerank=use_rerank, use_agentic=use_agentic)
        query_time = time.time() - query_start

        total_time = time.time() - start_time
        logger.info(f"Query executed on {kb_name}: {query[:50]}... (total: {total_time:.2f}s, query: {query_time:.2f}s)")

        # Add timing info to result for debugging
        result['_timing'] = {
            'total_time': total_time,
            'query_time': query_time
        }

        return result
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {"error": str(e), "answer": "", "sources": []}


async def list_knowledge_bases() -> List[Dict[str, any]]:
    """List all available knowledge bases with metadata."""
    try:
        db_manager = get_sqlite_manager()
        kbs = db_manager.list_collections()
        logger.info(f"Listed {len(kbs)} knowledge bases")
        return kbs
    except Exception as e:
        logger.error(f"Failed to list knowledge bases: {e}")
        return []


async def get_kb_stats(kb_name: str) -> dict:
    """Get statistics for a knowledge base."""
    try:
        stats = get_collection_stats(kb_name)
        logger.info(f"Retrieved stats for {kb_name}")
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats for {kb_name}: {e}")
        return {"error": str(e), "total_documents": 0, "total_chunks": 0, "last_updated": None}


async def list_documents(kb_name: str) -> List[dict]:
    """List all documents in a knowledge base."""
    try:
        docs = get_documents_metadata(kb_name)
        logger.info(f"Listed {len(docs)} documents in {kb_name}")
        return docs
    except Exception as e:
        logger.error(f"Failed to list documents in {kb_name}: {e}")
        return []


async def list_knowledge_bases_by_type(kb_type: str) -> List[Dict[str, any]]:
    """List knowledge bases filtered by type."""
    try:
        db_manager = get_sqlite_manager()
        kb_type_enum = KBType(kb_type)
        kbs = db_manager.list_collections_by_type(kb_type_enum)
        logger.info(f"Listed {len(kbs)} knowledge bases of type {kb_type}")
        return kbs
    except Exception as e:
        logger.error(f"Failed to list knowledge bases by type {kb_type}: {e}")
        return []


async def create_knowledge_base(name: str, kb_type: str = "generic", description: str = "") -> dict:
    """Create a new knowledge base."""
    try:
        db_manager = get_sqlite_manager()

        # Check if already exists
        if db_manager.collection_exists(name):
            return {
                "success": False,
                "error": f"Knowledge base '{name}' already exists"
            }

        # Create collection
        kb_type_enum = KBType(kb_type)
        success = db_manager.create_collection(
            name=name,
            kb_type=kb_type_enum,
            description=description
        )

        if success:
            logger.info(f"Created knowledge base: {name} (type: {kb_type})")
            return {
                "success": True,
                "name": name,
                "kb_type": kb_type,
                "description": description
            }
        else:
            return {
                "success": False,
                "error": "Failed to create knowledge base"
            }
    except Exception as e:
        logger.error(f"Failed to create knowledge base {name}: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def ingest_agent_os_profile(kb_name: str, profile_path: str) -> dict:
    """Ingest an Agent OS profile into a knowledge base."""
    try:
        db_manager = get_sqlite_manager()
        agent_os_ingestion = AgentOSIngestion(db_manager)

        stats = agent_os_ingestion.ingest_profile(
            kb_name=kb_name,
            profile_path=profile_path
        )

        logger.info(f"Ingested Agent OS profile from {profile_path} into {kb_name}")
        return stats
    except Exception as e:
        logger.error(f"Failed to ingest Agent OS profile: {e}")
        return {
            "success": False,
            "error": str(e),
            "documents_processed": 0
        }


async def get_agent_os_stats(kb_name: str) -> dict:
    """Get statistics about Agent OS content in a knowledge base."""
    try:
        db_manager = get_sqlite_manager()
        agent_os_ingestion = AgentOSIngestion(db_manager)

        stats = agent_os_ingestion.get_profile_stats(kb_name)
        logger.info(f"Retrieved Agent OS stats for {kb_name}")
        return stats
    except Exception as e:
        logger.error(f"Failed to get Agent OS stats for {kb_name}: {e}")
        return {
            "total_documents": 0,
            "documents_by_type": {},
            "error": str(e)
        }


async def get_standards(kb_name: str, query: str = "") -> List[dict]:
    """Get coding standards from an Agent OS knowledge base."""
    try:
        db_manager = get_sqlite_manager()
        agent_os_ingestion = AgentOSIngestion(db_manager)

        results = agent_os_ingestion.search_by_type(
            kb_name=kb_name,
            content_type=AgentOSContentType.STANDARD,
            query=query if query else None,
            limit=20
        )

        logger.info(f"Retrieved {len(results)} standards from {kb_name}")
        return results
    except Exception as e:
        logger.error(f"Failed to get standards from {kb_name}: {e}")
        return []


async def get_workflows(kb_name: str, query: str = "") -> List[dict]:
    """Get development workflows from an Agent OS knowledge base."""
    try:
        db_manager = get_sqlite_manager()
        agent_os_ingestion = AgentOSIngestion(db_manager)

        results = agent_os_ingestion.search_by_type(
            kb_name=kb_name,
            content_type=AgentOSContentType.WORKFLOW,
            query=query if query else None,
            limit=20
        )

        logger.info(f"Retrieved {len(results)} workflows from {kb_name}")
        return results
    except Exception as e:
        logger.error(f"Failed to get workflows from {kb_name}: {e}")
        return []


async def get_specs(kb_name: str, query: str = "") -> List[dict]:
    """Get feature specifications from an Agent OS knowledge base."""
    try:
        db_manager = get_sqlite_manager()
        agent_os_ingestion = AgentOSIngestion(db_manager)

        results = agent_os_ingestion.search_by_type(
            kb_name=kb_name,
            content_type=AgentOSContentType.SPEC,
            query=query if query else None,
            limit=20
        )

        logger.info(f"Retrieved {len(results)} specs from {kb_name}")
        return results
    except Exception as e:
        logger.error(f"Failed to get specs from {kb_name}: {e}")
        return []


async def get_product_context(kb_name: str) -> List[dict]:
    """Get product vision and context from an Agent OS knowledge base."""
    try:
        db_manager = get_sqlite_manager()
        agent_os_ingestion = AgentOSIngestion(db_manager)

        results = agent_os_ingestion.search_by_type(
            kb_name=kb_name,
            content_type=AgentOSContentType.PRODUCT,
            query=None,
            limit=20
        )

        logger.info(f"Retrieved {len(results)} product context documents from {kb_name}")
        return results
    except Exception as e:
        logger.error(f"Failed to get product context from {kb_name}: {e}")
        return []


# Pydantic models for REST API
class CreateKBRequest(BaseModel):
    name: str
    kb_type: str = "generic"
    description: str = ""

class ChatRequest(BaseModel):
    query: str
    use_hybrid: bool = False
    use_rerank: bool = False
    use_agentic: bool = False


# REST API Endpoints for UI
@app.get("/api/kb")
async def api_list_knowledge_bases():
    """REST API: List all knowledge bases."""
    kbs = await list_knowledge_bases()
    return {"knowledge_bases": kbs}


@app.post("/api/kb")
async def api_create_knowledge_base(request: CreateKBRequest):
    """REST API: Create a new knowledge base."""
    result = await create_knowledge_base(
        name=request.name,
        kb_type=request.kb_type,
        description=request.description
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


@app.delete("/api/kb/{kb_name}")
async def api_delete_knowledge_base(kb_name: str):
    """REST API: Delete a knowledge base."""
    try:
        db_manager = get_sqlite_manager()
        if not db_manager.collection_exists(kb_name):
            raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_name}' not found")

        success = db_manager.delete_collection(kb_name)
        if success:
            return {"success": True, "message": f"Knowledge base '{kb_name}' deleted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete knowledge base")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete KB {kb_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/kb/{kb_name}/stats")
async def api_get_kb_stats(kb_name: str):
    """REST API: Get knowledge base statistics."""
    stats = await get_kb_stats(kb_name)
    if "error" in stats:
        raise HTTPException(status_code=404, detail=stats["error"])
    return stats


@app.get("/api/kb/{kb_name}/documents")
async def api_list_documents(kb_name: str):
    """REST API: List documents in a knowledge base."""
    docs = await list_documents(kb_name)
    return {"documents": docs}


@app.post("/api/kb/{kb_name}/chat")
@limiter.limit("20/minute")  # Rate limit: 20 queries per minute per IP
async def api_chat(request: Request, kb_name: str, chat_request: ChatRequest):
    """REST API: Chat with a knowledge base."""
    result = await search_knowledge_base(
        kb_name=kb_name,
        query=chat_request.query,
        use_hybrid=chat_request.use_hybrid,
        use_rerank=chat_request.use_rerank,
        use_agentic=chat_request.use_agentic
    )
    if "error" in result and result["error"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@app.post("/api/kb/{kb_name}/upload")
async def api_upload_document(kb_name: str, file: UploadFile = File(...)):
    """REST API: Upload a single document to a knowledge base."""
    import tempfile
    import os
    from app.core.ingestion import ingest_file

    # Validate KB exists
    db_manager = get_sqlite_manager()
    if not db_manager.collection_exists(kb_name):
        raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_name}' not found")

    # Save uploaded file to temp location
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        # Ingest the file
        result = ingest_file(tmp_path, kb_name, file.filename)

        # Clean up temp file
        os.unlink(tmp_path)

        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result.get("error", "Upload failed"))

        return {
            "success": True,
            "filename": result["filename"],
            "chunks": result["chunks"],
            "file_type": result["file_type"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/kb/{kb_name}/import")
async def api_import_directory(kb_name: str, directory_path: str):
    """REST API: Import all files from a directory into a knowledge base."""
    from app.core.ingestion import ingest_directory

    # Validate KB exists
    db_manager = get_sqlite_manager()
    if not db_manager.collection_exists(kb_name):
        raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_name}' not found")

    # Validate directory exists
    if not Path(directory_path).exists():
        raise HTTPException(status_code=404, detail=f"Directory not found: {directory_path}")

    try:
        results = ingest_directory(directory_path, kb_name)

        # Count successes and failures
        successes = [r for r in results if r.get("status") == "success"]
        failures = [r for r in results if r.get("status") == "error"]

        return {
            "success": True,
            "total_files": len(results),
            "successful": len(successes),
            "failed": len(failures),
            "results": results
        }
    except Exception as e:
        logger.error(f"Directory import failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/kb/{kb_name}/documents/{filename}")
async def api_delete_document(kb_name: str, filename: str):
    """REST API: Delete a document from a knowledge base by filename."""
    db_manager = get_sqlite_manager()

    # Validate KB exists
    if not db_manager.collection_exists(kb_name):
        raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_name}' not found")

    try:
        # Get the collection ID
        conn = db_manager.get_connection()
        try:
            with conn.cursor() as cur:
                # Get collection ID
                cur.execute(
                    "SELECT id FROM knowledge_bases WHERE name = ?",
                    (kb_name,)
                )
                result = cur.fetchone()
                if not result:
                    raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_name}' not found")

                collection_id = result[0]

                # Delete documents with this filename
                cur.execute(
                    """
                    DELETE FROM documents
                    WHERE kb_id = ? AND json_extract(metadata, '$.filename') = ?
                    RETURNING id
                    """,
                    (collection_id, filename)
                )
                deleted_count = len(cur.fetchall())
                conn.commit()

                if deleted_count == 0:
                    raise HTTPException(status_code=404, detail=f"No documents found with filename '{filename}'")

                logger.info(f"Deleted {deleted_count} document(s) with filename '{filename}' from KB '{kb_name}'")
                return {
                    "success": True,
                    "message": f"Deleted {deleted_count} document(s)",
                    "filename": filename,
                    "kb_name": kb_name
                }
        finally:
            db_manager.return_connection(conn)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HYBRID INDEXING ENDPOINTS (NEW - Tree-sitter structural indexing)
# ============================================================================

class StructuralIndexRequest(BaseModel):
    """Request model for structural indexing."""
    project_path: str
    cache_path: Optional[str] = None
    token_budget: int = 1024


class SemanticIndexRequest(BaseModel):
    """Request model for semantic indexing."""
    project_path: str
    selective: bool = True  # Only index top 20% + docs
    personalization: Optional[Dict[str, float]] = None


@app.post("/api/kb/{kb_name}/index-structural")
async def api_index_structural(kb_name: str, request: StructuralIndexRequest):
    """
    REST API: Fast structural indexing using tree-sitter.
    Phase 1 of hybrid indexing - completes in ~30 seconds for 10k files.
    """
    from app.core.tree_sitter_indexer import TreeSitterIndexer
    import json

    # Validate KB exists
    db_manager = get_sqlite_manager()
    if not db_manager.collection_exists(kb_name):
        raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_name}' not found")

    # Validate project path
    if not Path(request.project_path).exists():
        raise HTTPException(status_code=404, detail=f"Project path not found: {request.project_path}")

    try:
        logger.info(f"Starting structural indexing for {kb_name} at {request.project_path}")
        start_time = time.time()

        # Create indexer with cache
        cache_path = request.cache_path or str(Path(request.project_path) / ".claude-os" / "tree_sitter_cache.db")
        indexer = TreeSitterIndexer(cache_path)

        # Index the directory
        repo_map = indexer.index_directory(
            request.project_path,
            personalization=None,
            token_budget=request.token_budget
        )

        # Store repo map as JSON document directly (NO EMBEDDING!)
        repo_map_json = json.dumps(repo_map.to_dict(), indent=2)

        # Store directly in database without embedding - use raw SQL
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        # Get KB ID
        cursor.execute("SELECT id FROM knowledge_bases WHERE name = ?", (kb_name,))
        kb_result = cursor.fetchone()
        if not kb_result:
            raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_name}' not found")
        kb_id = kb_result['id']

        # Insert or replace the repo map document
        metadata_json = json.dumps({
            "filename": "repo_map.json",
            "type": "structural_index",
            "total_files": repo_map.total_files,
            "total_symbols": repo_map.total_symbols,
            "indexed_at": time.time(),
            "kb_id": str(kb_id)
        })

        # Check if document already exists
        cursor.execute(
            "SELECT id FROM documents WHERE kb_id = ? AND doc_id = ?",
            (kb_id, "repo_map")
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing
            cursor.execute(
                """UPDATE documents
                   SET content = ?, metadata = ?
                   WHERE kb_id = ? AND doc_id = ?""",
                (repo_map_json, metadata_json, kb_id, "repo_map")
            )
        else:
            # Insert new
            cursor.execute(
                """INSERT INTO documents
                   (kb_id, doc_id, content, metadata)
                   VALUES (?, ?, ?, ?)""",
                (kb_id, "repo_map", repo_map_json, metadata_json)
            )
        conn.commit()

        # Close indexer
        indexer.close()

        elapsed = time.time() - start_time
        logger.info(f"Structural indexing complete for {kb_name} in {elapsed:.1f}s")

        return {
            "success": True,
            "kb_name": kb_name,
            "total_files": repo_map.total_files,
            "total_symbols": repo_map.total_symbols,
            "time_taken_seconds": elapsed,
            "repo_map_preview": indexer.generate_repo_map(repo_map.tags[:50], token_budget=512),
            "message": f"Structural index created: {repo_map.total_symbols} symbols in {repo_map.total_files} files"
        }

    except Exception as e:
        logger.error(f"Structural indexing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/kb/{kb_name}/index-semantic")
async def api_index_semantic(kb_name: str, request: SemanticIndexRequest):
    """
    REST API: Semantic indexing with selective embedding.
    Phase 2 of hybrid indexing - optional, runs in background.
    """
    from app.core.tree_sitter_indexer import TreeSitterIndexer
    from app.core.ingestion import ingest_directory
    import json

    # Validate KB exists
    db_manager = get_sqlite_manager()
    if not db_manager.collection_exists(kb_name):
        raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_name}' not found")

    # Validate project path
    if not Path(request.project_path).exists():
        raise HTTPException(status_code=404, detail=f"Project path not found: {request.project_path}")

    try:
        logger.info(f"Starting semantic indexing for {kb_name} at {request.project_path}")
        start_time = time.time()

        if request.selective:
            # Get structural index first
            structure_kb = f"{kb_name.split('-')[0]}-code_structure"

            # Load repo map if exists
            cache_path = str(Path(request.project_path) / ".claude-os" / "tree_sitter_cache.db")
            indexer = TreeSitterIndexer(cache_path)
            repo_map = indexer.index_directory(request.project_path, request.personalization)
            indexer.close()

            # Select top 20% files by importance
            top_20_percent = int(len(repo_map.tags) * 0.2)
            important_tags = repo_map.tags[:top_20_percent]

            # Get unique files
            important_files = list(set(tag.file for tag in important_tags))

            # Add all documentation files
            docs_patterns = ["*.md", "*.txt", "*.rst"]
            doc_files = []
            for pattern in docs_patterns:
                doc_files.extend(Path(request.project_path).rglob(pattern))

            all_files = important_files + [str(f.relative_to(request.project_path)) for f in doc_files]

            logger.info(f"Selective indexing: {len(all_files)} files (top 20% + docs)")

            # Ingest selected files only
            from app.core.ingestion import ingest_file
            results = []

            for file_rel_path in all_files:
                file_path = Path(request.project_path) / file_rel_path
                if file_path.exists() and file_path.is_file():
                    try:
                        result = ingest_file(str(file_path), kb_name, str(file_rel_path))
                        results.append({"status": "success", "file": str(file_rel_path)})
                        logger.debug(f"Ingested: {file_rel_path}")
                    except Exception as e:
                        logger.warning(f"Failed to ingest {file_rel_path}: {e}")
                        results.append({"status": "error", "file": str(file_rel_path), "error": str(e)})

            successes = [r for r in results if r.get("status") == "success"]
            elapsed = time.time() - start_time

            logger.info(f"Selective semantic indexing complete for {kb_name} in {elapsed:.1f}s")

            return {
                "success": True,
                "kb_name": kb_name,
                "mode": "selective",
                "files_selected": len(all_files),
                "files_indexed": len(successes),
                "time_taken_seconds": elapsed,
                "message": f"Selective semantic indexing complete: {len(successes)}/{len(all_files)} files indexed"
            }
        else:
            # Full indexing (all files)
            results = ingest_directory(request.project_path, kb_name)
            successes = [r for r in results if r.get("status") == "success"]

            elapsed = time.time() - start_time
            logger.info(f"Full semantic indexing complete for {kb_name} in {elapsed:.1f}s")

            return {
                "success": True,
                "kb_name": kb_name,
                "mode": "full",
                "total_files": len(results),
                "successful": len(successes),
                "time_taken_seconds": elapsed,
                "message": f"Full semantic indexing complete: {len(successes)} files indexed"
            }

    except Exception as e:
        logger.error(f"Semantic indexing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/kb/{kb_name}/repo-map")
async def api_get_repo_map(
    kb_name: str,
    token_budget: int = 1024,
    project_path: Optional[str] = None,
    personalization: Optional[str] = None  # JSON string
):
    """
    REST API: Get compact repo map for Claude's prompt context.
    Returns the most important symbols fitting within token budget.
    """
    from app.core.tree_sitter_indexer import TreeSitterIndexer
    import json

    # Validate KB exists
    db_manager = get_sqlite_manager()
    if not db_manager.collection_exists(kb_name):
        raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_name}' not found")

    try:
        # Try to load cached repo map from KB first
        # Query for repo_map.json document
        results = db_manager.query_documents(kb_name, query_embedding=None, n_results=1)

        if results and "documents" in results and len(results["documents"]) > 0:
            # Check if first result is repo_map
            metadata = results["metadatas"][0] if "metadatas" in results else []
            if metadata and metadata[0].get("filename") == "repo_map.json":
                # Load from KB
                from app.core.tree_sitter_indexer import RepoMap
                repo_map_data = json.loads(results["documents"][0][0])
                repo_map = RepoMap.from_dict(repo_map_data)

                # Apply personalization if provided
                if personalization:
                    personalization_dict = json.loads(personalization)
                    indexer = TreeSitterIndexer()
                    ranked_tags = indexer.rank_symbols(repo_map.tags, repo_map.dependency_graph, personalization_dict)
                    repo_map.tags = ranked_tags
                    indexer.close()

                # Generate compact map
                indexer = TreeSitterIndexer()
                compact_map = indexer.generate_repo_map(repo_map.tags, token_budget)
                indexer.close()

                return {
                    "success": True,
                    "kb_name": kb_name,
                    "repo_map": compact_map,
                    "token_count": len(compact_map) // 4,  # Rough estimate
                    "total_symbols": repo_map.total_symbols,
                    "total_files": repo_map.total_files,
                    "source": "cached"
                }

        # If no cached repo map, generate on-the-fly (requires project_path)
        if not project_path:
            raise HTTPException(
                status_code=400,
                detail="No cached repo map found. Please provide project_path or run /index-structural first"
            )

        if not Path(project_path).exists():
            raise HTTPException(status_code=404, detail=f"Project path not found: {project_path}")

        # Generate repo map
        cache_path = str(Path(project_path) / ".claude-os" / "tree_sitter_cache.db")
        indexer = TreeSitterIndexer(cache_path)

        personalization_dict = json.loads(personalization) if personalization else None
        repo_map = indexer.index_directory(project_path, personalization_dict, token_budget)
        compact_map = indexer.generate_repo_map(repo_map.tags, token_budget)

        indexer.close()

        return {
            "success": True,
            "kb_name": kb_name,
            "repo_map": compact_map,
            "token_count": len(compact_map) // 4,
            "total_symbols": repo_map.total_symbols,
            "total_files": repo_map.total_files,
            "source": "generated"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get repo map: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROJECT MANAGEMENT ENDPOINTS (NEW - for Claude OS project integration)
# ============================================================================

class ProjectRequest(BaseModel):
    """Request model for creating a project."""
    name: str
    path: str
    description: Optional[str] = ""


class ProjectKBFolderRequest(BaseModel):
    """Request model for setting KB folder."""
    mcp_type: str  # knowledge_docs, project_profile, project_index, project_memories
    folder_path: str
    auto_sync: bool = False


class ProjectDocumentIngestRequest(BaseModel):
    """Request model for ingesting a document into project MCP."""
    mcp_type: str  # knowledge_docs, project_profile, project_index, project_memories
    filename: str
    content: str


@app.get("/api/projects")
async def api_list_projects():
    """REST API: List all projects."""
    try:
        db_manager = get_sqlite_manager()
        projects = db_manager.list_projects()
        return {"projects": projects}
    except Exception as e:
        logger.error(f"Failed to list projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects")
async def api_create_project(request: ProjectRequest):
    """REST API: Create a new project with 4 required MCPs."""
    try:
        db_manager = get_sqlite_manager()

        # Create project
        project = db_manager.create_project(
            name=request.name,
            path=request.path,
            description=request.description
        )
        logger.info(f"Created project: {request.name}")

        # Create 4 required MCPs
        mcp_types = ["knowledge_docs", "project_profile", "project_index", "project_memories"]
        mcps_created = []

        for i, mcp_type in enumerate(mcp_types):
            kb_name = f"{request.name}-{mcp_type}"

            # Create KB for this MCP type
            kb = db_manager.create_collection(
                name=kb_name,
                kb_type=KBType.GENERIC,
                description=f"{mcp_type.replace('_', ' ').title()} for {request.name}"
            )

            # Link KB to project
            db_manager.assign_kb_to_project(
                project["id"],
                kb["id"],
                mcp_type
            )

            mcps_created.append({
                "mcp_type": mcp_type,
                "kb_name": kb_name,
                "kb_id": kb["id"]
            })
            logger.info(f"Created MCP {mcp_type} KB: {kb_name}")

        return {
            "project": project,
            "mcps": mcps_created,
            "message": f"Project '{request.name}' created with 4 required MCPs"
        }

    except ValueError as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}")
async def api_get_project(project_id: int):
    """REST API: Get project details with MCP assignments."""
    try:
        db_manager = get_sqlite_manager()
        project = db_manager.get_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        # Get MCP KBs for this project
        project_kbs = db_manager.get_project_kbs(project_id)
        project_folders = db_manager.get_kb_folders(project_id)

        return {
            "project": project,
            "mcps": project_kbs,
            "folders": project_folders
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}/mcps")
async def api_get_project_mcps(project_id: int):
    """REST API: Get detailed MCP info for a project (KB names and IDs)."""
    try:
        db_manager = get_sqlite_manager()
        project = db_manager.get_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        # Get detailed MCP info with KB names (returns dict)
        mcps_dict = db_manager.get_project_mcps_detailed(project_id)

        # Convert to list format for frontend
        mcps_list = []
        for mcp_type, mcp_data in mcps_dict.items():
            # Get KB slug
            kb = db_manager.get_collection_by_id(mcp_data['kb_id'])
            mcps_list.append({
                "mcp_type": mcp_type,
                "kb_id": mcp_data['kb_id'],
                "kb_name": mcp_data['kb_name'],
                "kb_slug": kb.get('slug', '') if kb else ''
            })

        return {
            "project_id": project_id,
            "project_name": project['name'],
            "project_path": project['path'],
            "mcps": mcps_list
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project MCPs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/{project_id}/folders")
async def api_set_kb_folder(project_id: int, request: ProjectKBFolderRequest):
    """REST API: Set the folder path for a project's MCP KB."""
    try:
        db_manager = get_sqlite_manager()

        # Verify project exists
        project = db_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        # Verify MCP type is valid
        valid_mcp_types = ["knowledge_docs", "project_profile", "project_index", "project_memories", "code_structure"]
        if request.mcp_type not in valid_mcp_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid MCP type. Must be one of: {', '.join(valid_mcp_types)}"
            )

        # Verify folder exists
        from pathlib import Path
        folder_path = Path(request.folder_path)
        if not folder_path.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Folder does not exist: {request.folder_path}"
            )

        # Get the KB name for this MCP type
        mcps = db_manager.get_project_mcps_detailed(project_id)
        if request.mcp_type not in mcps:
            raise HTTPException(
                status_code=404,
                detail=f"MCP type {request.mcp_type} not found for project {project_id}"
            )

        kb_name = mcps[request.mcp_type]['kb_name']

        # Set folder for this MCP type
        result = db_manager.set_kb_folder(
            project_id,
            request.mcp_type,
            request.folder_path,
            request.auto_sync
        )

        logger.info(f"Set {request.mcp_type} folder for project {project_id}: {request.folder_path} (auto_sync={request.auto_sync})")

        # Automatically sync the folder contents
        from app.core.ingestion import ingest_directory
        sync_results = None
        try:
            logger.info(f"Auto-syncing folder {request.folder_path} to {kb_name}...")
            results = ingest_directory(request.folder_path, kb_name)
            successes = [r for r in results if r.get("status") == "success"]
            failures = [r for r in results if r.get("status") == "error"]
            sync_results = {
                "total_files": len(results),
                "successful": len(successes),
                "failed": len(failures)
            }
            logger.info(f"Folder sync complete: {len(successes)}/{len(results)} files uploaded successfully")
        except Exception as e:
            logger.error(f"Failed to sync folder: {e}")
            # Don't fail the whole request if sync fails
            sync_results = {
                "error": str(e)
            }

        return {
            "project_id": project_id,
            "mcp_type": request.mcp_type,
            "folder_path": request.folder_path,
            "auto_sync": request.auto_sync,
            "sync_results": sync_results,
            "message": f"Folder configured for {request.mcp_type}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set KB folder: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}/folders")
async def api_get_kb_folders(project_id: int):
    """REST API: Get folder configurations for a project's MCPs."""
    try:
        db_manager = get_sqlite_manager()

        # Verify project exists
        project = db_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        # Get folder configurations
        folders = db_manager.get_kb_folders(project_id)

        return {
            "project_id": project_id,
            "folders": folders
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get KB folders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/{project_id}/ingest-document")
async def api_ingest_document(project_id: int, request: ProjectDocumentIngestRequest):
    """REST API: Ingest a document directly into a project's MCP KB."""
    try:
        db_manager = get_sqlite_manager()

        # Verify project exists
        project = db_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        # Verify MCP type is valid
        valid_mcp_types = ["knowledge_docs", "project_profile", "project_index", "project_memories", "code_structure"]
        if request.mcp_type not in valid_mcp_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid MCP type. Must be one of: {', '.join(valid_mcp_types)}"
            )

        # Get the KB name for this MCP type
        mcps = db_manager.get_project_mcps_detailed(project_id)
        if request.mcp_type not in mcps:
            raise HTTPException(
                status_code=404,
                detail=f"MCP type {request.mcp_type} not found for project {project_id}"
            )

        kb_name = mcps[request.mcp_type]['kb_name']

        # Ingest the document into the KB
        from app.core.ingestion import ingest_documents
        try:
            logger.info(f"Ingesting document {request.filename} to {kb_name} for project {project_id}...")
            result = ingest_documents(
                collection_name=kb_name,
                documents=[request.content],
                metadatas=[{
                    "filename": request.filename,
                    "type": "text/markdown",
                    "project_id": project_id
                }]
            )
            logger.info(f"Document {request.filename} ingested successfully")

            return {
                "project_id": project_id,
                "mcp_type": request.mcp_type,
                "filename": request.filename,
                "kb_name": kb_name,
                "status": "success",
                "message": f"Document {request.filename} ingested into {request.mcp_type}"
            }
        except Exception as e:
            logger.error(f"Failed to ingest document {request.filename}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to ingest document: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to ingest document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/projects/{project_id}")
async def api_delete_project(project_id: int):
    """REST API: Delete a project and its associated KBs."""
    try:
        db_manager = get_sqlite_manager()

        # Get project to verify it exists
        project = db_manager.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

        # Get all KBs for this project
        project_kbs = db_manager.get_project_kbs(project_id)

        # Delete all KBs associated with this project
        for mcp_type, kb_id in project_kbs.items():
            # Get KB name to delete
            collections = db_manager.list_collections()
            for kb in collections:
                if kb.get("id") == kb_id:
                    db_manager.delete_collection(kb["name"])
                    logger.info(f"Deleted KB {kb['name']} for project {project_id}")
                    break

        # Delete project (cascades to project_mcps and project_kb_folders)
        # Note: SQLite doesn't have CASCADE by default, so we manually delete
        conn = db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM project_kb_folders WHERE project_id = ?", (project_id,))
            cursor.execute("DELETE FROM project_mcps WHERE project_id = ?", (project_id,))
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
        finally:
            conn.close()

        logger.info(f"Deleted project {project_id}")

        return {
            "message": f"Project {project_id} and all associated KBs deleted",
            "project_id": project_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PROJECT HOOKS ENDPOINTS (for KB folder synchronization)
# ============================================================================

class HookRequest(BaseModel):
    """Request model for configuring hooks."""
    folder_path: str
    file_patterns: Optional[List[str]] = None


class SyncRequest(BaseModel):
    """Request model for syncing KB folders."""
    mcp_type: Optional[str] = None  # If None, sync all


@app.post("/api/projects/{project_id}/hooks/{mcp_type}/enable")
async def api_enable_hook(project_id: int, mcp_type: str, request: HookRequest):
    """Enable automatic KB synchronization for a folder."""
    try:
        hook = get_project_hook(project_id)

        # Enable hook
        hook_config = hook.enable_kb_autosync(
            mcp_type,
            request.folder_path,
            request.file_patterns
        )

        return {
            "project_id": project_id,
            "mcp_type": mcp_type,
            "hook": hook_config,
            "message": f"Hook enabled for {mcp_type}"
        }

    except Exception as e:
        logger.error(f"Failed to enable hook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/{project_id}/hooks/{mcp_type}/disable")
async def api_disable_hook(project_id: int, mcp_type: str):
    """Disable automatic KB synchronization."""
    try:
        hook = get_project_hook(project_id)
        hook.disable_kb_autosync(mcp_type)

        return {
            "project_id": project_id,
            "mcp_type": mcp_type,
            "message": f"Hook disabled for {mcp_type}"
        }

    except Exception as e:
        logger.error(f"Failed to disable hook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/{project_id}/hooks/sync")
async def api_sync_hooks(project_id: int, request: Optional[SyncRequest] = None):
    """Manually sync KB folders for a project."""
    try:
        hook = get_project_hook(project_id)

        if request and request.mcp_type:
            # Sync specific MCP type
            result = hook.sync_kb_folder(request.mcp_type)
            return {
                "project_id": project_id,
                "sync_result": result
            }
        else:
            # Sync all folders
            results = hook.sync_all_folders()
            return {
                "project_id": project_id,
                "sync_results": results
            }

    except Exception as e:
        logger.error(f"Failed to sync hooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}/hooks")
async def api_get_hooks_status(project_id: int):
    """Get hook status for a project."""
    try:
        hook = get_project_hook(project_id)
        status = hook.get_hook_status()

        return {
            "project_id": project_id,
            "status": status
        }

    except Exception as e:
        logger.error(f"Failed to get hooks status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FILE WATCHER ENDPOINTS (for automatic folder synchronization)
# ============================================================================

@app.post("/api/watcher/start/{project_id}")
async def api_start_watcher(project_id: int):
    """Start file watcher for a project."""
    try:
        watcher = get_global_watcher()
        watcher.start_project(project_id)

        return {
            "project_id": project_id,
            "message": "File watcher started",
            "status": watcher.get_status()
        }

    except Exception as e:
        logger.error(f"Failed to start watcher: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/watcher/stop/{project_id}")
async def api_stop_watcher(project_id: int):
    """Stop file watcher for a project."""
    try:
        watcher = get_global_watcher()
        watcher.stop_project(project_id)

        return {
            "project_id": project_id,
            "message": "File watcher stopped",
            "status": watcher.get_status()
        }

    except Exception as e:
        logger.error(f"Failed to stop watcher: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/watcher/restart/{project_id}")
async def api_restart_watcher(project_id: int):
    """Restart file watcher for a project."""
    try:
        watcher = get_global_watcher()
        watcher.restart_project(project_id)

        return {
            "project_id": project_id,
            "message": "File watcher restarted",
            "status": watcher.get_status()
        }

    except Exception as e:
        logger.error(f"Failed to restart watcher: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/watcher/status")
async def api_watcher_status():
    """Get file watcher status."""
    try:
        watcher = get_global_watcher()
        return {"status": watcher.get_status()}
    except Exception as e:
        logger.error(f"Failed to get watcher status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SPEC TRACKING ENDPOINTS (for agent-os integration and Kanban board)
# ============================================================================

@app.get("/api/projects/{project_id}/specs")
async def api_get_project_specs(project_id: int):
    """Get all specs for a project."""
    try:
        manager = SpecManager()
        specs = manager.get_project_specs(project_id)
        return {"project_id": project_id, "specs": specs}
    except Exception as e:
        logger.error(f"Failed to get specs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/specs/{spec_id}/tasks")
async def api_get_spec_tasks(spec_id: int):
    """Get all tasks for a spec."""
    try:
        manager = SpecManager()
        tasks = manager.get_spec_tasks(spec_id)
        return {"spec_id": spec_id, "tasks": tasks}
    except Exception as e:
        logger.error(f"Failed to get tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class TaskStatusUpdate(BaseModel):
    status: str
    actual_minutes: Optional[int] = None


@app.patch("/api/tasks/{task_id}/status")
async def api_update_task_status(task_id: int, update: TaskStatusUpdate):
    """Update a task's status."""
    try:
        manager = SpecManager()
        result = manager.update_task_status(
            task_id,
            update.status,
            update.actual_minutes
        )

        if not result['success']:
            raise HTTPException(status_code=404, detail=result.get('error', 'Task not found'))

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update task status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/projects/{project_id}/specs/sync")
async def api_sync_project_specs(project_id: int):
    """Sync specs from project's agent-os folder."""
    try:
        # Get project path
        manager_db = get_sqlite_manager()
        project = manager_db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Sync specs
        spec_manager = SpecManager()
        result = spec_manager.sync_project_specs(project_id, project['path'])

        return {
            "project_id": project_id,
            "message": "Specs synced successfully",
            **result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync specs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/projects/{project_id}/kanban")
async def api_get_kanban_view(project_id: int, include_archived: bool = False):
    """Get Kanban board view for a project."""
    try:
        manager = SpecManager()
        # Get specs with archive filter
        specs = manager.get_project_specs(project_id, include_archived)

        # Build kanban manually with filtered specs
        kanban = {
            "project_id": project_id,
            "specs": [],
            "summary": {
                "total_specs": len(specs),
                "total_tasks": 0,
                "completed_tasks": 0,
                "archived_count": sum(1 for s in specs if s.get('archived', False))
            }
        }

        for spec in specs:
            tasks = manager.get_spec_tasks(spec['id'])

            # Group tasks by status
            task_groups = {
                "todo": [t for t in tasks if t['status'] == 'todo'],
                "in_progress": [t for t in tasks if t['status'] == 'in_progress'],
                "done": [t for t in tasks if t['status'] == 'done'],
                "blocked": [t for t in tasks if t['status'] == 'blocked']
            }

            kanban['specs'].append({
                **spec,
                "tasks": task_groups,
                "task_count_by_status": {
                    "todo": len(task_groups['todo']),
                    "in_progress": len(task_groups['in_progress']),
                    "done": len(task_groups['done']),
                    "blocked": len(task_groups['blocked'])
                }
            })

            kanban['summary']['total_tasks'] += spec['total_tasks']
            kanban['summary']['completed_tasks'] += spec['completed_tasks']

        return kanban
    except Exception as e:
        logger.error(f"Failed to get kanban view: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/specs/{spec_id}/archive")
async def api_archive_spec(spec_id: int):
    """Archive a spec."""
    try:
        manager = SpecManager()
        result = manager.archive_spec(spec_id)
        return result
    except Exception as e:
        logger.error(f"Failed to archive spec: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/specs/{spec_id}/unarchive")
async def api_unarchive_spec(spec_id: int):
    """Unarchive a spec."""
    try:
        manager = SpecManager()
        result = manager.unarchive_spec(spec_id)
        return result
    except Exception as e:
        logger.error(f"Failed to unarchive spec: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# OLLAMA ENDPOINTS
# ============================================================================

@app.get("/api/ollama/models")
async def api_list_ollama_models():
    """REST API: List available Ollama models."""
    try:
        response = requests.get(f"{Config.OLLAMA_HOST}/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return {"models": models}
        else:
            raise HTTPException(status_code=503, detail="Ollama service unavailable")
    except Exception as e:
        logger.error(f"Failed to list Ollama models: {e}")
        raise HTTPException(status_code=503, detail=str(e))


# ============================================================================
# SERVICE DASHBOARD ENDPOINTS (NEW - Real-time service monitoring)
# ============================================================================

import subprocess
import shutil

class ServiceControlRequest(BaseModel):
    """Request model for service control."""
    action: str  # start, stop, restart


def check_process_running(process_name: str) -> dict:
    """
    Check if a process is running by name.

    Returns:
        dict with status, pid, memory, cpu
    """
    try:
        # Use pgrep to find process
        result = subprocess.run(
            ["pgrep", "-f", process_name],
            capture_output=True,
            text=True,
            timeout=2
        )

        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            pid = pids[0]  # Get first matching PID

            # Get process stats using ps
            ps_result = subprocess.run(
                ["ps", "-p", pid, "-o", "pid,%cpu,%mem,command"],
                capture_output=True,
                text=True,
                timeout=2
            )

            if ps_result.returncode == 0:
                lines = ps_result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split(None, 3)
                    return {
                        "running": True,
                        "pid": int(pid),
                        "cpu": float(parts[1]) if len(parts) > 1 else 0.0,
                        "memory": float(parts[2]) if len(parts) > 2 else 0.0,
                        "status": "running"
                    }

        return {
            "running": False,
            "pid": None,
            "cpu": 0.0,
            "memory": 0.0,
            "status": "stopped"
        }
    except Exception as e:
        logger.warning(f"Failed to check process {process_name}: {e}")
        return {
            "running": False,
            "pid": None,
            "cpu": 0.0,
            "memory": 0.0,
            "status": "unknown",
            "error": str(e)
        }


def check_port_listening(port: int) -> bool:
    """Check if a port is being listened on."""
    try:
        # Use netstat or ss to check if port is listening
        result = subprocess.run(
            ["sh", "-c", f"lsof -i :{port} -t || netstat -tuln | grep :{port} || ss -tuln | grep :{port}"],
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.returncode == 0 and result.stdout.strip() != ""
    except Exception as e:
        logger.warning(f"Failed to check port {port}: {e}")
        return False


@app.get("/api/services/status")
async def api_get_services_status():
    """
    Get status of all Claude OS services.

    Returns real-time status for:
    - MCP Server (this server)
    - Frontend (Vite dev server)
    - Redis
    - RQ Worker
    - Ollama
    - File Watcher
    """
    services = []

    # 1. MCP Server (always running since we're responding)
    mcp_status = {
        "name": "MCP Server",
        "type": "mcp_server",
        "port": Config.MCP_SERVER_PORT,
        "running": True,
        "status": "running",
        "pid": os.getpid(),
        "cpu": 0.0,
        "memory": 0.0,
        "description": "Main API server and MCP endpoint"
    }
    services.append(mcp_status)

    # 2. Frontend (Vite dev server on port 5173)
    frontend_port = 5173
    frontend_process = check_process_running("vite")
    frontend_status = {
        "name": "Frontend",
        "type": "frontend",
        "port": frontend_port,
        "running": frontend_process["running"] or check_port_listening(frontend_port),
        "status": frontend_process["status"],
        "pid": frontend_process.get("pid"),
        "cpu": frontend_process.get("cpu", 0.0),
        "memory": frontend_process.get("memory", 0.0),
        "description": "React web interface"
    }
    services.append(frontend_status)

    # 3. Redis (port 6379)
    redis_port = 6379
    redis_process = check_process_running("redis-server")
    redis_status = {
        "name": "Redis",
        "type": "redis",
        "port": redis_port,
        "running": redis_process["running"] or check_port_listening(redis_port),
        "status": redis_process["status"],
        "pid": redis_process.get("pid"),
        "cpu": redis_process.get("cpu", 0.0),
        "memory": redis_process.get("memory", 0.0),
        "description": "Job queue and caching"
    }
    services.append(redis_status)

    # 4. RQ Worker
    rq_process = check_process_running("rq worker")
    rq_status = {
        "name": "RQ Worker",
        "type": "rq_worker",
        "port": None,
        "running": rq_process["running"],
        "status": rq_process["status"],
        "pid": rq_process.get("pid"),
        "cpu": rq_process.get("cpu", 0.0),
        "memory": rq_process.get("memory", 0.0),
        "description": "Background job processor"
    }
    services.append(rq_status)

    # 5. Ollama (port 11434)
    ollama_port = 11434
    ollama_running = False
    try:
        response = requests.get(f"{Config.OLLAMA_HOST}/api/tags", timeout=1)
        ollama_running = response.status_code == 200
    except:
        ollama_running = check_port_listening(ollama_port)

    ollama_process = check_process_running("ollama")
    ollama_status = {
        "name": "Ollama",
        "type": "ollama",
        "port": ollama_port,
        "running": ollama_running or ollama_process["running"],
        "status": "running" if ollama_running else ollama_process["status"],
        "pid": ollama_process.get("pid"),
        "cpu": ollama_process.get("cpu", 0.0),
        "memory": ollama_process.get("memory", 0.0),
        "description": "Local AI model server"
    }
    services.append(ollama_status)

    # 6. File Watcher
    try:
        watcher = get_global_watcher()
        watcher_status_data = watcher.get_status()
        # Watcher is running if it has projects being watched
        watcher_running = watcher_status_data.get("projects_watched", 0) > 0
    except:
        watcher_running = False

    watcher_status = {
        "name": "File Watcher",
        "type": "file_watcher",
        "port": None,
        "running": watcher_running,
        "status": "running" if watcher_running else "stopped",
        "pid": None,
        "cpu": 0.0,
        "memory": 0.0,
        "description": "Automatic folder sync"
    }
    services.append(watcher_status)

    # Calculate summary
    total = len(services)
    running = sum(1 for s in services if s["running"])
    stopped = total - running

    return {
        "services": services,
        "summary": {
            "total": total,
            "running": running,
            "stopped": stopped,
            "health": "healthy" if running >= total - 1 else ("degraded" if running > 0 else "critical")
        },
        "timestamp": time.time()
    }


@app.post("/api/services/{service_type}/control")
async def api_control_service(service_type: str, request: ServiceControlRequest):
    """
    Control a service (start/stop/restart).

    Note: This is a basic implementation. In production, you'd want more
    sophisticated service management (systemd, supervisord, etc.)
    """
    action = request.action.lower()

    if action not in ["start", "stop", "restart"]:
        raise HTTPException(status_code=400, detail=f"Invalid action: {action}")

    # For now, return a helpful message about manual control
    # In a production system, you'd integrate with systemd or supervisord

    if service_type == "mcp_server":
        return {
            "success": False,
            "message": "Cannot control MCP server from itself. Use ./start.sh or stop_all_services.sh",
            "service": service_type
        }

    service_commands = {
        "frontend": {
            "start": "cd frontend && npm run dev &",
            "stop": "pkill -f 'vite'",
            "script": "frontend/package.json"
        },
        "redis": {
            "start": "redis-server --daemonize yes",
            "stop": "redis-cli shutdown",
            "script": None
        },
        "rq_worker": {
            "start": "rq worker &",
            "stop": "pkill -f 'rq worker'",
            "script": None
        },
        "ollama": {
            "start": "ollama serve &",
            "stop": "pkill -f ollama",
            "script": None
        }
    }

    if service_type not in service_commands:
        raise HTTPException(status_code=404, detail=f"Unknown service: {service_type}")

    commands = service_commands[service_type]

    return {
        "success": False,
        "message": f"Service control not fully implemented yet. Manual command:",
        "manual_command": commands.get(action),
        "service": service_type,
        "action": action,
        "note": "Use start_all_services.sh or stop_all_services.sh for full control"
    }


@app.get("/api/browse-directory")
async def api_browse_directory(path: str = None):
    """REST API: Browse directories and return subdirectories."""
    try:
        from pathlib import Path
        import os

        # If no path provided or empty string, start from home directory
        if not path or path.strip() == '':
            path = str(Path.home())

        # Normalize and validate path
        dir_path = Path(path).expanduser().resolve()

        # Security check: ensure path exists and is a directory
        if not dir_path.exists():
            raise HTTPException(status_code=404, detail=f"Directory not found: {path}")

        if not dir_path.is_dir():
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")

        # Get subdirectories with robust error handling
        subdirs = []
        try:
            # Collect items first to handle iteration errors
            items = []
            try:
                items = list(dir_path.iterdir())
            except PermissionError:
                raise HTTPException(status_code=403, detail=f"Permission denied: {path}")

            # Sort items with error handling for broken symlinks
            def safe_sort_key(item):
                try:
                    return str(item).lower()
                except Exception as e:
                    logger.warning(f"Error sorting item {item}: {e}")
                    return ""

            sorted_items = sorted(items, key=safe_sort_key)

            # Process each item with individual error handling
            for item in sorted_items:
                try:
                    # Skip hidden files/directories
                    if item.name.startswith('.'):
                        continue

                    # Check if it's a directory (this can fail for broken symlinks)
                    if item.is_dir():
                        subdirs.append({
                            "name": item.name,
                            "path": str(item),
                            "is_dir": True
                        })
                except (OSError, PermissionError) as e:
                    # Skip items that cause errors (broken symlinks, permission issues, etc.)
                    logger.warning(f"Skipping item {item.name} in {dir_path}: {e}")
                    continue
                except Exception as e:
                    # Catch any other unexpected errors and skip the item
                    logger.warning(f"Unexpected error processing item {item.name} in {dir_path}: {e}")
                    continue
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error iterating directory {dir_path}: {e}")
            raise HTTPException(status_code=500, detail=f"Error reading directory: {str(e)}")

        return {
            "current_path": str(dir_path),
            "parent_path": str(dir_path.parent) if dir_path.parent != dir_path else None,
            "subdirectories": subdirs
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to browse directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint (detailed version at end of file)


# MCP Protocol Endpoints
@app.post("/")
async def mcp_root(request: Request):
    """Main MCP endpoint - handles JSON-RPC requests."""
    return await handle_mcp_request(request)


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Global MCP endpoint - exposes all KBs."""
    return await handle_mcp_request(request, kb_filter=None)


@app.post("/mcp/kb/{kb_slug}")
async def mcp_kb_endpoint(kb_slug: str, request: Request):
    """KB-specific MCP endpoint - only exposes tools for this KB."""
    # Get KB name from slug
    db_manager = get_sqlite_manager()
    kb_name = db_manager.get_kb_by_slug(kb_slug)

    if not kb_name:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32000,
                "message": f"Knowledge base with slug '{kb_slug}' not found"
            }
        }, status_code=404)

    return await handle_mcp_request(request, kb_filter=kb_name)


async def handle_mcp_request(request: Request, kb_filter: Optional[str] = None) -> JSONResponse:
    """
    Handle MCP JSON-RPC requests.

    Args:
        request: FastAPI request object
        kb_filter: If provided, only expose tools for this specific KB
    """
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        logger.info(f"MCP request: {method} (kb_filter={kb_filter})")

        # Handle MCP protocol methods
        if method == "initialize":
            server_name = f"claude-os-{kb_filter}" if kb_filter else "claude-os"
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": server_name,
                        "version": "1.0.0"
                    }
                }
            })

        elif method == "tools/list":
            # Filter tools based on kb_filter
            if kb_filter:
                # KB-specific endpoint: only expose search tool for this KB
                tools_list = [
                    {
                        "name": "search",
                        "description": f"Search the '{kb_filter}' knowledge base using RAG with optional advanced features",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "The search query"},
                                "use_hybrid": {"type": "boolean", "description": "Enable hybrid search (vector + BM25)", "default": False},
                                "use_rerank": {"type": "boolean", "description": "Enable reranking for better relevance", "default": False},
                                "use_agentic": {"type": "boolean", "description": "Enable agentic RAG for complex queries", "default": False}
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "get_stats",
                        "description": f"Get statistics for the '{kb_filter}' knowledge base",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "list_documents",
                        "description": f"List all documents in the '{kb_filter}' knowledge base",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            else:
                # Global endpoint: expose all tools
                tools_list = [
                    {"name": name, **info}
                    for name, info in TOOLS.items()
                ]

            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools_list}
            })

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            # Handle KB-specific endpoint tool calls
            if kb_filter:
                # Inject kb_name into arguments for KB-specific tools
                if tool_name == "search":
                    result = await search_knowledge_base(kb_name=kb_filter, **arguments)
                elif tool_name == "get_stats":
                    result = await get_kb_stats(kb_name=kb_filter)
                elif tool_name == "list_documents":
                    result = await list_documents(kb_name=kb_filter)
                else:
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    })
            else:
                # Global endpoint: route to appropriate tool function
                if tool_name == "search_knowledge_base":
                    result = await search_knowledge_base(**arguments)
                elif tool_name == "list_knowledge_bases":
                    result = await list_knowledge_bases()
                elif tool_name == "list_knowledge_bases_by_type":
                    result = await list_knowledge_bases_by_type(**arguments)
                elif tool_name == "create_knowledge_base":
                    result = await create_knowledge_base(**arguments)
                elif tool_name == "get_kb_stats":
                    result = await get_kb_stats(**arguments)
                elif tool_name == "list_documents":
                    result = await list_documents(**arguments)
                elif tool_name == "ingest_agent_os_profile":
                    result = await ingest_agent_os_profile(**arguments)
                elif tool_name == "get_agent_os_stats":
                    result = await get_agent_os_stats(**arguments)
                elif tool_name == "get_standards":
                    result = await get_standards(**arguments)
                elif tool_name == "get_workflows":
                    result = await get_workflows(**arguments)
                elif tool_name == "get_specs":
                    result = await get_specs(**arguments)
                elif tool_name == "get_product_context":
                    result = await get_product_context(**arguments)
                else:
                    return JSONResponse({
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Unknown tool: {tool_name}"
                        }
                    })

            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": str(result)
                        }
                    ]
                }
            })

        else:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            })

    except Exception as e:
        logger.error(f"MCP request failed: {e}", exc_info=True)
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": body.get("id") if 'body' in locals() else None,
            "error": {
                "code": -32603,
                "message": str(e)
            }
        })


# ============================================================================
# Authentication Endpoints
# ============================================================================

from mcp_server.auth import (
    authenticate_user,
    create_access_token,
    is_auth_enabled,
    get_current_user
)
from datetime import timedelta


class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/api/auth/login")
async def login(request: LoginRequest):
    """Login endpoint - returns JWT token if credentials are valid."""
    if not is_auth_enabled():
        raise HTTPException(
            status_code=501,
            detail="Authentication is not configured. Set CLAUDE_OS_EMAIL and CLAUDE_OS_PASSWORD in environment."
        )

    if not authenticate_user(request.email, request.password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )

    access_token = create_access_token(
        data={"sub": request.email},
        expires_delta=timedelta(days=7)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email": request.email
    }


@app.get("/api/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info."""
    return current_user


@app.get("/api/auth/status")
async def auth_status():
    """Check if authentication is enabled."""
    return {
        "auth_enabled": is_auth_enabled()
    }


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """
    Health check endpoint that verifies all system components.
    Returns detailed status for monitoring.
    """
    health_status = {
        "status": "healthy",
        "components": {},
        "timestamp": None
    }

    from datetime import datetime
    health_status["timestamp"] = datetime.utcnow().isoformat()

    # Check SQLite Database
    try:
        db_manager = get_sqlite_manager()
        collections = db_manager.list_collections()

        # Get SQLite table count
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
        table_count = cursor.fetchone()[0]

        health_status["components"]["sqlite"] = {
            "status": "healthy",
            "connected": True,
            "database": "claude-os.db",
            "tables": table_count,
            "knowledge_bases": len(collections)
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["sqlite"] = {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }

    # Check Ollama
    try:
        response = requests.get(f"{Config.OLLAMA_HOST}/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]

            # Check for required models
            required_models = ["nomic-embed-text:latest", "llama3.2:3b"]
            missing_models = [m for m in required_models if m not in model_names]

            health_status["components"]["ollama"] = {
                "status": "healthy" if not missing_models else "degraded",
                "running": True,
                "models_installed": len(models),
                "required_models": required_models,
                "missing_models": missing_models
            }

            if missing_models:
                health_status["status"] = "degraded"
        else:
            health_status["status"] = "degraded"
            health_status["components"]["ollama"] = {
                "status": "degraded",
                "running": True,
                "error": f"Unexpected status code: {response.status_code}"
            }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["ollama"] = {
            "status": "unhealthy",
            "running": False,
            "error": str(e)
        }

    # Return appropriate HTTP status code
    status_code = 200 if health_status["status"] in ["healthy", "degraded"] else 503

    return JSONResponse(content=health_status, status_code=status_code)


def main():
    """Start the MCP server."""
    # Validate configuration before starting
    try:
        Config.validate_config()
        logger.info("✅ Configuration validated successfully")
    except ValueError as e:
        logger.error(f"❌ Configuration validation failed:\n{e}")
        sys.exit(1)

    logger.info(f"Starting Claude OS MCP Server on {Config.MCP_SERVER_HOST}:{Config.MCP_SERVER_PORT}")
    logger.info(f"MCP endpoint: http://{Config.MCP_SERVER_HOST}:{Config.MCP_SERVER_PORT}/mcp")

    uvicorn.run(
        app,
        host=Config.MCP_SERVER_HOST,
        port=Config.MCP_SERVER_PORT,
        log_level="info"
    )


if __name__ == "__main__":
    main()

