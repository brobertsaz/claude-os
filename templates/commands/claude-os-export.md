# Claude OS Export Command

You are helping export Claude OS knowledge bases to a portable, standalone format.

## User's Request

The user ran: `/claude-os-export <project_name> [options]`

## Your Task

Export the specified project's knowledge bases to a portable SQLite database that can be used by external applications without requiring Claude OS to be running.

### Step 1: Parse Arguments

Extract from the command:
- `project_name` (required): The project to export
- `--kb <kb_name>`: Export specific KB only (optional, default: all KBs)
- `--output <path>`: Output directory (optional, default: `./exports`)
- `--format <format>`: Export format (optional, default: `sqlite`)
- `--no-embeddings`: Exclude vector embeddings (optional, default: false)

### Step 2: Validate Project

1. Check if project exists using `mcp__claude-os__list_knowledge_bases`
2. Find all KBs matching the project name pattern (e.g., `dealer_123-*`)
3. If `--kb` specified, verify that specific KB exists
4. Confirm with user which KBs will be exported

### Step 3: Execute Export

Call the knowledge exporter:

```python
from app.core.knowledge_exporter import KnowledgeExporter

exporter = KnowledgeExporter()
result = exporter.export_project(
    project_name="<project_name>",
    kb_filter="<kb_name>" if specified else None,
    output_dir="<output_path>",
    include_embeddings=True,  # False if --no-embeddings
    format="sqlite"
)
```

### Step 4: Report Results

Present to user:
- Export file location
- File size
- Number of knowledge bases exported
- Number of documents included
- Embedding information (model, dimensions)
- Manifest file location

### Step 5: Provide Next Steps

Tell the user:
- Where the export file is located
- How to use it in external applications
- Reference the EXPORT_FORMAT_SPEC.md for integration details

## Export Format

The export creates:
1. **SQLite Database** (`<project>_export_<timestamp>.db`)
   - `knowledge_bases` table: KB metadata
   - `documents` table: Document content and metadata
   - `embeddings` table: Vector embeddings (if included)

2. **Manifest File** (`<project>_export_<timestamp>.manifest.json`)
   - Export metadata
   - KB statistics
   - Embedding model information
   - Schema version

## Examples

**Basic Export:**
```
/claude-os-export dealer_123
```
→ Exports all KBs for dealer_123 to `./exports/dealer_123_export_<timestamp>.db`

**Export Specific KB:**
```
/claude-os-export dealer_123 --kb dealer_123-knowledge_docs
```
→ Exports only the documentation KB

**Export to Custom Location:**
```
/claude-os-export dealer_123 --output /path/to/exports
```

**Export Without Embeddings (smaller file):**
```
/claude-os-export dealer_123 --no-embeddings
```
→ Exports documents only, no vector embeddings (much smaller file)

## Error Handling

If project doesn't exist:
- List available projects
- Suggest `/claude-os-list` to see all projects

If output directory doesn't exist:
- Create it automatically
- Confirm with user

If export fails:
- Show clear error message
- Suggest troubleshooting steps
- Offer to retry with different options

## Use Cases

This export is designed for:
- **Standalone Applications**: Apps that need knowledge without Claude OS running
- **Backup/Archive**: Snapshot of knowledge at a point in time
- **Migration**: Moving knowledge between environments
- **Integration**: Providing knowledge to external systems
- **Distribution**: Packaging knowledge with applications

## Consumer Applications

The exported database can be consumed by:
- AI chatbots (ServiceBot, customer support)
- API services (knowledge endpoints)
- CLI tools (search utilities)
- Analytics platforms
- Any application that needs read-only access to knowledge

## Important Notes

- **Read-Only Export**: The export is a snapshot, not synced
- **No Claude OS Dependency**: Exported data is self-contained
- **Standard Format**: Well-documented schema for easy integration
- **Versioned**: Format version included for compatibility
- **Portable**: Single SQLite file with all data

## After Export

The exported file is:
- ✅ Self-contained (no external dependencies)
- ✅ Portable (copy to any system)
- ✅ Efficient (SQLite with indices)
- ✅ Queryable (standard SQL + vector search if embeddings included)
- ✅ Documented (manifest + spec)

Refer user to `docs/EXPORT_FORMAT_SPEC.md` for integration details.
