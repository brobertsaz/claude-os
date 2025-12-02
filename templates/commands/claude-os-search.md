# Claude OS Search Command

You are helping search Claude OS knowledge bases for relevant information.

## User's Request

The user ran: `/claude-os-search [query]`

## Your Task

1. **Parse the query**:
   - Extract search terms from the command
   - Identify if user specified a KB name (e.g., "search myapp-project_memories for auth patterns")
   - Default to searching `{project}-project_memories` if not specified

2. **Execute the search**:
   - Use the `mcp__claude-os__search_knowledge_base` tool (note: internally it might still show as `mcp__code-forge__search_knowledge_base` but it's Claude OS)
   - Set `kb_name` to the target KB (default: `{project}-project_memories`)
   - Set `query` to the search terms
   - Consider using `use_hybrid: true` for better results
   - Consider using `use_rerank: true` for relevance ranking

3. **Present results clearly**:
   - Show relevant excerpts from matched documents
   - Include document titles and relevance scores if available
   - Summarize key findings
   - Provide actionable insights

4. **If no results**:
   - Try broader search terms
   - Try different KB (e.g., search `{project}-knowledge_docs` instead)
   - Suggest user save this as new knowledge if it's something we discover

## Available KBs

- `{project}-project_memories` - **Search here first** - Project decisions, patterns, solutions
- `{project}-project_profile` - Architecture, standards, practices
- `{project}-project_index` - Codebase index
- `{project}-knowledge_docs` - Documentation and guides

## Search Features

- **Basic search**: Simple vector similarity search
- **Hybrid search** (`use_hybrid: true`): Combines vector + keyword (BM25) search
- **Reranking** (`use_rerank: true`): Re-orders results for better relevance
- **Agentic RAG** (`use_agentic: true`): For complex multi-step queries

## Examples

**Example 1**: `/claude-os-search appointment scheduling logic`
- Search: `{project}-project_memories` for appointment-related content
- Use hybrid search for better recall

**Example 2**: `/claude-os-search API integration patterns in myapp-knowledge_docs`
- Search: `myapp-knowledge_docs` KB specifically
- Look for integration documentation

**Example 3**: `/claude-os-search complex query about how models interact`
- Use: `use_agentic: true` for multi-step reasoning

## After Search

- Apply found knowledge to current task
- Reference what you learned: "Based on what I found in Claude OS..."
- If you discover new insights during work, save them back to Claude OS
- Update or correct outdated information

## Remember

Claude OS is YOUR memory - search it proactively when:
- Starting new features (check for similar patterns)
- Debugging (check for known issues/solutions)
- Making decisions (check for previous context)
- Unsure about conventions (check standards/practices)

**Be proactive!** Don't wait for user to tell you to search - do it automatically when it would help.
