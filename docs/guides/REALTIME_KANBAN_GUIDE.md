# Real-Time Kanban Board Guide

## Overview

Claude OS features a **real-time Kanban board** that automatically syncs with your agent-os spec files as they're created and updated. This provides live visibility into your development progress without any manual intervention.

## How It Works

The real-time Kanban system consists of three integrated components:

```
agent-os updates tasks.md
        ↓ (2 sec debounce)
Spec Watcher detects change
        ↓
Auto-syncs to database
        ↓ (within 3 seconds)
Kanban board auto-refreshes
        ↓
You see updated tasks in real-time! 🎉
```

### 1. Spec File Watcher

The **Spec Watcher** monitors your project's `agent-os/specs/` folder for file changes:

- **Watches**: All `tasks.md` and `spec.md` files in your specs folders
- **Triggers on**: File modifications and new file/folder creation
- **Debounce**: 2-second delay to batch rapid changes
- **Auto-starts**: Launches automatically when MCP server starts

**Technical Details:**
- Location: `app/core/spec_watcher.py`
- Uses: `watchdog` library for filesystem monitoring
- Monitors: `/path/to/project/agent-os/specs/**/*`
- Thread-safe: Uses locks for concurrent access

### 2. Automatic Database Sync

When the spec watcher detects changes, it:

1. Parses the updated `tasks.md` file
2. Extracts tasks in checkbox format:
   ```markdown
   - [x] 1.0 Complete database layer
   - [ ] 2.1 Write tests for services
   ```
3. Updates the SQLite database with new/modified tasks
4. Tracks task status (todo, in_progress, done, blocked)

**Supported Task Formats:**

The parser supports two formats:

**Checkbox Format** (recommended for agent-os):
```markdown
- [x] 1.0 Complete database layer
  - [x] 1.1 Write 2-8 focused tests for database models
  - [x] 1.2 Create migration: add_manual_time_slots_support
- [ ] 2.0 Complete service layer
  - [ ] 2.1 Write 2-8 focused tests for services
```

**Classic Format** (legacy support):
```markdown
### PHASE1-TASK1: Database Setup
**Title:** Setup Database Schema
**Description:** Create all required database tables
**Estimated Time:** 2 hours
**Risk Level:** low
**Status:** ✅ COMPLETED
```

### 3. Frontend Auto-Refresh

The Kanban board frontend:

- **Polls**: Every 3 seconds for database updates
- **Refreshes**: Automatically when new data is detected
- **Smooth**: Uses React Query for optimistic updates
- **Animations**: Framer Motion for smooth task transitions

## Using the Kanban Board

### Accessing the Board

1. Open Claude OS web interface
2. Select your project from the sidebar
3. Click the **"Kanban Board"** tab
4. Board loads automatically with all specs and tasks

### Board Layout

The Kanban board displays:

**Top Section:**
- Summary statistics (total specs, total tasks, completed tasks)
- "Sync Specs" button (manual sync if needed)
- "Show Archived" toggle

**Spec Cards:**
Each spec shows:
- Spec name and status
- Progress bar
- Task counts by status
- Four columns: Todo, In Progress, Done, Blocked

**Task Cards:**
- Task code (e.g., PHASE1-TASK1)
- Title
- Risk level badge
- Estimated/actual time
- Dependencies

### Manual Sync Button

While the board updates automatically, you can manually trigger a sync:

1. Click **"Sync Specs"** button at the top
2. All spec files are re-parsed
3. Database updates immediately
4. Board refreshes within 3 seconds

Use this when:
- Testing the sync functionality
- Recovering from errors
- Adding a new spec folder manually

## Configuration

### Spec Watcher Management

The spec watcher starts automatically, but you can control it via API:

**Start watcher for a project:**
```bash
curl -X POST http://localhost:8051/api/spec-watcher/start/{project_id}
```

**Stop watcher for a project:**
```bash
curl -X POST http://localhost:8051/api/spec-watcher/stop/{project_id}
```

**Start all project watchers:**
```bash
curl -X POST http://localhost:8051/api/spec-watcher/start-all
```

**Check watcher status:**
```bash
curl http://localhost:8051/api/spec-watcher/status
```

Example status response:
```json
{
  "status": {
    "enabled": true,
    "projects_watched": 1,
    "projects": {
      "1": {
        "project_path": "/Users/you/Projects/myapp",
        "specs_path": "/Users/you/Projects/myapp/agent-os/specs",
        "watching": true
      }
    }
  }
}
```

### Adjusting Refresh Rate

The default refresh rate is 3 seconds. To change it:

**File:** `frontend/src/components/KanbanBoard.tsx`

```typescript
const { data: kanbanData, isLoading } = useQuery({
  queryKey: ['kanban', projectId, includeArchived],
  queryFn: async () => {
    // ... fetch logic
  },
  refetchInterval: 3000, // Change this value (milliseconds)
});
```

**Recommended values:**
- **3000ms (3s)**: Real-time updates, good UX
- **5000ms (5s)**: Balanced performance
- **10000ms (10s)**: Low-traffic, battery-saving

### Debounce Delay

The spec watcher waits 2 seconds after detecting a change before syncing. To adjust:

**File:** `app/core/spec_watcher.py`

```python
class SpecFileHandler(FileSystemEventHandler):
    def __init__(self, project_id: int, project_path: str):
        # ...
        self.debounce_delay = 2.0  # Change this value (seconds)
```

**Why debounce?**
- Prevents sync spam during rapid file edits
- Batches related changes together
- Reduces database load

## Project Structure Requirements

For the Kanban board to work, your project must have this structure:

```
your-project/
└── agent-os/
    └── specs/
        ├── 2025-10-29-feature-name/
        │   ├── spec.md          # Optional: Feature specification
        │   └── tasks.md         # Required: Task breakdown
        └── 2025-11-01-another-feature/
            ├── spec.md
            └── tasks.md
```

**Folder naming convention:**
- Format: `YYYY-MM-DD-feature-slug`
- Example: `2025-10-29-manual-appointment-times`
- Slug becomes the spec name (spaces replace hyphens)

## Troubleshooting

### Tasks Not Showing Up

**Check 1: Is the spec watcher running?**
```bash
curl http://localhost:8051/api/spec-watcher/status
```

If `"watching": false`, restart the watcher:
```bash
curl -X POST http://localhost:8051/api/spec-watcher/start/{project_id}
```

**Check 2: Are your tasks in the right format?**

Tasks must use the checkbox format with numeric prefixes:
```markdown
- [ ] 1.0 Task title
- [x] 2.1 Another task
```

Not this:
```markdown
- [ ] Task without number
- Some random text
```

**Check 3: Is tasks.md in the right location?**
```
✅ project/agent-os/specs/2025-10-29-feature/tasks.md
❌ project/specs/tasks.md
❌ project/agent-os/tasks.md
```

**Check 4: Check the MCP server logs**
```bash
tail -50 logs/mcp_server.log
```

Look for:
- `✅ Updated spec 'Feature Name' with X tasks`
- Any error messages about parsing

### Board Not Auto-Refreshing

**Check 1: Is polling enabled?**

Open browser DevTools → Network tab → Filter by "kanban"

You should see requests every 3 seconds to:
```
GET /api/projects/1/kanban?include_archived=false
```

If not, check that React Query is configured correctly.

**Check 2: Clear browser cache**
```
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)
```

**Check 3: Check frontend logs**

Open browser Console and look for errors related to:
- React Query
- Axios requests
- WebSocket connections (if applicable)

### Sync Taking Too Long

**Expected timings:**
- File change detected: < 1 second
- Debounce wait: 2 seconds
- Database sync: < 1 second
- Frontend refresh: 3 seconds
- **Total**: ~6 seconds max

**If slower:**

1. Check disk I/O (is your disk slow?)
2. Check database size (vacuum if needed):
   ```bash
   sqlite3 data/claude-os.db "VACUUM;"
   ```
3. Check CPU usage (spec parsing is CPU-intensive for large specs)

### Parser Errors

**Common issues:**

**Issue:** "No tasks found"
- **Cause:** Tasks not in checkbox format
- **Fix:** Add `- [ ]` or `- [x]` before task lines

**Issue:** "Invalid task code"
- **Cause:** Missing numeric prefix (e.g., `1.0`, `2.1`)
- **Fix:** Add numbers: `- [ ] 1.0 Task title`

**Issue:** "Spec not found"
- **Cause:** Folder name doesn't match expected format
- **Fix:** Rename to `YYYY-MM-DD-feature-name`

## Advanced Usage

### Custom Task Status Updates

You can manually update task status via API:

```bash
curl -X PATCH http://localhost:8051/api/tasks/{task_id}/status \
  -H "Content-Type: application/json" \
  -d '{
    "status": "in_progress",
    "actual_minutes": 120
  }'
```

Valid statuses: `todo`, `in_progress`, `done`, `blocked`

### Archiving Specs

Archive completed specs to declutter the board:

**Via UI:**
1. Click "Archive" button on spec card
2. Spec moves to archived view

**Via API:**
```bash
curl -X POST http://localhost:8051/api/specs/{spec_id}/archive
```

**To view archived specs:**
- Toggle "Show Archived" checkbox in the UI

### Bulk Operations

**Sync all specs for a project:**
```bash
curl -X POST http://localhost:8051/api/projects/{project_id}/specs/sync
```

Response:
```json
{
  "project_id": 1,
  "message": "Specs synced successfully",
  "synced": 0,
  "updated": 3,
  "total": 3,
  "errors": []
}
```

## Performance Considerations

### Database Size

Each task creates a database row. For large projects:

**Estimate storage:**
- 100 specs × 50 tasks = 5,000 rows
- SQLite handles this easily (millions of rows supported)

**Optimize periodically:**
```bash
sqlite3 data/claude-os.db "VACUUM; ANALYZE;"
```

### Frontend Performance

With many tasks, the Kanban board may slow down:

**Optimization tips:**
1. Archive old specs (reduces rendered tasks)
2. Increase refresh interval to 5-10 seconds
3. Filter by status (show only active tasks)

### File Watcher Overhead

The spec watcher uses minimal resources:
- CPU: < 1% idle, ~5% during sync
- Memory: ~20 MB per project
- Disk I/O: Only on file changes

**Disable if needed:**
```bash
curl -X POST http://localhost:8051/api/spec-watcher/stop/{project_id}
```

## API Reference

See full API documentation in `docs/API_REFERENCE.md`

**Key endpoints:**

- `GET /api/projects/{id}/kanban` - Get Kanban data
- `GET /api/projects/{id}/specs` - List all specs
- `POST /api/projects/{id}/specs/sync` - Manual sync
- `PATCH /api/tasks/{id}/status` - Update task status
- `POST /api/specs/{id}/archive` - Archive spec
- `GET /api/spec-watcher/status` - Watcher status

## Related Documentation

- **What is Claude OS**: `docs/guides/WHAT_IS_CLAUDE_OS.md`
- **Session Workflow**: `docs/guides/IDEAL_SESSION_WORKFLOW.md`
- **API Reference**: `docs/API_REFERENCE.md`
- **Quick Start**: `docs/QUICK_START_CLAUDE_OS.md`

## Support

If you encounter issues:

1. Check the logs: `tail -f logs/mcp_server.log`
2. Check watcher status: `curl http://localhost:8051/api/spec-watcher/status`
3. Try manual sync: Click "Sync Specs" button
4. Restart MCP server: `./scripts/restart_mcp.sh`
5. Open an issue: [GitHub Issues](https://github.com/anthropics/claude-os/issues)
