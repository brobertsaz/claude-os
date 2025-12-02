# Claude OS Smart Incremental Indexing System

## Overview

The analyze-project skill now includes an intelligent, multi-stage indexing strategy that gradually builds a complete project index without expensive full-reindex operations.

## How It Works

### Stage 1: Initial Analysis (Fast Setup)

When you run `analyze-project: <project_id>`:

1. **Quick setup** (~30-60 seconds for large projects)
   - Analyzes project structure and creates documentation
   - Registers 4 MCPs for on-demand loading
   - Indexes top 25 most important code files (source files prioritized)
   - Creates index state file (`.claude-os/.index_state`)
   - Installs smart git post-commit hook

2. **Result**
   - 400-500 code chunks indexed from priority files
   - Complete documentation for coding standards, architecture, practices
   - Foundation ready for AI assistance immediately

### Stage 2: Smart Incremental Expansion (Automatic)

Every time you commit:

1. **On EVERY commit**
   - Git hook tracks commit count
   - Changed files are marked for incremental indexing

2. **Every 10 commits**
   - Git hook triggers incremental indexer
   - ~30 previously unindexed files are indexed
   - Index state is updated in `.claude-os/.index_state`
   - No disruption to your workflow

### Timeline Example (Large Project: ~3,000 files)

```
Day 1:     analyze-project → 25 files indexed (0.75%)
Days 2-3:  10 commits → 25 + 30 = 55 files (1.65%)
Days 4-5:  20 commits → 55 + 60 = 115 files (3.46%)
Weeks 2-3: 100 commits → gradually reaches 400+ files (12%)
Months:    Index grows naturally to 500+ files (15%+)
```

## File Structure

### Key Files Created

```
.claude-os/
├── .index_state          # Tracks which files have been indexed
├── .commit_count         # Tracks commits since last expansion
├── project-profile/
│   ├── CODING_STANDARDS.md
│   ├── ARCHITECTURE.md
│   └── DEVELOPMENT_PRACTICES.md
```

### Git Hook

```
.git/hooks/post-commit    # Smart indexing trigger (executable)
```

## Configuration

### Expansion Frequency

Current default: Every 10 commits, index ~30 files

To customize, edit the git hook:

```bash
if [ $((COMMIT_COUNT % 10)) -eq 0 ]; then  # Change 10 to 5/15/20 as desired
    python3 "$INDEXER_PATH" "$PROJECT_ID" "$PROJECT_PATH" "$API_URL" 30  # Change 30 for batch size
```

### Batch Size

Current default: 30 files per expansion

Recommendations:

- **Large projects (3000+ files)**: 30-50 files per pass
- **Medium projects (500-3000 files)**: 50-100 files per pass
- **Small projects (<500 files)**: 100+ files per pass

## Key Design Decisions

### Why Not Index Everything Immediately?

1. **Performance**: Large projects (3000+ files) would take 5-10 minutes upfront
2. **UX**: Users want immediate feedback, not a blocking operation
3. **Incremental growth**: Mirrors natural development—as code changes, context grows

### Why Every 10 Commits?

1. **Timing**: 10 commits ≈ 2-3 hours of typical development
2. **Balance**: Frequent enough to build index quickly, rare enough to minimize overhead
3. **Deterministic**: Easy to predict and adjust

### Why Keep Unindexed Files?

1. **Memory**: Only recently used files need full context
2. **Speed**: Incremental scanning is much faster than full analysis
3. **Coverage**: Eventually, all important files get indexed as they're modified

## CLI Scripts

### incremental_indexer.py

Expands the project index with previously unindexed files.

```bash
python3 incremental_indexer.py <project_id> <project_path> [api_url] [batch_size]

# Example: Index next 50 files
python3 incremental_indexer.py 1 /path/to/your/project http://localhost:8051 50
```

Returns JSON with progress:

```json
{
  "indexed": 10,
  "chunks": 245,
  "progress": "35/3137",
  "percentage": 1,
  "status": "in_progress"
}
```

### Triggering Expansion Early

If you want to expand the index before the scheduled 10-commit mark:

```bash
# Manually trigger expansion
python3 ~/.claude/skills/analyze-project/incremental_indexer.py 1 /path/to/your/project
```

## Monitoring Progress

Check indexing progress:

```bash
# See current indexed files
cat .claude-os/.index_state

# See commit count (how many until next expansion)
cat .claude-os/.commit_count
```

## MCPs and Memory

### Native Memory

Save this to Claude's native memory for each project:

```
PROJECT: [Name] (ID: [ID])
TYPE: [Rails/Node/etc]
PATH: [path]

INDEXING STRATEGY:
- Initial: 25 key files indexed immediately
- Auto-expand: Every 10 commits, ~30 more files
- Incremental: Changed files indexed on each commit
- Timeline: Full index in ~6-10 weeks (typical dev pace)
```

### Loading MCPs On-Demand

When working on a project, you can load MCPs explicitly:

```
load myapp-project-profile     # Get coding standards & architecture
load myapp-project-index       # Search indexed code
load myapp-knowledge-docs      # Access project documentation
```

## Troubleshooting

### Hook Not Firing

1. Check hook is executable: `ls -la .git/hooks/post-commit`
2. Make hook executable: `chmod +x .git/hooks/post-commit`
3. Check incremental_indexer.py path in hook matches your system

### Index Not Growing

1. Check commit count: `cat .claude-os/.commit_count`
2. Make sure you're making actual commits (not `--amend`)
3. Manually trigger expansion: `python3 incremental_indexer.py 4 [project_path]`

### Too Many Files Being Found

The incremental indexer may find more files than expected if:

1. node_modules wasn't properly ignored (check git status)
2. Vendor directories have many code files
3. Generated files or caches have code-like extensions

Solution: Expand skip_dirs list in incremental_indexer.py for your project.

## Future Enhancements

Potential improvements to consider:

1. **Smart file prioritization**: Index files by change frequency
2. **Selective expansion**: Index only recently-modified files
3. **Parallel indexing**: Speed up expansion passes
4. **ML-based prioritization**: Index files most relevant to user queries
5. **Background indexing**: Run during idle time instead of on commits

---

**Built with Claude OS** - Intelligent context management for AI-assisted development
