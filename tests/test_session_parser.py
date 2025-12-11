"""
Tests for session parser and insight extractor.
"""

import json
import pytest
from pathlib import Path
from app.core.session_parser import (
    SessionParser,
    get_project_sessions_dir,
    list_session_files,
    Message,
    ToolCall,
    FileChange,
    SessionData
)


@pytest.fixture
def sample_session_file(tmp_path):
    """Create a sample session file for testing."""
    session_file = tmp_path / "test-session.jsonl"

    entries = [
        {
            "type": "summary",
            "summary": "Test session summary",
            "leafUuid": "abc123"
        },
        {
            "type": "user",
            "uuid": "msg-001",
            "parentUuid": None,
            "timestamp": "2025-12-11T10:00:00Z",
            "cwd": "/Users/test/Projects/myapp",
            "gitBranch": "main",
            "sessionId": "test-session",
            "message": {
                "role": "user",
                "content": "Hello, can you help me with testing?"
            }
        },
        {
            "type": "assistant",
            "uuid": "msg-002",
            "parentUuid": "msg-001",
            "timestamp": "2025-12-11T10:00:05Z",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Of course! I can help you with testing."}
                ]
            }
        },
        {
            "type": "user",
            "uuid": "msg-003",
            "parentUuid": "msg-002",
            "timestamp": "2025-12-11T10:00:10Z",
            "message": {
                "role": "user",
                "content": "Can you write a test for me?"
            }
        },
        {
            "type": "assistant",
            "uuid": "msg-004",
            "parentUuid": "msg-003",
            "timestamp": "2025-12-11T10:00:15Z",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "I'll write a test for you."},
                    {
                        "type": "tool_use",
                        "id": "tool-001",
                        "name": "Write",
                        "input": {
                            "file_path": "/Users/test/Projects/myapp/test.py",
                            "content": "def test_example():\n    pass"
                        }
                    }
                ]
            }
        },
        {
            "type": "file-history-snapshot",
            "messageId": "msg-004",
            "snapshot": {
                "messageId": "msg-004",
                "timestamp": "2025-12-11T10:00:20Z",
                "trackedFileBackups": {
                    "/Users/test/Projects/myapp/test.py": {"content": "def test_example():\n    pass"}
                }
            }
        }
    ]

    with open(session_file, 'w') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')

    return session_file


def test_session_parser_init(sample_session_file):
    """Test SessionParser initialization."""
    parser = SessionParser(str(sample_session_file))
    assert parser.path == sample_session_file
    assert parser.session_id == "test-session"


def test_session_parser_parse(sample_session_file):
    """Test parsing a session file."""
    parser = SessionParser(str(sample_session_file))
    session_data = parser.parse()

    # Check basic metadata
    assert session_data.session_id == "test-session"
    assert session_data.cwd == "/Users/test/Projects/myapp"
    assert session_data.git_branch == "main"
    assert session_data.total_entries == 6

    # Check messages (2 user + 2 assistant = 4 messages)
    assert len(session_data.messages) == 4
    assert session_data.messages[0].role == "user"
    assert "help me with testing" in session_data.messages[0].content
    assert session_data.messages[1].role == "assistant"
    assert "help you with testing" in session_data.messages[1].content

    # Check tool calls
    assert len(session_data.tool_calls) == 1
    assert session_data.tool_calls[0].tool_name == "Write"
    assert session_data.tool_calls[0].input_data["file_path"] == "/Users/test/Projects/myapp/test.py"

    # Check file changes
    assert len(session_data.file_changes) == 1
    assert session_data.file_changes[0].file_path == "/Users/test/Projects/myapp/test.py"


def test_session_parser_get_conversation(sample_session_file):
    """Test getting conversation messages."""
    parser = SessionParser(str(sample_session_file))
    messages = parser.get_conversation()

    assert len(messages) == 4  # 2 user + 2 assistant messages
    assert all(isinstance(msg, Message) for msg in messages)
    assert messages[0].role == "user"
    assert messages[1].role == "assistant"


def test_session_parser_get_summary(sample_session_file):
    """Test generating summary for extraction."""
    parser = SessionParser(str(sample_session_file))
    summary = parser.get_summary_for_extraction()

    assert "test-session" in summary
    assert "/Users/test/Projects/myapp" in summary
    assert "main" in summary
    assert "help me with testing" in summary
    assert "Write" in summary


def test_get_project_sessions_dir():
    """Test encoding project path to sessions directory."""
    project_path = "/Users/test/Projects/myapp"
    sessions_dir = get_project_sessions_dir(project_path)

    # Leading hyphen is preserved from the path encoding
    expected = Path.home() / ".claude" / "projects" / "-Users-test-Projects-myapp"
    assert sessions_dir == expected


def test_list_session_files_empty_dir(tmp_path):
    """Test listing sessions when directory doesn't exist."""
    fake_project = str(tmp_path / "nonexistent")
    sessions = list_session_files(fake_project)
    assert sessions == []


def test_session_parser_invalid_file():
    """Test parser with non-existent file."""
    with pytest.raises(FileNotFoundError):
        parser = SessionParser("/path/to/nonexistent/file.jsonl")


def test_session_parser_malformed_json(tmp_path):
    """Test parser handles malformed JSON gracefully."""
    session_file = tmp_path / "malformed.jsonl"

    with open(session_file, 'w') as f:
        f.write('{"type": "user", "content": "valid"}\n')
        f.write('this is not json\n')
        f.write('{"type": "assistant", "content": "also valid"}\n')

    parser = SessionParser(str(session_file))
    session_data = parser.parse()

    # Should parse the valid lines, skip the malformed one
    assert session_data.total_entries == 2


def test_session_data_defaults():
    """Test SessionData dataclass defaults."""
    data = SessionData(
        session_id="test",
        session_path="/path/to/session.jsonl"
    )

    assert data.messages == []
    assert data.tool_calls == []
    assert data.file_changes == []
    assert data.start_time is None
    assert data.end_time is None
    assert data.total_entries == 0


@pytest.mark.asyncio
async def test_insight_extractor_import():
    """Test that InsightExtractor can be imported."""
    from app.core.insight_extractor import InsightExtractor, Insight

    # Just verify imports work
    assert InsightExtractor is not None
    assert Insight is not None


def test_session_parser_truncation(tmp_path):
    """Test that very long sessions are truncated in summary."""
    session_file = tmp_path / "long-session.jsonl"

    # Create a very long message
    long_content = "A" * 2000

    entries = [
        {
            "type": "user",
            "uuid": "msg-001",
            "parentUuid": None,
            "timestamp": "2025-12-11T10:00:00Z",
            "cwd": "/test",
            "sessionId": "long-session",
            "message": {
                "role": "user",
                "content": long_content
            }
        }
    ]

    with open(session_file, 'w') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')

    parser = SessionParser(str(session_file))
    summary = parser.get_summary_for_extraction(max_tokens=100)

    # Summary should be shorter than the original content
    # (header adds overhead, so just verify truncation occurred)
    assert len(summary) < len(long_content)
    assert "[... truncated ...]" in summary
