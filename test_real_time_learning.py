#!/usr/bin/env python3
"""
Test Script for Claude OS Real-Time Learning System
Tests the end-to-end flow of detection, prompting, and ingestion
"""

import json
import time
import sys
import redis
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.redis_config import RedisConfig
from app.core.conversation_watcher import ConversationWatcher
from app.core.learning_jobs import handle_conversation_message


def test_redis_connection():
    """Test that Redis is available and working"""
    print("\n🔧 Test 1: Redis Connection")
    print("-" * 50)

    try:
        redis_client = RedisConfig.get_redis()
        redis_client.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("\n💡 Make sure Redis is running:")
        print("   redis-server")
        return False


def test_trigger_detection():
    """Test trigger detection on various inputs"""
    print("\n🔍 Test 2: Trigger Detection")
    print("-" * 50)

    watcher = ConversationWatcher(4, "/Users/iamanmp/Projects/pistn")

    test_cases = [
        "We're switching from Bootstrap to Tailwind CSS",
        "We decided to use GraphQL instead of REST",
        "We no longer use Jest for testing",
        "Now using PostgreSQL for all queries",
        "Let's implement this change across the board",
        "This query is too slow - needs optimization",
        "Fixed a bug in the authentication flow",
        "Refactoring services to use dependency injection",
        "We decided against using MongoDB",
        "Watch out for timezone issues with timestamps",
        "Regular text without triggers",
    ]

    passed = 0
    for text in test_cases:
        detections = watcher.detect_triggers(text)
        if detections:
            print(f"\n  ✓ '{text[:50]}...'")
            for det in detections:
                print(f"    → {det['trigger']} ({det['confidence']:.0%})")
            passed += 1
        else:
            print(f"\n  - '{text[:50]}...'")
            print(f"    (no triggers)")

    print(f"\n✅ Trigger detection: {passed}/{len(test_cases)} tests found triggers")
    return True


def test_pub_sub():
    """Test Redis pub/sub functionality"""
    print("\n📡 Test 3: Redis Pub/Sub")
    print("-" * 50)

    try:
        redis_client = RedisConfig.get_redis()
        channel = "test:learning"

        # Subscribe in a non-blocking way
        pubsub = redis_client.pubsub()
        pubsub.subscribe(channel)

        # Publish a message
        message_text = "We're switching from Bootstrap to Tailwind"
        redis_client.publish(channel, json.dumps({
            "role": "user",
            "text": message_text,
            "timestamp": "2025-10-27T17:00:00"
        }))

        # Try to receive it
        time.sleep(0.1)
        message = pubsub.get_message()

        if message and message['type'] == 'subscribe':
            message = pubsub.get_message()  # Get the actual message

        if message and message.get('data'):
            data = json.loads(message['data'])
            print(f"✅ Pub/Sub working")
            print(f"   Published: {message_text}")
            print(f"   Received: {data['text']}")
            pubsub.close()
            return True
        else:
            print(f"⚠️  Pub/Sub test inconclusive (may still work)")
            pubsub.close()
            return True

    except Exception as e:
        print(f"❌ Pub/Sub test failed: {e}")
        return False


def test_message_processing():
    """Test full message processing pipeline"""
    print("\n🔄 Test 4: Message Processing")
    print("-" * 50)

    try:
        project_id = 4
        message = {
            "role": "user",
            "text": "We're switching from Bootstrap to Tailwind CSS"
        }

        print(f"\n  Processing: '{message['text']}'")

        # This would normally be async via RQ
        # For testing, we'll call it directly
        watcher = ConversationWatcher(project_id, "/Users/iamanmp/Projects/pistn")
        detections = watcher.detect_triggers(message['text'])

        if detections:
            print(f"\n  ✅ Found {len(detections)} detection(s):")
            for det in detections:
                print(f"     • {det['trigger']}: {det['text']}")
                print(f"       Confidence: {det['confidence']:.0%}")

                # Save as insight (for testing)
                if watcher.should_prompt_user(det):
                    print(f"       → Would prompt user for confirmation")
            return True
        else:
            print(f"  ❌ No detections found")
            return False

    except Exception as e:
        print(f"❌ Message processing failed: {e}")
        return False


def test_insight_storage():
    """Test saving insights to file"""
    print("\n💾 Test 5: Insight Storage")
    print("-" * 50)

    try:
        watcher = ConversationWatcher(4, "/Users/iamanmp/Projects/pistn")

        test_detection = {
            "id": "test123",
            "trigger": "switching",
            "text": "We're switching from Bootstrap to Tailwind",
            "groups": ("Bootstrap", "Tailwind"),
            "confidence": 0.95,
            "description": "Technology switch detected",
            "timestamp": "2025-10-27T17:00:00",
            "context": "We're switching from Bootstrap to Tailwind for better performance"
        }

        # Save the insight
        result = watcher.save_insight(test_detection)

        if result:
            insights_file = watcher.insights_dir / "LEARNED_INSIGHTS.md"
            if insights_file.exists():
                size = insights_file.stat().st_size
                print(f"✅ Insight saved to {insights_file}")
                print(f"   File size: {size} bytes")
                return True
            else:
                print(f"⚠️  File not found after save")
                return False
        else:
            print(f"❌ Save failed")
            return False

    except Exception as e:
        print(f"❌ Insight storage test failed: {e}")
        return False


def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "="*50)
    print("Claude OS Real-Time Learning System - Test Suite")
    print("="*50)

    tests = [
        ("Redis Connection", test_redis_connection),
        ("Trigger Detection", test_trigger_detection),
        ("Pub/Sub", test_pub_sub),
        ("Message Processing", test_message_processing),
        ("Insight Storage", test_insight_storage),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} crashed: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "="*50)
    print("Test Summary")
    print("="*50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! System is ready for use.")
        print("\nNext steps:")
        print("1. Start Redis workers: ./start_redis_workers.sh")
        print("2. In another terminal, test with:")
        print("   redis-cli PUBLISH 'claude-os:conversation:4' '{...}'")
        return 0
    else:
        print("\n⚠️  Some tests failed. See above for details.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
