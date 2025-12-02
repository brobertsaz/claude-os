---
name: remember-this
description: "Capture conversation context, insights, or discoveries and save them as markdown documents to Claude OS knowledge bases. Use when you want to save important information like 'remember this:', design decisions, troubleshooting solutions, or architectural patterns for future reference."
allowed-tools: Read, Write, Bash, Task
---

# Remember This Skill

## Purpose

Automatically capture important context from our conversations and save it to Claude OS knowledge bases so I can reference it in future sessions. Perfect for:

- Design decisions and rationale
- Troubleshooting solutions discovered
- Architectural patterns you've explained
- Edge cases encountered
- Integration patterns
- Best practices you've shared
- Complex system behavior

## How to Use

Simply say one of:
- **"Remember this: [information]"**
- **"Save this: [information]"**
- **"Document this: [information]"**
- **"Remember: [explanation]"**

## What Happens

When you invoke this skill:

1. **I extract the key information** from your statement
2. **I create a formatted markdown document** with proper structure
3. **I upload it to Claude OS** (default: {project}-project_memories KB)
4. **I confirm what was saved** and where
5. **I reference it in future conversations** automatically

## Document Structure

```markdown
# [Topic Title]

**Date Saved**: [Auto-generated]
**Context**: [Where this came from]
**Category**: [Architecture/Integration/Pattern/Troubleshooting/etc]

[Main content in well-structured format]

## Key Takeaways
- Bullet point 1
- Bullet point 2

## Related Topics
- Links to related documentation
```

## Examples

### Example 1: Remember a Pattern
```
User: "Remember this: When creating a new service, always follow this structure:
initialize with domain objects and params, have a single perform method that returns
model on success or error string on failure, use private methods for complex logic."

→ Saves to: "Service Pattern Guide.md" in project KB
→ I reference it: "Like the pattern you documented, services should..."
```

### Example 2: Save a Solution
```
User: "Save this: Fixed the N+1 query problem in AppointmentsScheduler by adding
.includes(:block_settings, :children) to prevent multiple DB queries."

→ Saves to: "Query Optimization Solutions.md"
→ I use it: "We can apply the same .includes strategy here..."
```

### Example 3: Document an Architecture Decision
```
User: "Remember: Block model uses acts_as_tree for hierarchical structure because
we need semantic role-based organization of child blocks, not just a flat list."

→ Saves to: "Blocks System Decisions.md"
→ I reference it: "Following the hierarchical pattern you documented..."
```

## Customization

You can specify:

- **KB Name**: "Remember this [content] - save to my-project-memories"
- **Document Title**: "Remember this [content] - as 'My Custom Title'"
- **Tags/Category**: "Remember this [content] - category: Integration"

## Benefits

✅ **Build institutional knowledge** over time
✅ **I remember context** across sessions
✅ **Reduces repetition** of explanations
✅ **Creates searchable archive** of decisions
✅ **Helps with onboarding** (your knowledge is documented)
✅ **Perfect for discoveries** made during debugging

---

**Pro Tip**: Use this skill liberally! Every insight you share gets permanently indexed and makes me a better developer for your project.
