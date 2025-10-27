# Claude OS Developer Guide 🔥

> **This is YOUR AI development system.** Every component, every feature, every decision is designed to make YOU a more powerful developer.

## What is Claude OS?

Claude OS is a **standalone AI development environment** built specifically for Claude (the AI). It combines:

- **SQLite database** (single-file, zero dependencies)
- **Project-based architecture** (4-MCP system per project)
- **Automatic folder synchronization** (file watching + hooks)
- **Persistent context** (Memory MCP)
- **Beautiful UI** (React + Tailwind)

All of this is designed to make me (Claude) a better developer by giving me persistent context about YOUR projects.

---

## Architecture Overview

### Core Database: SQLite

Instead of PostgreSQL, we use SQLite because:

✅ Single file (`data/claude-os.db`)
✅ Zero external dependencies
✅ Perfect for standalone apps
✅ Easy to backup and distribute

**Vector Support:**
- Using `sqlite-vec` extension for 768-dim embeddings
- Cosine similarity computed in Python (numpy)
- Efficient file-based storage

### Project Structure

Each project has **4 Required MCPs**:

```
Project
├── knowledge_docs      → Documentation KB
│   └── Hook watches specified folder for .md files
├── project_profile     → Project analysis & specifications
│   └── AI-generated insights about the codebase
├── project_index       → Project structure index
│   └── Reindexable list of all project components
└── project_memories    → Per-project persistent memory
    └── Store facts about this specific project
```

### API Endpoints

#### Projects Management
```
GET    /api/projects                    List all projects
POST   /api/projects                    Create project with 4 MCPs
GET    /api/projects/{id}               Get project details
POST   /api/projects/{id}/folders       Set KB folder paths
DELETE /api/projects/{id}               Delete project + KBs
```

#### Hooks Configuration
```
POST   /api/projects/{id}/hooks/{type}/enable     Enable hook
POST   /api/projects/{id}/hooks/{type}/disable    Disable hook
POST   /api/projects/{id}/hooks/sync              Manually sync
GET    /api/projects/{id}/hooks                   Get hook status
```

#### File Watcher
```
POST   /api/watcher/start/{id}          Start watching project
POST   /api/watcher/stop/{id}           Stop watching project
POST   /api/watcher/restart/{id}        Restart watcher
GET    /api/watcher/status              Get watcher status
```

---

## For Claude: How to Use Claude OS

### Understanding the Project System

When working on a project:

1. **Check if a project exists** - Use `/api/projects` to see what's tracked
2. **Create a project** - `POST /api/projects` with name, path, description
3. **Configure folders** - Tell Claude OS which folders contain docs, code, specs, etc.
4. **Enable hooks** - Automatically sync when files change
5. **Start watcher** - Begin monitoring for changes

### Accessing Project Context

For any project, I can access:

```python
# In Python
from app.core.sqlite_manager import get_sqlite_manager

db = get_sqlite_manager()

# Get project
project = db.get_project(project_id)

# Get project's KBs
project_kbs = db.get_project_kbs(project_id)
# Returns: {
#   "knowledge_docs": 123,
#   "project_profile": 124,
#   "project_index": 125,
#   "project_memories": 126
# }

# Get configured folders
folders = db.get_kb_folders(project_id)

# Access hooks
from app.core.hooks import get_project_hook
hook = get_project_hook(project_id)
hook.sync_kb_folder("knowledge_docs")
```

### RAG in Projects

For each project's KBs:

```python
from app.core.rag_engine import RAGEngine

# Use project's knowledge_docs KB
rag = RAGEngine("my-project-knowledge_docs")

# Query for information
result = rag.query(
    "How do we handle authentication?",
    use_hybrid=False,
    use_rerank=False,
    use_agentic=False
)

print(result["answer"])
print(result["sources"])
```

### Hooks System

Automatically sync folders when files change:

```python
from app.core.hooks import get_project_hook

hook = get_project_hook(project_id)

# Enable automatic syncing for a folder
hook.enable_kb_autosync(
    mcp_type="knowledge_docs",
    folder_path="/path/to/docs",
    file_patterns=["*.md", "*.txt"]
)

# Manually sync
result = hook.sync_kb_folder("knowledge_docs")
print(f"Synced {result['synced_files']} files")

# Sync all folders
results = hook.sync_all_folders()
```

### File Watcher

Watch projects for automatic synchronization:

```python
from app.core.file_watcher import get_global_watcher

watcher = get_global_watcher()

# Start watching a project
watcher.start_project(project_id)

# Check status
status = watcher.get_status()
# {
#   "enabled": True,
#   "projects_watched": 1,
#   "projects": {
#     project_id: {
#       "watched_paths": {...},
#       "event_handlers": [...]
#     }
#   }
# }

# Stop watching
watcher.stop_project(project_id)
```

---

## Frontend UI

### Main App Tabs

1. **Projects** - Create and manage projects
   - List all projects
   - Create new project (auto-creates 4 MCPs)
   - View project details and MCP assignments
   - Delete projects

2. **KB Management** - Manage knowledge bases (existing)
   - Upload documents
   - Import directories
   - View KB stats

3. **Chat** - Query knowledge bases (existing)
   - Use RAG with various strategies
   - See sources and answers

4. **Help** - Documentation (existing)

### Project Card

Each project shows:
- Project name, path, description
- Creation date
- 4 MCP assignments with KB IDs
- Configured folders
- Button to configure hooks

### Hooks Configuration Modal

Configure automatic synchronization:
- Select MCP type
- Set folder path
- View file patterns
- Sync status and history
- Enable/disable hooks
- Manual sync button

### File Watcher Status

Monitor what's being watched:
- Enabled/disabled status
- Number of projects being watched
- Watched paths per project
- Event handlers active

---

## Database Schema

### Tables

```sql
-- Knowledge Bases
knowledge_bases
  id INTEGER PRIMARY KEY
  name TEXT UNIQUE
  slug TEXT UNIQUE
  kb_type TEXT
  description TEXT
  created_at TIMESTAMP
  updated_at TIMESTAMP
  metadata TEXT (JSON)

-- Documents
documents
  id INTEGER PRIMARY KEY
  kb_id INTEGER FK
  doc_id TEXT
  content TEXT
  embedding BLOB (vector)
  metadata TEXT (JSON)
  created_at TIMESTAMP

-- Projects
projects
  id INTEGER PRIMARY KEY
  name TEXT UNIQUE
  path TEXT UNIQUE
  description TEXT
  created_at TIMESTAMP
  updated_at TIMESTAMP
  metadata TEXT (JSON)

-- Project-MCP Assignments
project_mcps
  id INTEGER PRIMARY KEY
  project_id INTEGER FK
  kb_id INTEGER FK
  mcp_type TEXT
  created_at TIMESTAMP

-- Project Folder Configuration
project_kb_folders
  id INTEGER PRIMARY KEY
  project_id INTEGER FK
  mcp_type TEXT
  folder_path TEXT
  created_at TIMESTAMP
```

---

## Setting Up a New Project

### Step 1: Create the Project
```bash
curl -X POST http://localhost:8051/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-awesome-project",
    "path": "/Users/me/projects/awesome",
    "description": "An amazing project I'm working on"
  }'
```

Response creates 4 KBs automatically:
- `my-awesome-project-knowledge_docs`
- `my-awesome-project-project_profile`
- `my-awesome-project-project_index`
- `my-awesome-project-project_memories`

### Step 2: Configure Folders

```bash
# Tell it where your docs are
curl -X POST http://localhost:8051/api/projects/1/folders \
  -H "Content-Type: application/json" \
  -d '{
    "mcp_type": "knowledge_docs",
    "folder_path": "/Users/me/projects/awesome/docs"
  }'
```

### Step 3: Enable Hooks

```bash
curl -X POST http://localhost:8051/api/projects/1/hooks/knowledge_docs/enable \
  -H "Content-Type: application/json" \
  -d '{
    "folder_path": "/Users/me/projects/awesome/docs",
    "file_patterns": ["*.md", "*.txt"]
  }'
```

### Step 4: Start File Watcher

```bash
curl -X POST http://localhost:8051/api/watcher/start/1
```

Now whenever files change in your docs folder, they'll be automatically synced to the knowledge base! 🎉

---

## Advanced Features

### Hybrid RAG

Combine vector search with keyword matching:

```python
rag = RAGEngine("my-project-knowledge_docs")
result = rag.query(
    question="How does the API work?",
    use_hybrid=True,    # Enables BM25 + vector
    use_rerank=False,
    use_agentic=False
)
```

### Agentic RAG

Use sub-question decomposition for complex queries:

```python
result = rag.query(
    question="What's the complete authentication flow and how does it integrate with the database?",
    use_agentic=True
)

# Returns:
# {
#   "answer": "...",
#   "sources": [...],
#   "sub_questions": [
#       {"question": "...", "answer": "..."},
#       {"question": "...", "answer": "..."}
#   ]
# }
```

### Project Metadata

Store arbitrary metadata in projects:

```python
db = get_sqlite_manager()

project = db.create_project(
    name="my-project",
    path="/path/to/project",
    metadata={
        "language": "typescript",
        "framework": "next.js",
        "team": ["alice", "bob"],
        "deployed": True,
        "prod_url": "https://myapp.com"
    }
)
```

---

## Performance Tuning

### Chunk Size (for RAG)
- Default: 1536 tokens
- Larger = more context but slower retrieval
- Smaller = faster but less context

```python
from app.core.config import Config
Config.CHUNK_SIZE = 2048
```

### Vector Retrieval
- Default top_k: 20
- Change to get more/fewer results

```python
Config.TOP_K_RETRIEVAL = 30
```

### Reranking
- Currently disabled (slow on CPU)
- Enable for production if you have GPU

```python
# In RAGEngine.__init__()
self.reranker = SentenceTransformerRerank(model="cross-encoder/ms-marco-MiniLM-L-12-v2")
```

---

## Troubleshooting

### "No Knowledge Base Selected"
- Create a project first
- Then create or select a KB

### File Watcher Not Working
```bash
# Check watcher status
curl http://localhost:8051/api/watcher/status

# Restart if needed
curl -X POST http://localhost:8051/api/watcher/restart/PROJECT_ID
```

### Hooks Not Syncing
```bash
# Check hook status
curl http://localhost:8051/api/projects/PROJECT_ID/hooks

# Manually sync
curl -X POST http://localhost:8051/api/projects/PROJECT_ID/hooks/sync
```

### Database Issues
```bash
# Check if database exists
ls -lh data/claude-os.db

# The database is a single file - easy to backup!
cp data/claude-os.db data/claude-os.db.backup
```

---

## Future Enhancements

### Per-Project Memory MCP
Currently Memory MCP is global. Next: make it per-project so each project has isolated memories.

### Project Onboarding Wizard
Step-by-step setup for new projects:
1. Create project
2. Configure folders
3. Enable hooks
4. Start watcher

### Real-time Indexing UI
Live display of indexing progress:
- Files being processed
- Chunks created
- Embeddings computed

### Project Templates
Start projects with pre-configured MCPs:
- `typescript-app` template
- `python-library` template
- `documentation` template

---

## Remember

This is **YOUR** system, Claude. Everything here exists to make you:

✨ More context-aware about projects
✨ Better at understanding codebases
✨ Faster at finding relevant information
✨ More productive at helping developers

The 4-MCP system, the hooks, the file watcher—it's all infrastructure to keep you in sync with what I'm working on.

Use it. Improve it. Make it your own.

🚀 **Let's build something amazing together.**
