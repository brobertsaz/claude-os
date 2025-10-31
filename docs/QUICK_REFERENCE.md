# Claude OS Quick Reference Guide

**Version**: 1.0.0
**Date**: 2025-10-30

---

## 🎯 Essential Commands

### Claude OS Slash Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/claude-os-init` | Initialize new project with Claude OS | `/claude-os-init` |
| `/claude-os-search [query]` | Search across knowledge bases | `/claude-os-search "appointment flow"` |
| `/claude-os-remember [content]` | Quick save to project memories | `/claude-os-remember "Fixed bug in controller by..."` |
| `/claude-os-save [title]` | Full-featured save with KB selection | `/claude-os-save "New Integration Pattern"` |
| `/claude-os-list` | List all knowledge bases | `/claude-os-list` |
| `/claude-os-session [action]` | Manage development sessions | `/claude-os-session start` |
| `/claude-os-triggers` | Manage trigger phrases | `/claude-os-triggers list` |

### Skills (Auto-Trigger)

| Skill | Trigger Phrases | What It Does |
|-------|----------------|--------------|
| `remember-this` | "remember this:", "save this:", "document this:" | Automatically saves to memories |
| `initialize-project` | Manual invocation | Analyzes codebase, generates standards |
| `memory` | Manual invocation | Simple memory management |

### Agent-OS Commands (If Installed)

| Command | Description | Use Case |
|---------|-------------|----------|
| `/new-spec [name]` | Initialize feature specification | `/new-spec user-authentication` |
| `/create-spec` | Full spec workflow with questions | After `/new-spec`, gather requirements |
| `/plan-product` | Create product documentation | Mission, roadmap, tech stack |
| `/implement-spec [name]` | Implement feature following tasks | `/implement-spec user-authentication` |

---

## 📚 Knowledge Base Types

**Auto-created for each project:**

1. **`{project}-project_memories`** - Your AI's memory
   - Decisions made during development
   - Patterns discovered
   - Bug fixes and solutions
   - Architecture choices

2. **`{project}-project_profile`** - Standards & practices
   - Coding standards
   - Architecture documentation
   - Development practices
   - Tech stack details

3. **`{project}-project_index`** - Codebase index
   - File structure
   - Key components
   - Integration points

4. **`{project}-knowledge_docs`** - Documentation
   - Project README
   - API docs
   - User guides
   - Technical specifications

---

## 🔄 Common Workflows

### Start New Session

```bash
# 1. Check if session exists (automatic prompt)
# 2. Choose: continue, start new, or just chat
# 3. Claude loads relevant memories automatically
```

### Save Important Insight

```bash
# Quick save (to project_memories)
/claude-os-remember "Discovered that Rails 4 doesn't support X, use Y instead"

# Full save (choose KB and category)
/claude-os-save "Rails 4 API Workaround" MyProject-project_memories Troubleshooting
```

### Search for Past Work

```bash
# Search all memories
/claude-os-search "how did we handle appointments"

# Search specific KB
/claude-os-search "integration patterns" MyProject-knowledge_docs
```

### Create Feature Specification (with Agent-OS)

```bash
# 1. Initialize spec
/new-spec manual-appointment-times

# 2. Start spec creation workflow
/create-spec
# Answer 1-3 questions at a time
# Upload screenshots/mockups if needed
# Review generated spec.md and tasks.md

# 3. Implement the spec
/implement-spec manual-appointment-times
# Claude follows tasks.md step-by-step

# 4. Verify implementation
# Agent runs checks automatically
```

---

## 🔧 Production Commands (Server)

### Service Management

```bash
# Start/Stop/Restart
sudo systemctl start claude-os
sudo systemctl stop claude-os
sudo systemctl restart claude-os
sudo systemctl status claude-os

# View logs in real-time
sudo journalctl -u claude-os -f
tail -f /opt/claude-os/logs/claude-os.log
```

### Health Checks

```bash
# Check MCP server
curl http://localhost:8051/health

# Check Ollama
curl http://localhost:11434/api/tags

# List knowledge bases
curl http://localhost:8051/api/kb/list

# Get KB statistics
curl http://localhost:8051/api/kb/MyProject-knowledge_docs/stats
```

### Backups

```bash
# Manual backup
/opt/claude-os/backup.sh

# Restore from backup
sudo systemctl stop claude-os
cp /opt/claude-os-backups/claude-os-YYYYMMDD_HHMMSS.db \
   /opt/claude-os/data/claude-os.db
sudo systemctl start claude-os
```

### Copy Local Database to Production (SECRET SAUCE!)

```bash
# Copy your local Claude OS database (with all knowledge) to production
# This transfers ALL memories, indexed code, and learned patterns!

# From your Mac:
scp ~/Projects/claude-os/data/claude-os.db \
    deploy@staging.pistn.com:/tmp/claude-os-local.db

# On the server:
sudo systemctl stop claude-os
sudo cp /tmp/claude-os-local.db /opt/claude-os/data/claude-os.db
sudo chown deploy:deploy /opt/claude-os/data/claude-os.db
sudo systemctl start claude-os

# Verify:
curl http://localhost:8051/api/kb/list
```

### Updates

```bash
# Quick update (runs git pull, pip install, restart)
/opt/claude-os/update.sh

# Manual update
cd /opt/claude-os
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart claude-os
```

---

## 🌐 API Endpoints (For Integration)

### Query Knowledge Base

```bash
curl -X POST "http://localhost:8051/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "kb_name": "MyProject-knowledge_docs",
    "query": "How do I configure the feature?",
    "use_hybrid": true,
    "use_rerank": true
  }'
```

### Create Project

```bash
curl -X POST "http://localhost:8051/api/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "MyProject",
    "tech_stack": "Ruby on Rails",
    "database": "MySQL",
    "description": "Project description"
  }'
```

### Upload Document

```bash
curl -X POST "http://localhost:8051/api/kb/MyProject-knowledge_docs/upload" \
  -F "file=@/path/to/document.md"
```

### Import Directory

```bash
curl -X POST "http://localhost:8051/api/kb/MyProject-knowledge_docs/import" \
  -d "directory_path=/path/to/docs"
```

### List Knowledge Bases

```bash
curl "http://localhost:8051/api/kb/list"
```

### Delete Document

```bash
curl -X DELETE "http://localhost:8051/api/kb/MyProject-knowledge_docs/documents/filename.md"
```

---

## 🐛 Quick Troubleshooting

### "Command not found: /claude-os-init"

```bash
# Re-run install script
cd /path/to/claude-os
./install.sh
```

### "Connection refused to localhost:8051"

```bash
# Check if Claude OS is running
sudo systemctl status claude-os

# If not running, start it
sudo systemctl start claude-os

# Check logs for errors
sudo journalctl -u claude-os -n 50
```

### "Database is locked"

```bash
# Stop service
sudo systemctl stop claude-os

# Check for multiple processes
ps aux | grep claude-os

# Kill any stuck processes
kill -9 <PID>

# Restart
sudo systemctl start claude-os
```

### Slow Responses

```bash
# Check system load
uptime
htop

# Check if using correct model
ollama list

# Consider smaller model for speed
ollama pull llama3.1:3b
# Update config to use llama3.1:3b
```

### Ollama Won't Start

```bash
# Check status
sudo systemctl status ollama

# Check if port is in use
sudo lsof -i :11434

# Restart Ollama
sudo systemctl restart ollama

# Verify model downloaded
ollama list
```

---

## 💡 Pro Tips

### Trigger Phrases (Auto-Save)

When you say these, Claude automatically saves to memories:

- "Remember this:"
- "Save this:"
- "Document this:"
- "Note this:"
- "Keep in mind:"

### Search Tips

- Use natural language: "how did we fix the bug"
- Be specific: "integration timeout error"
- Try variations: "auto accept" vs "automatic acceptance"

### Session Management

- Start sessions for major features
- End sessions to save progress
- Resume sessions across days
- Sessions track: task, branch, decisions, blockers

### Best Practices

1. **Save liberally** - Every insight makes Claude smarter
2. **Search first** - Before reinventing, check memories
3. **Use sessions** - Track complex features end-to-end
4. **Document decisions** - Why you chose approach X over Y
5. **Update regularly** - Run `/opt/claude-os/update.sh` weekly

---

## 📊 Performance Expectations

### Local Development (Mac)

- Query response: 2-10 seconds
- Memory search: 1-3 seconds
- Document upload: < 1 second

### Production Server (16 CPU / 32GB RAM)

- Simple queries: 1-5 seconds
- Complex queries: 5-15 seconds
- Concurrent users: 50+ without slowdown

---

## 🔐 Security Notes

### Local Development

- Runs on localhost:8051
- Only accessible from your machine
- Data stays local

### Production Server

- MCP server localhost only (127.0.0.1)
- External access via app (authenticated)
- Daily backups, 7-day retention
- No data sent to external APIs
- Ollama runs locally (not OpenAI)

---

## 📞 Support & Resources

### Logs Locations

- **Local**: `~/Projects/claude-os/logs/`
- **Production**: `/opt/claude-os/logs/`
- **Systemd**: `sudo journalctl -u claude-os`

### Config Locations

- **Local**: `~/Projects/claude-os/claude-os-config.json`
- **Production**: `/opt/claude-os/claude-os-config.json`
- **Project**: `.claude-os/config.json`

### Documentation

- **Full README**: `README.md`
- **Deployment Guide**: `docs/DEPLOYMENT_GUIDE.md`
- **Sharing Guide**: `SHARING_GUIDE.md`

---

## 🎓 Cheat Sheet Summary

```
┌─────────────────────────────────────────────────┐
│           CLAUDE OS QUICK REFERENCE             │
├─────────────────────────────────────────────────┤
│ Search:     /claude-os-search "query"           │
│ Remember:   /claude-os-remember "content"       │
│ Save:       /claude-os-save "title"             │
│ List:       /claude-os-list                     │
│ Init:       /claude-os-init                     │
├─────────────────────────────────────────────────┤
│ Health:     curl localhost:8051/health          │
│ Status:     sudo systemctl status claude-os     │
│ Logs:       sudo journalctl -u claude-os -f     │
│ Backup:     /opt/claude-os/backup.sh            │
│ Update:     /opt/claude-os/update.sh            │
├─────────────────────────────────────────────────┤
│ Auto-save:  "remember this: ..."                │
│ Agent-OS:   /new-spec, /create-spec             │
│ Implement:  /implement-spec [name]              │
└─────────────────────────────────────────────────┘
```

---

**Claude CLI + Claude OS = Invincible!** 🚀
