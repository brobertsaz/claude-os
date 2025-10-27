#!/usr/bin/env python3
"""
Redis Configuration for Claude OS Real-Time Learning System
Manages connections, pub/sub channels, and job queues
"""

import os
from redis import Redis
from rq import Queue, Worker
from typing import Optional


class RedisConfig:
    """Redis connection and configuration management"""

    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

    # Pub/Sub channels
    CONVERSATION_CHANNEL_TEMPLATE = "claude-os:conversation:{project_id}"
    LEARNING_CHANNEL = "claude-os:learning"
    NOTIFICATION_CHANNEL = "claude-os:notifications"

    # Job queue names
    LEARNING_QUEUE = "claude-os:learning"
    PROMPT_QUEUE = "claude-os:prompts"
    INGEST_QUEUE = "claude-os:ingest"

    # Key patterns
    PROMPT_KEY_TEMPLATE = "claude_os:prompt:{project_id}:{detection_id}"
    CONFIRMATION_KEY_TEMPLATE = "claude_os:prompt:{project_id}:{detection_id}:confirmed"
    WATCHED_MESSAGES_KEY_TEMPLATE = "claude_os:watched:{project_id}"

    _redis_instance: Optional[Redis] = None

    @classmethod
    def get_redis(cls) -> Redis:
        """Get or create Redis connection (singleton)"""
        if cls._redis_instance is None:
            cls._redis_instance = Redis(
                host=cls.REDIS_HOST,
                port=cls.REDIS_PORT,
                db=cls.REDIS_DB,
                password=cls.REDIS_PASSWORD,
                decode_responses=True,  # Auto-decode responses to strings
            )
            # Test connection
            try:
                cls._redis_instance.ping()
            except Exception as e:
                print(f"⚠️  Redis connection failed: {e}")
                raise

        return cls._redis_instance

    @classmethod
    def get_learning_queue(cls) -> Queue:
        """Get the learning job queue"""
        return Queue(cls.LEARNING_QUEUE, connection=cls.get_redis())

    @classmethod
    def get_prompt_queue(cls) -> Queue:
        """Get the prompt notification queue"""
        return Queue(cls.PROMPT_QUEUE, connection=cls.get_redis())

    @classmethod
    def get_ingest_queue(cls) -> Queue:
        """Get the MCP ingestion queue"""
        return Queue(cls.INGEST_QUEUE, connection=cls.get_redis())

    @classmethod
    def publish_conversation(cls, project_id: int, role: str, text: str) -> None:
        """Publish a conversation message to Redis"""
        import json
        from datetime import datetime

        redis = cls.get_redis()
        channel = cls.CONVERSATION_CHANNEL_TEMPLATE.format(project_id=project_id)

        message = json.dumps(
            {
                "role": role,
                "text": text,
                "timestamp": datetime.now().isoformat(),
            }
        )

        redis.publish(channel, message)

    @classmethod
    def subscribe_to_conversation(cls, project_id: int):
        """Subscribe to conversation channel (blocking)"""
        redis = cls.get_redis()
        channel = cls.CONVERSATION_CHANNEL_TEMPLATE.format(project_id=project_id)
        pubsub = redis.pubsub()
        pubsub.subscribe(channel)

        print(f"🔔 Listening to conversations for project {project_id}...")
        return pubsub

    @classmethod
    def queue_learning_job(cls, project_id: int, detection: dict) -> str:
        """Queue a learning job"""
        queue = cls.get_learning_queue()
        job = queue.enqueue(
            "app.core.learning_jobs.process_learning_detection",
            project_id,
            detection,
            job_timeout="5m",
        )
        return job.id

    @classmethod
    def queue_prompt_job(cls, project_id: int, detection: dict) -> str:
        """Queue a user prompt job"""
        queue = cls.get_prompt_queue()
        job = queue.enqueue(
            "app.core.learning_jobs.prompt_user_for_confirmation",
            project_id,
            detection,
            job_timeout="10m",  # Give user 10 minutes to respond
        )
        return job.id

    @classmethod
    def queue_ingest_job(cls, project_id: int, file_path: str) -> str:
        """Queue an MCP ingestion job"""
        queue = cls.get_ingest_queue()
        job = queue.enqueue(
            "app.core.learning_jobs.ingest_to_mcp",
            project_id,
            file_path,
            job_timeout="5m",
        )
        return job.id

    @classmethod
    def set_confirmation(cls, project_id: int, detection_id: str, confirmed: bool) -> None:
        """Record user confirmation for a detection"""
        redis = cls.get_redis()
        key = cls.CONFIRMATION_KEY_TEMPLATE.format(
            project_id=project_id, detection_id=detection_id
        )
        redis.setex(key, 600, str(confirmed))  # Expire after 10 minutes

    @classmethod
    def get_confirmation(cls, project_id: int, detection_id: str) -> Optional[bool]:
        """Get user confirmation status"""
        redis = cls.get_redis()
        key = cls.CONFIRMATION_KEY_TEMPLATE.format(
            project_id=project_id, detection_id=detection_id
        )
        value = redis.get(key)
        if value is None:
            return None
        return value.lower() == "true"


def start_redis_workers():
    """Start RQ workers for job processing"""
    import signal

    queues = [
        RedisConfig.LEARNING_QUEUE,
        RedisConfig.PROMPT_QUEUE,
        RedisConfig.INGEST_QUEUE,
    ]

    with Worker(
        queues, connection=RedisConfig.get_redis(), job_monitoring_interval=10
    ) as worker:
        print(f"🚀 Starting Redis workers for: {', '.join(queues)}")

        def handle_signal(signum, frame):
            print("\n👋 Shutting down workers...")
            worker.request_stop()

        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)

        worker.work(with_scheduler=True)


if __name__ == "__main__":
    # Test connection
    try:
        redis = RedisConfig.get_redis()
        redis.ping()
        print("✅ Redis connection successful")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        exit(1)
