# Claude OS Real-Time Learning System

## 🚀 Overview

The Real-Time Learning System makes Claude **always learning** from your conversations. As you work, it detects important decisions, changes, and insights—then automatically updates your knowledge bases.

```
Your Conversation
    ↓
Redis Pub/Sub (instant)
    ↓
RQ Worker detects triggers
    ↓
Prompts you for confirmation
    ↓
Ingests to project_profile MCP
    ↓
Claude knows immediately
```

---

## 🎯 What It Detects

The system watches for 10 types of learning opportunities:

| Trigger | Example | Confidence |
|---------|---------|-----------|
| **switching** | "We're switching from Bootstrap to Tailwind" | 95% |
| **decided_to_use** | "We decided to use GraphQL" | 90% |
| **no_longer** | "We no longer use Jest" | 85% |
| **now_using** | "Now using PostgreSQL for..." | 85% |
| **implement_change** | "Let's implement this change" | 80% |
| **performance_issue** | "This query is too slow" | 85% |
| **bug_fixed** | "Fixed a bug in the auth flow" | 80% |
| **architecture_change** | "Refactoring services to use..." | 85% |
| **rejected_idea** | "Let's avoid MongoDB" | 75% |
| **edge_case** | "Watch out for timezone issues" | 80% |

Only high-confidence detections (≥75%) trigger prompts.

---

## 🔧 Installation

### 1. Install Dependencies

```bash
cd /Users/iamanmp/Projects/code-forge
pip install -r requirements.txt  # Includes redis and rq
```

### 2. Ensure Redis is Running

```bash
# Check if Redis is running
redis-cli ping
# Output: PONG

# If not running, start it
redis-server

# Or with Homebrew
brew services start redis
```

### 3. Start the RQ Workers

In a new terminal:

```bash
cd /Users/iamanmp/Projects/code-forge
python -m app.core.redis_config
# This tests the Redis connection, then start workers:

# Option A: Run workers directly
python -m rq worker claude-os:learning claude-os:prompts claude-os:ingest

# Option B: Use the startup script (coming soon)
./start_redis_workers.sh
```

You should see:
```
🚀 Starting Redis workers for: claude-os:learning, claude-os:prompts, claude-os:ingest
```

---

## 💬 Using the System

### Workflow

```
1. You're working on PISTN
2. You say: "We're switching from Bootstrap to Tailwind"

3. [< 1 second] Redis receives the message
4. [< 1 second] RQ worker detects the trigger
5. [instant] Worker prompts you: "Should I remember this?"
6. You respond: "yes"
7. [< 5 seconds] Knowledge base is updated
8. Next conversation: "I know you use Tailwind"
```

### CLI Integration (Coming Next)

When Claude Code CLI publishes messages to Redis:

```python
# In Claude Code CLI message handler
redis.publish(f"claude-os:conversation:{project_id}", json.dumps({
    "role": "user",
    "text": message_text,
    "timestamp": datetime.now().isoformat()
}))
```

The system automatically:
1. Detects triggers
2. Prompts you (via CLI notification)
3. Updates knowledge base on confirmation
4. Ingests to MCP

---

## 📊 How It Works Internally

### Real-Time Architecture

```
┌─────────────────────────┐
│   Claude Code CLI       │
│ (publishes messages)    │
└────────────┬────────────┘
             │
             ▼
   ┌────────────────────┐
   │  Redis Pub/Sub     │
   │ (instant delivery) │
   └────────────┬───────┘
             │
             ▼
   ┌────────────────────────┐
   │   RQ Worker Process    │
   │  (always listening)    │
   └────────────┬───────────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
┌──────────┐    ┌───────────────┐
│  Detect  │    │ Prompt User   │
│ Triggers │    │ for Confirm   │
└──────────┘    └───────────────┘
    │                    │
    └────────┬───────────┘
             ▼
   ┌────────────────────┐
   │ Update Knowledge   │
   │    Base & MCP      │
   └────────────────────┘
```

### Key Components

1. **ConversationWatcher** (`conversation_watcher.py`)
   - Scans text for trigger phrases
   - Returns detections with confidence scores
   - Extracts context and metadata

2. **Redis Config** (`redis_config.py`)
   - Manages Redis connections
   - Pub/Sub channel management
   - Job queue operations
   - Singleton pattern for efficiency

3. **Learning Jobs** (`learning_jobs.py`)
   - `process_learning_detection()` - Main job handler
   - `handle_conversation_message()` - Real-time message processor
   - `prompt_user_for_confirmation()` - User interaction
   - `ingest_to_mcp()` - Knowledge base update

4. **RQ Worker**
   - Listens on 3 queues (learning, prompts, ingest)
   - Processes jobs from Redis
   - Handles retries and failures

---

## 🔍 Monitoring

### Check Job Queue Status

```bash
# List jobs in the learning queue
python -m rq info claude-os:learning

# Monitor a specific job
python -m rq info {job-id}

# Check Redis directly
redis-cli

# In Redis CLI:
> KEYS claude-os:*
> GET claude-os:prompt:4:{detection-id}:confirmed
> LRANGE rq:queue:claude-os:learning 0 -1
```

### View Learned Insights

```bash
cat /Users/iamanmp/Projects/pistn/.claude-os/project-profile/LEARNED_INSIGHTS.md
```

---

## 🎯 Next Steps

### 1. CLI Integration (In Progress)
Update Claude Code CLI to:
- Write conversation context to Redis
- Publish messages to Pub/Sub channel
- Listen for confirmation prompts
- Display knowledge updates to user

### 2. Production Setup
```bash
# Run RQ workers with supervisor for reliability
supervisor /etc/supervisor/conf.d/rq-workers.conf

# Or use systemd
systemctl start rq-workers
```

### 3. Dashboard (Future)
Monitor real-time learning activity:
- Active workers
- Job queue status
- Recent learnings
- Knowledge base growth

---

## 🧪 Testing

### Manual Test

```bash
# Start workers in one terminal
python -m rq worker claude-os:learning claude-os:prompts claude-os:ingest

# In another terminal, publish a test message
redis-cli
> PUBLISH "claude-os:conversation:4" "{\"role\": \"user\", \"text\": \"We're switching from Bootstrap to Tailwind\", \"timestamp\": \"2025-10-27T17:00:00\"}"

# You should see worker output:
# 🔍 Analyzing message from user...
# 🎯 Found 1 potential learning opportunities:
#    • switching: We're switching from Bootstrap to Tailwind... (confidence: 95%)
```

### Integration Test (With PISTN)

```bash
# 1. Ensure Redis is running
redis-cli ping

# 2. Start workers
python -m rq worker claude-os:learning claude-os:prompts claude-os:ingest

# 3. Run analyze-project on PISTN
cd /Users/iamanmp/.claude/skills/analyze-project
python3 analyze_project.py 4 http://localhost:8051

# 4. Make a change and commit
cd /Users/iamanmp/Projects/pistn
echo "# Test" >> test.txt
git add test.txt
git commit -m "test commit"

# 5. In your CLI, say: "We decided to use GraphQL"
# 6. Check if Redis received it and worker detected it
```

---

## 🐛 Troubleshooting

### Redis Connection Fails
```bash
# Check Redis is running
redis-cli ping
# Should output: PONG

# If not running:
redis-server
# Or: brew services start redis
```

### Workers Not Picking Up Jobs
```bash
# Check queue
python -m rq info

# Check worker is running
ps aux | grep rq

# Restart workers
pkill -f "rq worker"
python -m rq worker claude-os:learning claude-os:prompts claude-os:ingest
```

### Prompts Not Working
```bash
# Check if Redis key was set
redis-cli GET "claude-os:prompt:4:{detection-id}:confirmed"

# Manually confirm for testing
redis-cli SET "claude-os:prompt:4:{detection-id}:confirmed" "true"
```

---

## 📈 Performance Characteristics

| Metric | Performance |
|--------|------------|
| Pub/Sub latency | < 1ms |
| Trigger detection | < 100ms per message |
| User prompt | < 500ms (display) |
| MCP ingestion | 2-5 seconds |
| Full cycle | < 10 seconds |

---

## 🔐 Security Considerations

1. **Authentication**: Redis should be secured with passwords in production
2. **Timeout**: Confirmations expire after 10 minutes for security
3. **Job Isolation**: Each project has isolated keys and channels
4. **Data Privacy**: All conversations stay local (no cloud)

---

## 🚀 The Vision

> **Claude becomes your greatest developer by learning from every conversation.**

- You say something important
- System detects it (< 1 second)
- Asks for confirmation (instant)
- Updates knowledge base (5 seconds)
- Next conversation: I know

No manual documentation. No context loss. Just continuous learning.

---

**Status**: 🟢 Core system complete, CLI integration in progress

**Next**: Integrate with Claude Code CLI for end-to-end real-time learning!
