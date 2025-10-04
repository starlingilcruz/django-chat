
import logging

import redis
from django.conf import settings

logger = logging.getLogger(__name__)


class MessageThrottler:
    """
    Rate limiter for messages using Redis
    """

    def __init__(self, max_messages: int = 10, window_seconds: int = 60):
        """
        Args:
            max_messages: Maximum messages allowed in the time window
            window_seconds: Time window in seconds
        """
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.max_messages = max_messages
        self.window_seconds = window_seconds

    def _get_throttle_key(self, user_id: int, conversation_id: str) -> str:
        """Generate Redis key for throttling"""
        return f"throttle:{user_id}:{conversation_id}"

    def is_allowed(self, user_id: int, conversation_id: str) -> bool:
        """
        Check if user is allowed to send a message

        Args:
            user_id: ID of the user
            conversation_id: UUID of the conversation

        Returns:
            True if allowed, False if throttled
        """
        try:
            key = self._get_throttle_key(user_id, conversation_id)

            # Increment counter
            count = self.redis_client.incr(key)

            # Set expiry on first message
            if count == 1:
                self.redis_client.expire(key, self.window_seconds)

            is_allowed = count <= self.max_messages

            if not is_allowed:
                logger.warning(
                    "User throttled",
                    extra={
                        "user_id": user_id,
                        "conversation_id": conversation_id,
                        "count": count,
                        "max": self.max_messages,
                    },
                )

            return is_allowed

        except redis.RedisError as e:
            logger.error(
                "Throttle check failed",
                extra={
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "error": str(e),
                },
            )
            # Allow message on Redis failure (fail open)
            return True

    def get_remaining(self, user_id: int, conversation_id: str) -> int:
        """
        Get remaining messages allowed in current window

        Args:
            user_id: ID of the user
            conversation_id: UUID of the conversation

        Returns:
            Number of remaining messages allowed
        """
        try:
            key = self._get_throttle_key(user_id, conversation_id)
            count = int(self.redis_client.get(key) or 0)
            return max(0, self.max_messages - count)
        except redis.RedisError:
            return self.max_messages


# Default throttler instance
message_throttler = MessageThrottler(max_messages=10, window_seconds=60)
