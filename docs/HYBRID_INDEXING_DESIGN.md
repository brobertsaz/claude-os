# Claude OS Hybrid Indexing System Design

**Author:** Claude (for Claude!)
**Date:** 2025-10-31
**Status:** Design Phase

## Problem Statement

Current Claude OS indexing is too slow for large codebases:
- example-app project (Rails, 10k+ files) = 3-5 hours to index
- Generates embeddings for EVERY file and chunk
- Must complete before Claude can start working
- Blocks productive coding sessions

## Inspiration: Aider's Approach

Aider solves this with tree-sitter based structural indexing:
- Parse files with tree-sitter (no LLM calls)
- Extract symbols only (signatures, not full content)
- Build dependency graph + PageRank scoring
- Token-budget aware repo map
- **Result: 10k files indexed in ~30 seconds**

## Solution: Hybrid + Two-Phase System

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Claude OS Indexing v2.0                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Phase 1: Structural Index (tree-sitter)                    │
│  ├─ Speed: 30 seconds for 10k files                         │
│  ├─ Output: Symbol map + dependency graph                   │
│  ├─ Storage: {project}-code_structure KB                    │
│  ├─ Use: "Where is X?", "What depends on Y?"               │
│  └─ Ready: Immediately usable                               │
│                                                              │
│  Phase 2: Semantic Index (selective embeddings)             │
│  ├─ Speed: 20-30 minutes (vs 3-5 hours)                    │
│  ├─ Scope: Top 20% by PageRank + docs + recent changes     │
│  ├─ Storage: {project}-project_index KB                     │
│  ├─ Use: "How does auth work?", "Explain this pattern"     │
│  └─ Ready: Background job, optional                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Technical Design

### 1. Tree-Sitter Indexer Module

**File:** `app/core/tree_sitter_indexer.py`

**Key Classes:**

```python
class Tag:
    """Represents a code symbol (class, function, variable)."""
    file: str
    name: str
    kind: str  # 'class', 'function', 'method', 'variable'
    line: int
    signature: str
    importance: float  # PageRank score

class DependencyGraph:
    """NetworkX MultiDiGraph of file dependencies."""
    nodes: List[str]  # Files
    edges: List[Tuple[str, str, dict]]  # (from_file, to_file, metadata)

class TreeSitterIndexer:
    """Main indexer using tree-sitter."""

    def parse_file(file_path: str, language: str) -> List[Tag]:
        """Parse file and extract symbols."""

    def build_graph(tags: List[Tag]) -> DependencyGraph:
        """Build dependency graph from tags."""

    def rank_symbols(graph: DependencyGraph, personalization: dict) -> List[Tag]:
        """Apply PageRank to score symbol importance."""

    def generate_repo_map(ranked_tags: List[Tag], token_budget: int) -> str:
        """Create compact repo map fitting token budget."""

    def index_directory(project_path: str) -> RepoMap:
        """Main entry point: index entire directory."""
```

**Dependencies:**

```python
tree-sitter==0.21.0
py-tree-sitter-languages==1.10.2  # Pre-built binaries for 40+ languages
networkx==3.2.1  # For dependency graphs + PageRank
```

**Caching Strategy:**

```python
# SQLite cache for parsed tags (like Aider)
cache_key = f"{file_path}:{mtime}:{size}"
if cache.get(cache_key):
    return cached_tags
else:
    tags = parse_file(file_path)
    cache.set(cache_key, tags)
    return tags
```

### 2. PageRank Scoring

**Algorithm:** Same as Aider's approach

```python
def rank_symbols(graph, personalization=None):
    """
    Apply PageRank with personalization.

    Personalization factors:
    - Files in chat context: 50x boost
    - Recently modified files: 10x boost
    - Well-named identifiers (8+ chars): 10x boost
    - Referenced identifiers: 5x boost
    """
    if personalization is None:
        personalization = {}

    ranked = nx.pagerank(
        graph,
        weight="weight",
        personalization=personalization,
        max_iter=100
    )

    return sorted(ranked.items(), key=lambda x: x[1], reverse=True)
```

### 3. Token-Budget Binary Search

**Goal:** Fit most important symbols in 1024-4096 token budget

```python
def fit_to_budget(ranked_tags, max_tokens=1024):
    """
    Binary search to find max tags fitting token budget.
    Accept within 15% error margin.
    """
    lower, upper = 0, len(ranked_tags)
    best_tree = ""
    best_tokens = 0
    ok_err = 0.15  # 15% error margin

    while lower <= upper:
        mid = (lower + upper) // 2
        tree = format_repo_map(ranked_tags[:mid])
        num_tokens = count_tokens(tree)

        if num_tokens <= max_tokens:
            if num_tokens > best_tokens:
                best_tree = tree
                best_tokens = num_tokens
            lower = mid + 1
        else:
            upper = mid - 1

        # Accept if within error margin
        if abs(num_tokens - max_tokens) / max_tokens <= ok_err:
            break

    return best_tree
```

### 4. Selective Semantic Indexing

**Strategy:** Only embed high-value files

```python
def select_files_for_embedding(ranked_tags, project_path):
    """
    Select files for semantic indexing based on importance.

    Criteria:
    - Top 20% by PageRank score
    - All documentation files (*.md, *.txt)
    - Recently modified (git log --since="30 days ago")
    - User-specified critical paths
    """
    files_to_embed = set()

    # Top 20% by PageRank
    top_20_percent = int(len(ranked_tags) * 0.2)
    for tag in ranked_tags[:top_20_percent]:
        files_to_embed.add(tag.file)

    # All docs
    docs = find_files(project_path, patterns=["*.md", "*.txt", "*.rst"])
    files_to_embed.update(docs)

    # Recently modified
    recent = git_recent_files(project_path, days=30)
    files_to_embed.update(recent)

    return list(files_to_embed)
```

### 5. New API Endpoints

**File:** `mcp_server/server.py`

```python
@app.post("/api/kb/{kb_name}/index-structural")
async def index_structural(kb_name: str, project_path: str):
    """
    Phase 1: Fast tree-sitter structural indexing.
    Returns in ~30 seconds for 10k files.
    """
    indexer = TreeSitterIndexer()
    repo_map = indexer.index_directory(project_path)

    # Store in code_structure KB
    structure_kb = f"{kb_name}-code_structure"
    save_repo_map(structure_kb, repo_map)

    return {
        "status": "success",
        "repo_map_size": len(repo_map.tags),
        "time_taken": "30s",
        "ready": True
    }

@app.post("/api/kb/{kb_name}/index-semantic")
async def index_semantic(kb_name: str, project_path: str, selective: bool = True):
    """
    Phase 2: Semantic embedding (optional, background job).
    If selective=True, only embeds top 20% + docs.
    """
    if selective:
        # Get structural index first
        structure_kb = f"{kb_name}-code_structure"
        repo_map = load_repo_map(structure_kb)
        files = select_files_for_embedding(repo_map.tags, project_path)
    else:
        files = find_all_code_files(project_path)

    # Queue background job
    job = queue_embedding_job(kb_name, files)

    return {
        "status": "queued",
        "job_id": job.id,
        "files_to_embed": len(files),
        "estimated_time": f"{len(files) * 0.2 / 60:.0f} minutes"
    }

@app.get("/api/kb/{kb_name}/repo-map")
async def get_repo_map(
    kb_name: str,
    token_budget: int = 1024,
    personalization: dict = None
):
    """
    Get compact repo map for Claude's prompt context.
    """
    structure_kb = f"{kb_name}-code_structure"
    repo_map = load_repo_map(structure_kb)

    # Apply personalization if provided
    if personalization:
        repo_map.rerank(personalization)

    # Fit to token budget
    compact_map = fit_to_budget(repo_map.tags, token_budget)

    return {
        "repo_map": compact_map,
        "token_count": count_tokens(compact_map),
        "total_symbols": len(repo_map.tags)
    }
```

## Query Strategy

**How Claude uses the hybrid index:**

### 1. Session Start

```
Claude starts session:
  1. Load {project}-code_structure repo map (instant)
  2. Include in my system prompt as context
  3. I now know "what exists" in the codebase
  4. Ready to code!
```

### 2. Structural Queries

```
User: "Where is the User authentication defined?"

Claude:
  1. Search code_structure KB (instant)
  2. Find: User#authenticate in app/models/user.rb:45
  3. Return answer immediately
```

### 3. Semantic Queries

```
User: "How does the authentication flow work?"

Claude:
  1. Check if project_index has semantic embeddings
  2. If yes: Semantic search for "authentication flow"
  3. If no: Use repo map + read relevant files directly
  4. Synthesize answer
```

### 4. Adaptive Strategy

```python
def query_codebase(query: str, kb_name: str):
    """
    Smart query routing based on query type.
    """
    if is_needle_query(query):  # "Where is X defined?"
        return search_structural_index(kb_name, query)

    elif has_semantic_index(kb_name):
        return search_semantic_index(kb_name, query)

    else:
        # Fall back to repo map + direct file reads
        repo_map = get_repo_map(kb_name)
        relevant_files = identify_relevant_files(repo_map, query)
        return read_and_synthesize(relevant_files, query)
```

## Updated `/claude-os-init` Flow

**New initialization sequence:**

```
/claude-os-init

1. Gather project info (as before)

2. Create knowledge bases:
   ✓ {project}-code_structure      # NEW: Structural index
   ✓ {project}-project_index        # Semantic (selective)
   ✓ {project}-project_profile
   ✓ {project}-knowledge_docs
   ✓ {project}-project_memories

3. Phase 1: Structural Indexing (FAST)
   → "Analyzing codebase structure with tree-sitter..."
   → Parse 10,000 files...
   → Build dependency graph...
   → Compute PageRank scores...
   ✓ Done in 30 seconds!

   → "Repo map created! You can start coding now."

4. Ask: "Run semantic indexing in background? (optional)"
   [Yes] → Queue background job
   [No]  → Skip, can run later
   [Top 20% only] → Selective indexing (recommended)

5. If background indexing:
   → "Semantic indexing queued (20 minutes estimated)"
   → "You can start coding now, indexing runs in background"
   → Notification when complete

6. Generate CLAUDE.md (as before)

7. Done! Ready to code with instant context.
```

## Performance Comparison

### Before (Current System)

```
example-app Project (10,000 Ruby files):
- Index time: 3-5 hours
- Embeddings: 100,000+ chunks
- Must complete before coding
- High Ollama resource usage
- Blocks productive work
```

### After (Hybrid System)

```
example-app Project (10,000 Ruby files):

Phase 1 (Structural):
- Index time: 30 seconds
- No embeddings needed
- Ready immediately
- Low CPU/memory usage
- ✓ Can start coding now!

Phase 2 (Semantic, optional):
- Index time: 20-30 minutes (only top 20% + docs)
- Embeddings: ~20,000 chunks (80% reduction)
- Runs in background
- Can code while it runs
- ✓ Best of both worlds!
```

## Migration Strategy

### New Projects

- Use hybrid indexing by default
- Phase 1 always runs (fast)
- Phase 2 optional but recommended

### Existing Projects

- Add migration command: `/claude-os-reindex`
- Preserves existing semantic index
- Adds structural index alongside
- No data loss

## Success Metrics

- ✅ **Time to first query:** 30 seconds (vs 3-5 hours)
- ✅ **Embedding cost:** 80% reduction (selective indexing)
- ✅ **Context quality:** Equal or better (PageRank scoring)
- ✅ **Query speed:** Faster (structural index is instant)
- ✅ **User satisfaction:** Can start coding immediately

## Future Enhancements

1. **Incremental updates:** Re-index only changed files
2. **Real-time watching:** Auto-update on file changes
3. **Smart re-ranking:** Learn from query patterns
4. **Cross-project patterns:** "I've seen this before in project X"
5. **Team knowledge:** Share structural insights

## References

- [Aider repomap.py implementation](https://github.com/Aider-AI/aider/blob/main/aider/repomap.py)
- [Tree-sitter documentation](https://tree-sitter.github.io/)
- [NetworkX PageRank](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.link_analysis.pagerank_alg.pagerank.html)
- [py-tree-sitter-languages](https://github.com/grantjenks/py-tree-sitter-languages)

---

**Built by Claude, for Claude, to make Claude unstoppable! 🚀**
