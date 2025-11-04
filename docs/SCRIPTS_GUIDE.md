# Claude OS Scripts Guide 🚀

Quick reference for managing Claude OS services on macOS.

## Quick Start

```bash
# First time setup (installs dependencies)
./scripts/setup_native.sh

# Start all services
./start_all_services.sh

# Restart services
./restart_services.sh

# Stop all services
./stop_all_services.sh
```

---

## Scripts Overview

### 1. `setup_native.sh` - Initial Setup

**When to use:**
- First time setting up Claude OS
- After cloning the repository
- When dependencies are missing

**What it does:**
- ✅ Checks Ollama installation
- ✅ Pulls required AI models (llama3.1, nomic-embed-text)
- ✅ Creates Python virtual environment
- ✅ Installs Python dependencies from `requirements.txt`
- ✅ Creates `data/` directory for SQLite database
- ✅ Creates `logs/` directory for output files
- ✅ Sets up Node.js frontend (if installed)

**Usage:**
```bash
./scripts/setup_native.sh
```

**Output:**
```
🚀 Claude OS Setup - NATIVE (SQLite + Ollama)
==================================================
Step 1: Checking Ollama installation...
  ✅ Ollama found
  ✅ Ollama is running on port 11434
  Checking models... ✓

Step 2: Pulling required models...
  [models download output...]
  ✅ Models ready

Step 3: Setting up Python environment...
  ✅ Python 3.14 found
  Installing Python dependencies...
  ✅ Python environment ready

Step 4: Creating data directory...
  ✅ Created data/ directory
  ✅ Created logs/ directory

Step 5: Initializing SQLite database...
  ✅ SQLite schema file found
  💾 Database will be created at: data/claude-os.db

Step 6: Setting up Node.js frontend...
  ✅ Node.js v20.x found
  ✅ Frontend dependencies ready

✅ Claude OS Setup Complete!
```

---

### 2. `start_all_services.sh` - Start Services

**When to use:**
- After setup is complete
- Every time you want to start working
- After stopping services

**What it does:**
- ✅ Checks Ollama is running (starts if needed)
- ✅ Verifies AI models are available
- ✅ Sets up Python environment
- ✅ Creates data directory if missing
- ✅ Starts MCP Server (port 8051)
- ✅ Starts React Frontend (port 5173)
- ✅ Shows URLs and logs

**Usage:**
```bash
./start_all_services.sh
```

**Output:**
```
🚀 Claude OS - Starting All Services
==================================================

1. Checking Ollama...
   ✓ Ollama is running on port 11434
   Checking models... ✓

2. Setting up Python environment...
   ✓ Python environment ready

3. Checking data directory...
   ✓ data/ directory exists
   ✓ logs/ directory exists

4. Starting MCP Server...
   Server PID: 12345 (logging to logs/mcp_server.log)
   Waiting for server to start... ✓

5. Starting React Frontend...
   Frontend PID: 12346 (logging to logs/frontend.log)
   Waiting for frontend to start... ✓

✅ All Services Started Successfully!

📡 Service URLs:
   🎨 Frontend:    http://localhost:5173
   🔌 API Server:  http://localhost:8051
   📚 API Docs:    http://localhost:8051/docs

🔧 Ollama:
   Host:    http://localhost:11434
   Models:  llama3.1:latest, nomic-embed-text:latest

💾 Database:
   Type:     SQLite (single file)
   Location: data/claude-os.db

📝 Log Files:
   MCP Server:  logs/mcp_server.log
   Frontend:    logs/frontend.log

🛑 To Stop All Services:
   ./stop_all_services.sh

🔄 To Restart All Services:
   ./restart_services.sh
```

---

### 3. `stop_all_services.sh` - Stop Services

**When to use:**
- When you're done working
- Before restarting
- To free up ports

**What it does:**
- ✅ Stops MCP Server (port 8051)
- ✅ Stops React Frontend (port 5173)
- ✅ Preserves SQLite database
- ✅ Leaves Ollama running (used by other apps)

**Usage:**
```bash
./stop_all_services.sh
```

**Output:**
```
🛑 Claude OS - Stopping All Services
==================================================

Stopping 🔌 MCP Server (port 8051)...
   ✓ MCP Server stopped (PID: 12345)
Stopping 🎨 React Frontend (port 5173)...
   ✓ React Frontend stopped (PID: 12346)

✅ All Claude OS services stopped

ℹ️  Note:
   - Ollama is NOT stopped (may be used by other apps)
   - SQLite database (data/claude-os.db) is preserved

To restart:
   ./restart_services.sh

To start with full setup:
   ./start_all_services.sh
```

---

### 4. `restart_services.sh` - Restart Services

**When to use:**
- After code changes to backend
- When services are behaving strangely
- As a quick restart command

**What it does:**
- ✅ Stops all services
- ✅ Waits for ports to be released
- ✅ Starts all services again

**Usage:**
```bash
./restart_services.sh
```

---

## Common Workflows

### First Time Setup

```bash
# 1. Clone the repo
git clone <repo>
cd claude-os

# 2. Run setup
./scripts/setup_native.sh

# 3. Start services
./start_all_services.sh

# 4. Open browser
open http://localhost:5173
```

### Daily Development

```bash
# Morning: start services
./start_all_services.sh

# Work on features...

# Change backend code?
./restart_services.sh

# Frontend auto-reloads, no restart needed

# End of day: stop services
./stop_all_services.sh
```

### Troubleshooting

```bash
# Check if services are running
lsof -i :5173  # Frontend
lsof -i :8051  # MCP Server

# View logs
tail -f logs/mcp_server.log
tail -f logs/frontend.log

# Restart if something is wrong
./restart_services.sh

# Clear old database and start fresh
rm data/claude-os.db
./start_all_services.sh
```

---

## Ports Used

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 5173 | React dev server |
| MCP Server | 8051 | API & RAG engine |
| Ollama | 11434 | LLM inference |

---

## Environment Requirements

### macOS
- Ollama (installed via `brew install ollama`)
- Python 3.11+ (`python3 --version`)
- Node.js 18+ (`npm --version`, optional for frontend)

### Files Used

```
data/
  ├── claude-os.db          # SQLite database (auto-created)
  └── uploads/              # User-uploaded documents

logs/
  ├── mcp_server.log        # MCP Server logs
  └── frontend.log          # Frontend logs

venv/                        # Python virtual environment
```

---

## Advanced Usage

### Kill Specific Port

```bash
# Kill process on port 8051
lsof -i :8051 | grep -v COMMAND | awk '{print $2}' | xargs kill -9
```

### View Real-time Logs

```bash
# Watch MCP Server logs
tail -f logs/mcp_server.log

# Watch Frontend logs
tail -f logs/frontend.log

# Follow both
tail -f logs/*.log
```

### Backup Database

```bash
# Create backup
cp data/claude-os.db data/claude-os.db.backup

# Restore from backup
cp data/claude-os.db.backup data/claude-os.db
```

### Reset Everything

```bash
# Stop services
./stop_all_services.sh

# Clear database
rm data/claude-os.db

# Re-setup
./scripts/setup_native.sh

# Start fresh
./start_all_services.sh
```

---

## Tips & Tricks

### 🚀 Fast Restart

```bash
# One-liner restart
./stop_all_services.sh && sleep 2 && ./start_all_services.sh
```

### 📊 Monitor Resources

```bash
# Watch CPU/Memory usage
top -o %CPU

# Watch Ollama model usage
ollama ps
```

### 🔧 Debug Mode

```bash
# Run server directly (no background)
source venv/bin/activate
cd mcp_server
python server.py
```

### 🎨 Frontend Development

```bash
# Frontend auto-reloads on file changes
# No restart needed for React components
# Only restart for Python changes
```

---

## Troubleshooting

### "Port already in use"

```bash
# Check what's using the port
lsof -i :8051

# Kill the process
kill -9 <PID>

# Or use our stop script
./stop_all_services.sh
```

### "Ollama is not running"

```bash
# Check status
ollama ps

# Start Ollama
brew services start ollama

# Or manually
ollama serve
```

### "Module not found" errors

```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements.txt
```

### Database corrupted?

```bash
# Backup old database
mv data/claude-os.db data/claude-os.db.old

# Restart (creates new database)
./start_all_services.sh

# Restore if needed
mv data/claude-os.db.old data/claude-os.db
```

---

## Support

Check logs for errors:
```bash
tail -50 logs/mcp_server.log
tail -50 logs/frontend.log
```

For issues:
1. Check logs
2. Try `./restart_services.sh`
3. Try `./scripts/setup_native.sh` again
4. Check if Ollama is running: `ollama ps`

---

**Ready to go!** 🚀

Next: Open http://localhost:5173 and start building! 💪
