import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model

from conversations.models import Participant

from .redis_stream import RedisStreamError, redis_stream_client
from .throttle import message_throttler

User = get_user_model()
logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for chat messages
    """

    async def connect(self):
        """Handle WebSocket connection"""
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"
        self.user = self.scope["user"]

        # Check authentication
        if not self.user.is_authenticated:
            logger.warning(
                "Unauthenticated WebSocket connection attempt",
                extra={"conversation_id": self.conversation_id},
            )
            await self.close(code=4001)
            return

        # Check if user is a participant (sync to async)
        try:
            from channels.db import database_sync_to_async

            @database_sync_to_async
            def is_participant():
                return Participant.objects.filter(
                    conversation_id=self.conversation_id,
                    user=self.user,
                ).exists()

            if not await is_participant():
                logger.warning(
                    "Non-participant WebSocket connection attempt",
                    extra={
                        "user_id": self.user.id,
                        "conversation_id": self.conversation_id,
                    },
                )
                await self.close(code=4003)
                return

        except Exception as e:
            logger.error(
                "Error checking participant membership",
                extra={
                    "user_id": self.user.id,
                    "conversation_id": self.conversation_id,
                    "error": str(e),
                },
            )
            await self.close(code=4500)
            return

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

        logger.info(
            "WebSocket connection established",
            extra={
                "user_id": self.user.id,
                "conversation_id": self.conversation_id,
            },
        )

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

            logger.info(
                "WebSocket connection closed",
                extra={
                    "user_id": getattr(self.user, "id", None),
                    "conversation_id": self.conversation_id,
                    "close_code": close_code,
                },
            )

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get("type")

            if message_type == "message.send":
                await self.handle_message_send(data)
            else:
                await self.send_error(
                    "INVALID_TYPE",
                    f"Unknown message type: {message_type}",
                )

        except json.JSONDecodeError:
            await self.send_error("INVALID_JSON", "Invalid JSON format")
        except Exception as e:
            logger.error(
                "Error processing WebSocket message",
                extra={
                    "user_id": self.user.id,
                    "conversation_id": self.conversation_id,
                    "error": str(e),
                },
            )
            await self.send_error("INTERNAL_ERROR", "An error occurred")

    async def handle_message_send(self, data: dict):
        """Handle message send request"""
        content = data.get("content", "").strip()

        # Validate content length
        if not content or len(content) < 1:
            await self.send_error("INVALID_CONTENT", "Message content is required")
            return

        if len(content) > 2000:
            await self.send_error(
                "CONTENT_TOO_LONG",
                "Message content must be 2000 characters or less",
            )
            return

        # Check throttling
        if not message_throttler.is_allowed(self.user.id, self.conversation_id):
            await self.send_error(
                "THROTTLED",
                "You are sending messages too quickly. Please slow down.",
            )
            return

        # Add message to Redis Stream
        try:
            from channels.db import database_sync_to_async

            @database_sync_to_async
            def add_to_stream():
                return redis_stream_client.add_message(
                    self.conversation_id,
                    self.user.id,
                    self.user.username,
                    content,
                )

            message_id = await add_to_stream()

            # Broadcast message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": {
                        "id": message_id,
                        "user_id": self.user.id,
                        "user_email": self.user.email,
                        "username": self.user.username,
                        "content": content,
                        "conversation_id": self.conversation_id,
                    },
                },
            )

            logger.info(
                "Message sent",
                extra={
                    "user_id": self.user.id,
                    "conversation_id": self.conversation_id,
                    "message_id": message_id,
                },
            )

        except RedisStreamError as e:
            logger.error(
                "Failed to add message to Redis Stream",
                extra={
                    "user_id": self.user.id,
                    "conversation_id": self.conversation_id,
                    "error": str(e),
                },
            )
            await self.send_error("STORAGE_ERROR", "Failed to save message")

    async def chat_message(self, event):
        """Handle broadcast message from group"""
        message = event["message"]

        await self.send(
            text_data=json.dumps(
                {
                    "type": "message",
                    "message": message,
                }
            )
        )

    async def send_error(self, code: str, message: str):
        """Send error message to client"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "error",
                    "code": code,
                    "message": message,
                }
            )
        )
