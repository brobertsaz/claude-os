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

> Production-grade RAG system with PostgreSQL + pgvector, Ollama LLMs, and Model Context Protocol

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL 17](https://img.shields.io/badge/PostgreSQL-17-green.svg)](https://www.postgresql.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Latest-pink.svg)](https://ollama.ai/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-85%25-green.svg)](tests/TEST_COVERAGE.md)

---

## 🚀 What is Code-Forge?

**Code-Forge** is a **localized, production-grade RAG (Retrieval-Augmented Generation) system** that runs entirely on your machine. It combines:

- **🗄️ PostgreSQL + pgvector** - ACID-compliant vector database with 768-dimensional embeddings
- **🤖 Ollama** - Local LLMs (llama3.2, llama3.1) and embeddings (nomic-embed-text)
- **🔌 MCP (Model Context Protocol)** - HTTP API for AI agent integration
- **⚡ React + FastAPI UI** - Modern, beautiful interface with electric teal design
- **📚 Multi-KB Architecture** - Isolated knowledge bases per project
- **🧠 Advanced RAG** - Vector search, hybrid search, reranking, agentic RAG

### Why Code-Forge?

✅ **100% Local** - Your data never leaves your machine
✅ **Production-Ready** - PostgreSQL ensures data persistence and ACID compliance
✅ **Multi-Knowledge-Base** - Separate KBs for different projects/contexts
✅ **Agent OS Support** - First-class support for spec-driven development
✅ **Advanced RAG** - Multiple retrieval strategies for optimal results
✅ **MCP Integration** - Expose knowledge bases to AI agents via HTTP

---

## ✨ Features

### Core Features

- **🗄️ PostgreSQL + pgvector Vector Store**
  - ACID-compliant transactions
  - 768-dimensional vector embeddings
  - IVFFlat indexing for fast similarity search
  - JSONB metadata for flexible filtering

- **🤖 Local LLM Integration**
  - Ollama-powered LLMs (llama3.2:3b, llama3.1)
  - nomic-embed-text embeddings (768 dimensions)
  - No API keys or cloud dependencies

- **📚 Multi-Knowledge-Base Architecture**
  - Isolated KBs per project
  - 4 KB types: GENERIC, CODE, DOCUMENTATION, AGENT_OS
  - Type-specific ingestion and retrieval

- **🧠 Advanced RAG Strategies**
  - **Vector Search** - Semantic similarity via pgvector
  - **Hybrid Search** - BM25 + vector fusion
  - **Reranking** - Cross-encoder for top results
  - **Agentic RAG** - Sub-question decomposition

- **🔌 MCP (Model Context Protocol) Server**
  - 12 HTTP endpoints for AI agent integration
  - Create, query, and manage knowledge bases
  - Agent OS-specific tools (standards, specs, workflows)

- **⚡ Modern React + FastAPI UI**
  - Electric teal design system
  - Drag & drop document upload
  - Real-time chat interface with markdown rendering
  - Interactive KB management dashboard
  - Built-in help documentation

- **🎨 Legacy Streamlit UI** (Still available)
  - Alternative interface on port 8501
  - Full feature parity with React UI

### Knowledge Base Types

| Type | Icon | Description | Use Case |
|------|------|-------------|----------|
| **GENERIC** | 📚 | General-purpose knowledge | Documentation, notes, research |
| **CODE** | 💻 | Source code repositories | Code search, API reference |
| **DOCUMENTATION** | 📖 | Technical documentation | User guides, API docs |
| **AGENT_OS** | 🤖 | Spec-driven development | Standards, workflows, specs |

### 📁 Supported File Types

- **Documents**: `.md`, `.txt`, `.pdf`
- **Code**: `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go`, `.rs`, `.java`, `.cpp`, `.c`, `.h`
- **Config**: `.json`, `.yaml`, `.yml`

---

## 🏗️ Architecture

```text
┌─────────────────────────────────────────────────────────────────────┐
│                        Code-Forge System                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐      ┌──────────────┐           │
│  │  React UI    │  │  Streamlit   │      │  MCP Server  │           │
│  │  (Vite)      │  │     UI       │      │   (HTTP)     │           │
│  │  Port 5173   │  │  Port 8501   │      │  Port 8051   │           │
│  └──────┬───────┘  └──────┬───────┘      └──────┬───────┘           │
│         │                 │                     │                   │
│         └─────────────────┴──────────┬──────────┘                   │
│                                      │                              │
│                           ┌──────────▼──────────┐                   │
│                           │   FastAPI Backend   │                   │
│                           │   (REST + MCP)      │                   │
│                           └──────────┬──────────┘                   │
│                                      │                              │
│                           ┌──────────▼──────────┐                   │
│                           │   RAG Engine        │                   │
│                           │  (llama-index)      │                   │
│                           │                     │                   │
│                           │  • Vector Search    │                   │
│                           │  • Hybrid Search    │                   │
│                           │  • Reranking        │                   │
│                           │  • Agentic RAG      │                   │
│                           └──────────┬──────────┘                   │
│                                      │                              │
│                           ┌──────────▼──────────┐                   │
│                           │  PostgresManager    │                   │
│                           └──────────┬──────────┘                   │
│                                      │                              │
│              ┌───────────────────────▼───────────────────┐          │
│              │       PostgreSQL + pgvector               │          │
│              │           (Local Database)                │          │
│              │                                           │          │
│              │  Tables:                                  │          │
│              │  • knowledge_bases                        │          │
│              │  • documents (with embeddings)            │          │
│              │  • agent_os_content                       │          │
│              └───────────────────────────────────────────┘          │
│                                                                     │
│  ┌──────────────┐      ┌──────────────┐                             │
│  │    Ollama    │      │  Ollama LLM  │                             │
│  │  Container   │──────│   Service    │                             │
│  │ Port 11434   │      │              │                             │
│  └──────────────┘      └──────────────┘                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Ingestion**: Documents → Chunking → Embedding → PostgreSQL
2. **Query**: User query → Embedding → Vector search → Reranking → LLM → Response
3. **MCP**: AI Agent → HTTP request → RAG Engine → Response

### Services

1. **Frontend Container** (port 5173): React + Vite UI with hot reload
2. **App Container** (ports 8501, 8051):
   - FastAPI backend with MCP server
   - Streamlit UI (legacy)
3. **Ollama Container** (port 11434): Local LLM and embeddings
4. **PostgreSQL** (local, not Docker): Vector database with pgvector extension

---

## 🚀 Performance Optimizations & Upload Guides

**Make Claude CLI the most amazing AI developer for your project!**

### Quick Reference Guides

- **[UPLOAD_CHECKLIST.md](UPLOAD_CHECKLIST.md)** ⭐ **START HERE** - Simple checklist for uploading Pistn files via UI
- **[AGENT_OS_UPLOAD_HELP.md](AGENT_OS_UPLOAD_HELP.md)** - In-app help text for Agent OS uploads (new!)
- **[PERFORMANCE_OPTIMIZATIONS.md](PERFORMANCE_OPTIMIZATIONS.md)** - Complete performance fixes (40s → 25s)
- **[PISTN_QUERY_GUIDE.md](PISTN_QUERY_GUIDE.md)** - How to query efficiently for best results
- **[AGENT_OS_SETUP_GUIDE.md](AGENT_OS_SETUP_GUIDE.md)** - Guide for Agent OS knowledge bases

### Performance Summary
- **Before**: 30-40 second response times with hallucinations
- **After**: 25-26 seconds (cached) with accurate, context-aware responses
- **LLM**: Upgraded to llama3.1:8B for 35% faster inference
- **Key Fixes**: RAGEngine caching + optimized retrieval + larger model

### In-App Help
When you create an **Agent OS** knowledge base in Code-Forge UI, you'll see a blue help box showing exactly which files to upload and in what priority order. No guessing needed!

---

## ⚡ Quick Start

### First-Time Setup

```bash
./setup.sh
```

This automated script will:

- ✅ Check for Docker, Node.js, PostgreSQL, Ollama
- ✅ Install pgvector extension
- ✅ Create `codeforge` database
- ✅ Download required Ollama models (~7GB)
- ✅ Install frontend dependencies
- ✅ Build and start Docker containers
- ✅ Start React dev server
- ✅ Open browser automatically
- ✅ Verify installation

### Daily Usage

After initial setup, start Code-Forge with one command:

```bash
./start.sh
```

This will:

- ✅ Start backend services (Docker)
- ✅ Start frontend dev server
- ✅ Open browser automatically

To stop all services:

```bash
./stop.sh
```

### Access the Application

- **React UI**: <http://localhost:5173> **(Recommended)**
- **Streamlit UI**: <http://localhost:8501> (Legacy)
- **MCP Server**: <http://localhost:8051>
- **Ollama API**: <http://localhost:11434>

---

## 📦 Prerequisites

### Required

- **macOS** (tested on macOS 14+)
- **Docker Desktop** - [Download](https://www.docker.com/products/docker-desktop)
- **Node.js 18+** - [Download](https://nodejs.org/) or `brew install node`
- **PostgreSQL 17+** - [Download Postgres.app](https://postgresapp.com/) or `brew install postgresql@17`
- **Ollama** - [Download](https://ollama.ai/download) or `brew install ollama`

### Disk Space

- **PostgreSQL**: ~500MB
- **Ollama Models**: ~7GB
  - llama3.2:3b (2.0 GB)
  - llama3.1:latest (4.9 GB)
  - nomic-embed-text (274 MB)
- **Docker Images**: ~2GB

**Total**: ~10GB

---

## 📚 Usage Guide

### Creating a Knowledge Base

1. Open the React UI at <http://localhost:5173>
2. Click the **"Main App"** button
3. Click **"+ New KB"** in the sidebar
4. Enter a name (e.g., `my-project`)
5. Select a KB type (GENERIC, CODE, DOCUMENTATION, or AGENT_OS)
6. Click **"Create"**

### Uploading Documents

#### Option 1: File Upload

1. Select your KB from the sidebar
2. Go to the **"Documents"** tab
3. Drag & drop files or click **"Choose Files"**
4. Click **"Upload"**

#### Option 2: Directory Import

1. Select your KB from the sidebar
2. Go to the **"Documents"** tab
3. Enter the full path to your project directory
4. Click **"Import Directory"**

### Chatting with Your KB

1. Select your KB from the sidebar
2. Go to the **"Chat"** tab
3. (Optional) Configure RAG settings:
   - **Strategy**: Vector, Hybrid, Reranking, or Agentic
   - **Top K**: Number of documents to retrieve
   - **Temperature**: LLM creativity (0.0-1.0)
4. Type your question and press Enter
5. View sources in the response

### Sharing with Your Team

Want to share Code-Forge with coworkers? See **[SHARING.md](SHARING.md)** for:

- ✅ How to share the repository
- ✅ What your coworker needs to install
- ✅ Quick start guide for new users
- ✅ Exporting/importing knowledge bases
- ✅ Network sharing options
- ✅ Troubleshooting guide

**TL;DR:** Share the repo → They run `docker compose up -d` → Pull models → Done! 🎉

---

## 🔗 MCP Integration

### Connecting Claude Desktop

1. Ensure the MCP server is running (it starts automatically with `docker compose up`)
2. Get the MCP endpoint URL from the Streamlit sidebar:

   ```text
   http://localhost:8051/mcp
   ```

3. Add to Claude Desktop:

   ```bash
   claude mcp add --transport http code-forge http://localhost:8051/mcp
   ```

### Available MCP Tools

#### `search_knowledge_base`

Search a KB using RAG with optional advanced features.

**Parameters:**

- `kb_name` (string): Name of the knowledge base
- `query` (string): Search query
- `use_hybrid` (boolean): Enable hybrid search
- `use_rerank` (boolean): Enable reranking
- `use_agentic` (boolean): Enable agentic RAG

**Example:**

```json
{
  "kb_name": "my-project",
  "query": "How does authentication work?",
  "use_hybrid": true,
  "use_rerank": true
}
```

#### `list_knowledge_bases`

List all available knowledge bases.

**Returns:** Array of KB names

#### `get_kb_stats`

Get statistics for a knowledge base.

**Parameters:**

- `kb_name` (string): Name of the knowledge base

**Returns:**

```json
{
  "total_documents": 42,
  "total_chunks": 387,
  "last_updated": "2025-10-22T10:30:00"
}
```

#### `list_documents`

List all documents in a knowledge base.

**Parameters:**

- `kb_name` (string): Name of the knowledge base

**Returns:** Array of document metadata objects

---

## ⚙️ Configuration

### Environment Variables

Create `.env` file:

```bash
# Ollama
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_EMBED_MODEL=nomic-embed-text

# PostgreSQL
POSTGRES_HOST=host.docker.internal
POSTGRES_PORT=5432
POSTGRES_DB=codeforge
POSTGRES_USER=your_username

# RAG
TOP_K_RETRIEVAL=5
CHUNK_SIZE=512
CHUNK_OVERLAP=50
```

### RAG Strategy Tuning

Edit `app/core/config.py`:

```python
# Retrieval settings
TOP_K_RETRIEVAL = 5
RERANK_TOP_N = 3

# Chunking settings
CHUNK_SIZE = 512
CHUNK_OVERLAP = 50
```

---

## 🛠️ Development

### Project Structure

```text
code-forge/
├── app/
│   ├── core/
│   │   ├── config.py             # Configuration management
│   │   ├── pg_manager.py         # PostgreSQL operations
│   │   ├── ingestion.py          # Document processing
│   │   ├── agent_os_ingestion.py # Agent OS profile ingestion
│   │   ├── kb_metadata.py        # KB metadata management
│   │   ├── kb_types.py           # KB type definitions
│   │   └── rag_engine.py         # RAG implementation
│   ├── db/
│   │   └── schema.sql            # PostgreSQL schema
│   └── main.py                   # Streamlit application
├── mcp_server/
│   └── server.py                 # MCP server (FastMCP)
├── .streamlit/
│   └── config.toml               # Streamlit theme (Archon colors)
├── data/
│   └── ollama/                   # Ollama models (persistent)
├── docs/                         # Documentation
├── docker-compose.yml            # Service orchestration
├── Dockerfile                    # Application container
├── requirements.txt              # Python dependencies
├── setup.sh                      # Automated setup script
└── README.md                     # This file
```

### Running Locally (Without Docker)

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Ensure PostgreSQL and Ollama are running locally

3. Start the MCP server:

   ```bash
   python mcp_server/server.py
   ```

4. Start Streamlit:

   ```bash
   streamlit run app/main.py
   ```

---

## 🐛 Troubleshooting

### PostgreSQL Connection Failed

```bash
# Check if PostgreSQL is running
psql -c "SELECT version();"

# If using Postgres.app, ensure it's started
# Check: Applications → Postgres.app
```

### Ollama Models Not Found

```bash
# List installed models
ollama list

# Re-download if needed
ollama pull nomic-embed-text
ollama pull llama3.2:3b
```

### Docker Container Won't Start

```bash
# Check logs
docker-compose logs -f app

# Rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Data Persistence Issues

Your data is stored in:

- **PostgreSQL**: Local database (survives all Docker operations)
- **Ollama models**: `./data/ollama/` (survives all Docker operations)

To verify:

```bash
# Check database
psql -d codeforge -c "\dt"

# Check models
ls -lh data/ollama/
```

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for more solutions.

---

## 🧪 Testing

Code-Forge has a comprehensive test suite to ensure reliability and catch bugs early.

### Quick Start

```bash
# Run all tests
./run_tests.sh

# Run with coverage
./run_tests.sh --coverage

# Run only unit tests (fast)
./run_tests.sh --unit

# Run only integration tests
./run_tests.sh --integration
```

### Test Categories

- **Unit Tests** (`--unit`) - Fast, no external dependencies
- **Integration Tests** (`--integration`) - Require database/Ollama
- **Vector Tests** (`--vector`) - PostgreSQL vector operations
- **RAG Tests** (`--rag`) - RAG engine functionality
- **API Tests** (`--api`) - FastAPI endpoints

### Test Coverage

| Component | Coverage |
|-----------|----------|
| PostgreSQL Manager | 90% |
| RAG Engine | 85% |
| Document Processing | 80% |
| API Endpoints | 90% |
| Embeddings | 85% |
| **Overall** | **85%** |

See [tests/TEST_COVERAGE.md](tests/TEST_COVERAGE.md) for detailed coverage information.

### Writing Tests

When adding new features:

1. **Write tests first** (TDD approach)
2. **Use appropriate markers** (`@pytest.mark.unit`, etc.)
3. **Ensure >80% coverage** for new code
4. **Run tests before committing**

```python
import pytest

@pytest.mark.unit
def test_my_feature():
    """Test description."""
    assert my_function() == expected_result
```

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. **Add tests** (see Testing section above)
5. Run `./run_tests.sh` to verify
6. Submit a pull request

All PRs must:
- ✅ Pass all tests
- ✅ Maintain >80% code coverage
- ✅ Follow existing code style
- ✅ Include documentation updates

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **llama-index** - RAG framework
- **Ollama** - Local LLM runtime
- **pgvector** - PostgreSQL vector extension
- **Streamlit** - UI framework
- **FastMCP** - MCP server library

---

> **Built with ❤️ for the local-first AI community**
>
> [Documentation](docs/) • [Issues](https://github.com/yourusername/code-forge/issues) • [Discussions](https://github.com/yourusername/code-forge/discussions)
