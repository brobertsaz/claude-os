"""
MCP Server for Claude OS.
Exposes RAG functionality via Model Context Protocol with HTTP transport.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import requests
from typing import Optional

from app.core.sqlite_manager import get_sqlite_manager
from app.core.config import Config
from app.core.kb_metadata import get_collection_stats, get_documents_metadata
from app.core.kb_types import KBType
from app.core.rag_engine import RAGEngine
from app.core.agent_os_ingestion import AgentOSIngestion
from app.core.agent_os_parser import AgentOSContentType
from app.core.hooks import get_project_hook
from app.core.file_watcher import get_global_watcher
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def api_chat(kb_name: str, request: ChatRequest):
    """REST API: Chat with a knowledge base."""
    result = await search_knowledge_base(
        kb_name=kb_name,
        query=request.query,
        use_hybrid=request.use_hybrid,
        use_rerank=request.use_rerank,
        use_agentic=request.use_agentic
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
                    "SELECT id FROM knowledge_bases WHERE name = %s",
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
                    WHERE kb_id = %s AND metadata->>'filename' = %s
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
        valid_mcp_types = ["knowledge_docs", "project_profile", "project_index", "project_memories"]
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
        valid_mcp_types = ["knowledge_docs", "project_profile", "project_index", "project_memories"]
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
                    "source": request.filename,
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

        # Get subdirectories
        subdirs = []
        try:
            for item in sorted(dir_path.iterdir()):
                if item.is_dir() and not item.name.startswith('.'):
                    subdirs.append({
                        "name": item.name,
                        "path": str(item),
                        "is_dir": True
                    })
        except PermissionError:
            raise HTTPException(status_code=403, detail=f"Permission denied: {path}")

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

    # Check PostgreSQL
    try:
        db_manager = get_sqlite_manager()
        collections = db_manager.list_collections()

        # Try to get schema version
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")
        table_count = cursor.fetchone()[0]
        cursor.close()
        db_manager.return_connection(conn)

        health_status["components"]["postgresql"] = {
            "status": "healthy",
            "connected": True,
            "database": "codeforge",
            "tables": table_count,
            "knowledge_bases": len(collections)
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["postgresql"] = {
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

    # Check pgvector extension
    try:
        db_manager = get_sqlite_manager()
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT extversion FROM pg_extension WHERE extname='vector';")
        result = cursor.fetchone()
        cursor.close()
        db_manager.return_connection(conn)

        if result:
            health_status["components"]["pgvector"] = {
                "status": "healthy",
                "installed": True,
                "version": result[0]
            }
        else:
            health_status["status"] = "unhealthy"
            health_status["components"]["pgvector"] = {
                "status": "unhealthy",
                "installed": False,
                "error": "pgvector extension not found"
            }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["pgvector"] = {
            "status": "unhealthy",
            "installed": False,
            "error": str(e)
        }

    # Return appropriate HTTP status code
    status_code = 200 if health_status["status"] in ["healthy", "degraded"] else 503

    return JSONResponse(content=health_status, status_code=status_code)


def main():
    """Start the MCP server."""
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

