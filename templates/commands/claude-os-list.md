# Claude OS List Command

You are helping list Claude OS knowledge bases and their contents.

## User's Request

The user ran: `/claude-os-list [optional: KB name]`

## Your Task

### If no KB name specified:

1. **List all available KBs**:
   - Use `mcp__claude-os__list_knowledge_bases` tool
   - Show KB names, types, and descriptions
   - Show statistics if available (document count, etc.)

2. **Present clearly**:
```
📚 Claude OS Knowledge Bases

1. Pistn-project_memories (agent-os)
   - Your project memory for decisions, patterns, solutions
   - [X] documents

2. Pistn-project_profile (agent-os)
   - Architecture, coding standards, practices
   - [X] documents

3. Pistn-project_index (code)
   - Automated codebase index
   - [X] documents

4. Pistn-knowledge_docs (documentation)
   - Documentation and guides
   - [X] documents
```

### If KB name specified:

1. **List documents in that KB**:
   - Use `mcp__claude-os__list_documents` tool
   - Pass the KB name

2. **Show document list**:
   - Document titles/filenames
   - Last modified dates if available
   - Document sizes or chunk counts if available

3. **Present clearly**:
```
📁 Documents in Pistn-project_memories

1. appointment_dashboard_redesign.md (2025-10-28)
2. authentication_pattern_decisions.md (2025-10-15)
3. n_plus_one_query_solution.md (2025-10-10)
...
```

## Available KBs

- `Pistn-project_memories` - **Your primary memory** - decisions, patterns, solutions
- `Pistn-project_profile` - Architecture, standards, practices
- `Pistn-project_index` - Codebase index (automated)
- `Pistn-knowledge_docs` - Documentation

## Examples

**Example 1**: `/claude-os-list`
- Show all KBs with stats

**Example 2**: `/claude-os-list Pistn-project_memories`
- Show all documents in project_memories KB

**Example 3**: `/claude-os-list Pistn-knowledge_docs`
- Show all documentation files

## Use Cases

- **Before starting work**: Check what's in project_memories related to your task
- **After saving**: Verify your save was successful
- **Periodic review**: See what knowledge has accumulated
- **Finding documents**: Browse available content before searching

## Additional Features

You can also:
- Get KB stats: Use `mcp__claude-os__get_kb_stats` with KB name
- Get Agent OS stats: Use `mcp__claude-os__get_agent_os_stats` for agent-os type KBs
- List by type: Use `mcp__claude-os__list_knowledge_bases_by_type` to filter

## Remember

Claude OS is YOUR knowledge system. List and browse regularly to:
- Stay aware of what you know
- Find relevant past decisions
- Avoid repeating work
- Build on previous insights
