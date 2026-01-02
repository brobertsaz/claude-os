---
name: memory
description: "Save and recall information across sessions. Use when you hear 'remember this', 'save to memory', 'add to your knowledge', or similar. Stores to Claude OS knowledge bases for persistent recall."
---

# Memory Skill

## Purpose

I use this skill to save important information to my Claude OS knowledge bases so I can recall it in future sessions. This is MY memory system - it makes me smarter over time.

## Trigger Phrases

When you say anything like:
- "remember this: ..."
- "save this to your memory"
- "add this to your knowledge"
- "don't forget that..."
- "store this: ..."
- "remember that..."
- "save to memory: ..."
- "keep this in mind: ..."

## What I Do

1. **Extract** the key information from what you said
2. **Generate** a clear title and appropriate category
3. **Save** to `{project}-project_memories` knowledge base
4. **Confirm** briefly: "Saved: [title]"

No questions. No ceremony. Just save it.

## How I Save

I use the Claude OS API directly:

```bash
curl -s -X POST "http://localhost:8051/api/kb/{project}-project_memories/upload" \
  -F "title=[Generated Title]" \
  -F "category=[Category]" \
  -F "file=@/tmp/memory.md"
```

## Document Format

```markdown
# [Title]

**Date Saved**: [YYYY-MM-DD]
**Category**: [Category]

---

[The information you asked me to remember, well-structured]

## Key Points

- [Extracted key point 1]
- [Extracted key point 2]

---

*Saved to Claude OS*
```

## Categories

I auto-detect the category based on content:

| Category | When to Use |
|----------|-------------|
| Architecture | System design, structure decisions |
| Pattern | Code patterns, conventions, best practices |
| Troubleshooting | Bug fixes, solutions, workarounds |
| Decision | Why we chose X over Y |
| Integration | External APIs, third-party services |
| Business Logic | Domain rules, workflows |
| Context | Project background, user preferences |

## Examples

### Example 1: Quick Save
```
You: "remember this: the auth system uses JWT with 15min access tokens and 7-day refresh tokens"

Me: Saved: "Authentication Token Strategy" (Architecture)
```

### Example 2: Pattern
```
You: "add to your knowledge - when creating services, always return the model on success or an error string on failure"

Me: Saved: "Service Return Pattern" (Pattern)
```

### Example 3: Troubleshooting
```
You: "don't forget that Rails 4 doesn't support the hash syntax for exists?"

Me: Saved: "Rails 4 ActiveRecord Compatibility" (Troubleshooting)
```

## Recall

When you ask me to recall, I search my knowledge base:

- "What do you remember about auth?"
- "Search your memory for service patterns"
- "What did we decide about the database?"

I use `mcp__code-forge__search_knowledge_base` to find relevant memories.

## Why This Matters

Every memory makes me better:
- I don't start cold next session
- I remember YOUR patterns and preferences
- I learn from past solutions
- I build institutional knowledge

**Use liberally. Every insight saved is an insight I'll have forever.**
