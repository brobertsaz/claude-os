# Recommended Skills

**Our curated list of skills we actually use and trust.**

This isn't a comprehensive catalog—it's an opinionated "staff picks" of skills that have proven valuable in real projects. Each skill is here because we've used it and found it genuinely improves how Claude Code works.

---

## How We Choose Skills

A skill makes this list if it:
- ✅ We've actually used it in real projects
- ✅ It solves a real problem (not theoretical)
- ✅ It's well-written with clear instructions
- ✅ It prevents common mistakes or saves significant time

---

## 🔧 Debugging & Problem Solving

### systematic-debugging ⭐ Essential
**Source:** [superpowers-marketplace](https://github.com/obra/superpowers)

The most important debugging skill. Five-phase framework that prevents "guess and check" debugging:

| Phase | What It Does |
|-------|--------------|
| **Phase 0: Problem Intake** | ASK QUESTIONS before investigating |
| **Phase 1: Root Cause** | Read errors, reproduce, gather evidence |
| **Phase 2: Pattern Analysis** | Find working examples, compare |
| **Phase 3: Hypothesis** | Form theory, test minimally |
| **Phase 4: Implementation** | Fix with TDD, verify |

**Why we love it:** The Phase 0 "ask first" approach prevents Claude from jumping straight into code when you report a bug. The confidence rule (ask if <90% confident) is gold.

**Install:** `/claude-os-skills install` → Community Skills → superpowers → systematic-debugging

---

### root-cause-tracing
**Source:** [superpowers-marketplace](https://github.com/obra/superpowers)

When errors occur deep in the call stack, this skill teaches Claude to trace backward to find the original trigger instead of fixing symptoms.

**When to use:**
- Stack trace shows long call chain
- Unclear where invalid data originated
- Fixing the obvious spot didn't work

**Key insight:** "NEVER fix just where the error appears. Trace back to find the original trigger."

**Install:** `/claude-os-skills install` → Community Skills → superpowers → root-cause-tracing

---

## ✅ Testing

### test-driven-development
**Source:** [superpowers-marketplace](https://github.com/obra/superpowers)

Rigorous TDD: write failing test first, watch it fail, write minimal code to pass.

**The Iron Law:** "NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST"

**When to use:**
- Bug fixes (always—proves the fix works)
- New features (when quality matters)
- Refactoring (safety net)

**Why it works:** If you didn't watch the test fail, you don't know if it tests the right thing.

**Install:** `/claude-os-skills install` → Community Skills → superpowers → test-driven-development

---

### testing-anti-patterns
**Source:** [superpowers-marketplace](https://github.com/obra/superpowers)

Prevents common testing mistakes:
- Testing mock behavior instead of real code
- Adding test-only methods to production code
- Mocking without understanding dependencies

**When to use:** Whenever writing or reviewing tests.

**Install:** `/claude-os-skills install` → Community Skills → superpowers → testing-anti-patterns

---

## 🔄 Workflows & Process

### verification-before-completion ⭐ Essential
**Source:** [superpowers-marketplace](https://github.com/obra/superpowers)

Prevents Claude from saying "done" without proof.

**The Iron Law:** "NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE"

**What it prevents:**
- "Should pass now" (without running tests)
- "Looks correct" (without verification)
- "Fixed!" (without testing the fix)

**Why we love it:** Catches the #1 Claude bad habit—claiming success without evidence.

**Install:** `/claude-os-skills install` → Community Skills → superpowers → verification-before-completion

---

### brainstorming
**Source:** [superpowers-marketplace](https://github.com/obra/superpowers)

Structured process for turning ideas into designs:
1. Understand the idea (ask questions one at a time)
2. Explore approaches (2-3 options with trade-offs)
3. Present design (in small sections, validate each)

**When to use:** Before implementing any non-trivial feature.

**Key principle:** "One question at a time—don't overwhelm."

**Install:** `/claude-os-skills install` → Community Skills → superpowers → brainstorming

---

### using-git-worktrees
**Source:** [superpowers-marketplace](https://github.com/obra/superpowers)

Work on multiple branches simultaneously without switching. Creates isolated workspaces sharing the same repository.

**When to use:**
- Feature work that needs isolation
- Reviewing PRs while your work stays intact
- Comparing behavior between branches

**Install:** `/claude-os-skills install` → Community Skills → superpowers → using-git-worktrees

---

## 🤖 Agent Coordination

### dispatching-parallel-agents
**Source:** [superpowers-marketplace](https://github.com/obra/superpowers)

When you have 3+ independent failures, dispatch separate agents to investigate concurrently.

**When to use:**
- Multiple test files failing with different causes
- Multiple subsystems broken independently
- Each problem can be understood in isolation

**When NOT to use:**
- Failures might be related
- Need to understand full system context
- Exploratory debugging (don't know what's broken yet)

**Install:** `/claude-os-skills install` → Community Skills → superpowers → dispatching-parallel-agents

---

### requesting-code-review
**Source:** [superpowers-marketplace](https://github.com/obra/superpowers)

Dispatch a code review subagent after completing significant work.

**When to use:**
- After implementing a feature
- Before creating a PR
- After architectural changes

**Install:** `/claude-os-skills install` → Community Skills → superpowers → requesting-code-review

---

## 📄 Document & File Skills

### pdf
**Source:** [Anthropic Official](https://github.com/anthropics/skills)

Create, edit, and analyze PDF documents.

**Install:** `/claude-os-skills install` → Community Skills → anthropic → pdf

---

### xlsx
**Source:** [Anthropic Official](https://github.com/anthropics/skills)

Spreadsheet manipulation with formulas, formatting, and data analysis.

**Install:** `/claude-os-skills install` → Community Skills → anthropic → xlsx

---

### frontend-design
**Source:** [Anthropic Official](https://github.com/anthropics/skills)

Create distinctive, production-grade UI components. Avoids generic "AI-generated" aesthetics.

**Install:** `/claude-os-skills install` → Community Skills → anthropic → frontend-design

---

## 🛤️ Rails-Specific (Create Your Own)

These aren't in community repos but are worth creating for Rails projects:

### rails-debugging (template)

Extends systematic-debugging with Rails-specific tools:

```markdown
# Rails Debugging

## Console Investigation
docker-compose exec web bundle exec rails console
Account.find(123).inspect

## Log Investigation
docker-compose logs -f web

## Route Debugging
docker-compose exec web bundle exec rails routes | grep <pattern>

## Common Gotchas
- form_for @object vs :symbol (f.object will be nil with symbol)
- exists?() over pluck().include?() for efficiency
```

### hybrid-testing (template)

Our testing philosophy:

```markdown
# Hybrid Testing

BUG FIX → Write failing test FIRST, then fix (TDD)
NEW FEATURE → Build feature, then test core flows (Pragmatic)
CRITICAL → Test thoroughly (Rigorous)
```

---

## Quick Install Guide

### Via Claude OS UI
1. Open http://localhost:5173
2. Select your project
3. Click **Skills** tab
4. Click **Install Template**
5. Switch to **Community Skills** tab
6. Find skill → Click **Install**

### Via Command
```bash
/claude-os-skills install <skill-name>
```

### Via API
```bash
curl -X POST "http://localhost:8051/api/skills/community/install?project_path=/your/project" \
  -H "Content-Type: application/json" \
  -d '{"name": "systematic-debugging", "source": "superpowers"}'
```

---

## Our "Must Have" Stack

If you install nothing else, install these:

| Skill | Why |
|-------|-----|
| **systematic-debugging** | Prevents guess-and-check debugging |
| **verification-before-completion** | Prevents false "done" claims |
| **brainstorming** | Structured design before coding |

These three skills address the most common Claude Code failure modes.

---

## Contributing

Found a great skill we should add? [Open an issue](https://github.com/brobertsaz/claude-os/issues) with:
- Skill name and source
- Why you recommend it
- How you've used it

We'll try it out and add it if it meets our bar.

---

**See Also:**
- [Skills Guide](./SKILLS_GUIDE.md) - Full skills documentation
- [API Reference](../API_REFERENCE.md) - Skills API endpoints
