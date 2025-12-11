# Claude OS Ports Guide

## Two Different Services

Claude OS has **two separate services** running on **different ports**:

### 1. MCP Server (Port 8051)

**Purpose:** API server for Claude Code integration

**Technology:** FastAPI (Python)

**URL:** `http://localhost:8051`

**Usage:**
- Used by Claude Code (via MCP protocol)
- Handles AI memory operations
- Manages knowledge bases
- Serves API endpoints

**⚠️ IMPORTANT:**
- **Do NOT open this in a web browser**
- It expects MCP protocol POST requests
- Browser GET requests will show "Method Not Allowed"

**How to start:**
```bash
./start.sh  # Starts MCP server
```

---

### 2. Web UI (Port 5173)

**Purpose:** Visual interface for humans

**Technology:** React + Vite (JavaScript)

**URL:** `http://localhost:5173`

**Usage:**
- Browse knowledge bases
- Upload documents
- Search and query
- Project management
- Visual interface

**✅ CORRECT:**
- **Open this URL in your browser**
- Designed for human interaction
- Nice visual interface

**How to start:**
```bash
cd frontend
npm install     # First time only
npm run dev     # Starts on port 5173
```

---

## Quick Reference

| Service | Port | Open in Browser? | Purpose |
|---------|------|------------------|---------|
| **MCP Server** | 8051 | ❌ NO | For Claude Code (API) |
| **Web UI** | 5173 | ✅ YES | For humans (visual interface) |

---

## Common Confusion

### ❌ Wrong: Opening http://localhost:8051 in browser

**What you see:**
```json
{
  "detail": "Method Not Allowed"
}
```

**Why:** The MCP server expects POST requests with MCP protocol data, not browser GET requests.

### ✅ Correct: Opening http://localhost:5173 in browser

**What you see:**
- Nice web interface
- Project management
- Knowledge base browser
- Document upload

---

## Typical Workflow

### 1. Start MCP Server (for Claude Code)

```bash
./start.sh
```

**Output:**
```
✅ Claude OS is running!

   📡 MCP Server: http://localhost:8051
      (For Claude Code integration - do NOT open in browser)
```

### 2. Start Web UI (optional, for visual interface)

```bash
cd frontend
npm run dev
```

**Output:**
```
  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

Now you can:
- Use Claude Code with MCP server (port 8051)
- Open Web UI in browser (port 5173)

---

## Testing Each Service

### Test MCP Server (Port 8051)

**Correct way (API call):**
```bash
curl -X POST http://localhost:8051/mcp/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

**Wrong way (browser):**
```
Open http://localhost:8051 in browser
→ Shows "Method Not Allowed" ❌
```

### Test Web UI (Port 5173)

**Correct way:**
```
Open http://localhost:5173 in browser
→ Shows nice web interface ✅
```

---

## Troubleshooting

### "Method Not Allowed" error

**Problem:** You're trying to access the MCP server (port 8051) in a browser

**Solution:**
- Don't open port 8051 in browser
- That's for Claude Code to use, not humans
- If you want a web interface, start the frontend (port 5173)

### "Connection refused" on port 5173

**Problem:** Web UI is not running

**Solution:**
```bash
cd frontend
npm install  # If first time
npm run dev
```

### "Connection refused" on port 8051

**Problem:** MCP server is not running

**Solution:**
```bash
./start.sh
```

---

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│        YOUR BROWSER                     │
│   http://localhost:5173 ✅              │
│   (Web UI - React)                      │
└──────────────┬──────────────────────────┘
               │ HTTP requests
               ▼
┌─────────────────────────────────────────┐
│    MCP Server (FastAPI)                 │
│    http://localhost:8051                │
│                                         │
│    ┌──────────────┐    ┌─────────┐    │
│    │  API Routes  │◄───┤ Claude  │    │
│    │              │    │  Code   │    │
│    └──────┬───────┘    └─────────┘    │
│           │                             │
│           ▼                             │
│    ┌──────────────┐                    │
│    │   Database   │                    │
│    │  (SQLite)    │                    │
│    └──────────────┘                    │
└─────────────────────────────────────────┘
```

**Access patterns:**
- Browser → Port 5173 (Web UI) → Port 8051 (MCP Server) → Database
- Claude Code → Port 8051 (MCP Server) → Database

---

## Summary

**Remember:**
- 🔴 **Port 8051:** For Claude Code (MCP protocol) - Don't open in browser!
- 🟢 **Port 5173:** For humans (Web UI) - Open this in browser!

**When you run `./start.sh`:**
- MCP server starts on 8051 (for Claude Code)
- Web UI does NOT start automatically
- Start Web UI separately with `cd frontend && npm run dev`

**Clear now?** 🚀
