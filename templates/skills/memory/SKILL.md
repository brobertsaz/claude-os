---
name: memory
description: "Save and recall important information from previous sessions. Use when you want to remember technical insights, decisions, project context, or discoveries. Simply say 'remember:' or 'save to memory:' and I'll store it persistently and automatically reference it in future conversations."
allowed-tools: Read, Write, Bash
---

# Memory Skill

## Purpose

Create a persistent memory across all Claude Code sessions without needing to search through knowledge bases. Perfect for:

- **Yesterday's work**: "What did we work on yesterday?"
- **Technical insights**: "Remember: Block rendering works like X"
- **Project context**: "Store: We're migrating Block 122 to Rails"
- **Debugging solutions**: "Save: Fixed N+1 query by adding .includes(:blocks)"
- **Architectural decisions**: "Remember: Always use Service classes for business logic"
- **Quick facts**: "Block 122 is 43KB, 1,150 lines"

## How to Use

Simply say one of:
- **"Remember: [information]"**
- **"Save to memory: [information]"**
- **"Memory: [information]"**
- **"Store this: [information]"**

Or ask me to recall:
- **"What did we work on yesterday?"**
- **"Remind me about the Block deprecation"**
- **"Search my memory for 'Block 122'"**
- **"Show me my recent memories"**

## What Happens

When you invoke this skill:

1. **I extract key information** from your statement
2. **I store it in the Memory MCP** with tags and timestamp
3. **I confirm what was saved** and provide instant recall
4. **In future sessions**, I automatically reference this memory when relevant

## Memory Structure

Each memory includes:
- **Title**: Quick reference name
- **Content**: Full details
- **Tags**: Keywords for searching (e.g., "Block122", "migration", "appointment-form")
- **Created**: Timestamp
- **Updated**: Last modification time

## Examples

### Example 1: Save Technical Insight
```
You: "Remember: Block 122 is 43KB and the most complex block in PISTN.
      It has a 4-step wizard, 600+ lines of inline JavaScript, and handles
      phone verification, vehicle lookup, and service selection."

→ I save to memory with tags: ["Block122", "Architecture", "Complexity"]
→ I confirm: "✓ Saved to memory: Block 122 complexity analysis"
```

### Example 2: Project Progress
```
You: "Save to memory: We completed Block deprecation research.
      Created BLOCKS_DEPRECATION_STRATEGY.md and case study for Block 122.
      Next: Build feature flag infrastructure."

→ I save with tags: ["BlockDeprecation", "Progress", "Roadmap"]
→ In future session: "Based on our memory, we completed..."
```

### Example 3: Recall with Context
```
You: "What was special about Block 122?"

→ I search memory automatically
→ "From our memory: Block 122 is a 4-step wizard form with 43KB content..."
```

## Key Benefits

✅ **Instant Recall** - No searching through KB or scrolling history
✅ **Automatic Context** - I know what we worked on without asking
✅ **Persistent** - Memories survive session restarts
✅ **Searchable** - Find memories by title, content, or tags
✅ **Organized** - See recent work, all memories, or search specific topics
✅ **Natural** - Just say "remember" and I handle the rest

## Memory Operations

### Add Memory
```
remember: [Your information here]
```

### Search Memory
```
search memory for: [keyword or phrase]
```

### Show Recent Memories
```
show my recent memories (from last 24 hours)
show my memories from yesterday
```

### Show All Memories
```
list all my memories
```

### Update Memory
```
update memory: [title or keyword] with [new information]
```

### Clear Memory (if needed)
```
forget: [memory title or keyword]
```

## Technical Details

**Storage**: ~/.claude/mcp-servers/memory/data/memories.json
**Searchable**: Full-text search on titles, content, and tags
**Timestamped**: All memories include creation and update times
**Persistent**: Survives across all sessions and devices

---

**Pro Tip**: Use this liberally! Every insight, decision, and discovery you share builds your persistent context. I remember everything you tell me to remember, so you don't have to repeat yourself.

