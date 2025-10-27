# Native Claude OS Setup (No Docker)

This guide covers running Claude OS natively on your M4 Pro Mac with Metal GPU acceleration.

## Prerequisites

### 1. **PostgreSQL** (Required for MCP Server)

If you don't have PostgreSQL installed, install it:

```bash
# Option A: Via Homebrew (recommended)
brew install postgresql@16
brew services start postgresql@16

# Option B: Download from https://www.postgresql.org/download/macosx/

# Verify it's running
psql --version
psql -h localhost -U $USER -d postgres -c "SELECT 1"
```

Once PostgreSQL is running, create the database:

```bash
createdb codeforge
```

### 2. **Ollama** (For LLM)

Already installed via Homebrew in the previous steps. It should be running with:

```bash
brew services start ollama
```

### 3. **Node.js** (For React Frontend)

```bash
# Check if installed
node --version

# If not installed
brew install node
```

### 4. **Python 3.11+** (For MCP Server)

```bash
python3 --version
```

## Quick Start

Once all prerequisites are installed and running:

```bash
# From the project directory
cd ~/Projects/claude-os

# Start all services
./start_all_services.sh
```

This will:
1. ✅ Check PostgreSQL is running
2. ✅ Check/Start Ollama
3. ✅ Setup Python virtual environment
4. ✅ Start MCP Server (port 8051)
5. ✅ Start React Frontend (port 5173)

## Service URLs

Once everything is running:

- **Frontend UI**: http://localhost:5173
- **MCP Server**: http://localhost:8051
- **API Endpoint**: http://localhost:8051/api
- **MCP Endpoint**: http://localhost:8051/mcp/kb/pistn

## Stopping Services

```bash
./stop_all_services.sh
```

## Logs

Service logs are stored in the `logs/` directory:

```bash
# Watch MCP server logs
tail -f logs/mcp_server.log

# Watch frontend logs
tail -f logs/frontend.log
```

## Environment Variables

The system uses environment variables from:

```bash
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=codeforge
POSTGRES_USER=$USER
POSTGRES_PASSWORD=

# Ollama
OLLAMA_HOST=http://localhost:11434

# MCP Server
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8051
```

## Performance

With native setup on M4 Pro:

- **Query Response Time**: 2-5 seconds (vs 30-45s with Docker)
- **GPU Acceleration**: Full Metal GPU support
- **RAM Usage**: ~8-10GB for models + app
- **CPU Utilization**: 12 cores (leave 2 for system)

## Troubleshooting

### "PostgreSQL not running"
```bash
brew services start postgresql@16
# or find your postgresql version
brew services list
```

### "Ollama models not found"
```bash
ollama pull llama3.1:latest
ollama pull nomic-embed-text:latest
```

### "Port already in use"
```bash
# Port 8051 (MCP Server)
lsof -i :8051 | grep -v COMMAND | awk '{print $2}' | xargs kill -9

# Port 5173 (Frontend)
lsof -i :5173 | grep -v COMMAND | awk '{print $2}' | xargs kill -9
```

### "npm packages not installed"
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

## Architecture

```
localhost:5173 (React Frontend)
    ↓
localhost:8051 (FastAPI MCP Server)
    ↓
localhost:11434 (Ollama with Metal GPU)
    ↓
localhost:5432 (PostgreSQL)
```

## For Claude (Me)

The MCP server is configured to expose:

- **Global endpoint**: `/mcp` - All knowledge bases and tools
- **KB-specific endpoint**: `/mcp/kb/pistn` - Pistn KB only

Query examples:

```bash
curl -X POST http://localhost:8051/mcp/kb/pistn \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "search",
      "arguments": {
        "query": "appointment settings"
      }
    },
    "id": 1
  }'
```

## System Requirements

- **CPU**: M4 Pro or similar Apple Silicon (14+ cores)
- **RAM**: 48GB (or 32GB minimum)
- **Storage**: ~10GB for models + application
- **macOS**: 12.0+

Enjoy your high-performance local MCP server! 🚀
