# Agent OS Knowledge Base Setup & Optimization Guide

## 🎯 Purpose
The Agent OS KB type is designed to give Claude CLI deep understanding of your project structure, standards, workflows, and specifications from https://github.com/buildermethods/agent-os.

## 📁 Agent OS Profile Structure

Agent OS profiles should follow this structure:
```
agent-os/
├── standards/       # Coding standards, conventions
├── workflows/       # Development workflows, processes
├── specs/          # Feature specifications
├── product/        # Product vision, context
└── docs/           # General documentation
```

## 🚀 Quick Setup Steps

### 1. Clone the Agent OS Repository
```bash
# Clone the agent-os project
git clone https://github.com/buildermethods/agent-os.git /tmp/agent-os
```

### 2. Create an Agent OS Knowledge Base
```bash
# Using the MCP tool in Claude CLI
# Or via curl:
curl -X POST http://localhost:8051/api/kb \
  -H "Content-Type: application/json" \
  -d '{
    "name": "agent-os-project",
    "kb_type": "agent-os",
    "description": "Agent OS project knowledge base"
  }'
```

### 3. Ingest the Agent OS Profile
```python
# Via MCP tool in Claude CLI:
# Use: ingest_agent_os_profile
# kb_name: "agent-os-project"
# profile_path: "/tmp/agent-os"
```

Or via Python script:
```python
from app.core.pg_manager import get_pg_manager
from app.core.agent_os_ingestion import AgentOSIngestion

pg_manager = get_pg_manager()
ingestion = AgentOSIngestion(pg_manager)

stats = ingestion.ingest_profile(
    kb_name="agent-os-project",
    profile_path="/tmp/agent-os"
)
print(f"Ingested {stats['documents_processed']} documents")
```

## ⚡ Performance Optimizations for Agent OS KBs

### 1. Optimize Agent OS Query Settings

Agent OS KBs default to ALL advanced features enabled:
- `use_hybrid: true` - Combines vector + keyword search
- `use_rerank: true` - Reranks results for relevance
- `use_agentic: true` - Uses SubQuestion decomposition

**For faster queries**, selectively disable features:

```python
# Fast query (5-10s) - Basic vector search only
result = search_knowledge_base(
    kb_name="agent-os-project",
    query="What are the coding standards?",
    use_hybrid=False,    # Disable hybrid search
    use_rerank=False,    # Disable reranking
    use_agentic=False    # Disable agentic mode
)

# Balanced query (10-15s) - With hybrid search
result = search_knowledge_base(
    kb_name="agent-os-project",
    query="How do we handle authentication?",
    use_hybrid=True,     # Enable for better keyword matching
    use_rerank=False,    # Still skip reranking
    use_agentic=False    # Skip sub-question decomposition
)

# Comprehensive query (20-30s) - All features for complex questions
result = search_knowledge_base(
    kb_name="agent-os-project",
    query="Explain the entire deployment workflow and CI/CD pipeline",
    use_hybrid=True,     # Full hybrid search
    use_rerank=True,     # Rerank for best relevance
    use_agentic=True     # Break into sub-questions
)
```

### 2. Create Specialized Queries by Content Type

Agent OS content is categorized. Use type-specific searches for speed:

```python
# Fast: Query specific content types
standards = get_standards(kb_name="agent-os-project", query="python")
workflows = get_workflows(kb_name="agent-os-project", query="deployment")
specs = get_specs(kb_name="agent-os-project", query="authentication")
product = get_product_context(kb_name="agent-os-project")
```

### 3. Pre-warm Cache for Agent OS KB

Add to your startup script:
```python
# Pre-warm the Agent OS RAGEngine cache
from mcp_server.server import get_cached_rag_engine

# This creates and caches the engine at startup
engine = get_cached_rag_engine("agent-os-project")
print("Agent OS knowledge base cache warmed")
```

## 📊 Expected Performance with Agent OS

### Query Performance by Type
| Query Type | Features | First Query | Cached Query |
|------------|----------|-------------|--------------|
| Simple lookup | None | 15-20s | 5-8s |
| Standard search | Hybrid | 20-25s | 8-12s |
| Complex analysis | All | 30-40s | 15-20s |

### Why Agent OS Can Be Slower
1. **Richer content structure** - Multiple document types
2. **Complex relationships** - Cross-references between standards/specs
3. **Agentic mode overhead** - Sub-question decomposition adds 5-10s

## 🎯 Best Practices for Agent OS KBs

### 1. Document Organization
```
# Good: Clear, organized structure
agent-os/
├── standards/
│   ├── python-style.md
│   ├── api-design.md
│   └── testing-guidelines.md
├── workflows/
│   ├── dev-workflow.md
│   └── deployment.md
└── specs/
    ├── auth-spec.md
    └── api-spec.md
```

### 2. Query Strategies
```python
# ❌ Slow: Vague, requires agentic decomposition
"Tell me everything about the project"

# ✅ Fast: Specific, targeted queries
"What are the Python coding standards?"
"Show me the authentication workflow"
"What is the API rate limiting spec?"
```

### 3. MCP Integration in Claude CLI

Configure your MCP client settings:
```json
{
  "mcpServers": {
    "code-forge": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "DEFAULT_KB": "agent-os-project",
        "DEFAULT_USE_HYBRID": "false",
        "DEFAULT_USE_RERANK": "false"
      }
    }
  }
}
```

## 🔍 Monitoring Agent OS Queries

Watch the logs to understand performance:
```bash
# See which features are being used
docker-compose logs -f mcp_server | grep -E "agent-os|agentic|hybrid|rerank"

# Monitor cache hits
docker-compose logs -f mcp_server | grep "cached RAGEngine"

# Track query times
docker-compose logs -f mcp_server | grep "Query executed"
```

## 🚨 Common Issues & Solutions

### Issue: "Agent OS profile not found"
**Solution**: Ensure the profile directory follows the expected structure with standards/, workflows/, specs/, product/ subdirectories.

### Issue: Slow Agent OS queries (30-40s)
**Solutions**:
1. Disable agentic mode unless needed
2. Use type-specific queries (get_standards, get_workflows)
3. Ensure RAGEngine cache is working
4. Consider increasing cache TTL for Agent OS KBs

### Issue: Poor context retrieval from Agent OS
**Solutions**:
1. Ensure documents are well-structured with clear headings
2. Use more specific queries
3. Increase TOP_K_RETRIEVAL for Agent OS queries specifically

## 📝 Example: Optimized Agent OS Query Flow

```python
# 1. First, warm the cache (do once at startup)
engine = get_cached_rag_engine("agent-os-project")

# 2. For quick lookups, use type-specific queries
standards = get_standards("agent-os-project", "python style")
# Returns in 2-3s with cache

# 3. For general questions, start without agentic mode
result = search_knowledge_base(
    "agent-os-project",
    "How do we handle user authentication?",
    use_hybrid=True,
    use_rerank=False,
    use_agentic=False
)
# Returns in 8-10s with cache

# 4. Only use full features for complex, multi-part questions
result = search_knowledge_base(
    "agent-os-project",
    "Explain the complete CI/CD pipeline including testing, deployment, and rollback procedures",
    use_hybrid=True,
    use_rerank=True,
    use_agentic=True
)
# Returns in 15-20s with cache, but provides comprehensive answer
```

## 🎯 Next Steps

1. **Ingest your Agent OS profile** using the steps above
2. **Test with simple queries first** to warm the cache
3. **Use type-specific queries** when possible for speed
4. **Monitor logs** to understand which features impact performance
5. **Adjust feature flags** based on your query complexity needs

---

**Agent OS Integration Guide for Claude CLI** 🤖