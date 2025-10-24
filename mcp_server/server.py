"""
MCP Server for Code-Forge.
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
import psycopg2
from typing import Optional

from app.core.pg_manager import get_pg_manager
from app.core.config import Config
from app.core.kb_metadata import get_collection_stats, get_documents_metadata
from app.core.kb_types import KBType
from app.core.rag_engine import RAGEngine
from app.core.agent_os_ingestion import AgentOSIngestion
from app.core.agent_os_parser import AgentOSContentType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Code-Forge MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    """Search a knowledge base using RAG."""
    try:
        pg_manager = get_pg_manager()
        if not pg_manager.collection_exists(kb_name):
            return {"error": f"Knowledge base '{kb_name}' not found", "answer": "", "sources": []}

        count = pg_manager.get_collection_count(kb_name)
        if count == 0:
            return {"error": f"Knowledge base '{kb_name}' is empty", "answer": "", "sources": []}

        rag_engine = RAGEngine(kb_name)
        result = rag_engine.query(question=query, use_hybrid=use_hybrid,
                                 use_rerank=use_rerank, use_agentic=use_agentic)
        logger.info(f"Query executed on {kb_name}: {query[:50]}...")
        return result
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {"error": str(e), "answer": "", "sources": []}


async def list_knowledge_bases() -> List[Dict[str, any]]:
    """List all available knowledge bases with metadata."""
    try:
        pg_manager = get_pg_manager()
        kbs = pg_manager.list_collections()
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
        pg_manager = get_pg_manager()
        kb_type_enum = KBType(kb_type)
        kbs = pg_manager.list_collections_by_type(kb_type_enum)
        logger.info(f"Listed {len(kbs)} knowledge bases of type {kb_type}")
        return kbs
    except Exception as e:
        logger.error(f"Failed to list knowledge bases by type {kb_type}: {e}")
        return []


async def create_knowledge_base(name: str, kb_type: str = "generic", description: str = "") -> dict:
    """Create a new knowledge base."""
    try:
        pg_manager = get_pg_manager()

        # Check if already exists
        if pg_manager.collection_exists(name):
            return {
                "success": False,
                "error": f"Knowledge base '{name}' already exists"
            }

        # Create collection
        kb_type_enum = KBType(kb_type)
        success = pg_manager.create_collection(
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
        pg_manager = get_pg_manager()
        agent_os_ingestion = AgentOSIngestion(pg_manager)

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
        pg_manager = get_pg_manager()
        agent_os_ingestion = AgentOSIngestion(pg_manager)

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
        pg_manager = get_pg_manager()
        agent_os_ingestion = AgentOSIngestion(pg_manager)

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
        pg_manager = get_pg_manager()
        agent_os_ingestion = AgentOSIngestion(pg_manager)

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
        pg_manager = get_pg_manager()
        agent_os_ingestion = AgentOSIngestion(pg_manager)

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
        pg_manager = get_pg_manager()
        agent_os_ingestion = AgentOSIngestion(pg_manager)

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
        pg_manager = get_pg_manager()
        if not pg_manager.collection_exists(kb_name):
            raise HTTPException(status_code=404, detail=f"Knowledge base '{kb_name}' not found")

        success = pg_manager.delete_collection(kb_name)
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
    pg_manager = get_pg_manager()
    kb = pg_manager.get_collection(kb_name)
    if not kb:
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
    pg_manager = get_pg_manager()
    kb = pg_manager.get_collection(kb_name)
    if not kb:
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


# Health check endpoint (detailed version at end of file)


# MCP Protocol Endpoints
@app.post("/")
async def mcp_root(request: Request):
    """Main MCP endpoint - handles JSON-RPC requests."""
    return await handle_mcp_request(request)


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """Alternative MCP endpoint path."""
    return await handle_mcp_request(request)


async def handle_mcp_request(request: Request) -> JSONResponse:
    """Handle MCP JSON-RPC requests."""
    try:
        body = await request.json()
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        logger.info(f"MCP request: {method}")

        # Handle MCP protocol methods
        if method == "initialize":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "code-forge",
                        "version": "1.0.0"
                    }
                }
            })

        elif method == "tools/list":
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

            # Route to appropriate tool function
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
        pg_manager = get_pg_manager()
        collections = pg_manager.list_collections()

        # Try to get schema version
        conn = pg_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';")
        table_count = cursor.fetchone()[0]
        cursor.close()
        pg_manager.return_connection(conn)

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
        pg_manager = get_pg_manager()
        conn = pg_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT extversion FROM pg_extension WHERE extname='vector';")
        result = cursor.fetchone()
        cursor.close()
        pg_manager.return_connection(conn)

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
    logger.info(f"Starting Code-Forge MCP Server on {Config.MCP_SERVER_HOST}:{Config.MCP_SERVER_PORT}")
    logger.info(f"MCP endpoint: http://{Config.MCP_SERVER_HOST}:{Config.MCP_SERVER_PORT}/mcp")

    uvicorn.run(
        app,
        host=Config.MCP_SERVER_HOST,
        port=Config.MCP_SERVER_PORT,
        log_level="info"
    )


if __name__ == "__main__":
    main()

