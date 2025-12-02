"""
Tests for learning jobs functionality.
"""

import pytest
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from app.core.learning_jobs import (
    process_learning_detection,
    prompt_user_for_confirmation,
    ingest_to_mcp,
    handle_conversation_message,
    wait_for_confirmation,
    subscribe_to_conversations
)


@pytest.mark.unit
class TestLearningJobs:
    """Test learning jobs functions."""

    @patch('app.core.learning_jobs.RedisConfig')
    def test_process_learning_detection_confirmed(self, mock_redis_config, tmp_path):
        """Test processing learning detection with user confirmation."""
        # Configure RedisConfig mock
        mock_redis_config.set_confirmation = MagicMock()
        mock_redis_config.queue_prompt_job = MagicMock(return_value="prompt_job_123")
        mock_redis_config.queue_ingest_job = MagicMock(return_value="ingest_job_123")

        detection = {
            "id": "detection_123",
            "trigger": "switching",
            "text": "switching from A to B",
            "confidence": 0.95
        }

        with patch('app.core.learning_jobs.wait_for_confirmation') as mock_wait:
            mock_wait.return_value = True

            result = process_learning_detection(123, detection)

            assert result["status"] == "confirmed"
            assert result["ingest_job_id"] == "ingest_job_123"
            assert result["detection_id"] == "detection_123"

            # Verify Redis calls
            mock_redis_config.set_confirmation.assert_called_once_with(123, "detection_123", False)
            mock_redis_config.queue_prompt_job.assert_called_once_with(123, detection)
            mock_wait.assert_called_once_with(123, "detection_123", timeout=600)

    @patch('app.core.learning_jobs.RedisConfig')
    def test_process_learning_detection_skipped(self, mock_redis_config, tmp_path):
        """Test processing learning detection with user skipping."""
        # Configure RedisConfig mock
        mock_redis_config.set_confirmation = MagicMock()
        mock_redis_config.queue_prompt_job = MagicMock(return_value="prompt_job_123")
        mock_redis_config.queue_ingest_job = MagicMock()

        detection = {
            "id": "detection_123",
            "trigger": "switching",
            "text": "switching from A to B",
            "confidence": 0.95
        }

        with patch('app.core.learning_jobs.wait_for_confirmation') as mock_wait:
            mock_wait.return_value = False

            result = process_learning_detection(123, detection)

            assert result["status"] == "skipped"
            assert result["detection_id"] == "detection_123"

            # Verify Redis calls
            mock_redis_config.set_confirmation.assert_called_once_with(123, "detection_123", False)
            mock_redis_config.queue_prompt_job.assert_called_once_with(123, detection)
            mock_wait.assert_called_once_with(123, "detection_123", timeout=600)
            # Should not call ingest when skipped
            mock_redis_config.queue_ingest_job.assert_not_called()

    @patch('app.core.learning_jobs.RedisConfig')
    def test_process_learning_detection_timeout(self, mock_redis_config, tmp_path):
        """Test processing learning detection with timeout."""
        # Configure RedisConfig mock
        mock_redis_config.set_confirmation = MagicMock()
        mock_redis_config.queue_prompt_job = MagicMock(return_value="prompt_job_123")
        mock_redis_config.queue_ingest_job = MagicMock()

        detection = {
            "id": "detection_123",
            "trigger": "switching",
            "text": "switching from A to B",
            "confidence": 0.95
        }

        with patch('app.core.learning_jobs.wait_for_confirmation') as mock_wait:
            mock_wait.return_value = False  # Timeout returns False

            result = process_learning_detection(123, detection)

            assert result["status"] == "skipped"
            assert result["detection_id"] == "detection_123"

            # Should not call ingest when timeout
            mock_redis_config.queue_ingest_job.assert_not_called()

    @patch('app.core.learning_jobs.ConversationWatcher')
    def test_prompt_user_for_confirmation(self, mock_watcher_class):
        """Test prompting user for confirmation."""
        mock_watcher = MagicMock()
        mock_watcher_class.return_value = mock_watcher

        detection = {
            "id": "detection_123",
            "trigger": "switching",
            "text": "switching from A to B",
            "confidence": 0.95,
            "context": "Some context around the switch"
        }

        result = prompt_user_for_confirmation(123, detection)

        assert result["status"] == "prompted"
        assert result["detection_id"] == "detection_123"
        assert result["trigger"] == "switching"

    @patch('app.core.learning_jobs.ConversationWatcher')
    @patch('app.core.learning_jobs.urllib.request.urlopen')
    @patch('app.core.learning_jobs.urllib.request.Request')
    def test_ingest_to_mcp_success(self, mock_request, mock_urlopen, mock_watcher_class, tmp_path):
        """Test successful ingestion to MCP."""
        mock_watcher = MagicMock()
        mock_watcher_class.return_value = mock_watcher

        # Create insights file
        insights_dir = tmp_path / ".claude-os" / "project-profile"
        insights_dir.mkdir(parents=True)
        insights_file = insights_dir / "LEARNED_INSIGHTS.md"
        insights_file.write_text("# Test Insights\n\nThis is a test insight.")

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = ingest_to_mcp(123, str(tmp_path))

        assert result["status"] == "ingested"
        assert result["project_id"] == 123
        assert str(insights_file) in result["file"]

    @patch('app.core.learning_jobs.ConversationWatcher')
    def test_ingest_to_mcp_no_file(self, mock_watcher_class, tmp_path):
        """Test ingestion to MCP with no insights file."""
        mock_watcher = MagicMock()
        mock_watcher_class.return_value = mock_watcher

        # Don't create insights file
        insights_dir = tmp_path / ".claude-os" / "project-profile"
        insights_dir.mkdir(parents=True)

        result = ingest_to_mcp(123, str(tmp_path))

        assert result["status"] == "error"
        assert result["message"] == "insights_file_not_found"

    @patch('app.core.learning_jobs.ConversationWatcher')
    @patch('app.core.learning_jobs.urllib.request.urlopen')
    @patch('app.core.learning_jobs.urllib.request.Request')
    def test_ingest_to_mcp_api_error(self, mock_request, mock_urlopen, mock_watcher_class, tmp_path):
        """Test ingestion to MCP with API error."""
        mock_watcher = MagicMock()
        mock_watcher_class.return_value = mock_watcher

        # Create insights file
        insights_dir = tmp_path / ".claude-os" / "project-profile"
        insights_dir.mkdir(parents=True)
        insights_file = insights_dir / "LEARNED_INSIGHTS.md"
        insights_file.write_text("# Test Insights")

        # Mock API error
        mock_urlopen.side_effect = Exception("API Error")

        result = ingest_to_mcp(123, str(tmp_path))

        assert result["status"] == "error"
        assert "API Error" in result["message"]

    @patch('app.core.learning_jobs.ConversationWatcher')
    @patch('app.core.learning_jobs.urllib.request.urlopen')
    @patch('app.core.learning_jobs.urllib.request.Request')
    def test_ingest_to_mcp_request_error(self, mock_request, mock_urlopen, mock_watcher_class, tmp_path):
        """Test ingestion to MCP with request error."""
        mock_watcher = MagicMock()
        mock_watcher_class.return_value = mock_watcher

        # Create insights file
        insights_dir = tmp_path / ".claude-os" / "project-profile"
        insights_dir.mkdir(parents=True)
        insights_file = insights_dir / "LEARNED_INSIGHTS.md"
        insights_file.write_text("# Test Insights")

        # Mock request error
        mock_urlopen.side_effect = Exception("Request failed")

        result = ingest_to_mcp(123, str(tmp_path))

        assert result["status"] == "error"
        assert "Request failed" in result["message"]

    @patch('app.core.learning_jobs.RedisConfig')
    @patch('app.core.learning_jobs.ConversationWatcher')
    def test_handle_conversation_message_user(self, mock_watcher_class, mock_redis_config):
        """Test handling user conversation message."""
        # Configure mocks
        mock_watcher = MagicMock()
        mock_watcher.detect_triggers.return_value = [
            {
                "id": "detection_1",
                "trigger": "switching",
                "text": "switching from A to B",
                "confidence": 0.95
            }
        ]
        mock_watcher.should_prompt_user.return_value = True
        mock_watcher_class.return_value = mock_watcher

        mock_redis_config.queue_learning_job = MagicMock(return_value="job_123")

        message = {
            "role": "user",
            "text": "We're switching from A to B"
        }

        handle_conversation_message(123, message)

        # Should process user message
        mock_watcher.detect_triggers.assert_called_once_with("We're switching from A to B")
        mock_watcher.should_prompt_user.assert_called_once()

        # Should queue learning job
        mock_redis_config.queue_learning_job.assert_called_once()

    @patch('app.core.learning_jobs.RedisConfig')
    @patch('app.core.learning_jobs.ConversationWatcher')
    def test_handle_conversation_message_assistant(self, mock_watcher_class, mock_redis_config):
        """Test handling assistant conversation message."""
        mock_watcher = MagicMock()
        mock_watcher_class.return_value = mock_watcher

        message = {
            "role": "assistant",
            "text": "I can help you with that switch"
        }

        handle_conversation_message(123, message)

        # Should not process assistant message
        mock_watcher.detect_triggers.assert_not_called()

    @patch('app.core.learning_jobs.RedisConfig')
    @patch('app.core.learning_jobs.ConversationWatcher')
    def test_handle_conversation_message_no_detections(self, mock_watcher_class, mock_redis_config):
        """Test handling message with no detections."""
        mock_watcher = MagicMock()
        mock_watcher.detect_triggers.return_value = []
        mock_watcher_class.return_value = mock_watcher

        mock_redis_config.queue_learning_job = MagicMock()

        message = {
            "role": "user",
            "text": "This is a normal message"
        }

        handle_conversation_message(123, message)

        # Should not queue job for no detections
        mock_watcher.detect_triggers.assert_called_once()
        mock_redis_config.queue_learning_job.assert_not_called()

    @patch('app.core.learning_jobs.RedisConfig')
    @patch('app.core.learning_jobs.ConversationWatcher')
    def test_handle_conversation_message_low_confidence(self, mock_watcher_class, mock_redis_config):
        """Test handling message with low confidence detections."""
        mock_watcher = MagicMock()
        mock_watcher.detect_triggers.return_value = [
            {
                "id": "detection_1",
                "trigger": "switching",
                "text": "switching from A to B",
                "confidence": 0.70  # Low confidence
            }
        ]
        mock_watcher.should_prompt_user.return_value = False
        mock_watcher_class.return_value = mock_watcher

        mock_redis_config.queue_learning_job = MagicMock()

        message = {
            "role": "user",
            "text": "We're switching from A to B"
        }

        handle_conversation_message(123, message)

        # Should not queue job for low confidence
        mock_watcher.detect_triggers.assert_called_once()
        mock_watcher.should_prompt_user.assert_called_once()
        mock_redis_config.queue_learning_job.assert_not_called()

    @patch('app.core.learning_jobs.RedisConfig')
    @patch('app.core.learning_jobs.time.sleep')
    def test_wait_for_confirmation_confirmed(self, mock_sleep, mock_redis_config):
        """Test waiting for confirmation when confirmed."""
        # First call returns None, second returns True
        mock_redis_config.get_confirmation = MagicMock(side_effect=[None, True])

        result = wait_for_confirmation(123, "detection_123", timeout=600)

        assert result is True
        assert mock_redis_config.get_confirmation.call_count == 2
        mock_sleep.assert_called_once_with(1)

    @patch('app.core.learning_jobs.RedisConfig')
    @patch('app.core.learning_jobs.time.sleep')
    @patch('app.core.learning_jobs.time.time')
    def test_wait_for_confirmation_timeout(self, mock_time, mock_sleep, mock_redis_config):
        """Test waiting for confirmation with timeout."""
        # Always return None
        mock_redis_config.get_confirmation = MagicMock(return_value=None)
        # Simulate time passing
        mock_time.side_effect = [0, 0.5, 601]  # start, first check, timeout

        result = wait_for_confirmation(123, "detection_123", timeout=600)

        assert result is False

    @patch('app.core.learning_jobs.RedisConfig')
    @patch('app.core.learning_jobs.time.sleep')
    def test_wait_for_confirmation_immediate(self, mock_sleep, mock_redis_config):
        """Test waiting for confirmation when immediately confirmed."""
        mock_redis_config.get_confirmation = MagicMock(return_value=True)

        result = wait_for_confirmation(123, "detection_123", timeout=600)

        assert result is True
        # Should not sleep when immediately confirmed
        mock_sleep.assert_not_called()

    @patch('app.core.learning_jobs.RedisConfig')
    @patch('app.core.learning_jobs.handle_conversation_message')
    def test_subscribe_to_conversations(self, mock_handle, mock_redis_config):
        """Test subscribing to conversations."""
        mock_pubsub = MagicMock()
        mock_redis_config.subscribe_to_conversation = MagicMock(return_value=mock_pubsub)

        # Mock pubsub messages
        message1 = json.dumps({"role": "user", "text": "Test message 1"})

        # Mock pubsub listen to return one message then raise KeyboardInterrupt
        def mock_listen():
            yield {"type": "message", "data": message1}
            raise KeyboardInterrupt()

        mock_pubsub.listen = mock_listen

        # Run subscription (will stop on KeyboardInterrupt)
        subscribe_to_conversations(123)

        # Should handle valid message
        mock_handle.assert_called_once_with(123, {"role": "user", "text": "Test message 1"})

        # Should close pubsub
        mock_pubsub.close.assert_called_once()


@pytest.mark.integration
class TestLearningJobsIntegration:
    """Integration tests for learning jobs."""

    @patch('app.core.learning_jobs.RedisConfig')
    @patch('app.core.learning_jobs.ConversationWatcher')
    @patch('app.core.learning_jobs.wait_for_confirmation')
    def test_full_learning_workflow(self, mock_wait, mock_watcher_class, mock_redis_config, tmp_path):
        """Test full learning workflow from message to ingestion."""
        # Configure RedisConfig mock
        mock_redis_config.set_confirmation = MagicMock()
        mock_redis_config.queue_prompt_job = MagicMock(return_value="prompt_job_123")
        mock_redis_config.queue_ingest_job = MagicMock(return_value="ingest_job_123")
        mock_redis_config.queue_learning_job = MagicMock(return_value="learning_job_123")

        # Configure watcher mock
        mock_watcher = MagicMock()
        mock_watcher.detect_triggers.return_value = [
            {
                "id": "detection_123",
                "trigger": "switching",
                "text": "switching from A to B",
                "confidence": 0.95
            }
        ]
        mock_watcher.should_prompt_user.return_value = True
        mock_watcher_class.return_value = mock_watcher

        # User confirms
        mock_wait.return_value = True

        # Handle message
        message = {"role": "user", "text": "We're switching from A to B"}
        handle_conversation_message(123, message)

        # Process detection
        result = process_learning_detection(123, {
            "id": "detection_123",
            "trigger": "switching",
            "text": "switching from A to B",
            "confidence": 0.95
        })

        assert result["status"] == "confirmed"
        assert result["ingest_job_id"] == "ingest_job_123"

        # Verify workflow
        mock_watcher.detect_triggers.assert_called_once()
        mock_redis_config.queue_learning_job.assert_called_once()
        mock_redis_config.queue_prompt_job.assert_called_once()
        mock_wait.assert_called_once()
        mock_redis_config.queue_ingest_job.assert_called_once()
