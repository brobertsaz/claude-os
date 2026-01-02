# Claude OS

[![Run in Smithery](https://smithery.ai/badge/skills/brobertsaz)](https://smithery.ai/skills?ns=brobertsaz&utm_source=github&utm_medium=badge)


<p align="center">
  <img src="frontend/public/assets/claude-os-hero.png" alt="Claude OS Hero" width="800"/>
</p>

<p align="center">
  <strong>Give Your AI a Memory</strong><br>
  <em>Claude Code that actually remembers you.</em>
</p>

<p align="center">
  <a href="#license"><img src="https://img.shields.io/badge/License-MIT-purple.svg" alt="License: MIT"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11%20|%203.12-blue.svg" alt="Python 3.11 | 3.12"></a>
  <a href="https://www.sqlite.org/"><img src="https://img.shields.io/badge/SQLite-3.0+-green.svg" alt="SQLite"></a>
  <a href="https://ollama.ai/"><img src="https://img.shields.io/badge/Ollama-Latest-pink.svg" alt="Ollama"></a>
</p>

<p align="center">
  <a href="https://thebob.dev/claude-os/">
    <img src="https://img.shields.io/badge/🌐_Explore-Claude_OS-00D9FF?style=for-the-badge&logo=github" alt="Explore Claude OS">
  </a>
  <a href="https://github.com/brobertsaz/claude-os/wiki">
    <img src="https://img.shields.io/badge/📚_Wiki-Guides_&_Skills-8B5CF6?style=for-the-badge&logo=github" alt="Wiki">
  </a>
</p>

---

<p align="center">
  <a href="https://discord.gg/BrvVYdXkCU">
    <img src="https://img.shields.io/badge/Join_our_Discord!-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Join Discord">
  </a>
</p>

<p align="center">
  <strong>We have a Discord!</strong> Join our community to get help, share your projects, and connect with other Claude OS users.
</p>

---

## ✨ The Magic

**You:** "Remember this: our API uses JWT tokens with 15-minute expiry and 7-day refresh tokens"

**Claude:** *Saved: "API Authentication Strategy" (Architecture)*

That's it. Next week, next month, next project - Claude remembers. No commands to memorize. No complex setup. Just talk naturally.

```
"remember this..."     → saved to your knowledge base
"what did we decide?"  → searches your memories
"how did we fix that?" → finds past solutions
```

**Every conversation makes Claude smarter. Every insight builds your shared knowledge.**

---

## 🆕 What's New in v2.3

> **Latest Release: December 2025**

### 🎯 Skills Library & Community Skills

Browse and install **36+ skills** from the community with one click!

```bash
/claude-os-skills                    # List all skills
/claude-os-skills install pdf        # Install from community
```

**New Features:**
- 📚 **Local Templates** - Pre-built skills for Rails, React, testing workflows
- 🌐 **Community Skills** - Install from Anthropic Official (16) & Superpowers (20)
- 🔧 **Custom Skills** - Create and share project-specific skills
- 🎨 **Beautiful UI** - Browse, search, and install via web interface
- 📖 **[Recommended Skills](https://github.com/brobertsaz/claude-os/wiki/Recommended-Skills)** - Our curated list of skills we actually use and trust

### 📊 Session Insights

Parse Claude Code sessions and extract insights automatically!

**New Features:**
- 🔍 **Session Parser** - Reads Claude Code's native `.jsonl` session files
- 💡 **Insight Extraction** - Extracts patterns, decisions, blockers
- 📈 **Analytics Ready** - Track tool usage and file changes across sessions

### ✨ Beautiful New Installer (v2.2)

The installer got a major upgrade with **Charm CLI (gum)** support!

```bash
./setup-claude-os.sh --demo    # See the beautiful UI without changes
./setup-claude-os.sh --dry-run # Preview what would happen
./setup-claude-os.sh --help    # See all options
```

**New Features:**
- 🎨 **Gum Integration** - Beautiful interactive menus with arrow-key navigation (with graceful bash fallback)
- 🛡️ **Safety Features** - `--demo`, `--dry-run`, and automatic config backups
- 💨 **Lite Model Default** - Now defaults to `llama3.2:3b` (2GB) instead of 8b (4.7GB)
- ☁️ **Cloud Option** - Choose between Local (Ollama) or Cloud (OpenAI) during setup
- 🐧 **Better Linux Support** - Improved package manager detection and installation

**Safety First:**
- `--demo` - Try the installer UI without making any changes
- `--dry-run` - See exactly what would be done before doing it
- Auto-backup - Existing `.env` files backed up before overwriting

### 📋 Recent Improvements

| Version | Highlights |
|---------|------------|
| **v2.3** | Skills library, community skills, session insights |
| **v2.2** | Gum CLI support, safety features, lite model default |
| **v2.1** | Unified installer, OpenAI provider support |
| **v2.0** | Hybrid tree-sitter indexing, real-time Kanban board |

### 🙌 Community Contributions

Thanks to our amazing contributors!

| PR | Contributor | Description |
|----|-------------|-------------|
| [#22](https://github.com/brobertsaz/claude-os/pull/22) | [@illAssad](https://github.com/illAssad) | Fix delete document endpoint SQLite cursor handling |
| [#21](https://github.com/brobertsaz/claude-os/pull/21) | [@illAssad](https://github.com/illAssad) | Skip node_modules and build directories during ingestion |
| [#20](https://github.com/brobertsaz/claude-os/pull/20) | [@illAssad](https://github.com/illAssad) | Fix tree-sitter version compatibility |
| [#19](https://github.com/brobertsaz/claude-os/pull/19) | [@illAssad](https://github.com/illAssad) | Add non-blocking semantic indexing with Jobs Dashboard UI |
| [#18](https://github.com/brobertsaz/claude-os/pull/18) | [@illAssad](https://github.com/illAssad) | Fix frontend startup by auto-installing npm dependencies |
| [#17](https://github.com/brobertsaz/claude-os/pull/17) | [@williamclavier](https://github.com/williamclavier) | Fix: Ensure commands/skills directories exist |
| [#16](https://github.com/brobertsaz/claude-os/pull/16) | [@jplimack](https://github.com/jplimack) | Fix hardcoded paths - make dynamic |
| [#12](https://github.com/brobertsaz/claude-os/pull/12) | [@gkastanis](https://github.com/gkastanis) | Add missing frontend lib files |
| [#11](https://github.com/brobertsaz/claude-os/pull/11) | [@gkastanis](https://github.com/gkastanis) | Add Linux support for installation |
| [#10](https://github.com/brobertsaz/claude-os/pull/10) | [@nicseltzer](https://github.com/nicseltzer) | Fix broken README link |

---

## 🚀 What is Claude OS?

Claude OS isn't just a tool - **it's Claude's memory**.

Think about it: you and Claude work together on a feature. You explain your architecture, your patterns, your preferences. Then you close the terminal... and it's all gone. Tomorrow, you start over.

**What if Claude actually remembered?**

### Before Claude OS

```
Day 1: "We use JWT tokens with refresh..."
Day 2: "As I mentioned, we use JWT tokens..."
Day 3: "Again, the auth system uses JWT..."
```

### After Claude OS

```
Day 1: "Remember this: we use JWT tokens with refresh..."
Day 2: Claude already knows. Applies the pattern automatically.
Day 3: Claude suggests improvements based on what worked.
```

### The Difference

| Without Claude OS | With Claude OS |
|-------------------|----------------|
| Explain the same things repeatedly | Claude remembers your decisions |
| Start cold every session | Context loaded automatically |
| Patterns forgotten | Patterns compound over time |
| Claude is a tool | Claude is a partner |

### Why It Works

- 🧠 **Persistent Knowledge** - Decisions, patterns, solutions saved across sessions
- 🔍 **Automatic Recall** - Relevant memories surface when you need them
- 📚 **Documentation Search** - Your docs indexed and searchable via RAG
- 🎯 **Session Learning** - Claude extracts insights from past conversations
- 🔒 **100% Local** - Your knowledge never leaves your machine

### Features at a Glance

| Feature | What It Does |
|---------|--------------|
| **Natural Language Memory** | Just say "remember this" - no commands needed |
| **Session Insights** | Auto-extracts patterns from past conversations |
| **Lightning Indexing** | 10,000 files indexed in 30 seconds |
| **Skills Library** | 36+ community skills, one-click install |
| **Cross-Project Learning** | Patterns from Project A help in Project B |
| **One-Command Setup** | `/claude-os-init` and you're ready |

---

## ⚡ NEW: Hybrid Indexing System

**Claude OS v2.0 introduces lightning-fast tree-sitter based indexing!**

### The Problem with Traditional Indexing

Previous versions embedded EVERY file, which was painfully slow for large codebases:

- **Large projects (10,000+ files):** 3-5 hours to index
- Must complete before Claude can start working
- High resource usage, blocks productive coding

### The Solution: Hybrid Two-Phase Indexing

Inspired by [Aider's](https://github.com/Aider-AI/aider) approach, Claude OS now uses:

**Phase 1: Structural Index (30 seconds)**

- ⚡ Parse files with tree-sitter (no LLM calls!)
- 📊 Extract symbols only (classes, functions, signatures)
- 🔗 Build dependency graph
- 🏆 PageRank importance scoring
- ✅ Ready to code immediately!

**Phase 2: Semantic Index (optional, background)**

- 🎯 Selective embedding (top 20% most important files)
- 📚 Full embedding for documentation
- 🔍 Deep semantic search when needed
- ⏰ Runs in background while you code

### Performance Comparison

| Feature | Before | After (Hybrid) |
|---------|--------|----------------|
| **Large project (10k files)** | 3-5 hours | **30 seconds** + 20 min optional |
| **Files embedded** | 100,000+ chunks | ~20,000 chunks (80% reduction) |
| **Start coding** | After full index | **Immediately!** |
| **Resource usage** | High Ollama load | Minimal CPU/memory |
| **Query speed** | Semantic search | Instant structural + semantic |

📖 **Read the full design:** [docs/HYBRID_INDEXING_DESIGN.md](docs/HYBRID_INDEXING_DESIGN.md)

---

## 🎨 Visual Interface

**Claude OS provides a beautiful, intuitive web interface for managing your AI development workflow:**

<table>
<tr>
<td width="50%">

### Welcome Screen

![Welcome](frontend/public/assets/screenshots/welcome-screen.png)
Get started with Claude OS

</td>
<td width="50%">

### Project Overview

![Overview](frontend/public/assets/screenshots/project-overview-page.png)
View project details and MCP status

</td>
</tr>
<tr>
<td width="50%">

### Kanban Board

![Kanban](frontend/public/assets/screenshots/project-kanban-page.png)
Track spec implementation progress

</td>
<td width="50%">

### Services Dashboard

![Services](frontend/public/assets/screenshots/project-services-dashboard-page.png)
Monitor all Claude OS services

</td>
</tr>
</table>

**📖 See the complete visual guide:** [docs/guides/VISUAL_GUIDE.md](docs/guides/VISUAL_GUIDE.md)

---

## 🏗️ Architecture Overview

<p align="center">
  <img src="frontend/public/assets/claude-os-architecture.svg" alt="Claude OS Architecture Diagram" width="100%"/>
</p>

**Claude OS is built on 5 core pillars that work together to give Claude persistent memory:**

1. **🧠 Real-Time Learning** - Automatically captures insights from conversations via Redis Pub/Sub
2. **💾 Memory MCP** - Persistent memory system with instant recall using natural language
3. **🔍 Analyze-Project** - Intelligent codebase indexing with git hooks and tree-sitter
4. **🎯 Session Management** - Auto-resume sessions with full context preservation
5. **📚 Semantic Search** - Vector-based code understanding and pattern recognition

All knowledge flows through the **Semantic Knowledge Base** (SQLite + sqlite-vec), exposed via the **MCP Server** (port 8051) to **Claude Code**, giving you an AI assistant that never forgets.

**Data Flow:** `Git Commit → 3s indexing → SQLite → MCP → Claude → You`

---

## 💻 Installation & Setup

### Prerequisites

**Required:**

- macOS or Linux (Ubuntu, Debian, Fedora, RHEL, Arch)
- Python 3.11 or 3.12 (`python3 --version`)
  - **Note:** Python 3.13+ not yet supported due to dependency constraints
- Git (`git --version`)

**Optional:**

- Node.js 16+ (for React UI)
- Ollama (for local AI) or OpenAI API key

> **Note:** Windows support coming soon.

### Quick Installation

```bash
# Clone the repository
git clone https://github.com/brobertsaz/claude-os.git
cd claude-os

# Run the unified installer
./setup-claude-os.sh
```

**First time? Try the demo first:**

```bash
./setup-claude-os.sh --demo    # See the beautiful UI (no changes made)
./setup-claude-os.sh --dry-run # Preview what would be installed
```

The installer will guide you through:

1. **Choose Provider:** Local (Ollama) or Cloud (OpenAI)
2. **Choose Model Size:** Lite (2GB) or Full (4.7GB) - for local installs
3. **Automatic Setup:** Python, dependencies, MCP server, commands/skills

**What gets installed:**

- ✅ Python virtual environment
- ✅ All dependencies
- ✅ MCP server configuration
- ✅ Commands and skills symlinked to `~/.claude/`
- ✅ Ollama + models (if local provider selected)
- ✅ Redis for caching

### Installer Options

```bash
./setup-claude-os.sh           # Interactive installation
./setup-claude-os.sh --demo    # Try the UI without changes
./setup-claude-os.sh --dry-run # Preview what would happen
./setup-claude-os.sh --help    # Show all options
./setup-claude-os.sh --version # Show version
```

### Legacy Scripts

The old `install.sh` and `setup.sh` scripts still work - they redirect to the new unified installer.

**Visit** <http://localhost:5173> to use the web UI.

### Starting Claude OS

After installation, start the services:

```bash
./start.sh
```

This starts the MCP server at `http://localhost:8051`

---

## 🚀 Quick Start

**Initialize any project with Claude OS in under 2 minutes:**

### Step 1: Navigate to Your Project

```bash
cd /path/to/your/project
```

### Step 2: Initialize with Claude OS

In Claude Code, run:

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

### What You Get

- ✅ 4 knowledge bases created (memories, profile, index, docs)
- ✅ Documentation auto-indexed
- ✅ Codebase analyzed
- ✅ CLAUDE.md file with all context
- ✅ Ready to code with AI memory!

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
- **`/claude-os-skills [action]`** - Manage skills (list, install, create)

### Available Skills

**Global Skills (always available):**
- **`initialize-project`** - Analyze codebase and generate standards
- **`memory`** - Save and recall information (supports "remember this:", "save to memory", etc.)

**Community Skills (install via `/claude-os-skills`):**
- **36+ skills** from Anthropic Official and Superpowers repos
- PDF/XLSX manipulation, frontend design, TDD, debugging, code review, and more

---

## 🤖 Agent-OS: Spec-Driven Development (Optional)

> **Created by [Builder Methods (CasJam Media LLC)](https://github.com/buildermethods/agent-os)**
> MIT Licensed • Separate Optional Integration

**Agent-OS adds structured workflows for planning and implementing features using 8 specialized agents.**

Agent-OS is a separate open-source project that can be installed alongside Claude OS. We're grateful to Builder Methods for creating such powerful spec-driven development tools.

### Manual Installation

If the Agent-OS repository is available, you can install it with:

```bash
git clone https://github.com/buildermethods/agent-os.git ~/.claude/agents/agent-os
```

**Note:** Check if the repository exists before attempting to install.

### When to Use Agent-OS

If you have Agent-OS installed, use it when you want:

- **Structured feature planning** with iterative requirements gathering
- **Detailed specifications** before coding
- **Task breakdowns** with clear implementation steps
- **Verification workflows** to ensure completeness

### The 8 Agents

**Specification Workflow:**

1. **`spec-initializer`** - Initialize new spec directories
2. **`spec-shaper`** - Gather requirements through 1-3 questions at a time
3. **`spec-writer`** - Create detailed technical specifications
4. **`tasks-list-creator`** - Break specs into actionable tasks

**Implementation Workflow:**

5. **`implementer`** - Implement features following task list
6. **`implementation-verifier`** - Verify implementation completeness
7. **`spec-verifier`** - Verify specs and tasks consistency
8. **`product-planner`** - Create product documentation

### Agent-OS Commands

Available when enabled:

- **`/new-spec`** - Initialize a new feature specification
- **`/create-spec`** - Full specification workflow (gather requirements → create spec → generate tasks)
- **`/plan-product`** - Create product mission, roadmap, and tech stack docs
- **`/implement-spec`** - Implement a specification following its tasks

### How It Works

```
1. User: "/new-spec user-authentication"
   → Agent creates spec directory structure

2. User: "/create-spec"
   → spec-shaper asks 1-3 questions at a time
   → Gathers requirements iteratively
   → Identifies reusable code
   → Collects visual assets

3. Agent: spec-writer creates detailed specification
   → tasks-list-creator generates actionable tasks

4. User: "/implement-spec user-authentication"
   → implementer follows tasks step-by-step
   → implementation-verifier checks completeness

5. Result: Fully specified, implemented, and verified feature!
```

### Agent-OS Project Structure

When enabled, your project gets:

```
your-project/
├── agent-os/
│   ├── config.yml          # Agent-OS configuration
│   ├── product/            # Product documentation
│   │   ├── mission.md      # Product mission
│   │   ├── roadmap.md      # Feature roadmap
│   │   └── tech-stack.md   # Technology stack
│   ├── specs/              # Feature specifications
│   │   └── YYYY-MM-DD-feature-name/
│   │       ├── planning/
│   │       │   ├── requirements.md
│   │       │   └── visuals/
│   │       ├── spec.md
│   │       └── tasks.md
│   └── standards/          # Coding standards (as skills)
└── .claude/agents/agent-os/  # 8 agents (symlinked)
```

### Integration with Claude OS

Agent-OS agents deeply integrate with Claude OS:

- **Search memories** before creating specs (avoid reinventing)
- **Save decisions** to project_memories during planning
- **Reference patterns** from previous work
- **Build knowledge** that improves over time

**This is the complete AI development system!**

---

## 🎯 Skills Library

**Browse, install, and manage Claude Code skills with ease!**

### What Are Skills?

Skills are reusable instruction sets that teach Claude specific capabilities. They can include:
- Coding patterns and best practices
- Tool usage workflows
- Domain-specific knowledge
- Development methodologies

### Skill Types

**Global Skills** (`~/.claude/skills/`)
- Available in ALL projects
- Core skills: `memory`, `initialize-project`

**Project Skills** (`{project}/.claude/skills/`)
- Available only in that project
- Installed from templates or custom created

**Community Skills** (fetched from GitHub)
- **Anthropic Official** - 16 skills from `anthropics/skills`
- **Superpowers** - 20 skills from `obra/superpowers`

### Using the Skills Command

```bash
# List all installed skills
/claude-os-skills

# Browse local templates
/claude-os-skills templates

# Install a template to your project
/claude-os-skills install rails-backend

# Create a custom skill
/claude-os-skills create

# View skill details
/claude-os-skills view <name>

# Delete a project skill
/claude-os-skills delete <name>
```

### Community Skills (via Web UI)

1. Open the web UI at http://localhost:5173
2. Select your project
3. Click the **Skills** tab
4. Click **Install Template**
5. Switch to **Community Skills** tab
6. Browse skills from Anthropic Official and Superpowers
7. Click **Install** on any skill

### Featured Community Skills

**From Anthropic Official:**
- `pdf` - Create, edit, and analyze PDF documents
- `xlsx` - Spreadsheet manipulation with formulas
- `frontend-design` - Production-grade UI components
- `mcp-builder` - Create MCP servers
- `doc-coauthoring` - Collaborative documentation

**From Superpowers:**
- `test-driven-development` - TDD workflow
- `systematic-debugging` - Four-phase debugging framework
- `code-review` - Rigorous code review process
- `git-worktrees` - Isolated development branches
- `brainstorming` - Structured ideation process

---

## 🎯 Spec Tracking & Kanban Board

**NEW: Real-time auto-syncing Kanban board for Agent-OS specs!**

![Kanban Board](frontend/public/assets/screenshots/project-kanban-page.png)
*Visual Kanban board showing specs, tasks, and progress tracking*

### What It Does

When you use Agent-OS to create specs with `/create-spec`, Claude OS automatically:

- 📋 **Parses tasks.md files** - Extracts all tasks, phases, dependencies, and metadata
- 🗄️ **Stores in database** - Tracks progress, completion, and time estimates
- 📊 **Displays as Kanban** - Visual board showing specs and tasks by status
- ⚡ **Real-time sync** - NEW! Auto-detects file changes and updates within 3 seconds
- 👀 **File watching** - Monitors `agent-os/specs/` folder for changes
- ✅ **Auto-refresh** - Board polls every 3 seconds for live updates
- 🗃️ **Archives completed specs** - Keep your board focused on active work

### Features

**Real-Time File Watching (NEW!):**

- Automatically monitors your `agent-os/specs/` folder
- Detects changes to `tasks.md` and `spec.md` files
- 2-second debounce to batch rapid edits
- Auto-syncs to database within 3 seconds
- Frontend auto-refreshes every 3 seconds
- **Total latency: ~6 seconds from file save to board update**

**Automatic Syncing:**

- Syncs all specs from your project's `agent-os/specs/` folder
- Tracks task metadata (estimated time, dependencies, risk level)
- Auto-detects completed tasks (marked with ✅ or `[x]` in tasks.md)
- Supports both checkbox format and classic format

**Progress Tracking:**

- **Status auto-updates** based on completion:
  - `planning` - No tasks completed yet
  - `in_progress` - Some tasks completed
  - `completed` - All tasks done
- Progress percentage calculated automatically
- Time estimates tracked (estimated vs actual minutes)

**Archive Feature:**

- Archive completed specs to keep your board clean
- Archived specs hidden by default but can be viewed
- Preserves all task history for future reference

### API Endpoints

All spec tracking functionality is exposed via REST API:

```bash
# Get all specs for a project
GET /api/projects/{project_id}/specs

# Get all tasks for a spec
GET /api/specs/{spec_id}/tasks

# Update task status
PATCH /api/tasks/{task_id}/status
{
  "status": "in_progress",  # todo, in_progress, done, blocked
  "actual_minutes": 15
}

# Sync specs from agent-os folder (manual)
POST /api/projects/{project_id}/specs/sync

# Get Kanban board view
GET /api/projects/{project_id}/kanban?include_archived=false

# Archive/unarchive specs
POST /api/specs/{spec_id}/archive
POST /api/specs/{spec_id}/unarchive

# NEW: Real-time spec watcher control
GET /api/spec-watcher/status
POST /api/spec-watcher/start/{project_id}
POST /api/spec-watcher/stop/{project_id}
POST /api/spec-watcher/start-all
```

**See:** `docs/guides/REALTIME_KANBAN_GUIDE.md` for complete documentation.

### How It Works

```
1. You create a spec with Agent-OS:
   /create-spec → agent-os/specs/2025-01-15-user-auth/

2. Spec Watcher detects the new folder:
   - Auto-starts when MCP server boots
   - Monitors agent-os/specs/ directory
   - 2-second debounce for batch changes

3. Auto-sync to database:
   - Reads tasks.md
   - Parses checkbox format: - [x] Task title
   - Extracts metadata, tasks, phases
   - Stores in SQLite database
   - ✅ Completes within 3 seconds

4. View in Kanban board (auto-refreshes every 3 seconds):
   - Todo: PHASE1-TASK1, PHASE1-TASK2
   - In Progress: PHASE2-TASK1
   - Done: PHASE1-TASK3, PHASE1-TASK4

5. As you work, agent-os updates tasks.md:
   - File watcher detects change
   - Auto-syncs to database
   - Board refreshes automatically
   - Total latency: ~6 seconds

6. Archive when complete:
   - Mark spec as archived
   - Keeps history but cleans up board
```

### Database Schema

Two new tables track specs and tasks:

**`specs` table:**

- Stores spec metadata (name, path, status)
- Tracks total/completed tasks
- Calculates progress percentage
- Archive flag to hide completed specs

**`spec_tasks` table:**

- Individual tasks with codes (PHASE1-TASK1)
- Status (todo/in_progress/done/blocked)
- Time tracking (estimated vs actual)
- Dependencies between tasks
- Risk levels and phases

### Example Usage

```bash
# Sync all specs for your project
curl -X POST http://localhost:8051/api/projects/1/specs/sync

# Response:
{
  "synced": 3,
  "updated": 0,
  "total": 3,
  "errors": []
}

# Get Kanban view
curl http://localhost:8051/api/projects/1/kanban

# Response shows:
# - Your specs with tasks
# - Tasks grouped by status
# - Progress percentages
# - Time estimates
```

**This is the complete AI development system!**

---

## 📂 Template System

```
claude-os/
├── templates/              # Shared templates
│   ├── commands/          # Slash commands (symlinked to ~/.claude/)
│   │   ├── claude-os-init.md
│   │   ├── claude-os-search.md
│   │   ├── claude-os-skills.md    # NEW: Skills management
│   │   └── ...
│   ├── skills/            # Global skills (symlinked to ~/.claude/)
│   │   ├── initialize-project/
│   │   └── memory/
│   ├── skill-library/     # NEW: Local skill templates
│   │   ├── general/       # General purpose skills
│   │   ├── rails/         # Ruby on Rails skills
│   │   ├── react/         # React/TypeScript skills
│   │   └── testing/       # Testing frameworks
│   └── project-files/     # Files created during /claude-os-init
│       ├── CLAUDE.md.template
│       └── .claude-os/
│           ├── config.json.template
│           └── hooks.json.template
├── cli/                   # CLI tools
│   └── claude-os-consolidate.sh
├── install.sh             # Quick setup script
└── start.sh               # Start services
```

**Benefits:**

- ✅ Update once, all projects benefit
- ✅ Symlinks mean instant updates
- ✅ Consistent across projects

---

## 📚 Managing Knowledge Bases

### Via Web UI

1. **Visit** <http://localhost:5173>
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

## ⚙️ Configuration

### Environment Variables

```bash
# Provider (local = Ollama, openai = OpenAI API)
CLAUDE_OS_PROVIDER=local            # Default: local

# SQLite Database
SQLITE_DB_PATH=data/claude-os.db    # Default: data/claude-os.db

# Ollama (for local provider)
OLLAMA_HOST=http://localhost:11434  # Default: localhost:11434
OLLAMA_MODEL=llama3.2:3b            # Default: llama3.2:3b (lite model)
OLLAMA_EMBED_MODEL=nomic-embed-text # Default: nomic-embed-text

# OpenAI (for openai provider)
OPENAI_API_KEY=sk-...               # Required if using OpenAI
OPENAI_LLM_MODEL=gpt-4o-mini        # Default: gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small  # Default

# MCP Server
MCP_SERVER_HOST=0.0.0.0             # Default: 0.0.0.0
MCP_SERVER_PORT=8051                # Default: 8051
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

#### `./setup-claude-os.sh` - Unified Installer (Recommended)

```bash
./setup-claude-os.sh           # Interactive installation
./setup-claude-os.sh --demo    # Try the beautiful UI (no changes)
./setup-claude-os.sh --dry-run # Preview what would happen
./setup-claude-os.sh --help    # Show all options
./setup-claude-os.sh --version # Show version (v2.2.0)
```

**Features:**

- 🎨 Beautiful interactive UI with [Charm CLI (gum)](https://github.com/charmbracelet/gum) support
- 🛡️ Safety features: `--demo`, `--dry-run`, automatic config backups
- ☁️ Provider choice: Local (Ollama) or Cloud (OpenAI)
- 💨 Model choice: Lite (llama3.2:3b, 2GB) or Full (llama3.1:8b, 4.7GB)
- 🐧 Cross-platform: macOS and Linux (Ubuntu, Debian, Fedora, RHEL, Arch)

**What it installs:**

- ✅ Python virtual environment + dependencies
- ✅ Ollama + AI models (if local provider)
- ✅ Redis for caching
- ✅ MCP server configuration
- ✅ Commands and skills symlinked to `~/.claude/`

#### Legacy Scripts

The old scripts redirect to the unified installer:

```bash
./install.sh  # → redirects to setup-claude-os.sh
./setup.sh    # → redirects to setup-claude-os.sh
```

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

## 🗑️ Uninstalling Claude OS

To completely remove Claude OS from your system:

```bash
cd /path/to/claude-os
./uninstall.sh
```

**The uninstall script removes:**

- Command symlinks from `~/.claude/commands/`
- Skill symlinks from `~/.claude/skills/`
- MCP server config from `~/.claude/mcp-servers/`
- Python virtual environment (`venv/`)
- Config files and logs
- Optionally: your knowledge base data

**What it does NOT remove:**

- The `claude-os/` directory itself (delete manually with `rm -rf`)
- Ollama (see [Ollama uninstall docs](https://ollama.ai/docs/uninstall))
- Redis (`brew uninstall redis` on macOS)

**Manual Uninstall:**

If you prefer to uninstall manually:

```bash
# Remove symlinks
rm ~/.claude/commands/claude-os-*.md
rm -rf ~/.claude/skills/initialize-project
rm -rf ~/.claude/skills/memory
rm ~/.claude/mcp-servers/code-forge.json

# Remove Claude OS directory
rm -rf /path/to/claude-os
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

Project name is taken. Choose a different name or delete via UI at <http://localhost:5173>

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
├── templates/              # Shared templates system
│   ├── commands/          # Slash commands
│   ├── skills/            # Global skills
│   ├── skill-library/     # Local skill templates (NEW)
│   └── project-files/     # Files created during init
├── cli/                   # CLI tools
│   └── claude-os-consolidate.sh
├── app/                    # Backend application
│   ├── core/              # Core modules
│   │   ├── sqlite_manager.py
│   │   ├── rag_engine.py
│   │   ├── skill_manager.py    # NEW: Skills management
│   │   ├── session_parser.py   # NEW: Session parsing
│   │   ├── insight_extractor.py # NEW: Insight extraction
│   │   └── ...
│   └── db/                # Database schemas
├── frontend/              # React UI (Vite)
│   ├── src/
│   │   ├── components/
│   │   │   ├── SkillsManagement.tsx  # NEW: Skills UI
│   │   │   └── ...
│   │   └── pages/
│   └── public/
│       └── assets/
├── mcp_server/           # MCP Server (HTTP)
│   └── server.py         # FastAPI + MCP endpoints
├── data/                 # SQLite database
│   └── claude-os.db
├── logs/                 # Service logs
├── install.sh            # Quick setup script
├── start.sh              # Start services
└── README.md             # This file
```

---

## 📖 Additional Documentation

### Getting Started

- **[templates/README.md](templates/README.md)** - 📂 Template system documentation

### Core Features

- **[docs/guides/REALTIME_KANBAN_GUIDE.md](docs/guides/REALTIME_KANBAN_GUIDE.md)** - ⚡ **NEW! Real-time Kanban board** (auto-sync, file watching, API reference)
- **[docs/SELF_LEARNING_SYSTEM.md](docs/SELF_LEARNING_SYSTEM.md)** - 🧠 How Claude learns automatically
- **[docs/REAL_TIME_LEARNING_GUIDE.md](docs/REAL_TIME_LEARNING_GUIDE.md)** - Real-time learning usage

### Technical Documentation

- **[docs/API_REFERENCE.md](docs/API_REFERENCE.md)** - 🔌 **Complete API Reference** (all endpoints, examples, authentication)
- **[docs/HYBRID_INDEXING_DESIGN.md](docs/HYBRID_INDEXING_DESIGN.md)** - ⚡ Hybrid indexing architecture
- **[README_NATIVE_SETUP.md](README_NATIVE_SETUP.md)** - Detailed native setup
- **[NATIVE_VS_DOCKER_DECISION.md](NATIVE_VS_DOCKER_DECISION.md)** - Why native Ollama
- **[PERFORMANCE_TEST_RESULTS.md](PERFORMANCE_TEST_RESULTS.md)** - Benchmark results

---

## 🤝 Contributing

Claude OS is open source. Feel free to:

- Modify for your specific needs
- Add new commands and skills
- Optimize RAG strategies
- Contribute improvements back

---

## 🙏 Acknowledgments

**Agent-OS Integration**

Claude OS optionally integrates with [Agent-OS](https://github.com/builder-methods/agent-os) by Builder Methods (CasJam Media LLC).

- **Project**: Agent-OS - Spec-driven development workflow system
- **Author**: Builder Methods (CasJam Media LLC)
- **License**: MIT
- **Repository**: <https://github.com/builder-methods/agent-os>

Agent-OS provides 8 specialized agents for structured feature planning and implementation. We're grateful to Builder Methods for creating such powerful tools and for licensing them under MIT, making this integration possible.

If you find Agent-OS valuable, consider:

- ⭐ Starring their repository
- 📣 Sharing it with other developers
- 🤝 Contributing to their project

---

## 📄 License

MIT License - Use it freely!

**Note**: This project (Claude OS) is MIT licensed. Agent-OS, when installed, is a separate project also MIT licensed by Builder Methods (CasJam Media LLC). See the Agent-OS repository for their specific license terms.

---

<p align="center">
  <strong>Claude Code + Claude OS = Invincible! 🚀</strong><br>
  <em>Built by AI coders, for AI coders</em>
</p>
