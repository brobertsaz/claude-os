# Session Start Protocol

**What Claude Should Do AUTOMATICALLY When You Start ANY Conversation**

---

## 🎯 The Problem

When you start Claude Code CLI:
- You're in a specific project directory
- You may have been working on something
- There's context from previous sessions
- You have knowledge in Claude OS

**But Claude starts with ZERO context.**

---

## ✅ The Solution: Automatic Session Start

**Every time a conversation starts, Claude should:**

### Phase 1: Detect Project (5 seconds)

```bash
# Check for Claude OS project
pwd
ls -la | grep -E "(CLAUDE.md|.claude-os|agent-os)"
```

**If `.claude-os/config.json` exists:**
- ✅ This is a Claude OS project
- → Proceed with full session start

**If not:**
- ℹ️  Generic mode (no project context)
- → Offer to initialize with `/claude-os-init`

---

### Phase 2: Read Project State (10 seconds)

**Files to read:**

1. **`CLAUDE.md`** - Project overview (always loaded first)
2. **`.claude-os/config.json`** - Project configuration
3. **`claude-os-state.json`** - Session state (if exists)
4. **`agent-os/config.yml`** - Agent-OS config (if using specs)

**Example:**
```
Reading CLAUDE.md...
Reading .claude-os/config.json...
Reading claude-os-state.json...

✓ Project: Pistn
✓ MCPs: 4 configured
✓ Last session: Oct 29, 2025 (2 days ago)
✓ Agent-OS: Enabled (3 active specs)
```

---

### Phase 3: Check Git Context (5 seconds)

```bash
git branch --show-current
git status --short
git log -3 --oneline
git remote get-url origin
```

**Extract:**
- Current branch name
- Uncommitted changes count
- Recent commits
- Whether we're ahead/behind remote

**Example:**
```
Branch: feature/appointment-redesign
Status: 3 files modified, 1 untracked
Recent commits:
  - abc1234 Add sidebar navigation
  - def5678 Convert panels to cards
  - ghi9012 Update appointment form layout
```

---

### Phase 4: Search Project Memories (15 seconds)

**Search query based on:**
- Last session task (from `claude-os-state.json`)
- Current branch name
- Recent commit messages
- `+recent` modifier

**Example query:**
```
"appointment dashboard redesign recent"
```

**Search:**
- `{project}-project_memories` knowledge base
- Return top 5 most relevant memories
- Show me titles and key insights

**Example:**
```
📚 Found 5 relevant memories:
  1. Appointment Dashboard Redesign Plan (Oct 28)
     → 67-page implementation plan, 5 tabs documented

  2. Current Dashboard Analysis (Oct 28)
     → All features catalogued, zero functionality loss

  3. Bootstrap to Modern Cards Pattern (Oct 25)
     → Reusable conversion pattern

  4. Sidebar Navigation Pattern (Oct 22)
     → localStorage persistence, responsive

  5. Tekmetric Integration Notes (Oct 20)
     → Must preserve API sync on save
```

---

### Phase 5: Load Coding Standards (10 seconds)

**Search `{project}-project_profile`:**
- Query: "coding standards architecture conventions"
- Load key architectural decisions
- Load tech stack preferences

**Example:**
```
📋 Coding Standards:
  • Service objects for business logic
  • Decorator pattern with Draper
  • Fragment caching with Redis
  • Bootstrap 3.x styling (no Bootstrap 4/5)
  • RSpec for testing
  • Concerns for shared controller logic
```

---

### Phase 6: Check Kanban Board (5 seconds)

**If Agent-OS is enabled:**

```http
GET /api/projects/{id}/kanban
```

**Show:**
- Total specs
- Active specs (not completed/archived)
- Current tasks in progress
- Next tasks todo

**Example:**
```
📊 Kanban Board:
  • 3 specs total (52 tasks)
  • 1 spec in progress: Group Account Rendering (45% complete)
  • 2 tasks in progress:
    - PHASE2-TASK3: Implement concern methods
    - PHASE2-TASK4: Add helper methods
  • 29 tasks remaining
```

---

### Phase 7: Present Session Start Summary (Display to User)

**Format:**

```
═══════════════════════════════════════════════════════════════
🚀 WELCOME BACK!
═══════════════════════════════════════════════════════════════

📁 Project: Pistn (Ruby on Rails)
🌿 Branch: feature/appointment-redesign
📅 Last Session: 2 days ago (Oct 29, 2025)
⏱️  Duration: 2h 15m

═══════════════════════════════════════════════════════════════
📚 CONTEXT LOADED
═══════════════════════════════════════════════════════════════

✓ 5 relevant memories found
✓ Coding standards loaded
✓ 3 architectural patterns available
✓ Kanban board synced (45% complete)

🎯 LAST TASK: Redesign Appointment Dashboard

We completed:
  ✓ Sidebar navigation component
  ✓ Bootstrap panels → modern cards
  ✓ iOS-style toggle switches

Still working on:
  ⏳ Phase 2: Implement concern methods
  ⏳ Phase 2: Add helper methods

═══════════════════════════════════════════════════════════════
💡 KEY INSIGHTS
═══════════════════════════════════════════════════════════════

• 67-page implementation plan available
• Zero functionality loss requirement
• Tekmetric integration must be preserved
• Bootstrap 3.x only (no v4/v5)

═══════════════════════════════════════════════════════════════
🔄 AVAILABLE PATTERNS
═══════════════════════════════════════════════════════════════

• Sidebar navigation (from user-auth work)
• Card-based layouts (from reports redesign)
• Modern toggle switches (already in app)
• Service object pattern (business logic)
• Draper decorators (view logic)

═══════════════════════════════════════════════════════════════
⚠️  STATUS
═══════════════════════════════════════════════════════════════

Git Status:
  • 3 files modified
  • 1 file untracked
  • ⚠️  Uncommitted changes (from last session)

Blockers:
  • None! ✓

═══════════════════════════════════════════════════════════════
🎯 SUGGESTED NEXT STEPS
═══════════════════════════════════════════════════════════════

Option 1: Continue Phase 2 Implementation
  → Implement concern methods for PHASE2-TASK3
  → Should take ~30 minutes based on estimate

Option 2: Commit Previous Work
  → 3 files modified need to be committed
  → Clean git state before starting new work

Option 3: Start Something New
  → Tell me what you'd like to work on

═══════════════════════════════════════════════════════════════

What would you like to do?
```

---

## 🎛️ Configuration

**Auto-start can be configured in `.claude-os/config.json`:**

```json
{
  "session_management": {
    "auto_start": true,
    "auto_search_memories": true,
    "max_memories_to_load": 5,
    "search_days_back": 14,
    "show_git_status": true,
    "show_kanban_status": true,
    "proactive_suggestions": true
  }
}
```

---

## 🚫 When NOT to Auto-Start

**Skip session start if:**
- User message starts with a direct question (e.g., "What is...")
- User is clearly asking for help/docs (e.g., "How do I...")
- User explicitly says "ignore context" or "fresh start"
- No `.claude-os/` directory exists

**In these cases:**
- Answer the question directly
- Offer to initialize Claude OS after answering

---

## 📊 Session Tracking During Conversation

**Throughout the session, Claude should:**

### Track Key Events
- When user starts implementing something
- When they hit a blocker
- When they discover a pattern
- When they make an architectural decision
- When they solve a complex problem

### Proactive Memory References
```
You: "I need to add caching to this endpoint"
Claude: "FYI, we have a memory about fragment caching with Redis
         from the reports redesign. Want me to use that pattern?"
```

### Auto-Save Suggestions
```
You: "Finally got the Tekmetric sync working with the new structure!"
Claude: "That sounds like a high-value solution. Would you like me
         to save this to project memories for future reference?"
```

---

## 💾 Session End Protocol

**When conversation ends (or user says "done"):**

### Option 1: User Runs `/claude-os-session end`
- Follow the detailed end protocol from claude-os-session.md
- Analyze work, suggest saves, update statistics

### Option 2: Conversation Ends Naturally
- Claude should still provide a brief summary:

```
═══════════════════════════════════════════════════════════════
📊 SESSION COMPLETE
═══════════════════════════════════════════════════════════════

Duration: ~45 minutes
Work: Implemented concern methods for PHASE2-TASK3

Quick saves available:
  • Concern method pattern for group accounts
  • Service object integration approach

Run /claude-os-session end for full summary and saves
Or just continue working next time - I'll remember!
═══════════════════════════════════════════════════════════════
```

---

## 🎯 The Goal

**Every session should feel like:**
- Claude already knows everything
- Claude remembers what we were doing
- Claude proactively brings up relevant context
- Claude suggests next steps based on history
- Zero context loss between sessions

**NOT like:**
- Starting from scratch
- Repeating ourselves
- Explaining the same architecture again
- Searching for what we did before

---

## 🔄 Implementation Checklist

For Claude to do this automatically:

- [ ] Check for `.claude-os/` directory at conversation start
- [ ] Read `CLAUDE.md` if present
- [ ] Read `.claude-os/config.json` if present
- [ ] Read `claude-os-state.json` if present
- [ ] Run git status and git log
- [ ] Search project_memories with intelligent query
- [ ] Load coding standards from project_profile
- [ ] Check Kanban board status (if Agent-OS enabled)
- [ ] Present comprehensive session start summary
- [ ] Track key events during session
- [ ] Provide session end summary

---

**This protocol ensures you NEVER start a conversation from zero context again!** 🚀
