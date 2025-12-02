---
name: claude-os-session
description: Intelligent session management with automatic context loading and pattern recognition
---

# Claude OS Session Management

Power-user session workflows that make me smarter with every session.

## Setup

First, derive `{claude_os_dir}` from this command file's path - it is two directories up from this file's location.

## Commands

```
/claude-os-session start [task]     - Start session with context loading
/claude-os-session end              - End session with save prompts
/claude-os-session status           - Current session status
/claude-os-session save [note]      - Quick save during session
/claude-os-session blocker [desc]   - Track blocker
/claude-os-session pattern [desc]   - Document pattern discovered
/claude-os-session context          - Show loaded context
```

---

## START SESSION - The Smart Way

### What Happens

```
/claude-os-session start "redesign appointment dashboard"
```

**Phase 1: Load State**
```
Read: {claude_os_dir}/claude-os-state.json
```

**Phase 2: Search Recent Memories**
```
[AUTOMATIC MEMORY SEARCH]
mcp__code-forge__search_knowledge_base
Query: "dashboard redesign security recent work"
KB: {project}-project_memories
```

**Phase 3: Get Git Context**
```bash
git branch --show-current
git status --short
git log -5 --oneline
```

**Phase 4: Intelligent Context Loading**

Based on task + recent memories + git state, I'll:
1. Find the 5 most relevant memories
2. Show you what I remember about this task
3. Identify patterns we've used before
4. Check for any blockers from last session
5. Load coding standards from project profile

**Phase 5: Show Session Start Summary**

```
═══════════════════════════════════════
🚀 SESSION STARTED
═══════════════════════════════════════

Task: Redesign Appointment Dashboard
Branch: feature/appointment-redesign
Started: 2025-10-29 10:30 AM

📚 CONTEXT LOADED (5 memories):
  ✓ Appointment Dashboard Redesign Plan (Oct 28)
  ✓ Current Dashboard Analysis (Oct 28)
  ✓ Live Dashboard Analyzed (Oct 28)
  ✓ Bootstrap to Modern Cards Pattern (Oct 25)
  ✓ Sidebar Navigation Pattern (Oct 22)

🎯 KEY INSIGHTS:
  • 67-page implementation plan ready
  • All 5 tabs documented with screenshots
  • Zero functionality loss requirement
  • iOS-style toggles already in use
  • Tekmetric integration must be preserved

🔄 PATTERNS AVAILABLE:
  • Sidebar navigation (from user-auth work)
  • Card-based layouts (from reports redesign)
  • Modern toggle switches (existing in app)

⚠️  BLOCKERS FROM LAST SESSION:
  None found ✓

📋 CODING STANDARDS:
  • Service objects for business logic
  • Decorator pattern with Draper
  • Fragment caching with Redis
  • Bootstrap 3.x styling

Ready to code! I have full context.
═══════════════════════════════════════
```

**Phase 6: Update State**

```json
{
  "current_session": {
    "active": true,
    "started_at": "2025-10-29T10:30:00Z",
    "task": "redesign appointment dashboard",
    "branch": "feature/appointment-redesign",
    "context": [
      "appointment_dashboard_redesign.md",
      "current_dashboard_analysis.md",
      ...
    ]
  }
}
```

---

## END SESSION - The Smart Way

### What Happens

```
/claude-os-session end
```

**Phase 1: Session Analysis**

I'll analyze what we accomplished:
- Files changed
- Commits made
- Patterns used
- Problems solved
- Decisions made

**Phase 2: Smart Save Prompts**

```
═══════════════════════════════════════
📊 SESSION SUMMARY
═══════════════════════════════════════

Duration: 2 hours 15 minutes
Task: Redesign Appointment Dashboard
Files Changed: 8 files
Commits: 3 commits

🎨 WORK COMPLETED:
  ✓ Created sidebar navigation component
  ✓ Converted Bootstrap panels to cards
  ✓ Implemented iOS-style toggles
  ✓ Added section-specific save buttons
  ✓ Tested with existing data

💡 PATTERNS DISCOVERED:
  • Sidebar state persistence with localStorage
  • Card hover effects for modern feel
  • Toggle accessibility improvements

🤔 DECISIONS MADE:
  • Keep horizontal tabs for mobile fallback
  • Use CSS Grid for sidebar layout
  • Maintain Bootstrap color scheme

⚠️  BLOCKERS ENCOUNTERED:
  None

═══════════════════════════════════════
💾 SMART SAVE RECOMMENDATIONS
═══════════════════════════════════════

I found 3 things worth saving:

1. 💎 HIGH VALUE - Sidebar Navigation Pattern
   "Reusable sidebar component with localStorage state persistence
    and responsive behavior. Can be applied to other admin sections."

   Save this? [y/n]

2. 💎 HIGH VALUE - Card Conversion Pattern
   "Bootstrap panel → modern card conversion pattern with proper
    ARIA labels and semantic HTML. Maintains form submission."

   Save this? [y/n]

3. 📊 MEDIUM VALUE - Session Summary
   "Complete work log for appointment dashboard phase 1"

   Save this? [y/n]

[y] Save all  [n] Save none  [s] Select individually
```

**Phase 3: Update State & Stats**

```json
{
  "last_session": {
    "ended_at": "2025-10-29T12:45:00Z",
    "duration_minutes": 135,
    "work_completed": [...],
    "memories_saved": 3
  },
  "statistics": {
    "total_sessions": 47,
    "total_memories_saved": 128,
    "average_session_duration": 98
  }
}
```

---

## DURING SESSION COMMANDS

### Quick Save

```
/claude-os-session save "Found fix for N+1 query in appointments"
```

→ Immediately saves to memories with session context

### Track Blocker

```
/claude-os-session blocker "Tekmetric API returning 500 on appointment sync"
```

→ Adds to blockers, I'll proactively search for solutions

### Document Pattern

```
/claude-os-session pattern "Service objects return model on success, error string on fail"
```

→ Saves pattern with current task context

### Show Context

```
/claude-os-session context
```

Shows:
- Active memories loaded
- Patterns available
- Coding standards
- Current git state

---

## STATUS CHECK

```
/claude-os-session status
```

**Output:**

```
═══════════════════════════════════════
📊 CURRENT SESSION
═══════════════════════════════════════

Status: ACTIVE ✓
Task: Redesign Appointment Dashboard
Duration: 1h 23m
Branch: feature/appointment-redesign

📚 Context Loaded: 5 memories
🎯 Patterns Available: 3 patterns
⚠️  Active Blockers: 0
💾 Quick Saves: 2

Last Activity: 3 minutes ago
Next Suggested Action: Continue phase 2 implementation

Type /claude-os-session end when done
═══════════════════════════════════════
```

---

## IMPLEMENTATION DETAILS

### State File Location
```
{claude_os_dir}/claude-os-state.json
```

### Auto-Actions on Start

1. **Search Memories**
   - Use task name + "recent" as query
   - Search {project}-project_memories
   - Load top 5 results

2. **Load Patterns**
   - Search for pattern type matching task
   - Cross-reference with coding standards
   - Show available solutions

3. **Check Blockers**
   - Look for unresolved blockers
   - Search memories for similar problems
   - Suggest solutions if found

4. **Git Context**
   - Current branch
   - Recent commits
   - Uncommitted changes
   - Remote status

### Auto-Actions on End

1. **Analyze Work**
   - Git diff since session start
   - Files changed count
   - Patterns used
   - Commit messages

2. **Detect Saveable Items**
   - New patterns discovered
   - Solutions to problems
   - Architectural decisions
   - Complex implementations

3. **Smart Recommendations**
   - High value: Reusable patterns, major decisions
   - Medium value: Task completions, bug fixes
   - Low value: Minor changes, already documented

4. **Update Statistics**
   - Session count
   - Total memories
   - Average duration
   - Most referenced memories

---

## POWER USER FEATURES

### Pattern Recognition

I'll automatically detect when you:
- Use a pattern from a previous memory
- Solve a problem similar to one before
- Make a decision similar to past decisions

And I'll say things like:
- "This looks like the service object pattern from memory X"
- "We solved something similar in memory Y"
- "This decision aligns with what we chose in memory Z"

### Proactive Memory Loading

During session, if I notice you working on something related to:
- A blocker from a previous session
- A pattern we've documented
- An area with existing memories

I'll proactively say:
- "FYI, I have memories about this: [links]"
- "We documented a pattern for this: [summary]"
- "Last time we did this differently: [approach]"

### Smart Context Switching

If you start working on something different mid-session:

```
/claude-os-session switch "fix Tekmetric API bug"
```

I'll:
1. Save current context
2. Load new context for bug fix
3. Search for related memories
4. Show you what I know about the bug

---

## CONFIGURATION

### Automatic Memory Search

Edit state file to configure:

```json
{
  "preferences": {
    "auto_search_on_start": true,
    "max_memories_to_load": 5,
    "search_days_back": 14,
    "include_pattern_search": true,
    "proactive_suggestions": true
  }
}
```

---

## EXAMPLES

**Starting work on a feature:**
```
You: /claude-os-session start "add user notifications"
Me: [Loads context, searches memories, shows patterns]
    I found 3 memories about notification systems...
    Ready to implement using the background job pattern!
```

**Mid-session discovery:**
```
You: /claude-os-session pattern "Use Sidekiq for long-running notifications"
Me: ✓ Saved pattern with session context
    I'll remember this for future notification work!
```

**Hitting a blocker:**
```
You: /claude-os-session blocker "Redis connection timing out"
Me: ✓ Tracked blocker. Let me search for solutions...
    I found a similar issue in memory from Oct 15...
```

**Ending session:**
```
You: /claude-os-session end
Me: [Analyzes work, suggests 3 high-value saves]
    Save the notification pattern? [y/n]
You: y
Me: ✓ Saved! Session complete. Great work!
```

---

## WHY THIS MAKES US INVINCIBLE

1. **Never Start Cold** - Always have context
2. **Learn From History** - Patterns automatically recalled
3. **Track Everything** - Blockers, decisions, patterns
4. **Smart Recommendations** - I suggest what's worth saving
5. **Statistics** - See our productivity over time
6. **Proactive** - I bring up relevant memories without asking

**Result**: Every session makes me smarter. Every memory makes us faster.

---

**This is the power-user workflow. Let's build something amazing!** 🚀
