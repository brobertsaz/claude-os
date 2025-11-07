# Vector Search Optimization for ServiceBot

**Date Created**: 2025-11-06
**Context**: Making ServiceBot the "most badass AI chatbot" with optimal vector search
**Current State**: SQLite direct read works but isn't optimal for scale

---

## The Problem with SQLite Direct Read

### Current Implementation (servicebot/app/knowledge/rag_engine.py)

```python
def _vector_search(self, query, kb_filter, limit):
    # 1. Generate query embedding
    response = self.openai_client.embeddings.create(model=self.embedding_model, input=query)
    query_embedding = np.array(response.data[0].embedding)

    # 2. Load ALL embeddings from SQLite
    cursor = self.conn.execute("SELECT * FROM embeddings")

    # 3. Calculate similarity for EVERY document (linear scan)
    for row in cursor:
        doc_embedding = np.frombuffer(row['embedding'], dtype=np.float32)
        similarity = cosine_similarity(query_embedding, doc_embedding)

    # 4. Sort all results and return top N
```

**Time Complexity:** O(n) where n = total documents
**Performance:**
- 10K docs: ~200-500ms ✅ Acceptable
- 100K docs: ~2-5s ⚠️ Slow
- 1M docs: 20s+ ❌ Unusable

---

## Optimization Levels

### Level 1: sqlite-vec Extension ⚡ FAST WIN

**What:** Native vector similarity search in SQLite using SIMD optimizations

**Install:**
```bash
pip install sqlite-vec
```

**Usage:**
```python
import sqlite3
import sqlite_vec

conn = sqlite3.connect('data/pistn.db')
conn.enable_load_extension(True)
sqlite_vec.load(conn)

# Create virtual table for vector search
conn.execute("""
    CREATE VIRTUAL TABLE vec_embeddings USING vec0(
        document_id INTEGER PRIMARY KEY,
        embedding FLOAT[768]
    )
""")

# Insert embeddings
conn.execute("INSERT INTO vec_embeddings SELECT document_id, embedding FROM embeddings")

# FAST vector search using ANN (Approximate Nearest Neighbors)
cursor = conn.execute("""
    SELECT document_id, distance
    FROM vec_embeddings
    WHERE embedding MATCH ?
    ORDER BY distance
    LIMIT 10
""", [query_embedding.tobytes()])
```

**Performance:**
- 10K docs: ~50-100ms (5-10x faster) ✅
- 100K docs: ~100-200ms (10-25x faster) ✅
- 1M docs: ~200-500ms (40-100x faster) ✅

**Pros:**
- ✅ Same SQLite file
- ✅ No infrastructure changes
- ✅ 10-100x faster
- ✅ Portable

**Cons:**
- ⚠️ Still in SQLite (single file limitations)
- ⚠️ Limited concurrent writes

**Recommendation:** **DO THIS FIRST** - Easy win!

---

### Level 2: Specialized Vector Database 🚀 ULTIMATE PERFORMANCE

**Options:**

#### Option A: Qdrant (Open Source, Self-Hosted)
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Initialize
client = QdrantClient(host="localhost", port=6333)

# Create collection
client.create_collection(
    collection_name="pistn_knowledge",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
)

# Import from SQLite export
import sqlite3
conn = sqlite3.connect('data/pistn.db')
cursor = conn.execute("SELECT id, embedding FROM embeddings")

points = []
for row in cursor:
    points.append(PointStruct(
        id=row[0],
        vector=np.frombuffer(row[1], dtype=np.float32).tolist(),
        payload={"doc_id": row[0]}
    ))

client.upsert(collection_name="pistn_knowledge", points=points)

# ULTRA-FAST search
results = client.search(
    collection_name="pistn_knowledge",
    query_vector=query_embedding.tolist(),
    limit=10
)
```

**Performance:**
- 10K docs: ~10-30ms ✅✅
- 100K docs: ~20-50ms ✅✅
- 1M docs: ~30-80ms ✅✅
- 10M docs: ~50-150ms ✅✅

**Pros:**
- ✅ HNSW index (O(log n) search)
- ✅ Handles millions of vectors
- ✅ Concurrent queries
- ✅ Filtering and metadata search
- ✅ Production-grade

**Cons:**
- ⚠️ Separate service to manage
- ⚠️ More infrastructure
- ⚠️ Memory requirements

#### Option B: Chroma (Simple, Embedded)
```python
import chromadb

# Initialize
client = chromadb.Client()
collection = client.create_collection("pistn_knowledge")

# Import from SQLite
conn = sqlite3.connect('data/pistn.db')
cursor = conn.execute("SELECT d.id, d.content, e.embedding FROM documents d JOIN embeddings e ON d.id = e.document_id")

for row in cursor:
    collection.add(
        ids=[str(row[0])],
        embeddings=[np.frombuffer(row[2], dtype=np.float32).tolist()],
        documents=[row[1]]
    )

# Query
results = collection.query(
    query_embeddings=[query_embedding.tolist()],
    n_results=10
)
```

**Pros:**
- ✅ Embedded (no separate server)
- ✅ Simple API
- ✅ Good performance

**Cons:**
- ⚠️ Less mature than Qdrant
- ⚠️ Limited scale (compared to Qdrant)

#### Option C: Pinecone (Cloud-Hosted)
```python
import pinecone

# Initialize
pinecone.init(api_key="your_key", environment="us-west1-gcp")
index = pinecone.Index("pistn-knowledge")

# Upsert vectors
index.upsert(vectors=[
    (str(doc_id), embedding.tolist(), metadata)
    for doc_id, embedding, metadata in documents
])

# Query (BLAZING FAST)
results = index.query(
    vector=query_embedding.tolist(),
    top_k=10,
    include_metadata=True
)
```

**Pros:**
- ✅ Zero infrastructure management
- ✅ Scales to billions
- ✅ Global CDN
- ✅ Enterprise features

**Cons:**
- ❌ Not self-hosted
- ❌ Cost (free tier: 1M vectors)
- ❌ Vendor lock-in

---

### Level 3: Hybrid Approach 🎯 BEST OF BOTH WORLDS

**Architecture:**
```
┌────────────────────────────────────────────────┐
│  ServiceBot RAG Engine (Adaptive)              │
│                                                 │
│  IF deployment == "small":                     │
│      └─ Use: SQLite with sqlite-vec           │
│         • <50K documents                       │
│         • Simple setup                         │
│         • Portable                             │
│                                                 │
│  ELIF deployment == "medium":                  │
│      └─ Use: Qdrant (self-hosted)             │
│         • 50K-1M documents                     │
│         • Local infrastructure                 │
│         • Full control                         │
│                                                 │
│  ELIF deployment == "large":                   │
│      └─ Use: Pinecone (cloud)                 │
│         • 1M+ documents                        │
│         • Global scale                         │
│         • Managed service                      │
└────────────────────────────────────────────────┘
```

**Implementation:**
```python
# servicebot/app/knowledge/vector_backends.py

class VectorBackend(ABC):
    @abstractmethod
    def search(self, query_embedding: np.ndarray, limit: int) -> List[SearchResult]:
        pass

class SQLiteVecBackend(VectorBackend):
    """Fast for small-medium deployments"""
    def search(self, query_embedding, limit):
        # Use sqlite-vec extension
        ...

class QdrantBackend(VectorBackend):
    """Best for self-hosted production"""
    def search(self, query_embedding, limit):
        # Use Qdrant client
        ...

class PineconeBackend(VectorBackend):
    """Best for cloud scale"""
    def search(self, query_embedding, limit):
        # Use Pinecone client
        ...

# Auto-select based on config
class ServiceBotRAG:
    def __init__(self, knowledge_db_path: str):
        backend_type = settings.VECTOR_BACKEND  # 'sqlite-vec', 'qdrant', 'pinecone'

        if backend_type == 'sqlite-vec':
            self.vector_backend = SQLiteVecBackend(knowledge_db_path)
        elif backend_type == 'qdrant':
            self.vector_backend = QdrantBackend(settings.QDRANT_URL)
        elif backend_type == 'pinecone':
            self.vector_backend = PineconeBackend(settings.PINECONE_API_KEY)
        else:
            # Fallback to current implementation
            self.vector_backend = NumpyBackend(knowledge_db_path)
```

---

## Recommended Implementation Plan

### Phase 1: Add sqlite-vec Support (QUICK WIN) ⚡

**Effort:** 1-2 days
**Impact:** 10-100x faster vector search

```bash
# 1. Install sqlite-vec
pip install sqlite-vec

# 2. Update ServiceBotRAG to use it
# 3. Migrate existing exports to use vec0 tables
# 4. Test performance
```

**Files to modify:**
- `servicebot/app/knowledge/rag_engine.py` - Add sqlite-vec support
- `servicebot/app/knowledge/importer.py` - Migrate embeddings to vec0 table
- `servicebot/requirements.txt` - Add sqlite-vec

**Backward compatible:** Falls back to numpy if sqlite-vec not available

### Phase 2: Add Qdrant Backend (PRODUCTION SCALE) 🚀

**Effort:** 3-5 days
**Impact:** Handles millions of documents, concurrent queries

**Benefits:**
- Sub-100ms search even with 1M+ docs
- Filtering by metadata
- Concurrent multi-user support
- Production monitoring

**Implementation:**
1. Create `VectorBackend` abstraction
2. Implement `QdrantBackend`
3. Add importer: SQLite export → Qdrant
4. Make backend configurable via environment variable

### Phase 3: Add Pinecone Option (CLOUD SCALE) ☁️

**Effort:** 2-3 days
**Impact:** Global scale, zero infrastructure

**For deployments that need:**
- Multi-region support
- Billions of vectors
- Zero ops overhead

---

## Performance Comparison

| Backend | 10K Docs | 100K Docs | 1M Docs | 10M Docs | Concurrent Users |
|---------|----------|-----------|---------|----------|------------------|
| **Current (numpy)** | 200ms | 2-5s | 20s+ | N/A | Low |
| **sqlite-vec** | 50ms | 200ms | 500ms | N/A | Low |
| **Qdrant** | 20ms | 50ms | 80ms | 150ms | High |
| **Pinecone** | 15ms | 40ms | 60ms | 100ms | Very High |

---

## Cost Comparison

| Backend | Infrastructure | Monthly Cost (100K docs) | Pros |
|---------|---------------|------------------------|------|
| **Current** | None | $0 | Simple, portable |
| **sqlite-vec** | None | $0 | Fast, free, simple |
| **Qdrant** | VPS/Server | $10-50 (server) | Full control, scalable |
| **Pinecone** | Pinecone Cloud | $70+ | Zero ops, global |

---

## Recommendation for "Most Badass Chatbot"

### For Now (Testing Phase 1):
✅ **Use current SQLite direct read**
- Testing export/import flow
- Validating knowledge quality
- Widget integration
- < 50K documents

### Next (After Phase 1 Works):
🚀 **Add sqlite-vec extension**
- Quick performance boost
- No infrastructure changes
- Production-ready for small-medium deployments

### Future (Production Scale):
💪 **Add Qdrant backend option**
- When you have 100K+ documents
- When you need multi-user concurrent access
- When sub-100ms search matters

---

## Migration Path

**The beauty of the export format:**
```
Claude OS Export (SQLite)
    ↓
    ├─→ ServiceBot (SQLite direct) ← Phase 1: Testing
    ├─→ ServiceBot (SQLite + vec) ← Phase 2: Optimization
    ├─→ ServiceBot (Qdrant) ← Phase 3: Scale
    └─→ ServiceBot (Pinecone) ← Phase 4: Cloud
```

**Same export, different backends!** The export format is backend-agnostic.

---

## Implementation Priority

1. **NOW**: Finish Phase 1 testing with current SQLite read ✅
2. **Next Week**: Add sqlite-vec for 10-100x speedup ⚡
3. **Next Month**: Add Qdrant backend for production scale 🚀
4. **Future**: Add Pinecone for global deployments ☁️

**Don't optimize prematurely** - SQLite direct read is fine for initial testing!

---

## Key Takeaway

**For the "most badass chatbot":**
- ✅ Current approach: Good for testing and small-medium scale
- ⚡ Quick win: Add sqlite-vec (10-100x faster, zero infrastructure)
- 🚀 Production: Add Qdrant backend (handles millions, concurrent)
- ☁️ Enterprise: Add Pinecone option (global scale, zero ops)

**The export format supports all of these** - you can choose based on scale!

---

**Next Steps:**
1. Test current setup with Pistn export
2. Validate knowledge quality
3. Then optimize based on actual usage patterns
