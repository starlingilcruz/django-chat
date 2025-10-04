"""
Tests for Redis Streams messaging
"""

import pytest

from messaging.redis_stream import RedisStreamClient


@pytest.fixture
def redis_client():
    """Fixture for RedisStreamClient"""
    client = RedisStreamClient()
    client.redis_client.flushdb()
    yield client
    client.redis_client.flushdb()


@pytest.fixture
def test_conversation_id():
    """Fixture for test conversation ID"""
    return "test-conversation-123"


class TestRedisStream:
    """Test Redis Stream operations"""

    def test_add_message(self, redis_client, test_conversation_id):
        """Test adding a message to stream"""
        message_id = redis_client.add_message(
            conversation_id=test_conversation_id,
            user_id=1,
            content="Test message",
        )

        assert message_id is not None
        assert isinstance(message_id, str)

    def test_get_messages(self, redis_client, test_conversation_id):
        """Test retrieving messages from stream"""
        # Add some messages
        redis_client.add_message(
            conversation_id=test_conversation_id,
            user_id=1,
            content="Message 1",
        )
        redis_client.add_message(
            conversation_id=test_conversation_id,
            user_id=2,
            content="Message 2",
        )

        messages = redis_client.get_messages(
            conversation_id=test_conversation_id,
            limit=10,
        )

        assert len(messages) >= 2
        assert all("id" in msg for msg in messages)
        assert all("content" in msg for msg in messages)
        assert all("user_id" in msg for msg in messages)

    def test_ping_redis(self, redis_client):
        """Test Redis connectivity"""
        assert redis_client.ping_redis() is True
