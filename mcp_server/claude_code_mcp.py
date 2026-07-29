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
import time
from pathlib import Path
from typing import Any

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configuration
API_BASE = os.environ.get("CLAUDE_OS_API", "http://localhost:8051")

# Health cache — tracks last health check time per KB and any warnings
HEALTH_CACHE: dict[str, dict] = {}
HEALTH_CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "health_cache.json"
)
HEALTH_CHECK_INTERVAL = 86400  # 24 hours


def _load_health_cache() -> None:
    """Load health cache from disk."""
    global HEALTH_CACHE
    try:
        if os.path.exists(HEALTH_CACHE_FILE):
            with open(HEALTH_CACHE_FILE, "r") as f:
                HEALTH_CACHE = json.load(f)
    except Exception:
        HEALTH_CACHE = {}


def _save_health_cache() -> None:
    """Persist health cache to disk."""
    try:
        Path(HEALTH_CACHE_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(HEALTH_CACHE_FILE, "w") as f:
            json.dump(HEALTH_CACHE, f)
    except Exception:
        pass


async def _maybe_check_health(kb_name: str) -> list[str]:
    """Run a health check if stale (>24h) for this KB. Returns warning strings."""
    _load_health_cache()
    now = time.time()
    entry = HEALTH_CACHE.get(kb_name)
    if entry and (now - entry.get("checked_at", 0)) < HEALTH_CHECK_INTERVAL:
        return entry.get("warnings", [])

    # Run health check
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(api_url(f"/api/kb/{kb_name}/lifecycle/health"), timeout=15.0)
            resp.raise_for_status()
            health = resp.json()

        warnings = []
        recs = health.get("recommendations", [])
        for rec in recs:
            severity = rec.get("severity", "")
            msg = rec.get("message", rec.get("recommendation", ""))
            if severity in ("high", "critical") and msg:
                warnings.append(f"[{severity.upper()}] {msg}")

        HEALTH_CACHE[kb_name] = {"checked_at": now, "warnings": warnings}
        _save_health_cache()
        return warnings
    except Exception:
        # Never break search — just skip the health check
        return []

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


async def api_put(path: str, data: dict = None) -> dict:
    """Make PUT request to API."""
    async with httpx.AsyncClient() as client:
        response = await client.put(api_url(path), json=data or {}, timeout=30.0)
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
        ),

        # Session Tools
        Tool(
            name="list_sessions",
            description="List Claude Code session files for a project. Sessions are stored in ~/.claude/projects/{encoded-path}/ and contain conversation history.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "description": "Absolute path to project directory (e.g., /Users/x/Projects/myapp)"},
                    "limit": {"type": "integer", "default": 50, "description": "Maximum sessions to return (default: 50)"}
                },
                "required": ["project_path"]
            }
        ),
        Tool(
            name="extract_session_insights",
            description="Extract insights from a Claude Code session file using LLM. Analyzes conversation to find decisions, patterns, solutions, and blockers. Optionally saves insights to a knowledge base.",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_path": {"type": "string", "description": "Absolute path to .jsonl session file"},
                    "kb_name": {"type": "string", "description": "Knowledge base name to save insights (optional)"},
                    "auto_save": {"type": "boolean", "default": False, "description": "Auto-save all insights without prompting"},
                    "insight_types": {
                        "type": "array",
                        "items": {"type": "string", "enum": ["decision", "pattern", "solution", "blocker"]},
                        "default": ["decision", "pattern", "solution", "blocker"],
                        "description": "Types of insights to extract"
                    },
                    "min_confidence": {"type": "number", "default": 0.7, "description": "Minimum confidence threshold (0.0-1.0)"}
                },
                "required": ["session_path"]
            }
        ),

        # Skill Management Tools
        Tool(
            name="list_skills",
            description="List all skills (global and project-level). Global skills are in ~/.claude/skills/, project skills are in {project}/.claude/skills/.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "description": "Project path to include project-level skills (optional)"},
                    "include_content": {"type": "boolean", "default": False, "description": "Include full skill content"}
                },
                "required": []
            }
        ),
        Tool(
            name="list_skill_templates",
            description="List available skill templates that can be installed to projects. Templates are organized by category.",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Filter by category (optional)"}
                },
                "required": []
            }
        ),
        Tool(
            name="get_skill",
            description="Get skill details including full content.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Skill name"},
                    "scope": {"type": "string", "enum": ["global", "project"], "description": "Where the skill is located"},
                    "project_path": {"type": "string", "description": "Project path (required if scope is 'project')"}
                },
                "required": ["name", "scope"]
            }
        ),
        Tool(
            name="install_skill_template",
            description="Install a skill template to a project. Copies the template to {project}/.claude/skills/.",
            inputSchema={
                "type": "object",
                "properties": {
                    "template_name": {"type": "string", "description": "Name of template to install"},
                    "project_path": {"type": "string", "description": "Project path to install to"},
                    "custom_name": {"type": "string", "description": "Custom name for installed skill (optional)"}
                },
                "required": ["template_name", "project_path"]
            }
        ),
        Tool(
            name="create_skill",
            description="Create a custom skill for a project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Skill name"},
                    "description": {"type": "string", "description": "Skill description"},
                    "content": {"type": "string", "description": "Skill content (markdown)"},
                    "project_path": {"type": "string", "description": "Project path"},
                    "category": {"type": "string", "description": "Category (optional)"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags (optional)"}
                },
                "required": ["name", "description", "content", "project_path"]
            }
        ),
        Tool(
            name="update_skill",
            description="Update an existing project skill.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Skill name"},
                    "project_path": {"type": "string", "description": "Project path"},
                    "content": {"type": "string", "description": "New content (optional)"},
                    "description": {"type": "string", "description": "New description (optional)"},
                    "tags": {"type": "array", "items": {"type": "string"}, "description": "New tags (optional)"}
                },
                "required": ["name", "project_path"]
            }
        ),
        Tool(
            name="delete_skill",
            description="Delete a project skill. Cannot delete global skills.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Skill name to delete"},
                    "project_path": {"type": "string", "description": "Project path"}
                },
                "required": ["name", "project_path"]
            }
        ),

        # Knowledge Lifecycle Tools
        Tool(
            name="kb_lifecycle_health",
            description="Get a comprehensive health report for a knowledge base including duplicate detection, embedding coverage, age distribution, and recommendations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "kb_name": {"type": "string", "description": "Name of the knowledge base"}
                },
                "required": ["kb_name"]
            }
        ),
        Tool(
            name="kb_lifecycle_dedup",
            description="Scan for and merge duplicate documents in a knowledge base. Use action='scan' to find duplicates, action='merge' to merge them.",
            inputSchema={
                "type": "object",
                "properties": {
                    "kb_name": {"type": "string", "description": "Name of the knowledge base"},
                    "action": {"type": "string", "enum": ["scan", "merge"], "description": "Action to perform: scan for duplicates or merge them"},
                    "threshold": {"type": "number", "default": 0.85, "description": "Similarity threshold for scan (0.0-1.0)"},
                    "max_pairs": {"type": "integer", "default": 100, "description": "Maximum duplicate pairs to return"},
                    "keep_doc_id": {"type": "string", "description": "Document ID to keep (required for merge)"},
                    "remove_doc_ids": {"type": "array", "items": {"type": "string"}, "description": "Document IDs to remove (required for merge)"},
                    "dry_run": {"type": "boolean", "default": False, "description": "Preview changes without applying"}
                },
                "required": ["kb_name", "action"]
            }
        ),
        Tool(
            name="kb_lifecycle_consolidate",
            description="Consolidate multiple related documents into a single merged document using LLM-powered summarization.",
            inputSchema={
                "type": "object",
                "properties": {
                    "kb_name": {"type": "string", "description": "Name of the knowledge base"},
                    "doc_ids": {"type": "array", "items": {"type": "string"}, "description": "Document IDs to consolidate"},
                    "new_filename": {"type": "string", "description": "Filename for the consolidated document"},
                    "dry_run": {"type": "boolean", "default": False, "description": "Preview without consolidating"}
                },
                "required": ["kb_name", "doc_ids", "new_filename"]
            }
        ),
        Tool(
            name="kb_lifecycle_archive",
            description="Manage document archival: archive, restore, list archived, or find stale documents.",
            inputSchema={
                "type": "object",
                "properties": {
                    "kb_name": {"type": "string", "description": "Name of the knowledge base"},
                    "action": {"type": "string", "enum": ["archive", "restore", "list", "stale"], "description": "Archival action to perform"},
                    "doc_ids": {"type": "array", "items": {"type": "string"}, "description": "Document IDs (required for archive/restore)"},
                    "reason": {"type": "string", "default": "manual", "description": "Reason for archiving"},
                    "stale_days": {"type": "integer", "default": 90, "description": "Days threshold for stale detection"}
                },
                "required": ["kb_name", "action"]
            }
        ),

        # Cross-KB Search
        Tool(
            name="search_all_knowledge_bases",
            description="Search across multiple knowledge bases at once. Returns merged results sorted by relevance with KB attribution.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "top_k": {"type": "integer", "default": 10, "description": "Number of results to return"},
                    "kb_filter": {"type": "string", "description": "Optional prefix filter for KB names (e.g. 'Pistn-' to search only Pistn KBs)"}
                },
                "required": ["query"]
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
        result = await api_post(f"/api/kb/{args['kb_name']}/chat", {
            "query": args["query"],
            "top_k": args.get("top_k", 5),
            "use_hybrid": args.get("use_hybrid", True)
        })
        # Inline health check — append warnings if stale
        warnings = await _maybe_check_health(args["kb_name"])
        if warnings:
            result["_health_warnings"] = warnings
        return result

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
            # API expects "project_path" - sending "path" returns 422
            "project_path": args["path"]
        })

    elif name == "index_semantic":
        return await api_post(f"/api/kb/{args['kb_name']}/index-semantic", {
            "project_path": args["project_path"],
            "selective": args.get("selective", True),
            "background": args.get("background", True)
        })

    # Document Management
    elif name == "upload_document":
        return await api_post(f"/api/kb/{args['kb_name']}/documents/content", {
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

    # Session Tools
    elif name == "list_sessions":
        return await api_get(f"/api/sessions/list?project_path={args['project_path']}&limit={args.get('limit', 50)}")

    elif name == "extract_session_insights":
        return await api_post("/api/sessions/extract", {
            "session_path": args["session_path"],
            "kb_name": args.get("kb_name"),
            "auto_save": args.get("auto_save", False),
            "insight_types": args.get("insight_types"),
            "min_confidence": args.get("min_confidence", 0.7)
        })

    # Skill Management Tools
    elif name == "list_skills":
        project_path = args.get("project_path", "")
        include_content = args.get("include_content", False)
        url = f"/api/skills?include_content={include_content}"
        if project_path:
            url += f"&project_path={project_path}"
        return await api_get(url)

    elif name == "list_skill_templates":
        category = args.get("category")
        url = "/api/skills/templates"
        if category:
            url += f"?category={category}"
        return await api_get(url)

    elif name == "get_skill":
        scope = args["scope"]
        name_param = args["name"]
        project_path = args.get("project_path", "")
        url = f"/api/skills/{scope}/{name_param}"
        if project_path:
            url += f"?project_path={project_path}"
        return await api_get(url)

    elif name == "install_skill_template":
        return await api_post(f"/api/skills/install?project_path={args['project_path']}", {
            "template_name": args["template_name"],
            "custom_name": args.get("custom_name")
        })

    elif name == "create_skill":
        return await api_post(f"/api/skills?project_path={args['project_path']}", {
            "name": args["name"],
            "description": args["description"],
            "content": args["content"],
            "category": args.get("category"),
            "tags": args.get("tags")
        })

    elif name == "update_skill":
        return await api_put(f"/api/skills/{args['name']}?project_path={args['project_path']}", {
            "content": args.get("content"),
            "description": args.get("description"),
            "tags": args.get("tags")
        })

    elif name == "delete_skill":
        return await api_delete(f"/api/skills/{args['name']}?project_path={args['project_path']}")

    # Knowledge Lifecycle Tools
    elif name == "kb_lifecycle_health":
        return await api_get(f"/api/kb/{args['kb_name']}/lifecycle/health")

    elif name == "kb_lifecycle_dedup":
        action = args["action"]
        kb_name = args["kb_name"]
        if action == "scan":
            return await api_post(f"/api/kb/{kb_name}/lifecycle/dedup-scan", {
                "threshold": args.get("threshold", 0.85),
                "max_pairs": args.get("max_pairs", 100)
            })
        elif action == "merge":
            return await api_post(f"/api/kb/{kb_name}/lifecycle/dedup-merge", {
                "keep_doc_id": args["keep_doc_id"],
                "remove_doc_ids": args["remove_doc_ids"],
                "dry_run": args.get("dry_run", False)
            })
        else:
            return {"error": f"Unknown dedup action: {action}"}

    elif name == "kb_lifecycle_consolidate":
        return await api_post(f"/api/kb/{args['kb_name']}/lifecycle/consolidate", {
            "doc_ids": args["doc_ids"],
            "new_filename": args["new_filename"],
            "dry_run": args.get("dry_run", False)
        })

    elif name == "kb_lifecycle_archive":
        action = args["action"]
        kb_name = args["kb_name"]
        if action == "archive":
            return await api_post(f"/api/kb/{kb_name}/lifecycle/archive", {
                "doc_ids": args["doc_ids"],
                "reason": args.get("reason", "manual")
            })
        elif action == "restore":
            return await api_post(f"/api/kb/{kb_name}/lifecycle/restore", {
                "doc_ids": args["doc_ids"]
            })
        elif action == "list":
            return await api_get(f"/api/kb/{kb_name}/lifecycle/archived")
        elif action == "stale":
            stale_days = args.get("stale_days", 90)
            return await api_get(f"/api/kb/{kb_name}/lifecycle/stale?stale_days={stale_days}")
        else:
            return {"error": f"Unknown archive action: {action}"}

    # Cross-KB Search
    elif name == "search_all_knowledge_bases":
        return await api_post("/api/kb/search-all", {
            "query": args["query"],
            "top_k": args.get("top_k", 10),
            "kb_filter": args.get("kb_filter")
        })

    else:
        return {"error": f"Unknown tool: {name}"}


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
