# Cloudflare Workers Deployment (Alternative Approach)

This directory contains a **starter template** for deploying Claude OS MCP endpoints on Cloudflare Workers, similar to the [cloudflare_mcp](https://github.com/forayconsulting/cloudflare_mcp) project.

> ⚠️ **Important**: This is a **significant undertaking** compared to the Docker approach. Only use this if you need global distribution and auto-scaling.

## What This Requires

### 1. Cloudflare Account Setup
- Cloudflare account (free tier available)
- D1 database (Cloudflare's SQLite service)
- Vectorize (Cloudflare's vector search service)
- Workers AI (for embeddings)

### 2. Code Rewrite
- Rewrite all Python code → JavaScript/TypeScript
- Reimplement SQLiteManager → D1 queries
- Reimplement RAGEngine → Vectorize queries
- Port all 12 MCP tools

### 3. Data Migration
- Export SQLite schema and data
- Import to D1
- Extract vectors and import to Vectorize
- Set up sync process (if needed)

## Estimated Effort

| Task | Time Estimate |
|------|--------------|
| Setup Cloudflare infrastructure | 2-4 hours |
| Migrate database schema | 1-2 hours |
| Migrate data and vectors | 2-4 hours |
| Rewrite MCP endpoints | 8-16 hours |
| Testing and debugging | 4-8 hours |
| **Total** | **17-34 hours** |

Compare to Docker approach: **5 minutes**

## When to Use This

✅ Only use Cloudflare Workers if:
- You have **global users** across continents
- You need **automatic scaling** beyond a single server
- You're okay with **vendor lock-in** to Cloudflare
- You have **time to rewrite** the codebase in JavaScript
- Your database is **< 500MB** (free tier limit)

Otherwise, use the Docker approach.

## Quick Start

### 1. Install Wrangler (Cloudflare CLI)

```bash
npm install -g wrangler

# Login to Cloudflare
wrangler login
```

### 2. Create D1 Database

```bash
# Create database
wrangler d1 create claude-os-db

# This will output a database ID - save it!
```

### 3. Export Your SQLite Database

```bash
# From the root of claude-os repo
sqlite3 data/claude-os.db .dump > deployment/mcp-only/cloudflare-workers/schema.sql
```

### 4. Import to D1

```bash
cd deployment/mcp-only/cloudflare-workers

# Import schema and data
wrangler d1 execute claude-os-db --file=schema.sql
```

### 5. Create Vectorize Index

```bash
# Create vector index (for embeddings)
wrangler vectorize create claude-os-vectors --dimensions=768 --metric=cosine

# Note: You'll need to export and import your vectors separately
```

### 6. Configure wrangler.toml

Edit `wrangler.toml` with your database and vectorize IDs:

```toml
name = "claude-os-mcp"
main = "src/index.ts"
compatibility_date = "2024-01-01"

[[d1_databases]]
binding = "DB"
database_name = "claude-os-db"
database_id = "your-database-id-here"

[[vectorize]]
binding = "VECTORIZE"
index_name = "claude-os-vectors"
index_id = "your-vectorize-id-here"

[ai]
binding = "AI"
```

### 7. Implement MCP Endpoints

See `src/index.ts` for a basic example. You'll need to implement all tools:

```typescript
// Example structure
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const { pathname } = new URL(request.url);

    // Health check
    if (pathname === '/health') {
      return new Response(JSON.stringify({ status: 'ok' }));
    }

    // MCP endpoint
    if (pathname === '/mcp') {
      const body = await request.json();
      const result = await handleMCPRequest(body, env);
      return new Response(JSON.stringify(result));
    }

    return new Response('Not found', { status: 404 });
  }
};
```

### 8. Deploy

```bash
wrangler deploy
```

Your MCP server will be available at: `https://claude-os-mcp.your-subdomain.workers.dev`

## Code Structure

```
cloudflare-workers/
├── src/
│   ├── index.ts              # Main worker entry point
│   ├── handlers/
│   │   ├── search.ts         # Search knowledge base
│   │   ├── list.ts           # List KBs
│   │   └── ...               # Other tools
│   ├── db/
│   │   ├── queries.ts        # D1 query helpers
│   │   └── schema.ts         # Type definitions
│   └── utils/
│       ├── embeddings.ts     # Workers AI embeddings
│       └── vectorize.ts      # Vectorize queries
├── wrangler.toml             # Cloudflare config
├── package.json
├── tsconfig.json
└── schema.sql                # Exported database
```

## Key Differences from Python Version

### Database Access

**Python (SQLiteManager):**
```python
def query_documents(kb_name, query_embedding, n_results):
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT ... FROM documents WHERE ...")
    return cursor.fetchall()
```

**TypeScript (D1):**
```typescript
async function queryDocuments(env: Env, kbName: string, n: number) {
  const results = await env.DB.prepare(
    "SELECT ... FROM documents WHERE ..."
  ).all();
  return results;
}
```

### Vector Search

**Python (sqlite-vec):**
```python
cursor.execute("""
    SELECT *, vec_distance_cosine(embedding, ?) as distance
    FROM documents
    ORDER BY distance
    LIMIT ?
""", [query_embedding, n_results])
```

**TypeScript (Vectorize):**
```typescript
const matches = await env.VECTORIZE.query(queryEmbedding, {
  topK: n,
  returnMetadata: true
});
```

### Embeddings

**Python (Ollama):**
```python
from llama_index.embeddings.ollama import OllamaEmbedding

embedding_model = OllamaEmbedding(
    model_name="nomic-embed-text",
    base_url="http://localhost:11434"
)
embedding = embedding_model.get_query_embedding(text)
```

**TypeScript (Workers AI):**
```typescript
const embedding = await env.AI.run('@cf/baai/bge-base-en-v1.5', {
  text: queryText
});
```

## Migration Script Example

Here's a script to export your vectors for Vectorize:

```python
# export_vectors.py
import sqlite3
import json

conn = sqlite3.connect('../../data/claude-os.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT id, embedding, metadata
    FROM documents
""")

vectors = []
for doc_id, embedding, metadata in cursor.fetchall():
    vectors.append({
        'id': str(doc_id),
        'values': list(embedding),  # Convert BLOB to list
        'metadata': json.loads(metadata)
    })

with open('vectors.json', 'w') as f:
    json.dump(vectors, f)
```

Then import to Vectorize:
```bash
# You'll need to use the Vectorize API
# See: https://developers.cloudflare.com/vectorize/
```

## Limitations

### Free Tier
- D1: 5 GB storage, 5M rows read/day, 100K writes/day
- Vectorize: 30M queries/month, 10M dimensions stored
- Workers: 100K requests/day, 10ms CPU per request

### Paid Tier Required For
- Large databases (> 500MB)
- High query volume (> 100K/day)
- Long-running queries (> 10ms CPU)

## Testing Locally

```bash
# Install dependencies
npm install

# Run local dev server
wrangler dev

# Test endpoint
curl http://localhost:8787/health
```

## Comparison with Docker Approach

| Feature | Docker | Cloudflare Workers |
|---------|--------|-------------------|
| Setup time | 5 min | 17-34 hours |
| Code changes | None | Complete rewrite |
| Database | Direct use | Must migrate |
| Scaling | Manual | Automatic |
| Cost (small) | $0 | $0 |
| Cost (large) | Fixed | Variable |
| Latency | Regional | Global |

## My Recommendation

**Unless you have specific requirements for global distribution, use the Docker approach.**

The Cloudflare Workers approach is powerful but requires significant development effort. It's best suited for:
- Public-facing APIs with global users
- Applications that need to scale to millions of requests
- Teams with JavaScript/TypeScript expertise

For most use cases, Docker on your server is simpler, faster, and more maintainable.

## Resources

- [Cloudflare Workers Docs](https://developers.cloudflare.com/workers/)
- [D1 Database Docs](https://developers.cloudflare.com/d1/)
- [Vectorize Docs](https://developers.cloudflare.com/vectorize/)
- [Workers AI Docs](https://developers.cloudflare.com/workers-ai/)
- [Example: cloudflare_mcp](https://github.com/forayconsulting/cloudflare_mcp)
