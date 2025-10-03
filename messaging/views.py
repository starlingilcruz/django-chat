"""
REST API views for message history
"""

import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from conversations.models import Participant

from .redis_stream import RedisStreamError, redis_stream_client

logger = logging.getLogger(__name__)


class MessageHistoryView(APIView):
    """
    API endpoint for retrieving message history
    GET /api/v1/conversations/<conversation_id>/messages
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        """
        Retrieve message history for a conversation

        Query parameters:
        - from: Message ID to start from (optional)
        - limit: Maximum number of messages to retrieve (default: 50, max: 100)
        """
        # Check if user is a participant
        if not Participant.objects.filter(
            conversation_id=conversation_id,
            user=request.user,
        ).exists():
            logger.warning(
                "Unauthorized message history access attempt",
                extra={
                    "user_id": request.user.id,
                    "conversation_id": conversation_id,
                },
            )
            return Response(
                {"error": "You are not a participant in this conversation"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Parse query parameters
        from_id = request.query_params.get("from", "-")
        try:
            limit = min(int(request.query_params.get("limit", 50)), 100)
        except ValueError:
            limit = 50

        # Retrieve messages from Redis Stream
        try:
            messages = redis_stream_client.get_messages(
                conversation_id=conversation_id,
                from_id=from_id,
                limit=limit,
            )

            # Determine next_from for pagination
            next_from = messages[-1]["id"] if messages else None

            logger.info(
                "Message history retrieved",
                extra={
                    "user_id": request.user.id,
                    "conversation_id": conversation_id,
                    "count": len(messages),
                },
            )

            return Response(
                {
                    "conversation_id": conversation_id,
                    "messages": messages,
                    "next_from": next_from,
                },
                status=status.HTTP_200_OK,
            )

        except RedisStreamError as e:
            logger.error(
                "Failed to retrieve message history",
                extra={
                    "user_id": request.user.id,
                    "conversation_id": conversation_id,
                    "error": str(e),
                },
            )
            return Response(
                {"error": "Failed to retrieve messages"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
