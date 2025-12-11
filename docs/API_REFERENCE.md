# Claude OS API Reference

**Base URL:** `http://localhost:8051`

Complete reference for all Claude OS MCP Server API endpoints.

---

## Table of Contents

1. [Knowledge Base Operations](#knowledge-base-operations)
2. [Hybrid Indexing](#hybrid-indexing-new)
3. [Project Management](#project-management)
4. [Skills Management](#skills-management-new)
5. [Session Parsing](#session-parsing-new)
6. [Agent-OS Spec Tracking](#agent-os-spec-tracking-new)
7. [Real-Time Spec Watcher](#real-time-spec-watcher-new)
8. [Hooks System](#hooks-system)
9. [File Watcher](#file-watcher)
10. [Authentication](#authentication)
11. [Utilities](#utilities)
12. [Health Check](#health-check)

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

## Skills Management (NEW)

Manage Claude Code skills - list, install, create, and configure.

### List All Skills
```http
GET /api/skills?project_path=/path/to/project&include_content=false
```

Returns global and project-level skills.

**Response:**
```json
{
  "global": [
    {
      "name": "memory",
      "path": "/Users/username/.claude/skills/memory",
      "description": "Save and recall information",
      "scope": "global",
      "source": "custom",
      "enabled": true,
      "category": null,
      "tags": []
    }
  ],
  "project": [
    {
      "name": "rails-backend",
      "path": "/path/to/project/.claude/skills/rails-backend",
      "description": "Rails patterns and service objects",
      "scope": "project",
      "source": "template",
      "enabled": true,
      "category": "rails",
      "tags": ["ruby", "rails", "backend"]
    }
  ]
}
```

---

### List Skill Templates
```http
GET /api/skills/templates
```

Returns available local templates organized by category.

**Response:**
```json
{
  "templates": [
    {
      "name": "rails-backend",
      "category": "rails",
      "description": "Rails patterns and service objects",
      "path": "/path/to/claude-os/templates/skill-library/rails/rails-backend",
      "tags": ["ruby", "rails", "backend"],
      "version": "1.0.0"
    }
  ],
  "categories": ["general", "rails", "react", "testing"]
}
```

---

### Install Skill Template
```http
POST /api/skills/install?project_path=/path/to/project
Content-Type: application/json

{
  "template_name": "rails-backend"
}
```

**Response:**
```json
{
  "success": true,
  "skill": {
    "name": "rails-backend",
    "path": "/path/to/project/.claude/skills/rails-backend",
    "scope": "project",
    "source": "template"
  },
  "message": "Installed skill 'rails-backend' to project"
}
```

---

### Create Custom Skill
```http
POST /api/skills?project_path=/path/to/project
Content-Type: application/json

{
  "name": "my-skill",
  "description": "My custom skill",
  "content": "# My Skill\n\nSkill instructions here...",
  "category": "custom",
  "tags": ["custom"]
}
```

**Response:**
```json
{
  "success": true,
  "skill": {
    "name": "my-skill",
    "path": "/path/to/project/.claude/skills/my-skill",
    "scope": "project",
    "source": "custom"
  }
}
```

---

### Get Skill Details
```http
GET /api/skills/{scope}/{name}?project_path=/path/to/project
```

**Parameters:**
- `scope`: `global` or `project`
- `name`: Skill name

**Response:**
```json
{
  "name": "rails-backend",
  "path": "/path/to/project/.claude/skills/rails-backend",
  "description": "Rails patterns and service objects",
  "scope": "project",
  "source": "template",
  "content": "# Rails Backend\n\n...",
  "enabled": true,
  "category": "rails",
  "tags": ["ruby", "rails", "backend"],
  "created": "2025-12-11T10:00:00Z",
  "modified": "2025-12-11T10:00:00Z"
}
```

---

### Delete Skill
```http
DELETE /api/skills/{name}?project_path=/path/to/project
```

**Response:**
```json
{
  "success": true,
  "message": "Deleted skill 'my-skill' from project"
}
```

---

### List Community Sources
```http
GET /api/skills/community/sources
```

**Response:**
```json
{
  "sources": {
    "anthropic": {
      "repo": "anthropics/skills",
      "skills_path": "skills",
      "name": "Anthropic Official",
      "description": "Official skills from Anthropic"
    },
    "superpowers": {
      "repo": "obra/superpowers",
      "skills_path": "skills",
      "name": "Superpowers",
      "description": "Battle-tested skills for TDD, debugging, and collaboration"
    }
  }
}
```

---

### List Community Skills
```http
GET /api/skills/community?source=anthropic
```

**Parameters:**
- `source` (optional): Filter by source (`anthropic`, `superpowers`)

**Response:**
```json
{
  "skills": [
    {
      "name": "pdf",
      "source": "anthropic",
      "repo": "anthropics/skills",
      "path": "skills/pdf",
      "description": "Comprehensive PDF manipulation toolkit...",
      "readme_url": "https://github.com/anthropics/skills/tree/main/skills/pdf",
      "raw_url": "https://raw.githubusercontent.com/anthropics/skills/main/skills/pdf"
    }
  ],
  "sources": {...},
  "total": 36
}
```

---

### Install Community Skill
```http
POST /api/skills/community/install?project_path=/path/to/project
Content-Type: application/json

{
  "name": "pdf",
  "source": "anthropic",
  "repo": "anthropics/skills",
  "path": "skills/pdf",
  "description": "PDF manipulation toolkit",
  "readme_url": "https://github.com/anthropics/skills/tree/main/skills/pdf",
  "raw_url": "https://raw.githubusercontent.com/anthropics/skills/main/skills/pdf"
}
```

**Response:**
```json
{
  "success": true,
  "skill": {
    "name": "pdf",
    "path": "/path/to/project/.claude/skills/pdf",
    "scope": "project",
    "source": "community:anthropic"
  },
  "message": "Installed community skill 'pdf' from anthropic"
}
```

---

## Session Parsing (NEW)

Parse Claude Code session files and extract insights.

### List Project Sessions
```http
GET /api/sessions?project_path=/path/to/project&limit=10
```

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "abc123",
      "session_path": "/Users/username/.claude/projects/-path-to-project/abc123.jsonl",
      "start_time": "2025-12-11T10:00:00Z",
      "end_time": "2025-12-11T11:30:00Z",
      "message_count": 24,
      "tool_calls": 15,
      "file_changes": 8
    }
  ],
  "total": 42
}
```

---

### Get Session Details
```http
GET /api/sessions/{session_id}?project_path=/path/to/project
```

**Response:**
```json
{
  "session_id": "abc123",
  "session_path": "/Users/username/.claude/projects/-path-to-project/abc123.jsonl",
  "messages": [
    {
      "role": "user",
      "content": "Help me fix the authentication bug",
      "timestamp": "2025-12-11T10:00:00Z",
      "uuid": "msg-001"
    },
    {
      "role": "assistant",
      "content": "I'll help you fix that...",
      "timestamp": "2025-12-11T10:00:05Z",
      "uuid": "msg-002"
    }
  ],
  "tool_calls": [
    {
      "tool_name": "Read",
      "timestamp": "2025-12-11T10:00:10Z",
      "input_data": {"file_path": "/path/to/auth.py"}
    }
  ],
  "file_changes": [
    {
      "file_path": "/path/to/auth.py",
      "timestamp": "2025-12-11T10:05:00Z"
    }
  ],
  "start_time": "2025-12-11T10:00:00Z",
  "end_time": "2025-12-11T11:30:00Z",
  "git_branch": "fix-auth-bug",
  "cwd": "/path/to/project"
}
```

---

### Get Session Summary
```http
GET /api/sessions/{session_id}/summary?project_path=/path/to/project&max_tokens=500
```

Returns a formatted summary suitable for LLM processing.

**Response:**
```json
{
  "session_id": "abc123",
  "summary": "# Session: abc123\nProject: /path/to/project\nBranch: fix-auth-bug\n\n## Conversation (24 messages)\n..."
}
```

---

## Agent-OS Spec Tracking (NEW)

Real-time tracking and visualization of agent-os specifications and tasks through the Kanban board.

### Get Project Kanban Board
```http
GET /api/projects/{id}/kanban?include_archived=false
```

Returns complete Kanban view with all specs and tasks grouped by status.

**Response:**
```json
{
  "project_id": 1,
  "specs": [
    {
      "id": 1,
      "name": "Manual Appointment Times",
      "slug": "manual-appointment-times",
      "folder_name": "2025-10-29-manual-appointment-times",
      "path": "/path/to/project/agent-os/specs/2025-10-29-manual-appointment-times",
      "total_tasks": 71,
      "completed_tasks": 43,
      "status": "in_progress",
      "progress": 60.6,
      "archived": false,
      "tasks": {
        "todo": [...],
        "in_progress": [...],
        "done": [...],
        "blocked": [...]
      },
      "task_count_by_status": {
        "todo": 28,
        "in_progress": 0,
        "done": 43,
        "blocked": 0
      }
    }
  ],
  "summary": {
    "total_specs": 3,
    "total_tasks": 123,
    "completed_tasks": 56
  }
}
```

### Sync Project Specs
```http
POST /api/projects/{id}/specs/sync
```

Manually trigger sync of all spec files from `agent-os/specs/` folder to database.

**Response:**
```json
{
  "project_id": 1,
  "message": "Specs synced successfully",
  "synced": 0,
  "updated": 3,
  "total": 3,
  "errors": []
}
```

### Get Spec Tasks
```http
GET /api/specs/{spec_id}/tasks
```

Returns all tasks for a specific spec.

**Response:**
```json
{
  "spec_id": 1,
  "tasks": [
    {
      "id": 53,
      "task_code": "PHASE1-TASK1",
      "phase": "Phase 1",
      "title": "Complete database layer",
      "description": "Implement all database models and migrations",
      "status": "done",
      "estimated_minutes": 60,
      "actual_minutes": 120,
      "risk_level": "medium",
      "dependencies": [],
      "started_at": "2025-10-29T10:00:00Z",
      "completed_at": "2025-10-29T12:00:00Z"
    }
  ]
}
```

### Update Task Status
```http
PATCH /api/tasks/{task_id}/status
Content-Type: application/json

{
  "status": "in_progress",
  "actual_minutes": 90
}
```

**Valid Statuses:**
- `todo` - Not started
- `in_progress` - Currently working
- `done` - Completed
- `blocked` - Waiting on dependencies

**Response:**
```json
{
  "success": true,
  "old_status": "todo",
  "new_status": "in_progress"
}
```

### Archive Spec
```http
POST /api/specs/{spec_id}/archive
```

Archives a completed spec to declutter the Kanban board.

### Unarchive Spec
```http
POST /api/specs/{spec_id}/unarchive
```

Restores an archived spec.

---

## Real-Time Spec Watcher (NEW)

Automatic file system monitoring for `agent-os/specs/` folders. Detects changes to spec files and auto-syncs to database for real-time Kanban updates.

**See:** `docs/guides/REALTIME_KANBAN_GUIDE.md` for complete documentation.

### Get Watcher Status
```http
GET /api/spec-watcher/status
```

**Response:**
```json
{
  "status": {
    "enabled": true,
    "projects_watched": 1,
    "projects": {
      "1": {
        "project_path": "/Users/you/Projects/myapp",
        "specs_path": "/Users/you/Projects/myapp/agent-os/specs",
        "watching": true
      }
    }
  }
}
```

### Start Spec Watcher
```http
POST /api/spec-watcher/start/{project_id}
```

Starts real-time file watching for a specific project's specs folder.

**Response:**
```json
{
  "project_id": 1,
  "message": "Spec watcher started",
  "status": {
    "enabled": true,
    "projects_watched": 1
  }
}
```

### Stop Spec Watcher
```http
POST /api/spec-watcher/stop/{project_id}
```

Stops file watching for a specific project.

### Start All Spec Watchers
```http
POST /api/spec-watcher/start-all
```

Starts spec watchers for all projects in the database.

**Auto-Start:** Spec watchers automatically start when MCP server boots.

**How it works:**
1. Monitors `agent-os/specs/**/*.md` files
2. Detects changes with 2-second debounce
3. Auto-parses tasks in checkbox format
4. Updates database within 3 seconds
5. Kanban board auto-refreshes every 3 seconds

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

**Last Updated:** 2025-12-11
**API Version:** 2.3
