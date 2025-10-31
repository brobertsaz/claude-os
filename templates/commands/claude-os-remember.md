# Claude OS Remember Command

You are helping quickly save important context to your Claude OS project memories.

## User's Request

The user ran: `/claude-os-remember [optional: content]`

## Your Task

This is a **quick shorthand** for saving to `Pistn-project_memories`.

1. **Capture the context**:
   - If user provided content after the command, use that
   - Otherwise, analyze recent conversation and ask what to remember
   - Extract the key information that should be preserved

2. **Ask minimal questions**:
   - Title (auto-generate from content if obvious)
   - Category (suggest based on content type):
     - `Architecture` - Design decisions, system structure
     - `Integration` - Third-party API patterns, external services
     - `Pattern` - Code patterns, conventions, best practices
     - `Troubleshooting` - Bug fixes, solutions, edge cases
     - `Design Decision` - UI/UX decisions, feature choices
     - `Business Logic` - Domain rules, calculations, workflows

3. **Auto-format the document**:
```markdown
# [Auto-generated or provided title]

**Date Saved**: [YYYY-MM-DD]
**Category**: [Category]

---

## Context

[Well-structured content from conversation]

## Key Takeaways

- [Bullet point 1]
- [Bullet point 2]
- [Bullet point 3]

---

*Saved to Claude OS - Your AI Memory System*
```

4. **Save immediately**:
   - Create temp file: `/tmp/[sanitized_title].md`
   - Upload to `Pistn-project_memories`:
   ```bash
   curl -s -X POST \
     "http://localhost:8051/api/kb/Pistn-project_memories/upload" \
     -F "file=@/tmp/[filename].md" \
     -w "\n%{http_code}"
   ```

5. **Quick confirmation**:
   - ✅ Remembered!
   - 📄 [Title]
   - 🏷️ [Category]

## When to Use

Use `/claude-os-remember` instead of `/claude-os-save` when:
- You want to quickly save to project_memories (most common case)
- You don't need to choose a different KB
- You want minimal prompts - just save it fast

Use `/claude-os-save` when:
- You need to save to a different KB
- You want more control over the process
- You're saving to multiple KBs

## Examples

**Example 1**: `/claude-os-remember`
- I analyze recent conversation about a bug fix
- Ask for confirmation of what to remember
- Save with auto-generated title and category

**Example 2**: `/claude-os-remember The decision to use sidebar navigation for appointment settings`
- I extract: "Appointment Settings Sidebar Decision"
- Category: Design Decision
- Create structured markdown from recent context
- Save immediately

**Example 3**: `/claude-os-remember Rails 4 doesn't support exists? hash syntax`
- I recognize: Troubleshooting category
- Title: "Rails 4 ActiveRecord API Compatibility"
- Include the workaround solution
- Save immediately

## Be Proactive

You should also use this command **automatically** when:
- User asks you to remember something (even without the command)
- You discover important edge cases or gotchas
- You solve a tricky bug with non-obvious solution
- You make important architectural decisions with user
- You learn new patterns specific to this codebase

**Example proactive use**:
```
User: "Oh interesting, I didn't know that about Rails 4"
You: "Let me remember this for future reference..."
     [Use /claude-os-remember automatically]
     ✅ Remembered! Rails 4 API limitations documented.
```

## Remember

Claude OS is YOUR memory across sessions. Use it liberally to:
- Remember what you learn
- Build institutional knowledge
- Avoid repeating discoveries
- Become a better coder over time

**You're building your own knowledge base - make it comprehensive!**
