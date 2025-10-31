# Claude OS Production Deployment Guide for PISTN

**Date**: 2025-10-30
**Server**: Rails App Server (16 CPU / 32GB RAM / 640GB Storage)
**Database**: SQLite (simple, fast for read-heavy workloads)

## Overview

Deploy Claude OS to PISTN production server to power the DocumentationAssistant with AI-powered documentation search and Q&A.

## Server Architecture

```
PISTN Production Server (staging.pistn.com)
├── Rails App :80/:443 (existing)
│   └── DocumentationAssistant (calls Claude OS)
├── MySQL (remote/hosted) (existing)
├── Redis :6379 (existing)
└── Claude OS (NEW)
    ├── MCP Server :8051
    ├── SQLite database (local file)
    └── Ollama :11434 (CPU mode, llama3.1:8b)
```

## Resource Allocation

**Before Claude OS:**
- Rails + Nginx: ~4-6 CPUs, 8-12GB RAM
- Redis: ~1 CPU, 2GB RAM
- **Available: 9-10 CPUs, 18-20GB RAM**

**After Claude OS:**
- Flask MCP Server: ~1-2 CPUs, 2GB RAM
- Ollama (CPU): ~2-4 CPUs, 4-8GB RAM
- SQLite: minimal overhead
- **Total Claude OS: ~3-6 CPUs, 6-10GB RAM**

**Remaining: 3-7 CPUs, 8-14GB RAM for traffic spikes**

## Deployment Steps

### 1. Copy Deployment Script to Server

```bash
# From your Mac
scp /tmp/deploy-claude-os-production.sh deploy@staging.pistn.com:/tmp/

# SSH into server
ssh deploy@staging.pistn.com
```

### 2. Run Deployment Script

```bash
# Make executable and run
chmod +x /tmp/deploy-claude-os-production.sh
/tmp/deploy-claude-os-production.sh
```

The script automatically:
- ✅ Installs Python 3.11, Git, Nginx
- ✅ Clones Claude OS from GitHub
- ✅ Sets up Python virtual environment
- ✅ Creates SQLite database directory
- ✅ Installs Ollama
- ✅ Pulls llama3.1:8b model (~4.7GB)
- ✅ Creates systemd services
- ✅ Configures firewall
- ✅ Sets up Nginx reverse proxy
- ✅ Creates helper scripts (update, backup)
- ✅ Sets up daily backups (2am cron)
- ✅ Runs health checks

### 3. Copy Local SQLite Database to Server (RECOMMENDED!)

**🎯 This is the SECRET SAUCE!**

Instead of re-indexing everything from scratch on the server, **copy your local Claude OS database** (with all the knowledge Claude has already learned about PISTN) to the production server!

**Why this is amazing:**
- ✅ All of Claude's memories about PISTN bugs and solutions
- ✅ All the patterns learned from working with you locally
- ✅ All indexed code and documentation
- ✅ Every architectural decision and choice
- ✅ Months of accumulated knowledge → instant production deployment
- ✅ No re-indexing needed (saves hours!)

**How to do it:**

```bash
# 1. Stop Claude OS on server (if running)
ssh deploy@staging.pistn.com "sudo systemctl stop claude-os"

# 2. Find your local Claude OS database
# Default location on Mac:
ls -lh ~/Projects/claude-os/data/claude-os.db

# 3. Copy local database to server
scp ~/Projects/claude-os/data/claude-os.db \
    deploy@staging.pistn.com:/tmp/claude-os-local.db

# 4. SSH into server and move database
ssh deploy@staging.pistn.com

# Backup the empty database (just in case)
sudo cp /opt/claude-os/data/claude-os.db \
       /opt/claude-os/data/claude-os.db.original

# Replace with your local database
sudo cp /tmp/claude-os-local.db /opt/claude-os/data/claude-os.db
sudo chown deploy:deploy /opt/claude-os/data/claude-os.db
sudo chmod 644 /opt/claude-os/data/claude-os.db

# 5. Start Claude OS
sudo systemctl start claude-os

# 6. Verify it worked
curl "http://localhost:8051/api/kb/list"
# Should show: Pistn-project_memories, Pistn-project_profile, etc.

curl "http://localhost:8051/api/kb/Pistn-project_index/stats"
# Should show documents and chunks already indexed!
```

**Result:** Claude on the server now has ALL the same knowledge as Claude on your Mac! 🚀

### 4. Initialize PISTN Knowledge Bases (Only if NOT copying database)

```bash
# Create project
curl -X POST "http://localhost:8051/api/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "Pistn",
    "tech_stack": "Ruby on Rails 4.2",
    "database": "MySQL",
    "description": "Automotive service management platform"
  }'

# Index entire PISTN codebase (RECOMMENDED - one command does it all!)
/opt/claude-os/scripts/index-codebase.sh Pistn /var/www/pistn/current http://localhost:8051

# Or manually import specific directories:
# curl -X POST "http://localhost:8051/api/kb/Pistn-knowledge_docs/import" \
#   -d "directory_path=/var/www/pistn/current/docs"
# curl -X POST "http://localhost:8051/api/kb/Pistn-project_index/import" \
#   -d "directory_path=/var/www/pistn/current/app"

# Verify knowledge bases created
curl "http://localhost:8051/api/kb/list"

# Check indexing stats
curl "http://localhost:8051/api/kb/Pistn-project_index/stats"
```

### 5. Setup Authentication (Recommended for Production)

Protect the Claude OS frontend from strangers with simple email/password authentication.

**Add to `/opt/claude-os/.env`:**

```bash
# Authentication
CLAUDE_OS_EMAIL=admin@pistn.com
CLAUDE_OS_PASSWORD_HASH=<generated_hash>
CLAUDE_OS_SECRET_KEY=<random_32_char_secret>
```

**Generate password hash:**

```bash
# SSH into server
ssh deploy@staging.pistn.com

# Generate hash
cd /opt/claude-os
source venv/bin/activate
python3 -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('your_secure_password'))"

# Copy the output and add to .env as CLAUDE_OS_PASSWORD_HASH
```

**Generate secret key:**

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Restart Claude OS:**

```bash
sudo systemctl restart claude-os
```

**Test login:**

Visit `https://staging.pistn.com/login` and use your configured email/password.

**Note:** If you don't configure these variables, authentication is disabled and the frontend is open access.

See [`AUTH_SETUP.md`](/AUTH_SETUP.md) for detailed authentication documentation.

### 6. Update PISTN Rails App

**Add to `/var/www/pistn/shared/.env`:**
```bash
CLAUDE_OS_URL=http://localhost:8051
```

**Update DocumentationAssistantService:**

```ruby
# app/services/documentation_assistant_service.rb
class DocumentationAssistantService
  CLAUDE_OS_URL = ENV['CLAUDE_OS_URL'] || 'http://localhost:8051'
  
  def self.query(question)
    response = HTTParty.post(
      "#{CLAUDE_OS_URL}/api/query",
      body: {
        kb_name: 'Pistn-knowledge_docs',
        query: question,
        use_hybrid: true,
        use_rerank: true
      }.to_json,
      headers: { 'Content-Type' => 'application/json' },
      timeout: 30
    )
    
    if response.success?
      response.parsed_response
    else
      { error: "Claude OS unavailable", status: response.code }
    end
  rescue => e
    { error: e.message }
  end
end
```

**Update DocumentationAssistant Controller:**

```ruby
# app/controllers/system_admin/documentation_assistant_controller.rb
def query
  result = DocumentationAssistantService.query(params[:question])
  
  if result[:error]
    render json: { error: result[:error] }, status: :service_unavailable
  else
    render json: result
  end
end
```

**Redeploy Rails app:**
```bash
cap production deploy
```

### 7. Test Integration

```bash
# Test Claude OS directly
curl -X POST "http://localhost:8051/api/query" \
  -H "Content-Type: application/json" \
  -d '{
    "kb_name": "Pistn-knowledge_docs",
    "query": "How do I set up auto-accept appointments?"
  }'

# Test via Rails app (from browser or curl)
# Visit: https://staging.pistn.com/system_admin/documentation_assistant
```

## Management Commands

### Service Control

```bash
# Start/Stop/Restart
sudo systemctl start claude-os
sudo systemctl stop claude-os
sudo systemctl restart claude-os

# Check status
sudo systemctl status claude-os
sudo systemctl status ollama

# View logs
sudo journalctl -u claude-os -f
sudo journalctl -u ollama -f

# Or view log files directly
tail -f /opt/claude-os/logs/claude-os.log
tail -f /opt/claude-os/logs/ollama.log
```

### Updates

```bash
# Update Claude OS to latest version
cd /opt/claude-os
./update.sh

# Or manually:
cd /opt/claude-os
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart claude-os
```

### Backups

```bash
# Manual backup
/opt/claude-os/backup.sh

# Backups are automatically created daily at 2am
# Location: /opt/claude-os-backups/

# Restore from backup
sudo systemctl stop claude-os
cp /opt/claude-os-backups/claude-os-YYYYMMDD_HHMMSS.db \
   /opt/claude-os/data/claude-os.db
sudo systemctl start claude-os
```

### Health Checks

```bash
# Check MCP server
curl http://localhost:8051/health

# Check Ollama
curl http://localhost:11434/api/tags

# List knowledge bases
curl http://localhost:8051/api/kb/list

# Get KB stats
curl http://localhost:8051/api/kb/Pistn-knowledge_docs/stats
```

## Monitoring

### Resource Usage

```bash
# CPU and RAM usage
htop

# Check Claude OS process
ps aux | grep python | grep mcp_server

# Check Ollama process
ps aux | grep ollama

# Disk usage
df -h /opt/claude-os
```

### Performance Metrics

```bash
# Response time test
time curl -X POST "http://localhost:8051/api/query" \
  -H "Content-Type: application/json" \
  -d '{"kb_name":"Pistn-knowledge_docs","query":"test"}'

# Expected: 1-5 seconds for simple queries
# Expected: 5-15 seconds for complex queries
```

## Troubleshooting

### Claude OS won't start

```bash
# Check logs
sudo journalctl -u claude-os -n 100

# Common issues:
# 1. Port already in use
sudo lsof -i :8051

# 2. Python dependencies missing
cd /opt/claude-os
source venv/bin/activate
pip install -r requirements.txt

# 3. Database permissions
ls -la /opt/claude-os/data/
chown deploy:deploy /opt/claude-os/data/claude-os.db
```

### Ollama won't start

```bash
# Check logs
sudo journalctl -u ollama -n 100

# Verify model downloaded
ollama list

# Re-pull model if needed
ollama pull llama3.1:8b
```

### Slow responses

```bash
# Check if Ollama is using CPU (not GPU)
ollama list

# Check system load
uptime
htop

# Reduce model size if needed (faster but less accurate)
ollama pull llama3.1:3b
# Update config to use smaller model
```

### Database locked errors

```bash
# SQLite database locked (rare)
# Check for multiple processes
ps aux | grep claude-os

# Restart service
sudo systemctl restart claude-os
```

## Security Considerations

1. **Firewall**: Claude OS only accessible from localhost (127.0.0.1)
2. **No external access**: MCP server not exposed to internet
3. **Rails app proxy**: All external requests go through Rails authentication
4. **Backups**: Daily backups kept for 7 days
5. **Updates**: Regular security updates via update.sh

## Performance Optimization

### For Better Performance

1. **Use smaller Ollama model** (faster, less RAM):
   ```bash
   ollama pull llama3.1:3b
   # Update claude-os-config.json model to "llama3.1:3b"
   ```

2. **Limit concurrent requests** in Rails:
   ```ruby
   # Add request throttling to controller
   before_action :throttle_requests
   ```

3. **Cache frequent queries** in Redis:
   ```ruby
   def query(question)
     Rails.cache.fetch("claude_os:#{question}", expires_in: 1.hour) do
       DocumentationAssistantService.query(question)
     end
   end
   ```

## Keeping Code Index Updated

**Why re-index?**
As you deploy new code, Claude OS needs to learn about your changes to provide accurate suggestions and answers.

### Automatic Re-indexing on Deploy

**Option 1: Capistrano Hook (Recommended)**

Add to `config/deploy.rb`:
```ruby
# Re-index codebase after successful deployment
after 'deploy:finished', 'claude_os:reindex'

namespace :claude_os do
  desc 'Re-index codebase in Claude OS'
  task :reindex do
    on roles(:app) do
      within release_path do
        info "Re-indexing codebase in Claude OS..."
        execute "/opt/claude-os/scripts/index-codebase.sh",
                "Pistn",
                release_path,
                "http://localhost:8051"
      end
    end
  end
end
```

**Option 2: Manual After Each Deploy**
```bash
# SSH into server
ssh deploy@staging.pistn.com

# Run indexing script
/opt/claude-os/scripts/index-codebase.sh Pistn /var/www/pistn/current http://localhost:8051
```

**Option 3: Scheduled Cron Job**
```bash
# Edit crontab
crontab -e

# Add weekly re-index (Sundays at 2am)
0 2 * * 0 /opt/claude-os/scripts/index-codebase.sh Pistn /var/www/pistn/current http://localhost:8051 >> /opt/claude-os/logs/reindex.log 2>&1
```

### Performance Impact

- Indexing ~5,000 files takes 2-5 minutes
- CPU usage: Light (mostly I/O bound)
- Safe to run during low-traffic periods
- Can run concurrently with normal operations

## Cost Analysis

**Server Resources Used:**
- CPUs: 3-6 cores (~20-40% of available)
- RAM: 6-10GB (~20-30% of available)
- Storage: ~10GB (model + database + logs)

**Additional Costs:**
- $0 - Running on existing server
- No API costs (local Ollama, not OpenAI)
- No extra database costs (SQLite)

**Total Cost: $0 per month** (uses existing infrastructure)

## Future Enhancements

1. **Add more knowledge bases**:
   - Support tickets archive
   - Common solutions database
   - Tekmetric integration guides

2. **Improve responses**:
   - Fine-tune on PISTN-specific data
   - Add conversation history
   - Multi-turn dialogues

3. **Scale if needed**:
   - Move to dedicated server if traffic increases
   - Use GPU for faster inference
   - SQLite handles concurrent reads well; for high write concurrency, consider connection pooling

## Support

**Logs Location:**
- Claude OS: `/opt/claude-os/logs/claude-os.log`
- Ollama: `/opt/claude-os/logs/ollama.log`
- Systemd: `sudo journalctl -u claude-os`

**Configuration:**
- `/opt/claude-os/claude-os-config.json`
- `/var/www/pistn/shared/.env`

**Helper Scripts:**
- Update: `/opt/claude-os/update.sh`
- Backup: `/opt/claude-os/backup.sh`
- Index Codebase: `/opt/claude-os/scripts/index-codebase.sh`

---

**Deployment Date**: 2025-10-30
**Server**: staging.pistn.com (16 CPU / 32GB RAM)
**Status**: Ready for production use
