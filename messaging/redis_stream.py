"""
Redis Streams layer for message storage and retrieval
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import redis
from django.conf import settings

logger = logging.getLogger(__name__)


class RedisStreamError(Exception):
    """Custom exception for Redis Stream operations"""

    pass


class RedisStreamClient:
    """
    Client for managing messages in Redis Streams
    """

    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def _get_stream_key(self, conversation_id: str) -> str:
        """Generate Redis stream key for a conversation"""
        return f"stream:conv:{conversation_id}"

    def add_message(
        self,
        conversation_id: str,
        user_id: int,
        content: str,
        maxlen: int = 5000,
    ) -> str:
        """
        Add a message to a conversation stream

        Args:
            conversation_id: UUID of the conversation
            user_id: ID of the user sending the message
            content: Message content
            maxlen: Maximum length of the stream (default: 5000)

        Returns:
            Message ID from Redis Streams

        Raises:
            RedisStreamError: If message addition fails
        """
        try:
            stream_key = self._get_stream_key(conversation_id)
            message_data = {
                "user_id": str(user_id),
                "content": content,
                "timestamp": datetime.utcnow().isoformat(),
            }

            message_id = self.redis_client.xadd(
                stream_key,
                message_data,
                maxlen=maxlen,
                approximate=True,
            )

            logger.info(
                "Message added to Redis Stream",
                extra={
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "message_id": message_id,
                },
            )

            return message_id

        except redis.RedisError as e:
            logger.error(
                "Failed to add message to Redis Stream",
                extra={
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "error": str(e),
                },
            )
            raise RedisStreamError(f"Failed to add message: {str(e)}") from e

    def get_messages(
        self,
        conversation_id: str,
        from_id: str = "-",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve messages from a conversation stream

        Args:
            conversation_id: UUID of the conversation
            from_id: Message ID to start from (default: "-" for beginning)
            limit: Maximum number of messages to retrieve (default: 50)

        Returns:
            List of message dictionaries

        Raises:
            RedisStreamError: If message retrieval fails
        """
        try:
            stream_key = self._get_stream_key(conversation_id)

            # Use XRANGE to get messages
            if from_id == "-":
                # Get latest messages
                messages = self.redis_client.xrevrange(
                    stream_key,
                    "+",
                    "-",
                    count=limit,
                )
                messages.reverse()  # Reverse to chronological order
            else:
                # Get messages after a specific ID
                messages = self.redis_client.xrange(
                    stream_key,
                    f"({from_id}",  # Exclusive start
                    "+",
                    count=limit,
                )

            result = []
            for message_id, message_data in messages:
                result.append(
                    {
                        "id": message_id,
                        "user_id": int(message_data.get("user_id", 0)),
                        "content": message_data.get("content", ""),
                        "timestamp": message_data.get("timestamp", ""),
                    }
                )

            logger.info(
                "Messages retrieved from Redis Stream",
                extra={
                    "conversation_id": conversation_id,
                    "count": len(result),
                    "from_id": from_id,
                },
            )

            return result

        except redis.RedisError as e:
            logger.error(
                "Failed to retrieve messages from Redis Stream",
                extra={
                    "conversation_id": conversation_id,
                    "error": str(e),
                },
            )
            raise RedisStreamError(f"Failed to retrieve messages: {str(e)}") from e

    def ping_redis(self) -> bool:
        """
        Check if Redis is accessible

        Returns:
            True if Redis is accessible, False otherwise
        """
        try:
            return self.redis_client.ping()
        except redis.RedisError as e:
            logger.error("Redis ping failed", extra={"error": str(e)})
            return False

    def get_stream_info(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a conversation stream

        Args:
            conversation_id: UUID of the conversation

        Returns:
            Stream info dictionary or None if stream doesn't exist
        """
        try:
            stream_key = self._get_stream_key(conversation_id)
            info = self.redis_client.xinfo_stream(stream_key)
            return info
        except redis.ResponseError:
            # Stream doesn't exist
            return None
        except redis.RedisError as e:
            logger.error(
                "Failed to get stream info",
                extra={
                    "conversation_id": conversation_id,
                    "error": str(e),
                },
            )
            return None


# Singleton instance
redis_stream_client = RedisStreamClient()
