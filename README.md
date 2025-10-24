# Code-Forge

```text
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ██████╗ ██████╗ ██████╗ ███████╗    ███████╗ ██████╗ ██████╗  ██████╗ ███████╗
║  ██╔════╝██╔═══██╗██╔══██╗██╔════╝    ██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
║  ██║     ██║   ██║██║  ██║█████╗      █████╗  ██║   ██║██████╔╝██║  ███╗█████╗
║  ██║     ██║   ██║██║  ██║██╔══╝      ██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝
║  ╚██████╗╚██████╔╝██████╔╝███████╗    ██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
║   ╚═════╝ ╚═════╝ ╚═════╝ ╚══════╝    ╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
║                                                               ║
║           Localized Multi-Knowledge-Base RAG System           ║
║                    with MCP Integration                       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

> **Production-grade RAG system** with PostgreSQL + pgvector, Ollama LLMs, and Model Context Protocol. Runs 100% locally on your machine.

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL 16+](https://img.shields.io/badge/PostgreSQL-16+-green.svg)](https://www.postgresql.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Latest-pink.svg)](https://ollama.ai/)

---

## 🚀 What is Code-Forge?

**Code-Forge** is a **localized RAG (Retrieval-Augmented Generation) system** designed to make AI assistants deeply knowledgeable about your codebase and documentation. It combines:

- **🗄️ PostgreSQL + pgvector** - Vector database for semantic search
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

Before running the setup, ensure you have:

1. **PostgreSQL 16+** (macOS)
   ```bash
   # Install via Homebrew
   brew install postgresql@16
   brew services start postgresql@16

   # Verify
   psql --version
   ```

2. **Python 3.11+**
   ```bash
   python3 --version
   ```

3. **Node.js 16+** (for React frontend)
   ```bash
   node --version
   ```

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd code-forge
   ```

2. **Run the setup script** (handles Ollama, Python, models)
   ```bash
   chmod +x setup_native.sh
   ./setup_native.sh
   ```

   This will:
   - ✅ Check PostgreSQL is installed and running
   - ✅ Create the `codeforge` database automatically
   - ✅ Install/start Ollama
   - ✅ Download LLM models (5-10 GB total)
   - ✅ Setup Python environment

3. **Start services**
   ```bash
   ./start_all_services.sh
   ```

   This starts:
   - **MCP Server** (port 8051) - Backend RAG engine
   - **React UI** (port 5173) - Web dashboard
   - **Ollama** (port 11434) - LLM service

4. **Access the UI**
   - Open http://localhost:5173 in your browser
   - Start uploading documents to create knowledge bases

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
│   PostgreSQL + pgvector (Local Database)       │
│  • knowledge_bases                             │
│  • documents (with embeddings)                 │
│  • Full ACID compliance                        │
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
# PostgreSQL
POSTGRES_HOST=localhost          # Default: localhost
POSTGRES_PORT=5432              # Default: 5432
POSTGRES_DB=codeforge           # Default: codeforge
POSTGRES_USER=$USER             # Default: current user
POSTGRES_PASSWORD=              # Default: empty (no password)

# Ollama
OLLAMA_HOST=http://localhost:11434  # Default: localhost:11434

# MCP Server
MCP_SERVER_HOST=0.0.0.0         # Default: 0.0.0.0
MCP_SERVER_PORT=8051            # Default: 8051
```

### PostgreSQL Password (if needed)

If your PostgreSQL requires a password:

```bash
export POSTGRES_PASSWORD="your_password"
./start_all_services.sh
```

---

## 📊 Performance

**Native Ollama Setup (Current)**
- Response time: ~40 seconds per query
- GPU acceleration: Full Metal GPU on Apple Silicon
- Memory usage: 8-10GB (models + context)
- CPU usage: 12 cores (M4 Pro, leaves 2 for system)

**Why it's fast:**
- 33-56% faster than Docker containers
- Direct GPU acceleration (no virtualization)
- Efficient vector search in PostgreSQL
- Optimized RAG engine with caching

---

## 📁 Project Structure

```
code-forge/
├── app/                    # Backend application
│   ├── core/              # Core modules
│   │   ├── config.py      # Configuration management
│   │   ├── pg_manager.py  # PostgreSQL interface
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
├── setup_native.sh       # Installation script
├── start_all_services.sh # Start all services
├── stop_all_services.sh  # Stop all services
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

---

## 🐛 Troubleshooting

### PostgreSQL Connection Issues

```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Start PostgreSQL if stopped
brew services start postgresql@16

# Check if database exists
psql -h localhost -U $USER -l | grep codeforge

# If database doesn't exist, create it
createdb -h localhost -U $USER codeforge
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

