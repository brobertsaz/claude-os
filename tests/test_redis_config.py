"""
Tests for Redis configuration functionality.
"""

import pytest
import json
import time
from unittest.mock import patch, MagicMock

from app.core.redis_config import RedisConfig


@pytest.mark.unit
class TestRedisConfig:
    """Test RedisConfig class."""

    def test_redis_config_constants(self):
        """Test Redis configuration constants."""
        assert RedisConfig.REDIS_HOST == "localhost"
        assert RedisConfig.REDIS_PORT == 6379
        assert RedisConfig.REDIS_DB == 0
        assert RedisConfig.REDIS_PASSWORD is None

        assert RedisConfig.CONVERSATION_CHANNEL_TEMPLATE == "claude-os:conversation:{project_id}"
        assert RedisConfig.LEARNING_CHANNEL == "claude-os:learning"
        assert RedisConfig.NOTIFICATION_CHANNEL == "claude-os:notifications"

        assert RedisConfig.LEARNING_QUEUE == "claude-os:learning"
        assert RedisConfig.PROMPT_QUEUE == "claude-os:prompts"
        assert RedisConfig.INGEST_QUEUE == "claude-os:ingest"

        assert RedisConfig.PROMPT_KEY_TEMPLATE == "claude_os:prompt:{project_id}:{detection_id}"
        assert RedisConfig.CONFIRMATION_KEY_TEMPLATE == "claude_os:prompt:{project_id}:{detection_id}:confirmed"
        assert RedisConfig.WATCHED_MESSAGES_KEY_TEMPLATE == "claude_os:watched:{project_id}"

    @patch('app.core.redis_config.redis.Redis')
    def test_get_redis_singleton(self, mock_redis_class):
        """Test that get_redis returns singleton."""
        mock_redis = MagicMock()
        mock_redis_class.return_value = mock_redis

        # Clear any existing instance
        import app.core.redis_config
        app.core.redis_config.RedisConfig._redis_instance = None

        # Get instance twice
        redis1 = RedisConfig.get_redis()
        redis2 = RedisConfig.get_redis()

        # Should create only once
        mock_redis_class.assert_called_once()
        assert redis1 is redis2
        assert redis1 is mock_redis

    @patch('app.core.redis_config.redis.Redis')
    def test_get_redis_connection_parameters(self, mock_redis_class):
        """Test that get_redis uses correct connection parameters."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        redis = RedisConfig.get_redis()

        # Should create with correct parameters
        mock_redis_class.assert_called_once_with(
            host="localhost",
            port=6379,
            db=0,
            password=None,
            decode_responses=True
        )

    @patch('app.core.redis_config.redis.Redis')
    def test_get_redis_connection_failure(self, mock_redis_class):
        """Test that get_redis handles connection failure."""
        mock_redis_class.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Redis connection failed"):
            RedisConfig.get_redis()

    @patch('app.core.redis_config.redis.Redis')
    @patch('app.core.redis_config.rq.Queue')
    def test_get_learning_queue(self, mock_redis_class, mock_queue_class):
        """Test getting learning queue."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        mock_queue = MagicMock()
        mock_queue_class.return_value = mock_queue

        queue = RedisConfig.get_learning_queue()

        # Should create queue with correct parameters
        mock_queue_class.assert_called_once_with(
            "claude-os:learning",
            connection=mock_redis
        )
        assert queue is mock_queue

    @patch('app.core.redis_config.redis.Redis')
    @patch('app.core.redis_config.rq.Queue')
    def test_get_prompt_queue(self, mock_redis_class, mock_queue_class):
        """Test getting prompt queue."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        mock_queue = MagicMock()
        mock_queue_class.return_value = mock_queue

        queue = RedisConfig.get_prompt_queue()

        # Should create queue with correct parameters
        mock_queue_class.assert_called_once_with(
            "claude-os:prompts",
            connection=mock_redis
        )
        assert queue is mock_queue

    @patch('app.core.redis_config.redis.Redis')
    @patch('app.core.redis_config.rq.Queue')
    def test_get_ingest_queue(self, mock_redis_class, mock_queue_class):
        """Test getting ingest queue."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        mock_queue = MagicMock()
        mock_queue_class.return_value = mock_queue

        queue = RedisConfig.get_ingest_queue()

        # Should create queue with correct parameters
        mock_queue_class.assert_called_once_with(
            "claude-os:ingest",
            connection=mock_redis
        )
        assert queue is mock_queue

    @patch('app.core.redis_config.redis.Redis')
    def test_publish_conversation(self, mock_redis_class):
        """Test publishing conversation message."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        redis = RedisConfig.get_redis()

        # Publish message
        project_id = 123
        role = "user"
        text = "Test message"

        RedisConfig.publish_conversation(project_id, role, text)

        # Should publish to correct channel
        mock_redis.publish.assert_called_once()
        call_args = mock_redis.publish.call_args
        assert call_args[0][0] == "claude-os:conversation:123"

        # Check message format
        message = json.loads(call_args[0][1])
        assert message["role"] == role
        assert message["text"] == text
        assert "timestamp" in message

    @patch('app.core.redis_config.redis.Redis')
    def test_subscribe_to_conversation(self, mock_redis_class):
        """Test subscribing to conversation messages."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        mock_pubsub = MagicMock()
        mock_redis.pubsub.return_value = mock_pubsub

        redis = RedisConfig.get_redis()

        # Subscribe to conversation
        project_id = 123
        pubsub = RedisConfig.subscribe_to_conversation(project_id)

        # Should subscribe to correct channel
        mock_redis.pubsub.assert_called_once()
        mock_pubsub.subscribe.assert_called_once_with("claude-os:conversation:123")
        assert pubsub is mock_pubsub

    @patch('app.core.redis_config.redis.Redis')
    def test_queue_learning_job(self, mock_redis_class, mock_queue_class):
        """Test queuing learning job."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        mock_queue = MagicMock()
        mock_queue_class.return_value = mock_queue
        mock_queue.enqueue.return_value = MagicMock(id="job_123")

        redis = RedisConfig.get_redis()

        # Queue job
        project_id = 123
        detection = {"id": "detection_123", "trigger": "switching"}

        job_id = RedisConfig.queue_learning_job(project_id, detection)

        # Should enqueue with correct parameters
        mock_queue.enqueue.assert_called_once_with(
            "app.core.learning_jobs.process_learning_detection",
            project_id,
            detection,
            job_timeout="5m"
        )
        assert job_id == "job_123"

    @patch('app.core.redis_config.redis.Redis')
    def test_queue_prompt_job(self, mock_redis_class, mock_queue_class):
        """Test queuing prompt job."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        mock_queue = MagicMock()
        mock_queue_class.return_value = mock_queue
        mock_queue.enqueue.return_value = MagicMock(id="prompt_job_123")

        redis = RedisConfig.get_redis()

        # Queue prompt job
        project_id = 123
        detection = {"id": "detection_123", "trigger": "switching"}

        job_id = RedisConfig.queue_prompt_job(project_id, detection)

        # Should enqueue with correct parameters
        mock_queue.enqueue.assert_called_once_with(
            "app.core.learning_jobs.prompt_user_for_confirmation",
            project_id,
            detection,
            job_timeout="10m"
        )
        assert job_id == "prompt_job_123"

    @patch('app.core.redis_config.redis.Redis')
    def test_queue_ingest_job(self, mock_redis_class, mock_queue_class):
        """Test queuing ingest job."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        mock_queue = MagicMock()
        mock_queue_class.return_value = mock_queue
        mock_queue.enqueue.return_value = MagicMock(id="ingest_job_123")

        redis = RedisConfig.get_redis()

        # Queue ingest job
        project_id = 123
        file_path = "/path/to/file"

        job_id = RedisConfig.queue_ingest_job(project_id, file_path)

        # Should enqueue with correct parameters
        mock_queue.enqueue.assert_called_once_with(
            "app.core.learning_jobs.ingest_to_mcp",
            project_id,
            file_path,
            job_timeout="5m"
        )
        assert job_id == "ingest_job_123"

    @patch('app.core.redis_config.redis.Redis')
    def test_set_confirmation(self, mock_redis_class):
        """Test setting user confirmation."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        redis = RedisConfig.get_redis()

        # Set confirmation
        project_id = 123
        detection_id = "detection_123"
        confirmed = True

        RedisConfig.set_confirmation(project_id, detection_id, confirmed)

        # Should set with TTL
        mock_redis.setex.assert_called_once_with(
            "claude_os:prompt:123:detection_123:confirmed",
            600,  # 10 minutes
            "True"
        )

    @patch('app.core.redis_config.redis.Redis')
    def test_set_confirmation_false(self, mock_redis_class):
        """Test setting user confirmation to false."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        redis = RedisConfig.get_redis()

        # Set confirmation to false
        project_id = 123
        detection_id = "detection_123"
        confirmed = False

        RedisConfig.set_confirmation(project_id, detection_id, confirmed)

        # Should set with TTL
        mock_redis.setex.assert_called_once_with(
            "claude_os:prompt:123:detection_123:confirmed",
            600,  # 10 minutes
            "False"
        )

    @patch('app.core.redis_config.redis.Redis')
    def test_get_confirmation_exists(self, mock_redis_class):
        """Test getting confirmation when it exists."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis
        mock_redis.get.return_value = "True"

        redis = RedisConfig.get_redis()

        # Get confirmation
        project_id = 123
        detection_id = "detection_123"

        result = RedisConfig.get_confirmation(project_id, detection_id)

        # Should get from Redis
        mock_redis.get.assert_called_once_with(
            "claude_os:prompt:123:detection_123:confirmed"
        )
        assert result is True

    @patch('app.core.redis_config.redis.Redis')
    def test_get_confirmation_not_exists(self, mock_redis_class):
        """Test getting confirmation when it doesn't exist."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis
        mock_redis.get.return_value = None

        redis = RedisConfig.get_redis()

        # Get confirmation
        project_id = 123
        detection_id = "nonexistent_detection"

        result = RedisConfig.get_confirmation(project_id, detection_id)

        # Should get from Redis
        mock_redis.get.assert_called_once_with(
            "claude_os:prompt:123:nonexistent_detection:confirmed"
        )
        assert result is None

    @patch('app.core.redis_config.redis.Redis')
    def test_get_confirmation_string_value(self, mock_redis_class):
        """Test getting confirmation when stored as string."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis
        mock_redis.get.return_value = "true"  # Lowercase string

        redis = RedisConfig.get_redis()

        # Get confirmation
        project_id = 123
        detection_id = "detection_123"

        result = RedisConfig.get_confirmation(project_id, detection_id)

        # Should handle string value
        mock_redis.get.assert_called_once_with(
            "claude_os:prompt:123:detection_123:confirmed"
        )
        assert result is True

    @patch('app.core.redis_config.redis.Redis')
    def test_get_confirmation_false_string_value(self, mock_redis_class):
        """Test getting confirmation when stored as false string."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis
        mock_redis.get.return_value = "false"  # Lowercase string

        redis = RedisConfig.get_redis()

        # Get confirmation
        project_id = 123
        detection_id = "detection_123"

        result = RedisConfig.get_confirmation(project_id, detection_id)

        # Should handle string value
        mock_redis.get.assert_called_once_with(
            "claude_os:prompt:123:detection_123:confirmed"
        )
        assert result is False


@pytest.mark.integration
class TestRedisConfigIntegration:
    """Integration tests for Redis configuration."""

    @patch('app.core.redis_config.redis.Redis')
    @patch('app.core.redis_config.rq.Queue')
    def test_full_workflow(self, mock_redis_class, mock_queue_class):
        """Test full Redis workflow with all operations."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        mock_queue = MagicMock()
        mock_queue_class.return_value = mock_queue
        mock_queue.enqueue.return_value = MagicMock(id="job_123")

        redis = RedisConfig.get_redis()

        # Test full workflow
        project_id = 123
        detection = {"id": "detection_123", "trigger": "switching"}

        # 1. Publish conversation
        RedisConfig.publish_conversation(project_id, "user", "Test message")

        # 2. Queue learning job
        job_id = RedisConfig.queue_learning_job(project_id, detection)

        # 3. Set initial confirmation
        RedisConfig.set_confirmation(project_id, "detection_123", False)

        # 4. Get confirmation (should be False initially)
        result = RedisConfig.get_confirmation(project_id, "detection_123")
        assert result is False

        # 5. Update confirmation
        RedisConfig.set_confirmation(project_id, "detection_123", True)

        # 6. Get confirmation (should be True now)
        result = RedisConfig.get_confirmation(project_id, "detection_123")
        assert result is True

        # Verify all Redis calls
        assert mock_redis.publish.call_count == 1
        assert mock_queue.enqueue.call_count == 1
        assert mock_redis.setex.call_count == 2
        assert mock_redis.get.call_count == 2

    @patch('app.core.redis_config.redis.Redis')
    def test_connection_error_handling(self, mock_redis_class):
        """Test Redis connection error handling."""
        mock_redis_class.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Redis connection failed"):
            RedisConfig.get_redis()

    @patch('app.core.redis_config.redis.Redis')
    def test_queue_error_handling(self, mock_redis_class, mock_queue_class):
        """Test Redis queue error handling."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        mock_queue = MagicMock()
        mock_queue_class.return_value = mock_queue
        mock_queue.enqueue.side_effect = Exception("Queue error")

        redis = RedisConfig.get_redis()

        # Should handle queue error gracefully
        with pytest.raises(Exception, match="Queue error"):
            RedisConfig.queue_learning_job(123, {"test": "data"})

    @patch('app.core.redis_config.redis.Redis')
    def test_publish_error_handling(self, mock_redis_class):
        """Test Redis publish error handling."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis
        mock_redis.publish.side_effect = Exception("Publish error")

        redis = RedisConfig.get_redis()

        # Should handle publish error gracefully
        with pytest.raises(Exception, match="Publish error"):
            RedisConfig.publish_conversation(123, "user", "test")

    @patch('app.core.redis_config.redis.Redis')
    def test_set_get_confirmation_error_handling(self, mock_redis_class):
        """Test Redis set/get confirmation error handling."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis
        mock_redis.setex.side_effect = Exception("Set error")
        mock_redis.get.side_effect = Exception("Get error")

        redis = RedisConfig.get_redis()

        # Should handle set error gracefully
        with pytest.raises(Exception, match="Set error"):
            RedisConfig.set_confirmation(123, "detection_123", True)

        # Should handle get error gracefully
        with pytest.raises(Exception, match="Get error"):
            RedisConfig.get_confirmation(123, "detection_123")

    @patch('app.core.redis_config.redis.Redis')
    def test_subscribe_error_handling(self, mock_redis_class):
        """Test Redis subscribe error handling."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis
        mock_redis.pubsub.side_effect = Exception("Pubsub error")

        redis = RedisConfig.get_redis()

        # Should handle pubsub error gracefully
        with pytest.raises(Exception, match="Pubsub error"):
            RedisConfig.subscribe_to_conversation(123)

    @patch('app.core.redis_config.redis.Redis')
    def test_queue_job_timeout_configuration(self, mock_redis_class, mock_queue_class):
        """Test that queue jobs use correct timeout configuration."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        mock_queue = MagicMock()
        mock_queue_class.return_value = mock_queue

        redis = RedisConfig.get_redis()

        # Queue learning job
        RedisConfig.queue_learning_job(123, {"test": "data"})

        # Should use 5m timeout
        mock_queue.enqueue.assert_called_once_with(
            "app.core.learning_jobs.process_learning_detection",
            123,
            {"test": "data"},
            job_timeout="5m"
        )

    @patch('app.core.redis_config.redis.Redis')
    def test_queue_prompt_job_timeout_configuration(self, mock_redis_class, mock_queue_class):
        """Test that prompt queue jobs use correct timeout configuration."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        mock_queue = MagicMock()
        mock_queue_class.return_value = mock_queue

        redis = RedisConfig.get_redis()

        # Queue prompt job
        RedisConfig.queue_prompt_job(123, {"test": "data"})

        # Should use 10m timeout
        mock_queue.enqueue.assert_called_once_with(
            "app.core.learning_jobs.prompt_user_for_confirmation",
            123,
            {"test": "data"},
            job_timeout="10m"
        )

    @patch('app.core.redis_config.redis.Redis')
    def test_queue_ingest_job_timeout_configuration(self, mock_redis_class, mock_queue_class):
        """Test that ingest queue jobs use correct timeout configuration."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        mock_queue = MagicMock()
        mock_queue_class.return_value = mock_queue

        redis = RedisConfig.get_redis()

        # Queue ingest job
        RedisConfig.queue_ingest_job(123, "/path/to/file")

        # Should use 5m timeout
        mock_queue.enqueue.assert_called_once_with(
            "app.core.learning_jobs.ingest_to_mcp",
            123,
            "/path/to/file",
            job_timeout="5m"
        )

    @patch('app.core.redis_config.redis.Redis')
    def test_set_confirmation_ttl_configuration(self, mock_redis_class):
        """Test that set confirmation uses correct TTL configuration."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        redis = RedisConfig.get_redis()

        # Set confirmation
        RedisConfig.set_confirmation(123, "detection_123", True)

        # Should use 600 seconds TTL (10 minutes)
        mock_redis.setex.assert_called_once_with(
            "claude_os:prompt:123:detection_123:confirmed",
            600,  # 10 minutes
            "True"
        )

    @patch('app.core.redis_config.redis.Redis')
    def test_publish_conversation_message_format(self, mock_redis_class):
        """Test that publish conversation uses correct message format."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        redis = RedisConfig.get_redis()

        # Publish message
        project_id = 123
        role = "user"
        text = "Test message"

        RedisConfig.publish_conversation(project_id, role, text)

        # Check message format
        call_args = mock_redis.publish.call_args
        message = json.loads(call_args[0][1])

        assert message["role"] == role
        assert message["text"] == text
        assert "timestamp" in message
        assert isinstance(message["timestamp"], str)

    @patch('app.core.redis_config.redis.Redis')
    def test_subscribe_to_conversation_channel_format(self, mock_redis_class):
        """Test that subscribe uses correct channel format."""
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        mock_redis_class.return_value = mock_redis

        mock_pubsub = MagicMock()
        mock_redis.pubsub.return_value = mock_pubsub

        redis = RedisConfig.get_redis()

        # Subscribe to conversation
        project_id = 123
        pubsub = RedisConfig.subscribe_to_conversation(project_id)

        # Should subscribe to correct channel
        mock_redis.pubsub.assert_called_once()
        mock_pubsub.subscribe.assert_called_once_with("claude-os:conversation:123")