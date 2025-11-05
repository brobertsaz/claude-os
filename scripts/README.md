# Claude OS Helper Scripts

Utility scripts for managing and operating Claude OS.

## Index Codebase Script

**`index-codebase.sh`** - Index an entire project codebase into Claude OS knowledge bases.

### Usage

```bash
./scripts/index-codebase.sh <project_name> [project_path] [claude_os_url]
```

### Examples

**Local Development (Mac):**
```bash
# Index PISTN codebase locally
./scripts/index-codebase.sh Pistn ~/Projects/pistn http://localhost:8051

# Index from current directory
cd ~/Projects/myapp
/path/to/claude-os/scripts/index-codebase.sh MyApp . http://localhost:8051
```

**Production Server:**
```bash
# Index PISTN on production server
/opt/claude-os/scripts/index-codebase.sh Pistn /var/www/pistn/current http://localhost:8051

# Run after deployment to update index
cd /opt/claude-os
./scripts/index-codebase.sh Pistn /var/www/pistn/current http://localhost:8051
```

### What It Indexes

The script automatically detects and indexes:

**1. Documentation** → `{project}-knowledge_docs`
- `docs/` or `documentation/` directory
- All `.md`, `.txt`, `.pdf` files

**2. Application Code** → `{project}-project_index`
- `app/` (Rails, Laravel)
- `src/` (Node.js, Go, Rust, modern frameworks)
- `lib/` (Ruby gems, libraries)
- All code files: `.rb`, `.py`, `.js`, `.ts`, `.go`, `.java`, `.php`, `.c`, `.cpp`, etc.

**3. Models & Database** → `{project}-project_index`
- `app/models/`
- `db/` (migrations, schema)

**4. Services & Business Logic** → `{project}-project_index`
- `app/services/`
- `services/`

**5. Controllers & API** → `{project}-project_index`
- `app/controllers/`
- `api/`

**6. Configuration** → `{project}-project_profile`
- `config/`
- All `.yml`, `.yaml`, `.json`, `.xml` files

### Output

The script provides:
- Progress indicators for each directory
- File counts and success/failure stats
- Final knowledge base statistics
- Next steps and usage examples

### Re-indexing

**When to re-index:**
- After major code changes
- After deployment
- When adding new features
- Weekly for active projects

**How to re-index:**
Simply run the script again with the same parameters. It will update the existing knowledge bases with new/changed files.

```bash
# Set up a weekly cron job (production server)
# Add to crontab: crontab -e
0 2 * * 0 /opt/claude-os/scripts/index-codebase.sh Pistn /var/www/pistn/current http://localhost:8051 >> /opt/claude-os/logs/indexing.log 2>&1
```

### Requirements

- Claude OS server must be running
- Curl must be installed
- Read access to project directory

### Troubleshooting

**"Claude OS server is not responding"**
```bash
# Check if Claude OS is running
curl http://localhost:8051/health

# Start Claude OS
# Local: cd ~/Projects/claude-os && ./start.sh
# Server: sudo systemctl start claude-os
```

**"Project path does not exist"**
```bash
# Verify the path is correct
ls -la /path/to/project

# Use absolute path, not relative
./scripts/index-codebase.sh MyApp /full/path/to/project http://localhost:8051
```

**Slow indexing**
Large codebases (10,000+ files) may take several minutes. This is normal. The script shows progress for each directory.

### Benefits

Once indexed, you get:

✅ **Semantic code search** - Find code by meaning, not just keywords
✅ **Complete context** - Claude knows your entire codebase
✅ **Pattern recognition** - Claude learns your coding style
✅ **Instant answers** - "Where is the appointment logic?" → exact file and line
✅ **Better suggestions** - Code generation matches your patterns

### Integration with Deployment

**Capistrano (Rails):**

```ruby
# config/deploy.rb
after 'deploy:finished', 'claude_os:index'

namespace :claude_os do
  task :index do
    on roles(:app) do
      within release_path do
        execute "/opt/claude-os/scripts/index-codebase.sh Pistn #{release_path} http://localhost:8051"
      end
    end
  end
end
```

**Docker deployment:**

```dockerfile
# Dockerfile
RUN /opt/claude-os/scripts/index-codebase.sh MyApp /app http://claude-os:8051
```

**GitHub Actions:**

```yaml
# .github/workflows/deploy.yml
- name: Index codebase in Claude OS
  run: |
    ssh deploy@server "/opt/claude-os/scripts/index-codebase.sh Pistn /var/www/pistn/current http://localhost:8051"
```

---

## Screenshot Capture Script

**`capture-screenshots.js`** - Automatically capture beautiful screenshots of the Claude OS interface using Playwright.

### Usage

```bash
# From frontend directory
cd frontend
npm run screenshots

# Or directly
node ../scripts/capture-screenshots.js
```

### Prerequisites

1. **Services running:**
   ```bash
   ./start.sh  # Starts MCP server (8051) and frontend (5173)
   ```

2. **At least one project created** (e.g., Pistn)

3. **Playwright installed:**
   ```bash
   cd frontend
   npx playwright install chromium
   ```

### What Gets Captured

Automatically captures 9 screenshots:

1. `welcome-screen.png` - Landing page
2. `projects-list-page.png` - Projects overview
3. `project-overview-page.png` - Project details & MCP status
4. `project-kanban-page.png` - Kanban board (full page)
5. `kanban-task-detail-modal.png` - Task detail popup
6. `project-mcp-page.png` - Knowledge base management
7. `project-chat-page.png` - Chat interface
8. `project-services-dashboard-page.png` - Service monitoring
9. `mobile-welcome-screen.png` - Mobile version (375x812)

### Output

All screenshots saved to:
```
frontend/public/assets/screenshots/
```

### When to Re-capture

**Update screenshots when:**
- UI design changes
- New features added
- Before major releases
- For updated documentation

**Quick update:**
```bash
# 1. Ensure services running
./start.sh

# 2. Run screenshot capture
cd frontend && npm run screenshots

# 3. Commit updated screenshots
git add public/assets/screenshots/
git commit -m "📸 Update UI screenshots"
```

### Configuration

Edit `scripts/capture-screenshots.js` to customize:
- Viewport size (default: 1920x1080)
- Wait times for animations
- Which pages to capture
- Headless mode for CI/CD

---

## Future Scripts

Additional utility scripts will be added here:

- `backup-knowledge-bases.sh` - Backup all knowledge bases
- `migrate-project.sh` - Migrate project between Claude OS instances
- `export-memories.sh` - Export project memories as markdown
- `sync-team-knowledge.sh` - Sync knowledge bases across team
- `test-e2e.js` - End-to-end UI testing with Playwright
- `seed-data.js` - Seed test data for demos

---

**Questions or issues?** Check the main [Claude OS README](../README.md) or open an issue on GitHub.
