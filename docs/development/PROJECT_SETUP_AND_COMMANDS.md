# Claude OS - Complete Setup & Command Reference 🛠️

*Everything you need to set up and operate Claude OS*

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Service Management Commands](#service-management-commands)
4. [Claude Code Commands](#claude-code-commands)
5. [Real-Time Learning Commands](#real-time-learning-commands)
6. [Project Analysis Commands](#project-analysis-commands)
7. [Memory & Knowledge Base Commands](#memory--knowledge-base-commands)
8. [Troubleshooting](#troubleshooting)
9. [Daily Workflows](#daily-workflows)

---

## Prerequisites

### Required Software

```bash
# macOS (using Homebrew)
brew install python@3.11
brew install redis
brew install ollama
brew install git
brew install node

# Verify installations
python3 --version      # Should be 3.11+
redis-cli --version    # Should be 6.0+
ollama --version       # Should be latest
node --version         # Should be 18+
npm --version          # Should be 9+
```

### Ollama Models

```bash
# Pull required models
ollama pull llama3.1:latest
ollama pull nomic-embed-text:latest

# Verify models
ollama list
```

---

## Initial Setup

### 1. Clone and Navigate

```bash
git clone <your-repo-url> code-forge
cd code-forge
```

### 2. Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

### 4. Initialize Databases

```bash
# Create data directory
mkdir -p data logs

# SQLite database will be created automatically on first run
```

### 5. Configure Claude Code

```bash
# Install Claude Code (if not already installed)
npm install -g @anthropic/claude-code

# Set up MCP servers directory
mkdir -p ~/.claude/mcp-servers/memory
mkdir -p ~/.claude/mcp-servers/project_profile

# Configure claude_macos.json (example below)
```

### 6. Start All Services

```bash
# Make scripts executable
chmod +x start_all_services.sh
chmod +x stop_all_services.sh
chmod +x restart_services.sh

# Start everything
./start_all_services.sh
```

---

## Service Management Commands

### 🚀 **Start All Services**

```bash
./start_all_services.sh
```

**What it does:**

1. Checks/starts Ollama (port 11434)
2. Sets up Python virtual environment
3. Creates data/logs directories
4. Starts Redis (port 6379)
5. Starts RQ Workers (real-time learning)
6. Starts MCP Server (port 8051)
7. Starts React Frontend (port 5173)

**Output:**

```
🚀 Claude OS - Starting All Services
==================================================
1. Checking Ollama...
   ✓ Ollama is running on port 11434
2. Setting up Python environment...
   ✓ Python environment ready
3. Checking data directory...
   ✓ data/ directory exists
4. Checking Redis...
   ✓ Redis is running
5. Starting RQ Workers (Real-Time Learning)...
   ✓ RQ workers started
6. Starting MCP Server...
   ✓ Server started on port 8051
7. Starting React Frontend...
   ✓ Frontend started on port 5173

✅ All Services Started Successfully!
```

### 🛑 **Stop All Services**

```bash
./stop_all_services.sh
```

**What it does:**

- Stops MCP Server (port 8051)
- Stops React Frontend (port 5173)
- Stops RQ Workers
- Stops Redis
- Preserves all data

### 🔄 **Restart All Services**

```bash
./restart_services.sh
```

**What it does:**

- Gracefully stops all services
- Waits for ports to be released
- Starts all services fresh

---

## Claude Code Commands

### Working with Memory

```bash
# In your Claude Code session

# Save something to memory
"Remember: We decided to use PostgreSQL instead of MySQL for better JSON support"

# Recall memories
"What do I remember about database decisions?"

# Search memories
"Show me memories about authentication"
```

### Working with Skills

#### Analyze Project Skill

```bash
# Run the analyze-project skill
/analyze-project

# What happens:
# 1. Prompts for project details
# 2. Indexes your codebase (25 files initially)
# 3. Sets up git hooks for auto-updates
# 4. Creates project profile in knowledge base
```

#### Creating Custom Skills

```bash
# Skills directory
~/.claude/skills/your-skill-name/

# Required files:
- skill.py          # Main skill logic
- requirements.txt  # Dependencies
- SKILL.md         # Documentation
```

---

## Real-Time Learning Commands

### Monitor Learning System

```bash
# Check if RQ workers are running
ps aux | grep "rq worker"

# View RQ worker logs
tail -f logs/rq_workers.log

# Check Redis status
redis-cli ping  # Should return PONG

# Monitor Redis pub/sub
redis-cli
> SUBSCRIBE claude-os:conversations
```

### Test Real-Time Learning

```bash
# Run the test suite
cd /Users/iamanmp/Projects/code-forge
python test_real_time_learning.py

# Expected output:
✅ Test 1 passed: Redis connection
✅ Test 2 passed: Redis pub/sub
✅ Test 3 passed: Trigger detection
✅ Test 4 passed: Job enqueuing
✅ Test 5 passed: Full pipeline

All tests passed!
```

### Trigger Learning Manually

```python
# In Python
from app.core.redis_config import publish_conversation

# Simulate a learning trigger
publish_conversation({
    "user_message": "We're switching from Bootstrap to Tailwind",
    "assistant_response": "I'll update our styles to use Tailwind",
    "timestamp": "2024-10-27T10:30:00Z"
})
```

---

## Project Analysis Commands

### Initial Project Setup

```bash
# From project root
cd ~/.claude/skills/analyze-project
python3 analyze_project.py

# Interactive prompts:
# 1. Enter project ID (e.g., "4")
# 2. Enter project path
# 3. Enter project name
# 4. Enter description
```

### Manual Re-indexing

```bash
# Force re-index of project
cd ~/.claude/skills/analyze-project
python3 incremental_indexer.py <project_id> <project_path> http://localhost:8051 30

# Example:
python3 incremental_indexer.py 4 /Users/you/myproject http://localhost:8051 30
```

### Git Hook Management

```bash
# Check if git hooks are installed
cat .git/hooks/post-commit

# Manually trigger git hook
./.claude-os/hooks/post-commit.sh

# View indexing state
cat .claude-os/.index_state
```

---

## Memory & Knowledge Base Commands

### MCP Server API

```bash
# Check MCP server health
curl http://localhost:8051/health

# View API documentation
open http://localhost:8051/docs

# Search knowledge base
curl -X POST http://localhost:8051/search \
  -H "Content-Type: application/json" \
  -d '{"query": "authentication", "limit": 5}'

# Ingest new document
curl -X POST http://localhost:8051/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Architecture Decision",
    "content": "We chose microservices...",
    "metadata": {"type": "decision"}
  }'
```

### Memory MCP Commands

```bash
# List all memories
ls ~/.claude/mcp-servers/memory/*.md

# Search memories (in Claude Code)
"Show me all memories about performance"

# Export memories
cat ~/.claude/mcp-servers/memory/*.md > memories_backup.md
```

### Knowledge Base Queries

```bash
# Using SQLite directly
sqlite3 data/claude-os.db

# Useful queries:
.tables                          # List all tables
SELECT COUNT(*) FROM documents;  # Document count
SELECT COUNT(*) FROM chunks;     # Chunk count

# Search for specific content
SELECT title, substring(content, 1, 100)
FROM documents
WHERE content LIKE '%authentication%';
```

---

## Troubleshooting

### Service Issues

#### MCP Server Won't Start

```bash
# Check if port is in use
lsof -i :8051

# Kill existing process
kill -9 $(lsof -i :8051 | grep LISTEN | awk '{print $2}')

# Check logs
tail -f logs/mcp_server.log
```

#### Frontend Won't Start

```bash
# Check port 5173
lsof -i :5173

# Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

#### Redis Issues

```bash
# Test Redis
redis-cli ping

# If not running
redis-server --daemonize yes

# Or with Homebrew
brew services restart redis
```

#### RQ Workers Not Processing

```bash
# Check worker status
ps aux | grep "rq worker"

# Restart workers
pkill -f "rq worker"
python -m rq worker claude-os:learning claude-os:prompts claude-os:ingest --with-scheduler
```

### Database Issues

#### Reset SQLite Database

```bash
# Backup existing
cp data/claude-os.db data/claude-os.db.backup

# Remove and restart
rm data/claude-os.db
./restart_services.sh
```

#### Clear Redis Cache

```bash
redis-cli FLUSHALL
```

### Ollama Issues

#### Models Not Found

```bash
# Re-pull models
ollama pull llama3.1:latest
ollama pull nomic-embed-text:latest

# Verify
ollama list
```

#### Ollama Not Responding

```bash
# Restart Ollama
brew services restart ollama

# Or manually
ollama serve
```

---

## Daily Workflows

### Morning Startup

```bash
# 1. Start all services
./start_all_services.sh

# 2. In Claude Code, recall context
"What were we working on yesterday?"

# 3. Check system status
"Show me the current project status"
```

### During Development

```bash
# Save important decisions
"Remember: We decided to cache API responses for 5 minutes"

# When switching technologies
"We're switching from REST to GraphQL for the admin API"
# → Automatically captured by real-time learning

# After fixing bugs
"Fixed the timezone bug in user registration"
# → Automatically learned and remembered
```

### Before Major Changes

```bash
# 1. Create a checkpoint
"Remember: Checkpoint before refactoring auth system - Oct 27"

# 2. Document the plan
"Remember: Plan to refactor auth - extract to microservice"

# 3. Proceed with changes
```

### End of Day

```bash
# 1. Summarize progress
"Remember: Today we completed the user dashboard and fixed 3 bugs"

# 2. Note tomorrow's tasks
"Remember: Tomorrow - implement email notifications"

# 3. Optionally stop services
./stop_all_services.sh
```

### Project Handoff

```bash
# Export all knowledge
sqlite3 data/claude-os.db .dump > knowledge_export.sql
tar -czf memories.tar.gz ~/.claude/mcp-servers/memory/

# Share with team
# - knowledge_export.sql (knowledge base)
# - memories.tar.gz (context memories)
# - .claude-os/ directory (project profile)
```

---

## Environment Variables

### Optional Configuration

```bash
# Create .env file
cat > .env << EOF
# API Configuration
API_URL=http://localhost:8051
FRONTEND_URL=http://localhost:5173

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:latest
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:latest

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Logging
LOG_LEVEL=INFO
EOF
```

---

## Claude Config Example

### ~/.claude/claude_macos.json

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "env": {}
    },
    "project_profile": {
      "command": "python",
      "args": ["/Users/you/code-forge/mcp_server/server.py"],
      "env": {}
    }
  }
}
```

---

## Quick Reference Card

```
SERVICE MANAGEMENT
├── ./start_all_services.sh     # Start everything
├── ./stop_all_services.sh      # Stop everything
└── ./restart_services.sh       # Restart everything

URLS
├── Frontend:    http://localhost:5173
├── API Server:  http://localhost:8051
├── API Docs:    http://localhost:8051/docs
└── Ollama:      http://localhost:11434

PORTS
├── 5173  - React Frontend
├── 8051  - MCP Server
├── 11434 - Ollama
└── 6379  - Redis

LOGS
├── logs/mcp_server.log   - MCP Server logs
├── logs/frontend.log     - Frontend logs
└── logs/rq_workers.log   - Learning system logs

KEY DIRECTORIES
├── data/                 - SQLite database
├── logs/                 - All log files
├── ~/.claude/skills/     - Claude Code skills
└── ~/.claude/mcp-servers/ - MCP configurations
```

---

## Getting Help

### Check System Status

```bash
# Quick health check
curl http://localhost:8051/health

# Detailed status
./status_check.sh  # (if available)
```

### View Logs

```bash
# All logs at once
tail -f logs/*.log

# Specific service
tail -f logs/mcp_server.log
tail -f logs/rq_workers.log
```

### Common Issues

- **"Port already in use"** → Use `./restart_services.sh`
- **"Model not found"** → Run `ollama pull llama3.1:latest`
- **"Redis not connected"** → Run `redis-server --daemonize yes`
- **"No memories found"** → Memories are project-specific, check current project

---

*With Claude OS properly set up, Claude becomes your most knowledgeable team member - always learning, never forgetting.*
