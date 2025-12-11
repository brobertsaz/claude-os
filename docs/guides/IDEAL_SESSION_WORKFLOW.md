# The Ideal Claude OS Session Workflow

**What SHOULD happen vs what ACTUALLY happens (and how to fix it)**

---

## 🌅 Morning Coffee Scenario

You grab your coffee, open your terminal, and type:

```bash
cd ~/Projects/pistn
code .
# Claude Code CLI opens
```

---

## ✅ IDEAL: What SHOULD Happen Automatically

```
═══════════════════════════════════════════════════════════════
🚀 CLAUDE OS INITIALIZED
═══════════════════════════════════════════════════════════════

Detected Project: Pistn (Ruby on Rails)
Loading context... ⏳

[Claude automatically reads:]
✓ CLAUDE.md
✓ .claude-os/config.json
✓ claude-os-state.json
✓ agent-os/config.yml

[Claude automatically checks:]
✓ Git status (feature/appointment-redesign, 3 files modified)
✓ Recent commits (last 3)
✓ Project memories (searching "appointment dashboard recent")

[Claude automatically loads:]
✓ 5 relevant memories
✓ Coding standards
✓ Architectural patterns
✓ Kanban board (3 specs, 52 tasks, 45% complete)

═══════════════════════════════════════════════════════════════
📚 CONTEXT LOADED - Ready to code!
═══════════════════════════════════════════════════════════════

You were working on: Appointment Dashboard Redesign
Progress: 45% complete (23 of 52 tasks done)

Last session: 2 days ago
Duration: 2h 15m
Completed: Sidebar navigation, card layouts, toggle switches

Still in progress:
  ⏳ PHASE2-TASK3: Implement concern methods
  ⏳ PHASE2-TASK4: Add helper methods

═══════════════════════════════════════════════════════════════
💡 KEY REMINDERS
═══════════════════════════════════════════════════════════════

• 67-page implementation plan in memories
• Zero functionality loss requirement
• Tekmetric integration must work on save
• Use service objects for business logic
• Bootstrap 3.x only (no v4/v5)

═══════════════════════════════════════════════════════════════
🎯 SUGGESTED ACTIONS
═══════════════════════════════════════════════════════════════

1. Continue Phase 2 (30 min estimated)
2. Commit your 3 modified files first
3. Start something new

What would you like to do?
═══════════════════════════════════════════════════════════════
```

**You say:** "Let's continue phase 2"

**Claude:** "Perfect! Let me implement the concern methods for PHASE2-TASK3. Based on our service object pattern, I'll..."

---

## ❌ CURRENT: What ACTUALLY Happens

```
You: [Opens Claude Code]

Claude: Hello! How can I help you today?

You: Let's continue working on the appointment dashboard

Claude: I'd be happy to help with the appointment dashboard!
        Could you tell me more about the project and what
        you've been working on?

You: *Sigh* We're redesigning the appointment dashboard in
     Pistn. We've been working on this for 2 days. I have
     a 67-page implementation plan. We completed the sidebar
     and cards. We're on phase 2...

Claude: Thanks for the context! What would you like to work
        on specifically?

You: Let me just share the implementation plan again...
     [Copies and pastes 67 pages]
```

**Problem:** You spend 15 minutes re-explaining everything Claude should already know!

---

## 🔧 THE FIX: Making It Work Today

**Until automatic session start is implemented in Claude Code itself, YOU need to trigger it manually:**

### Step 1: Add This to Your CLAUDE.md

```markdown
# IMPORTANT: Session Start Protocol

**EVERY TIME we start a conversation, YOU (Claude) must:**

1. **Check if this is a Claude OS project**
   ```bash
   ls -la | grep -E "(CLAUDE.md|.claude-os|agent-os)"
   ```

2. **If yes, AUTOMATICALLY do the following WITHOUT me asking:**

   a) Read these files:
      - CLAUDE.md (you're reading it now!)
      - .claude-os/config.json
      - claude-os-state.json (if exists)
      - agent-os/config.yml (if exists)

   b) Check git context:
      ```bash
      git branch --show-current
      git status --short
      git log -3 --oneline
      ```

   c) Search my project memories:
      - Use last session task + current branch + "recent"
      - Load top 5 memories from {project}-project_memories

   d) Load coding standards:
      - Search {project}-project_profile for "coding standards"

   e) Check Kanban board:
      - GET /api/projects/{id}/kanban
      - Show current spec progress

   f) Present a session start summary showing:
      - What we were working on last
      - Current progress
      - Key reminders
      - Suggested next steps

3. **Then ask:** "What would you like to work on?"

**DO THIS AUTOMATICALLY. DO NOT wait for me to ask!**
```

### Step 2: Create a Morning Routine

Add this alias to your `~/.zshrc` or `~/.bashrc`:

```bash
alias pistn='cd ~/Projects/pistn && code . && cat .claude-os/session-reminder.txt'
```

Create `.claude-os/session-reminder.txt`:

```
═══════════════════════════════════════════════════════════════
🚨 REMINDER TO CLAUDE 🚨
═══════════════════════════════════════════════════════════════

This is a Claude OS project!

Please AUTOMATICALLY:
1. Read CLAUDE.md
2. Read .claude-os/config.json
3. Check git status
4. Search project_memories
5. Load coding standards
6. Check Kanban board
7. Present session start summary

DO NOT make me paste context manually!
═══════════════════════════════════════════════════════════════
```

Now you just type `pistn` and Claude will see the reminder!

### Step 3: Use Session Commands

When you want to ensure context is loaded:

```bash
# Option A: Explicit session start
/claude-os-session start "continue appointment dashboard"

# Option B: Just remind Claude
"Hey Claude, can you load my project context and tell me
 where we left off?"

# Option C: Direct command
"Read CLAUDE.md, check git status, search my memories for
 'appointment dashboard', and load my coding standards.
 Then tell me what we were working on."
```

---

## 🎯 Making This Automatic (Future)

**What needs to happen for true automation:**

### In Claude Code CLI:

1. **Project Detection Hook**
   - When CLI starts, check for `.claude-os/`
   - If found, trigger automatic context loading
   - Display session start summary

2. **Auto-Load Behavior**
   - Read `CLAUDE.md` into system prompt
   - Search knowledge bases automatically
   - Present context before user types anything

3. **Session State Persistence**
   - Save session state on exit
   - Restore on next start
   - Track what was being worked on

### In Claude OS:

4. **Session API Endpoint**
   ```http
   GET /api/projects/{id}/session/start

   Returns:
   - Last session summary
   - Relevant memories (top 5)
   - Coding standards
   - Git context
   - Kanban status
   - Suggested actions
   ```

5. **MCP Session Tool**
   - Expose session data via MCP
   - Claude Code can call it automatically
   - No user intervention needed

---

## 📋 Checklist: Am I Using Sessions Effectively?

### ✅ Good Session Practice

- [ ] Claude presents context at start without me asking
- [ ] I never re-explain the project architecture
- [ ] Claude references past decisions automatically
- [ ] I can pick up exactly where I left off
- [ ] Claude suggests next steps based on history

### ❌ Bad Session Practice

- [ ] I paste the same context document every session
- [ ] I explain "we use service objects" every time
- [ ] Claude asks "what's your tech stack?" repeatedly
- [ ] I have to search for what I did yesterday
- [ ] Every session feels like starting over

---

## 🔥 Power User Tips

### 1. Create Session Shortcuts

```bash
# ~/.zshrc
alias cs-start='echo "Claude: load context, check memories, show status"'
alias cs-end='echo "Claude: analyze session, suggest saves, update state"'
alias cs-blocker='echo "Claude: track blocker and search for solutions"'
```

### 2. Use Quick Saves During Work

```bash
# When you discover something important
/claude-os-session save "Service objects return model on success, error on fail"

# When you hit a blocker
/claude-os-session blocker "Tekmetric API 500 errors on appointment sync"

# When you find a pattern
/claude-os-session pattern "Use localStorage for sidebar state persistence"
```

### 3. End Sessions Properly

```bash
# At end of day
/claude-os-session end

# Claude will:
# - Analyze what you did
# - Suggest high-value saves
# - Update statistics
# - Prepare context for next session
```

### 4. Check Status Mid-Session

```bash
/claude-os-session status

# Shows:
# - How long you've been working
# - What context is loaded
# - Active blockers
# - Next suggested action
```

---

## 🚀 The Ultimate Goal

**Imagine this future:**

You open Claude Code. No typing needed. Claude says:

```
Welcome back! It's been 2 days since your last session.

You were redesigning the Appointment Dashboard. You're 45% done
(23 of 52 tasks). Last session you completed the sidebar navigation
and card layouts.

You have 2 tasks in progress:
- PHASE2-TASK3: Implement concern methods (30 min estimated)
- PHASE2-TASK4: Add helper methods (20 min estimated)

I have your 67-page implementation plan loaded, plus 5 relevant
memories and all your coding standards.

Your git branch has 3 uncommitted files. Want to commit those
first or continue with PHASE2-TASK3?
```

**That's zero context loss. That's the vision.**

---

## 📖 Related Docs

- [SESSION_START_PROTOCOL.md](./SESSION_START_PROTOCOL.md) - Detailed protocol
- [claude-os-session.md](../../templates/commands/claude-os-session.md) - Command reference
- [WHAT_IS_CLAUDE_OS.md](./WHAT_IS_CLAUDE_OS.md) - Overall system guide

---

**Until full automation exists, use the CLAUDE.md instructions and session commands to get the same result manually. But it WILL be automatic soon!** 🚀
