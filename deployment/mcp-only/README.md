# Claude OS - MCP-Only Deployment

This deployment package extracts **just the MCP knowledge base server** from Claude OS, allowing you to expose your populated knowledge bases to other applications without running the full coding environment.

## 🎯 What This Does

- ✅ Exposes MCP HTTP endpoints for knowledge base queries
- ✅ Serves your existing SQLite database (read-only by default)
- ✅ Provides RAG (Retrieval Augmented Generation) search
- ✅ Lightweight: No CLI, no coding tools, no UI
- ✅ Perfect for: Knowledge base APIs, live chat backends, documentation search

## 🏗️ Architecture

```
┌─────────────────┐
│  Your Other Apps│
│  (Chat, Docs)   │
└────────┬────────┘
         │ HTTP/JSON-RPC
         ↓
┌─────────────────┐
│  MCP Server     │
│  (Port 8051)    │
└────────┬────────┘
         │
         ├──→ SQLite DB (your local data/claude-os.db)
         └──→ Ollama (embeddings + LLM)
```

## 📦 What's Included

- **MCP Server**: HTTP endpoints for all knowledge base operations
- **SQLite Manager**: Database access layer
- **RAG Engine**: Semantic search with hybrid modes
- **Ollama**: Local AI for embeddings and LLM (required)

## 🚀 Quick Start

### Option 1: Using Your Existing Local Database (Recommended)

This is the easiest approach - just mount your existing `data/claude-os.db`:

```bash
# From the deployment/mcp-only directory
docker-compose up -d

# This will:
# 1. Start Ollama container
# 2. Start MCP server with your DB mounted at ../../data (read-only)
# 3. Pull required models on first run
```

Your MCP server will be available at: `http://localhost:8051`

### Option 2: Copy Database to Server

If you're deploying to a remote server:

```bash
# 1. Copy your local database to the server
scp ../../data/claude-os.db user@server:/path/to/claude-os/data/

# 2. On the server, start services
docker-compose up -d
```

### Option 3: Volume-Based (For Persistent Changes)

If you want the Docker container to have its own copy:

```bash
# 1. Edit docker-compose.yml - uncomment the mcp_data volume
# 2. Copy your database into the volume
docker-compose up -d
docker cp ../../data/claude-os.db claude-os-mcp:/app/data/
```

## 🔧 Configuration

### Environment Variables

Edit `docker-compose.yml` to configure:

```yaml
environment:
  # Database (required)
  SQLITE_DB_PATH: /app/data/claude-os.db

  # Ollama (required)
  OLLAMA_HOST: http://ollama:11434
  OLLAMA_EMBED_MODEL: nomic-embed-text
  OLLAMA_MODEL: llama3.1:latest

  # CORS - Important for your other apps!
  CORS_ORIGINS: "https://your-chat-app.com,https://your-docs-app.com"

  # Optional: Authentication
  JWT_SECRET_KEY: your-secret-key-here
  API_USERNAME: admin
  API_PASSWORD: changeme
```

### First-Time Setup: Pull Ollama Models

On first run, you need to download the models:

```bash
# Wait for containers to start
docker-compose up -d

# Pull embedding model (required)
docker exec claude-os-ollama ollama pull nomic-embed-text

# Pull LLM model (optional, for agentic queries)
docker exec claude-os-ollama ollama pull llama3.1:latest
```

## 🔌 Using the MCP Endpoints

### Health Check

```bash
curl http://localhost:8051/health
```

### List All Knowledge Bases

```bash
curl -X POST http://localhost:8051/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "list_knowledge_bases",
      "arguments": {}
    },
    "id": 1
  }'
```

### Search Knowledge Base

```bash
curl -X POST http://localhost:8051/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "search_knowledge_base",
      "arguments": {
        "kb_name": "my-docs",
        "query": "How do I configure authentication?",
        "top_k": 10
      }
    },
    "id": 1
  }'
```

### KB-Specific Endpoint (Cleaner URLs)

```bash
# Search a specific KB directly
curl -X POST http://localhost:8051/mcp/kb/my-docs \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "search",
      "arguments": {
        "query": "authentication setup",
        "top_k": 5
      }
    },
    "id": 1
  }'
```

## 🔗 Integration Examples

### Python Client

```python
import requests

def search_knowledge(kb_name: str, query: str, top_k: int = 10):
    response = requests.post(
        "http://localhost:8051/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "search_knowledge_base",
                "arguments": {
                    "kb_name": kb_name,
                    "query": query,
                    "top_k": top_k
                }
            },
            "id": 1
        }
    )
    return response.json()["result"]

# Use in your chat app
results = search_knowledge("my-docs", "How to deploy?")
print(results)
```

### JavaScript/Node.js Client

```javascript
async function searchKnowledge(kbName, query, topK = 10) {
  const response = await fetch('http://localhost:8051/mcp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'tools/call',
      params: {
        name: 'search_knowledge_base',
        arguments: { kb_name: kbName, query, top_k: topK }
      },
      id: 1
    })
  });

  const data = await response.json();
  return data.result;
}

// Use in your app
const results = await searchKnowledge('my-docs', 'How to deploy?');
console.log(results);
```

## 📊 Available MCP Tools

### Global Endpoint (`/mcp`)

| Tool | Description |
|------|-------------|
| `search_knowledge_base` | Semantic search across any KB |
| `list_knowledge_bases` | List all available KBs |
| `list_knowledge_bases_by_type` | Filter KBs by type |
| `create_knowledge_base` | Create new KB (if writable) |
| `get_kb_stats` | Get KB statistics |
| `list_documents` | List documents in KB |
| `ingest_agent_os_profile` | Import Agent OS data |
| `get_agent_os_stats` | Agent OS statistics |
| `get_standards` | Retrieve standards |
| `get_workflows` | Retrieve workflows |
| `get_specs` | Retrieve specifications |
| `get_product_context` | Get product context |

### KB-Specific Endpoint (`/mcp/kb/{kb_slug}`)

| Tool | Description |
|------|-------------|
| `search` | Search within specific KB |
| `get_stats` | Get stats for specific KB |
| `list_documents` | List documents in KB |

## 🔒 Security Considerations

### 1. Read-Only Database (Default)

The default `docker-compose.yml` mounts your database as **read-only** (`:ro` flag). This prevents the container from modifying your local data.

To allow writes (e.g., for creating new KBs), change:
```yaml
volumes:
  - ../../data:/app/data:ro  # Read-only
```
to:
```yaml
volumes:
  - ../../data:/app/data  # Read-write
```

### 2. Enable Authentication

Uncomment and set these in `docker-compose.yml`:

```yaml
JWT_SECRET_KEY: "your-strong-secret-key-here"
API_USERNAME: "admin"
API_PASSWORD: "secure-password-here"
```

Then authenticate:

```bash
# Get token
curl -X POST http://localhost:8051/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=secure-password-here"

# Use token in requests
curl -X POST http://localhost:8051/mcp \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '...'
```

### 3. CORS Configuration

Restrict `CORS_ORIGINS` to your specific domains:

```yaml
CORS_ORIGINS: "https://chat.yourapp.com,https://docs.yourapp.com"
```

### 4. Network Isolation

If deploying with your other apps, use Docker networks:

```yaml
networks:
  - your_app_network
```

## 🌐 Cloudflare Workers Deployment

For a serverless approach similar to [cloudflare_mcp](https://github.com/forayconsulting/cloudflare_mcp):

### What You'd Need

1. **Export your SQLite DB to Cloudflare D1** (their SQLite service)
2. **Rewrite MCP endpoints as Workers** (JavaScript/TypeScript)
3. **Use Cloudflare AI** instead of Ollama (for embeddings)

### Pros of Cloudflare Approach
- ✅ Globally distributed
- ✅ Auto-scaling
- ✅ No server management

### Cons
- ❌ Must rewrite Python → JavaScript
- ❌ Cloudflare AI models (less flexibility)
- ❌ D1 has size limits (500MB free tier)
- ❌ More complex to set up initially

**This Docker approach** is simpler if you just need to expose your existing data to your apps on a server you control.

## 📈 Monitoring

### View Logs

```bash
# MCP Server logs
docker-compose logs -f mcp-server

# Ollama logs
docker-compose logs -f ollama
```

### Check Health

```bash
# MCP Server
curl http://localhost:8051/health

# Ollama
curl http://localhost:11434/api/tags
```

## 🛠️ Troubleshooting

### Models Not Found

```bash
# Pull models manually
docker exec claude-os-ollama ollama pull nomic-embed-text
docker exec claude-os-ollama ollama pull llama3.1:latest
```

### Database Not Found

```bash
# Verify database path
docker exec claude-os-mcp ls -la /app/data/

# Check if mounted correctly
docker inspect claude-os-mcp | grep -A 10 Mounts
```

### CORS Errors

Update `CORS_ORIGINS` in `docker-compose.yml` to include your app's domain.

### Port Conflicts

If port 8051 or 11434 are in use, change them:

```yaml
ports:
  - "9051:8051"  # Use port 9051 externally
```

## 🔄 Updating Your Database

### While Container is Running

Your database is mounted from `../../data/claude-os.db`. Any changes you make locally (using Claude OS) will be immediately visible to the container.

```bash
# No restart needed - changes are live!
# Just query the MCP endpoint and you'll see new data
```

### Deploying to Production

1. **Option A: Sync database periodically**
   ```bash
   # Cron job to sync from local to server
   rsync -avz data/claude-os.db user@server:/path/to/data/
   ```

2. **Option B: Use shared network storage**
   - Mount same NFS/S3 volume on both local and server

3. **Option C: Use database replication**
   - Set up SQLite replication (more complex)

## 📚 Next Steps

1. **Deploy this to your server** alongside your other apps
2. **Update CORS** to allow your chat/docs apps
3. **Enable authentication** for production
4. **Configure monitoring** (logs, health checks)
5. **Set up database sync** if needed

## 🆚 Comparison: This vs. Full Claude OS

| Feature | MCP-Only | Full Claude OS |
|---------|----------|----------------|
| Knowledge Base API | ✅ | ✅ |
| CLI Coding Assistant | ❌ | ✅ |
| Frontend UI | ❌ | ✅ |
| File Watchers | ❌ | ✅ |
| Spec Tracking | ❌ | ✅ |
| Project Management | ❌ | ✅ |
| Container Size | ~500MB | ~2GB |
| Memory Usage | ~200MB | ~1GB |

## 📞 Support

For issues specific to:
- **MCP Endpoints**: See `/docs/API_REFERENCE.md` in main repo
- **Deployment**: Open issue in claude-os repo
- **Your Apps Integration**: This is the right approach!

## 🎉 You're All Set!

Your knowledge bases are now available as an API for your other applications to consume. No coding environment needed - just pure data access!
