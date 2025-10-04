"""
Views for conversations
"""

import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Conversation, Participant
from .serializers import ConversationCreateSerializer, ConversationSerializer

logger = logging.getLogger(__name__)


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing conversations
    """

    permission_classes = [IsAuthenticated]
    queryset = Conversation.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return ConversationCreateSerializer
        return ConversationSerializer

    def get_queryset(self):
        """
        Filter conversations where user is a participant
        """
        return Conversation.objects.filter(participants__user=self.request.user).distinct()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conversation = serializer.save()

        logger.info(
            "Conversation created",
            extra={
                "user_id": request.user.id,
                "conversation_id": str(conversation.id),
            },
        )

        # Return with full serializer
        output_serializer = ConversationSerializer(conversation)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve conversation only if user is a participant
        """
        conversation = self.get_object()
        if not Participant.objects.filter(
            conversation=conversation,
            user=request.user,
        ).exists():
            return Response(
                {"error": "You are not a participant in this conversation"},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = self.get_serializer(conversation)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def add_participant(self, request, pk=None):
        """
        Add a participant to a conversation
        """
        conversation = self.get_object()

        # Check if requester is admin
        participant = Participant.objects.filter(
            conversation=conversation,
            user=request.user,
            role=Participant.Role.ADMIN,
        ).first()

        if not participant:
            return Response(
                {"error": "Only admins can add participants"},
                status=status.HTTP_403_FORBIDDEN,
            )

        user_id = request.data.get("user_id")
        if not user_id:
            return Response(
                {"error": "user_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
            Participant.objects.get_or_create(
                conversation=conversation,
                user=user,
                defaults={"role": Participant.Role.MEMBER},
            )
            logger.info(
                "Participant added to conversation",
                extra={
                    "user_id": request.user.id,
                    "conversation_id": str(conversation.id),
                    "new_participant_id": user_id,
                },
            )
            return Response({"success": True}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
