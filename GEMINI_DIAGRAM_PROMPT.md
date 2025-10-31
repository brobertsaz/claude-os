# Prompt for Gemini: Create Visual Diagrams for Claude OS

I need you to create professional, visually appealing diagrams for Claude OS documentation. Please create the following diagrams in a modern, clean style with consistent colors.

---

## Diagram 1: Claude OS - 5 Core Pillars Architecture

Create a modern architecture diagram showing these 5 interconnected components:

**Center Hub:** "Claude OS Ecosystem" (SQLite Database with Vector Embeddings)

**5 Pillars Around It:**
1. **Real-Time Learning System** 🧠
   - Redis Pub/Sub (< 1ms)
   - 10+ Pattern Types
   - Auto Knowledge Update

2. **Memory MCP** 💾
   - Persistent Memory
   - Natural Language Save
   - Instant Recall

3. **Semantic Knowledge Base** 📚
   - Vector Embeddings
   - Instant Semantic Search
   - 800+ Code Chunks

4. **Analyze-Project** 🔍
   - Intelligent Indexing
   - Auto Documentation
   - Git Hooks

5. **Session Management** 🎯
   - Context Preservation
   - Auto Resume
   - Zero Cold Starts

All connecting to:
**MCP Server (port 8051)** → **Claude Code Interface** → **You (Developer)**

Style: Modern, tech-focused, use colors like electric blue, teal, purple accents on dark background

---

## Diagram 2: Real-Time Learning Flow

Create a flowchart showing the learning pipeline:

```
Your Conversation
     ↓
Redis Pub/Sub (< 1ms latency)
     ↓
AI Pattern Detection (10 types)
     ↓
Confidence Check (75-95%)
     ↓
Auto Knowledge Update
     ↓
Instant Indexing to Vector DB
     ↓
Available in Next Conversation
```

Show the 10 pattern types branching from "Pattern Detection":
- Architectural Decisions
- Technology Changes
- Bug Fixes & Solutions
- Performance Insights
- Edge Cases & Gotchas
- Team Preferences
- Naming Conventions
- Common Pitfalls
- Integration Patterns
- Security Concerns

Style: Flowchart with decision nodes, modern flat design

---

## Diagram 3: Complete System Architecture

Create a detailed system architecture diagram:

```
┌─────────────────────────────────────────────────────┐
│            CLAUDE OS ECOSYSTEM                       │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌─────────────────┐   │
│  │Real-Time │  │ Memory   │  │ Analyze-Project │   │
│  │Learning  │  │ System   │  │ Indexing        │   │
│  │(Redis)   │  │ (MCP)    │  │ (Git Hooks)     │   │
│  └────┬─────┘  └────┬─────┘  └────┬────────────┘   │
│       │             │              │                 │
│       └─────────────┼──────────────┘                 │
│                     ▼                                │
│     ┌───────────────────────────────┐                │
│     │ Semantic Knowledge Base       │                │
│     │ (SQLite + sqlite-vec)         │                │
│     │ • 800+ code chunks indexed    │                │
│     │ • Vector embeddings           │                │
│     │ • Team patterns               │                │
│     │ • Architecture docs           │                │
│     └───────────────┬───────────────┘                │
│                     ▼                                │
│     ┌───────────────────────────────┐                │
│     │ MCP Server (http:8051)        │                │
│     │ Exposes ALL knowledge         │                │
│     └───────────────┬───────────────┘                │
│                     ▼                                │
│     ┌───────────────────────────────┐                │
│     │ Claude Code Interface         │                │
│     │ (Your superpowers here!)      │                │
│     └───────────────────────────────┘                │
└─────────────────────────────────────────────────────┘
```

Style: Technical diagram, modern, with clear data flow arrows

---

## Diagram 4: The Multiplier Effect Timeline

Create a timeline/growth chart showing:

**Week 1:** Basic learning (Claude learns project structure)
**Week 2:** Pattern recognition (Claude suggests patterns)
**Week 3:** Bug prevention (Claude catches bugs early)
**Week 4:** Architecture ideas (Claude contributes design)
**Month 2:** Expert level (Claude = most productive team member)

Show this as an exponential growth curve with annotations at each milestone.

Style: Infographic style, growth chart with milestones

---

## Diagram 5: Before & After Comparison

Create a split-screen comparison diagram:

**LEFT SIDE: Traditional Claude/AI** ❌
- Sessions start from zero
- Manual context copying
- Generic solutions
- 30 min explanations needed
- Forgets everything
- Same approach for all projects

**RIGHT SIDE: Claude OS** ✅
- Sessions build on knowledge
- Automatic context
- YOUR solutions
- Instant understanding
- Remembers forever
- Expert on YOUR project

Show arrows pointing to benefits on the right side

Style: Modern comparison, green checkmarks vs red X's, split screen

---

## Diagram 6: Data Flow - From Code to Claude

Create an animated-style flow diagram:

```
Your Codebase
     ↓
[Git Commit]
     ↓
Git Hook Triggered
     ↓
Tree-Sitter Parsing (Structural)
     ↓
Symbol Extraction (38,406 symbols in 3s)
     ↓
SQLite Storage (JSON + Vectors)
     ↓
MCP Server Exposes
     ↓
Claude Code Queries
     ↓
You Get Context-Aware Responses
```

Style: Modern data pipeline, with timing annotations

---

## Diagram 7: Team Collaboration Flow

Create a team workflow diagram:

```
Developer 1 (Setup)
     ↓
./install.sh
     ↓
Templates Installed
     ↓
/claude-os-init on Project A
     ↓
Knowledge Base Created
     ↓
CLAUDE.md → Git (shared)
     ↓
Developer 2 Clones Repo
     ↓
./install.sh (gets all templates)
     ↓
/claude-os-init (gets shared context)
     ↓
Both Developers: Same AI Knowledge!
```

Style: Team collaboration, multiple users, shared knowledge flow

---

## Color Palette Suggestion:

- **Primary:** Electric Blue (#00D9FF)
- **Secondary:** Purple (#8B5CF6)
- **Accent:** Teal (#14B8A6)
- **Background:** Dark Navy (#0F172A)
- **Success:** Green (#10B981)
- **Warning:** Amber (#F59E0B)
- **Text:** White/Light Gray

---

## Output Format:

Please create each diagram as a separate high-resolution image suitable for:
1. README.md display
2. Documentation
3. Presentation slides
4. Social media sharing

Make them **visually stunning** and **easy to understand at a glance**. Use modern design trends like:
- Glassmorphism effects
- Subtle gradients
- Clear typography
- Icons where appropriate
- Consistent spacing and alignment

Thanks! 🎨
