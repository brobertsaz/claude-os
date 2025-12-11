"""
Session Parser for Claude Code built-in session files.
Parses .jsonl session files from ~/.claude/projects/ and extracts structured data.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """A user or assistant message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    uuid: str
    parent_uuid: Optional[str] = None


@dataclass
class ToolCall:
    """A tool call made during the session."""
    tool_name: str
    timestamp: str
    uuid: str
    parent_uuid: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None


@dataclass
class FileChange:
    """A file modification tracked during the session."""
    file_path: str
    timestamp: str
    message_id: str


@dataclass
class SessionData:
    """Parsed session data."""
    session_id: str
    session_path: str
    messages: List[Message] = field(default_factory=list)
    tool_calls: List[ToolCall] = field(default_factory=list)
    file_changes: List[FileChange] = field(default_factory=list)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    git_branch: Optional[str] = None
    cwd: Optional[str] = None
    total_entries: int = 0


class SessionParser:
    """Parse Claude Code built-in session files (.jsonl format)."""

    def __init__(self, session_path: str):
        """
        Initialize parser with path to session file.

        Args:
            session_path: Path to .jsonl session file
        """
        self.path = Path(session_path).expanduser()
        if not self.path.exists():
            raise FileNotFoundError(f"Session file not found: {self.path}")

        self.session_id = self.path.stem
        self.entries: List[Dict[str, Any]] = []

    def parse(self) -> SessionData:
        """
        Parse JSONL file and return structured session data.

        Returns:
            SessionData object with parsed information
        """
        logger.info(f"Parsing session file: {self.path}")

        # Read JSONL file
        with open(self.path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    self.entries.append(entry)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse line: {e}")
                    continue

        # Build session data
        session_data = SessionData(
            session_id=self.session_id,
            session_path=str(self.path),
            total_entries=len(self.entries)
        )

        # Extract metadata from first entry if available
        for entry in self.entries:
            if entry.get("type") in ["user", "assistant"]:
                if not session_data.cwd:
                    session_data.cwd = entry.get("cwd")
                if not session_data.git_branch:
                    session_data.git_branch = entry.get("gitBranch")
                break

        # Parse entries
        for entry in self.entries:
            entry_type = entry.get("type")

            if entry_type == "user":
                self._parse_user_message(entry, session_data)
            elif entry_type == "assistant":
                self._parse_assistant_message(entry, session_data)
            elif entry_type == "file-history-snapshot":
                self._parse_file_snapshot(entry, session_data)

        # Set start/end times from messages
        if session_data.messages:
            session_data.start_time = session_data.messages[0].timestamp
            session_data.end_time = session_data.messages[-1].timestamp

        logger.info(
            f"Parsed session {self.session_id}: "
            f"{len(session_data.messages)} messages, "
            f"{len(session_data.tool_calls)} tool calls, "
            f"{len(session_data.file_changes)} file changes"
        )

        return session_data

    def _parse_user_message(self, entry: Dict[str, Any], session_data: SessionData) -> None:
        """Parse a user message entry."""
        message_obj = entry.get("message", {})
        content = message_obj.get("content", "")

        session_data.messages.append(Message(
            role="user",
            content=content,
            timestamp=entry.get("timestamp", ""),
            uuid=entry.get("uuid", ""),
            parent_uuid=entry.get("parentUuid")
        ))

    def _parse_assistant_message(self, entry: Dict[str, Any], session_data: SessionData) -> None:
        """Parse an assistant message entry."""
        message_obj = entry.get("message", {})
        content_parts = message_obj.get("content", [])

        # Extract text content
        text_content = []
        for part in content_parts:
            if isinstance(part, dict):
                if part.get("type") == "text":
                    text_content.append(part.get("text", ""))
                elif part.get("type") == "tool_use":
                    # Track tool calls
                    tool_call = ToolCall(
                        tool_name=part.get("name", ""),
                        timestamp=entry.get("timestamp", ""),
                        uuid=entry.get("uuid", ""),
                        parent_uuid=entry.get("parentUuid"),
                        input_data=part.get("input")
                    )
                    session_data.tool_calls.append(tool_call)

        # Only add message if there's text content
        if text_content:
            session_data.messages.append(Message(
                role="assistant",
                content="\n".join(text_content),
                timestamp=entry.get("timestamp", ""),
                uuid=entry.get("uuid", ""),
                parent_uuid=entry.get("parentUuid")
            ))

    def _parse_file_snapshot(self, entry: Dict[str, Any], session_data: SessionData) -> None:
        """Parse a file history snapshot entry."""
        snapshot = entry.get("snapshot", {})
        tracked_files = snapshot.get("trackedFileBackups", {})

        for file_path in tracked_files.keys():
            session_data.file_changes.append(FileChange(
                file_path=file_path,
                timestamp=snapshot.get("timestamp", ""),
                message_id=entry.get("messageId", "")
            ))

    def get_conversation(self) -> List[Message]:
        """
        Extract user/assistant messages only (no tool calls).

        Returns:
            List of Message objects in chronological order
        """
        if not self.entries:
            session_data = self.parse()
        else:
            session_data = self.parse()

        return session_data.messages

    def get_tool_results(self) -> List[ToolCall]:
        """
        Extract tool calls and results.

        Returns:
            List of ToolCall objects
        """
        if not self.entries:
            session_data = self.parse()
        else:
            session_data = self.parse()

        return session_data.tool_calls

    def get_file_changes(self) -> List[FileChange]:
        """
        Extract file modifications from snapshots.

        Returns:
            List of FileChange objects
        """
        if not self.entries:
            session_data = self.parse()
        else:
            session_data = self.parse()

        return session_data.file_changes

    def get_summary_for_extraction(self, max_tokens: int = 8000) -> str:
        """
        Build condensed conversation summary for LLM extraction.

        Focuses on user/assistant messages and major tool calls.
        Truncates to fit within token limit (roughly 4 chars per token).

        Args:
            max_tokens: Maximum tokens for summary (default: 8000)

        Returns:
            Condensed conversation string
        """
        session_data = self.parse()

        summary_parts = []
        summary_parts.append(f"# Session: {self.session_id}")
        summary_parts.append(f"Project: {session_data.cwd or 'Unknown'}")
        summary_parts.append(f"Branch: {session_data.git_branch or 'Unknown'}")
        summary_parts.append(f"Duration: {session_data.start_time} to {session_data.end_time}")
        summary_parts.append(f"\n## Conversation ({len(session_data.messages)} messages)\n")

        # Add messages
        for msg in session_data.messages:
            role_prefix = "USER" if msg.role == "user" else "ASSISTANT"
            # Truncate very long messages
            content = msg.content[:1000] if len(msg.content) > 1000 else msg.content
            summary_parts.append(f"{role_prefix}: {content}\n")

        # Add tool calls summary
        if session_data.tool_calls:
            summary_parts.append(f"\n## Tool Calls ({len(session_data.tool_calls)})\n")
            for tool in session_data.tool_calls[:20]:  # Limit to first 20
                summary_parts.append(f"- {tool.tool_name}")
                if tool.input_data:
                    # Show first few input keys
                    keys = list(tool.input_data.keys())[:3]
                    summary_parts.append(f" ({', '.join(keys)})")
                summary_parts.append("\n")

        # Add file changes summary
        if session_data.file_changes:
            summary_parts.append(f"\n## Files Modified ({len(session_data.file_changes)})\n")
            unique_files = list(set(fc.file_path for fc in session_data.file_changes))
            for file_path in unique_files[:10]:  # Limit to first 10
                summary_parts.append(f"- {file_path}\n")

        full_summary = "".join(summary_parts)

        # Truncate if needed (roughly 4 chars per token)
        max_chars = max_tokens * 4
        if len(full_summary) > max_chars:
            full_summary = full_summary[:max_chars] + "\n\n[... truncated ...]"

        return full_summary


def get_project_sessions_dir(project_path: str) -> Path:
    """
    Get the Claude Code sessions directory for a project path.

    Claude Code stores sessions in ~/.claude/projects/{encoded-path}/
    where path like "/Users/user/Projects/myapp" becomes "-Users-user-Projects-myapp"

    Args:
        project_path: Absolute path to project directory

    Returns:
        Path to sessions directory
    """
    # Encode path: replace slashes with hyphens
    # Claude keeps the leading hyphen (e.g., "-Users-iamanmp-Projects-claude-os")
    encoded_path = project_path.replace("/", "-")

    sessions_dir = Path.home() / ".claude" / "projects" / encoded_path
    return sessions_dir


def list_session_files(project_path: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    List session files for a project.

    Args:
        project_path: Absolute path to project directory
        limit: Maximum number of sessions to return (most recent first)

    Returns:
        List of session file info dicts
    """
    sessions_dir = get_project_sessions_dir(project_path)

    if not sessions_dir.exists():
        logger.warning(f"Sessions directory not found: {sessions_dir}")
        return []

    # Find all .jsonl files
    session_files = list(sessions_dir.glob("*.jsonl"))

    # Sort by modification time (most recent first)
    session_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    # Limit results
    session_files = session_files[:limit]

    # Build info list
    sessions_info = []
    for session_file in session_files:
        stat = session_file.stat()

        # Try to get basic info without full parse
        session_id = session_file.stem
        created_time = datetime.fromtimestamp(stat.st_ctime).isoformat()
        modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat()

        # Count lines to estimate message count
        try:
            with open(session_file, 'r') as f:
                line_count = sum(1 for _ in f)
        except Exception:
            line_count = 0

        sessions_info.append({
            "id": session_id,
            "path": str(session_file),
            "created": created_time,
            "modified": modified_time,
            "size_bytes": stat.st_size,
            "estimated_entries": line_count
        })

    return sessions_info
