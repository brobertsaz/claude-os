# Claude OS

```text
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║  ██████╗██╗      █████╗ ██╗   ██╗██████╗ ███████╗    ██████╗ ███████╗
║ ██╔════╝██║     ██╔══██╗██║   ██║██╔══██╗██╔════╝   ██╔═══██╗██╔════╝
║ ██║     ██║     ███████║██║   ██║██║  ██║█████╗     ██║   ██║███████╗
║ ██║     ██║     ██╔══██║██║   ██║██║  ██║██╔══╝     ██║   ██║╚════██║
║ ╚██████╗███████╗██║  ██║╚██████╔╝██████╔╝███████╗   ╚██████╔╝███████║
║  ╚═════╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚═════╝ ╚══════╝
║                                                               ║
║           Localized Multi-Knowledge-Base RAG System           ║
║                    with MCP Integration                       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

> **Production-grade RAG system** with SQLite vector search, Ollama LLMs, and Model Context Protocol. Runs 100% locally on your machine.

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![SQLite](https://img.shields.io/badge/SQLite-3.0+-green.svg)](https://www.sqlite.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Latest-pink.svg)](https://ollama.ai/)

---

## 🚀 What is Claude OS?

**Claude OS** is a **localized RAG (Retrieval-Augmented Generation) system** designed to make AI assistants deeply knowledgeable about your codebase and documentation. It combines:

- **🗄️ SQLite + sqlite-vec** - Lightweight vector database for semantic search
- **🤖 Ollama** - Local LLMs (llama3.1) with no API keys needed
- **🔌 MCP Integration** - Claude Desktop integration via Model Context Protocol
- **⚡ React UI** - Modern dashboard for managing knowledge bases
- **📚 Multi-KB Support** - Separate knowledge bases for different projects
- **🧠 Advanced RAG** - Hybrid search, reranking, and agentic modes

### Perfect For

✅ Making Claude deeply familiar with your codebase
✅ Private, secure knowledge base (never leaves your machine)
✅ Team collaboration (share with coworkers easily)
✅ Integration with Claude Desktop via MCP
✅ Building AI-assisted development workflows

---

## ⚡ Quick Start (5-10 minutes)

### Prerequisites

**You MUST have these installed first:**

1. **Python 3.11+** (required)
   ```bash
   python3 --version
   ```
   - macOS: `brew install python@3.11`
   - Linux: `sudo apt-get install python3.11`
   - Windows: Download from https://www.python.org/downloads/

2. **Git** (required)
   ```bash
   git --version
   ```
   - macOS: `brew install git`
   - Linux: `sudo apt-get install git`
   - Windows: Download from https://git-scm.com/

3. **Node.js 16+** (optional, for React frontend)
   ```bash
   node --version
   ```
   - macOS: `brew install node`
   - Linux: `sudo apt-get install nodejs`
   - Windows: Download from https://nodejs.org/

---

### One-Line Installer ✨

**Once you have Python 3.11+ and Git, run this command:**

```bash
curl -fsSL https://raw.githubusercontent.com/brobertsaz/claude-os/main/setup.sh | bash
```

**The script will automatically:**
- ✅ Install Ollama (if needed) + download LLM models
- ✅ Install Redis (if needed) for caching/queues
- ✅ Set up Python virtual environment
- ✅ Install all Python dependencies
- ✅ Create SQLite database
- ✅ Install frontend dependencies (if Node.js present)

**Then start services:**
```bash
./start_all_services.sh
```

**Done!** Visit http://localhost:5173 to start using Claude OS.

### Installation (Step by Step)

**Step 1: Install Prerequisites** (one-time only)

Choose your OS:

**macOS:**
```bash
# Install Python 3.11
brew install python@3.11

# Install Git
brew install git

# Optional: Install Node.js for frontend
brew install node
```

**Linux (Ubuntu/Debian):**
```bash
# Install Python 3.11
sudo apt-get update
sudo apt-get install python3.11 python3.11-venv

# Install Git
sudo apt-get install git

# Optional: Install Node.js for frontend
sudo apt-get install nodejs npm
```

**Verify installation:**
```bash
python3 --version  # Should be 3.11+
git --version      # Should exist
```

---

**Step 2: Run the Installer**

Once you have Python 3.11+ and Git:

```bash
curl -fsSL https://raw.githubusercontent.com/brobertsaz/claude-os/main/setup.sh | bash
```

This automatically installs:
- ✅ **Ollama** - LLM engine (auto-installed if missing)
- ✅ **Redis** - Cache & queues (auto-installed if missing)
- ✅ **Python dependencies** - All required packages
- ✅ **SQLite database** - Local vector store
- ✅ **Frontend** - React UI (if Node.js present)

The script will download ~5-10 GB of LLM models (llama3.1, embeddings).

---

**Step 3: Start Services**

```bash
./start_all_services.sh
```

This starts:
- 🔌 **MCP Server** (port 8051) - Backend RAG engine
- 🎨 **React UI** (port 5173) - Web dashboard
- 🤖 **Ollama** (port 11434) - LLM service
- 💾 **Redis** (port 6379) - Cache & queues
- 🧠 **RQ Workers** - Real-time learning system

---

**Step 4: Access the Application**

Open your browser and visit:
- **Frontend:** http://localhost:5173
- **API Docs:** http://localhost:8051/docs

Start uploading documents to create knowledge bases!

---

## 🎯 Initialize Your Project (The Magic Sauce ✨)

Once Claude OS is running, follow these 3 simple steps to make Claude an expert on your codebase:

### Step 1: Create a Project in Claude OS UI

1. **Open the UI** - Visit http://localhost:5173 in your browser
2. **Click "Create Project"** button
3. **Fill in the form:**
   - **Project Name** - e.g., "my-awesome-app"
   - **Project Path** - Select your project directory (e.g., `/Users/you/Projects/my-awesome-app`)
   - **Description** - (optional) Brief description of your project

4. **Click "Create Project"**

Your project is now registered in Claude OS!

### Step 2: Get Your Project ID

After creating your project, you'll see it listed in the Projects view. The **Project ID** is displayed right on the project card (e.g., `#1`, `#2`, etc.).

Simply note the number - that's your project ID!

**Example:**
- If you see `#1` on your project card, your project ID is `1`
- If you see `#3` on your project card, your project ID is `3`

### Step 3: Initialize Project with Claude Code

This is where the magic happens! The initialization will:
- ✅ Analyze your entire codebase (5 minutes)
- ✅ Generate coding standards & architecture docs
- ✅ Index 50 key files (~800 code chunks)
- ✅ Set up Git hooks for auto-indexing
- ✅ Create 4 Knowledge Bases automatically

**In Claude Code, run:**

```bash
/initialize-project [project-id]
```

**Example:**
```bash
/initialize-project 1
```

**What happens:**
- Claude analyzes your project structure, patterns, and conventions
- Generates `CODING_STANDARDS.md`, `ARCHITECTURE.md`, `DEVELOPMENT_PRACTICES.md`
- Creates semantic indexes for instant retrieval
- Installs Git hooks to keep knowledge up-to-date

**After 5 minutes:**
✅ Claude is now an expert on your project!

---

## 🔌 MCP Integration with Claude Desktop

To use your knowledge bases with Claude Desktop:

### Option 1: Via CLI (Easiest)

```bash
# Add PISTN knowledge base to Claude Desktop
claude mcp add pistn http://localhost:8051/mcp/kb/pistn

# Add PISTN Agent OS knowledge base
claude mcp add pistn-agent-os http://localhost:8051/mcp/kb/pistn-agent-os
```

Then in Claude Desktop, your knowledge bases are available as built-in tools. Ask Claude about your codebase directly!

### Option 2: Manual Configuration

Edit `~/.claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "pistn": {
      "url": "http://localhost:8051/mcp/kb/pistn"
    },
    "pistn-agent-os": {
      "url": "http://localhost:8051/mcp/kb/pistn-agent-os"
    }
  }
}
```

Then restart Claude Desktop.

---

## 📚 Managing Knowledge Bases

### Create a Knowledge Base

1. Visit http://localhost:5173
2. Click "Create Knowledge Base"
3. Choose type:
   - **GENERIC** - General documentation
   - **CODE** - Source code repositories
   - **DOCUMENTATION** - Technical docs
   - **AGENT_OS** - Spec-driven development

### Upload Documents

1. Select a knowledge base
2. Click "Upload Documents"
3. Choose files (supports .md, .txt, .pdf, .py, .js, .ts, .json, .yaml)
4. Watch as documents are indexed

### Query the Knowledge Base

**Via Web UI:**
1. Select a KB from the dropdown
2. Type your question
3. View answer with source citations

**Via Claude Desktop:**
Once added as MCP server, Claude can query automatically when working on your project.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│              Claude Desktop                      │
│         (or any MCP client)                      │
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
│  • Vector Search   │  │                   │
│  • Hybrid Search   │  └────────────────────┘
│  • Reranking       │
└───────┬────────────┘
        │
┌───────▼────────────────────────────────────────┐
│   SQLite + sqlite-vec (Local Database)         │
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

---

## ⚙️ Configuration

### Environment Variables

The system uses sensible defaults, but you can customize via environment variables:

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

---

## 📊 Performance

**Native Ollama Setup (Current)**
- Response time: ~40 seconds per query
- GPU acceleration: Full Metal GPU on Apple Silicon
- Memory usage: 8-10GB (models + context)
- CPU usage: 12 cores (M4 Pro, leaves 2 for system)

**Why it's fast:**
- Direct GPU acceleration (no virtualization)
- Efficient vector search in SQLite
- Optimized RAG engine with caching
- Single-file database with minimal overhead

---

## 🛠️ Scripts Guide

Claude OS includes comprehensive shell scripts for setup, service management, and testing. Here's what each one does:

### Installation & Setup

#### `./setup.sh` - Complete Setup ⭐ **USE THIS ONE**
```bash
./setup.sh
```
**This is the standard setup script that 99% of users need.**

**Prerequisites (must be installed first):**
- ✅ Python 3.11+ (required - script will fail if missing)
- ✅ Git (required - script will fail if missing)
- ⚠️ Node.js 16+ (optional - script skips frontend if missing)

**What it automatically installs:**
- ✅ **Ollama** - Downloads and starts if not installed
- ✅ **Redis** - Installs and starts if not present
- ✅ **Python virtual environment** - Isolated environment
- ✅ **Python dependencies** - All packages from `requirements.txt`
- ✅ **LLM models** - llama3.1 and nomic-embed-text (~5-10 GB)
- ✅ **SQLite database** - Local vector store
- ✅ **Frontend dependencies** - npm packages (if Node.js present)

**Supported platforms:** macOS & Linux

**When to use:**
- ✅ **First-time setup (recommended for 99% of users)**
- ✅ You have Python 3.11+ and Git already installed
- ✅ You don't have Ollama or Redis yet
- ✅ You want a complete, automated setup
- ✅ You're on any Unix system (macOS/Linux)

---

#### `./setup_native.sh` - Fast macOS Setup (Advanced Users Only)
```bash
./setup_native.sh
```
**This is an optional lightweight setup for macOS users who already have Ollama installed via Homebrew.**

**What it does:**
- ✅ Verifies Ollama is already installed via Homebrew (fails if not)
- ✅ Pulls required LLM models (llama3.1, nomic-embed-text)
- ✅ Sets up Python virtual environment
- ✅ Installs Python dependencies
- ✅ Creates data/ and logs/ directories
- ✅ Initializes SQLite database
- ⚠️ Does NOT install Redis

**When to use (rare):**
- ⚠️ Only if you already have **Ollama installed via `brew install ollama`**
- ⚠️ You're on macOS only
- ⚠️ You already have Redis running separately

**Note:** Most users should use `./setup.sh` instead. Only use this if you know what you're doing.

---

### Service Management

#### `./start_all_services.sh` - Start Everything
```bash
./start_all_services.sh
```
**Starts:**
- 🔌 **MCP Server** (port 8051) - Backend RAG engine
- 🎨 **React Frontend** (port 5173) - Web dashboard
- 🤖 **RQ Workers** - Real-time learning system
- 💾 **Redis** - Cache & message queue
- 🧠 **Ollama** - LLM service

**Features:**
- Automatic health checks for all services
- Creates required directories if missing
- Checks that ports are free
- Logs all services to `logs/` directory
- Shows service URLs and PIDs

**Output:**
```
Service URLs:
  🎨 Frontend:    http://localhost:5173
  🔌 API Server:  http://localhost:8051
  📚 API Docs:    http://localhost:8051/docs

Log Files:
  MCP Server:   logs/mcp_server.log
  Frontend:     logs/frontend.log
  RQ Workers:   logs/rq_workers.log
```

---

#### `./stop_all_services.sh` - Stop All Services
```bash
./stop_all_services.sh
```
**Stops:**
- 🔌 MCP Server (port 8051)
- 🎨 React Frontend (port 5173)
- 🤖 RQ Workers (real-time learning)
- 💾 Redis

**Note:** Ollama is preserved (may be used by other apps)

---

#### `./restart_services.sh` - Restart Everything
```bash
./restart_services.sh
```
**Does:**
1. Stops all services gracefully
2. Waits for ports to be released (3 second delay)
3. Starts all services fresh

**Use when:** Code changes aren't reflected or services need a clean restart

---

#### `./start_mcp_server.sh` - Start Only MCP Server
```bash
./start_mcp_server.sh
```
**Starts:**
- 🔌 MCP Server (port 8051)

**Checks:**
- ✅ Ollama is running
- ✅ SQLite database exists
- ✅ Python environment is ready

**Use when:** You only need the backend API (e.g., for testing)

---

#### `./start_redis_workers.sh` - Start RQ Workers
```bash
./start_redis_workers.sh
```
**Starts:**
- 🤖 RQ Workers for real-time learning system
- Listening on queues: `claude-os:learning`, `claude-os:prompts`, `claude-os:ingest`
- Scheduler for periodic tasks

**Checks:**
- ✅ Redis is running
- ✅ Python virtual environment exists
- ✅ RQ dependencies are installed

**Use when:** Running the real-time learning system separately

---

### Testing

#### `./run_tests.sh` - Run Test Suite
```bash
./run_tests.sh [OPTIONS]
```

**Options:**
```bash
./run_tests.sh                    # Run all tests
./run_tests.sh --unit             # Unit tests only
./run_tests.sh --integration      # Integration tests only
./run_tests.sh --vector           # Vector DB tests
./run_tests.sh --rag              # RAG engine tests
./run_tests.sh --api              # API endpoint tests
./run_tests.sh --coverage         # Generate coverage report
./run_tests.sh --verbose          # Detailed output
./run_tests.sh --unit --coverage  # Combine options
```

**Features:**
- Validates PostgreSQL connection
- Creates test database if needed
- Shows test configuration
- Generates HTML coverage report (with `--coverage`)

---

## 📁 Project Structure

```
claude-os/
├── app/                    # Backend application
│   ├── core/              # Core modules
│   │   ├── config.py      # Configuration management
│   │   ├── sqlite_manager.py  # SQLite interface
│   │   ├── rag_engine.py  # RAG logic
│   │   └── ...
│   ├── db/                # Database schemas
│   └── ...
├── frontend/              # React UI (Vite)
│   ├── src/
│   │   ├── pages/
│   │   ├── components/
│   │   └── ...
│   └── package.json
├── mcp_server/           # MCP Server (HTTP)
│   ├── server.py         # FastAPI + MCP endpoints
│   └── ...
├── migrations/           # Database migrations
├── data/                 # SQLite database (auto-created)
│   └── claude-os.db
├── logs/                 # Service logs (auto-created)
├── .sh scripts           # Utility scripts (see Scripts Guide above)
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

---

## 🐛 Troubleshooting

### Database Issues

The SQLite database is automatically created at `data/claude-os.db`. If you encounter issues:

```bash
# Check if database exists
ls -lh data/claude-os.db

# Remove and recreate (WARNING: deletes all data)
rm data/claude-os.db
# Restart the server to recreate
```

### Ollama Issues

```bash
# Check if Ollama is running
ollama list

# Start Ollama manually
ollama serve

# Check for specific model
ollama list | grep llama3.1
```

### Port Already in Use

```bash
# Find process on port 8051 (MCP Server)
lsof -i :8051

# Find process on port 5173 (React UI)
lsof -i :5173

# Kill if needed (replace PID with actual process ID)
kill -9 <PID>
```

### MCP Server Not Starting

```bash
# Check logs
tail -f /tmp/mcp_server.log

# Verify Python environment
source venv/bin/activate
python mcp_server/server.py

# Check port 8051 is accessible
curl http://localhost:8051/health
```

---

## 📖 Additional Documentation

### Core Features
- **[docs/SELF_LEARNING_SYSTEM.md](docs/SELF_LEARNING_SYSTEM.md)** - 🧠 How Claude learns from your conversations automatically
- **[docs/REAL_TIME_LEARNING_GUIDE.md](docs/REAL_TIME_LEARNING_GUIDE.md)** - Real-time learning system usage guide
- **[docs/MEMORY_MCP_GUIDE.md](docs/MEMORY_MCP_GUIDE.md)** - Persistent memory across sessions

### Technical Documentation
- **[README_NATIVE_SETUP.md](README_NATIVE_SETUP.md)** - Detailed native setup guide
- **[NATIVE_VS_DOCKER_DECISION.md](NATIVE_VS_DOCKER_DECISION.md)** - Why we chose native Ollama
- **[PERFORMANCE_TEST_RESULTS.md](PERFORMANCE_TEST_RESULTS.md)** - Benchmark results
- **[SLUG_IMPLEMENTATION_SUMMARY.md](SLUG_IMPLEMENTATION_SUMMARY.md)** - URL slug system
- **[MCP_KB_ENDPOINTS.md](MCP_KB_ENDPOINTS.md)** - MCP endpoint documentation

---

## 🤝 Contributing

This is a personal development tool. Feel free to:
- Modify for your specific needs
- Add new KB types
- Optimize RAG strategies
- Contribute improvements back

---

## 📄 License

MIT License - Use it freely!

---

## 🎯 Next Steps

1. **First-time setup:** Run `./setup_native.sh`
2. **Start services:** Run `./start_all_services.sh`
3. **Create knowledge base:** Visit http://localhost:5173
4. **Upload documents:** Add your codebase/docs
5. **Integrate with Claude:** Run `claude mcp add ...`
6. **Start coding:** Ask Claude about your project!

Happy coding! 🚀

