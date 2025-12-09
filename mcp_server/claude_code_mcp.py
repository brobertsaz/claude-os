#!/usr/bin/env python3
"""
True MCP Server for Claude Code integration.
Wraps the Claude OS REST API as a proper MCP server with stdio transport.

Server name is "code-forge" for backwards compatibility with existing
memories and documentation, but it IS Claude OS.

Usage:
  Run: ./install.sh (this will configure everything)

  Or manually add to ~/.claude/settings.json:
  {
    "mcpServers": {
      "code-forge": {
        "command": "/path/to/claude-os/venv/bin/python3",
        "args": ["/path/to/claude-os/mcp_server/claude_code_mcp.py"],
        "env": {
          "CLAUDE_OS_API": "http://localhost:8051"
        }
      }
    }
  }
"""

import asyncio
import json
import os
import sys
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configuration
API_BASE = os.environ.get("CLAUDE_OS_API", "http://localhost:8051")

# Initialize MCP server - named "code-forge" for backwards compatibility
server = Server("code-forge")


def api_url(path: str) -> str:
    """Build full API URL."""
    return f"{API_BASE}{path}"


async def api_get(path: str) -> dict:
    """Make GET request to API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(api_url(path), timeout=30.0)
        response.raise_for_status()
        return response.json()


async def api_post(path: str, data: dict = None) -> dict:
    """Make POST request to API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(api_url(path), json=data or {}, timeout=60.0)
        response.raise_for_status()
        return response.json()


async def api_delete(path: str) -> dict:
    """Make DELETE request to API."""
    async with httpx.AsyncClient() as client:
        response = await client.delete(api_url(path), timeout=30.0)
        response.raise_for_status()
        return response.json()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Claude OS tools.

    Tool names match what templates/commands expect:
    - mcp__code-forge__search_knowledge_base
    - mcp__code-forge__list_knowledge_bases
    - mcp__code-forge__list_documents
    - etc.
    """
    return [
        # Knowledge Base Tools
        Tool(
            name="list_knowledge_bases",
            description="List all knowledge bases in Claude OS",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="create_knowledge_base",
            description="Create a new knowledge base",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the knowledge base"},
                    "kb_type": {"type": "string", "enum": ["generic", "code", "documentation"], "default": "generic"},
                    "description": {"type": "string", "description": "Description of the KB"}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="search_knowledge_base",
            description="Search/query a knowledge base using RAG. Returns relevant documents and an AI-generated answer.",
            inputSchema={
                "type": "object",
                "properties": {
                    "kb_name": {"type": "string", "description": "Name of the knowledge base to search"},
                    "query": {"type": "string", "description": "Search query"},
                    "top_k": {"type": "integer", "default": 5, "description": "Number of results to return"},
                    "use_hybrid": {"type": "boolean", "default": True, "description": "Use hybrid search (semantic + keyword)"}
                },
                "required": ["kb_name", "query"]
            }
        ),
        Tool(
            name="get_kb_stats",
            description="Get statistics for a knowledge base (document count, chunk count, etc.)",
            inputSchema={
                "type": "object",
                "properties": {
                    "kb_name": {"type": "string", "description": "Name of the knowledge base"}
                },
                "required": ["kb_name"]
            }
        ),
        Tool(
            name="list_documents",
            description="List all documents in a knowledge base",
            inputSchema={
                "type": "object",
                "properties": {
                    "kb_name": {"type": "string", "description": "Name of the knowledge base"}
                },
                "required": ["kb_name"]
            }
        ),
        Tool(
            name="delete_knowledge_base",
            description="Delete a knowledge base and all its documents",
            inputSchema={
                "type": "object",
                "properties": {
                    "kb_name": {"type": "string", "description": "Name of the knowledge base to delete"}
                },
                "required": ["kb_name"]
            }
        ),

        # Project Tools
        Tool(
            name="list_projects",
            description="List all projects registered with Claude OS",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="create_project",
            description="Create/register a new project with Claude OS",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Project name"},
                    "path": {"type": "string", "description": "Absolute path to project directory"},
                    "description": {"type": "string", "description": "Project description"}
                },
                "required": ["name", "path"]
            }
        ),
        Tool(
            name="get_project",
            description="Get details for a specific project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "integer", "description": "Project ID"}
                },
                "required": ["project_id"]
            }
        ),

        # Indexing Tools
        Tool(
            name="index_structural",
            description="Run tree-sitter structural indexing on code files. Fast indexing that extracts functions, classes, imports.",
            inputSchema={
                "type": "object",
                "properties": {
                    "kb_name": {"type": "string", "description": "Name of the knowledge base"},
                    "path": {"type": "string", "description": "Path to directory to index"}
                },
                "required": ["kb_name", "path"]
            }
        ),
        Tool(
            name="index_semantic",
            description="Run semantic embedding indexing on a knowledge base. Creates vector embeddings for similarity search. Runs in background by default - returns job_id to check progress at /api/jobs/{job_id}.",
            inputSchema={
                "type": "object",
                "properties": {
                    "kb_name": {"type": "string", "description": "Name of the knowledge base"},
                    "project_path": {"type": "string", "description": "Path to project to index"},
                    "selective": {"type": "boolean", "description": "If true, only index top 20% most important files + docs (default: true)"},
                    "background": {"type": "boolean", "description": "If true, run in background (default: true). Set false to block until complete."}
                },
                "required": ["kb_name", "project_path"]
            }
        ),

        # Document Management
        Tool(
            name="upload_document",
            description="Upload/save a document or memory to a knowledge base",
            inputSchema={
                "type": "object",
                "properties": {
                    "kb_name": {"type": "string", "description": "Name of the knowledge base"},
                    "content": {"type": "string", "description": "Content to save (markdown supported)"},
                    "filename": {"type": "string", "description": "Filename for the document (e.g., 'my-memory.md')"},
                    "title": {"type": "string", "description": "Title for the document"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags for categorization"}
                },
                "required": ["kb_name", "content", "filename"]
            }
        ),
        Tool(
            name="delete_document",
            description="Delete a document from a knowledge base",
            inputSchema={
                "type": "object",
                "properties": {
                    "kb_name": {"type": "string", "description": "Name of the knowledge base"},
                    "filename": {"type": "string", "description": "Filename of the document to delete"}
                },
                "required": ["kb_name", "filename"]
            }
        ),

        # Utility Tools
        Tool(
            name="get_ollama_models",
            description="List available Ollama models for embeddings and LLM",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="health_check",
            description="Check if Claude OS API server is running and healthy",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a Claude OS tool."""
    try:
        result = await _execute_tool(name, arguments)
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except httpx.HTTPStatusError as e:
        error_msg = f"API error: {e.response.status_code} - {e.response.text}"
        return [TextContent(type="text", text=json.dumps({"error": error_msg}))]
    except httpx.ConnectError:
        return [TextContent(type="text", text=json.dumps({
            "error": "Cannot connect to Claude OS API. Is the server running? Start with: ./start_all_services.sh"
        }))]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _execute_tool(name: str, args: dict[str, Any]) -> dict:
    """Route tool calls to appropriate API endpoints."""

    # Knowledge Base Tools
    if name == "list_knowledge_bases":
        return await api_get("/api/kb")

    elif name == "create_knowledge_base":
        return await api_post("/api/kb", {
            "name": args["name"],
            "kb_type": args.get("kb_type", "generic"),
            "description": args.get("description", "")
        })

    elif name == "search_knowledge_base":
        return await api_post(f"/api/kb/{args['kb_name']}/chat", {
            "query": args["query"],
            "top_k": args.get("top_k", 5),
            "use_hybrid": args.get("use_hybrid", True)
        })

    elif name == "get_kb_stats":
        return await api_get(f"/api/kb/{args['kb_name']}/stats")

    elif name == "list_documents":
        return await api_get(f"/api/kb/{args['kb_name']}/documents")

    elif name == "delete_knowledge_base":
        return await api_delete(f"/api/kb/{args['kb_name']}")

    # Project Tools
    elif name == "list_projects":
        return await api_get("/api/projects")

    elif name == "create_project":
        return await api_post("/api/projects", {
            "name": args["name"],
            "path": args["path"],
            "description": args.get("description", "")
        })

    elif name == "get_project":
        return await api_get(f"/api/projects/{args['project_id']}")

    # Indexing Tools
    elif name == "index_structural":
        return await api_post(f"/api/kb/{args['kb_name']}/index-structural", {
            "path": args["path"]
        })

    elif name == "index_semantic":
        return await api_post(f"/api/kb/{args['kb_name']}/index-semantic", {
            "project_path": args["project_path"],
            "selective": args.get("selective", True),
            "background": args.get("background", True)
        })

    # Document Management
    elif name == "upload_document":
        return await api_post(f"/api/kb/{args['kb_name']}/import", {
            "content": args["content"],
            "filename": args["filename"],
            "metadata": {
                "title": args.get("title", ""),
                "tags": args.get("tags", [])
            }
        })

    elif name == "delete_document":
        return await api_delete(f"/api/kb/{args['kb_name']}/documents/{args['filename']}")

    # Utility Tools
    elif name == "get_ollama_models":
        return await api_get("/api/ollama/models")

    elif name == "health_check":
        try:
            # Simple health check - list KBs should work if server is up
            result = await api_get("/api/kb")
            return {"status": "healthy", "message": "Claude OS is running", "kb_count": len(result.get("knowledge_bases", []))}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    else:
        return {"error": f"Unknown tool: {name}"}


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
