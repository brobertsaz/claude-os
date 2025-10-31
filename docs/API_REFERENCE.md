# Claude OS API Reference

**Base URL:** `http://localhost:8051`

Complete reference for all Claude OS MCP Server API endpoints.

---

## Table of Contents

1. [Knowledge Base Operations](#knowledge-base-operations)
2. [Hybrid Indexing](#hybrid-indexing-new)
3. [Project Management](#project-management)
4. [Hooks System](#hooks-system)
5. [File Watcher](#file-watcher)
6. [Authentication](#authentication)
7. [Utilities](#utilities)
8. [Health Check](#health-check)

---

## Knowledge Base Operations

### Create Knowledge Base
```http
POST /api/kb
Content-Type: application/json

{
  "name": "my-project-docs",
  "kb_type": "generic",
  "description": "Project documentation"
}
```

**KB Types:**
- `generic` - General purpose
- `code` - Code-specific
- `documentation` - Documentation files
- `agent-os` - Agent-OS integration

**Response:**
```json
{
  "success": true,
  "name": "my-project-docs",
  "kb_type": "generic",
  "description": "Project documentation"
}
```

---

### List Knowledge Bases
```http
GET /api/kb
```

**Response:**
```json
{
  "knowledge_bases": [
    {
      "id": 1,
      "name": "my-project-docs",
      "slug": "my-project-docs",
      "metadata": {
        "kb_type": "generic",
        "description": "Project documentation",
        "created_at": "2025-10-31 12:00:00"
      }
    }
  ]
}
```

---

### Get Knowledge Base Stats
```http
GET /api/kb/{kb_name}/stats
```

**Response:**
```json
{
  "name": "my-project-docs",
  "document_count": 42,
  "total_size_bytes": 1048576,
  "created_at": "2025-10-31 12:00:00"
}
```

---

### List Documents in Knowledge Base
```http
GET /api/kb/{kb_name}/documents
```

**Response:**
```json
{
  "kb_name": "my-project-docs",
  "documents": [
    {
      "id": "doc_123",
      "filename": "README.md",
      "size_bytes": 2048,
      "chunks": 3,
      "created_at": "2025-10-31 12:00:00"
    }
  ]
}
```

---

### Query Knowledge Base
```http
POST /api/kb/{kb_name}/chat
Content-Type: application/json

{
  "message": "What is the authentication flow?",
  "context_size": 5
}
```

**Response:**
```json
{
  "response": "The authentication flow uses JWT tokens...",
  "sources": [
    {
      "filename": "auth.md",
      "chunk_id": "chunk_42",
      "similarity": 0.87
    }
  ],
  "context_used": 3
}
```

---

### Upload Document
```http
POST /api/kb/{kb_name}/upload
Content-Type: multipart/form-data

file=@/path/to/document.pdf
```

**Response:**
```json
{
  "success": true,
  "filename": "document.pdf",
  "kb_name": "my-project-docs",
  "chunks_created": 15
}
```

---

### Import Directory
```http
POST /api/kb/{kb_name}/import
Content-Type: application/json

{
  "directory_path": "/path/to/docs",
  "file_types": [".md", ".txt", ".pdf"]
}
```

**Response:**
```json
{
  "success": true,
  "files_processed": 42,
  "files_successful": 40,
  "files_failed": 2,
  "total_chunks": 350
}
```

---

### Delete Document
```http
DELETE /api/kb/{kb_name}/documents/{filename}
```

**Response:**
```json
{
  "success": true,
  "message": "Document deleted successfully"
}
```

---

### Delete Knowledge Base
```http
DELETE /api/kb/{kb_name}
```

**Response:**
```json
{
  "success": true,
  "message": "Knowledge base deleted successfully"
}
```

---

## Hybrid Indexing (NEW!)

### Phase 1: Structural Indexing (Tree-Sitter)
```http
POST /api/kb/{kb_name}/index-structural
Content-Type: application/json

{
  "project_path": "/Users/username/Projects/myproject",
  "token_budget": 2048,
  "cache_path": ".claude-os/tree_sitter_cache.db"
}
```

**What it does:**
- Parses code with tree-sitter (no LLM calls)
- Extracts all symbols (classes, functions, methods)
- Builds dependency graph
- Computes PageRank importance scores
- Stores as JSON (no embeddings)

**Speed:** ~30 seconds for 10,000 files

**Response:**
```json
{
  "success": true,
  "kb_name": "myproject-code_structure",
  "total_files": 3117,
  "total_symbols": 36591,
  "time_taken_seconds": 3.04,
  "repo_map_preview": "app/models/user.rb:\n  1: class User...",
  "message": "Structural index created: 36591 symbols in 3117 files"
}
```

---

### Phase 2: Selective Semantic Indexing (Embeddings)
```http
POST /api/kb/{kb_name}/index-semantic
Content-Type: application/json

{
  "project_path": "/Users/username/Projects/myproject",
  "selective": true,
  "code_structure_kb": "myproject-code_structure"
}
```

**What it does (Selective Mode):**
- Gets top 20% most important files from structural index (by PageRank)
- Includes all documentation files
- Generates embeddings only for selected files
- 80% reduction in embedding time and storage

**What it does (Full Mode):**
```json
{
  "selective": false
}
```
- Generates embeddings for ALL files
- Slower but more comprehensive

**Response (Selective):**
```json
{
  "success": true,
  "kb_name": "myproject-project_index",
  "mode": "selective",
  "files_selected": 623,
  "files_indexed": 620,
  "time_taken_seconds": 1200,
  "message": "Selective semantic indexing complete: 620/623 files indexed"
}
```

**Response (Full):**
```json
{
  "success": true,
  "kb_name": "myproject-project_index",
  "mode": "full",
  "total_files": 3117,
  "successful": 3100,
  "time_taken_seconds": 10800,
  "message": "Full semantic indexing complete: 3100 files indexed"
}
```

---

### Get Repo Map
```http
GET /api/kb/{kb_name}/repo-map?token_budget=1024&project_path=/path/to/project
```

**What it does:**
- Generates compact code structure map
- Fits within specified token budget
- Shows most important symbols first (PageRank-ranked)
- Perfect for including in Claude's prompt context

**Response:**
```json
{
  "success": true,
  "repo_map": "app/models/user.rb:\n  1: class User < ApplicationRecord\n  15: def authenticate...",
  "token_count": 820,
  "total_symbols": 36591,
  "total_files": 3117
}
```

---

## Project Management

### List Projects
```http
GET /api/projects
```

**Response:**
```json
{
  "projects": [
    {
      "id": 1,
      "name": "My Project",
      "path": "/Users/username/Projects/myproject",
      "created_at": "2025-10-31 12:00:00",
      "mcps": {
        "memories": "myproject-project_memories",
        "index": "myproject-project_index",
        "profile": "myproject-project_profile",
        "docs": "myproject-knowledge_docs",
        "structure": "myproject-code_structure"
      }
    }
  ]
}
```

---

### Create Project
```http
POST /api/projects
Content-Type: application/json

{
  "name": "My Project",
  "path": "/Users/username/Projects/myproject",
  "description": "My awesome project"
}
```

**Response:**
```json
{
  "success": true,
  "project_id": 1,
  "name": "My Project",
  "mcps_created": ["memories", "index", "profile", "docs", "structure"]
}
```

---

### Get Project
```http
GET /api/projects/{id}
```

**Response:**
```json
{
  "id": 1,
  "name": "My Project",
  "path": "/Users/username/Projects/myproject",
  "description": "My awesome project",
  "created_at": "2025-10-31 12:00:00",
  "mcps": {
    "memories": "myproject-project_memories",
    "index": "myproject-project_index",
    "profile": "myproject-project_profile",
    "docs": "myproject-knowledge_docs",
    "structure": "myproject-code_structure"
  }
}
```

---

### Get Project MCPs
```http
GET /api/projects/{id}/mcps
```

**Response:**
```json
{
  "project_id": 1,
  "mcps": {
    "memories": {
      "name": "myproject-project_memories",
      "document_count": 42,
      "status": "active"
    },
    "index": {
      "name": "myproject-project_index",
      "document_count": 3100,
      "status": "active"
    },
    "structure": {
      "name": "myproject-code_structure",
      "document_count": 1,
      "status": "active"
    }
  }
}
```

---

### Set KB Folders
```http
POST /api/projects/{id}/folders
Content-Type: application/json

{
  "memories": "/docs/memories",
  "docs": "/docs"
}
```

---

### Get KB Folders
```http
GET /api/projects/{id}/folders
```

---

### Ingest Document into Project
```http
POST /api/projects/{id}/ingest-document
Content-Type: multipart/form-data

mcp_type=docs
file=@/path/to/document.md
```

**MCP Types:** `memories`, `index`, `profile`, `docs`, `structure`

---

### Delete Project
```http
DELETE /api/projects/{id}
```

**Response:**
```json
{
  "success": true,
  "message": "Project and all associated knowledge bases deleted"
}
```

---

## Hooks System

### Enable Hook
```http
POST /api/projects/{id}/hooks/{mcp_type}/enable
Content-Type: application/json

{
  "folder_path": "/docs"
}
```

**MCP Types:** `memories`, `index`, `profile`, `docs`

**Response:**
```json
{
  "success": true,
  "message": "Hook enabled for {mcp_type}",
  "folder_path": "/docs"
}
```

---

### Disable Hook
```http
POST /api/projects/{id}/hooks/{mcp_type}/disable
```

**Response:**
```json
{
  "success": true,
  "message": "Hook disabled for {mcp_type}"
}
```

---

### Manual Sync
```http
POST /api/projects/{id}/hooks/sync
Content-Type: application/json

{
  "mcp_type": "docs"
}
```

**Response:**
```json
{
  "success": true,
  "files_synced": 15,
  "files_added": 3,
  "files_updated": 12
}
```

---

### Get Hook Status
```http
GET /api/projects/{id}/hooks
```

**Response:**
```json
{
  "project_id": 1,
  "hooks": {
    "memories": {
      "enabled": true,
      "folder_path": "/docs/memories",
      "last_sync": "2025-10-31 12:00:00"
    },
    "docs": {
      "enabled": true,
      "folder_path": "/docs",
      "last_sync": "2025-10-31 11:45:00"
    }
  }
}
```

---

## File Watcher

### Start Watcher
```http
POST /api/watcher/start/{project_id}
```

**Response:**
```json
{
  "success": true,
  "project_id": 1,
  "watching_folders": ["/docs", "/docs/memories"],
  "status": "active"
}
```

---

### Stop Watcher
```http
POST /api/watcher/stop/{project_id}
```

**Response:**
```json
{
  "success": true,
  "project_id": 1,
  "status": "stopped"
}
```

---

### Restart Watcher
```http
POST /api/watcher/restart/{project_id}
```

---

### Get Watcher Status
```http
GET /api/watcher/status
```

**Response:**
```json
{
  "active_watchers": [
    {
      "project_id": 1,
      "project_name": "My Project",
      "folders": ["/docs", "/docs/memories"],
      "files_watched": 42,
      "status": "active"
    }
  ],
  "total_watchers": 1
}
```

---

## Authentication

### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your-password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

---

### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2025-10-31 12:00:00"
}
```

---

### Check Auth Status
```http
GET /api/auth/status
```

**Response:**
```json
{
  "auth_enabled": true,
  "require_login": true
}
```

---

## Utilities

### List Ollama Models
```http
GET /api/ollama/models
```

**Response:**
```json
{
  "models": [
    {
      "name": "llama3.2:latest",
      "size": "4.7GB",
      "modified_at": "2025-10-31 12:00:00"
    }
  ]
}
```

---

### Browse Directory
```http
GET /api/browse-directory?path=/Users/username/Projects
```

**Response:**
```json
{
  "path": "/Users/username/Projects",
  "directories": [
    {
      "name": "myproject",
      "path": "/Users/username/Projects/myproject",
      "size": 1048576
    }
  ],
  "files": [
    {
      "name": "README.md",
      "path": "/Users/username/Projects/README.md",
      "size": 2048
    }
  ]
}
```

---

## Health Check

### System Health
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-31T12:00:00",
  "components": {
    "sqlite": {
      "status": "healthy",
      "connected": true,
      "database": "claude-os.db",
      "tables": 15,
      "knowledge_bases": 10
    },
    "ollama": {
      "status": "healthy",
      "connected": true,
      "models": 3,
      "host": "http://localhost:11434"
    },
    "redis": {
      "status": "healthy",
      "connected": true,
      "host": "localhost",
      "port": 6379
    }
  }
}
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (authentication required)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error

---

## Rate Limiting

Currently no rate limiting is implemented. May be added in future versions.

---

## Pagination

For endpoints that return large lists (projects, documents), pagination is not yet implemented.
All results are returned in a single response.

---

## WebSocket Support

WebSocket support for real-time updates is planned but not yet implemented.

---

## Examples

### Complete Hybrid Indexing Workflow

```bash
# 1. Create structure KB
curl -X POST http://localhost:8051/api/kb \
  -H "Content-Type: application/json" \
  -d '{
    "name": "myproject-code_structure",
    "kb_type": "generic",
    "description": "Structural index"
  }'

# 2. Run Phase 1 (structural - FAST!)
curl -X POST http://localhost:8051/api/kb/myproject-code_structure/index-structural \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "/Users/username/Projects/myproject",
    "token_budget": 2048
  }'

# 3. Create index KB
curl -X POST http://localhost:8051/api/kb \
  -H "Content-Type: application/json" \
  -d '{
    "name": "myproject-project_index",
    "kb_type": "generic",
    "description": "Semantic index"
  }'

# 4. Run Phase 2 (semantic - selective)
curl -X POST http://localhost:8051/api/kb/myproject-project_index/index-semantic \
  -H "Content-Type: application/json" \
  -d '{
    "project_path": "/Users/username/Projects/myproject",
    "selective": true,
    "code_structure_kb": "myproject-code_structure"
  }'

# 5. Get repo map for Claude's context
curl "http://localhost:8051/api/kb/myproject-code_structure/repo-map?token_budget=1024"
```

---

## Support

For issues, questions, or contributions:
- GitHub: https://github.com/brobertsaz/claude-os/issues
- Documentation: https://github.com/brobertsaz/claude-os/tree/main/docs

---

**Last Updated:** 2025-10-31
**API Version:** 1.0
