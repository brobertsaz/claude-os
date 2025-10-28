# File Watcher Hooks - Quick Start Guide

## What Changed?

The `initialize-project` skill now **automatically configures file watchers** for your project's knowledge bases. No more manual setup needed!

## Before vs After

### Before (Manual Setup Required)
```bash
# Initialize project
initialize-project: 1

# Then manually enable hooks via API
curl -X POST http://localhost:8051/api/projects/1/hooks/knowledge_docs/enable \
  -H "Content-Type: application/json" \
  -d '{"folder_path": "/path/to/knowledge_docs"}'

# Then manually start the file watcher
curl -X POST http://localhost:8051/api/watcher/start/1

# Only THEN would new files auto-sync
```

### After (Fully Automatic)
```bash
# Initialize project
initialize-project: 1

# ✨ File watchers are now automatically configured!
# New files will be auto-synced immediately
```

## How File Watchers Work

When you initialize a project, the system automatically:

1. **Creates hooks for all 4 MCP types:**
   - `knowledge_docs` → Watches your project's documentation folder
   - `project_profile` → Watches `.claude-os/project-profile/`
   - `project_index` → Watches `.claude-os/project-index/`
   - `project_memories` → Watches `.claude-os/memories/`

2. **Starts the file watcher service**
   - Monitors all configured folders
   - Detects file changes within ~2 seconds
   - Automatically syncs changes to knowledge bases

3. **Creates the necessary folders**
   - Project folders are created if they don't exist
   - Ready to accept new files immediately

## Default Folder Mappings

| MCP Type | Default Folder | Behavior |
|----------|---|---|
| `knowledge_docs` | `docs/` (or `documentation/`) | Watches for markdown, text, PDF files |
| `project_profile` | `.claude-os/project-profile/` | Auto-created, stores profile docs |
| `project_index` | `.claude-os/project-index/` | Auto-created, stores code index |
| `project_memories` | `.claude-os/memories/` | Auto-created, stores insights |

## Using Custom Folders

If you want to use a different folder for `knowledge_docs`:

```bash
# Create your custom folder
mkdir my-docs

# Enable hook for custom folder
curl -X POST "http://localhost:8051/api/projects/1/hooks/knowledge_docs/enable" \
  -H "Content-Type: application/json" \
  -d '{"folder_path": "/path/to/my-docs"}'

# Restart the watcher to pick up changes
curl -X POST "http://localhost:8051/api/watcher/restart/1"
```

## Verify Hooks Are Working

### Check Watcher Status
```bash
curl http://localhost:8051/api/watcher/status
```

Expected output shows your project is being watched:
```json
{
  "status": {
    "enabled": true,
    "projects_watched": 1,
    "projects": {
      "1": {
        "watched_paths": {
          "knowledge_docs": "/path/to/docs",
          "project_profile": "/path/to/.claude-os/project-profile",
          ...
        },
        "event_handlers": ["knowledge_docs", "project_profile", ...]
      }
    }
  }
}
```

### Check Hooks Configuration
```bash
cat /path/to/project/.claude-os/hooks.json
```

Should show something like:
```json
{
  "version": "1.0",
  "project_id": 1,
  "hooks": {
    "knowledge_docs": {
      "enabled": true,
      "folder_path": "/path/to/docs",
      "synced_files": {}
    },
    ...
  }
}
```

## Testing Auto-Sync

### Test knowledge_docs Auto-Sync
```bash
# Create a test file
echo "# Test Document" > /path/to/docs/test.md

# Wait 2-3 seconds for the watcher to pick it up

# Verify it was indexed
sqlite3 /path/to/claude-os/data/claude-os.db \
  "SELECT COUNT(*) FROM documents WHERE doc_id LIKE 'test.md%' AND kb_id = 1"
```

Should show a count > 0 if successfully indexed.

## Troubleshooting

### Hooks not triggering auto-sync?

1. **Check if watcher is running:**
   ```bash
   curl http://localhost:8051/api/watcher/status
   ```
   If `"enabled": false`, start it:
   ```bash
   curl -X POST "http://localhost:8051/api/watcher/start/1"
   ```

2. **Check hooks configuration:**
   ```bash
   cat .claude-os/hooks.json
   ```
   Verify `"enabled": true` for your MCP type

3. **Check folder permissions:**
   - Ensure folder is readable by the MCP server
   - Try creating a test file manually

4. **Check MCP server logs:**
   - Look for errors in `/private/tmp/` or application logs
   - Check if server is running: `ps aux | grep python | grep server`

### Files not appearing in search?

1. **Verify files were indexed:**
   ```bash
   sqlite3 /path/to/claude-os/data/claude-os.db \
     "SELECT COUNT(*) FROM documents WHERE kb_id = 1"
   ```

2. **Check file format is supported:**
   - Default: `.md`, `.txt`, `.pdf`, `.py`, `.js`, `.ts`, `.json`, `.yaml`
   - Configure custom patterns in hooks.json `file_patterns` array

3. **Manually trigger sync:**
   ```bash
   curl -X POST "http://localhost:8051/api/projects/1/hooks/sync?mcp_type=knowledge_docs"
   ```

## Advanced: Restart Watchers

If watchers stop responding:

```bash
# Restart a specific project's watcher
curl -X POST "http://localhost:8051/api/watcher/restart/1"

# Or restart all watchers
# (Note: not available via API, requires server restart)
```

## Git Integration

The system also installs **git post-commit hooks** that:
- Auto-index changed files on each commit
- Periodically expand the index with new files (every 10 commits)
- Track commit count for smart indexing

This works seamlessly with the file watcher hooks.

## FAQ

**Q: Do I need to restart anything after running initialize-project?**
A: No! Everything is set up automatically. File watchers start immediately.

**Q: Can I add files while the watcher is running?**
A: Yes! Add files anytime. They'll be indexed within ~2 seconds.

**Q: What if I want to disable auto-sync for a folder?**
A: Disable the hook via API:
```bash
curl -X POST "http://localhost:8051/api/projects/1/hooks/knowledge_docs/disable"
```

**Q: Can multiple projects have watchers running?**
A: Yes! The system can monitor multiple projects simultaneously.

**Q: Do file watchers persist after server restart?**
A: No, watchers stop when the server restarts. They'll restart automatically when projects are loaded.

---

**Last Updated:** October 28, 2025
