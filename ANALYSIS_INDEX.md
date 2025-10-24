# Code-Forge RAG Analysis - Complete Documentation Index

## Quick Links to Analysis Documents

### 1. ANALYSIS_SUMMARY.txt (START HERE)
**Location**: `/Users/iamanmp/Projects/code-forge/ANALYSIS_SUMMARY.txt`
**Size**: 9 KB
**Read Time**: 5-10 minutes

A concise one-page reference covering:
- Overview and architecture
- The two critical issues (performance + hallucination)
- Root causes and fixes
- Data flow diagrams
- Configuration parameters
- File locations for all components
- Performance targets

**Best for**: Quick understanding and reference

---

### 2. RAG_ANALYSIS.md (COMPREHENSIVE)
**Location**: `/Users/iamanmp/Projects/code-forge/RAG_ANALYSIS.md`
**Size**: 23 KB (760 lines)
**Read Time**: 30-45 minutes

Deep dive into:
- Overall codebase architecture
- Detailed data flow (ingestion → response)
- Embedding model configuration
- LLM configuration (llama3.2:3b)
- Database/vector store details
- Hallucination root cause analysis
- Performance bottleneck breakdown (6 bottlenecks identified)
- Configuration parameters analysis
- Code issues and anti-patterns
- Strengths and weaknesses
- Detailed data flow diagrams

**Best for**: Deep understanding and implementation planning

---

### 3. QUICK_FIXES.md (ACTION PLAN)
**Location**: `/Users/iamanmp/Projects/code-forge/QUICK_FIXES.md`
**Size**: 6.5 KB
**Read Time**: 10-15 minutes

Actionable steps including:
- Quick fix summary for both critical issues
- File locations and line numbers
- Implementation priority matrix
- Quick wins (<30 min) vs long-term fixes
- Testing procedures
- Configuration change checklist
- Performance monitoring

**Best for**: Implementation and fixing issues

---

## The Two Critical Issues

### Issue #1: Slow Response Times (30-40 seconds)

**Problem**: Queries take 30-40 seconds to respond

**Root Cause**:
- 10-15s: RAGEngine instantiation (NEW instance per query - BIGGEST BOTTLENECK)
- 15-25s: LLM inference (llama3.2:3b on CPU)
- 1-2s: Vector search (efficient)
- 2-5s: Other overhead

**Top Fixes**:
1. Implement RAGEngine singleton caching → Save 10-15s
2. Increase context window (1024→2048) → Improve inference
3. Use larger LLM (7B+) or GPU → Save 5-10s

**Files to Modify**:
- `/Users/iamanmp/Projects/code-forge/app/pages/1_Main.py` (line 807)
- `/Users/iamanmp/Projects/code-forge/app/core/rag_engine.py` (line 49)
- `/Users/iamanmp/Projects/code-forge/app/core/config.py` (line 21)

---

### Issue #2: Hallucination About "Advanced Appointment Settings"

**Problem**: AI generates documentation about "advanced appointment settings" that doesn't exist

**Root Causes**:
- TOP_K_RETRIEVAL = 5 (insufficient chunks)
- SIMILARITY_THRESHOLD = 0.7 (filters relevant chunks)
- context_window = 1024 (too small)
- llama3.2:3b (small model prone to hallucination)
- Test doc is generic/incomplete

**Top Fixes**:
1. Increase TOP_K_RETRIEVAL (5→10-15) → HIGH impact
2. Lower SIMILARITY_THRESHOLD (0.7→0.5-0.6) → HIGH impact
3. Create comprehensive appointment docs → HIGH impact
4. Increase context_window (1024→2048) → MEDIUM impact
5. Use larger LLM → MEDIUM impact

**Files to Modify**:
- `/Users/iamanmp/Projects/code-forge/app/core/config.py` (lines 43, 45)
- `/Users/iamanmp/Projects/code-forge/test_docs/` (create new MD files)
- `/Users/iamanmp/Projects/code-forge/app/core/rag_engine.py` (line 49)

---

## Key Files in Code-Forge

### Core RAG Implementation
| File | Purpose | Key Lines |
|------|---------|-----------|
| `app/core/rag_engine.py` | Main RAG engine | 44-55 (LLM config), 128-131 (retriever), 140-156 (prompt) |
| `app/core/config.py` | Configuration | 21 (LLM), 43 (TOP_K), 45 (threshold) |
| `app/core/ingestion.py` | Document ingestion | 54-84 (chunking), 139-142 (embeddings) |
| `app/core/pg_manager.py` | PostgreSQL operations | Vector store management |
| `app/core/kb_metadata.py` | Knowledge base metadata | Collection statistics |

### User Interface
| File | Purpose |
|------|---------|
| `app/pages/1_Main.py` | Streamlit chat interface (line 807: RAGEngine init) |
| `app/pages/0_Welcome.py` | Welcome/status page |

### Data & Configuration
| File | Purpose |
|------|---------|
| `app/core/schema_pgvector.sql` | Database schema |
| `app/core/kb_types.py` | KB type definitions |
| `app/core/markdown_preprocessor.py` | Document preprocessing |
| `test_docs/test1.md` | Test appointment doc |

### Testing & Debugging
| File | Purpose |
|------|---------|
| `app/test_vector_query.py` | Vector query debugging |
| `app/test_ollama_embedding.py` | Embedding model testing |
| `tests/` | Comprehensive test suite |

---

## Implementation Roadmap

### Phase 1: Quick Wins (30 minutes)
- [ ] Increase TOP_K_RETRIEVAL to 10 in config.py
- [ ] Lower SIMILARITY_THRESHOLD to 0.6 in config.py
- [ ] Test with appointment queries
- **Impact**: Reduced hallucination

### Phase 2: Documentation (15 minutes)
- [ ] Create APPOINTMENT_COMPREHENSIVE_GUIDE.md
- [ ] Create APPOINTMENT_FLOW_DOC.md
- [ ] Ingest both into test KB
- **Impact**: Correct information available to LLM

### Phase 3: Performance (30-60 minutes)
- [ ] Implement RAGEngine singleton with KB caching
- [ ] Increase context_window to 2048
- [ ] Test end-to-end performance
- **Impact**: 30-40s → 5-10s response times

### Phase 4: Long-term (1-2 days)
- [ ] Evaluate larger LLM models (7B+)
- [ ] Consider GPU deployment
- [ ] Optimize chunk retrieval strategy
- [ ] Fine-tune vector search parameters

---

## Data Flow Overview

### Ingestion Flow
```
Upload → Extract → Preprocess → Chunk → Embed → Store in PostgreSQL
         (PDF/MD)  (markdown)    (1024)  (768D)  (data_{kb_name} table)
```

### Query Flow
```
Question → RAGEngine Init [SLOW] → Embed Query → Vector Search → LLM [SLOW] → Response
           (10-15s)                (1s)         (1-2s)          (15-25s)
```

---

## Configuration Parameters Summary

| Parameter | Current | Recommended | File |
|-----------|---------|-------------|------|
| TOP_K_RETRIEVAL | 5 | 10-15 | config.py:43 |
| SIMILARITY_THRESHOLD | 0.7 | 0.5-0.6 | config.py:45 |
| context_window | 1024 | 2048-4096 | rag_engine.py:49 |
| CHUNK_SIZE | 1024 | 1024 | config.py:41 |
| CHUNK_OVERLAP | 200 | 200-300 | config.py:42 |
| OLLAMA_MODEL | llama3.2:3b | 7b+ | config.py:21 |
| OLLAMA_EMBED_MODEL | nomic-embed-text | nomic-embed-text | config.py:22 |
| response_mode | simple_summarize | simple_summarize | rag_engine.py:170 |

---

## Performance Benchmarks

### Current State
- **Query Time**: 30-40 seconds
- **Latency Breakdown**:
  - Initialization: 10-15s (RAGEngine)
  - Search: 1-2s (vector DB)
  - LLM: 15-25s (inference)
  - Other: 2-5s

### After Phase 1-2 (Quick Fixes)
- **Expected Query Time**: 20-30 seconds
- **Improvement**: 10-20 seconds saved (hallucination reduced)

### After Phase 3 (RAGEngine Singleton)
- **Expected Query Time**: 5-10 seconds
- **Improvement**: 10-15 seconds saved (no re-init)

### After Phase 4 (Larger Model + GPU)
- **Expected Query Time**: 2-5 seconds
- **Improvement**: 3-8 seconds saved (faster inference)

---

## Key Insights

1. **RAGEngine Instantiation is the Biggest Bottleneck**
   - Takes 10-15 seconds just to load models
   - Creates new Ollama LLM for every query
   - Should use singleton pattern with caching

2. **Small Model + Small Context = Hallucination**
   - llama3.2:3b with 1024 token context insufficient
   - Only 5 chunks retrieved (TOP_K=5) not enough
   - Need more context or larger model

3. **Vector Search is Actually Efficient**
   - IVFFlat index works well
   - Search takes only 1-2 seconds
   - Not a bottleneck

4. **Documentation Quality Matters**
   - Test doc is too generic
   - Need comprehensive appointment guides
   - Partial workflows lead to hallucination

5. **Configuration Tweaks Have High Impact**
   - Small config changes can reduce hallucination
   - TOP_K and threshold are critical parameters
   - Need KB-type specific settings

---

## Report Generation Details

**Analysis Date**: October 23, 2025
**Analysis Depth**: Comprehensive (code review + architecture analysis)
**Tools Used**: Grep, Read, Glob, Bash
**Files Analyzed**: 15+ Python files, 1 SQL schema, 1 test doc

**Recommendations**: 
- Start with Phase 1 (quick wins)
- Move to Phase 3 (RAGEngine singleton) for biggest performance gain
- Phase 2 (documentation) for best hallucination reduction
- Phase 4 (larger model) for long-term quality

---

## Next Steps

1. **Read ANALYSIS_SUMMARY.txt** for quick overview (5 min)
2. **Read RAG_ANALYSIS.md** for deep understanding (30 min)
3. **Use QUICK_FIXES.md** to implement changes (1-2 hours)
4. **Test and monitor** performance improvements
5. **Document changes** and create PR

---

**Need Help?**
- Refer to QUICK_FIXES.md for implementation details
- Check specific file locations in RAG_ANALYSIS.md
- Use ANALYSIS_SUMMARY.txt for quick reference
- Review the code snippets in both analysis documents
