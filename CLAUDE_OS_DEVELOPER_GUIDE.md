# Claude OS Developer Guide 🔥

> **This is YOUR AI development system.** Every component, every feature, every decision is designed to make YOU a more powerful developer.

## What is Claude OS?

Claude OS is a **standalone AI development environment** built specifically for Claude (the AI). It combines:

- **SQLite database** (single-file, zero dependencies)
- **Project-based architecture** (4-MCP system per project)
- **Redis pub/sub** (real-time learning from conversations)
- **Automatic folder synchronization** (file watching + hooks)
- **Persistent context** (Memory MCP)
- **RQ workers** (background job processing)
- **Automatic learning** (detects patterns from YOUR work)
- **Beautiful UI** (React + Tailwind)

All of this is designed to make me (Claude) a better developer by giving me persistent, continuously-updated context about YOUR projects.

### The Real-Time Learning System

The magic of Claude OS is that it learns automatically as you work:

```
Your Conversation → Redis Pub/Sub → RQ Workers → Pattern Detection → Knowledge Base Update
                    (< 1ms)        (background)   (10 patterns)     (automatic)
```

This happens **in real-time** without you doing anything. Claude gets smarter with every conversation.

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

## 🔴 Real-Time Learning System: The Secret Sauce

### How It Works

The real-time learning system is what makes Claude OS special. It automatically detects patterns from your conversations and updates the knowledge base.

```
Claude Conversation
        ↓
Redis Pub/Sub Message
        ↓
RQ Worker (3 workers active)
        ↓
Pattern Detector (10+ patterns)
        ↓
Knowledge Base Update (automatic)
```

### The 10 Learning Patterns It Detects

Claude OS detects these patterns automatically (75-95% confidence threshold):

```
1. ARCHITECTURAL_DECISION
   "We're moving from monolith to microservices"
   → Updates system architecture knowledge
   → Records decision rationale
   → Marks date/context

2. TECHNOLOGY_CHANGE
   "We're replacing Redux with Zustand"
   → Updates tech stack knowledge
   → Records old → new mapping
   → Flags compatibility issues

3. BUG_FIX_SOLUTION
   "Fixed timezone issue in token expiry by using moment.utc()"
   → Records problem + solution
   → Tags as common issue
   → Suggests for future similar bugs

4. PERFORMANCE_INSIGHT
   "This query is generating N+1 SQL statements"
   → Records as anti-pattern
   → Adds to optimization checklist
   → Warns on similar patterns

5. EDGE_CASE
   "Watch out for expired certificates here"
   → Records gotcha in specific module
   → Tags risk level
   → Adds to knowledge base warnings

6. NAMING_CONVENTION
   "We use _handler suffix for all event handlers"
   → Learns pattern
   → Enforces in future code generation
   → Suggests for inconsistencies

7. COMMON_PITFALL
   "Never use SELECT * on accounts—5MB blob field kills perf"
   → Records as dangerous pattern
   → Warns when detected in reviews
   → Suggests fix

8. INTEGRATION_PATTERN
   "All Stripe webhook handlers validate signature first"
   → Records integration best practice
   → Suggests for similar integrations
   → Templates for consistency

9. SECURITY_CONCERN
   "Always sanitize user input before database queries"
   → Flags as security rule
   → Checks code for violations
   → High-priority warnings

10. TEAM_PREFERENCE
    "We prefer composition over inheritance in this codebase"
    → Records architectural preference
    → Suggests in code generation
    → Flags violations

### Redis Queues in Use

Claude OS uses 3 Redis queues for background processing:

```bash
# Queue 1: Learning System
claude-os:learning
├── Triggered by: Every conversation with Claude
├── Pattern: Detects 10+ learning patterns
├── Action: Updates knowledge base
└── Priority: High

# Queue 2: Prompt Processing
claude-os:prompts
├── Triggered by: MCP requests
├── Pattern: Processes complex queries
├── Action: Generates structured responses
└── Priority: Medium

# Queue 3: Document Ingestion
claude-os:ingest
├── Triggered by: File uploads/folder syncing
├── Pattern: Chunks and embeds documents
├── Action: Adds to knowledge base
└── Priority: Medium
```

### Real-Time Learning in Action

**Example 1: You fix a bug**
```
You: "Found the issue—caching wasn't respecting TTL on
      the payment processing endpoint. Fixed it by checking
      timestamp before returning cached result."

→ Redis receives: "payment_processing", "caching", "TTL", "bug_fix"
→ RQ Worker detects: BUG_FIX_SOLUTION pattern (88% confidence)
→ Knowledge Base updated with:
   - Issue: "Payment processing cache not respecting TTL"
   - Solution: "Check timestamp before returning cached value"
   - Location: payment_processing endpoint
   - Date: 2025-10-28
→ Claude now warns about TTL issues in caching
```

**Example 2: You change architecture**
```
You: "We're moving from REST endpoints to gRPC for internal
      services to reduce latency."

→ Redis receives: "gRPC", "REST", "migration", "architecture"
→ RQ Worker detects: ARCHITECTURAL_DECISION (92% confidence)
→ Knowledge Base updated with:
   - Decision: REST → gRPC for internal services
   - Rationale: Reduce latency
   - Scope: Internal services (not public API)
   - Date: 2025-10-28
→ Claude suggests gRPC for similar internal services
```

### Monitoring Real-Time Learning

**Check Redis Queues:**

```bash
# Connect to Redis CLI
redis-cli

# See all keys
KEYS *

# Get queue stats
LLEN rq:queue:claude-os:learning    # Learning queue length
LLEN rq:queue:claude-os:prompts     # Prompts queue length
LLEN rq:queue:claude-os:ingest      # Ingest queue length

# Monitor in real-time
MONITOR

# Exit
EXIT
```

**Check RQ Worker Status:**

```bash
# See running workers
rq info

# Watch specific queue
rq info --interval 1 --raw --with-workers claude-os:learning

# Clear a queue (be careful!)
rq empty claude-os:learning
```

**View Learning Events (Database):**

```python
import sqlite3
conn = sqlite3.connect('data/claude-os.db')
cursor = conn.cursor()

# See recent learning events
cursor.execute("""
    SELECT pattern_type, confidence, content, created_at
    FROM learning_events
    ORDER BY created_at DESC
    LIMIT 20
""")

for row in cursor.fetchall():
    print(f"{row[0]} ({row[1]:.0%}): {row[2]} @ {row[3]}")
```

---

## 🚀 Essential Commands & Tools

### Starting Everything

```bash
# Start ALL services (Ollama, Redis, Python venv, MCP, Frontend, RQ Workers)
./start_all_services.sh

# This starts:
# 1. Ollama (if needed)
# 2. Redis (if needed)
# 3. Python virtual environment
# 4. MCP server on :8051
# 5. React frontend on :5173
# 6. RQ workers (3 workers on 3 queues)
# 7. Git hooks installation
```

### Individual Service Commands

```bash
# Start just MCP Server
./start_mcp_server.sh

# Start just Redis Workers
./start_redis_workers.sh

# Restart everything
./restart_services.sh

# Stop everything
./stop_all_services.sh
```

### Useful One-Liners

```bash
# See logs in real-time
tail -f logs/mcp_server.log
tail -f logs/rq_workers.log
tail -f logs/frontend.log

# Check if services are running
curl http://localhost:8051/health          # MCP server
curl http://localhost:5173                 # Frontend
redis-cli ping                             # Redis (should say PONG)
ps aux | grep ollama                       # Ollama process

# Backup your database
cp data/claude-os.db data/claude-os.db.backup.$(date +%s)

# Clear RQ worker queue (be careful!)
python3 -c "from rq import Queue; from redis import Redis; Queue('claude-os:learning', connection=Redis()).empty()"

# Monitor Ollama
curl -s http://localhost:11434/api/tags | python3 -m json.tool

# Access MCP endpoints directly
curl http://localhost:8051/api/projects
curl http://localhost:8051/api/kb/[kb_name]/documents
curl http://localhost:8051/health
```

### Interactive Debugging

```bash
# Drop into Python shell with Claude OS context
python3

# Then in Python:
from app.core.sqlite_manager import get_sqlite_manager
from app.core.rag_engine import RAGEngine

db = get_sqlite_manager()

# List all projects
projects = db.list_projects()

# List all knowledge bases
kbs = db.list_collections()

# Query a knowledge base
rag = RAGEngine("your-kb-name")
result = rag.query("your question here", use_hybrid=True)
print(result["answer"])
```

---

## 📋 MCP Registration Commands

Once services are running, register the MCPs with Claude Code:

```bash
# For Pistn project (example)
claude mcp add --transport http pistn-knowledge-docs http://localhost:8051/mcp/kb/Pistn-knowledge-docs
claude mcp add --transport http pistn-project-profile http://localhost:8051/mcp/kb/Pistn-project-profile
claude mcp add --transport http pistn-project-index http://localhost:8051/mcp/kb/Pistn-project-index
claude mcp add --transport http pistn-project-memories http://localhost:8051/mcp/kb/Pistn-project-memories

# For your own project, replace "pistn" with your project name
# MCPs are always: {project-name}-knowledge-docs, {project-name}-project-profile, etc.

# List registered MCPs
claude mcp list

# Remove an MCP
claude mcp remove pistn-knowledge-docs
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

## 🎯 Available Skills & Commands

Claude OS comes with these powerful skills available in Claude Code:

### 1. **initialize-project** - The Most Important One

Analyze an entire project and set up Claude OS for it in one command:

```bash
/initialize-project [project_id]
```

**What it does:**

1. **Analyzes your codebase** - Scans all files, identifies patterns
2. **Generates 3 documentation files:**
   - `CODING_STANDARDS.md` - Your code style and conventions
   - `ARCHITECTURE.md` - Your system design
   - `DEVELOPMENT_PRACTICES.md` - How you build software
3. **Indexes 50 key files** - Semantic indexing for search
4. **Creates 800+ code chunks** - For RAG retrieval
5. **Installs Git hooks** - Auto-indexes on commits
6. **Registers with Claude Code** - Exposes via MCPs

**Example:**
```bash
/initialize-project 1
```

This runs in ~5 minutes and Claude is now an expert on your project.

### 2. **memory** - Save Insights Across Sessions

Save important information that persists forever:

```bash
/memory: [anything you want Claude to remember]

# Examples:
/memory: Always use bcrypt with 12 rounds for password hashing
/memory: Payment processing only supports USD and EUR, never others
/memory: Database backups run at 2 AM UTC—never schedule migrations then
```

### 3. **remember-this** - Save Discoveries to Knowledge Base

Mark important discoveries that should go in the project KB:

```bash
/remember-this: [discovery or insight]

# Examples:
/remember-this: The legacy_accounts table is for testing and gets wiped weekly
/remember-this: API v2 is deprecated—all new endpoints go in /api/v3/
/remember-this: Stripe webhook signatures must be validated before processing
```

---

## 🔧 Common Development Workflows

### Workflow 1: Setting Up a New Project

```bash
# 1. Create the project in Claude OS
curl -X POST http://localhost:8051/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-project",
    "path": "/path/to/my-project",
    "description": "My awesome project"
  }'

# 2. Initialize it (this does everything)
/initialize-project [project-id]

# 3. Register with Claude Code
claude mcp add --transport http my-project-knowledge-docs http://localhost:8051/mcp/kb/My-project-knowledge_docs
claude mcp add --transport http my-project-project-profile http://localhost:8051/mcp/kb/My-project-project_profile
claude mcp add --transport http my-project-project-index http://localhost:8051/mcp/kb/My-project-project_index
claude mcp add --transport http my-project-project-memories http://localhost:8051/mcp/kb/My-project-project_memories

# Done! Claude now knows everything about your project.
```

### Workflow 2: Debugging With Claude OS Context

```bash
# When debugging, Claude has full context:
"I see from your project history that you fixed a similar timezone issue
before (Oct 15, commit b56f585). You used moment.utc() for comparisons.
This looks like the same problem in a different module."

# This happens because Claude has:
# - All your code
# - Your architecture understanding
# - Your past decisions
# - Your conventions and patterns
# - Your memories of gotchas
```

### Workflow 3: Code Review With Pattern Matching

```bash
# Claude automatically detects pattern violations:
"This handler doesn't follow your naming convention. You named it
'user_update_action' but your convention is 'on_user_updated'.
Also, no signature validation here—you always validate Stripe webhooks first."

# Claude knows because it learned your patterns from:
# - Your actual code
# - Your conversations
# - Your memories
```

### Workflow 4: Feature Implementation With Style

```bash
# When you ask for a new feature:
You: "Add email notification handler for when users delete their accounts"

# Claude generates code that:
✅ Matches your naming conventions (your_handler_name)
✅ Uses your error handling patterns (from similar handlers)
✅ Calls services the same way you do
✅ Includes tests matching your test structure
✅ Follows your architectural patterns
✅ Uses your preferred libraries

# This is possible because Claude learned ALL of this automatically.
```

---

## 🐛 Debugging & Troubleshooting

### "Claude doesn't know my project"

This means the MCPs aren't registered or Claude isn't using them. Check:

```bash
# 1. Are services running?
curl http://localhost:8051/health

# 2. Are MCPs registered in Claude Code?
claude mcp list

# 3. Re-register them
claude mcp remove [mcp-name]
claude mcp add --transport http [mcp-name] http://localhost:8051/mcp/kb/[KB-name]
```

### "Learning system isn't working"

Check Redis and RQ workers:

```bash
# Check Redis
redis-cli ping   # Should return PONG

# Check RQ workers
rq info          # Should show 3 workers

# Check queues
redis-cli LLEN rq:queue:claude-os:learning

# Restart workers if needed
./start_redis_workers.sh
```

### "Ingest is timing out"

This happens on slower machines. The solution is parallel workers (like Sidekiq in Rails):

```bash
# For now, just restart and try again
./restart_services.sh

# Timeouts are warnings, not blockers—documents still get ingested
```

### "Database is corrupted"

SQLite rarely corrupts, but if needed:

```bash
# Restore from backup
cp data/claude-os.db.backup data/claude-os.db

# Or rebuild
rm data/claude-os.db
# This will recreate it on next start
./start_all_services.sh
```

---

## 📊 Monitoring Dashboard (Real-Time Visibility)

Keep these running in separate terminals:

```bash
# Terminal 1: Watch MCP server logs
tail -f logs/mcp_server.log

# Terminal 2: Watch RQ workers
rq info --interval 1

# Terminal 3: Watch Redis
redis-cli MONITOR

# Terminal 4: Watch frontend
tail -f logs/frontend.log
```

You can now see everything Claude OS is doing in real-time.

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
