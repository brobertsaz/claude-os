"""
MCP Server for Code-Forge.
Exposes RAG functionality via Model Context Protocol with HTTP transport.
"""

import logging
import sys
from pathlib import Path
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP
import uvicorn

from app.core.chroma_manager import get_chroma_manager
from app.core.config import Config
from app.core.kb_metadata import get_collection_stats, get_documents_metadata
from app.core.rag_engine import RAGEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI and FastMCP
app = FastAPI(title="Code-Forge MCP Server")
mcp = FastMCP("code-forge")

# Add CORS middleware for Claude Desktop
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@mcp.tool()
async def search_knowledge_base(
    kb_name: str,
    query: str,
    use_hybrid: bool = False,
    use_rerank: bool = False,
    use_agentic: bool = False
) -> dict:
    """
    Search a knowledge base using RAG with optional advanced features.
    
    Args:
        kb_name: Name of the knowledge base to search
        query: The search query
        use_hybrid: Enable hybrid search (vector + BM25 keyword search)
        use_rerank: Enable reranking of results for better relevance
        use_agentic: Enable agentic RAG for complex multi-step queries
    
    Returns:
        dict with 'answer' and 'sources' keys
    """
    try:
        # Validate KB exists
        chroma_manager = get_chroma_manager()
        if not chroma_manager.collection_exists(kb_name):
            return {
                "error": f"Knowledge base '{kb_name}' not found",
                "answer": "",
                "sources": []
            }
        
        # Check if KB is empty
        count = chroma_manager.get_collection_count(kb_name)
        if count == 0:
            return {
                "error": f"Knowledge base '{kb_name}' is empty. Please upload documents first.",
                "answer": "",
                "sources": []
            }
        
        # Initialize RAG engine
        rag_engine = RAGEngine(kb_name)
        
        # Execute query
        result = rag_engine.query(
            question=query,
            use_hybrid=use_hybrid,
            use_rerank=use_rerank,
            use_agentic=use_agentic
        )
        
        logger.info(f"Query executed on {kb_name}: {query[:50]}...")
        
        return result
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {
            "error": str(e),
            "answer": "",
            "sources": []
        }


@mcp.tool()
async def list_knowledge_bases() -> List[str]:
    """
    List all available knowledge bases.
    
    Returns:
        List of knowledge base names
    """
    try:
        chroma_manager = get_chroma_manager()
        kbs = chroma_manager.list_collections()
        logger.info(f"Listed {len(kbs)} knowledge bases")
        return kbs
    except Exception as e:
        logger.error(f"Failed to list knowledge bases: {e}")
        return []


@mcp.tool()
async def get_kb_stats(kb_name: str) -> dict:
    """
    Get statistics for a knowledge base.
    
    Args:
        kb_name: Name of the knowledge base
    
    Returns:
        dict with total_documents, total_chunks, and last_updated
    """
    try:
        stats = get_collection_stats(kb_name)
        logger.info(f"Retrieved stats for {kb_name}")
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats for {kb_name}: {e}")
        return {
            "error": str(e),
            "total_documents": 0,
            "total_chunks": 0,
            "last_updated": None
        }


@mcp.tool()
async def list_documents(kb_name: str) -> List[dict]:
    """
    List all documents in a knowledge base.
    
    Args:
        kb_name: Name of the knowledge base
    
    Returns:
        List of document metadata dicts
    """
    try:
        docs = get_documents_metadata(kb_name)
        logger.info(f"Listed {len(docs)} documents in {kb_name}")
        return docs
    except Exception as e:
        logger.error(f"Failed to list documents in {kb_name}: {e}")
        return []


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "code-forge-mcp"}


# MCP endpoint
@app.post("/mcp")
async def mcp_endpoint(request: dict):
    """
    MCP protocol endpoint.
    Handles JSON-RPC style requests from MCP clients.
    """
    try:
        # FastMCP handles the request routing
        return await mcp.handle_request(request)
    except Exception as e:
        logger.error(f"MCP request failed: {e}")
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": str(e)
            },
            "id": request.get("id")
        }


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

