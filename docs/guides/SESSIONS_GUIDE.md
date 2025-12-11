# Session Parsing & Insights Guide

**Parse Claude Code sessions and extract insights automatically.**

---

## Overview

Claude Code stores conversation history in `.jsonl` session files located at:
```
~/.claude/projects/{encoded-project-path}/{session-id}.jsonl
```

Claude OS can parse these files to:
- Extract conversations, tool calls, and file changes
- Generate summaries for context loading
- Extract insights (patterns, decisions, blockers)
- Build analytics on your development sessions

---

## Session File Format

Claude Code session files are JSON Lines format with various entry types:

```jsonl
{"type": "summary", "summary": "...", "leafUuid": "..."}
{"type": "user", "uuid": "msg-001", "message": {"role": "user", "content": "..."}}
{"type": "assistant", "uuid": "msg-002", "message": {"role": "assistant", "content": [...]}}
{"type": "file-history-snapshot", "messageId": "...", "snapshot": {...}}
```

### Entry Types

| Type | Description |
|------|-------------|
| `summary` | Session summary (usually at start) |
| `user` | User message |
| `assistant` | Assistant response (may contain tool_use) |
| `file-history-snapshot` | File changes made during session |

---

## Using the Session Parser

### Python API

```python
from app.core.session_parser import (
    SessionParser,
    get_project_sessions_dir,
    list_session_files
)

# Find sessions for a project
project_path = "/Users/me/Projects/myapp"
sessions = list_session_files(project_path)
# Returns: ['/path/to/session1.jsonl', '/path/to/session2.jsonl']

# Parse a session
parser = SessionParser(sessions[0])
session_data = parser.parse()

# Access parsed data
print(f"Session ID: {session_data.session_id}")
print(f"Messages: {len(session_data.messages)}")
print(f"Tool Calls: {len(session_data.tool_calls)}")
print(f"File Changes: {len(session_data.file_changes)}")
print(f"Duration: {session_data.start_time} to {session_data.end_time}")

# Get conversation messages
messages = parser.get_conversation()
for msg in messages:
    print(f"{msg.role}: {msg.content[:100]}...")

# Get summary for LLM processing
summary = parser.get_summary_for_extraction(max_tokens=500)
print(summary)
```

### REST API

```bash
# List sessions for a project
curl "http://localhost:8051/api/sessions?project_path=/path/to/project&limit=10"

# Get session details
curl "http://localhost:8051/api/sessions/abc123?project_path=/path/to/project"

# Get session summary
curl "http://localhost:8051/api/sessions/abc123/summary?project_path=/path/to/project&max_tokens=500"
```

---

## Session Data Structure

### SessionData

```python
@dataclass
class SessionData:
    session_id: str
    session_path: str
    messages: List[Message]
    tool_calls: List[ToolCall]
    file_changes: List[FileChange]
    start_time: Optional[str]
    end_time: Optional[str]
    git_branch: Optional[str]
    cwd: Optional[str]
    total_entries: int
```

### Message

```python
@dataclass
class Message:
    role: str           # "user" or "assistant"
    content: str        # Message content
    timestamp: str      # ISO timestamp
    uuid: str           # Message UUID
    parent_uuid: Optional[str]
```

### ToolCall

```python
@dataclass
class ToolCall:
    tool_name: str      # e.g., "Read", "Write", "Bash"
    timestamp: str
    uuid: str
    parent_uuid: Optional[str]
    input_data: Dict    # Tool input parameters
```

### FileChange

```python
@dataclass
class FileChange:
    file_path: str
    timestamp: str
    message_id: str     # Which message triggered this change
```

---

## Insight Extraction

The InsightExtractor analyzes sessions to identify:

- **Patterns** - Recurring solutions and approaches
- **Decisions** - Architecture and implementation choices
- **Blockers** - Problems encountered and how they were resolved
- **Discoveries** - New learnings about the codebase

### Using InsightExtractor

```python
from app.core.insight_extractor import InsightExtractor, Insight

# Create extractor with Ollama
extractor = InsightExtractor(
    ollama_host="http://localhost:11434",
    model="llama3.1:8b"
)

# Extract insights from a session
parser = SessionParser("/path/to/session.jsonl")
summary = parser.get_summary_for_extraction(max_tokens=1000)

insights = await extractor.extract_insights(summary)

for insight in insights:
    print(f"Type: {insight.insight_type}")
    print(f"Title: {insight.title}")
    print(f"Content: {insight.content}")
    print(f"Tags: {insight.tags}")
    print("---")
```

### Insight Types

| Type | Description |
|------|-------------|
| `pattern` | A reusable solution or approach |
| `decision` | An architectural or implementation choice |
| `blocker` | A problem that was encountered |
| `discovery` | Something new learned about the codebase |

### Saving Insights to Memory

```python
from app.core.sqlite_manager import get_sqlite_manager

db = get_sqlite_manager()

for insight in insights:
    # Save to project memories KB
    db.add_document(
        kb_name=f"{project_name}-project_memories",
        content=f"# {insight.title}\n\n{insight.content}",
        filename=f"insight-{insight.insight_type}-{timestamp}.md",
        metadata={
            "type": insight.insight_type,
            "tags": insight.tags,
            "session_id": session_data.session_id
        }
    )
```

---

## Session Summary Format

The `get_summary_for_extraction()` method generates a structured summary:

```
# Session: abc123
Project: /Users/me/Projects/myapp
Branch: feature-auth
Duration: 2025-12-11T10:00:00Z to 2025-12-11T11:30:00Z

## Conversation (24 messages)
USER: Help me implement user authentication...
ASSISTANT: I'll help you implement authentication. Let me start by...
USER: Can you add password hashing?
ASSISTANT: Of course! I'll use bcrypt for secure password hashing...

## Tool Calls
- Read: /Users/me/Projects/myapp/src/auth.py
- Write: /Users/me/Projects/myapp/src/auth.py
- Read: /Users/me/Projects/myapp/tests/test_auth.py
- Write: /Users/me/Projects/myapp/tests/test_auth.py
- Bash: pytest tests/test_auth.py

## File Changes
- /Users/me/Projects/myapp/src/auth.py
- /Users/me/Projects/myapp/tests/test_auth.py
```

---

## Project Sessions Directory

Claude Code encodes project paths for the sessions directory:

```
/Users/me/Projects/myapp
→ ~/.claude/projects/-Users-me-Projects-myapp/
```

The encoding:
1. Replaces `/` with `-`
2. Keeps the leading `-` (from the initial `/`)

### Finding Sessions

```python
from app.core.session_parser import get_project_sessions_dir, list_session_files

# Get sessions directory for a project
sessions_dir = get_project_sessions_dir("/Users/me/Projects/myapp")
# Returns: ~/.claude/projects/-Users-me-Projects-myapp

# List all session files
sessions = list_session_files("/Users/me/Projects/myapp")
# Returns sorted list of .jsonl files (newest first)
```

---

## Use Cases

### 1. Load Context at Session Start

```python
# At session start, load recent session insights
sessions = list_session_files(project_path)
if sessions:
    parser = SessionParser(sessions[0])
    summary = parser.get_summary_for_extraction(max_tokens=500)
    # Use summary to prime Claude with recent context
```

### 2. Build Session Analytics

```python
# Analyze all sessions for a project
sessions = list_session_files(project_path)
stats = {
    "total_sessions": len(sessions),
    "total_messages": 0,
    "total_tool_calls": 0,
    "tools_used": {}
}

for session_path in sessions:
    parser = SessionParser(session_path)
    data = parser.parse()

    stats["total_messages"] += len(data.messages)
    stats["total_tool_calls"] += len(data.tool_calls)

    for tc in data.tool_calls:
        stats["tools_used"][tc.tool_name] = \
            stats["tools_used"].get(tc.tool_name, 0) + 1
```

### 3. Extract and Save Patterns

```python
# Extract insights from recent sessions
extractor = InsightExtractor()

for session_path in sessions[:5]:  # Last 5 sessions
    parser = SessionParser(session_path)
    summary = parser.get_summary_for_extraction()

    insights = await extractor.extract_insights(summary)

    for insight in insights:
        if insight.insight_type == "pattern":
            # Save to memories KB
            save_to_memories(project_name, insight)
```

### 4. Debug Failed Sessions

```python
# Find sessions with errors
for session_path in sessions:
    parser = SessionParser(session_path)
    data = parser.parse()

    # Look for error patterns in messages
    for msg in data.messages:
        if "error" in msg.content.lower() or "failed" in msg.content.lower():
            print(f"Session {data.session_id} may have errors")
            print(f"  Message: {msg.content[:100]}...")
            break
```

---

## Configuration

### Environment Variables

```bash
# Ollama settings for insight extraction
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

### Truncation Settings

Large sessions are automatically truncated for LLM processing:

```python
# Default: 500 tokens (~2000 chars)
summary = parser.get_summary_for_extraction(max_tokens=500)

# For more context
summary = parser.get_summary_for_extraction(max_tokens=2000)
```

---

## Troubleshooting

### "No sessions found"
- Verify project path is correct
- Check that sessions exist: `ls ~/.claude/projects/`
- The encoded path includes leading hyphen: `-Users-me-Projects-myapp`

### "Failed to parse session"
- Session file may be corrupted
- Check for valid JSON on each line
- Malformed lines are skipped automatically

### "Insight extraction failed"
- Verify Ollama is running: `ollama list`
- Check model is available: `ollama pull llama3.1:8b`
- Check logs for API errors

---

## API Reference

### REST Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sessions` | GET | List project sessions |
| `/api/sessions/{id}` | GET | Get session details |
| `/api/sessions/{id}/summary` | GET | Get session summary |

### MCP Tools

| Tool | Description |
|------|-------------|
| `mcp__code-forge__list_sessions` | List sessions for a project |
| `mcp__code-forge__get_session` | Get session details |
| `mcp__code-forge__get_session_summary` | Get formatted summary |

---

**See Also:**
- [API Reference](../API_REFERENCE.md) - Session API endpoints
- [Self Learning System](../SELF_LEARNING_SYSTEM.md) - How Claude learns
- [README](../../README.md) - Full Claude OS documentation
