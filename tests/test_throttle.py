"""
Tests for message throttling
"""

import pytest
import redis
from django.conf import settings

from messaging.throttle import MessageThrottler


@pytest.fixture
def redis_client():
    """Fixture for Redis client"""
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    client.flushdb()
    yield client
    client.flushdb()


@pytest.fixture
def throttler(redis_client):
    """Fixture for MessageThrottler with low limits for testing"""
    return MessageThrottler(max_messages=3, window_seconds=60)


class TestMessageThrottler:
    """Test message throttling"""

    def test_allow_under_limit(self, throttler):
        """Test that messages are allowed under the limit"""
        user_id = 1
        conversation_id = "test-conv-1"

        # Send 3 messages (under limit)
        for _ in range(3):
            assert throttler.is_allowed(user_id, conversation_id) is True

    def test_block_over_limit(self, throttler):
        """Test that messages are blocked over the limit"""
        user_id = 2
        conversation_id = "test-conv-2"

        # Send 3 messages (at limit)
        for _ in range(3):
            throttler.is_allowed(user_id, conversation_id)

        # 4th message should be blocked
        assert throttler.is_allowed(user_id, conversation_id) is False

    def test_get_remaining(self, throttler):
        """Test getting remaining messages count"""
        user_id = 3
        conversation_id = "test-conv-3"

        # Initial remaining should be max
        remaining = throttler.get_remaining(user_id, conversation_id)
        assert remaining == 3

        # After 1 message
        throttler.is_allowed(user_id, conversation_id)
        remaining = throttler.get_remaining(user_id, conversation_id)
        assert remaining == 2
