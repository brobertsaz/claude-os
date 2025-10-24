# Code-Forge RAG Issues - Quick Fix Guide

## Critical Issues Summary

### Issue 1: Slow Response Times (30-40 seconds)
**Root Cause**: RAGEngine instantiated per query + small LLM on CPU

**Breakdown**:
- 10-15s: RAGEngine initialization (Ollama LLM + embeddings + PGVectorStore)
- 15-25s: LLM inference (llama3.2:3b generating response)
- 1-2s: Vector search (actually efficient)
- 2-5s: Other overhead

**Quick Fixes** (in order of impact):
1. **Implement RAGEngine Singleton** (save 10-15 seconds)
   - Cache per KB name in Streamlit session state
   - File: `/Users/iamanmp/Projects/code-forge/app/pages/1_Main.py` line 807

2. **Increase Context Window** (save inference time, improve quality)
   - File: `/Users/iamanmp/Projects/code-forge/app/core/rag_engine.py` line 49
   - Change: `context_window=1024` → `context_window=2048` or `4096`
   - Trade-off: Slightly slower but better results

3. **Use Larger LLM Model** (save 5-10 seconds)
   - File: `/Users/iamanmp/Projects/code-forge/app/core/config.py` line 21
   - Change: `OLLAMA_MODEL: "llama3.2:3b"` → `"llama2:7b"` or larger
   - Requires: More memory/GPU

---

### Issue 2: Hallucination About "Advanced Appointment Settings"
**Root Cause**: Insufficient context + small model + missing documentation

**Evidence**:
- TOP_K=5 retrieval insufficient for complete workflow understanding
- Similarity threshold 0.7 filters out potentially relevant chunks  
- Context window 1024 tokens too small for 5 chunks + instructions
- Documentation is incomplete/generic

**Quick Fixes** (in order of impact):

1. **Increase TOP_K_RETRIEVAL** (HIGH PRIORITY)
   - File: `/Users/iamanmp/Projects/code-forge/app/core/config.py` line 43
   - Change: `TOP_K_RETRIEVAL: int = 5` → `10` or `15`
   - Effect: More context = less hallucination
   - Cost: Negligible (~200ms)

2. **Lower SIMILARITY_THRESHOLD for Documentation KB** (HIGH PRIORITY)
   - File: `/Users/iamanmp/Projects/code-forge/app/core/config.py` line 45
   - Change: `SIMILARITY_THRESHOLD: float = 0.7` → `0.5` or `0.6`
   - Effect: Include more potentially relevant chunks
   - Cost: Might retrieve some irrelevant chunks
   - Make KB-type specific if possible

3. **Add Complete Appointment Documentation** (HIGH PRIORITY)
   - Create: `APPOINTMENT_COMPREHENSIVE_GUIDE.md` with:
     - Complete workflow steps (user, provider, admin perspectives)
     - All available settings/options
     - Edge cases and error handling
     - Examples
   - Create: `APPOINTMENT_FLOW_DOC.md` with flowcharts and state diagrams
   - Ingest both into the knowledge base

4. **Increase Context Window** (MEDIUM PRIORITY)
   - File: `/Users/iamanmp/Projects/code-forge/app/core/rag_engine.py` line 49
   - Change: `context_window=1024` → `2048` or `4096`
   - Effect: More space for context + instructions

5. **Use Larger LLM** (MEDIUM PRIORITY)
   - Better understanding with larger model
   - But requires more resources

---

## File Locations for Quick Fixes

| Issue | File | Line(s) | Change |
|-------|------|---------|--------|
| RAGEngine instantiation | `app/pages/1_Main.py` | 807 | Use singleton caching |
| TOP_K_RETRIEVAL | `app/core/config.py` | 43 | 5 → 10-15 |
| SIMILARITY_THRESHOLD | `app/core/config.py` | 45 | 0.7 → 0.5-0.6 |
| Context window | `app/core/rag_engine.py` | 49 | 1024 → 2048-4096 |
| LLM model | `app/core/config.py` | 21 | llama3.2:3b → larger |
| Appointment docs | `test_docs/` | - | Create guides |

---

## Implementation Priority Matrix

### Quick Wins (< 30 min to implement, high impact)

1. **Increase TOP_K_RETRIEVAL to 10**
   - Change one line in config.py
   - Test if hallucination reduces
   - Impact: HIGH on hallucination

2. **Lower SIMILARITY_THRESHOLD to 0.6**
   - Change one line in config.py
   - May need tuning
   - Impact: MEDIUM to HIGH on hallucination

3. **Add appointment documentation files**
   - Create MD files with complete info
   - Ingest into KB
   - Impact: HIGH (provides correct info)

### Medium Effort (1-2 hours)

4. **Implement RAGEngine singleton**
   - Wrap initialization in singleton factory
   - Cache by KB name
   - Impact: HIGH on performance (10-15s)

5. **Increase context_window to 2048**
   - Change rag_engine.py
   - Slight perf hit, better quality
   - Impact: MEDIUM on both issues

### Long Term (architecture changes)

6. **Use larger LLM or GPU**
   - Deploy 7B+ model
   - Or add GPU support
   - Impact: HIGH on both issues
   - Cost: More resources

---

## Testing Changes

After each change, test with:

```bash
# Test specific query about appointments
curl -X POST http://localhost:8501/api/chat \
  -H "Content-Type: application/json" \
  -d '{"kb_name": "appointments", "query": "How do appointments work?", "settings": {}}'
```

Check for:
1. Response time < 15s (target after RAGEngine caching)
2. No hallucination about "advanced settings"
3. Proper citations to APPOINTMENT_COMPREHENSIVE_GUIDE.md
4. Complete workflow explanation

---

## Configuration Change Checklist

- [ ] Increase TOP_K_RETRIEVAL: 5 → 10
- [ ] Lower SIMILARITY_THRESHOLD: 0.7 → 0.6
- [ ] Increase context_window: 1024 → 2048
- [ ] Create APPOINTMENT_COMPREHENSIVE_GUIDE.md
- [ ] Create APPOINTMENT_FLOW_DOC.md
- [ ] Ingest appointment docs
- [ ] Test with sample queries
- [ ] Monitor response times
- [ ] Check for hallucinations
- [ ] Implement RAGEngine singleton
- [ ] Performance test end-to-end

---

## Performance Monitoring

**Before changes**:
```
Query time: 30-40s
├─ Initialization: 10-15s
├─ Search: 1-2s
├─ LLM: 15-25s
└─ Other: 2-5s
```

**After RAGEngine singleton + config changes**:
```
Query time (target): 5-15s
├─ Initialization: <1s (cached)
├─ Search: 1-2s
├─ LLM: 3-10s (larger context, better model)
└─ Other: 1-2s
```

---

## Key Learnings

1. **RAGEngine initialization is EXPENSIVE**
   - Takes 10-15 seconds just to load models
   - Must be cached/singleton

2. **Context window directly impacts quality**
   - 1024 tokens insufficient for 5+ chunks
   - Increase to 2048+ for dense documentation

3. **Retrieval parameters matter**
   - TOP_K=5 is too restrictive
   - Threshold=0.7 filters relevant chunks
   - These are KB-type dependent

4. **Documentation quality is critical**
   - Hallucination partly due to incomplete docs
   - Need comprehensive guides with all details
   - Examples and edge cases help

5. **Small models are prone to hallucination**
   - llama3.2:3b with 1024 context is challenging
   - 7B+ models or larger context help significantly

---

**Last Updated**: 2025-10-23
**Status**: Ready for implementation
