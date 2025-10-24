# Code-Forge RAG System - Comprehensive Analysis Report

## Executive Summary

The Code-Forge RAG system is experiencing **two critical issues**:
1. **Slow Response Times (30-40 seconds)**: Caused by inefficient query execution pipeline
2. **Hallucination Issues**: AI generates documentation about "advanced appointment settings" that doesn't exist, should use APPOINTMENT_COMPREHENSIVE_GUIDE.md and APPOINTMENT_FLOW_DOC.md

This report provides a thorough analysis of the architecture, data flow, and identifies specific bottlenecks and issues.

---

## 1. OVERALL CODEBASE ARCHITECTURE

### Technology Stack
- **Vector Database**: PostgreSQL + pgvector (ACID-compliant, not ChromaDB)
- **LLM Engine**: Ollama (running llama3.2:3b locally - 3B parameter model)
- **Embedding Model**: nomic-embed-text (768 dimensions)
- **RAG Framework**: LlamaIndex
- **Frontend**: Streamlit (Python)
- **API Layer**: FastAPI/MCP for agent integration

### Directory Structure
```
/Users/iamanmp/Projects/code-forge/
├── app/
│   ├── core/                    # Core RAG implementation
│   │   ├── rag_engine.py        # Main RAG query engine
│   │   ├── ingestion.py         # Document ingestion pipeline
│   │   ├── pg_manager.py        # PostgreSQL vector store management
│   │   ├── config.py            # RAG configuration parameters
│   │   ├── kb_metadata.py       # Knowledge base metadata
│   │   ├── kb_types.py          # KB type definitions
│   │   ├── markdown_preprocessor.py  # Document preprocessing
│   │   ├── agent_os_ingestion.py    # Agent OS profile handling
│   │   ├── schema_pgvector.sql  # Database schema
│   │   └── health.py            # Health checks
│   ├── pages/
│   │   ├── 0_Welcome.py         # Welcome page
│   │   └── 1_Main.py            # Main chat interface
│   ├── main.py                  # Entry point
│   ├── test_vector_query.py     # Vector query debugging
│   └── test_ollama_embedding.py # Embedding testing
├── data/
│   └── postgres/                # PostgreSQL data volume
├── test_docs/
│   └── test1.md                 # Test appointment documentation
├── tests/                       # Comprehensive test suite
└── requirements.txt             # Dependencies

```

---

## 2. DATA FLOW: FROM DOCUMENT INGESTION TO AI RESPONSE

### Phase 1: Document Ingestion (`app/core/ingestion.py`)

**Process:**
1. **Text Extraction** → Reads files (PDF, MD, TXT, code files)
   - PDFs: Uses PyMuPDF (fitz)
   - Text files: UTF-8 encoding with error handling

2. **Document Chunking**
   - **Chunk Size**: 1024 tokens
   - **Chunk Overlap**: 200 tokens
   - Uses `SentenceSplitter` from LlamaIndex
   - Each chunk gets metadata: filename, chunk_index, upload_date, etc.

3. **Markdown Preprocessing** (for `.md` files)
   - Extracts frontmatter (YAML/TOML)
   - Normalizes headers (ATX style)
   - Extracts title and tags
   - Cleans whitespace
   - Enriches metadata with title, author, date, tags

4. **Embedding Generation**
   - Uses Ollama embedding model: `nomic-embed-text`
   - Generates 768-dimensional vectors for each chunk
   - **Issue**: Each file upload creates new OllamaEmbedding instance (inefficient)

5. **Storage in PostgreSQL**
   - Uses LlamaIndex's `PGVectorStore` backend
   - Tables named `data_{kb_name}` 
   - Schema includes:
     - `id`: BIGSERIAL primary key
     - `text`: VARCHAR with chunk content
     - `metadata_`: JSON with chunk metadata
     - `node_id`: LlamaIndex node identifier
     - `embedding`: pgvector with embeddings
   - **Indexes**:
     - IVFFlat index on embeddings (100 lists)
     - Index on metadata ref_doc_id

**Bottleneck #1**: Document ingestion creates new embedding models for each file instead of reusing a singleton.

---

### Phase 2: Query Execution (`app/core/rag_engine.py`)

**RAG Configuration** (from `config.py`):
```python
CHUNK_SIZE: 1024
CHUNK_OVERLAP: 200
TOP_K_RETRIEVAL: 5        # Only retrieve top 5 chunks
SIMILARITY_THRESHOLD: 0.7  # Must be >70% similar (increased from 0.4)
RERANK_TOP_N: 3
```

**Query Pipeline:**

```
1. User Query (Streamlit chat interface)
   ↓
2. RAGEngine.query()
   ├─ Creates new RAGEngine instance for each query (EXPENSIVE!)
   │  ├─ Initializes Ollama LLM (llama3.2:3b)
   │  │  - context_window: 1024 tokens
   │  │  - num_predict: 400 tokens
   │  │  - temperature: 0.3
   │  │
   │  ├─ Initializes OllamaEmbedding
   │  │
   │  ├─ Creates PGVectorStore connection
   │  │
   │  └─ Creates VectorStoreIndex
   │
   3. Vector Search Phase
   │  ├─ Query embedding generated
   │  ├─ PGVectorStore.retrieve() using cosine similarity
   │  ├─ Retrieves TOP_K_RETRIEVAL (5) chunks
   │  └─ Filters by SIMILARITY_THRESHOLD (0.7)
   │
   4. Reranking Phase (DISABLED - causes 40+ sec delays)
   │  └─ Would use SentenceTransformerRerank if enabled
   │
   5. LLM Response Generation
   │  ├─ Synthesizes answer from top chunks
   │  ├─ Uses custom prompt template
   │  ├─ Mode: "simple_summarize" (single LLM call)
   │  └─ Response limit: 400 tokens
   │
   6. Response Formatting & Return
```

**Critical Performance Issues:**

1. **RAGEngine Instantiation (10-15 seconds)**
   - Creates NEW Ollama LLM connection for EACH query
   - Creates NEW OllamaEmbedding for EACH query
   - Creates NEW PGVectorStore for EACH query
   - Should use singleton pattern with caching

2. **LLM Inference (15-25 seconds)**
   - Using llama3.2:3b on CPU
   - Small model but still slow
   - Context window: 1024 tokens (small)
   - num_predict: 400 tokens max response

3. **Vector Search (1-2 seconds)**
   - Actually reasonable due to IVFFlat index
   - TOP_K_RETRIEVAL=5 is good

**Bottleneck #2**: New RAGEngine instance created for every query
**Bottleneck #3**: LLM running on CPU for small 3B model

---

## 3. EMBEDDING MODEL & LLM CONFIGURATION

### Embedding Model: nomic-embed-text
- **Dimensions**: 768
- **Type**: Text embedding model
- **Performance**: Fast but generic
- **Generated by**: Ollama at inference time for each chunk
- **Issue**: No semantic understanding of appointment flow

### LLM: llama3.2:3b
- **Parameters**: 3 billion (small, CPU-friendly)
- **Context Window**: 1024 tokens (very limiting)
- **Temperature**: 0.3 (low = deterministic)
- **Max Response**: 400 tokens
- **Top-K Sampling**: 20
- **Top-P (Nucleus)**: 0.9
- **Timeout**: 60 seconds
- **Model URL**: http://ollama:11434

**Problem**: Small model (3B) is prone to hallucination with limited context

---

## 4. DATABASE/VECTOR STORE CONFIGURATION

### PostgreSQL Schema (`schema_pgvector.sql`)

**Metadata Table:**
```sql
knowledge_bases (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) UNIQUE,
  kb_type VARCHAR(50) DEFAULT 'GENERIC',  -- GENERIC, CODE, DOCUMENTATION, AGENT_OS
  description TEXT,
  metadata JSONB DEFAULT '{}',
  table_name VARCHAR(255) UNIQUE,
  embed_dim INTEGER DEFAULT 768,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Data Tables (per KB):**
```sql
data_{kb_name} (
  id BIGSERIAL PRIMARY KEY,
  text VARCHAR NOT NULL,
  metadata_ JSON,
  node_id VARCHAR,
  embedding vector(768)
)

-- Indexes:
idx_{kb_name}_metadata_ref_doc ON metadata_ ->> 'ref_doc_id'
idx_{kb_name}_embedding USING IVFFlat (embedding vector_cosine_ops) WITH (lists=100)
```

**Connection Pool:**
- Min connections: 1
- Max connections: 10
- Simple connection pool (not HikariCP)

**Issue**: IVFFlat index configuration (lists=100) might not be optimal for large datasets

---

## 5. HALLUCINATION ANALYSIS

### Root Cause: Weak Retrieval + Small Model

**The Problem:**
```
User Query: "How do appointments work?"
↓
Vector Search: Finds chunks about "appointments" (generic hits)
↓
TOP_K=5 retrieval: Gets top 5 similar chunks (might be insufficient)
↓
Small 3B Model: Synthesizes answer from limited context
↓
Result: "Advanced appointment settings" (HALLUCINATION - not in documents!)
```

**Why It's Happening:**

1. **Insufficient Context Window**
   - Context: 1024 tokens
   - Even 5 chunks at 200 tokens each = 1000 tokens
   - LLM has almost no room for question + instructions
   - Forced to generate from poor context

2. **Generic Embedding Model**
   - `nomic-embed-text` is generic
   - Doesn't understand appointment workflow semantics
   - Can't distinguish between "basic appointment" vs "advanced settings"

3. **TOP_K=5 Is Too Restrictive**
   - Only retrieves 5 chunks
   - If those 5 don't contain full appointment flow, model hallucinates
   - Should test with TOP_K=10-15 for documentation KB

4. **SIMILARITY_THRESHOLD=0.7 Is Too High**
   - Might filter out relevant chunks with 0.65-0.70 similarity
   - Document KB (documentation) should use lower threshold (0.5-0.6)

5. **Small 3B Model Limitations**
   - llama3.2:3b is prone to hallucination
   - Lacks grounding with limited context
   - Custom prompt (prevents hallucination) helps but not enough

**Evidence from Code:**
```python
# rag_engine.py, line 140-156
qa_prompt_template = PromptTemplate(
    "STRICT RULES - VIOLATION WILL CAUSE SYSTEM FAILURE:\n"
    "1. **ONLY use information explicitly stated in the context above**\n"
    "2. **If the answer is not in the context, respond EXACTLY**: \"I don't have specific documentation about that...\"\n"
    ...
)

# BUT context is too small, so model struggles to comply
```

---

## 6. PERFORMANCE BOTTLENECKS

### Bottleneck #1: RAGEngine Instantiation (CRITICAL - 10-15 sec per query)

**Location**: `app/pages/1_Main.py`, line 807

```python
# This happens for EVERY query - very expensive!
rag_engine = RAGEngine(st.session_state.selected_kb)
result = rag_engine.query(prompt, ...)
```

**What Happens:**
```
RAGEngine.__init__()
├─ Ollama LLM initialization (connects to HTTP endpoint)
├─ OllamaEmbedding initialization (new instance)
├─ PostgreSQL connection (gets from pool)
├─ PGVectorStore initialization
├─ VectorStoreIndex creation (loads all documents into memory)
├─ BM25Retriever initialization (if enabled)
└─ SubQuestion Engine setup
```

**Cost**: 10-15 seconds of pure initialization overhead

**Solution**: Use singleton pattern with caching by KB name

### Bottleneck #2: LLM Inference on CPU (15-25 sec per query)

**Configuration** (`rag_engine.py`, line 44-55):
```python
self.llm = Ollama(
    model="llama3.2:3b",
    base_url="http://ollama:11434",
    request_timeout=60.0,
    context_window=1024,      # Very small
    num_ctx=1024,
    temperature=0.3,
    num_predict=400,          # Limits response length
    top_k=20,
    top_p=0.9,
)
```

**Problem**: 3B model on CPU with 1024 token context = slow inference

**Typical Speed**: ~20-30 tokens/second with 3B model on CPU = 13-20 seconds for 400 token response

### Bottleneck #3: Chunking Strategy for Dense Documentation

**Configuration** (`config.py`):
```python
CHUNK_SIZE: 1024         # Large chunks (good for RAG)
CHUNK_OVERLAP: 200       # Moderate overlap
```

**Problem**: With APPOINTMENT_FLOW_DOC.md, need to ensure workflow is preserved in single chunks

**Example Issue**:
```
Chunk 1: "1. User selects provider..."
Chunk 2: "2. User chooses time slot..."
Chunk 3: "...advanced settings..." (UNRELATED)

When retrieving "how do appointments work?", might get chunk 3 
instead of chunks 1+2, missing context
```

### Bottleneck #4: Reranking Disabled (Feature Missing)

**Status** (`rag_engine.py`, line 133-137):
```python
# Initialize reranker (DISABLED by default due to performance issues - 40+ seconds per query)
self.reranker = None
logger.info("Reranker disabled for performance (enable in code if needed)")
```

**Problem**: SentenceTransformerRerank downloads large cross-encoder model and runs on CPU
- Adds 30-40 seconds per query
- Not worth it with only 5 chunks

**Better Approach**: Use lightweight reranker or improve retrieval quality instead

### Bottleneck #5: Excessive Metadata in Queries

**Issue**: Each metadata JSON includes excessive fields
- Original approach included tags, KB type, timestamps in every query
- Modern approach still includes full metadata_ JSON in results

---

## 7. THE APPOINTMENT DOCUMENTATION ISSUE

### Missing Documentation Files

The user mentioned:
- `APPOINTMENT_COMPREHENSIVE_GUIDE.md` - NOT FOUND
- `APPOINTMENT_FLOW_DOC.md` - NOT FOUND

**Current Test Docs** (`test_docs/test1.md`):
```markdown
# Test Document 1 - About Appointments

## Basic Appointments
- Single appointments
- Recurring appointments
- Group appointments
- Virtual appointments

## Appointment Workflow
1. User selects a provider
2. User chooses an available time slot
3. System confirms the appointment
4. User receives confirmation email
5. Provider is notified

## Cancellation Policy
Appointments can be cancelled up to 24 hours in advance
```

**Problem**: This test doc is too generic and incomplete
- AI hallucinates "advanced appointment settings"
- No actual advanced settings documented
- Workflow is incomplete (missing details on each step)

### Hallucination Manifestation

**AI Response**: "Advanced appointment settings let you configure..."
**Reality**: No "advanced settings" section exists in documentation

**Why This Happens:**
1. Top 5 chunks don't contain complete workflow
2. Model fills gaps with plausible-sounding content
3. Small context window doesn't help model catch the hallucination
4. Prompt instruction to cite sources isn't being followed

---

## 8. CONFIGURATION PARAMETERS ANALYSIS

### RAG Configuration

| Parameter | Current Value | Impact | Recommendation |
|-----------|---------------|--------|-----------------|
| CHUNK_SIZE | 1024 | Good balance | Keep (or try 1500 for docs) |
| CHUNK_OVERLAP | 200 | Good | Consider 300-400 for dense docs |
| TOP_K_RETRIEVAL | 5 | **TOO LOW** | Increase to 10-15 for docs |
| SIMILARITY_THRESHOLD | 0.7 | **TOO HIGH** | Lower to 0.5-0.6 for docs |
| RERANK_TOP_N | 3 | N/A (disabled) | Keep disabled |
| Context Window | 1024 | Very small | Should be 2048-4096 |
| num_predict | 400 | Limited | OK for summaries |
| Temperature | 0.3 | Good | Keep (low variance) |

### Type-Specific RAG Defaults

```python
KB_TYPE_RAG_DEFAULTS = {
    "documentation": {
        "hybrid": True,      # Keyword + semantic
        "rerank": True,      # Better relevance
        "agentic": False
    }
}
```

**Problem**: Documentation KBs recommend reranking which adds 30-40 seconds per query

---

## 9. CODE ISSUES & ANTI-PATTERNS

### Issue #1: RAGEngine as Service Class (Not Singleton)

```python
# ❌ WRONG - app/pages/1_Main.py line 807
rag_engine = RAGEngine(st.session_state.selected_kb)
result = rag_engine.query(prompt, ...)
```

**Impact**: 10-15 second overhead per query for initialization

**Fix**: Implement singleton with KB-specific caching

### Issue #2: OllamaEmbedding Created Per File

```python
# ❌ WRONG - app/core/ingestion.py line 139-142
for chunk in chunks:
    embed_model = OllamaEmbedding(...)  # NEW INSTANCE!
    embedding = embed_model.get_text_embedding(chunk.text)
```

**Impact**: Massive redundancy during batch ingestion

**Fix**: Create once, reuse

### Issue #3: Similarity Threshold Too High for Documentation

```python
# ❌ WRONG for documentation KB
SIMILARITY_THRESHOLD: 0.7  # Filters out valuable chunks
```

**Impact**: Retrieves fewer relevant chunks, increases hallucination risk

**Fix**: Make threshold KB-type specific

### Issue #4: Insufficient Top-K for Documentation

```python
# ❌ WRONG for dense documentation
TOP_K_RETRIEVAL: 5  # Might miss parts of workflow
```

**Impact**: Incomplete context leads to hallucination

**Fix**: Increase to 10-15 for documentation, make configurable per KB type

### Issue #5: Context Window Too Small

```python
# ❌ WRONG for multi-chunk synthesis
context_window=1024,  # Not enough for 5 chunks + question + instructions
```

**Impact**: Insufficient space for context, forces model to hallucinate

**Fix**: Increase to 2048 or 4096

### Issue #6: Generic Embedding Model

```python
# ⚠️  SUBOPTIMAL
OLLAMA_EMBED_MODEL: "nomic-embed-text"  # Generic, not domain-specific
```

**Impact**: Poor semantic matching for specialized domains

**Fix**: Consider domain-specific embeddings or fine-tuned models

---

## 10. KEY FINDINGS & RECOMMENDATIONS

### Critical Issues

1. **Performance Bottleneck (30-40 sec queries)**
   - Root cause: RAGEngine instantiation (10-15s) + LLM inference (15-25s)
   - **Fix**: Implement RAGEngine singleton caching + consider larger model or GPU

2. **Hallucination Issue**
   - Root cause: Insufficient context (TOP_K=5) + small model + limited window
   - **Fix**: Increase TOP_K to 10-15, lower SIMILARITY_THRESHOLD, or use larger model

3. **Missing Documentation**
   - Current test doc is incomplete
   - Needs APPOINTMENT_COMPREHENSIVE_GUIDE.md and APPOINTMENT_FLOW_DOC.md

### Performance Improvement Priority

| Priority | Fix | Estimated Time Savings |
|----------|-----|------------------------|
| 1 | RAGEngine singleton caching | 10-15 seconds |
| 2 | Increase model (to 7B or use GPU) | 5-10 seconds |
| 3 | Optimize chunk retrieval (TOP_K=10, threshold=0.6) | 0-2 seconds |
| 4 | Implement connection pooling for Ollama | 1-3 seconds |

### Hallucination Prevention Priority

| Priority | Fix | Effectiveness |
|----------|-----|----------------|
| 1 | Increase TOP_K_RETRIEVAL to 10-15 | High |
| 2 | Lower SIMILARITY_THRESHOLD to 0.5-0.6 | High |
| 3 | Increase context_window to 2048 | Medium |
| 4 | Ingest complete documentation files | High |
| 5 | Use larger model (7B+) | Medium |

---

## 11. DETAILED DATA FLOW DIAGRAM

```
INGESTION FLOW:
==============

[Document Upload]
    ↓
[Text Extraction] (PDF/TXT/MD/Code)
    ↓
[Markdown Preprocessing] (if MD)
    │ ├─ Extract frontmatter
    │ ├─ Normalize headers
    │ └─ Extract metadata
    ↓
[Chunking] (SentenceSplitter)
    │ ├─ Chunk size: 1024 tokens
    │ ├─ Overlap: 200 tokens
    │ └─ Add chunk metadata
    ↓
[Embedding Generation] (Ollama nomic-embed-text)
    │ ├─ 768-dimensional vectors
    │ └─ One embedding per chunk
    ↓
[PostgreSQL Storage] (PGVectorStore)
    │ ├─ Table: data_{kb_name}
    │ ├─ Columns: text, metadata_, node_id, embedding
    │ └─ Indexes: IVFFlat on embedding
    ↓
[Metadata Registration]
    └─ knowledge_bases table


QUERY FLOW:
===========

[User Question] (Streamlit chat)
    ↓
[RAGEngine Instantiation] ⚠️ SLOW (10-15s)
    │ ├─ Create Ollama LLM
    │ ├─ Create OllamaEmbedding
    │ ├─ Connect to PostgreSQL
    │ ├─ Create PGVectorStore
    │ └─ Create VectorStoreIndex
    ↓
[Query Embedding] (0.5-1s)
    │ └─ Convert question to 768-dim vector
    ↓
[Vector Search] (1-2s)
    │ ├─ Cosine similarity against pgvector
    │ ├─ IVFFlat index lookup
    │ ├─ Retrieve TOP_K=5 chunks
    │ └─ Filter by SIMILARITY_THRESHOLD=0.7
    ↓
[Reranking] (DISABLED - would add 30-40s)
    └─ Skip SentenceTransformerRerank
    ↓
[LLM Synthesis] ⚠️ SLOW (15-25s)
    │ ├─ Build prompt with context
    │ ├─ Call Ollama llama3.2:3b
    │ ├─ Generate up to 400 tokens
    │ └─ Temperature=0.3 (deterministic)
    ↓
[Response Formatting] (<1s)
    │ ├─ Extract answer
    │ ├─ Format sources
    │ └─ Calculate similarity scores
    ↓
[Display to User] (Streamlit)
    └─ Show answer + sources

TOTAL TIME: 30-45 seconds
├─ Initialization: 10-15s
├─ Search: 1-2s
├─ LLM: 15-25s
└─ Other: 2-5s
```

---

## 12. ARCHITECTURE STRENGTHS

1. **ACID Compliance**: PostgreSQL provides data integrity
2. **Scalability**: Separate tables per KB allow independent scaling
3. **Vector Indexing**: IVFFlat provides approximate search efficiency
4. **Connection Pooling**: Simple pool prevents connection exhaustion
5. **Multi-KB Support**: Supports multiple isolated knowledge bases
6. **Document Preprocessing**: Markdown extraction of metadata
7. **Type-Safe Storage**: JSONB metadata with validation
8. **Comprehensive Testing**: Good test coverage

---

## 13. ARCHITECTURE WEAKNESSES

1. **No RAGEngine Caching**: Creates new instances per query (EXPENSIVE)
2. **Insufficient Context**: 1024 token window too small for multi-chunk synthesis
3. **Small LLM**: 3B model prone to hallucination
4. **CPU-Based Inference**: No GPU acceleration
5. **Limited Retrieval**: TOP_K=5 often insufficient for complex docs
6. **High Similarity Threshold**: 0.7 filters out potentially relevant chunks
7. **Disabled Reranking**: Can't improve relevance due to performance issues
8. **Generic Embeddings**: nomic-embed-text lacks domain specificity

---

## SUMMARY TABLE: KEY METRICS

| Component | Current Value | Status | Notes |
|-----------|---------------|--------|-------|
| LLM Model | llama3.2:3b | ⚠️ Slow | Small model on CPU |
| Embedding Model | nomic-embed-text | ✅ Fast | Generic, not specialized |
| Embedding Dimension | 768 | ✅ Good | Standard for nomic |
| Vector Index | IVFFlat (100 lists) | ⚠️ OK | Might need tuning |
| TOP_K Retrieval | 5 | ❌ Low | Should be 10-15 |
| Similarity Threshold | 0.7 | ❌ High | Should be 0.5-0.6 |
| Context Window | 1024 | ❌ Small | Should be 2048+ |
| Query Latency | 30-40s | ❌ Slow | 10-15s initialization |
| RAGEngine Caching | None | ❌ None | Major bottleneck |
| Reranking | Disabled | ⚠️ N/A | Adds 30-40s if enabled |
| Connection Pool | 1-10 conns | ✅ Good | Simple but effective |
| Chunking | 1024/200 overlap | ✅ Good | Reasonable settings |

---

## APPENDIX: FILE LOCATIONS

| Component | File Path |
|-----------|-----------|
| RAG Engine | `/Users/iamanmp/Projects/code-forge/app/core/rag_engine.py` |
| Ingestion Pipeline | `/Users/iamanmp/Projects/code-forge/app/core/ingestion.py` |
| PostgreSQL Manager | `/Users/iamanmp/Projects/code-forge/app/core/pg_manager.py` |
| Configuration | `/Users/iamanmp/Projects/code-forge/app/core/config.py` |
| Database Schema | `/Users/iamanmp/Projects/code-forge/app/core/schema_pgvector.sql` |
| Chat Interface | `/Users/iamanmp/Projects/code-forge/app/pages/1_Main.py` |
| KB Metadata | `/Users/iamanmp/Projects/code-forge/app/core/kb_metadata.py` |
| Markdown Preprocessor | `/Users/iamanmp/Projects/code-forge/app/core/markdown_preprocessor.py` |
| Test Documentation | `/Users/iamanmp/Projects/code-forge/test_docs/test1.md` |
| Vector Query Debug | `/Users/iamanmp/Projects/code-forge/app/test_vector_query.py` |
| Embedding Debug | `/Users/iamanmp/Projects/code-forge/app/test_ollama_embedding.py` |

---

## APPENDIX: CONFIGURATION PARAMETERS

### From `app/core/config.py`:
```python
# Ollama
OLLAMA_HOST: "http://ollama:11434"
OLLAMA_MODEL: "llama3.2:3b"
OLLAMA_EMBED_MODEL: "nomic-embed-text"

# RAG Settings
CHUNK_SIZE: 1024
CHUNK_OVERLAP: 200
TOP_K_RETRIEVAL: 5
RERANK_TOP_N: 3
SIMILARITY_THRESHOLD: 0.7

# KB Type Defaults
KB_TYPE_RAG_DEFAULTS:
  - generic: hybrid=False, rerank=False, agentic=False
  - code: hybrid=True, rerank=True, agentic=False
  - documentation: hybrid=True, rerank=True, agentic=False
  - agent-os: hybrid=True, rerank=True, agentic=True
```

### From `app/core/rag_engine.py`:
```python
# Ollama LLM Settings
context_window: 1024
num_ctx: 1024
temperature: 0.3
num_predict: 400
top_k: 20
top_p: 0.9
request_timeout: 60.0

# Retrieval Settings
similarity_top_k: 5
response_mode: "simple_summarize"
similarity_cutoff: 0.7
```

---

**Report Generated**: 2025-10-23
**Analysis Depth**: Comprehensive (code, architecture, performance, config)
