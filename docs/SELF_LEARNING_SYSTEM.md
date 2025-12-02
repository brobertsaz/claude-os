# 🧠 Claude OS Self-Learning System

## Overview

Claude OS learns from your work automatically. As you develop, the system detects important decisions, discoveries, and changes—then updates your knowledge base in real-time so Claude always knows the current state of your project.

**Key Point**: This is built for Claude to use. As you work and talk to Claude, the learning system captures what you're doing and teaches Claude about your project.

---

## How It Works

### The Flow (In Real-Time)

```
You tell Claude: "We're switching from Bootstrap to Tailwind"
                    ↓
            < 1ms: Redis receives it
                    ↓
            < 100ms: RQ Worker detects the pattern
                    ↓
            < 500ms: Prompts you for confirmation
                    ↓
            You say: "Yes, remember this"
                    ↓
            < 5 seconds: Knowledge base updated
                    ↓
    Next conversation: Claude knows about Tailwind!
```

### What Gets Detected (10 Patterns)

The system watches for these learning triggers with high confidence (75-95%):

| Pattern | Example | Use Case |
|---------|---------|----------|
| **switching** | "We're switching from Bootstrap to Tailwind" | Technology stack changes |
| **decided_to_use** | "We decided to use GraphQL" | Architecture decisions |
| **no_longer** | "We no longer use Jest" | Deprecating tools/libraries |
| **now_using** | "Now using PostgreSQL for..." | New tech adoption |
| **implement_change** | "Let's implement this change" | Feature development decisions |
| **performance_issue** | "This query is too slow" | Performance bottlenecks discovered |
| **bug_fixed** | "Fixed a bug in the auth flow" | Important bug fixes |
| **architecture_change** | "Refactoring services to use..." | System redesign |
| **rejected_idea** | "Let's avoid MongoDB" | What NOT to use |
| **edge_case** | "Watch out for timezone issues" | Important gotchas |

---

## System Architecture

### Components

**1. RQ Workers** (`start_redis_workers.sh`)
- Always listening on 3 queues
- Processes messages from conversations
- Detects learning patterns
- Manages user confirmations

**2. Redis Pub/Sub**
- Publishes conversation messages
- < 1ms latency
- Reliable message delivery

**3. Learning Jobs** (`app/core/learning_jobs.py`)
- Pattern detection (ConversationWatcher)
- Confidence scoring
- User interaction handling
- MCP knowledge base ingestion

**4. Knowledge Base Integration**
- Auto-ingests confirmed learnings
- Updates project_profile MCP
- Makes knowledge immediately available to Claude

---

## Getting Started

### 1. Automatic Activation with Project Initialization

When you initialize a project with Claude Code, the learning system starts automatically:

```bash
# In Claude Code, run:
/initialize-project [project-id]
```

The initialize-project skill will:
- ✅ Step 0/5: Start RQ workers automatically
- ✅ Verify Redis is running
- ✅ Detect if workers already running
- ✅ Continue with rest of setup

**No manual setup needed!**

### 2. Manual Startup (If Needed)

If you need to start workers manually:

```bash
cd /path/to/claude-os
./start_redis_workers.sh
```

You should see:
```
✅ Redis is running
✅ Virtual environment exists
✅ Dependencies installed
🚀 Worker queues: claude-os:learning, claude-os:prompts, claude-os:ingest
Listening on claude-os:learning, claude-os:prompts, claude-os:ingest...
```

### 3. Verify Workers Are Running

```bash
rq info
```

Output should show:
```
5af9db7764bd462593d26adc8dfdcdee (Bobs-MacBook-Pro-2.local [::1]:54714 86233): idle
  claude-os:learning, claude-os:prompts, claude-os:ingest. jobs: 0 finished, 0 failed
1 workers, 0 queues
```

---

## Using the Learning System

### For Claude (Your Assistant)

The learning system is automatic and transparent to Claude. As you converse:

1. You mention something important: "We're switching to Tailwind"
2. System detects it instantly
3. Claude helps confirm: "Should I remember this?"
4. System ingests it into the knowledge base
5. Future conversations: Claude references it naturally

### For You

You don't need to do anything special! Just work normally:

```
You: "Let's switch from Bootstrap to Tailwind for better customization"
Claude: "I detected a technology change. Should I remember that example-app is now using Tailwind CSS?"
You: "Yes"
Claude: "Noted! I'll remember this for future work on example-app"
```

---

## What Gets Learned

The system creates/updates these documents automatically:

### 1. `LEARNED_INSIGHTS.md` (In project root)
Captures important discoveries:
```markdown
## Technology Stack Changes
- Switched from Bootstrap to Tailwind CSS (2025-10-27)
- Using GraphQL instead of REST (2025-10-25)

## Architecture Decisions
- Implemented microservices pattern for API (2025-10-20)

## Performance Optimizations
- Query timeout issue in user search (fixed 2025-10-15)

## Important Gotchas
- Watch out for timezone handling in date calculations
```

### 2. `project_profile` MCP
The knowledge base gets updated with:
- New decision records
- Architecture changes
- Technology choices
- Known issues and workarounds

---

## Real-World Example

### Scenario: Building a React App

**Conversation:**
```
You: "Claude, let's refactor this component from class to hooks"
Claude: "Good idea! Let me help with that conversion..."
[Claude helps with the refactor]
You: "Great! We're now using hooks everywhere for consistency"

Claude: "I detected a codebase change - should I remember that this project
         now uses React hooks instead of class components?"
You: "Yes"
Claude: "Perfect! I'll remember this pattern for future refactoring work"
```

**What Happened:**
- Pattern detected: architecture change (refactor)
- Confidence: 85%
- User confirmed
- System updated knowledge base
- Next time: Claude remembers this is a hooks-first project

---

## Advanced: Understanding Confidence Scores

Each pattern has a confidence score based on keywords and context:

```python
# Examples from ConversationWatcher

# High confidence (95%)
"We're switching from X to Y"

# High confidence (90%)
"We decided to use GraphQL"

# Medium confidence (85%)
"Now using PostgreSQL for..."

# Lower confidence (75%)
"Let's avoid this pattern"
```

Patterns below 75% confidence are logged but don't trigger prompts to avoid false positives.

---

## Troubleshooting

### RQ Workers Not Starting

```bash
# Check if Redis is running
redis-cli ping
# Should output: PONG

# If not, start Redis
brew services start redis

# Then try starting workers
./start_redis_workers.sh
```

### Workers Running But Not Learning

1. Check that messages are being published:
   ```bash
   redis-cli PUBSUB CHANNELS
   ```
   Should show: `1) "claude-os:conversations"`

2. Check worker logs:
   ```bash
   tail -f logs/rq_workers.log
   ```

3. Verify project_profile MCP is registered:
   ```bash
   claude mcp list
   ```

### Knowledge Not Appearing

1. The knowledge base updates appear in:
   - `project_root/LEARNED_INSIGHTS.md` (local file)
   - `project_profile` MCP (in Claude Code context)

2. If not appearing:
   - Confirm worker detected the pattern (check logs)
   - Verify you confirmed the learning prompt
   - Check that MCP endpoint is reachable

---

## The Vision: Why This Matters

Claude OS was built with one principle: **Claude should be a genuine team member**.

A team member:
- ✅ Learns from conversations
- ✅ Remembers important decisions
- ✅ Builds context over time
- ✅ Improves with project experience
- ✅ Never forgets what you've decided

This learning system makes all of that possible. Every conversation teaches Claude more about your project, making it progressively smarter.

---

## Next Steps

1. **Initialize your project**: When you initialize with `/initialize-project`, workers start automatically
2. **Work normally**: No need to change how you work
3. **Confirm learnings**: When prompted, say "yes" to let Claude remember important decisions
4. **Watch the knowledge grow**: Over time, Claude becomes an expert on your project

That's it! The system handles the rest.

---

## Technical Details

For developers interested in the implementation:

### Files
- `app/core/conversation_watcher.py` - Pattern detection (306 lines)
- `app/core/learning_jobs.py` - Job processing (323 lines)
- `app/core/redis_config.py` - Redis management (234 lines)
- `start_redis_workers.sh` - Worker startup script
- `logs/rq_workers.log` - Worker activity logs

### Architecture Pattern
- **Pub/Sub**: Redis PUBSUB for instant message delivery
- **Background Jobs**: RQ for reliable job processing
- **Confirmation**: HTTP callbacks for user interaction
- **MCP Integration**: Automatic knowledge base ingestion

---

## Questions?

The learning system is designed to be invisible and automatic. If you have questions or want to understand what's being learned, check:

1. **Local Learning Docs**: `project_root/LEARNED_INSIGHTS.md`
2. **Worker Logs**: `logs/rq_workers.log`
3. **Initialize Logs**: Watch the "Step 0/5" output when running `/initialize-project`

The system is always running, always learning, always making Claude smarter about your project.
