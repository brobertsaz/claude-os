# Start Scripts Guide

Claude OS has **two different start scripts** for different use cases:

---

## 1. `./start.sh` - MCP Server Only

**What it starts:**
- ✅ MCP Server (port 8051)

**What it does NOT start:**
- ❌ Frontend Web UI
- ❌ Redis
- ❌ RQ Workers
- ❌ Ollama

**Use when:**
- You only need Claude Code integration
- You don't need the visual web interface
- You want minimal services running
- Quick start for development

**Command:**
```bash
./start.sh
```

**Output:**
```
✅ Claude OS MCP Server is running!

   📡 MCP Server: http://localhost:8051
      (For Claude Code integration - do NOT open in browser)

💡 Want the full experience?
To start ALL services: ./start_all_services.sh
```

**What you can do:**
- ✅ Use Claude Code with `/claude-os-init`
- ✅ Use Claude Code commands (`/claude-os-search`, etc.)
- ❌ Can't access web UI (no frontend running)
- ❌ No real-time learning (no workers running)

---

## 2. `./start_all_services.sh` - Everything

**What it starts:**
- ✅ Ollama (port 11434) - Local AI models
- ✅ Redis (port 6379) - Cache & job queue
- ✅ RQ Workers - Background job processing
- ✅ MCP Server (port 8051) - API for Claude Code
- ✅ React Frontend (port 5173) - Web UI

**Use when:**
- You want the complete experience
- You need the web interface
- You want real-time learning features
- Production-like environment

**Command:**
```bash
./start_all_services.sh
```

**Output:**
```
==================================================
✅ All Services Started Successfully!
==================================================

📡 Service URLs:
   🎨 Frontend:    http://localhost:5173
   🔌 API Server:  http://localhost:8051
   📚 API Docs:    http://localhost:8051/docs

🔧 Ollama:
   Host:    http://localhost:11434
   Models:  llama3.1:latest, nomic-embed-text:latest

💾 Databases:
   SQLite:  data/claude-os.db
   Redis:   localhost:6379

🤖 Real-Time Learning System:
   RQ Workers: listening on 3 queues
```

**What you can do:**
- ✅ Use Claude Code integration
- ✅ Open web UI at http://localhost:5173
- ✅ Browse knowledge bases visually
- ✅ Upload documents via UI
- ✅ Real-time learning system active
- ✅ Full feature set

---

## Quick Comparison

| Feature | `start.sh` | `start_all_services.sh` |
|---------|------------|-------------------------|
| **MCP Server** | ✅ Port 8051 | ✅ Port 8051 |
| **Web UI** | ❌ | ✅ Port 5173 |
| **Ollama** | ❌ (must start manually) | ✅ Auto-started |
| **Redis** | ❌ | ✅ Auto-started |
| **RQ Workers** | ❌ | ✅ Background jobs |
| **Real-time Learning** | ❌ | ✅ Active |
| **Startup Time** | ~1 second | ~30 seconds |
| **Resource Usage** | Minimal | Moderate |

---

## Which Should You Use?

### Use `./start.sh` if:
- Just testing Claude Code integration
- Don't need web interface
- Want faster startup
- Minimal resource usage
- Development/debugging

### Use `./start_all_services.sh` if:
- Want full functionality
- Need web interface
- Want to browse/manage KBs visually
- Production or demo environment
- Want real-time learning features

---

## Common Mistakes

### ❌ Mistake 1: Opening MCP server in browser

**Problem:**
```bash
./start.sh
# Then opening http://localhost:8051 in browser
# → "Method Not Allowed" error
```

**Why:** MCP server (port 8051) is for Claude Code API calls, not browsers

**Solution:**
- Don't open 8051 in browser
- Use `./start_all_services.sh` and open http://localhost:5173 instead

### ❌ Mistake 2: Expecting Web UI with start.sh

**Problem:**
```bash
./start.sh
# Then trying to access http://localhost:5173
# → Connection refused
```

**Why:** `start.sh` doesn't start the frontend

**Solution:**
- Use `./start_all_services.sh` instead

### ❌ Mistake 3: Wrong port numbers

**Problem:** Confusing which service runs on which port

**Remember:**
- **Port 8051:** MCP Server (for Claude Code) - Don't open in browser!
- **Port 5173:** Web UI (for humans) - Open this in browser!

---

## Stopping Services

### Stop MCP Server Only (`start.sh`)

**Option 1:** Press `Ctrl+C` in the terminal

**Option 2:** Kill by PID
```bash
# PID shown when you start it
kill <PID>
```

### Stop All Services (`start_all_services.sh`)

**Use the stop script:**
```bash
./stop_all_services.sh
```

This will stop:
- MCP Server
- Frontend
- RQ Workers
- Redis (optional)
- Ollama (optional)

---

## Restarting Services

### Restart MCP Only

```bash
# Stop (Ctrl+C or kill PID)
./start.sh
```

### Restart Everything

```bash
./restart_services.sh
```

Or manually:
```bash
./stop_all_services.sh
./start_all_services.sh
```

---

## Logs

### MCP Server Logs

**If started with `start.sh`:**
- Output shows in terminal

**If started with `start_all_services.sh`:**
```bash
tail -f logs/mcp_server.log
```

### Frontend Logs

```bash
tail -f logs/frontend.log
```

### RQ Workers Logs

```bash
tail -f logs/rq_workers.log
```

### All Logs

```bash
tail -f logs/*.log
```

---

## Installation Recommendation

After running `./install.sh`, the README says:

```
1️⃣  Start Claude OS:
    ./start.sh
```

**But for the full experience, you should use:**
```
1️⃣  Start Claude OS (all services):
    ./start_all_services.sh
```

Then you can:
- Use Claude Code at port 8051
- Open web UI at http://localhost:5173
- Have full functionality

---

## Summary

**Remember:**
- `./start.sh` = MCP server only (minimal, fast)
- `./start_all_services.sh` = Everything (full features)

**For most users:**
```bash
./start_all_services.sh  # ← Recommended!
```

**Then access:**
- Web UI: http://localhost:5173 ✅ Open in browser
- MCP Server: http://localhost:8051 ❌ Don't open in browser (for Claude Code only)

**Problem solved!** 🎉
