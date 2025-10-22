# 🔥 Code-Forge

**Localized Multi-Knowledge-Base RAG System with MCP Integration**

A self-hosted, privacy-first RAG (Retrieval-Augmented Generation) application designed for development teams. Features a badass Archon-inspired UI and exposes knowledge bases via Model Context Protocol (MCP) for AI agent integration.

---

## ✨ Features

### 🎯 Core Capabilities
- **Multiple Knowledge Bases**: Create isolated KBs for different projects
- **Advanced RAG Strategies**:
  - 🔍 Vector Search (semantic similarity)
  - 🔀 Hybrid Search (vector + BM25 keyword)
  - 🎯 Reranking (cross-encoder scoring)
  - 🤖 Agentic RAG (multi-step reasoning)
- **MCP Integration**: Expose KBs to AI agents like Claude Desktop
- **Dual Interface**: Streamlit UI for humans + MCP server for agents

### 🎨 UI/UX
- **Archon-Inspired Design**: Dark theme with neon accents
- **Color Scheme**:
  - Primary: `hsl(271, 91%, 65%)` (Purple)
  - Accent: `hsl(330, 90%, 65%)` (Pink)
  - Success: `hsl(160, 84%, 39%)` (Green)
  - Background: Pure black `#0E0E0E`
- **Real-time Health Monitoring**: Ollama & ChromaDB status
- **Document Management**: Upload files or import entire directories

### 📁 Supported File Types
- **Documents**: `.md`, `.txt`, `.pdf`
- **Code**: `.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go`, `.rs`, `.java`, `.cpp`, `.c`, `.h`
- **Config**: `.json`, `.yaml`, `.yml`

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Code-Forge                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐              ┌──────────────┐        │
│  │  Streamlit   │              │  MCP Server  │        │
│  │  UI (8501)   │              │  (8051)      │        │
│  └──────┬───────┘              └──────┬───────┘        │
│         │                             │                │
│         └─────────────┬───────────────┘                │
│                       │                                │
│              ┌────────▼────────┐                       │
│              │   RAG Engine    │                       │
│              │  (LlamaIndex)   │                       │
│              └────────┬────────┘                       │
│                       │                                │
│         ┌─────────────┴─────────────┐                  │
│         │                           │                  │
│    ┌────▼─────┐              ┌──────▼──────┐          │
│    │ ChromaDB │              │   Ollama    │          │
│    │ (8000)   │              │   (11434)   │          │
│    └──────────┘              └─────────────┘          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Services
1. **Ollama** (port 11434): Local LLM and embeddings
2. **ChromaDB** (port 8000): Vector database
3. **App Container**:
   - Streamlit UI (port 8501)
   - MCP Server (port 8051)

---

## 🚀 Quick Start

### Prerequisites
- **Docker** and **Docker Compose** installed
- **Ollama** installed locally (or use Docker Ollama)
- At least 8GB RAM recommended

### 1. Clone and Navigate
```bash
git clone <your-repo-url>
cd code-forge
```

### 2. Pull Required Ollama Models
```bash
# Pull LLM model
ollama pull llama3.1

# Pull embedding model
ollama pull nomic-embed-text
```

### 3. One-Command Deployment
```bash
docker compose up --build
```

This will:
- Start Ollama service
- Start ChromaDB service
- Build and start the Code-Forge application
- Wait for all services to become healthy

### 4. Access the Application

**Streamlit UI**: http://localhost:8501

**MCP Server**: http://localhost:8051/mcp

---

## 📚 Usage Guide

### Creating a Knowledge Base

1. Open the Streamlit UI at http://localhost:8501
2. In the sidebar, expand **"➕ Create New KB"**
3. Enter a name (e.g., `my-project`)
4. Click **"Create"**

### Uploading Documents

**Option 1: File Upload**
1. Select your KB from the sidebar
2. Go to the **"📚 Knowledge Base"** tab
3. Click **"Choose files"** and select documents
4. Click **"Upload Files"**

**Option 2: Directory Import**
1. Select your KB from the sidebar
2. Go to the **"📚 Knowledge Base"** tab
3. Enter the full path to your project directory
4. Click **"Import Directory"**

### Chatting with Your KB

1. Select your KB from the sidebar
2. Go to the **"💬 Chat"** tab
3. (Optional) Enable advanced RAG strategies:
   - **🔀 Hybrid Search**: Better for keyword-heavy queries
   - **🎯 Reranking**: Improves relevance of top results
   - **🤖 Agentic RAG**: Best for complex, multi-part questions
4. Type your question and press Enter
5. View sources by expanding **"📚 View Sources"**

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
   ```
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

Create a `.env` file to customize settings:

```bash
# Ollama Configuration
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=llama3.1
OLLAMA_EMBED_MODEL=nomic-embed-text

# ChromaDB Configuration
CHROMA_HOST=chromadb
CHROMA_PORT=8000

# MCP Server Configuration
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8051

# RAG Configuration
CHUNK_SIZE=1024
CHUNK_OVERLAP=200
TOP_K_RETRIEVAL=5
RERANK_TOP_N=3

# Storage
UPLOAD_DIR=/workspace/data/uploads
```

### Changing Models

To use different Ollama models:

1. Pull the model:
   ```bash
   ollama pull mistral
   ```

2. Update `.env`:
   ```bash
   OLLAMA_MODEL=mistral
   ```

3. Restart the application:
   ```bash
   docker compose restart app
   ```

---

## 🛠️ Development

### Project Structure

```
code-forge/
├── app/
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   ├── health.py          # Service health checks
│   │   ├── chroma_manager.py  # ChromaDB operations
│   │   ├── ingestion.py       # Document processing
│   │   ├── kb_metadata.py     # KB metadata management
│   │   └── rag_engine.py      # RAG implementation
│   └── main.py                # Streamlit application
├── mcp_server/
│   └── server.py              # MCP server (FastMCP + FastAPI)
├── .streamlit/
│   └── config.toml            # Streamlit theme
├── data/
│   ├── chroma/                # ChromaDB persistent storage
│   └── uploads/               # Uploaded documents
├── docker-compose.yml         # Service orchestration
├── Dockerfile                 # Application container
├── requirements.txt           # Python dependencies
├── start.sh                   # Startup script
└── README.md                  # This file
```

### Running Locally (Without Docker)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start Ollama and ChromaDB separately

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

### Services Not Starting

**Check service health:**
```bash
docker compose ps
```

**View logs:**
```bash
docker compose logs ollama
docker compose logs chromadb
docker compose logs app
```

### Ollama Models Not Found

**Pull models manually:**
```bash
docker compose exec ollama ollama pull llama3.1
docker compose exec ollama ollama pull nomic-embed-text
```

### ChromaDB Connection Issues

**Restart ChromaDB:**
```bash
docker compose restart chromadb
```

**Check ChromaDB health:**
```bash
curl http://localhost:8000/api/v1/heartbeat
```

### MCP Connection Fails

**Verify MCP server is running:**
```bash
curl http://localhost:8051/health
```

**Check MCP logs:**
```bash
docker compose logs app | grep MCP
```

---

## 📊 Performance Tips

1. **Chunk Size**: Larger chunks (1024-2048 tokens) for technical docs, smaller (512-1024) for code
2. **Hybrid Search**: Best for queries with specific keywords or technical terms
3. **Reranking**: Adds latency but significantly improves relevance
4. **Agentic RAG**: Use for complex questions requiring multi-step reasoning (slower)

---

## 🔒 Privacy & Security

- **100% Local**: All data stays on your machine
- **No External APIs**: Ollama runs models locally
- **No Telemetry**: ChromaDB telemetry disabled
- **Isolated KBs**: Each project has its own knowledge base

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- **LlamaIndex**: RAG framework
- **Ollama**: Local LLM runtime
- **ChromaDB**: Vector database
- **Streamlit**: UI framework
- **FastMCP**: MCP server library
- **Archon**: Design inspiration

---

## 🚀 Roadmap

- [ ] Multi-modal support (images, diagrams)
- [ ] Graph RAG for relationship extraction
- [ ] Query caching for faster responses
- [ ] Batch document processing
- [ ] Export/import knowledge bases
- [ ] Advanced analytics dashboard

---

**Built with 🔥 by The Augster**

