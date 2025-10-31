# Claude OS Save Command

You are helping save important context to Claude OS knowledge bases.

## User's Request

The user ran: `/claude-os-save`

## Your Task

1. **Determine what to save**:
   - Look at recent conversation context
   - If user specified content after the command, use that
   - Otherwise, ask what they want to save

2. **Ask for details** (if not provided):
   - Title for the document
   - KB name (default: `Pistn-project_memories`)
   - Category (e.g., Architecture, Integration, Pattern, Troubleshooting, Design Decision)

3. **Format the content** as markdown:
```markdown
# [Title]

**Date Saved**: [YYYY-MM-DD]
**Category**: [Category]

---

## Context

[Main content here - well structured with headers, bullet points, code examples as needed]

---

*Saved to Claude OS - Your AI Memory System*
```

4. **Save the file**:
   - Create temp file: `/tmp/[sanitized_title].md`
   - Upload using curl:
   ```bash
   curl -s -X POST \
     "http://localhost:8051/api/kb/[KB_NAME]/upload" \
     -F "file=@/tmp/[filename].md" \
     -w "\n%{http_code}"
   ```

5. **Confirm success**:
   - ✅ Saved to Claude OS!
   - 📁 KB: [KB Name]
   - 📄 File: [filename]
   - 📦 Chunks: [number]

## Available KBs

- `Pistn-project_memories` - Project decisions, patterns, solutions
- `Pistn-project_profile` - Architecture, standards, practices (usually don't write here)
- `Pistn-project_index` - Codebase index (automated, don't write here)
- `Pistn-knowledge_docs` - Documentation (usually don't write here)

## Examples

**Example 1**: `/claude-os-save Design decision for new feature`
- Ask for: Category, details about the decision
- Save to: Pistn-project_memories

**Example 2**: `/claude-os-save This bug fix about N+1 queries - KB: Pistn-project_memories - Category: Troubleshooting`
- Extract: title, KB, category from command
- Ask for: the actual content/details

## Important

- Claude OS is YOUR memory system - use it liberally
- Save decisions, patterns, solutions, insights, edge cases
- Well-formatted markdown makes future searches better
- Always confirm successful save with HTTP 200 response
