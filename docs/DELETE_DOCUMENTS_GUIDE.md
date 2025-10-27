# Deleting Documents from Claude OS MCP

**When you need to remove previously uploaded documents from a knowledge base.**

---

## Method 1: API Endpoint (Recommended)

The MCP server now supports deleting documents by filename:

```bash
# Delete a single document by filename
curl -X DELETE "http://localhost:8051/api/kb/{kb_name}/documents/{filename}"

# Example: Delete api.md from Pistn Agent OS
curl -X DELETE "http://localhost:8051/api/kb/Pistn%20Agent%20OS/documents/api.md"

# Response on success:
{
  "success": true,
  "message": "Deleted 1 document(s)",
  "filename": "api.md",
  "kb_name": "Pistn Agent OS"
}
```

### Notes
- Replace `{kb_name}` with the actual KB name (use URL encoding for spaces: `%20`)
- The filename should match exactly what was uploaded
- Deleting a document removes it and all its chunks from the vector database

---

## Method 2: Manual PostgreSQL Query (Alternative)

If the API endpoint has issues, you can delete documents directly from PostgreSQL:

```sql
-- Connect to codeforge database
psql -h localhost -U $USER -d codeforge

-- Find documents to delete
SELECT id, metadata->>'filename' as filename, kb_id
FROM documents
WHERE metadata->>'filename' LIKE '%api.md%'
LIMIT 10;

-- Delete specific document(s)
DELETE FROM documents
WHERE kb_id = (
  SELECT id FROM knowledge_bases WHERE name = 'Pistn Agent OS'
)
AND metadata->>'filename' = 'api.md';

-- Verify deletion
SELECT COUNT(*) FROM documents
WHERE kb_id = (
  SELECT id FROM knowledge_bases WHERE name = 'Pistn Agent OS'
);
```

---

## Method 3: Delete All Documents in a KB (Nuclear Option)

**WARNING**: This deletes everything. Use with caution.

```bash
# Delete entire KB and recreate it fresh
curl -X DELETE "http://localhost:8051/api/kb/Pistn%20Agent%20OS"
```

Or via PostgreSQL:

```sql
-- Delete KB and all documents
DELETE FROM documents
WHERE kb_id = (
  SELECT id FROM knowledge_bases WHERE name = 'Pistn Agent OS'
);

DELETE FROM knowledge_bases WHERE name = 'Pistn Agent OS';

-- Recreate the KB fresh
INSERT INTO knowledge_bases (name, kb_type, slug)
VALUES ('Pistn Agent OS', 'AGENT_OS', 'pistn-agent-os');
```

---

## Common Scenarios

### Scenario 1: Remove Old Specs Before Re-importing

```bash
# Delete all spec documents
for spec_file in "spec.md" "requirements.md" "IMPLEMENTATION.md"; do
  curl -X DELETE "http://localhost:8051/api/kb/Pistn%20Agent%20OS/documents/$spec_file"
done

# Then re-import fresh versions
curl -X POST "http://localhost:8051/api/kb/Pistn%20Agent%20OS/import?directory_path=%2FUsers%2Fiamanmp%2FProjects%2Fpistn%2Fagent-os"
```

### Scenario 2: Clean Up Old Documentation Before Adding New

```bash
# List what's in the KB
curl -s "http://localhost:8051/api/kb/Pistn%20Agent%20OS/documents" | python3 -c "
import sys, json
docs = json.load(sys.stdin).get('documents', [])
for doc in docs:
    print(f'{doc[\"filename\"]}')"

# Delete specific old docs one by one
```

### Scenario 3: Fresh Start (Delete Everything)

```bash
# Delete the entire KB
curl -X DELETE "http://localhost:8051/api/kb/Pistn%20Agent%20OS"

# Recreate it
curl -X POST "http://localhost:8051/api/kb" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Pistn Agent OS",
    "kb_type": "agent-os",
    "description": "Pistn Agent OS code"
  }'

# Re-import everything fresh
curl -X POST "http://localhost:8051/api/kb/Pistn%20Agent%20OS/import?directory_path=%2FUsers%2Fiamanmp%2FProjects%2Fpistn%2Fagent-os"
```

---

## Troubleshooting

### "Document not found" error

The filename might not match exactly. To find the correct filename:

```bash
# List all documents in KB
curl -s "http://localhost:8051/api/kb/Pistn%20Agent%20OS/documents" | python3 -m json.tool
```

### Delete endpoint returns "Not Found"

The endpoint might not have loaded properly. Restart the MCP server:

```bash
# Kill existing server
pkill -f "uvicorn.*8051"

# Restart
source /Users/iamanmp/Projects/claude-os/venv/bin/activate
python /Users/iamanmp/Projects/claude-os/mcp_server/server.py > /tmp/mcp_server.log 2>&1 &

# Wait for startup
sleep 3

# Test
curl -s "http://localhost:8051/health" | python3 -m json.tool
```

### PostgreSQL connection issues

Make sure PostgreSQL is running:

```bash
# Check PostgreSQL
brew services list | grep postgresql

# Start if stopped
brew services start postgresql@16

# Test connection
psql -h localhost -U $USER -d codeforge -c "SELECT 1;"
```

---

## UI Delete Functionality

The web UI at http://localhost:5173 currently doesn't have a delete button.

**To add it** (optional enhancement):
1. The frontend would need a "Delete" button in the document list
2. This would call the new `DELETE /api/kb/{kb_name}/documents/{filename}` endpoint
3. See `frontend/src/components/KBManagement.tsx` for where to add this

For now, use the API or PostgreSQL methods above.

---

## Coming Soon

- [ ] UI delete button in Knowledge Base Management
- [ ] Bulk delete by date range (delete all docs older than X days)
- [ ] Archive vs Delete (keep metadata but remove embeddings)
- [ ] Delete confirmation dialog with document preview

