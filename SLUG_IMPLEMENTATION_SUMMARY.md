# KB Slug Implementation Summary

## Overview

Successfully implemented **URL-friendly slugs** for knowledge bases to create clean, readable MCP endpoint URLs.

## Problem Solved

**Before:**
```
http://localhost:8051/mcp/kb/Pistn%20Agent%20OS  ❌ Ugly URL encoding
```

**After:**
```
http://localhost:8051/mcp/kb/pistn-agent-os  ✅ Clean, readable slug
```

## Changes Made

### 1. Database Schema

**Added `slug` column to `knowledge_bases` table:**

```sql
ALTER TABLE knowledge_bases ADD COLUMN slug VARCHAR(255) UNIQUE NOT NULL;
CREATE INDEX idx_kb_slug ON knowledge_bases(slug);
```

**Slug generation rules:**
- Lowercase conversion
- Spaces/underscores → hyphens
- Remove special characters
- Remove consecutive hyphens
- Trim leading/trailing hyphens

**Examples:**
- "Pistn Agent OS" → "pistn-agent-os"
- "My Code Base!" → "my-code-base"
- "Test_KB 123" → "test-kb-123"

### 2. Backend (`app/core/pg_manager.py`)

**Added slug generation function:**
```python
def generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from a KB name."""
    slug = name.lower()
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug
```

**Updated methods:**
- `create_collection()` - Generates and stores slug on KB creation
- `list_collections()` - Returns slug with KB metadata
- `get_kb_by_slug()` - New method to lookup KB name by slug
- `slug_exists()` - New method to check slug uniqueness

### 3. MCP Server (`mcp_server/server.py`)

**Updated endpoint to use slugs:**
```python
@app.post("/mcp/kb/{kb_slug}")
async def mcp_kb_endpoint(kb_slug: str, request: Request):
    """KB-specific MCP endpoint - only exposes tools for this KB."""
    pg_manager = get_pg_manager()
    kb_name = pg_manager.get_kb_by_slug(kb_slug)
    
    if not kb_name:
        return JSONResponse({...}, status_code=404)
    
    return await handle_mcp_request(request, kb_filter=kb_name)
```

**Benefits:**
- No URL encoding needed
- Clean, readable URLs
- Slug-to-name lookup in database
- 404 for invalid slugs

### 4. Frontend

**Updated `KBManagement.tsx`:**
```tsx
const slug = kbSlug || kbName.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
const mcpEndpoint = `http://localhost:8051/mcp/kb/${slug}`;
const mcpCommand = `claude mcp add ${slug} ${mcpEndpoint}`;
```

**Updated `MainApp.tsx`:**
```tsx
<KBManagement
  kbName={selectedKB}
  kbSlug={kbs.find(kb => kb.name === selectedKB)?.slug}
  kbType={kbs.find(kb => kb.name === selectedKB)?.metadata?.kb_type}
/>
```

**Updated API types (`lib/api.ts`):**
```tsx
export interface KnowledgeBase {
  id: number;
  name: string;
  slug: string;  // ← New field
  kb_type: string;
  description: string;
  created_at: string;
  metadata?: any;
}
```

### 5. Migration

**Created migration script (`migrations/add_slug_column.sql`):**
- Adds slug column if not exists
- Generates slugs for existing KBs
- Makes slug unique and not null
- Creates index for fast lookups

**Migration executed successfully:**
```
UPDATE 2
ALTER TABLE
ALTER TABLE
CREATE INDEX
      name      |      slug      
----------------+----------------
 Pistn          | pistn
 Pistn Agent OS | pistn-agent-os
```

### 6. Documentation

**Updated files:**
- `README.md` - Explained slug-based endpoints
- `HelpDocs.tsx` - Added slug examples
- `MCP_KB_ENDPOINTS.md` - Documented slug implementation

## Testing Results

**Test 1: Pistn KB (simple slug)**
```bash
curl -X POST http://localhost:8051/mcp/kb/pistn \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'

✅ Response: {"serverInfo":{"name":"code-forge-Pistn"}}
```

**Test 2: Pistn Agent OS (slug with hyphen)**
```bash
curl -X POST http://localhost:8051/mcp/kb/pistn-agent-os \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

✅ Response: 3 tools (search, get_stats, list_documents)
```

**Test 3: Invalid slug**
```bash
curl -X POST http://localhost:8051/mcp/kb/nonexistent \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'

✅ Response: 404 "Knowledge base with slug 'nonexistent' not found"
```

## Usage Examples

### Adding to Claude Desktop

**Using slug (recommended):**
```bash
claude mcp add pistn http://localhost:8051/mcp/kb/pistn
claude mcp add pistn-agent-os http://localhost:8051/mcp/kb/pistn-agent-os
```

**Manual configuration:**
```json
{
  "mcpServers": {
    "pistn": {
      "url": "http://localhost:8051/mcp/kb/pistn"
    },
    "pistn-agent-os": {
      "url": "http://localhost:8051/mcp/kb/pistn-agent-os"
    }
  }
}
```

### Finding Slugs in UI

1. Open Code-Forge UI at `http://localhost:5173`
2. Select a knowledge base
3. Go to **KB Management** tab
4. Look for the **MCP Integration** section
5. The slug is shown in the endpoint URL

## Benefits

✅ **Clean URLs** - No URL encoding, spaces, or special characters
✅ **Readable** - Easy to type and remember
✅ **Unique** - Database constraint ensures no duplicates
✅ **Indexed** - Fast slug lookups
✅ **Backward Compatible** - Fallback for old KBs without slugs
✅ **User-Friendly** - Displayed prominently in UI

## Future Enhancements

Potential improvements:
- [ ] Custom slug editing in UI
- [ ] Slug validation on KB creation
- [ ] Slug history/aliases for renamed KBs
- [ ] Slug suggestions based on KB name
- [ ] Bulk slug regeneration tool

