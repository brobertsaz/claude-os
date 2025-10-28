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
from app.core.redis_config import RedisConfig


@pytest.mark.unit
class TestLearningJobs:
    """Test learning jobs functions."""

    @patch('app.core.learning_jobs.RedisConfig')
    @patch('app.core.learning_jobs.ConversationWatcher')
    def test_process_learning_detection_confirmed(self, mock_watcher_class, mock_redis_class, tmp_path):
        """Test processing learning detection with user confirmation."""
        # Mock Redis
        mock_redis = MagicMock()
        mock_redis_class.set_confirmation.return_value = None
        mock_redis_class.queue_prompt_job.return_value = "prompt_job_123"
        mock_redis_class.get_confirmation.return_value = True
        mock_redis_class.return_value = mock_redis

        # Mock watcher
        mock_watcher = MagicMock()
        mock_watcher_class.return_value = mock_watcher

        detection = {
            "id": "detection_123",
            "trigger": "switching",
            "text": "switching from A to B",
            "confidence": 0.95
        }

        with patch('app.core.learning_jobs.wait_for_confirmation') as mock_wait:
            mock_wait.return_value = True

            with patch('app.core.learning_jobs.ingest_to_mcp') as mock_ingest:
                mock_ingest.return_value = {"status": "ingested"}

                result = process_learning_detection(123, detection)

                assert result["status"] == "confirmed"
                assert result["ingest_job_id"] is not None
                assert result["detection_id"] == "detection_123"

                # Verify Redis calls
                mock_redis.set_confirmation.assert_called_once_with(123, "detection_123", False)
                mock_redis.queue_prompt_job.assert_called_once_with(123, detection)
                mock_wait.assert_called_once_with(123, "detection_123", timeout=600)
                mock_ingest.assert_called_once_with(123, str(Path.cwd()))

    @patch('app.core.learning_jobs.RedisConfig')
    @patch('app.core.learning_jobs.ConversationWatcher')
    def test_process_learning_detection_skipped(self, mock_watcher_class, mock_redis_class, tmp_path):
        """Test processing learning detection with user skipping."""
        # Mock Redis
        mock_redis = MagicMock()
        mock_redis_class.set_confirmation.return_value = None
        mock_redis_class.queue_prompt_job.return_value = "prompt_job_123"
        mock_redis_class.get_confirmation.return_value = False
        mock_redis_class.return_value = mock_redis

        # Mock watcher
        mock_watcher = MagicMock()
        mock_watcher_class.return_value = mock_watcher

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
            mock_redis.set_confirmation.assert_called_once_with(123, "detection_123", False)
            mock_redis.queue_prompt_job.assert_called_once_with(123, detection)
            mock_wait.assert_called_once_with(123, "detection_123", timeout=600)
            # Should not call ingest when skipped
            mock_redis.queue_ingest_job.assert_not_called()

    @patch('app.core.learning_jobs.RedisConfig')
    @patch('app.core.learning_jobs.ConversationWatcher')
    def test_process_learning_detection_timeout(self, mock_watcher_class, mock_redis_class, tmp_path):
        """Test processing learning detection with timeout."""
        # Mock Redis
        mock_redis = MagicMock()
        mock_redis_class.set_confirmation.return_value = None
        mock_redis_class.queue_prompt_job.return_value = "prompt_job_123"
        mock_redis_class.get_confirmation.return_value = None  # Timeout
        mock_redis_class.return_value = mock_redis

        # Mock watcher
        mock_watcher = MagicMock()
        mock_watcher_class.return_value = mock_watcher

        detection = {
            "id": "detection_123",
            "trigger": "switching",
            "text": "switching from A to B",
            "confidence": 0.95
        }

        with patch('app.core.learning_jobs.wait_for_confirmation') as mock_wait:
            mock_wait.return_value = None  # Timeout

            result = process_learning_detection(123, detection)

            assert result["status"] == "skipped"
            assert result["detection_id"] == "detection_123"

            # Should not call ingest when timeout
            mock_redis.queue_ingest_job.assert_not_called()

    @patch('app.core.learning_jobs.ConversationWatcher')
    def test_prompt_user_for_confirmation(self, mock_watcher_class):
        """Test prompting user for confirmation."""
        # Mock watcher
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

        # Should print prompt information
        # In real implementation, this would show to user
        # For test, we just verify the function returns correctly

    @patch('app.core.learning_jobs.ConversationWatcher')
    @patch('app.core.learning_jobs.urllib.request')
    def test_ingest_to_mcp_success(self, mock_watcher_class, mock_request, tmp_path):
        """Test successful ingestion to MCP."""
        # Mock watcher
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
        mock_request.return_value.__enter__.return_value = mock_response

        result = ingest_to_mcp(123, str(tmp_path))

        assert result["status"] == "ingested"
        assert result["project_id"] == 123
        assert str(insights_file) in result["file"]

        # Verify API call
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert "http://localhost:8051" in call_args[0][0]  # URL
        assert "/api/projects/123/ingest-document" in call_args[0][0]  # Endpoint

        # Verify request data
        request_data = json.loads(call_args[0][1]["data"])
        assert request_data["filename"] == "LEARNED_INSIGHTS.md"
        assert request_data["mcp_type"] == "project_profile"
        assert request_data["metadata"]["type"] == "learned_insights"
        assert request_data["metadata"]["auto_generated"] is True

    @patch('app.core.learning_jobs.ConversationWatcher')
    def test_ingest_to_mcp_no_file(self, mock_watcher_class, tmp_path):
        """Test ingestion to MCP with no insights file."""
        # Mock watcher
        mock_watcher = MagicMock()
        mock_watcher_class.return_value = mock_watcher

        # Don't create insights file
        insights_dir = tmp_path / ".claude-os" / "project-profile"
        insights_dir.mkdir(parents=True)

        result = ingest_to_mcp(123, str(tmp_path))

        assert result["status"] == "error"
        assert result["message"] == "insights_file_not_found"

    @patch('app.core.learning_jobs.ConversationWatcher')
    @patch('app.core.learning_jobs.urllib.request')
    def test_ingest_to_mcp_api_error(self, mock_watcher_class, mock_request, tmp_path):
        """Test ingestion to MCP with API error."""
        # Mock watcher
        mock_watcher = MagicMock()
        mock_watcher_class.return_value = mock_watcher

        # Create insights file
        insights_dir = tmp_path / ".claude-os" / "project-profile"
        insights_dir.mkdir(parents=True)
        insights_file = insights_dir / "LEARNED_INSIGHTS.md"
        insights_file.write_text("# Test Insights")

        # Mock API error
        import urllib.error
        mock_request.side_effect = urllib.error.HTTPError("500 Server Error")

        result = ingest_to_mcp(123, str(tmp_path))

        assert result["status"] == "error"
        assert "API returned" in result["message"]

    @patch('app.core.learning_jobs.ConversationWatcher')
    @patch('app.core.learning_jobs.urllib.request')
    def test_ingest_to_mcp_request_error(self, mock_watcher_class, mock_request, tmp_path):
        """Test ingestion to MCP with request error."""
        # Mock watcher
        mock_watcher = MagicMock()
        mock_watcher_class.return_value = mock_watcher

        # Create insights file
        insights_dir = tmp_path / ".claude-os" / "project-profile"
        insights_dir.mkdir(parents=True)
        insights_file = insights_dir / "LEARNED_INSIGHTS.md"
        insights_file.write_text("# Test Insights")

        # Mock request error
        mock_request.side_effect = Exception("Request failed")

        result = ingest_to_mcp(123, str(tmp_path))

        assert result["status"] == "error"
        assert "Request failed" in result["message"]

    @patch('app.core.learning_jobs.RedisConfig')
    @patch('app.core.learning_jobs.ConversationWatcher')
    def test_handle_conversation_message_user(self, mock_watcher_class, mock_redis_class):
        """Test handling user conversation message."""
        # Mock Redis
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis

        # Mock watcher
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

        message = {
            "role": "user",
            "text": "We're switching from A to B"
        }

        with patch('app.core.learning_jobs.RedisConfig.queue_learning_job') as mock_queue:
            mock_queue.return_value = "job_123"

            handle_conversation_message(123, message)

            # Should process user message
            mock_watcher.detect_triggers.assert_called_once_with("We're switching from A to B")
            mock_watcher.should_prompt_user.assert_called_once()

            # Should queue learning job
            mock_queue.assert_called_once_with(123, {
                "id": "detection_1",
                "trigger": "switching",
                "text": "switching from A to B",
                "confidence": 0.95
            })

    @patch('app.core.learning_jobs.RedisConfig')
    @patch('app.core.learning_jobs.ConversationWatcher')
    def test_handle_conversation_message_assistant(self, mock_watcher_class, mock_redis_class):
        """Test handling assistant conversation message."""
        # Mock Redis
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis

        # Mock watcher
        mock_watcher = MagicMock()
        mock_watcher_class.return_value = mock_watcher

        message = {
            "role": "assistant",
            "text": "I can help you with that switch"
        }

        with patch('app.core.learning_jobs.RedisConfig.queue_learning_job') as mock_queue:
            handle_conversation_message(123, message)

            # Should not process assistant message
            mock_watcher.detect_triggers.assert_not_called()
            mock_queue.assert_not_called()

    @patch('app.core.learning_jobs.RedisConfig')
    @patch('app.core.learning_jobs.ConversationWatcher')
    def test_handle_conversation_message_no_detections(self, mock_watcher_class, mock_redis_class):
        """Test handling message with no detections."""
        # Mock Redis
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis

        # Mock watcher
        mock_watcher = MagicMock()
        mock_watcher.detect_triggers.return_value = []
        mock_watcher_class.return_value = mock_watcher

        message = {
            "role": "user",
            "text": "This is a normal message"
        }

        with patch('app.core.learning_jobs.RedisConfig.queue_learning_job') as mock_queue:
            handle_conversation_message(123, message)

            # Should not queue job for no detections
            mock_watcher.detect_triggers.assert_called_once()
            mock_queue.assert_not_called()

    @patch('app.core.learning_jobs.RedisConfig')
    @patch('app.core.learning_jobs.ConversationWatcher')
    def test_handle_conversation_message_low_confidence(self, mock_watcher_class, mock_redis_class):
        """Test handling message with low confidence detections."""
        # Mock Redis
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis

        # Mock watcher
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

        message = {
            "role": "user",
            "text": "We're switching from A to B"
        }

        with patch('app.core.learning_jobs.RedisConfig.queue_learning_job') as mock_queue:
            handle_conversation_message(123, message)

            # Should not queue job for low confidence
            mock_watcher.detect_triggers.assert_called_once()
            mock_watcher.should_prompt_user.assert_called_once()
            mock_queue.assert_not_called()

    @patch('app.core.learning_jobs.RedisConfig')
    def test_wait_for_confirmation_confirmed(self, mock_redis_class):
        """Test waiting for confirmation when confirmed."""
        # Mock Redis
        mock_redis = MagicMock()
        mock_redis_class.get_confirmation.side_effect = [None, True]  # First None, then True
        mock_redis_class.return_value = mock_redis

        with patch('app.core.learning_jobs.time.sleep') as mock_sleep:
            result = wait_for_confirmation(123, "detection_123", timeout=1)

            assert result is True
            # Should sleep once
            mock_sleep.assert_called_once_with(1)

    @patch('app.core.learning_jobs.RedisConfig')
    def test_wait_for_confirmation_timeout(self, mock_redis_class):
        """Test waiting for confirmation with timeout."""
        # Mock Redis
        mock_redis = MagicMock()
        mock_redis_class.get_confirmation.return_value = None  # Always None
        mock_redis_class.return_value = mock_redis

        with patch('app.core.learning_jobs.time.sleep') as mock_sleep:
            result = wait_for_confirmation(123, "detection_123", timeout=0.1)

            assert result is False
            # Should sleep once
            mock_sleep.assert_called_once_with(0.1)

    @patch('app.core.learning_jobs.RedisConfig')
    def test_wait_for_confirmation_immediate(self, mock_redis_class):
        """Test waiting for confirmation when immediately confirmed."""
        # Mock Redis
        mock_redis = MagicMock()
        mock_redis_class.get_confirmation.return_value = True  # Immediately True
        mock_redis_class.return_value = mock_redis

        with patch('app.core.learning_jobs.time.sleep') as mock_sleep:
            result = wait_for_confirmation(123, "detection_123", timeout=1)

            assert result is True
            # Should not sleep
            mock_sleep.assert_not_called()

    @patch('app.core.learning_jobs.RedisConfig')
    @patch('app.core.learning_jobs.ConversationWatcher')
    def test_subscribe_to_conversations(self, mock_watcher_class, mock_redis_class):
        """Test subscribing to conversations."""
        # Mock Redis
        mock_redis = MagicMock()
        mock_pubsub = MagicMock()
        mock_redis.subscribe_to_conversation.return_value = mock_pubsub
        mock_redis_class.return_value = mock_redis

        # Mock watcher
        mock_watcher = MagicMock()
        mock_watcher_class.return_value = mock_watcher

        with patch('app.core.learning_jobs.time.sleep') as mock_sleep:
            # Mock pubsub messages
            message1 = json.dumps({"role": "user", "text": "Test message 1"})
            message2 = json.dumps({"role": "assistant", "text": "Test response"})
            invalid_message = "invalid json"

            # Mock pubsub listen
            def mock_listen():
                # First call returns message dict
                yield {"type": "message", "data": message1}
                # Second call returns message dict
                yield {"type": "message", "data": message2}
                # Third call returns invalid JSON
                yield {"type": "message", "data": invalid_message}
                # Fourth call is not message type
                yield {"type": "other", "data": "something"}
                # Fifth call stops listening
                raise KeyboardInterrupt()

            mock_pubsub.listen.side_effect = mock_listen()

            with patch('builtins.print'):  # Suppress print output
                try:
                    subscribe_to_conversations(123)
                except KeyboardInterrupt:
                    pass  # Expected

            # Should handle valid messages
            mock_watcher.handle_conversation_message.assert_any_call(123, {"role": "user", "text": "Test message 1"})
            mock_watcher.handle_conversation_message.assert_any_call(123, {"role": "assistant", "text": "Test response"})

            # Should ignore invalid JSON
            assert mock_watcher.handle_conversation_message.call_count == 2

            # Should close pubsub
            mock_pubsub.close.assert_called_once()


@pytest.mark.integration
class TestLearningJobsIntegration:
    """Integration tests for learning jobs."""

    @patch('app.core.learning_jobs.RedisConfig')
    @patch('app.core.learning_jobs.ConversationWatcher')
    def test_full_learning_workflow(self, mock_watcher_class, mock_redis_class, tmp_path):
        """Test full learning workflow from message to ingestion."""
        # Mock Redis
        mock_redis = MagicMock()
        mock_redis_class.set_confirmation.return_value = None
        mock_redis_class.queue_prompt_job.return_value = "prompt_job_123"
        mock_redis_class.get_confirmation.return_value = True
        mock_redis_class.queue_ingest_job.return_value = "ingest_job_123"
        mock_redis_class.return_value = mock_redis

        # Mock watcher
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

        # Create insights file
        insights_dir = tmp_path / ".claude-os" / "project-profile"
        insights_dir.mkdir(parents=True)
        insights_file = insights_dir / "LEARNED_INSIGHTS.md"
        insights_file.write_text("# Test Insights\n\nThis is a test insight.")

        # Mock API response
        with patch('app.core.learning_jobs.urllib.request') as mock_request:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_request.return_value.__enter__.return_value = mock_response

            # Start with message
            message = {"role": "user", "text": "We're switching from A to B"}

            with patch('app.core.learning_jobs.wait_for_confirmation') as mock_wait:
                mock_wait.return_value = True

                # Handle message
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

                # Verify full workflow
                mock_watcher.detect_triggers.assert_called_once()
                mock_redis.queue_learning_job.assert_called_once()
                mock_redis.queue_prompt_job.assert_called_once()
                mock_wait.assert_called_once()
                mock_redis.queue_ingest_job.assert_called_once()
                mock_request.assert_called_once()


@pytest.mark.unit
class TestRedisConfigLearning:
    """Test Redis configuration for learning jobs."""

    @patch('app.core.learning_jobs.redis.Redis')
    def test_redis_config_connection(self, mock_redis_class):
        """Test Redis configuration for learning jobs."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        # Get Redis instance
        redis = RedisConfig.get_redis()

        # Should create connection with correct parameters
        mock_redis_class.assert_called_once_with(
            host="localhost",
            port=6379,
            db=0,
            password=None,
            decode_responses=True
        )

        # Should be singleton
        redis2 = RedisConfig.get_redis()
        assert redis is redis2

    @patch('app.core.learning_jobs.redis.Redis')
    def test_redis_config_connection_failure(self, mock_redis_class):
        """Test Redis configuration connection failure."""
        mock_redis = MagicMock()
        mock_redis.ping.side_effect = Exception("Connection failed")
        mock_redis_class.return_value = mock_redis

        with pytest.raises(Exception, match="Redis connection failed"):
            RedisConfig.get_redis()

    @patch('app.core.learning_jobs.redis.Redis')
    @patch('app.core.learning_jobs.rq.Queue')
    def test_redis_config_queues(self, mock_redis_class, mock_queue_class):
        """Test Redis queue configuration."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        mock_queue = MagicMock()
        mock_queue_class.return_value = mock_queue

        # Get learning queue
        learning_queue = RedisConfig.get_learning_queue()

        # Should create queue with correct parameters
        mock_queue_class.assert_called_once_with(
            "claude-os:learning",
            connection=mock_redis
        )

        # Get prompt queue
        prompt_queue = RedisConfig.get_prompt_queue()

        # Should create queue with correct parameters
        mock_queue_class.assert_any_call(
            "claude-os:prompts",
            connection=mock_redis
        )

        # Get ingest queue
        ingest_queue = RedisConfig.get_ingest_queue()

        # Should create queue with correct parameters
        mock_queue_class.assert_any_call(
            "claude-os:ingest",
            connection=mock_redis
        )

    @patch('app.core.learning_jobs.redis.Redis')
    def test_redis_config_publish_conversation(self, mock_redis_class):
        """Test publishing conversation messages."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        redis = RedisConfig.get_redis()

        # Publish message
        RedisConfig.publish_conversation(123, "user", "Test message")

        # Should publish to correct channel
        redis.publish.assert_called_once_with(
            "claude-os:conversation:123",
            json.dumps({
                "role": "user",
                "text": "Test message",
                "timestamp": pytest.ANY  # Any timestamp
            })
        )

    @patch('app.core.learning_jobs.redis.Redis')
    def test_redis_config_subscribe_to_conversation(self, mock_redis_class):
        """Test subscribing to conversation messages."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        mock_pubsub = MagicMock()
        mock_redis.pubsub.return_value = mock_pubsub

        redis = RedisConfig.get_redis()

        # Subscribe to conversation
        pubsub = RedisConfig.subscribe_to_conversation(123)

        # Should subscribe to correct channel
        redis.pubsub.assert_called_once()
        mock_pubsub.subscribe.assert_called_once_with("claude-os:conversation:123")

        # Should return pubsub
        assert pubsub is mock_pubsub

    @patch('app.core.learning_jobs.redis.Redis')
    def test_redis_config_confirmation_operations(self, mock_redis_class):
        """Test Redis confirmation operations."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        redis = RedisConfig.get_redis()

        # Set confirmation
        RedisConfig.set_confirmation(123, "detection_123", True)

        # Should set with TTL
        redis.setex.assert_called_once_with(
            "claude_os:prompt:123:detection_123:confirmed",
            600,  # 10 minutes
            "True"
        )

        # Get confirmation (exists)
        redis.get.return_value = "True"
        result = RedisConfig.get_confirmation(123, "detection_123")

        assert result is True
        redis.get.assert_called_once_with(
            "claude_os:prompt:123:detection_123:confirmed"
        )

        # Get confirmation (doesn't exist)
        redis.get.return_value = None
        result = RedisConfig.get_confirmation(123, "nonexistent_detection")

        assert result is None
        redis.get.assert_called_once_with(
            "claude_os:prompt:123:nonexistent_detection:confirmed"
        )

    @patch('app.core.learning_jobs.redis.Redis')
    @patch('app.core.learning_jobs.rq.Queue')
    def test_redis_config_job_queueing(self, mock_redis_class, mock_queue_class):
        """Test Redis job queueing operations."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        mock_queue = MagicMock()
        mock_queue_class.return_value = mock_queue
        mock_queue.enqueue.return_value = MagicMock(id="job_123")

        redis = RedisConfig.get_redis()

        # Queue learning job
        job_id = RedisConfig.queue_learning_job(123, {"test": "data"})

        # Should enqueue with correct parameters
        mock_queue.enqueue.assert_called_once_with(
            "app.core.learning_jobs.process_learning_detection",
            123,
            {"test": "data"},
            job_timeout="5m"
        )

        assert job_id == "job_123"