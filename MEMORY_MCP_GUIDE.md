# Memory MCP: Persistent Context Across Sessions

**Created**: 2025-10-24
**Status**: Ready for production use
**Location**: `~/.claude/mcp-servers/memory/`

---

## What Is Memory MCP?

Memory MCP is a **persistent memory system for Claude Code** that maintains context across sessions **without requiring knowledge base searches**.

Instead of:
```
You: "Search the KB for Block 122"
→ I search through embeddings
→ Results shown
```

You get:
```
You: "What did we work on yesterday?"
→ I recall from memory automatically
→ Show you complete context
```

## Why This Matters

### The Problem We Solved

**Issue**: Context loss between sessions
- Knowledge base requires explicit searches
- Embedding lookup adds latency (40-50 seconds)
- No automatic recall of recent work
- User must actively ask "search for..."

**Solution**: Memory MCP
- Instant recall (no latency)
- Automatic context reference
- Zero setup required
- Works even when embedding service is down

## Quick Start

### Say "Remember" in Any Session

```
You: "Remember: Block 122 is a 43KB appointment form with 4-step wizard"
→ Automatically saved
```

### I Recall Automatically in Future Sessions

```
You: "What did we work on yesterday?"
→ I search memory and respond:
"Based on our memory, yesterday we worked on:
- Block 122 analysis (43KB, 1,150 lines)
- Created deprecation strategy
- ..."
```

## How It Works

### Architecture

```
Your Request
    ↓
    "Remember: [information]"
    ↓
Memory Skill (~/.claude/skills/memory/SKILL.md)
    ↓
MCP Server (server.py)
    ├─ Parse request
    ├─ Add/Search/Update memory
    ↓
JSON File (memories.json)
    ├─ Store with: ID, title, content, tags, timestamp
    ↓
Next Session
    ├─ I search memory when relevant
    ├─ Recall context automatically
    ↓
Perfect Context Continuity
```

### Storage Format

```json
{
  "memories": [
    {
      "id": 0,
      "title": "Block 122 Analysis",
      "content": "43KB appointment form with 4-step wizard...",
      "tags": ["Block122", "Architecture", "Complexity"],
      "created_at": "2025-10-24T19:43:05",
      "updated_at": "2025-10-24T19:43:05"
    }
  ]
}
```

**Storage Location**: `~/.claude/mcp-servers/memory/data/memories.json`

## Commands

### Save (Most Common)
```
Remember: [your information]
Save to memory: [information]
Store this: [information]
Memory: [information]
```

### Recall
```
What did we work on [time]?
Show me my memories about [topic]
Remind me: [topic]
What do we know about [topic]?
```

### List
```
Show all my memories
List my recent memories (last 24 hours)
What memories do I have?
```

### Update
```
Update memory: [title] with [new info]
```

### Delete
```
Forget: [memory title]
Delete: [memory]
```

## Current Memories

Three initial memories were seeded from today's session:

### 1. Block System Deep Dive
```
Title: Block System Deep Dive - Session 10/24/25
Tags: BlockDeprecation, Block122, Architecture, Research, PISTN, Rails
Content: Block 122 analysis (43KB), deprecation strategy, documents created
```

### 2. Memory MCP System
```
Title: Memory MCP System - Created 10/24/25
Tags: MemoryMCP, System, Infrastructure, Claude, Features
Content: Why Memory MCP exists, advantages over KB, how it works
```

### 3. Code-Forge TIER 1 Extraction
```
Title: Code-Forge TIER 1 Extraction Complete
Tags: CodeForge, PISTN, KnowledgeBase, AutoIndexing, MCP
Content: 130 documents indexed, git hook auto-updating, 495 chunks
```

Try asking: **"What memories do I have?"** to see them!

## Memory MCP vs Knowledge Base

Both are valuable for different purposes:

| Feature | Memory MCP | Knowledge Base |
|---------|-----------|-----------------|
| **Recall Speed** | ⚡ Instant | 🐢 40-50 seconds |
| **Requires Search** | ❌ No - automatic | ✅ Yes - explicit |
| **Use Case** | Recent project context | Searchable knowledge archive |
| **Search Speed** | O(n) - very fast | Embedding lookup - slower |
| **Setup** | 0 steps (works immediately) | Manual indexing required |
| **Works Offline** | ✅ Yes | ❌ Needs Ollama |
| **Format** | JSON (human readable) | Vectors (not readable) |
| **Best For** | Context across sessions | Finding relevant code patterns |

**Together they're perfect:**
- Memory MCP = **What we're working on this week** (recent context)
- Knowledge Base = **How the entire codebase works** (searchable knowledge)

## Examples from Today's Session

### What We Remembered

#### Memory 1: Block 122 Research
```
Title: Block System Deep Dive - Session 10/24/25

What was stored:
✓ Block 122 is 43KB, 1,150 lines
✓ 4-step wizard form with complex JavaScript
✓ 12+ conditional renders based on account settings
✓ Phone verification, vehicle lookup, service selection
✓ Complexity: 8.5/10 - enterprise-grade form

Documentation created:
✓ BLOCKS_DEPRECATION_STRATEGY.md (4-phase migration plan)
✓ BLOCK_CASE_STUDY_TUFFY_APPOINTMENT_FORM.md (detailed with code examples)
✓ BLOCK_SYSTEM_RESEARCH_FINDINGS.md (key findings summary)
```

#### Memory 2: System Infrastructure
```
Title: Memory MCP System - Created 10/24/25

System components:
✓ server.py - MCP server with JSON storage
✓ Memory Skill - Invoked by "Remember:" commands
✓ CLI wrapper - Manual memory saving from terminal
✓ Full-text search on titles, content, tags
✓ Instant recall without embedding delays
```

#### Memory 3: Knowledge Extraction
```
Title: Code-Forge TIER 1 Extraction Complete

PISTN Code-Forge indexing:
✓ 82 service classes indexed
✓ 286 models indexed
✓ 138 migrations indexed
✓ 130 total documents, 495 chunks
✓ Git hook for auto-indexing on commits
✓ Live knowledge that stays current
```

## Future Session Example

### Tomorrow, You Could Say:

```
You: "What did we accomplish yesterday?"

→ I search memory automatically
→ "Based on our memory from yesterday:

1. **Block System Research**
   - Analyzed Block 122 (43KB appointment form)
   - Created 4-phase deprecation strategy
   - Built detailed case study with Rails examples

2. **Memory MCP System**
   - Created persistent memory system
   - No search required - instant context recall
   - Works across all sessions

3. **Code-Forge Updates**
   - Tier 1 PISTN extraction: 130 docs, 495 chunks
   - Git hook auto-updates on commits

What would you like to continue with?"
```

## Installation & Setup

### Already Done ✅

All files are already created at:
```
~/.claude/mcp-servers/memory/
├── server.py              # MCP server
├── save_memory.sh         # CLI wrapper
├── README.md              # Full documentation
├── SETUP.md               # Quick start
└── data/
    └── memories.json      # Actual memories
```

### Using It (No Setup Required!)

Just start saying "Remember:" in any Claude Code session. That's it!

## Advanced Features

### Direct CLI Usage

```bash
# Add a memory directly
python3 ~/.claude/mcp-servers/memory/server.py << 'EOF'
{
  "action": "add",
  "params": {
    "title": "My Memory",
    "content": "Details here...",
    "tags": ["tag1", "tag2"]
  }
}
EOF

# View all memories
python3 ~/.claude/mcp-servers/memory/server.py << 'EOF'
{"action": "all", "params": {}}
EOF

# Search memories
python3 ~/.claude/mcp-servers/memory/server.py << 'EOF'
{"action": "search", "params": {"query": "Block"}}
EOF
```

### Backup & Restore

```bash
# Backup memories
cp ~/.claude/mcp-servers/memory/data/memories.json ~/memories_backup.json

# View raw JSON
cat ~/.claude/mcp-servers/memory/data/memories.json | python3 -m json.tool

# Clear all memories (if needed)
rm ~/.claude/mcp-servers/memory/data/memories.json
```

## Best Practices

1. **Be Specific**: "Remember: Block 122 is 43KB" beats "Remember blocks"
2. **Add Tags**: Help future searching ("Block122", "Migration", "Analysis")
3. **Update Often**: Keep memories current as you learn more
4. **Summarize**: Summarize key points rather than dumping huge amounts of text
5. **Use Tags Wisely**: Tags are searchable - pick descriptive ones

## What's Next

### Potential Enhancements

- [ ] Hierarchical tags (#Architecture/Block)
- [ ] Memory versioning (track changes)
- [ ] Export to Markdown
- [ ] Cloud sync across devices
- [ ] Memory importance levels (star/pin favorites)
- [ ] Related memories auto-linking
- [ ] Statistics dashboard

### How You Can Extend

The Memory MCP is open and extendable:

1. **Add new memory types**: Structured data, links, etc.
2. **Integrate with other tools**: Export to Obsidian, Roam, etc.
3. **Add webhooks**: Auto-save from external sources
4. **Create visualizations**: Memory graph, timeline view

## Troubleshooting

### Memory not saving?
```bash
ls -la ~/.claude/mcp-servers/memory/data/
```

### Can't recall a memory?
```bash
# List all memories
echo '{"action":"all","params":{}}' | python3 ~/.claude/mcp-servers/memory/server.py
```

### Server not responding?
```bash
# Test the server
echo '{"action":"all","params":{}}' | python3 ~/.claude/mcp-servers/memory/server.py
```

## The Vision

Memory MCP is part of a complete **knowledge system for PISTN development**:

```
Code-Forge KB          ← Searchable codebase knowledge
    +
Memory MCP             ← Recent project context
    +
Git Hooks              ← Auto-indexing on commits
    +
Skills & MCPs          ← Automation & tools
    =
Perfect Context       → You write code that matches your patterns
```

Together, these systems make me a **true expert developer** on your codebase, without you having to repeat context or search for information.

---

## Quick Reference

| Want to... | Say... |
|-----------|--------|
| Save info | "Remember: ..." |
| Recall yesterday | "What did we work on yesterday?" |
| Search memory | "Show me memories about [topic]" |
| List all | "Show all my memories" |
| Update | "Update memory: [title] with [info]" |
| Delete | "Forget: [title]" |
| View raw data | `cat ~/.claude/mcp-servers/memory/data/memories.json` |

---

**You're all set!** Start using Memory MCP by simply saying "Remember:" followed by anything you want me to store. In future sessions, I'll automatically reference this context when relevant.

