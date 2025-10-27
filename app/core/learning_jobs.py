#!/usr/bin/env python3
"""
Claude OS Learning Jobs
RQ jobs for real-time knowledge capture and MCP updates
"""

import json
import time
from pathlib import Path
from typing import Dict, Optional
import urllib.request
import urllib.error

from app.core.conversation_watcher import ConversationWatcher
from app.core.redis_config import RedisConfig


def process_learning_detection(project_id: int, detection: Dict) -> Dict:
    """
    Process a detected learning opportunity
    - Store in Redis
    - Prompt user
    - Update knowledge base if confirmed
    """
    print(f"\n🔍 Processing detection: {detection['trigger']}")
    print(f"   Text: {detection['text']}")

    # Store prompt in Redis with TTL (10 minutes for user response)
    RedisConfig.set_confirmation(project_id, detection["id"], False)

    # Queue user prompt
    prompt_job_id = RedisConfig.queue_prompt_job(project_id, detection)
    print(f"   ⏳ Waiting for user confirmation (job: {prompt_job_id})")

    # Wait for user confirmation (up to 10 minutes)
    confirmed = wait_for_confirmation(project_id, detection["id"], timeout=600)

    if confirmed:
        print(f"   ✅ User confirmed! Updating knowledge base...")
        ingest_job_id = RedisConfig.queue_ingest_job(project_id, str(Path.cwd()))
        return {
            "status": "confirmed",
            "ingest_job_id": ingest_job_id,
            "detection_id": detection["id"],
        }
    else:
        print(f"   ⏭️  User skipped or timed out")
        return {"status": "skipped", "detection_id": detection["id"]}


def prompt_user_for_confirmation(project_id: int, detection: Dict) -> Dict:
    """
    Prompt user to confirm if we should remember this
    In real Claude Code CLI, this would show an interactive prompt
    """
    print(f"\n🔔 KNOWLEDGE UPDATE DETECTED:")
    print(f"   Trigger: {detection['trigger']}")
    print(f"   Confidence: {detection['confidence']:.0%}")
    print(f"   Text: {detection['text']}")
    print(f"   Context: {detection.get('context', '')}\n")

    # In a real CLI, this would be interactive
    # For now, we'll use environment variable or Redis for response
    # In production, Claude Code CLI would set the confirmation
    print(f"   Waiting for confirmation (check Redis key)...")
    print(f"   Key: claude_os:prompt:{project_id}:{detection['id']}:confirmed")

    return {
        "status": "prompted",
        "detection_id": detection["id"],
        "trigger": detection["trigger"],
    }


def ingest_to_mcp(project_id: int, project_path: str) -> Dict:
    """
    Ingest the learned insights file to project_profile MCP
    """
    try:
        watcher = ConversationWatcher(project_id, project_path)
        insights_file = (
            Path(project_path) / ".claude-os" / "project-profile" / "LEARNED_INSIGHTS.md"
        )

        if not insights_file.exists():
            print(f"⚠️  No insights file found at {insights_file}")
            return {"status": "error", "message": "insights_file_not_found"}

        # Read the insights file
        with open(insights_file, "r") as f:
            content = f.read()

        # Prepare ingest payload
        payload = {
            "filename": "LEARNED_INSIGHTS.md",
            "content": content,
            "mcp_type": "project_profile",
            "metadata": {
                "type": "learned_insights",
                "auto_generated": True,
                "learning_system": "real_time_watcher",
            },
        }

        # Post to Claude OS API
        api_url = "http://localhost:8051"  # Should be configurable
        ingest_url = f"{api_url}/api/projects/{project_id}/ingest-document"

        payload_json = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            ingest_url,
            data=payload_json,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status in [200, 201]:
                print(f"   ✅ Ingested to project_profile MCP")
                return {
                    "status": "ingested",
                    "project_id": project_id,
                    "file": str(insights_file),
                }
            else:
                return {
                    "status": "error",
                    "message": f"API returned {response.status}",
                }

    except Exception as e:
        print(f"⚠️  Error ingesting to MCP: {e}")
        return {"status": "error", "message": str(e)}


def handle_conversation_message(project_id: int, message: Dict) -> None:
    """
    Process an incoming conversation message
    - Detect triggers
    - Queue learning jobs for high-confidence detections
    """
    try:
        text = message.get("text", "")
        role = message.get("role", "user")

        # Only learn from user messages (not Claude responses)
        if role != "user":
            return

        watcher = ConversationWatcher(project_id, ".")
        detections = watcher.detect_triggers(text)

        print(f"\n🔍 Analyzing message from {role}...")

        if not detections:
            print(f"   No learning opportunities detected")
            return

        print(f"   🎯 Found {len(detections)} potential learning opportunities:")

        for detection in detections:
            if watcher.should_prompt_user(detection):
                print(
                    f"      • {detection['trigger']}: {detection['text'][:50]}... (confidence: {detection['confidence']:.0%})"
                )
                # Queue the learning job
                job_id = RedisConfig.queue_learning_job(project_id, detection)
                print(f"        → Queued (job: {job_id})")

    except Exception as e:
        print(f"⚠️  Error processing message: {e}")


def wait_for_confirmation(
    project_id: int, detection_id: str, timeout: int = 600
) -> Optional[bool]:
    """
    Wait for user confirmation with timeout
    Checks Redis every second for confirmation
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        confirmed = RedisConfig.get_confirmation(project_id, detection_id)

        if confirmed is not None:
            return confirmed

        # Check every second
        time.sleep(1)

    # Timeout - return False
    return False


def subscribe_to_conversations(project_id: int) -> None:
    """
    Subscribe to conversation channel and process messages
    Runs continuously, processing each message as it arrives
    """
    print(f"\n🎧 Subscribing to conversations for project {project_id}...")

    pubsub = RedisConfig.subscribe_to_conversation(project_id)

    try:
        for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    handle_conversation_message(project_id, data)
                except json.JSONDecodeError:
                    pass  # Invalid JSON, skip

    except KeyboardInterrupt:
        print("\n👋 Unsubscribing from conversations...")
        pubsub.close()


if __name__ == "__main__":
    # Testing
    import sys

    if len(sys.argv) > 1:
        project_id = int(sys.argv[1])
        subscribe_to_conversations(project_id)
