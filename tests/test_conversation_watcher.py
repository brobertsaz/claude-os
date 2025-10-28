"""
Tests for conversation watcher functionality.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from app.core.conversation_watcher import ConversationWatcher, detect_learning_opportunities


@pytest.mark.unit
class TestConversationWatcher:
    """Test ConversationWatcher class."""

    def test_watcher_initialization(self):
        """Test conversation watcher initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_id = 123
            watcher = ConversationWatcher(project_id, temp_dir)

            assert watcher.project_id == project_id
            assert watcher.project_path == Path(temp_dir).resolve()
            assert watcher.insights_dir == (Path(temp_dir).resolve() / ".claude-os" / "project-profile")

    def test_detect_triggers_switching(self):
        """Test detecting technology switching triggers."""
        watcher = ConversationWatcher(123, "/tmp")

        text = "We're switching from React to Vue.js for the frontend."
        detections = watcher.detect_triggers(text)

        assert len(detections) > 0

        switching_detections = [d for d in detections if d["trigger"] == "switching"]
        assert len(switching_detections) > 0

        detection = switching_detections[0]
        assert detection["text"] == "switching from React to Vue.js"
        assert detection["groups"] == ("React", "Vue.js")
        assert detection["confidence"] == 0.95
        assert "Technology/library switch detected" in detection["description"]

    def test_detect_triggers_decided_to_use(self):
        """Test detecting 'decided to use' triggers."""
        watcher = ConversationWatcher(123, "/tmp")

        text = "We decided to use TypeScript for the new project."
        detections = watcher.detect_triggers(text)

        decided_detections = [d for d in detections if d["trigger"] == "decided_to_use"]
        assert len(decided_detections) > 0

        detection = decided_detections[0]
        assert detection["text"] == "decided to use TypeScript"
        assert detection["groups"] == ("TypeScript",)
        assert detection["confidence"] == 0.90

    def test_detect_triggers_no_longer(self):
        """Test detecting 'no longer using' triggers."""
        watcher = ConversationWatcher(123, "/tmp")

        text = "We're no longer using jQuery in this project."
        detections = watcher.detect_triggers(text)

        no_longer_detections = [d for d in detections if d["trigger"] == "no_longer"]
        assert len(no_longer_detections) > 0

        detection = no_longer_detections[0]
        assert detection["text"] == "no longer using jQuery"
        assert detection["groups"] == ("jQuery",)
        assert detection["confidence"] == 0.85

    def test_detect_triggers_now_using(self):
        """Test detecting 'now using' triggers."""
        watcher = ConversationWatcher(123, "/tmp")

        text = "We're now using Docker for containerization."
        detections = watcher.detect_triggers(text)

        now_using_detections = [d for d in detections if d["trigger"] == "now_using"]
        assert len(now_using_detections) > 0

        detection = now_using_detections[0]
        assert detection["text"] == "now using Docker"
        assert detection["groups"] == ("Docker",)
        assert detection["confidence"] == 0.85

    def test_detect_triggers_performance_issue(self):
        """Test detecting performance issue triggers."""
        watcher = ConversationWatcher(123, "/tmp")

        text = "The database queries are too slow."
        detections = watcher.detect_triggers(text)

        perf_detections = [d for d in detections if d["trigger"] == "performance_issue"]
        assert len(perf_detections) > 0

        detection = perf_detections[0]
        assert detection["text"] == "database queries are too slow"
        assert detection["groups"] == ("database queries",)
        assert detection["confidence"] == 0.85

    def test_detect_triggers_bug_fixed(self):
        """Test detecting bug fix triggers."""
        watcher = ConversationWatcher(123, "/tmp")

        text = "We fixed a bug in the authentication module."
        detections = watcher.detect_triggers(text)

        bug_detections = [d for d in detections if d["trigger"] == "bug_fixed"]
        assert len(bug_detections) > 0

        detection = bug_detections[0]
        assert detection["text"] == "fixed a bug in the authentication module"
        assert detection["groups"] == ("the authentication module",)
        assert detection["confidence"] == 0.80

    def test_detect_triggers_architecture_change(self):
        """Test detecting architecture change triggers."""
        watcher = ConversationWatcher(123, "/tmp")

        text = "We're refactoring the monolith to microservices."
        detections = watcher.detect_triggers(text)

        arch_detections = [d for d in detections if d["trigger"] == "architecture_change"]
        assert len(arch_detections) > 0

        detection = arch_detections[0]
        assert detection["text"] == "refactoring the monolith to microservices"
        assert detection["groups"] == ("the monolith", "microservices")
        assert detection["confidence"] == 0.85

    def test_detect_triggers_rejected_idea(self):
        """Test detecting rejected idea triggers."""
        watcher = ConversationWatcher(123, "/tmp")

        text = "We decided against using WebAssembly for this project."
        detections = watcher.detect_triggers(text)

        rejected_detections = [d for d in detections if d["trigger"] == "rejected_idea"]
        assert len(rejected_detections) > 0

        detection = rejected_detections[0]
        assert detection["text"] == "decided against using WebAssembly"
        assert detection["groups"] == ("using WebAssembly",)
        assert detection["confidence"] == 0.75

    def test_detect_triggers_edge_case(self):
        """Test detecting edge case triggers."""
        watcher = ConversationWatcher(123, "/tmp")

        text = "Beware of the gotcha with async/await in loops."
        detections = watcher.detect_triggers(text)

        edge_detections = [d for d in detections if d["trigger"] == "edge_case"]
        assert len(edge_detections) > 0

        detection = edge_detections[0]
        assert "gotcha with async/await" in detection["text"]
        assert detection["confidence"] == 0.80

    def test_detect_multiple_triggers(self):
        """Test detecting multiple triggers in one text."""
        watcher = ConversationWatcher(123, "/tmp")

        text = """
        We're switching from React to Vue.js and decided to use TypeScript.
        We're no longer using jQuery because it was too slow.
        We fixed a bug in the authentication module.
        """
        detections = watcher.detect_triggers(text)

        # Should detect multiple triggers
        assert len(detections) >= 4

        trigger_types = {d["trigger"] for d in detections}
        assert "switching" in trigger_types
        assert "decided_to_use" in trigger_types
        assert "no_longer" in trigger_types
        assert "bug_fixed" in trigger_types

    def test_detect_no_triggers(self):
        """Test text with no triggers."""
        watcher = ConversationWatcher(123, "/tmp")

        text = "This is a normal conversation about the weather and other topics."
        detections = watcher.detect_triggers(text)

        assert len(detections) == 0

    def test_detections_sorted_by_confidence(self):
        """Test that detections are sorted by confidence."""
        watcher = ConversationWatcher(123, "/tmp")

        text = """
        We decided to use TypeScript (90% confidence).
        We're switching from React to Vue.js (95% confidence).
        We're no longer using jQuery (85% confidence).
        """
        detections = watcher.detect_triggers(text)

        # Should be sorted by confidence (descending)
        confidences = [d["confidence"] for d in detections]
        assert confidences == sorted(confidences, reverse=True)

    def test_extract_context(self):
        """Test context extraction around matches."""
        watcher = ConversationWatcher(123, "/tmp")

        text = "This is some context before the trigger. We decided to use TypeScript. This is some context after the trigger."

        # Find the match manually for testing
        import re
        pattern = r"decided to (?:use|adopt|switch to) (.+?)(?:\.|,|$)"
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)

        if match:
            context = watcher._extract_context(text, match)

            # Should include text before and after
            assert "context before" in context.lower()
            assert "decided to use TypeScript" in context
            assert "context after" in context.lower()
            # Should be reasonably sized
            assert len(context) <= len(text) + 100  # Allow some padding

    def test_generate_id(self):
        """Test ID generation for detections."""
        watcher = ConversationWatcher(123, "/tmp")

        # Generate IDs for same trigger multiple times
        id1 = watcher._generate_id("switching", "switching from A to B")
        id2 = watcher._generate_id("switching", "switching from A to B")

        # Should be different due to timestamp
        assert id1 != id2
        assert len(id1) == 8  # MD5 hash truncated to 8 chars
        assert len(id2) == 8

    def test_save_insight(self, tmp_path):
        """Test saving insights to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_id = 123
            watcher = ConversationWatcher(project_id, temp_dir)

            detection = {
                "id": "test123",
                "trigger": "switching",
                "text": "switching from A to B",
                "confidence": 0.95,
                "description": "Technology switch",
                "timestamp": "2023-01-01T12:00:00",
                "context": "Some context"
            }

            result = watcher.save_insight(detection)

            assert result is True

            # Check file was created
            insights_file = Path(temp_dir) / ".claude-os" / "project-profile" / "LEARNED_INSIGHTS.md"
            assert insights_file.exists()

            # Check content
            content = insights_file.read_text()
            assert "switching" in content
            assert "switching from A to B" in content
            assert "95%" in content
            assert "Technology switch" in content

    def test_save_insight_creates_directory(self, tmp_path):
        """Test that save_insight creates directory if needed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_id = 123
            watcher = ConversationWatcher(project_id, temp_dir)

            detection = {
                "id": "test123",
                "trigger": "switching",
                "text": "test",
                "confidence": 0.95,
                "description": "Test",
                "timestamp": "2023-01-01T12:00:00",
                "context": "test"
            }

            result = watcher.save_insight(detection)

            assert result is True

            # Directory should be created
            insights_dir = Path(temp_dir) / ".claude-os" / "project-profile"
            assert insights_dir.exists()
            assert insights_dir.is_dir()

    def test_save_insight_error_handling(self, tmp_path):
        """Test save_insight error handling."""
        # Use invalid path that should cause error
        watcher = ConversationWatcher(123, "/invalid/path/that/does/not/exist")

        detection = {
            "id": "test123",
            "trigger": "switching",
            "text": "test",
            "confidence": 0.95,
            "description": "Test",
            "timestamp": "2023-01-01T12:00:00",
            "context": "test"
        }

        result = watcher.save_insight(detection)

        # Should handle error gracefully
        assert result is False

    def test_format_insight(self):
        """Test insight formatting."""
        watcher = ConversationWatcher(123, "/tmp")

        detection = {
            "timestamp": "2023-01-01T12:00:00",
            "trigger": "switching",
            "confidence": 0.95,
            "text": "switching from React to Vue.js",
            "context": "Some context around the switch",
            "description": "Technology switch detected"
        }

        formatted = watcher._format_insight(detection)

        assert "### 2023-01-01T12:00:00" in formatted
        assert "**Type**: switching" in formatted
        assert "**Confidence**: 95%" in formatted
        assert "**Text**: switching from React to Vue.js" in formatted
        assert "**Context**: Some context around the switch" in formatted
        assert "**Description**: Technology switch detected" in formatted

    def test_get_learned_insights_no_file(self, tmp_path):
        """Test getting insights when no file exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_id = 123
            watcher = ConversationWatcher(project_id, temp_dir)

            insights = watcher.get_learned_insights()

            assert insights == []

    def test_get_learned_insights_with_file(self, tmp_path):
        """Test getting insights when file exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_id = 123
            watcher = ConversationWatcher(project_id, temp_dir)

            # Create insights file
            insights_dir = Path(temp_dir) / ".claude-os" / "project-profile"
            insights_dir.mkdir(parents=True)
            insights_file = insights_dir / "LEARNED_INSIGHTS.md"

            content = """
### 2023-01-01T12:00:00
**Type**: switching
**Confidence**: 95%
**Text**: switching from A to B

### 2023-01-02T13:00:00
**Type**: decided_to_use
**Confidence**: 90%
**Text**: decided to use TypeScript
"""
            insights_file.write_text(content)

            insights = watcher.get_learned_insights()

            assert insights["count"] == 2
            assert "switching" in insights["content"]
            assert "decided_to_use" in insights["content"]

    def test_should_prompt_user(self):
        """Test user prompt decision logic."""
        watcher = ConversationWatcher(123, "/tmp")

        # High confidence should prompt
        high_conf = {"confidence": 0.80}
        assert watcher.should_prompt_user(high_conf) is True

        # Low confidence should not prompt
        low_conf = {"confidence": 0.70}
        assert watcher.should_prompt_user(low_conf) is False

        # Edge case - exactly 0.75 should prompt
        edge_conf = {"confidence": 0.75}
        assert watcher.should_prompt_user(edge_conf) is True


@pytest.mark.unit
class TestConversationWatcherUtility:
    """Test conversation watcher utility functions."""

    def test_detect_learning_opportunities_function(self):
        """Test the utility function for detecting opportunities."""
        text = "We're switching from React to Vue.js and decided to use TypeScript."

        detections = detect_learning_opportunities(123, "/tmp", text)

        assert len(detections) >= 2
        trigger_types = {d["trigger"] for d in detections}
        assert "switching" in trigger_types
        assert "decided_to_use" in trigger_types

    def test_detect_learning_opportunities_empty(self):
        """Test utility function with no triggers."""
        text = "This is a normal conversation."

        detections = detect_learning_opportunities(123, "/tmp", text)

        assert len(detections) == 0

    def test_detect_learning_opportunities_case_insensitive(self):
        """Test that detection is case insensitive."""
        text = "WE'RE SWITCHING FROM REACT TO VUE.JS"

        detections = detect_learning_opportunities(123, "/tmp", text)

        switching_detections = [d for d in detections if d["trigger"] == "switching"]
        assert len(switching_detections) > 0

    def test_detect_learning_opportunities_multiline(self):
        """Test detection across multiple lines."""
        text = """We decided to use TypeScript
for the new project. We're no longer
using jQuery because it was too slow."""

        detections = detect_learning_opportunities(123, "/tmp", text)

        trigger_types = {d["trigger"] for d in detections}
        assert "decided_to_use" in trigger_types
        assert "no_longer" in trigger_types

    def test_detect_learning_opportunities_with_punctuation(self):
        """Test detection with various punctuation."""
        test_cases = [
            "We decided to use TypeScript!",
            "We're switching from React to Vue.js?",
            "We're no longer using jQuery...",
            "We now using Docker (for containerization)."
        ]

        for text in test_cases:
            detections = detect_learning_opportunities(123, "/tmp", text)
            assert len(detections) > 0, f"Failed to detect in: {text}"

    def test_trigger_patterns_completeness(self):
        """Test that all expected trigger patterns are defined."""
        watcher = ConversationWatcher(123, "/tmp")

        expected_triggers = {
            "switching", "decided_to_use", "no_longer", "now_using",
            "implement_change", "performance_issue", "bug_fixed",
            "architecture_change", "rejected_idea", "edge_case"
        }

        actual_triggers = set(watcher.TRIGGERS.keys())

        assert actual_triggers == expected_triggers

    def test_trigger_pattern_structure(self):
        """Test that all trigger patterns have required structure."""
        watcher = ConversationWatcher(123, "/tmp")

        for trigger_name, trigger_config in watcher.TRIGGERS.items():
            assert "pattern" in trigger_config
            assert "confidence" in trigger_config
            assert "description" in trigger_config

            # Check that pattern is a valid regex
            import re
            assert isinstance(trigger_config["pattern"], str)
            assert trigger_config["confidence"] >= 0.0
            assert trigger_config["confidence"] <= 1.0
            assert isinstance(trigger_config["description"], str)

    def test_context_extraction_edge_cases(self):
        """Test context extraction edge cases."""
        watcher = ConversationWatcher(123, "/tmp")

        # Test with match at beginning
        text_beginning = "Switching from A to B. More text here."
        match_beginning = re.search(r"switching from (.+?) to (.+?)", text_beginning, re.IGNORECASE)
        context_beginning = watcher._extract_context(text_beginning, match_beginning)
        assert "Switching from A to B" in context_beginning

        # Test with match at end
        text_ending = "Text here. Switching from A to B"
        match_ending = re.search(r"switching from (.+?) to (.+?)", text_ending, re.IGNORECASE)
        context_ending = watcher._extract_context(text_ending, match_ending)
        assert "Switching from A to B" in context_ending

        # Test with short text (no context)
        text_short = "Switching from A to B"
        match_short = re.search(r"switching from (.+?) to (.+?)", text_short, re.IGNORECASE)
        context_short = watcher._extract_context(text_short, match_short)
        assert "Switching from A to B" in context_short

    def test_id_uniqueness(self):
        """Test that generated IDs are unique."""
        watcher = ConversationWatcher(123, "/tmp")

        # Generate multiple IDs
        ids = []
        for i in range(10):
            id_val = watcher._generate_id("test", f"test text {i}")
            ids.append(id_val)

        # All should be unique
        assert len(set(ids)) == len(ids)

        # All should be valid hex strings
        for id_val in ids:
            assert len(id_val) == 8
            assert all(c in "0123456789abcdef" for c in id_val)