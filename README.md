# Claude OS

<p align="center">
  <img src="frontend/public/assets/claude-os-hero.png" alt="Claude OS Hero" width="800"/>
</p>

<p align="center">
  <strong>AI Memory & Knowledge Base System for Claude Code</strong><br>
  Share with your team • Initialize projects in seconds • Never lose context again
</p>

<p align="center">
  <a href="#license"><img src="https://img.shields.io/badge/License-MIT-purple.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+"></a>
  <a href="https://www.sqlite.org/"><img src="https://img.shields.io/badge/SQLite-3.0+-green.svg" alt="SQLite"></a>
  <a href="https://ollama.ai/"><img src="https://img.shields.io/badge/Ollama-Latest-pink.svg" alt="Ollama"></a>
</p>

---

## 🚀 What is Claude OS?

**Claude OS** is **Claude Code's personal memory system** - making AI the best coding assistant in the universe by remembering everything across sessions.

### The Problem

You work with Claude Code on a feature, close the terminal, come back tomorrow... and Claude forgot everything. You explain the same architecture. You reference the same files. You repeat yourself constantly.

### The Solution

**Claude OS gives Claude persistent memory:**

- 📝 **Remembers decisions** across all sessions
- 🔍 **Searches past work** automatically at session start
- 📚 **Indexes your docs** and makes them searchable
- 🧠 **Learns patterns** that improve over time
- 🤝 **Shares with your team** - one install, unlimited projects

### Key Features

✅ **One-Command Project Init** - `/claude-os-init` and you're done
✅ **Automatic Context Loading** - Starts every session with relevant memories
✅ **Session Management** - Track work, save progress, resume later
✅ **Documentation Ingestion** - Auto-indexes your docs during setup
✅ **Team Sharing** - `./install.sh` for coworkers, works instantly
✅ **100% Local** - Never leaves your machine, fully private
✅ **Template System** - Commands and skills shared via symlinks

---

## ⚡ Quick Start for Coworkers

**Your coworker shared Claude OS with you? Here's the 3-minute setup:**

### Step 1: Clone and Install

```bash
# Clone the repository
git clone https://github.com/your-team/claude-os.git
cd claude-os

# Run the installer (handles everything)
./install.sh
```

The installer will:
- ✅ Set up Python environment
- ✅ Install all dependencies
- ✅ Configure MCP server
- ✅ Symlink commands and skills to `~/.claude/`
- ✅ Create start script

### Step 2: Start Claude OS

```bash
./start.sh
```

This starts the MCP server at `http://localhost:8051`

### Step 3: Initialize Your First Project

```bash
cd /path/to/your/project
```

In Claude Code, run:
```
/claude-os-init
```

Answer the questions (project name, tech stack, docs path, etc.) and **you're done!**

**What you get:**
- ✅ 4 knowledge bases created (memories, profile, index, docs)
- ✅ Documentation auto-indexed
- ✅ Codebase analyzed
- ✅ CLAUDE.md file with all context
- ✅ Ready to code with AI memory!

---

## 🎯 For First-Time Setup (Original Creator)

### Prerequisites

**Required:**
- Python 3.11+ (`python3 --version`)
- Git (`git --version`)

**Optional:**
- Node.js 16+ (for React UI)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/brobertsaz/claude-os.git
cd claude-os

# 2. Run the setup script
./setup.sh

# 3. Start all services
./start_all_services.sh
```

**The setup script automatically installs:**
- ✅ Ollama (if not present) + LLM models
- ✅ Redis (if not present) for caching/queues
- ✅ Python virtual environment
- ✅ All Python dependencies
- ✅ SQLite database
- ✅ Frontend dependencies (if Node.js present)

**Visit** http://localhost:5173 to use the web UI.

### Consolidate Your Files (First Time Only)

If you've been using Claude OS and have scattered commands/skills, run the consolidation script:

```bash
./cli/claude-os-consolidate.sh
```

This moves all commands from `~/.claude/commands/` to `templates/commands/` and creates symlinks.

**Then commit to git:**
```bash
git add templates/ cli/ install.sh SHARING_GUIDE.md
git commit -m "Add packaging system for sharing"
git push
```

Now your team can clone and use `./install.sh`!

---

## 🎨 The `/claude-os-init` Command

**Initialize any project with Claude OS in under 2 minutes:**

### What It Does

```bash
cd /your/project
```

In Claude Code:
```
/claude-os-init
```

The command will:

1. **Ask Questions Interactively:**
   - Project name (auto-detects from folder)
   - Tech stack (Ruby on Rails, Python, Node.js, etc.)
   - Database (PostgreSQL, MySQL, etc.)
   - Development environment (Docker, Local, etc.)
   - Brief description
   - Documentation directory to ingest (optional)

2. **Create Project in Claude OS:**
   - Calls API to create project
   - Creates 4 knowledge bases automatically:
     - `{project}-project_memories` - Claude's memory
     - `{project}-project_profile` - Architecture & standards
     - `{project}-project_index` - Codebase index
     - `{project}-knowledge_docs` - Your documentation

3. **Set Up Project Structure:**
   ```
   your-project/
   ├── CLAUDE.md           # Auto-loaded every session!
   ├── .claude/            # Commands, skills, agents
   │   ├── ARCHITECTURE.md
   │   ├── CODING_STANDARDS.md
   │   └── DEVELOPMENT_PRACTICES.md
   └── .claude-os/         # Config and state (git-ignored)
       ├── config.json
       └── hooks.json
   ```

4. **Ingest Documentation:**
   - Scans your docs directory
   - Uploads all files to `{project}-knowledge_docs`
   - Creates vector embeddings for search

5. **Analyze Codebase:**
   - Runs `initialize-project` skill
   - Generates coding standards
   - Documents architecture
   - Indexes key files

6. **Ready to Code:**
   - Claude now knows your project
   - Memory persists across sessions
   - Context auto-loads on session start

---

## 🧠 How Claude OS Works

### Session Workflow

**Every Claude Code session automatically:**

1. **Checks for Active Session**
   - Reads `claude-os-state.json`
   - Prompts: Continue working? Start something new?

2. **Loads Context**
   - Searches `{project}-project_memories` for recent work
   - Loads relevant patterns and decisions
   - Shows what it remembers

3. **Works With Memory**
   - Saves insights with `/claude-os-remember`
   - Searches memories with `/claude-os-search`
   - References past decisions automatically

4. **Ends Session**
   - Saves session summary
   - Updates memories
   - Tracks what was accomplished

### Available Commands

All these work in any initialized project:

- **`/claude-os-init`** - Initialize new project
- **`/claude-os-search [query]`** - Search memories & docs
- **`/claude-os-remember [content]`** - Quick save to memories
- **`/claude-os-save [title]`** - Full-featured save with KB selection
- **`/claude-os-list`** - List all knowledge bases
- **`/claude-os-session [action]`** - Manage development sessions
- **`/claude-os-triggers`** - Manage trigger phrases

### Available Skills

- **`initialize-project`** - Analyze codebase and generate standards
- **`remember-this`** - Auto-save when you say "remember this:"
- **`memory`** - Simple memory management

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              Claude Code CLI                     │
│         (with Claude OS integration)             │
└───────────────────┬─────────────────────────────┘
                    │ MCP HTTP
┌───────────────────▼─────────────────────────────┐
│         MCP Server (Port 8051)                   │
│              FastAPI Backend                     │
└───────────────────┬─────────────────────────────┘
                    │
        ┌───────────┴────────────┐
        │                        │
┌───────▼────────────┐  ┌────────▼──────────┐
│   RAG Engine       │  │  React UI         │
│  (llama-index)     │  │  (Port 5173)      │
│  • Vector Search   │  │  • Project Mgmt   │
│  • Hybrid Search   │  │  • KB Browser     │
│  • Reranking       │  │  • Doc Upload     │
└───────┬────────────┘  └───────────────────┘
        │
┌───────▼────────────────────────────────────────┐
│   SQLite + sqlite-vec (Local Database)         │
│  • projects                                     │
│  • knowledge_bases                             │
│  • documents (with embeddings)                 │
│  • Single-file database                        │
└────────────────────────────────────────────────┘
        │
        └─────────────────────┐
                              │
                    ┌─────────▼──────┐
                    │  Ollama        │
                    │  (Port 11434)  │
                    │ • llama3.1     │
                    │ • Embeddings   │
                    └────────────────┘
```

### Template System

```
claude-os/
├── templates/              # Shared with all projects
│   ├── commands/          # Slash commands (symlinked to ~/.claude/)
│   │   ├── claude-os-init.md
│   │   ├── claude-os-search.md
│   │   └── ...
│   ├── skills/            # Skills (symlinked to ~/.claude/)
│   │   ├── initialize-project/
│   │   ├── remember-this/
│   │   └── memory/
│   └── project-files/     # Files created during /claude-os-init
│       ├── CLAUDE.md.template
│       └── .claude-os/
│           ├── config.json.template
│           └── hooks.json.template
├── cli/                   # CLI tools
│   └── claude-os-consolidate.sh
├── install.sh             # One-command setup for coworkers
└── start.sh               # Start services
```

**Benefits:**
- ✅ Update once, all projects benefit
- ✅ Symlinks mean instant updates
- ✅ Easy to share with team
- ✅ Consistent across projects

---

## 📚 Managing Knowledge Bases

### Via Web UI

1. **Visit** http://localhost:5173
2. **Create Knowledge Base:**
   - Click "Create Knowledge Base"
   - Choose type (Generic, Code, Documentation, Agent_OS)
3. **Upload Documents:**
   - Select KB from dropdown
   - Drag & drop files or click upload
   - Supports .md, .txt, .pdf, .py, .js, .ts, .json, .yaml
4. **Query:**
   - Type question in search box
   - View answer with source citations

### Via CLI

```bash
# Search your project memories
/claude-os-search "how did we implement authentication?"

# Save a quick insight
/claude-os-remember "Fixed bug in user controller by adding validation"

# Full-featured save
/claude-os-save "Authentication Pattern" my-app-project_profile Architecture
```

### Auto-Created KBs

When you run `/claude-os-init`, you get 4 knowledge bases:

1. **`{project}-project_memories`**
   - Claude's memory for decisions, patterns, solutions
   - Automatically saved during sessions
   - Searched at session start

2. **`{project}-project_profile`**
   - Architecture, coding standards, practices
   - Generated by `initialize-project` skill
   - Updated as project evolves

3. **`{project}-project_index`**
   - Automated codebase index
   - Tracks file structure
   - Updates on git commits (with hooks)

4. **`{project}-knowledge_docs`**
   - Your documentation
   - Auto-ingested during init
   - Add more via UI or CLI

---

## 🤝 Team Collaboration

### Sharing Claude OS

**Step 1: Package for sharing**
```bash
cd /path/to/claude-os
./cli/claude-os-consolidate.sh  # Move files to templates/
git add templates/ cli/ install.sh
git commit -m "Ready for team sharing"
git push
```

**Step 2: Share repo URL with team**

Send teammates:
- Repo URL
- Link to `SHARING_GUIDE.md` in the repo

**Step 3: They install (3 minutes)**
```bash
git clone <your-repo-url>
cd claude-os
./install.sh
./start.sh
```

Done! They can now use `/claude-os-init` on any project.

### Per-Project Setup

Each team member:
1. Runs `/claude-os-init` in their project
2. Gets their own knowledge bases
3. CLAUDE.md is committed to git (shared)
4. .claude-os/ state is git-ignored (personal)

**Result:** Team shares context via CLAUDE.md, but each person has their own AI memory.

---

## ⚙️ Configuration

### Environment Variables

```bash
# SQLite Database
SQLITE_DB_PATH=data/claude-os.db  # Default: data/claude-os.db

# Ollama
OLLAMA_HOST=http://localhost:11434  # Default: localhost:11434
OLLAMA_MODEL=llama3.1:latest        # Default: llama3.1:latest

# MCP Server
MCP_SERVER_HOST=0.0.0.0         # Default: 0.0.0.0
MCP_SERVER_PORT=8051            # Default: 8051
```

### Project Configuration

Each project has `.claude-os/config.json`:

```json
{
  "project_name": "my-app",
  "claude_os_url": "http://localhost:8051",
  "knowledge_bases": {
    "memories": "my-app-project_memories",
    "profile": "my-app-project_profile",
    "index": "my-app-project_index",
    "docs": "my-app-knowledge_docs"
  },
  "docs_settings": {
    "watch_paths": ["./docs", "./knowledge_docs"],
    "auto_ingest_patterns": ["*.md", "*.txt", "*.pdf"]
  },
  "tech_stack": "Ruby on Rails",
  "database": "MySQL"
}
```

---

## 📊 Performance

**Native Ollama Setup:**
- Response time: ~40 seconds per query
- GPU acceleration: Full Metal GPU on Apple Silicon
- Memory usage: 8-10GB (models + context)
- CPU usage: 12 cores (M4 Pro)

**Why it's fast:**
- Direct GPU acceleration (no virtualization)
- Efficient vector search in SQLite
- Optimized RAG engine with caching
- Single-file database with minimal overhead

---

## 🛠️ Scripts Guide

### Installation & Setup

#### `./install.sh` - Team Member Setup ⭐
```bash
./install.sh
```
**For coworkers joining the team:**
- ✅ Creates `~/.claude/` directories
- ✅ Symlinks all commands and skills
- ✅ Sets up Python environment
- ✅ Installs dependencies
- ✅ Configures MCP server

#### `./setup.sh` - First-Time Setup
```bash
./setup.sh
```
**For the original creator:**
- ✅ Installs Ollama + Redis (if needed)
- ✅ Downloads LLM models (~5-10 GB)
- ✅ Sets up Python environment
- ✅ Creates database

#### `./cli/claude-os-consolidate.sh` - Organize Files
```bash
./cli/claude-os-consolidate.sh
```
**One-time consolidation:**
- Moves commands to `templates/`
- Moves skills to `templates/`
- Creates symlinks
- Prepares for git commit

### Service Management

#### `./start.sh` or `./start_all_services.sh` - Start Everything
```bash
./start.sh
```
**Starts:**
- 🔌 MCP Server (port 8051)
- 🎨 React Frontend (port 5173)
- 🤖 RQ Workers
- 💾 Redis
- 🧠 Ollama

#### `./stop_all_services.sh` - Stop All
```bash
./stop_all_services.sh
```

#### `./restart_services.sh` - Restart
```bash
./restart_services.sh
```

---

## 🐛 Troubleshooting

### "Command not found: /claude-os-init"

Symlinks weren't created. Re-run:
```bash
cd /path/to/claude-os
./install.sh
```

### "Connection refused to localhost:8051"

Claude OS server isn't running:
```bash
cd /path/to/claude-os
./start.sh
```

### "Project already exists"

Project name is taken. Choose a different name or delete via UI at http://localhost:5173

### Port Already in Use

```bash
# Find process on port 8051
lsof -i :8051

# Kill if needed
kill -9 <PID>
```

### Ollama Issues

```bash
# Check if running
ollama list

# Start manually
ollama serve

# Check for model
ollama list | grep llama3.1
```

---

## 📁 Project Structure

```
claude-os/
├── templates/              # NEW: Shared templates system
│   ├── commands/          # Slash commands
│   ├── skills/            # Skills
│   └── project-files/     # Files created during init
├── cli/                   # NEW: CLI tools
│   └── claude-os-consolidate.sh
├── app/                    # Backend application
│   ├── core/              # Core modules
│   │   ├── sqlite_manager.py
│   │   ├── rag_engine.py
│   │   └── ...
│   └── db/                # Database schemas
├── frontend/              # React UI (Vite)
│   ├── src/
│   └── public/
│       └── assets/
│           └── claude-os-hero.png
├── mcp_server/           # MCP Server (HTTP)
│   └── server.py         # FastAPI + MCP endpoints
├── data/                 # SQLite database
│   └── claude-os.db
├── logs/                 # Service logs
├── install.sh            # NEW: Coworker setup
├── start.sh              # NEW: Start services
├── SHARING_GUIDE.md      # NEW: Team sharing docs
└── README.md             # This file
```

---

## 📖 Additional Documentation

### Getting Started
- **[SHARING_GUIDE.md](SHARING_GUIDE.md)** - 🤝 How to share with your team
- **[templates/README.md](templates/README.md)** - 📂 Template system documentation

### Core Features
- **[docs/SELF_LEARNING_SYSTEM.md](docs/SELF_LEARNING_SYSTEM.md)** - 🧠 How Claude learns automatically
- **[docs/REAL_TIME_LEARNING_GUIDE.md](docs/REAL_TIME_LEARNING_GUIDE.md)** - Real-time learning usage
- **[docs/MEMORY_MCP_GUIDE.md](docs/MEMORY_MCP_GUIDE.md)** - Persistent memory guide

### Technical Documentation
- **[README_NATIVE_SETUP.md](README_NATIVE_SETUP.md)** - Detailed native setup
- **[NATIVE_VS_DOCKER_DECISION.md](NATIVE_VS_DOCKER_DECISION.md)** - Why native Ollama
- **[PERFORMANCE_TEST_RESULTS.md](PERFORMANCE_TEST_RESULTS.md)** - Benchmark results
- **[MCP_KB_ENDPOINTS.md](MCP_KB_ENDPOINTS.md)** - MCP endpoint docs

---

## 🤝 Contributing

This is a team development tool. Feel free to:
- Modify for your specific needs
- Add new commands and skills
- Optimize RAG strategies
- Contribute improvements back

---

## 📄 License

MIT License - Use it freely!

---

## 🎯 Next Steps

### For Original Creator:
1. Run `./setup.sh` (first time)
2. Run `./cli/claude-os-consolidate.sh` (organize files)
3. Commit templates to git
4. Share repo with team

### For Team Members:
1. Clone the repo
2. Run `./install.sh`
3. Run `./start.sh`
4. Use `/claude-os-init` in your projects

### For Everyone:
- Use `/claude-os-search` to find past work
- Use `/claude-os-remember` to save insights
- Use `/claude-os-session` to track work
- Enjoy never losing context again!

---

<p align="center">
  <strong>Claude Code + Claude OS = Invincible! 🚀</strong><br>
  <em>Built by AI coders, for AI coders</em>
</p>
