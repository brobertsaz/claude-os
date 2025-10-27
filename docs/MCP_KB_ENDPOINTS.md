# KB-Specific MCP Endpoints

## Overview

Claude OS now supports **KB-specific MCP endpoints** that allow you to connect individual knowledge bases to Claude Desktop, rather than exposing all KBs through a single global endpoint.

## Architecture

### Before (Global Endpoint Only)

```
http://localhost:8051/mcp
├── search_knowledge_base (requires kb_name parameter)
├── list_knowledge_bases
├── create_knowledge_base
├── get_kb_stats (requires kb_name parameter)
└── ... 8 more tools
```

**Problem:** All KBs exposed through one endpoint, requiring `kb_name` parameter for every query.

### After (KB-Specific + Global)

```
http://localhost:8051/mcp (Global - all KBs)
├── search_knowledge_base (requires kb_name parameter)
├── list_knowledge_bases
├── create_knowledge_base
└── ... 12 tools total

http://localhost:8051/mcp/kb/my-kb (KB-specific, using slug)
├── search (auto-scoped to 'my-kb')
├── get_stats (auto-scoped to 'my-kb')
└── list_documents (auto-scoped to 'my-kb')

http://localhost:8051/mcp/kb/pistn-agent-os (KB-specific, using slug)
├── search (auto-scoped to 'Pistn Agent OS')
├── get_stats (auto-scoped to 'Pistn Agent OS')
└── list_documents (auto-scoped to 'Pistn Agent OS')
```

**Benefits:**
- ✅ Clean separation between knowledge bases
- ✅ No need to specify `kb_name` parameter
- ✅ Prevents accidental cross-KB queries
- ✅ Better organization in Claude Desktop
- ✅ URL-friendly slugs (no spaces, special characters, or URL encoding)

## Implementation Details

### Backend Changes (`mcp_server/server.py`)

1. **New KB-specific endpoint using slugs:**

   ```python
   @app.post("/mcp/kb/{kb_slug}")
   async def mcp_kb_endpoint(kb_slug: str, request: Request):
       """KB-specific MCP endpoint - only exposes tools for this KB."""
       # Get KB name from slug
       pg_manager = get_pg_manager()
       kb_name = pg_manager.get_kb_by_slug(kb_slug)

       if not kb_name:
           return JSONResponse({...}, status_code=404)

       return await handle_mcp_request(request, kb_filter=kb_name)
   ```

   Slugs are URL-friendly identifiers generated from KB names:
   - "Pistn Agent OS" → "pistn-agent-os"
   - "My Code Base" → "my-code-base"
   - "Test_KB 123!" → "test-kb-123"

2. **Updated MCP request handler:**
   ```python
   async def handle_mcp_request(request: Request, kb_filter: Optional[str] = None):
       """
       Handle MCP JSON-RPC requests.

       Args:
           kb_filter: If provided, only expose tools for this specific KB
       """
   ```

3. **KB-scoped tool filtering:**
   - When `kb_filter` is set, only 3 tools are exposed: `search`, `get_stats`, `list_documents`
   - Tool calls automatically inject the `kb_name` parameter
   - Server name includes KB name: `claude-os-{kb_name}`

### Frontend Changes

#### `KBManagement.tsx`

Added **MCP Integration** section showing:
- KB-specific endpoint URL with copy button
- Claude Desktop CLI command
- Helpful notes about the endpoint

```tsx
const mcpEndpoint = `http://localhost:8051/mcp/kb/${encodeURIComponent(kbName)}`;
const mcpCommand = `claude mcp add ${kbName} ${mcpEndpoint}`;
```

#### `HelpDocs.tsx`

Updated MCP Integration documentation to explain:
- KB-specific endpoints (recommended)
- Global endpoint (all KBs)
- How to find KB-specific endpoints in the UI
- Examples for both approaches

### Documentation Updates

#### `README.md`

Completely rewrote the **MCP Integration** section to:
- Explain both endpoint types
- Recommend KB-specific endpoints
- Show clear examples
- List available tools for each type
- Guide users to find endpoints in the UI

## Usage Examples

### Adding a KB-Specific Endpoint to Claude Desktop

```bash
# Add the "my-docs" knowledge base
claude mcp add my-docs http://localhost:8051/mcp/kb/my-docs

# Add the "my-code" knowledge base
claude mcp add my-code http://localhost:8051/mcp/kb/my-code
```

### Using KB-Specific Tools in Claude

Once added, Claude can use the KB-specific tools:

```
User: Search for authentication in my-docs
Claude: [Uses the 'search' tool from my-docs endpoint]

User: What are the stats for my-code?
Claude: [Uses the 'get_stats' tool from my-code endpoint]
```

No need to specify `kb_name` - it's automatically scoped!

### Manual Configuration

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "my-docs": {
      "url": "http://localhost:8051/mcp/kb/my-docs"
    },
    "my-code": {
      "url": "http://localhost:8051/mcp/kb/my-code"
    }
  }
}
```

## Testing

Tested with existing KBs:
- ✅ Global endpoint works (12 tools exposed)
- ✅ KB-specific endpoints work (3 tools exposed per KB)
- ✅ URL encoding handles KB names with spaces
- ✅ 404 returned for non-existent KBs
- ✅ Server name includes KB name in initialize response

## Migration Guide

### For Existing Users

If you're already using the global endpoint:

**Option 1: Keep using global endpoint**
- No changes needed
- Continue using `search_knowledge_base` with `kb_name` parameter

**Option 2: Switch to KB-specific endpoints**
1. Remove the global endpoint from Claude Desktop
2. Add individual KB endpoints using the UI
3. Enjoy cleaner, scoped queries

### For New Users

**Recommended:** Use KB-specific endpoints from the start
1. Create a knowledge base in the UI
2. Go to KB Management tab
3. Copy the MCP endpoint URL from the "MCP Integration" section
4. Add to Claude Desktop using the provided command

## Future Enhancements

Potential improvements:
- [ ] Auto-discovery endpoint that lists all KB-specific endpoints
- [ ] WebSocket support for real-time updates
- [ ] Per-KB authentication/API keys
- [ ] Rate limiting per KB
- [ ] Usage analytics per KB endpoint

