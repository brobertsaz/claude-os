# Claude OS Export Format Specification

Version: 1.0
Last Updated: 2025-11-06

## Overview

Claude OS exports knowledge bases to a portable, self-contained SQLite database format. This format is designed to be consumed by external applications without requiring Claude OS to be running.

## Format Characteristics

- **Self-Contained**: Single SQLite file with all data
- **Portable**: Copy to any system, no external dependencies
- **Queryable**: Standard SQL interface
- **Versioned**: Format version included for compatibility
- **Documented**: Clear schema and usage patterns
- **Efficient**: Indexed for fast queries

## Export Artifacts

Each export produces two files:

1. **Database File**: `<project>_export_<timestamp>.db`
2. **Manifest File**: `<project>_export_<timestamp>.manifest.json`

### Example

```
exports/
├── dealer_123_export_20251106_193000.db
└── dealer_123_export_20251106_193000.manifest.json
```

---

## Database Schema

### Tables

#### 1. `knowledge_bases`

Metadata about exported knowledge bases.

```sql
CREATE TABLE knowledge_bases (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    kb_type TEXT,
    description TEXT,
    created_at TEXT,
    document_count INTEGER DEFAULT 0,
    embedding_model TEXT,
    embedding_dimensions INTEGER
);
```

**Columns:**
- `id`: Unique identifier
- `name`: Knowledge base name (e.g., "dealer_123-knowledge_docs")
- `kb_type`: Type of KB (documentation, profile, memories, index)
- `description`: Human-readable description
- `created_at`: ISO 8601 timestamp
- `document_count`: Number of documents in this KB
- `embedding_model`: Model used for embeddings (e.g., "nomic-embed-text")
- `embedding_dimensions`: Vector dimension count (e.g., 768)

**Example:**
```sql
SELECT * FROM knowledge_bases;
```
| id | name | kb_type | description | created_at | document_count | embedding_model | embedding_dimensions |
|----|------|---------|-------------|------------|----------------|-----------------|---------------------|
| 1 | dealer_123-knowledge_docs | documentation | Service guides and FAQs | 2025-11-01T10:00:00Z | 45 | nomic-embed-text | 768 |
| 2 | dealer_123-project_profile | profile | Business context | 2025-11-01T10:00:00Z | 12 | nomic-embed-text | 768 |

---

#### 2. `documents`

Document content and metadata.

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    kb_id INTEGER NOT NULL,
    kb_name TEXT NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    source_file TEXT,
    metadata TEXT,
    created_at TEXT,
    FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id)
);

CREATE INDEX idx_documents_kb_id ON documents(kb_id);
CREATE INDEX idx_documents_kb_name ON documents(kb_name);
```

**Columns:**
- `id`: Unique identifier
- `kb_id`: Foreign key to knowledge_bases
- `kb_name`: KB name (denormalized for convenience)
- `title`: Document title
- `content`: Full document text content
- `source_file`: Original filename (e.g., "service_guide.md")
- `metadata`: JSON string with additional metadata
- `created_at`: ISO 8601 timestamp

**Example:**
```sql
SELECT id, kb_name, title, source_file FROM documents LIMIT 3;
```
| id | kb_name | title | source_file |
|----|---------|-------|-------------|
| 1 | dealer_123-knowledge_docs | Oil Change Guide | service_guide.md |
| 2 | dealer_123-knowledge_docs | Pricing Information | pricing.md |
| 3 | dealer_123-knowledge_docs | FAQ | faq.md |

**Metadata Format:**
```json
{
  "chunk_index": 0,
  "total_chunks": 3,
  "file_type": "markdown",
  "tags": ["service", "maintenance"]
}
```

---

#### 3. `embeddings` (Optional)

Vector embeddings for semantic search.

```sql
CREATE TABLE embeddings (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL,
    embedding BLOB NOT NULL,
    model TEXT,
    dimensions INTEGER,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

CREATE INDEX idx_embeddings_document_id ON embeddings(document_id);
```

**Columns:**
- `id`: Unique identifier
- `document_id`: Foreign key to documents
- `embedding`: Binary vector data
- `model`: Embedding model name
- `dimensions`: Vector dimension count

**Note:** This table is only present if `--include-embeddings` was used during export.

---

#### 4. `export_metadata`

Export metadata and versioning information.

```sql
CREATE TABLE export_metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

**Required Keys:**
- `format_version`: Export format version (e.g., "1.0")
- `exported_at`: Export timestamp (ISO 8601)

**Example:**
```sql
SELECT * FROM export_metadata;
```
| key | value |
|-----|-------|
| format_version | 1.0 |
| exported_at | 2025-11-06T19:30:00Z |

---

## Manifest File Format

The manifest is a JSON file with export metadata.

### Structure

```json
{
  "format_version": "1.0",
  "exported_at": "2025-11-06T19:30:00Z",
  "project_name": "dealer_123",
  "export_file": "dealer_123_export_20251106_193000.db",
  "knowledge_bases": [
    {
      "name": "dealer_123-knowledge_docs",
      "type": "documentation",
      "description": "Service guides, FAQs, and policies"
    },
    {
      "name": "dealer_123-project_profile",
      "type": "profile",
      "description": "Business context and standards"
    }
  ],
  "stats": {
    "kb_count": 2,
    "total_documents": 57,
    "file_size_bytes": 91234567,
    "file_size_mb": 87.0,
    "includes_embeddings": true
  },
  "schema": {
    "tables": ["knowledge_bases", "documents", "embeddings", "export_metadata"],
    "format": "sqlite3",
    "version": "3.0"
  }
}
```

### Fields

- `format_version`: Export format specification version
- `exported_at`: When export was created (ISO 8601)
- `project_name`: Name of exported project
- `export_file`: Database filename
- `knowledge_bases`: Array of exported KBs
- `stats`: Export statistics
- `schema`: Database schema information

---

## Usage Examples

### Basic Queries

**List all knowledge bases:**
```sql
SELECT name, kb_type, document_count
FROM knowledge_bases;
```

**Search documents by keyword:**
```sql
SELECT d.title, d.content, kb.name
FROM documents d
JOIN knowledge_bases kb ON d.kb_id = kb.id
WHERE d.content LIKE '%oil change%'
LIMIT 10;
```

**Get all documents from specific KB:**
```sql
SELECT title, content, source_file
FROM documents
WHERE kb_name = 'dealer_123-knowledge_docs'
ORDER BY created_at DESC;
```

**Count documents per KB:**
```sql
SELECT kb_name, COUNT(*) as doc_count
FROM documents
GROUP BY kb_name;
```

---

## Integration Patterns

### Python Example

```python
import sqlite3
import json

# Load export
conn = sqlite3.connect('dealer_123_export.db')
conn.row_factory = sqlite3.Row

# Check format version
cursor = conn.execute(
    "SELECT value FROM export_metadata WHERE key = 'format_version'"
)
version = cursor.fetchone()[0]
assert version == "1.0", f"Unsupported format version: {version}"

# Query documents
def search_knowledge(query_text):
    cursor = conn.execute("""
        SELECT d.title, d.content, d.source_file, kb.name as kb_name
        FROM documents d
        JOIN knowledge_bases kb ON d.kb_id = kb.id
        WHERE d.content LIKE ?
        ORDER BY d.created_at DESC
        LIMIT 5
    """, (f'%{query_text}%',))

    return [dict(row) for row in cursor.fetchall()]

# Example query
results = search_knowledge("appointment booking")
for doc in results:
    print(f"{doc['title']} ({doc['kb_name']})")
    print(f"Source: {doc['source_file']}")
    print(f"Content: {doc['content'][:200]}...")
    print()

conn.close()
```

### JavaScript/Node.js Example

```javascript
const sqlite3 = require('sqlite3').verbose();

// Load export
const db = new sqlite3.Database('dealer_123_export.db');

// Query knowledge
function searchKnowledge(queryText) {
  return new Promise((resolve, reject) => {
    db.all(`
      SELECT d.title, d.content, d.source_file, kb.name as kb_name
      FROM documents d
      JOIN knowledge_bases kb ON d.kb_id = kb.id
      WHERE d.content LIKE ?
      LIMIT 5
    `, [`%${queryText}%`], (err, rows) => {
      if (err) reject(err);
      else resolve(rows);
    });
  });
}

// Usage
searchKnowledge('oil change')
  .then(results => {
    results.forEach(doc => {
      console.log(`${doc.title} (${doc.kb_name})`);
      console.log(`Source: ${doc.source_file}`);
      console.log(`Content: ${doc.content.substring(0, 200)}...`);
      console.log();
    });
  });
```

---

## Vector Search (Advanced)

If embeddings are included, you can perform vector similarity search using the `sqlite-vec` extension or by extracting embeddings and using an external vector library.

### Using sqlite-vec Extension

```python
import sqlite3
import numpy as np

conn = sqlite3.connect('dealer_123_export.db')
conn.enable_load_extension(True)
conn.load_extension('vec0')  # Load sqlite-vec

def vector_search(query_embedding, limit=5):
    # Convert embedding to format expected by sqlite-vec
    embedding_blob = np.array(query_embedding, dtype=np.float32).tobytes()

    cursor = conn.execute("""
        SELECT d.title, d.content,
               vec_distance_cosine(e.embedding, ?) as distance
        FROM documents d
        JOIN embeddings e ON d.id = e.document_id
        ORDER BY distance ASC
        LIMIT ?
    """, (embedding_blob, limit))

    return cursor.fetchall()
```

---

## Migration and Updates

### Format Version Changes

Future versions may add:
- Additional tables
- New columns (always optional/nullable)
- Enhanced metadata

**Backward Compatibility:**
- Version 1.x exports will remain readable
- New features will be additive, not breaking
- Format version in manifest and database

### Checking Format Version

Always check format version before processing:

```python
def check_format_compatibility(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.execute(
        "SELECT value FROM export_metadata WHERE key = 'format_version'"
    )
    version = cursor.fetchone()[0]
    conn.close()

    major_version = int(version.split('.')[0])
    if major_version > 1:
        raise ValueError(f"Unsupported format version: {version}")

    return version
```

---

## Best Practices

### For Export

1. **Include Embeddings** if consumer needs semantic search
2. **Exclude Embeddings** for smaller file size if only keyword search needed
3. **Export Regularly** to keep snapshots up to date
4. **Name Consistently** using project name as prefix

### For Consumption

1. **Check Format Version** before processing
2. **Use Indices** for fast queries (already created)
3. **Read-Only Access** - treat export as immutable
4. **Cache Locally** - don't query over network
5. **Handle Missing Data** - not all fields are required

---

## File Size Estimates

Typical export sizes:

| Documents | With Embeddings | Without Embeddings |
|-----------|----------------|-------------------|
| 10 docs   | ~5 MB          | ~500 KB          |
| 50 docs   | ~25 MB         | ~2 MB            |
| 100 docs  | ~50 MB         | ~5 MB            |
| 500 docs  | ~250 MB        | ~20 MB           |

*Note: Sizes vary based on document length and embedding dimensions*

---

## Support and Issues

For questions or issues with the export format:

1. Check format version compatibility
2. Verify manifest file
3. Validate schema with reference queries
4. See Claude OS documentation

---

## License

Claude OS exports are intended for use with applications consuming the knowledge. The export format itself is documented for integration purposes.

---

**Version History:**
- **1.0** (2025-11-06): Initial format specification
